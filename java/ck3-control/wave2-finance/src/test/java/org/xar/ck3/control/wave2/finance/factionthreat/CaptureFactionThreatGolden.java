package org.xar.ck3.control.wave2.finance.factionthreat;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** One-time original-producer capture. Default JUnit never launches Python. */
public final class CaptureFactionThreatGolden {
    private CaptureFactionThreatGolden() { }
    private static final String ORACLE = """
        from __future__ import annotations
        
        import copy
        import datetime
        import hashlib
        import json
        from pathlib import Path
        import sys
        
        ROOT = Path(sys.argv[1])
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
        from xar_autoplayer.faction_threat_response_inputs_v1 import observe_faction_gift_stock_threat_v1
        from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
        
        SOURCE = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/faction_threat_response_inputs_v1.py'
        ACTUAL = ROOT / 'ck3_autonomous_player/tests/unit/fixtures/faction_gift_actual_0515_0531_projection.json'
        projection = json.loads(ACTUAL.read_text(encoding='utf-8'))
        actual = projection['planning_source_frame']
        snapshot = {'snapshot_id': actual['snapshot_id'], 'revision': actual['revision'],
                    'native_revision': actual['native_revision'], 'date_raw': actual['date_raw'],
                    'played_character': {'character_id': actual['actor_character_id'], 'alive': True},
                    'paused': True, 'map_ready': True, 'extension_retained': {'not_a_decision_input': True}}
        row = copy.deepcopy(projection['war_entry_faction_context']['factions'][0])
        row.update({'target_character_id': actual['actor_character_id'], 'leader_character_id': 33946,
                    'character_member_ids': [33946]})
        raw = {'status': 'available', 'snapshot_revision': actual['native_revision'],
               'date_raw': actual['date_raw'], 'player_character_id': actual['actor_character_id'],
               'readiness': {'targeting_rows_ready': True, 'stock_dangerous_predicate_ready': True,
                             'same_frame_ready': True, 'extension': 'declared SDK projection'},
               'targeting_factions': [row]}
        base = {'snapshot': snapshot, 'history': [{'command': 'query-player-faction-alerts-v1', 'ok': True,
                'result': {'player_faction_alerts': raw, 'additional_result': 'retained'}}],
                'candidate': {'status': projection['actual_candidate']['status'],
                              'choice': {field: projection['actual_candidate']['choice'][field]
                                         for field in ('source_faction_id', 'recipient_character_id')},
                              'additional_candidate': 'declared projection of existing candidate'},
                'expected_revision': actual['revision']}
        cases = []
        
        class ExistingObserver:
            def __init__(self, specification):
                self.specification = specification
                self.calls = []
        
            def capabilities(self):
                return {'bridge_capabilities': ['game.command.query-player-faction-alerts-v1']
                        if self.specification.get('supports', False) else []}
        
            def execute_step(self, step, *, expected_revision):
                self.calls.append({'step': step, 'expected_revision': expected_revision})
                if self.specification.get('error') == 'bridge':
                    raise BridgeUnavailableError(self.specification['message'])
                if self.specification.get('error') == 'unsupported':
                    raise UnsupportedStepError(self.specification['message'])
                return copy.deepcopy(self.specification.get('result'))
        
        def add(name, request=None, driver=None):
            request = copy.deepcopy(base if request is None else request)
            specification = copy.deepcopy({'supports': False} if driver is None else driver)
            observer = ExistingObserver(specification)
            expected = observe_faction_gift_stock_threat_v1(observer, snapshot=request['snapshot'],
                history=request['history'], candidate=request['candidate'], expected_revision=request['expected_revision'])
            cases.append({'name': name, 'input': request, 'driver': specification,
                          'expected': expected, 'expected_observer_calls': observer.calls})
        
        def mutate(name, function, *, reader=None):
            request = copy.deepcopy(base)
            function(request)
            add(name, request, reader)
        
        def alert(request):
            return request['history'][-1]['result']['player_faction_alerts']
        
        add('actual-watch-observation-with-explicit-synthetic-envelope')
        mutate('matching-stock-danger', lambda request: alert(request)['targeting_factions'][0].update(
               {'dangerous_by_stock_rule': True, 'extension': {'retained_exactly': [None, False, 2 ** 63]}}))
        mutate('at-war-never-authorizes-peaceful-gift', lambda request: alert(request)['targeting_factions'][0].update(
               {'dangerous_by_stock_rule': True, 'faction_at_war': True}))
        mutate('missing-danger-is-not-false-evidence', lambda request: alert(request)['targeting_factions'][0].pop('dangerous_by_stock_rule'))
        mutate('null-danger-is-unknown', lambda request: alert(request)['targeting_factions'][0].update({'dangerous_by_stock_rule': None}))
        mutate('missing-war-is-not-peace', lambda request: alert(request)['targeting_factions'][0].pop('faction_at_war'))
        mutate('unselected-no-query', lambda request: request['candidate'].update({'status': 'unavailable'}))
        mutate('missing-choice-no-query', lambda request: request['candidate'].pop('choice'))
        mutate('empty-history-missing-capability', lambda request: request.update({'history': []}))
        reader = {'supports': True, 'result': {'player_faction_alerts': raw}}
        mutate('one-existing-observer-read', lambda request: request.update({'history': []}), reader=reader)
        for kind in ('bridge', 'unsupported'):
            mutate('existing-observer-' + kind, lambda request: request.update({'history': []}),
                   reader={'supports': True, 'error': kind, 'message': 'retained ' + kind + ' observation failure'})
        mutate('observer-non-object-result', lambda request: request.update({'history': []}),
               reader={'supports': True, 'result': None})
        for field in ('snapshot_revision', 'date_raw', 'player_character_id'):
            mutate('stale-history-' + field, lambda request, field=field: alert(request).update({field: alert(request)[field] + 1}))
        for field in ('targeting_rows_ready', 'stock_dangerous_predicate_ready', 'same_frame_ready'):
            mutate('readiness-false-' + field, lambda request, field=field: alert(request)['readiness'].update({field: False}))
            mutate('readiness-null-' + field, lambda request, field=field: alert(request)['readiness'].update({field: None}))
        mutate('same-frame-unavailable-not-bypassed', lambda request: alert(request).update({'status': 'unavailable'}))
        mutate('readiness-container-missing', lambda request: alert(request).pop('readiness'))
        mutate('targeting-rows-missing', lambda request: alert(request).pop('targeting_factions'))
        mutate('targeting-rows-null', lambda request: alert(request).update({'targeting_factions': None}))
        mutate('targeting-rows-not-array', lambda request: alert(request).update({'targeting_factions': 'unavailable'}))
        mutate('targeting-empty', lambda request: alert(request).update({'targeting_factions': []}))
        mutate('unmatched-source', lambda request: alert(request)['targeting_factions'][0].update({'faction_id': 55}))
        mutate('duplicate-source-not-unique', lambda request: alert(request)['targeting_factions'].append(
               copy.deepcopy(alert(request)['targeting_factions'][0])))
        mutate('wrong-target', lambda request: alert(request)['targeting_factions'][0].update({'target_character_id': 999}))
        mutate('wrong-recipient', lambda request: alert(request)['targeting_factions'][0].update(
               {'leader_character_id': 999, 'character_member_ids': [999]}))
        mutate('member-without-leader', lambda request: alert(request)['targeting_factions'][0].update({'leader_character_id': None}))
        mutate('leader-without-member-list', lambda request: alert(request)['targeting_factions'][0].pop('character_member_ids'))
        mutate('non-object-unrelated-row-ignored', lambda request: alert(request)['targeting_factions'].insert(0, None))
        request = copy.deepcopy(base)
        older = copy.deepcopy(request['history'][0])
        older['result']['player_faction_alerts']['targeting_factions'][0]['dangerous_by_stock_rule'] = True
        request['history'].insert(0, older)
        add('latest-same-frame-watch-wins', request)
        request = copy.deepcopy(base)
        newer = copy.deepcopy(request['history'][0])
        newer['result']['player_faction_alerts']['status'] = 'unavailable'
        request['history'].append(newer)
        add('latest-same-frame-unavailable-wins', request)
        request = copy.deepcopy(base)
        newer = copy.deepcopy(request['history'][0])
        newer['result']['player_faction_alerts']['snapshot_revision'] += 1
        request['history'].append(newer)
        add('latest-stale-does-not-hide-prior-current', request)
        request = copy.deepcopy(base)
        request['history'][0]['ok'] = False
        add('failed-history-result-not-reused', request, reader)
        request = copy.deepcopy(base)
        request['history'][0]['command'] = 'other-query'
        add('other-command-not-reused', request, reader)
        
        def ref(path):
            raw_bytes = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw_bytes),
                    'sha256': hashlib.sha256(raw_bytes).hexdigest()}
        
        document = {'schema': 'xar.ck3.java.faction-threat-producer-golden/v1',
                    'capture': {'machine_id': 'xenoamess-full-tower-eb9d2c1186',
                                'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'method': 'unchanged observe_faction_gift_stock_threat_v1 with retained historical narrow input and explicitly synthetic observer/same-frame envelope',
                                'native_rpc_count': 0, 'ledger_writes': 0, 'historical_machine_id': 'unknown',
                                'boundary': projection['fixture_boundary']},
                    'producer': ref(SOURCE), 'historical_projection': ref(ACTUAL), 'cases': cases}
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 110_000:
            raise ValueError('bounded golden estimate exceeded')
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases),
                          'bytes': len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
                          'native_rpc_count': 0, 'ledger_writes': 0}))
        
        """;

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("source-root python output-path required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("capture output must be new");
        ProcessBuilder command = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", ORACLE,
                root.toString(), output.toString());
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
        if (log.length > 65_536) throw new IllegalStateException("capture diagnostic limit");
        System.out.print(new String(log, StandardCharsets.UTF_8));
        if (exit != 0) throw new IllegalStateException("original producer capture exit " + exit);
        if (!Files.isRegularFile(output) || Files.size(output) > 110_000) {
            throw new IllegalStateException("capture output unavailable or over budget");
        }
    }
}

