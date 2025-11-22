from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_volume_name, validate_json_param, validate_boolean_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_volumes(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/volumes', 'GET')


def inspect_volume(config, params, *args, **kwargs):
    name = params.get('name')
    if not name:
        raise ConnectorError('Missing required input: name')
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
    name = params.get('name')
    force = params.get('force', False)
    if not name:
        raise ConnectorError('Missing required input: name')
    return invoke_rest_endpoint(config, '/volumes/{0}'.format(name), 'DELETE', query_params={'force': int(bool(force))})


def prune_volumes(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_volumes')
    query_params = {'filters': filters} if filters else {}
    return invoke_rest_endpoint(config, '/volumes/prune', 'POST', query_params=query_params)


