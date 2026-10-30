package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJsonTest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.FinanceEvidenceArchive;
import org.xar.ck3.control.application.effects.NativeFinanceEffects;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.factionalerts.*;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** Full public Collector.current -> gift -> Native request path with real private WriteFrame originals.
 * Public ROOT/alerts/market and state/guard/archive wrappers are authored DATA derived from retained
 * source corpora. Test read/ledger ports grant no live reader, writer, opaque, action or SAVE authority. */
final class GiftOrdinaryCollectorCharacterTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/ordinary-gift-source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-30T00:00:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static Obj domain(JsonNode value) {return DriverJson.object(StrictJson.canonical(value),RawJson.MAXIMUM_BYTES);}
    private static ObjectNode tree(Obj value) {return (ObjectNode)StrictJson.parse(DriverJson.encode(value));}
    private record World(NativeWire.CommandResult preview,ObjectNode observation,PlanningRequest request,ObjectNode root,ObjectNode alert,BigInteger recipient) { }
    private static byte[] resource(String path)throws Exception {
        try(var stream=GiftOrdinaryCollectorCharacterTest.class.getResourceAsStream(path)) {assertNotNull(stream,path);return stream.readAllBytes();}
    }
    private static final Set<String> CHARACTER_FIELDS=Set.of("player_character_id","top_liege_character_id","immediate_liege_character_id","first_heir_character_id","owner_character_id","incumbent_character_id","character_id");
    private static final Set<String> CHARACTER_VECTORS=Set.of("primary_title_succession_character_ids","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids");
    private static void remap(ObjectNode root,BigInteger old,BigInteger replacement) {
        remapValue(root,"",old,replacement);
        for(String field:List.of("direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids")) {
            var values=new ArrayList<JsonNode>();root.get(field).forEach(values::add);values.sort(Comparator.comparing(JsonNode::bigIntegerValue));root.putArray(field).addAll(values);
        }
        var related=new ArrayList<JsonNode>();root.get("related_character_contexts").forEach(related::add);
        related.sort(Comparator.comparing(item->item.get("character_id").bigIntegerValue()));root.putArray("related_character_contexts").addAll(related);
    }
    private static void remapValue(JsonNode value,String field,BigInteger old,BigInteger replacement) {
        if(value.isObject()) {
            var object=(ObjectNode)value;var names=new ArrayList<String>();object.fieldNames().forEachRemaining(names::add);
            for(String name:names) {
                JsonNode child=object.get(name);
                if(CHARACTER_FIELDS.contains(name)&&child.isIntegralNumber()&&old.equals(child.bigIntegerValue()))object.put(name,replacement);
                else remapValue(child,name,old,replacement);
            }
        } else if(value.isArray()) {
            var rows=(com.fasterxml.jackson.databind.node.ArrayNode)value;
            for(int index=0;index<rows.size();index++) {
                JsonNode child=rows.get(index);
                if(CHARACTER_VECTORS.contains(field)&&child.isIntegralNumber()&&old.equals(child.bigIntegerValue()))rows.set(index,com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(replacement));
                else remapValue(child,"",old,replacement);
            }
        }
    }
    private static ObjectNode alert(ObjectNode observation,BigInteger actor,BigInteger recipient)throws Exception {
        JsonNode corpus=StrictJson.parse(resource("/factionalerts/original-producer-golden.json"));JsonNode vector=null;
        for(JsonNode row:corpus.get("cases"))if(row.path("name").asText().equals("exact-build-1.20.0.4"))vector=row;
        assertNotNull(vector);ObjectNode frame=(ObjectNode)corpus.path("bases").get(vector.get("base").textValue()).deepCopy();
        for(JsonNode op:vector.get("operations")) {
            String path=op.get("path").textValue();int slash=path.lastIndexOf('/');ObjectNode parent=slash==0?frame:(ObjectNode)frame.at(path.substring(0,slash));
            if(op.path("remove").asBoolean(false))parent.remove(path.substring(slash+1));else parent.set(path.substring(slash+1),op.get("value").deepCopy());
        }
        ObjectNode selected=null;for(JsonNode row:frame.get("targeting_factions"))if(row.path("faction_id").asInt()==771)selected=(ObjectNode)row.deepCopy();
        assertNotNull(selected);BigInteger faction=observation.get("queried_source_faction_id").bigIntegerValue();
        selected.put("faction_id",faction).put("target_character_id",actor).put("leader_character_id",recipient);selected.putArray("character_member_ids").add(recipient);
        frame.put("snapshot_revision",observation.get("snapshot_revision").bigIntegerValue()).put("date_raw",observation.get("observed_date_raw").bigIntegerValue())
                .put("player_character_id",actor).put("targeting_faction_count",1);
        frame.putArray("targeting_factions").add(selected);frame.putArray("county_exposures");
        ObjectNode planner=(ObjectNode)frame.get("planner_projection");planner.putArray("dangerous_faction_ids").add(faction);
        for(String field:List.of("watch_faction_ids","war_handoff_faction_ids","exposed_county_title_ids"))planner.putArray(field);
        ObjectNode result=StrictJson.object().put("step",FactionAlertModel.STEP).put("accepted",true).put("status","available").put("query_sequence",1)
                .put("snapshot_revision",observation.get("snapshot_revision").bigIntegerValue()).put("player_faction_alerts_ready",true).put("backend_id","native-headless");
        result.set("player_faction_alerts",frame);return result;
    }
    private static World world(String name)throws Exception {
        byte[] packet=resource("/finance/private-gift-raw32/packets/"+name+"/private-query-faction-gift-member-v1.json.packet.bin");
        var preview=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));assertArrayEquals(packet,preview.packet().value());
        ObjectNode observation=(ObjectNode)StrictJson.parse(preview.result().token().orElseThrow().value()).path("native").path("observation");
        BigInteger actor=NativeCharacterId.fromRawUInt32(observation.get("player_character_id").bigIntegerValue()).asBigInteger();
        BigInteger recipient=NativeCharacterId.fromRawUInt32(observation.get("recipient_character_id").bigIntegerValue()).asBigInteger();
        BigInteger revision=observation.get("snapshot_revision").bigIntegerValue(),date=observation.get("observed_date_raw").bigIntegerValue();
        ObjectNode root=tree(CampaignRootContextJsonTest.originalActual4RootFixture());remap(root,BigInteger.valueOf(12345),actor);remap(root,BigInteger.valueOf(23456),recipient);
        root.put("snapshot_revision",revision).put("date_raw",date).put("player_targeting_faction_count",1);root.putNull("player_heir_candidate_v1");
        ObjectNode snapshot=StrictJson.object().put("snapshot_id","collector-public").put("revision",revision).put("native_revision",revision)
                .put("date_raw",date).put("episode_run_id","collector-episode").put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",actor).put("alive",true);
        snapshot.putObject("played_character_gold").put("raw",observation.get("player_gold_raw").bigIntegerValue()).put("scale",100000);
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");snapshot.putNull("active_event");snapshot.putNull("pending_character_interaction");
        snapshot.putObject("diagnostics").putObject("hello").put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",SHA);
        var before=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,revision,date),"collector-public",revision,"collector-episode"),1);
        var request=new PlanningRequest(before,SOURCE,"collector-session",DEADLINE,new PlanningObservation(domain(snapshot),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        return new World(preview,observation,request,root,alert(observation,actor,recipient),recipient);
    }
    private static FinanceReadContracts definitions() {return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));}
    private static final class Reads implements PlanningReadPort {
        final World world;final List<OperationKey> calls=new ArrayList<>();
        Reads(World world){this.world=world;}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            calls.add(request.operation());
            try {
                NativeWire.CommandResult wire;
                if(request.operation().equals(FinanceReadContracts.Query.FACTION_GIFT.operation())) {
                    wire=world.preview();Obj prepared=object(parse(contract.prepare(request,wire.requestId()).additionalFields().bytes()),"private read fields");
                    assertEquals(new IntegerValue(world.observation().get("player_character_id").bigIntegerValue()),prepared.get("expected_player_character_id"));
                } else {
                    ObjectNode result;
                    if(request.operation().equals(FinanceReadContracts.Query.ROOT.operation())) {
                        result=StrictJson.object().put("step",request.operation().value()).put("accepted",true).put("status","available").put("query_sequence",1)
                                .put("snapshot_revision",world.observation().get("snapshot_revision").bigIntegerValue()).put("backend_id","native-headless");result.set("campaign_root_context",world.root());
                    } else if(request.operation().equals(FinanceReadContracts.Query.FACTION_ALERTS.operation()))result=world.alert();
                    else {
                        assertEquals(FinanceReadContracts.Query.MERCENARIES.operation(),request.operation());
                        result=StrictJson.object().put("step",request.operation().value()).put("accepted",true).put("snapshot_revision",world.observation().get("snapshot_revision").bigIntegerValue());
                        ObjectNode market=result.putObject("player_mercenary_context").put("schema","ck3_12004_player_mercenary_context_v1").put("game_version","1.20.0.4").put("executable_sha256",SHA)
                                .put("actor_character_id",request.before().frame().identity().player()).put("date_raw",request.before().frame().identity().dateRaw()).put("capture_epoch",1)
                                .put("read_only",true).put("native_hire_mode",1).put("available",true);market.putNull("unavailable_reason");market.putArray("rows");
                    }
                    ObjectNode body=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","authored-public-read-"+calls.size()).put("ok",true);body.set("result",result);
                    wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(StrictJson.canonical(body))));
                }
                var binding=new GuardEvidence(request.before(),SOURCE,request.sessionId(),BigInteger.ONE,request.operation(),REF,REF,"software-collector-data",DEADLINE.minusSeconds(10),DEADLINE);
                var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
                var ack=new NativeActionPort.AckReceived(wire.requestId(),wire.nativeOk(),wire.result().token().map(value->new RawJson(value.value())),new RawJson(wire.payload().value()),wire.packet().value());
                var read=new PlanningReadReceipt(request,contract.contractId(),wire.requestId(),guard,guard,ack);
                return new PlanningReadResult.Known<>(contract.replay(read),read,REF);
            } catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        }
    }
    private static FinanceStatePort state(World world,boolean checkpoint) {
        var documents=new ArrayList<FinanceStatePort.Document>();var readers=new ArrayList<FinanceStatePort.ReaderBinding>();
        for(var domain:FinanceStatePort.Domain.values()) {
            byte[] body=domain==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingCodec.encodeLedger(GiftPendingModel.Ledger.empty()):"{\"pending\":null}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            var ref=new ExactRef("D:/fixture/authored-clear-"+domain+".json",body.length,DriverJson.sha256(body));
            documents.add(new FinanceStatePort.Document(domain,ref,body));
            readers.add(domain==FinanceStatePort.Domain.FACTION_GIFT?FinanceStatePort.giftReader(REF):new FinanceStatePort.ReaderBinding(domain,REF,document->FinanceStatePort.Pending.CLEAR));
        }
        Optional<FinanceStatePort.Checkpoint> saved=checkpoint?Optional.of(new FinanceStatePort.Checkpoint(REF,"collector-episode",world.request().before().frame().identity().dateRaw())):Optional.empty();
        return new FinanceStatePort(request->new FinanceStatePort.Head(request.before(),REF,documents,List.of(),saved),readers);
    }
    private static OrdinaryFinanceCollector.Current current(OrdinaryFinanceCollector collector,World world) {
        var read=collector.current(world.request());
        return assertInstanceOf(OrdinaryFinanceCollector.Current.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,read,read::toString).value());
    }
    @ParameterizedTest
    @ValueSource(strings={"positive","actor-zero","recipient-zero","actor-min","recipient-min","both-high"})
    void actualPrivatePacketThroughCompleteCurrentAndGiftCollectorRetainsPublicRolesUntilPrivateSubmit(String name)throws Exception {
        World world=world(name);var reads=new Reads(world);var collector=new OrdinaryFinanceCollector(definitions(),reads,state(world,true));
        var held=current(collector,world);var result=collector.gift(world.request(),held);
        var gift=assertInstanceOf(OrdinaryFinanceCollector.Gift.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,result,result::toString).value());
        assertEquals(world.request().before().frame().identity().player(),gift.selected().playerCharacterId());assertEquals(world.recipient(),gift.selected().recipientCharacterId());
        assertEquals(4,gift.originalReads().size());assertEquals(List.of(FinanceReadContracts.Query.ROOT.operation(),FinanceReadContracts.Query.MERCENARIES.operation(),FinanceReadContracts.Query.FACTION_GIFT.operation(),FinanceReadContracts.Query.FACTION_ALERTS.operation()),reads.calls);
        assertTrue(gift.cash().newGiftSpendingAllowed());assertEquals(BigInteger.valueOf(10000000),gift.minimumGoldReserveRaw());
        Obj args=OrdinaryFinanceCollector.obj("choice",object(parse(org.xar.ck3.control.finance.factiongift.FactionGiftPolicy.encode(gift.selected())),"actual selected choice"),"candidate",gift.candidate(),
                "minimum_gold_reserve_raw",new IntegerValue(gift.minimumGoldReserveRaw()),FinanceEvidenceArchive.ARGUMENT,domain(REF.toJson()));
        var expected=NativeFinanceEffects.expected(OrdinaryFinancePolicies.GIFT,world.request(),args).orElseThrow();
        var command=new ActionCommand("collector-gift",world.request().before(),SOURCE,world.request().sessionId(),OrdinaryFinancePolicies.GIFT,args,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(world.recipient()),Set.of()),DEADLINE);
        Obj submit=object(parse(NativeFinanceEffects.prepare(command,"software-only-submit-fields").additionalFields().bytes()),"private submit");
        assertEquals(new IntegerValue(world.observation().get("player_character_id").bigIntegerValue()),submit.get("expected_player_character_id"));
        assertEquals(new IntegerValue(world.observation().get("recipient_character_id").bigIntegerValue()),submit.get("recipient_character_id"));
    }
    @Test void currentBudgetAndExistingCheckpointStillConstrainTheActualCollector()throws Exception {
        World world=world("positive");var reads=new Reads(world);var collector=new OrdinaryFinanceCollector(definitions(),reads,state(world,true));var held=current(collector,world);
        assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,collector.gift(world.request(),held,BigInteger.valueOf(12500001)));
        var without=new OrdinaryFinanceCollector(definitions(),new Reads(world),state(world,false));
        var result=assertInstanceOf(OrdinaryFinanceCollector.Unavailable.class,without.gift(world.request(),current(without,world)));
        assertTrue(result.missing().reason().contains("checkpoint"));
    }
    @Test void publicRoleSentinelSelfTargetBuildAndFactionDomainsStayStrict() {
        var frame=new FactionAlertModel.ExpectedFrame(1,BigInteger.ONE,Optional.of(FactionAlertModel.Build.CK3_12004));
        for(int role:new int[]{0,Integer.MIN_VALUE,-2,Integer.MAX_VALUE}) {
            var request=new FactionThreatAdmission.Request(frame,role,1,2);assertEquals(role,request.actorCharacterId());
            assertThrows(IllegalArgumentException.class,()->new FactionThreatAdmission.Request(frame,role,1,role));
        }
        assertThrows(IllegalArgumentException.class,()->new FactionThreatAdmission.Request(frame,-1,1,2));
        assertThrows(IllegalArgumentException.class,()->new FactionThreatAdmission.Request(frame,2,1,-1));
        for(int faction:new int[]{0,-1,-2})assertThrows(IllegalArgumentException.class,()->new FactionThreatAdmission.Request(frame,2,faction,3));
        assertThrows(IllegalArgumentException.class,()->new FactionThreatAdmission.Request(new FactionAlertModel.ExpectedFrame(1,BigInteger.ONE,Optional.of(FactionAlertModel.Build.CK3_11906)),2,1,3));
    }
}
