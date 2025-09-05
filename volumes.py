from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
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
    opts = params.get('DriverOpts')
    labels = params.get('Labels')
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
    filters = params.get('filters')
    return invoke_rest_endpoint(config, '/volumes/prune', 'POST', query_params={'filters': filters})


