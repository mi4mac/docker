from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_json_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def get_version(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/version', 'GET')


def get_info(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/info', 'GET')


def system_df(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/system/df', 'GET')


def system_events(config, params, *args, **kwargs):
    # For simplicity, we expose a snapshot using GET with filters
    filters = validate_json_param(params.get('filters'), 'filters', 'system_events')
    since = params.get('since')
    until = params.get('until')
    query_params = {}
    if filters:
        query_params['filters'] = filters
    if since:
        query_params['since'] = since
    if until:
        query_params['until'] = until
    return invoke_rest_endpoint(config, '/events', 'GET', query_params=query_params if query_params else None)


def system_prune(config, params, *args, **kwargs):
    """Remove unused data (containers, networks, images, and build cache)"""
    filters = validate_json_param(params.get('filters'), 'filters', 'system_prune')
    return invoke_rest_endpoint(config, '/system/prune', 'POST', query_params={'filters': filters})


def ping(config, params, *args, **kwargs):
    """Ping the Docker daemon"""
    return invoke_rest_endpoint(config, '/_ping', 'GET')


def auth(config, params, *args, **kwargs):
    """Authenticate with a registry"""
    validate_required_params(params, ['username', 'password'], 'auth')
    username = params.get('username')
    password = params.get('password')
    serveraddress = params.get('serveraddress', 'https://index.docker.io/v1/')
    
    auth_data = {
        'username': username,
        'password': password,
        'serveraddress': serveraddress
    }
    
    return invoke_rest_endpoint(config, '/auth', 'POST', data=auth_data)


