"""One process, serial public-API publication for a fresh promo run.

Import is read-only. The caller supplies an already-created fresh native manifest
and already-frozen output queue. Existing terminal runs are never resumed here.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
import subprocess
import sys

KEYS = {'id', 'path', 'bytes', 'sha256', 'collection', 'role', 'label', 'media_type'}

def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def write_json(path, value):
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def validate_native(run_path, output_directory):
    argv = [sys.executable, '-B', '-m', 'xar_promo', 'validate', str(run_path), '--json']
    write_json(output_directory / 'validate-argv.json', argv)
    completed = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False, shell=False)
    for suffix, data in [('stdout.txt', completed.stdout), ('stderr.txt', completed.stderr)]:
        with (output_directory / ('validate-' + suffix)).open('xb') as stream:
            stream.write(data)
    return {'argv': argv, 'returncode': completed.returncode,
            'stdout': pin(output_directory / 'validate-stdout.txt'),
            'stderr': pin(output_directory / 'validate-stderr.txt')}

def publish_serial(run_path, entries, receipt_directory, *,
                   preserve_callable=None, validate_callable=None):
    """Stop at the first failure; retain after-state when an API call fails.

    Injected callables are only for fake verification and their receipts explicitly
    say so. No thread pool, per-file interpreter launch, private manifest write,
    retry, repair, overwrite, signoff or deletion occurs.
    """
    run_path, receipt_directory = Path(run_path), Path(receipt_directory)
    injected = preserve_callable is not None or validate_callable is not None
    if receipt_directory.exists():
        raise FileExistsError('A fresh append-only publication receipt directory is required')
    receipt_directory.mkdir(parents=True)
    write_json(receipt_directory / 'queue.json', entries)
    mode = 'INJECTED_FAKE_CHECK_ONLY' if injected else 'ACTUAL_PUBLIC_LIBRARY_API'
    journal_path = receipt_directory / 'operations.jsonl'
    started = datetime.now(timezone.utc).isoformat()
    completed_count = 0
    stage = 'preflight'
    before = None
    active = None
    try:
        if not isinstance(entries, list) or not entries:
            raise ValueError('A nonempty frozen queue is required')
        ids = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != KEYS:
                raise ValueError('Unexpected frozen queue keys')
            if not isinstance(entry['id'], str) or not entry['id'] or entry['id'] in ids:
                raise ValueError('Missing or duplicate artifact ID')
            ids.add(entry['id'])
            if entry['collection'] not in {'raw', 'derived'}:
                raise ValueError('Unknown collection')
            if type(entry['bytes']) is not int or entry['bytes'] < 0:
                raise ValueError('Invalid bytes pin')
            expected = {k: entry[k] for k in ['path', 'bytes', 'sha256']}
            if pin(entry['path']) != expected:
                raise ValueError('Frozen source bytes changed before any publication')
        before = pin(run_path)
        if preserve_callable is None:
            from xar_promo.operations import preserve_artifact
            preserve_callable = preserve_artifact
            write_json(receipt_directory / 'actual-public-API-source.json',
                       pin(Path(inspect.getfile(preserve_artifact))))
        with journal_path.open('xb') as journal:
            def append(value):
                journal.write((json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8'))
                journal.flush()
                os.fsync(journal.fileno())
            for entry in entries:
                stage = 'pre-call-file-validation'
                active = entry['id']
                if pin(entry['path']) != {k: entry[k] for k in ['path', 'bytes', 'sha256']}:
                    raise ValueError('Frozen source bytes changed before publication')
                item_before = pin(run_path)
                stage = 'public-preserve-artifact-call'
                try:
                    preserve_callable(run_path, Path(entry['path']),
                                      artifact_id=entry['id'], collection=entry['collection'],
                                      role=entry['role'], label=entry['label'],
                                      media_type=entry['media_type'])
                except Exception as error:
                    append({'mode': mode, 'id': entry['id'], 'status': 'API_CALL_FAILED_NO_RETRY',
                            'before': item_before, 'after': pin(run_path) if run_path.is_file() else None,
                            'exception_type': type(error).__name__, 'message': str(error)})
                    raise
                stage = 'post-call-record'
                append({'mode': mode, 'id': entry['id'], 'status': 'PUBLIC_API_RETURNED',
                        'before': item_before, 'after': pin(run_path),
                        'source': {k: entry[k] for k in ['path', 'bytes', 'sha256']}})
                completed_count += 1
        stage = 'one-final-native-validation'
        validated = (validate_callable or validate_native)(run_path, receipt_directory)
        if validated['returncode'] != 0:
            raise ValueError('Final actual native validation failed')
        result = {'mode': mode, 'status': 'SERIAL_PUBLICATION_AND_NATIVE_VALIDATION_RETURNED_ZERO',
                  'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                  'completed_count': completed_count, 'queued_count': len(entries),
                  'before': before, 'after': pin(run_path), 'final_validation': validated,
                  'human_signoff': False, 'film_or_external_publication_credit': False}
        write_json(receipt_directory / 'RESULT.json', result)
        return result
    except Exception as error:
        write_json(receipt_directory / 'FAILURE.json',
                   {'mode': mode, 'status': 'FAILED_ATTEMPT_PRESERVED_NO_NEXT_PUBLICATION',
                    'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                    'stage': stage, 'active_id': active, 'completed_count': completed_count,
                    'queued_count': len(entries) if isinstance(entries, list) else None,
                    'manifest_before': before,
                    'manifest_after': pin(run_path) if run_path.is_file() else None,
                    'exception_type': type(error).__name__, 'message': str(error),
                    'retry_performed': False, 'human_signoff': False})
        raise
