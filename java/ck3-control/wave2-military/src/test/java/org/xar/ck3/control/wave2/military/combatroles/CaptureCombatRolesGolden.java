package org.xar.ck3.control.wave2.military.combatroles;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeFixtureBuild;

/** Compiled test capture. The storage-owned Job supplies genuine C++ bytes and the actual producer receipt. */
public final class CaptureCombatRolesGolden {
    private CaptureCombatRolesGolden() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 6 && args.length != 7) {
            throw new IllegalArgumentException("repo python approved-task-root native-wire-ref native-producer-receipt-ref fresh-output.gz [compiled-java-packet]");
        }
        Path repo = Path.of(args[0]).toRealPath();
        Path taskRoot = Path.of(args[2]).toRealPath();
        CombatWholeWire.FileReference wireRef = CombatWholeWire.reference(readSmall(Path.of(args[3])));
        CombatWholeWire.FileReference receiptRef = CombatWholeWire.reference(readSmall(Path.of(args[4])));
        byte[] wireBytes = CombatWholeWire.readPinned(wireRef, taskRoot);
        CombatWholeWire.parse(wireBytes);
        CombatWholeWire.readPinned(receiptRef, taskRoot);
        NativeFixtureBuild.Actual receipt = verifyNativeProducer(receiptRef.path(), wireRef);
        ControlBuild.FileRef manifest = receipt.sourceManifestRef();
        CombatWholeWire.FileReference sourceManifest = new CombatWholeWire.FileReference(
                Path.of(manifest.path()), manifest.bytes(), manifest.sha256());
        CombatWholeWire.readPinned(sourceManifest, taskRoot);
        Path output = Path.of(args[5]).toAbsolutePath().normalize();
        if (!output.startsWith(taskRoot) || Files.exists(output)) throw new IllegalArgumentException("fresh task output required");
        String javaPacket = args.length == 7 ? args[6] : "";
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", SCRIPT,
                repo.toString(), wireRef.path().toString(), output.toString(), receipt.machineId(),
                javaPacket, args[3], args[4]));
        builder.directory(repo.toFile()).inheritIO();
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repo.resolve("ck3_autonomous_player/src")
                + java.io.File.pathSeparator + repo.resolve("ck3_workshop_mcp/src")
                + java.io.File.pathSeparator + repo.resolve("ck3_autonomous_player/tests/unit"));
        Process child = builder.start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IllegalStateException("consumer capture timeout; shared Job retains descendant custody");
        }
        if (child.exitValue() != 0) throw new IllegalStateException("actual original consumer exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 32768) {
            throw new IllegalStateException("finite genuine producer golden missing or oversized");
        }
        CombatWholeWire.readPinned(wireRef, taskRoot);
        CombatWholeWire.readPinned(receiptRef, taskRoot);
        CombatWholeWire.readPinned(sourceManifest, taskRoot);
        verifyNativeProducer(receiptRef.path(), wireRef);
    }

    static NativeFixtureBuild.Actual verifyNativeProducer(Path receiptPath,
            CombatWholeWire.FileReference originalWire) throws IOException {
        NativeFixtureBuild.Actual receipt = NativeFixtureBuild.readActual(
                receiptPath, NativeFixtureBuild.ActualStage.COMBATROLES_PRODUCER);
        List<String> command = receipt.command();
        if (command.size() != 3 || !"--wire-dir".equals(command.get(1))) {
            throw new IOException("exact original C++ whole-query producer command required");
        }
        Path executable = Path.of(command.getFirst()), outputDirectory = Path.of(command.get(2));
        if (!executable.isAbsolute() || !executable.normalize().equals(executable)
                || !executable.getFileName().toString().equals(
                    "xar_bridge_ck3_12003_army_combat_roles_phase_rule24_pins_test.exe")
                || !outputDirectory.isAbsolute() || !outputDirectory.normalize().equals(outputDirectory)
                || !outputDirectory.resolve("ck3_12003_army_combat_roles_phase_rule24_pins_wire.json")
                    .equals(originalWire.path())) {
            throw new IOException("original native executable and output directory roles disagree");
        }
        ControlBuild.FileRef executableRef = NativeFixtureBuild.linkedExecutableRef(receipt, executable);
        int matchingExecutable = 0;
        for (ControlBuild.FileRef linked : receipt.linkedArtifactRefs()) {
            if (Path.of(linked.path()).normalize().equals(executable)) {
                if (!linked.equals(executableRef)) throw new IOException("original native executable pin differs");
                matchingExecutable++;
            }
        }
        if (matchingExecutable != 1 || receipt.outputRefs().isEmpty() || receipt.outputRefs().size() > 16) {
            throw new IOException("one exact linked native executable and bounded actual outputs required");
        }
        int matchingWire = 0;
        for (ControlBuild.FileRef output : receipt.outputRefs()) {
            if (Path.of(output.path()).normalize().equals(originalWire.path())) {
                if (!new CombatWholeWire.FileReference(Path.of(output.path()), output.bytes(), output.sha256())
                        .equals(originalWire)) throw new IOException("native producer raw output reference disagrees");
                matchingWire++;
            }
        }
        if (matchingWire != 1) throw new IOException("one exact original native wire required");
        return receipt;
    }
    private static byte[] readSmall(Path path) throws IOException {
        try (var stream = Files.newInputStream(path)) {
            byte[] raw = stream.readNBytes(CombatWholeWire.REFERENCE_MAX_BYTES + 1);
            if (raw.length > CombatWholeWire.REFERENCE_MAX_BYTES) throw new IllegalArgumentException("bounded reference required");
            return raw;
        }
    }

    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip,subprocess,importlib.util,unittest,contextlib,os,asyncio
            from pathlib import Path
            from unittest.mock import patch
            repo=Path(sys.argv[1]); wire_path=Path(sys.argv[2]); output=Path(sys.argv[3]); machine=sys.argv[4]
            java_packet_path=Path(sys.argv[5]) if sys.argv[5] else None
            wire_ref_path=Path(sys.argv[6]); receipt_ref_path=Path(sys.argv[7])
            if output.exists():raise ValueError('fresh output required')
            wire_raw=wire_path.read_bytes()
            if len(wire_raw)>16*1024*1024:raise ValueError('whole-wire cap')
            wire=json.loads(wire_raw)
            from xar_autoplayer.bridge.army_current_combat_roles_phase_inputs_contract import normalize_current_army_combat_roles_phase_inputs_v1 as normalize
            from xar_autoplayer.simulation.army_current_combat_roles_phase_inputs_12003 import project_current_army_combat_roles_phase_inputs_12003 as project
            from xar_autoplayer.bridge.army_strengths_manager_shared_wire import pack_army_strengths_manager_inputs as pack,expand_army_strengths_manager_inputs as expand
            from xar_autoplayer.bridge import war_contract
            test=repo/'ck3_autonomous_player/tests/unit/test_army_current_combat_rule24_service_12003.py'
            spec=importlib.util.spec_from_file_location('combat_roles_original_service_capture',test)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            old_wire=os.environ.get('XAR_ARMY_COMBAT_RULE24_WIRE'); old_case=os.environ.pop('XAR_ARMY_COMBAT_RULE24_CASE_OUTPUT',None)
            os.environ['XAR_ARMY_COMBAT_RULE24_WIRE']=str(wire_path)
            try:
                suite=unittest.TestSuite([module.ArmyCurrentCombatRule24Service12003Tests('test_first_compiled_current_combat_roles_phase_and_rule24_pins_through_service')])
                with contextlib.redirect_stdout(sys.stderr): actual=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
                if not actual.wasSuccessful() or actual.testsRun!=1 or actual.skipped:raise ValueError('actual original fourteen-scene Service compound failed/skipped')
            finally:
                if old_wire is None:os.environ.pop('XAR_ARMY_COMBAT_RULE24_WIRE',None)
                else:os.environ['XAR_ARMY_COMBAT_RULE24_WIRE']=old_wire
                if old_case is not None:os.environ['XAR_ARMY_COMBAT_RULE24_CASE_OUTPUT']=old_case
            member='current_army_combat_roles_phase_inputs_v1'
            java_packet=json.loads(java_packet_path.read_bytes()) if java_packet_path else None
            raw_token_results=[]
            if java_packet is not None:
                if java_packet.get('schema')!='xar.compiled-combat-consumer-packet/v1':raise ValueError('compiled packet schema')
                if java_packet['original_wire_sha256']!=hashlib.sha256(wire_raw).hexdigest():raise ValueError('compiled packet is from another original wire')
                actual_java={row['name']:row for row in java_packet['cases']}
                if set(actual_java)!=set(wire['samples']):raise ValueError('compiled packet scene set')
                for vector in java_packet['raw_token_rejections']:
                    raw_request=vector['raw_request_json']
                    try:normalize(json.loads(raw_request))
                    except (ValueError,TypeError) as error:original_accepted=False;original_error=type(error).__name__
                    else:original_accepted=True;original_error=None
                    raw_token_results.append({'raw_request_json':raw_request,'compiled_java_rejected':True,
                        'valid_token_domain':False,'historical_original_accepted':original_accepted,'historical_original_error':original_error})
                if len(raw_token_results)!=5:raise ValueError('complete actual raw token probes required')
            cases=[]
            for name,native_row in wire['samples'].items():
                original=copy.deepcopy(native_row); leaf=native_row[member]; normalized=normalize(leaf)
                service=module.MemoryCombatRule24Route(copy.deepcopy(native_row))
                returned=service.query_army_strengths([11],expected_revision=42)
                projection=project(normalized,source_provenance=module._SOURCE)
                if native_row!=original or normalized!=leaf or returned['army_strengths'][0][member]!=leaf:raise ValueError('original whole-row source changed')
                if service.calls!=[('query-army-strengths-v1',42)]:raise ValueError('actual original Service call changed')
                family=returned[member]
                if family!=[{'army_id':11,'projection':projection}]:raise ValueError('actual Service projection differs')
                transport={'army_strengths':[{'army_id':0,member:copy.deepcopy(leaf)},{'army_id':11,member:copy.deepcopy(leaf)}]}
                packed=pack(transport)
                if expand(packed)!=transport:raise ValueError('original transport changed owned leaf')
                if java_packet is not None:
                    java=actual_java[name]; java_input=json.loads(java['normalized_input_json'])
                    if normalize(java_input)!=normalized:raise ValueError('actual Java bytes fail original strict normalizer')
                    if json.loads(java['projection_json'])!=project(java_input,source_provenance=module._SOURCE):raise ValueError('actual Java bytes differ from original pure projection')
                    carrier=copy.deepcopy(native_row); carrier[member]=java_input
                    observed=module.MemoryCombatRule24Route(carrier).query_army_strengths([11],expected_revision=42)
                    if observed[member]!=json.loads(java['service_family_json']):raise ValueError('actual Java bytes differ through original Service consumer')
                cases.append({'name':name,'origin':'genuine_native_whole_query_with_synthetic_world_and_service_frame',
                    'input':leaf,'expected_normalized':normalized,'expected_projection':projection,'expected_service_family':family,
                    'shared_transport':{'army_ids':[0,11],'field_names':list(packed['army_manager_inputs_shared_v1']['fields']),
                    'origin':'explicit synthetic transport carriers; unchanged owned original leaf'}})
            registered=[]
            if java_packet is not None:
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
                from xar_autoplayer.bridge.service import GameplayBridgeService
                from xar_autoplayer.bridge.mcp_server import create_server
                from xar_autoplayer.bridge.version_identity import CK3_12004
                from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY
                harness_file=repo/'ck3_autonomous_player/tests/unit/test_army_manager_shared_registered_mcp_12004.py'
                hs=importlib.util.spec_from_file_location('combat_original_endpoint',harness_file); held=importlib.util.module_from_spec(hs);hs.loader.exec_module(held)
                async def routes():
                    for name,native_row in wire['samples'].items():
                        java=actual_java[name]; carrier=copy.deepcopy(native_row); carrier[member]=json.loads(java['normalized_input_json'])
                        expected=war_contract.normalize_army_strengths([copy.deepcopy(carrier)],expected_scope=[{'army_id':11,'scope_role':'player','war_ids':[]}])
                        body={'step':'query-army-strengths-v1','accepted':True,'status':war_contract.army_strength_query_status(expected),
                            'query_sequence':1,'army_strengths':[carrier],'backend_id':'synthetic-current-combat-whole-query-carrier',
                            'army_strengths_profile':'ordinary_core_v1','army_observed_phase_coverage':'not_requested'}
                        packet={'type':'command_result','protocol_version':1,'request_id':'synthetic-correlated-request','ok':True,'result':body}
                        for route in ('ck3_query_army_strengths','ck3_execute_step','ck3_auto_turn'):
                            endpoint=held._OriginalWholeEndpoint(copy.deepcopy(packet)); driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,command_timeout_seconds=1.0,state_dir=None,episode_projection='native_campaign')
                            try:
                                server=create_server(driver)
                                endpoint.publish({'type':'hello','protocol_version':1,'bridge_version':'0.1.0','pid':4242,'connection_generation':1,
                                    'game_version':CK3_12004.game_version,'executable_sha256':CK3_12004.executable_sha256,
                                    'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256,
                                    'capabilities':['game.state.snapshot',QUERY_ARMY_STRENGTHS_CAPABILITY]})
                                endpoint.publish({'type':'state_snapshot','protocol_version':1,'snapshot_id':'native:1','revision':1,
                                    'state':{'phase':'map_hud','date':'synthetic-current-not-live','date_raw':10000,'speed':1,'paused':True,'map_ready':True,
                                    'history':[],'active_event':None,'pending_character_interaction':None,'played_character':{'character_id':29829,'alive':True},
                                    'player_armies':[{'army_id':11,'controllable':True,'owner_character_id':29829,'current_province_id':100}],'active_wars':[]}})
                                before=driver.take_snapshot()
                                if route=='ck3_auto_turn':
                                    planned={'snapshot_id':before['snapshot_id'],'revision':before['revision'],'plan':{'selected_step':'query-army-strengths-v1','phase':'synthetic_army_query_selection'}}
                                    with patch.object(GameplayBridgeService,'plan_turn',autospec=True,return_value=planned) as selected:
                                        result=await server.call_tool(route,{})
                                    selected.assert_called_once()
                                else:
                                    arguments={'expected_revision':before['revision']}
                                    if route=='ck3_query_army_strengths':arguments['army_ids']=[11]
                                    else:arguments['step']='query-army-strengths-v1'
                                    if route=='ck3_query_army_strengths':
                                        endpoint.whole['result']['army_strengths_query_scope']={'army_ids':[11],'published_scope_status':'available'}
                                    result=await server.call_tool(route,arguments)
                                if result.is_error:raise ValueError('real registered consumer rejected actual Java bytes '+route)
                                structured=result.structured_content
                                semantic=structured['result'] if route=='ck3_auto_turn' else structured
                                expanded=expand(semantic)
                                if expanded['army_strengths']!=expected:raise ValueError('real registered consumer changed full actual Java leaf')
                                if route!='ck3_query_army_strengths':
                                    # Current source intentionally publishes only the core projection to its cache.
                                    core=driver._army_strength_snapshot_fields({'army_strengths':expected})['army_strengths']
                                    if driver._army_strength_query['army_strengths']!=core:raise ValueError('real cache differs from current core contract')
                                commands=[r for r in endpoint.requests if r.get('type')=='execute_step']
                                if len(commands)!=1 or commands[0]['expected_revision']!=before['native_revision']:raise ValueError('registered route did not use exactly one native fixture query')
                                if len(endpoint.delivered)!=1 or endpoint.delivered[0]['result']!=endpoint.whole['result']:raise ValueError('fixture endpoint changed actual Java carrier body')
                                registered.append({'name':name,'registered_tool':route,'transport_requests':1,'full_java_leaf_preserved':True,
                                    'returned_json_sha256':hashlib.sha256(json.dumps(structured,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
                            finally:driver.close()
                asyncio.run(routes())
                if len(registered)!=42:raise ValueError('all real registered consumers required')
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_combat_roles_phase_inputs_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/simulation/army_current_combat_roles_phase_inputs_12003.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_flag31_inputs_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_assault_roster_admission_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/simulation/army_current_flag31_inputs_12003.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/army_strengths_profile_contract.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/army_strengths_manager_shared_wire.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py',
                'ck3_autonomous_player/tests/unit/test_army_current_combat_rule24_service_12003.py',
                'ck3_autonomous_player/tests/unit/test_army_manager_shared_registered_mcp_12004.py']
            bindings=[{'path':p,'bytes':(repo/p).stat().st_size,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in paths]
            observed_machine=subprocess.check_output([sys.executable,'-B',str(repo/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
            if observed_machine!=machine:raise ValueError('native source/capture machine mismatch')
            result={'schema':'xar.combat-roles-original-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_bindings':bindings,'original_wire':dict(json.loads(wire_ref_path.read_bytes()),machine_id=machine,qualification=wire['qualification']),
                'native_producer_receipt':json.loads(receipt_ref_path.read_bytes()),'original_service_compound_tests':1,
                'original_service_compound_skipped':0,'actual_live_qualification':False,'source_provenance':module._SOURCE,
                'capture_method':'Original C++ raw wire retained unchanged; real original strict/pure/Service consumers; optional compiled Java output to real Driver/Service/three MCP routes. All endpoint/world/frame/planner choices synthetic; zero Game.',
                'null_expected_projection':project(None,source_provenance=module._SOURCE),'cases':cases,
                'compiled_java_consumer_probe':java_packet is not None,'registered_consumer_receipts':registered,
                'raw_token_consumer_results':raw_token_results}
            raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8'); packed=gzip.compress(raw,mtime=0)
            if len(raw)>1048576 or len(packed)>32768:raise ValueError('finite golden budget exceeded')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('xb') as handle:handle.write(packed)
            print(json.dumps({'machine_id':machine,'cases':len(cases),'registered_calls':len(registered),'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest()}))
            """;
}
