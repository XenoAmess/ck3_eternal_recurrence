package org.xar.ck3.control.admission.deadlinecredit;

import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit one-time capture of existing producers. Default tests never launch Python. */
public final class CaptureDeadlineGolden {
    private CaptureDeadlineGolden() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) {
            throw new IllegalArgumentException("python repository-root input-spec output-golden required");
        }
        ProcessBuilder command = new ProcessBuilder(args[0], "-B", "-c", PROGRAM,
                Path.of(args[1]).toAbsolutePath().toString(), Path.of(args[2]).toAbsolutePath().toString(),
                Path.of(args[3]).toAbsolutePath().toString());
        command.inheritIO();
        Process process = command.start();
        try {
            if (!process.waitFor(30, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                process.waitFor(10, TimeUnit.SECONDS);
                throw new IllegalStateException("existing producer capture exceeded 30-second bound");
            }
            if (process.exitValue() != 0) {
                throw new IllegalStateException("existing producer capture exited " + process.exitValue());
            }
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); }
        }
    }

    private static final String PROGRAM = """
            import copy, hashlib, json, pathlib, sys, types
            from datetime import datetime, timezone
            root, spec_path, output_path = map(pathlib.Path, sys.argv[1:])
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
            sys.path.insert(0, str(root / 'tools'))
            from ck3_live_run_id import current_machine_id
            from xar_autoplayer.bridge.campaign_deadline_v1 import configure_v1, deadline_v1, endpoint_result_v1
            from xar_autoplayer.campaign_score_cadence_v1 import date_to_raw
            spec_bytes = spec_path.read_bytes()
            spec = json.loads(spec_bytes)
            configurations, drivers, rows = {}, {}, []
            for args in spec['configurations']:
                ident = args['id']
                founding = {k: v for k, v in args.items() if k != 'id'}
                founding['start_date_raw'] = date_to_raw(founding['start_date'])
                driver = types.SimpleNamespace()
                summary = configure_v1(driver, **founding)
                configurations[ident] = {'founding': founding, 'configuration': driver._campaign_clock_deadline_v1, 'summary': summary}
                drivers[ident] = driver
            for spec_case in spec['cases']:
                case = copy.deepcopy(spec_case)
                operation = case['operation']
                ident = case.get('configuration_id')
                driver = drivers.get(ident)
                record = {'name': case['name'], 'operation': operation, 'configuration_id': ident}
                try:
                    if operation in {'configure', 'configure_repeat', 'configure_replace'}:
                        founding = copy.deepcopy(configurations[ident]['founding'])
                        founding.update(case.get('changes', {}))
                        record['founding'] = founding
                        record['prior_configuration'] = None if operation == 'configure' else copy.deepcopy(driver._campaign_clock_deadline_v1)
                        actual_driver = types.SimpleNamespace() if operation == 'configure' else copy.deepcopy(driver)
                        output = configure_v1(actual_driver, **founding)
                    elif operation == 'no_configuration':
                        record['starting'] = {'date_raw': None}
                        record['proposed_target_raw'] = None
                        output = deadline_v1(types.SimpleNamespace(), record['starting'], None)
                    else:
                        start = configurations[ident]['founding']['start_date_raw']
                        current = start + int(case['current_day_offset']) * 24 + case.get('current_raw_adjustment', 0)
                        proposed = start + int(case['proposed_day_offset']) * 24 + case.get('proposed_raw_adjustment', 0)
                        starting = {'date_raw': current, **case.get('frame', {})}
                        record['starting'] = starting
                        record['proposed_target_raw'] = proposed
                        output = deadline_v1(driver, starting, proposed)
                        if operation == 'endpoint':
                            record['cap'] = output
                            record['result_step'] = 'life-advance'
                            output = endpoint_result_v1(starting, record['result_step'], output)
                    record['outcome'] = {'status': 'returned', 'value': output}
                except ValueError as error:
                    record['outcome'] = {'status': 'rejected', 'error_type': type(error).__name__, 'error': str(error)}
                rows.append(record)
            source_paths = ['ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_v1.py',
                            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_cadence_v1.py']
            sources = []
            for name in source_paths:
                raw = (root / name).read_bytes()
                sources.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            result = {'schema': 'xar.ck3.java-deadline-producer-golden/v1',
                      'machine_id': current_machine_id(), 'machine_identity_source': 'tools/ck3_live_run_id.py machine',
                      'captured_at_utc': datetime.now(timezone.utc).isoformat(),
                      'input_spec_sha256': hashlib.sha256(spec_bytes).hexdigest(), 'sources': sources,
                      'method': 'actual_existing_producers_no_game_no_runtime_mutation',
                      'configurations': configurations, 'cases': rows,
                      'new_game_rpc': 0, 'ledger_writes': 0, 'saved_day_credit': 0}
            raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\\n').encode('utf-8')
            if len(raw) > 98304:
                raise ValueError('golden byte budget exceeded')
            with output_path.open('xb') as stream:
                stream.write(raw)
            print(json.dumps({'status': 'CAPTURED', 'cases': len(rows), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}))
            """;
}
