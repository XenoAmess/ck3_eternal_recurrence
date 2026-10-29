package org.xar.ck3.control.events.interactionfallback;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Immutable, side-effect-free inputs and proposals. No object grants dispatch authority. */
public final class InteractionFallback {
    public static final String REQUEST_SCHEMA = "xar.pending-interaction-left-candidate-request/v1";
    public static final String RESULT_SCHEMA = "xar.pending-interaction-left-candidate-result/v1";
    public static final String GUI_SOURCE = "gui/interaction_notification_window.gui";
    public static final String GUI_SHA256 = "a3c946a98346de2f57c5c3408a24bf298329df24a6ab25ec88d893befa1fe6e0";
    public static final String UNKNOWN_REASON = "Capture this unfamiliar native request, then choose the source-proved GUI left reply through MCP under the owner's continuation policy.";
    public static final String UNAVAILABLE_REASON = "The selected native reply is unavailable; preserve the actual choice list and mechanism diagnosis.";
    public static final String KNOWN_REASON = "Owner chooses the source-authored left decline. Acceptance starts a five-year chastity vow path; decline has authored piety/stress/opinion penalties, whose material application is not inferred from reply ACK.";

    private InteractionFallback() { }

    public enum Status { AVAILABLE, UNAVAILABLE, INVALID }
    public enum Presence { MISSING, NULL, VALUE }
    public enum Action {
        ACCEPT("accept", "accept-pending-character-interaction"),
        REJECT("reject", "reject-pending-character-interaction"),
        BLOCK("block", "block-pending-character-interaction"),
        ACKNOWLEDGE("acknowledge", "acknowledge-pending-character-interaction");
        private final String wire;
        private final String step;
        Action(String wire, String step) { this.wire = wire; this.step = step; }
        public String wire() { return wire; }
        public String step() { return step; }
    }
    public enum Disposition { CANDIDATE, DEDICATED_PLAN_RETAINED, NOT_APPLICABLE, STALE_CONTEXT }
    public enum Phase {
        REVIEWED("pending_character_interaction_reviewed_left_reply"),
        FALLBACK("pending_character_interaction_left_fallback"),
        DISABLED("pending_character_interaction_left_disabled"),
        UNSUPPORTED("pending_character_interaction_left_unsupported");
        private final String wire;
        Phase(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Binding(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, String episodeRunId, boolean paused, boolean mapReady,
            int actorCharacterId, BigInteger connectionGeneration, long bridgePid) {
        public Binding {
            stable(snapshotId); stable(episodeRunId); uint64(revision); uint64(nativeRevision);
            uint64(dateRaw); uint64(connectionGeneration);
            NativeCharacterId.of(actorCharacterId);
            StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL,
                    "uint32 process identity required");
        }
    }
    public record Pending(int instanceId, int senderCharacterId, Boolean autoAcceptNotification) {
        public Pending { pendingId(instanceId); NativeCharacterId.of(senderCharacterId); }
    }
    public record Definition(String canonicalKey, long deterministicKeyHash) {
        public Definition {
            stable(canonicalKey);
            StrictJson.require(deterministicKeyHash >= 0 && deterministicKeyHash <= 0xffff_ffffL, "uint32 definition hash required");
        }
    }
    /** MISSING, explicit null and a present legality object remain distinguishable. */
    public record Legality(Presence presence, Status status, Boolean allowed, String reason) {
        public Legality {
            Objects.requireNonNull(presence);
            StrictJson.require(presence == Presence.VALUE ? status != null : status == null && allowed == null && reason == null,
                    "legality presence and value disagree");
            if (reason != null) { stable(reason); }
        }
        public boolean enabled() { return presence == Presence.VALUE && status == Status.AVAILABLE && Boolean.TRUE.equals(allowed); }
    }
    public record ReplyLegality(Legality accept, Legality reject, Legality block, Legality acknowledge) {
        public ReplyLegality { Objects.requireNonNull(accept); Objects.requireNonNull(reject); Objects.requireNonNull(block); Objects.requireNonNull(acknowledge); }
        public Legality forAction(Action action) {
            return switch (action) { case ACCEPT -> accept; case REJECT -> reject; case BLOCK -> block; case ACKNOWLEDGE -> acknowledge; };
        }
    }
    public record Context(Status status, BigInteger snapshotRevision, BigInteger dateRaw,
            int pendingInteractionId, Definition definition, ReplyLegality legality) {
        public Context { Objects.requireNonNull(status); uint64(snapshotRevision); uint64(dateRaw); pendingId(pendingInteractionId); Objects.requireNonNull(definition); Objects.requireNonNull(legality); }
    }
    public record OriginalPlan(String phase, String selectedStep, boolean blockedMarriageReply,
            boolean existingInteractionFallback) {
        public OriginalPlan { stable(phase); if (selectedStep != null) { stable(selectedStep); } }
    }
    public record Request(Binding binding, Pending pending, Context context,
            OriginalPlan originalPlan, Set<String> actionSteps) {
        public Request {
            Objects.requireNonNull(binding); Objects.requireNonNull(pending); Objects.requireNonNull(context); Objects.requireNonNull(originalPlan);
            actionSteps = Set.copyOf(actionSteps);
            StrictJson.require(actionSteps.size() <= 512, "bounded action set required");
            actionSteps.forEach(InteractionFallback::stable);
        }
    }
    public record Selection(Action action, String position, int renderedIndex, String button,
            boolean nativeLegal, boolean actionReachable) {
        public Selection {
            Objects.requireNonNull(action); stable(position); stable(button);
            StrictJson.require(renderedIndex == 0, "fallback selects only the authored first position");
            StrictJson.require(action == Action.REJECT && position.equals("left") && button.equals("reject_button")
                    || action == Action.ACKNOWLEDGE && position.equals("only") && button.equals("acknowledge_button"),
                    "fallback must not substitute right accept");
        }
        public boolean proposed() { return nativeLegal && actionReachable; }
    }
    public record ReviewedRule(String classification, String preferredAction, long deterministicKeyHash,
            String source, String sourceSha256, String sourceLines, String reason) {
        public ReviewedRule {
            stable(classification); stable(source); stable(sourceLines); stable(reason);
            StrictJson.require(preferredAction.equals("reject") && deterministicKeyHash == 1_409_884_230L,
                    "only compiled reviewed rule is implemented");
            StrictJson.require(sourceSha256.matches("[0-9a-f]{64}"), "source SHA-256 required");
        }
    }
    public record ReplyOption(Action action, String position, int renderedIndex, String button,
            String onclick, String enabled, Legality nativeLegality) {
        public ReplyOption { Objects.requireNonNull(action); stable(position); stable(button); stable(onclick); stable(enabled); Objects.requireNonNull(nativeLegality); }
    }
    public record Candidate(Phase phase, String selectedStep, String reason, Pending pending,
            Binding binding, Definition definition, Selection selection, List<ReplyOption> replyOptions,
            ReviewedRule reviewedRule) {
        public Candidate {
            Objects.requireNonNull(phase); stable(reason); Objects.requireNonNull(pending); Objects.requireNonNull(binding);
            Objects.requireNonNull(definition); Objects.requireNonNull(selection); replyOptions = List.copyOf(replyOptions);
            StrictJson.require(replyOptions.size() == 2 && replyOptions.get(0).action() == Action.REJECT
                    && replyOptions.get(1).action() == Action.ACCEPT, "source GUI order is reject, accept");
            StrictJson.require(Objects.equals(selectedStep, selection.proposed() ? selection.action().step() : null), "proposed step and legality disagree");
            Phase expected = !selection.nativeLegal() ? Phase.DISABLED : !selection.actionReachable() ? Phase.UNSUPPORTED
                    : reviewedRule == null ? Phase.FALLBACK : Phase.REVIEWED;
            StrictJson.require(phase == expected, "phase must reflect native legality and reachability");
        }
        public boolean registryKnown() { return reviewedRule != null; }
        public String classification() { return registryKnown() ? reviewedRule.classification() : "uncovered_pending_character_interaction"; }
        public boolean offlineFollowupRequired() { return !registryKnown(); }
    }
    public record Result(Disposition disposition, Candidate candidate) {
        public Result { Objects.requireNonNull(disposition); StrictJson.require((disposition == Disposition.CANDIDATE) == (candidate != null), "result disposition disagrees with candidate"); }
    }

    static void stable(String value) {
        StrictJson.text(value);
        StrictJson.require(value.length() <= 1024 && value.chars().noneMatch(c -> c < 0x20), "bounded stable text required");
    }
    static void uint64(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 numeric identity required");
    }
    static void pendingId(int value) { StrictJson.require(value != -1, "pending ID cannot use the -1 invalid sentinel"); }
}
