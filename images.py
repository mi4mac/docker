from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_image_name, validate_boolean_param, validate_json_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_images(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/images/json', 'GET')


def pull_image(config, params, *args, **kwargs):
    validate_required_params(params, ['fromImage'], 'pull_image')
    from_image = params.get('fromImage')
    validate_image_name(from_image, 'pull_image')
    # Docker pulls via POST /images/create?fromImage=xxx
    return invoke_rest_endpoint(config, '/images/create', 'POST', query_params={'fromImage': from_image},
                                headers={'accept': 'application/json'}, use_registry_auth=True)


def inspect_image(config, params, *args, **kwargs):
    image_id = params.get('id')
    if not image_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/images/{0}/json'.format(image_id), 'GET')


def remove_image(config, params, *args, **kwargs):
    image_id = params.get('id')
    force = params.get('force', False)
    if not image_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/images/{0}'.format(image_id), 'DELETE', query_params={'force': force})


def tag_image(config, params, *args, **kwargs):
    image_id = params.get('id')
    repo = params.get('repo')
    tag = params.get('tag', 'latest')
    if not image_id or not repo:
        raise ConnectorError('Missing required inputs: id, repo')
    return invoke_rest_endpoint(config, '/images/{0}/tag'.format(image_id), 'POST', 
                                query_params={'repo': repo, 'tag': tag})


def prune_images(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_images')
    query_params = {'filters': filters} if filters else {}
    return invoke_rest_endpoint(config, '/images/prune', 'POST', query_params=query_params)


def build_image(config, params, *args, **kwargs):
    # Docker build via POST /build
    # This is a complex operation that typically requires tar stream
    # For now, we'll implement a basic version
    dockerfile = params.get('dockerfile', 'Dockerfile')
    context = params.get('context', '.')
    tag = params.get('tag')
    
    # Note: This is a simplified implementation
    # Real Docker builds require tar stream upload
    return invoke_rest_endpoint(config, '/build', 'POST', 
                                query_params={'dockerfile': dockerfile, 't': tag})


def search_images(config, params, *args, **kwargs):
    term = params.get('term')
    if not term:
        raise ConnectorError('Missing required input: term')
    return invoke_rest_endpoint(config, '/images/search', 'GET', query_params={'term': term})


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
    """Load an image from a tar archive"""
    # Note: This is a simplified implementation
    # Real implementation would require tar stream upload
    return invoke_rest_endpoint(config, '/images/load', 'POST',
                                headers={'accept': 'application/json'})


def save_image(config, params, *args, **kwargs):
    """Save an image to a tar archive"""
    validate_required_params(params, ['name'], 'save_image')
    image_name = params.get('name')
    validate_image_name(image_name, 'save_image')
    
    return invoke_rest_endpoint(config, '/images/{0}/get'.format(image_name), 'GET',
                                headers={'accept': 'application/octet-stream'})
