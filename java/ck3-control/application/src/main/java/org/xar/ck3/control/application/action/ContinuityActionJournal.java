package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
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
            @Override public ContinuityStorePort.Session writerSession() { try { session.head(); return session; } catch (IOException failure) { throw new UncheckedIOException(failure); } }
            @Override public Optional<ActionReceipt> find(String actionId) {
                try { return lookup(session.head().state(), actionId, archive); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public List<ActionReceipt> unresolved() {
                try { return receipts(session.head().state(), archive).stream().filter(receipt -> !receipt.settled()).toList(); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public ActionReceipt append(ActionCommand command, String bodySha256, ActionState next) {
                try {
                    var head = session.head();
                    List<ActionReceipt> prior = receipts(head.state(), archive);
                    ProtocolIdentityAdmission.requireUnique(prior, command);
                    ActionTransitions.validate(prior.stream().filter(value -> value.command().actionId().equals(command.actionId())).findFirst(),
                            command, bodySha256, next);
                    if (next instanceof PhysicalActionState physical) PhysicalActionCodec.preserve(physical, archive);
                    ActionTransitions.attempt(next).ifPresent(attempt -> archive.preserveRequest(attempt.preparedRequest()));
                    ActionTransitions.dispatch(next).ifPresent(archive::preserve);
                    if (next instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed sent) {
                        archive.preserveRead(sent.observation().beforeStorage()); archive.preserveRead(sent.observation().afterStorage());
                    }
                    if (next instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied control) { archive.preserveRead(control.read()); control.supportingReads().forEach(archive::preserveRead); control.reconciledAck().ifPresent(value -> archive.preserve(value.ack())); }
                    if (next instanceof ActionState.CompositeSettled settled) {
                        ActionEffects.validateCompositeChildren(settled.execution(), settled.settlement(), settled.execution().children().stream()
                                .map(child -> lookup(head.state(), child.actionId(), archive).orElseThrow()).toList());
                        if (settled.settlement() instanceof ActionState.CompositeControlApplied control) {
                            archive.preserveRead(control.observation().terminalStatus()); control.observation().supportingReads().forEach(archive::preserveRead);
                        }
                    }
                    ActionReceipt candidate = new ActionReceipt(1, Math.addExact(head.state().sequence(), 1), command, bodySha256, next);
                    var receiptRef = archive.preserveReceipt(candidate);
                    ActionRecord record = new ActionRecord(candidate, recordHead(head.state()));
                    var recordRef = archive.preserveRecord(record);
                    ObjectNode details = StrictJson.object(); details.put("evidence_id", command.actionId() + ":" + candidate.sequence());
                    details.set("source", ProposalLifecycleCodec.source(command.source()));
                    details.set("receipt_ref", recordRef.toJson());
                    List<org.xar.ck3.control.contracts.ExactRef> evidence = new ArrayList<>(); evidence.add(command.source().sourceRef());
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
                    if (next instanceof ActionState.Unknown unknown) evidence.addAll(unknown.evidence());
                    if (next instanceof ActionState.CompositeUnknown unknown) evidence.addAll(unknown.evidence());
                    WriterContracts.Request request = new WriterContracts.Request(KIND, ContinuityJson.canonical(details), evidence.stream().distinct().toList());
                    var committed = session.commit(session.preview(request));
                    return lookup(committed.head(), command.actionId(), archive).orElseThrow();
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public Snapshot snapshot() {
                try {
                    var head = session.head(); ObjectNode state = head.state().toJson(); LegacyHistoryBasis basis;
                    if (!state.has("java_driver_history_baseline")) basis = new MissingHistoryBasis();
                    else if (state.get("java_driver_history_baseline").isNull()) basis = new NullHistoryBasis();
                    else basis = new BoundHistoryBasis(org.xar.ck3.control.contracts.ExactRef.fromJson(state.get("java_driver_history_baseline")));
                    return new Snapshot(head.state().sequence(), head.digest(), receipts(head.state(), archive), basis);
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
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
    /** Read-only canonical projection. A state object alone grants no writer or submit qualification. */
    public static Optional<ActionReceipt> lookup(ContinuityState state, String actionId, ActionPorts.OutcomeArchive archive) {
        return receipts(state, archive).stream().filter(receipt -> receipt.command().actionId().equals(actionId)).findFirst();
    }
    public static List<ActionReceipt> receipts(ContinuityState state, ActionPorts.OutcomeArchive archive) {
        java.util.LinkedHashMap<String, ActionReceipt> latest = new java.util.LinkedHashMap<>();
        for (Historical item : historical(state, archive)) latest.putIfAbsent(item.receipt().command().actionId(), item.receipt());
        return List.copyOf(latest.values());
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
    /** Membership in the actual canonical action chain, not just an independently stored receipt with matching bytes. */
    public static org.xar.ck3.control.contracts.ExactRef requireHistoricalReceipt(ContinuityState state, ActionReceipt exact, ActionPorts.OutcomeArchive archive) {
        java.util.Objects.requireNonNull(exact); StrictJson.require(exact.sequence() <= state.sequence()
                && exact.command().origin().machineId().equals(state.machineId()), "historical receipt crossed actual writer machine/sequence");
        List<Historical> complete = historical(state, archive);
        Historical actual = complete.stream().filter(item -> item.receipt().sequence() == exact.sequence()).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("receipt is not in the surviving canonical action record chain"));
        StrictJson.require(java.util.Arrays.equals(ActionReceiptCodec.encodeReceipt(exact, archive), ActionReceiptCodec.encodeReceipt(actual.receipt(), archive)),
                "historical action record has another complete original receipt body");
        return actual.record();
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


