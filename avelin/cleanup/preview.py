"""A read-only observation contract, not a scan or permission to clean.

Allocated bytes describe observed regular-file allocation only. They are not a
claim about space that deleting those files would reclaim: links and open files
can prevent that, and shared extents or snapshots complicate accounting.
See https://man7.org/linux/man-pages/man2/unlink.2.html.
"""
from dataclasses import dataclass
from enum import Enum


class PreviewStatus(str, Enum):
    COMPLETE = 'complete'
    PARTIAL = 'partial'
    UNAVAILABLE = 'unavailable'


class RiskTier(str, Enum):
    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'


@dataclass(frozen=True)
class Preview:
    """Caller-supplied observations, with no I/O, execution, or approval.

    `scope` describes what was actually observed, not what may be deleted.
    A partial subtotal may be unknown, and an unavailable reading is unknown.
    Even a complete observation is not a guarantee of reclaimable bytes.
    """
    category: str
    scope: str
    risk: RiskTier
    status: PreviewStatus
    allocated_bytes: int | None
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.category, self.scope):
            if not isinstance(value, str) or not value.strip():
                raise ValueError('category and scope must be non-empty text')
        if not isinstance(self.risk, RiskTier) or not isinstance(self.status, PreviewStatus):
            raise ValueError('risk and status must use the declared enum values')
        if (not isinstance(self.warnings, tuple)
                or any(not isinstance(w, str) or not w.strip() for w in self.warnings)):
            raise ValueError('warnings must be a tuple of non-empty strings')
        n = self.allocated_bytes
        if n is not None and (not isinstance(n, int) or isinstance(n, bool) or n < 0):
            raise ValueError('allocated_bytes must be a non-negative integer or None')
        if self.status is PreviewStatus.COMPLETE and n is None:
            raise ValueError('a complete observation requires an allocated byte count')
        if self.status is PreviewStatus.UNAVAILABLE and n is not None:
            raise ValueError('an unavailable observation cannot have an allocated byte count')

    @property
    def reclaimable_bytes(self) -> None:
        """A measurement of allocation is not a prediction of freed space."""
        return None
