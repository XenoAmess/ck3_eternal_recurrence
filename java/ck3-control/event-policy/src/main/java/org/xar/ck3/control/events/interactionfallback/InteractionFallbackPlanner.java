package org.xar.ck3.control.events.interactionfallback;

import java.util.List;
import static org.xar.ck3.control.events.interactionfallback.InteractionFallback.*;

/** Produces a candidate only. It neither submits nor acknowledges any native action. */
public final class InteractionFallbackPlanner {
    private static final ReviewedRule CLERICAL_CHASTITY = new ReviewedRule(
            "reviewed_religious_clerical_chastity_request", "reject", 1_409_884_230L,
            "common/character_interactions/clerical_chastity_interaction.txt",
            "9a7470b42d2f9bfed8a71932014a4c2f8d6fdcc24277f99f79238c5703010b8a",
            "1-14; on_accept132-221; on_decline223-262", KNOWN_REASON);

    private InteractionFallbackPlanner() { }

    public static Result plan(Request input) {
        java.util.Objects.requireNonNull(input);
        OriginalPlan original = input.originalPlan();
        if (original.blockedMarriageReply() || original.selectedStep() != null || original.existingInteractionFallback()) {
            return new Result(Disposition.DEDICATED_PLAN_RETAINED, null);
        }
        if (!original.phase().startsWith("pending_") || input.pending().autoAcceptNotification() == null) {
            return new Result(Disposition.NOT_APPLICABLE, null);
        }
        Context context = input.context();
        Binding binding = input.binding();
        if (context.status() != Status.AVAILABLE || context.pendingInteractionId() != input.pending().instanceId()
                || !context.snapshotRevision().equals(binding.nativeRevision()) || !context.dateRaw().equals(binding.dateRaw())) {
            return new Result(Disposition.STALE_CONTEXT, null);
        }
        ReviewedRule known = context.definition().canonicalKey().equals("request_clerical_chastity_interaction")
                && context.definition().deterministicKeyHash() == CLERICAL_CHASTITY.deterministicKeyHash() ? CLERICAL_CHASTITY : null;
        boolean notification = input.pending().autoAcceptNotification();
        Action action = notification ? Action.ACKNOWLEDGE : Action.REJECT;
        boolean legal = context.legality().forAction(action).enabled();
        boolean reachable = input.actionSteps().contains(action.step());
        Selection selected = new Selection(action, notification ? "only" : "left", 0,
                notification ? "acknowledge_button" : "reject_button", legal, reachable);
        Phase phase = !legal ? Phase.DISABLED : !reachable ? Phase.UNSUPPORTED : known == null ? Phase.FALLBACK : Phase.REVIEWED;
        List<ReplyOption> options = List.of(
                new ReplyOption(Action.REJECT, "left", 0, "reject_button", "CharacterInteractionNotificationWindow.Reject",
                        "CharacterInteractionNotificationWindow.CanReject", context.legality().reject()),
                new ReplyOption(Action.ACCEPT, "right", 1, "accept_button", "CharacterInteractionNotificationWindow.Accept",
                        "CharacterInteractionNotificationWindow.CanAccept", context.legality().accept()));
        return new Result(Disposition.CANDIDATE, new Candidate(phase, selected.proposed() ? action.step() : null,
                selected.proposed() ? known == null ? UNKNOWN_REASON : known.reason() : UNAVAILABLE_REASON,
                input.pending(), binding, context.definition(), selected, options, known));
    }
}
