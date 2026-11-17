package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.FinanceEvidenceArchive;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.factiongift.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.factionalerts.*;
import org.xar.ck3.control.wave2.finance.factioncandidate.*;
import org.xar.ck3.control.wave2.finance.giftoutcome.*;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** New representation regressions execute production producers/consumers.
 * Modified historical fixtures are explicitly authored DATA, not new Native packet originals.
 * Separate actual Native faction-generation packets are consumed by their own integration test. */
final class FactionIdProducerConsumerTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/faction-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-30T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private static final BigInteger SENTINEL=new BigInteger("4294967295");
    private static byte[] bytes(JsonNode value){return StrictJson.canonical(value);}
    private static byte[] resource(String name)throws Exception {try(var input=FactionIdProducerConsumerTest.class.getResourceAsStream(name)){assertNotNull(input,name);return input.readAllBytes();}}
    private static BigInteger raw(int value){return BigInteger.valueOf(Integer.toUnsignedLong(value));}
    private static Obj domain(JsonNode value){return DriverJson.object(bytes(value),RawJson.MAXIMUM_BYTES);}
    private static ObjectNode observation(int faction)throws Exception {
        var packet=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(resource("/finance/private-gift-raw32/packets/positive/private-query-faction-gift-member-v1.json.packet.bin")));
        ObjectNode result=(ObjectNode)StrictJson.parse(packet.result().token().orElseThrow().value());
        ObjectNode observation=(ObjectNode)result.path("native").path("observation");observation.put("queried_source_faction_id",raw(faction));return observation;
    }
    private static ObjectNode publicAlert(int... factions)throws Exception {
        JsonNode golden=StrictJson.parse(resource("/factionalerts/original-producer-golden.json"));
        ObjectNode frame=(ObjectNode)golden.path("bases").path("full").deepCopy();ObjectNode row=null;
        for(JsonNode value:frame.path("targeting_factions"))if(value.path("faction_id").intValue()==771)row=(ObjectNode)value.deepCopy();
        assertNotNull(row);var rows=frame.putArray("targeting_factions");var danger=((ObjectNode)frame.get("planner_projection")).putArray("dangerous_faction_ids");
        for(int faction:factions){ObjectNode selected=row.deepCopy();selected.put("faction_id",faction);rows.add(selected);danger.add(faction);}
        frame.put("targeting_faction_count",factions.length);frame.putArray("county_exposures");ObjectNode planner=(ObjectNode)frame.get("planner_projection");
        planner.put("present",true).put("dangerous",true);for(String field:List.of("watch_faction_ids","war_handoff_faction_ids","exposed_county_title_ids"))planner.putArray(field);return frame;
    }
    @ParameterizedTest @ValueSource(ints={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE})
    void publicNormalizerAndImmutableModelPreserveEveryFactionGeneration(int faction)throws Exception {
        ObjectNode frame=publicAlert(faction);var normalized=FactionAlertsCodec.normalize(bytes(frame),new FactionAlertModel.ExpectedFrame(53789952,BigInteger.valueOf(41),Optional.empty()));
        var value=assertInstanceOf(FactionAlertModel.Available.class,normalized.frame());assertEquals(faction,value.targetingFactions().getFirst().factionId());
        assertEquals(List.of(faction),assertInstanceOf(FactionAlertModel.AvailablePlanner.class,value.planner()).dangerousFactionIds());assertArrayEquals(bytes(frame),normalized.json());
    }
    @Test void publicFactionListsUseSignedOrderWhileTitleAndWarFieldsStayPositive()throws Exception {
        ObjectNode frame=publicAlert(Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE);var expected=new FactionAlertModel.ExpectedFrame(53789952,BigInteger.valueOf(41),Optional.empty());
        assertEquals(4,assertInstanceOf(FactionAlertModel.Available.class,FactionAlertsCodec.normalize(bytes(frame),expected).frame()).targetingFactionCount());
        for(int invalid:new int[]{-1})assertThrows(IllegalArgumentException.class,()->FactionAlertsCodec.normalize(bytes(publicAlert(invalid)),expected));
        var row=(ObjectNode)frame.path("targeting_factions").get(0);row.put("special_title_id",0);assertThrows(IllegalArgumentException.class,()->FactionAlertsCodec.normalize(bytes(frame),expected));
        row.putNull("special_title_id");row.put("faction_at_war",true).put("faction_war_id",0);assertThrows(IllegalArgumentException.class,()->FactionAlertsCodec.normalize(bytes(frame),expected));
    }
    private static FactionGiftChoice.Selected choice(ObjectNode observation){ObjectNode request=StrictJson.object().put("complete_native_enumeration",true).put("minimum_gold_reserve_raw",0);request.putArray("observations").add(observation);return assertInstanceOf(FactionGiftChoice.Selected.class,FactionGiftPolicy.choose(bytes(request)));}
    @ParameterizedTest @ValueSource(ints={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE})
    void privateObservationProducesPublicChoiceAndExplicitPrivateSubmit(int faction)throws Exception {
        ObjectNode observation=observation(faction);var selected=choice(observation);assertEquals(BigInteger.valueOf(faction),selected.sourceFactionId());
        assertEquals(selected,FactionGiftPolicy.decodeChoice(FactionGiftPolicy.encode(selected)));
        BigInteger actor=selected.playerCharacterId(),revision=selected.nativeSnapshotRevision(),date=selected.dateRaw();
        ObjectNode snapshot=StrictJson.object().put("snapshot_id","faction-pre").put("revision",selected.snapshotRevision()).put("native_revision",revision).put("date_raw",date).put("episode_run_id","faction-episode").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",actor).put("alive",true);snapshot.putObject("played_character_gold").put("raw",observation.path("player_gold_raw").bigIntegerValue()).put("scale",100000);
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");snapshot.putNull("active_event");snapshot.putNull("pending_character_interaction");
        var identity=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,revision,date),"faction-pre",selected.snapshotRevision(),"faction-episode"),1);
        ObjectNode args=StrictJson.object().put("minimum_gold_reserve_raw",0);args.set("choice",StrictJson.parse(FactionGiftPolicy.encode(selected)));args.putObject("candidate").set("observation",observation);args.set(FinanceEvidenceArchive.ARGUMENT,REF.toJson());
        var request=new PlanningRequest(identity,SOURCE,"faction-session",DEADLINE,new PlanningObservation(domain(snapshot),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var expected=NativeFinanceEffects.expected(OrdinaryFinancePolicies.GIFT,request,domain(args)).orElseThrow();var command=new ActionCommand("faction-producer",identity,SOURCE,"faction-session",OrdinaryFinancePolicies.GIFT,domain(args),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(selected.recipientCharacterId()),Set.of()),DEADLINE);
        assertEquals(raw(faction),NativeFinanceEffects.giftBaseline(command.arguments()).sourceFactionId());
        var prepared=object(parse(NativeFinanceEffects.prepare(command,"faction-data-request").additionalFields().bytes()),"actual private submit fields");assertEquals(new IntegerValue(raw(faction)),prepared.get("source_faction_id"));
    }
    @Test void privateFactionSentinelSignedAliasesAndNonintegerTokensCannotSelect()throws Exception {
        for(String token:List.of("-1","-2","4294967295","4294967296","true","2.0","\"2\"","null")){
            ObjectNode observation=observation(0);observation.set("queried_source_faction_id",new com.fasterxml.jackson.databind.ObjectMapper().readTree(token));ObjectNode request=StrictJson.object().put("complete_native_enumeration",true).put("minimum_gold_reserve_raw",0);request.putArray("observations").add(observation);assertInstanceOf(FactionGiftChoice.Declined.class,FactionGiftPolicy.choose(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(request)),token);
        }
        for(BigInteger invalid:List.of(BigInteger.valueOf(-2),BigInteger.valueOf(-1),SENTINEL,SENTINEL.add(BigInteger.ONE)))assertThrows(IllegalArgumentException.class,()->GiftPendingModel.rawSourceFactionId(invalid));
    }
    @ParameterizedTest @ValueSource(ints={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE})
    void privatePendingAndCodecRetainZeroAndAllFactionBits(int faction)throws Exception {
        ObjectNode observed=observation(faction);ObjectNode begin=StrictJson.object().put("request_id","faction-pending").put("episode_run_id","faction-episode").put("source_round_id","R1").put("source_bridge_pid",10).put("source_bridge_creation_date","authored-birth").put("minimum_gold_reserve_raw",0).put("checkpoint_sha256_before_submit","a".repeat(64));begin.set("observation",observed);
        var ledger=GiftPendingReducer.begin(GiftPendingModel.Ledger.empty(),GiftPendingCodec.decodeBegin(bytes(begin)));assertEquals(raw(faction),ledger.pending().orElseThrow().baseline().sourceFactionId());assertEquals(ledger,GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(ledger)));
    }
    private static void remapFaction(JsonNode node,BigInteger raw,BigInteger signed){if(node.isObject()){var object=(ObjectNode)node;for(var entry:object.properties()){String key=entry.getKey();if(key.equals("source_faction_id")||key.equals("queried_source_faction_id"))object.put(key,raw);else if(key.equals("faction_id"))object.put(key,signed);else remapFaction(entry.getValue(),raw,signed);}}else if(node.isArray())node.forEach(value->remapFaction(value,raw,signed));}
    @ParameterizedTest @ValueSource(ints={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE})
    void resolvedOutcomeComparesPublicAlertToPrivateHistoryThroughExplicitBoundary(int faction)throws Exception {
        ObjectNode spec=(ObjectNode)StrictJson.parse(resource("/giftoutcome/original-producer-golden.json")).path("base").deepCopy();remapFaction(spec,raw(faction),BigInteger.valueOf(faction));
        ObjectNode alert=(ObjectNode)spec.path("alert_result").path("player_faction_alerts");var row=StrictJson.object().put("faction_id",faction);alert.putArray("targeting_factions").add(row);
        var calls=new ArrayList<JsonNode>();var recorded=new ArrayList<JsonNode>();
        var driver=new ExistingGiftOutcomeAdapter.OwnedDriverPort(){private int snapshots;
            @Override public byte[] takeInternalSemanticSnapshot(){return bytes(spec.get(++snapshots==1?"snapshot":"after_snapshot"));}
            @Override public <T> T underOriginalHistoryLock(Function<Iterable<byte[]>,T> projection){var history=new ArrayList<byte[]>();spec.path("history").forEach(value->history.add(bytes(value)));return projection.apply(history);}
            @Override public ExistingGiftOutcomeAdapter.Invocation readOriginalIndependentPair(byte[] request){calls.add(StrictJson.parse(request));return new ExistingGiftOutcomeAdapter.Packet(bytes(spec.get("pair_result")));}
            @Override public ExistingGiftOutcomeAdapter.Invocation queryOriginalPlayerFactionAlerts(BigInteger revision){return new ExistingGiftOutcomeAdapter.Packet(bytes(spec.get("alert_result")));}
            @Override public void recordOriginalObservedCommand(String step,boolean ok,byte[] result){assertTrue(ok);recorded.add(StrictJson.parse(result));}
        };
        JsonNode output=StrictJson.parse(new ExistingGiftOutcomeAdapter(driver).queryResolvedFactionGiftOutcome(bytes(spec.get("request"))));assertEquals("observed",output.path("status").textValue());assertEquals("observed",output.path("current_alert").path("status").textValue());assertEquals(raw(faction),calls.getFirst().get("source_faction_id").bigIntegerValue());assertEquals(1,recorded.size());assertFalse(output.path("gift_submit_performed").booleanValue());
    }
}
