package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls.*;

public final class CheckpointPublicCodecTest {
    private static PublicBindings.Value value(String json){return new PublicBindings.Value(new RawJson(json.getBytes(StandardCharsets.UTF_8)));}
    private static ExactRef ref(String name){return new ExactRef(Path.of(name).toAbsolutePath().toString(),7,"a".repeat(64));}
    private static ObservationIdentity frame(){
        return new ObservationIdentity("test-machine-1",new GameGeneration(13,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29),StrictJson.UINT64_MAX,BigInteger.valueOf(240)),
                        "snapshot:full64",StrictJson.UINT64_MAX,"episode-public"),1);
    }
    @Test void omittedAndNullFieldBranchesRemainDistinctAndBothBindTheCurrentFrame(){
        var missing=CheckpointPublicCodec.decode(new PublicBindings.Missing());
        assertInstanceOf(MissingRevision.class,missing.expectedRevision());assertTrue(missing.effectiveExpectedRevision().isEmpty());
        var nul=CheckpointPublicCodec.decode(value("{\"expected_revision\":null}"));
        assertInstanceOf(NullRevision.class,nul.expectedRevision());assertTrue(nul.effectiveExpectedRevision().isEmpty());
        assertNotEquals(missing,nul);
        assertEquals(missing,CheckpointPublicCodec.decode(PublicBindings.present(CheckpointPublicCodec.encodeRequest(missing))));
        assertEquals(nul,CheckpointPublicCodec.decode(PublicBindings.present(CheckpointPublicCodec.encodeRequest(nul))));
    }
    @Test void exactUint64StringAndLegacySafeNumericRevisionUseOneValidatedContract(){
        for(String json:new String[]{"{\"expected_revision\":0}","{\"expected_revision\":\"0\"}","{\"expected_revision\":9007199254740991}","{\"expected_revision\":\"18446744073709551615\"}"}){
            var parsed=CheckpointPublicCodec.decode(value(json));assertInstanceOf(ExactRevision.class,parsed.expectedRevision());
            assertEquals(parsed,CheckpointPublicCodec.decode(PublicBindings.present(CheckpointPublicCodec.encodeRequest(parsed))));
        }
        for(String token:new String[]{"true","0.0","-1","9007199254740992","\"01\"","\"+1\"","\"18446744073709551616\""})
            assertThrows(Exception.class,()->CheckpointPublicCodec.decode(value("{\"expected_revision\":"+token+"}")),token);
        assertThrows(Exception.class,()->CheckpointPublicCodec.decode(new PublicBindings.Null()));
        assertThrows(Exception.class,()->CheckpointPublicCodec.decode(value("{\"request_id\":\"caller-minted-restore\"}")));
        assertThrows(Exception.class,()->CheckpointPublicCodec.decode(value("{\"expected_revision\":1,\"checkpoint\":null}")));
    }
    @Test void publicPairRoundTripPreservesEveryIdentityDigitWithoutChangingBoundedNumericFields(){
        var identity=new FileStatIdentity(BigInteger.valueOf(7),"9007199254740993","13400000000000000100");
        var pair=new CheckpointPair(new CheckpointPair.FileWitness(ref("xar_checkpoint.ck3"),identity),
                new CheckpointPair.FileWitness(ref("driver.json"),identity),frame(),"lineage-public",1,"save-public",ref("ack.json"),Instant.parse("2026-10-24T00:00:00Z"));
        var json=CheckpointPublicCodec.pair(pair);assertEquals(pair,CheckpointPairCodec.decode(StrictJson.canonical(json)));
        assertTrue(json.get("history_index").isIntegralNumber());assertEquals("9007199254740993",json.get("save").get("identity").get("file_id").textValue());
        assertEquals("18446744073709551615",json.get("frame").get("frame").get("revision").textValue());
        assertEquals("134000000000000001",json.get("frame").get("game").get("creation_filetime").textValue());
    }
    @Test void unknownSaveAndRestoreCannotAcquireCheckpointOrPublicationSuccess(){
        var save=CheckpointPublicCodec.save(new SaveCall(new CheckpointResult.Unknown("save-unknown","native result unknown",Optional.empty()),Optional.empty(),Optional.empty()));
        var saved=StrictJson.parse(save.bytes());assertEquals("unknown",saved.get("status").textValue());assertFalse(saved.has("checkpoint"));
        assertFalse(saved.get("materialization").get("available").booleanValue());
        var source=new G2Source("test-machine-1","2026-10-24T00:00:00Z","fixture-codec-data",ref("source.txt"));
        var starting=new CheckpointRequest.Readiness(frame(),source,"public-session","lineage-public",true,true,true,"codec data only",ref("native.json"),Instant.parse("2026-10-24T00:00:00Z"));
        var restored=StrictJson.parse(CheckpointPublicCodec.restore(new RestoreCall(new RestoreCheckpointService.Unknown("restore-unknown","original launch unresolved"),starting,Optional.empty())).bytes());
        assertEquals("unknown",restored.get("status").textValue());assertFalse(restored.has("checkpoint"));assertFalse(restored.has("published_game"));
    }
    @Test void aLargeOriginalUnknownReasonUsesTheFullPublicDataLaneWithoutClaimingASavedCheckpoint(){
        String original="unchanged original 中".repeat(10000);
        var encoded=CheckpointPublicCodec.save(new SaveCall(new CheckpointResult.Unknown("large-unknown",original,Optional.empty()),Optional.empty(),Optional.empty()));
        assertTrue(encoded.bytes().length>65536);
        var row=org.xar.ck3.control.application.driver.PublicDataJson.object(encoded);
        assertEquals(original,row.get("reason").textValue());assertEquals(original,row.get("materialization").get("reason").textValue());
        assertEquals("unknown",row.get("status").textValue());assertFalse(row.has("checkpoint"));
    }
    @Test void largeResultSupportDoesNotExpandTheOriginalSmallPublicRequestBudget(){
        assertEquals("{}",new String(CheckpointPublicCodec.encodeRequest(new Request(new MissingRevision())).bytes(),StandardCharsets.UTF_8));
        String oversized="{\"expected_revision\":null,\"unexpected_original\":\""+ "x".repeat(70000)+"\"}";
        assertThrows(Exception.class,()->CheckpointPublicCodec.decode(value(oversized)));
    }
}
