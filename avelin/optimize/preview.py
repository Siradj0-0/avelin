"""Assess supplied capability observations and construct an inert preview.

No host detection, authorization, mutation or snapshot is performed here. A
ready result is a planning state, not proof that the setting remains writable.
"""
from .applicability import evaluate_applicability
from .registry import RegistryError, _object, validate_catalog


def _validate_capability(capability):
    _object(capability, {'supported', 'readable', 'writable', 'current'}, 'capability')
    for name in ('supported', 'readable', 'writable', 'current'):
        value = capability[name]
        if value is not None and type(value) is not bool:
            raise RegistryError(f'capability.{name}: expected Boolean or None')
    if capability['supported'] is False and (capability['readable'] is True or capability['writable'] is True):
        raise RegistryError('capability: unsupported setting cannot be readable or writable')
    if capability['current'] is not None and (capability['supported'] is not True or capability['readable'] is not True):
        raise RegistryError('capability: current value requires supported and readable')


def preview(entry, observations, capability):
    """Describe a proposed operation from supplied observations, without I/O.

    None denotes unknown; False is an actual observation. A preview can become
    stale immediately and must not be used as authority to perform a write.
    """
    validate_catalog({'version': 1, 'entries': [entry]})
    applicable = evaluate_applicability(entry['applicability'], observations)
    _validate_capability(capability)
    current, target = capability['current'], entry['apply']['value']
    if applicable == 'not_applicable':
        status = 'not_applicable'
    elif capability['supported'] is False or capability['readable'] is False:
        status = 'unavailable'
    elif applicable == 'unknown' or capability['supported'] is None or capability['readable'] is None or current is None:
        status = 'unknown'
    elif current == target:
        status = 'no_change'
    elif capability['writable'] is False:
        status = 'unavailable'
    elif capability['writable'] is None:
        status = 'unknown'
    else:
        status = 'ready'
    return {
        'status': status,
        'id': entry['id'],
        'description': entry['description'],
        'schema': entry['read']['schema'],
        'key': entry['read']['key'],
        'current': current,
        'target': target,
        'source': entry['source'],
        'risk': entry['risk'],
        'warning': entry['warning'],
        'advanced': entry['advanced'],
        'reversible': entry['reversible'],
    }
