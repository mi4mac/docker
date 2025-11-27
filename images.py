from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, invoke_binary_endpoint, validate_required_params, validate_image_name, validate_boolean_param, validate_json_param, validate_positive_integer
import base64
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_images(config, params, *args, **kwargs):
    """List Docker images"""
    all_flag = validate_boolean_param(params.get('all', False), 'all', 'list_images', False)
    digests = validate_boolean_param(params.get('digests', False), 'digests', 'list_images', False)
    filters = validate_json_param(params.get('filters'), 'filters', 'list_images')
    query_params = {}
    if all_flag:
        query_params['all'] = int(bool(all_flag))
    if digests:
        query_params['digests'] = int(bool(digests))
    if filters:
        query_params['filters'] = filters
    return invoke_rest_endpoint(config, '/images/json', 'GET', query_params=query_params if query_params else None)


def pull_image(config, params, *args, **kwargs):
    validate_required_params(params, ['fromImage'], 'pull_image')
    from_image = params.get('fromImage')
    validate_image_name(from_image, 'pull_image')
    # Docker pulls via POST /images/create?fromImage=xxx
    return invoke_rest_endpoint(config, '/images/create', 'POST', query_params={'fromImage': from_image},
                                headers={'accept': 'application/json'}, use_registry_auth=True)


def inspect_image(config, params, *args, **kwargs):
    # Accept both 'id' and 'name' for compatibility with info.json and FortiSOAR UI
    # Docker Engine API allows image name or ID; we normalize to image_id here.
    if 'id' in params:
        image_id = params.get('id')
    else:
        # Backward-compatible fallback if info.json uses 'name'
        image_id = params.get('name')
    validate_required_params({'id': image_id}, ['id'], 'inspect_image')
    validate_image_name(image_id, 'inspect_image')
    return invoke_rest_endpoint(config, '/images/{0}/json'.format(image_id), 'GET')


def remove_image(config, params, *args, **kwargs):
    # Accept both 'id' and 'name' to align with info.json and Docker semantics
    if 'id' in params:
        image_id = params.get('id')
    else:
        image_id = params.get('name')
    validate_required_params({'id': image_id}, ['id'], 'remove_image')
    validate_image_name(image_id, 'remove_image')
    force = validate_boolean_param(params.get('force', False), 'force', 'remove_image', False)
    noprune = validate_boolean_param(params.get('noprune', False), 'noprune', 'remove_image', False)
    query_params = {'force': int(bool(force)), 'noprune': int(bool(noprune))}
    return invoke_rest_endpoint(config, '/images/{0}'.format(image_id), 'DELETE', query_params=query_params)


def tag_image(config, params, *args, **kwargs):
    # Accept both 'id' and 'name' to align with info.json and Docker semantics
    if 'id' in params:
        image_id = params.get('id')
    else:
        image_id = params.get('name')
    validate_required_params({'id': image_id, 'repo': params.get('repo')}, ['id', 'repo'], 'tag_image')
    validate_image_name(image_id, 'tag_image')
    repo = params.get('repo')
    tag = params.get('tag', 'latest')
    return invoke_rest_endpoint(config, '/images/{0}/tag'.format(image_id), 'POST', 
                                query_params={'repo': repo, 'tag': tag})


def prune_images(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_images')
    query_params = {'filters': filters} if filters else None
    return invoke_rest_endpoint(config, '/images/prune', 'POST', query_params=query_params)


def build_image(config, params, *args, **kwargs):
    """
    Build image from Dockerfile.
    
    NOTE: This is a simplified implementation.
    Full implementation requires tar stream upload of build context.
    
    For complete functionality, use Docker CLI or docker-py library.
    """
    remote = params.get('remote')  # Build context URL
    dockerfile = params.get('dockerfile', 'Dockerfile')
    tag = params.get('t') or params.get('tag')
    
    # Build parameters
    nocache = validate_boolean_param(params.get('nocache', False), 'nocache', 'build_image', False)
    pull = validate_boolean_param(params.get('pull', False), 'pull', 'build_image', False)
    rm = validate_boolean_param(params.get('rm', True), 'rm', 'build_image', True)
    forcerm = validate_boolean_param(params.get('forcerm', False), 'forcerm', 'build_image', False)
    q = validate_boolean_param(params.get('q', False), 'q', 'build_image', False)
    
    query_params = {}
    if remote:
        query_params['remote'] = remote
    if dockerfile:
        query_params['dockerfile'] = dockerfile
    if tag:
        query_params['t'] = tag
    if nocache:
        query_params['nocache'] = int(bool(nocache))
    if pull:
        query_params['pull'] = int(bool(pull))
    if rm:
        query_params['rm'] = int(bool(rm))
    if forcerm:
        query_params['forcerm'] = int(bool(forcerm))
    if q:
        query_params['q'] = int(bool(q))
    
    # Additional build parameters (can be added as JSON in body)
    buildargs = validate_json_param(params.get('buildargs'), 'buildargs', 'build_image')
    labels = validate_json_param(params.get('labels'), 'labels', 'build_image')
    networkmode = params.get('networkmode')
    platform = params.get('platform')
    
    # Note: Real implementation would require tar stream upload
    # This simplified version only works with remote URLs
    return invoke_rest_endpoint(config, '/build', 'POST', 
                                query_params=query_params if query_params else None,
                                data={'buildargs': buildargs, 'labels': labels, 'networkmode': networkmode, 'platform': platform} if (buildargs or labels or networkmode or platform) else None)


def search_images(config, params, *args, **kwargs):
    validate_required_params(params, ['term'], 'search_images')
    term = params.get('term')
    limit = validate_positive_integer(params.get('limit'), 'limit', 'search_images')
    query_params = {'term': term}
    if limit:
        query_params['limit'] = limit
    return invoke_rest_endpoint(config, '/images/search', 'GET', query_params=query_params)


def image_history(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'image_history')
    image_id = params.get('id')
    return invoke_rest_endpoint(config, '/images/{0}/history'.format(image_id), 'GET')


def push_image(config, params, *args, **kwargs):
    """Push an image to a registry"""
    validate_required_params(params, ['name'], 'push_image')
    image_name = params.get('name')
    validate_image_name(image_name, 'push_image')
    
    # Docker push via POST /images/{name}/push
    return invoke_rest_endpoint(config, '/images/{0}/push'.format(image_name), 'POST',
                                headers={'accept': 'application/json'}, use_registry_auth=True)


def load_image(config, params, *args, **kwargs):
    """Load an image from a tar archive.
    
    Expects a base64-encoded tar archive in the 'image_archive' parameter.
    This aligns with Docker's POST /images/load API, which expects a tar
    stream body and returns JSON.
    """
    validate_required_params(params, ['image_archive'], 'load_image')
    archive_b64 = params.get('image_archive')
    if not archive_b64:
        raise ConnectorError('image_archive (base64-encoded tar) is required for load_image')
    
    try:
        archive_bytes = base64.b64decode(archive_b64)
    except Exception as e:
        raise ConnectorError('Invalid base64 archive for load_image: {0}'.format(str(e)))
    
    return invoke_binary_endpoint(
        config,
        '/images/load',
        'POST',
        body=archive_bytes,
        headers={'Content-Type': 'application/x-tar', 'accept': 'application/json'},
        expect_json_response=True
    )


def save_image(config, params, *args, **kwargs):
    """Save an image to a tar archive"""
    validate_required_params(params, ['name'], 'save_image')
    image_name = params.get('name')
    validate_image_name(image_name, 'save_image')
    
    # Return base64-encoded tar archive for the image
    return invoke_binary_endpoint(
        config,
        '/images/{0}/get'.format(image_name),
        'GET',
        headers={'accept': 'application/octet-stream'}
    )
