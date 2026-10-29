package org.xar.ck3.control.admission.cold;

import java.util.HashSet;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Offline receipt shape only; no issuer, native readiness, writer permit or recovery grant. */
public record CurrentSavedPreflightContract(
        String machineId, String observedAtUtc, String runtimeRoot, String attemptNonce, String taskNonce,
        ExactRef planRef, ExactRef quoteRef, ExactRef basisRef, ExactRef validationRef,
        ExactRef coreSourceRef, List<ExactRef> runtimeSourceRefs, HistoricalSemanticReplay historicalReplay,
        ExactRef startupDispatchReplayRef, ExactRef consumerProbeRef,
        long currentNextSequence, long filesVerified, int closureCount, PathFlavor pathFlavor) {
    public static final String SCHEMA = "xar.current-saved-campaign-preflight/v1";
    public static final int CANONICAL_ENTRY_COUNT = 8;
    public static final int MAX_CLOSURE_COUNT = 67;

    public enum Phase { OfflineColdContractQualified }
    public enum ValidationScope { OFFLINE_RECEIPT_SHAPE_AND_BINDING_COMPARISON }

    public CurrentSavedPreflightContract {
        StrictJson.text(machineId); StrictJson.utc(observedAtUtc); StrictJson.text(runtimeRoot);
        StrictJson.require(pathFlavor != null && pathFlavor.isAbsolute(runtimeRoot),
                "absolute actual runtime root");
        nonce(attemptNonce); nonce(taskNonce);
        StrictJson.require(planRef != null && quoteRef != null && basisRef != null && validationRef != null
                        && coreSourceRef != null && startupDispatchReplayRef != null && consumerProbeRef != null,
                "complete preflight references required");
        StrictJson.require(runtimeSourceRefs != null, "runtime source array required");
        runtimeSourceRefs = new ArrayList<>(runtimeSourceRefs);
        StrictJson.require(runtimeSourceRefs.size() >= CANONICAL_ENTRY_COUNT
                        && runtimeSourceRefs.size() <= MAX_CLOSURE_COUNT,
                "finite unique receiver source pins");
        HashSet<String> paths = new HashSet<>();
        for (ExactRef ref : runtimeSourceRefs) {
            StrictJson.require(ref != null && paths.add(ref.path()), "finite unique receiver source pins");
        }
        runtimeSourceRefs = List.copyOf(runtimeSourceRefs);
        StrictJson.require(closureCount >= 1 && closureCount <= MAX_CLOSURE_COUNT,
                "original finite active closure limit");
        StrictJson.safe(currentNextSequence, 1); StrictJson.safe(filesVerified, 1);
        StrictJson.require(historicalReplay != null && historicalReplay.historicalSequence() < currentNextSequence,
                "historical and current request sequence remain distinct");
    }

    public Phase phase() { return Phase.OfflineColdContractQualified; }
    public ValidationScope validationScope() { return ValidationScope.OFFLINE_RECEIPT_SHAPE_AND_BINDING_COMPARISON; }
    public boolean grantsFreshReadiness() { return false; }
    public boolean grantsWarmBinding() { return false; }
    public boolean grantsFullLoop() { return false; }
    public boolean grantsReducerOrRecoveryQualification() { return false; }

    private static void nonce(String value) {
        StrictJson.require(value != null && value.matches("[0-9a-f]{32}"), "exact current attempt nonce");
    }
}
