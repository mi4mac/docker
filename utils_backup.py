import requests
import json
from urllib.parse import urlencode
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def _build_auth(config):
    username = config.get('username')
    password = config.get('password')
    token = config.get('access_token')
    headers = {}
    auth = None
    if token:
        headers['Authorization'] = 'Bearer {0}'.format(token)
    elif username and password:
        auth = (username, password)
    return auth, headers


def _build_url(config, endpoint, query_params=None):
    server_address = config.get('server_address')
    port = config.get('port', '2376')
    protocol = config.get('protocol', 'https')
    
    if not server_address:
        raise ConnectorError('Missing required parameter: server_address')
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    url = '{protocol}://{server_address}:{port}{endpoint}'.format(protocol=protocol.lower(),
                                                                  server_address=server_address,
                                                                  port=port,
                                                                  endpoint=endpoint)
    if query_params:
        query = urlencode({k: v for k, v in query_params.items() if v is not None}, doseq=True)
        if query:
            url = url + '?' + query
    return url


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None, query_params=None, timeout=60):
    verify_ssl = config.get('verify_ssl', True)
    default_headers = {'accept': 'application/json'}
    auth, auth_headers = _build_auth(config)
    if headers is None:
        headers = {}
    # Merge headers with precedence to explicit headers
    merged_headers = {**default_headers, **auth_headers, **headers}

    url = _build_url(config, endpoint, query_params)
    try:
        payload = None
        if data is not None:
            payload = json.dumps(data)
            if 'content-type' not in {k.lower() for k in merged_headers.keys()}:
                merged_headers['Content-Type'] = 'application/json'
        response = requests.request(method=method, url=url, auth=auth, verify=verify_ssl,
                                    data=payload, headers=merged_headers, timeout=timeout)
    except Exception as e:
        logger.exception('Error invoking endpoint: {0}'.format(endpoint))
        raise ConnectorError('Error invoking {0}: {1}'.format(endpoint, str(e)))

    if response.ok:
        # Some Docker endpoints return plain text, others json
        try:
            return response.json()
        except ValueError:
            return {'result': response.text}
    else:
        content = response.text
        logger.error(content)
        raise ConnectorError('Status: {0}, Response: {1}'.format(response.status_code, content))
