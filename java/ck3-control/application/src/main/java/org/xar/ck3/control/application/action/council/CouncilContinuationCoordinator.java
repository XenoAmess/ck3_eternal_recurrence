package org.xar.ck3.control.application.action.council;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Sole Council continuation issuer. Every potentially mutating STATUS is durably issued before its one write. */
public final class CouncilContinuationCoordinator {
    public static final String INPUT_SCHEMA = "xar.java-council-continuation-reducer-input/v1";
    public enum Boundary { ISSUED_COMMITTED, OUTCOME_ARCHIVED, OUTCOME_COMMITTED }
    @FunctionalInterface public interface FaultProbe { void after(Boundary boundary) throws IOException; }
    private record Runtime(ActionJournal journal, ActionPorts.OutcomeArchive archive, CouncilContinuationPorts.GuardPort guard,
            CouncilContinuationPorts.NativePort nativePort, CouncilContinuationPorts.Policy policy) { }
    private record Commit(ExactRef payload, ExactRef event) { }
    private record View(DomainBodies.Available body, State state, List<Retained> records) { }
    @FunctionalInterface private interface Work<T> { T run() throws IOException; }
    private final Path originalLock;
    private final List<ExactRef> sources;
    private final Clock clock;
    private final FaultProbe faults;
    private final ThreadLocal<ContinuityStorePort.Session> active = new ThreadLocal<>();
    private Runtime runtime;

    public CouncilContinuationCoordinator(Path originalWriterLock, List<ExactRef> exactProducerSources, Clock clock) {
        this(originalWriterLock, exactProducerSources, clock, boundary -> { });
    }
    public CouncilContinuationCoordinator(Path originalWriterLock, List<ExactRef> exactProducerSources, Clock clock, FaultProbe faults) {
        originalLock = Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize(); sources = List.copyOf(exactProducerSources);
        StrictJson.require(!sources.isEmpty() && sources.size() <= 64, "actual fixed continuation producer/reducer source closure required");
        this.clock = Objects.requireNonNull(clock); this.faults = Objects.requireNonNull(faults);
    }
    /** One bootstrap binding, before Root freezes/uses the runtime. Rebinding an installed graph is forbidden. */
    public synchronized void bind(ActionJournal journal, ActionPorts.OutcomeArchive archive, CouncilContinuationPorts.GuardPort guard,
            CouncilContinuationPorts.NativePort nativePort, CouncilContinuationPorts.Policy policy) {
        StrictJson.require(runtime == null, "continuation runtime already bound");
        runtime = new Runtime(Objects.requireNonNull(journal), Objects.requireNonNull(archive), Objects.requireNonNull(guard), Objects.requireNonNull(nativePort), Objects.requireNonNull(policy));
    }
    private synchronized Runtime runtime() { return Objects.requireNonNull(runtime, "actual Root continuation runtime is not bound"); }

    public CouncilContinuationReceipt continueOnce(ContinuityStorePort.Session same, ActionCommand parent, ActionState.Attempt original,
            Stage stage, Instant callerDeadline) throws IOException {
        return scoped(same, () -> runtime().journal().locked(same, locked -> {
            try { return issueAndSend(same, locked, parent, original, stage, callerDeadline); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }));
    }
    private CouncilContinuationReceipt issueAndSend(ContinuityStorePort.Session same, ActionJournal.LockedJournal locked,
            ActionCommand parent, ActionState.Attempt original, Stage stage, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(stage); Objects.requireNonNull(callerDeadline); Runtime r = runtime();
        ActionReceipt actual = canonical(locked.head(), parent.actionId()); requireOriginal(actual, parent, original, true);
        StrictJson.require(ActionScope.currentActionId().filter(parent.actionId()::equals).isPresent(), "continuation requires the original coordinator-owned parent scope");
        Instant observationDeadline = ActionObservationWindow.deadline(parent);
        Instant deadline = callerDeadline.isBefore(observationDeadline) ? callerDeadline : observationDeadline;
        StrictJson.require(clock.instant().isBefore(deadline), "continuation caller deadline already expired");
        View view = view(same);
        Scope scope = new Scope(parent.actionId(), actual.bodySha256(), original.requestId());
        if (view.state().active().isPresent() && !view.state().active().orElseThrow().equals(scope)) view = rotate(same, view);
        StrictJson.require(view.records().stream().allMatch(row -> row.status() == Status.ACK), "original ISSUED or UNKNOWN continuation blocks all further request IDs");
        GuardEvidence guard = r.guard().current(same, locked.head(), actual, deadline); verifyFresh(actual, original, guard, deadline);
        List<ExactRef> supporting = List.copyOf(r.policy().prepareEvidence(same, locked.head(), actual, stage, view.records(), r.archive()));
        String id = RequestIds.nextRead(); NativeRequest prepared = new NativeRequest(stage.step(), Optional.empty(), new RawJson(new byte[] {'{', '}'}));
        ExactRef preparedRef = r.archive().preserveRequest(prepared), parentRef = r.archive().preserveReceipt(actual);
        Request request = new Request(scope, id, stage, parentRef, preparedRef, guard, clock.instant(), deadline,
                Math.addExact(same.head().state().sequence(), 1), supporting);
        Retained issued = preserve(new Entry(request, Status.ISSUED, Optional.empty(), Optional.empty(), 0));
        State issuedState = CouncilContinuationReducer.issue(view.state(), view.records(), issued);
        Commit committed = commit(same, issuedState, input("ISSUE", Optional.of(issued.reference()), Optional.empty(), Optional.empty()), evidence(view, issued));
        StrictJson.require(same.head().state().sequence() == request.issuedSequence(), "actual issued canonical sequence differs from the original request");
        IssuedCustody custody = new IssuedCustody(issued.reference(), committed.payload(), committed.event());
        faults.after(Boundary.ISSUED_COMMITTED);
        String issuedHead = same.head().digest();
        CouncilContinuationPermit permit = new CouncilContinuationPermit(request, prepared, () -> {
            try {
                requireSession(same); View current = view(same);
                StrictJson.require(current.body().reference().payload().equals(custody.domainPayload()) && same.head().digest().equals(issuedHead)
                        && current.records().getLast().equals(issued), "durable original ISSUED state changed before the one native write");
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }, clock);
        NativeActionPort.DispatchOutcome outcome;
        try { outcome = Objects.requireNonNull(r.nativePort().submit(permit, prepared, deadline)); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); outcome = new NativeActionPort.Unknown(id, "continuation interrupted after durable ISSUED; collect original only", new byte[0], Optional.empty());
        } catch (IOException | RuntimeException failure) {
            outcome = new NativeActionPort.Unknown(id, "continuation result unavailable after durable ISSUED: " + failure.getClass().getName(), new byte[0], Optional.empty());
        } finally { permit.close(); }
        if (!outcome.requestId().equals(id)) outcome = new NativeActionPort.Unknown(id, "continuation returned another request ID; no replay", new byte[0], Optional.empty());
        return recordOutcome(same, issued, custody, outcome, false);
    }

    /** Collects the already issued exact request ID. No permit, fresh nonce or submission port is available here. */
    public CouncilContinuationReceipt recover(ContinuityStorePort.Session same, String requestId, Instant deadline) throws IOException {
        return scoped(same, () -> runtime().journal().locked(same, locked -> {
            try {
                View current = view(same); Retained previous = current.records().stream().filter(row -> row.request().requestId().equals(requestId)).findFirst().orElseThrow(() -> new IllegalArgumentException("original continuation request absent"));
                if (previous.status() == Status.ACK) return retainedReceipt(same, previous);
                IssuedCustody custody = previous.entry().issued().orElseGet(() -> new IssuedCustody(previous.reference(), current.body().reference().payload(), event(locked.head(), previous.request().issuedSequence())));
                Optional<NativeActionPort.AckReceived> late;
                try { late = runtime().nativePort().collectOriginalOutcome(requestId, deadline); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); late = Optional.empty(); }
                catch (IOException failure) { late = Optional.empty(); }
                if (previous.status() == Status.UNKNOWN && (late.isEmpty() || late.orElseThrow().outbound().isEmpty())) return retainedReceipt(same, previous);
                NativeActionPort.DispatchOutcome outcome = late.<NativeActionPort.DispatchOutcome>map(value -> value).orElseGet(() ->
                        new NativeActionPort.Unknown(requestId, "restored ISSUED has no original terminal result; collect only, never replay", new byte[0], Optional.empty()));
                return recordOutcome(same, previous, custody, outcome, true);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }));
    }
    public List<Retained> retained(ContinuityStorePort.Session same) throws IOException { return scoped(same, () -> view(same).records()); }

    /** Re-opens exact immutable ledger events and their actual producer inputs; decoding a row alone grants nothing. */
    public void verifyCanonicalChain(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
            List<CouncilContinuationReceipt> receipts) throws IOException {
        scoped(same, () -> {
            WriterContracts.Head current = same.head();
            StrictJson.require(current.digest().equals(actualHead.digest()) && current.documents().equals(actualHead.documents())
                    && current.absent().equals(actualHead.absent()) && current.indexRepairs().equals(actualHead.indexRepairs()), "continuation verifier needs the exact current original writer Head");
            StrictJson.require(!receipts.isEmpty() && receipts.size() <= MAX_ACTIVE_REQUESTS, "complete bounded continuation receipt chain required");
            Set<String> seen = new java.util.HashSet<>(); Scope scope = receipts.getFirst().request().scope();
            for (CouncilContinuationReceipt receipt : List.copyOf(receipts)) {
                StrictJson.require(scope.equals(receipt.request().scope()) && seen.add(receipt.request().requestId()), "continuation chain repeats or crosses an original action");
                Retained issued = retained(receipt.issued().record()), result = retained(receipt.latestRecord());
                StrictJson.require(issued.status() == Status.ISSUED && issued.request().equals(receipt.request())
                        && result.request().equals(receipt.request()) && result.status() == receipt.status()
                        && result.entry().issued().filter(receipt.issued()::equals).isPresent(), "receipt does not retain the original immutable issued/result rows");
                NativeActionPort.DispatchOutcome original = runtime().archive().load(result.entry().outcome().orElseThrow());
                StrictJson.require(receipt.outcome().filter(original::equals).isPresent() && original.requestId().equals(receipt.request().requestId()), "receipt original dispatch changed");
                verifyCanonicalEvent(same, actualHead, receipt.issued().event(), receipt.request().issuedSequence(), receipt.issued().domainPayload(),
                        receipt.issued().record(), Set.of("ISSUE"));
                verifyCanonicalEvent(same, actualHead, receipt.resultEvent(), result.entry().resultSequence(), receipt.resultDomainPayload(),
                        receipt.latestRecord(), Set.of("OUTCOME", "COLLECT"));
                var parent = runtime().archive().loadReceipt(receipt.request().originalParentReceipt());
                StrictJson.require(parent.command().actionId().equals(scope.parentActionId()) && parent.bodySha256().equals(scope.parentBodySha256())
                        && ActionTransitions.attempt(parent.state()).filter(attempt -> attempt.requestId().equals(scope.originalAttemptRequestId())).isPresent(), "continuation chain crossed its original action/attempt");
                verifyRequest(receipt.request());
            }
            return null;
        });
    }
    private void verifyCanonicalEvent(ContinuityStorePort.Session same, WriterContracts.Head head, ExactRef reference, long sequence,
            ExactRef payload, ExactRef record, Set<String> kinds) throws IOException {
        WriterContracts.Pin pin = same.capturePin(reference, MAX_BODY_BYTES);
        StrictJson.require(head.documents().contains(pin) && reference.equals(event(head, sequence)), "continuation event is not an actual immutable canonical pin");
        byte[] raw = same.readPinned(pin, MAX_BODY_BYTES); same.verifyPin(pin);
        ObjectNode event = StrictJson.object(StrictJson.parse(raw, MAX_BODY_BYTES), Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        StrictJson.require(StrictJson.integer(event.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER) == sequence
                && DomainBodies.IMPORT_KIND.equals(StrictJson.text(event.get("kind"))), "continuation event has another sequence/kind");
        ObjectNode details = StrictJson.object(event.get("details"), Set.of("evidence_id", "machine_id", "source", "domain_body", "precondition_digest"));
        StrictJson.require(StrictJson.text(details.get("machine_id")).equals(head.state().machineId()), "continuation event crossed machines");
        DomainBodies.BodyRef body = DomainBodies.BodyRef.fromJson(details.get("domain_body"));
        StrictJson.require(body.slot() == DomainBodies.Slot.COUNCIL_CONTINUATION && body.contractSchema().equals(SCHEMA)
                && body.payload().equals(payload) && body.producerSources().equals(sources), "continuation event references another domain/body/producer");
        ObjectNode source = StrictJson.object(details.get("source"), Set.of("original_body", "producer_input", "producer_sources", "evidence"));
        StrictJson.require(ExactRef.fromJson(source.get("original_body")).equals(payload), "continuation publication lost its original full body");
        ObjectNode input = StrictJson.object(StrictJson.parse(readMaterial(ExactRef.fromJson(source.get("producer_input"))), MAX_BODY_BYTES), Set.of("schema", "kind", "record", "seed_manifest", "closed_scope"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(input.get("schema"))) && kinds.contains(StrictJson.text(input.get("kind")))
                && ExactRef.fromJson(input.get("record")).equals(record) && input.get("seed_manifest").isNull() && input.get("closed_scope").isNull(), "canonical continuation producer input does not bind its exact issued/result row");
        State state = CouncilContinuationCodec.decodeState(readMaterial(payload)); StrictJson.require(state.records().contains(record), "canonical continuation body omitted its exact row");
        ContinuityState after = ContinuityState.fromJson(event.get("after"), head.state().machineId());
        StrictJson.require(after.sequence() == sequence && DomainBodies.reference(after, DomainBodies.Slot.COUNCIL_CONTINUATION).filter(body::equals).isPresent(), "canonical event after-state lost the original continuation body");
        var request = new WriterContracts.Request(DomainBodies.IMPORT_KIND, ContinuityJson.canonical(details), List.of());
        StrictJson.require(request.identity().equals(StrictJson.text(event.get("identity"))), "canonical continuation event identity differs");
    }

    private CouncilContinuationReceipt recordOutcome(ContinuityStorePort.Session same, Retained previous, IssuedCustody custody,
            NativeActionPort.DispatchOutcome original, boolean collectedLate) throws IOException {
        Runtime r = runtime(); ExactRef originalRef = r.archive().preserve(original);
        StrictJson.require(original.equals(r.archive().load(originalRef)), "actual continuation outcome archive changed");
        faults.after(Boundary.OUTCOME_ARCHIVED);
        Status status = original instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent() ? Status.ACK : Status.UNKNOWN;
        Retained next = preserve(new Entry(previous.request(), status, Optional.of(originalRef), Optional.of(custody), Math.addExact(same.head().state().sequence(), 1)));
        View before = view(same); State reduced = CouncilContinuationReducer.outcome(before.state(), before.records(), previous, next, collectedLate);
        Commit committed = commit(same, reduced, input(collectedLate ? "COLLECT" : "OUTCOME", Optional.of(next.reference()), Optional.empty(), Optional.empty()), evidence(before, next));
        StrictJson.require(same.head().state().sequence() == next.entry().resultSequence(), "actual result event sequence differs from its original durable row");
        faults.after(Boundary.OUTCOME_COMMITTED);
        return new CouncilContinuationReceipt(next.request(), next.status(), Optional.of(original), custody, next.reference(), committed.payload(), committed.event());
    }
    private CouncilContinuationReceipt retainedReceipt(ContinuityStorePort.Session same, Retained retained) throws IOException {
        var issued = retained.entry().issued().orElseThrow(); var outcome = runtime().archive().load(retained.entry().outcome().orElseThrow());
        ExactRef result = event(same.head(), retained.entry().resultSequence());
        WriterContracts.Pin pin = same.capturePin(result, MAX_BODY_BYTES);
        StrictJson.require(same.head().documents().contains(pin), "historical result must retain its exact immutable event pin");
        ObjectNode event = StrictJson.object(StrictJson.parse(same.readPinned(pin, MAX_BODY_BYTES), MAX_BODY_BYTES), Set.of("sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"));
        same.verifyPin(pin);
        ObjectNode details = StrictJson.object(event.get("details"), Set.of("evidence_id", "machine_id", "source", "domain_body", "precondition_digest"));
        DomainBodies.BodyRef body = DomainBodies.BodyRef.fromJson(details.get("domain_body"));
        ExactRef payload = body.payload();
        verifyCanonicalEvent(same, same.head(), result, retained.entry().resultSequence(), payload, retained.reference(), Set.of("OUTCOME", "COLLECT"));
        return new CouncilContinuationReceipt(retained.request(), retained.status(), Optional.of(outcome), issued, retained.reference(), payload, result);
    }
    private View rotate(ContinuityStorePort.Session same, View before) throws IOException {
        Scope scope = before.state().active().orElseThrow(); ActionReceipt settled = canonical(same.head(), scope.parentActionId());
        ExactRef parent = runtime().archive().preserveReceipt(settled);
        ObjectNode complete = StrictJson.object(); complete.put("schema", "xar.java-council-closed-scope/v1");
        complete.set("previous_state", before.body().reference().payload().toJson()); complete.set("settled_parent", parent.toJson());
        ExactRef completeRef = preserveMaterial(StrictJson.canonical(complete, MAX_BODY_BYTES));
        State reduced = CouncilContinuationReducer.rotate(before.state(), before.records(), settled, completeRef);
        commit(same, reduced, input("ROTATE", Optional.empty(), Optional.empty(), Optional.of(completeRef)), List.of(before.body().reference().payload(), parent, completeRef));
        return view(same);
    }

    /** Missing storage never means clear. Root must adopt a complete original manifest or a proven fresh-session seed. */
    public void adoptOriginal(ContinuityStorePort.Session same, ExactRef completeOriginalManifest, CouncilContinuationPorts.SeedAuthority seed) throws IOException {
        scoped(same, () -> {
            StrictJson.require(same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION) instanceof DomainBodies.Unavailable, "continuation seed is only imported once");
            State original = seed.readCompleteOriginal(same, same.head(), completeOriginalManifest, runtime().archive());
            StrictJson.require(original.machineId().equals(same.head().state().machineId()), "continuation seed crossed the original writer machine");
            commit(same, original, input("SEED", Optional.empty(), Optional.of(completeOriginalManifest), Optional.empty()), List.of(completeOriginalManifest)); return null;
        });
    }
    public DomainBodies.Registration registration(CouncilContinuationPorts.SeedAuthority seed) {
        Objects.requireNonNull(seed);
        return new DomainBodies.Registration(DomainBodies.Slot.COUNCIL_CONTINUATION, SCHEMA, MAX_BODY_BYTES, sources, new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState detached, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) { throw new IllegalStateException("continuation verification needs the actual held writer Head"); }
            @Override public String verify(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) throws IOException {
                return verifyImport(head, previous, request, body, seed);
            }
        });
    }
    private String verifyImport(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request,
            byte[] proposedBody, CouncilContinuationPorts.SeedAuthority seed) throws IOException {
        ContinuityStorePort.Session same = active.get(); requireSession(same);
        StrictJson.require(same.head().digest().equals(head.digest()) && same.head().documents().equals(head.documents()), "continuation reducer received a detached writer Head");
        ObjectNode in = StrictJson.object(StrictJson.parse(request.producerInput(), MAX_BODY_BYTES), Set.of("schema", "kind", "record", "seed_manifest", "closed_scope"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(in.get("schema"))), "continuation reducer input schema");
        String kind = StrictJson.text(in.get("kind")); State expected;
        if (kind.equals("SEED")) {
            StrictJson.require(previous.isEmpty() && in.get("record").isNull() && in.get("closed_scope").isNull(), "seed cannot overwrite an existing continuation domain");
            ExactRef manifest = ExactRef.fromJson(in.get("seed_manifest")); StrictJson.require(request.evidence().contains(manifest), "complete original seed manifest must be pinned");
            expected = seed.readCompleteOriginal(same, head, manifest, runtime().archive());
        } else {
            StrictJson.require(previous.isPresent() && in.get("seed_manifest").isNull(), "unimported continuation state is unavailable");
            State before = CouncilContinuationCodec.decodeState(readMaterial(previous.orElseThrow().payload())); List<Retained> prior = load(before);
            if (kind.equals("ROTATE")) {
                StrictJson.require(in.get("record").isNull(), "closed scope is a distinct transition"); ExactRef closed = ExactRef.fromJson(in.get("closed_scope"));
                var closure = StrictJson.object(StrictJson.parse(readMaterial(closed), MAX_BODY_BYTES), Set.of("schema", "previous_state", "settled_parent"));
                StrictJson.require("xar.java-council-closed-scope/v1".equals(StrictJson.text(closure.get("schema"))) && ExactRef.fromJson(closure.get("previous_state")).equals(previous.orElseThrow().payload()), "closed scope lost the complete prior manifest");
                ActionReceipt actual = canonical(head, before.active().orElseThrow().parentActionId());
                StrictJson.require(actual.equals(runtime().archive().loadReceipt(ExactRef.fromJson(closure.get("settled_parent")))), "closed scope did not preserve the canonical settled parent");
                expected = CouncilContinuationReducer.rotate(before, prior, actual, closed);
            } else {
                StrictJson.require(in.get("closed_scope").isNull(), "request transition cannot archive its scope");
                Retained next = retained(ExactRef.fromJson(in.get("record"))); ActionReceipt parent = canonical(head, next.request().scope().parentActionId());
                requireOriginal(parent, runtime().archive().loadReceipt(next.request().originalParentReceipt()).command(), ActionTransitions.attempt(parent.state()).orElseThrow(), kind.equals("ISSUE"));
                StrictJson.require(parent.bodySha256().equals(next.request().scope().parentBodySha256())
                        && ActionTransitions.attempt(parent.state()).orElseThrow().requestId().equals(next.request().scope().originalAttemptRequestId()), "continuation row changed the original attempt");
                verifyRequest(next.request());
                if (kind.equals("ISSUE")) {
                    StrictJson.require(next.request().issuedSequence() == Math.addExact(head.state().sequence(), 1), "issued request did not consume the actual next sequence");
                    GuardEvidence actual = runtime().guard().current(same, head, parent, next.request().deadline());
                    verifyFresh(parent, ActionTransitions.attempt(parent.state()).orElseThrow(), actual, next.request().deadline());
                    StrictJson.require(actual.origin().equals(next.request().guard().origin()) && actual.source().equals(next.request().guard().source())
                            && actual.connectionGeneration().equals(next.request().guard().connectionGeneration())
                            && actual.nativeEvidence().equals(next.request().guard().nativeEvidence()) && actual.capabilityEvidence().equals(next.request().guard().capabilityEvidence()), "actual source frame changed before continuation issue");
                    runtime().policy().verifyIssue(same, head, parent, prior, next.request(), runtime().archive());
                    expected = CouncilContinuationReducer.issue(before, prior, next);
                } else {
                    StrictJson.require(kind.equals("OUTCOME") || kind.equals("COLLECT"), "known continuation reducer transition required");
                    StrictJson.require(next.entry().resultSequence() == Math.addExact(head.state().sequence(), 1), "result must consume the actual next canonical sequence");
                    Retained old = prior.stream().filter(row -> row.request().requestId().equals(next.request().requestId())).findFirst().orElseThrow();
                    NativeActionPort.DispatchOutcome original = runtime().archive().load(next.entry().outcome().orElseThrow());
                    StrictJson.require(original.requestId().equals(next.request().requestId()), "original continuation result belongs to another request");
                    Status actual = original instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent() ? Status.ACK : Status.UNKNOWN;
                    StrictJson.require(actual == next.status(), "ACK/UNKNOWN classification changed");
                    runtime().policy().verifyOutcome(same, head, parent, prior, next.entry(), original, runtime().archive());
                    expected = CouncilContinuationReducer.outcome(before, prior, old, next, kind.equals("COLLECT"));
                }
            }
        }
        StrictJson.require(expected.machineId().equals(head.state().machineId()) && Arrays.equals(CouncilContinuationCodec.encodeState(expected), proposedBody), "continuation body differs from the same real reducer replay");
        return ActionCodec.sha256(proposedBody);
    }

    private Commit commit(ContinuityStorePort.Session same, State state, byte[] producer, List<ExactRef> evidence) throws IOException {
        ExactRef body = preserveMaterial(CouncilContinuationCodec.encodeState(state));
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL_CONTINUATION, SCHEMA, body, producer, List.copyOf(new LinkedHashSet<>(evidence)),
                "council-continuation-" + same.head().state().sequence() + "-" + body.sha256());
        var result = same.commitImport(same.previewImport(request)); View actual = view(same);
        StrictJson.require(actual.body().reference().payload().equals(body) && actual.state().equals(state), "canonical continuation commit readback differs");
        return new Commit(body, event(same.head(), result.head().sequence()));
    }
    private View view(ContinuityStorePort.Session same) throws IOException {
        requireSession(same); var read = same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION);
        if (!(read instanceof DomainBodies.Available body)) throw new IOException("complete continuation domain unavailable; missing never means empty");
        StrictJson.require(body.reference().contractSchema().equals(SCHEMA), "continuation domain schema changed");
        State state = CouncilContinuationCodec.decodeState(body.canonicalBody()); return new View(body, state, load(state));
    }
    private List<Retained> load(State state) { return state.records().stream().map(this::retained).toList(); }
    private Retained retained(ExactRef reference) { return new Retained(reference, CouncilContinuationCodec.decodeEntry(readMaterial(reference))); }
    private Retained preserve(Entry entry) { ExactRef ref = preserveMaterial(CouncilContinuationCodec.encodeEntry(entry)); return retained(ref); }
    private ExactRef preserveMaterial(byte[] body) {
        var raw = new RawJson(body); ExactRef ref = runtime().archive().preserveMaterial(raw);
        StrictJson.require(Arrays.equals(body, readMaterial(ref)), "continuation immutable archive differs"); return ref;
    }
    private byte[] readMaterial(ExactRef reference) {
        byte[] raw = runtime().archive().loadMaterial(reference).bytes();
        StrictJson.require(reference.bytes() == raw.length && reference.sha256().equals(ActionCodec.sha256(raw)), "continuation original body changed"); return raw;
    }
    private ActionReceipt canonical(WriterContracts.Head head, String actionId) { return ContinuityActionJournal.lookup(head.state(), actionId, runtime().archive()).orElseThrow(() -> new IllegalArgumentException("canonical original action absent")); }
    private void requireOriginal(ActionReceipt actual, ActionCommand expected, ActionState.Attempt attempt, boolean issuing) {
        StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(actual.command()), ActionCodec.encodeCommand(expected))
                && ActionTransitions.attempt(actual.state()).filter(attempt::equals).isPresent(), "continuation changed the complete canonical parent/original attempt");
        StrictJson.require(actual.command().operation().value().equals("private-assign-councillor-v1"), "only the reviewed Council action may use continuation");
        StrictJson.require(!actual.settled() && (!issuing || actual.state() instanceof ActionState.AckReceived), "new continuation only follows the live original ACK; UNKNOWN is collect-only");
        var original = ActionTransitions.dispatch(actual.state()).orElseThrow();
        StrictJson.require(original instanceof NativeActionPort.AckReceived ack && ack.nativeOk() && ack.outbound().isPresent(), "original Council submit needs its actual successful pending ACK and outbound");
    }
    private void verifyFresh(ActionReceipt parent, ActionState.Attempt original, GuardEvidence actual, Instant deadline) {
        Instant now = clock.instant(); GuardEvidence before = original.guard();
        StrictJson.require(actual.origin() instanceof CommandOrigin.Gameplay && before.origin() instanceof CommandOrigin.Gameplay
                && actual.origin().machineId().equals(before.origin().machineId()) && actual.origin().game().equals(before.origin().game())
                && actual.observed().frame().episodeRunId().equals(before.observed().frame().episodeRunId())
                && actual.observed().frame().identity().player().equals(before.observed().frame().identity().player())
                && actual.observed().frame().identity().nativeRevision().compareTo(before.observed().frame().identity().nativeRevision()) >= 0,
                "fresh continuation crossed original Game/player/episode or moved backward");
        StrictJson.require(actual.source().equals(parent.command().source()) && actual.sessionId().equals(parent.command().sessionId())
                && actual.connectionGeneration().equals(before.connectionGeneration()) && actual.authorityId().equals(before.authorityId())
                && actual.operation().equals(parent.command().operation()) && !actual.supportingEvidence().isEmpty(), "fresh continuation source/session/authority/original operation changed");
        StrictJson.require(now.isBefore(deadline) && now.isBefore(ActionObservationWindow.deadline(parent.command())) && !now.isBefore(actual.observedAt()) && !now.isAfter(actual.validUntil()), "continuation source guard is stale or future-dated");
    }
    private void verifyRequest(Request request) {
        NativeRequest prepared = runtime().archive().loadRequest(request.preparedRequest());
        StrictJson.require(prepared.step().equals(request.stage().step()) && prepared.requiredCapability().isEmpty()
                && prepared.additionalFields().objectFieldNames().isEmpty(), "continuation cannot select another step/capability/argument");
        request.supportingEvidence().forEach(ref -> { try { var pin = active.get().capturePin(ref, WriterContracts.MAX_PIN_BYTES); active.get().verifyPin(pin); } catch (IOException failure) { throw new UncheckedIOException(failure); } });
    }
    private void requireSession(ContinuityStorePort.Session same) throws IOException {
        Objects.requireNonNull(same, "live original continuation writer Session required"); same.requireWriter(originalLock);
        runtime().archive().withSession(same); StrictJson.require(active.get() == same, "continuation writer scope is escaped or on another thread");
    }
    private <T> T scoped(ContinuityStorePort.Session same, Work<T> work) throws IOException {
        ContinuityStorePort.Session previous = active.get(); StrictJson.require(previous == null || previous == same, "another continuation writer Session is active"); active.set(same);
        try {
            requireSession(same);
            return runtime().archive().inSession(same, bound -> {
                try { return work.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
        }
        catch (UncheckedIOException failure) { throw failure.getCause(); }
        finally { if (previous == null) active.remove(); else active.set(previous); }
    }
    private List<ExactRef> evidence(View previous, Retained next) {
        var refs = new ArrayList<ExactRef>(); refs.add(previous.body().reference().payload()); refs.add(next.reference());
        Request request = next.request(); refs.add(request.originalParentReceipt()); refs.add(request.preparedRequest());
        refs.add(request.guard().nativeEvidence()); refs.add(request.guard().capabilityEvidence()); refs.addAll(request.guard().supportingEvidence()); refs.addAll(request.supportingEvidence());
        next.entry().outcome().ifPresent(refs::add); next.entry().issued().ifPresent(custody -> { refs.add(custody.record()); refs.add(custody.domainPayload()); refs.add(custody.event()); });
        return List.copyOf(new LinkedHashSet<>(refs));
    }
    private static byte[] input(String kind, Optional<ExactRef> record, Optional<ExactRef> seed, Optional<ExactRef> closed) {
        var row = StrictJson.object(); row.put("schema", INPUT_SCHEMA); row.put("kind", kind); row.set("record", record.map(ExactRef::toJson).orElse(null));
        row.set("seed_manifest", seed.map(ExactRef::toJson).orElse(null)); row.set("closed_scope", closed.map(ExactRef::toJson).orElse(null)); return StrictJson.canonical(row, MAX_BODY_BYTES);
    }
    private static ExactRef event(WriterContracts.Head head, long sequence) {
        String name = String.format(java.util.Locale.ROOT, "%08d.json", sequence);
        List<ExactRef> actual = head.documents().stream().map(WriterContracts.Pin::reference).filter(ref -> {
            Path path = Path.of(ref.path()); return path.getFileName().toString().equals(name) && path.getParent() != null
                    && path.getParent().getFileName().toString().equals("ROOT-CONTINUITY-WINDOW-EVENTS");
        }).toList(); StrictJson.require(actual.size() == 1, "exact actual immutable continuation event pin required"); return actual.getFirst();
    }
}
