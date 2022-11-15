"""Nomina model."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Nomina(BaseModel):
    """Nomina model."""
    id: str
    fecha_inicial: datetime
    fecha_final: datetime
    fecha_pago: datetime
    receptor: str
    emisor: str
    percepciones: float
    deducciones: float
    otros_pagos: float
    total_gravado: float
    total_retenido: float
    isr_retenido: float
    imss_retenido: float
