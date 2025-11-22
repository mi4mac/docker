import requests
import json
import base64
import time
import os
import re
import threading
from urllib.parse import urlencode
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)

# Rate limiting storage (thread-safe)
_rate_limit_lock = threading.Lock()
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
    try:
        server_address = config.get('server_address')
        port = config.get('port', '2376')
        protocol = config.get('protocol', 'https')
        api_version = config.get('api_version', 'v1.44')
        
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
            # Process query params - JSON parameters must be serialized as JSON strings
            processed_params = {}
            for k, v in query_params.items():
                if v is not None:
                    # If value is already a string (JSON-encoded), use it directly
                    if isinstance(v, str):
                        processed_params[k] = v
                    # If value is dict or list, serialize as JSON string
                    elif isinstance(v, (dict, list)):
                        processed_params[k] = json.dumps(v)
                    else:
                        processed_params[k] = v
            
            query = urlencode(processed_params, doseq=True)
            if query:
                url = url + '?' + query
        return url
    except Exception as e:
        logger.error('Error building URL: {0}'.format(str(e)))
        raise ConnectorError('Error building URL: {0}'.format(str(e)))


def _apply_rate_limit(config):
    """Apply rate limiting based on configuration (thread-safe)"""
    rate_limit = config.get('rate_limit', 60)  # requests per minute
    if rate_limit <= 0:
        return
    
    with _rate_limit_lock:
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
        try:
            if os.path.exists(cert_path) and os.path.exists(key_path):
                cert = (cert_path, key_path)
            else:
                logger.warning('Certificate or key file not found: {0}, {1}'.format(cert_path, key_path))
        except Exception as e:
            logger.warning('Error checking certificate files: {0}'.format(str(e)))
    
    # CA certificate
    verify = verify_ssl
    if ca_cert_path:
        try:
            if os.path.exists(ca_cert_path):
                verify = ca_cert_path
            else:
                logger.warning('CA certificate file not found: {0}'.format(ca_cert_path))
        except Exception as e:
            logger.warning('Error checking CA certificate file: {0}'.format(str(e)))
    elif not verify_ssl:
        verify = False
    
    return verify, cert


def invoke_rest_endpoint(config, endpoint, method='GET', data=None, headers=None, query_params=None, timeout=None, use_registry_auth=False):
    try:
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
    except Exception as e:
        logger.error('Error in invoke_rest_endpoint setup: {0}'.format(str(e)))
        raise ConnectorError('Error setting up request: {0}'.format(str(e)))
    
    # Retry logic
    retry_attempts = config.get('retry_attempts', 3)
    retry_delay = config.get('retry_delay', 1)
    response = None
    
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
            if attempt == retry_attempts - 1:
                raise ConnectorError('Error invoking {0}: {1}'.format(endpoint, str(e)))
            continue

    if response is None:
        raise ConnectorError('No response received from Docker API after {0} attempts'.format(retry_attempts))

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


def validate_required_params(params, required_fields, operation_name):
    """Validate that all required parameters are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if field not in params or params[field] is None or params[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ConnectorError('Missing required parameters for {0}: {1}'.format(
            operation_name, ', '.join(missing_fields)))


def validate_container_id(container_id, operation_name):
    """Validate container ID format (supports short/long hex IDs, names, and partial IDs)"""
    if not container_id:
        raise ConnectorError('Container ID is required for {0}'.format(operation_name))
    
    # Docker accepts:
    # - Short form: 12 hex characters (e.g., "abc123def456")
    # - Long form: 64 hex characters
    # - Partial ID: minimum 3 hex characters
    # - Container names: alphanumeric with hyphens, underscores, dots, slashes
    # - Docker Compose names: can contain underscores, dots, slashes
    
    # Check if it's a hex ID (short, long, or partial)
    hex_pattern = r'^[a-f0-9]{3,64}$'
    # Check if it's a container name (alphanumeric with common separators)
    name_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
    
    if re.match(hex_pattern, container_id) or re.match(name_pattern, container_id):
        return  # Valid format
    
    raise ConnectorError('Invalid container ID format for {0}: {1}. Must be hex ID (3-64 chars) or container name'.format(operation_name, container_id))


def validate_image_name(image_name, operation_name):
    """Validate image name format"""
    if not image_name:
        raise ConnectorError('Image name is required for {0}'.format(operation_name))
    
    # Basic validation for image names (repository:tag format)
    if not re.match(r'^[a-zA-Z0-9._/-]+(:[a-zA-Z0-9._-]+)?$', image_name):
        raise ConnectorError('Invalid image name format for {0}: {1}'.format(operation_name, image_name))


def validate_network_name(network_name, operation_name):
    """Validate network name format"""
    if not network_name:
        raise ConnectorError('Network name is required for {0}'.format(operation_name))
    
    # Network names should be alphanumeric with hyphens and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', network_name):
        raise ConnectorError('Invalid network name format for {0}: {1}'.format(operation_name, network_name))


def validate_volume_name(volume_name, operation_name):
    """Validate volume name format"""
    if not volume_name:
        raise ConnectorError('Volume name is required for {0}'.format(operation_name))
    
    # Volume names should be alphanumeric with hyphens and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', volume_name):
        raise ConnectorError('Invalid volume name format for {0}: {1}'.format(operation_name, volume_name))


def validate_json_param(param_value, param_name, operation_name):
    """Validate JSON parameter format"""
    if param_value is None:
        return None
    
    if isinstance(param_value, str):
        try:
            return json.loads(param_value)
        except json.JSONDecodeError as e:
            raise ConnectorError('Invalid JSON format for {0} in {1}: {2}'.format(
                param_name, operation_name, str(e)))
    
    return param_value


def validate_positive_integer(value, param_name, operation_name):
    """Validate that a parameter is a positive integer"""
    if value is None:
        return None
    
    try:
        int_value = int(value)
        if int_value < 0:
            raise ConnectorError('{0} must be a positive integer for {1}'.format(
                param_name, operation_name))
        return int_value
    except (ValueError, TypeError):
        raise ConnectorError('{0} must be a valid integer for {1}'.format(
            param_name, operation_name))


def validate_boolean_param(value, param_name, operation_name, default=False):
    """Validate and convert boolean parameter"""
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    
    return bool(value)
