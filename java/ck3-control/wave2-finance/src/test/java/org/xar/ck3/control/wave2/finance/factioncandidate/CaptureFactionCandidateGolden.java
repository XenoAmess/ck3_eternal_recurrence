package org.xar.ck3.control.wave2.finance.factioncandidate;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** One-time existing producer capture; default JUnit never executes Python. */
public final class CaptureFactionCandidateGolden {
    private CaptureFactionCandidateGolden() { }
    private static final String ORACLE = """
        from __future__ import annotations
        import copy
        import datetime
        import hashlib
        import inspect
        import json
        from pathlib import Path
        import runpy
        import sys
        ROOT = Path(sys.argv[1])
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
        from xar_autoplayer.faction_gift_formal_candidate_v1 import latest_same_frame_faction_root_v1, choose_private_faction_gift_candidate_v1
        SOURCE = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/faction_gift_formal_candidate_v1.py'
        TEST = ROOT / 'ck3_autonomous_player/tests/unit/test_faction_gift_formal_candidate_v1.py'
        scope = runpy.run_path(str(TEST))
        executed = []
        for name, function in sorted(scope.items()):
            if name.startswith('test_') and callable(function) and not inspect.signature(function).parameters:
                function()
                executed.append(name)
        root_base = {'snapshot': scope['snapshot'](), 'history': scope['history'](1)}
        candidate_base = {'snapshot': scope['snapshot'](), 'root': scope['root'](1),
                          'private_result': scope['private_result'](), 'minimum_gold_reserve_raw': 10000000}
        cases = []
        def add(name, operation, request):
            request = copy.deepcopy(request)
            if operation == 'root':
                expected = latest_same_frame_faction_root_v1(request['snapshot'], request['history'])
            else:
                expected = choose_private_faction_gift_candidate_v1(request['snapshot'], request['root'],
                    request['private_result'], minimum_gold_reserve_raw=request['minimum_gold_reserve_raw'])
            cases.append({'name': name, 'operation': operation, 'input': request, 'expected': expected})
        def mutate(name, operation, change):
            request = copy.deepcopy(root_base if operation == 'root' else candidate_base)
            change(request)
            add(name, operation, request)
        def context(request):
            return request['history'][-1]['result']['campaign_root_context']
        def native(request):
            return request['private_result']['native']
        add('latest-root-targeting-present', 'root', root_base)
        mutate('latest-root-known-empty', 'root', lambda request: context(request).update({'player_targeting_faction_count': 0}))
        for field in ('paused', 'map_ready'):
            mutate('snapshot-not-' + field, 'root', lambda request, field=field: request['snapshot'].update({field: False}))
        mutate('snapshot-actor-not-alive', 'root', lambda request: request['snapshot']['played_character'].update({'alive': False}))
        mutate('snapshot-revision-bool', 'root', lambda request: request['snapshot'].update({'native_revision': True}))
        mutate('snapshot-revision-float', 'root', lambda request: request['snapshot'].update({'native_revision': 412.0}))
        mutate('history-empty', 'root', lambda request: request.update({'history': []}))
        mutate('history-result-failed', 'root', lambda request: request['history'][-1].update({'ok': False}))
        mutate('history-other-command', 'root', lambda request: request['history'][-1].update({'command': 'other-query'}))
        mutate('history-context-unavailable', 'root', lambda request: context(request).update({'status': 'unavailable'}))
        mutate('root-government-out-of-scope', 'root', lambda request: context(request)['government'].update({'key': 'clan_government'}))
        for value, name in ((None, 'null'), (True, 'bool'), (1.0, 'float'), (-1, 'negative')):
            mutate('root-count-' + name, 'root', lambda request, value=value: context(request).update({'player_targeting_faction_count': value}))
        mutate('root-direct-list-null', 'root', lambda request: context(request).update({'direct_landed_vassal_character_ids': None}))
        mutate('root-direct-list-duplicate', 'root', lambda request: context(request).update({'direct_landed_vassal_character_ids': [33011, 33011]}))
        mutate('root-direct-list-bool', 'root', lambda request: context(request).update({'direct_landed_vassal_character_ids': [True]}))
        mutate('root-stale-revision', 'root', lambda request: context(request).update({'snapshot_revision': 413}))
        request = copy.deepcopy(root_base)
        latest = copy.deepcopy(request['history'][0])
        latest['result']['campaign_root_context']['player_targeting_faction_count'] = 0
        request['history'].append(latest)
        add('latest-current-root-wins', 'root', request)
        request = copy.deepcopy(root_base)
        latest = copy.deepcopy(request['history'][0])
        latest['result']['campaign_root_context']['snapshot_revision'] = 413
        request['history'].append(latest)
        add('stale-root-does-not-hide-current', 'root', request)
        add('private-native-selected', 'candidate', candidate_base)
        mutate('private-no-targeting-vector', 'candidate', lambda request: request['root'].update({'player_targeting_faction_count': 0}))
        mutate('private-root-count-bool', 'candidate', lambda request: request['root'].update({'player_targeting_faction_count': True}))
        for field, value in (('step', 'other-private-query'), ('accepted', False), ('private_build', False), ('advertised', True)):
            mutate('private-envelope-' + field, 'candidate', lambda request, field=field, value=value: request['private_result'].update({field: value}))
        mutate('private-no-eligible-direct-vassal', 'candidate', lambda request: request['private_result'].update({'status': 'no_eligible_direct_vassal', 'native': None}))
        mutate('private-status-nonterminal', 'candidate', lambda request: request['private_result'].update({'status': 'known_empty'}))
        mutate('private-native-object-missing', 'candidate', lambda request: request['private_result'].pop('native'))
        mutate('private-native-failure-flags', 'candidate', lambda request: native(request).update({'failure_flags': 1}))
        mutate('private-native-wrong-completion', 'candidate', lambda request: native(request).update({'completion': 'pending'}))
        mutate('private-observation-null', 'candidate', lambda request: native(request).update({'observation': None}))
        mutate('private-recipient-outside-direct-list', 'candidate', lambda request: request['root'].update({'direct_landed_vassal_character_ids': [999]}))
        mutate('private-native-source-mismatch', 'candidate', lambda request: native(request).update({'source_faction_id': 772}))
        mutate('private-native-recipient-mismatch', 'candidate', lambda request: native(request).update({'recipient_character_id': 33012}))
        for field in ('snapshot_revision', 'observed_date_raw', 'player_character_id'):
            mutate('private-observation-frame-' + field, 'candidate',
                   lambda request, field=field: native(request)['observation'].update({field: native(request)['observation'][field] + 1}))
        mutate('private-root-frame-mismatch', 'candidate', lambda request: request['root'].update({'snapshot_revision': 413}))
        mutate('private-metric-unknown-stays-unavailable', 'candidate',
               lambda request: native(request)['observation'].update({'source_faction_discontent_raw': None}))
        mutate('private-legal-preview-denial', 'candidate',
               lambda request: native(request)['observation']['gift_preview'].update({'interaction_legal': False}))
        mutate('private-budget-reject', 'candidate', lambda request: request.update({'minimum_gold_reserve_raw': 20000000}))
        mutate('private-reserve-exact-boundary', 'candidate', lambda request: request.update({'minimum_gold_reserve_raw': 17500000}))
        mutate('private-reserve-bool', 'candidate', lambda request: request.update({'minimum_gold_reserve_raw': True}))
        mutate('private-reserve-float', 'candidate', lambda request: request.update({'minimum_gold_reserve_raw': 0.0}))
        mutate('private-status-known-no-legal-still-evaluates-preview', 'candidate',
               lambda request: request['private_result'].update({'status': 'no_legal_candidate'}))
        def ref(path):
            data = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        document = {'schema': 'xar.ck3.java.faction-candidate-producer-golden/v1',
            'capture': {'machine_id': 'xenoamess-full-tower-eb9d2c1186',
                        'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'method': 'unchanged original root selector and private-candidate producer on original committed unit fixtures; synthetic offline inputs only',
                        'native_rpc_count': 0, 'ledger_writes': 0},
            'producer': ref(SOURCE), 'gift_policy_producer': ref(ROOT / 'ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py'),
            'fixture_test': ref(TEST), 'original_zero_argument_tests_executed': executed, 'cases': cases}
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 95000:
            raise ValueError('golden output exceeds 95000 byte allowance')
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases), 'bytes': len(encoded),
                          'sha256': hashlib.sha256(encoded).hexdigest(), 'zero_argument_tests': len(executed),
                          'native_rpc_count': 0, 'ledger_writes': 0}))
        
        """;
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("source-root python output-path required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("capture requires new output");
        ProcessBuilder command = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", ORACLE, root.toString(), output.toString());
        command.directory(root.toFile());
        command.environment().put("OPENBLAS_NUM_THREADS", "1");
        command.environment().put("OMP_NUM_THREADS", "1");
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        command.environment().put("TEMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.environment().put("TMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.redirectErrorStream(true);
        Process child = command.start();
        byte[] log = child.getInputStream().readNBytes(65_537);
        int exit = child.waitFor();
        if (log.length > 65_536) throw new IllegalStateException("capture log limit");
        System.out.print(new String(log, StandardCharsets.UTF_8));
        if (exit != 0) throw new IllegalStateException("original producer exit " + exit);
        if (!Files.isRegularFile(output) || Files.size(output) > 95_000) throw new IllegalStateException("capture output limit");
    }
}

