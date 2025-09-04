from .utils import invoke_rest_endpoint
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def health_check(config=None, *args, **kwargs):
    # Docker Engine API ping endpoint
    try:
        response = invoke_rest_endpoint(config, '/_ping', 'GET', headers={'accept': 'text/plain'})
    except ConnectorError:
        raise
    # Success if we got here without exception
    return 'Connector is Available'
