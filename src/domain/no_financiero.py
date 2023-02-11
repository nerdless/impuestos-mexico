"""No financiero daily status model."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

class DayStatus(BaseModel):
    """Factura model."""
    fecha: datetime
    institucion_id: str
    abono: float
    comision: float
    iva_comision: float
    interes: float
    iva_interes: float
    recuperacion: float
    capital: float
