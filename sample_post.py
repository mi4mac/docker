from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def sample_post(config, params, *args, **kwargs):
    endpoint = params.get('url')
    data = params.get('data')
    if not endpoint or not data:
        raise ConnectorError('Missing required input')

    request_body = {'data': data}

    api_response = invoke_rest_endpoint(config, endpoint, 'POST', request_body)
    api_response.update({'my_custom_response_key': 'my_custom_value'})
    return api_response
