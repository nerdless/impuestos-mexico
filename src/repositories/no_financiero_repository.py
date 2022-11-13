"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from domain.factura import Factura

class AbstractNoFinancieroRepository(ABC):
    """No Financiero revenue Repository."""

    @abstractmethod
    def filter(
        self,
        institucion_ids: Optional[List[Factura]] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> List[Factura]:
        """Filter raw facturas."""
        raise NotImplementedError

    @abstractmethod
    def add(self, item: Factura) -> Optional[Factura]:
        """Create/update factura."""
        raise NotImplementedError
