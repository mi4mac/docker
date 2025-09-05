import requests
import json
import base64
import time
import os
from urllib.parse import urlencode
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)

# Rate limiting storage
_request_times = []


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


def _build_registry_auth(config):
    """Build Docker registry authentication header"""
    registry_username = config.get('registry_username')
    registry_password = config.get('registry_password')
    registry_server = config.get('registry_server', 'https://index.docker.io/v1/')
    
    if registry_username and registry_password:
        auth_config = {
            'username': registry_username,
            'password': registry_password,
            'serveraddress': registry_server
        }
        auth_string = base64.b64encode(json.dumps(auth_config).encode()).decode()
        return {'X-Registry-Auth': auth_string}
    return {}


def _build_url(config, endpoint, query_params=None):
    server_address = config.get('server_address')
    port = config.get('port', '2376')
    protocol = config.get('protocol', 'https')
    api_version = config.get('api_version', 'v1.41')
    
    if not server_address:
        raise ConnectorError('Missing required parameter: server_address')
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    # Add API version to endpoint
    if not endpoint.startswith('/' + api_version):
        endpoint = '/' + api_version + endpoint
    
    url = '{protocol}://{server_address}:{port}{endpoint}'.format(protocol=protocol.lower(),
                                                                  server_address=server_address,
                                                                  port=port,
                                                                  endpoint=endpoint)
    if query_params:
        query = urlencode({k: v for k, v in query_params.items() if v is not None}, doseq=True)
        if query:
            url = url + '?' + query
    return url


def _apply_rate_limit(config):
    """Apply rate limiting based on configuration"""
    rate_limit = config.get('rate_limit', 60)  # requests per minute
    if rate_limit <= 0:
        return
    
    current_time = time.time()
    # Remove requests older than 1 minute
    global _request_times
    _request_times = [t for t in _request_times if current_time - t < 60]
    
    # If we're at the rate limit, wait
    if len(_request_times) >= rate_limit:
        sleep_time = 60 - (current_time - _request_times[0])
        if sleep_time > 0:
            logger.info('Rate limit reached, sleeping for {0:.2f} seconds'.format(sleep_time))
            time.sleep(sleep_time)
    
    _request_times.append(current_time)


def _build_ssl_context(config):
    """Build SSL context with certificate options"""
    verify_ssl = config.get('verify_ssl', True)
    cert_path = config.get('cert_path')
    key_path = config.get('key_path')
    ca_cert_path = config.get('ca_cert_path')
    
    # Client certificate tuple
    cert = None
    if cert_path and key_path:
        if os.path.exists(cert_path) and os.path.exists(key_path):
            cert = (cert_path, key_path)
        else:
            logger.warning('Certificate or key file not found: {0}, {1}'.format(cert_path, key_path))
    
    # CA certificate
    verify = verify_ssl
    if ca_cert_path and os.path.exists(ca_cert_path):
        verify = ca_cert_path
    elif not verify_ssl:
        verify = False
    
    return verify, cert


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None, query_params=None, timeout=None, use_registry_auth=False):
    # Apply rate limiting
    _apply_rate_limit(config)
    
    timeout = timeout or config.get('timeout', 60)
    default_headers = {'accept': 'application/json'}
    auth, auth_headers = _build_auth(config)
    
    if headers is None:
        headers = {}
    
    # Add registry authentication if needed
    if use_registry_auth:
        registry_headers = _build_registry_auth(config)
        auth_headers.update(registry_headers)
    
    # Merge headers with precedence to explicit headers
    merged_headers = {**default_headers, **auth_headers, **headers}

    # Build SSL context
    verify, cert = _build_ssl_context(config)
    
    url = _build_url(config, endpoint, query_params)
    
    # Retry logic
    retry_attempts = config.get('retry_attempts', 3)
    retry_delay = config.get('retry_delay', 1)
    
    for attempt in range(retry_attempts):
        try:
            payload = None
            if data is not None:
                payload = json.dumps(data)
                if 'content-type' not in {k.lower() for k in merged_headers.keys()}:
                    merged_headers['Content-Type'] = 'application/json'
            
            response = requests.request(method=method, url=url, auth=auth, verify=verify, cert=cert,
                                        data=payload, headers=merged_headers, timeout=timeout)
            
            # If successful, break out of retry loop
            if response.ok:
                break
                
            # If it's a client error (4xx), don't retry
            if 400 <= response.status_code < 500:
                break
                
            # For server errors (5xx), retry if we have attempts left
            if attempt < retry_attempts - 1:
                logger.warning('Server error {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    response.status_code, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue
                
        except requests.exceptions.Timeout:
            if attempt < retry_attempts - 1:
                logger.warning('Timeout connecting to {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    endpoint, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue
            else:
                logger.error('Timeout connecting to {0}'.format(endpoint))
                raise ConnectorError('Timeout connecting to Docker API: {0}'.format(endpoint))
        except requests.exceptions.ConnectionError:
            if attempt < retry_attempts - 1:
                logger.warning('Connection error to {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    endpoint, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue
            else:
                logger.error('Connection error to {0}'.format(endpoint))
                raise ConnectorError('Cannot connect to Docker API: {0}'.format(endpoint))
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
        logger.error('HTTP {0}: {1}'.format(response.status_code, content))
        
        # Specific error handling based on HTTP status codes
        if response.status_code == 400:
            raise ConnectorError('Bad Request: {0}'.format(content))
        elif response.status_code == 401:
            raise ConnectorError('Unauthorized: Check your authentication credentials')
        elif response.status_code == 403:
            raise ConnectorError('Forbidden: Insufficient permissions for this operation')
        elif response.status_code == 404:
            raise ConnectorError('Resource not found: {0}'.format(endpoint))
        elif response.status_code == 409:
            raise ConnectorError('Conflict: {0}'.format(content))
        elif response.status_code == 500:
            raise ConnectorError('Docker Engine internal error: {0}'.format(content))
        elif response.status_code == 503:
            raise ConnectorError('Docker Engine unavailable: {0}'.format(content))
        else:
            raise ConnectorError('HTTP {0}: {1}'.format(response.status_code, content))
