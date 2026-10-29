package org.xar.ck3.control.wave2.military.supplyschedule;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only capture of the original Python contract and projection; normal tests are Java-only. */
public final class CaptureSupplyScheduleGolden {
    private CaptureSupplyScheduleGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) throw new IllegalArgumentException("repository python-exe fresh-output machine-id required");
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("fresh output required");
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src") + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> process.getInputStream().readNBytes(131_073));
            if (!process.waitFor(45, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                throw new IOException("producer capture timeout");
            }
            try { bytes = response.get(); } catch (ExecutionException failure) { throw new IOException("producer read failed", failure.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 131_072) throw new IOException("producer capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }
    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,unittest,contextlib
            from pathlib import Path
            from test_army_zero_stock_clock_12004 import clock_row,ZeroStockClockTests
            from xar_autoplayer.bridge.army_future_daily_supply_schedule_contract import normalize_future_daily_supply_schedule_inputs_v1 as normalize
            from xar_autoplayer.bridge.army_future_daily_supply_schedule_projection import project_future_daily_supply_schedule_v1 as project
            from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_projection import project_native_next_daily_supply_schedule_v1 as native_project
            root=Path(sys.argv[1]); machine=sys.argv[2]
            with contextlib.redirect_stdout(sys.stderr):
                result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ZeroStockClockTests))
            if not result.wasSuccessful() or result.skipped or result.testsRun!=7: raise RuntimeError('original zero stock tests failed/skipped/count differs')
            base=clock_row()['future_daily_supply_schedule_inputs_v1']; cases=[]
            def put(name,value,frames):
                before=copy.deepcopy(value)
                normalized=normalize(value,expected_army_id=10,expected_carmy_id=20)
                projected=project(value,prospective_frames=frames) if value is not None else project({'future_daily_supply_schedule_inputs_v1':None},prospective_frames=frames)
                if value!=before: raise RuntimeError('old producer mutated input')
                cases.append(dict(name=name,input=value,frames=frames,normalized=normalized,projection=projected))
            put('all30-original-repeated-slots',base,[{'date_raw_i32':43800024,'native_day_index_raw_i32':1}])
            partial=copy.deepcopy(base); partial.update(status='partial',ready=False,unavailable_reason='phase29_unreadable')
            partial['phases'][29].update(status='unavailable',ready=False,unavailable_reason='negative_native_count',capacity_raw_i32=-9,count_raw_i32=-1,data_pointer_present=False,matching_positions=None,subject_occurrence_count_i32=None)
            put('partial-unrelated-phase-retains-selected-slots',partial,[{'date_raw_i32':43800024,'native_day_index_raw_i32':1},{'date_raw_i32':-2147483648,'native_day_index_raw_i32':29}])
            edge=copy.deepcopy(base); edge.update(subject_army_id_u32=4294967295,subject_carmy_id_u32=2147483648,current_date_storage_raw64=-9223372036854775808,current_date_raw_i32=-2147483648,native_day_index_raw_i32=-1,selected_phase_index_i32=15)
            edge['phases'][0].update(capacity_raw_i32=-2147483648,count_raw_i32=0,data_pointer_present=False,matching_positions=[],subject_occurrence_count_i32=0)
            # Same-row masking is tested independently; this case deliberately uses the full uint32 native IDs.
            cases.append(dict(name='native-bitwidth-unsigned-modulo',input=edge,frames=[{'date_raw_i32':2147483647,'native_day_index_raw_i32':-2147483648}],normalized=normalize(edge,expected_army_id=-1,expected_carmy_id=-2147483648),projection=project(edge,prospective_frames=[{'date_raw_i32':2147483647,'native_day_index_raw_i32':-2147483648}])))
            unavailable=copy.deepcopy(base); unavailable.update(status='unavailable',ready=False,unavailable_reason='bindings_unavailable',subject_army_id_u32=None,subject_carmy_id_u32=None,current_date_storage_raw64=None,current_date_raw_i32=None,native_day_index_raw_i32=None,selected_phase_index_i32=None,phases=[])
            put('unavailable-pre-capture-null-operands',unavailable,[{'date_raw_i32':1,'native_day_index_raw_i32':-1}]); put('explicit-null',None,[])
            joins=[]
            for name,family,frame in [('same-row-legacy-next-pair',base,clock_row()['source_derived_next_daily_supply_frame_inputs_v1']),('selected-ready-despite-partial-all30',partial,clock_row()['source_derived_next_daily_supply_frame_inputs_v1']),('missing-next-pair',base,None),('unavailable-current-membership',unavailable,None)]:
                row=dict(army_id=10,native_carmy_id=20,future_daily_supply_schedule_inputs_v1=family,source_derived_next_daily_supply_frame_inputs_v1=frame,unrelated_sdk_extension={'retained':True})
                joins.append(dict(name=name,row=row,projection=native_project(row)))
            full=copy.deepcopy(joins[0]['row']); full['source_derived_next_daily_supply_frame_inputs_v1'].update(source_derived_next_date_storage_raw64=-9223372036854775808,source_derived_next_calendar_day_u8=1,source_derived_next_calendar_month_u8=2,source_derived_full_cdate64_ready=True)
            joins.append(dict(name='extended-complete-CDate64-independent-of-calendar-inference',row=full,projection=native_project(full)))
            raw=json.dumps(base,sort_keys=True,separators=(',',':')); negatives=[]
            changes=[('schema_version','1','1.0'),('subject_army_id_u32','10','true'),('subject_army_id_u32','10','4294967296'),('current_date_storage_raw64','43800000','9223372036854775808'),('current_date_raw_i32','43800000','2147483648'),('native_day_index_raw_i32','12','12.0'),('selected_phase_index_i32','12','13'),('actual_future_callback_observed','false','true'),('count_raw_i32','3','true'),('matching_positions','[]','[0,0]'),('matching_positions','[]','[3]'),('data_pointer_present','true','1'),('source',json.dumps(base['source']),json.dumps('unqualified_source')),('unavailable_reason','null',json.dumps('unexpected'))]
            for field,old,new in changes:
                needle=json.dumps(field)+':'+old
                if needle not in raw: raise RuntimeError('capture replacement not found '+field)
                changed=raw.replace(needle,json.dumps(field)+':'+new,1)
                try: normalize(json.loads(changed))
                except (ValueError,TypeError): accepted=False
                else: accepted=True
                if accepted: raise RuntimeError('old normalizer unexpectedly accepted negative '+field+' '+new)
                negatives.append(dict(field=field,old_token=old,replacement_token=new,accepted=False))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_future_daily_supply_schedule_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_future_daily_supply_schedule_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_source_derived_next_daily_supply_frame_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_zero_stock_clock_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_army_zero_stock_clock_12004.py','ck3_autonomous_player/native_bridge/include/xar_bridge/army_future_daily_supply_schedule_v1.hpp','ck3_autonomous_player/native_bridge/include/xar_bridge/army_future_daily_supply_schedule_serializer_v1.hpp','ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_future_daily_supply_schedule.hpp']
            pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            payload=dict(schema='xar.ck3.supply-schedule-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_pins=pins,native_collector_execution='NOTRUN',input_origin='existing_test_army_zero_stock_clock_12004.clock_row_plus_declared_boundary_variations',original_tests=result.testsRun,original_skipped=len(result.skipped),cases=cases,joins=joins,negative_base_raw=raw,negatives=negatives)
            encoded=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(encoded)>131072: raise RuntimeError('golden exceeds 128KiB')
            sys.stdout.buffer.write(encoded)
            """;
}
