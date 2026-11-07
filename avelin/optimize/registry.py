"""Validate versioned catalog data without probing or modifying the host.

Descriptors are inert data, not permission to perform an operation. The sole
recognized operation is a Boolean GSettings preference; execution, consent,
capability checks, snapshot persistence and recovery are intentionally absent.
"""
import json
import re
from urllib.parse import urlsplit


class RegistryError(ValueError):
    """A catalog is malformed or contains unsupported data."""


_ID = re.compile(r'[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z')
_SCHEMA = re.compile(r'[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+\Z')
_KEY = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')
_TOKEN = re.compile(r'[a-z0-9][a-z0-9._-]{0,63}\Z')
_FIELDS = {'id', 'description', 'source', 'risk', 'advanced', 'reversible',
           'warning', 'read', 'apply', 'revert', 'applicability'}


def _object(value, keys, label):
    if type(value) is not dict or set(value) != keys:
        raise RegistryError(f'{label}: expected exactly {sorted(keys)}')


def _text(value, label, limit, allow_empty=False):
    if (type(value) is not str or len(value) > limit or
            (not allow_empty and not value.strip()) or
            any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise RegistryError(f'{label}: invalid text')


def _citation(value):
    _text(value, 'source', 2048)
    if any(c.isspace() for c in value) or '\\' in value:
        raise RegistryError('source: invalid URL')
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError as exc:
        raise RegistryError('source: invalid URL') from exc
    if (url.scheme != 'https' or not url.hostname or url.username is not None or
            url.password is not None or port not in (None, 443)):
        raise RegistryError('source: expected HTTPS URL without credentials')


def _applicability(value):
    _object(value, {'distros', 'desktops', 'hardware'}, 'applicability')
    for name, choices in value.items():
        if type(choices) is not list or len(choices) > 100:
            raise RegistryError(f'applicability.{name}: expected a bounded list')
        if any(type(x) is not str or not _TOKEN.fullmatch(x) for x in choices):
            raise RegistryError(f'applicability.{name}: invalid selector')
        if len(set(choices)) != len(choices):
            raise RegistryError(f'applicability.{name}: duplicate selector')


def _entry(value):
    _object(value, _FIELDS, 'entry')
    if type(value['id']) is not str or len(value['id']) > 128 or not _ID.fullmatch(value['id']):
        raise RegistryError('id: invalid identifier')
    _text(value['description'], 'description', 500)
    _citation(value['source'])
    if value['risk'] not in ('low', 'medium', 'high'):
        raise RegistryError('risk: unsupported tier')
    if type(value['advanced']) is not bool or type(value['reversible']) is not bool:
        raise RegistryError('advanced and reversible must be Boolean')
    if value['risk'] == 'high' and not value['advanced']:
        raise RegistryError('high risk requires advanced opt-in')
    _text(value['warning'], 'warning', 1000, allow_empty=True)
    if value['reversible']:
        _object(value['revert'], {'type'}, 'revert')
        if value['revert']['type'] != 'snapshot':
            raise RegistryError('revert: unsupported descriptor')
    elif value['revert'] is not None or not value['warning'].strip():
        raise RegistryError('irreversible entries require a warning and null revert')
    _applicability(value['applicability'])
    read, apply = value['read'], value['apply']
    _object(read, {'type', 'schema', 'key'}, 'read')
    _object(apply, {'type', 'value'}, 'apply')
    if read['type'] != 'gsettings_boolean' or apply['type'] != read['type']:
        raise RegistryError('unsupported or mismatched operation')
    if (type(read['schema']) is not str or len(read['schema']) > 255 or
            not _SCHEMA.fullmatch(read['schema'])):
        raise RegistryError('read: invalid GSettings schema')
    if (type(read['key']) is not str or len(read['key']) > 128 or
            not _KEY.fullmatch(read['key'])):
        raise RegistryError('read: invalid GSettings key')
    if type(apply['value']) is not bool:
        raise RegistryError('apply: expected Boolean')


def validate_catalog(catalog):
    """Reject unsupported data; return None without mutating the input.

    Empty applicability lists mean no restriction for that dimension, not
    evidence of hardware support. Actual capability detection is future work.
    """
    _object(catalog, {'version', 'entries'}, 'catalog')
    if type(catalog['version']) is not int or catalog['version'] != 1:
        raise RegistryError('catalog: unsupported version')
    entries = catalog['entries']
    if type(entries) is not list or len(entries) > 1000:
        raise RegistryError('entries: expected a bounded list')
    seen = set()
    for item in entries:
        _entry(item)
        if item['id'] in seen:
            raise RegistryError('entries: duplicate id')
        seen.add(item['id'])


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError(f'JSON: duplicate key {key!r}')
        result[key] = value
    return result


def parse_catalog(text):
    """Parse bounded JSON, reject duplicate keys, and validate its structure."""
    if type(text) is not str or len(text.encode('utf-8', errors='surrogatepass')) > 1024 * 1024:
        raise RegistryError('JSON: expected at most 1 MiB of text')
    try:
        catalog = json.loads(text, object_pairs_hook=_unique_pairs)
    except (ValueError, RecursionError) as exc:
        raise RegistryError('JSON: invalid catalog') from exc
    validate_catalog(catalog)
    return catalog
