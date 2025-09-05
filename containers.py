from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)


def list_containers(config, params, *args, **kwargs):
    all_flag = params.get('all', False)
    return invoke_rest_endpoint(config, '/containers/json', 'GET', query_params={'all': int(bool(all_flag))})


def inspect_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/json'.format(container_id), 'GET')


def start_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    return invoke_rest_endpoint(config, '/containers/{0}/start'.format(container_id), 'POST')


def stop_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    timeout = params.get('t')
    if not container_id:
        raise ConnectorError('Missing required input: id')
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
    container_id = params.get('id')
    if not container_id:
        raise ConnectorError('Missing required input: id')
    
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


