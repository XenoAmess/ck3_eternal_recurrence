package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Retained real frontend observation plus a held process birth. Construction alone grants no permission. */
public record FrontendIdentity(String machineId, GameGeneration game, String frontendSessionId,
        BigInteger connectionGeneration, long bridgePid, FrontendFrame frame,
        ExactRef nativeEvidence, ExactRef capabilityEvidence) {
    public FrontendIdentity {
        StrictJson.require(machineId != null && !machineId.equals("unknown")
                && machineId.matches("[a-z0-9][a-z0-9-]{0,63}"), "explicit frontend machine identity required");
        Objects.requireNonNull(game); StrictJson.text(frontendSessionId);
        FrontendFrame.positive(connectionGeneration);
        StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL && bridgePid == game.pid(),
                "frontend bridge must be the exact held Game process");
        Objects.requireNonNull(frame); Objects.requireNonNull(nativeEvidence); Objects.requireNonNull(capabilityEvidence);
        StrictJson.require(nativeEvidence.bytes() > 0 && capabilityEvidence.bytes() > 0,
                "real native and capability evidence required");
    }
    public boolean sameSession(FrontendIdentity other) {
        return other != null && machineId.equals(other.machineId) && game.equals(other.game)
                && frontendSessionId.equals(other.frontendSessionId)
                && connectionGeneration.equals(other.connectionGeneration) && bridgePid == other.bridgePid;
    }
    /** Guard refresh may have a later real query sequence, but may not silently become a different snapshot. */
    public boolean sameGuardFrame(FrontendIdentity other) {
        if (!sameSession(other) || other.frame.querySequence().compareTo(frame.querySequence()) < 0) return false;
        if (frame instanceof FrontendFrame.Menu) return other.frame instanceof FrontendFrame.Menu;
        if (!(other.frame instanceof FrontendFrame.Snapshot after)) return false;
        FrontendFrame.Snapshot before = (FrontendFrame.Snapshot) frame;
        return before.snapshotId().equals(after.snapshotId()) && before.revision().equals(after.revision())
                && before.nativeRevision().equals(after.nativeRevision()) && before.dateRaw() == after.dateRaw();
    }
}
