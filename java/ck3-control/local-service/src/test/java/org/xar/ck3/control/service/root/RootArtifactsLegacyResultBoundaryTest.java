package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootArtifactsSourcesFactory.*;

/** Original Python normalizer and result writer at a software Native edge. No Game/ledger/archive. */
final class RootArtifactsLegacyResultBoundaryTest {
    private static ObjectNode originals;
    private static final String MACHINE = "software-artifact-sidecar-boundary";
    @TempDir static Path temporary;

    @BeforeAll static void originalPythonNormalizerAndResultWriter() throws Exception {
        Path repository = Path.of(System.getProperty("xar.repository.root")).toRealPath();
        String program = """
            import base64,copy,json,sys
            from pathlib import Path
            from unittest.mock import patch
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import relic_action_private_transport as action
            from xar_autoplayer.bridge.version_identity import CK3_12004
            frame={'snapshot_id':'software-sidecar-frame','revision':7,'native_revision':17,'date_raw':12345,
                'episode_run_id':'software-sidecar-episode','paused':True,'map_ready':True,
                'diagnostics':{'connection_generation':1,'bridge_pid':4242,'hello':{
                    'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256}},
                'played_character':{'character_id':42,'alive':True}}
            machine=('software-artifact-sidecar-boundary','a'*64,{'policy_version':'software-boundary-policy',
                'policy_sha256':'b'*64,'policy_path':str(root/'docs/storage-retention-policy.json'),'protection_max_hours':24})
            def selection(artifact):
                return {'available':True,'artifact_id':artifact,'slot_index':0,'slot_artifact_ids':[8,None],'unavailable_reason':''}
            def native_result(resolved,already=False):
                nested={'available':True,'status':'acknowledged_verification_pending','loaded_source_pins_verified':True,
                    'native_dispatch_attempted':True,'dispatch_invoked':True,'verification_pending':True,
                    'already_in_requested_state':False,'selection_postcondition_observed':resolved,
                    'original_button_enabled_observed':False,'original_button_enabled':None,
                    'actual_button_presentation_observed':False,'button_child_path':'','frozen_preview_verified':False,
                    'gameplay_command_may_have_been_queued':False,'business_outcome_observed':False,'action_ready':False,
                    'before':selection(7),'after':selection(8 if resolved else 7),'unavailable_reason':''}
                if already:
                    nested.update(status='already_in_requested_state_verification_pending',native_dispatch_attempted=False,
                        dispatch_invoked=False,already_in_requested_state=True,before=selection(8))
                raw={'schema':'ck3-ingame-ui-window-v1','window_kind':'holy_site','window_name':'holy_site_window',
                    'requested_subject_id':9,'current_subject_id':9,'native_revision':17,'date_raw':12345,
                    'paused':True,'played_character_id':42,'backend_id':'native-headless',
                    'native_backend_id':'ck3-1.20.0.4-native-ingame-ui-v1','game_version':CK3_12004.game_version,
                    'executable_sha256':CK3_12004.executable_sha256,'application_owner_thread_verified':True,
                    'gui_owner_binding_verified':True,'window_exists':True,'effective_visible':True,'enabled':True,
                    'subject_id_available':True,'thread_id':1,'pump_epoch':1,'gui_context_address':1,'gui_owner_address':1,
                    'rng_owner_is_ui_admission_gate':False,'accepted':True,'holy_site_relic_action':nested,
                    'modal_admission':{'attempted':True,'header_read':True,'receivers_verified':True,'effective_visible_count':0}}
                for key in ('available','status','native_dispatch_attempted','dispatch_invoked','verification_pending','unavailable_reason'):
                    raw[key]=nested[key]
                return raw
            class Driver:
                allow_private_holy_site_relic_actions=True
                def __init__(self,path,resolved,already=False):self.path=path;self.resolved=resolved;self.already=already;self.calls=0
                def _native_driver_state_path(self):return self.path/'driver.json'
                def take_snapshot_without_native_command_history(self):return copy.deepcopy(frame)
                def _execute_primitive_step(self,*args,**kwargs):
                    self.calls+=1
                    assert kwargs['required_capability']=='game.command.navigate-ingame-ui-v1'
                    return native_result(self.resolved,self.already)
                def _record_command(self,*args,**kwargs):pass
            output={}
            contradictory=native_result(True)
            for target in (contradictory,contradictory['holy_site_relic_action']):
                target.update(native_dispatch_attempted=False,dispatch_invoked=False,verification_pending=False)
            try:
                action.normalize_relic_action_result_v1(contradictory,before=frame,operation='select_relic_artifact',
                    holy_site_id=9,fields={'relic_artifact_id':8})
            except ValueError as error:
                assert 'availability lacks an original callback ACK' in str(error)
                output['rejected_contradictory_flags']=True
            else:raise AssertionError('original normalizer accepted contradictory action availability')
            tmp=Path(sys.argv[2]);tmp.mkdir(parents=True,exist_ok=False)
            for name,resolved,already in [('resolved',True,False),('pending',False,False),('already_requested',True,True)]:
                driver=Driver(tmp/name,resolved,already)
                with patch.object(action,'_machine_identity',return_value=machine):
                    result=action.execute_relic_action_private_v1(driver,expected_revision=7,holy_site_id=9,
                        operation='select_relic_artifact',fields={'relic_artifact_id':8})
                assert driver.calls==1 and result['identical_intent_replay_blocked'] is (not resolved)
                files=sorted((driver.path/'holy-site-relic-action-intents').iterdir())
                assert len(files)==(1 if resolved else 2)
                output[name]=[{'name':p.name,'bytes_base64':base64.b64encode(p.read_bytes()).decode()} for p in files]
            print(json.dumps(output,separators=(',',':')))
            """;
        String captureOverride = System.getProperty("xar.sidecar.original.path");
        Path capture = captureOverride == null ? temporary.resolve("original-produced.json") : Path.of(captureOverride);
        String fixtureOverride = System.getProperty("xar.sidecar.fixture.root");
        Path fixtureRoot = fixtureOverride == null ? temporary.resolve("original-fixtures") : Path.of(fixtureOverride);
            ProcessBuilder builder = new ProcessBuilder(System.getProperty("xar.python"), "-B", "-X", "utf8", "-c", program, repository.toString(), fixtureRoot.toString());
            builder.directory(repository.toFile());
            builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src").toString());
            builder.environment().put("XAR_SOURCE_REPOSITORY", repository.toString());
            builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.environment().put("PYTHONUTF8", "1");
            builder.environment().put("TEMP", System.getProperty("java.io.tmpdir"));
            builder.environment().put("TMP", System.getProperty("java.io.tmpdir"));
            Process process = builder.redirectErrorStream(true).redirectOutput(capture.toFile()).start();
            boolean ended = process.waitFor(15, TimeUnit.SECONDS);
            if (!ended) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
            assertTrue(ended, "original sidecar producer timed out");
            byte[] bytes = Files.readAllBytes(capture);
            assertEquals(0, process.exitValue(), new String(bytes, StandardCharsets.UTF_8));
            originals = StrictJson.object(StrictJson.parse(bytes, 1 << 20), Set.of("resolved", "pending", "already_requested", "rejected_contradictory_flags"));
    }

    private static List<LegacyFile> produced(String scenario) {
        var files = new ArrayList<LegacyFile>();
        for (JsonNode row : originals.get(scenario)) {
            files.add(new LegacyFile(row.get("name").textValue(), new RawJson(Base64.getDecoder().decode(row.get("bytes_base64").textValue()))));
        }
        return List.copyOf(files);
    }

    private static LegacyScope scope() { return new LegacyScope(MACHINE, 42, ScopeKind.ONE_LIFE_EPISODE, "software-sidecar-episode"); }

    @Test void originalEmptyPathAndDiagnosticSidecarKeepsActualResolvedAndPendingMeanings() {
        List<LegacyFile> resolved = produced("resolved");
        assertEquals(1, resolved.size());
        assertTrue(resolved.getFirst().name().endsWith(".result.json"));
        assertTrue(legacyBlockers(resolved, scope()).isEmpty(), "actual original resolved sidecar must remain readable");
        List<LegacyFile> pending = produced("pending");
        assertEquals(2, pending.size());
        assertEquals(2, legacyBlockers(pending, scope()).size(), "both retained pending and unresolved result own exclusion");
        LegacyFile pendingResult = pending.stream().filter(file -> file.name().endsWith(".result.json")).findFirst().orElseThrow();
        assertEquals(List.of(pendingResult.name()), legacyBlockers(List.of(pendingResult), scope()));
    }

    @Test void wrongTypedNullAndMissingResultStringsCannotReleaseOriginalExclusion() {
        LegacyFile source = produced("resolved").getFirst();
        ObjectNode controlValue = assertInstanceOf(ObjectNode.class, StrictJson.parse(source.original().bytes()));
        ObjectNode controlResult = assertInstanceOf(ObjectNode.class, controlValue.get("native_result"));
        controlResult.put("button_child_path", "software-boundary-button").put("unavailable_reason", "software-boundary-diagnostic");
        LegacyFile control = new LegacyFile(source.name(), new RawJson(StrictJson.canonical(controlValue)));
        assertTrue(legacyBlockers(List.of(control), scope()).isEmpty(), "non-target string fields must not mask the malformed-field rejection");
        for (String field : List.of("button_child_path", "unavailable_reason")) {
            for (int mutation = 0; mutation < 3; mutation++) {
                ObjectNode value = assertInstanceOf(ObjectNode.class, StrictJson.parse(control.original().bytes()));
                ObjectNode result = assertInstanceOf(ObjectNode.class, value.get("native_result"));
                if (mutation == 0) result.put(field, true);
                else if (mutation == 1) result.putNull(field);
                else result.remove(field);
                LegacyFile invalid = new LegacyFile(source.name(), new RawJson(StrictJson.canonical(value)));
                assertThrows(IllegalArgumentException.class, () -> legacyBlockers(List.of(invalid), scope()), field + " mutation " + mutation);
            }
        }
    }

    @Test void originalNormalizerRejectedInvocationFlagsCannotBecomeAResolvedSidecar() {
        assertTrue(originals.get("rejected_contradictory_flags").booleanValue());
        assertTrue(legacyBlockers(produced("resolved"), scope()).isEmpty());
        assertEquals(2, legacyBlockers(produced("pending"), scope()).size());
        assertTrue(legacyBlockers(produced("already_requested"), scope()).isEmpty(), "original already-observed no-op keeps the availability exception");
        LegacyFile source = produced("resolved").getFirst();
        ObjectNode value = assertInstanceOf(ObjectNode.class, StrictJson.parse(source.original().bytes()));
        ObjectNode result = assertInstanceOf(ObjectNode.class, value.get("native_result"));
        result.put("native_dispatch_attempted", false).put("dispatch_invoked", false).put("verification_pending", false);
        LegacyFile contradictory = new LegacyFile(source.name(), new RawJson(StrictJson.canonical(value)));
        assertThrows(IllegalArgumentException.class, () -> legacyBlockers(List.of(contradictory), scope()),
                "the original normalizer rejects this tuple; the Java migration consumer must not clear it as resolved");
    }
}
