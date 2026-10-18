"""Same-Game recovery for the independent text provider, never the retired panel.

The historical overlay policy remains readable for old evidence. This explicit
branch uses publisher STARTED pins and never constructs a legacy Overlay value.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from types import SimpleNamespace

from recording_recovery_adapter import ActualAdapter, atomic, load_source, maybe_json, shared_bytes, shared_json, utc
from recording_recovery_supervisor import Game, SdkGuard
import decision_text_publisher as publisher

@dataclass(frozen=True)
class TextRecorder:
    session_id: str
    game: Game
    publisher_started: dict
    receipt_root: Path
    failed: bool
    cleanup: object = None

@dataclass(frozen=True)
class TextObservation:
    game: Game
    game_alive_exact: bool
    recorder: TextRecorder
    publisher_alive_exact: bool
    sdk: SdkGuard

class TextActualAdapter(ActualAdapter):
    """Reuse owned cleanup/local controls, with a distinct real display protocol."""
    def __init__(self, config, platform):
        super().__init__(config, platform)
        self.publisher_owners = {}

    def observe(self):
        request_path = (self.journal.get('active') or {}).get('old_request', self.journal['current_request'])
        request = shared_json(self.owned(request_path), 16384)
        root = self.owned(request['receipt_root'])
        if not root.is_relative_to(self.n / 'recordings'): raise ValueError('Recording escaped session')
        job = shared_json(root / 'job.json')
        if job.get('capture_mode') != 'game_decision_text' or job.get('overlay') is not None:
            raise ValueError('Explicit independent text recording required')
        launch = job['launch']; game = Game(job['pid'], job['game_creation_filetime'], launch['creation_date'], launch['pipe'])
        reference = job['decision_text_publisher_receipt']
        bound = publisher.checked(reference)
        if bound != job['decision_text_publisher'] or bound.get('game', {}).get('pid') != game.pid or bound['game']['creation_filetime'] != game.creation_filetime:
            raise ValueError('Actual publisher/Game generation differs')
        live = self.platform.alive(bound['publisher']['pid'], bound['publisher']['creation_filetime'])
        if live: publisher.validate_started(reference)
        state = maybe_json(self.q / 'ROOT-CUMULATIVE-LOOP-STATE.json',262144) or {}
        halt = maybe_json(self.n / ('ROOT-CURRENT-HALT-' + self.c.sdk_prefix.upper() + '.json'),16384) or {}
        pending = state.get('pending_cycle') or {}
        fingerprint = hashlib.sha256(json.dumps(halt,sort_keys=True).encode()).hexdigest()
        cause = None if fingerprint == self.journal.get('last_resumed_halt') else halt.get('error_type')
        verified = False
        if pending.get('stage') == 'auto_verified' and type(pending.get('auto_sequence')) is int:
            row = maybe_json(self.outbox / f"{pending['auto_sequence']:04d}-1-result.json")
            body = self.decode(row) if row else None
            verified = bool(body and body.get('status') in {'executed','observed','readonly_rejected'})
        sdk = SdkGuard(cause == 'RecordingPaused' and halt.get('original_response') is None, cause,
                       (halt.get('original_request') or {}).get('command'),pending.get('stage'),verified)
        obs = maybe_json(root / 'obs-launch.json',16384)
        obs_alive = bool(obs and self.platform.alive(obs['pid'],obs['creation_filetime']))
        terminal = any((root/name).exists() for name in ('failed.json','completed.json','cleanup.json','capture_closed.json'))
        recorder = TextRecorder(request['session_id'], game, reference, root, terminal or not obs_alive or sdk.recording_paused,
                                self.cleanup(root,request['session_id']))
        pins = shared_json(self.n / ('ROOT-ACTUAL-SDK-PROCESSES-PINNED-' + self.c.sdk_prefix.upper() + '.json'),16384)
        if not all(self.platform.alive(p['pid'],p['creation_filetime']) for p in pins['processes']):
            raise ValueError('Same SDK pair is no longer alive')
        if any((self.n/name).exists() for name in ('EXIT-SDK','EXIT-SDK-'+self.c.sdk_prefix.upper(),'REQUEST-ADMISSION-CLOSED')):
            raise ValueError('SDK admission closed')
        return TextObservation(game,self.platform.alive(game.pid,game.creation_filetime),recorder,live,sdk)

    def ensure_publisher(self, old, rid):
        bound = publisher.checked(old.publisher_started)
        if self.platform.alive(bound['publisher']['pid'],bound['publisher']['creation_filetime']):
            publisher.validate_started(old.publisher_started)
            return old.publisher_started
        _, root = self.attempt(rid)
        config_path = root / 'publisher-config.json'
        if not config_path.exists():
            config = publisher.checked(bound['configuration'])
            config.update(state_root=str(root/'publisher'),decision_text_file=str(root/'decision.txt'))
            atomic(config_path,config,new=True)
        started_path = root/'publisher/STARTED.json'
        if started_path.exists():
            reference = publisher.pin(started_path); publisher.validate_started(reference)
            return reference
        if rid not in self.publisher_owners:
            owner = publisher.PublisherOwner(config_path)
            owner.start()  # Existing unknown intent refuses; never a blind retry.
            self.publisher_owners[rid] = owner
        return self.publisher_owners[rid].started()

    def launch_text_segment(self, game, reference, rid):
        active, root = self.attempt(rid)
        request_path = root/'recording-request.json'
        requested = maybe_json(request_path,16384)
        if requested is None:
            if not self.exclusive_controls(): return None
            intent = root/'recording-launch-intent.json'
            if intent.exists(): raise RuntimeError('Recording launch outcome unknown; no second launch')
            old = shared_json(Path(shared_json(active['old_request'])['receipt_root'])/'job.json')
            provider = load_source('new_text_capture_provider_'+rid,self.c.provider_source)
            capture = getattr(provider,'capture',provider)
            if capture.SCHEMA != 'xar.ck3.obs-window-capture.v3': raise ValueError('Explicit new provider schema required')
            bound = publisher.validate_started(reference)
            config = publisher.checked(bound['configuration'])
            atomic(intent,{'game':game.__dict__,'publisher_started':reference},new=True)
            requested = capture.launch_recording(Path(old['profile_path']),self.n/'recordings',old['pid'],old['hwnd'],None,
                launch_receipt=Path(config['game_launch_receipt']['path']),ffprobe=Path(old['ffprobe']),
                placement_receipt=self.c.placement_receipt,decision_publisher_receipt=Path(reference['path']),continuous=True)
            atomic(request_path,requested,new=True)
        receipt_root = self.owned(requested['receipt_root'])
        job = shared_json(receipt_root/'job.json')
        if (requested['session_id'] == shared_json(active['old_request'])['session_id']
                or not receipt_root.is_relative_to(self.n/'recordings') or job.get('receipt_root') != str(receipt_root)
                or job.get('pid') != game.pid or job.get('game_creation_filetime') != game.creation_filetime
                or job.get('decision_text_publisher_receipt') != reference or job.get('capture_mode') != 'game_decision_text'
                or job.get('continuous') is not True or any(job.get(k) is not None for k in ('duration_seconds','max_output_bytes','deadline_utc'))):
            raise ValueError('Actual replacement segment identity/unlimited contract differs')
        active['new_request'] = str(request_path); self.save()
        return SimpleNamespace(session_id=requested['session_id'],game=game,publisher_started=reference,
                               receipt_root=receipt_root,request_receipt=request_path)

    def admit_text_segment(self, segment, rid):
        active, root = self.attempt(rid)
        if active.get('admission') and (root/'control-attach_recording_segment.json').exists():
            path = Path(active['admission']);row = shared_json(path,32768)
            return SimpleNamespace(receipt_path=path,**row)
        job = shared_json(segment.receipt_root/'job.json')
        started = maybe_json(segment.receipt_root/'started.json',32768)
        latest = maybe_json(segment.receipt_root/'recording-latest.json')
        if not started or not latest: return None
        frame = latest['frame']; assets = {}
        for key in ('game','scene'):
            item = frame[key]; source = self.owned(item['path'])
            if not source.is_relative_to(segment.receipt_root): raise ValueError('Actual frame escaped recording')
            data = shared_bytes(source,8*1024**2); digest = hashlib.sha256(data).hexdigest()
            if len(data) != item['bytes'] or digest != item['sha256']: return None
            path = segment.receipt_root / ('text-continuity-'+rid+'-'+digest+'-'+key+'.png')
            if not path.exists():
                with path.open('xb') as stream: stream.write(data)
            assets[key] = {'path':str(path),'bytes':len(data),'sha256':digest}
        frozen = {'at_utc':frame['at_utc'],'mutable_latest_frame':False,**assets}
        row = self.automatic.automatic_text_continuity_admission(job=job,started=started,frame=frozen,session_root=self.n,now_utc=utc())
        tag = hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()[:20]
        path = root/('text-admission-'+tag+'.json')
        if not path.exists(): atomic(path,row,new=True)
        active['admission'] = str(path);self.save()
        return SimpleNamespace(receipt_path=path,**row)

class TextRecoverySupervisor:
    """One bounded poll per stage; each real operation has a retained intent."""
    def __init__(self, adapter): self.adapter = adapter

    def drive(self):
        a = self.adapter; obs = a.observe()
        if not obs.game_alive_exact: return 'blocked_game_generation'
        if not obs.recorder.failed and obs.publisher_alive_exact: return 'healthy'
        g = obs.sdk
        if not (g.recording_paused and g.halt_cause == 'RecordingPaused' and g.original_command == 'full_loop'
                and g.pending_cycle_stage == 'auto_verified' and g.original_auto_executed):
            return 'waiting_exact_post_AUTO_recording_guard'
        rid = hashlib.sha256(f'{obs.game.pid}:{obs.game.creation_filetime}:{obs.recorder.session_id}'.encode()).hexdigest()[:32]
        active, root = a.attempt(rid)
        if not a.exclusive_controls(): return 'waiting_exclusive_local_controls'
        cleanup = obs.recorder.cleanup or a.cleanup_old(obs.recorder,rid)
        if cleanup is None: return 'waiting_normal_old_OBS_cleanup'
        if (cleanup.session_id != obs.recorder.session_id or not cleanup.inputs_unbound or cleanup.actual_exit_code != 0
                or not cleanup.normal_exit_proven or cleanup.forced_process_calls != 0):
            raise ValueError('Exact normal old OBS cleanup required')
        reference = a.ensure_publisher(obs.recorder,rid)
        segment = a.launch_text_segment(obs.game,reference,rid)
        if segment is None: return 'waiting_new_segment'
        admission = a.admit_text_segment(segment,rid)
        if admission is None: return 'waiting_actual_new_Game_text_pixels'
        attached = a.attach_recording_segment(obs.recorder,segment,admission,rid)
        if attached is None: return 'waiting_local_attach'
        if (attached.status != 'same_game_recording_segment_attached' or attached.game != obs.game
                or attached.rpc_calls != 0 or attached.replay_allowed): raise ValueError('Exact zero-RPC no-replay attach required')
        resumed = a.resume_recording_pause(rid)
        if resumed is None: return 'waiting_original_cycle_resume'
        return a.finish_continuation()
