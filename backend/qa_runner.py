"""Ejecuta cada prueba y genera un reporte Markdown comparable."""

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(command, cwd):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def main() -> int:
    root = Path(__file__).parent
    workspace = root.parent
    collected = run(
        [sys.executable, "-m", "pytest", str(root), "--collect-only", "-q"],
        workspace,
    )
    nodeids = [
        line.strip()
        for line in collected.stdout.splitlines()
        if "::" in line and not line.startswith("=")
    ]
    results = []
    for nodeid in nodeids:
        result = run([sys.executable, "-m", "pytest", nodeid, "-q"], workspace)
        output = (result.stdout + "\n" + result.stderr).strip()
        summary = re.search(r"(\d+) passed|(\d+) failed|(\d+) error", output)
        obtained = "PASS" if result.returncode == 0 else "FAIL"
        cause = "Sin discrepancias." if result.returncode == 0 else (
            output[-1000:] or "La prueba terminó sin salida diagnóstica."
        )
        results.append((nodeid, "PASS", obtained, cause, summary.group(0) if summary else "sin resumen"))

    failed = [result for result in results if result[2] != "PASS"]
    estado = "PASS" if not failed and collected.returncode == 0 else "FAIL"
    recommendations = (
        "Mantener las pruebas unitarias y agregar pruebas de integración con PostgreSQL y MongoDB."
        if estado == "PASS"
        else "Corregir primero las causas raíz indicadas en la columna de discrepancias."
    )
    rows = "\n".join(
        f"| `{nodeid}` | {expected} | {obtained} | {cause.replace(chr(10), ' ')[:300]} |"
        for nodeid, expected, obtained, cause, _summary in results
    )
    report = f"""# Reporte QA

- Fecha UTC: {datetime.now(timezone.utc).isoformat()}
- Resultado global: **{estado}**
- Pruebas ejecutadas: **{len(results)}**

## Resultados esperados vs. obtenidos

| Caso | Esperado | Obtenido | Discrepancia / causa raíz |
|---|---|---|---|
{rows or '| Sin pruebas | PASS | FAIL | No se pudieron descubrir pruebas. |'}

## Recomendaciones

{recommendations}
"""
    report_path = root / "qa_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReporte guardado en: {report_path}")
    return 0 if estado == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
