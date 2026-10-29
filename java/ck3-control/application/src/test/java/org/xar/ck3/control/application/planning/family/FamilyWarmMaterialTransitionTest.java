package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Captured unchanged original Python test/producer plus explicit software read seams; no live authority. */
final class FamilyWarmMaterialTransitionTest {
    private static final ExactRef SOURCE=new ExactRef("D:/software-family-warm/source",1,"c".repeat(64));
    private static final BridgeIdentity BRIDGE=new BridgeIdentity(55,"created");
    private static final Instant NOW=Instant.parse("2026-10-29T00:00:00Z");
    private static Obj fixture()throws Exception {
        try(var input=FamilyWarmMaterialTransitionTest.class.getResourceAsStream("/family/original-warm-material.json")) {
            assertNotNull(input,"actual unchanged original test capture is required");
            Obj root=decode(input.readAllBytes());
            assertEquals(n(1),root.get("test_count"));assertTrue(array(root.get("errors")).isEmpty());assertTrue(array(root.get("failures")).isEmpty());
            return object(array(root.get("cases")).getFirst());
        }
    }
    private static Obj empty(Slot slot) {return obj("schema",t(FamilyDomainSource.schema(slot)),"pending",Nil.INSTANCE,"resolved",Nil.INSTANCE);}
    private static Obj canonical(Obj body) {return FamilyDomainSource.validate(Slot.FAMILY,
            ContinuityJson.canonical(OpportunityJson.toNode(body),ContinuityJson.DOMAIN_MAX_BYTES));}
    private static PlanningRequest request(Obj captured) {
        Obj snapshot=object(captured.get("snapshot")).with("revision",n(8)).with("snapshot_id",t("native:7")).with("player_armies",rows(List.of()));
        var source=new G2Source("software-family-warm",NOW.toString(),"software-no-game",SOURCE);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(53215920)),
                "native:7",BigInteger.valueOf(8),"robert-test");
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new PlanningRequest(before,source,"software-warm-session",NOW.plusSeconds(60),
                new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey("life-advance")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static Draft baseline(PlanningRequest r) {
        var expected=new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,r.before(),r.source(),
                "software-warm-existing-action/v1",List.of(new ExpectedBoolean(new FieldKey("software_existing_command_retained"),true)));
        var command=new ActionCommand("software-existing-life",r.before(),r.source(),r.sessionId(),new OperationKey("life-advance"),obj(),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),r.deadline());
        return new Draft("one-life-turn-v1","peace_growth","retain the original independently selected turn",Kind.ORDINARY,
                Optional.of(command),Purpose.DATE_ADVANCE,Optional.empty(),obj("selected_step",t("life-advance")));
    }
    private static final class Harness {
        final PlanningRequest request;final Obj relation;Obj domain;
        final List<Query> reads=new ArrayList<>(),imports=new ArrayList<>();
        final FamilyOrdinaryPolicy policy;
        Harness(Obj captured) {
            request=request(captured);relation=object(captured.get("relation"));domain=canonical(object(captured.get("before")));
            var projected=Map.<Query,ProjectedSource>of(Query.CURRENT_RELATION,source(Query.CURRENT_RELATION),Query.FAMILY_ALLIANCE,source(Query.FAMILY_ALLIANCE));
            policy=new FamilyOrdinaryPolicy(SOURCE,new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError("only supplied software read seams");}},
                    new Reads(Map.of(),projected),r->new KnownDocuments(new Documents(domain,empty(Slot.CHILD_MATRILINEAL),empty(Slot.DEFAULT_MARRIAGE),BRIDGE,SOURCE,List.of(SOURCE,SOURCE,SOURCE))),
                    (r,operation,args,plan)->{throw new AssertionError("a warm material read cannot prepare or submit another command");},
                    (r,query,args,observed)->{
                        assertSame(request,r);assertEquals(query.operation(),observed.receipt().request().operation());
                        assertEquals(args,observed.receipt().request().arguments());imports.add(query);
                        if(query==Query.CURRENT_RELATION)domain=canonical(FamilyResultReducer.matureWarm(domain,observed.value(),BRIDGE,
                                r.before().frame().episodeRunId(),r.before().frame().identity().nativeRevision()));
                        else domain=canonical(FamilyResultReducer.reduce(query,domain,args,observed.value(),BRIDGE,r.before().frame().identity().dateRaw()));
                        return true;
                    },new Settings(true,false,false,false,Optional.empty()));
        }
        private ProjectedSource source(Query query) {return new ProjectedSource(){
            @Override public ProjectedRead read(PlanningRequest actual,Obj args) {
                assertSame(request,actual);reads.add(query);Obj value;
                if(query==Query.CURRENT_RELATION)value=relation;
                else {assertEquals(Query.FAMILY_ALLIANCE,query);assertEquals(domain.get("resolved"),args.get("resolved"));
                    value=obj("alliance_status",t("allied"),"played_has_recipient_alliance",new Bool(true),"recipient_has_played_alliance",new Bool(true),
                            "relationship_status",t("marriage"),"native_revision",n(7));}
                var rawRequest=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),query.operation(),args,actual.deadline());
                String id="software-warm-read-"+reads.size();RawJson result=new RawJson(bytes(value));
                RawJson raw=new RawJson(bytes(obj("type",t("command_result"),"protocol_version",n(1),"request_id",t(id),"ok",new Bool(true),"result",value)));
                byte[] packet=ByteBuffer.allocate(raw.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.bytes().length).put(raw.bytes()).array();
                var ack=new NativeActionPort.AckReceived(id,true,Optional.of(result),raw,packet);
                var guard=new PlanningReadGuard(new GuardEvidence(actual.before(),actual.source(),actual.sessionId(),BigInteger.ONE,query.operation(),SOURCE,SOURCE,"software-warm-authority",NOW,actual.deadline()),true,true,true,"d".repeat(64));
                var receipt=new PlanningReadReceipt(rawRequest,"software-warm-contract:"+query.name(),id,guard,guard,ack);
                return new ProjectedRead(args,new PlanningReadResult.Known<>(value,receipt,SOURCE));
            }
            @Override public Obj decode(PlanningReadReceipt original) {throw new AssertionError("this seam grants no retained native authority");}
        };}
    }
    @Test void originalPrimarySpouseProducerFlowsThroughTheActualOrdinaryMaterialPortAndRequestsAFreshAlliance()throws Exception {
        Obj original=fixture();var h=new Harness(original);
        assertInstanceOf(Refresh.class,h.policy.evaluate(h.request,baseline(h.request)));
        assertEquals(List.of(Query.CURRENT_RELATION),h.reads);
        assertEquals(List.of(Query.CURRENT_RELATION),h.imports);
        assertEquals(canonical(object(original.get("after"))),h.domain);
        assertNull(object(h.domain.get("resolved")).get("alliance_result"));
        assertInstanceOf(Refresh.class,h.policy.evaluate(h.request,baseline(h.request)));
        assertEquals(List.of(Query.CURRENT_RELATION,Query.CURRENT_RELATION,Query.FAMILY_ALLIANCE),h.reads);
        assertEquals(List.of(Query.CURRENT_RELATION,Query.FAMILY_ALLIANCE),h.imports);
        assertEquals(t("marriage"),object(object(h.domain.get("resolved")).get("alliance_result")).get("relationship_status"));
    }
    @Test void pureReducerMatchesTheOriginalSerializedBodyAndRetainsAllOtherFields()throws Exception {
        Obj original=fixture(),before=canonical(object(original.get("before")));
        Obj actual=FamilyResultReducer.matureWarm(before,object(original.get("relation")),BRIDGE,"robert-test",BigInteger.valueOf(7));
        assertEquals(canonical(object(original.get("after"))),canonical(actual));
        Obj extension=obj("state",t("unknown_no_replay"),"pending_reference",rows(List.of(n(5),n(4))));
        assertEquals(actual.with("retained_extension",extension),FamilyResultReducer.matureWarm(before.with("retained_extension",extension),
                object(original.get("relation")),BRIDGE,"robert-test",BigInteger.valueOf(7)));
        assertEquals(object(before.get("resolved")).get("source_pending"),object(actual.get("resolved")).get("source_pending"));
    }
    @Test void spouseArrayAlsoProvesTheSamePairWithoutInventingAnyOtherMarriage()throws Exception {
        Obj original=fixture(),relation=object(original.get("relation")).with("primary_spouse_character_id",Nil.INSTANCE).with("spouse_character_ids",rows(List.of(n(399))));
        assertEquals(canonical(object(original.get("after"))),canonical(FamilyResultReducer.matureWarm(object(original.get("before")),relation,BRIDGE,"robert-test",BigInteger.valueOf(7))));
    }
    @Test void wrongBridgeEpisodeRevisionHeirAndUnknownOrDifferentBilateralRelationCannotMature()throws Exception {
        Obj original=fixture(),before=object(original.get("before")),relation=object(original.get("relation"));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before,relation,new BridgeIdentity(56,"new"),"robert-test",BigInteger.valueOf(7)));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before,relation,BRIDGE,"other-episode",BigInteger.valueOf(7)));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before,relation,BRIDGE,"robert-test",BigInteger.valueOf(8)));
        for(Obj wrong:List.of(relation.with("heir_character_id",n(203)),relation.with("bilateral_verified",new Bool(false)),relation.with("status",t("unavailable")),
                relation.with("native_revision",new Bool(true)),relation.with("primary_spouse_character_id",n(400)),
                relation.with("primary_spouse_character_id",Nil.INSTANCE).with("betrothed_character_id",n(399))))
            assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before,wrong,BRIDGE,"robert-test",BigInteger.valueOf(7)));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before.with("pending",obj("state",t("unknown_no_replay"))),relation,BRIDGE,"robert-test",BigInteger.valueOf(7)));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.matureWarm(before.with("resolved",object(before.get("resolved")).with("material_result",new Bool(false))),relation,BRIDGE,"robert-test",BigInteger.valueOf(7)));
    }
}

