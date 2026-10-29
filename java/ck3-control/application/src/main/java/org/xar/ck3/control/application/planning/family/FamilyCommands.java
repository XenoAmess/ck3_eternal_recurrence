package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure family command producer. Native preparation, reservation and submission stay with the shared authority. */
public final class FamilyCommands implements Commands {
    public static final String OBSERVER_SCHEMA = "xar.java.family-action-observation/v1";
    private static final Set<String> PRIVATE = Set.of("submit-observed-first-heir-marriage-v1-private",
            "submit-current-first-heir-betrothal-fulfillment-v1-private", "submit-player-child-matrilineal-marriage-v1-private",
            "submit-player-child-default-marriage-v1-private", "private-select-child-education-focus-v1", "initiate-character-interaction-ordinary-v1");
    private final Commands sharedDateAdvance;
    private final FamilyNativePreparation.PlanningOriginalCapture originals;
    public FamilyCommands(Commands sharedDateAdvance,FamilyNativePreparation.PlanningOriginalCapture actualOriginals) {
        this.sharedDateAdvance=Objects.requireNonNull(sharedDateAdvance);originals=Objects.requireNonNull(actualOriginals);
    }
    @Override public Optional<ActionCommand> prepare(PlanningRequest request, OperationKey operation, Obj arguments, Obj completePlan) {
        String step = operation.value();
        if ("life-advance".equals(step)) return sharedDateAdvance.prepare(request, operation, arguments, completePlan);
        if (!PRIVATE.contains(step) && !step.matches("arrange-marriage-[0-9]+-[0-9]+")) return Optional.empty();
        if (!request.observations().actionSteps().contains(operation)) return Optional.empty();
        if (!new Text(step).equals(completePlan.get("selected_step"))) throw new IllegalArgumentException("family command differs from selected producer plan");
        List<ExpectedValue> expected = expected(operation, arguments, completePlan);
        Claims claims = claims(request, operation, arguments, completePlan);
        Obj payload;
        if (step.equals("initiate-character-interaction-ordinary-v1")) {
            // The shared contract carries the exact intent. The native preparation
            // obtains fresh terms and materializes them under the original writer.
            // The planner's source query/review remains evidence in planningProof.
            var education = new OrdinaryInitiationIntent.Education(positive(arguments.get("child_full_id")).longValueExact(),
                    positive(arguments.get("guardian_full_id")).longValueExact(),
                    array(arguments.get("requested_option_keys")).stream().map(FamilyJson::text).toList());
            payload = new OrdinaryInitiationIntent(text(arguments.get("interaction_key")), positive(arguments.get("recipient_id")).longValueExact(),
                    Optional.of(education), Optional.of(completePlan)).toJson();
        } else if (step.startsWith("arrange-marriage-")) {
            Obj choice = object(completePlan.get("marriage_choice"));
            var intent = new RulerMarriageIntent(text(arguments.get("choice_id")), positive(choice.get("played_character_id")).longValueExact(),
                    positive(choice.get("candidate_character_id")).longValueExact(), Optional.of(completePlan));
            if (!step.equals(intent.step()) || !eq(choice.get("played_character_id"), object(request.observations().snapshot().get("played_character")).get("character_id")))
                throw new IllegalArgumentException("ruler marriage intent differs from selected pair or actual actor");
            payload = intent.toJson();
        } else if (FamilyPendingProducer.operations().contains(operation)) payload = marriageIntent(request, operation, completePlan).toJson();
        else payload = focusIntent(arguments,completePlan).toJson();
        String decision = step + ":" + ActionCodec.sha256(bytes(payload));
        ExpectedPostcondition postcondition;
        if (step.startsWith("arrange-marriage-") || FamilyPendingProducer.operations().contains(operation)) {
            var pair = marriagePair(operation, completePlan);
            postcondition = FamilyMarriageSendExpectation.expected(request.before(), request.source(), pair.subject(), pair.candidate());
        } else if(step.equals(ChildEducationFocusIntent.STEP))postcondition=ChildEducationFocusIntent.fromJson(payload).expected(request.before(),request.source());
        else postcondition = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, request.before(), request.source(), OBSERVER_SCHEMA, expected);
        var command=new ActionCommand(ActionIds.forDecision(request.sessionId(), request.before(), decision), request.before(), request.source(), request.sessionId(),
                operation, payload, postcondition, claims, request.deadline());
        FamilyNativePreparation.requireCommandFrame(command,request.observations().snapshot());
        try {if(step.startsWith("arrange-marriage-")||FamilyPendingProducer.operations().contains(operation))originals.capture(request,command);}
        catch(java.io.IOException unavailable) {throw new java.io.UncheckedIOException("actual complete family planning original unavailable",unavailable);}
        return Optional.of(command);
    }
    private record MarriagePair(long subject,long candidate) { }
    private static ChildEducationFocusIntent focusIntent(Obj arguments,Obj plan) {
        var query=object(arguments.get("query"));return new ChildEducationFocusIntent(positive(query.get("child_full_id")).longValueExact(),
                ChildEducationFocusIntent.FocusKey.fromWire(text(query.get("target_key"))),Optional.of(plan));
    }
    private static MarriagePair marriagePair(OperationKey operation, Obj plan) {
        String step = operation.value();Obj pair;Value subject;
        if (step.startsWith("arrange-marriage-")) {pair=object(plan.get("marriage_choice"));subject=pair.get("played_character_id");}
        else if (step.equals("submit-current-first-heir-betrothal-fulfillment-v1-private")) {pair=object(plan.get("current_betrothal_choice"));subject=pair.get("heir_character_id");}
        else if (step.equals("submit-observed-first-heir-marriage-v1-private")) {pair=object(plan.get("family_marriage_choice"));subject=object(plan.get("family_marriage_legality")).get("observed_first_heir_character_id");}
        else {String prefix=step.contains("matrilineal")?"child_matrilineal":"child_default";pair=object(plan.get(prefix+"_value"));subject=object(plan.get(prefix+"_legality")).get("subject_character_id");}
        return new MarriagePair(positive(subject).longValueExact(),positive(pair.get("candidate_character_id")).longValueExact());
    }
    private static FamilyMarriageIntent marriageIntent(PlanningRequest request,OperationKey operation,Obj plan) {
        FamilyMarriageIntent.Route route=java.util.Arrays.stream(FamilyMarriageIntent.Route.values()).filter(value->value.step().equals(operation.value())).findFirst().orElseThrow();
        var pair=marriagePair(operation,plan);Value recipient,matrilineal;List<Integer> comparisons=List.of();
        switch(route) {
            case FIRST_HEIR -> {
                Value selected=new IntegerValue(BigInteger.valueOf(pair.candidate()));
                Obj legal=one(array(object(plan.get("family_marriage_legality")).get("native_legal_candidates")),selected);
                List<Value> rows=array(object(plan.get("family_marriage_projection")).get("rows"));Obj row=one(rows,selected);
                recipient=legal.get("recipient_matchmaker_character_id");matrilineal=row.get("matrilineal_option_selected");
                comparisons=rows.stream().map(FamilyJson::object).map(value->positive(value.get("candidate_character_id")).intValueExact()).toList();
            }
            case FULFILL_BETROTHAL -> {Obj choice=object(plan.get("current_betrothal_choice"));recipient=choice.get("recipient_character_id");matrilineal=choice.get("effective_matrilineal_if_accepted");}
            case CHILD_MATRILINEAL,CHILD_DEFAULT -> {String prefix=route==FamilyMarriageIntent.Route.CHILD_MATRILINEAL?"child_matrilineal":"child_default";Obj row=object(object(plan.get(prefix+"_value")).get("row"));recipient=row.get("recipient_character_id");matrilineal=row.get("matrilineal_option_selected");}
            default -> throw new IllegalStateException("unhandled marriage route");
        }
        if (!(matrilineal instanceof Bool option)) throw new IllegalArgumentException("selected native marriage option is unknown");
        return new FamilyMarriageIntent(route,positive(object(request.observations().snapshot().get("played_character")).get("character_id")).longValueExact(),
                Math.toIntExact(pair.subject()),Math.toIntExact(pair.candidate()),positive(recipient).intValueExact(),option.value(),comparisons,Optional.of(plan));
    }
    private static Obj one(List<Value> rows,Value candidate) {
        var selected=rows.stream().map(FamilyJson::object).filter(row->eq(row.get("candidate_character_id"),candidate)).toList();
        if(selected.size()!=1)throw new IllegalArgumentException("one exact selected marriage row required");return selected.get(0);
    }
    static List<ExpectedValue> expected(OperationKey operation, Obj arguments, Obj plan) {
        String step = operation.value(); List<ExpectedValue> result = new ArrayList<>();
        if (step.startsWith("arrange-marriage-") || FamilyPendingProducer.operations().contains(operation)) {
            var pair=marriagePair(operation,plan);return FamilyMarriageSendExpectation.values(pair.subject(),pair.candidate());
        } else if (step.equals("private-select-child-education-focus-v1")) {
            return focusIntent(arguments,plan).values();
        } else if (step.equals("initiate-character-interaction-ordinary-v1")) {
            result.add(id("child_full_id", arguments.get("child_full_id"))); result.add(id("guardian_full_id", arguments.get("guardian_full_id")));
            // A ward may travel after the send. Only an independent outgoing-request
            // observation can settle submission; the later guardian relation is separate.
            result.add(new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"), true));
        } else throw new IllegalArgumentException("no family expectation producer for operation");
        return List.copyOf(result);
    }
    private static ExpectedInteger id(String key, Value value) { return new ExpectedInteger(new FieldKey(key), positive(value)); }
    private static Claims claims(PlanningRequest request, OperationKey operation, Obj arguments, Obj plan) {
        Set<BigInteger> characters = new HashSet<>(); Set<BigInteger> allies = new HashSet<>(); Set<String> commitments = new HashSet<>();
        String step = operation.value();
        for (ExpectedValue value : expected(operation, arguments, plan)) if (value instanceof ExpectedInteger id) characters.add(id.value());
        if (step.equals("initiate-character-interaction-ordinary-v1"))
            characters.add(positive(object(request.observations().snapshot().get("played_character")).get("character_id")));
        if (step.equals("submit-current-first-heir-betrothal-fulfillment-v1-private")) {
            Obj resource = object(object(plan.get("current_betrothal_choice")).get("resource_proposal"));
            characters.clear(); for (Value id : array(resource.get("character_claims"))) characters.add(positive(id));
            commitments.add("first-heir-marriage:" + positive(resource.get("heir_character_id")));
        } else if (step.equals("submit-observed-first-heir-marriage-v1-private")) {
            Obj choice = object(plan.get("family_marriage_choice")); Value candidate = choice.get("candidate_character_id");
            Obj legality = object(plan.get("family_marriage_legality"));
            Obj nativeRow = array(legality.get("native_legal_candidates")).stream().map(FamilyJson::object)
                    .filter(row -> eq(row.get("candidate_character_id"), candidate)).findFirst().orElseThrow();
            BigInteger recipient = positive(nativeRow.get("recipient_matchmaker_character_id")); characters.add(recipient);
            characters.add(positive(object(request.observations().snapshot().get("played_character")).get("character_id")));
            if (yes(choice.get("realm_alliance_attempt_if_accepted"))) allies.add(recipient);
            commitments.add("first-heir-marriage:" + positive(legality.get("observed_first_heir_character_id")));
        } else if (step.contains("child") && step.contains("marriage")) {
            String prefix = step.contains("matrilineal") ? "child_matrilineal" : "child_default";
            BigInteger subject = positive(object(plan.get(prefix + "_legality")).get("subject_character_id"));
            Obj row = object(object(plan.get(prefix + "_value")).get("row"));
            characters.add(subject); characters.add(positive(row.get("recipient_character_id")));
            characters.add(positive(object(request.observations().snapshot().get("played_character")).get("character_id")));
            commitments.add("child-marriage:" + subject);
        }
        return new Claims(Set.of(), allies, characters, commitments);
    }
}
