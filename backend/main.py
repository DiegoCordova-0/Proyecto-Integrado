import csv
import io
import os
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

from .auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    autenticar_usuario,
    obtener_usuario_actual,
    renovar_tokens,
    requerir_roles,
)
from .calculator import TOTAL_FACTORES, procesar_factores_tributarios
from .declarations import (
    cambiar_estado_declaracion,
    listar_declaraciones,
    obtener_detalle_declaracion,
)
from .mongo_db import (
    almacenar_csv_crudo,
    listar_logs_auditoria,
    registrar_log_auditoria,
)

app = FastAPI(
    title="Mantenedor de Calificaciones y Factores Tributarios",
    version="0.1.0",
    description="API para DJ 1949 y DJ 1922 de nuam.",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


app.add_middleware(SecurityHeadersMiddleware)


class FactoresRequest(BaseModel):
    rut_usuario: str = Field(min_length=3, max_length=12)
    id_declaracion: int = Field(gt=0)
    factores: Annotated[
        list[Decimal],
        Field(min_length=TOTAL_FACTORES, max_length=TOTAL_FACTORES),
    ]


class FactoresResponse(BaseModel):
    exito: bool
    mensaje: str
    suma_calculada: str | None = None
    factores: list[str] | None = None


class EstadoRequest(BaseModel):
    estado: str = Field(pattern="^(Aprobado|Rechazado)$")
    comentario: str | None = Field(default=None, max_length=1000)


class DeclaracionResponse(BaseModel):
    id: int
    folio: str
    rut_empresa: str
    periodo_tributario: int
    estado: str
    id_usuario_creador: int
    fecha_creacion: datetime | None
    suma_factores_criticos: str | None
    es_valido: bool | None


CSV_MAX_BYTES = 10 * 1024 * 1024
CSV_REQUIRED_COLUMNS = {
    "id_declaracion",
    *(f"factor_{indice}" for indice in range(1, TOTAL_FACTORES + 1)),
}


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    return {"estado": "ok"}


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Autenticación"])
def login(payload: LoginRequest) -> TokenResponse:
    return autenticar_usuario(payload.identificador, payload.password)


@app.post("/api/v1/auth/refresh", response_model=TokenResponse, tags=["Autenticación"])
def refresh(payload: RefreshRequest) -> TokenResponse:
    return renovar_tokens(payload.refresh_token)


@app.get("/api/v1/auth/me", tags=["Autenticación"])
def perfil_actual(usuario=Depends(obtener_usuario_actual)):
    return usuario


@app.get("/api/v1/auditoria/logs", tags=["Auditoría"])
def consultar_auditoria(
    limit: int = 100,
    skip: int = 0,
    _usuario=Depends(requerir_roles("Auditor")),
) -> dict:
    if not 1 <= limit <= 500 or skip < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los parámetros de paginación son inválidos.",
        )
    try:
        return {"logs": listar_logs_auditoria(limit=limit, skip=skip)}
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@app.get(
    "/api/v1/declaraciones",
    response_model=list[DeclaracionResponse],
    tags=["Declaraciones"],
)
def consultar_declaraciones(
    estado: str | None = None,
    periodo_tributario: int | None = None,
    rut_empresa: str | None = None,
    _usuario=Depends(obtener_usuario_actual),
) -> list[DeclaracionResponse]:
    if estado and estado not in ("Borrador", "Pendiente", "Aprobado", "Rechazado"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Estado de declaración inválido.",
        )
    return [
        DeclaracionResponse(**declaracion)
        for declaracion in listar_declaraciones(
            estado, periodo_tributario, rut_empresa
        )
    ]


@app.get("/api/v1/declaraciones/{id_declaracion}", tags=["Declaraciones"])
def consultar_detalle(
    id_declaracion: int,
    _usuario=Depends(requerir_roles("Aprobador")),
) -> dict:
    detalle = obtener_detalle_declaracion(id_declaracion)
    if detalle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Declaración no encontrada.",
        )
    return detalle


@app.patch(
    "/api/v1/declaraciones/{id_declaracion}/estado",
    tags=["Declaraciones"],
)
def actualizar_estado(
    id_declaracion: int,
    payload: EstadoRequest,
    request: Request,
    usuario=Depends(requerir_roles("Aprobador")),
) -> dict:
    try:
        resultado = cambiar_estado_declaracion(
            id_declaracion,
            payload.estado,
            usuario.id,
            payload.comentario,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        )
    registrar_log_auditoria(
        usuario.rut,
        "CAMBIO_ESTADO_DECLARACION",
        (
            f"Declaración {id_declaracion}: estado cambiado a {payload.estado}. "
            f"Comentario: {payload.comentario or 'sin comentario'}."
        ),
        payload.estado.upper(),
        request.client.host if request.client else None,
    )
    return resultado


@app.post(
    "/api/v1/declaraciones/carga-masiva",
    tags=["Declaraciones"],
)
async def carga_masiva_csv(
    request: Request,
    archivo: UploadFile = File(...),
    usuario=Depends(requerir_roles("Analista")),
) -> dict:
    if not archivo.filename or not archivo.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten archivos con extensión .csv.",
        )
    contenido_bytes = await archivo.read(CSV_MAX_BYTES + 1)
    if len(contenido_bytes) > CSV_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo CSV supera el límite de 10 MB.",
        )
    try:
        contenido = contenido_bytes.decode("utf-8-sig")
        lector = csv.DictReader(io.StringIO(contenido))
        encabezados = set(lector.fieldnames or [])
        faltantes = CSV_REQUIRED_COLUMNS - encabezados
        if faltantes:
            raise ValueError(
                f"Faltan columnas requeridas: {', '.join(sorted(faltantes))}."
            )
        filas = list(lector)
        if not filas:
            raise ValueError("El archivo CSV no contiene filas de datos.")
    except (UnicodeDecodeError, csv.Error, ValueError) as error:
        registrar_log_auditoria(
            usuario.rut,
            "CARGA_CSV_INVALIDA",
            str(error),
            "RECHAZADO",
            request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV inválido: {error}",
        ) from error

    if not almacenar_csv_crudo(
        archivo.filename,
        contenido,
        usuario.rut,
        len(filas),
        request.client.host if request.client else None,
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible almacenar el CSV crudo en MongoDB.",
        )

    resultados = []
    for numero_fila, fila in enumerate(filas, start=2):
        try:
            id_declaracion = int(fila["id_declaracion"])
            if id_declaracion <= 0:
                raise ValueError("id_declaracion debe ser positivo.")
            factores = [fila[f"factor_{indice}"] for indice in range(1, TOTAL_FACTORES + 1)]
        except (KeyError, TypeError, ValueError) as error:
            resultados.append(
                {"fila": numero_fila, "exito": False, "mensaje": str(error)}
            )
            continue
        resultado = procesar_factores_tributarios(
            usuario.rut,
            id_declaracion,
            factores,
            request.client.host if request.client else None,
        )
        resultados.append({"fila": numero_fila, **resultado})

    exitosas = sum(1 for resultado in resultados if resultado["exito"])
    return {
        "archivo": archivo.filename,
        "filas_procesadas": len(resultados),
        "filas_exitosas": exitosas,
        "filas_rechazadas": len(resultados) - exitosas,
        "resultados": resultados,
    }


@app.post(
    "/api/v1/declaraciones/{id_declaracion}/factores",
    response_model=FactoresResponse,
    tags=["Factores tributarios"],
)
def guardar_factores(
    id_declaracion: int,
    payload: FactoresRequest,
    request: Request,
    usuario=Depends(requerir_roles("Analista")),
) -> FactoresResponse:
    if payload.id_declaracion != id_declaracion:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El id de la ruta no coincide con el id_declaracion del payload.",
        )

    resultado = procesar_factores_tributarios(
        rut_usuario=usuario.rut,
        id_declaracion=id_declaracion,
        lista_factores=payload.factores,
        ip_cliente=request.client.host if request.client else None,
    )
    if not resultado["exito"]:
        if resultado.get("suma_calculada") is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=resultado,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=resultado["mensaje"],
        )
    return FactoresResponse(**resultado)
