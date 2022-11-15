"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from domain.nomina import Nomina

class AbstractNominasRepository(ABC):
    """NominasRepository."""

    @abstractmethod
    def filter(
        self,
        rfc: str,
        ids: Optional[List[Nomina]] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> List[Nomina]:
        """Filter raw facturas."""
        raise NotImplementedError

    @abstractmethod
    def add(self, item: Nomina) -> Optional[Nomina]:
        """Create/update factura."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, item: Nomina) -> None:
        """Delete factura."""
        raise NotImplementedError