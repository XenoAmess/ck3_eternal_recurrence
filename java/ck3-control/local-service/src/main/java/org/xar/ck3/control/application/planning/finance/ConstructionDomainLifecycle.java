package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncomeJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;

/** One owning body producer. The registry exists before Core; its exact writer/archive link is once bound afterwards. */
public final class ConstructionDomainLifecycle {
    public static final String SCHEMA = "xar.construction-domain-transition/v3";
    public static final int MAX_BYTES = ConstructionLedgerCodec.MAX_BYTES;
    public static final int MAX_INPUT_BYTES = org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES;
    public enum Kind { FRESH, RESTORE, NEXT_EPISODE, INTENT, OUTCOME, MATERIAL, PREPARED_ZERO_DISPATCH }
    public record Publication(Head predecessor, WriterContracts.Receipt receipt) {
        public Publication { Objects.requireNonNull(predecessor); Objects.requireNonNull(receipt); }
        public OrdinaryPlanCompletion.Published completion() { return new OrdinaryPlanCompletion.Published(predecessor, receipt); }
    }
    /** The concrete Root owner binds the actual original-proof producer once for this Core. */
    public interface OriginalBodyProducer {
        OriginalBody replay(ContinuityStorePort.Session same, Head actualHead, Kind kind, Obj input,
                Optional<ConstructionLedgerCodec.Ledger> previous) throws IOException;
    }
    public record OriginalBody(Obj body, List<ExactRef> evidence) {
        public OriginalBody { Objects.requireNonNull(body); evidence = List.copyOf(evidence); require(evidence.size() < 64, "finite complete original proof closure required"); }
    }
    private ConstructionDomainLifecycle() { }
    public static Prepared prepare(List<ExactRef> completeActualProducerClosure, ExactRef actualObserverSource) {
        return new Prepared(completeActualProducerClosure, actualObserverSource);
    }
    public static final class Prepared implements DomainBodies.Verifier {
        private final DomainBodies.Registration registration;
        private final ExactRef observerSource;
        private Bound bound;
        private OriginalBodyProducer originals;
        private ExactRef originalsSource;
        public synchronized Optional<OriginalBodyProducer> originals() { return Optional.ofNullable(originals); }
        public synchronized void bindOriginals(ExactRef source, OriginalBodyProducer actual) {
            Objects.requireNonNull(source); Objects.requireNonNull(actual);
            require(registration.producerSources().contains(source) && !actual.getClass().isSynthetic() && !actual.getClass().isAnonymousClass(),
                    "actual named original-proof producer must belong to the complete selected construction source closure");
            require(originals == null || originals == actual && originalsSource.equals(source), "construction original-proof authority is once bound");
            originals = actual; originalsSource = source;
        }
        private synchronized OriginalBodyProducer originalProducer() throws IOException {
            if (originals == null) throw new IOException("actual fresh/restore construction original-proof producer is not bound");
            return originals;
        }
        private Prepared(List<ExactRef> sources, ExactRef observerSource) {
            this.observerSource = Objects.requireNonNull(observerSource);
            require(observerSource.bytes() > 0, "actual construction observer source required");
            registration = new DomainBodies.Registration(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA, MAX_BYTES, sources, this);
            require(registration.producerSources().contains(observerSource), "construction lifecycle observer is outside the actual complete producer closure");
        }
        public DomainBodies.Registration registration() { return registration; }
        public synchronized void bindCore(ContinuityWriter writer, NativeOutcomeArchive archive,
                NativeEffectEvidence.FrameLoader frames, FinanceReadContracts definitions) {
            Objects.requireNonNull(writer); Objects.requireNonNull(archive); Objects.requireNonNull(frames); Objects.requireNonNull(definitions);
            ReadContract<?> soleConstructionQuery = definitions.contract(FinanceReadContracts.Query.CONSTRUCTION);
            require(archive.writer() == writer && soleConstructionQuery.operation().equals(NativeConstructionEffects.QUERY), "same Core writer/archive and unique construction query required");
            if (bound != null) {
                require(bound.writer == writer && bound.archive == archive && bound.frames == frames
                        && bound.query.contractId().equals(soleConstructionQuery.contractId()) && bound.query.sourceRef().equals(soleConstructionQuery.sourceRef()),
                        "construction domain registry cannot be rebound to another Core/source");
                for (FinanceReadContracts.Query query : List.of(FinanceReadContracts.Query.ROOT, FinanceReadContracts.Query.CASH)) {
                    ReadContract<?> original = bound.definitions.contract(query), replacement = definitions.contract(query);
                    require(original.contractId().equals(replacement.contractId()) && original.sourceRef().equals(replacement.sourceRef()),
                            "construction material cannot rebind a Root/cash producer within an existing Core");
                }
                return;
            }
            bound = new Bound(writer, archive, frames, definitions, soleConstructionQuery);
        }
        private synchronized Bound required() throws IOException {
            if (bound == null) throw new IOException("actual construction Core binding is not installed"); return bound;
        }
        public ConstructionLedgerCodec.Ledger read(ContinuityStorePort.Session session) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            var read = session.readDomain(DomainBodies.Slot.CONSTRUCTION);
            if (!(read instanceof DomainBodies.Available known)) throw new IOException("original construction domain body unavailable: " + read);
            return ConstructionLedgerCodec.decodeLedger(known.canonicalBody());
        }
        /** Only the actual Root original-proof producer can derive a fresh or restored full body. */
        public Publication publishOriginal(ContinuityStorePort.Session session, Kind kind, Obj input, List<ExactRef> evidence) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            require(kind == Kind.FRESH || kind == Kind.RESTORE || kind == Kind.NEXT_EPISODE, "private original-proof import cannot use a live mutation kind");
            Optional<ConstructionLedgerCodec.Ledger> previous = Optional.empty();
            var existing = session.readDomain(DomainBodies.Slot.CONSTRUCTION);
            if (existing instanceof DomainBodies.Available known) previous = Optional.of(ConstructionLedgerCodec.decodeLedger(known.canonicalBody()));
            else require(existing instanceof DomainBodies.Unavailable unavailable && unavailable.reason() == DomainBodies.Reason.UNIMPORTED,
                    "original import requires exact current body or actual UNIMPORTED, not an unavailable identity/source");
            OriginalBody replayed = originalProducer().replay(session, session.head(), kind, input, previous);
            require(replayed.evidence().equals(List.copyOf(evidence)), "construction original producer evidence differs");
            Obj details = obj("schema", new Text(SCHEMA), "kind", new Text(kind.name()), "original_input", input);
            return publish(session, details, replayed.body(), replayed.evidence(),
                    "construction-original:" + kind.name() + ":" + ActionCodec.sha256(encode(input)));
        }
        /** Called only by the coordinator's actual same-session pre-INTENT hook, after its actual final cash/material revalidation. */
        public void prepareIntent(ContinuityStorePort.Session session, ActionCommand command) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent(), "construction pending publication requires the sole active coordinator scope");
            ConstructionFundingEvidence.command(command);
            var archive = actual.archive.withSession(session);
            ExactRef original = actual.archive.preserveArtifact(session, ActionCodec.encodeCommand(command), ActionCodec.MAX_COMMAND_BYTES);
            Obj details = obj("schema", new Text(SCHEMA), "kind", new Text(Kind.INTENT.name()), "command_ref", ref(original));
            Obj body = intent(read(session), command);
            publish(session, details, body, List.of(original), "construction-intent:" + command.actionId());
        }
        /** Applied, zero-dispatch rejection and UNKNOWN all consume the real surviving canonical coordinator receipt. */
        public Optional<Publication> synchronizeOutcome(ContinuityStorePort.Session session, ActionReceipt received) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            if (!received.command().operation().equals(OrdinaryConstructionPolicy.OPERATION)) return Optional.empty();
            var archive = actual.archive.withSession(session); var canonical = canonical(session.head(), received, archive);
            var ledger = read(session);
            if (ledger.pending().isEmpty()) {
                if (ledger.receipts(canonical.command().before().frame().episodeRunId()).stream().anyMatch(row -> row.identity().actionRequestId().equals(RequestIds.forActionBody(canonical.bodySha256())))) return Optional.empty();
                if (ledger.original().get("last_rejected_coordinator_receipt") instanceof Obj ref
                        && archive.receiptReferenceOf(canonical).equals(exactRef(ref))) return Optional.empty();
                throw new IOException("construction canonical outcome has no matching original pending body");
            }
            ExactRef original = archive.receiptReferenceOf(canonical);
            Obj details = obj("schema", new Text(SCHEMA), "kind", new Text(Kind.OUTCOME.name()), "receipt_ref", ref(original));
            Obj body = outcome(session.head(), ledger, canonical, actual, session);
            if (body.equals(ledger.original())) return Optional.empty();
            return Optional.of(publish(session, details, body, List.of(original), "construction-outcome:" + canonical.command().actionId() + ":" + canonical.sequence()));
        }
        public Publication publishMaterial(ContinuityStorePort.Session session, ConstructionLedgerCodec.Ledger previous,
                ConstructionMaterialReducer.RefreshKind kind, String actionId, OrdinaryConstructionCollector.MaterialAvailable material) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            require(Objects.requireNonNull(kind) != ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH,
                    "ordinary material publication cannot enter prepared zero-dispatch recovery");
            require(read(session).original().equals(previous.original()), "construction body changed before original material publication");
            Obj input = ConstructionMaterialReducer.input(kind, previous, actionId, material.queryInput(), material.root(), material.cash());
            var archive = actual.archive.withSession(session);
            List<ExactRef> reads = material.originalReads().stream().map(archive::readReferenceOf).toList();
            var source = ConstructionMaterialSource.preserve(session, actual.archive, input);
            Obj details = obj("schema", new Text(SCHEMA), "kind", new Text(Kind.MATERIAL.name()), "material_source", source.toJson(),
                    "read_refs", new Arr(reads.stream().<Value>map(ConstructionDomainLifecycle::ref).toList()));
            Obj body = material(session.head(), details, actual, session);
            List<ExactRef> evidence = new ArrayList<>(reads); evidence.add(source.input());
            return publish(session, details, body, evidence, "construction-material:" + actionId + ":" + text(material.queryInput().get("native_query_request_id"), "query identity"));
        }
        /** A failed pre-INTENT journal publication is a distinct zero-dispatch branch, never a legacy UNKNOWN retry. */
        public Optional<Publication> recoverPreparedWithoutIntent(ContinuityStorePort.Session session, PlanningRequest request,
                OrdinaryConstructionCollector.MaterialAvailable material) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session); var ledger = read(session);
            if (!recoverablePreparedHead(session.head(), ledger, actual.archive.withSession(session))) return Optional.empty();
            var pending = ledger.pending().orElseThrow();
            Obj reducerInput = ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH, ledger, pending.identity().actionRequestId(), material.queryInput(), material.root(), material.cash());
            var archive = actual.archive.withSession(session); var refs = material.originalReads().stream().map(archive::readReferenceOf).toList();
            var source = ConstructionMaterialSource.preserve(session, actual.archive, reducerInput);
            Obj details = obj("schema", new Text(SCHEMA), "kind", new Text(Kind.PREPARED_ZERO_DISPATCH.name()), "material_source", source.toJson(),
                    "read_refs", new Arr(refs.stream().<Value>map(ConstructionDomainLifecycle::ref).toList()));
            var input = materialInput(session.head(), details, actual, session);
            Optional<Obj> body = preparedZeroDispatchBody(input.ledger(), input.queryObservation());
            if (body.isEmpty()) return Optional.empty();
            List<ExactRef> evidence = new ArrayList<>(refs); evidence.add(source.input());
            return Optional.of(publish(session, details, source.retainIn(body.orElseThrow()), evidence, "construction-zero-dispatch:" + pending.coordinatorActionId().orElseThrow()));
        }
        public boolean hasRecoverablePreparedHead(ContinuityStorePort.Session session) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session);
            return recoverablePreparedHead(session.head(), read(session), actual.archive.withSession(session));
        }
        private Publication publish(ContinuityStorePort.Session session, Obj input, Obj body, List<ExactRef> evidence, String id) throws IOException {
            Bound actual = required(); actual.writer.requireSession(session); Head head = session.head();
            byte[] rawInput = encode(input), rawBody = canonicalBody(body);
            DriverJson.object(rawInput, MAX_INPUT_BYTES); ConstructionLedgerCodec.validateLedger(rawBody);
            ExactRef archivedInput = actual.archive.preserveArtifact(session, rawInput, MAX_INPUT_BYTES);
            ExactRef archivedBody = actual.archive.preserveArtifact(session, rawBody, MAX_BYTES);
            List<ExactRef> all = new ArrayList<>(evidence); all.add(archivedInput);
            var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA, archivedBody, rawInput, all, id);
            var prepared = session.previewImport(request); var receipt = session.commitImport(prepared);
            var readback = session.readDomain(DomainBodies.Slot.CONSTRUCTION);
            require(readback instanceof DomainBodies.Available && Arrays.equals(((DomainBodies.Available) readback).canonicalBody(), rawBody), "construction committed body did not read back exactly");
            return new Publication(head, receipt);
        }
        static byte[] canonicalBody(Obj body) {
            return org.xar.ck3.control.continuity.ContinuityJson.canonical(org.xar.ck3.control.continuity.ContinuityJson.parseObject(encode(body), MAX_BYTES), MAX_BYTES);
        }
        @Override public String verify(ContinuityState head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) throws IOException {
            throw new IOException("construction lifecycle requires the actual full locked writer Head");
        }
        @Override public String verify(Head head, Optional<DomainBodies.BodyRef> previous, DomainBodies.ImportRequest request, byte[] body) throws IOException {
            Bound actual = required(); var session = actual.writer.borrowedSession(); actual.writer.requireSession(session);
            require(head.digest().equals(session.head().digest()), "construction verifier is not consuming its current original writer Head");
            require(request.slot() == DomainBodies.Slot.CONSTRUCTION && request.contractSchema().equals(ConstructionLedgerCodec.SCHEMA), "exact construction domain contract required");
            Obj details = DriverJson.object(request.producerInput(), MAX_INPUT_BYTES);
            require(new Text(SCHEMA).equals(details.get("schema")), "construction lifecycle input schema required");
            Kind kind;
            try { kind = Kind.valueOf(text(details.get("kind"), "construction lifecycle kind")); }
            catch (IllegalArgumentException failure) { throw new IOException("unknown construction lifecycle kind", failure); }
            Obj expected;
            if (kind == Kind.FRESH || kind == Kind.RESTORE || kind == Kind.NEXT_EPISODE) {
                require(details.members().keySet().equals(Set.of("schema", "kind", "original_input")), "exact original-proof input required");
                Optional<ConstructionLedgerCodec.Ledger> current = previous.isEmpty() ? Optional.empty()
                        : Optional.of(ConstructionLedgerCodec.decodeLedger(actual.archive.readArtifact(session, previous.orElseThrow().payload(), MAX_BYTES)));
                OriginalBody replayed = originalProducer().replay(session, head, kind, object(details.get("original_input"), "actual original proof input"), current);
                require(request.evidence().containsAll(replayed.evidence()), "actual original proof evidence omitted from writer request");
                expected = replayed.body();
            } else {
                require(previous.isPresent(), "construction mutation requires its actual original body");
                var original = ConstructionLedgerCodec.decodeLedger(actual.archive.readArtifact(session, previous.orElseThrow().payload(), MAX_BYTES));
                expected = switch (kind) {
                    case INTENT -> {
                        require(details.members().keySet().equals(Set.of("schema", "kind", "command_ref")), "exact original intent fields required");
                        ExactRef reference = exactRef(details.get("command_ref"));
                        ActionCommand command = ActionCodec.decodeCommand(actual.archive.readArtifact(session, reference, ActionCodec.MAX_COMMAND_BYTES));
                        require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent(), "pending body publication lost its actual coordinator scope");
                        ConstructionFundingEvidence.command(command);
                        require(ContinuityActionJournal.lookup(head.state(), command.actionId(), actual.archive.withSession(session)).isEmpty(), "pending producer cannot replace an already durable command");
                        require(request.evidence().contains(reference), "pending command original is absent from evidence");
                        yield intent(original, command);
                    }
                    case OUTCOME -> {
                        require(details.members().keySet().equals(Set.of("schema", "kind", "receipt_ref")), "exact outcome fields required");
                        var archive = actual.archive.withSession(session); ExactRef reference = exactRef(details.get("receipt_ref"));
                        ActionReceipt receipt = canonical(head, archive.loadReceipt(reference), archive);
                        require(archive.receiptReferenceOf(receipt).equals(reference) && request.evidence().contains(reference), "outcome original archive identity drift");
                        yield outcome(head, original, receipt, actual, session);
                    }
                    case MATERIAL -> {
                        for (Value value : array(details.get("read_refs"), "actual material evidence refs")) require(request.evidence().contains(exactRef(value)), "material read omitted from complete writer evidence");
                        var source = materialSource(details);
                        require(request.evidence().contains(source.input()), "complete material input omitted from writer evidence");
                        var input = materialInput(head, details, actual, session);
                        require(input.ledger().original().equals(original.original()), "material reducer predecessor differs from current original body");
                        yield source.retainIn(ConstructionMaterialReducer.reduce(input).originalBody());
                    }
                    case PREPARED_ZERO_DISPATCH -> {
                        for (Value value : array(details.get("read_refs"), "actual zero-dispatch evidence refs")) require(request.evidence().contains(exactRef(value)), "zero-dispatch read omitted from complete writer evidence");
                        require(recoverablePreparedHead(head, original, actual.archive.withSession(session)), "zero-dispatch recovery cannot clear an actual canonical or legacy UNKNOWN action");
                        var source = materialSource(details);
                        require(request.evidence().contains(source.input()), "zero-dispatch complete input omitted from writer evidence");
                        var input = materialInput(head, details, actual, session);
                        require(input.ledger().original().equals(original.original()), "zero-dispatch reducer predecessor changed");
                        yield source.retainIn(preparedZeroDispatchBody(original, input.queryObservation()).orElseThrow(() -> new IOException("actual native project/wallet do not prove the prepared command unapplied")));
                    }
                    case FRESH, RESTORE, NEXT_EPISODE -> throw new IOException("original-proof transition cannot enter a live mutation branch");
                };
            }
            require(Arrays.equals(body, encode(expected)), "construction body differs from its actual owning lifecycle reducer");
            return ActionCodec.sha256(encode(obj("input_sha256", new Text(ActionCodec.sha256(request.producerInput())), "body_sha256", new Text(ActionCodec.sha256(body)))));
        }
        private Obj outcome(Head head, ConstructionLedgerCodec.Ledger ledger, ActionReceipt receipt, Bound actual, ContinuityStorePort.Session session) throws IOException {
            require(receipt.command().operation().equals(OrdinaryConstructionPolicy.OPERATION), "canonical outcome is not construction");
            var pending = ledger.pending().orElseThrow(() -> new IOException("canonical construction outcome requires its original pending intent"));
            require(new Text(receipt.command().actionId()).equals(pending.original().get("coordinator_action_id"))
                    && new Text(receipt.bodySha256()).equals(pending.original().get("coordinator_body_sha256"))
                    && pending.identity().actionRequestId().equals(RequestIds.forActionBody(receipt.bodySha256())), "construction pending/canonical command identity drift");
            var archive = actual.archive.withSession(session);
            if (receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Applied) {
                NativeConstructionEffects.archivedVerifier(OrdinaryConstructionPolicy.OPERATION, observerSource, actual.frames, actual.query).verifier().verify(head, receipt, archive);
                var original = NativeEffectEvidence.load(receipt, archive, actual.frames);
                Obj material = DriverJson.object(original.compatibleResult().bytes(), 262_144);
                Obj confirmed = ConstructionMaterialReducer.confirmedStart(pending, material, original.frames().after().semantic());
                List<Value> prior = new ArrayList<>(ledger.prior().stream().<Value>map(ConstructionLedgerCodec.Receipt::original).toList());
                ledger.applied().filter(row -> !row.completed() || row.economy().postGross().isEmpty()).ifPresent(row -> prior.add(row.original()));
                return ledger.original().with("pending", Nil.INSTANCE).with("applied", confirmed).with("applied_prior", new Arr(prior));
            }
            if (receipt.state() instanceof ActionState.RejectedBeforeDispatch
                    || receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected) {
                return ledger.original().with("pending", Nil.INSTANCE).with("last_rejected_coordinator_receipt", ref(archive.receiptReferenceOf(receipt)));
            }
            return ledger.original().with("pending", pending.original().with("status", new Text("action_state_unknown"))
                    .with("java_original_coordinator_receipt", ref(archive.receiptReferenceOf(receipt))));
        }
        private Obj material(Head head, Obj details, Bound actual, ContinuityStorePort.Session session) throws IOException {
            var input = materialInput(head, details, actual, session);
            return materialSource(details).retainIn(ConstructionMaterialReducer.reduce(input).originalBody());
        }
        private ConstructionMaterialReducer.Input materialInput(Head head, Obj details, Bound actual, ContinuityStorePort.Session session) throws IOException {
            var decoded = materialSource(details).load(session, actual.archive);
            if (decoded.version() == ConstructionMaterialReducer.InputVersion.REFRESH_V2) {
                var kind = decoded.refreshKind().orElseThrow();
                require(new Text(Kind.MATERIAL.name()).equals(details.get("kind"))
                                && kind != ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH
                        || new Text(Kind.PREPARED_ZERO_DISPATCH.name()).equals(details.get("kind"))
                                && kind == ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH,
                        "material transition differs from its original refresh kind");
            }
            var archive = actual.archive.withSession(session); List<PlanningReadReceipt> reads = new ArrayList<>();
            for (Value value : array(details.get("read_refs"), "actual immutable material read refs")) {
                ExactRef reference = exactRef(value); var read = archive.loadRead(reference);
                require(archive.readReferenceOf(read).equals(reference), "material read immutable identity changed"); reads.add(read);
            }
            new ConstructionSnapshotVerifier(archive, actual.frames).verify(head, object(decoded.queryObservation().get("starting_snapshot"), "original native/Driver snapshot"), reads);
            var material = reads.stream().filter(read -> read.request().operation().equals(NativeConstructionEffects.QUERY)).toList();
            require(material.size() == 1 && material.getFirst().contractId().equals(actual.query.contractId())
                    && new Text(material.getFirst().requestId()).equals(decoded.queryObservation().get("native_query_request_id"))
                    && DriverJson.object(material.getFirst().original().originalFrame().bytes(), 262_144).equals(decoded.queryObservation().get("native_envelope")), "material projection is not the exact original single registered Native query");
            actual.query.decode(material.getFirst());
            // Optional root/cash are accepted only through the same current registered reads; the owning raw normalizer is reused.
            verifyOptionalMaterial(decoded, reads, actual.definitions);
            return decoded;
        }
    }
    private static ConstructionMaterialSource materialSource(Obj details) {
        require(details.members().keySet().equals(Set.of("schema", "kind", "material_source", "read_refs")), "exact referenced material transition fields required");
        return ConstructionMaterialSource.decode(object(details.get("material_source"), "complete original material source"));
    }
    static Obj intent(ConstructionLedgerCodec.Ledger ledger, ActionCommand command) {
        require(command.operation().equals(OrdinaryConstructionPolicy.OPERATION) && ledger.pending().isEmpty(), "exact construction action and original clear body required");
        // Historical four-field commands retain their original schema. Every newly installed dispatch requires the fifth source field.
        Optional<CanonicalFundingPending.SourceEvidence> funding = command.arguments().members().containsKey(ConstructionFundingEvidence.FIELD)
                ? Optional.of(ConstructionFundingEvidence.command(command)) : Optional.empty();
        var original = new OrdinaryWartimeConstructionCodec.ObservedRequest(encode(object(command.arguments().get("ordinary_cash_request"), "original quoted actual cash input")));
        var assessment = OrdinaryWartimeConstruction.compose(original.input());
        require(assessment.disposition() == OrdinaryWartimeConstruction.Disposition.QUOTED_CANDIDATE, "pending construction requires the original qualified quoted outlay");
        Obj request = DriverJson.object(original.original(), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        Obj query = object(object(request.get("quoted_outlay"), "original outlay").get("query_observation"), "actual original Native query");
        Obj finalized = DriverJson.object(ConstructionQueryCodec.finalizeObservation(encode(query)), ConstructionQueryCodec.MAX_BYTES);
        Obj before = object(query.get("starting_snapshot"), "original complete frame"), source = object(finalized.get("source_frame"), "actual quote source");
        var f = command.before().frame();
        require(source.get("snapshot_id").equals(new Text(f.snapshotId())) && source.get("revision").equals(new IntegerValue(f.revision()))
                && source.get("native_revision").equals(new IntegerValue(f.identity().nativeRevision())) && source.get("date_raw").equals(new IntegerValue(f.identity().dateRaw()))
                && source.get("episode_run_id").equals(new Text(f.episodeRunId())) && source.get("actor_character_id").equals(new IntegerValue(f.identity().player())), "pending action/quote frame drift");
        require(finalized.get("candidate").equals(command.arguments().get("candidate")) && finalized.get("proof_epoch").equals(command.arguments().get("pre_proof_epoch"))
                && NativeConstructionEffects.expected(command.before(), command.source(), command.arguments()).equals(command.expected()), "pending full candidate/material expectation drift");
        Obj diagnostic = object(before.get("diagnostics"), "actual original Game diagnostics");
        Obj province = DriverJson.object(ConstructionProvinceIncomeJson.project(encode(obj("schema", new Text(ConstructionProvinceIncomeJson.SCHEMA),
                "operation", new Text("observe"), "world", finalized.get("world"), "candidate", finalized.get("candidate"), "source_frame", source))), 262_144);
        Obj cashInput = object(request.get("cash_input"), "actual original cash input"), root = object(cashInput.get("root"), "actual source-bound income root");
        Value income = Nil.INSTANCE;
        if (root.get("player_character_id").equals(source.get("actor_character_id")) && root.get("snapshot_revision").equals(source.get("native_revision")) && root.get("date_raw").equals(source.get("date_raw"))
                && root.get("player_monthly_gold_income") instanceof Obj value && new IntegerValue(java.math.BigInteger.valueOf(100000)).equals(value.get("scale"))) {
            Value raw = value.get("raw"); if (raw instanceof IntegerValue) income = raw;
        }
        Obj pending = obj("status", new Text("java_intent_prepared"), "action_request_id", new Text(RequestIds.forActionBody(ActionCodec.bodySha256(command))),
                "coordinator_action_id", new Text(command.actionId()), "coordinator_body_sha256", new Text(ActionCodec.bodySha256(command)),
                "episode_run_id", new Text(f.episodeRunId()), "actor_character_id", new IntegerValue(f.identity().player()),
                "pre_native_revision", new IntegerValue(f.identity().nativeRevision()), "pre_public_revision", new IntegerValue(f.revision()),
                "pre_date_raw", new IntegerValue(f.identity().dateRaw()), "pre_proof_epoch", finalized.get("proof_epoch"),
                "source_bridge_pid", diagnostic.get("bridge_pid"), "source_bridge_creation_date", diagnostic.get("bridge_creation_date"),
                "pre_player_monthly_gold_income_raw", income, "pre_province_income_observation", province, "candidate", finalized.get("candidate"),
                "pre_cash_v2", object(object(request.get("quoted_outlay"), "actual outlay").get("cash_observation"), "actual cash").get("cash"));
        // Persist the same prepared cash packet and monthly scenarios used by the quoted-outlay gate.
        // The material reducer carries the original intent into its independently verified receipt.
        var preparedCash = assessment.monthly().flatMap(value -> value.prepared());
        if (preparedCash.isPresent()) {
            Obj fields = DriverJson.object(ConstructionEconomyCodec.encodePrepared(preparedCash.orElseThrow()), ConstructionEconomyCodec.MAX_BYTES);
            pending = pending.with("pre_cash_v2", fields.get("pre_cash_v2"))
                    .with("construction_monthly_budget", fields.get("construction_monthly_budget"));
        }
        if (funding.isPresent()) pending = pending.with(ConstructionFundingEvidence.FIELD, CanonicalFundingPending.evidenceJson(funding.orElseThrow()));
        ConstructionLedgerCodec.intent(pending); return ledger.original().with("pending", pending);
    }

    private static boolean recoverablePreparedHead(Head head, ConstructionLedgerCodec.Ledger ledger, ActionPorts.OutcomeArchive archive) {
        if (ledger.pending().isEmpty() || ActionScope.currentActionId().isPresent()) return false;
        var pending = ledger.pending().orElseThrow();
        if (!new Text("java_intent_prepared").equals(pending.original().get("status")) || pending.coordinatorActionId().isEmpty()) return false;
        if (ContinuityActionJournal.lookup(head.state(), pending.coordinatorActionId().orElseThrow(), archive).isPresent()) return false;
        return ContinuityActionJournal.receipts(head.state(), archive).stream().allMatch(ActionReceipt::settled);
    }
    /** Pure actual native finalizer -> zero-dispatch material reducer; the owning verifier separately proves canonical INTENT absence. */
    public static Optional<Obj> preparedZeroDispatchBody(ConstructionLedgerCodec.Ledger ledger, Obj originalQuery) {
        var pending = ledger.pending().orElseThrow(() -> new IllegalArgumentException("original prepared construction required"));
        require(new Text("java_intent_prepared").equals(pending.original().get("status")) && pending.coordinatorActionId().isPresent(), "legacy UNKNOWN is not a prepared zero-dispatch command");
        require(!pending.original().members().containsKey("native_ack") && !pending.original().members().containsKey("native_submit_result")
                && !pending.original().members().containsKey("java_original_coordinator_receipt"), "prepared zero-dispatch cannot clear retained dispatch evidence");
        require(new Bool(true).equals(originalQuery.get("material_receipt")), "zero-dispatch requires an actual independent material query");
        Obj query = DriverJson.object(ConstructionQueryCodec.finalizeObservation(encode(originalQuery)), ConstructionQueryCodec.MAX_BYTES);
        require(new Text("material_source").equals(query.get("status")), "zero-dispatch actual native material source unavailable");
        Obj frame = object(query.get("source_frame"), "actual recovery frame"), world = object(query.get("world"), "actual project inventory");
        require(new Text(pending.identity().episode()).equals(frame.get("episode_run_id")) && new IntegerValue(pending.identity().actor()).equals(frame.get("actor_character_id")), "prepared recovery crossed its original episode/player");
        Obj candidate = object(pending.original().get("candidate"), "original construction candidate");
        if (!frame.get("date_raw").equals(pending.original().get("pre_date_raw"))
                || !world.get("player_gold_raw").equals(candidate.get("gold_before_raw")) || !new Bool(true).equals(world.get("completed_buildings_observed"))) return Optional.empty();
        List<Obj> holding = new ArrayList<>();
        for (Value value : array(world.get("active_constructions"), "actual target holding projection")) {
            Obj row = object(value, "actual target holding row");
            if (Objects.equals(row.get("barony_title_id"), candidate.get("barony_title_id")) && Objects.equals(row.get("province_id"), candidate.get("province_id"))) holding.add(row);
        }
        if (holding.size() != 1 || !new Bool(false).equals(holding.getFirst().get("active"))) return Optional.empty();
        for (Value value : array(world.get("completed_buildings"), "actual completed inventory")) {
            Obj row = object(value, "actual completed row"); boolean same = true;
            for (String field : List.of("barony_title_id", "province_id", "building_type_id", "slot_index")) {
                integer(row.get(field), "actual completed " + field); same &= Objects.equals(row.get(field), candidate.get(field));
            }
            if (same) return Optional.empty();
        }
        Obj proof = obj("status", new Text("not_submitted_before_intent"), "coordinator_action_id", new Text(pending.coordinatorActionId().orElseThrow()),
                "action_request_id", new Text(pending.identity().actionRequestId()), "original_pending", pending.original(), "source_frame", frame,
                "native_query_request_id", query.get("native_query_request_id"), "native_submit_calls", new IntegerValue(java.math.BigInteger.ZERO),
                "replay_allowed", new Bool(false), "requested_postcondition_verified", new Bool(false));
        return Optional.of(ledger.original().with("pending", Nil.INSTANCE).with("last_pre_intent_zero_dispatch", proof));
    }
    private static void verifyOptionalMaterial(ConstructionMaterialReducer.Input input, List<PlanningReadReceipt> reads, FinanceReadContracts definitions) {
        List<PlanningReadReceipt> roots = reads.stream().filter(read -> read.request().operation().equals(FinanceReadContracts.Query.ROOT.operation())).toList();
        List<PlanningReadReceipt> cash = reads.stream().filter(read -> read.request().operation().equals(FinanceReadContracts.Query.CASH.operation())).toList();
        require(roots.size() <= 1 && cash.size() <= 1 && reads.size() == 1 + roots.size() + cash.size(), "duplicate/unrelated construction material evidence");
        for (PlanningReadReceipt read : roots) {
            require(read.contractId().equals(definitions.contract(FinanceReadContracts.Query.ROOT).contractId()), "material root differs from the sole Root source contract");
            definitions.contract(FinanceReadContracts.Query.ROOT).decode(read);
        }
        for (PlanningReadReceipt read : cash) {
            require(read.contractId().equals(definitions.contract(FinanceReadContracts.Query.CASH).contractId()), "material cash differs from the sole Root source contract");
            definitions.contract(FinanceReadContracts.Query.CASH).decode(read);
        }
        Optional<Obj> root = roots.stream().findFirst().flatMap(read -> {
            Obj value = DriverJson.object(read.original().originalResultToken().orElseThrow().bytes(), 262_144);
            return new Text("available").equals(value.get("status")) ? Optional.of(object(value.get("campaign_root_context"), "actual root")) : Optional.empty();
        });
        require(root.equals(input.root()), "material income differs from actual archived root read");
        Optional<Obj> normalized = cash.stream().findFirst().map(read -> {
            Obj value = DriverJson.object(read.original().originalResultToken().orElseThrow().bytes(), 262_144);
            Obj raw = object(value.get("war_cash_current_resources"), "actual native cash");
            Obj result = object(parse(org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.normalize(encode(raw), encode(object(input.queryObservation().get("starting_snapshot"), "starting snapshot"))).toJson()), "actual normalized cash");
            var frame = read.request().before().frame(); return result.with("queried_snapshot_id", new Text(frame.snapshotId()))
                    .with("queried_revision", new IntegerValue(frame.revision())).with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision()));
        });
        require(normalized.equals(input.cash()), "material cash differs from actual archived raw cash producer");
    }
    private static ActionReceipt canonical(Head head, ActionReceipt receipt, ActionPorts.OutcomeArchive archive) throws IOException {
        var actual = ContinuityActionJournal.lookup(head.state(), receipt.command().actionId(), archive).orElseThrow(() -> new IOException("construction receipt absent from actual surviving canonical action chain"));
        require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt, archive), ActionReceiptCodec.encodeReceipt(actual, archive)), "construction receipt is not the actual canonical coordinator outcome"); return actual;
    }
    private static Obj ref(ExactRef value) { return object(parse(StrictJson.canonical(value.toJson())), "original exact reference"); }
    private static ExactRef exactRef(Value value) { return ExactRef.fromJson(StrictJson.parse(encode(object(value, "exact original reference")))); }
    private record Bound(ContinuityWriter writer, NativeOutcomeArchive archive, NativeEffectEvidence.FrameLoader frames, FinanceReadContracts definitions, ReadContract<?> query) { }
}
