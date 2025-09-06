from .utils import invoke_rest_endpoint
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def health_check(config=None, *args, **kwargs):
    """Enhanced health check that actually tests Docker API connectivity"""
    try:
        if not config:
            return 'Connector is Available - No configuration provided'
        
        # Check if required configuration is present
        server_address = config.get('server_address')
        if not server_address:
            return 'Connector is Available - Server address not configured'
        
        # Test actual connectivity using the ping endpoint
        try:
            from .utils import invoke_rest_endpoint
            result = invoke_rest_endpoint(config, '/_ping', 'GET', timeout=10)
            if result and 'OK' in str(result):
                return 'Connector is Available - Docker API is reachable'
            else:
                return 'Connector is Available - Docker API responded but with unexpected result'
        except Exception as api_error:
            logger.warning('Docker API ping failed: {0}'.format(str(api_error)))
            return 'Connector is Available - Docker API not reachable: {0}'.format(str(api_error))
        
    except Exception as e:
        logger.error('Health check failed: {0}'.format(str(e)))
        return 'Connector is Available - Health check error: {0}'.format(str(e))
