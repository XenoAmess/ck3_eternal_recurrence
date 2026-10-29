package org.xar.ck3.control.wave2.finance.factionthreat;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Joins an existing, qualified alert observation to a gift proposal; never submits gameplay. */
public final class FactionThreatObserver {
    public static final String STEP = "query-player-faction-alerts-v1";
    public static final String CAPABILITY = "game.command.query-player-faction-alerts-v1";
    private static final BigInteger UINT32_MAX = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    private FactionThreatObserver() { }

    public enum Truth { TRUE, FALSE, UNKNOWN }
    public enum HistoryOrigin { REUSED, READ_EXISTING_OBSERVER }
    public enum ReadFailureKind { BRIDGE_UNAVAILABLE, UNSUPPORTED_STEP }
    public enum Reason {
        NO_SELECTED_GIFT("no_selected_gift"),
        EXISTING_ALERT_OBSERVER_UNAVAILABLE("existing_alert_observer_unavailable"),
        EXISTING_ALERT_READ_UNAVAILABLE("existing_alert_read_unavailable"),
        SAME_FRAME_STOCK_THREAT_NOT_OBSERVED("same_frame_stock_threat_not_observed"),
        CURRENT_TARGETING_ROWS_UNAVAILABLE("current_targeting_rows_unavailable"),
        SELECTED_FACTION_NOT_IN_CURRENT_ALERT("selected_faction_not_in_current_alert"),
        SELECTED_RECIPIENT_NOT_IN_CURRENT_FACTION("selected_recipient_not_in_current_faction");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record Frame(BigInteger nativeRevision, int dateRaw, BigInteger playerCharacterId) {
        public Frame {
            positiveWithin(nativeRevision, UINT64_MAX, "nativeRevision");
            positiveWithin(playerCharacterId, UINT32_MAX, "playerCharacterId");
        }
    }

    public record SelectedGift(BigInteger sourceFactionId, BigInteger recipientCharacterId) {
        public SelectedGift {
            positiveWithin(sourceFactionId, UINT32_MAX, "sourceFactionId");
            positiveWithin(recipientCharacterId, UINT32_MAX, "recipientCharacterId");
        }
    }

    public sealed interface Request permits NoSelectedGift, SelectedGiftRequest { }
    public record NoSelectedGift() implements Request { }
    public record SelectedGiftRequest(Frame frame, SelectedGift gift,
                                      List<Alert> eligibleHistory, BigInteger expectedRevision) implements Request {
        public SelectedGiftRequest {
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(gift, "gift");
            eligibleHistory = List.copyOf(eligibleHistory);
            if (eligibleHistory.size() > FactionThreatCodec.MAX_HISTORY) throw new IllegalArgumentException("history limit");
            positiveWithin(expectedRevision, UINT64_MAX, "expectedRevision");
        }
    }

    public record Readiness(Truth targetingRowsReady, Truth stockDangerousPredicateReady, Truth sameFrameReady) {
        public Readiness {
            Objects.requireNonNull(targetingRowsReady, "targetingRowsReady");
            Objects.requireNonNull(stockDangerousPredicateReady, "stockDangerousPredicateReady");
            Objects.requireNonNull(sameFrameReady, "sameFrameReady");
        }
        boolean complete() {
            return targetingRowsReady == Truth.TRUE && stockDangerousPredicateReady == Truth.TRUE
                    && sameFrameReady == Truth.TRUE;
        }
    }

    /** Projection only: provider owns exact-build/source qualification of the original alert. */
    public record Alert(Optional<Frame> frame, boolean available, Readiness readiness,
                        boolean targetingRowsAvailable, List<NativeFactionRow> targetingRows) {
        public Alert {
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(readiness, "readiness");
            targetingRows = List.copyOf(targetingRows);
            if (targetingRows.size() > FactionThreatCodec.MAX_ROWS) throw new IllegalArgumentException("targeting rows limit");
            if (!targetingRowsAvailable && !targetingRows.isEmpty()) throw new IllegalArgumentException("unavailable rows cannot carry rows");
        }
    }

    /** Declared decision projection plus immutable original JSON object for consumer evidence. */
    public static final class NativeFactionRow {
        private final Optional<BigInteger> factionId;
        private final Optional<BigInteger> targetId;
        private final Optional<BigInteger> leaderId;
        private final List<BigInteger> memberIds;
        private final Truth dangerous;
        private final Truth atWar;
        private final byte[] originalJson;

        NativeFactionRow(Optional<BigInteger> factionId, Optional<BigInteger> targetId,
                         Optional<BigInteger> leaderId, List<BigInteger> memberIds,
                         Truth dangerous, Truth atWar, byte[] originalJson) {
            this.factionId = Objects.requireNonNull(factionId, "factionId");
            this.targetId = Objects.requireNonNull(targetId, "targetId");
            this.leaderId = Objects.requireNonNull(leaderId, "leaderId");
            this.memberIds = List.copyOf(memberIds);
            this.dangerous = Objects.requireNonNull(dangerous, "dangerous");
            this.atWar = Objects.requireNonNull(atWar, "atWar");
            this.originalJson = originalJson.clone();
        }
        public Optional<BigInteger> factionId() { return factionId; }
        public Optional<BigInteger> targetId() { return targetId; }
        public Optional<BigInteger> leaderId() { return leaderId; }
        public List<BigInteger> memberIds() { return memberIds; }
        public Truth dangerous() { return dangerous; }
        public Truth atWar() { return atWar; }
        public byte[] originalJson() { return originalJson.clone(); }
    }

    public sealed interface ReadResult permits AlertRead, ReadUnavailable { }
    public record AlertRead(Alert alert) implements ReadResult {
        public AlertRead { Objects.requireNonNull(alert, "alert"); }
    }
    public record ReadUnavailable(ReadFailureKind kind, String error) implements ReadResult {
        public ReadUnavailable {
            Objects.requireNonNull(kind, "kind");
            Objects.requireNonNull(error, "error");
            if (error.length() > 4096) throw new IllegalArgumentException("observer error limit");
        }
    }

    /** Bound to the original driver/session by the host; no alternate native transport is created here. */
    public interface ExistingAlertReader {
        boolean supportsExistingObserver();
        ReadResult readExistingObserver(BigInteger expectedRevision);
    }

    public sealed interface Response permits Unavailable, Observed { }
    public record Unavailable(Reason reason, Optional<String> observerError) implements Response {
        public Unavailable {
            Objects.requireNonNull(reason, "reason");
            Objects.requireNonNull(observerError, "observerError");
            if (observerError.isPresent() && reason != Reason.EXISTING_ALERT_READ_UNAVAILABLE) {
                throw new IllegalArgumentException("observer error requires read unavailable");
            }
        }
    }
    public record Observed(HistoryOrigin origin, SelectedGift gift, Frame frame,
                           boolean dangerousResponseReady, NativeFactionRow nativeRow) implements Response {
        public Observed {
            Objects.requireNonNull(origin, "origin");
            Objects.requireNonNull(gift, "gift");
            Objects.requireNonNull(frame, "frame");
            Objects.requireNonNull(nativeRow, "nativeRow");
            if (nativeRow.factionId().filter(gift.sourceFactionId()::equals).isEmpty()
                    || nativeRow.targetId().filter(frame.playerCharacterId()::equals).isEmpty()
                    || (nativeRow.leaderId().filter(gift.recipientCharacterId()::equals).isEmpty()
                    && !nativeRow.memberIds().contains(gift.recipientCharacterId()))
                    || dangerousResponseReady != (nativeRow.dangerous() == Truth.TRUE && nativeRow.atWar() == Truth.FALSE)) {
                throw new IllegalArgumentException("observed response inconsistent with native row");
            }
        }
    }

    public static Response observe(Request input, ExistingAlertReader reader) {
        Objects.requireNonNull(input, "input");
        Objects.requireNonNull(reader, "reader");
        if (input instanceof NoSelectedGift) return unavailable(Reason.NO_SELECTED_GIFT);
        SelectedGiftRequest request = (SelectedGiftRequest) input;
        Alert alert = null;
        HistoryOrigin origin = HistoryOrigin.READ_EXISTING_OBSERVER;
        for (int index = request.eligibleHistory().size() - 1; index >= 0; index--) {
            Alert prior = request.eligibleHistory().get(index);
            if (prior.frame().filter(request.frame()::equals).isPresent()) {
                alert = prior;
                origin = HistoryOrigin.REUSED;
                break;
            }
        }
        if (alert == null) {
            if (!reader.supportsExistingObserver()) return unavailable(Reason.EXISTING_ALERT_OBSERVER_UNAVAILABLE);
            ReadResult read = Objects.requireNonNull(reader.readExistingObserver(request.expectedRevision()), "read result");
            if (read instanceof ReadUnavailable failed) {
                return new Unavailable(Reason.EXISTING_ALERT_READ_UNAVAILABLE, Optional.of(failed.error()));
            }
            alert = ((AlertRead) read).alert();
        }
        if (alert.frame().filter(request.frame()::equals).isEmpty() || !alert.available()
                || !alert.readiness().complete()) return unavailable(Reason.SAME_FRAME_STOCK_THREAT_NOT_OBSERVED);
        if (!alert.targetingRowsAvailable()) return unavailable(Reason.CURRENT_TARGETING_ROWS_UNAVAILABLE);
        NativeFactionRow matched = null;
        for (NativeFactionRow row : alert.targetingRows()) {
            if (row.factionId().filter(request.gift().sourceFactionId()::equals).isPresent()) {
                if (matched != null) return unavailable(Reason.SELECTED_FACTION_NOT_IN_CURRENT_ALERT);
                matched = row;
            }
        }
        if (matched == null) return unavailable(Reason.SELECTED_FACTION_NOT_IN_CURRENT_ALERT);
        BigInteger recipient = request.gift().recipientCharacterId();
        if (matched.targetId().filter(request.frame().playerCharacterId()::equals).isEmpty()
                || (matched.leaderId().filter(recipient::equals).isEmpty() && !matched.memberIds().contains(recipient))) {
            return unavailable(Reason.SELECTED_RECIPIENT_NOT_IN_CURRENT_FACTION);
        }
        return new Observed(origin, request.gift(), request.frame(),
                matched.dangerous() == Truth.TRUE && matched.atWar() == Truth.FALSE, matched);
    }

    private static Unavailable unavailable(Reason reason) { return new Unavailable(reason, Optional.empty()); }

    private static void positiveWithin(BigInteger value, BigInteger maximum, String field) {
        if (Objects.requireNonNull(value, field).signum() <= 0 || value.compareTo(maximum) > 0) {
            throw new IllegalArgumentException(field + " outside identity domain");
        }
    }
}
