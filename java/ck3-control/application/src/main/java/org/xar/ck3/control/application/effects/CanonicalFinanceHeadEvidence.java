package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact mutable writer input and immutable archive output remain separate identities. */
public final class CanonicalFinanceHeadEvidence {
    private CanonicalFinanceHeadEvidence() { }
    public static ExactRef preserve(Session session,ExactRef actualPersistedHead,ActionPorts.OutcomeArchive sameWriterArchive,int maximumBytes) throws IOException {
        Objects.requireNonNull(session);Objects.requireNonNull(actualPersistedHead);Objects.requireNonNull(sameWriterArchive);
        StrictJson.require(maximumBytes>0&&maximumBytes<=StrictJson.EXPLICIT_MAX_BYTES,"bounded actual head original read required");
        StrictJson.require(session.persistedHead().equals(actualPersistedHead),"finance quote head differs from the actual same-lock writer head");
        var originalPin=session.capturePin(actualPersistedHead,maximumBytes);session.verifyPin(originalPin);
        // This seam performs the actual same-lock raw file read and verifies its native identity after the read.
        byte[] bytes=session.readPinned(originalPin,maximumBytes);RootGuardChecks.exact(actualPersistedHead,bytes);
        RawJson original=new RawJson(bytes);ExactRef archived=sameWriterArchive.preserveMaterial(original);
        StrictJson.require(original.equals(sameWriterArchive.loadMaterial(archived)),"finance quote head archive readback changed its original bytes");
        RootGuardChecks.exact(archived,bytes);session.verifyPin(originalPin);
        StrictJson.require(session.persistedHead().equals(actualPersistedHead),"finance quote head changed while archiving the original");
        return archived;
    }
}
