package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The original blocked-marriage continuation, retaining the factual pending window in every frame. */
public final class KnownPendingInteractionContinuation {
    @FunctionalInterface public interface Core {
        OrdinaryPolicy.Decision choose(PlanningRequest sameObservedFrame,OrdinaryPolicy.Draft previous);
    }
    private record Scope(PlanningRequest original,PlanningRequest candidatesOnly,int pendingId) { }
    private static final Set<String> PENDING=Set.of("accept-pending-character-interaction",
            "reject-pending-character-interaction","block-pending-character-interaction",
            "acknowledge-pending-character-interaction",PendingContextCodec.STEP);
    private final Core core;
    private final ThreadLocal<Scope> scope=new ThreadLocal<>();
    public KnownPendingInteractionContinuation(Core actualSameCore) { core=Objects.requireNonNull(actualSameCore); }

    /** Only this instance's two pending leaves may defer during the synchronous same-core invocation. */
    public boolean defers(PlanningRequest request) {
        Scope current=scope.get();
        if(current==null)return false;
        need(current.candidatesOnly().equals(request),"blocked-marriage continuation crossed its exact request");
        ObjectNode snapshot=InteractionArguments.parseApp(request.observations().snapshot());
        JsonNode pending=snapshot.get("pending_character_interaction");
        need(pending!=null&&pending.isObject()&&KnownPendingInteractionEvidence.equalInt(pending.get("instance_id"),
                java.math.BigInteger.valueOf(current.pendingId()))
                &&KnownPendingInteractionEvidence.equalBoolean(pending.get("auto_accept_notification"),false),
                "blocked-marriage continuation lost its actual original pending window");
        need(request.before().equals(current.original().before())&&request.source().equals(current.original().source())
                &&request.sessionId().equals(current.original().sessionId())
                &&request.observations().snapshot().equals(current.original().observations().snapshot()),
                "ordinary continuation cannot manufacture a cleared-window observation");
        return true;
    }
    public OrdinaryPolicy.Decision choose(PlanningRequest request,OrdinaryPolicy.Draft diagnosis,OrdinaryPolicy.Draft previous) {
        if(!blockedMarriage(diagnosis))return new OrdinaryPolicy.Replace(diagnosis,"retain the dedicated pending diagnosis");
        ObjectNode snapshot=InteractionArguments.parseApp(request.observations().snapshot());
        ObjectNode detail=InteractionArguments.parseApp(diagnosis.detail());
        JsonNode pending=snapshot.get("pending_character_interaction");
        JsonNode modal=snapshot.get("top_exclusive_modal_choice_hint");
        if(pending==null||!pending.isObject()||!KnownPendingInteractionEvidence.equalBoolean(pending.get("auto_accept_notification"),false)
                ||!Objects.equals(pending.get("instance_id"),detail.path("decision").get("pending_interaction_id"))
                ||present(snapshot.get("active_event"))||present(snapshot.get("current_event"))
                ||modal!=null&&modal.isObject()&&KnownPendingInteractionEvidence.equalText(modal.get("status"),"present"))
            return new OrdinaryPolicy.Replace(diagnosis,"real events and exclusive modals retain priority");
        int pendingId=integer(pending,"instance_id",Integer.MIN_VALUE,Integer.MAX_VALUE);
        need(pendingId!=-1,"full generation-bearing pending ID required");
        PlanningObservation base=request.observations();
        Set<OperationKey> allowed=base.actionSteps().stream().filter(operation->!PENDING.contains(operation.value()))
                .collect(Collectors.toUnmodifiableSet());
        PlanningRequest projected=new PlanningRequest(request.before(),request.source(),request.sessionId(),request.deadline(),
                new PlanningObservation(base.snapshot(),base.history(),allowed,base.bridgeCapabilities(),base.battleSpeedReadiness(),
                        base.actionFacts(),base.campaignGoal(),base.crossRunPlan(),base.initialLifestyleFocusRequired()));
        need(scope.get()==null,"recursive blocked-marriage continuation is forbidden");
        OrdinaryPolicy.Decision selected;
        scope.set(new Scope(request,projected,pendingId));
        try { selected=Objects.requireNonNull(core.choose(projected,previous)); }
        finally { scope.remove(); }
        if(!(selected instanceof OrdinaryPolicy.Replace replacement)||replacement.draft().command().isEmpty())
            return new OrdinaryPolicy.Replace(diagnosis,"ordinary core produced no independently executable continuation");
        OrdinaryPolicy.Draft ordinary=replacement.draft();
        var command=ordinary.command().orElseThrow();
        if(!allowed.contains(command.operation())||PENDING.contains(command.operation().value())||ordinary.phase().startsWith("pending_"))
            return new OrdinaryPolicy.Replace(diagnosis,"ordinary continuation cannot offer any pending reply or query");
        need(command.before().equals(request.before())&&command.source().equals(request.source())
                &&command.sessionId().equals(request.sessionId())&&!command.deadline().isAfter(request.deadline()),
                "ordinary continuation changed the observed frame/source/session/deadline");
        ObjectNode output=InteractionArguments.parseApp(ordinary.detail());
        output.set("deferred_pending_interaction",detail.deepCopy());
        output.putObject("notification_continuation").put("policy","blocked-marriage-reply-ordinary-continuation-v1")
                .put("pending_interaction_id",pendingId).put("interaction_submission",false)
                .put("observed_notification_cleared",false).put("planning_projection_only",true)
                .put("observed_snapshot_unchanged",true);
        return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(ordinary.policy(),ordinary.phase(),ordinary.reason(),ordinary.kind(),
                ordinary.command(),ordinary.purpose(),ordinary.domain(),InteractionArguments.app(output)),
                "defer the exact blocked marriage reply while the actual ordinary core continues");
    }
    static boolean blockedMarriage(OrdinaryPolicy.Draft draft) {
        if(draft.command().isPresent()||!draft.phase().equals("pending_character_interaction_degraded_blocked"))return false;
        ObjectNode detail=InteractionArguments.parseApp(draft.detail());
        JsonNode decision=detail.get("decision");
        if(decision==null||!decision.isObject())return false;
        String classification=KnownPendingInteractionEvidence.nullableString(decision.get("classification"));
        boolean known="known_marriage_special".equals(classification);
        boolean invalid="evidence_invalid".equals(classification)
                &&KnownPendingInteractionEvidence.equalText(decision.get("interaction_key"),"arrange_marriage_interaction")
                &&decision.has("marriage_contract_gaps")&&decision.get("marriage_contract_gaps").isArray()
                &&!decision.get("marriage_contract_gaps").isEmpty();
        return (known||invalid)&&KnownPendingInteractionEvidence.equalText(
                decision.path("definition_classification").get("definition_key"),"arrange_marriage_interaction");
    }
    private static boolean present(JsonNode value) { return value!=null&&!value.isNull(); }
}
