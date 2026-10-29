package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual facade/read/command codecs with software packets; no Root custody, submission success or Game claim. */
final class InteractionPublicCommandPreparationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("synthetic/public-interaction-original",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("synthetic-public-interactions",NOW.toString(),Build.CROZIER4.version(),REF);
    private static final Claims CLAIMS=new Claims(Set.of(BigInteger.valueOf(8)),Set.of(BigInteger.valueOf(9)),Set.of(BigInteger.valueOf(10)),Set.of("existing-commitment"));

    @Test void marriageProducerPreparesOriginalProofWithoutSubmission() {
        var rig=new Rig();var context=context(56,SOURCE,"session");rig.facade.queryArrangeMarriageChoices(context);
        var command=rig.facade.prepareArrangeMarriage(context,"marriage-public",CLAIMS,"101-202");
        assertEquals(0,rig.actions.calls);assertEquals(context.before(),command.before());
        assertEquals("arrange-marriage-101-202",command.operation().value());
        var intent=RulerMarriageIntent.fromJson(command.arguments());assertEquals("101-202",intent.choiceId());
        var proof=intent.planningProof().orElseThrow();
        assertEquals(BigInteger.valueOf(11),OpportunityJson.integer(proof.get("query_sequence"),"query sequence"));
        assertEquals(REF,InteractionArguments.ref(InteractionArguments.parseApp(proof).get("original_query")));
        assertEquals(CLAIMS.armyIds(),command.claims().armyIds());assertEquals(CLAIMS.commitmentKeys(),command.claims().commitmentKeys());
        assertEquals(Set.of(BigInteger.valueOf(10),BigInteger.valueOf(101),BigInteger.valueOf(202)),command.claims().characterIds());
        assertEquals(FamilyMarriageSendExpectation.expected(context.before(),SOURCE,101,202),command.expected());
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        consumed(rig,context);
    }
    @Test void wrapperKeepsOriginalFinallyBoundary() {
        var context=context(56,SOURCE,"session");var prepared=new Rig();prepared.facade.queryArrangeMarriageChoices(context);
        var expected=prepared.facade.prepareArrangeMarriage(context,"marriage-wrapper",CLAIMS,"101-202");
        var legacy=new Rig();legacy.facade.queryArrangeMarriageChoices(context);
        legacy.actions.during=()->legacy.facade.queryArrangeMarriageChoices(context);
        assertSame(legacy.actions.stop,assertThrows(SubmissionBoundary.class,()->legacy.facade.arrangeMarriage(action(context,"marriage-wrapper"),"101-202")));
        assertEquals(1,legacy.actions.calls);assertEquals(expected,legacy.actions.last);
        consumed(legacy,context);
    }
    @Test void changedFrameSourceSessionAndMissingChoiceConsumeTheQuery() {
        var original=context(56,SOURCE,"session");
        var foreignSource=new G2Source(SOURCE.machineId(),NOW.plusSeconds(1).toString(),Build.CROZIER4.version(),REF);
        for(var changed:List.of(context(57,SOURCE,"session"),context(56,foreignSource,"session"),context(56,SOURCE,"other-session"))) {
            var rig=new Rig();rig.facade.queryArrangeMarriageChoices(original);
            assertThrows(IllegalArgumentException.class,()->rig.facade.prepareArrangeMarriage(changed,"changed",CLAIMS,"101-202"));
            consumed(rig,original);assertEquals(0,rig.actions.calls);
        }
        for(String choice:List.of("101-303","invalid-choice")) {
            var rig=new Rig();rig.facade.queryArrangeMarriageChoices(original);
            if(choice.equals("101-303"))
                assertThrows(InteractionOriginalFailure.class,()->rig.facade.prepareArrangeMarriage(original,"missing-choice",CLAIMS,choice));
            else assertThrows(IllegalArgumentException.class,()->rig.facade.prepareArrangeMarriage(original,"missing-choice",CLAIMS,choice));
            consumed(rig,original);
        }
    }
    @Test void originalProjectionRejectsIncompleteMissingNullAndWrongTypeDiagnostics() {
        var context=context(56,SOURCE,"session");
        for(int mode=0;mode<4;mode++) {
            var rig=new Rig();var diagnostics=(ObjectNode)rig.nativeResult.get("arrange_marriage_diagnostics");
            switch(mode) {case 0->diagnostics.put("slots_scanned",0);case 1->diagnostics.remove("slots_scanned");case 2->diagnostics.putNull("slots_scanned");case 3->diagnostics.put("slots_scanned",true);default->throw new AssertionError();}
            rig.facade.queryArrangeMarriageChoices(context);
            assertThrows(IllegalArgumentException.class,()->rig.facade.prepareArrangeMarriage(context,"bad-original",CLAIMS,"101-202"));
            assertEquals(0,rig.actions.calls);consumed(rig,context);
        }
    }
    @Test void ordinaryProducerAndWrapperPreservePlainAndEducationIntents() {
        var action=action(context(56,SOURCE,"session"),"ordinary-public");
        for(var request:List.of(new OrdinaryRequest(new InteractionKey("sway_interaction"),new CharacterId(202),Optional.empty()),
                education(List.of()),education(List.of(new InteractionKey("convert_culture"),new InteractionKey("convert_faith"))))) {
            var rig=new Rig();var prepared=rig.facade.prepareInitiateCharacterInteractionOrdinaryV1(action,request);
            assertEquals(0,rig.actions.calls);assertSame(action.expected(),prepared.expected());assertSame(CLAIMS,prepared.claims());
            var intent=OrdinaryInitiationIntent.fromJson(prepared.arguments());assertEquals(request.interaction().value(),intent.interactionKey());
            assertEquals(request.recipient().value(),intent.recipientId());assertTrue(intent.planningProof().isEmpty());
            request.education().ifPresent(value->{var typed=intent.education().orElseThrow();assertEquals(202,typed.childId());assertEquals(303,typed.guardianId());assertEquals(value.options().orElseThrow().stream().map(InteractionKey::value).toList(),typed.optionKeys());});
            assertEquals(prepared,ActionCodec.decodeCommand(ActionCodec.encodeCommand(prepared)));
            assertSame(rig.actions.stop,assertThrows(SubmissionBoundary.class,()->rig.facade.initiateCharacterInteractionOrdinaryV1(action,request)));
            assertEquals(1,rig.actions.calls);assertEquals(prepared,rig.actions.last);
        }
    }
    @Test void originalMissingChoiceFaultRequiresTheActualFacadeContextAndSelector() {
        var context=context(56,SOURCE,"session");var rig=new Rig();
        var missing=assertThrows(InteractionOriginalFailure.class,
                ()->rig.facade.prepareArrangeMarriage(context,"missing-query",CLAIMS,"101-202"));
        assertEquals(InteractionOriginalFailure.Kind.MARRIAGE_CHOICE_NOT_IN_LATEST_QUERY,missing.kind());
        assertEquals(InteractionOriginalFailure.CauseBranch.NO_RETAINED_QUERY,missing.causeBranch());
        assertEquals("BridgeUnavailableError",missing.originalErrorClass());
        assertEquals("native arrange-marriage choice is not in the latest query",missing.originalMessage());
        assertEquals(missing.originalMessage(),missing.getMessage());assertSame(context,missing.actualContext());
        assertTrue(missing.originalQuery().isEmpty());missing.requireProducer(rig.facade,context,"101-202");
        assertThrows(IllegalArgumentException.class,()->missing.requireProducer(new Rig().facade,context,"101-202"));
        assertThrows(IllegalArgumentException.class,()->missing.requireProducer(rig.facade,context(57,SOURCE,"session"),"101-202"));
        assertThrows(IllegalArgumentException.class,()->missing.requireProducer(rig.facade,context,"101-303"));
        for(var constructor:InteractionOriginalFailure.class.getDeclaredConstructors())
            assertTrue(java.lang.reflect.Modifier.isPrivate(constructor.getModifiers()),"no caller DTO constructor can mint an original failure");
        rig.facade.queryArrangeMarriageChoices(context);
        var absent=assertThrows(InteractionOriginalFailure.class,
                ()->rig.facade.prepareArrangeMarriage(context,"missing-choice",CLAIMS,"101-303"));
        assertEquals(InteractionOriginalFailure.CauseBranch.CHOICE_ABSENT,absent.causeBranch());
        assertEquals(Optional.of(REF),absent.originalQuery());absent.requireProducer(rig.facade,context,"101-303");
        consumed(rig,context);assertEquals(0,rig.actions.calls);
        rig.facade.queryArrangeMarriageChoices(context);
        assertEquals("arrange-marriage-101-202",rig.facade.prepareArrangeMarriage(context,"new-original-query",CLAIMS,"101-202").operation().value());
        assertEquals(0,rig.actions.calls);
    }
    @Test void failedRequeryInvalidatesThePreviousChoicesWithoutInventingAnOriginalFailureClass() {
        var context=context(56,SOURCE,"session");var rig=new Rig();rig.facade.queryArrangeMarriageChoices(context);
        rig.nativeResult.put("query_sequence",true);
        Throwable actual=assertThrows(IllegalStateException.class,()->rig.facade.queryArrangeMarriageChoices(context));
        assertFalse(actual instanceof InteractionOriginalFailure,"native decoder failure cannot be classified from a Java exception message");
        consumed(rig,context);assertEquals(0,rig.actions.calls);
    }
    @Test void malformedJavaSelectorDoesNotMintAPythonOriginalFailure() {
        var context=context(56,SOURCE,"session");var rig=new Rig();
        assertThrows(NullPointerException.class,()->rig.facade.prepareArrangeMarriage(context,"bad-empty",CLAIMS,"invalid-choice"));
        rig.facade.queryArrangeMarriageChoices(context);
        Throwable actual=assertThrows(IllegalArgumentException.class,()->rig.facade.prepareArrangeMarriage(context,"bad-selector",CLAIMS,"invalid-choice"));
        assertFalse(actual instanceof InteractionOriginalFailure);consumed(rig,context);assertEquals(0,rig.actions.calls);
    }
    private static void consumed(Rig rig,Context context){
        var failure=assertThrows(InteractionOriginalFailure.class,()->rig.facade.prepareArrangeMarriage(context,"no-replay",CLAIMS,"101-202"));
        assertEquals(InteractionOriginalFailure.CauseBranch.NO_RETAINED_QUERY,failure.causeBranch());
        assertTrue(failure.originalQuery().isEmpty());failure.requireProducer(rig.facade,context,"101-202");
    }
    private static OrdinaryRequest education(List<InteractionKey> options){return new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(202),Optional.of(new EducationIntent(Optional.of(new CharacterId(202)),Optional.of(new CharacterId(303)),Optional.of(options))));}
    private static ActionContext action(Context context,String id){return new ActionContext(context,id,FamilyMarriageSendExpectation.expected(context.before(),context.source(),101,202),CLAIMS);}
    private static Context context(int revision,G2Source source,String session){
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(53146848)),"native:7",BigInteger.valueOf(revision),"synthetic-public-episode");
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        return new Context(before,source,session,BigInteger.TWO,Build.CROZIER4,NOW.plusSeconds(30),new ControlFrame(true,true,true,1,19L,101,"synthetic-public-episode",false,null,null,List.of()));
    }
    private static final class SubmissionBoundary extends RuntimeException { private static final long serialVersionUID=1L; }
    private static final class Capture implements ActionCoordinatorPort {
        final SubmissionBoundary stop=new SubmissionBoundary();int calls;ActionCommand last;Runnable during;
        @Override public ActionReceipt execute(ActionCommand command){calls++;last=command;if(during!=null)during.run();throw stop;}
        @Override public ActionReceipt reconcile(String id){throw new AssertionError("preparation does not reconcile");}
    }
    private static final class Rig {
        final Capture actions=new Capture();final ObjectNode nativeResult=packet();final InteractionCapabilities facade;
        Rig(){
            var sources=new InteractionCapabilities.Sources(REF,REF,REF,REF,REF,REF,REF,REF,REF,REF);
            var subject=new InteractionCapabilities.RootHeirSource(){
                @Override public PlanningReadResult<HeirSubject> read(Context context){throw new AssertionError("no Root read required");}
                @Override public PlanningReadResult<HeirSubject> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Context context){throw new AssertionError("no Root read required");}
            };
            var installed=new InteractionCapabilities.Installation(sources,new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of()),subject);
            var reads=new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                assertSame(installed.marriageChoices(),contract);
                try{var receipt=receipt(contract,request,nativeResult);return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);}
                catch(Exception failure){throw new IllegalStateException(failure);}
            }};
            facade=new InteractionCapabilities(installed,reads,actions);
        }
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,ObjectNode result)throws Exception {
        String id="choices-query";var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",result);
        byte[] bytes=StrictJson.canonical(frame);var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(bytes),NativeWire.packet(bytes));
        var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.TWO,request.operation(),REF,REF,"synthetic-authority",NOW,NOW.plusSeconds(60));
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static ObjectNode packet(){
        var n=StrictJson.object().put("step","query-arrange-marriage-choices").put("accepted",true).put("status","available").put("query_sequence",11);
        n.putArray("arrange_marriage_choices").addObject().put("choice_id","101-202").put("played_character_id",101).put("candidate_character_id",202);
        n.putObject("arrange_marriage_diagnostics").put("storage_capacity",1).put("slots_scanned",1).put("empty_slots",0).put("live_candidates",1).put("dead_candidates",0).put("self_candidates",0).put("generation_mismatch_candidates",0).put("contexts_constructed",1).put("context_construct_failures",0).put("native_validate_true",1).put("native_validate_false",0).putArray("validation_false_samples");return n;
    }
}
