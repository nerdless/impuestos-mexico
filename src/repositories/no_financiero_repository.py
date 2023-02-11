"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from src.domain.no_financiero import DayStatus

class AbstractNoFinancieroRepository(ABC):
    """No Financiero revenue Repository."""

    @abstractmethod
    def filter(
        self,
        institucion_ids: Optional[List[DayStatus]] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None
    ) -> List[DayStatus]:
        """Filter raw facturas."""
        raise NotImplementedError

    @abstractmethod
    def add(self, item: DayStatus) -> Optional[DayStatus]:
        """Create/update factura."""
        raise NotImplementedError
