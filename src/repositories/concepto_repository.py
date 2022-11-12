"""Abstract deducible repository."""
from abc import ABC, abstractmethod
from typing import Optional
from domain.factura import Concepto

class AbstractConceptosRepository(ABC):
    """ConceptoRepository."""

    @abstractmethod
    def add(self, item: Concepto) -> Optional[Concepto]:
        """Create/update factura."""
        raise NotImplementedError