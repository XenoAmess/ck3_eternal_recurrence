package org.xar.ck3.control.wave2.governance.heirlineage;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;

/** The existing same-frame, first-positive native preview decision loop. */
public final class HeirLineagePolicy {
    private HeirLineagePolicy() { }

    public record CharacterId(long value) {
        public CharacterId {
            if (value <= 0 || value >= 4_294_967_296L) {
                throw new IllegalArgumentException("full uint32 character ID required");
            }
        }
    }

    public record DynastyId(BigInteger value) {
        public DynastyId {
            Objects.requireNonNull(value, "dynasty ID");
            if (value.signum() < 0) {
                throw new IllegalArgumentException("nonnegative dynasty ID required");
            }
        }
    }

    public record Context(BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
                          CharacterId observedFirstHeir) {
        public Context {
            Objects.requireNonNull(revision, "revision");
            Objects.requireNonNull(nativeRevision, "native revision");
            Objects.requireNonNull(dateRaw, "date raw");
            Objects.requireNonNull(observedFirstHeir, "first heir");
            if (revision.signum() < 0 || nativeRevision.signum() < 0) {
                throw new IllegalArgumentException("nonnegative revision required");
            }
        }
    }

    public record Opportunity(int orderedOrdinal, CharacterId candidate, CharacterId heir,
                              boolean selectedMatrilineal, boolean effectiveMatrilineal,
                              Optional<DynastyId> playedDynasty) {
        public Opportunity {
            if (orderedOrdinal < 0) {
                throw new IllegalArgumentException("nonnegative opportunity ordinal required");
            }
            Objects.requireNonNull(candidate, "candidate");
            Objects.requireNonNull(heir, "heir");
            playedDynasty = Objects.requireNonNull(playedDynasty, "nullable observed dynasty");
        }
    }

    public record PreviewQuery(BigInteger expectedRevision, CharacterId subject, CharacterId candidate,
                               boolean requestMatrilinealOption) {
        public PreviewQuery {
            Objects.requireNonNull(expectedRevision, "expected revision");
            Objects.requireNonNull(subject, "subject");
            Objects.requireNonNull(candidate, "candidate");
            if (expectedRevision.signum() < 0 || subject.equals(candidate)) {
                throw new IllegalArgumentException("native preview requires a revision and distinct pair");
            }
        }
    }

    public sealed interface Preview permits AvailablePreview, UnavailablePreview { }

    public record AvailablePreview(boolean selectedMatrilineal, boolean effectiveMatrilineal,
                                   boolean completeCanSend, Optional<DynastyId> dynasty) implements Preview {
        public AvailablePreview {
            dynasty = Objects.requireNonNull(dynasty, "nullable observed dynasty");
        }
    }

    public record UnavailablePreview(String reason) implements Preview {
        public UnavailablePreview { Objects.requireNonNull(reason, "native reason"); }
    }

    public record PreviewObservation(BigInteger queriedNativeRevision, BigInteger dateRaw,
                                     CharacterId subject, CharacterId candidate, Preview preview) {
        public PreviewObservation {
            Objects.requireNonNull(queriedNativeRevision, "queried native revision");
            Objects.requireNonNull(dateRaw, "native date");
            Objects.requireNonNull(subject, "observed subject");
            Objects.requireNonNull(candidate, "observed candidate");
            Objects.requireNonNull(preview, "native preview");
        }
    }

    /** Implemented by the existing read authority; it is not a submit port. */
    @FunctionalInterface
    public interface PreviewPort {
        PreviewObservation query(PreviewQuery request);
    }

    public record Attempt(PreviewQuery request, PreviewObservation observation, String reason) {
        public Attempt {
            Objects.requireNonNull(request, "request");
            Objects.requireNonNull(observation, "observation");
            Objects.requireNonNull(reason, "reason");
        }
    }

    public record Selection(OptionalInt orderedOrdinal, List<Attempt> attempts) {
        public Selection {
            Objects.requireNonNull(orderedOrdinal, "optional selected ordinal");
            attempts = List.copyOf(attempts);
        }
    }

    /** The consumer supplies the existing shared preference order, without copying its policy. */
    public static Selection chooseInPreferenceOrder(Context context, List<Opportunity> opportunities,
                                                     PreviewPort previews) {
        Objects.requireNonNull(context, "context");
        Objects.requireNonNull(previews, "existing preview reader");
        List<Attempt> attempts = new ArrayList<>();
        for (Opportunity opportunity : List.copyOf(opportunities)) {
            PreviewQuery request = new PreviewQuery(context.revision(), context.observedFirstHeir(),
                    opportunity.candidate(), opportunity.selectedMatrilineal());
            PreviewObservation observation = Objects.requireNonNull(previews.query(request), "observed preview");
            if (!observation.queriedNativeRevision().equals(context.nativeRevision())
                    || !observation.dateRaw().equals(context.dateRaw())
                    || !observation.subject().equals(request.subject())
                    || !observation.subject().equals(opportunity.heir())
                    || !observation.candidate().equals(opportunity.candidate())) {
                throw new IllegalArgumentException("first-heir native lineage preview changed its candidate frame");
            }
            boolean positive = false;
            String reason;
            if (observation.preview() instanceof AvailablePreview available) {
                if (available.selectedMatrilineal() != opportunity.selectedMatrilineal()
                        || available.effectiveMatrilineal() != opportunity.effectiveMatrilineal()) {
                    throw new IllegalArgumentException("first-heir native lineage preview changed its proposal option");
                }
                reason = !available.completeCanSend() ? "native_can_send_not_true"
                        : !available.dynasty().equals(opportunity.playedDynasty())
                        ? "native_preview_not_played_dynasty" : "native_main_dynasty_opportunity";
                positive = available.completeCanSend() && available.dynasty().equals(opportunity.playedDynasty());
            } else {
                reason = ((UnavailablePreview) observation.preview()).reason();
            }
            attempts.add(new Attempt(request, observation, reason));
            if (positive) {
                return new Selection(OptionalInt.of(opportunity.orderedOrdinal()), attempts);
            }
        }
        return new Selection(OptionalInt.empty(), attempts);
    }
}
