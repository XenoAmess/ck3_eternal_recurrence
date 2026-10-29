package org.xar.ck3.control.g2.m6;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Immutable observations only. Constructing these values grants no native action or milestone credit. */
public final class G2M6Contracts {
    private G2M6Contracts() { }

    /** Full native Sway subject for queries; contains no submission or action identity. */
    public record NativeSubject(long actorCharacterId, long targetCharacterId,
            long schemeInstanceId, int schemeInstanceGeneration) {
        public NativeSubject {
            characterId(actorCharacterId); characterId(targetCharacterId);
            StrictJson.require(actorCharacterId != targetCharacterId, "M6 actor and target differ");
            StrictJson.require(schemeInstanceId >= 0 && schemeInstanceId < 0xffff_ffffL
                    && schemeInstanceGeneration >= 0 && schemeInstanceGeneration <= 255
                    && schemeInstanceGeneration == schemeInstanceId >> 24, "M6 full instance and generation agree; generation zero is valid");
        }
    }

    public record Identity(String actionId, long actorCharacterId, long targetCharacterId,
            long schemeInstanceId, int schemeInstanceGeneration) {
        public Identity {
            StrictJson.text(actionId);
            new NativeSubject(actorCharacterId, targetCharacterId, schemeInstanceId, schemeInstanceGeneration);
        }
        public NativeSubject nativeSubject() {
            return new NativeSubject(actorCharacterId, targetCharacterId, schemeInstanceId, schemeInstanceGeneration);
        }
    }

    public record Stamp(BigInteger nativeRevision, int dateRaw) {
        public Stamp {
            Objects.requireNonNull(nativeRevision);
            StrictJson.require(nativeRevision.signum() > 0 && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "M6 exact positive uint64 native revision");
        }
        /** Existing following contract: at least one actual native revision or date is later. */
        public boolean laterThan(Stamp other) {
            Objects.requireNonNull(other);
            return nativeRevision.compareTo(other.nativeRevision) > 0 || dateRaw > other.dateRaw;
        }
        public boolean notEarlierThan(Stamp other) {
            Objects.requireNonNull(other);
            return nativeRevision.compareTo(other.nativeRevision) >= 0 && dateRaw >= other.dateRaw;
        }
    }

    /** A same-semantics refresh may retain an older consumed stamp; assessment checks new credit separately. */
    public record Consumption(boolean nextTurnConsumed, Optional<Stamp> following) {
        public Consumption { Objects.requireNonNull(following); }
        public boolean consumedAfter(Stamp source) {
            Objects.requireNonNull(source);
            return nextTurnConsumed && following.isPresent() && following.orElseThrow().laterThan(source);
        }
    }

    public enum StartOrigin { ORDINARY_FULL_PLANNER, EXPLICIT_TARGET, RECOVERED_IDENTITY_ONLY, UNKNOWN }
    public record StartEvidence(Stamp applied, Stamp independentActive, boolean postconditionVerified,
            StartOrigin origin, Consumption consumption) {
        public StartEvidence {
            Objects.requireNonNull(applied); Objects.requireNonNull(independentActive);
            Objects.requireNonNull(origin); Objects.requireNonNull(consumption);
        }
    }

    /** Complete absence is known zero. Unread, explicit absence, and a signed observed value remain distinct. */
    public record NamedValue(boolean observed, boolean present, Optional<BigInteger> value) {
        public NamedValue {
            Objects.requireNonNull(value);
            StrictJson.require(!present || observed, "M6 unread named measurement cannot claim presence");
            StrictJson.require(present == value.isPresent(), "M6 present named measurement has an exact integer value");
        }
        public Optional<BigInteger> points() {
            return !observed ? Optional.empty() : present ? value : Optional.of(BigInteger.ZERO);
        }
    }
    public record NamedGainEvidence(Stamp baseline, NamedValue before, Stamp observed, NamedValue after,
            boolean incrementalNamedGainObserved, boolean trackedInstanceActive, Consumption consumption) {
        public NamedGainEvidence {
            Objects.requireNonNull(baseline); Objects.requireNonNull(before); Objects.requireNonNull(observed);
            Objects.requireNonNull(after); Objects.requireNonNull(consumption);
        }
    }

    public enum TerminalCause {
        AUTHORED_SWAY_COMPLETE_100, TERMINATED_UNATTRIBUTED, FAILED, CANCELLED, INVALIDATED, UNKNOWN
    }
    public record TerminalEvidence(Stamp observed, boolean independentNatural, boolean instanceTerminalOutcomeObserved,
            TerminalCause cause, boolean terminalCauseObserved, Consumption consumption) {
        public TerminalEvidence {
            Objects.requireNonNull(observed); Objects.requireNonNull(cause); Objects.requireNonNull(consumption);
            StrictJson.require(!terminalCauseObserved
                    || (cause != TerminalCause.UNKNOWN && cause != TerminalCause.TERMINATED_UNATTRIBUTED),
                    "M6 neutral terminal cannot acquire an attributed cause");
        }
    }

    public record Episode(Identity identity, Optional<StartEvidence> start, Optional<NamedGainEvidence> firstNamedGain,
            Optional<TerminalEvidence> terminal, ProjectionJson originalResolved) {
        public Episode {
            Objects.requireNonNull(identity); Objects.requireNonNull(start); Objects.requireNonNull(firstNamedGain);
            Objects.requireNonNull(terminal); Objects.requireNonNull(originalResolved);
            StrictJson.require(originalResolved.isObject(), "M6 original resolved object is retained");
        }
    }

    public record CampaignEvidence(G2Source source, List<Episode> episodes, ProjectionJson originalLedger) {
        public CampaignEvidence {
            Objects.requireNonNull(source); episodes = List.copyOf(episodes); Objects.requireNonNull(originalLedger);
            StrictJson.require(originalLedger.isObject(), "M6 original ledger object is retained");
            Set<Identity> seen = new HashSet<>();
            for (Episode episode : episodes) {
                StrictJson.require(seen.add(episode.identity()), "M6 current and archived episodes are deduplicated by full original identity");
            }
        }
    }

    public enum Gate {
        ORDINARY_START, EARLY_NAMED_BASELINE, INCREMENTAL_NAMED_GAIN, NATURAL_RETAINED_TERMINAL, LATER_ORDINARY_CONSUMPTION
    }
    public record EpisodeAssessment(Identity identity, Set<Gate> satisfied, Set<Gate> missing,
            boolean evidencePacketReady, boolean usefulSchemeComplete) {
        public EpisodeAssessment {
            Objects.requireNonNull(identity); satisfied = Set.copyOf(satisfied); missing = Set.copyOf(missing);
            Set<Gate> all = new HashSet<>(satisfied);
            StrictJson.require(all.addAll(missing) || missing.isEmpty(), "M6 assessed gates are disjoint");
            StrictJson.require(all.equals(Set.of(Gate.values()))
                    && satisfied.stream().noneMatch(missing::contains), "M6 each gate has exactly one assessment");
            StrictJson.require(evidencePacketReady == missing.isEmpty() && (!usefulSchemeComplete || evidencePacketReady),
                    "M6 evidence readiness and attributed success are separate");
        }
    }

    public record CampaignAssessment(List<EpisodeAssessment> episodes, boolean evidencePacketReady,
            boolean schemeComplete, boolean wholeM6Complete) {
        public CampaignAssessment {
            episodes = List.copyOf(episodes);
            StrictJson.require(evidencePacketReady == episodes.stream().anyMatch(EpisodeAssessment::evidencePacketReady)
                    && schemeComplete == episodes.stream().anyMatch(EpisodeAssessment::usefulSchemeComplete),
                    "M6 campaign evidence derives from original episodes");
            StrictJson.require(!wholeM6Complete, "Sway evidence alone does not assess institution, nonreligious law and activity lifecycles");
        }
        public boolean grantsSubmissionAuthority() { return false; }
    }

    private static void characterId(long value) {
        NativeCharacterId.of(value);
    }
}


