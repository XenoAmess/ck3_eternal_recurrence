"""Read original snapshots while separating one known game-owned settings output."""
import hashlib
from pathlib import Path


MUTABLE_PROFILE_FILES = {"pdx_settings.txt"}


def identity(path):
    path=Path(path).resolve();digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':digest.hexdigest()}


def validate_running_inputs(live, frozen, *, observer=identity):
    """Never rewrite or re-pin original input; check every immutable original byte.

    Only the exact top-level pdx_settings.txt in this allocated profile is mutable.
    Its original snapshot must still match the prelaunch pin; its current bytes
    are observed separately. All mod content, dlc_load and original snapshots
    stay immutable. A future mutable class requires a deliberate source change.
    """
    live=Path(live).resolve();profile=(Path(frozen['state_dir'])/'profile').resolve()
    result={'immutable_inputs_checked':0,'mutable_profile_observations':[]}
    for name,row in frozen['files'].items():
        path=Path(name).resolve()
        relative=path.relative_to(profile).as_posix() if path.is_relative_to(profile) else None
        if relative in MUTABLE_PROFILE_FILES:
            snapshot=(live/'input-snapshots/profile'/relative).resolve()
            snapshot_pin=frozen['files'].get(str(snapshot))
            if snapshot_pin!=row:raise ValueError('Mutable input has no exact original immutable snapshot: '+name)
            original=observer(snapshot)
            if (original['bytes'],original['sha256'])!=(row['bytes'],row['sha256']):
                raise ValueError('Original mutable input snapshot changed: '+str(snapshot))
            observed=observer(path)
            result['mutable_profile_observations'].append({'original_launch_pin':{'path':str(path),**row},
                'immutable_original_snapshot':original,'current_game_owned_output':observed,
                'bytes_changed':(observed['bytes'],observed['sha256'])!=(row['bytes'],row['sha256']),
                'meaning':'current game-owned settings output; original input remains retained and unchanged'})
            continue
        actual=observer(path)
        if (actual['bytes'],actual['sha256'])!=(row['bytes'],row['sha256']):
            raise ValueError('Immutable original input changed: '+name)
        result['immutable_inputs_checked']+=1
    return result


def verify_allocated_running_settings(profile, settings_row):
    """Bind a game-owned output to its original allocated immutable input bytes."""
    import json
    live=Path(profile['evidence_directory']).resolve()
    frozen_path=live/'frozen-argv.json'
    frozen=json.loads(frozen_path.read_text(encoding='utf-8-sig'))
    context=json.loads((live/'ready-context.json').read_text(encoding='utf-8-sig'))
    if (identity(frozen_path)!=context.get('frozen_argv') or context.get('run_id')!=frozen.get('run_id')
            or Path(context['run_dir']).resolve()!=live):
        raise ValueError('Normal-exit running profile lacks its exact original ready/frozen allocation')
    state=Path(profile['state_directory']).resolve();userdir=Path(profile['userdir']).resolve()
    if Path(frozen['state_dir']).resolve()!=state or userdir!=state/'profile':
        raise ValueError('Normal-exit running profile crossed the actual allocated state/userdir')
    if (not isinstance(settings_row,dict) or set(settings_row)!={'path','bytes','sha256'}
            or Path(settings_row['path']).resolve()!=userdir/'pdx_settings.txt'):
        raise ValueError('Only allocated top-level pdx_settings is a game-owned output')
    original=frozen.get('files',{}).get(str(userdir/'pdx_settings.txt'))
    if original!={key:settings_row[key] for key in ('bytes','sha256')}:
        raise ValueError('Normal-exit settings inventory differs from the original allocated launch pin')
    observed=validate_running_inputs(live,frozen)
    values=observed['mutable_profile_observations']
    if len(values)!=1:raise ValueError('One exact allocated settings output observation required')
    return {'allocation':identity(frozen_path),'settings':values[0],
            'immutable_inputs_checked':observed['immutable_inputs_checked']}
