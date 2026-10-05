"""Backend-owned retained-handle lifecycle; no caller process/handle selection."""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .driver import UnsupportedStepError
from .normal_exit_contract_v1 import classify_terminal_exit_receipt
from .normal_exit_process_observer_v1 import RetainedProcessObserver


def _preserve(path: Path, value: dict) -> None:
    actual=Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path
    with actual.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


@dataclass
class RetainedNormalExitObservationV1:
    observer: RetainedProcessObserver
    native_observation: dict | None
    driver_dispatch_receipt_observed_monotonic_ns: int | None
    metadata: dict
    directory: Path


def retain_normal_exit_observer_v1(driver, observer, native, receipt_ns, metadata, directory):
    if getattr(driver,'_normal_exit_owned_observer_v1',None) is not None:
        raise RuntimeError('a backend-owned original-process observer already exists')
    state=RetainedNormalExitObservationV1(observer,copy.deepcopy(native),receipt_ns,
                                        copy.deepcopy(metadata),directory)
    driver._normal_exit_owned_observer_v1=state
    return state


def complete_normal_exit_observer_after_receipt_v1(driver, state, result, receipt_path):
    """Caller must durably save the actual exit fact before disposing its handle."""
    if result.get('process_exit_observed') is not True:
        return
    actual_receipt=Path('\\\\?\\'+str(receipt_path.resolve())) if os.name=='nt' else receipt_path
    if not actual_receipt.is_file():
        raise RuntimeError('terminal process fact must be preserved before handle closure')
    # Original identity remains retained in the fact receipt; no reopened handle.
    state.observer.close()
    prefix=hashlib.sha256(state.metadata['request_id'].encode()).hexdigest()[:20]
    close_path=state.directory/(prefix+'.observer-close-'+uuid.uuid4().hex[:16]+'.json')
    driver._normal_exit_completed_observation_receipt_v1=str(receipt_path)
    driver._normal_exit_owned_observer_v1=None
    result['observer_retained']=False
    try:
        _preserve(close_path,{'schema':'ck3-normal-exit-observer-close-v1',
        'reason':'independent_exit_fact_preserved','fact_receipt_path':str(receipt_path),
        'pid':state.observer.identity.pid,
        'creation_filetime_100ns':state.observer.identity.creation_filetime_100ns,
        'retained_handle_token':state.observer.identity.retained_handle_token,
            'close_error':state.observer.close_error,'retry_authorized':False})
        result['observer_close_receipt_path']=str(close_path)
    except Exception as error:
        # The signaled/code fact is already durably preserved; cleanup-receipt
        # errors must not replace it with a generic unknown response.
        result['observer_close_receipt_error']=f'{type(error).__name__}: {error}'


def observe_normal_exit_v1(driver) -> dict:
    state=getattr(driver,'_normal_exit_owned_observer_v1',None)
    if type(state) is not RetainedNormalExitObservationV1:
        raise UnsupportedStepError('no backend-owned pending original-process observer is available')
    process=state.observer.observe(5000)
    facts=classify_terminal_exit_receipt(state.native_observation,process,
        driver_dispatch_receipt_observed_monotonic_ns=state.driver_dispatch_receipt_observed_monotonic_ns,
        expected_process_identity=state.observer.identity)
    prefix=hashlib.sha256(state.metadata['request_id'].encode()).hexdigest()[:20]
    name=prefix+'.observe-'+uuid.uuid4().hex[:16]
    receipt_path=state.directory/(name+'.json')
    result={'schema':'ck3-normal-exit-process-observation-result-v1',**state.metadata,**facts,
        'native_observation':state.native_observation,'process_observation':process,
        'driver_dispatch_receipt_observed_monotonic_ns':state.driver_dispatch_receipt_observed_monotonic_ns,
        'receipt_clock_meaning':'driver observed validated dispatch_invoked response; not native callback time',
        'observer_retained':True,'snapshot_after_required':False,'native_submission_count':0,
        'uses_desktop_input':False,'uses_ocr':False,'receipt_path':str(receipt_path)}
    # Save the signaled/code fact before closing; an IO failure leaves ownership
    # and the original handle retained for another read-only observation attempt.
    _preserve(receipt_path,result)
    complete_normal_exit_observer_after_receipt_v1(driver,state,result,receipt_path)
    return result


def dispose_normal_exit_observer_v1(driver) -> None:
    state=getattr(driver,'_normal_exit_owned_observer_v1',None)
    if type(state) is not RetainedNormalExitObservationV1:
        return
    # Explicit SDK/driver close is cleanup, never process-exit evidence. Preserve
    # that distinction before disposal, then retain its actual cleanup outcome.
    prefix=hashlib.sha256(state.metadata['request_id'].encode()).hexdigest()[:20]
    path=state.directory/(prefix+'.observer-dispose-'+uuid.uuid4().hex[:16]+'.json')
    receipt_error=None
    try:
        _preserve(path,{'schema':'ck3-normal-exit-observer-dispose-v1',**state.metadata,
        'status':'observer_disposed_without_exit_proof','claim_consumed':True,'retry_authorized':False,
        'process_exit_observed':False,'typed_normal_exit_observed':False,'autosave_verified':False,
        'native_observation':state.native_observation,
        'retained_handle_token':state.observer.identity.retained_handle_token,
            'recorded_monotonic_ns':time.monotonic_ns()})
    except Exception as error:
        receipt_error=f'{type(error).__name__}: {error}'
    finally:
        state.observer.close()
        driver._normal_exit_owned_observer_v1=None
    try:
        _preserve(path.with_name(path.stem+'.close.json'),{'dispose_receipt_path':str(path),
            'dispose_receipt_error':receipt_error,
            'close_error':state.observer.close_error,'exit_proof_created':False})
    except Exception as error:
        receipt_error=(receipt_error or '')+f'; close_receipt: {type(error).__name__}: {error}'
    driver._normal_exit_disposal_error_v1=receipt_error
