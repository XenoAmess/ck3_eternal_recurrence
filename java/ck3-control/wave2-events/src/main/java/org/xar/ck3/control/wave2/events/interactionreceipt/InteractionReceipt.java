package org.xar.ck3.control.wave2.events.interactionreceipt;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-response assessment only; it never submits, retries or infers authored material effects. */
public final class InteractionReceipt {
    private InteractionReceipt() { }
    public enum OutcomeStatus { ACCEPTED, REJECTED, ACKNOWLEDGED }
    public enum Action {
        ACCEPT("accept", OutcomeStatus.ACCEPTED), REJECT("reject", OutcomeStatus.REJECTED), ACKNOWLEDGE("acknowledge", OutcomeStatus.ACKNOWLEDGED);
        private final String wire;
        private final OutcomeStatus status;
        Action(String wire, OutcomeStatus status) { this.wire = wire; this.status = status; }
        public String wire() { return wire; }
        public OutcomeStatus expectedStatus() { return status; }
        public String step() { return wire + "-pending-character-interaction"; }
    }
    public enum Origin { EXECUTE_STEP, REPLY_API, ACKNOWLEDGE_API }
    public enum Presence { MISSING, NULL, VALUE }
    public enum Ack { ACKNOWLEDGED, NOT_ACKNOWLEDGED, NOT_REPORTED_AS_ACK }
    public enum Gap { NO_RESPONSE, STEP_MISMATCH, ACK_NOT_TRUE, MISSING_INTERACTION, ORIGINAL_ID_MISMATCH,
        STATUS_MISMATCH, REMAINING_MISSING, ORIGINAL_STILL_PENDING, NOT_PAUSED, INTENT_MISMATCH, WRAPPER_ID_MISMATCH, WRAPPER_ACK_MISMATCH, ERROR_PRESENT }

    public record Expected(int pendingInteractionId, Action action) {
        public Expected { id(pendingInteractionId); Objects.requireNonNull(action); }
    }
    public record BooleanField(Presence presence, Boolean value) {
        public BooleanField { Objects.requireNonNull(presence); StrictJson.require((presence == Presence.VALUE) == (value != null), "boolean presence mismatch"); }
        public boolean isTrue() { return presence == Presence.VALUE && Boolean.TRUE.equals(value); }
    }
    public record Outcome(Presence presence, Integer instanceId, OutcomeStatus status) {
        public Outcome {
            Objects.requireNonNull(presence);
            StrictJson.require(presence == Presence.VALUE ? instanceId != null && status != null : instanceId == null && status == null, "outcome presence mismatch");
            if (instanceId != null) { id(instanceId); }
        }
    }
    public record Remaining(Presence presence, Integer instanceId) {
        public Remaining { Objects.requireNonNull(presence); StrictJson.require((presence == Presence.VALUE) == (instanceId != null), "remaining presence mismatch"); if (instanceId != null) { id(instanceId); } }
    }
    public record ErrorInfo(String type, String message) {
        public ErrorInfo { stable(type); Objects.requireNonNull(message); StrictJson.require(message.length() <= 8192, "bounded original error required"); }
    }
    public record Response(Presence presence, String step, BooleanField accepted, BooleanField paused,
            Outcome outcome, Remaining remaining, Integer wrapperInstanceId, BooleanField wrapperAcknowledged, String originalSha256) {
        public Response {
            Objects.requireNonNull(presence); Objects.requireNonNull(accepted); Objects.requireNonNull(paused); Objects.requireNonNull(outcome); Objects.requireNonNull(remaining); Objects.requireNonNull(wrapperAcknowledged);
            if (step != null) { stable(step); } if (wrapperInstanceId != null) { id(wrapperInstanceId); }
            StrictJson.require(originalSha256 != null && originalSha256.matches("[0-9a-f]{64}"), "actual original response digest required");
            StrictJson.require(presence == Presence.VALUE || step == null && accepted.presence() == Presence.MISSING
                    && paused.presence() == Presence.MISSING && outcome.presence() == Presence.MISSING && remaining.presence() == Presence.MISSING
                    && wrapperInstanceId == null && wrapperAcknowledged.presence() == Presence.MISSING, "absent response cannot carry present fields");
        }
    }
    public record Assessment(Origin origin, Ack commandAcknowledged, Boolean replyAcceptArgument,
            boolean originalPendingAdvancedInResponse, boolean legacyCaptureWouldMarkAdvanced,
            List<Gap> gaps, ErrorInfo error, String originalSha256) {
        public Assessment {
            Objects.requireNonNull(origin); Objects.requireNonNull(commandAcknowledged); gaps = List.copyOf(gaps);
            StrictJson.require(gaps.size() <= Gap.values().length && originalSha256 != null && originalSha256.matches("[0-9a-f]{64}"), "bounded source-pinned assessment required");
        }
        public boolean replayAllowed() { return false; }
        public boolean materialEffectsVerified() { return false; }
    }

    public static Assessment assess(Expected expected, Origin origin, Response response, ErrorInfo error) {
        Objects.requireNonNull(expected); Objects.requireNonNull(origin); Objects.requireNonNull(response);
        StrictJson.require(origin != Origin.REPLY_API || expected.action() != Action.ACKNOWLEDGE, "reply API cannot encode acknowledgement");
        StrictJson.require(origin != Origin.ACKNOWLEDGE_API || expected.action() == Action.ACKNOWLEDGE, "acknowledge API cannot encode acceptance/rejection");
        List<Gap> gaps = new ArrayList<>();
        boolean normal = response.presence() == Presence.VALUE;
        if (!normal) { gaps.add(Gap.NO_RESPONSE); }
        boolean sourceStep = Objects.equals(expected.action().step(), response.step()); if (!sourceStep) { gaps.add(Gap.STEP_MISMATCH); }
        Ack acknowledged = origin == Origin.REPLY_API ? Ack.NOT_REPORTED_AS_ACK
                : response.accepted().isTrue() ? Ack.ACKNOWLEDGED : Ack.NOT_ACKNOWLEDGED;
        if (acknowledged == Ack.NOT_ACKNOWLEDGED) { gaps.add(Gap.ACK_NOT_TRUE); }
        boolean original = response.outcome().presence() == Presence.VALUE && response.outcome().instanceId() == expected.pendingInteractionId();
        if (response.outcome().presence() != Presence.VALUE) { gaps.add(Gap.MISSING_INTERACTION); }
        else if (!original) { gaps.add(Gap.ORIGINAL_ID_MISMATCH); }
        boolean status = Objects.equals(response.outcome().status(), expected.action().expectedStatus()); if (!status) { gaps.add(Gap.STATUS_MISMATCH); }
        boolean hasRemaining = response.remaining().presence() != Presence.MISSING;
        if (!hasRemaining) { gaps.add(Gap.REMAINING_MISSING); }
        boolean advanced = response.remaining().presence() == Presence.NULL || response.remaining().presence() == Presence.VALUE
                && response.remaining().instanceId() != expected.pendingInteractionId();
        if (hasRemaining && !advanced) { gaps.add(Gap.ORIGINAL_STILL_PENDING); }
        boolean paused = response.paused().isTrue(); if (!paused) { gaps.add(Gap.NOT_PAUSED); }
        boolean commonPostcondition = normal && original && status && hasRemaining && advanced && paused;
        // The legacy capture did not distinguish service.reply's business accepted parameter from execute_step's ACK.
        boolean legacy = response.accepted().isTrue() && commonPostcondition;
        Boolean intent = origin == Origin.REPLY_API && response.accepted().presence() == Presence.VALUE ? response.accepted().value() : null;
        boolean acceptedIntent = origin != Origin.REPLY_API || response.accepted().presence() == Presence.VALUE
                && response.accepted().value() == (expected.action() == Action.ACCEPT);
        if (!acceptedIntent) { gaps.add(Gap.INTENT_MISMATCH); }
        boolean wrapper = origin == Origin.EXECUTE_STEP || response.wrapperInstanceId() != null
                && response.wrapperInstanceId() == expected.pendingInteractionId();
        if (!wrapper) { gaps.add(Gap.WRAPPER_ID_MISMATCH); }
        boolean wrapperAck = origin != Origin.ACKNOWLEDGE_API || response.wrapperAcknowledged().isTrue();
        if (!wrapperAck) { gaps.add(Gap.WRAPPER_ACK_MISMATCH); }
        boolean dispatchShape = origin == Origin.REPLY_API ? acceptedIntent && wrapper : acknowledged == Ack.ACKNOWLEDGED && wrapper && wrapperAck;
        if (error != null) { gaps.add(Gap.ERROR_PRESENT); }
        return new Assessment(origin, acknowledged, intent, commonPostcondition && sourceStep && dispatchShape, legacy, gaps, error, response.originalSha256());
    }

    static void id(int value) { StrictJson.require(value != -1, "pending ID cannot use invalid -1 sentinel"); }
    static void stable(String value) { StrictJson.text(value); StrictJson.require(value.length() <= 1024 && value.chars().noneMatch(c -> c < 0x20), "bounded stable receipt token required"); }
}
