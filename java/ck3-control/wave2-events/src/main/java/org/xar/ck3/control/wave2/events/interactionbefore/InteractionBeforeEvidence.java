package org.xar.ck3.control.wave2.events.interactionbefore;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Pure before-evidence proposal; the unique evidence owner must still persist it before dispatch. */
public final class InteractionBeforeEvidence {
    private InteractionBeforeEvidence() { }
    public enum Action {
        REJECT("reject", "left"), ACKNOWLEDGE("acknowledge", "only");
        private final String wire;
        private final String position;
        Action(String wire, String position) { this.wire = wire; this.position = position; }
        public String wire() { return wire; }
        public String position() { return position; }
        public String step() { return wire + "-pending-character-interaction"; }
    }
    public record GuiSourcePin(String source, String sha256) {
        public GuiSourcePin { stable(source); sha(sha256); }
    }
    public record Identity(String incidentId, String capturedAtUtc, String machineId) {
        public Identity {
            StrictJson.require(incidentId != null && incidentId.matches("[0-9a-f]{32}"), "canonical original incident UUID required");
            StrictJson.utc(capturedAtUtc); stable(machineId);
        }
    }
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            String episodeRunId, boolean paused, boolean mapReady, int actorCharacterId, BigInteger connectionGeneration, long bridgePid) {
        public Frame {
            stable(snapshotId); stable(episodeRunId); unsigned(revision); unsigned(nativeRevision); unsigned(dateRaw); unsigned(connectionGeneration);
            NativeCharacterId.of(actorCharacterId);
            StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL, "uint32 bridge PID required");
        }
    }
    public sealed interface Result permits NotApplicable, Prepared { }
    public record NotApplicable() implements Result { }
    public static final class Prepared implements Result {
        private final byte[] json;
        private final Identity identity;
        private final Frame frame;
        private final int pendingInteractionId;
        private final Action action;
        private final Optional<String> selectedStep;
        private final String plannedSourceSha256;
        Prepared(byte[] json, Identity identity, Frame frame, int pendingInteractionId, Action action, Optional<String> selectedStep, String plannedSourceSha256) {
            this.json = json.clone(); this.identity = Objects.requireNonNull(identity); this.frame = Objects.requireNonNull(frame);
            StrictJson.require(pendingInteractionId != -1, "pending ID cannot use -1 sentinel"); this.pendingInteractionId = pendingInteractionId;
            this.action = Objects.requireNonNull(action); this.selectedStep = Objects.requireNonNull(selectedStep);
            selectedStep.ifPresent(value -> StrictJson.require(value.equals(action.step()), "selected original step must match proposed action"));
            sha(plannedSourceSha256); this.plannedSourceSha256 = plannedSourceSha256;
        }
        public byte[] json() { return json.clone(); }
        public Identity identity() { return identity; }
        public Frame frame() { return frame; }
        public int pendingInteractionId() { return pendingInteractionId; }
        public Action action() { return action; }
        public Optional<String> selectedStep() { return selectedStep; }
        public String plannedSourceSha256() { return plannedSourceSha256; }
        public boolean dispatchAttempted() { return false; }
        public boolean durableBeforeWritten() { return false; }
        public boolean replayAllowed() { return false; }
    }
    static void stable(String value) { StrictJson.text(value); StrictJson.require(value.length() <= 4096 && value.chars().noneMatch(c -> c < 0x20), "bounded stable evidence field required"); }
    static void sha(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "canonical SHA-256 required"); }
    static void unsigned(BigInteger value) { StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "exact uint64 frame integer required"); }
}
