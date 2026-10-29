package org.xar.ck3.control.wave2.finance.giftoutcome;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import static org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel.*;

/** One wire entry for the existing Native Driver / Service / MCP consumers; no independent transport. */
public final class ExistingGiftOutcomeAdapter implements GiftOutcomeQuery.ExistingDriver {
    /** Host must implement this on the original owned driver and its existing history lock.
     * History rows are lazily exported only for direct submit/receipt/alerts or auto-turn gift rows;
     * complete Army/native history must never be serialized into this projection.
     */
    public interface OwnedDriverPort {
        byte[] takeInternalSemanticSnapshot();
        <T> T underOriginalHistoryLock(Function<Iterable<byte[]>, T> projection);
        Invocation readOriginalIndependentPair(byte[] request);
        Invocation queryOriginalPlayerFactionAlerts(BigInteger expectedRevision);
        void recordOriginalObservedCommand(String step, boolean ok, byte[] result);
    }
    public sealed interface Invocation permits Packet, Unavailable { }
    public static final class Packet implements Invocation {
        private final byte[] json;
        public Packet(byte[] json) {
            Objects.requireNonNull(json); if (json.length == 0 || json.length > GiftOutcomeCodec.MAX_BYTES) throw new IllegalArgumentException("packet byte limit");
            this.json = json.clone();
        }
        public byte[] json() { return json.clone(); }
    }
    public enum ReadFailure { BRIDGE_UNAVAILABLE, UNSUPPORTED_STEP }
    public record Unavailable(ReadFailure kind, String error) implements Invocation {
        public Unavailable { Objects.requireNonNull(kind); Objects.requireNonNull(error); }
    }
    private final OwnedDriverPort driver;
    public ExistingGiftOutcomeAdapter(OwnedDriverPort driver) { this.driver = Objects.requireNonNull(driver); }

    /** Same request/result bytes are forwarded by all three original consumer wrappers. */
    public byte[] queryResolvedFactionGiftOutcome(byte[] request) {
        return GiftOutcomeCodec.outcome(GiftOutcomeQuery.query(this, GiftOutcomeCodec.request(request)));
    }
    @Override public Snapshot takeSemanticSnapshot() { return GiftOutcomeCodec.snapshot(driver.takeInternalSemanticSnapshot()); }
    @Override public List<HistoryEntry> projectRelevantHistoryUnderOriginalLock(Request request, Snapshot before) {
        return driver.underOriginalHistoryLock(rows -> {
            HistoryEntry latestSubmit = null; HistoryEntry latestReceipt = null; HistoryEntry latestAlert = null;
            for (byte[] row : rows) {
                java.util.Optional<HistoryEntry> parsed = GiftOutcomeCodec.historyEntry(row);
                if (parsed.isEmpty()) continue;
                HistoryEntry entry = parsed.orElseThrow();
                if (entry.selectedStep().equals(SUBMIT_STEP) && entry.pending().filter(value -> value.requestId().filter(request.requestId()::equals).isPresent()).isPresent()) latestSubmit = entry;
                if (entry.selectedStep().equals(RECEIPT_STEP) && entry.receipt().filter(value -> value.eligible(request.requestId())).isPresent()) latestReceipt = entry;
                if (entry.directAlert().filter(value -> value.sameFrame(before)).isPresent()) latestAlert = entry;
            }
            List<HistoryEntry> relevant = new ArrayList<>(3);
            if (latestSubmit != null) relevant.add(latestSubmit);
            if (latestReceipt != null) relevant.add(latestReceipt);
            if (latestAlert != null) relevant.add(latestAlert);
            return List.copyOf(relevant);
        });
    }
    @Override public PairRead readIndependentPair(PairRequest request) {
        Invocation read = Objects.requireNonNull(driver.readOriginalIndependentPair(GiftOutcomeCodec.pairRequest(request)));
        if (read instanceof Unavailable unavailable) {
            if (unavailable.kind() == ReadFailure.UNSUPPORTED_STEP) throw new IllegalStateException(unavailable.error());
            return new PairUnavailable(unavailable.error());
        }
        return GiftOutcomeCodec.pairResult(((Packet) read).json());
    }
    @Override public AlertRead readCurrentAlert(BigInteger expectedRevision) {
        Invocation read = Objects.requireNonNull(driver.queryOriginalPlayerFactionAlerts(expectedRevision));
        if (read instanceof Unavailable unavailable) return new AlertReadUnavailable(unavailable.error());
        return new AlertPacket(GiftOutcomeCodec.alertResult(((Packet) read).json()));
    }
    @Override public void recordObservedCommand(Observed outcome) {
        driver.recordOriginalObservedCommand(STEP, true, GiftOutcomeCodec.outcome(outcome));
    }
}
