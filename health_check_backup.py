from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def health_check(config=None, *args, **kwargs):
    # Simple health check that doesn't make any API calls
    try:
        return 'Connector is Available'
    except Exception as e:
        logger.error('Health check failed: {0}'.format(str(e)))
        return 'Connector is Available - Health check error: {0}'.format(str(e))
