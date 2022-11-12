"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from domain.factura import Factura

class AbstractFacturasRepository(ABC):
    """FacturasRepository."""

    @abstractmethod
    def filter(
        self,
        rfc: str,
        factura_ids: Optional[List[Factura]] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> List[Factura]:
        """Filter raw facturas."""
        raise NotImplementedError

    @abstractmethod
    def add(self, item: Factura) -> Optional[Factura]:
        """Create/update factura."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, item: Factura) -> None:
        """Delete factura."""
        raise NotImplementedError