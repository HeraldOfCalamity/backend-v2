# app/infrastructure/repositories/print_repo.py
from __future__ import annotations
import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
import re
from PIL import Image

from jinja2 import Environment, FileSystemLoader, select_autoescape
import requests
from xhtml2pdf import pisa

from beanie import PydanticObjectId
from app.core.config import settings
from app.infrastructure.schemas.historial import HistorialClinico  # beanie document
from app.infrastructure.repositories.historial_repo import signed_get  # presign GET urls 60s
from app.infrastructure.repositories.paciente_repo import get_paciente_profile_by_id  # perfil paciente

# === Config de plantillas y assets ===
ROOT_DIR = Path(__file__).resolve().parents[3]  # .../app
TEMPLATES_DIR = ROOT_DIR / "templates"
PRINT_DIR = TEMPLATES_DIR / "print"
ASSETS_DIR = PRINT_DIR / "assets"               # <= NUEVO
CSS_PATH = PRINT_DIR / "benedetta_pisa.css"
TPL_TRATAMIENTO = "print/tratamiento_pisa.html"    # <- Template pensado para xhtml2pdf (tablas, sin grid)

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def _file_to_data_uri(path: str | Path, max_w: int = 256) -> str | None:
    """Abre PNG/JPG local, reescala y devuelve data:image/jpeg;base64,..."""
    try:
        p = Path(path)
        if not p.exists():
            return None
        img = Image.open(p)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = img.size
        if max_w and w > max_w:
            ratio = max_w / float(w)
            img = img.resize((max_w, int(h * ratio)))
        out = BytesIO()
        img.save(out, format="JPEG", quality=88, optimize=True)
        b64 = base64.b64encode(out.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None

def _svg_file_to_png_data_uri(path: str | Path, max_w: int = 256) -> str | None:
    """Rasteriza un SVG local a PNG (si 'cairosvg' está disponible) y devuelve data:image/png;base64,..."""
    try:
        import cairosvg  # opcional
    except Exception:
        return None
    try:
        png_bytes = cairosvg.svg2png(url=str(path), output_width=max_w)
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def _resolve_logo_data_uri() -> str:
    # 1) Directo por settings: ya en formato data:image/...
    data_uri = getattr(settings, "CLINIC_LOGO_DATA_URI", None)
    if data_uri:
        return data_uri

    # 2) Path configurado por settings (SVG/PNG/JPG)
    logo_path = getattr(settings, "CLINIC_LOGO_PATH", None)
    candidates: List[Path] = []
    if logo_path:
        candidates.append(Path(logo_path))

    # 3) Fallbacks del backend (assets versionadas)
    candidates += [
        ASSETS_DIR / "benedetta-logo.png",       # PNG recomendado
        ASSETS_DIR / "benedetta-bellezza.svg",   # SVG (se rasteriza si es posible)
    ]

    for p in candidates:
        if not p.exists():
            continue
        ext = p.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg"):
            data = _file_to_data_uri(p, max_w=256)
            if data:
                return data
        if ext == ".svg":
            data = _svg_file_to_png_data_uri(p, max_w=256)
            if data:
                return data
    return ""  # último recurso: sin logo

def _clinic_info() -> Dict[str, str]:
    return {
        "logo_url": _resolve_logo_data_uri(),  # <= AHORA DATA URI
        "name": "Benedetta Bellezza",
        "sub1": "",
        "sub2": "Ministerio de salud- resolución ministerial N°825 cap IV art. 44. Cochabamba - Bolivia.",
        "phone": "",
        "address": "Av. América #459 entre Av. Santa Cruz y Calle Pantaleón Dalence.\n Edif. Torre Montreal piso 1, of. 3. Frente al Paseo Aranjuez.",
        "city": "",
    }


async def _fetch_context(historial_id: str, tratamiento_id: str, tenant_id: str) -> Dict[str, Any]:
    # 1) cargar historial + tratamiento
    hist = await HistorialClinico.find_one(
        HistorialClinico.id == PydanticObjectId(historial_id),
        HistorialClinico.tenant_id == PydanticObjectId(tenant_id)
    )
    if not hist:
        raise ValueError("Historial no encontrado")

    trat = next((t for t in hist.tratamientos if t.id == tratamiento_id), None)
    if not trat:
        raise ValueError("Tratamiento no encontrado")

    # 2) perfil de paciente
    prof = await get_paciente_profile_by_id(str(hist.paciente_id), str(tenant_id))
    user = getattr(prof, "user", None)
    pac = getattr(prof, "paciente", None)

    # 3) ordenar entradas y firmar imágenes (solo campo imagenes)
    entradas = sorted(trat.entradas, key=lambda e: getattr(e, "createdAt", None) or "")
    entradas_ctx: List[Dict[str, Any]] = []
    for idx, e in enumerate(entradas, start=1):
        urls = []
        for key in (e.imagenes or []):
            try:
                u = signed_get(key)
                if u and u.get("url"):
                    urls.append(_url_to_data_uri(u["url"]))   # <- convertimos AQUÍ
            except Exception:
                continue
        entradas_ctx.append({
            "idx": idx,
            "fecha": str(e.createdAt)[:16].replace("T", " "),
            "recursos": (e.recursosTerapeuticos or ""),
            "evolucion": (e.evolucionText or ""),
            "recomendaciones": getattr(e, "recomendaciones", "") or "",
            "imagenes": urls,
        })

    clinic = _clinic_info()
    # también podemos embeber el logo si es remoto:
    if clinic.get("logo_url", "").startswith("http"):
        clinic["logo_url"] = _url_to_data_uri(clinic["logo_url"], max_w=256)

    ctx = {
        "css_inline": CSS_PATH.read_text(encoding="utf-8"),
        "clinic": clinic,
        "historial_id": str(hist.id),
        "paciente": {
            "nombre": f"{getattr(user,'name','') or ''} {getattr(user,'lastname','') or ''}".strip(),
            "ci": getattr(user, "ci", "—") or "—",
            "phone": getattr(user, "phone", "—") or "—",
            "fecha_nac": getattr(pac, "fecha_nacimiento", None),
        },
        "tratamiento": {
            "motivo": trat.motivo or "—",
            "antPersonales": trat.antPersonales or "",
            "antFamiliares": getattr(trat, "antfamiliares", "") or "",
            "condActual": trat.condActual or "",
            "intervencionClinica": trat.intervencionClinica or "",
            "diagnostico": getattr(trat, "diagnostico", "") or "",
        },
        "entradas": entradas_ctx,
    }
    return ctx

def _render_html(template_name: str, context: Dict[str, Any]) -> str:
    tpl = _env.get_template(template_name)
    return tpl.render(**context)

def _html_to_pdf_pisa(html: str) -> bytes:
    out = BytesIO()
    html = re.sub(r"<br(?!/)>", "<br/>", html)
    pisa.CreatePDF(src=html, dest=out, encoding='utf-8')
    return out.getvalue()

# API pública del repo:
async def generate_tratamiento_pdf(historial_id: str, tratamiento_id: str, tenant_id: str) -> bytes:
    ctx = await _fetch_context(historial_id, tratamiento_id, tenant_id)
    html = _render_html(TPL_TRATAMIENTO, ctx)
    return _html_to_pdf_pisa(html)

def _url_to_data_uri(url: str, max_w: int = 1400) -> str:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        # convertir a RGB y reescalar si es muy ancha (para peso de PDF)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = img.size
        if max_w and w > max_w:
            ratio = max_w / float(w)
            img = img.resize((max_w, int(h * ratio)))
        out = BytesIO()
        img.save(out, format="JPEG", quality=85, optimize=True)
        b64 = base64.b64encode(out.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        # si algo falla, devolvemos la URL firmada tal cual (último recurso)
        return url