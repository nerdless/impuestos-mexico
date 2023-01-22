"""Abstract raw facturas repository."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from pandas import DataFrame

class AbstractISRsRepository(ABC):
    """ISRsRepository."""

    @abstractmethod
    def filter(
        self,
        fecha: int,
    ) -> DataFrame:
        """Filter raw facturas."""
        raise NotImplementedError