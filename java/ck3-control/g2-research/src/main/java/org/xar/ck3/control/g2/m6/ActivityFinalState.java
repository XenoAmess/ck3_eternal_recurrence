package org.xar.ck3.control.g2.m6;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/**
 * The unique pure reducer for independent retained Activity final flags.
 * Root supplies a strictly decoded hosted read and its actual archived receipt.
 * This reducer grants neither original Start credit nor an action permission.
 * A missing instance, a counter and an opaque stamp cannot establish a final
 * state; named material and terminal cause remain independently unobserved.
 * Native +408 is also written by active phase scheduling; a changed or
 * unchanged rawCompletionStamp never substitutes for either independent flag.
 */
public final class ActivityFinalState {
    private ActivityFinalState() {}

    public record Identity(String originalActionId, long activityFullId, long hostCharacterId, String typeKey) {
        public Identity {
            StrictJson.text(originalActionId);
            StrictJson.require(originalActionId.length() <= 128, "bounded original Activity action identity required");
            StrictJson.require(activityFullId >= 0 && activityFullId <= 0xFFFF_FFFEL,
                    "complete Activity uint32 ID required, sentinel excluded");
            StrictJson.require(hostCharacterId >= 1 && hostCharacterId <= 0xFFFF_FFFEL,
                    "complete positive host ID required");
            StrictJson.require("activity_feast".equals(typeKey), "only the actual source-qualified Feast path is admitted");
        }
        public int generation() { return (int) (activityFullId >>> 24); }
    }

    /** Exact source locators, never an invented cross-machine observation. */
    public record Provenance(ExactRef originalRead, ExactRef producerSource, ExactRef helloSource) {
        public Provenance {
            for (ExactRef source : java.util.List.of(originalRead, producerSource, helloSource)) {
                StrictJson.require(source.bytes() > 0, "retained original read and source bytes required");
            }
        }
    }

    public sealed interface Instance permits Missing, FlagsUnavailable, Flags, RetainedFlags {}
    public record Missing() implements Instance {}
    public record FlagsUnavailable(Optional<BigInteger> rawCompletionStamp) implements Instance {
        public FlagsUnavailable { stamp(rawCompletionStamp); }
    }
    /** The two flags stay independent, including native observations where both are true. */
    public record Flags(boolean completed, boolean invalidated,
            Optional<BigInteger> rawCompletionStamp) implements Instance {
        public Flags { stamp(rawCompletionStamp); }
        public boolean finalObserved() { return completed || invalidated; }
    }
    /** Historical pre-call cut, not a manager-reachable object or a new query-time terminal. */
    public record RetainedFlags(Optional<Integer> completedRaw, Optional<Integer> invalidatedRaw,
            Optional<BigInteger> rawCompletionStamp, BigInteger captureSequence,
            BigInteger capturedDateRaw) implements Instance {
        public RetainedFlags {
            Objects.requireNonNull(completedRaw); Objects.requireNonNull(invalidatedRaw);
            for (Optional<Integer> raw : java.util.List.of(completedRaw, invalidatedRaw))
                raw.ifPresent(value -> StrictJson.require(value >= 0 && value <= 255, "native terminal byte required"));
            stamp(rawCompletionStamp); Objects.requireNonNull(captureSequence); Objects.requireNonNull(capturedDateRaw);
            StrictJson.require(captureSequence.signum() > 0 && captureSequence.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "positive exact terminal capture sequence required");
            StrictJson.require(capturedDateRaw.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0
                    && capturedDateRaw.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "signed64 original capture date required");
            StrictJson.require(completedRaw.filter(value -> value != 0).isPresent()
                    || invalidatedRaw.filter(value -> value != 0).isPresent(), "retained source requires an observed nonzero terminal byte");
        }
    }
    public enum Kind { UNKNOWN, ACTIVE, FINAL_UNATTRIBUTED }

    public record Sample(Identity identity, ObservationIdentity queried, Instance instance, Provenance provenance) {
        public Sample {
            Objects.requireNonNull(identity); Objects.requireNonNull(queried);
            Objects.requireNonNull(instance); Objects.requireNonNull(provenance);
            host(identity, queried);
        }
        public Kind kind() {
            if (instance instanceof RetainedFlags) return Kind.FINAL_UNATTRIBUTED;
            return instance instanceof Flags flags
                    ? flags.finalObserved() ? Kind.FINAL_UNATTRIBUTED : Kind.ACTIVE : Kind.UNKNOWN;
        }
        public boolean terminalCauseObserved() { return false; }
        public boolean benefitObserved() { return false; }
        public boolean actionAuthorized() { return false; }
    }

    public static final class State {
        private final Identity identity;
        private final ObservationIdentity origin;
        private final Optional<Sample> latest;
        private final Optional<Sample> firstFinal;
        private State(Identity identity, ObservationIdentity origin,
                Optional<Sample> latest, Optional<Sample> firstFinal) {
            this.identity = identity; this.origin = origin;
            this.latest = latest; this.firstFinal = firstFinal;
        }
        public Identity identity() { return identity; }
        public ObservationIdentity origin() { return origin; }
        public Optional<Sample> latest() { return latest; }
        public Optional<Sample> firstFinal() { return firstFinal; }
        public Kind currentKind() { return latest.map(Sample::kind).orElse(Kind.UNKNOWN); }
        public boolean observedFinalAt(ObservationIdentity current) {
            Objects.requireNonNull(current);
            return latest.filter(sample -> sample.queried().equals(current)
                    && sample.instance() instanceof Flags
                    && sample.kind() == Kind.FINAL_UNATTRIBUTED).isPresent();
        }
    }

    public static State empty(Identity identity, ObservationIdentity origin) {
        Objects.requireNonNull(identity); Objects.requireNonNull(origin); host(identity, origin);
        return new State(identity, origin, Optional.empty(), Optional.empty());
    }

    /** Root must have validated the actual complete source/receipt before this pure operation. */
    public static State observe(State state, Sample sample) {
        Objects.requireNonNull(state); Objects.requireNonNull(sample);
        StrictJson.require(state.identity().equals(sample.identity()), "Activity read crossed the original complete instance");
        sameScope(state.origin(), sample.queried());
        notEarlier(state.origin(), sample.queried());
        if (sample.instance() instanceof RetainedFlags retained)
            StrictJson.require(retained.capturedDateRaw().compareTo(state.origin().frame().identity().dateRaw()) >= 0
                    && retained.capturedDateRaw().compareTo(sample.queried().frame().identity().dateRaw()) <= 0,
                    "retained terminal cut crossed the original Start/query date window");
        state.latest().ifPresent(old -> notEarlier(old.queried(), sample.queried()));
        Optional<Sample> first = state.firstFinal();
        if (first.isEmpty() && sample.kind() == Kind.FINAL_UNATTRIBUTED) first = Optional.of(sample);
        return new State(state.identity(), state.origin(), Optional.of(sample), first);
    }

    static void sameScope(ObservationIdentity origin, ObservationIdentity queried) {
        StrictJson.require(origin.machineId().equals(queried.machineId()) && origin.game().equals(queried.game())
                && origin.frame().episodeRunId().equals(queried.frame().episodeRunId())
                && origin.frame().identity().player().equals(queried.frame().identity().player())
                && origin.observationVersion() == queried.observationVersion(),
                "Activity final read crossed machine, Game birth, episode, player or observation version");
    }
    private static void notEarlier(ObservationIdentity origin, ObservationIdentity queried) {
        StrictJson.require(queried.frame().revision().compareTo(origin.frame().revision()) >= 0
                && queried.frame().identity().nativeRevision().compareTo(origin.frame().identity().nativeRevision()) >= 0
                && queried.frame().identity().dateRaw().compareTo(origin.frame().identity().dateRaw()) >= 0,
                "Activity source cannot move backwards in the original native/semantic frame or date");
    }
    private static void host(Identity identity, ObservationIdentity queried) {
        StrictJson.require(BigInteger.valueOf(identity.hostCharacterId()).equals(queried.frame().identity().player()),
                "Activity host is not the actual bound player");
    }
    private static void stamp(Optional<BigInteger> stamp) {
        Objects.requireNonNull(stamp);
        stamp.ifPresent(value -> StrictJson.require(value.signum() >= 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, "opaque native completion stamp must be uint64"));
    }
}

