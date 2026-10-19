"""Canonical preload authority over a private, kernel-bound creation chain.

Default OFF. The source remains the original controller holder, never a JSON
qualification. Received holders keep source_verified=False. Only the existing
loaded-provider issuer can mint its existing DTO after a live origin readback.
"""
from dataclasses import dataclass
import secrets
import threading

from . import native_loaded_provider_custody_v1 as contract
from .native_loaded_provider_origin_io_v1 import OriginKernelIOV1


def _epoch():
    from ..successor_ui_pending_ledger_v1 import owner_source_epoch_v1
    return owner_source_epoch_v1()


def _process_key(value):
    value=contract._process(value)
    return [value.pid,str(value.creation_filetime),contract._path(value.executable)]


def _file_key(value):
    value=contract._dll(value)
    return [str(value.volume_serial),value.file_id.hex(),value.size,value.sha256,contract._path(value.final_path)]


@dataclass
class _ChildEdgeV1:
    """Local retained creator return, not deserialized qualification."""
    holder: object
    io: object
    child: object
    process_handle: object
    process: object
    control: int
    role: str
    seal: object
    chain_handles: tuple = ()


def _record_actual_child_v1(holder,io,child,process_handle,control,role):
    # Called only by the one-shot creator immediately after its actual return.
    actual=contract._process(io.facade.observe_process(process_handle))
    contract._require(actual.pid==child.pid,"actual returned child identity differs")
    io.connected(control)
    contract._require(io.api.pipe_client_pid(control)==actual.pid,"private child kernel peer differs")
    hello=io.recv(control)
    contract._require(hello=={"kind":"staged","role":role,"epoch":_epoch(),
        "creator":holder._creator_source_digest_v1},"actual child bootstrap differs")
    io.send(control,{"kind":"parent_accepted","epoch":_epoch(),"creator":holder._creator_source_digest_v1})
    return _ChildEdgeV1(holder,io,child,process_handle,actual,control,role,contract._RESOURCE_SEAL)


def _pull_actual_chain_v1(edge):
    contract._require(type(edge) is _ChildEdgeV1 and edge.seal is contract._RESOURCE_SEAL,
                      "actual local creation edge required")
    io=edge.io
    contract._require(contract._same_process(edge.process,io.facade.observe_process(edge.process_handle)),
                      "source child exited or changed before upward transfer")
    message=io.recv(edge.control)
    expected={"owner":("Queue","MCPApp"),"Queue":("MCPApp",),"MCPApp":()}[edge.role]
    contract._require(set(message)=={"kind","exports"} and message["kind"]=="actual_child_exports"
        and type(message["exports"]) is list and len(message["exports"])==len(expected),
        "actual child export shape differs")
    direct=io.duplicate(edge.process_handle,holder=edge.holder,access=io.api.PROCESS_READ_ACCESS)
    handles=[direct]
    for row,role in zip(message["exports"],expected):
        contract._require(type(row) is dict and set(row)=={"role","location"} and row["role"]==role,
                          "private child role/order differs")
        handles.append(io.pull_read_process(edge.process_handle,row["location"],holder=edge.holder))
    keys=[_process_key(io.facade.observe_process(h)) for h in handles]
    contract._require(len({key[0] for key in keys})==len(keys),"creation chain aliases a process")
    edge.chain_handles=tuple(handles)
    return edge.chain_handles


class _CanonicalOriginV1:
    def __init__(self,holder,io):
        contract._require(type(holder) is contract._PreloadCustodyV1
            and holder.seal is contract._RESOURCE_SEAL and holder.source_role=="controller"
            and holder.target is not None and holder.target.resumed is False and not holder.closed,
            "original pre-resume controller custody required")
        self.holder,self.io,self.epoch=holder,io,_epoch()
        contract._require(contract._sha(getattr(holder,"_creator_source_digest_v1",None)),
                          "actual creator source closure missing")
        self.lock=threading.RLock();self.active=True;self.error=None
        self.ready=threading.Event();self.final_handle=None;self.chain=None;self.last_sequence=0
        self.revoke_handle=io.event(holder=holder)
        self.origin_handle=io.duplicate(io.api.current(),holder=holder,access=io.api.PROCESS_READ_ACCESS)
        self.origin=contract._process(io.facade.observe_process(self.origin_handle))
        self.server,self.pipe_name=io.server(holder=holder)
        holder._canonical_origin_v1=self
        holder._canonical_chain_io_v1=io
        holder._creation_role_v1="supervisor"

    def bind_actual_chain(self,edge):
        contract._require(type(edge) is _ChildEdgeV1 and edge.holder is self.holder
            and edge.io is self.io and edge.role=="owner" and edge.seal is contract._RESOURCE_SEAL,
            "original supervisor's actual owner edge required")
        handles=_pull_actual_chain_v1(edge)
        contract._require(len(handles)==3,"owner Queue App chain incomplete")
        with self.lock:
            contract._require(self.chain is None and self.active,"origin chain already bound or revoked")
            self.chain=tuple((h,contract._process(self.io.facade.observe_process(h))) for h in handles)
            self.final_handle=handles[-1]
            self.ready.set()

    def _body(self,*,full):
        contract._require(self.active and not self.holder.closed,
                          "original source origin closed or epoch changed")
        contract._require(self.io.api.wait_zero(self.revoke_handle)==0x102,"original root revoked")
        contract._require(self.chain is not None,"actual final App not registered")
        for handle,identity in self.chain:
            contract._require(self.io.api.wait_zero(handle)==0x102,"actual creation ancestor exited")
            if full:
                contract._require(contract._same_process(identity,self.io.facade.observe_process(handle)),
                                  "actual creation generation changed")
        contract._require(self.io.api.wait_zero(self.holder.process_handle)==0x102,"held target exited")
        if full:
            contract._require(contract._same_process(self.holder.process,self.io.facade.observe_process(self.holder.process_handle))
                and contract._same_dll(self.holder.dll,self.io.facade.observe_dll(self.holder.dll_handle)),
                "original preload retained resources changed")
        contract._require(self.active and not self.holder.closed,"origin revoked during readback")
        return {"epoch":self.epoch,"creator":self.holder._creator_source_digest_v1,
                "target":_process_key(self.holder.process),"file":_file_key(self.holder.dll),
                "origin":_process_key(self.origin),"app":_process_key(self.chain[-1][1])}

    def serve(self):
        """One private final-App connection; no public service or reconnect."""
        try:
            self.io.connected(self.server)
            contract._require(self.ready.wait(self.io.timeout),"final App chain registration timeout")
            peer=self.io.api.pipe_client_pid(self.server)
            contract._require(peer==self.chain[-1][1].pid,"origin client is not actual returned final App")
            while True:
                try:
                    request=self.io.recv(self.server)
                except TimeoutError:
                    if self.active:continue
                    raise
                with self.lock:
                    contract._require(set(request)=={"kind","sequence","epoch","nonce"}
                        and request["kind"] in ("verify","live")
                        and type(request["sequence"]) is int and request["sequence"]==self.last_sequence+1
                        and request["epoch"]==self.epoch and isinstance(request["nonce"],str)
                        and len(request["nonce"])==32,"fresh private origin request required")
                    self.last_sequence=request["sequence"]
                    body=self._body(full=request["kind"]=="verify")
                    contract._require(self.io.api.pipe_client_pid(self.server)==peer,"origin App peer changed")
                    self.io.send(self.server,{"kind":"original_preload_live","sequence":self.last_sequence,
                        "nonce":request["nonce"],"body":body})
        except Exception as error:
            self.error=type(error).__name__+":"+str(error)[:180]
        finally:
            self.revoke_before_close()

    def revoke_before_close(self):
        with self.lock:
            self.active=False
            # Keep handles if event revocation cannot be proved. Closing the
            # pipe also makes any cached source consumer fail its fresh check.
            errors=[]
            if self.revoke_handle in self.io.facade._owned:
                try:self.io.revoke(self.revoke_handle)
                except Exception as error:errors.append(error)
            if self.server in self.io.facade._owned:
                try:self.io.close(self.server)
                except Exception as error:errors.append(error)
            if errors:raise ValueError("canonical root revocation/release unverified") from errors[0]


def prepare_canonical_origin_v1(*,custody,enabled=False):
    if enabled is not True:return None
    io=OriginKernelIOV1(custody.facade,enabled=True)
    return _CanonicalOriginV1(custody,io)


class _OriginSessionV1:
    def __init__(self,holder,io,origin_handle,origin_pipe):
        self.holder,self.io,self.origin_handle=holder,io,origin_handle
        self.origin=contract._process(io.facade.observe_process(origin_handle))
        self.epoch,self.sequence,self.lock=_epoch(),0,threading.RLock()
        self.app_handle=io.duplicate(io.api.current(),holder=holder,access=io.api.PROCESS_READ_ACCESS)
        self.app=contract._process(io.facade.observe_process(self.app_handle))
        self.handle=io.client(origin_pipe,holder=holder)
        contract._require(io.api.private_parent_pid(self.handle)==self.origin.pid,
                          "fresh origin server differs from inherited origin")

    def require(self,owner,*,full):
        with self.lock:
            holder=self.holder
            contract._require(not holder.closed and getattr(owner,"_player_heir_loaded_custody_v1",None) is holder
                and owner.epoch==self.epoch and holder.owner is owner,"same local canonical owner/epoch required")
            record=holder.facade._received_preloads_v1.get(holder)
            contract._require(record is not None and record.active,"same verified receiver required")
            for handle in (self.origin_handle,record.parent_handle,holder.process_handle):
                contract._require(self.io.api.wait_zero(handle)==0x102,"origin/parent/target exited")
            contract._require(self.io.api.wait_zero(record.revoke_handle)==0x102,"canonical root revoked")
            contract._require(self.io.api.private_parent_pid(self.handle)==self.origin.pid,"origin peer changed")
            self.sequence+=1;nonce=secrets.token_hex(16)
            self.io.send(self.handle,{"kind":"verify" if full else "live","sequence":self.sequence,
                "epoch":self.epoch,"nonce":nonce})
            reply=self.io.recv(self.handle)
            expected={"epoch":self.epoch,"creator":holder._creator_source_digest_v1,
                "target":_process_key(holder.process),"file":_file_key(holder.dll),
                "origin":_process_key(self.origin),"app":_process_key(self.app)}
            contract._require(reply=={"kind":"original_preload_live","sequence":self.sequence,"nonce":nonce,"body":expected},
                              "canonical origin readback differs from actual local resources")
            contract._require(self.io.api.wait_zero(record.revoke_handle)==0x102
                and self.io.api.private_parent_pid(self.handle)==self.origin.pid,"origin revoked during readback")


def attach_received_origin_v1(result,*,origin_handle,origin_pipe,enabled=False):
    """Private bootstrap only; locations never assert qualification."""
    if enabled is not True:return None
    from .native_loaded_provider_receiver_v1 import ReceiverResultV1
    contract._require(type(result) is ReceiverResultV1 and result.available,"staged local receiver required")
    holder=result.holder
    contract._require(holder.source_role=="received" and not holder.closed
        and not hasattr(holder,"_origin_session_v1"),"one received origin session required")
    io=OriginKernelIOV1(holder.facade,enabled=True)
    try:
        io.adopt_inherited(origin_handle,holder=holder)
        session=_OriginSessionV1(holder,io,origin_handle,origin_pipe)
        holder._origin_session_v1=session
        return session
    except Exception:
        holder.close()
        raise


def require_original_preload_origin_v1(custody,owner):
    contract._require(type(custody) is contract._PreloadCustodyV1 and custody.seal is contract._RESOURCE_SEAL,
                      "original typed custody required")
    if custody.source_role=="controller":
        contract._require(custody._preload_source_verified is True and custody.target is not None,
                          "original controller preload source required")
        return
    session=getattr(custody,"_origin_session_v1",None)
    contract._require(type(session) is _OriginSessionV1 and session.holder is custody,
                      "received canonical preload continuity is not qualified")
    session.require(owner,full=True)


def ensure_received_provider_v1(owner):
    """First eligible optional component only; missing bootstrap does no IO."""
    holder=getattr(owner,"_player_heir_loaded_custody_v1",None)
    if not isinstance(holder,contract._PreloadCustodyV1) or not hasattr(holder,"_origin_session_v1"):
        return None
    with owner.lock:
        if getattr(owner,"_player_heir_loaded_provider_v1",None) is not None:return None
        driver=owner.driver
        holder.facade.bind_server_endpoint(driver.endpoint)
        return contract.issue_loaded_native_provider_v1(custody=holder,owner=owner,driver=driver,
            endpoint=driver.endpoint,transfer=holder.transfer,os_facade=holder.facade,enabled=True)


def exact_live_provider_game_v1(owner,provider):
    with owner.lock:
        return _exact_live_provider_game_locked_v1(owner,provider)


def _exact_live_provider_game_locked_v1(owner,provider):
    """No CIM rounding. Cheap held liveness + private source readback per use."""
    holder=getattr(owner,"_player_heir_loaded_custody_v1",None)
    try:
        contract._require(type(holder) is contract._PreloadCustodyV1 and not holder.closed
            and holder.owner is owner and provider is owner._player_heir_loaded_provider_v1,
            "same live issued custody required")
        process=holder.process
        contract._require(type(provider.game_creation_filetime) is int
            and provider.game_creation_filetime==process.creation_filetime
            and provider.game_pid==process.pid and provider.game_birth==process.creation_date
            and contract._path(provider.game_executable)==contract._path(process.executable),
            "loaded exact kernel birth differs")
        session=getattr(holder,"_origin_session_v1",None)
        if holder.source_role=="received":
            contract._require(type(session) is _OriginSessionV1 and session.holder is holder,"original origin session unavailable")
            session.require(owner,full=False)
        else:
            contract._require(holder.facade._os().wait_zero(holder.process_handle)==0x102,"original target exited")
        return {"pid":process.pid,"creation_date":process.creation_date,"executable":process.executable}
    except Exception:
        contract.invalidate_loaded_native_provider_v1(owner,reason="provider_source_liveness_failed")
        raise
