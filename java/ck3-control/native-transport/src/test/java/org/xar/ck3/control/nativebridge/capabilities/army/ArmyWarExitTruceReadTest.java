package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeWarExitEffects;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic original packets exercise actual installed factory/decoder/consumer. They grant no Root lease or Game credit. */
final class ArmyWarExitTruceReadTest {
    private static final Instant NOW=Instant.parse("2026-10-24T01:00:00Z"),DEADLINE=NOW.plusSeconds(60);
    private static final ExactRef SOURCE=ref("source");
    private static final G2Source BUILD=new G2Source("synthetic-war-exit-no-game",NOW.toString(),"1.20.0.4",SOURCE);
    private static final PlanningReadPort NO_IO=new PlanningReadPort(){
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("pure replay must not query Native");}
    };
    @Test void installedOriginalPendingFactoryUsesOnlyItsDedicatedReconProfileAndExactPrimitive() {
        var f=fixture("surrender-war-7");var contract=f.issued().contract();
        ArmyWarExitTruceReads.requireProfile(contract);assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION,contract.guardMode());
        assertEquals("query-raiktor-actual-truce-expiry-v1-202",contract.prepare(f.issued().request(),"truce-query").step());
        assertEquals(f.selected().identity(),f.issued().request().origin().requireReconciliation());
        assertEquals("22",OpportunityJson.toNode(f.issued().request().arguments()).get("expected_revision").textValue());
        var ordinary=new PlanningReadRequest(f.selected().actualAfter().identity(),BUILD,"session",contract.operation(),f.issued().request().arguments(),DEADLINE);
        assertThrows(IllegalArgumentException.class,()->contract.prepare(ordinary,"forbidden-gameplay-borrow"));
    }
    @Test void actualNativePacketToInstalledDecoderAndOutcomeConsumerPreservesTruceAndUnattributedMoney() throws IOException {
        var f=fixture("offer-white-peace-7");var packet=packet(true);var original=receipt(f,packet);
        var actual=f.reads().replay(f.catalog(),f.selected(),original);assertTrue(actual.hasTruce());
        assertEquals(9000,((ArmyTypes.Present<Integer>)actual.expiryDateRaw()).value());
        var input=ArmyJson.empty();input.set("before_snapshot",OpportunityJson.toNode(f.selected().originalBefore().semantic()));
        input.set("post_snapshot",OpportunityJson.toNode(f.selected().actualAfter().semantic()));
        input.set("action_result",ArmyJson.empty().put("step","offer-white-peace-7").put("accepted",true));
        input.putNull("claims_result");input.putNull("title_holder_results");input.set("truce_result",packet.get("result"));
        byte[] unchanged=ArmyJson.bytes(packet.get("result"));
        // The raw native producer has no SDK queried_* fields. Its old direct path was unavailable.
        assertInstanceOf(OrdinaryWarExitObservation.TruceUnavailable.class,
                OrdinaryWarExitObservationCodec.decodeAndCompose(ArmyJson.bytes(input)).truce());
        var consumed=OrdinaryWarExitObservationCodec.composeNativeTruce(input.get("before_snapshot"),input.get("post_snapshot"),
                input.get("action_result"),packet.get("result"));
        assertArrayEquals(unchanged,ArmyJson.bytes(packet.get("result")),"material projection cannot rewrite the retained native token");
        var directed=assertInstanceOf(OrdinaryWarExitObservation.NativeTruce.class,consumed.truce());
        assertEquals(101,directed.ownerCharacterId());assertEquals(202,directed.towardCharacterId());assertEquals(9000,directed.expiryDateRaw());
        var encoded=ArmyJson.parse(OrdinaryWarExitObservationCodec.encode(consumed));
        assertTrue(encoded.get("observed_result_identity").isNull());
        assertEquals("unproven",encoded.path("resources").path("gold").path("action_attribution").textValue());
        assertEquals(BigInteger.valueOf(-100000),encoded.path("resources").path("gold").path("delta_raw").bigIntegerValue());
        assertEquals(actual,f.issued().contract().decode(original));assertEquals(actual,f.issued().contract().replay(original));
        assertEquals("truce-query",original.requestId());assertEquals(DEADLINE,original.request().deadline());
    }
    @Test void successfulNoTruceIsAnObservedNegativeRatherThanASettlementFormula() throws IOException {
        var f=fixture("enforce-demands-7");var value=f.reads().replay(f.catalog(),f.selected(),receipt(f,packet(false)));
        assertEquals(ArmyClosedReads.TruceStatus.NO_TRUCE,value.status());assertFalse(value.hasTruce());assertFalse(value.readiness());
        assertInstanceOf(ArmyTypes.NullValue.class,value.expiryDateRaw());
        var consumed=OrdinaryWarExitObservationCodec.composeNativeTruce(
                OpportunityJson.toNode(f.selected().originalBefore().semantic()),OpportunityJson.toNode(f.selected().actualAfter().semantic()),
                ArmyJson.empty().put("step","enforce-demands-7").put("accepted",true),packet(false).get("result"));
        var observed=assertInstanceOf(OrdinaryWarExitObservation.NativeTruce.class,consumed.truce());
        assertEquals(OrdinaryWarExitObservation.TruceStatus.NO_TRUCE,observed.status());assertNull(observed.expiryDateRaw());
    }
    @Test void wrongSourceFrameTargetNativeTypeOrMissingFieldCannotReplay() {
        var f=fixture("surrender-war-7");
        var bad=packet(true);((ObjectNode)bad.path("result").path("raiktor_actual_truce_expiry")).put("toward_character_id",203);
        assertThrows(IllegalArgumentException.class,()->f.reads().replay(f.catalog(),f.selected(),receipt(f,bad)));
        var wrong=packet(true);((ObjectNode)wrong.path("result")).put("snapshot_revision",true);
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(receipt(f,wrong)));
        var missing=packet(true);((ObjectNode)missing.path("result").path("raiktor_actual_truce_expiry")).remove("expiry_date_raw");
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(receipt(f,missing)));
        var different=f.issued().request();var changed=PlanningReadRequest.newReconciliation(f.selected().identity(),different.operation(),
                different.arguments().with("toward_character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(203))),DEADLINE);
        assertThrows(IllegalArgumentException.class,()->NativeWarExitEffects.requireOriginalRequest(changed,f.selected().original(),f.selected().attempt(),f.selected().originalBefore(),f.selected().actualAfter()));
    }
    @Test void originalUint64SequenceRoundTripsThroughTheExistingPublicTypedCodecWithoutNumberCoercion() throws IOException {
        var f=fixture("surrender-war-7");var raw=packet(true);var maximum=new BigInteger("18446744073709551615");
        ((ObjectNode)raw.get("result")).put("query_sequence",maximum);var original=receipt(f,raw);
        var actual=f.issued().contract().replay(original);assertEquals(maximum,actual.frame().sequence().value());
        var wire=ArmyClosedReadCodec.encode(actual,f.selected().facts());
        assertEquals(maximum.toString(),ArmyJson.parse(wire.bytes()).get("query_sequence").textValue());
        assertEquals(actual,ArmyClosedReadCodec.decodePublic(f.selected().call(),f.selected().facts(),wire));
        assertEquals(maximum,ArmyJson.parse(original.original().originalResultToken().orElseThrow().bytes()).get("query_sequence").bigIntegerValue());
        var bad=packet(true);((ObjectNode)bad.path("result").path("raiktor_actual_truce_expiry")).put("executable_sha256","0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(receipt(f,bad)));
        var floating=packet(true);((ObjectNode)floating.path("result").path("raiktor_actual_truce_expiry")).put("owner_character_id",101.0);
        assertThrows(IllegalArgumentException.class,()->f.issued().contract().replay(receipt(f,floating)));
    }
    @Test void sameFrameWarPresenceOrDifferentOriginalCannotAcquireTheTruceSelector() {
        var f=fixture("surrender-war-7");
        assertTrue(NativeWarExitEffects.truceQuery(f.selected().original(),f.selected().originalBefore(),frame(false,true)).isEmpty());
        var query=NativeWarExitEffects.truceQuery(f.selected().original(),f.selected().originalBefore(),f.selected().actualAfter()).orElseThrow();
        assertEquals(202,query.towardCharacterId());
        var wrong=new ActionState.Attempt("another-original",NOW,f.selected().attempt().guard(),f.selected().attempt().preparedRequest());
        assertThrows(IllegalArgumentException.class,()->NativeWarExitEffects.requireOriginalRequest(f.issued().request(),f.selected().original(),wrong,f.selected().originalBefore(),f.selected().actualAfter()));
    }
    @Test void nativeEnvelopeFrameTypesMissingFieldsAndInjectedSdkMetadataCannotBeRebound() {
        var f=fixture("surrender-war-7");
        var before=OpportunityJson.toNode(f.selected().originalBefore().semantic());
        var after=OpportunityJson.toNode(f.selected().actualAfter().semantic());
        var action=ArmyJson.empty().put("step","surrender-war-7").put("accepted",false);
        for(int mode=0;mode<7;mode++) {
            ObjectNode raw=(ObjectNode)packet(true).get("result");
            switch(mode) {
                case 0 -> raw.put("snapshot_revision",31);
                case 1 -> raw.put("snapshot_revision",true);
                case 2 -> raw.put("snapshot_revision",32.0);
                case 3 -> raw.put("date_raw",78);
                case 4 -> raw.remove("date_raw");
                case 5 -> raw.put("queried_snapshot_id","forged-sdk-source");
                default -> raw.put("queried_revision",22);
            }
            byte[] unchanged=ArmyJson.bytes(raw);
            assertThrows(IllegalArgumentException.class,()->OrdinaryWarExitObservationCodec.composeNativeTruce(before,after,action,raw));
            assertArrayEquals(unchanged,ArmyJson.bytes(raw));
        }
    }
    @Test void serializedOriginalNativeResultAndEitherActionAckKeepFactsSeparateFromCausalCredit() throws IOException {
        var f=fixture("offer-white-peace-7");
        for(boolean acknowledged:List.of(false,true)) {
            var original=receipt(f,packet(true));f.reads().replay(f.catalog(),f.selected(),original);
            byte[] retained=original.original().originalResultToken().orElseThrow().bytes();
            var raw=ArmyJson.parse(retained);
            var material=OrdinaryWarExitObservationCodec.composeNativeTruce(
                    OpportunityJson.toNode(f.selected().originalBefore().semantic()),OpportunityJson.toNode(f.selected().actualAfter().semantic()),
                    ArmyJson.empty().put("step","offer-white-peace-7").put("accepted",acknowledged),raw);
            var encoded=ArmyJson.parse(OrdinaryWarExitObservationCodec.encode(material));
            assertEquals(acknowledged,encoded.get("command_acknowledged").booleanValue());
            assertTrue(encoded.get("war_absence_observed").booleanValue());
            assertTrue(encoded.get("observed_result_identity").isNull());
            assertEquals("available",encoded.path("truce").path("status").textValue());
            assertEquals("not_observed",encoded.path("claims").path("status").textValue());
            assertEquals("not_observed",encoded.path("titles").path("status").textValue());
            assertEquals("unproven",encoded.path("resources").path("gold").path("action_attribution").textValue());
            assertArrayEquals(retained,original.original().originalResultToken().orElseThrow().bytes());
        }
    }
    private record Fixture(ArmyWarExitTruceReads reads,RootReadContractCatalog catalog,ArmyWarExitTruceReads.Selection selected,ArmyWarExitTruceReads.Issued issued) { }
    private static Fixture fixture(String operation) {
        var before=frame(true,true);var after=frame(false,false);var op=new OperationKey(operation);
        var expected=new ExpectedPostcondition(1,before.identity(),BUILD,OrdinaryWarExitObservation.SCHEMA,
                List.of(new ExpectedInteger(new FieldKey("war_id"),BigInteger.valueOf(7)),new ExpectedBoolean(new FieldKey("war_absence_observed"),true)));
        var command=new ActionCommand("original-war-exit",before.identity(),BUILD,"session",op,new OpportunityJson.Obj(java.util.Map.of()),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        var guard=new GuardEvidence(before.identity(),BUILD,"session",BigInteger.ONE,op,before.originalEvidence(),ref("hello"),"synthetic-no-authority",NOW,DEADLINE);
        var attempt=new ActionState.Attempt("original-primitive",NOW,guard,new NativeRequest(op.value(),Optional.empty(),new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var pending=new ReconciliationIdentity.Pending(command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),before.identity(),ref("pending-receipt"),ref("driver"));
        var evidence=new ReconciliationIdentity.Evidence(after.originalEvidence(),ref("hello"),ref("heartbeat"),ref("manifest"),ref("driver"),ref("qualification"));
        var identity=new ReconciliationIdentity(after.identity(),BUILD,"session",BigInteger.ONE,pending,evidence,NOW.plusSeconds(1));
        var selected=new ArmyWarExitTruceReads.Selection(identity,command,attempt,before,after,DEADLINE);
        var reads=new ArmyWarExitTruceReads(new ArmyWarExitTruceReads.Sources(SOURCE,SOURCE),NO_IO);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());return new Fixture(reads,catalog,selected,reads.issue(catalog,selected));
    }
    private static Complete frame(boolean before,boolean warPresent) {
        int revision=before?21:22;int nativeRevision=before?31:32;
        var key=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(77)),"native:"+nativeRevision,BigInteger.valueOf(revision),"war-exit-fixture");
        var identity=new ObservationIdentity(BUILD.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),key,1);
        var n=ArmyJson.empty().put("paused",true).put("map_ready",true).put("snapshot_id","native:"+nativeRevision)
                .put("revision",revision).put("native_revision",nativeRevision).put("date_raw",77).put("episode_run_id","war-exit-fixture");
        n.putObject("played_character").put("character_id",101).put("alive",true);
        var hello=n.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",1).putObject("hello");
        hello.put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",OrdinaryWarExitObservation.EXE_SHA256);
        var wars=n.putArray("active_wars");if(warPresent){var war=wars.addObject().put("war_id",7).put("player_side","attacker").put("primary_opponent_character_id",202);war.putArray("targeted_title_ids").add(17);}
        for(var resource:List.of("gold","prestige","piety"))n.putObject("played_character_"+resource).put("raw",before?1000000:900000).put("scale",100000);
        var semantic=DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES);
        return new Complete(identity,BUILD,"session",BigInteger.ONE,semantic,ref(before?"before-native":"after-native"),NOW.plusSeconds(before?0:1),(before?"b":"c").repeat(64));
    }
    private static ObjectNode packet(boolean hasTruce) {
        var top=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","truce-query").put("ok",true);
        var result=top.putObject("result").put("step","query-raiktor-actual-truce-expiry-v1-202").put("accepted",true)
                .put("query_sequence",5).put("snapshot_revision",32).put("date_raw",77).put("backend_id","native-headless").put("read_only",true);
        var payload=result.putObject("raiktor_actual_truce_expiry").put("schema_version",1).put("backend_id","ck3-1.20.0.4-native-player-truce-expiry-v1")
                .put("ck3_build","1.20.0.4").put("executable_sha256",OrdinaryWarExitObservation.EXE_SHA256)
                .put("status",hasTruce?"available":"no_truce").put("snapshot_revision",32).put("current_date_raw",77)
                .put("owner_character_id",101).put("toward_character_id",202).put("native_has_truce",hasTruce).put("actual_expiry_observable",hasTruce)
                .put("same_frame_stable",true).put("readiness",hasTruce).put("temporal_semantics","post_application_persisted_relation_state");
        if(hasTruce){payload.put("expiry_date_raw",9000);payload.putNull("unavailable_reason");}
        else{payload.putNull("expiry_date_raw");payload.put("unavailable_reason","native_has_truce_false");}return top;
    }
    private static PlanningReadReceipt receipt(Fixture f,ObjectNode packet) throws IOException {
        var selection=f.selected();var id=selection.identity();var guard=new GuardEvidence(new CommandOrigin.Reconciliation(id),BUILD,"session",BigInteger.ONE,
                f.issued().contract().operation(),id.nativeEvidence(),id.capabilityEvidence(),"synthetic-no-authority",NOW,DEADLINE,List.of(ref("qualification")));
        var checked=new PlanningReadGuard(guard,new PlanningReadGuard.Reconciliation(),id.bindingSha256());
        var raw=new RawJson(ArmyJson.bytes(packet));var ack=new NativeActionPort.AckReceived("truce-query",true,Optional.of(new RawJson(ArmyJson.bytes(packet.get("result")))),raw,NativeWire.packet(raw.bytes()));
        return new PlanningReadReceipt(f.issued().request(),f.issued().contract().contractId(),"truce-query",checked,checked,ack);
    }
    private static ExactRef ref(String name){return new ExactRef("synthetic-data-only/"+name,1,ActionCodec.sha256(name.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
}
