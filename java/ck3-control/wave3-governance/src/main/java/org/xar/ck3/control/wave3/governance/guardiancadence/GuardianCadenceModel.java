package org.xar.ck3.control.wave3.governance.guardiancadence;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;

/** In-memory policy records only. No source, action, canonical persistence or cold-restoration authority. */
public final class GuardianCadenceModel {
    private GuardianCadenceModel() { }
    public record Frame(String status, long gamePid, BigInteger connectionGeneration, String episodeRunId,
            long actorCharacterId, BigInteger dateRaw, BigInteger nativeRevision, BigInteger publicRevision) {
        public Frame {
            StrictJson.text(status); StrictJson.text(episodeRunId); positive(gamePid); positive(actorCharacterId);
            positive(connectionGeneration); Objects.requireNonNull(dateRaw); nonnegative(nativeRevision); nonnegative(publicRevision);
        }
    }
    public record Focus(boolean available, FocusState state, String currentKey) {
        public Focus { StrictJson.require(!available || state != null && state != FocusState.UNKNOWN, "available focus requires a known management state"); }
    }
    public record Court(boolean available, boolean sourceQualified, Long ownerId) { }
    public record ProviderObservation(Long guardianId, String roleSource) { }
    public record Provider(String status, boolean collectionAvailable, Optional<ProviderObservation> observation) {
        public Provider { Objects.requireNonNull(observation); }
    }
    public record NamedGuardian(boolean available, boolean identityRoundTrip, boolean sampleStable, Long matchedPeerId) { }
    public record Relation(boolean observed, boolean collectionAvailable, Optional<NamedGuardian> namedGuardian) {
        public Relation { Objects.requireNonNull(namedGuardian); }
    }
    public record ScopeMaterials(long childId, String valuesStatus, BigInteger ageMeasureRaw, BigInteger sexSelectorRaw,
            Focus focus, Court court, Provider provider, Relation relation, List<String> missingObservations) {
        public ScopeMaterials {
            positive(childId); Objects.requireNonNull(ageMeasureRaw); Objects.requireNonNull(focus); Objects.requireNonNull(court);
            Objects.requireNonNull(provider); Objects.requireNonNull(relation); missingObservations = List.copyOf(missingObservations);
        }
    }
    /** Exact legacy tuple members; date and daily revision deliberately do not belong to this scope. */
    public record SourceScope(long gamePid, BigInteger connectionGeneration, String episodeRunId, long actorId,
            long heirId, long childId, BigInteger ageMeasureRaw, BigInteger sexSelectorRaw, FocusState focusState,
            String focusKey, long courtOwnerId, long namedPeerId, Long providerGuardianId, String providerRoleSource) {
        public SourceScope {
            positive(gamePid); positive(connectionGeneration); StrictJson.text(episodeRunId); positive(actorId); positive(heirId);
            positive(childId); Objects.requireNonNull(ageMeasureRaw); positive(courtOwnerId); positive(namedPeerId);
        }
    }
    public enum Flag {
        ACTOR_ALIVE("actor_alive"), RECIPIENT_ALIVE("recipient_alive"), SHOWN("shown"), CAN_SEND("can_send"),
        READY("ready_to_initiate"), NATIVE_CONTEXT("native_context_available"), ORDINARY_SUPPORTED("ordinary_context_supported"),
        SOURCE_PINS("source_code_pins_verified"), ACTOR_BINDING("actor_binding_verified"), RECIPIENT_BINDING("recipient_binding_verified"),
        OWNER_THREAD("owner_thread_verified"), TLS("tls_verified"), FRAME("frame_verified"), ACTIVE_EVENT("active_event_present"),
        INCOMING_INTERACTION("incoming_interaction_present");
        private final String wire;
        Flag(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Roles(Long actorId, Long recipientId, Long secondaryActorId, Long secondaryRecipientId) { }
    /** Cadence readiness wraps the shared wire contract without changing its nullable observations. */
    public sealed interface Materialization permits IncompleteMaterialization, CompleteMaterialization {
        EducationOptionsModel.Materialization observation();
        static Materialization fromObservation(EducationOptionsModel.Materialization observation) {
            Objects.requireNonNull(observation);
            return complete(observation) ? new CompleteMaterialization(observation) : new IncompleteMaterialization(observation);
        }
    }
    /** Default queries and legal pair-only or keys-only requests retain their original wire facts. */
    public record IncompleteMaterialization(EducationOptionsModel.Materialization observation) implements Materialization {
        public IncompleteMaterialization {
            Objects.requireNonNull(observation);
            StrictJson.require(!complete(observation), "incomplete cadence materialization required");
        }
    }
    public record CompleteMaterialization(EducationOptionsModel.Materialization observation) implements Materialization {
        public CompleteMaterialization {
            Objects.requireNonNull(observation);
            StrictJson.require(complete(observation), "available complete cadence request required");
        }
    }
    private static boolean complete(EducationOptionsModel.Materialization observation) {
        return observation.status() == EducationOptionsModel.Availability.AVAILABLE
                && observation.pair().isPresent() && observation.requestedOptionKeys().isPresent();
    }
    public record Context(String schema, String status, String source, boolean readOnly, long gamePid,
            BigInteger connectionGeneration, BigInteger dateRaw, BigInteger nativeRevision, String interactionKey,
            long playerId, long recipientId, Set<Flag> trueFlags, String unavailableReason, String executableSha256,
            BigInteger definitionStableHash, Roles roles, BigInteger selectedOptionCount, Optional<Materialization> materialization) {
        public Context {
            trueFlags = Set.copyOf(trueFlags); Objects.requireNonNull(roles); Objects.requireNonNull(materialization);
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(dateRaw); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(definitionStableHash); Objects.requireNonNull(selectedOptionCount);
        }
    }
    public sealed interface QueryRead permits UnusableQuery, ObservedQuery { }
    public record UnusableQuery(String reason) implements QueryRead { public UnusableQuery { StrictJson.text(reason); } }
    /** Observed data, not a producer-supplied GREEN eligibility flag. */
    public record ObservedQuery(String step, boolean accepted, String status, boolean readOnly, long gamePid,
            BigInteger connectionGeneration, BigInteger dateRaw, BigInteger queriedNativeRevision,
            BigInteger queriedPublicRevision, BigInteger querySequence, Context context) implements QueryRead {
        public ObservedQuery {
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(dateRaw); Objects.requireNonNull(queriedNativeRevision);
            Objects.requireNonNull(queriedPublicRevision); nonnegative(querySequence); Objects.requireNonNull(context);
        }
    }
    public record Attempt(String variant, QueryRead query) { public Attempt { Objects.requireNonNull(query); } }
    public record NegativeRecord(SourceScope scope, int count, BigInteger lastDateRaw, BigInteger lastNativeRevision,
            Optional<BigInteger> cooldownUntilDateRaw, String lastExecutableSha256, BigInteger lastDefinitionStableHash) {
        public NegativeRecord {
            Objects.requireNonNull(scope); StrictJson.require(count == 1 || count == 2, "bounded consecutive date count");
            Objects.requireNonNull(lastDateRaw); nonnegative(lastNativeRevision); Objects.requireNonNull(cooldownUntilDateRaw);
            StrictJson.text(lastExecutableSha256); Objects.requireNonNull(lastDefinitionStableHash);
        }
    }
    public record State(Map<Long, NegativeRecord> records) {
        public State {
            records = Map.copyOf(records);
            records.forEach((child, record) -> StrictJson.require(child != null && child == record.scope().childId(), "state child/scope identity mismatch"));
        }
        public static State empty() { return new State(Map.of()); }
    }
    public enum DeferStatus {
        SAME_FRAME("same_frame_negative_reuse"), POLICY_DEFERRED("policy_deferred");
        private final String wire;
        DeferStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Deferred(DeferStatus status, long childId, long guardianId, BigInteger lastDateRaw,
            BigInteger lastNativeRevision, Optional<BigInteger> cooldownUntilDateRaw) { }
    public record NegativeObserved(long childId, long guardianId, int consecutiveObservedDates,
            BigInteger lastObservedDateRaw, Optional<BigInteger> cooldownUntilDateRaw) { }
    public record ObservationResult(State state, Optional<NegativeObserved> observation) {
        public ObservationResult { Objects.requireNonNull(state); Objects.requireNonNull(observation); }
    }
    public record Input(Frame frame, Optional<ScopeMaterials> materials, Long heirId, State state,
            QueryRead defaultQuery, List<Attempt> attempts, String selectedStep) {
        public Input {
            Objects.requireNonNull(frame); Objects.requireNonNull(materials); Objects.requireNonNull(state);
            Objects.requireNonNull(defaultQuery); attempts = List.copyOf(attempts); StrictJson.text(selectedStep);
        }
    }
    public record Evaluation(Optional<SourceScope> scope, Optional<Deferred> deferredBefore, ObservationResult after) { }
    private static void positive(long value) { StrictJson.require(value > 0, "positive native identity required"); }
    private static void positive(BigInteger value) { StrictJson.require(value != null && value.signum() > 0, "positive integer required"); }
    private static void nonnegative(BigInteger value) { StrictJson.require(value != null && value.signum() >= 0, "nonnegative integer required"); }
}
