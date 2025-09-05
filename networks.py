from connectors.core.connector import get_logger, ConnectorError
try:
    from .utils import invoke_rest_endpoint
    from .constants import LOGGER_NAME
except ImportError:
    from utils import invoke_rest_endpoint
    from constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_networks(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/networks', 'GET')


def inspect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    if not net_id:
        raise ConnectorError('Missing required input: id')

    return invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'GET')


def create_network(config, params, *args, **kwargs):
    name = params.get('Name')
    if not name:
        raise ConnectorError('Missing required input: Name')
    body = {
        'Name': name,
        'Driver': params.get('Driver'),
        'Options': params.get('Options'),

    }
    return invoke_rest_endpoint(config, '/networks/create', 'POST', data=body)


def connect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    container = params.get('Container')
    if not net_id or not container:
        raise ConnectorError('Missing required inputs: id, Container')
    body = {'Container': container}
    return invoke_rest_endpoint(config, '/networks/{0}/connect'.format(net_id), 'POST', data=body)


def disconnect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    container = params.get('Container')
    if not net_id or not container:
        raise ConnectorError('Missing required inputs: id, Container')
    body = {'Container': container}
    return invoke_rest_endpoint(config, '/networks/{0}/disconnect'.format(net_id), 'POST', data=body)


def remove_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    if not net_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'DELETE')


def prune_networks(config, params, *args, **kwargs):
    filters = params.get('filters')
    return invoke_rest_endpoint(config, '/networks/prune', 'POST', query_params={'filters': filters})
