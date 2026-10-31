package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.BiFunction;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Read-only, one-head domain body adoption. The only physical reader/writer remains ContinuityStorePort. */
public final class GovernanceStateSupplier implements GovernanceCollector.StateSupplier {
    public record BodyContract<T>(DomainBodies.Slot slot, String schema, List<ExactRef> originalProducerSources,
            BiFunction<PlanningRequest, byte[], T> decode) {
        public BodyContract {
            Objects.requireNonNull(slot); StrictJson.text(schema); originalProducerSources = List.copyOf(originalProducerSources);
            StrictJson.require(!originalProducerSources.isEmpty() && originalProducerSources.stream().allMatch(ref -> ref.bytes() > 0),
                    "actual original body producer closure required"); Objects.requireNonNull(decode);
        }
    }
    @FunctionalInterface public interface RetryFrameSupplier {
        Read<CrownRetryPolicy.Frame> read(PlanningRequest request);
        default Read<CrownRetryDue.VerifiedDue> due(PlanningRequest request) {
            return new Unavailable<>("actual same-proof Crown due capture is not installed");
        }
    }
    /** Bind the M7 publisher's private committed proof before exposing the unchanged legacy pure match input. */
    public static RetryFrameSupplier verifiedCrownRetryFrames(GovernanceBorrowedSession scope, CrownRetryPublication publication,
            java.util.function.Supplier<Optional<CrownRetryPublication.ImportProof>> proofSupplier, CrownRetryDue due) {
        Objects.requireNonNull(scope); Objects.requireNonNull(publication); Objects.requireNonNull(proofSupplier); Objects.requireNonNull(due);
        return new RetryFrameSupplier() {
        @Override public Read<CrownRetryPolicy.Frame> read(PlanningRequest request) {
            Optional<CrownRetryPublication.ImportProof> retained = Objects.requireNonNull(proofSupplier.get());
            if (retained.isEmpty()) return new Unavailable<>("actual same-Game committed Crown retry publication proof is absent");
            CrownRetryPublication.ImportProof proof = retained.orElseThrow();
            try {
                CrownRetryPolicy.Frame frame = scope.use(request, session ->
                        publication.requireCurrentPublication(proof, session, request.before(), request.source(), request.deadline()));
                List<ExactRef> sources = new ArrayList<>();
                sources.add(proof.body().payload()); sources.add(proof.input().crownReadback()); sources.add(proof.input().finalTermsConsume());
                return new Known<>(frame, sources);
            } catch (IOException | IllegalArgumentException unavailable) {
                return new Unavailable<>("actual Crown retry publication proof rejected: " + unavailable.getMessage());
            }
        }
        @Override public Read<CrownRetryDue.VerifiedDue> due(PlanningRequest request) {
            Optional<CrownRetryPublication.ImportProof> retained = Objects.requireNonNull(proofSupplier.get());
            if (retained.isEmpty()) return new Unavailable<>("actual same-Game committed Crown retry publication proof is absent");
            CrownRetryPublication.ImportProof proof = retained.orElseThrow();
            try {
                return scope.use(request, session -> {
                    publication.requireCurrentPublication(proof, session, request.before(), request.source(), request.deadline());
                    CrownRetryDue.VerifiedDue captured = due.capture(session, proof, request.before(), request.source(), request.observations().snapshot(), request.deadline());
                    due.requireCurrent(session, captured, request.deadline());
                    List<ExactRef> sources = new ArrayList<>();
                    sources.add(proof.body().payload()); sources.add(proof.input().crownReadback()); sources.add(proof.input().finalTermsConsume());
                    sources.add(proof.input().source().sourceRef());
                    return new Known<>(captured, sources.stream().distinct().toList());
                });
            } catch (IOException | IllegalArgumentException unavailable) {
                return new Unavailable<>("actual same-frame Crown due capture rejected: " + unavailable.getMessage());
            }
        }
        };
    }
    private final Optional<ContinuityStorePort> store;
    private final Optional<GovernanceBorrowedSession> borrowed;
    private final Optional<BodyContract<CadenceModels.State>> cadence;
    private final Optional<BodyContract<OpeningGate>> opening;
    private final Optional<BodyContract<DomainState>> council;
    private final Optional<BodyContract<DomainState>> crown;
    private final RetryFrameSupplier retryFrames;
    public GovernanceStateSupplier(ContinuityStorePort store, Optional<BodyContract<CadenceModels.State>> cadence,
            Optional<BodyContract<OpeningGate>> opening, Optional<BodyContract<DomainState>> council,
            Optional<BodyContract<DomainState>> crown, RetryFrameSupplier retryFrames) {
        this.store = Optional.of(Objects.requireNonNull(store)); this.cadence = checked(cadence, DomainBodies.Slot.OPTIONAL_CADENCE);
        this.borrowed = Optional.empty();
        this.opening = checked(opening, DomainBodies.Slot.OPENING_GATE); this.council = checked(council, DomainBodies.Slot.COUNCIL);
        this.crown = checked(crown, DomainBodies.Slot.CROWN); this.retryFrames = Objects.requireNonNull(retryFrames);
    }
    /** Root runtime entry: all domain reads borrow the already-held concrete writer Session. */
    public GovernanceStateSupplier(GovernanceBorrowedSession borrowed, Optional<BodyContract<CadenceModels.State>> cadence,
            Optional<BodyContract<OpeningGate>> opening, Optional<BodyContract<DomainState>> council,
            Optional<BodyContract<DomainState>> crown, RetryFrameSupplier retryFrames) {
        this.store = Optional.empty(); this.borrowed = Optional.of(Objects.requireNonNull(borrowed));
        this.cadence = checked(cadence, DomainBodies.Slot.OPTIONAL_CADENCE);
        this.opening = checked(opening, DomainBodies.Slot.OPENING_GATE);
        this.council = checked(council, DomainBodies.Slot.COUNCIL);
        this.crown = checked(crown, DomainBodies.Slot.CROWN);
        this.retryFrames = Objects.requireNonNull(retryFrames);
    }
    private <T> T session(PlanningRequest request, ContinuityStorePort.SessionWork<T> work) throws IOException {
        if (borrowed.isPresent()) return borrowed.orElseThrow().use(request, work);
        return store.orElseThrow().locked(work);
    }
    private static <T> Optional<BodyContract<T>> checked(Optional<BodyContract<T>> contract, DomainBodies.Slot slot) {
        Objects.requireNonNull(contract); contract.ifPresent(value -> StrictJson.require(value.slot() == slot, "domain body contract installed under another slot")); return contract;
    }
    @Override public Read<Durable> read(PlanningRequest request) {
        try {
            return session(request, session -> {
                var head = session.head();
                StrictJson.require(head.state().machineId().equals(request.before().machineId()), "domain head machine differs");
                ExactRef headRef = session.persistedHead(); List<ExactRef> originals = new ArrayList<>();
                Optional<CadenceModels.State> cadenceState = body(session, cadence, request, headRef, originals);
                Optional<OpeningGate> gate = body(session, opening, request, headRef, originals);
                Optional<DomainState> councilState = body(session, council, request, headRef, originals);
                Optional<DomainState> crownState = body(session, crown, request, headRef, originals);
                // With no imported body, retain the existing absent-state observation metadata.
                if (originals.isEmpty()) originals.add(headRef);
                // Optional.empty means unregistered/unimported/unavailable, never clear/zero.
                return new Known<>(new Durable(request.before(), request.sessionId(), cadenceState, gate, councilState, crownState), originals);
            });
        } catch (IOException error) { return new Unavailable<>("actual continuity domain body read unavailable: " + error.getMessage()); }
    }
    private static <T> Optional<T> body(ContinuityStorePort.Session session, Optional<BodyContract<T>> installed,
            PlanningRequest request, ExactRef head, List<ExactRef> originals) throws IOException {
        if (installed.isEmpty()) return Optional.empty(); BodyContract<T> contract = installed.orElseThrow();
        StrictJson.require(session.head().state().machineId().equals(request.before().machineId()), "domain body machine differs");
        DomainBodies.Read read = session.readDomain(contract.slot());
        if (read instanceof DomainBodies.Unavailable) return Optional.empty();
        DomainBodies.Available available = (DomainBodies.Available) read; var reference = available.reference();
        StrictJson.require(available.head().equals(head) && reference.slot() == contract.slot()
                && reference.contractSchema().equals(contract.schema()),
                "domain body crossed the locked head, schema or slot");
        StrictJson.require(DomainBodies.reference(session.head().state(), contract.slot()).filter(reference::equals).isPresent(),
                "domain body is absent from the same actual head");
        originals.add(reference.payload());
        return Optional.of(Objects.requireNonNull(contract.decode().apply(request, available.canonicalBody()), "domain body decoder returned null"));
    }
    public static BodyContract<CadenceModels.State> cadence(List<ExactRef> originalProducerSources) {
        return new BodyContract<>(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, originalProducerSources,
                (request, body) -> {
                    Obj original = object(parse(body), "actual cadence body");
                    StrictJson.require(new Text(request.before().frame().episodeRunId()).equals(original.get("episode_run_id")),
                            "another episode's cadence requires the actual producer transition before publication");
                    return CadenceJson.readState(body, request.before().frame().episodeRunId());
                });
    }
    public static BodyContract<DomainState> legacyCouncil(String registeredSchema, List<ExactRef> originalProducerSources) {
        return new BodyContract<>(DomainBodies.Slot.COUNCIL, registeredSchema, originalProducerSources, GovernanceStateSupplier::decodeLegacyCouncil);
    }
    public static BodyContract<DomainState> legacyCrown(String registeredSchema, List<ExactRef> originalProducerSources) {
        return new BodyContract<>(DomainBodies.Slot.CROWN, registeredSchema, originalProducerSources, GovernanceStateSupplier::decodeLegacyCrown);
    }
    public static DomainState decodeLegacyCouncil(PlanningRequest request, byte[] body) {
        Obj value = object(parse(body), "original Council body");
        StrictJson.require(value.members().keySet().equals(java.util.Set.of("schema", "pending", "applied"))
                && new Text("xar.ck3.private-council-formal/v1").equals(value.get("schema")), "original Council body schema/fields differ");
        nullableObject(value.get("applied"), "original Council applied record"); return domain(request, value);
    }
    public static DomainState decodeLegacyCrown(PlanningRequest request, byte[] body) {
        Obj value = object(parse(body), "original Crown body");
        StrictJson.require(value.members().keySet().equals(java.util.Set.of("pending", "resolved", "retry")), "original Crown body fields differ");
        nullableObject(value.get("resolved"), "original Crown resolved record"); nullableObject(value.get("retry"), "original Crown retry"); return domain(request, value);
    }
    private static DomainState domain(PlanningRequest request, Obj value) {
        Optional<Obj> pending = nullableObject(value.get("pending"), "original pending record");
        DomainStatus status = pending.isEmpty() ? DomainStatus.KNOWN_CLEAR
                : new Text(request.before().frame().episodeRunId()).equals(pending.orElseThrow().get("episode_run_id")) ? DomainStatus.PENDING : DomainStatus.UNKNOWN;
        // Original ACK/applied JSON remains original evidence. It is never reconstructed as a Java ActionReceipt.
        return new DomainState(status, Optional.empty(), pending, value);
    }
    private static Optional<Obj> nullableObject(Value value, String field) {
        StrictJson.require(value != null, field + " is missing"); return value == Nil.INSTANCE ? Optional.empty() : Optional.of(object(value, field));
    }
    @Override public Read<CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) {
        if (crown.isEmpty()) return new Unavailable<>("actual Crown body contract is not installed");
        try {
            return session(request, session -> {
                // Proof consumption and actual body read share the same outer writer critical section.
                Read<CrownRetryPolicy.Frame> frameRead = retryFrames.read(request);
                if (frameRead instanceof Unavailable<CrownRetryPolicy.Frame> unavailable)
                    return new Unavailable<CrownRetryCodec.MatchRequest>(unavailable.reason());
                Known<CrownRetryPolicy.Frame> actual = (Known<CrownRetryPolicy.Frame>) frameRead; var context = actual.value().context();
                if (context == null || context.bridgePid() == null || context.bridgePid().signum() <= 0)
                    return new Unavailable<CrownRetryCodec.MatchRequest>("actual bridge PID/episode context is unavailable");
                StrictJson.require(context.episodeRunId().equals(request.before().frame().episodeRunId()) && actual.value().playedCharacterObject()
                        && request.before().frame().identity().player().equals(actual.value().actorCharacterId())
                        && request.before().frame().identity().dateRaw().equals(actual.value().dateRaw()), "actual Crown retry context crossed the current actor/episode/date");
                List<ExactRef> originals = new ArrayList<>(actual.originals()); ExactRef head = session.persistedHead();
                var state = body(session, crown, request, head, originals);
                if (state.isEmpty()) return new Unavailable<CrownRetryCodec.MatchRequest>("actual Crown body is unimported");
                Obj input = new Obj(Map.of()).with("schema", new Text(CrownRetryCodec.MATCH_SCHEMA))
                        .with("bridge_pid", context.bridgePid() == null ? Nil.INSTANCE : new IntegerValue(context.bridgePid()))
                        .with("snapshot", request.observations().snapshot()).with("state", state.orElseThrow().originalBody()).with("law_key", new Text(lawKey));
                return new Known<>(CrownRetryCodec.decodeMatch(encode(input)), originals);
            });
        } catch (IOException error) { return new Unavailable<>("actual Crown retry body read unavailable: " + error.getMessage()); }
    }
    @Override public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {
        if (crown.isEmpty()) return new Unavailable<>("actual Crown body contract is not installed");
        try { return session(request, session -> retryFrames.due(request)); }
        catch (IOException | IllegalArgumentException unavailable) {
            return new Unavailable<>("actual Crown due body read unavailable: " + unavailable.getMessage());
        }
    }
}
