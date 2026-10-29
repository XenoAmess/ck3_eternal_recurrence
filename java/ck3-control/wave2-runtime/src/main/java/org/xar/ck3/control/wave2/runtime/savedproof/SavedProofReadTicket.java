package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Root's independently issued, exact one-read release; construction is not authorization. */
public record SavedProofReadTicket(RecoveryEvidence release, String machineId, String nonce,
        Instant observedAt, Instant reviewAt, Path driverPath, FileStatIdentity driverIdentity,
        ExactRef save, FileStatIdentity saveIdentity, Path sdkRoot, ExactRef sdkFreeze,
        ExactRef validatorSource, String pipeName, Path pythonExecutable, Path outputRoot,
        long maxDriverBytes, long jobMemoryBytes, int timeoutSeconds) {
    public static final String SCHEMA = "xar.current-save-sdk-measurement-release/v1";
    public static final long MAX_DRIVER_BYTES = 64L * 1024 * 1024;
    public static final long MAX_JOB_MEMORY_BYTES = 1536L * 1024 * 1024;

    public SavedProofReadTicket {
        Objects.requireNonNull(release); StrictJson.text(machineId);
        StrictJson.require(nonce != null && nonce.matches("[0-9a-f]{32}"), "unique lowercase read nonce");
        Objects.requireNonNull(observedAt); Objects.requireNonNull(reviewAt);
        StrictJson.require(reviewAt.isAfter(observedAt), "finite read release interval");
        for (Path path : new Path[] {driverPath, sdkRoot, pythonExecutable, outputRoot}) {
            StrictJson.require(path != null && path.isAbsolute() && path.normalize().equals(path), "absolute normalized owned path");
        }
        Objects.requireNonNull(driverIdentity); Objects.requireNonNull(saveIdentity);
        Objects.requireNonNull(save); Objects.requireNonNull(sdkFreeze); Objects.requireNonNull(validatorSource);
        StrictJson.text(pipeName);
        StrictJson.require(maxDriverBytes > 0 && maxDriverBytes <= MAX_DRIVER_BYTES
                && driverIdentity.bytes().signum() > 0
                && driverIdentity.bytes().compareTo(java.math.BigInteger.valueOf(maxDriverBytes)) <= 0,
                "finite whole Driver read budget");
        StrictJson.require(save.bytes() > 0 && saveIdentity.bytes().equals(java.math.BigInteger.valueOf(save.bytes())), "SAVE identity bytes");
        StrictJson.require(jobMemoryBytes > 0 && jobMemoryBytes <= MAX_JOB_MEMORY_BYTES,
                "independently released SDK-measurement Job bound");
        StrictJson.require(timeoutSeconds > 0 && timeoutSeconds <= 120, "finite measurement process timeout");
        StrictJson.require(validatorSource.bytes() > 0 && validatorSource.bytes() <= 65_536
                && sdkFreeze.bytes() > 0 && sdkFreeze.bytes() <= 1_048_576, "distinct SDK source/inventory caps");
        Path saved = Path.of(save.path()), validator = Path.of(validatorSource.path());
        StrictJson.require(saved.isAbsolute() && saved.normalize().equals(saved)
                && "xar_checkpoint.ck3".equals(saved.getFileName().toString())
                && saved.getParent() != null && "save games".equals(saved.getParent().getFileName().toString()), "exact original SDK SAVE location");
        StrictJson.require(validator.equals(sdkRoot.resolve("xar_autoplayer/cold_checkpoint_validator.py")), "sole frozen SDK validator module");
    }

    public static SavedProofReadTicket parse(RecoveryEvidence release) {
        ObjectNode row = StrictJson.object(StrictJson.parse(release.bytes()), Set.of("schema", "machine_id", "nonce",
            "observed_at_utc", "review_at_utc", "driver_path", "driver_identity", "save_ref", "save_identity",
            "sdk_root", "sdk_freeze_ref", "validator_ref", "pipe_name", "python_executable", "output_root",
            "max_driver_bytes", "physical_driver_reads", "original_sdk_save_hash_calls", "job_memory_limit_bytes", "timeout_seconds"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "measurement release schema");
        StrictJson.require(StrictJson.integer(row.get("physical_driver_reads"), 1, 1) == 1
                && StrictJson.integer(row.get("original_sdk_save_hash_calls"), 1, 1) == 1,
                "exact independently authorized physical read/hash counts");
        return new SavedProofReadTicket(release, StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("nonce")),
            Instant.parse(StrictJson.utc(StrictJson.text(row.get("observed_at_utc")))),
            Instant.parse(StrictJson.utc(StrictJson.text(row.get("review_at_utc")))),
            Path.of(StrictJson.text(row.get("driver_path"))), FileStatIdentity.fromJson(row.get("driver_identity"), FileStatIdentity.SCHEMA),
            ExactRef.fromJson(row.get("save_ref")), FileStatIdentity.fromJson(row.get("save_identity"), FileStatIdentity.SCHEMA),
            Path.of(StrictJson.text(row.get("sdk_root"))), ExactRef.fromJson(row.get("sdk_freeze_ref")),
            ExactRef.fromJson(row.get("validator_ref")), StrictJson.text(row.get("pipe_name")),
            Path.of(StrictJson.text(row.get("python_executable"))), Path.of(StrictJson.text(row.get("output_root"))),
            StrictJson.integer(row.get("max_driver_bytes"), 1, MAX_DRIVER_BYTES),
            StrictJson.integer(row.get("job_memory_limit_bytes"), 1, MAX_JOB_MEMORY_BYTES),
            Math.toIntExact(StrictJson.integer(row.get("timeout_seconds"), 1, 120)));
    }
}
