package org.xar.ck3.control.wave2.military.armyqueue;


import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** One-time actual legacy producer/consumer capture; ordinary JUnit never starts Python. */
public final class CaptureArmyQueueGolden {
    private CaptureArmyQueueGolden() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length > 0 && ("--consumer-baseline".equals(args[0]) || "--compiled-consumers".equals(args[0]))) { consumerProbe(args); return; }
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM,
                repository.toString(), args[3]));
        builder.directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONPATH", repository + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/src") + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> {
                try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); }
            });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly);
                process.destroyForcibly();
                throw new IOException("army queue producer capture timeout");
            }
            try { bytes = response.get(); }
            catch (ExecutionException failure) { throw new IOException("capture read failed", failure.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) {
            throw new IOException("capture failed or over budget: exit=" + process.exitValue() + " bytes=" + bytes.length);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }

    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,contextlib
            from pathlib import Path
            import pytest
            from xar_autoplayer.bridge.army_daily_queue_inputs_contract import normalize_monthly_daily_queue_inputs_v1 as normalize
            from xar_autoplayer.bridge.army_daily_queue_transfer_projection import _initial_resolution_available
            from xar_autoplayer.bridge.army_daily_assault_queue_append_projection import project_current_daily_assault_queue_append_v1 as append
            from xar_autoplayer.bridge.army_current_assault_first_removal_projection import project_current_assault_first_removal_v1 as removal
            from xar_autoplayer.bridge.war_contract import normalize_army_strengths
            from test_conditional_daily_queue_transfer import daily_queue_packet
            root=Path(sys.argv[1]); machine=sys.argv[2]
            
            # A compiled probe supplies complete Java return bytes. It never falls back after a
            # missing, rejected or unknown transport result. Baseline mode records the same
            # original provider calls made by the actual complete consumer suites.
            from contextlib import ExitStack
            from unittest.mock import patch
            from pathlib import Path
            import gzip
            def consumer_json(value):
                return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            def consumer_strict(raw):
                def pairs(items):
                    value={}
                    for key,item in items:
                        if key in value: raise RuntimeError('duplicate compiled packet JSON key')
                        value[key]=item
                    return value
                def constant(value): raise RuntimeError('non-JSON compiled packet constant')
                return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
            consumer_mode=len(sys.argv)>4 and sys.argv[4] in ('baseline','compiled')
            consumer_packet_path=Path(sys.argv[3]) if consumer_mode and sys.argv[3] else None
            consumer_packet_bytes=None
            consumer_packet=None
            consumer_inputs=[]
            consumer_services=[]
            consumer_cursor=0
            consumer_phase='reference'
            if consumer_packet_path is not None:
                if not consumer_packet_path.is_file() or consumer_packet_path.is_symlink() or consumer_packet_path.stat().st_size>524288:
                    raise RuntimeError('compiled packet input is missing, linked or oversized')
                consumer_packet_bytes=consumer_packet_path.read_bytes()
                consumer_packet=consumer_strict(consumer_packet_bytes)
                required={'schema','family','observed_at_utc','qualified_main_jar','qualified_main_jar_sha256','qualified_test_classes','qualified_test_class_sha256','original_golden_sha256','cases'}
                if type(consumer_packet) is not dict or set(consumer_packet)!=required or consumer_packet['schema']!='xar.compiled-army-consumer-wire-packet/v1' or consumer_packet['family']!='armyqueue' or type(consumer_packet['cases']) is not list:
                    raise RuntimeError('compiled packet schema/family differs')
                consumer_phase='java'
            def consumer_invoke(value,reference):
                global consumer_cursor
                raw=consumer_json(value)
                if consumer_phase=='java':
                    index=consumer_cursor
                    consumer_cursor+=1
                    if index>=len(consumer_packet['cases']):
                        raise RuntimeError('unexpected consumer call; no producer fallback or retry')
                    supplied=consumer_packet['cases'][index]
                    if type(supplied) is not dict or set(supplied)!={'input_json','accepted','output_json'} or supplied['input_json']!=raw or type(supplied['accepted']) is not bool:
                        raise RuntimeError('consumer call order or exact source operand bytes drifted')
                    if supplied['accepted']:
                        if type(supplied['output_json']) is not str: raise RuntimeError('compiled complete result lacks return bytes')
                        result=consumer_strict(supplied['output_json'])
                        consumer_inputs.append(dict(input_json=raw,accepted=True,output_json=supplied['output_json']))
                        return result
                    if supplied['output_json'] is not None: raise RuntimeError('rejected compiled result carries output')
                    consumer_inputs.append(dict(input_json=raw,accepted=False,output_json=None))
                    raise ValueError('actual compiled producer rejected original raw operand tokens')
                try:
                    result=reference()
                except (ValueError,TypeError):
                    consumer_inputs.append(dict(input_json=raw,accepted=False,output_json=None))
                    raise
                consumer_inputs.append(dict(input_json=raw,accepted=True,output_json=consumer_json(result)))
                return result
            def consumer_query_count(service):
                value=getattr(service,'calls',None)
                if type(value) is int: return value
                value=getattr(getattr(service,'driver',None),'calls',None)
                if type(value) is list: return len(value)
                if type(value) is int: return value
                raise RuntimeError('actual driver fixture has no observable query counter')
            def consumer_observe_service(original):
                def observed(service,*args,**kwargs):
                    before=consumer_query_count(service)
                    try:
                        result=original(service,*args,**kwargs)
                    except Exception as error:
                        delta=consumer_query_count(service)-before
                        if delta not in (0,1): raise RuntimeError('failed consumer retried native query') from error
                        consumer_services.append(dict(status='rejected',exception_type=type(error).__name__,native_query_delta=delta,fixture_type=type(service).__module__+'.'+type(service).__qualname__))
                        raise
                    delta=consumer_query_count(service)-before
                    if delta!=1: raise RuntimeError('successful actual consumer did not make exactly one native fixture query')
                    fields={key:result[key] for key in ('loss_allocation_requests_v1','same_input_current_daily_assault_queue_append_v1','same_input_current_assault_first_removal_v1') if key in result}
                    view=consumer_json(fields).encode('utf-8')
                    family=[dict(present='monthly_daily_queue_inputs_v1' in row,value=row.get('monthly_daily_queue_inputs_v1')) for row in result['army_strengths']]
                    consumer_services.append(dict(status='complete',native_query_delta=delta,fixture_type=type(service).__module__+'.'+type(service).__qualname__,normalized_families=family,declared_consumer_fields_sha256=hashlib.sha256(view).hexdigest(),declared_consumer_fields_bytes=len(view),consumer_field_names=sorted(fields)))
                    return result
                return observed
            def consumer_finish(payload):
                if not consumer_mode: return payload
                if consumer_packet is not None and (consumer_cursor!=len(consumer_packet['cases']) or consumer_packet_path.read_bytes()!=consumer_packet_bytes):
                    raise RuntimeError('compiled packet was not consumed exactly once or drifted')
                payload['schema']='xar.armyqueue.original-consumer-baseline/v1'
                payload['consumer_inputs']=consumer_inputs
                payload['actual_service_consumers']=consumer_services
                payload['transport_contract']={'native_query_limit_per_service_call':1,'unknown_result_retries':0,'python_fallback_after_java_failure':False,'all_original_tests_passed':True,'compiled_calls':consumer_cursor}
                if consumer_packet is not None:
                    payload['schema']='xar.armyqueue.compiled-java-consumer-probe/v1'
                    payload['compiled_java_input']={key:consumer_packet[key] for key in ('qualified_main_jar','qualified_main_jar_sha256','qualified_test_classes','qualified_test_class_sha256','original_golden_sha256')}
                    payload['compiled_java_input'].update(packet_path=str(consumer_packet_path),packet_bytes=len(consumer_packet_bytes),packet_sha256=hashlib.sha256(consumer_packet_bytes).hexdigest())
                for key in ('cases','rows','projections','refreshes','consumers'):payload.pop(key,None)
                return payload
            
            tests=['ck3_autonomous_player/tests/unit/test_conditional_daily_queue_transfer.py','ck3_autonomous_player/tests/unit/test_current_daily_assault_queue_append_service.py','ck3_autonomous_player/tests/unit/test_current_assault_first_removal_context_service.py','ck3_autonomous_player/tests/unit/test_conditional_manager_cleanup.py']
            reports=[]
            class Reports:
                def pytest_runtest_logreport(self,report): reports.append(report)
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_queue_inputs_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_queue_transfer_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_queue_append_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_assault_first_removal_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_manager_cleanup_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_loss_allocation_projection.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/army_assault_group_release_12004.py','ck3_autonomous_player/src/xar_autoplayer/simulation/army_actual_assault_release_stage_12004.py','ck3_autonomous_player/native_bridge/src/ck3_12002_army.cpp','ck3_autonomous_player/native_bridge/include/xar_bridge/army_strength_v1_serializer.hpp','ck3_autonomous_player/native_bridge/include/xar_bridge/game_contract.hpp','ck3_autonomous_player/tests/unit/test_conditional_monthly_loss_budgets.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py',*tests]
            consumer_source_before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths} if consumer_mode else None
            consumer_stack=ExitStack()
            if consumer_mode:
                from xar_autoplayer.bridge import war_contract as consumer_war
                from xar_autoplayer.bridge.service import GameplayBridgeService as ConsumerService
                consumer_stack.enter_context(patch.object(ConsumerService,'query_army_strengths',consumer_observe_service(ConsumerService.query_army_strengths)))
                consumer_stack.enter_context(patch.object(consumer_war,'normalize_monthly_daily_queue_inputs_v1',side_effect=lambda value:consumer_invoke(value,lambda:normalize(value))))
            with consumer_stack,contextlib.redirect_stdout(sys.stderr):
                code=pytest.main(['-q','-p','no:cacheprovider',*tests],plugins=[Reports()])
            calls=[r for r in reports if r.when=='call']
            if code != 0 or len(calls)!=4 or not all(r.passed for r in calls) or any(r.skipped for r in reports): raise RuntimeError('original queue consumer tests failed or skipped')
            cases=[]; magic=0x41726D79
            def put(name,value,packet=None):
                raw=json.dumps(value,ensure_ascii=False,separators=(',',':'))
                row=dict(name=name,input_json=raw)
                try:
                    normalized=normalize(json.loads(raw)); row.update(accepted=True,normalized=normalized)
                except (ValueError,TypeError):
                    row.update(accepted=False); cases.append(row); return
                if isinstance(normalized,dict):
                    ids=normalized['manager_army_id_list_2a5a8']; rows=normalized['initial_army_resolution_rows']
                    row['identity_consistent']=[_initial_resolution_available(item,index,item['raw_army_reference_id']) for index,item in enumerate(rows)] if rows is not None else None
                    strength=dict(status='available',army_id=0,monthly_daily_queue_inputs_v1=normalized)
                    ap=append(strength,None); rp=removal(strength,None)
                    row['append_pending_ids']=ap['observed_pending_army_ids_i32']
                    row['removal_pending_raw_ids']=[item['raw_full_id_u32'] for item in rp['current_pending_selection']['remaining_known_occurrences']]
                    row['removal_pending_complete']=rp['current_pending_selection']['sequence_complete']
                if packet is not None:
                    normalized_strength=normalize_army_strengths([packet])[0]
                    row['normalized_strength_family']=normalized_strength['monthly_daily_queue_inputs_v1']
                cases.append(row)
            def packet_case(name,ids,identities):
                packet=daily_queue_packet(ids,identities); put(name,packet['monthly_daily_queue_inputs_v1'],packet)
            put('explicit-null',None)
            packet_case('empty-observed',[],[])
            packet_case('ordered-invalid-prefix-duplicates',[19,23,7,7,8],[(-1,True,magic),(23,False,0),(7,False,magic),(7,False,magic),(8,False,magic)])
            packet_case('fallback',[991],[(77,True,magic)])
            packet_case('unknown-middle',[19,20,7],[(-1,True,magic),None,(7,False,magic)])
            packet_case('unavailable-queue',None,[])
            packet_case('signed-bounds-high-magic',[-2147483648,2147483647,-1],[(-2147483648,False,4294967295),(2147483647,False,magic),(-1,True,magic)])
            base=daily_queue_packet([7],[(7,False,magic)])['monthly_daily_queue_inputs_v1']
            x=copy.deepcopy(base); x.update(status='unavailable',ready=False,unavailable_reason='initial_resolution_unavailable',initial_army_resolution_rows=None); put('ids-without-rows',x)
            x=copy.deepcopy(base); x.update(status='unavailable',ready=False,unavailable_reason='queue-unavailable',manager_army_id_list_2a5a8=None); put('rows-without-ids',x)
            x=copy.deepcopy(base); x.update(status='unavailable',ready=False,unavailable_reason='caller-conservative'); put('unavailable-with-complete-operands',x)
            x=copy.deepcopy(base); x['initial_army_resolution_rows'][0]['native_army_identity_valid']=False; put('schema-accepted-inconsistent-identity',x)
            x=copy.deepcopy(base); x.update(status='unavailable',ready=False,unavailable_reason=' '); x['initial_army_resolution_rows'][0].update(status='unavailable',unavailable_reason=' ',resolved_army_id=None,used_fallback=None,army_magic_14_raw=None,native_army_identity_valid=None); put('unknown-operands-whitespace-reason',x)
            for field in list(base):
                x=copy.deepcopy(base); del x[field]; put('missing-root-'+field,x)
            x=copy.deepcopy(base); x['extra']=False; put('unknown-root-field',x)
            for field in list(base['initial_army_resolution_rows'][0]):
                x=copy.deepcopy(base); del x['initial_army_resolution_rows'][0][field]; put('missing-row-'+field,x)
            x=copy.deepcopy(base); x['initial_army_resolution_rows'][0]['extra']=False; put('unknown-row-field',x)
            for name,field,value in [('ready-numeric','ready',1),('status-bool','status',True),('available-reason','unavailable_reason','unexpected'),('ids-not-array','manager_army_id_list_2a5a8',{}),('rows-not-array','initial_army_resolution_rows',{}),('rows-length','initial_army_resolution_rows',[])]:
                x=copy.deepcopy(base); x[field]=value; put(name,x)
            for name,value in [('bool',True),('float',7.0),('exponent',7e0),('string','7'),('underflow',-2147483649),('overflow',2147483648),('null',None)]:
                x=copy.deepcopy(base); x['manager_army_id_list_2a5a8']=[value]; put('raw-id-'+name,x)
            for field,values in [('stored_index',[True,0.0,-1,1]),('raw_army_reference_id',[True,7.0,8]),('resolved_army_id',[True,7.0,2147483648,None]),('army_magic_14_raw',[True,1.0,-1,4294967296,None]),('used_fallback',[0,'false',None]),('native_army_identity_valid',[1,'true',None])]:
                for index,value in enumerate(values):
                    x=copy.deepcopy(base); x['initial_army_resolution_rows'][0][field]=value; put(field+'-bad-'+str(index),x)
            if consumer_mode and any(hashlib.sha256((root/p).read_bytes()).hexdigest()!=consumer_source_before[p] for p in paths): raise RuntimeError('actual consumer source drifted')
            output=dict(schema='xar.ck3.army-daily-queue-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',original_tests=len(calls),original_skipped=0,source_pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths],cases=cases)
            output=consumer_finish(output)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>(262144 if consumer_mode else 65536): raise RuntimeError('army queue golden exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;

    private static final int CONSUMER_RAW_LIMIT = 256 * 1024;
    private static final int CONSUMER_GZIP_LIMIT = 24 * 1024;
    private static final int CONSUMER_PACKET_LIMIT = 512 * 1024;
    private static final ObjectMapper CONSUMER_JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    /**
     * Existing collector's qualified compiled mode. Only fixture transport is
     * substituted; the original complete tests, Service and queue consumers run.
     */
    private static void consumerProbe(String[] args) throws IOException, InterruptedException {
        boolean compiled = args.length > 0 && "--compiled-consumers".equals(args[0]);
        if ((!compiled && (args.length != 7 || !"--consumer-baseline".equals(args[0])))
                || (compiled && args.length != 13)) {
            throw new IllegalArgumentException("baseline: mode/repo/python/output/fresh-scratch/machine/owned-root; compiled: mode/repo/python/golden/output/fresh-scratch/main-jar/main-sha/golden-sha/test-classes/test-class-sha/machine/owned-root");
        }
        Path repository = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[compiled ? 4 : 3]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[compiled ? 5 : 4]).toAbsolutePath().normalize();
        String machine = args[compiled ? 11 : 5];
        Path ownedRoot = Path.of(args[compiled ? 12 : 6]).toAbsolutePath().normalize();
        if (!output.getParent().equals(ownedRoot) || !scratch.getParent().equals(ownedRoot)
                || !Files.isDirectory(ownedRoot) || Files.isSymbolicLink(ownedRoot)
                || !ownedRoot.toRealPath().equals(ownedRoot)
                || !output.getFileName().toString().endsWith(".json.gz")
                || Files.exists(output) || Files.exists(scratch) || machine.isBlank()) {
            throw new IllegalArgumentException("fresh bounded owned output/scratch and explicit actual machine required");
        }
        Path mainJar = null, golden = null, testClasses = null, packetPath = null, classFile = null;
        String mainSha = null, goldenSha = null, classSha = null, packetSha = null;
        if (compiled) {
            mainJar = Path.of(args[6]).toAbsolutePath().normalize();
            golden = Path.of(args[3]).toAbsolutePath().normalize();
            testClasses = Path.of(args[9]).toAbsolutePath().normalize();
            if (!consumerOrigin(ArmyDailyQueueInputsCodec.class).equals(mainJar)
                    || !consumerOrigin(CaptureArmyQueueGolden.class).equals(testClasses)) {
                throw new IllegalStateException("actual compiled producer or consumer bridge origin differs");
            }
            classFile = testClasses.resolve(CaptureArmyQueueGolden.class.getName().replace('.', '/') + ".class");
            mainSha = consumerHash(mainJar, 16 * 1024 * 1024);
            goldenSha = consumerHash(golden, CONSUMER_RAW_LIMIT);
            classSha = consumerHash(classFile, 1024 * 1024);
            if (!mainSha.equals(args[7]) || !goldenSha.equals(args[8]) || !classSha.equals(args[10])) {
                throw new IllegalStateException("actual main/reference/compiled test class SHA differs");
            }
            JsonNode reference = CONSUMER_JSON.readTree(consumerReadGolden(golden));
            if (!"xar.armyqueue.original-consumer-baseline/v1".equals(reference.path("schema").asText())
                    || !reference.path("consumer_inputs").isArray()
                    || reference.path("consumer_inputs").isEmpty()
                    || reference.path("consumer_inputs").size() > 512) {
                throw new IllegalArgumentException("complete original consumer baseline is required");
            }
            ObjectNode packet = CONSUMER_JSON.createObjectNode();
            packet.put("schema", "xar.compiled-army-consumer-wire-packet/v1");
            packet.put("family", "armyqueue"); packet.put("observed_at_utc", Instant.now().toString());
            packet.put("qualified_main_jar", mainJar.toString()); packet.put("qualified_main_jar_sha256", mainSha);
            packet.put("qualified_test_classes", testClasses.toString()); packet.put("qualified_test_class_sha256", classSha);
            packet.put("original_golden_sha256", goldenSha);
            ArrayNode cases = packet.putArray("cases");
            for (JsonNode row : reference.path("consumer_inputs")) {
                if (!row.path("input_json").isTextual() || !row.path("accepted").isBoolean()) {
                    throw new IllegalArgumentException("original consumer operand/acceptance fields differ");
                }
                String raw = row.get("input_json").textValue(); byte[] wire = null;
                try { wire = ArmyDailyQueueInputsCodec.encode(ArmyDailyQueueInputsCodec.decode(raw.getBytes(StandardCharsets.UTF_8))); }
                catch (IllegalArgumentException rejection) {
                    if (row.get("accepted").booleanValue()) throw rejection;
                }
                if ((wire != null) != row.get("accepted").booleanValue()) {
                    throw new IllegalStateException("actual compiled producer acceptance differs from original consumer baseline");
                }
                ObjectNode value = cases.addObject(); value.put("input_json", raw);
                value.put("accepted", wire != null);
                if (wire == null) value.putNull("output_json");
                else {
                    if (!row.path("output_json").isTextual()
                            || !CONSUMER_JSON.readTree(wire).equals(CONSUMER_JSON.readTree(row.get("output_json").textValue()))) {
                        throw new IllegalStateException("actual Java return differs before original consumer transport");
                    }
                    value.put("output_json", new String(wire, StandardCharsets.UTF_8));
                }
            }
            byte[] packetBytes = CONSUMER_JSON.writeValueAsBytes(packet);
            if (packetBytes.length > CONSUMER_PACKET_LIMIT) throw new IllegalArgumentException("compiled return packet exceeds finite transport profile");
            packetPath = output.resolveSibling(output.getFileName().toString() + ".java-wire-packet.json");
            Files.createDirectories(output.getParent());
            Files.write(packetPath, packetBytes, java.nio.file.StandardOpenOption.CREATE_NEW);
            packetSha = consumerHash(packetPath, CONSUMER_PACKET_LIMIT);
        }
        Files.createDirectories(scratch);
        if (!scratch.toRealPath().equals(scratch)) throw new IllegalArgumentException("consumer scratch redirects through a link");
        Path rawOutput = scratch.resolve("original-consumers.raw.json");
        Path errors = scratch.resolve("original-consumers.stderr.log");
        java.util.List<String> command = new java.util.ArrayList<>(java.util.List.of(args[2], "-B", "-X", "utf8", "-c", PROGRAM));
        command.add(repository.toString()); command.add(machine);
        
        command.add(packetPath == null ? "" : packetPath.toString());
        command.add(compiled ? "compiled" : "baseline");
        ProcessBuilder builder = new ProcessBuilder(command).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONHASHSEED", "0");
        builder.environment().put("PYTHONPATH", repository + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/src") + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        for (String name : java.util.List.of("XAR_DAILY_QUEUE_APPEND_FIRST_OUTPUT", "XAR_ASSAULT_FIRST_REMOVAL_FIRST_OUTPUT", "XAR_CURRENT_REPLENISHMENT_FIRST_OUTPUT")) {
            builder.environment().remove(name);
        }
        Process child = builder.start();
        byte[] rawProof, errorBytes;
        boolean timedOut;
        try (var readers = java.util.concurrent.Executors.newFixedThreadPool(2)) {
            var stdout = readers.submit(() -> { try (var stream = child.getInputStream()) { return stream.readNBytes(CONSUMER_RAW_LIMIT + 1); } });
            var stderr = readers.submit(() -> { try (var stream = child.getErrorStream()) { return stream.readNBytes(65_537); } });
            timedOut = !child.waitFor(90, TimeUnit.SECONDS);
            if (timedOut) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly().waitFor(); }
            try { rawProof = stdout.get(); errorBytes = stderr.get(); }
            catch (java.util.concurrent.ExecutionException failure) { throw new IOException("bounded consumer stream failed", failure.getCause()); }
        }
        Files.write(rawOutput, java.util.Arrays.copyOf(rawProof, Math.min(rawProof.length, CONSUMER_RAW_LIMIT)), java.nio.file.StandardOpenOption.CREATE_NEW);
        Files.write(errors, java.util.Arrays.copyOf(errorBytes, Math.min(errorBytes.length, 65_536)), java.nio.file.StandardOpenOption.CREATE_NEW);
        if (errorBytes.length > 65_536 || rawProof.length > CONSUMER_RAW_LIMIT) throw new IOException("actual consumer stream exceeded hard profile; bounded partial evidence retained");
        if (timedOut) throw new IOException("actual original consumer probe timed out; bounded evidence retained; unknown result is not retried");
        System.err.println("original_consumer_stderr_bytes=" + errorBytes.length + " retained=" + errors);
        if (child.exitValue() != 0) throw new IOException("actual original consumer probe exit " + child.exitValue());
        if (rawProof.length < 1) throw new IOException("actual consumer proof is empty");
        JsonNode proof = CONSUMER_JSON.readTree(rawProof);
        String expectedSchema = compiled ? "xar.armyqueue.compiled-java-consumer-probe/v1" : "xar.armyqueue.original-consumer-baseline/v1";
        if (!expectedSchema.equals(proof.path("schema").asText())
                || !proof.path("transport_contract").path("all_original_tests_passed").isBoolean()
                || !proof.path("transport_contract").path("all_original_tests_passed").booleanValue()) {
            throw new IOException("actual complete original consumer proof is missing");
        }
        if (compiled && (!consumerHash(mainJar, 16 * 1024 * 1024).equals(mainSha)
                || !consumerHash(golden, CONSUMER_RAW_LIMIT).equals(goldenSha)
                || !consumerHash(classFile, 1024 * 1024).equals(classSha)
                || !consumerHash(packetPath, CONSUMER_PACKET_LIMIT).equals(packetSha))) {
            throw new IOException("qualified artifact/reference/return packet drifted during actual consumer calls");
        }
        java.io.ByteArrayOutputStream packed = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(packed)) { gzip.write(rawProof); }
        byte[] zipped = packed.toByteArray();
        if (zipped.length > CONSUMER_GZIP_LIMIT) throw new IOException("actual consumer proof exceeds bounded gzip profile");
        try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(zipped))) {
            if (!java.util.Arrays.equals(rawProof, gzip.readNBytes(CONSUMER_RAW_LIMIT + 1))) throw new IOException("consumer proof gzip lost original bytes");
        }
        Files.createDirectories(output.getParent());
        Files.write(output, zipped, java.nio.file.StandardOpenOption.CREATE_NEW);
        System.out.println("machine_id=" + machine + " family=armyqueue compiled=" + compiled
                + " raw_bytes=" + rawProof.length + " gzip_bytes=" + zipped.length + " original_consumers_completed=true");
    }
    private static Path consumerOrigin(Class<?> type) throws IOException {
        try { return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize(); }
        catch (URISyntaxException failure) { throw new IOException("compiled class origin is invalid", failure); }
    }
    private static String consumerHash(Path file, int maximum) throws IOException {
        if (!Files.isRegularFile(file) || Files.size(file) < 1 || Files.size(file) > maximum) throw new IOException("qualified input path/size rejected");
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException("SHA-256 unavailable", failure); }
    }
    private static byte[] consumerReadGolden(Path file) throws IOException {
        try (java.io.InputStream raw = Files.newInputStream(file);
                java.io.InputStream input = file.getFileName().toString().endsWith(".gz") ? new java.util.zip.GZIPInputStream(raw) : raw) {
            byte[] bytes = input.readNBytes(CONSUMER_RAW_LIMIT + 1);
            if (bytes.length == 0 || bytes.length > CONSUMER_RAW_LIMIT) throw new IOException("consumer baseline raw size rejected");
            return bytes;
        }
    }

}
