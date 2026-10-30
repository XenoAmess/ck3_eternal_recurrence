package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.factiongift.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.factioncandidate.*;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftwarcash.*;

/** Exact Native WriteFrame originals drive the ordinary Java candidate and request producer.
 * Public ROOT/SEM and quote-reference metadata are authored DATA; no live authority is created. */
final class GiftFactionNativeProducerTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/gift-producer-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-30T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private record Input(ObjectNode original,ObjectNode observation,ObjectNode root,ObjectNode snapshot,BigInteger actor,BigInteger recipient) { }
    private static BigInteger signed(BigInteger raw) {return BigInteger.valueOf((int)raw.longValueExact());}
    private static Obj domain(ObjectNode node) {return DriverJson.object(StrictJson.canonical(node),RawJson.MAXIMUM_BYTES);}
    private static byte[] fixture(String world,String step)throws Exception {
        try(var stream=GiftFactionNativeProducerTest.class.getResourceAsStream("/finance/faction-generation-native90/packets/"+world+"/"+step+".json.packet.bin")) {
            assertNotNull(stream,"retained actual Native packet required");return stream.readAllBytes();
        }
    }
    private static ObjectNode original(String world,String step)throws Exception {
        byte[] packet=fixture(world,step);
        var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        assertArrayEquals(packet,wire.packet().value());
        assertArrayEquals(Arrays.copyOfRange(packet,4,packet.length),wire.payload().value());
        return (ObjectNode)StrictJson.parse(wire.result().token().orElseThrow().value());
    }
    private static NativeWire.CommandResult independentReceipt(String world)throws Exception {
        try(var stream=GiftFactionNativeProducerTest.class.getResourceAsStream("/finance/faction-generation-native90/packets/"+world+"/private-query-faction-gift-receipt-v1.json.packet.bin")) {
            assertNotNull(stream,"independent outer query ID must be produced by actual Native WriteFrame");
            byte[] original=stream.readAllBytes();var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(original));
            assertArrayEquals(original,wire.packet().value());assertArrayEquals(Arrays.copyOfRange(original,4,original.length),wire.payload().value());return wire;
        }
    }
    private static Input input(String world)throws Exception {
        ObjectNode original=original(world,"private-query-faction-gift-member-v1");
        ObjectNode observation=(ObjectNode)original.path("native").path("observation");
        BigInteger actor=signed(observation.get("player_character_id").bigIntegerValue());
        BigInteger recipient=signed(observation.get("recipient_character_id").bigIntegerValue());
        BigInteger revision=observation.get("snapshot_revision").bigIntegerValue(),date=observation.get("observed_date_raw").bigIntegerValue();
        ObjectNode root=StrictJson.object().put("status","available").put("player_character_alive",true)
                .put("snapshot_revision",revision).put("date_raw",date).put("player_character_id",actor).put("player_targeting_faction_count",1);
        root.putObject("government").put("key","feudal_government");root.putArray("direct_landed_vassal_character_ids").add(recipient);
        ObjectNode snapshot=StrictJson.object().put("snapshot_id","producer-pre").put("revision",revision).put("native_revision",revision)
                .put("date_raw",date).put("episode_run_id","producer-episode").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",actor).put("alive",true);
        snapshot.putObject("played_character_gold").put("raw",observation.get("player_gold_raw").bigIntegerValue()).put("scale",100000);
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");snapshot.putNull("active_event");snapshot.putNull("pending_character_interaction");
        return new Input(original,observation,root,snapshot,actor,recipient);
    }
    private static FactionGiftChoice.Selected select(Input input) {
        var result=FactionCandidateCodec.evaluatePrivateCandidate(StrictJson.canonical(input.snapshot()),
                FactionCandidateCodec.decodeRootProjection(StrictJson.canonical(input.root())),StrictJson.canonical(input.original()),BigInteger.ZERO);
        var evaluated=assertInstanceOf(FactionCandidatePolicy.Evaluated.class,result,result::toString);
        var selected=assertInstanceOf(FactionGiftChoice.Selected.class,evaluated.choice(),evaluated.choice()::toString);
        assertEquals(input.actor(),selected.playerCharacterId());assertEquals(input.recipient(),selected.recipientCharacterId());
        assertEquals(BigInteger.valueOf(input.observation().get("queried_source_faction_id").intValue()),selected.sourceFactionId());
        assertEquals(selected,FactionGiftPolicy.decodeChoice(FactionGiftPolicy.encode(selected)));
        return selected;
    }
    private static ObservationIdentity identity(Input input) {
        BigInteger revision=input.observation().get("snapshot_revision").bigIntegerValue(),date=input.observation().get("observed_date_raw").bigIntegerValue();
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(input.actor(),revision,date),"producer-pre",revision,"producer-episode"),1);
    }
    private static Obj arguments(Input input,FactionGiftChoice.Selected selected) {
        ObjectNode choice=(ObjectNode)StrictJson.parse(FactionGiftPolicy.encode(selected));
        ObjectNode args=StrictJson.object().put("minimum_gold_reserve_raw",0);
        args.set("choice",choice);args.putObject("candidate").set("observation",input.observation());
        args.set(FinanceEvidenceArchive.ARGUMENT,REF.toJson());return domain(args);
    }
    private static ActionCommand command(Input input,FactionGiftChoice.Selected selected) {
        var before=identity(input);var args=arguments(input,selected);
        var current=new PlanningRequest(before,SOURCE,"producer-session",DEADLINE,new PlanningObservation(domain(input.snapshot()),
                List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var expected=NativeFinanceEffects.expected(OrdinaryFinancePolicies.GIFT,current,args).orElseThrow();
        return new ActionCommand("ordinary-gift-producer",before,SOURCE,"producer-session",OrdinaryFinancePolicies.GIFT,args,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(input.recipient()),Set.of()),DEADLINE);
    }
    @ParameterizedTest
    @org.junit.jupiter.params.provider.MethodSource("org.xar.ck3.control.application.planning.finance.FactionNativeWorlds#worlds")
    void actualNativePreviewReachesOrdinarySelectionAndPrivateSubmitProducer(String world)throws Exception {
        Input input=input(world);var selected=select(input);var command=command(input,selected);
        var baseline=NativeFinanceEffects.giftBaseline(command.arguments());
        assertEquals(input.observation().get("player_character_id").bigIntegerValue(),baseline.playerCharacterId());
        assertEquals(input.observation().get("recipient_character_id").bigIntegerValue(),baseline.recipientCharacterId());
        Obj prepared=object(parse(NativeFinanceEffects.prepare(command,"ordinary-native-request").additionalFields().bytes()),"actual private submit fields");
        assertEquals(new IntegerValue(baseline.playerCharacterId()),prepared.get("expected_player_character_id"));
        assertEquals(new IntegerValue(baseline.recipientCharacterId()),prepared.get("recipient_character_id"));
        assertEquals(new IntegerValue(baseline.sourceFactionId()),prepared.get("source_faction_id"));
        assertEquals(new IntegerValue(selected.goldCostRaw()),prepared.get("gold_cost_raw"));
        assertEquals(new IntegerValue(selected.opinionDelta()),prepared.get("opinion_delta"));
    }



    private static FinanceReadContracts definitions() {
        return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),
                query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    }
    @ParameterizedTest
    @org.junit.jupiter.params.provider.MethodSource("org.xar.ck3.control.application.planning.finance.FactionNativeWorlds#worlds")
    void ordinarySelectedPublicChoiceReachesActualIndependentPrivateReceiptProjection(String world)throws Exception {
        Input input=input(world);var selected=select(input);var command=command(input,selected);
        var wire=independentReceipt(world);ObjectNode result=(ObjectNode)StrictJson.parse(wire.result().token().orElseThrow().value());
        ObjectNode receipt=(ObjectNode)result.get("receipt"),post=(ObjectNode)result.path("native").path("observation");
        String originalAction=receipt.get("request_id").textValue();assertNotEquals(originalAction,wire.requestId());
        var pre=command.before();BigInteger revision=post.get("snapshot_revision").bigIntegerValue(),nativeRevision=post.get("native_snapshot_revision").bigIntegerValue();
        var afterId=new ObservationIdentity(pre.machineId(),pre.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(input.actor(),nativeRevision,post.get("observed_date_raw").bigIntegerValue()),"producer-post",revision,"producer-episode"),pre.observationVersion());
        ObjectNode semantic=input.snapshot().deepCopy();semantic.put("snapshot_id","producer-post").put("revision",revision).put("native_revision",nativeRevision);
        ((ObjectNode)semantic.get("played_character_gold")).put("raw",post.get("player_gold_raw").bigIntegerValue());
        var afterRef=new ExactRef("D:/fixture/authored-public-after-sem.json",1,"d".repeat(64));
        var before=new Complete(pre,SOURCE,command.sessionId(),BigInteger.ONE,domain(input.snapshot()),REF,DEADLINE.minusSeconds(40),"b".repeat(64));
        var after=new Complete(afterId,SOURCE,command.sessionId(),BigInteger.ONE,domain(semantic),afterRef,DEADLINE.minusSeconds(10),"c".repeat(64));
        var actionGuard=new GuardEvidence(pre,SOURCE,command.sessionId(),BigInteger.ONE,command.operation(),REF,REF,"software-native-producer-data",DEADLINE.minusSeconds(30),DEADLINE);
        var attempt=new ActionState.Attempt(originalAction,DEADLINE.minusSeconds(20),actionGuard,NativeFinanceEffects.prepare(command,originalAction));
        var query=FinanceReadContracts.Query.FACTION_GIFT_RECEIPT;var contract=definitions().contract(query);
        var request=new PlanningReadRequest(afterId,SOURCE,command.sessionId(),query.operation(),new Obj(Map.of()),DEADLINE);
        var queryBinding=new GuardEvidence(afterId,SOURCE,command.sessionId(),BigInteger.ONE,query.operation(),afterRef,REF,"software-native-producer-data",DEADLINE.minusSeconds(10),DEADLINE);
        var queryGuard=new PlanningReadGuard(queryBinding,true,true,true,"c".repeat(64));
        var ack=new NativeActionPort.AckReceived(wire.requestId(),wire.nativeOk(),wire.result().token().map(value->new RawJson(value.value())),new RawJson(wire.payload().value()),wire.packet().value());
        var read=new PlanningReadReceipt(request,contract.contractId(),wire.requestId(),queryGuard,queryGuard,ack);
        var typed=contract.replay(read);assertArrayEquals(wire.payload().value(),typed.originalFrame());
        var projected=NativeFinanceEffects.project(command,attempt,new NativeEffectSnapshots.Pair(before,after),read,typed);
        var observed=assertInstanceOf(ActionPorts.EffectObserved.class,projected.result());
        assertEquals(command.expected().values(),observed.observation().actual());
        assertEquals(input.actor(),observed.observation().after().frame().identity().player());
        Obj compatible=object(parse(projected.compatibleResult().orElseThrow().bytes()),"Gift material");
        assertEquals(new Bool(true),compatible.get("postcondition_verified"));
        assertEquals(new IntegerValue(input.observation().get("player_character_id").bigIntegerValue()),object(compatible.get("receipt"),"original raw receipt").get("player_character_id"));
        // The successful DATA replay must not widen the existing independent-query rule.
        var reused=new ActionState.Attempt(wire.requestId(),attempt.submittedAt(),attempt.guard(),attempt.preparedRequest());
        assertThrows(IllegalArgumentException.class,()->NativeFinanceEffects.project(command,reused,new NativeEffectSnapshots.Pair(before,after),read,typed));
    }
}
