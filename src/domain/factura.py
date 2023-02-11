"""Factura model."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

class Deducible(BaseModel):
    emisor_rfc: str
    receptor_rfc: str
    descripcion: Optional[str]
    deducible: Optional[bool]
    regimen_id: Optional[int]

class Concepto(Deducible):
    """Concepto model."""
    factura_id: str
    emisor_nombre: str


class Factura(BaseModel):
    """Factura model."""
    id: str
    filepath: str
    fecha: datetime
    receptor_rfc: str
    receptor_nombre: str
    emisor_nombre: str
    emisor_rfc: str
    tipo_comprobante: str
    subtotal: float
    total: float
    iva_retenido: float
    isr_retenido: float
    iva_trasladado: float
    isr_trasladado: float
    conceptos: List[Concepto]
    deducible: Optional[bool]
    regimen_id: Optional[int]
