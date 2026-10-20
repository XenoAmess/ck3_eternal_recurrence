"""Exact profile selection through real provider/gate, with no OS reads."""
from __future__ import annotations
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import struct
import unittest
from steam_offline_native_profiles import PROFILES, PROFILE_1096, PROFILE_1112, NativeOfflineProfile, select_profile
from steam_offline_native_provider_v1 import Module, NativeObserved, NativeUnavailable, _probe_bound
from steam_offline_state_contract import ProcessIdentity, SourceIdentity
from ck3_mod_acceptance_steam_gate import validate_observation

BASE=0x180000000
MANAGER=0x200000000

class Reader:
    def __init__(self, profile: NativeOfflineProfile, *, ui_version: str | None=None) -> None:
        self.steam=ProcessIdentity(12001,'134000000000000001',str(Path('steam.exe').resolve()),profile.steam_version)
        self.ui_version=ui_version or profile.steam_version
    def identity(self,pid: int) -> ProcessIdentity:
        if pid!=self.steam.pid:raise ValueError('Unexpected fixture PID')
        return self.steam
    def file_version(self,path: str) -> str:
        return self.ui_version

class FakeBackend:
    def __init__(self, profile: NativeOfflineProfile, *, wrong_anchor: bool=False,
                 wrong_module: bool=False, raw: int=1, tray: int=4) -> None:
        self.profile=profile;self.wrong_anchor=wrong_anchor;self.wrong_module=wrong_module
        self.raw=raw;self.tray=tray;self.reads: list[tuple[int,int]]=[];self.closed=False
        self.source_value=SourceIdentity(str(Path('steamui.dll').resolve()),profile.image_bytes,profile.image_sha256,'1','2')
    def source(self,path: str) -> SourceIdentity:
        return self.source_value
    def module(self,pid: int,path: str) -> Module:
        return Module(BASE,self.profile.image_size+int(self.wrong_module),self.source_value.path)
    def open(self,pid: int) -> None:pass
    def close(self) -> None:self.closed=True
    def read(self,address: int,count: int) -> bytes:
        self.reads.append((address,count));p=self.profile
        for rva,expected in p.anchors:
            if address==BASE+rva and count==len(expected):return bytes(count) if self.wrong_anchor else expected
        if address==BASE+p.tray_manager_rva and count==8:return struct.pack('<Q',MANAGER)
        if address==BASE+p.value_rva and count==1:return bytes((self.raw,))
        if address==MANAGER+p.tray_offset and count==4:return struct.pack('<I',self.tray)
        raise ValueError('Unexpected or unbounded fixture read')

def wire(profile: NativeOfflineProfile) -> tuple[dict[str,object],Reader]:
    reader=Reader(profile);backend=FakeBackend(profile)
    result=_probe_bound('synthetic-profile-machine','nonce',reader.steam,reader,backend)
    if not isinstance(result,NativeObserved):raise AssertionError(result)
    evidence=result.evidence.to_wire()
    return dict(schema='xar.steam-offline-state-probe/v2',machine_id='synthetic-profile-machine',
        observed_at_utc=result.evidence.observed_at_utc,nonce='nonce',status='offline',offline_mode=True,
        reason='observed',steam=evidence['steam_before'],source=evidence['source_before'],endpoint=None,
        diagnostics=[],observation_method='native_current_user_byte',native_evidence=evidence),reader

class ProfilesTest(unittest.TestCase):
    def test_both_profiles_produce_and_consume_same_v2_json(self) -> None:
        for p in PROFILES:
            value,reader=wire(p)
            result=validate_observation(json.loads(json.dumps(value)),machine_id='synthetic-profile-machine',reader=reader)
            self.assertEqual(result.status,'offline')
            self.assertEqual(result.source.sha256,p.image_sha256)
            self.assertEqual(result.native_evidence.value_rva,str(p.value_rva))
    def test_version_image_cross_product_is_not_a_profile(self) -> None:
        for a,b in [(PROFILE_1096,PROFILE_1112),(PROFILE_1112,PROFILE_1096)]:
            with self.assertRaises(ValueError):select_profile(a.steam_version,b.image_bytes,b.image_sha256)
            reader=Reader(a);backend=FakeBackend(b)
            result=_probe_bound('machine','nonce',reader.steam,reader,backend)
            self.assertIsInstance(result,NativeUnavailable);self.assertEqual(backend.reads,[]);self.assertTrue(backend.closed)
    def test_gate_rejects_cross_profile_receipt(self) -> None:
        value,reader=wire(PROFILE_1112)
        value['steam']={**value['steam'],'file_version':PROFILE_1096.steam_version}
        with self.assertRaises(ValueError):validate_observation(value,machine_id='synthetic-profile-machine',reader=reader)
    def test_source_digest_size_and_unknown_version_are_exact(self) -> None:
        p=PROFILE_1112
        for version,size,digest in [('future',p.image_bytes,p.image_sha256),(p.steam_version,p.image_bytes+1,p.image_sha256),(p.steam_version,p.image_bytes,'0'*64)]:
            with self.assertRaises(ValueError):select_profile(version,size,digest)
        self.assertRaises(ValueError,select_profile,p.steam_version,True,p.image_sha256)
        self.assertRaises(ValueError,select_profile,p.steam_version,float(p.image_bytes),p.image_sha256)
    def test_steamui_file_version_and_loaded_imagesize_remain_bound(self) -> None:
        for p in PROFILES:
            reader=Reader(p,ui_version='wrong');backend=FakeBackend(p)
            self.assertIsInstance(_probe_bound('m','n',reader.steam,reader,backend),NativeUnavailable)
            self.assertEqual(backend.reads,[])
            reader=Reader(p);backend=FakeBackend(p,wrong_module=True)
            self.assertIsInstance(_probe_bound('m','n',reader.steam,reader,backend),NativeUnavailable)
            self.assertEqual(backend.reads,[])
    def test_anchors_tray_and_zero_are_not_weakened(self) -> None:
        for p in PROFILES:
            for options in [dict(wrong_anchor=True),dict(tray=5),dict(raw=0)]:
                reader=Reader(p);backend=FakeBackend(p,**options)
                self.assertIsInstance(_probe_bound('m','n',reader.steam,reader,backend),NativeUnavailable)
                self.assertTrue(backend.closed)
    def test_gate_freshness_and_machine_are_still_independent(self) -> None:
        for p in PROFILES:
            value,reader=wire(p)
            with self.assertRaises(ValueError):validate_observation(value,machine_id='other-machine',reader=reader)
            late=datetime.now(timezone.utc)+timedelta(seconds=31)
            with self.assertRaises(ValueError):validate_observation(value,machine_id='synthetic-profile-machine',reader=reader,now=late)
    def test_registry_records_and_anchor_sequences_are_immutable(self) -> None:
        self.assertIsInstance(PROFILES,tuple)
        self.assertRaises(FrozenInstanceError,setattr,PROFILE_1112,'image_size',0)
        self.assertEqual(len(PROFILE_1096.anchors),6);self.assertEqual(len(PROFILE_1112.anchors),6)

if __name__=='__main__':unittest.main()
