"""Capture inert, exact GSettings Boolean observation metadata.

No Gio calls, persistence, authorization or restoration are performed. A
snapshot does not prove that a write was attempted or succeeded. The caller
must obtain fresh, consistent observations in the correct desktop session.
"""
from dataclasses import dataclass

from .registry import RegistryError, _object, validate_catalog


@dataclass(frozen=True)
class BooleanSnapshot:
    setting_id: str
    schema: str
    key: str
    effective: bool
    override_present: bool
    override_value: bool | None
    target: bool


def capture_snapshot(entry, observed):
    """Validate and preserve supplied prior state without accessing the host.

    GSettings' user value may be absent even when the effective value is False.
    That absence is distinct from a False override. If values cannot be
    reconciled, decline to capture rather than guessing at a consistent state.
    An eventual reset could expose a changed default and therefore cannot
    guarantee recovery of the previously effective value.
    """
    validate_catalog({'version': 1, 'entries': [entry]})
    if not entry['reversible']:
        raise RegistryError('snapshot: setting is not reversible')
    _object(observed, {'effective', 'override_present', 'override_value'}, 'observation')
    effective = observed['effective']
    present = observed['override_present']
    value = observed['override_value']
    if type(effective) is not bool or type(present) is not bool:
        raise RegistryError('snapshot: effective value and override presence must be known')
    if present:
        if type(value) is not bool or value != effective:
            raise RegistryError('snapshot: inconsistent or unknown user override')
    elif value is not None:
        raise RegistryError('snapshot: absent override must not have a value')
    return BooleanSnapshot(
        setting_id=entry['id'], schema=entry['read']['schema'], key=entry['read']['key'],
        effective=effective, override_present=present, override_value=value,
        target=entry['apply']['value'],
    )
