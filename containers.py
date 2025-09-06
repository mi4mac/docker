from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_container_id, validate_positive_integer, validate_boolean_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_containers(config, params, *args, **kwargs):
    all_flag = params.get('all', False)
    return invoke_rest_endpoint(config, '/containers/json', 'GET', query_params={'all': int(bool(all_flag))})


def inspect_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'inspect_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'inspect_container')
    return invoke_rest_endpoint(config, '/containers/{0}/json'.format(container_id), 'GET')


def start_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'start_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'start_container')
    return invoke_rest_endpoint(config, '/containers/{0}/start'.format(container_id), 'POST')


def stop_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'stop_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'stop_container')
    timeout = validate_positive_integer(params.get('t'), 'timeout', 'stop_container')
    return invoke_rest_endpoint(config, '/containers/{0}/stop'.format(container_id), 'POST', query_params={'t': timeout})


def remove_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    force = params.get('force', False)
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}'.format(container_id), 'DELETE', query_params={'force': int(bool(force))})


def create_container(config, params, *args, **kwargs):
    image = params.get('image')
    name = params.get('name')
    host_config = params.get('HostConfig')
    if not image:
        raise ConnectorError('Missing required input: image')
    body = {'Image': image}
    if host_config:
        body['HostConfig'] = host_config
    query = {'name': name} if name else None
    return invoke_rest_endpoint(config, '/containers/create', 'POST', data=body, query_params=query)


def restart_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    t = params.get('t')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/restart'.format(container_id), 'POST', query_params={'t': t})


def kill_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    signal = params.get('signal')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/kill'.format(container_id), 'POST', query_params={'signal': signal})


def container_logs(config, params, *args, **kwargs):
    container_id = params.get('id')
    stdout = int(bool(params.get('stdout', True)))
    stderr = int(bool(params.get('stderr', False)))
    tail = params.get('tail')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/logs'.format(container_id), 'GET',
                                headers={'accept': 'text/plain'},
                                query_params={'stdout': stdout, 'stderr': stderr, 'tail': tail})


def rename_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    name = params.get('name')
    if not container_id or not name:
        raise ConnectorError('Missing required inputs: id, name')
    return invoke_rest_endpoint(config, '/containers/{0}/rename'.format(container_id), 'POST', query_params={'name': name})


def prune_containers(config, params, *args, **kwargs):
    filters = params.get('filters')
    return invoke_rest_endpoint(config, '/containers/prune', 'POST', query_params={'filters': filters})


def exec_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    cmd = params.get('Cmd')
    if not container_id or not cmd:
        raise ConnectorError('Missing required inputs: id, Cmd')
    body = {
        'AttachStdout': True,
        'AttachStderr': True,
        'Cmd': cmd if isinstance(cmd, list) else [cmd]
    }
    # Create exec instance
    exec_create = invoke_rest_endpoint(config, '/containers/{0}/exec'.format(container_id), 'POST', data=body)
    exec_id = exec_create.get('Id')
    if not exec_id:
        raise ConnectorError('Failed to create exec: missing Id')
    # Start exec
    started = invoke_rest_endpoint(config, '/exec/{0}/start'.format(exec_id), 'POST', data={'Detach': False, 'Tty': False})
    return {'exec_id': exec_id, 'output': started}


def pause_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/pause'.format(container_id), 'POST')


def unpause_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/unpause'.format(container_id), 'POST')


def container_stats(config, params, *args, **kwargs):
    container_id = params.get('id')
    stream = params.get('stream', False)
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/stats'.format(container_id), 'GET',
                                query_params={'stream': int(bool(stream))})


def container_export(config, params, *args, **kwargs):
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/export'.format(container_id), 'GET',
                                headers={'accept': 'application/octet-stream'})


def container_commit(config, params, *args, **kwargs):
    container_id = params.get('id')
    repo = params.get('repo')
    tag = params.get('tag', 'latest')
    comment = params.get('comment')
    author = params.get('author')
    changes = params.get('changes')
    pause = params.get('pause', True)
    
    if not container_id:
        raise ConnectorError('Missing required input: id')
    
    query_params = {
        'container': container_id,
        'repo': repo,
        'tag': tag,
        'comment': comment,
        'author': author,
        'changes': changes,
        'pause': int(bool(pause))
    }
    
    return invoke_rest_endpoint(config, '/commit', 'POST', query_params=query_params)


def update_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'update_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'update_container')
    
    # Get update parameters
    update_data = {}
    if 'Memory' in params:
        update_data['Memory'] = params['Memory']
    if 'CpuShares' in params:
        update_data['CpuShares'] = params['CpuShares']
    if 'CpuQuota' in params:
        update_data['CpuQuota'] = params['CpuQuota']
    if 'CpuPeriod' in params:
        update_data['CpuPeriod'] = params['CpuPeriod']
    if 'RestartPolicy' in params:
        update_data['RestartPolicy'] = params['RestartPolicy']
    
    return invoke_rest_endpoint(config, '/containers/{0}/update'.format(container_id), 'POST', data=update_data)


def wait_container(config, params, *args, **kwargs):
    """Wait for a container to stop and return its exit code"""
    validate_required_params(params, ['id'], 'wait_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'wait_container')
    
    return invoke_rest_endpoint(config, '/containers/{0}/wait'.format(container_id), 'POST')


def attach_container(config, params, *args, **kwargs):
    """Attach to a container's stdout/stderr streams"""
    validate_required_params(params, ['id'], 'attach_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'attach_container')
    
    # Get attachment parameters
    stdout = int(bool(params.get('stdout', True)))
    stderr = int(bool(params.get('stderr', True)))
    stream = int(bool(params.get('stream', True)))
    logs = int(bool(params.get('logs', False)))
    
    query_params = {
        'stdout': stdout,
        'stderr': stderr,
        'stream': stream,
        'logs': logs
    }
    
    return invoke_rest_endpoint(config, '/containers/{0}/attach'.format(container_id), 'POST',
                                query_params=query_params,
                                headers={'accept': 'application/vnd.docker.raw-stream'})


def resize_container(config, params, *args, **kwargs):
    """Resize a container's TTY"""
    validate_required_params(params, ['id', 'h', 'w'], 'resize_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'resize_container')
    
    height = params.get('h')
    width = params.get('w')
    
    query_params = {'h': height, 'w': width}
    return invoke_rest_endpoint(config, '/containers/{0}/resize'.format(container_id), 'POST',
                                query_params=query_params)


def copy_from_container(config, params, *args, **kwargs):
    """Copy files/folders from a container"""
    validate_required_params(params, ['id', 'path'], 'copy_from_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'copy_from_container')
    
    path = params.get('path')
    
    return invoke_rest_endpoint(config, '/containers/{0}/copy'.format(container_id), 'POST',
                                data={'Resource': path},
                                headers={'accept': 'application/octet-stream'})


def copy_to_container(config, params, *args, **kwargs):
    """Copy files/folders to a container"""
    validate_required_params(params, ['id', 'path'], 'copy_to_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'copy_to_container')
    
    path = params.get('path')
    
    # Note: This is a simplified implementation
    # Real implementation would require tar stream upload
    return invoke_rest_endpoint(config, '/containers/{0}/archive'.format(container_id), 'PUT',
                                data={'path': path},
                                headers={'accept': 'application/json'})


