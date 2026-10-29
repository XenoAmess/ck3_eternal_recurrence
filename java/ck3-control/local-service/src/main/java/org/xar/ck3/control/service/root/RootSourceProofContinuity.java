package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.StrictJson;

/** Historical source DATA comparison. Only the caller's actual metadata and guard provide live custody. */
public final class RootSourceProofContinuity {
    private RootSourceProofContinuity() { }

    public static void requireSameSourceEpoch(byte[] predecessorProof,byte[] currentProof) {
        requireSameSourceEpoch(decode(predecessorProof),decode(currentProof));
    }

    /** v3 retains complete original Witnesses. Allocation, change time and link count are not immutable identity. */
    public static void requireSameSourceEpoch(NativeSourceProofDocument before,NativeSourceProofDocument after) {
        Objects.requireNonNull(before);Objects.requireNonNull(after);
        StrictJson.require(before.machineId().equals(after.machineId())&&before.sessionId().equals(after.sessionId())
                &&before.mode()==after.mode()&&before.hostConfiguration().equals(after.hostConfiguration())
                &&before.source().equals(after.source())&&before.ownerSourceEpoch().equals(after.ownerSourceEpoch())
                &&before.sourceEpochManifest().equals(after.sourceEpochManifest())&&before.gameExecutable().equals(after.gameExecutable())
                &&before.completeEvidenceClosure().equals(after.completeEvidenceClosure())
                &&before.liveWitnesses().size()==after.liveWitnesses().size(),
                "actual Root software/source epoch or original native file Witness changed");
        for(int index=0;index<before.liveWitnesses().size();index++)
            StrictJson.require(before.liveWitnesses().get(index).sameImmutableFile(after.liveWitnesses().get(index)),
                    "actual Root original native source file identity changed");
    }

    public static void requireRetainedSourceContinuation(byte[] predecessorProof,byte[] currentProof) {
        var before=decode(predecessorProof);var after=decode(currentProof);
        requireSameSourceEpoch(before,after);
        StrictJson.require(!Instant.parse(before.observedAtUtc()).isAfter(Instant.parse(after.observedAtUtc())),
                "retained source proof observation regressed");
    }

    private static NativeSourceProofDocument decode(byte[] original) {
        try{return NativeSourceProofCodec.decode(original);}
        catch(IOException invalid){throw new IllegalArgumentException(
                "actual original v3 native source Witness proof required; v2 identity is missing",invalid);}
    }
}
