package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual family command producer -> shared native-preparation intent decoder -> command serialization. */
final class FamilyCommandsIntentTest {
    private static final OperationKey OPERATION = new OperationKey("initiate-character-interaction-ordinary-v1");
    private static Obj json(String raw) { return decode(raw.getBytes(StandardCharsets.UTF_8)); }
    private static PlanningRequest request() { return request(OPERATION); }
    private static PlanningRequest request(OperationKey operation) {
        var source = new G2Source("fixture-family-machine", "2026-10-23T18:00:00Z", "1.20.0.4", new ExactRef("D:/fixture/family-source.json", 1, "a".repeat(64)));
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(100)), "native-1", BigInteger.ONE, "ep"), 1);
        Obj snapshot = json("{\"snapshot_id\":\"native-1\",\"revision\":1,\"native_revision\":1,\"date_raw\":100,\"episode_run_id\":\"ep\",\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":1},\"active_wars\":[],\"player_armies\":[]}");
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(operation), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "family-intent-session", Instant.parse("2026-10-23T18:00:30Z"), observation);
    }
    private static FamilyCommands producer() { return new FamilyCommands((request, operation, arguments, plan) -> Optional.empty(),(original,command)->{
        assertEquals(original.before(),command.before());assertEquals(original.source(),command.source());
        assertEquals(original.sessionId(),command.sessionId());
    }); }
    private static Obj arguments() { return obj("interaction_key", t("educate_child_interaction"), "recipient_id", n(2), "child_full_id", n(2), "guardian_full_id", n(3),
            "requested_option_keys", rows(List.of()), "source_query", obj("old_query", new Bool(true)), "semantic_request_review", obj("review_token", t("old-token-evidence"))); }
    private static Obj plan() { return obj("selected_step", t(OPERATION.value()), "family_education_observations", rows(List.of(arguments()))); }

    @Test void actualProducerPublishesOnlySharedIntentAndPreservesExplicitEmptyOptionsAsIntent() {
        ActionCommand command = producer().prepare(request(), OPERATION, arguments(), plan()).orElseThrow();
        OrdinaryInitiationIntent intent = OrdinaryInitiationIntent.fromJson(command.arguments());
        assertEquals("educate_child_interaction", intent.interactionKey()); assertEquals(2, intent.recipientId());
        assertEquals(new OrdinaryInitiationIntent.Education(2, 3, List.of()), intent.education().orElseThrow());
        assertEquals(Optional.of(plan()), intent.planningProof());
        assertEquals(Set.of("schema", "interaction_key", "recipient_id", "education", "planning_proof"), command.arguments().members().keySet());
        assertFalse(command.arguments().members().containsKey("source_query"));
        assertFalse(command.arguments().members().containsKey("semantic_request_review"));
        assertEquals(Set.of(BigInteger.ONE, BigInteger.TWO, BigInteger.valueOf(3)), command.claims().characterIds());
        assertTrue(command.expected().values().contains(new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"), true)));
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertEquals(intent, OrdinaryInitiationIntent.fromJson(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)).arguments()));
    }
    @Test void actualProducerRejectsUnknownOptionsWrongPairAndNonIntegerIdsBeforeDispatch() {
        var missing = new LinkedHashMap<>(arguments().members()); missing.remove("requested_option_keys");
        for (Obj invalid : List.of(new Obj(missing), arguments().with("requested_option_keys", Nil.INSTANCE),
                arguments().with("child_full_id", new Bool(true)), arguments().with("recipient_id", n(4)),
                arguments().with("requested_option_keys", rows(List.of(t("send_language"), t("send_language"))))))
            assertThrows(IllegalArgumentException.class, () -> producer().prepare(request(), OPERATION, invalid, plan()));
    }
    @Test void rulerProducerAndSharedNativeDecoderBindTheExactPairWithoutOldQueryAuthority() {
        var operation=new OperationKey("arrange-marriage-1-2");
        Obj plan=obj("selected_step",t(operation.value()),"marriage_choice",obj("choice_id",t("1-2"),"played_character_id",n(1),"candidate_character_id",n(2),"query_sequence",n(77)));
        ActionCommand command=producer().prepare(request(operation),operation,obj("choice_id",t("1-2")),plan).orElseThrow();
        var intent=RulerMarriageIntent.fromJson(command.arguments());
        assertEquals(new RulerMarriageIntent("1-2",1,2,Optional.of(plan)),intent);assertEquals(operation.value(),intent.step());
        assertEquals(Set.of("schema","choice_id","actor_id","candidate_id","planning_proof"),command.arguments().members().keySet());
        assertFalse(command.arguments().members().containsKey("query_sequence"));assertFalse(command.arguments().members().containsKey("preflight_read"));
        assertEquals(Set.of(BigInteger.ONE,BigInteger.TWO),command.claims().characterIds());
        assertEquals(FamilyMarriageSendExpectation.expected(command.before(),command.source(),1,2),command.expected());
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertEquals(intent,RulerMarriageIntent.fromJson(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)).arguments()));
        assertThrows(IllegalArgumentException.class,()->producer().prepare(request(operation),operation,obj("choice_id",t("1-3")),plan));
        assertThrows(IllegalArgumentException.class,()->producer().prepare(request(operation),operation,obj("choice_id",t("1-2")),plan.with("marriage_choice",object(plan.get("marriage_choice")).with("played_character_id",n(4)))));
    }
    @Test void rulerSharedContractRejectsMissingFieldsNullIdsWrongDomainsAndAliasTokens() {
        Obj valid=new RulerMarriageIntent("1-2",1,2,Optional.empty()).toJson();
        var missing=new LinkedHashMap<>(valid.members());missing.remove("planning_proof");
        for(Obj invalid:List.of(new Obj(missing),valid.with("actor_id",new Bool(true)),valid.with("candidate_id",Nil.INSTANCE),
                valid.with("candidate_id",n(4294967295L)),valid.with("choice_id",t("01-2")),valid.with("choice_id",t("1-1")).with("candidate_id",n(1)),
                valid.with("query_sequence",n(1)),valid.with("planning_proof",new Arr(List.of()))))
            assertThrows(IllegalArgumentException.class,()->RulerMarriageIntent.fromJson(invalid));
    }
    private static Obj privatePlan(FamilyMarriageIntent.Route route) {
        Obj selected=obj("candidate_character_id",n(2),"recipient_character_id",n(4),"matrilineal_option_selected",new Bool(route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL));
        Obj plan=obj("selected_step",t(route.step()));
        return switch(route) {
            case FIRST_HEIR -> plan.with("family_marriage_choice",obj("candidate_character_id",n(2),"realm_alliance_attempt_if_accepted",new Bool(true)))
                .with("family_marriage_legality",obj("observed_first_heir_character_id",n(3),"native_legal_candidates",rows(List.of(obj("candidate_character_id",n(2),"recipient_matchmaker_character_id",n(4))))))
                .with("family_marriage_projection",obj("rows",rows(List.of(selected,obj("candidate_character_id",n(5)),obj("candidate_character_id",n(6)),obj("candidate_character_id",n(7)),obj("candidate_character_id",n(8))))));
            case FULFILL_BETROTHAL -> plan.with("current_betrothal_choice",selected.with("heir_character_id",n(3)).with("effective_matrilineal_if_accepted",new Bool(false))
                .with("resource_proposal",obj("heir_character_id",n(3),"character_claims",rows(List.of(n(1),n(3),n(2),n(4))))));
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> {String prefix=route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL?"child_matrilineal":"child_default";
                yield plan.with(prefix+"_legality",obj("subject_character_id",n(3))).with(prefix+"_value",obj("candidate_character_id",n(2),"row",selected));}
        };
    }
    @Test void allFourPrivateProducersUseTheSameImmutableIntentAndSendOnlyExpectation() {
        for(var route:FamilyMarriageIntent.Route.values()) {
            var operation=new OperationKey(route.step());Obj plan=privatePlan(route);
            ActionCommand command=producer().prepare(request(operation),operation,obj("old_query_sequence",n(17)),plan).orElseThrow();
            var intent=FamilyMarriageIntent.fromJson(command.arguments());
            assertEquals(route,intent.route());assertEquals(1,intent.actorId());assertEquals(3,intent.subjectId());
            assertEquals(2,intent.candidateId());assertEquals(4,intent.recipientId());
            assertEquals(route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL,intent.matrilineal());
            assertEquals(route==FamilyMarriageIntent.Route.FIRST_HEIR?List.of(2,5,6,7,8):List.of(),intent.comparisonCandidateIds());
            assertEquals(Optional.of(plan),intent.planningProof());
            assertFalse(command.arguments().members().containsKey("plan"));assertFalse(command.arguments().members().containsKey("old_query_sequence"));
            assertEquals(Set.of(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),BigInteger.valueOf(4)),command.claims().characterIds());
            assertEquals(FamilyMarriageSendExpectation.expected(command.before(),command.source(),3,2),command.expected());
            assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            assertEquals(intent,FamilyMarriageIntent.fromJson(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)).arguments()));
        }
    }
    @Test void privateProducerRejectsUnknownOptionsAndIncompleteOrDuplicateFiveRows() {
        var route=FamilyMarriageIntent.Route.FIRST_HEIR;var operation=new OperationKey(route.step());Obj plan=privatePlan(route);
        var projection=object(plan.get("family_marriage_projection"));var rows=array(projection.get("rows"));
        for(Obj changed:List.of(plan.with("family_marriage_projection",projection.with("rows",new Arr(rows.subList(0,4)))),
                plan.with("family_marriage_projection",projection.with("rows",new Arr(List.of(rows.get(0),rows.get(1),rows.get(2),rows.get(3),rows.get(3))))),
                plan.with("family_marriage_projection",projection.with("rows",new Arr(List.of(object(rows.get(0)).with("matrilineal_option_selected",n(1)),rows.get(1),rows.get(2),rows.get(3),rows.get(4)))))))
            assertThrows(IllegalArgumentException.class,()->producer().prepare(request(operation),operation,obj(),changed));
    }
    @Test void sharedPrivateDecoderRejectsBooleanIdsMissingNullableAndLegacyPlanAuthority() {
        Obj valid=new FamilyMarriageIntent(FamilyMarriageIntent.Route.FIRST_HEIR,1,3,2,4,false,List.of(2,5,6,7,8),Optional.empty()).toJson();
        var missing=new LinkedHashMap<>(valid.members());missing.remove("planning_proof");
        for(Obj invalid:List.of(new Obj(missing),valid.with("actor_id",new Bool(true)),valid.with("matrilineal",n(0)),
                valid.with("subject_id",Nil.INSTANCE),valid.with("comparison_candidate_ids",new Arr(List.of(n(2),n(5),n(6),n(7),new Bool(true)))),
                valid.with("plan",obj("query_sequence",n(77))),valid.with("route",t("child_default"))))
            assertThrows(IllegalArgumentException.class,()->FamilyMarriageIntent.fromJson(invalid));
    }
    @Test void allFiveMarriageProducersRetainTheActualCompletePlanningRequestAndRejectCrossedFrame() {
        var captured=new java.util.concurrent.atomic.AtomicReference<PlanningRequest>();
        var commands=new FamilyCommands((request,operation,args,plan)->Optional.empty(),(request,command)->captured.set(request));
        for(var route:FamilyMarriageIntent.Route.values()) {
            var operation=new OperationKey(route.step());var request=request(operation);
            var command=commands.prepare(request,operation,obj(),privatePlan(route)).orElseThrow();
            assertSame(request,captured.get());FamilyNativePreparation.requireCommandFrame(command,request.observations().snapshot());
            for(var changed:List.of(request.observations().snapshot().with("revision",n(2)),
                    request.observations().snapshot().with("native_revision",new Bool(true)),
                    request.observations().snapshot().with("episode_run_id",t("other")),
                    request.observations().snapshot().with("played_character",obj("character_id",n(2))),
                    request.observations().snapshot().with("paused",new Bool(false))))
                assertThrows(IllegalArgumentException.class,()->FamilyNativePreparation.requireCommandFrame(command,changed));
        }
        var operation=new OperationKey("arrange-marriage-1-2");var request=request(operation);
        var plan=obj("selected_step",t(operation.value()),"marriage_choice",obj("choice_id",t("1-2"),"played_character_id",n(1),"candidate_character_id",n(2)));
        var command=commands.prepare(request,operation,obj("choice_id",t("1-2")),plan).orElseThrow();
        assertSame(request,captured.get());FamilyNativePreparation.requireCommandFrame(command,request.observations().snapshot());
    }
    @Test void actualFocusProducerUsesAllFiveSharedTypedTargetsAndOnlyKeepsOldQueryAsPlanningEvidence() {
        var operation=new OperationKey(ChildEducationFocusIntent.STEP);
        for(var target:ChildEducationFocusIntent.FocusKey.values()) {
            Obj query=obj("child_full_id",n(2),"target_key",t(target.wire()),"query_sequence",n(77),"old_query_revision",n(88));
            Obj plan=obj("selected_step",t(operation.value()),"child_focus_observation",query);
            var command=producer().prepare(request(operation),operation,obj("query",query),plan).orElseThrow();
            var intent=ChildEducationFocusIntent.fromJson(command.arguments());
            assertEquals(new ChildEducationFocusIntent(2,target,Optional.of(plan)),intent);
            assertEquals(intent.expected(command.before(),command.source()),command.expected());
            assertEquals(Set.of("schema","child_full_id","target_key","planning_proof"),command.arguments().members().keySet());
            assertFalse(command.arguments().members().containsKey("query"));assertFalse(command.arguments().members().containsKey("plan"));
            assertEquals(Set.of(BigInteger.TWO),command.claims().characterIds());
            assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            assertEquals(intent,ChildEducationFocusIntent.fromJson(ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)).arguments()));
        }
    }
    @Test void actualFocusProducerRejectsWrongIdTypesUnknownFocusAndSentinelIdsBeforeDispatch() {
        var operation=new OperationKey(ChildEducationFocusIntent.STEP);Obj plan=obj("selected_step",t(operation.value()));
        Obj query=obj("child_full_id",n(2),"target_key",t(ChildEducationFocusIntent.FocusKey.values()[0].wire()));
        for(Obj invalid:List.of(query.with("child_full_id",new Bool(true)),query.with("child_full_id",n(4294967295L)),
                query.with("target_key",t("learning")),query.with("target_key",Nil.INSTANCE)))
            assertThrows(IllegalArgumentException.class,()->producer().prepare(request(operation),operation,obj("query",invalid),plan));
    }
}
