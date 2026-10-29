package org.xar.ck3.control.wave3.planning.peacetimescope;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Frame;

/** Observed peaceful-frame closure. This grants no action, recovery, SDK or Game qualification. */
public final class PeacetimeScope {
    private PeacetimeScope() { }
    public enum Flag { TRUE, FALSE, MISSING, NULL }
    public enum Presence { MISSING, NULL, PRESENT }
    public enum CollectionState { MISSING, NULL, EMPTY, NONEMPTY }
    public enum Failure {
        planning_revision_unavailable,
        peaceful_paused_actor_frame_required,
        observed_player_gold_unavailable,
        internal_snapshot_reader_unavailable,
        internal_snapshot_malformed,
        crossed_paused_frame,
        player_gold_changed
    }
    public record Actor(BigInteger characterId, Flag alive) {
        public Actor { positive(characterId); Objects.requireNonNull(alive); }
    }
    public record Gold(BigInteger raw, BigInteger scale) {
        public Gold { Objects.requireNonNull(raw); Objects.requireNonNull(scale); }
    }
    /** Presence and empty collections are original observation facts, never caller-supplied eligibility. */
    public record Scene(Frame frame, Flag paused, Flag mapReady, Actor playedCharacter,
                        Presence activeEvent, Presence pendingInteraction, Presence terminalReason,
                        CollectionState activeWars, CollectionState playerArmies, Gold gold) {
        public Scene {
            Objects.requireNonNull(frame); Objects.requireNonNull(paused); Objects.requireNonNull(mapReady);
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingInteraction); Objects.requireNonNull(terminalReason);
            Objects.requireNonNull(activeWars); Objects.requireNonNull(playerArmies);
        }
    }
    public record StableObservation(Frame frame, BigInteger observedGoldRaw) {
        public StableObservation { Objects.requireNonNull(frame); nonnegative(observedGoldRaw); }
        public boolean formalActionReady() { return false; }
    }
    public sealed interface Readback permits Observed, ReaderUnavailable, MalformedSnapshot { }
    public record Observed(Scene scene) implements Readback { public Observed { Objects.requireNonNull(scene); } }
    public enum ReaderUnavailable implements Readback { INSTANCE }
    public enum MalformedSnapshot implements Readback { INSTANCE }
    /** Application implements the existing reader; this package opens no transport or process. */
    @FunctionalInterface public interface SemanticSnapshotReader { Readback capture(); }
    public static final class Unavailable extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        private final Failure failure;
        public Unavailable(Failure failure) { super(message(failure)); this.failure = Objects.requireNonNull(failure); }
        public Failure failure() { return failure; }
    }

    public static StableObservation requirePeacefulFrame(Scene scene, BigInteger expectedRevision) {
        if (expectedRevision == null || expectedRevision.signum() <= 0) { throw new Unavailable(Failure.planning_revision_unavailable); }
        Objects.requireNonNull(scene);
        Frame frame = scene.frame;
        if (scene.paused != Flag.TRUE || scene.mapReady != Flag.TRUE || scene.playedCharacter == null
                || scene.playedCharacter.alive != Flag.TRUE || !scene.playedCharacter.characterId.equals(frame.player())
                || scene.activeEvent == Presence.PRESENT || scene.pendingInteraction == Presence.PRESENT
                || scene.terminalReason == Presence.PRESENT || scene.activeWars != CollectionState.EMPTY
                || scene.playerArmies != CollectionState.EMPTY || !frame.revision().equals(expectedRevision)
                || !frame.snapshotId().equals("native:" + frame.nativeRevision())) {
            throw new Unavailable(Failure.peaceful_paused_actor_frame_required);
        }
        return new StableObservation(frame, snapshotGold(scene));
    }

    public static BigInteger snapshotGold(Scene scene) {
        Objects.requireNonNull(scene);
        Gold gold = scene.gold;
        if (gold == null || gold.raw.signum() < 0 || !gold.scale.equals(BigInteger.valueOf(100000))) {
            throw new Unavailable(Failure.observed_player_gold_unavailable);
        }
        return gold.raw;
    }

    /** One returned readback must bind all six frame fields and the independently observed wallet. */
    public static StableObservation requireDriverFrame(StableObservation expected, Readback readback) {
        Objects.requireNonNull(expected); Objects.requireNonNull(readback);
        if (readback == ReaderUnavailable.INSTANCE) { throw new Unavailable(Failure.internal_snapshot_reader_unavailable); }
        if (readback == MalformedSnapshot.INSTANCE) { throw new Unavailable(Failure.internal_snapshot_malformed); }
        Scene current = ((Observed) readback).scene;
        StableObservation observed = requirePeacefulFrame(current, expected.frame.revision());
        if (!observed.frame.equals(expected.frame)) { throw new Unavailable(Failure.crossed_paused_frame); }
        if (!observed.observedGoldRaw.equals(expected.observedGoldRaw)) { throw new Unavailable(Failure.player_gold_changed); }
        return observed;
    }

    public static StableObservation verify(Scene before, BigInteger expectedRevision, Readback readback) {
        return requireDriverFrame(requirePeacefulFrame(before, expectedRevision), readback);
    }

    /** Initial failure prevents reader invocation; a valid initial frame invokes the provided reader exactly once. */
    public static StableObservation verifyFromReader(Scene before, BigInteger expectedRevision,
                                                      Optional<SemanticSnapshotReader> reader) {
        StableObservation expected = requirePeacefulFrame(before, expectedRevision);
        Objects.requireNonNull(reader);
        Readback readback = reader.isEmpty() ? ReaderUnavailable.INSTANCE : reader.orElseThrow().capture();
        return requireDriverFrame(expected, readback == null ? MalformedSnapshot.INSTANCE : readback);
    }

    public static String message(Failure failure) {
        return switch (Objects.requireNonNull(failure)) {
            case planning_revision_unavailable -> "M5 peacetime source lacks the planning revision";
            case peaceful_paused_actor_frame_required -> "M5 peacetime source requires one stable peaceful paused actor frame";
            case observed_player_gold_unavailable -> "M5 peacetime source lacks observed player gold";
            case internal_snapshot_reader_unavailable -> "M5 peacetime source lacks an internal semantic snapshot reader";
            case internal_snapshot_malformed -> "M5 peacetime source internal snapshot is malformed";
            case crossed_paused_frame -> "M5 peacetime source crossed its paused frame";
            case player_gold_changed -> "M5 peacetime source player gold changed during readback";
        };
    }
    private static void positive(BigInteger value) { if (value == null || value.signum() <= 0) { throw new IllegalArgumentException("positive integer identity required"); } }
    private static void nonnegative(BigInteger value) { if (value == null || value.signum() < 0) { throw new IllegalArgumentException("nonnegative integer required"); } }
}
