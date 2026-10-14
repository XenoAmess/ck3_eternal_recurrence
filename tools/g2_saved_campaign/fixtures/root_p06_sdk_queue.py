"""Immutable offline fixture: actual qualified queue control methods, no queue main."""
class ExistingQueueControls:
    def attach_recording_segment(self, request, path):
        """Local attachment only: no OBS/CK3 action and no action replay."""
        from root_continuous_segment_auto import verify_segment
        arguments = request.get('arguments', {})
        if not isinstance(arguments, dict) or set(arguments) != {'recording_job_root', 'first_frame_admission', 'recording_request_receipt'}:
            raise ValueError('exact reviewed same-Game segment paths required')
        root = Path(arguments['recording_job_root']).resolve()
        first = Path(arguments['first_frame_admission']).resolve()
        job, started, reviewed = verify_segment(N, R, self.launch, root, first, read, aware, now)
        requested_path = Path(arguments['recording_request_receipt']).resolve()
        if not requested_path.is_relative_to(N):
            raise ValueError('new recording worker request receipt escaped attempt')
        requested = read(requested_path, 16384)
        if requested.get('session_id') != job.get('session_id') or Path(requested.get('receipt_root', '')).resolve() != root or type(requested.get('worker_pid')) is not int or (requested['worker_pid'] <= 0):
            raise ValueError("new recorder's actual original worker request binding differs")
        if root == self.record_job:
            raise ValueError('replacement must be a distinct recorder session')
        sequence = request.get('sequence')
        if type(sequence) is not int or sequence != self.next_sequence:
            raise ValueError('one current unused sequential segment control required')
        old = self.record_job
        self.next_sequence += 1
        atomic(N / 'NEXT-SEQUENCE-P06.json', {'next_sequence': self.next_sequence, 'at_utc': now().isoformat()}, replace=True, limit=16384)
        self.record_job, self.job, self.record_started, self.first = (root, job, started, reviewed)
        self.args.recording_job_root = root
        self.args.first_frame_admission = first
        self.record_last_bytes, self.record_last_growth = (None, time.monotonic())
        self.recording_paused = False
        atomic(N / 'ROOT-CURRENT-OBS-RECORDING-REQUESTED.json', requested, replace=True, limit=16384)
        atomic(OUTBOX / path.name, {'request': request, 'result': {'is_error': False, 'structured_content': {'status': 'same_game_recording_segment_attached', 'old_job': str(old), 'new_job': str(root), 'game_pid': self.launch['pid'], 'rpc_calls': 0, 'halted_original_response_preserved': self.halted is not None, 'replay_allowed': False}}}, limit=16384)

    async def resume_recording_pause(self, session, request, path):
        """Only a local guard pause before RPC, never a rejected/unknown action."""
        original = self.halted
        state = getattr(self, 'full_loop_state', None)
        if request.get('arguments', {}) != {} or not isinstance(original, dict) or original.get('row') is not None or (original.get('response') is not None) or (original.get('request', {}).get('command') != 'full_loop') or (not isinstance(state, dict)) or (not isinstance(state.get('pending_cycle'), dict)) or (state['pending_cycle'].get('stage') != 'auto_verified'):
            raise ValueError('only retained auto_verified full_loop with zero-RPC recording guard pause can resume')
        if getattr(self, 'halt_cause', {}).get('error_type') != 'RecordingPaused':
            raise ValueError('first halt was not an exact recording guard pause')
        self.guard()
        sequence = self.consume_sequence(request)
        atomic(Q / f'RECORDING-PAUSE-RESUMED-{sequence:04d}.json', {'original_control': original['request'], 'pending_global_turn': state['pending_cycle']['global_turn'], 'next_step': 'new_readonly_metrics_then_settle_original_cycle', 'new_RPC_calls': 0, 'original_AUTO_replayed': False}, limit=16384)
        self.halted = self.current_attempt = self.held_control = None
        atomic(OUTBOX / path.name, {'request': request, 'result': {'is_error': False, 'structured_content': {'status': 'recording_guard_pause_resumed', 'original_AUTO_replayed': False, 'pending_cycle_preserved': True}}}, limit=16384)
