"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict

class AbstractFacturasRepository(ABC):
    """FacturasRepository."""

    @abstractmethod
    def filter(
        self,
        ids: Optional[List[str]] = None,
    ) -> List[Dict]:
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