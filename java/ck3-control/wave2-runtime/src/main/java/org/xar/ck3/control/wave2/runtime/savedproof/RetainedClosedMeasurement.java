package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/**
 * Same-JVM historical closed-measurement context, never a current Driver or warm qualification.
 * Only the original live coordinator can register one after its current cache still verifies.
 * No JSON loader, public constructor, HTTP operation or automatic drift fallback exists.
 */
public final class RetainedClosedMeasurement implements AutoCloseable {
    private final SavedCheckpointMeasurementCoordinator owner;
    private final Thread ownerThread = Thread.currentThread();
    private final HistoricalInputs historical;
    private boolean closed;

    private RetainedClosedMeasurement(SavedCheckpointMeasurementCoordinator owner, HistoricalInputs historical) {
        this.owner = Objects.requireNonNull(owner); this.historical = Objects.requireNonNull(historical);
    }

    /** Registration remains solely in the original coordinator; an unregistered object grants nothing. */
    static RetainedClosedMeasurement retainFor(SavedCheckpointMeasurementCoordinator owner, HistoricalInputs historical) {
        return new RetainedClosedMeasurement(owner,historical);
    }

    /** Immutable ordinary facts; constructing this value does not create a registered retained context. */
    public record HistoricalInputs(String machineId, Instant observedAtUtc, Instant reviewAtUtc,
            Instant retainedAtUtc, String ticketNonce, ExactRef releaseRef, RecoveryEvidence canonicalReceipt,
            ExactRef validatorSource, ExactRef sdkFreeze, String checkpointDigest, String workerSourceSha256,
            ExactRef historicalDriver, FileStatIdentity historicalDriverIdentity,
            ExactRef save, FileStatIdentity saveIdentity, List<ExactRef> importedSources) {
        public HistoricalInputs {
            StrictJson.text(machineId); Objects.requireNonNull(observedAtUtc); Objects.requireNonNull(reviewAtUtc);
            Objects.requireNonNull(retainedAtUtc);
            StrictJson.require(ticketNonce != null && ticketNonce.matches("[0-9a-f]{32}"), "original finite ticket nonce");
            Objects.requireNonNull(releaseRef); Objects.requireNonNull(canonicalReceipt);
            Objects.requireNonNull(validatorSource); Objects.requireNonNull(sdkFreeze);
            StrictJson.require(checkpointDigest != null && checkpointDigest.matches("[0-9a-f]{64}")
                    && workerSourceSha256 != null && workerSourceSha256.matches("[0-9a-f]{64}"), "exact original source/digest");
            Objects.requireNonNull(historicalDriver); Objects.requireNonNull(historicalDriverIdentity);
            Objects.requireNonNull(save); Objects.requireNonNull(saveIdentity);
            importedSources = List.copyOf(importedSources);
            StrictJson.require(!importedSources.isEmpty() && !retainedAtUtc.isBefore(observedAtUtc)
                    && retainedAtUtc.isBefore(reviewAtUtc), "bounded historical observation retained within original lease");
        }
        public boolean currentDriverQualified() { return false; }
        public boolean grantsWarmAttachment() { return false; }
    }

    /**
     * Revalidate original SAVE/source/deadline facts only. A subsequent new-source/restore/warm
     * guard must independently validate the actual current Driver/Game/SDK/Native tuple.
     */
    public HistoricalInputs requireHistoricalInputs() throws IOException {
        requireOpenOwnerThread();
        return owner.requireRetainedHistoricalInputs(this);
    }

    HistoricalInputs retainedInputs(SavedCheckpointMeasurementCoordinator expectedOwner) {
        requireOpenOwnerThread();
        StrictJson.require(owner == expectedOwner, "historical context belongs to its original coordinator");
        return historical;
    }

    private void requireOpenOwnerThread() {
        StrictJson.require(Thread.currentThread() == ownerThread,
                "historical context belongs to its original owning Java thread");
        StrictJson.require(!closed, "historical context is closed; no renewal or reconstruction");
    }

    @Override public void close() {
        StrictJson.require(Thread.currentThread() == ownerThread, "only original owning thread closes historical context");
        closed = true;
    }

    /** Metadata-only validation port; neither this port nor HistoricalInputs can issue measurement tokens. */
    interface MetadataReader {
        FileStatIdentity statSave(Path path) throws IOException;
        void requireExact(ExactRef reference, int maximumBytes) throws IOException;
    }

    /** Shared production check, testable with ordinary synthetic facts without minting any token. */
    static void requireMetadata(HistoricalInputs inputs, MetadataReader reader, Clock clock,
            String actualMachine, String actualWorkerSourceSha256) throws IOException {
        Objects.requireNonNull(inputs); Objects.requireNonNull(reader); Objects.requireNonNull(clock);
        requireScope(inputs,clock,actualMachine,actualWorkerSourceSha256);
        Path savePath = Path.of(inputs.save().path());
        StrictJson.require(inputs.saveIdentity().equals(reader.statSave(savePath)),
                "current SAVE native identity matches the original closed measurement");
        reader.requireExact(inputs.sdkFreeze(),1_048_576);
        reader.requireExact(inputs.validatorSource(),65_536);
        for (ExactRef source : inputs.importedSources()) { reader.requireExact(source,2_097_152); }
        reader.requireExact(inputs.canonicalReceipt().reference(),65_536);
        StrictJson.require(inputs.saveIdentity().equals(reader.statSave(savePath)),
                "original SAVE native identity remains stable through historical source checks");
        requireScope(inputs,clock,actualMachine,actualWorkerSourceSha256);
    }

    private static void requireScope(HistoricalInputs inputs, Clock clock, String actualMachine,
            String actualWorkerSourceSha256) {
        Instant now = clock.instant();
        StrictJson.require(!now.isBefore(inputs.observedAtUtc()) && !now.isBefore(inputs.retainedAtUtc())
                && now.isBefore(inputs.reviewAtUtc())
                && inputs.machineId().equals(actualMachine)
                && inputs.workerSourceSha256().equals(actualWorkerSourceSha256),
                "historical inputs retain the original machine/source and earliest finite read-ticket deadline");
    }
}
