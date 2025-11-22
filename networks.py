from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_network_name, validate_json_param, validate_boolean_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_networks(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/networks', 'GET')


def inspect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    if not net_id:
        raise ConnectorError('Missing required input: id')

    return invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'GET')


def create_network(config, params, *args, **kwargs):
    validate_required_params(params, ['Name'], 'create_network')
    name = params.get('Name')
    validate_network_name(name, 'create_network')
    body = {
        'Name': name,
        'Driver': params.get('Driver'),
        'Options': validate_json_param(params.get('Options'), 'Options', 'create_network'),
        'IPAM': validate_json_param(params.get('IPAM'), 'IPAM', 'create_network')
    }
    # Remove None values
    body = {k: v for k, v in body.items() if v is not None}
    return invoke_rest_endpoint(config, '/networks/create', 'POST', data=body)


def connect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    container = params.get('Container')
    if not net_id or not container:
        raise ConnectorError('Missing required inputs: id, Container')
    body = {'Container': container}
    return invoke_rest_endpoint(config, '/networks/{0}/connect'.format(net_id), 'POST', data=body)


def disconnect_network(config, params, *args, **kwargs):
    validate_required_params(params, ['id', 'Container'], 'disconnect_network')
    net_id = params.get('id')
    validate_network_name(net_id, 'disconnect_network')
    container = params.get('Container')
    force = validate_boolean_param(params.get('Force', False), 'Force', 'disconnect_network', False)
    body = {'Container': container}
    if force:
        body['Force'] = force
    return invoke_rest_endpoint(config, '/networks/{0}/disconnect'.format(net_id), 'POST', data=body)


def remove_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    if not net_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'DELETE')


def prune_networks(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_networks')
    query_params = {'filters': filters} if filters else {}
    return invoke_rest_endpoint(config, '/networks/prune', 'POST', query_params=query_params)
