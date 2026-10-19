"""Default-OFF local receiver staging; never asserts canonical preload origin.

Fresh kernel checks prove local inherited resources and parent peer only. The
same holder's source remains UNQUALIFIED until a future canonical source chain
is implemented. No API here promotes it or issues a Native provider token.
"""
from dataclasses import dataclass

from . import native_loaded_provider_custody_v1 as contract
from .native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1, _FileLeaseV1, _normal_dos


@dataclass(frozen=True)
class ReceiverResultV1:
    available: bool
    reason: str
    holder: object = None
    transfer: object = None


@dataclass
class _LocalReceiverV1:
    holder: object
    facade: object
    parent_handle: int
    revoke_handle: int
    control_handle: int
    parent: object
    receiver_pid: int
    seal: object
    owner: object = None
    active: bool = True


def receive_inherited_preload_v1(*, inherited, owned_control_handle, facade, machine_id,
                                 native_pipe_name, enabled=False):
    """Take ownership only after inherited-flag/client-peer checks; no JSON proof.

    The caller must retain returned holder on cleanup failure. Neither the
    control pipe nor parent/root handles may be an existing SDK/runtime handle.
    They belong exclusively to this private handoff. No source promotion exists.
    """
    if enabled is not True:
        return ReceiverResultV1(False,"default_off")
    acquired=[]
    try:
        contract._require(type(facade) is WindowsNativeCustodyFacadeV1 and facade.enabled,
                          "actual enabled Windows facade required")
        contract._require(type(inherited) is dict and set(inherited)=={"target","lease","parent","revoke"},
                          "four inherited resource locations required")
        values=list(inherited.values())
        contract._require(all(type(h) is int and h>0 for h in values)
                          and len(set(values))==4 and type(owned_control_handle) is int
                          and owned_control_handle>0 and owned_control_handle not in values,
                          "distinct local handle locations required")
        contract._require(isinstance(machine_id,str) and bool(machine_id.strip()),"machine identity required")
        from .native_driver import _validate_pipe_name
        native_pipe_name=_validate_pipe_name(native_pipe_name)
        with facade._lock:
            api=facade._os()
            contract._require(not any(h in facade._owned for h in values+[owned_control_handle]),
                              "resource already registered or borrowed")
            for handle in values:
                api.accept_inherited_handle(handle)
                facade._owned[handle]="received_pending"
                acquired.append(handle)
            process=contract._process(facade.observe_process(inherited["target"]))
            parent=contract._process(facade.observe_process(inherited["parent"]))
            contract._require(api.private_parent_pid(owned_control_handle)==parent.pid,
                              "private control server is not the inherited parent")
            facade._owned[owned_control_handle]="received_control"
            acquired.append(owned_control_handle)
            contract._require(api.wait_zero(inherited["revoke"])==0x102,"root already revoked")
            volume,identity,size=api.file_identity(inherited["lease"])
            dos=_normal_dos(api.final_path(inherited["lease"],nt=False))
            nt=api.final_path(inherited["lease"],nt=True)
            digest=api.hash_held_file(inherited["lease"],size)
            contract._require(api.file_identity(inherited["lease"])==(volume,identity,size),"received file changed")
            contract._require(api.wait_zero(inherited["revoke"])==0x102
                and contract._same_process(parent,facade.observe_process(inherited["parent"]))
                and api.private_parent_pid(owned_control_handle)==parent.pid,
                "root/parent changed during local receive")
            dll=contract._dll(contract._DLLReadbackV1(dos,volume,identity,digest,size))
            holder=contract._PreloadCustodyV1(target=None,facade=facade,
                process_handle=inherited["target"],dll_handle=inherited["lease"],process=process,dll=dll,
                machine_id=machine_id,pipe_name=native_pipe_name,seal=contract._RESOURCE_SEAL,source_role="received")
            holder._owned=list(acquired)
            facade._owned[inherited["lease"]]="preload_file"
            facade._files[inherited["lease"]]=_FileLeaseV1(dos,nt,volume,identity,size)
            record=_LocalReceiverV1(holder,facade,inherited["parent"],inherited["revoke"],
                owned_control_handle,parent,api.current_process_id(),contract._RESOURCE_SEAL)
            if not hasattr(facade,"_received_preloads_v1"):facade._received_preloads_v1={}
            facade._received_preloads_v1[holder]=record
            return ReceiverResultV1(True,"local_kernel_staged_canonical_origin_unknown",holder,record)
    except Exception as error:
        failed=[]
        for handle in reversed(acquired):
            try:facade.close_owned_handle(handle)
            except Exception:failed.append(handle)
        holder=None
        if failed:
            holder=contract._PreloadCustodyV1(target=None,facade=facade,process_handle=None,dll_handle=None,
                process=None,dll=None,machine_id=machine_id,pipe_name=native_pipe_name,
                seal=contract._RESOURCE_SEAL,source_role="received")
            holder._owned,holder.closed=failed,True
        return ReceiverResultV1(False,"unavailable:"+type(error).__name__+":"+str(error)[:160],holder)


def bind_received_owner_v1(result, owner):
    """Attach staged resources to the canonical owner; DOES NOT qualify source."""
    from .successor_ui_app_owner_v1 import SuccessorUIAppOwner
    from .native_driver import NativeHeadlessGameplayDriver
    contract._require(type(result) is ReceiverResultV1 and result.available,"staged local result required")
    holder,record=result.holder,result.transfer
    contract._require(type(owner) is SuccessorUIAppOwner and type(owner.driver) is NativeHeadlessGameplayDriver
        and owner.service.driver is owner.driver and getattr(owner.service,"_successor_ui_app_owner_v1",None) is owner
        and getattr(owner.driver,"_player_heir_candidate_owner_v1",None) is owner
        and owner.machine==holder.machine_id,"canonical local owner required")
    with owner.lock:
        contract._require(record is holder.facade._received_preloads_v1.get(holder)
                          and record.owner is None and record.active and not holder.closed,
                          "local receiver already bound or revoked")
        contract._require(getattr(owner,"_player_heir_loaded_custody_v1",None) is None
                          and getattr(owner,"_player_heir_loaded_provider_v1",None) is None,
                          "previous custody must be normally released")
        holder.owner=record.owner=owner
        owner._player_heir_loaded_custody_v1=holder
        holder.transfer=record
    return record


def _verified_transfer_v1(facade, record, owner):
    contract._require(type(record) is _LocalReceiverV1 and record.seal is contract._RESOURCE_SEAL
        and record.facade is facade and record.owner is owner and owner is not None
        and facade._received_preloads_v1.get(record.holder) is record
        and record.receiver_pid==facade.current_process_id(),"same local verified holder/owner required")
    holder=record.holder
    try:
        contract._require(record.active and not holder.closed and holder.target is None
                          and holder.source_role=="received","received holder closed or invalid")
        api=facade._os()
        contract._require(api.wait_zero(record.revoke_handle)==0x102,"root revoked")
        contract._require(contract._same_process(record.parent,facade.observe_process(record.parent_handle))
            and api.private_parent_pid(record.control_handle)==record.parent.pid,
            "parent generation/peer changed")
        contract._require(contract._same_process(holder.process,facade.observe_process(holder.process_handle))
            and contract._same_dll(holder.dll,facade.observe_dll(holder.dll_handle)),"received target/file changed")
        contract._require(api.wait_zero(record.revoke_handle)==0x102
            and contract._same_process(record.parent,facade.observe_process(record.parent_handle))
            and api.private_parent_pid(record.control_handle)==record.parent.pid,
            "root/parent changed during transfer readback")
        return contract._TransferReadbackV1(holder,owner,record.receiver_pid,holder.process_handle,holder.dll_handle)
    except Exception:
        record.active=False
        holder.close()  # existing owner clears DTO/cache before owned close
        raise
