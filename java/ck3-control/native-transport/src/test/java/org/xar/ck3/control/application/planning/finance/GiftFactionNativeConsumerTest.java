package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.ArrayList;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.giftoutcome.ExistingGiftOutcomeAdapter;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Private raw uint32 software originals remain distinct from public signed int32 frames.
 * Native files are copied unchanged; this grants no private action/opaque/writer admission.
 */
final class GiftFactionNativeConsumerTest {
    private static final BigInteger RAW_MAX=new BigInteger("4294967294");
    private static final BigInteger SENTINEL=new BigInteger("4294967295");
    private static final ExactRef REF=new ExactRef("D:/fixture/raw32-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-30T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private static byte[] fixture(String relative)throws Exception {
        try(var stream=GiftFactionNativeConsumerTest.class.getResourceAsStream("/finance/faction-generation-native90/"+relative)) {
            assertNotNull(stream,"retained actual Native original required: "+relative);return stream.readAllBytes();
        }
    }
    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,
                new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static GiftColdReadService coldOwner() {
        return new GiftColdReadService(new FinanceReadContracts.Registration(REF,
                new FinanceReadContracts.Permission(Optional.empty(),GiftColdReadService.OPERATION.value(),
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    private static ProposalLifecycle.ObservationIdentity before(BigInteger signedPlayer) {
        return before(signedPlayer,BigInteger.ONE,BigInteger.valueOf(53175816));
    }
    private static ProposalLifecycle.ObservationIdentity before(BigInteger signedPlayer,BigInteger revision,BigInteger date) {
        return new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(signedPlayer,revision,
                    date),"native:raw32",revision,"raw32-episode"),1);
    }
    private static PlanningReadRequest request(OperationKey operation,BigInteger signedPlayer,Obj args) {
        return new PlanningReadRequest(before(signedPlayer),SOURCE,"raw32-session",operation,args,DEADLINE);
    }
    private static Baseline baseline(BigInteger actor,BigInteger recipient,List<BigInteger> members) {
        return new Baseline(BigInteger.valueOf(83886083),recipient,BigInteger.ONE,BigInteger.ONE,
                BigInteger.valueOf(53175816),actor,BigInteger.valueOf(20000000),BigInteger.ZERO,
                BigInteger.valueOf(11000000),BigInteger.valueOf(7000000),members,
                BigInteger.valueOf(7500000),BigInteger.valueOf(35));
    }
    private static PendingAction pending(Baseline baseline) {
        return new PendingAction("raw32-native-action","raw32-episode","R1",
                new ProcessIdentity(BigInteger.TEN,"authored-old-birth"),baseline,BigInteger.ZERO,
                "a".repeat(64),PendingStatus.SUBMISSION_STARTED_UNCONFIRMED,Optional.empty());
    }










    private record Original(NativeWire.CommandResult wire,ObjectNode result,ObjectNode post) { }
    private static Original original(String world,String step)throws Exception {
        byte[] packet=fixture("packets/"+world+"/"+step+".json.packet.bin");
        var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        assertArrayEquals(packet,wire.packet().value());
        assertArrayEquals(Arrays.copyOfRange(packet,4,packet.length),wire.payload().value());
        ObjectNode result=(ObjectNode)StrictJson.parse(wire.result().token().orElseThrow().value());
        return new Original(wire,result,(ObjectNode)result.path("native").path("observation"));
    }
    private static PlanningReadReceipt readReceipt(Original original,String contractId,OperationKey operation,Obj args) {
        var post=original.post();BigInteger raw=post.get("player_character_id").bigIntegerValue();
        BigInteger signed=BigInteger.valueOf((int)raw.longValueExact());
        var identity=before(signed,post.get("snapshot_revision").bigIntegerValue(),post.get("observed_date_raw").bigIntegerValue());
        var request=new PlanningReadRequest(identity,SOURCE,"raw32-session",operation,args,DEADLINE);
        var wire=original.wire();
        var ack=new NativeActionPort.AckReceived(wire.requestId(),wire.nativeOk(),
                wire.result().token().map(value->new RawJson(value.value())),new RawJson(wire.payload().value()),wire.packet().value());
        var binding=new GuardEvidence(identity,SOURCE,request.sessionId(),BigInteger.ONE,operation,REF,REF,
                "software-native-raw32-source",DEADLINE.minusSeconds(30),DEADLINE);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,contractId,wire.requestId(),guard,guard,ack);
    }
    private static Obj domainObject(JsonNode value) {return DriverJson.object(StrictJson.canonical(value),RawJson.MAXIMUM_BYTES);}
    private static ObjectNode recovery(JsonNode post) {
        ObjectNode result=StrictJson.object().put("schema_version",1).put("status","independent_read_complete")
                .put("private_build",true).put("advertised",false).put("new_process_confirmed",true)
                .put("new_round_id","R2").put("new_bridge_pid",11).put("new_bridge_creation_date","authored-new-birth")
                .put("episode_run_id","raw32-episode").put("paused",true).put("map_ready",true)
                .put("independent_faction_storage_lookup_complete",true).put("independent_recipient_lookup_complete",true)
                .put("selected_from_current_targeting_vector",false).put("save_is_pre_action_checkpoint",false);
        result.putNull("selected_save_sha256");result.set("post_observation",post);return result;
    }
    @ParameterizedTest
    @org.junit.jupiter.params.provider.MethodSource("org.xar.ck3.control.application.planning.finance.FactionNativeWorlds#worlds")
    void actualWriteFramePacketsReachOriginalDecoderPendingAndColdAndResolvedConsumers(String world)throws Exception {
        Original preview=original(world,FinanceReadContracts.Query.FACTION_GIFT.operation().value());
        Original submit=original(world,"private-submit-faction-gift-member-v1");
        Original receipt=original(world,FinanceReadContracts.Query.FACTION_GIFT_RECEIPT.operation().value());
        Original cold=original(world,GiftColdReadService.OPERATION.value());
        var definitions=definitions();var previewContract=definitions.contract(FinanceReadContracts.Query.FACTION_GIFT);
        var previewRead=readReceipt(preview,previewContract.contractId(),previewContract.operation(),new Obj(Map.of()));
        var decodedPreview=previewContract.replay(previewRead);
        assertArrayEquals(preview.wire().payload().value(),decodedPreview.originalFrame());
        var submitAck=GiftPendingCodec.decodeAck(StrictJson.canonical(submit.result().path("native").get("ack")));
        String requestId=submitAck.requestId();
        ObjectNode begin=StrictJson.object().put("request_id",requestId).put("episode_run_id","raw32-episode")
                .put("source_round_id","R1").put("source_bridge_pid",10).put("source_bridge_creation_date","authored-old-birth")
                .put("minimum_gold_reserve_raw",0).put("checkpoint_sha256_before_submit","a".repeat(64));
        begin.set("observation",preview.post());
        var begun=GiftPendingReducer.begin(Ledger.empty(),GiftPendingCodec.decodeBegin(StrictJson.canonical(begin)));
        var acknowledged=GiftPendingReducer.markAck(begun,requestId,submitAck);
        assertEquals(acknowledged,GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(acknowledged)));
        var receiptContract=definitions.contract(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT);
        var receiptRead=readReceipt(receipt,receiptContract.contractId(),receiptContract.operation(),new Obj(Map.of()));
        var decodedReceipt=receiptContract.replay(receiptRead);
        var completed=GiftPendingReducer.complete(acknowledged,requestId,GiftPendingCodec.decodeReceipt(
                encode(decodedReceipt.result().get("receipt"))));
        assertTrue(completed.pending().isEmpty());
        assertThrows(IllegalArgumentException.class,()->GiftPendingReducer.begin(completed,GiftPendingCodec.decodeBegin(StrictJson.canonical(begin))));
        Obj args=OrdinaryFinanceCollector.obj("source_faction_id",new IntegerValue(preview.post().get("queried_source_faction_id").bigIntegerValue()),
                "recipient_character_id",new IntegerValue(preview.post().get("recipient_character_id").bigIntegerValue()));
        var owner=coldOwner();var coldRead=readReceipt(cold,owner.contract().contractId(),GiftColdReadService.OPERATION,args);
        var decodedCold=owner.contract().replay(coldRead);
        assertArrayEquals(cold.wire().payload().value(),decodedCold.receipt().original().originalFrame().bytes());
        assertEquals(preview.post().get("player_character_id").bigIntegerValue(),decodedCold.material().playerCharacterId().value());
        var resolved=GiftColdRecovery.resolve(acknowledged,requestId,
                GiftColdRecoveryCodec.decodeRecovery(StrictJson.canonical(recovery(toNode(decodedCold.originalPost())))));
        assertInstanceOf(GiftColdRecovery.Applied.class,resolved.result());
        assertFalse(resolved.result().originalRequestReplayAllowed());assertFalse(resolved.result().actionRetryAllowed());
        assertEquals(completed,resolved.ledger());
        assertEquals(resolved.ledger(),GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(resolved.ledger())));
        // The retained receipt and Native packet are original. Session/episode metadata, the public
        // SEM and Driver history wrappers are authored DATA; the alert's result token below is actual Native.
        var identity=coldRead.request().before();var nativeFrame=identity.frame().identity();
        ObjectNode semantic=StrictJson.object().put("snapshot_id",identity.frame().snapshotId()).put("revision",identity.frame().revision())
                .put("native_revision",nativeFrame.nativeRevision()).put("date_raw",nativeFrame.dateRaw())
                .put("episode_run_id","raw32-episode").put("paused",true).put("map_ready",true);
        semantic.putObject("played_character").put("character_id",nativeFrame.player()).put("alive",true);
        semantic.putArray("active_wars");semantic.putArray("player_armies");semantic.putNull("active_event");semantic.putNull("pending_character_interaction");
        ObjectNode historySubmit=StrictJson.object().put("command","private-submit-faction-gift-member-v1").put("ok",true);
        historySubmit.putObject("result").set("pending_ledger",StrictJson.parse(GiftPendingCodec.encodeLedger(acknowledged)));
        ObjectNode historyReceipt=StrictJson.object().put("command",FinanceReadContracts.Query.FACTION_GIFT_RECEIPT.operation().value()).put("ok",true);
        historyReceipt.set("result",receipt.result());
        var postAlert=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(fixture("packets/"+world+"/query-player-faction-alerts-cold-v1.json.packet.bin")));
        ObjectNode historyAlert=StrictJson.object().put("command",FinanceReadContracts.Query.FACTION_ALERTS.operation().value()).put("ok",true);
        historyAlert.set("result",StrictJson.parse(postAlert.result().token().orElseThrow().value()));
        var actualAlert=org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeCodec.historyEntry(StrictJson.canonical(historyAlert)).orElseThrow().directAlert().orElseThrow();
        assertEquals(Optional.of(nativeFrame.nativeRevision()),actualAlert.snapshotRevision(),"actual post-alert native revision");
        assertEquals(Optional.of(nativeFrame.dateRaw()),actualAlert.dateRaw(),"actual post-alert date");
        assertEquals(Optional.of(nativeFrame.player()),actualAlert.playerId(),"actual post-alert player");
        var rows=new ArrayList<DriverStateSnapshot.HistoryEntry>();long index=0;
        for(JsonNode row:List.of(historySubmit,historyReceipt,historyAlert)) {
            ObjectNode retained=((ObjectNode)row).deepCopy();retained.put("index",++index);
            rows.add(new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(StrictJson.canonical(retained))));
        }
        var absent=new DriverStateSnapshot.NullValue();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-raw32-pipe",123,
                nativeFrame.player(),"raw32-episode"),rows,absent,absent,absent,absent,absent,absent,absent);
        var frame=new Complete(identity,SOURCE,"raw32-session",BigInteger.ONE,domainObject(semantic),REF,DEADLINE.minusSeconds(10),"c".repeat(64));
        var observed=GiftResolvedEvidence.recompute(new GiftResolvedEvidence.Inputs(frame,driver,coldRead,Optional.empty(),requestId),
                owner.contract(),Optional.empty());
        JsonNode outcome=StrictJson.parse(observed.result().bytes());
        assertEquals("observed",outcome.path("status").textValue());
        assertEquals("still_member",outcome.path("faction_outcome").textValue());
        assertEquals("observed",outcome.path("current_alert").path("status").textValue());
        assertEquals(BigInteger.valueOf(preview.post().get("queried_source_faction_id").intValue()),outcome.path("current_alert").path("row").get("faction_id").bigIntegerValue());
        assertEquals(preview.post().get("player_character_id"),outcome.path("original").get("player_character_id"));
        assertFalse(outcome.path("gift_submit_performed").booleanValue());assertFalse(outcome.path("pending_resolution_performed").booleanValue());
        JsonNode publicRows=preview.result().path("native").path("direct_targeting_rows");
        assertEquals(nativeFrame.player(),publicRows.get("player_character_id").bigIntegerValue(),"public targeting rows retain signed IDs");
    }
    @Test void publishedNativeZeroRunsOrdinaryCollectorThroughColdResolvedConsumer()throws Exception {
        String world="published-zero";
        new GiftFactionNativeCollectorTest().actualPrivatePacketThroughCompleteCurrentAndGiftCollectorRetainsPublicRolesUntilPrivateSubmit(world);
        actualWriteFramePacketsReachOriginalDecoderPendingAndColdAndResolvedConsumers(world);
    }

}
