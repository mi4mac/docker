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
                                headers={'accept': 'application/json'}, use_registry_auth=True)


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


def build_image(config, params, *args, **kwargs):
    """Build an image from a Dockerfile"""
    dockerfile = params.get('dockerfile', 'Dockerfile')
    t = params.get('t')  # tag
    remote = params.get('remote')  # URL or path to build context
    q = params.get('q', False)  # quiet
    nocache = params.get('nocache', False)
    pull = params.get('pull', False)
    rm = params.get('rm', True)
    forcerm = params.get('forcerm', False)
    memory = params.get('memory')
    memswap = params.get('memswap')
    cpushares = params.get('cpushares')
    cpusetcpus = params.get('cpusetcpus')
    cpuperiod = params.get('cpuperiod')
    cpuquota = params.get('cpuquota')
    buildargs = params.get('buildargs')
    shmsize = params.get('shmsize')
    squash = params.get('squash', False)
    labels = params.get('labels')
    networkmode = params.get('networkmode')
    platform = params.get('platform')
    target = params.get('target')
    outputs = params.get('outputs')
    
    if not remote:
        raise ConnectorError('Missing required input: remote (build context)')
    
    query_params = {
        'dockerfile': dockerfile,
        't': t,
        'remote': remote,
        'q': int(bool(q)),
        'nocache': int(bool(nocache)),
        'pull': int(bool(pull)),
        'rm': int(bool(rm)),
        'forcerm': int(bool(forcerm)),
        'memory': memory,
        'memswap': memswap,
        'cpushares': cpushares,
        'cpusetcpus': cpusetcpus,
        'cpuperiod': cpuperiod,
        'cpuquota': cpuquota,
        'buildargs': buildargs,
        'shmsize': shmsize,
        'squash': int(bool(squash)),
        'labels': labels,
        'networkmode': networkmode,
        'platform': platform,
        'target': target,
        'outputs': outputs
    }
    
    # Remove None values
    query_params = {k: v for k, v in query_params.items() if v is not None}
    
    return invoke_rest_endpoint(config, '/build', 'POST', query_params=query_params,
                                headers={'Content-Type': 'application/x-tar'}, use_registry_auth=True)


def search_images(config, params, *args, **kwargs):
    """Search for images on Docker Hub"""
    term = params.get('term')
    limit = params.get('limit', 25)
    filters = params.get('filters')
    
    if not term:
        raise ConnectorError('Missing required input: term')
    
    query_params = {
        'term': term,
        'limit': limit,
        'filters': filters
    }
    
    return invoke_rest_endpoint(config, '/images/search', 'GET', query_params=query_params)


def image_history(config, params, *args, **kwargs):
    """Get the history of an image"""
    name = params.get('name')
    if not name:
        raise ConnectorError('Missing required input: name')
    return invoke_rest_endpoint(config, '/images/{0}/history'.format(name), 'GET')


