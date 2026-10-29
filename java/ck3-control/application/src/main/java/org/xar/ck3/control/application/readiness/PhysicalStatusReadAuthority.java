package org.xar.ck3.control.application.readiness;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** One actual source-owned raw Status read scope. It has no Driver, Ready, action or save capability. */
public interface PhysicalStatusReadAuthority {
    record Lease(NativeObservationPort.ObservedFrame frame,PhysicalStatusIdentity identity,Set<String> bridgeCapabilities,Instant validUntil) {
        public Lease {
            Objects.requireNonNull(frame);Objects.requireNonNull(identity);bridgeCapabilities=Set.copyOf(bridgeCapabilities);Objects.requireNonNull(validUntil);
            StrictJson.require(frame.session().equals(identity.transport())&&frame.snapshotId().equals(identity.snapshotId())
                    &&frame.nativeRevision().equals(identity.nativeRevision())&&frame.observedAt().equals(identity.observedAt())
                    &&frame.originalPacket().length==identity.nativeEvidence().bytes()
                    &&ActionCodec.sha256(frame.originalPacket()).equals(identity.nativeEvidence().sha256()),"physical lease changed its actual original packet/header");
            StrictJson.require(!validUntil.isBefore(frame.observedAt()),"physical read lease validity regressed");
        }
    }
    @FunctionalInterface interface CheckedWork<T>{T apply(Lease actual)throws IOException;}
    default <T>T withObserved(ContinuityStorePort.Session same,Instant deadline,CheckedWork<T> work)throws IOException,InterruptedException{
        throw new IOException("actual source-owned physical Status capture is unavailable");
    }
    default <T>T current(ContinuityStorePort.Session same,PhysicalStatusIdentity expected,Instant deadline,CheckedWork<T> work)throws IOException{
        throw new IOException("actual held-only physical Status scope is unavailable");
    }
    default void requireOutside(ContinuityStorePort.Session same)throws IOException{
        throw new IOException("actual physical Status action boundary is unavailable");
    }
    default PlanningReadGuard verify(WriterContracts.Head actualHead,PlanningReadRequest request,ReadContract<?> exactContract)throws IOException{
        throw new IOException("actual physical Status guard issuer is unavailable");
    }
    default PhysicalStatusIdentity verifyArchived(GuardEvidence original,ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session same,
            OriginalEvidencePort originals)throws IOException{
        throw new IOException("actual original physical Status guard verifier is unavailable");
    }
}
