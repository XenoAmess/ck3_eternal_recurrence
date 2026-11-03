package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionModel;
import org.xar.ck3.control.wave2.governance.succession.SuccessionPolicy;

/** Real M3/reducer -> shared proof-result reader/public DATA. No parent, proof issuer, writer or episode admission is made. */
final class PublicInheritanceProofDataBoundaryTest {
    private static final Instant AT=Instant.parse("2026-11-03T00:00:00Z");
    private static final String MACHINE="public-inheritance-software",OLD_RUN="original-episode",NEW_RUN="successor-episode";
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final GameGeneration GAME=new GameGeneration(7,new PythonOnlyUInt64(U64));
    private static final G2Source SOURCE=new G2Source(MACHINE,AT.toString(),"public-data-only",ref("source",bytes("source DATA")));
    private record Input(LifecycleObservationPort.Snapshot snapshot,byte[] reconciliation) { }

    @Test void realMatchedInheritanceKeepsBothSignedActorRolesThroughProofResultAndPublicData() {
        for(int actor:new int[]{Integer.MIN_VALUE,Integer.MIN_VALUE+1,-2,0,1,Integer.MAX_VALUE}) {
            assertMatched(source(actor,74,74),actor,74);
            assertMatched(source(73,actor,actor),73,actor);
        }
    }

    @Test void zeroIdentityDoesNotBypassTheRealMatchedEstateRequirement() {
        Input input=source(73,0,74);
        var parsed=FullJsonTree.parse(input.reconciliation(),SuccessionCodec.MAX_BYTES);
        assertEquals(BigInteger.ZERO,NativeCharacterId.fromJson(parsed.get("actual_successor_character_id")).asBigInteger());
        assertEquals(OrdinaryCampaignGoal.Verdict.UNEXPECTED_SUCCESSOR,GoalCodec.decodeReconciliation(input.reconciliation()).verdict());
        byte[] original=input.snapshot().facts().driver().encode();
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(input.snapshot(),NEW_RUN,AT.plusSeconds(1)));
        assertArrayEquals(original,input.snapshot().facts().driver().encode());
    }

    @Test void absentInvalidRawOverflowAndNonintegerTokensCannotBecomeAContinuedActor() {
        Input original=source(73,74,74);byte[] before=original.snapshot().facts().driver().encode();
        for(JsonNode invalid:List.<JsonNode>of(IntNode.valueOf(-1),
                BigIntegerNode.valueOf(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                BigIntegerNode.valueOf(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),
                BigIntegerNode.valueOf(new BigInteger("4294967295")),BooleanNode.TRUE,DoubleNode.valueOf(0.0),
                TextNode.valueOf("0"),TextNode.valueOf("INVALID"),NullNode.instance)) {
            assertThrows(IllegalArgumentException.class,()->NativeCharacterId.fromJson(invalid));
            ObjectNode semantic=(ObjectNode)OpportunityJson.toNode(original.snapshot().semantic());
            ((ObjectNode)semantic.get("played_character")).set("character_id",invalid.deepCopy());
            var badSnapshot=observe(original.snapshot().facts(),semantic);
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(badSnapshot,NEW_RUN,AT.plusSeconds(1)));
            ObjectNode reconciliation=(ObjectNode)FullJsonTree.parse(original.reconciliation(),SuccessionCodec.MAX_BYTES);
            reconciliation.set("actual_successor_character_id",invalid.deepCopy());
            byte[] changed=FullJsonTree.encode(reconciliation,SuccessionCodec.MAX_BYTES);
            assertThrows(IllegalArgumentException.class,()->GoalCodec.decodeReconciliation(changed));
            assertArrayEquals(before,original.snapshot().facts().driver().encode());
        }
    }

    private static void assertMatched(Input input,int predecessor,int successor) {
        assertEquals(OrdinaryCampaignGoal.Verdict.MATCHED,GoalCodec.decodeReconciliation(input.reconciliation()).verdict());
        byte[] originalDriver=input.snapshot().facts().driver().encode();
        var originalAuxiliary=input.snapshot().facts().auxiliary();var originalSemantic=input.snapshot().semantic();
        var reduced=LifecycleReducer.continueSuccessor(input.snapshot(),NEW_RUN,AT.plusSeconds(1));
        JsonNode proofResult=LifecycleProofMaterialJson.result(reduced.result());
        requireActor(proofResult.get("predecessor_character_id"),predecessor);
        requireActor(proofResult.get("actual_successor_character_id"),successor);
        assertEquals(BigInteger.valueOf(successor),reduced.driver().session().actorId());
        assertEquals(NEW_RUN,reduced.driver().session().episodeRunId());
        var goal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)reduced.driver().campaignGoal()).json());
        assertEquals(predecessor,goal.originCharacterId());assertEquals(successor,goal.currentCharacterId());
        assertEquals(1,goal.progress().reconciledSuccessions());
        RawJson publicData=LifecyclePublicResultCodec.encode(LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,new RawJson(reduced.result()));
        JsonNode wire=LifecycleProofMaterialJson.result(publicData.bytes());
        requireActor(wire.get("predecessor_character_id"),predecessor);requireActor(wire.get("actual_successor_character_id"),successor);
        assertTrue(wire.get("revision").isTextual());assertEquals(U64.toString(),wire.get("revision").textValue());
        var decoded=LifecyclePublicResultCodec.decode(LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,publicData);
        assertEquals(proofResult,LifecycleProofMaterialJson.result(decoded.bytes()));
        assertEquals(0,proofResult.get("heir_gameplay_actions").intValue());
        assertFalse(proofResult.get("ck3_command_submitted").booleanValue());assertFalse(proofResult.get("process_restarted").booleanValue());
        assertArrayEquals(originalDriver,input.snapshot().facts().driver().encode());
        assertEquals(originalAuxiliary,input.snapshot().facts().auxiliary());assertEquals(originalSemantic,input.snapshot().semantic());
    }

    private static void requireActor(JsonNode value,int expected) {
        assertTrue(value.isIntegralNumber());assertEquals(BigInteger.valueOf(expected),value.bigIntegerValue());
        NativeCharacterId signed=NativeCharacterId.fromJson(value);
        assertEquals(expected,signed.value());
    }

    private static Input source(int predecessor,int successor,int expectedHeir) {
        var empty=new DriverStateSnapshot.NullValue();
        ObjectNode lifecycle=StrictJson.object().put("schema","xar.ck3.succession-lifecycle-binding/v1")
                .put("lifecycle","ordinary_campaign_succession").put("xar_enabled","xar_off")
                .put("pact_contract","absent_by_fresh_campaign_xar_off_contract").put("source","public-software")
                .put("environment_sha256","a".repeat(64));
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("public-data-pipe",GAME.pid(),
                BigInteger.valueOf(predecessor),OLD_RUN),List.of(),empty,empty,empty,empty,
                new DriverStateSnapshot.Value(FullJsonTree.encode(lifecycle,65536)),
                new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("public-inheritance",predecessor))),
                new DriverStateSnapshot.Value(bytes("[]")));
        var facts=new DriverSnapshotFacts.Known(driver,new DriverSnapshotFacts.Stamp(3,4,GAME,OLD_RUN,sha(driver.encode())),
                ref("predecessor-driver",driver.encode()),List.of(),new OpportunityJson.Obj(Map.of("family_marriage_ledger",OpportunityJson.Nil.INSTANCE)),
                Optional.empty(),Optional.empty());
        var before=new SuccessionModel.Frame("before",U64.subtract(BigInteger.ONE),U64.subtract(BigInteger.TWO),100);
        var after=new SuccessionModel.Frame("after",U64,U64.subtract(BigInteger.ONE),100);
        var title=new SuccessionModel.Title(1,BigInteger.TWO,new SuccessionModel.WireObject(bytes("{\"title_id\":1,\"tier_raw\":2}")));
        var rows=List.of(new SuccessionModel.TitleRow(title,expectedHeir,true));
        var frozen=SuccessionPolicy.freeze(new SuccessionModel.TurnBundle(before,new SuccessionModel.Actor(predecessor,true),
                rows,expectedHeir,SuccessionModel.RiskState.SINGLE_SUCCESSOR),OLD_RUN,predecessor);
        var matched=SuccessionPolicy.reconcile(frozen,new SuccessionModel.Snapshot(after,OLD_RUN,predecessor,true,true,true,
                "played_character_changed",new SuccessionModel.Actor(successor,true),false,false,SuccessionModel.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION),
                new SuccessionModel.TurnBundle(after,new SuccessionModel.Actor(successor,true),rows,expectedHeir,SuccessionModel.RiskState.SINGLE_SUCCESSOR));
        byte[] reconciliation=SuccessionCodec.encodeReconciliation(matched);
        ObjectNode semantic=StrictJson.object().put("snapshot_id",after.snapshotId()).put("revision",after.revision())
                .put("native_revision",after.nativeRevision()).put("date_raw",after.dateRaw()).put("episode_run_id",OLD_RUN)
                .put("paused",true).put("map_ready",true).put("one_life_terminal_reason","played_character_changed");
        semantic.putObject("played_character").put("character_id",successor).put("alive",true);
        semantic.set("succession_reconciliation",FullJsonTree.parse(reconciliation,SuccessionCodec.MAX_BYTES));semantic.putNull("one_life_settlement");
        return new Input(observe(facts,semantic),reconciliation);
    }

    private static LifecycleObservationPort.Snapshot observe(DriverSnapshotFacts.Known facts,ObjectNode semantic) {
        byte[] state=FullJsonTree.encode(semantic,DriverJson.MAX_NATIVE_BYTES);
        ObjectNode envelope=StrictJson.object().put("type","state_snapshot").put("protocol_version",1)
                .put("snapshot_id",semantic.get("snapshot_id").textValue()).put("revision",semantic.get("native_revision").bigIntegerValue());
        envelope.set("state",semantic.deepCopy());byte[] json=FullJsonTree.encode(envelope,DriverJson.MAX_NATIVE_BYTES);
        byte[] packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE,GAME,BigInteger.ONE,"public-data-session"),
                semantic.get("snapshot_id").textValue(),semantic.get("native_revision").bigIntegerValue(),new RawJson(state),packet,AT);
        var typed=OpportunityJson.object(OpportunityJson.parse(state),"public software successor semantic");
        return new LifecycleObservationPort.Snapshot(actual,SOURCE,typed,facts,ref("successor-packet",packet));
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(String name,byte[] value){return new ExactRef("D:/software-public-inheritance/"+name,value.length,sha(value));}
    private static String sha(byte[] value) {
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
        catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}
    }
}
