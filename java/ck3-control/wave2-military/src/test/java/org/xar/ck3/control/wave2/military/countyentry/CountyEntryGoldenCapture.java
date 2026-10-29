package org.xar.ck3.control.wave2.military.countyentry;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** One-shot original-producer capture, scheduled by the shared bounded execution owner. */
public final class CountyEntryGoldenCapture {
    private CountyEntryGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) throw new IllegalArgumentException("repository python-exe fresh-output machine-id required");
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(), output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("fresh output required");
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONPATH", repository + File.pathSeparator + repository.resolve("ck3_autonomous_player/src")
                + File.pathSeparator + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(90_113); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                throw new IOException("original county producer capture timeout");
            }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("county capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 90_112)
            throw new IOException("county capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " county producer bytes to " + output);
    }
    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,contextlib
            from pathlib import Path
            import pytest
            from xar_autoplayer.bridge.war_contract import normalize_army_strengths
            from xar_autoplayer.bridge.army_county_entry_inputs_contract import normalize_army_county_entry_inputs_v1
            from xar_autoplayer.bridge.army_current_unit_arrival_prestore_disembark_write_projection import project_current_unit_arrival_prestore_disembark_write_v1
            from test_army_county_entry_inputs_contract import row
            from test_army_county_entry_multiplier_floor_inputs_contract import row as floor_row
            from test_county_entry_route_risk_projection import sample
            root=Path(sys.argv[1]); machine=sys.argv[2]
            test_paths=['ck3_autonomous_player/tests/unit/test_army_county_entry_inputs_contract.py','ck3_autonomous_player/tests/unit/test_army_county_entry_multiplier_floor_inputs_contract.py','ck3_autonomous_player/tests/unit/test_county_entry_route_risk_projection.py']
            reports=[]; finished=[]
            class Reports:
                def pytest_runtest_logreport(self,report): reports.append(report)
                def pytest_runtest_logfinish(self,nodeid,location): finished.append(nodeid)
            with contextlib.redirect_stdout(sys.stderr):
                code=pytest.main(['-q','-p','no:cacheprovider',*test_paths],plugins=[Reports()])
            calls=[r for r in reports if r.when=='call']
            if (code!=0 or len(finished)!=18 or len(set(finished))!=18 or len(calls)-len(finished)!=43
                or {r.nodeid for r in calls}!=set(finished) or not all(r.passed for r in calls)
                or any(r.skipped or r.failed for r in reports)):
                raise RuntimeError('original county producer/consumer 18 parent tests and 43 subtests failed, skipped or incomplete')
            contracts=[]; risks=[]
            def contract(name,x):
                normalized=normalize_army_strengths([x])[0]
                contracts.append(dict(name=name,input=x,expected=normalized.get('county_entry_inputs_v1'),present='county_entry_inputs_v1' in normalized))
            contract('current-native-137-not-recomputed',row())
            x=row(); x['county_entry_inputs_v1']['current_loss_budget']=0; x['county_entry_inputs_v1']['condition'].update(mode=0,passes=False); contract('observed-zero-false-mode0',x)
            x=row(); x['county_entry_inputs_v1'].update(effective_fraction_raw=-(2**63),minimum_multiplier_raw=2**63-1,loaded_minimum_soldiers=-(2**31)); contract('signed-native-extremes',x)
            x=row(); del x['county_entry_inputs_v1']; contract('historical-absence',x)
            for reason in ['no_stored_route','actor_character_unresolved']:
                x=row(); x['county_entry_inputs_v1']['condition'].update(status='unavailable',unavailable_reason=reason,actor_character_id=None,source_province_id=None,target_province_id=None,mode=None,passes=None); contract(reason,x)
            x=floor_row(); x['county_entry_inputs_v1']['multiplier_floor_inputs_v1'].update(base_floor_raw=-(2**63),army_1d4_nonzero_floor_raw=2**63-1,army_1d4_raw=255); x['county_entry_inputs_v1']['condition']['mode']=0; contract('floors-signed64-byte255',x)
            x=floor_row(); b=x['county_entry_inputs_v1']; b.update(status='unavailable',unavailable_reason='county_entry_budget_bindings_unavailable'); b.update({k:None for k in ['whole_soldiers','current_loss_budget','effective_fraction_raw','minimum_multiplier_raw','loaded_minimum_soldiers']}); b['condition'].update(status='unavailable',unavailable_reason='county_entry_budget_unavailable',actor_character_id=None,source_province_id=None,target_province_id=None,mode=None,passes=None); contract('unavailable-budget-independent-available-floors',x)
            def risk(name,parts):
                s,c,a,p=parts; normalized=normalize_army_strengths([s])[0]
                output=project_current_unit_arrival_prestore_disembark_write_v1(normalized,arrival_transition=a,army_context=c,movement_prefix=p)
                packet=dict(strength=s,army_context=c,movement_prefix=p,prestore_call=dict(selected=output['conditional_prestore_24e23e0_call_selected'],unavailable_reason=output['unavailable_reason']))
                risks.append(dict(name=name,input=packet,expected=output['county_entry_risk_v1']))
            risk('producer-to-full-prestore-consumer',sample())
            x=list(sample()); x[0]['county_entry_inputs_v1']['condition']['passes']=False; x[3]=None; risk('native-false-dominates-unknown-prefix',x)
            x=list(sample()); x[2]['conditional_first_province_assignment_selected']=False; risk('not-arriving-does-not-prove-edge-zero',x)
            x=list(sample()); x[1]=None; risk('missing-context-no-invented-target',x)
            x=list(sample()); x[3]=None; risk('missing-prefix-tristate',x)
            x=list(sample()); x[1].update(route_read_status='complete_empty',route_source_count=0,route_province_ids=[]); risk('observed-complete-empty-route',x)
            x=list(sample()); x[0]['county_entry_inputs_v1']['condition'].update(status='unavailable',unavailable_reason='no_stored_route',actor_character_id=None,source_province_id=None,target_province_id=None,mode=None,passes=None); x[1]=None; x[3]=None; risk('native-complete-empty-without-context',x)
            x=list(sample()); b=x[0]['county_entry_inputs_v1']; b.update(current_loss_budget=0,effective_fraction_raw=0,minimum_multiplier_raw=0); b['condition']['mode']=0; b['multiplier_floor_inputs_v1']['army_1d4_raw']=9; risk('positive-second-floor-identifies-special-zero',x)
            x=list(sample()); del x[0]['county_entry_inputs_v1']['multiplier_floor_inputs_v1']; risk('legacy-missing-floors',x)
            x=list(sample()); x[0]['county_entry_inputs_v1']['multiplier_floor_inputs_v1']['base_floor_raw']=10_000; risk('ordinary-property-inversion',x)
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_route_risk_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_unit_arrival_prestore_disembark_write_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/native_bridge/src/ck3_12002_army.cpp','ck3_autonomous_player/native_bridge/include/xar_bridge/army_strength_v1_serializer.hpp',*test_paths]
            pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            output=dict(schema='xar.ck3.county-entry.original-producer-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',original_tests=len(finished),original_subtests=len(calls)-len(finished),original_skipped=0,source_pins=pins,contract_cases=contracts,risk_cases=risks)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>90112: raise RuntimeError('county golden exceeds 88KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
