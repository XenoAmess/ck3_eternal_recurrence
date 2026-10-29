package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;
import static org.xar.ck3.control.service.root.RootArtifactsSourcesFactory.*;

/** Actual original CREATE_NEW/timeout producer into the sole Java parser. No constructed private Root/Lease or Native Ready. */
final class RootArtifactsSourcesFactoryTest {
    private static ObjectNode original;
    private static final String MACHINE="software-artifact-original-fixture";
    @TempDir Path temporary;
    @BeforeAll static void originalPythonFilesystemProducer()throws Exception {
        Path root=requiredPath("xar.repository.root",true);
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/relic_action_private_transport.py")),
                "actual original Python input required; a missing migration oracle is not a skip");
        String program="""
            import base64,copy,hashlib,json,sys,tempfile
            from pathlib import Path
            from unittest.mock import patch
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import relic_action_private_transport as action
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            output={}
            class Driver:
                def __init__(self,path):self.path=path;self.calls=0
                def _native_driver_state_path(self):return self.path/'driver.json'
                def _execute_primitive_step(self,*args,**kwargs):
                    self.calls+=1
                    assert kwargs['required_capability']=='game.command.navigate-ingame-ui-v1'
                    raise TimeoutError('software fixture: actual original claim survives unknown return')
                def _record_command(self,*args,**kwargs):pass
            frame={'snapshot_id':'original-software-capture','revision':7,'native_revision':17,'date_raw':12345,
                   'episode_run_id':'original-software-episode','diagnostics':{'connection_generation':1},
                   'played_character':{'character_id':42,'alive':True}}
            machine=('software-artifact-original-fixture','a'*64,{'policy_version':'test-original-policy',
                     'policy_sha256':'b'*64,'policy_path':str(root/'docs/storage-retention-policy.json'),'protection_max_hours':24})
            with tempfile.TemporaryDirectory(prefix='relic-original-claim-') as tmp:
                driver=Driver(Path(tmp));before=copy.deepcopy(frame)
                with patch.object(action,'_frame',side_effect=lambda d,r:copy.deepcopy(before)),patch.object(action,'_machine_identity',return_value=machine):
                    try:action.execute_relic_action_private_v1(driver,expected_revision=7,holy_site_id=9,
                            operation='select_relic_artifact',fields={'relic_artifact_id':8})
                    except TimeoutError:pass
                    else:raise AssertionError('unknown was silently accepted')
                    before['diagnostics']['connection_generation']=2
                    try:action.execute_relic_action_private_v1(driver,expected_revision=7,holy_site_id=9,
                            operation='select_relic_artifact',fields={'relic_artifact_id':8})
                    except BridgeUnavailableError:pass
                    else:raise AssertionError('actual CREATE_NEW cross-generation exclusion was bypassed')
                assert driver.calls==1
                folder=driver.path/'holy-site-relic-action-intents';files=sorted(folder.iterdir())
                assert len(files)==1 and files[0].name.endswith('.pending.json')
                output={'calls':driver.calls,'files':[{'name':p.name,'bytes_base64':base64.b64encode(p.read_bytes()).decode()} for p in files]}
                value={'ascii':'x','control':chr(127),'unicode':'汉😀'}
                output['python_identity']=json.dumps(value,sort_keys=True,separators=(',',':'))
                output['python_sha256']=hashlib.sha256(output['python_identity'].encode()).hexdigest()
            print(json.dumps(output,separators=(',',':')))
            """;
        Path capture=Files.createTempFile("artifact-original-producer-",".json");
        try {
            ProcessBuilder builder=new ProcessBuilder(requiredPath("xar.python",false).toString(),"-B","-X","utf8","-c",program,root.toString());
            originalEnvironment(builder,root);Process process=builder.redirectErrorStream(true).redirectOutput(capture.toFile()).start();
            boolean ended=process.waitFor(45,TimeUnit.SECONDS);
            if(!ended){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}assertTrue(ended,"original compatibility producer timed out");
            byte[] bytes=Files.readAllBytes(capture);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));
            original=StrictJson.object(StrictJson.parse(bytes,1<<20),Set.of("calls","files","python_identity","python_sha256"));
        }finally{Files.deleteIfExists(capture);}
    }
    private static List<LegacyFile> produced(){
        var files=new ArrayList<LegacyFile>();for(JsonNode row:original.get("files"))files.add(new LegacyFile(row.get("name").textValue(),
                new RawJson(Base64.getDecoder().decode(row.get("bytes_base64").textValue()))));return List.copyOf(files);
    }
    private static LegacyScope scope(long actor,String run){return new LegacyScope(MACHINE,actor,ScopeKind.ONE_LIFE_EPISODE,run);}
    private static ObjectNode claim(){return StrictJson.object(StrictJson.parse(produced().getFirst().original().bytes()),Set.of("schema","machine_id","observed_at_utc","review_after_utc","protected_until_utc","storage_policy","retention_reason","machine_reader_sha256","request_id","intent","intent_sha256","cross_generation_replay_guard_sha256","expected_public_revision","expected_native_revision","connection_generation","automatic_retry","business_outcome_observed"));}
    private static LegacyFile altered(ObjectNode value){return new LegacyFile(produced().getFirst().name(),new RawJson(StrictJson.canonical(value)));}
    @Test void actualOriginalExclusiveProducerBlocksReconnectAndTheJavaConsumerRetainsItsOriginalClaim(){
        assertEquals(1,original.get("calls").intValue());var files=produced();
        assertEquals(List.of(files.getFirst().name()),legacyBlockers(files,scope(42,"original-software-episode")));
        assertEquals(files,files.stream().map(f->new LegacyFile(f.name(),new RawJson(f.original().bytes()))).toList());
    }
    @Test void aChangedActorOrExpiredReviewDoesNotTurnAnOldUnknownIntoAnEmptyStore(){
        var value=claim();value.put("review_after_utc","2000-01-01T00:00:00Z").put("protected_until_utc","2000-01-01T00:00:00Z");
        assertEquals(1,legacyBlockers(List.of(altered(value)),scope(43,"original-software-episode")).size());
        assertTrue(legacyBlockers(produced(),scope(42,"different-complete-episode")).isEmpty());
        assertEquals(1,produced().size(),"another scope never deletes the retained original");
    }
    @Test void originalIdentityUsesPythonAsciiEscapingIncludingDelAndSupplementaryCodePoints(){
        var value=StrictJson.object().put("ascii","x").put("control",String.valueOf((char)127)).put("unicode","汉😀");
        String actual=pythonIdentity(value);assertEquals(original.get("python_identity").textValue(),actual);
        assertEquals(original.get("python_sha256").textValue(),ActionCodec.sha256(actual.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void changedFilenameHashMissingNullAndIntegerCoercionsCannotReleaseTheOriginalUnknown(){
        ObjectNode bool=claim();((ObjectNode)bool.get("intent")).put("played_character_id",true);
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(altered(bool)),scope(42,"original-software-episode")));
        ObjectNode missing=claim();missing.remove("connection_generation");
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(altered(missing)),scope(42,"original-software-episode")));
        ObjectNode nil=claim();nil.putNull("intent");
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(altered(nil)),scope(42,"original-software-episode")));
        ObjectNode floating=claim();floating.put("expected_native_revision",17.0);
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(altered(floating)),scope(42,"original-software-episode")));
        ObjectNode wrongBuild=claim();((ObjectNode)wrongBuild.get("intent")).put("executable_sha256","0".repeat(64));
        var wrongBuildFailure=assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(altered(wrongBuild)),scope(42,"original-software-episode")));
        assertTrue(wrongBuildFailure.getMessage().contains("machine/build/generation differs"));
        var wrong=new LegacyFile("f".repeat(64)+".pending.json",produced().getFirst().original());
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(wrong),scope(42,"original-software-episode")));
        assertThrows(IllegalArgumentException.class,()->legacyBlockers(List.of(produced().getFirst(),produced().getFirst()),scope(42,"original-software-episode")));
    }
    @Test void soleNativeRolesSelectOnlyTheActualQualifiedCutNotAFreshSameNamedSource()throws Exception {
        Path repository=requiredPath("xar.repository.root",true);
        assertTrue(Files.isRegularFile(repository.resolve("ck3_autonomous_player/native_bridge/src/bridge.cpp")),"actual immutable Native source input required");
        Path nativeRoot=repository.resolve("ck3_autonomous_player/native_bridge/src");var cut=new ArrayList<FileRef>();
        try(var paths=Files.list(nativeRoot)){for(Path path:paths.filter(Files::isRegularFile).toList())cut.add(FileRef.measure(path));}
        var actual=RootArtifactsSourcesFactory.nativeSources(nativeRoot,cut);assertEquals(33,actual.size());
        for(Method method:Method.values())assertTrue(actual.containsKey(nativePrimary(method)));
        var missing=new ArrayList<>(cut);missing.removeIf(r->Path.of(r.path()).getFileName().toString().equals(nativePrimary(Method.SELECT_RELIC)));
        assertThrows(java.io.IOException.class,()->RootArtifactsSourcesFactory.nativeSources(nativeRoot,missing));
        var duplicate=new ArrayList<>(cut);duplicate.add(cut.stream().filter(r->Path.of(r.path()).getFileName().toString().equals("bridge.cpp")).findFirst().orElseThrow());
        assertThrows(java.io.IOException.class,()->RootArtifactsSourcesFactory.nativeSources(nativeRoot,duplicate));
    }
    @Test void finitePreparedConsumerDeclaresExactlyItsRealFiveNavMethodsAndNoPrivateArtifactActions(){
        assertEquals(Set.of(Method.SELECT_RELIC,Method.RELIC_SLOT,Method.ENSHRINE,Method.REMOVE,Method.CREATION_SELECTION),navigationMethods());
        assertEquals(5,navigationSelectors().size());assertFalse(navigationMethods().contains(Method.PERSONAL_SUBMIT));
        for(Method method:navigationMethods())assertFalse(method.readOnly());
    }
    private static ObjectNode selected(long artifact,int slot){
        ObjectNode value=StrictJson.object().put("available",true).put("artifact_id",artifact).put("slot_index",slot).put("unavailable_reason","");
        value.putArray("slot_artifact_ids").add(8).addNull();
        return originalJson(value);
    }
    private static ObjectNode originalJson(ObjectNode value){
        return assertInstanceOf(ObjectNode.class,StrictJson.parse(StrictJson.canonical(value)));
    }
    private static ObjectNode permissions(){
        ObjectNode value=StrictJson.object().put("capture_epoch",102);
        value.set("window_context",StrictJson.object().put("available",true).put("root_present",true).put("selected_holy_site_id",9)
                .put("selected_artifact_id",8).put("selected_slot_index",0));
        var slots=value.putObject("site_inventory_slots").put("available",true).putArray("slots");
        slots.addObject().put("slot_index",0).put("artifact_id",8);slots.addObject().put("slot_index",1).putNull("artifact_id");return originalJson(value);
    }
    @Test void independentLaterSelectionRequiresBothRequestedControlAndUnchangedCompleteInventory(){
        Request request=new RelicPair(Method.SELECT_RELIC,BigInteger.valueOf(7),9,8);
        ObjectNode nav=StrictJson.object();nav.putObject("holy_site_relic_action").set("after",selected(8,0));
        verifyRelicSelection(request,nav,permissions(),BigInteger.valueOf(101));
        var stale=permissions();stale.put("capture_epoch",101);
        assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(request,nav,stale,BigInteger.valueOf(101)));
        var changed=permissions();((ObjectNode)changed.get("site_inventory_slots").get("slots").get(0)).put("artifact_id",18);
        assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(request,nav,changed,BigInteger.valueOf(101)));
        var another=permissions();((ObjectNode)another.get("window_context")).put("selected_holy_site_id",10);
        assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(request,nav,another,BigInteger.valueOf(101)));
        var wrongReason=selected(8,0);wrongReason.put("unavailable_reason",true);
        var nullReason=selected(8,0);nullReason.putNull("unavailable_reason");
        var missingReason=selected(8,0);missingReason.remove("unavailable_reason");
        var contradictoryReason=selected(8,0);contradictoryReason.put("unavailable_reason","not available");
        var missingRows=selected(8,0);missingRows.putNull("slot_artifact_ids");
        for(ObjectNode malformed:List.of(wrongReason,nullReason,missingReason,contradictoryReason,missingRows)){
            var invalid=nav.deepCopy();((ObjectNode)invalid.get("holy_site_relic_action")).set("after",malformed);
            assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(request,invalid,permissions(),BigInteger.valueOf(101)));
        }
        var pastActualRow=nav.deepCopy();((ObjectNode)pastActualRow.get("holy_site_relic_action")).set("after",selected(8,2));
        var matchingInvalidSlot=permissions();((ObjectNode)matchingInvalidSlot.get("window_context")).put("selected_slot_index",2);
        assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(request,pastActualRow,originalJson(matchingInvalidSlot),BigInteger.valueOf(101)));
        Request enshrine=new Enshrine(BigInteger.valueOf(7),9,8,0,true,"a".repeat(64),new org.xar.ck3.control.contracts.PublicUnsigned64.Missing());
        assertThrows(IllegalArgumentException.class,()->verifyRelicSelection(enshrine,nav,permissions(),BigInteger.valueOf(101)));
    }
    private static Path requiredPath(String property,boolean directory)throws java.io.IOException {
        String configured=System.getProperty(property);assertNotNull(configured,property+" is mandatory");
        assertFalse(configured.isBlank(),property+" is mandatory");Path input=Path.of(configured);
        assertTrue(input.isAbsolute(),property+" must be the admitted absolute path");Path actual=input.toRealPath();
        assertTrue(directory?Files.isDirectory(actual):Files.isRegularFile(actual),property+" actual input is missing");return actual;
    }
    private static void originalEnvironment(ProcessBuilder builder,Path root)throws java.io.IOException {
        builder.directory(root.toFile());var environment=builder.environment();
        environment.put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toRealPath().toString());
        environment.put("XAR_SOURCE_REPOSITORY",root.toString());
        environment.put("PYTHONDONTWRITEBYTECODE","1");environment.put("PYTHONUTF8","1");
    }

}
