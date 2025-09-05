from connectors.core.connector import get_logger, ConnectorError
from utils import invoke_rest_endpoint
from constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def get_version(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/version', 'GET')


def get_info(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/info', 'GET')


def system_df(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/system/df', 'GET')


def system_events(config, params, *args, **kwargs):
    # For simplicity, we expose a snapshot using GET with filters
    filters = params.get('filters')
    since = params.get('since')
    until = params.get('until')
    return invoke_rest_endpoint(config, '/events', 'GET', query_params={'filters': filters, 'since': since, 'until': until})


