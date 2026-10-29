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
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.marriage.MarriageCodec;
import org.xar.ck3.control.governance.marriage.MarriagePolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original policy values plus explicit software frame/read seams. No native custody or live submission credit. */
final class FamilyChildPriorityContinuationTest {
    private static final ExactRef SOURCE=new ExactRef("D:/software-family-priority/source",1,"a".repeat(64));
    private static final BridgeIdentity BRIDGE=new BridgeIdentity(77,"software-bridge-birth");
    private static final Instant NOW=Instant.parse("2026-10-29T00:00:00Z");
    private record Scene(Obj snapshot,Obj root,Obj subject,List<Obj> values) { }
    private static Scene scene(boolean war,boolean matrilineal)throws Exception {
        Obj original;
        try(var input=FamilyChildPriorityContinuationTest.class.getResourceAsStream("/marriage/python-golden-v1.json")) {
            assertNotNull(input,"reuse the immutable original marriage policy corpus");
            byte[] bytes=input.readAllBytes();assertEquals("226e6f0875c49c8a7b2eb6494c29c71fee6409ad9de93e079c29052759ca9af2",ActionCodec.sha256(bytes));
            original=object(decode(bytes).get("base_request"));
        }
        Obj snapshot=obj("snapshot_id",t("native:3"),"revision",n(9),"native_revision",n(3),"date_raw",n(100),
                "episode_run_id",t("child-priority-episode"),"paused",new Bool(true),"map_ready",new Bool(true),
                "played_character",obj("character_id",n(29829)),"played_character_gold",n(100000),
                "active_wars",war?rows(List.of(obj("war_id",n(7)))):rows(List.of()),"player_armies",rows(List.of()));
        Obj root=obj("status",t("available"),"queried_snapshot_id",snapshot.get("snapshot_id"),"queried_revision",n(9),"queried_native_revision",n(3),
                "campaign_root_context",obj("player_character_id",n(29829),"held_title_partition",rows(List.of(
                        obj("primary",new Bool(true),"first_heir_character_id",n(38987),"title",obj("title_id",n(1))),
                        obj("primary",new Bool(false),"first_heir_character_id",n(38988),"title",obj("title_id",n(2)))))));
        Obj subject=object(original.get("legality"));
        List<Obj> values=array(original.get("values")).stream().map(FamilyJson::object)
                .map(value->value.with("row",object(value.get("row")).with("selected_option_readback",Nil.INSTANCE))).toList();
        if(matrilineal) {
            subject=subject.with("adult_measure_raw",n(20));
            Obj value=values.getFirst(),row=object(value.get("row")).with("heir_is_adult",new Bool(true))
                    .with("heir_adult_measure_raw",n(20)).with("heir_sex_selector_raw",n(1)).with("candidate_sex_selector_raw",n(0))
                    .with("predicted_outcome_if_accepted",t("marriage")).with("selected_option_readback",new Bool(true))
                    .with("matrilineal_option_selected",new Bool(true)).with("effective_matrilineal_if_accepted",new Bool(true))
                    .with("requested_matrilineal_option",new Bool(true));
            values=List.of(value.with("request_matrilineal_option",new Bool(true)).with("row",row));
        }
        return new Scene(snapshot,root,subject,values);
    }
    private static Obj ledger(Slot slot){return obj("schema",t(FamilyDomainSource.schema(slot)),"pending",Nil.INSTANCE,"resolved",Nil.INSTANCE);}
    private static FamilyPendingProducer.State state(){return new FamilyPendingProducer.State(ledger(Slot.FAMILY),ledger(Slot.CHILD_MATRILINEAL),ledger(Slot.DEFAULT_MARRIAGE));}
    private static PlanningRequest request(Scene scene) {
        Obj s=scene.snapshot();var source=new G2Source("software-family-priority",NOW.toString(),"software-no-game",SOURCE);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(3),BigInteger.valueOf(100)),"native:3",BigInteger.valueOf(9),"child-priority-episode");
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        Set<OperationKey> operations=Set.of(new OperationKey("life-advance"),FamilyPendingProducer.Branch.DEFAULT.operation(),FamilyPendingProducer.Branch.MATRILINEAL.operation(),
                new OperationKey("private-select-child-education-focus-v1"));
        return new PlanningRequest(before,source,"software-family-priority-session",NOW.plusSeconds(60),
                new PlanningObservation(s,List.of(),operations,Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static ActionCommand baselineCommand(PlanningRequest r,String step) {
        var expected=new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,r.before(),r.source(),"software-existing-command/v1",List.of(new ExpectedBoolean(new FieldKey("software_existing_command_retained"),true)));
        return new ActionCommand("software-baseline-"+step,r.before(),r.source(),r.sessionId(),new OperationKey(step),obj(),expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),r.deadline());
    }
    private static Draft draft(PlanningRequest r,String step,String phase) {
        return new Draft("one-life-turn-v1",phase,"retain the independently selected original action",Kind.ORDINARY,
                step==null?Optional.empty():Optional.of(baselineCommand(r,step)),Purpose.WORLD_ACTION,Optional.empty(),
                obj("selected_step",step==null?Nil.INSTANCE:t(step),"baseline_extension",t("keep")));
    }
    private static final class Harness {
        final Scene scene;final PlanningRequest request;final List<Query> reads=new ArrayList<>();final List<ActionCommand> prepared=new ArrayList<>();
        final FamilyCommands commands;final FamilyOrdinaryPolicy policy;
        Harness(Scene scene,boolean configured) {
            this.scene=scene;request=request(scene);
            commands=new FamilyCommands((r,o,a,p)->Optional.of(baselineCommand(r,o.value())),(r,c)->{assertSame(request,r);prepared.add(c);});
            var projected=new EnumMap<Query,ProjectedSource>(Query.class);
            for(Query q:List.of(Query.CAMPAIGN_ROOT,Query.CHILD_SUBJECT,Query.CHILD_VALUE))projected.put(q,new ProjectedSource(){
                @Override public ProjectedRead read(PlanningRequest actual,Obj args) {
                    assertSame(request,actual);reads.add(q);
                    Obj value=switch(q){
                        case CAMPAIGN_ROOT->scene.root();case CHILD_SUBJECT->scene.subject();
                        case CHILD_VALUE->scene.values().stream().filter(v->eq(v.get("candidate_character_id"),args.get("candidate_character_id"))).findFirst().orElseThrow();
                        default->throw new AssertionError(q);
                    };
                    var rawRequest=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),q.operation(),args,actual.deadline());
                    String id="software-child-read-"+reads.size();RawJson result=new RawJson(bytes(value));
                    RawJson raw=new RawJson(bytes(obj("type",t("command_result"),"protocol_version",n(1),"request_id",t(id),"ok",new Bool(true),"result",value)));
                    byte[] packet=ByteBuffer.allocate(raw.bytes().length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.bytes().length).put(raw.bytes()).array();
                    var ack=new NativeActionPort.AckReceived(id,true,Optional.of(result),raw,packet);
                    var guard=new PlanningReadGuard(new GuardEvidence(actual.before(),actual.source(),actual.sessionId(),BigInteger.ONE,q.operation(),SOURCE,SOURCE,"software-child-authority",NOW,actual.deadline()),true,true,true,"b".repeat(64));
                    var receipt=new PlanningReadReceipt(rawRequest,"software-child-contract:"+q.name(),id,guard,guard,ack);
                    return new ProjectedRead(args,new PlanningReadResult.Known<>(value,receipt,SOURCE));
                }
                @Override public Obj decode(PlanningReadReceipt receipt){throw new AssertionError("no retained native authority in this software seam");}
            });
            var domains=state();var docs=new Documents(domains.family(),domains.matrilineal(),domains.childDefault(),BRIDGE,SOURCE,List.of(SOURCE,SOURCE,SOURCE));
            policy=new FamilyOrdinaryPolicy(SOURCE,new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError("only projected software originals");}},
                    new Reads(Map.of(),projected),r->{assertSame(request,r);return new KnownDocuments(docs);},commands,
                    (r,q,a,o)->{throw new AssertionError("no old material receipt in this software fixture");},
                    new Settings(false,false,false,!configured,configured?Optional.of(new Pair(BigInteger.valueOf(38988),BigInteger.valueOf(37909))):Optional.empty()));
        }
        ActionCommand select(Draft before) {
            var decision=assertInstanceOf(Replace.class,policy.evaluate(request,before));
            ActionCommand command=decision.draft().command().orElseThrow();assertEquals(command,prepared.getLast());
            return ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
        }
    }
    @Test void defaultKeepsAllExistingWarQueriesAndDoesNotReadAChildOrPrepareAnotherCommand()throws Exception {
        for(String step:List.of("query-war-termination-options-7","query-war-termination-options-8","query-war-strengths-v1","query-other")) {
            var h=new Harness(scene(true,false),false);Draft before=draft(h.request,step,"native_war_strategy");
            byte[] exact=ActionCodec.encodeCommand(before.command().orElseThrow());
            assertInstanceOf(Keep.class,h.policy.evaluate(h.request,before));assertTrue(h.reads.isEmpty());assertTrue(h.prepared.isEmpty());
            assertArrayEquals(exact,ActionCodec.encodeCommand(before.command().orElseThrow()));
        }
    }
    @Test void configuredPairDefersOnlyTheExactTerminationQueryOfAnActivePositiveWar()throws Exception {
        for(String step:List.of("query-war-termination-options-8","query-war-strengths-v1","query-other")) {
            var h=new Harness(scene(true,true),true);assertInstanceOf(Keep.class,h.policy.evaluate(h.request,draft(h.request,step,"native_war_strategy")));
            assertTrue(h.reads.isEmpty());assertTrue(h.prepared.isEmpty());
        }
        var h=new Harness(scene(true,true),true);ActionCommand command=h.select(draft(h.request,"query-war-termination-options-7","native_war_strategy"));
        assertEquals(FamilyPendingProducer.Branch.MATRILINEAL.operation(),command.operation());
        assertEquals(List.of(Query.CHILD_SUBJECT,Query.CHILD_VALUE),h.reads);
    }
    @Test void configuredPairRejectsNonIntegerAbsentAndOutOfRangeWarIdsBeforeReadingChildren()throws Exception {
        Scene base=scene(true,true);
        for(Value id:List.of(n(0),n(-1),new IntegerValue(BigInteger.ONE.shiftLeft(31)),new Bool(true),new DecimalValue("7.0"),t("7"),Nil.INSTANCE)) {
            Scene changed=new Scene(base.snapshot().with("active_wars",rows(List.of(obj("war_id",id)))),base.root(),base.subject(),base.values());
            var h=new Harness(changed,true);
            assertInstanceOf(Keep.class,h.policy.evaluate(h.request,draft(h.request,"query-war-termination-options-7","native_war_strategy")));
            assertTrue(h.reads.isEmpty());assertTrue(h.prepared.isEmpty());
        }
        Scene missing=new Scene(base.snapshot().with("active_wars",rows(List.of(obj()))),base.root(),base.subject(),base.values());
        var h=new Harness(missing,true);
        assertInstanceOf(Keep.class,h.policy.evaluate(h.request,draft(h.request,"query-war-termination-options-7","native_war_strategy")));
        assertTrue(h.reads.isEmpty());assertTrue(h.prepared.isEmpty());
    }
    @Test void defaultRequiresLifeAdvanceOrAnActualWarWaitWithoutASelectedStep()throws Exception {
        for(Scene scene:List.of(scene(false,false),scene(true,false))) {
            var h=new Harness(scene,false);assertEquals(FamilyPendingProducer.Branch.DEFAULT.operation(),h.select(draft(h.request,"life-advance","peace_growth")).operation());
        }
        var war=new Harness(scene(true,false),false);assertEquals(FamilyPendingProducer.Branch.DEFAULT.operation(),war.select(draft(war.request,null,"native_war_wait")).operation());
        var wrongPhase=new Harness(scene(true,false),false);assertInstanceOf(Keep.class,wrongPhase.policy.evaluate(wrongPhase.request,draft(wrongPhase.request,null,"other_wait")));assertTrue(wrongPhase.reads.isEmpty());
        var peace=new Harness(scene(false,false),false);assertInstanceOf(Keep.class,peace.policy.evaluate(peace.request,draft(peace.request,null,"native_war_wait")));assertTrue(peace.reads.isEmpty());
    }
    @Test void realEducationFocusCommandIsPreservedWithoutAnyChildMarriageRead()throws Exception {
        var h=new Harness(scene(true,false),false);Obj query=obj("child_full_id",n(17),"target_key",t("education_stewardship"));
        String step="private-select-child-education-focus-v1";Obj plan=obj("selected_step",t(step),"phase",t("family_child_education_focus_submission"),"family_child_education_focus_query",query);
        ActionCommand command=h.commands.prepare(h.request,new OperationKey(step),obj("query",query),plan).orElseThrow();
        byte[] original=ActionCodec.encodeCommand(command);Draft before=new Draft("one-life-turn-v1","family_child_education_focus_submission","submit the actual selected focus",Kind.ORDINARY,Optional.of(command),Purpose.WORLD_ACTION,Optional.empty(),plan);
        assertInstanceOf(Keep.class,h.policy.evaluate(h.request,before));assertTrue(h.reads.isEmpty());assertTrue(h.prepared.isEmpty());
        assertArrayEquals(original,ActionCodec.encodeCommand(before.command().orElseThrow()));
    }
    private static FamilyNativePreparation.MaterializedSend send(FamilyMarriageIntent intent) {
        return new FamilyNativePreparation.MaterializedSend(intent.actorId(),intent.recipientId(),OptionalLong.of(intent.subjectId()),OptionalLong.of(intent.candidateId()),OptionalLong.empty(),5,SOURCE);
    }
    @Test void displacedDefaultPlanSurvivesRealCommandSerdeFreshReviewPendingAndResultSerde()throws Exception {
        var h=new Harness(scene(false,false),false);Draft before=draft(h.request,"life-advance","peace_growth");ActionCommand command=h.select(before);
        FamilyMarriageIntent intent=FamilyMarriageIntent.fromJson(command.arguments());Obj displaced=obj("selected_step",t("life-advance"),"phase",t(before.phase()),"reason",t(before.reason()));
        assertEquals(displaced,intent.planningProof().orElseThrow().get("child_default_displaced_plan"));
        List<BigInteger> comparison=FamilyMarriagePreparationReview.defaultComparisonCandidates(h.scene.snapshot(),h.scene.root(),h.scene.subject(),state());
        List<Obj> values=comparison.stream().map(id->h.scene.values().stream().filter(v->integer(v.get("candidate_character_id")).equals(id)).findFirst().orElseThrow()).toList();
        Obj reviewed=FamilyMarriagePreparationReview.review(intent,h.scene.snapshot(),BRIDGE,state(),new FamilyMarriagePreparationReview.Policy(false),
                new FamilyMarriagePreparationReview.ChildDefault(h.scene.root(),h.scene.subject(),values));
        var pending=FamilyPendingProducer.produce(command,h.scene.snapshot(),BRIDGE,state(),reviewed,send(intent));
        assertEquals(displaced,pending.pending().get("deferred_prior_plan"));assertEquals(t("may_have_submitted"),pending.pending().get("submission_state"));
        Obj domain=FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE,ContinuityJson.canonical(OpportunityJson.toNode(pending.body()),ContinuityJson.DOMAIN_MAX_BYTES));
        assertEquals(pending.pending(),domain.get("pending"));
        var blocked=new FamilyPendingProducer.State(state().family(),state().matrilineal(),domain);
        assertThrows(IllegalArgumentException.class,()->FamilyPendingProducer.produce(command,h.scene.snapshot(),BRIDGE,blocked,reviewed,send(intent)));
        assertThrows(IllegalArgumentException.class,()->FamilyResultReducer.reduce(Query.DEFAULT_RESULT,domain,obj("pending",pending.pending(),"cold",new Bool(false)),obj("status",t("unknown")),BRIDGE,BigInteger.valueOf(100)));
        Obj result=obj("status",t("refused"),"material_result",new Bool(false),"heir_character_id",n(intent.subjectId()),"candidate_character_id",n(intent.candidateId()),"post_native_revision",n(4));
        Obj resolved=FamilyResultReducer.reduce(Query.DEFAULT_RESULT,domain,obj("pending",pending.pending(),"cold",new Bool(false)),result,BRIDGE,BigInteger.valueOf(100));
        Obj restored=FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE,ContinuityJson.canonical(OpportunityJson.toNode(resolved),ContinuityJson.DOMAIN_MAX_BYTES));
        assertEquals(displaced,object(object(restored.get("resolved")).get("source_pending")).get("deferred_prior_plan"));
    }
    @Test void deferredConfiguredQuerySurvivesFreshReviewAndRejectsChangedWarDateOrRoster()throws Exception {
        var h=new Harness(scene(true,true),true);ActionCommand command=h.select(draft(h.request,"query-war-termination-options-7","native_war_strategy"));
        var intent=FamilyMarriageIntent.fromJson(command.arguments());var reads=new FamilyMarriagePreparationReview.ChildMatrilineal(h.scene.subject(),h.scene.values().getFirst());
        Obj reviewed=FamilyMarriagePreparationReview.review(intent,h.scene.snapshot(),BRIDGE,state(),new FamilyMarriagePreparationReview.Policy(false),reads);
        var pending=FamilyPendingProducer.produce(command,h.scene.snapshot(),BRIDGE,state(),reviewed,send(intent));
        assertEquals(t("query-war-termination-options-7"),pending.pending().get("deferred_war_query"));
        Obj domain=FamilyDomainSource.validate(Slot.CHILD_MATRILINEAL,ContinuityJson.canonical(OpportunityJson.toNode(pending.body()),ContinuityJson.DOMAIN_MAX_BYTES));
        assertEquals(pending.pending(),domain.get("pending"));
        for(Obj changed:List.of(h.scene.snapshot().with("date_raw",n(101)),h.scene.snapshot().with("active_wars",rows(List.of(obj("war_id",n(8))))),
                h.scene.snapshot().with("active_wars",rows(List.of())))) {
            assertThrows(IllegalArgumentException.class,()->FamilyMarriagePreparationReview.review(intent,changed,BRIDGE,state(),new FamilyMarriagePreparationReview.Policy(false),reads));
        }
    }
}

