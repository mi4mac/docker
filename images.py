from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_images(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/images/json', 'GET')


def pull_image(config, params, *args, **kwargs):
    from_image = params.get('fromImage')
    if not from_image:
        raise ConnectorError('Missing required input: fromImage')
    # Docker pulls via POST /images/create?fromImage=xxx
    return invoke_rest_endpoint(config, '/images/create', 'POST', query_params={'fromImage': from_image},
                                headers={'accept': 'application/json'})


def inspect_image(config, params, *args, **kwargs):
    name = params.get('name')
    if not name:
        raise ConnectorError('Missing required input: name')
    return invoke_rest_endpoint(config, '/images/{0}/json'.format(name), 'GET')


def remove_image(config, params, *args, **kwargs):
    name = params.get('name')
    force = params.get('force', False)
    noprune = params.get('noprune', False)
    if not name:
        raise ConnectorError('Missing required input: name')
    return invoke_rest_endpoint(config, '/images/{0}'.format(name), 'DELETE',
                                query_params={'force': int(bool(force)), 'noprune': int(bool(noprune))})


def tag_image(config, params, *args, **kwargs):
    name = params.get('name')
    repo = params.get('repo')
    tag = params.get('tag')
    if not name or not repo:
        raise ConnectorError('Missing required inputs: name, repo')
    return invoke_rest_endpoint(config, '/images/{0}/tag'.format(name), 'POST', query_params={'repo': repo, 'tag': tag})


def prune_images(config, params, *args, **kwargs):
    filters = params.get('filters')
    return invoke_rest_endpoint(config, '/images/prune', 'POST', query_params={'filters': filters})


