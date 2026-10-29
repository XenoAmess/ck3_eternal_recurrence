package org.xar.ck3.control.application.driver;

import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public DATA from one preserved complete Native/Driver frame. Performs no observation or submission. */
public final class DriverPublicContext {
    private DriverPublicContext() { }

    /** Diagnostics retain their exact location in this full public snapshot, including public decimal identities. */
    public record Context(RawJson snapshot, RawJson diagnostics) {
        public Context {
            Objects.requireNonNull(snapshot);
            Objects.requireNonNull(diagnostics);
            // Use the sole public decoder to reject unencoded or malformed identity roles.
            PublicSnapshotCodec.decode(snapshot);
            OpportunityJson.Obj original = DriverJson.object(snapshot.bytes(), RawJson.MAXIMUM_BYTES);
            OpportunityJson.Obj actualDiagnostics = OpportunityJson.object(original.get("diagnostics"), "diagnostics");
            OpportunityJson.Obj suppliedDiagnostics = DriverJson.object(diagnostics.bytes(), RawJson.MAXIMUM_BYTES);
            StrictJson.require(actualDiagnostics.equals(suppliedDiagnostics),
                    "public Driver diagnostics crossed their actual complete snapshot");
        }
    }

    /**
     * Uses the supplied frame's already archived Native/Driver join. The caller supplies the retained
     * original frame for before, or the separately verified READ frame for after; this method cannot
     * turn a cached frame into an independent observation.
     */
    public static Context from(DriverObservationAssembler.Complete actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(DriverObservationAssembler.bindingSha256(actual.semantic()).equals(actual.fullBindingSha256()),
                "public Driver context differs from its complete frame binding");
        RawJson snapshot = PublicSnapshotCodec.encode(PublicSnapshotCodec.export(actual, true));
        OpportunityJson.Obj publicSnapshot = DriverJson.object(snapshot.bytes(), RawJson.MAXIMUM_BYTES);
        OpportunityJson.Obj diagnostics = OpportunityJson.object(publicSnapshot.get("diagnostics"), "diagnostics");
        return new Context(snapshot, RawJson.fullMaterial(DriverJson.encode(diagnostics)));
    }
}
