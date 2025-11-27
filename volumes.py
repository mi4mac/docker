from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_volume_name, validate_json_param, validate_boolean_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_volumes(config, params, *args, **kwargs):
    # Docker Engine API supports optional 'filters' for listing volumes.
    # We accept an optional JSON string or object for filters and pass it through.
    filters = validate_json_param(params.get('filters'), 'filters', 'list_volumes') if params else None
    query_params = {'filters': filters} if filters else None
    return invoke_rest_endpoint(config, '/volumes', 'GET', query_params=query_params)


def inspect_volume(config, params, *args, **kwargs):
    validate_required_params(params, ['name'], 'inspect_volume')
    name = params.get('name')
    validate_volume_name(name, 'inspect_volume')
    return invoke_rest_endpoint(config, '/volumes/{0}'.format(name), 'GET')


def create_volume(config, params, *args, **kwargs):
    name = params.get('Name')
    driver = params.get('Driver')
    opts = validate_json_param(params.get('DriverOpts'), 'DriverOpts', 'create_volume')
    labels = validate_json_param(params.get('Labels'), 'Labels', 'create_volume')
    body = {}
    if name:
        body['Name'] = name
    if driver:
        body['Driver'] = driver
    if opts:
        body['DriverOpts'] = opts
    if labels:
        body['Labels'] = labels
    return invoke_rest_endpoint(config, '/volumes/create', 'POST', data=body)


def remove_volume(config, params, *args, **kwargs):
    validate_required_params(params, ['name'], 'remove_volume')
    name = params.get('name')
    validate_volume_name(name, 'remove_volume')
    force = validate_boolean_param(params.get('force', False), 'force', 'remove_volume', False)
    return invoke_rest_endpoint(config, '/volumes/{0}'.format(name), 'DELETE', query_params={'force': int(bool(force))})


def prune_volumes(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_volumes')
    query_params = {'filters': filters} if filters else None
    return invoke_rest_endpoint(config, '/volumes/prune', 'POST', query_params=query_params)


