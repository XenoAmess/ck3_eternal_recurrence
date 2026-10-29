package org.xar.ck3.control.application.ritecreation;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationState.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual legacy producer boundary, pure reducer and serialization. No native/CK3 or business qualification. */
public final class RiteCreationMigrationTest {
    private static RawJson original;
    private static final Frame FRAME=new Frame("actual-fixture",BigInteger.valueOf(17),BigInteger.valueOf(9),BigInteger.ONE,123,34014,12345,new EpisodeScope("episode-fixture"));
    private static final SourceRite SOURCE=new SourceRite(26);
    private static final ActionId ID=new ActionId("rite-action-"+"1".repeat(32));
    private static ExactRef ref(String value){return new ExactRef("D:/fixture/"+value,1,"a".repeat(64));}
    @BeforeAll static void actualOriginalProducerAndOriginalFixture()throws Exception{
        Path root=Path.of(System.getProperty("xar.rite.repository",System.getProperty("user.dir"))).toAbsolutePath();
        while(root!=null&&!Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/rite_creation_action_private_v1.py")))root=root.getParent();
        assertNotNull(root,"actual repository original Rite source required; absence cannot skip the migration regression");
        String program="""
            import ast,json,sys
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import rite_creation_action_private_v1 as action
            from xar_autoplayer.bridge.version_identity import CK3_12004
            path=root/'ck3_autonomous_player/tests/unit/test_rite_creation_action_private_v1.py'
            tree=ast.parse(path.read_text(encoding='utf-8'))
            selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('unavailable','synthetic_preview')]
            assert len(selected)==2
            ns={'action':action,'CK3_12004':CK3_12004,'DATE':12345,'ACTOR':34014,'RITE':26}
            exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),ns)
            raw=ns['synthetic_preview']()
            fields=action.request_fields('preview',26)
            binding={'native_revision':9,'connection_generation':1,'date_raw':12345,'played_character_id':34014}
            accepted=action.normalize_result(raw,binding=binding,fields=fields)
            assert accepted['business_outcome_verified'] is False and accepted['action_ready'] is False
            print(json.dumps(raw,separators=(',',':'),ensure_ascii=False))
            """;
        Process process=new ProcessBuilder(System.getProperty("xar.rite.python","python"),"-c",program,root.toString()).redirectErrorStream(true).start();
        boolean ended=process.waitFor(30,TimeUnit.SECONDS);if(!ended)process.destroyForcibly();assertTrue(ended,"original compatibility oracle timeout");byte[] bytes=process.getInputStream().readAllBytes();assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));original=raw(object(new RawJson(bytes)));
    }
    private static Result preview(){return result(original,FRAME,NativeFields.preview(SOURCE));}
    private static State cached(){State state=initialize(State.empty(),new Basis(Initialization.FRESH,FRAME.scope(),FRAME.actor(),List.of(ref("root"))));return observedPreview(state,new Preview(FRAME,SOURCE,ref("read"),ref("token")),preview());}
    private static Execute confirm(){return new Execute(FRAME.publicRevision(),SOURCE,new Confirm(new Identity("a".repeat(64)),Outcome.CREATE_FAITH));}
    private static Claim claim(){return new Claim(ID,FRAME,confirm(),ref("read"),Status.CLAIMED_RESULT_UNKNOWN_NO_RETRY,Optional.empty());}
    @Test void actualPythonProducerIsConsumedWithoutInventingBusinessProof(){Result actual=preview();actual.requireFinalPreview((Confirm)confirm().action());assertFalse(actual.businessOutcomeVerified());assertFalse(actual.actionReady());assertEquals(original,actual.original());assertEquals(1234,actual.nativeCommandTextBytes().orElseThrow().intValueExact());}
    @Test void closedBoundaryRejectsWrongMissingAndBoolIntegerTokens(){ObjectNode n=object(original).deepCopy();n.put("unknown",true);assertThrows(IllegalArgumentException.class,()->result(raw(n),FRAME,NativeFields.preview(SOURCE)));ObjectNode m=object(original).deepCopy();object(get(object(get(m,"rite_creation_action")),"frame")).put("played_character_id",true);assertThrows(IllegalArgumentException.class,()->result(raw(m),FRAME,NativeFields.preview(SOURCE)));ObjectNode x=object(original).deepCopy();object(get(x,"rite_creation_action")).remove("original_writer_inputs_observed");assertThrows(IllegalArgumentException.class,()->result(raw(x),FRAME,NativeFields.preview(SOURCE)));}
    @Test void publicU64RetainsExactIdentityAndBoundedFieldsStayNumbers(){Query request=query(new RawJson("{\"expected_revision\":\"18446744073709551615\",\"expected_source_rite_id\":26}".getBytes(StandardCharsets.UTF_8)));assertEquals(U64,request.expectedRevision());assertThrows(IllegalArgumentException.class,()->query(new RawJson("{\"expected_revision\":9007199254740992,\"expected_source_rite_id\":26}".getBytes(StandardCharsets.UTF_8))));ObjectNode encoded=object(publicResult(preview(),FRAME,ID,ref("receipt"),false,false));assertTrue(get(encoded,"snapshot_revision").isTextual());assertTrue(get(object(get(object(get(encoded,"rite_creation_action")),"frame")),"played_character_id").isIntegralNumber());assertEquals(original,preview().original());}
    @Test void changedRevisionTokenConnectionAndActionIdCannotEscapeOnceScope(){State old=start(cached(),claim(),preview());Frame newer=new Frame("new",BigInteger.valueOf(18),BigInteger.TEN,BigInteger.TWO,123,34014,12345,FRAME.scope());assertTrue(old.blocking(new Key(newer.scope(),newer.actor(),SOURCE)).isPresent());assertThrows(IllegalArgumentException.class,()->start(old,new Claim(new ActionId("rite-action-"+"2".repeat(32)),FRAME,confirm(),ref("read"),Status.CLAIMED_RESULT_UNKNOWN_NO_RETRY,Optional.empty()),preview()));assertEquals(old,decode(encode(old)));}
    @Test void nextAndRestoredFirstPreserveOriginalUnknownAndLateResultProof(){State unknown=start(cached(),claim(),preview());State next=initialize(unknown,new Basis(Initialization.NEXT,new EpisodeScope("next"),34015,List.of(ref("next-proof"))));State restored=initialize(next,new Basis(Initialization.RESTORED_FIRST,new EpisodeScope("first"),34014,List.of(ref("first-proof"))));assertEquals(unknown.claims(),restored.claims());assertTrue(restored.preview().isEmpty());assertEquals(restored,decode(encode(restored)));}
    @Test void matchingKnownNoDispatchReleasesOnlyAfterOriginalProofIsRetained(){State old=start(cached(),claim(),preview());ObjectNode nativeResult=object(original).deepCopy();nativeResult.put("read_only",false);ObjectNode leaf=object(get(nativeResult,"rite_creation_action"));leaf.put("operation","confirm_once").put("action_id","step-17-original");Result result=result(raw(nativeResult),FRAME,new NativeFields(RiteCreation.CONFIRM_ONCE,SOURCE,Optional.of(confirm().action()),Optional.of("step-17-original")));State released=originalResult(old,ID,result,new OriginalResult("step-17-original",ref("native-packet"),ref("canonical-receipt")));assertTrue(released.blocking(claim().key()).isEmpty());assertEquals(Status.KNOWN_NO_DISPATCH_RELEASED,released.find(ID).orElseThrow().status());assertEquals(released,decode(encode(released)));}
    @Test void dedicatedBeforeWriteProofIsDistinctFromNativeAck(){State old=start(cached(),claim(),preview());OriginalResult proof=new OriginalResult("step-17-original",ref("canonical-zero-write"),ref("canonical-receipt"),ResultKind.CANONICAL_ZERO_DISPATCH_BEFORE_WRITE);State released=beforeSendRejected(old,ID,proof);assertTrue(released.blocking(claim().key()).isEmpty());assertEquals(proof,released.find(ID).orElseThrow().result().orElseThrow());assertEquals(released,decode(encode(released)));assertThrows(IllegalArgumentException.class,()->beforeSendRejected(old,ID,new OriginalResult("step-17-original",ref("native-packet"),ref("canonical-receipt"))));}
    @Test void selectorsDoNotGrantPreviewOrNullFinalToken(){assertThrows(IllegalArgumentException.class,()->execute(raw(empty().put("operation","preview").put("expected_revision",17).put("expected_source_rite_id",26))));assertThrows(IllegalArgumentException.class,()->execute(raw(empty().put("operation","confirm_once").put("expected_revision",17).put("expected_source_rite_id",26).putNull("expected_preview_identity").put("expected_outcome_kind","create_faith"))));assertEquals(Duration.ZERO,collect(raw(empty().put("action_request_id",ID.value()))).timeout());}
}
