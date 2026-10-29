package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Retained original producer rows -> strict software packet -> owning replay -> observed-history DATA.
 * No private Root, installed-source qualification, live READ ancestry, writer or Game authority is constructed. */
final class GiftResolvedEvidenceTest {
    private static final ExactRef SOURCE=new ExactRef("software-gift-source-only",1,"a".repeat(64));
    private static final GiftColdReadService OWNER=new GiftColdReadService(new FinanceReadContracts.Registration(SOURCE,
            new FinanceReadContracts.Permission(Optional.empty(),GiftColdReadService.OPERATION.value(),
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
    private record Material(ObjectNode base,Complete frame,PlanningReadReceipt pair,DriverStateSnapshot.Complete driver) { }
    private static Obj obj(JsonNode node) {return DriverJson.object(StrictJson.canonical(node),RawJson.MAXIMUM_BYTES);}
    private static ObjectNode original()throws Exception {
        try(var stream=GiftResolvedEvidenceTest.class.getResourceAsStream("/gift-resolved-original-base.json")) {
            assertNotNull(stream);return (ObjectNode)StrictJson.parse(stream.readAllBytes(),1048576).get("base");
        }
    }
    private static ObservationIdentity identity(BigInteger revision) {
        return new ObservationIdentity("fixture-machine",new GameGeneration(23456,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(12),
                    BigInteger.valueOf(53290200)),"native:9",revision,"native-29829-original"),1);
    }
    private static DriverStateSnapshot.Complete driver(List<Obj> actualRows) {
        var rows=new ArrayList<DriverStateSnapshot.HistoryEntry>();long index=0;
        for(Obj row:actualRows) {
            index++;rows.add(new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(
                    DriverJson.encode(row.with("index",new IntegerValue(BigInteger.valueOf(index)))))));
        }
        var absent=new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-only-pipe",23456,BigInteger.valueOf(29829),
                "native-29829-original"),rows,absent,absent,absent,absent,absent,absent,absent);
    }
    private static Material material()throws Exception {
        ObjectNode base=original();var source=new G2Source("fixture-machine","2026-10-24T00:00:00Z","1.20.0.4",SOURCE);
        var before=identity(BigInteger.valueOf(9));Instant deadline=Instant.now().plusSeconds(60);
        Obj arguments=OrdinaryFinanceCollector.obj("source_faction_id",new IntegerValue(BigInteger.valueOf(50331692)),
                "recipient_character_id",new IntegerValue(BigInteger.valueOf(33435)));
        var request=new PlanningReadRequest(before,source,"software-gift-session",GiftColdReadService.OPERATION,arguments,deadline);
        ObjectNode post=((ObjectNode)base.path("pair_result").path("native").path("observation")).deepCopy();
        post.put("date_raw",53290200).put("player_resources_query_complete",true).put("player_gold_raw",100000000)
                .put("player_gold_scale",100000).put("source_faction_target_character_id",29829).put("source_faction_at_war",false)
                .put("recipient_alive",true).put("recipient_is_ai",true).put("recipient_is_direct_landed_vassal",true);
        post.putObject("gift_preview").put("available",false).put("definition_key","").put("definition_stable_hash",0)
                .put("interaction_legal",false).put("auto_accept",false).put("gold_cost_raw",0).put("gold_scale",0).put("opinion_delta",0);
        ObjectNode nativeResult=StrictJson.object().put("schema_version",1).put("private",true).put("game_version","1.20.0.4")
                .put("executable_sha256","98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")
                .put("backend_id","ck3-1.20.0.4-private-faction-gift-mitigation-action-v1")
                .put("contract_stage","exact_build_private_action_source_static_ready_live_pending")
                .put("failure_flags",0).put("frame_failure_stage","none").put("direct_source_failure","none")
                .put("source_faction_id",50331692).put("recipient_character_id",33435).put("receipt_pending",false).put("executor_invocations",1);
        nativeResult.putNull("ack");nativeResult.putNull("preflight");nativeResult.putArray("typed_reds");nativeResult.set("observation",post);
        ObjectNode result=StrictJson.object().put("step",GiftColdReadService.OPERATION.value()).put("accepted",true)
                .put("private_build",true).put("advertised",false).put("status","independent_read_complete");
        result.set("native",nativeResult);result.putNull("receipt");
        ObjectNode envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-pair-read").put("ok",true);
        envelope.set("result",result);RawJson wire=new RawJson(StrictJson.canonical(envelope));
        byte[] packet=ByteBuffer.allocate(wire.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(wire.bytes().length).put(wire.bytes()).array();
        var nativeAck=new NativeActionPort.AckReceived("software-pair-read",true,Optional.of(new RawJson(StrictJson.canonical(result))),wire,packet);
        var binding=new GuardEvidence(before,source,request.sessionId(),BigInteger.ONE,request.operation(),SOURCE,SOURCE,"software-source",deadline.minusSeconds(30),deadline);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var read=new PlanningReadReceipt(request,OWNER.contract().contractId(),nativeAck.requestId(),guard,guard,nativeAck);
        ObjectNode semantic=((ObjectNode)base.get("snapshot")).deepCopy();semantic.putArray("active_wars");
        var frame=new Complete(before,source,request.sessionId(),BigInteger.ONE,obj(semantic),SOURCE,deadline.minusSeconds(20),"c".repeat(64));
        var rows=new ArrayList<Obj>();base.get("history").forEach(row->rows.add(obj(row)));
        rows.add(OrdinaryFinanceCollector.obj("command",new Text("query-player-faction-alerts-v1"),"ok",new Bool(true),"result",obj(base.get("alert_result"))));
        return new Material(base,frame,read,driver(rows));
    }
    private static GiftResolvedEvidence.Inputs inputs(Material m) {
        return new GiftResolvedEvidence.Inputs(m.frame(),m.driver(),m.pair(),Optional.empty(),"gift-original");
    }
    @Test void originalRowsStrictNativeParserAndPersistentDriverRoundTripProduceObservedOnly()throws Exception {
        Material m=material();var decoded=OWNER.contract().replay(m.pair());
        assertEquals(decoded.originalResult(),GiftColdReadService.requireHistoryResult(decoded.originalResult(),m.pair().request().arguments(),m.frame().identity()));
        var observed=GiftResolvedEvidence.recompute(inputs(m),OWNER.contract(),Optional.empty());
        Obj output=DriverJson.object(observed.result().bytes(),1048576);
        assertEquals(new Text("observed"),output.get("status"));assertEquals(new Text("still_member"),output.get("faction_outcome"));
        assertEquals(new Bool(false),output.get("gift_submit_performed"));assertEquals(new Bool(false),output.get("pending_resolution_performed"));
        assertEquals(m.base().path("history").get(1).path("result").get("receipt"),
                StrictJson.parse(encode(object(output.get("original"),"original").get("receipt")),1048576));
        assertEquals(GiftResolvedEvidence.OPERATION,observed.operation());
        assertArrayEquals(m.driver().encode(),DriverStateSnapshot.decodeComplete(m.driver().encode()).encode());
    }
    @Test void missingOriginalSubmitOrReceiptAndWrongPairCannotMintObserved()throws Exception {
        Material m=material();var rows=GiftResolvedEvidence.relevantHistory(m.driver());
        for(int missing:List.of(0,1)) {
            var retained=new ArrayList<Obj>();for(int i=0;i<rows.size();i++)if(i!=missing)retained.add(DriverJson.object(rows.get(i).bytes(),1048576));
            var incomplete=new GiftResolvedEvidence.Inputs(m.frame(),driver(retained),m.pair(),Optional.empty(),"gift-original");
            assertThrows(IllegalArgumentException.class,()->GiftResolvedEvidence.recompute(incomplete,OWNER.contract(),Optional.empty()));
        }
        assertThrows(IllegalArgumentException.class,()->GiftResolvedEvidence.recompute(new GiftResolvedEvidence.Inputs(
                m.frame(),m.driver(),m.pair(),Optional.empty(),"different-original-request"),OWNER.contract(),Optional.empty()));
        var original=OWNER.contract().replay(m.pair()).originalResult();Obj nativeResult=object(original.get("native"),"native");
        Obj post=object(nativeResult.get("observation"),"post");
        for(String field:List.of("snapshot_revision","queried_source_faction_id","recipient_character_id","player_gold_raw"))
            assertThrows(IllegalArgumentException.class,()->GiftColdReadService.requireHistoryResult(
                    original.with("native",nativeResult.with("observation",post.with(field,new Bool(true)))),m.pair().request().arguments(),m.frame().identity()));
    }
    @Test void dataCompatibilityRetainsOldPublicReceiptWithoutClaimingReadLineage()throws Exception {
        Material m=material();Obj semantic=m.frame().semantic().with("revision",new IntegerValue(BigInteger.valueOf(11)));
        var current=new Complete(identity(BigInteger.valueOf(11)),m.frame().source(),m.frame().sessionId(),m.frame().connectionGeneration(),
                semantic,m.frame().originalEvidence(),m.frame().observedAt(),m.frame().fullBindingSha256());
        var observed=GiftResolvedEvidence.recompute(new GiftResolvedEvidence.Inputs(current,m.driver(),m.pair(),Optional.empty(),"gift-original"),OWNER.contract(),Optional.empty());
        assertEquals(BigInteger.valueOf(9),observed.originals().pair().request().before().frame().revision());
        assertEquals(BigInteger.valueOf(11),observed.originals().frame().identity().frame().revision());
        // This DATA test has no publisher or writer, and therefore proves no actual READ-only extension.
    }
    @Test void unrelatedLargeArmyRowsAreNotFedToTheBoundedGiftHistoryParser()throws Exception {
        Material m=material();var rows=new ArrayList<Obj>();
        for(var row:GiftResolvedEvidence.relevantHistory(m.driver()))rows.add(DriverJson.object(row.bytes(),1048576));
        rows.add(OrdinaryFinanceCollector.obj("command",new Text("auto-turn"),"ok",new Bool(true),"result",
                OrdinaryFinanceCollector.obj("auto_turn",OrdinaryFinanceCollector.obj("selected_step",new Text("army-heavy-read"),"result",new Text("x".repeat(1100000))))));
        assertEquals(3,GiftResolvedEvidence.relevantHistory(driver(rows)).size());
    }
    @Test void actualOwningObservedWithoutStepReachesTheHistoryDataConsumerAndRejectsChangedLogicalIdentity()throws Exception {
        Material m=material();var observed=GiftResolvedEvidence.recompute(inputs(m),OWNER.contract(),Optional.empty());
        Obj result=DriverJson.object(observed.result().bytes(),1048576);assertFalse(result.members().containsKey("step"));
        // Unqualified source DATA only. No Candidate, archive qualification, Known, current proof or writer is minted.
        var binding=new DriverObservedHistoryRowProducer.ReadBinding(OWNER.contract().contractId(),SOURCE,SOURCE,SOURCE);
        var source=new DriverObservedHistoryRowProducer.Source(DriverObservedHistoryRowProducer.Kind.GIFT_RESOLVED,
                "gift-original",m.frame().identity(),SOURCE,SOURCE,SOURCE,SOURCE,binding,Optional.empty(),List.of(SOURCE));
        var row=new DriverObservedHistoryRowProducer.RawHistoryRow(1,observed.operation().value(),true,result,source);
        assertEquals(row,DriverObservedHistoryRowProducer.decode(row.encode()));
        assertEquals(observed.operation().value(),row.command());assertFalse(row.result().members().containsKey("step"));
        for(Obj wrong:List.of(result.with("schema",new Text("wrong-schema")),result.with("status",new Text("unavailable")),
                result.with("request_id",new Text("other-request")),result.with("attributed_to_gift",new Bool(true))))
            assertThrows(IllegalArgumentException.class,()->new DriverObservedHistoryRowProducer.RawHistoryRow(1,row.command(),true,wrong,source));
        assertThrows(IllegalArgumentException.class,()->new DriverObservedHistoryRowProducer.RawHistoryRow(1,GiftColdReadService.OPERATION.value(),true,result,source));
    }
}
