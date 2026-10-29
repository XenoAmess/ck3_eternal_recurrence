package org.xar.ck3.control.wave2.finance.giftpendingroute;

import java.io.IOException;
import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serial;
import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.time.Duration;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import java.util.function.Supplier;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ExistingCheckpointPort;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ProcessObservation;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecoveryCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Recovery;
import org.xar.ck3.control.wave2.finance.giftpending.GiftColdRecovery.Result;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.AppliedReceipt;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Envelope;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Snapshot;

/** Actual receipt/cold consumers of pending reducers, on existing read and original writer ports only. */
public final class GiftPendingReadRoute {
    public static final Duration TIMEOUT = Duration.ofSeconds(30);
    private GiftPendingReadRoute() { }
    public enum Step {
        RECEIPT("private-query-faction-gift-receipt-v1"), COLD("private-query-faction-gift-cold-recovery-v1");
        private final String wire;
        Step(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record QueryId(String value) {
        public QueryId {
            if (value == null || !value.matches("faction-gift-[0-9a-f]{32}")) { throw new IllegalArgumentException("original private read identity required"); }
        }
    }
    public record Frame(Snapshot snapshot, Read<String> episodeRunId) {
        public Frame { Objects.requireNonNull(snapshot); Objects.requireNonNull(episodeRunId); }
    }
    public record Command(QueryId requestId, Step step, BigInteger expectedRevision, BigInteger expectedDateRaw,
            BigInteger expectedPlayerCharacterId, Optional<BigInteger> sourceFactionId, Optional<BigInteger> recipientCharacterId) {
        public Command {
            Objects.requireNonNull(requestId); Objects.requireNonNull(step); GiftPendingModel.positive(expectedRevision);
            GiftPendingModel.nonnegative(expectedDateRaw); GiftPendingModel.positive(expectedPlayerCharacterId);
            Objects.requireNonNull(sourceFactionId); Objects.requireNonNull(recipientCharacterId);
            if ((step == Step.COLD) != sourceFactionId.isPresent() || (step == Step.COLD) != recipientCharacterId.isPresent()) {
                throw new IllegalArgumentException("only cold read carries exact original faction/recipient identities");
            }
            sourceFactionId.ifPresent(GiftPendingModel::positive); recipientCharacterId.ifPresent(GiftPendingModel::positive);
        }
    }
    public record Change<T>(Ledger candidate, T material) {
        public Change { Objects.requireNonNull(candidate); Objects.requireNonNull(material); }
    }
    public record Commit<T>(Ledger ledger, T material) {
        public Commit { Objects.requireNonNull(ledger); Objects.requireNonNull(material); }
    }
    public interface OriginalWriterPort {
        /** Invoke once under the existing writer lock using its current ledger; persist/return that candidate only.
         * An identical candidate must not rewrite the file. This port does not establish runtime writer qualification.
         */
        <T> Commit<T> applyUnderOriginalWriterLock(Function<Ledger, Change<T>> transition);
    }
    public interface ExistingOwnedReadPort {
        ProcessObservation observeCurrentProcess(PendingAction pending);
        Frame takeInternalSemanticSnapshot();
        void sendOriginalRead(Command command);
        Optional<Envelope> waitForOriginalCommandResult(QueryId queryId, Duration timeout);
        Read<String> currentPrivateRoundId();
        ExistingCheckpointPort originalCheckpointReader();
        OriginalWriterPort originalPendingWriter();
        void recordOriginalCommand(Step step, boolean ok, ObjectEvidence result, Optional<String> error);
    }
    public record ReceiptResult(ObjectEvidence originalResult, Ledger pendingLedger) {
        public ReceiptResult { Objects.requireNonNull(originalResult); Objects.requireNonNull(pendingLedger); }
    }
    public record ColdResult(ObjectEvidence originalResult, Recovery recovery, Result classification, Ledger ledger) {
        public ColdResult { Objects.requireNonNull(originalResult); Objects.requireNonNull(recovery); Objects.requireNonNull(classification); Objects.requireNonNull(ledger); }
    }
    public static final class RouteFailure extends IllegalStateException {
        @Serial private static final long serialVersionUID = 1L;
        public RouteFailure(String message) { super(message); }
    }
    public static final class ColdUnresolved extends IllegalStateException {
        @Serial private static final long serialVersionUID = 1L;
        // Serializable text uses the existing JSON contracts; domain records and Optional are not Java-serializable.
        private final String originalResultJson;
        private final String recoveryJson;
        private final GiftColdRecovery.Reason unresolvedReason;
        private final String ledgerJson;
        ColdUnresolved(ColdResult result) {
            super("cold faction recovery remains materially unresolved");
            Objects.requireNonNull(result);
            if (!(result.classification() instanceof GiftColdRecovery.Unresolved unresolved)) {
                throw new IllegalArgumentException("cold unresolved exception requires unresolved material");
            }
            originalResultJson = result.originalResult().json();
            recoveryJson = GiftPendingReadRouteCodec.encodeRecoveryJson(result.recovery());
            unresolvedReason = unresolved.reason();
            ledgerJson = new String(GiftPendingCodec.encodeLedger(result.ledger()), StandardCharsets.UTF_8);
        }
        public ColdResult result() {
            return new ColdResult(new ObjectEvidence(originalResultJson),
                    GiftColdRecoveryCodec.decodeRecovery(recoveryJson.getBytes(StandardCharsets.UTF_8)),
                    new GiftColdRecovery.Unresolved(unresolvedReason),
                    GiftPendingCodec.decodeLedger(ledgerJson.getBytes(StandardCharsets.UTF_8)));
        }
        @Serial private void readObject(ObjectInputStream input) throws IOException, ClassNotFoundException {
            input.defaultReadObject();
            try { result(); }
            catch (RuntimeException error) {
                InvalidObjectException invalid = new InvalidObjectException("invalid serialized cold unresolved result");
                invalid.initCause(error); throw invalid;
            }
        }
    }
    public static ReceiptResult queryReceipt(PendingAction pending, BigInteger expectedRevision, ExistingOwnedReadPort port) {
        return queryReceipt(pending, expectedRevision, port, GiftPendingReadRoute::newId);
    }
    public static ReceiptResult queryReceipt(PendingAction pending, BigInteger expectedRevision, ExistingOwnedReadPort port, Supplier<String> idFactory) {
        Objects.requireNonNull(pending); Objects.requireNonNull(port);
        if (!port.observeCurrentProcess(pending).sameProcess(pending)) { throw new RouteFailure("same-process faction receipt cannot cross CK3 process identity"); }
        Frame before = before(expectedRevision, port, "private faction receipt revision changed");
        ObjectEvidence result = send(pending, before, Step.RECEIPT, port, idFactory);
        AppliedReceipt receipt = GiftPendingReadRouteCodec.materialReceipt(result);
        Commit<AppliedReceipt> committed = apply(port.originalPendingWriter(), current ->
                new Change<>(GiftPendingReducer.complete(current, pending.requestId(), receipt), receipt));
        ReceiptResult projected = new ReceiptResult(result, committed.ledger());
        port.recordOriginalCommand(Step.RECEIPT, true, GiftPendingReadRouteCodec.receiptEvidence(projected), Optional.empty()); return projected;
    }
    public static ColdResult queryCold(PendingAction pending, BigInteger expectedRevision, ExistingOwnedReadPort port) {
        return queryCold(pending, expectedRevision, port, GiftPendingReadRoute::newId);
    }
    public static ColdResult queryCold(PendingAction pending, BigInteger expectedRevision, ExistingOwnedReadPort port, Supplier<String> idFactory) {
        Objects.requireNonNull(pending); Objects.requireNonNull(port);
        ProcessObservation process = Objects.requireNonNull(port.observeCurrentProcess(pending));
        if (process.sameProcess(pending)) { throw new RouteFailure("cold faction recovery requires a replaced CK3 process"); }
        Frame before = before(expectedRevision, port, "cold faction recovery revision changed");
        apply(port.originalPendingWriter(), current -> new Change<>(GiftPendingReducer.markRestore(current, pending.requestId()), Step.COLD));
        ObjectEvidence result = send(pending, before, Step.COLD, port, idFactory);
        var checkpoint = GiftRouteCoordinator.currentCheckpoint(before.snapshot(), before.episodeRunId(), port.originalCheckpointReader());
        Recovery recovery = GiftPendingReadRouteCodec.recovery(result, before, pending, process.current(), port.currentPrivateRoundId(), checkpoint);
        Commit<Result> committed = apply(port.originalPendingWriter(), current -> {
            var resolution = GiftColdRecovery.resolve(current, pending.requestId(), recovery);
            return new Change<>(resolution.ledger(), resolution.result());
        });
        ColdResult projected = new ColdResult(result, recovery, committed.material(), committed.ledger());
        boolean settled = !(projected.classification() instanceof GiftColdRecovery.Unresolved);
        port.recordOriginalCommand(Step.COLD, settled, GiftPendingReadRouteCodec.coldEvidence(projected),
                settled ? Optional.empty() : Optional.of("material_outcome_not_distinguishable"));
        if (!settled) { throw new ColdUnresolved(projected); } return projected;
    }
    private static Frame before(BigInteger expectedRevision, ExistingOwnedReadPort port, String message) {
        GiftPendingModel.positive(expectedRevision); Frame before = Objects.requireNonNull(port.takeInternalSemanticSnapshot());
        if (!equal(before.snapshot().binding().revision(), expectedRevision)) { throw new RouteFailure(message); } return before;
    }
    private static ObjectEvidence send(PendingAction pending, Frame before, Step step, ExistingOwnedReadPort port, Supplier<String> idFactory) {
        QueryId queryId = new QueryId(Objects.requireNonNull(idFactory).get()); var binding = before.snapshot().binding();
        if (!binding.nativeRevision().known() || !binding.dateRaw().known()) { throw new RouteFailure("private faction query frame is incomplete"); }
        Command command = new Command(queryId, step, binding.nativeRevision().value(), binding.dateRaw().value(), pending.baseline().playerCharacterId(),
                step == Step.COLD ? Optional.of(pending.baseline().sourceFactionId()) : Optional.empty(),
                step == Step.COLD ? Optional.of(pending.baseline().recipientCharacterId()) : Optional.empty());
        port.sendOriginalRead(command);
        Envelope frame = port.waitForOriginalCommandResult(queryId, TIMEOUT)
                .orElseThrow(() -> new RouteFailure(step.wire() + " command_result timed out"));
        if (!equal(frame.type(), "command_result") || !equal(frame.protocolVersion(), BigInteger.ONE)
                || !equal(frame.requestId(), queryId.value()) || !equal(frame.ok(), true) || !frame.result().known()) {
            String error = frame.error().known() && !frame.error().value().isEmpty() ? frame.error().value() : "malformed private command result";
            throw new RouteFailure(step.wire() + " failed: " + error);
        }
        return new ObjectEvidence(new String(frame.result().value().bytes(), java.nio.charset.StandardCharsets.UTF_8));
    }
    private static <T> Commit<T> apply(OriginalWriterPort writer, Function<Ledger, Change<T>> reducer) {
        AtomicInteger calls = new AtomicInteger(); AtomicReference<Change<T>> candidate = new AtomicReference<>();
        Commit<T> committed = Objects.requireNonNull(writer.applyUnderOriginalWriterLock(current -> {
            if (calls.incrementAndGet() != 1) { throw new RouteFailure("original writer attempted to replay a pending transition"); }
            Change<T> change = Objects.requireNonNull(reducer.apply(current)); candidate.set(change); return change;
        }));
        Change<T> actual = candidate.get();
        if (calls.get() != 1 || actual == null || !actual.candidate().equals(committed.ledger()) || !actual.material().equals(committed.material())) {
            throw new RouteFailure("original writer did not return the actual reducer candidate");
        }
        return committed;
    }
    private static String newId() { return "faction-gift-" + UUID.randomUUID().toString().replace("-", ""); }
    private static <T> boolean equal(Read<T> read, T expected) { return read.known() && read.value().equals(expected); }
}
