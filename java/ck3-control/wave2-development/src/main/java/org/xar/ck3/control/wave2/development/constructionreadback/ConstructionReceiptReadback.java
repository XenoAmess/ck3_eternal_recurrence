package org.xar.ck3.control.wave2.development.constructionreadback;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;
import org.xar.ck3.control.wave2.runtime.creationtime.ProcessCreationTime;

/** Pure readback lease projection and original oldest-first receipt priority. No writer or process probe. */
public final class ConstructionReceiptReadback {
    public static final BigInteger WATCH_INTERVAL_RAW = BigInteger.valueOf(30 * 24);
    private static final String UNAVAILABLE_SCHEMA = "xar.construction-material-observation-unavailable.v1";
    private ConstructionReceiptReadback() { }

    public record Scope(BigInteger bridgePid, String bridgeCreationDate, BigInteger nativeRevision,
                        BigInteger dateRaw) { }

    /** The caller supplies the actual existing process observation; no default probe is permitted. */
    public record CurrentProcess(BigInteger pid, String creationTime) {
        public CurrentProcess {
            if (!positive(pid) || creationTime == null || creationTime.isEmpty()) {
                throw new IllegalArgumentException("current construction process identity must be supplied");
            }
        }
    }

    public record SourceFrame(BigInteger actorCharacterId, String episodeRunId, BigInteger nativeRevision,
                              BigInteger revision, BigInteger dateRaw, BigInteger bridgePid,
                              String snapshotId, String bridgeCreationDate) { }

    public record MaterialObservation(String schema, Evidence readOnly, Evidence businessSubmission,
                                      BigInteger nativeSubmitCalls, String actionRequestId, SourceFrame sourceFrame) {
        public MaterialObservation {
            Objects.requireNonNull(readOnly);
            Objects.requireNonNull(businessSubmission);
        }
    }

    /** Presence is required because explicit null must suppress the old post-date fallback. */
    public record LastCheckDate(boolean present, BigInteger value) {
        public LastCheckDate {
            if (!present && value != null) { throw new IllegalArgumentException("missing date has no value"); }
        }
        public BigInteger orPostDate(BigInteger postDate) { return present ? value : postDate; }
    }

    /** This source reads raw identity strings, whereas selected-intent v1 intentionally normalizes empty strings. */
    public record ReceiptIdentity(String actionRequestId, String episodeRunId, BigInteger actorCharacterId) { }

    public record Receipt(ReceiptIdentity identity, Scope originalScope, MaterialObservation materialObservation,
                          String completionStatus, BigInteger observedPlayerMonthlyGoldIncomeRaw,
                          boolean postCashObject, String provinceIncomeStatus, LastCheckDate lastCheckDate) {
        public Receipt {
            Objects.requireNonNull(identity);
            Objects.requireNonNull(originalScope);
            Objects.requireNonNull(lastCheckDate);
        }
    }

    public record Snapshot(String episodeRunId, BigInteger nativeRevision, BigInteger dateRaw) { }

    public record Ledger(List<Receipt> appliedPrior, Receipt applied) {
        public Ledger { appliedPrior = List.copyOf(appliedPrior); }
    }

    public enum PriorityReason {
        PROCESS_OR_FRAME_RECHECK, COMPLETED_INCOME_OR_CASH, COMPLETED_PROVINCE_RECHECK, MONTHLY_COMPLETION_WATCH
    }

    /** Index is in the episode-filtered oldest-first sequence, not an action authorization. */
    public record Priority(int receiptIndex, Receipt receipt, PriorityReason reason) {
        public Priority {
            if (receiptIndex < 0) { throw new IllegalArgumentException("negative receipt index"); }
            Objects.requireNonNull(receipt);
            Objects.requireNonNull(reason);
        }
    }

    public static List<Receipt> appliedReceipts(Ledger ledger, String episodeRunId) {
        Objects.requireNonNull(ledger);
        var receipts = new java.util.ArrayList<Receipt>(ledger.appliedPrior());
        if (ledger.applied() != null) { receipts.add(ledger.applied()); }
        return receipts.stream().filter(row -> Objects.equals(row.identity().episodeRunId(), episodeRunId)).toList();
    }

    public static Scope readbackScope(Receipt receipt) {
        Objects.requireNonNull(receipt);
        MaterialObservation observation = receipt.materialObservation();
        SourceFrame source = observation == null ? null : observation.sourceFrame();
        if (observation == null || !UNAVAILABLE_SCHEMA.equals(observation.schema())
                || observation.readOnly() != Evidence.TRUE || observation.businessSubmission() != Evidence.FALSE
                || !BigInteger.ZERO.equals(observation.nativeSubmitCalls())
                || !Objects.equals(observation.actionRequestId(), receipt.identity().actionRequestId())
                || source == null
                || !Objects.equals(source.actorCharacterId(), receipt.identity().actorCharacterId())
                || !Objects.equals(source.episodeRunId(), receipt.identity().episodeRunId())
                || !positive(source.nativeRevision()) || !positive(source.revision())
                || !positive(source.dateRaw()) || !positive(source.bridgePid())
                || !Objects.equals(source.snapshotId(), "native:" + source.nativeRevision())
                || !Objects.equals(source.dateRaw(), receipt.lastCheckDate().value())
                || source.bridgeCreationDate() == null || source.bridgeCreationDate().isEmpty()) {
            return receipt.originalScope();
        }
        return new Scope(source.bridgePid(), source.bridgeCreationDate(), source.nativeRevision(), source.dateRaw());
    }

    public static Optional<Priority> priorityReceipt(Ledger ledger, Snapshot snapshot, Optional<CurrentProcess> observedProcess) {
        Objects.requireNonNull(snapshot);
        Objects.requireNonNull(observedProcess);
        List<Receipt> receipts = appliedReceipts(ledger, snapshot.episodeRunId());
        if (receipts.isEmpty()) { return Optional.empty(); }
        CurrentProcess process = observedProcess.orElseThrow(
                () -> new IllegalArgumentException("receipt priority needs an actual supplied process observation"));
        for (int index = 0; index < receipts.size(); index++) {
            Receipt receipt = receipts.get(index);
            Scope observed = readbackScope(receipt);
            if (!sameProcess(process, observed) || earlier(snapshot.nativeRevision(), observed.nativeRevision())
                    || earlier(snapshot.dateRaw(), observed.dateRaw())) {
                return Optional.of(new Priority(index, receipt, PriorityReason.PROCESS_OR_FRAME_RECHECK));
            }
        }
        for (int index = 0; index < receipts.size(); index++) {
            Receipt receipt = receipts.get(index);
            if (completed(receipt) && (receipt.observedPlayerMonthlyGoldIncomeRaw() == null || !receipt.postCashObject())) {
                return Optional.of(new Priority(index, receipt, PriorityReason.COMPLETED_INCOME_OR_CASH));
            }
        }
        for (int index = 0; index < receipts.size(); index++) {
            Receipt receipt = receipts.get(index);
            if (completed(receipt) && !"observed".equals(receipt.provinceIncomeStatus()) && due(receipt, snapshot.dateRaw())) {
                return Optional.of(new Priority(index, receipt, PriorityReason.COMPLETED_PROVINCE_RECHECK));
            }
        }
        for (int index = 0; index < receipts.size(); index++) {
            Receipt receipt = receipts.get(index);
            if (!completed(receipt) && due(receipt, snapshot.dateRaw())) {
                return Optional.of(new Priority(index, receipt, PriorityReason.MONTHLY_COMPLETION_WATCH));
            }
        }
        return Optional.empty();
    }

    public static boolean sameProcess(CurrentProcess current, Scope observed) {
        Objects.requireNonNull(current);
        Objects.requireNonNull(observed);
        if (!current.pid().equals(observed.bridgePid())) { return false; }
        if (current.creationTime().equals(observed.bridgeCreationDate())) { return true; }
        return ProcessCreationTime.same(current.creationTime(), observed.bridgeCreationDate());
    }
    private static boolean completed(Receipt receipt) { return "completed".equals(receipt.completionStatus()); }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static boolean earlier(BigInteger first, BigInteger second) {
        return first != null && second != null && first.compareTo(second) < 0;
    }
    private static boolean due(Receipt receipt, BigInteger date) {
        BigInteger last = receipt.lastCheckDate().orPostDate(receipt.originalScope().dateRaw());
        return date != null && last != null && date.compareTo(last.add(WATCH_INTERVAL_RAW)) >= 0;
    }
}
