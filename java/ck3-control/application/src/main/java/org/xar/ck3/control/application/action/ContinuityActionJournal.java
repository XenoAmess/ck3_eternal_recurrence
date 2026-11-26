package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Application adapter over the same canonical writer/lock. It owns neither a second file nor a writer process. */
public final class ContinuityActionJournal implements ActionJournal {
    public static final String KIND = WriterContracts.ACTION_LIFECYCLE_KIND;
    public static final String STATE_FIELD = WriterContracts.ACTION_LIFECYCLE_FIELD;
    private final ContinuityStorePort store;
    private final ActionPorts.OutcomeArchive archive;
    private final ThreadLocal<LockedJournal> current = new ThreadLocal<>();
    public ContinuityActionJournal(ContinuityStorePort store, ActionPorts.OutcomeArchive archive) {
        this.store = java.util.Objects.requireNonNull(store); this.archive = java.util.Objects.requireNonNull(archive);
    }
    @Override public <T> T locked(Function<LockedJournal, T> operation) {
        LockedJournal inherited = current.get(); if (inherited != null) return operation.apply(inherited);
        try { return store.locked(session -> locked(session, operation)); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    /** Borrow the actual Root session; archive binding checks the exact writer lock before any observation. */
    @Override public <T> T locked(ContinuityStorePort.Session session, Function<LockedJournal, T> operation) {
        java.util.Objects.requireNonNull(session); java.util.Objects.requireNonNull(operation);
        LockedJournal inherited = current.get();
        if (inherited != null) {
            StrictJson.require(inherited.writerSession() == session, "cannot replace the active original writer session");
            inherited.head(); return operation.apply(inherited);
        }
        return this.archive.inSession(session, bound -> {
            final ActionPorts.OutcomeArchive archive = bound;
            LockedJournal view = new LockedJournal() {
            private Snapshot retainedSnapshot;
            private ContinuityState cachedReceiptsState;
            private List<ActionReceipt> cachedReceiptsList;
            @Override public ContinuityStorePort.Session writerSession() { try { session.head(); return session; } catch (IOException failure) { throw new UncheckedIOException(failure); } }
            @Override public Optional<ActionReceipt> find(String actionId) {
                try { return cachedReceipts(session.head()).stream().filter(receipt -> receipt.command().actionId().equals(actionId)).findFirst(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public Optional<ActionState.IntentAbandoned> abandonableIntent(ActionReceipt original) {
                try { return IntentAbandonmentProof.capture(session.head().state(), original, archive); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public List<ActionReceipt> unresolved() {
                try { return cachedReceipts(session.head()).stream().filter(receipt -> !receipt.settled()).toList(); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public List<ActionReceipt> blockingUnresolved(ActionCommand command) {
                if (command.origin() instanceof CommandOrigin.Frontend) return unresolved();
                try {
                    var head = session.head();
                    return ContinuityActionJournal.blockingUnresolved(session, head, archive, command.origin().machineId(),
                            command.origin().game(), command.sessionId(), cachedReceipts(head));
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public ActionReceipt append(ActionCommand command, String bodySha256, ActionState next) {
                boolean traceSubmitting = next instanceof ActionState.Submitting;
                long appendStarted = traceSubmitting ? System.nanoTime() : 0L;
                long appendValidated = 0L, appendMaterials = 0L, appendPreviewed = 0L, appendCommitted = 0L, appendHistory = 0L, appendSelected = 0L;
                int appendPhase = 0;
                try {
                    var head = session.head();
                    List<ActionReceipt> prior = cachedReceipts(head);
                    ProtocolIdentityAdmission.requireUnique(prior, command);
                    ActionTransitions.validate(prior.stream().filter(value -> value.command().actionId().equals(command.actionId())).findFirst(),
                            command, bodySha256, next);
                    if (traceSubmitting) { appendValidated = System.nanoTime(); appendPhase = 1; }
                    if (next instanceof PhysicalActionState physical) PhysicalActionCodec.preserve(physical, archive);
                    ActionTransitions.attempt(next).ifPresent(attempt -> archive.preserveRequest(attempt.preparedRequest()));
                    ActionTransitions.dispatch(next).ifPresent(archive::preserve);
                    if (next instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed sent) {
                        archive.preserveRead(sent.observation().beforeStorage()); archive.preserveRead(sent.observation().afterStorage());
                    }
                    if (next instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied control) { archive.preserveRead(control.read()); control.supportingReads().forEach(archive::preserveRead); control.reconciledAck().ifPresent(value -> archive.preserve(value.ack())); }
                    if (next instanceof ActionState.CompositeSettled settled) {
                        ActionEffects.validateCompositeChildren(command, settled.execution(), settled.settlement(),
                                compositeChildren(head.state(), settled.execution().children(), archive));
                        if (settled.settlement() instanceof ActionState.CompositeControlApplied control) {
                            archive.preserveRead(control.observation().terminalStatus()); control.observation().supportingReads().forEach(archive::preserveRead);
                        }
                    }
                    ActionReceipt candidate = new ActionReceipt(1, Math.addExact(head.state().sequence(), 1), command, bodySha256, next);
                    ActionRecord record = new ActionRecord(candidate, recordHead(head.state()));
                    ActionPorts.PreservedActionRecord preserved = archive instanceof ActionPorts.ActionRecordPublicationArchive publication
                            ? publication.preserveRecordWithReceipt(record)
                            : new ActionPorts.PreservedActionRecord(archive.preserveReceipt(candidate), archive.preserveRecord(record));
                    var receiptRef = preserved.receiptReference();
                    var recordRef = preserved.recordReference();
                    ObjectNode details = StrictJson.object(); details.put("evidence_id", command.actionId() + ":" + candidate.sequence());
                    details.set("source", ProposalLifecycleCodec.source(command.source()));
                    details.set("receipt_ref", recordRef.toJson());
                    List<org.xar.ck3.control.contracts.ExactRef> evidence = new ArrayList<>();
                    evidence.add(recordRef); evidence.add(receiptRef); record.previous().ifPresent(evidence::add);
                    if (next instanceof PhysicalActionState physical) evidence.addAll(PhysicalActionCodec.references(physical, archive));
                    ActionTransitions.attempt(next).ifPresent(attempt -> { evidence.add(attempt.guard().nativeEvidence()); evidence.add(attempt.guard().capabilityEvidence()); evidence.addAll(attempt.guard().supportingEvidence()); evidence.add(archive.requestReferenceOf(attempt.preparedRequest())); evidence.addAll(attempt.preparedRequest().preparationEvidence()); });
                    ActionTransitions.composite(next).ifPresent(execution -> { evidence.add(execution.guard().nativeEvidence()); evidence.add(execution.guard().capabilityEvidence()); evidence.addAll(execution.guard().supportingEvidence()); });
                    ActionTransitions.dispatch(next).ifPresent(dispatch -> evidence.add(archive.referenceOf(dispatch)));
                    if (next instanceof ActionState.Settled settled) {
                        if (settled.settlement() instanceof ActionState.FamilySendConfirmed sent) evidence.addAll(sent.observation().references(archive));
                        if (settled.settlement() instanceof ActionState.Applied applied) { evidence.add(applied.observation().originalEvidence()); evidence.addAll(org.xar.ck3.control.application.effects.NativeEffectEvidence.reconciliationReferences(applied.observation(), archive)); }
                        else if (settled.settlement() instanceof ActionState.Rejected rejected) evidence.add(rejected.originalEvidence());
                        else if (settled.settlement() instanceof ActionState.ControlApplied control) { evidence.add(archive.readReferenceOf(control.read())); control.supportingReads().forEach(read -> evidence.add(archive.readReferenceOf(read))); control.reconciledAck().ifPresent(value -> evidence.add(value.reference(archive))); }
                        evidence.addAll(ActionEffects.supportingEvidence(settled.settlement()));
                    }
                    if (next instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.Applied applied) { evidence.add(applied.observation().originalEvidence()); evidence.addAll(org.xar.ck3.control.application.effects.NativeEffectEvidence.reconciliationReferences(applied.observation(), archive)); }
                    if (next instanceof ActionState.CompositeSettled settled) {
                        evidence.addAll(ActionEffects.supportingEvidence(settled.settlement()));
                        if (settled.settlement() instanceof ActionState.CompositeControlApplied control) {
                            evidence.add(control.observation().semantic().originalEvidence());
                            evidence.add(archive.readReferenceOf(control.observation().terminalStatus()));
                            control.observation().supportingReads().forEach(read -> evidence.add(archive.readReferenceOf(read)));
                        }
                    }
                    // Retain raw-only recovery originals as actual event pins, without treating packet bytes as JSON materials.
                    if (next instanceof ActionState.IntentAbandoned abandoned) {
                        evidence.add(abandoned.originalIntentRecord()); evidence.add(abandoned.originalActionHead());
                    }
                    if(next instanceof PreparedCleanupAction prepared)evidence.addAll(PreparedCleanupActionCodec.references(prepared,archive));
                     if(next instanceof ActionState.ReservedPreparedCleanupNoEffectConfirmed terminal){
                         evidence.add(terminal.preparationReference());evidence.add(terminal.proofReference());
                     }
                    if(next instanceof ActionState.PreparedCleanupNoEffectConfirmed terminal){
                        evidence.addAll(PreparedCleanupActionCodec.references(terminal.originalPreparedState(),archive));
                        evidence.add(terminal.proofReference());
                    }
                    if(next instanceof ActionState.CleanupNoEffectConfirmed terminal)evidence.add(terminal.proofReference());
                    if (next instanceof ActionState.CompositeOperatorQuarantined quarantined) evidence.add(quarantined.observationRef());
                    if (next instanceof ActionState.Unknown unknown) evidence.addAll(unknown.evidence());
                    if (next instanceof ActionState.CompositeUnknown unknown) evidence.addAll(unknown.evidence());
                    WriterContracts.Request request = new WriterContracts.Request(KIND, ContinuityJson.canonical(details), evidence.stream().distinct().toList());
                    if (traceSubmitting) { appendMaterials = System.nanoTime(); appendPhase = 2; }
                    var prepared = session.preview(request);
                    if (traceSubmitting) { appendPreviewed = System.nanoTime(); appendPhase = 3; }
                    var committed = session.commit(prepared);
                    if (traceSubmitting) { appendCommitted = System.nanoTime(); appendPhase = 4; }
                    var committedState = committed.head();
                    var history = historical(committedState, archive);
                    if (traceSubmitting) { appendHistory = System.nanoTime(); appendPhase = 5; }
                    var target = history.stream().filter(item -> item.receipt().command().actionId().equals(command.actionId())).findFirst().orElseThrow();
                    var latest = new java.util.LinkedHashMap<String, ActionReceipt>();
                    for (var item : history) latest.putIfAbsent(item.receipt().command().actionId(), item.receipt());
                    var complete = List.copyOf(latest.values());
                    cachedReceiptsList = complete;
                    cachedReceiptsState = committedState;
                    if (traceSubmitting) { appendSelected = System.nanoTime(); appendPhase = 6; }
                    return target.receipt();
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
                finally {
                    if (traceSubmitting) {
                        try {
                            long appendEnded = System.nanoTime();
                            // Never clear a caller's interrupt or invoke diagnostic IO on an already interrupted thread.
                            if (!Thread.currentThread().isInterrupted()) {
                                String id = command.actionId(); id = id.substring(0, Math.min(128, id.length())).replaceAll("[^A-Za-z0-9_.:-]", "_");
                                System.err.println("ACTION_APPEND_PHASE action=" + id + " thread=" + Thread.currentThread().threadId()
                                        + " phase=" + appendPhase + " event_ns=" + appendEnded
                                        + " elapsed_ns=" + Math.max(0L, appendEnded - appendStarted)
                                        + " validation_ns=" + (appendPhase >= 1 ? Math.max(0L, appendValidated - appendStarted) : -1L)
                                        + " materials_ns=" + (appendPhase >= 2 ? Math.max(0L, appendMaterials - appendValidated) : -1L)
                                        + " preview_ns=" + (appendPhase >= 3 ? Math.max(0L, appendPreviewed - appendMaterials) : -1L)
                                        + " commit_ns=" + (appendPhase >= 4 ? Math.max(0L, appendCommitted - appendPreviewed) : -1L)
                                        + " history_ns=" + (appendPhase >= 5 ? Math.max(0L, appendHistory - appendCommitted) : -1L)
                                        + " selection_ns=" + (appendPhase >= 6 ? Math.max(0L, appendSelected - appendHistory) : -1L)
                                        + " returned=" + (appendPhase == 6));
                            }
                        } catch (Throwable diagnosticUnavailable) { /* Diagnostic output never controls the original append outcome. */ }
                    }
                }
            }
            @Override public Snapshot snapshot() {
                try {
                    var head = session.head();
                    if (retainedSnapshot != null && retainedSnapshot.ledgerSequence() == head.state().sequence()
                            && retainedSnapshot.headSha256().equals(head.digest())) return retainedSnapshot;
                    ObjectNode state = head.state().toJson(); LegacyHistoryBasis basis;
                    if (!state.has("java_driver_history_baseline")) basis = new MissingHistoryBasis();
                    else if (state.get("java_driver_history_baseline").isNull()) basis = new NullHistoryBasis();
                    else basis = new BoundHistoryBasis(org.xar.ck3.control.contracts.ExactRef.fromJson(state.get("java_driver_history_baseline")));
                    Snapshot complete = new Snapshot(head.state().sequence(), head.digest(), cachedReceipts(head), basis);
                    retainedSnapshot = complete; return complete;
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            private List<ActionReceipt> cachedReceipts(WriterContracts.Head head) throws IOException {
                if (cachedReceiptsState != null && cachedReceiptsState.sequence() == head.state().sequence()
                        && ContinuityJson.digest(cachedReceiptsState.toJson()).equals(head.digest())) return cachedReceiptsList;
                List<ActionReceipt> complete = receipts(head.state(), archive);
                cachedReceiptsList = complete; cachedReceiptsState = head.state(); return complete;
            }
        };
        current.set(view); try { return operation.apply(view); } finally { current.remove(); }
        });
    }
    /** Live borrowing is available only inside this journal's explicit original-session callback. */
    public ContinuityStorePort.Session borrowedWriterSession() {
        LockedJournal active = current.get();
        StrictJson.require(active != null, "no live original writer session is borrowed"); return active.writerSession();
    }
    /** One fresh complete canonical DATA snapshot for a multi-child selection, never the prior callback cache. */
    private static List<ActionReceipt> compositeChildren(ContinuityState state, List<CompositeExecution.Child> children,
            ActionPorts.OutcomeArchive archive) {
        if (children.size() < 2) return children.stream()
                .map(child -> lookup(state, child.actionId(), archive).orElseThrow()).toList();
        var latest = new java.util.HashMap<String, ActionReceipt>();
        for (Historical item : historical(state, archive))
            latest.putIfAbsent(item.receipt().command().actionId(), item.receipt());
        return children.stream().map(child -> Optional.ofNullable(latest.get(child.actionId())).orElseThrow()).toList();
    }
    /** Read-only canonical projection. A state object alone grants no writer or submit qualification. */
    public static Optional<ActionReceipt> lookup(ContinuityState state, String actionId, ActionPorts.OutcomeArchive archive) {
        for (Historical item : historical(state, archive)) if (item.receipt().command().actionId().equals(actionId)) return java.util.Optional.of(item.receipt());
        return java.util.Optional.empty();
    }
    /**
     * Current-action eligibility under the original writer. Only the exact retained child of
     * an exited Life, bound by the canonical imported restore, can cease to block a new owner.
     * The canonical receipt still remains UNKNOWN and the retired IDs remain non-dispatchable.
     */
    public static List<ActionReceipt> blockingUnresolved(ContinuityStorePort.Session same, WriterContracts.Head head,
            ActionPorts.OutcomeArchive archive, SessionIdentity owner, List<ActionReceipt> canonical) throws IOException {
        return blockingUnresolved(same, head, archive, owner.machineId(), owner.game(), owner.sessionId(), canonical);
    }

    private static List<ActionReceipt> blockingUnresolved(ContinuityStorePort.Session same, WriterContracts.Head head,
            ActionPorts.OutcomeArchive archive, String machineId, GameGeneration game, String sessionId,
            List<ActionReceipt> canonical) throws IOException {
        var unresolved = canonical.stream().filter(receipt -> !receipt.settled()).toList();
        if (unresolved.isEmpty()) return unresolved;
        var whole = head.state().toJson();
        String importedOrigin = WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD;
        if (!whole.has(importedOrigin) || !whole.hasNonNull(WriterContracts.ORDINARY_CYCLE_FIELD)
                || !head.state().machineId().equals(machineId)
                || !ContinuityJson.same(whole.get("game_binding"), game.toJson())) return unresolved;
        var owner = OrdinaryCycleTransitions.sessionFromJson(whole.get(WriterContracts.ORDINARY_CYCLE_FIELD).get("session"));
        if (!owner.machineId().equals(machineId) || !owner.game().equals(game) || !owner.sessionId().equals(sessionId)) return unresolved;
        StrictJson.require(same.head().digest().equals(head.digest()), "current action eligibility requires its original locked head");
        var exact = importedRetiredResume(ExactRef.fromJson(whole.get(importedOrigin)), archive, owner, canonical, unresolved);
        StrictJson.require(same.head().digest().equals(head.digest()), "current action eligibility changed its original locked head");
        return exact.map(old -> unresolved.stream().filter(receipt -> !receipt.equals(old)).toList()).orElse(unresolved);
    }

    private static Optional<ActionReceipt> importedRetiredResume(ExactRef tombstoneRef, ActionPorts.OutcomeArchive archive,
            SessionIdentity owner, List<ActionReceipt> canonical, List<ActionReceipt> unresolved) {
        var tombstone = StrictJson.object(ContinuityJson.parseObject(archive.loadMaterial(tombstoneRef).bytes(),
                ContinuityJson.DOCUMENT_MAX_BYTES), Set.of("schema", "attachment_identity", "restored_session", "restore_pair",
                        "retained_legacy_pending_digest", WriterContracts.ORDINARY_CYCLE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                        WriterContracts.ORDINARY_CYCLE_REBIND_FIELD, "original_action_head"));
        StrictJson.require(StrictJson.text(tombstone.get("schema")).equals("xar.java-ordinary-cycle-restore-tombstone/v2"),
                "imported action eligibility requires the original restore tombstone");
        var restored = OrdinaryCycleTransitions.sessionFromJson(tombstone.get("restored_session"));
        var priorCycle = StrictJson.object(tombstone.get(WriterContracts.ORDINARY_CYCLE_FIELD), Set.of("present", "value"));
        StrictJson.require(priorCycle.get("present").isBoolean() && priorCycle.get("present").booleanValue(),
                "imported action eligibility requires the original interrupted cycle");
        var departed = OrdinaryCycleTransitions.sessionFromJson(priorCycle.get("value").get("session"));
        if (owner.game().equals(departed.game())) return Optional.empty();
        var oldPair = CheckpointPairCodec.decode(ContinuityJson.canonical(tombstone.get("restore_pair")));
        StrictJson.require(owner.machineId().equals(restored.machineId()) && owner.machineId().equals(departed.machineId())
                && !restored.game().equals(departed.game()) && !restored.game().equals(oldPair.frame().game()),
                "imported action eligibility crossed the original restore owners");

        var retiredRecord = archive.loadRecord(ExactRef.fromJson(tombstone.get("original_action_head")));
        var retired = retiredRecord.receipt();
        StrictJson.require(canonical.contains(retired) && retired.state() instanceof ActionState.CompositeOperatorQuarantined
                && retired.command().origin() instanceof CommandOrigin.Gameplay && retired.command().origin().game().equals(departed.game())
                && retired.command().sessionId().equals(departed.sessionId()), "imported action eligibility lost the exact canonical exited Life terminal");
        var proof = CompositeOperatorQuarantineObservation.load(retired, archive);
        var request = CompositeOperatorQuarantineRequest.decode(archive.loadMaterial(proof.requestMaterial()).bytes());
        var exit = request.exitedLife().orElseThrow();
        var original = archive.loadReceipt(proof.originalReceipt());
        request.requireParent(original);
        StrictJson.require(request.originalReceipt().equals(proof.originalReceipt())
                && request.expectedHeadSequence() == proof.predecessorSequence() && request.expectedHeadDigest().equals(proof.predecessorDigest())
                && request.machineId().equals(departed.machineId()) && request.game().equals(departed.game())
                && exit.ownerSessionId().equals(departed.sessionId())
                && exit.savedPairSha256().equals(ActionCodec.sha256(CheckpointPairCodec.encode(oldPair)))
                && retiredRecord.previous().equals(Optional.of(proof.originalActionHead())),
                "imported action eligibility changed the canonical retirement predecessor or physical pair");
        var resume = request.children().getLast();
        var binding = ((ActionState.CompositeOperatorQuarantined) retired.state()).execution().children().getLast();
        StrictJson.require(resume.ordinal() == 2 && resume.actionId().equals(binding.actionId())
                && resume.bodySha256().equals(binding.bodySha256()), "imported action eligibility changed the retired RESUME reservation");
        return unresolved.stream().filter(receipt -> exactRetiredResume(receipt, original.command(), resume, original.sequence())).findFirst();
    }

    private static boolean exactRetiredResume(ActionReceipt receipt, ActionCommand parent,
            CompositeOperatorQuarantineRequest.Child resume, long parentSequence) {
        var child = receipt.command();
        return receipt.state() instanceof ActionState.Unknown && receipt.sequence() < parentSequence
                && child.operation().value().equals("resume-map") && child.arguments().members().isEmpty()
                && child.actionId().equals(resume.actionId()) && receipt.bodySha256().equals(resume.bodySha256())
                && child.actionId().equals(ActionIds.child(parent.actionId(), resume.ordinal(), child.operation()))
                && child.origin().equals(parent.origin()) && child.sessionId().equals(parent.sessionId())
                && child.source().equals(parent.source()) && child.deadline().equals(parent.deadline()) && child.claims().equals(parent.claims())
                && child.expected().equals(AdvancePrimitives.expected(child.before(), child.source(), child.operation(), child.arguments()))
                && receipt.ack().filter(NativeActionPort.AckReceived::nativeOk).isPresent();
    }

    public static List<ActionReceipt> receipts(ContinuityState state, ActionPorts.OutcomeArchive archive) {
        java.util.LinkedHashMap<String, ActionReceipt> latest = new java.util.LinkedHashMap<>();
        for (Historical item : historical(state, archive)) latest.putIfAbsent(item.receipt().command().actionId(), item.receipt());
        return List.copyOf(latest.values());
    }
    /** One complete fresh logical batch, not a cache or a caller-provided history authority.
     * The private full chain is produced at the original lookup boundary; each query keeps its own old checks.
     * Separate canonical calls and the historical WAL-prefix state still perform their independent full reads. */
    public static <T>T withCanonicalHistory(ContinuityState state,ActionPorts.OutcomeArchive archive,
            java.util.function.BiFunction<java.util.function.Function<String,Optional<ActionReceipt>>,
                    java.util.function.Function<ActionReceipt,org.xar.ck3.control.contracts.ExactRef>,java.util.concurrent.Callable<T>> work)
            throws java.io.IOException {
        java.util.Objects.requireNonNull(work);
        List<Historical> complete=historical(state,archive);
        Thread thread=Thread.currentThread();boolean[] open={true};
        java.util.function.Function<String,Optional<ActionReceipt>> lookup=actionId->{
            StrictJson.require(open[0]&&Thread.currentThread()==thread,"canonical history query escaped its source-owned thread/callback");
            for(Historical item:complete)if(item.receipt().command().actionId().equals(actionId))return Optional.of(item.receipt());
            return Optional.empty();
        };
        java.util.function.Function<ActionReceipt,org.xar.ck3.control.contracts.ExactRef> membership=exact->{
            StrictJson.require(open[0]&&Thread.currentThread()==thread,"canonical history query escaped its source-owned thread/callback");
            java.util.Objects.requireNonNull(exact);StrictJson.require(exact.sequence()<=state.sequence()
                    &&exact.command().origin().machineId().equals(state.machineId()),"historical receipt crossed actual writer machine/sequence");
            Historical actual=complete.stream().filter(item->item.receipt().sequence()==exact.sequence()).findFirst()
                    .orElseThrow(()->new IllegalArgumentException("receipt is not in the surviving canonical action record chain"));
            StrictJson.require(java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(exact,archive),ActionReceiptCodec.encodeReceipt(actual.receipt(),archive)),
                    "historical action record has another complete original receipt body");
            return actual.record();
        };
        try{return java.util.Objects.requireNonNull(work.apply(lookup,membership)).call();}
        catch(java.io.IOException|RuntimeException|Error failure){throw failure;}
        catch(Exception failure){
            if(failure instanceof InterruptedException)Thread.currentThread().interrupt();
            throw new java.io.IOException("canonical history batch raised an unsupported checked exception",failure);
        }finally{open[0]=false;}
    }

    /** Immutable original prefix from the same canonical chain; the caller supplies the actual locked Head state. */
    public static List<ActionReceipt> receiptsBeforeIntent(ContinuityState current, String originalActionId, ActionPorts.OutcomeArchive scoped) {
        StrictJson.text(originalActionId); java.util.Objects.requireNonNull(scoped);
        List<Historical> complete = historical(current, scoped);
        List<ActionReceipt> original = complete.stream().map(Historical::receipt)
                .filter(value -> value.command().actionId().equals(originalActionId)).toList();
        StrictJson.require(!original.isEmpty(), "original action is absent from the actual surviving chain");
        String body = original.getFirst().bodySha256();
        StrictJson.require(original.stream().allMatch(value -> value.bodySha256().equals(body)), "original action body changed in canonical history");
        List<ActionReceipt> intents = original.stream().filter(value -> value.state() instanceof ActionState.IntentDurable).toList();
        StrictJson.require(intents.size() == 1, "one original durable INTENT required for historical admission");
        long boundary = intents.getFirst().sequence();
        java.util.LinkedHashMap<String, ActionReceipt> prior = new java.util.LinkedHashMap<>();
        for (Historical item : complete) if (item.receipt().sequence() < boundary)
            prior.putIfAbsent(item.receipt().command().actionId(), item.receipt());
        return List.copyOf(prior.values());
    }
    /** Verifies current lookup and historical membership from one fresh walk where the exact older head is a suffix.
     * Callers must supply the actual canonical predecessor under the writer's original historical edge scope. */
    public static Optional<ActionReceipt> lookupWithHistoricalMembership(ContinuityState current,
            ContinuityState predecessor, String actionId, ActionPorts.OutcomeArchive archive) {
        var complete = historical(current, archive);
        var selected = complete.stream().filter(item -> item.receipt().command().actionId().equals(actionId)).findFirst();
        if (selected.isEmpty()) return Optional.empty();
        var target = selected.orElseThrow();
        var exact = target.receipt();
        requireHistoricalReceiptIdentity(predecessor, exact);
        var olderHead = recordHead(predecessor);
        int from = -1;
        for (int i = 0; i < complete.size(); i++) {
            var item = complete.get(i);
            if (olderHead.isPresent() && item.record().equals(olderHead.orElseThrow())) {
                StrictJson.require(item.receipt().sequence() <= predecessor.sequence(),
                        "action record chain sequence/machine drift");
                from = i;
                break;
            }
        }
        if (from == -1) {
            // The earlier canonical edge may record an independently valid ancestry. Verify it as before.
            requireHistoricalReceipt(predecessor, exact, archive);
        } else {
            var actual = complete.subList(from, complete.size()).stream()
                    .filter(item -> item.receipt().sequence() == exact.sequence()).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("receipt is not in the surviving canonical action record chain"));
            requireSameHistoricalReceipt(exact, actual, archive);
        }
        return Optional.of(exact);
    }

    /** Membership in the actual canonical action chain, not just an independently stored receipt with matching bytes. */
    public static org.xar.ck3.control.contracts.ExactRef requireHistoricalReceipt(ContinuityState state, ActionReceipt exact, ActionPorts.OutcomeArchive archive) {
        requireHistoricalReceiptIdentity(state, exact);
        List<Historical> complete = historical(state, archive);
        Historical actual = complete.stream().filter(item -> item.receipt().sequence() == exact.sequence()).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("receipt is not in the surviving canonical action record chain"));
        requireSameHistoricalReceipt(exact, actual, archive);
        return actual.record();
    }

    private static void requireHistoricalReceiptIdentity(ContinuityState state, ActionReceipt exact) {
        java.util.Objects.requireNonNull(exact);
        StrictJson.require(exact.sequence() <= state.sequence() && exact.command().origin().machineId().equals(state.machineId()),
                "historical receipt crossed actual writer machine/sequence");
    }

    private static void requireSameHistoricalReceipt(ActionReceipt exact, Historical actual, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(exact, archive),
                ActionReceiptCodec.encodeReceipt(actual.receipt(), archive)),
                "historical action record has another complete original receipt body");
    }
    /** Fresh batch DATA validation. Each original record is decoded once in this invocation, never cached across calls. */
    public static List<org.xar.ck3.control.contracts.ExactRef> requireHistoricalReceipts(ContinuityState state,
            List<ActionReceipt> exacts, ActionPorts.OutcomeArchive archive) {
        var checked = List.copyOf(exacts);
        StrictJson.require(checked.size() <= 100_000, "bounded historical receipt batch required");
        if (checked.isEmpty()) return List.of();
        for (var exact : checked) StrictJson.require(exact.sequence() <= state.sequence()
                && exact.command().origin().machineId().equals(state.machineId()),
                "historical receipt crossed actual writer machine/sequence");
        var complete = historical(state, archive);
        var bySequence = new java.util.HashMap<Long, Historical>();
        for (var item : complete) StrictJson.require(bySequence.put(item.receipt().sequence(), item) == null,
                "canonical action chain repeated a receipt sequence");
        var result = new ArrayList<org.xar.ck3.control.contracts.ExactRef>(checked.size());
        for (var exact : checked) {
            var actual = bySequence.get(exact.sequence());
            StrictJson.require(actual != null, "receipt is not in the surviving canonical action record chain");
            StrictJson.require(java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(exact, archive),
                    ActionReceiptCodec.encodeReceipt(actual.receipt(), archive)),
                    "historical action record has another complete original receipt body");
            result.add(actual.record());
        }
        return List.copyOf(result);
    }
    private record Historical(org.xar.ck3.control.contracts.ExactRef record, ActionReceipt receipt) { }
    private static List<Historical> historical(ContinuityState state, ActionPorts.OutcomeArchive archive) {
        List<Historical> history = new ArrayList<>();
        java.util.HashSet<org.xar.ck3.control.contracts.ExactRef> seen = new java.util.HashSet<>();
        Optional<org.xar.ck3.control.contracts.ExactRef> cursor = recordHead(state); long maximumSequence = state.sequence();
        while (cursor.isPresent()) {
            var ref = cursor.orElseThrow(); StrictJson.require(seen.add(ref) && seen.size() <= 100_000, "action record chain is cyclic or exceeds explicit bounded read budget");
            ActionRecord record = archive.loadRecord(ref); ActionReceipt receipt = record.receipt();
            StrictJson.require(receipt.sequence() <= maximumSequence && receipt.command().origin().machineId().equals(state.machineId()), "action record chain sequence/machine drift");
            maximumSequence = receipt.sequence() - 1; history.add(new Historical(ref, receipt)); cursor = record.previous();
        }
        return List.copyOf(history);
    }
    public static Optional<org.xar.ck3.control.contracts.ExactRef> recordHead(ContinuityState state) {
        ObjectNode row = state.toJson(); if (!row.has(STATE_FIELD)) return Optional.empty();
        StrictJson.require(!row.get(STATE_FIELD).isNull(), "action record head cannot silently change from missing to null");
        return Optional.of(org.xar.ck3.control.contracts.ExactRef.fromJson(row.get(STATE_FIELD)));
    }
}


