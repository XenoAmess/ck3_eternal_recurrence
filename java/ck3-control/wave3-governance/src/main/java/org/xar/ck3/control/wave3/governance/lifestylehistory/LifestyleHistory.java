package org.xar.ck3.control.wave3.governance.lifestylehistory;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Pure selection of original LIFE history. No submit, retry, persistence, or native qualification. */
public final class LifestyleHistory {
    public static final String PERK_SUBMIT = "private-select-player-lifestyle-perk-v1";
    public static final String FOCUS_SUBMIT = "private-select-player-lifestyle-stock-focus-v1";
    public static final String RECEIPT = "private-query-player-lifestyle-receipt-v1";
    private LifestyleHistory() { }

    /** A validated original JSON object is retained verbatim, including unknown fields and decimal spelling. */
    public static final class RetainedJson {
        private final byte[] bytes;
        RetainedJson(byte[] validatedBytes) { bytes = validatedBytes.clone(); }
        public byte[] bytes() { return bytes.clone(); }
        @Override public boolean equals(Object other) { return other instanceof RetainedJson value && Arrays.equals(bytes, value.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }
    }
    public enum Kind {
        FOCUS("focus"), PERK("perk");
        private final String wire;
        Kind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Optional<Kind> fromWire(String value) {
            for (Kind kind : values()) { if (kind.wire.equals(value)) { return Optional.of(kind); } } return Optional.empty();
        }
    }
    /** Nullable fields are observations, never default zeros or inferred proof. Full original data stays in originalJson. */
    public record ReceiptData(String status, String episodeRunId, String actionRequestId, String targetKey, String kind,
            BigInteger prePublicRevision, BigInteger sourceNativeRevision, BigInteger sourceDateRaw,
            BigInteger sourcePlayerCharacterId, String postSnapshotId, BigInteger postPublicRevision, BigInteger postDateRaw,
            Boolean postTargetPerkOwned, Boolean postconditionVerified, Boolean postHasCurrentFocus,
            String postCurrentFocusKey, RetainedJson originalJson) {
        public ReceiptData { Objects.requireNonNull(originalJson); }
    }
    public record HistoryRow(String command, Boolean ok, ReceiptData result) { }
    public record Input(String episodeRunId, List<HistoryRow> history) {
        public Input { history = List.copyOf(history); }
    }
    public record AppliedReceipt(String actionRequestId, String targetKey, String postSnapshotId,
            BigInteger postPublicRevision, BigInteger postDateRaw, String episodeRunId,
            Boolean postTargetPerkOwned, boolean postconditionVerified, Kind kind,
            Boolean postHasCurrentFocus, String postCurrentFocusKey) {
        public AppliedReceipt { Objects.requireNonNull(actionRequestId); Objects.requireNonNull(targetKey);
            Objects.requireNonNull(postSnapshotId); Objects.requireNonNull(postPublicRevision); Objects.requireNonNull(postDateRaw);
            Objects.requireNonNull(episodeRunId); Objects.requireNonNull(kind);
            if (!postconditionVerified || !validId(actionRequestId, kind) || !nonempty(targetKey) || !nonempty(episodeRunId)
                    || !positive(postPublicRevision) || postDateRaw.signum() < 0 || !postSnapshotId.equals("native:" + postPublicRevision)
                    || (kind == Kind.FOCUS ? !Boolean.TRUE.equals(postHasCurrentFocus) || !targetKey.equals(postCurrentFocusKey)
                    : !Boolean.TRUE.equals(postTargetPerkOwned))) {
                throw new IllegalArgumentException("unverified or malformed result is not an applied receipt");
            }
        }
    }
    public enum Status { CLEAR, VERIFY_ORIGINAL_RECEIPT, HOLD_UNKNOWN, CONFLICT, EPISODE_UNAVAILABLE }
    public record Selection(String episodeRunId, Status status, List<ReceiptData> pendingActions, List<ReceiptData> unverifiedReceipts,
            Optional<AppliedReceipt> latestApplied) {
        public Selection { Objects.requireNonNull(status); pendingActions = List.copyOf(pendingActions);
            unverifiedReceipts = List.copyOf(unverifiedReceipts); Objects.requireNonNull(latestApplied);
            if ((status == Status.EPISODE_UNAVAILABLE) != !nonempty(episodeRunId)) {
                throw new IllegalArgumentException("selection must retain its actual episode binding");
            }
            for (ReceiptData data : pendingActions) { if (!Objects.equals(episodeRunId, data.episodeRunId())) { throw new IllegalArgumentException("foreign pending episode"); } }
            for (ReceiptData data : unverifiedReceipts) { if (!Objects.equals(episodeRunId, data.episodeRunId())) { throw new IllegalArgumentException("foreign receipt episode"); } }
            if (latestApplied.isPresent() && !Objects.equals(episodeRunId, latestApplied.orElseThrow().episodeRunId())) { throw new IllegalArgumentException("foreign applied episode"); }
            if (status == Status.CLEAR && (!pendingActions.isEmpty() || !unverifiedReceipts.isEmpty())) {
                throw new IllegalArgumentException("clear selection cannot contain unresolved evidence");
            }
            if (status == Status.VERIFY_ORIGINAL_RECEIPT && pendingActions.size() != 1) {
                throw new IllegalArgumentException("verification must name one original action");
            }
            ReceiptData original = pendingActions.isEmpty() ? null : pendingActions.getFirst();
            if (status == Status.VERIFY_ORIGINAL_RECEIPT && (!verifiable(original)
                    || unverifiedReceipts.stream().anyMatch(value -> !sameIdentity(original, value)))) {
                throw new IllegalArgumentException("verification requires a complete original action and matching uncertainty");
            }
        }
    }
    private record ActionIdentity(String requestId, String kind, String target) { }
    private record PendingKey(ActionIdentity identity, int missingIdentityIndex, String command) { }
    private record PendingObserved(String command, ReceiptData data) { }

    public static Selection select(Input input) {
        Objects.requireNonNull(input);
        if (input.episodeRunId() == null || input.episodeRunId().isEmpty()) {
            return new Selection(input.episodeRunId(), Status.EPISODE_UNAVAILABLE, List.of(), List.of(), Optional.empty());
        }
        LinkedHashMap<PendingKey, PendingObserved> pending = new LinkedHashMap<>();
        Set<String> conflictedIds = new HashSet<>();
        Set<String> completedRequestIds = new HashSet<>();
        List<ReceiptData> unverified = new ArrayList<>(); AppliedReceipt latest = null;
        for (int index = 0; index < input.history().size(); index++) {
            HistoryRow row = input.history().get(index); ReceiptData data = row.result();
            if (data == null || !input.episodeRunId().equals(data.episodeRunId())) { continue; }
            if (PERK_SUBMIT.equals(row.command()) || FOCUS_SUBMIT.equals(row.command())) {
                // A pre-submit rejection cannot settle a different older UNKNOWN request.
                if ("rejected_before_submit".equals(data.status())) { continue; }
                ActionIdentity identity = identity(data);
                boolean changedBinding = nonempty(data.actionRequestId()) && pending.values().stream()
                        .anyMatch(existing -> data.actionRequestId().equals(existing.data().actionRequestId())
                                && (!sameBinding(existing.data(), data) || !Objects.equals(existing.command(), row.command())));
                if (changedBinding || completedRequestIds.contains(data.actionRequestId())) { conflictedIds.add(data.actionRequestId()); }
                PendingKey key = new PendingKey(identity, identity == null || conflictedIds.contains(data.actionRequestId()) ? index : -1, row.command());
                pending.put(key, new PendingObserved(row.command(), data)); continue;
            }
            if (!RECEIPT.equals(row.command())) { continue; }
            AppliedReceipt material = applied(row, input.episodeRunId());
            if (material == null) { unverified.add(data); continue; }
            AppliedReceipt candidate = material;
            boolean nonIndependent = pending.values().stream().anyMatch(existing -> sameAction(candidate, existing.data())
                    && (!commandMatchesKind(existing.command(), existing.data()) || !settles(candidate, existing.data())));
            if (conflictedIds.contains(material.actionRequestId()) || nonIndependent) { unverified.add(data); continue; }
            latest = material;
            completedRequestIds.add(material.actionRequestId());
            pending.entrySet().removeIf(entry -> commandMatchesKind(entry.getValue().command(), entry.getValue().data())
                    && settles(material, entry.getValue().data()));
            unverified.removeIf(earlier -> sameAction(material, earlier));
        }
        List<ReceiptData> actions = pending.values().stream().map(PendingObserved::data).toList();
        Status status;
        if (!conflictedIds.isEmpty() || actions.size() > 1) { status = Status.CONFLICT; }
        else if (actions.isEmpty()) { status = unverified.isEmpty() ? Status.CLEAR : Status.HOLD_UNKNOWN; }
        else {
            ReceiptData action = actions.getFirst();
            boolean foreignReceipt = unverified.stream().anyMatch(receipt -> !sameIdentity(action, receipt));
            status = foreignReceipt ? Status.CONFLICT
                    : verifiable(action) && commandMatchesKind(pending.values().iterator().next().command(), action)
                    ? Status.VERIFY_ORIGINAL_RECEIPT : Status.HOLD_UNKNOWN;
        }
        return new Selection(input.episodeRunId(), status, actions, unverified, Optional.ofNullable(latest));
    }

    /** Material view matches the validated native producer contract, not an ACK's status string. */
    private static AppliedReceipt applied(HistoryRow row, String episode) {
        ReceiptData data = row.result(); Optional<Kind> kind = Kind.fromWire(data.kind());
        if (!Boolean.TRUE.equals(row.ok()) || !"applied".equals(data.status()) || !episode.equals(data.episodeRunId())
                || kind.isEmpty() || !validId(data.actionRequestId(), kind.orElseThrow()) || !nonempty(data.targetKey())
                || !positive(data.postPublicRevision()) || data.postDateRaw() == null || data.postDateRaw().signum() < 0
                || !Objects.equals(data.postSnapshotId(), "native:" + data.postPublicRevision()) || !Boolean.TRUE.equals(data.postconditionVerified())) {
            return null;
        }
        if (kind.orElseThrow() == Kind.FOCUS ? !Boolean.TRUE.equals(data.postHasCurrentFocus()) || !Objects.equals(data.targetKey(), data.postCurrentFocusKey())
                : !Boolean.TRUE.equals(data.postTargetPerkOwned())) { return null; }
        return new AppliedReceipt(data.actionRequestId(), data.targetKey(), data.postSnapshotId(), data.postPublicRevision(), data.postDateRaw(),
                episode, data.postTargetPerkOwned(), true, kind.orElseThrow(), data.postHasCurrentFocus(), data.postCurrentFocusKey());
    }
    private static boolean settles(AppliedReceipt applied, ReceiptData pending) {
        // Legacy post_public_revision carries the native revision. Do not compare it to pre_public_revision.
        return sameAction(applied, pending) && positive(pending.sourceNativeRevision())
                && applied.postPublicRevision().compareTo(pending.sourceNativeRevision()) > 0
                && pending.sourceDateRaw() != null && applied.postDateRaw().compareTo(pending.sourceDateRaw()) >= 0;
    }
    private static boolean sameAction(AppliedReceipt applied, ReceiptData data) {
        return applied.actionRequestId().equals(data.actionRequestId()) && applied.kind().wire().equals(data.kind())
                && applied.targetKey().equals(data.targetKey()) && applied.episodeRunId().equals(data.episodeRunId());
    }
    private static boolean sameIdentity(ReceiptData first, ReceiptData second) {
        ActionIdentity left = identity(first), right = identity(second); return left != null && left.equals(right);
    }
    private static boolean sameBinding(ReceiptData first, ReceiptData second) {
        return sameIdentity(first, second) && Objects.equals(first.episodeRunId(), second.episodeRunId())
                && Objects.equals(first.prePublicRevision(), second.prePublicRevision())
                && Objects.equals(first.sourceNativeRevision(), second.sourceNativeRevision())
                && Objects.equals(first.sourceDateRaw(), second.sourceDateRaw())
                && Objects.equals(first.sourcePlayerCharacterId(), second.sourcePlayerCharacterId());
    }
    private static ActionIdentity identity(ReceiptData data) {
        return nonempty(data.actionRequestId()) && nonempty(data.kind()) && nonempty(data.targetKey())
                ? new ActionIdentity(data.actionRequestId(), data.kind(), data.targetKey()) : null;
    }
    private static boolean verifiable(ReceiptData data) {
        Optional<Kind> kind = Kind.fromWire(data.kind());
        return ("submitted_verification_pending".equals(data.status()) || "action_state_unknown".equals(data.status()))
                && kind.isPresent() && validId(data.actionRequestId(), kind.orElseThrow()) && nonempty(data.targetKey())
                && positive(data.prePublicRevision()) && positive(data.sourceNativeRevision())
                && data.sourceDateRaw() != null && data.sourceDateRaw().signum() >= 0 && positive(data.sourcePlayerCharacterId());
    }
    private static boolean commandMatchesKind(String command, ReceiptData data) {
        return FOCUS_SUBMIT.equals(command) && "focus".equals(data.kind()) || PERK_SUBMIT.equals(command) && "perk".equals(data.kind());
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static boolean validId(String value, Kind kind) {
        if (value == null) return false;
        if (value.startsWith("life-" + kind.wire() + "-")) return value.length() > kind.wire().length() + 6;
        // Accept Java RequestIds producer syntax: step-<positive-decimal>-<12-hex>
        if (value.startsWith("step-")) {
            String rest = value.substring(5);
            int dash = rest.indexOf('-');
            if (dash <= 0 || dash == rest.length() - 1) return false;
            String num = rest.substring(0, dash);
            String hex = rest.substring(dash + 1);
            if (num.length() > 16 || !num.matches("[1-9][0-9]*")) return false;
            if (hex.length() != 12 || !hex.matches("[0-9a-f]{12}")) return false;
            return true;
        }
        return false;
    }
    private static boolean nonempty(String value) { return value != null && !value.isEmpty(); }
}
