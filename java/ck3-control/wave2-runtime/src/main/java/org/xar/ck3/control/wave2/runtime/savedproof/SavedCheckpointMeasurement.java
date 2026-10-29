package org.xar.ck3.control.wave2.runtime.savedproof;

import java.time.Instant;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Issued only by this package's completed managed measurement, never a JSON GREEN loader. */
public final class SavedCheckpointMeasurement {
    private final SavedProofReadTicket ticket;
    private final RecoveryEvidence canonical;
    private final RecoveryEvidence transport;
    private final ExactRef driver;
    private final FileStatIdentity driverIdentity;
    private final String checkpointDigest;
    private final String workerSourceSha256;
    private final Instant observedAt;

    SavedCheckpointMeasurement(SavedProofReadTicket ticket, RecoveryEvidence canonical,
            RecoveryEvidence transport, ExactRef driver, FileStatIdentity driverIdentity,
            String checkpointDigest, String workerSourceSha256, Instant observedAt) {
        this.ticket = ticket; this.canonical = canonical; this.transport = transport;
        this.driver = driver; this.driverIdentity = driverIdentity;
        this.checkpointDigest = checkpointDigest; this.workerSourceSha256 = workerSourceSha256;
        this.observedAt = observedAt;
    }
    public String machineId() { return ticket.machineId(); }
    public Instant observedAtUtc() { return observedAt; }
    public Instant reviewAtUtc() { return ticket.reviewAt(); }
    public String nonce() { return ticket.nonce(); }
    public ExactRef releaseRef() { return ticket.release().reference(); }
    public ExactRef canonicalCheckpointProof() { return canonical.reference(); }
    public RecoveryEvidence canonicalReceipt() { return canonical; }
    public RecoveryEvidence originalTransportObservation() { return transport; }
    public ExactRef validatorSource() { return ticket.validatorSource(); }
    public ExactRef sdkFreeze() { return ticket.sdkFreeze(); }
    public String checkpointDigest() { return checkpointDigest; }
    public String workerSourceSha256() { return workerSourceSha256; }
    public ExactRef driver() { return driver; }
    public FileStatIdentity driverIdentity() { return driverIdentity; }
    public ExactRef save() { return ticket.save(); }
    public FileStatIdentity saveIdentity() { return ticket.saveIdentity(); }
}
