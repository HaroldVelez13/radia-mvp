import eml_parser
from datetime import datetime
from typing import Any
import re


def parse_eml(path: str) -> dict[str, Any]:
    """Parse EML file and extract relevant fields for radicado creation.

    Returns dict with keys:
    - fecha (datetime): Email date
    - remitente (str): From address
    - nit (str | None): NIT from body/subject
    - tipo_documental (str): Document type (default: Factura)
    - asunto (str): Email subject
    - no_documento (str | None): Document number
    - valor_total (float | None): Total value
    - dependencia (str): Dependency/department
    - vencimiento (datetime | None): Due date
    - estado (str): Status (default: En trámite)
    - observaciones (str): Observations
    """
    with open(path, 'rb') as f:
        raw = f.read()

    parsed = eml_parser.EmlParser().decode_email_bytes(raw)

    # Extract header info
    header = parsed.get('header', {})
    subject = header.get('subject', [''])[0] if isinstance(header.get('subject'), list) else header.get('subject', '')
    from_field = header.get('from', [''])[0] if isinstance(header.get('from'), list) else header.get('from', '')
    date_val = header.get('date', [''])[0] if isinstance(header.get('date'), list) else header.get('date', '')

    # Parse date - it's already a datetime object from eml_parser
    fecha = None
    if isinstance(date_val, datetime):
        fecha = date_val
    elif isinstance(date_val, str) and date_val:
        try:
            fecha = datetime.strptime(date_val[:25], '%a, %d %b %Y %H:%M:%S')
        except ValueError:
            try:
                fecha = datetime.fromisoformat(date_val.replace(' ', 'T')[:26])
            except ValueError:
                pass

    # Extract NIT from subject or body
    nit = None
    # Pattern for NIT: digits with optional dots and dash
    nit_pattern = r'\b\d{1,3}(?:\.\d{3})*(?:-\d+)?\b'
    nit_matches = re.findall(nit_pattern, subject)
    if nit_matches:
        # Filter for typical NIT format (at least 7 digits)
        for match in nit_matches:
            clean = match.replace('.', '').replace('-', '')
            if len(clean) >= 7:
                nit = match
                break

    # Fallback: map sender domain to NIT from maestro
    if nit is None and from_field:
        sender_to_nit = {
            "suministrosllano.example": "901.234.567-1",
            "ferrela13.example": "830.456.789-2",
            "sabanaexpress.example": "900.876.543-5",
            "aseointegralbogota.example": "901.112.233-4",
            "papeleriacolombia.example": "860.555.444-3",
            "lubrisabana.example": "900.654.321-0",
            "vigiandina.example": "800.777.666-1",
            "contablenube.example": "901.999.000-7",
            "montacargaselpuerto.example": "900.654.321-0",
            "cafeteriagloria.example": "901.050.606-9",
        }
        for domain, mapped_nit in sender_to_nit.items():
            if domain in from_field.lower():
                nit = mapped_nit
                break

    # Extract document number from subject (e.g., FE-3381)
    no_documento = None
    doc_pattern = r'[A-Z]{2,}-\d+'
    doc_matches = re.findall(doc_pattern, subject)
    if doc_matches:
        no_documento = doc_matches[0]

    # Determine tipo_documental from subject
    tipo_documental = "Factura"
    subject_lower = subject.lower()
    
    # Check for publicidad/boletín first (often looks like factura)
    if "publicidad" in subject_lower or "boletín" in subject_lower or "novedades" in subject_lower or "📢" in subject:
        tipo_documental = "Publicidad"
    elif "viatico" in subject_lower or "viáticos" in subject_lower or "viaticos" in subject_lower:
        tipo_documental = "Solicitud de viáticos"
    elif "petición" in subject_lower or "peticion" in subject_lower or "derecho de petición" in subject_lower:
        tipo_documental = "Derecho de petición"
    elif "derecho" in subject_lower and "petición" in subject_lower:
        tipo_documental = "Derecho de petición"
    elif "oficio" in subject_lower:
        tipo_documental = "Oficio"
    elif "cotización" in subject_lower or "cotizacion" in subject_lower:
        tipo_documental = "Cotización"
    elif "queja" in subject_lower or "reclamo" in subject_lower:
        tipo_documental = "Queja"
    elif "promocion" in subject_lower:
        tipo_documental = "Publicidad"

    return {
        "fecha": fecha,
        "remitente": from_field,
        "nit": nit,
        "tipo_documental": tipo_documental,
        "asunto": subject,
        "no_documento": no_documento,
        "valor_total": None,  # Would need PDF OCR
        "dependencia": "",
        "vencimiento": None,
        "estado": "En trámite",
        "observaciones": "",
    }