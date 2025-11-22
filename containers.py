from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, validate_required_params, validate_container_id, validate_image_name, validate_positive_integer, validate_boolean_param, validate_json_param
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_containers(config, params, *args, **kwargs):
    """List Docker containers"""
    all_flag = validate_boolean_param(params.get('all', False), 'all', 'list_containers', False)
    limit = validate_positive_integer(params.get('limit'), 'limit', 'list_containers')
    size = validate_boolean_param(params.get('size', False), 'size', 'list_containers', False)
    since = params.get('since')
    before = params.get('before')
    filters = validate_json_param(params.get('filters'), 'filters', 'list_containers')
    
    query_params = {'all': int(bool(all_flag))}
    if limit:
        query_params['limit'] = limit
    if size:
        query_params['size'] = int(bool(size))
    if since:
        query_params['since'] = since
    if before:
        query_params['before'] = before
    if filters:
        query_params['filters'] = filters
    
    return invoke_rest_endpoint(config, '/containers/json', 'GET', query_params=query_params)


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
    validate_required_params(params, ['id'], 'remove_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'remove_container')
    force = validate_boolean_param(params.get('force', False), 'force', 'remove_container', False)
    return invoke_rest_endpoint(config, '/containers/{0}'.format(container_id), 'DELETE', query_params={'force': int(bool(force))})


def create_container(config, params, *args, **kwargs):
    validate_required_params(params, ['image'], 'create_container')
    image = params.get('image')
    validate_image_name(image, 'create_container')
    name = params.get('name')
    host_config = validate_json_param(params.get('HostConfig'), 'HostConfig', 'create_container')
    body = {'Image': image}
    if host_config:
        body['HostConfig'] = host_config
    query = {'name': name} if name else None
    return invoke_rest_endpoint(config, '/containers/create', 'POST', data=body, query_params=query)


def restart_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'restart_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'restart_container')
    timeout = validate_positive_integer(params.get('t'), 'timeout', 'restart_container')
    return invoke_rest_endpoint(config, '/containers/{0}/restart'.format(container_id), 'POST', query_params={'t': timeout})


def kill_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'kill_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'kill_container')
    signal = params.get('signal')
    query_params = {'signal': signal} if signal else {}
    return invoke_rest_endpoint(config, '/containers/{0}/kill'.format(container_id), 'POST', query_params=query_params)


def container_logs(config, params, *args, **kwargs):
    """Fetch container logs"""
    validate_required_params(params, ['id'], 'container_logs')
    container_id = params.get('id')
    validate_container_id(container_id, 'container_logs')
    stdout = validate_boolean_param(params.get('stdout', True), 'stdout', 'container_logs', True)
    stderr = validate_boolean_param(params.get('stderr', False), 'stderr', 'container_logs', False)
    tail = params.get('tail')
    since = params.get('since')
    until = params.get('until')
    timestamps = validate_boolean_param(params.get('timestamps', False), 'timestamps', 'container_logs', False)
    follow = validate_boolean_param(params.get('follow', False), 'follow', 'container_logs', False)
    details = validate_boolean_param(params.get('details', False), 'details', 'container_logs', False)
    
    query_params = {'stdout': int(bool(stdout)), 'stderr': int(bool(stderr))}
    if tail:
        query_params['tail'] = tail
    if since:
        query_params['since'] = since
    if until:
        query_params['until'] = until
    if timestamps:
        query_params['timestamps'] = int(bool(timestamps))
    if follow:
        query_params['follow'] = int(bool(follow))
    if details:
        query_params['details'] = int(bool(details))
    
    return invoke_rest_endpoint(config, '/containers/{0}/logs'.format(container_id), 'GET',
                                headers={'accept': 'text/plain'},
                                query_params=query_params)


def rename_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id', 'name'], 'rename_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'rename_container')
    name = params.get('name')
    return invoke_rest_endpoint(config, '/containers/{0}/rename'.format(container_id), 'POST', query_params={'name': name})


def prune_containers(config, params, *args, **kwargs):
    filters = validate_json_param(params.get('filters'), 'filters', 'prune_containers')
    query_params = {'filters': filters} if filters else None
    return invoke_rest_endpoint(config, '/containers/prune', 'POST', query_params=query_params)


def exec_container(config, params, *args, **kwargs):
    """Execute a command in a running container"""
    validate_required_params(params, ['id', 'Cmd'], 'exec_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'exec_container')
    cmd = params.get('Cmd')
    
    # Exec create parameters
    attach_stdout = validate_boolean_param(params.get('AttachStdout', True), 'AttachStdout', 'exec_container', True)
    attach_stderr = validate_boolean_param(params.get('AttachStderr', True), 'AttachStderr', 'exec_container', True)
    tty = validate_boolean_param(params.get('Tty', False), 'Tty', 'exec_container', False)
    privileged = validate_boolean_param(params.get('Privileged', False), 'Privileged', 'exec_container', False)
    user = params.get('User')
    env = params.get('Env')  # List of environment variables
    working_dir = params.get('WorkingDir')
    
    body = {
        'AttachStdout': attach_stdout,
        'AttachStderr': attach_stderr,
        'Tty': tty,
        'Privileged': privileged,
        'Cmd': cmd if isinstance(cmd, list) else [cmd]
    }
    
    if user:
        body['User'] = user
    if env:
        body['Env'] = env if isinstance(env, list) else [env]
    if working_dir:
        body['WorkingDir'] = working_dir
    
    # Create exec instance
    exec_create = invoke_rest_endpoint(config, '/containers/{0}/exec'.format(container_id), 'POST', data=body)
    exec_id = exec_create.get('Id')
    if not exec_id:
        raise ConnectorError('Failed to create exec: missing Id')
    
    # Exec start parameters
    detach = validate_boolean_param(params.get('Detach', False), 'Detach', 'exec_container', False)
    
    # Start exec
    started = invoke_rest_endpoint(config, '/exec/{0}/start'.format(exec_id), 'POST', 
                                    data={'Detach': detach, 'Tty': tty})
    return {'exec_id': exec_id, 'output': started}


def pause_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'pause_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'pause_container')
    return invoke_rest_endpoint(config, '/containers/{0}/pause'.format(container_id), 'POST')


def unpause_container(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'unpause_container')
    container_id = params.get('id')
    validate_container_id(container_id, 'unpause_container')
    return invoke_rest_endpoint(config, '/containers/{0}/unpause'.format(container_id), 'POST')


def container_stats(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'container_stats')
    container_id = params.get('id')
    validate_container_id(container_id, 'container_stats')
    stream = validate_boolean_param(params.get('stream', False), 'stream', 'container_stats', False)
    return invoke_rest_endpoint(config, '/containers/{0}/stats'.format(container_id), 'GET',
                                query_params={'stream': int(bool(stream))})


def container_export(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'container_export')
    container_id = params.get('id')
    validate_container_id(container_id, 'container_export')
    return invoke_rest_endpoint(config, '/containers/{0}/export'.format(container_id), 'GET',
                                headers={'accept': 'application/octet-stream'})


def container_commit(config, params, *args, **kwargs):
    validate_required_params(params, ['id'], 'container_commit')
    container_id = params.get('id')
    validate_container_id(container_id, 'container_commit')
    repo = params.get('repo')
    tag = params.get('tag', 'latest')
    comment = params.get('comment')
    author = params.get('author')
    changes = params.get('changes')
    pause = validate_boolean_param(params.get('pause', True), 'pause', 'container_commit', True)
    
    query_params = {
        'container': container_id,
        'repo': repo,
        'tag': tag,
        'comment': comment,
        'author': author,
        'changes': changes,
        'pause': int(bool(pause))
    }
    # Remove None values
    query_params = {k: v for k, v in query_params.items() if v is not None}
    
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
    stdout = validate_boolean_param(params.get('stdout', True), 'stdout', 'attach_container', True)
    stderr = validate_boolean_param(params.get('stderr', True), 'stderr', 'attach_container', True)
    stream = validate_boolean_param(params.get('stream', True), 'stream', 'attach_container', True)
    logs = validate_boolean_param(params.get('logs', False), 'logs', 'attach_container', False)
    
    query_params = {
        'stdout': int(bool(stdout)),
        'stderr': int(bool(stderr)),
        'stream': int(bool(stream)),
        'logs': int(bool(logs))
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
    
    # Use /archive endpoint instead of deprecated /copy (since API v1.20+)
    return invoke_rest_endpoint(config, '/containers/{0}/archive'.format(container_id), 'GET',
                                query_params={'path': path},
                                headers={'accept': 'application/x-tar'})


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


