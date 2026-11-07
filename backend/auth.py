import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .database import obtener_conexion

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    identificador: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UsuarioActual(BaseModel):
    id: int
    rut: str
    email: str
    nombre: str
    rol: str


def _secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY debe existir y tener al menos 32 caracteres.")
    return secret


def _crear_token(subject: str, rol: str, token_type: str, expires_delta: timedelta) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "rol": rol,
        "type": token_type,
        "iat": ahora,
        "exp": ahora + expires_delta,
    }
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _buscar_usuario(identificador: str):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.rut, u.email, u.nombre, u.password_hash,
                       r.nombre_rol
                FROM usuarios u
                JOIN roles r ON r.id = u.id_rol
                WHERE u.rut = %s OR u.email = %s
                """,
                (identificador, identificador),
            )
            return cursor.fetchone()
    finally:
        conexion.close()


def _crear_refresh_token(usuario_id: int, rol: str) -> str:
    token = _crear_token(
        str(usuario_id), rol, "refresh", timedelta(days=REFRESH_TOKEN_DAYS)
    )
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO refresh_tokens (usuario_id, token_hash, expira_en)
                VALUES (%s, %s, %s)
                """,
                (
                    usuario_id,
                    _hash_refresh_token(token),
                    datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS),
                ),
            )
        conexion.commit()
        return token
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def autenticar_usuario(identificador: str, password: str) -> TokenResponse:
    usuario = _buscar_usuario(identificador)
    if not usuario or not bcrypt.checkpw(
        password.encode("utf-8"), usuario[4].encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _crear_token(
        str(usuario[0]),
        usuario[5],
        "access",
        timedelta(minutes=ACCESS_TOKEN_MINUTES),
    )
    refresh_token = _crear_refresh_token(usuario[0], usuario[5])
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_MINUTES * 60,
    )


def renovar_tokens(refresh_token: str) -> TokenResponse:
    try:
        payload = jwt.decode(
            refresh_token, _secret_key(), algorithms=[ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise ValueError("Tipo de token inválido.")
        usuario_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        ) from error

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.nombre_rol
                FROM refresh_tokens t
                JOIN usuarios u ON u.id = t.usuario_id
                JOIN roles r ON r.id = u.id_rol
                WHERE t.usuario_id = %s
                  AND t.token_hash = %s
                  AND t.revocado_en IS NULL
                  AND t.expira_en > CURRENT_TIMESTAMP
                """,
                (usuario_id, _hash_refresh_token(refresh_token)),
            )
            registro = cursor.fetchone()
            if not registro:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token revocado o no encontrado.",
                )
            cursor.execute(
                """
                UPDATE refresh_tokens
                SET revocado_en = CURRENT_TIMESTAMP
                WHERE usuario_id = %s AND token_hash = %s
                """,
                (usuario_id, _hash_refresh_token(refresh_token)),
            )
        conexion.commit()
    finally:
        conexion.close()

    access_token = _crear_token(
        str(usuario_id),
        registro[0],
        "access",
        timedelta(minutes=ACCESS_TOKEN_MINUTES),
    )
    nuevo_refresh = _crear_refresh_token(usuario_id, registro[0])
    return TokenResponse(
        access_token=access_token,
        refresh_token=nuevo_refresh,
        expires_in=ACCESS_TOKEN_MINUTES * 60,
    )


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UsuarioActual:
    if not credenciales:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credenciales.credentials, _secret_key(), algorithms=[ALGORITHM]
        )
        if payload.get("type") != "access":
            raise ValueError("Tipo de token inválido.")
        usuario_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.rut, u.email, u.nombre, r.nombre_rol
                FROM usuarios u
                JOIN roles r ON r.id = u.id_rol
                WHERE u.id = %s
                """,
                (usuario_id,),
            )
            usuario = cursor.fetchone()
    finally:
        conexion.close()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UsuarioActual(
        id=usuario[0],
        rut=usuario[1],
        email=usuario[2],
        nombre=usuario[3],
        rol=usuario[4],
    )


def requerir_roles(*roles_permitidos: str) -> Callable:
    def dependencia(
        usuario: UsuarioActual = Depends(obtener_usuario_actual),
    ) -> UsuarioActual:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El rol no tiene permisos para esta operación.",
            )
        return usuario

    return dependencia
