"""Evaluate catalog selectors against explicit, already-collected observations.

This module does not detect the host. A positive result is neither authorization
nor proof that an underlying setting is available, writable or safe to apply.
"""
from .registry import RegistryError, _TOKEN, _applicability, _object


def _observation_token(value, label):
    if value is not None and (type(value) is not str or not _TOKEN.fullmatch(value)):
        raise RegistryError(f'observations.{label}: invalid token')


def evaluate_applicability(rules, observations):
    """Return 'applicable', 'not_applicable' or 'unknown'.

    Within each dimension, selectors are alternatives; dimensions combine with
    AND. None means unknown; an empty hardware list means known absence. Empty
    selector lists impose no restriction. A definite mismatch wins over unknown.
    Identifiers are exact, lowercase catalog tokens; no distro family or hardware
    inference is performed.
    """
    _applicability(rules)
    _object(observations, {'distro', 'desktop', 'hardware'}, 'observations')
    _observation_token(observations['distro'], 'distro')
    _observation_token(observations['desktop'], 'desktop')
    hardware = observations['hardware']
    if hardware is not None:
        if type(hardware) is not list or len(hardware) > 100:
            raise RegistryError('observations.hardware: expected a bounded list or None')
        for token in hardware:
            if token is None:
                raise RegistryError('observations.hardware: invalid token')
            _observation_token(token, 'hardware')
        if len(set(hardware)) != len(hardware):
            raise RegistryError('observations.hardware: duplicate token')

    unknown = False
    for key, observed in (('distros', observations['distro']),
                          ('desktops', observations['desktop']),
                          ('hardware', hardware)):
        choices = rules[key]
        if not choices:
            continue
        if observed is None:
            unknown = True
        elif key == 'hardware':
            if not set(choices).intersection(observed):
                return 'not_applicable'
        elif observed not in choices:
            return 'not_applicable'
    return 'unknown' if unknown else 'applicable'
