package org.xar.ck3.control.wave3.runtime.armysummary;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture; run only by the shared qualified Job coordinator. */
public final class ArmySummaryGoldenCapture {
    private ArmySummaryGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("python repository new-work-directory required"); }
        Path work = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(work)) { throw new IllegalArgumentException("fresh capture work directory required"); }
        Files.createDirectories(work);
        ProcessBuilder builder = new ProcessBuilder(args[0], "-I", "-B", "-c", PROGRAM, args[1], work.toString());
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().remove("PYTEST_ADDOPTS");
        builder.environment().remove("PYTEST_PLUGINS");
        builder.environment().put("XAR_ARMY_RESULT_PERFORMANCE_CASE_OUTPUT",
                work.resolve("existing-serialization-metrics.json").toString());
        Process child = builder.start(); byte[] captured;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = readers.submit(() -> drain(child.getInputStream(), 262_144));
            var stderr = readers.submit(() -> drain(child.getErrorStream(), 16_384));
            try {
                if (!child.waitFor(50, TimeUnit.SECONDS)) { throw new IllegalStateException("Army original capture timeout"); }
                Capture out = stdout.get(2, TimeUnit.SECONDS); Capture err = stderr.get(2, TimeUnit.SECONDS);
                if (child.exitValue() != 0 || out.count() > 262_144 || err.count() > 16_384) {
                    throw new IllegalStateException("Army capture rejected: exit=" + child.exitValue() + ", stdout="
                            + out.count() + ": " + new String(err.bytes(), StandardCharsets.UTF_8));
                }
                captured = out.bytes();
            } finally { if (child.isAlive()) { child.destroyForcibly(); child.waitFor(); } }
        }
        Files.write(work.resolve("producer-golden.json"), captured, StandardOpenOption.CREATE_NEW);
        System.out.println("captured existing Army producers and all three registered routes: " + captured.length + " bytes");
    }
    private static Capture drain(InputStream stream, int limit) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream(limit); byte[] buffer = new byte[8_192];
        int read; long count = 0;
        while ((read = stream.read(buffer)) != -1) {
            int keep = Math.min(read, limit - out.size()); if (keep > 0) { out.write(buffer, 0, keep); }
            count = Math.addExact(count, read);
        }
        return new Capture(out.toByteArray(), count);
    }
    private record Capture(byte[] bytes, long count) { }

    private static final String PROGRAM = """
            import asyncio,contextlib,copy,hashlib,importlib.abc,importlib.machinery,io,json,pathlib,sys
            from collections.abc import Sequence
            from types import CodeType,ModuleType
            from typing import TypedDict
            from datetime import datetime,timezone
            from pathlib import Path
            from unittest.mock import patch
            repo=Path(sys.argv[1]).resolve();root=repo;work=Path(sys.argv[2]);unit=repo/'ck3_autonomous_player/tests/unit'
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(unit),str(repo)]
            if sys.flags.optimize!=0:raise RuntimeError('complete original consumer assertions require optimize=0')
            _interpreter_prefixes = tuple({pathlib.Path(sys.prefix).resolve(), pathlib.Path(sys.base_prefix).resolve()})
            class _SourceRef(TypedDict):
                path: str
                bytes: int
                sha256: str
            _measured_sources: dict[str, _SourceRef] = {}
            def _repo_source(filename: str | pathlib.Path) -> pathlib.Path | None:
                original = pathlib.Path(filename).absolute()
                source = original.resolve()
                if original.is_relative_to(root) and not source.is_relative_to(root) and not any(original.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    raise ValueError('repository import escaped the resolved source root: ' + str(original))
                if not source.is_relative_to(root) or any(source.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    return None
                if source.suffix != '.py':
                    raise ValueError('repository import has unsupported non-source origin: ' + str(source))
                return source
            def _measure_source(source: pathlib.Path, raw: bytes | None = None) -> _SourceRef:
                content = source.read_bytes() if raw is None else raw
                return {'path': source.relative_to(root).as_posix(), 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            def _record_source(source: pathlib.Path, raw: bytes) -> None:
                measured = _measure_source(source, raw)
                previous = _measured_sources.setdefault(measured['path'], measured)
                if previous != measured:
                    raise ValueError('repository source changed before a repeated module execution: ' + measured['path'])
            def _repo_modules() -> set[str]:
                sources: set[str] = set()
                for module in tuple(sys.modules.values()):
                    filename = getattr(module, '__file__', None)
                    if isinstance(filename, str):
                        source = _repo_source(filename)
                        if source is not None:
                            sources.add(source.relative_to(root).as_posix())
                return sources
            _initial_repo_sources = _repo_modules()
            if _initial_repo_sources:
                raise ValueError('repository modules were loaded before source observation: ' + str(sorted(_initial_repo_sources)[:8]))
            class _MeasuredRepoSourceLoader(importlib.machinery.SourceFileLoader):
                def get_code(self, fullname: str) -> CodeType:
                    source = _repo_source(self.get_filename(fullname))
                    if source is None:
                        raise ValueError('measured loader escaped repository source scope')
                    raw = source.read_bytes()
                    _record_source(source, raw)
                    # Compile exactly the measured source bytes; never accept a cached pyc.
                    return self.source_to_code(raw, str(source))
            class _RepoSourceObserver(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname: str, path: Sequence[str] | None = None,
                              target: ModuleType | None = None) -> importlib.machinery.ModuleSpec | None:
                    spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
                    if spec is None or spec.origin is None or spec.origin in ('built-in', 'frozen'):
                        return None
                    source = _repo_source(spec.origin)
                    if source is None:
                        return None
                    if not isinstance(spec.loader, importlib.machinery.SourceFileLoader):
                        raise ValueError('repository source has an unsupported loader: ' + fullname)
                    spec.loader = _MeasuredRepoSourceLoader(fullname, str(source))
                    return spec
            sys.meta_path.insert(sys.meta_path.index(importlib.machinery.PathFinder), _RepoSourceObserver())
            def _verify_sources(stage: str) -> int:
                loaded = _repo_modules()
                unrecorded = loaded.difference(_measured_sources)
                if unrecorded:
                    raise ValueError(stage + ' has unrecorded repository source modules: ' + str(sorted(unrecorded)[:8]))
                for name, before_ref in tuple(_measured_sources.items()):
                    if _measure_source(root / name) != before_ref:
                        raise ValueError(stage + ' repository source changed: ' + name)
                return len(loaded)
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/'+name for name in [
                'army_strengths_mcp_result.py','army_native_timing_summary_v1.py','army_strengths_profile_contract.py',
                'mcp_server.py','service.py','native_driver.py','war_contract.py']]
            paths+=['ck3_autonomous_player/tests/unit/'+name for name in [
                'test_army_strengths_mcp_result_serialization_performance.py',
                'test_army_profile_mcp_compact_regression.py','test_army_auto_scalar_projection_v1.py']]
            from tools.ck3_live_run_id import current_machine_id
            machine=current_machine_id()
            from xar_autoplayer.bridge.army_strengths_mcp_result import build_army_strengths_mcp_result as direct,build_army_auto_turn_mcp_result as auto
            from test_army_profile_mcp_compact_regression import _registered_army_server
            _after_imports_repo_sources=_verify_sources('after actual Army fixture imports')
            row_fields=('status','army_id','native_carmy_id','regiment_count','current_soldiers','maximum_soldiers',
                'ai_base_power_raw','ai_base_power_scale','current_supply_raw','current_supply_scale',
                'current_attrition_fraction_raw','current_attrition_fraction_scale','unavailable_reason')
            fields=('accepted','status','query_sequence','army_strengths_profile','army_observed_phase_coverage',
                'source','queried_revision','queried_native_revision','army_ids','army_native_timing_v1')
            def projection(payload):
                out={key:copy.deepcopy(payload[key]) for key in fields if key in payload}
                if isinstance(out.get('source'),dict):out['source']={key:out['source'][key] for key in ('revision','native_revision') if key in out['source']}
                out['army_strengths']=[{key:copy.deepcopy(row[key]) for key in row_fields if key in row} for row in payload['army_strengths']]
                return out
            def auto_projection(payload):
                return {'status':payload.get('status'),'selected_step':payload.get('selected_step'),
                    'plan':{key:payload['plan'].get(key) for key in ('selected_step','phase')},'result':projection(payload['result'])}
            def wire(value):
                observed=json.loads(value.model_dump_json(by_alias=True,exclude_none=True))
                if set(observed)!={'content','structuredContent','isError','resultType'} or observed['resultType']!='complete':
                    raise RuntimeError('actual installed MCP complete four-field result contract changed')
                return observed
            cases=[]
            for route in ('direct','execute','auto','full'):
                with _registered_army_server() as (server,driver,before,requests):
                    if route=='auto':
                        with patch('xar_autoplayer.bridge.mcp_server.build_army_auto_turn_mcp_result',wraps=auto) as spy,patch(
                            'xar_autoplayer.bridge.service.choose_one_life_turn',return_value={
                            'selected_step':'query-army-strengths-v1','phase':'synthetic_army_query'}):
                            observed=asyncio.run(server.call_tool('ck3_auto_turn',{}))
                        payload=auto_projection(spy.call_args.args[0]);kind='auto';replayed=auto(payload)
                    else:
                        with patch('xar_autoplayer.bridge.mcp_server.build_army_strengths_mcp_result',wraps=direct) as spy:
                            if route=='execute':observed=asyncio.run(server.call_tool('ck3_execute_step',{
                                'step':'query-army-strengths-v1','expected_revision':before['revision']}))
                            else:
                                arguments={'army_ids':[82,81],'expected_revision':before['revision']}
                                if route=='full':arguments['profile']='observed_history_full_v1'
                                observed=asyncio.run(server.call_tool('ck3_query_army_strengths',arguments))
                        payload=projection(spy.call_args.args[0]);kind='query';replayed=direct(payload)
                    if wire(replayed)!=wire(observed):raise RuntimeError('consumed projection differs from registered result')
                    cases.append({'name':'registered_'+route,'kind':kind,'input_json':json.dumps(payload,ensure_ascii=False,separators=(',',':')),'expected':wire(observed),
                        'registered_native_requests':len(requests),'native_game_calls':0})
            base=json.loads(cases[0]['input_json']);valid={'read_total_ns':100,'owner_query_ns':80,'baseline_read_ns':60,'rich_attach_ns':5,'serialize_ns':10}
            mutations=[('timing_valid',{'army_native_timing_v1':valid}),
                ('timing_missing',{}),('timing_null',{'army_native_timing_v1':None}),
                ('timing_empty',{'army_native_timing_v1':{}}),
                ('timing_extra',{'army_native_timing_v1':{**valid,'extension':0}}),
                ('timing_bool',{'army_native_timing_v1':{**valid,'baseline_read_ns':True}}),
                ('timing_float',{'army_native_timing_v1':{**valid,'owner_query_ns':80.0}}),
                ('timing_negative',{'army_native_timing_v1':{**valid,'serialize_ns':-1}}),
                ('timing_owner_over_total',{'army_native_timing_v1':{**valid,'owner_query_ns':101}}),
                ('timing_child_over_owner',{'army_native_timing_v1':{**valid,'rich_attach_ns':81}}),
                ('timing_serialize_independent',{'army_native_timing_v1':{**valid,'serialize_ns':1000}}),
                ('ids_null',{'army_ids':None}),('ids_empty',{'army_ids':[]}),
                ('ids_order_duplicates',{'army_ids':[81,82,81,None]}),
                ('source_empty_no_fallback',{'source':{},'queried_revision':99,'queried_native_revision':98}),
                ('source_null_fallback',{'source':None,'queried_revision':99,'queried_native_revision':98}),
                ('source_nondict_fallback',{'source':False,'queried_revision':99,'queried_native_revision':98})]
            for name,changes in mutations:
                payload={**copy.deepcopy(base),**changes}
                cases.append({'name':name,'kind':'query','input_json':json.dumps(payload,ensure_ascii=False,separators=(',',':')),'expected':wire(direct(payload))})
            for name,payload in [('minimal_empty',{'army_strengths':[]}),('missing_row_members',{'army_strengths':[{}]}),
                ('false_acceptance',{'accepted':False,'status':'unavailable','army_strengths':[]})]:
                cases.append({'name':name,'kind':'query','input_json':json.dumps(payload,ensure_ascii=False,separators=(',',':')),'expected':wire(direct(payload))})
            import pytest
            class Outcomes:
                passed=0;failed=0;skipped=0
                def pytest_runtest_logreport(self,report):
                    if report.skipped:self.skipped+=1
                    elif report.when=='call':
                        if report.passed:self.passed+=1
                        else:self.failed+=1
            outcomes=Outcomes();test_names=paths[-3:]
            test_stdout=io.StringIO();test_stderr=io.StringIO()
            with contextlib.redirect_stdout(test_stdout),contextlib.redirect_stderr(test_stderr):
                code=pytest.main(['-q','--assert=plain','-p','no:cacheprovider','--basetemp',str(work/'pytest-tmp'),*[str(repo/name) for name in test_names]],plugins=[outcomes])
            for label,stream in [('stdout',test_stdout),('stderr',test_stderr)]:
                diagnostic=stream.getvalue().encode('utf-8')
                with (work/('original-consumer-'+label+'.log')).open('xb') as log:log.write(diagnostic[:32768])
                if len(diagnostic)>32768:raise RuntimeError(f'original consumer {label} log exceeds32768 bytes: {len(diagnostic)}')
            if code!=0 or outcomes.failed or outcomes.skipped or outcomes.passed!=17:
                raise RuntimeError(f'existing consumer closure failed code={code} pass={outcomes.passed} fail={outcomes.failed} skip={outcomes.skipped}')
            _after_suite_repo_sources=_verify_sources('after all three complete original consumer suites')
            required_sources=set(paths)|{'tools/ck3_live_run_id.py','ck3_autonomous_player/tests/unit/test_native_bridge_driver.py',
                'ck3_autonomous_player/tests/unit/test_army_profile_cache_regression.py'}
            if not required_sources.issubset(_measured_sources):raise RuntimeError('required producer/consumer fixture source was not actually observed')
            source_refs=sorted(_measured_sources.values(),key=lambda item:item['path'])
            document={'schema':'xar.java.army-mcp-summary-producer-golden/v1','machine_id':machine,
                'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                'scope':'unchanged actual builders; consumed-field inputs replay equal all three actual registered MCP routes and explicit full route; fake native endpoint only; no Game qualification',
                'cases':cases,'original_consumer_tests':{'passed':outcomes.passed,'failed':outcomes.failed,'skipped':outcomes.skipped},
                'source_provenance':{'schema':'xar.ck3.measured-repo-import-closure/v1',
                    'scope':'repo-python-excluding-interpreter-prefixes/v1','initial_repo_sources':0,
                    'after_imports_repo_sources':_after_imports_repo_sources,'after_suite_repo_sources':_after_suite_repo_sources,
                    'recorded_repo_sources':len(_measured_sources),'source_pre_post_equal':True,'unrecorded_repo_sources':[]},
                'source_refs':source_refs,'consumer_assertions':'plain-source-assertions-optimize0',
                'game_calls':0,'new_save_days_credit':0,'runtime_cutover':False}
            output=(json.dumps(document,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\\n').encode()
            if len(output)>262144:raise RuntimeError('Army golden exceeds finite byte budget')
            sys.stdout.buffer.write(output)
            """;
}
