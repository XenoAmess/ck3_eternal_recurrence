package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.SavedObservation;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.SavedWindow;

/** Observes already completed SDK measurements in memory. No new SDK, Driver, SAVE or metadata read. */
public final class DecisionSavedMetrics {
    private DecisionSavedMetrics() { }
    public static SavedWindow observeWindow(DecisionMetricRecorder metrics, SavedCheckpointMeasurement before,
                                           SavedCheckpointMeasurement after) {
        Objects.requireNonNull(metrics); Objects.requireNonNull(before); Objects.requireNonNull(after);
        StrictJson.require(!after.observedAtUtc().isBefore(before.observedAtUtc()), "saved measurement chronology regressed");
        StrictJson.require(before.machineId().equals(after.machineId()) && before.sdkFreeze().equals(after.sdkFreeze())
                && before.validatorSource().equals(after.validatorSource()), "saved window must preserve machine and SDK validator source");
        SavedWindow window = new SavedWindow(observed(before), observed(after)); metrics.savedObserved(window); return window;
    }
    private static SavedObservation observed(SavedCheckpointMeasurement measurement) {
        ObjectNode canonical = StrictJson.object(StrictJson.parse(measurement.canonicalReceipt().bytes()), Set.of(
                "schema", "status", "machine_id", "observed_at_utc", "validator_source_ref", "driver_ref", "driver_identity_before",
                "driver_identity_after", "save_ref", "save_identity_before", "save_identity_after", "checkpoint", "pipe_name",
                "driver_physical_body_reads", "driver_payload_reader_calls", "driver_physical_read_scope", "driver_payload_reader_scope",
                "original_validator_calls", "save_sha256_calls", "driver_body_rewritten", "ledger_write_already_performed", "game_or_RPC_calls"));
        StrictJson.require("xar.current-saved-recovery-checkpoint-qualification/v1".equals(StrictJson.text(canonical.get("schema")))
                && "ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED".equals(StrictJson.text(canonical.get("status")))
                && measurement.machineId().equals(StrictJson.text(canonical.get("machine_id"))), "completed measurement canonical proof binding");
        var checkpoint = canonical.get("checkpoint");
        StrictJson.require(checkpoint != null && checkpoint.isObject(), "actual complete saved checkpoint required");
        int date = Math.toIntExact(StrictJson.integer(checkpoint.get("date_raw"), 0, Integer.MAX_VALUE));
        StrictJson.require(measurement.save().sha256().equals(StrictJson.text(checkpoint.get("sha256")))
                && measurement.save().bytes() == StrictJson.integer(checkpoint.get("size"), 0, StrictJson.MAX_SAFE_INTEGER), "actual saved file/date observation differs");
        return new SavedObservation(measurement.machineId(), date, measurement.canonicalCheckpointProof(), measurement.save());
    }
}
