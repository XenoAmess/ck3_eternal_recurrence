package org.xar.ck3.control.application.ritecreation;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore.*;
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
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.ritecreation.RiteCreationLegacyStore.*;

/** Original Python execute/save/release producers into the actual Java legacy parser and sole v2 body.
 * File identities here are labelled fixture DATA. They never mint platform custody or a writer import. */
public final class RiteCreationLegacyStoreTest {
    private static ObjectNode produced;
    private static final String MACHINE="synthetic-test-machine";
    @BeforeAll static void actualOriginalFilesystemProducers()throws Exception{
        Path root=Path.of(System.getProperty("xar.rite.repository",System.getProperty("user.dir"))).toAbsolutePath();
        while(root!=null&&!Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/rite_creation_action_private_v1.py")))root=root.getParent();
        assertNotNull(root,"actual original Python source required; missing input is not a skipped migration regression");
        String program="""
            import ast,base64,json,os,sys,tempfile,unittest
            from copy import deepcopy
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import patch
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import rite_creation_action_private_v1 as action
            from xar_autoplayer.bridge.driver import BridgeUnavailableError,UnsupportedStepError
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.version_identity import CK3_12004
            source=root/'ck3_autonomous_player/tests/unit/test_rite_creation_action_private_v1.py'
            tree=ast.parse(source.read_text(encoding='utf-8'))
            chosen=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('unavailable','synthetic_preview','Endpoint','RiteCreationAdapterTests')]
            assert len(chosen)==4
            ns=dict(globals(),MACHINE='synthetic-test-machine',DATE=12345,ACTOR=34014,RITE=26,__file__=str(source))
            exec(compile(ast.Module(body=chosen,type_ignores=[]),str(source),'exec'),ns)
            output={}
            for label,timeout,reject in [('unknown',True,False),('queued',False,False),('released',False,True)]:
                case=ns['RiteCreationAdapterTests']();case.setUp()
                try:
                    driver,endpoint=case.driver();endpoint.timeout=timeout;endpoint.known_reject=reject
                    try:case.confirm(driver)
                    except BridgeUnavailableError:
                        assert timeout
                    assert len(endpoint.requests)==1
                    store=driver._native_driver_state_path().parent/'rite-creation-actions'
                    files=[{'leaf':p.name,'bytes_base64':base64.b64encode(p.read_bytes()).decode()} for p in sorted(store.iterdir()) if p.is_file()]
                    assert any(p['leaf'].endswith('.safe-no-dispatch.json' if reject else '.claim.json') for p in files)
                    output[label]={'store':str(store),'files':files}
                    if label=='unknown':
                        endpoint.known_reject=True;endpoint.publish(endpoint.packet(endpoint.requests[0]))
                        resolved=action.collect_private_result_v1(driver,action_request_id=endpoint.requests[0]['request_id'])
                        assert resolved['known_no_dispatch_intent_released'] is True and len(endpoint.requests)==1
                        output['late_released']={'store':str(store),'files':[{'leaf':p.name,'bytes_base64':base64.b64encode(p.read_bytes()).decode()} for p in sorted(store.iterdir()) if p.is_file()]}
                finally:case.doCleanups()
            # Real managed binding producer, real identity serializer, and real exclusive/fsync claim writer.
            fixture=root/'ck3_autonomous_player/tests/fixtures/rite_creation_actions12004/r0016-managed-frame.json'
            record=json.loads(fixture.read_text(encoding='utf-8'));snapshot=record['snapshot'];bound=action._binding(snapshot,snapshot['revision'])
            identity=action._intent_identity_v1(bound,0)
            import hashlib
            key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();request='rite-action-'+'e'*32
            fields=action.request_fields('confirm_once',0,expected_preview_identity='a'*64,expected_outcome_kind='create_faith');fields['action_id']=request
            with tempfile.TemporaryDirectory(prefix='rite-managed-original-') as temporary:
                path=Path(temporary)/(key+'.claim.json')
                action._save_exclusive(path,{'schema':'xar.ck3-rite-confirm-once.v1','machine_id':'synthetic-test-machine','observed_at_utc':'2026-10-24T00:00:00+00:00','request_id':request,'identity':identity,'binding':bound,'fields':fields,'status':'claimed_result_unknown_no_retry','native_result_file':key+'.'+request+'.native-result.json'})
                output['managed']={'store':bound['managed_campaign_run_binding']['state_dir']+'\\\\native-session\\\\rite-creation-actions','files':[{'leaf':path.name,'bytes_base64':base64.b64encode(path.read_bytes()).decode()}]}
            print(json.dumps(output,separators=(',',':')))
            """;
        Path captured=Files.createTempFile("rite-original-fs-oracle-",".json");
        try{Process process=new ProcessBuilder(System.getProperty("xar.rite.python","python"),"-c",program,root.toString()).redirectErrorStream(true).redirectOutput(captured.toFile()).start();
            boolean ended=process.waitFor(45,TimeUnit.SECONDS);if(!ended){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}assertTrue(ended,"original filesystem oracle timed out");byte[] bytes=Files.readAllBytes(captured);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));produced=object(new RawJson(bytes));
        }finally{Files.deleteIfExists(captured);}
    }
    private static ExactRef manifest(String name){return new ExactRef("D:/fixture-only/"+name,1,"a".repeat(64));}
    private static OriginalFile file(String leaf,byte[] bytes){String digest=ActionCodec.sha256(bytes);ExactRef source=new ExactRef("D:/fixture-only/original/"+leaf,bytes.length,digest),archive=new ExactRef("D:/fixture-only/preserved/"+digest,bytes.length,digest);return new OriginalFile(new Evidence(leaf,source,new FileIdentity("1","9007199254740993","133700000000000001","2026-10-24T00:00:00Z",bytes.length),archive),bytes);}
    private static Image image(String label){ObjectNode n=object(get(produced,label));var files=new ArrayList<OriginalFile>();for(JsonNode row:get(n,"files"))files.add(file(text(get(object(row),"leaf")),Base64.getDecoder().decode(text(get(object(row),"bytes_base64")))));return image(text(get(n,"store")),files);}
    private static Image image(String store,List<OriginalFile> files){return new Image(MACHINE,store,files.stream().map(v->v.evidence().leaf()).toList(),files);}
    private static Imported parsed(String label){return parse(image(label),manifest(label));}
    private static RiteCreationState.State javaBasis(){return RiteCreationState.initialize(RiteCreationState.State.empty(),new RiteCreationState.Basis(RiteCreationState.Initialization.FRESH,new EpisodeScope("actual-fixture"),34014,List.of(manifest("basis"))));}
    @Test void originalUnknownClaimNeverAcquiresJavaReceiptOrRetryCredit(){Imported actual=parsed("unknown");assertEquals(1,actual.intents().size());Intent claim=actual.intents().getFirst();assertEquals(Status.ORIGINAL_UNKNOWN_NO_RETRY,claim.status());assertTrue(claim.blocksRetry());assertTrue(claim.originalNativeResult().isEmpty());assertEquals(actual,fromJson(toJson(actual)));assertTrue(toJson(actual).toString().contains("9007199254740993"));assertFalse(toJson(actual).has("canonical_action_receipt"));}
    @Test void originalPossibleQueueRemainsBlockingAfterValidNativeAck(){Intent actual=parsed("queued").intents().getFirst();assertEquals(Status.ORIGINAL_NATIVE_RESULT_NO_RETRY,actual.status());assertTrue(actual.blocksRetry());assertTrue(actual.originalNativeResult().isPresent());assertTrue(actual.originalResultFailure().isEmpty());}
    @Test void originalLateCollectorUpdatesOnlyTheSameRetainedIntent(){Imported unknown=parsed("unknown"),late=parsed("late_released");assertEquals(unknown.intents().getFirst().id(),late.intents().getFirst().id());Imported actual=merge(Optional.of(unknown),late);assertEquals(1,actual.intents().size());assertFalse(actual.intents().getFirst().blocksRetry());assertEquals(2,actual.intents().getFirst().claimAndReleaseEvidence().size());assertEquals(2,actual.custodyManifests().size());assertEquals(actual,fromJson(toJson(actual)));}
    @Test void originalSafeReleaseAndCrashDuplicateCarryEveryOriginal(){Image original=image("released");Imported released=parse(original,manifest("released"));Intent claim=released.intents().getFirst();assertFalse(claim.blocksRetry());assertEquals(Status.ORIGINAL_KNOWN_NO_DISPATCH_RELEASED,claim.status());var files=new ArrayList<>(original.files());files.add(file(claim.originalClaimKey()+".claim.json",claim.originalClaim().bytes()));Intent crash=parse(image(original.actualCanonicalStore(),files),manifest("crash")).intents().getFirst();assertFalse(crash.blocksRetry());assertEquals(2,crash.claimAndReleaseEvidence().size());}
    @Test void malformedOriginalPacketIsPreservedAsUnknownInsteadOfDroppingTheClaim(){Image original=image("queued");var files=new ArrayList<OriginalFile>();for(OriginalFile actual:original.files())files.add(actual.evidence().leaf().endsWith(".native-result.json")?file(actual.evidence().leaf(),"{".getBytes(StandardCharsets.UTF_8)):actual);Intent claim=parse(image(original.actualCanonicalStore(),files),manifest("malformed")).intents().getFirst();assertEquals(Status.ORIGINAL_UNKNOWN_NO_RETRY,claim.status());assertTrue(claim.originalResultFailure().isPresent());assertTrue(claim.originalNativeResult().isPresent());}
    @Test void boolIntegerMissingFieldAndChangedClaimDigestAreRejected(){Image original=image("unknown");OriginalFile claim=original.files().stream().filter(v->v.evidence().leaf().endsWith(".claim.json")).findFirst().orElseThrow();ObjectNode n=object(new RawJson(claim.bytes()));object(get(n,"binding")).put("played_character_id",true);assertThrows(IllegalArgumentException.class,()->parse(image(original.actualCanonicalStore(),List.of(file(claim.evidence().leaf(),raw(n).bytes()))),manifest("bool")));ObjectNode missing=object(new RawJson(claim.bytes()));missing.remove("status");assertThrows(IllegalArgumentException.class,()->parse(image(original.actualCanonicalStore(),List.of(file(claim.evidence().leaf(),raw(missing).bytes()))),manifest("missing")));assertThrows(IllegalArgumentException.class,()->parse(image(original.actualCanonicalStore(),List.of(file("f".repeat(64)+".claim.json",claim.bytes()))),manifest("digest")));}
    @Test void orphanFinalPacketDoesNotBecomeAnEmptyQualifiedOnceHistory(){Image original=image("queued");OriginalFile packet=original.files().stream().filter(v->v.evidence().leaf().endsWith(".native-result.json")).findFirst().orElseThrow();assertThrows(IllegalArgumentException.class,()->parse(image(original.actualCanonicalStore(),List.of(packet)),manifest("orphan")));}
    @Test void managedOriginalBindingUsesSoleCanonicalizerAndCannotEscapeByMovingStore(){Image original=image("managed");Intent claim=parse(original,manifest("managed")).intents().getFirst();assertTrue(claim.binding().scope() instanceof ManagedScope);assertTrue(claim.binding().originalManagedBinding().isPresent());assertTrue(claim.blocksRetry());assertThrows(IllegalArgumentException.class,()->parse(image("D:/unrelated-state/native-session/rite-creation-actions",original.files()),manifest("moved")));assertEquals(claim.originalClaimKey(),ActionCodec.sha256(pythonIdentity(claim.binding().scope(),claim.binding().nativeActor(),claim.source()).getBytes(StandardCharsets.UTF_8)));}
    @Test void nextFirstAndLaterEmptyStoreRetainAllUnknownsAndCustodyManifests(){Imported unknown=parsed("unknown");Imported later=merge(Optional.of(unknown),new Imported(manifest("later-empty"),List.of()));assertEquals(unknown.intents(),later.intents());assertEquals(2,later.custodyManifests().size());RiteCreationDomainState full=new RiteCreationDomainState(javaBasis(),Optional.of(later));var next=RiteCreationState.initialize(full.javaState(),new RiteCreationState.Basis(RiteCreationState.Initialization.NEXT,new EpisodeScope("next"),34015,List.of(manifest("next"))));var first=RiteCreationState.initialize(next,new RiteCreationState.Basis(RiteCreationState.Initialization.RESTORED_FIRST,new EpisodeScope("first"),34014,List.of(manifest("first"))));assertEquals(later,full.withJava(first).legacyStore().orElseThrow());assertEquals(full.withJava(first),RiteCreationDomainState.decode(full.withJava(first).encode()));}
    @Test void opaqueOriginalQuarantineSurvivesValidRecaptureAndBlocksAllFinalConfirmations(){var full=new RiteCreationDomainState(javaBasis(),Optional.of(parsed("unknown"))).quarantine(new RiteCreationDomainState.OpaqueOriginalCapture(manifest("opaque"),"actual original bytes could not be classified"));var later=full.imported(new Imported(manifest("empty"),List.of()));assertEquals(full.unresolvedOpaqueOriginals(),later.unresolvedOpaqueOriginals());assertThrows(IllegalArgumentException.class,()->later.legacyBlocking(new RiteCreationState.Key(new EpisodeScope("anything"),34014,new SourceRite(26))));assertEquals(later,RiteCreationDomainState.decode(later.encode()));}
}
