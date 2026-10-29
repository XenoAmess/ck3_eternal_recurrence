package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Complete archived replay; only source-proven Java notice freshness and the manifest observation timestamp may differ. */
public final class DriverPlanningEvidence {
    private DriverPlanningEvidence() { }
    private record Verified(DriverObservationAssembler.Complete frame,DriverObservationFacts facts,
            OpportunityJson.Obj manifest,org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame nativeFrame) { }
    public static void requireEquivalent(ContinuityStorePort.Session borrowed,PlanningRequest original,
            LeaseSnapshot actual,OriginalEvidencePort originals) throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(original);Objects.requireNonNull(actual);Objects.requireNonNull(originals);
        var previous=verify(borrowed,original.observations().snapshot(),actual.semantic().originalNativePacket(),originals);
        var current=verify(borrowed,actual.frame().semantic(),actual.semantic().originalNativePacket(),originals);
        StrictJson.require(previous.frame().identity().equals(original.before())&&previous.frame().source().equals(original.source())
                &&previous.frame().sessionId().equals(original.sessionId()),"original plan differs from its complete archived producer");
        StrictJson.require(current.frame().identity().equals(actual.frame().identity())&&current.frame().source().equals(actual.frame().source())
                &&current.frame().sessionId().equals(actual.frame().sessionId())
                &&sameFacts(current.facts(),actual.driver().observation().orElseThrow())
                &&Arrays.equals(current.facts().driver().encode(),actual.driver().driver().encode())
                &&current.facts().driverVersion()==actual.driver().stamp().driverVersion()
                &&current.facts().episodeEpoch()==actual.driver().stamp().episodeEpoch(),"current plan lease differs from its complete archived producer");
        StrictJson.require(previous.frame().identity().equals(current.frame().identity())&&previous.frame().source().equals(current.frame().source())
                &&previous.frame().sessionId().equals(current.frame().sessionId())
                &&previous.frame().connectionGeneration().equals(current.frame().connectionGeneration()),"complete planning source/Game/frame changed");
        var priorManifest=DriverTransportNoticeStability.manifest(previous.manifest(),previous.facts(),previous.nativeFrame());
        var currentManifest=DriverTransportNoticeStability.manifest(current.manifest(),current.facts(),current.nativeFrame());
        StrictJson.require(priorManifest.equals(currentManifest),"complete planning manifest changed beyond its observation wrapper");
        StrictJson.require(DriverTransportNoticeStability.semantic(previous.frame(),previous.facts(),previous.nativeFrame(),priorManifest)
                .equals(DriverTransportNoticeStability.semantic(current.frame(),current.facts(),current.nativeFrame(),currentManifest)),
                "complete planning facts changed; a new ordinary plan is required");
        // Source remains exact provenance DATA; implementation files do not authorize a live planning frame.
    }
    private static boolean sameFacts(DriverObservationFacts left,DriverObservationFacts right) {
        return Arrays.equals(left.driver().encode(),right.driver().encode())&&left.driverVersion()==right.driverVersion()
                &&left.episodeEpoch()==right.episodeEpoch()&&left.transport().equals(right.transport())
                &&left.snapshotId().equals(right.snapshotId())&&left.nativeRevision().equals(right.nativeRevision())
                &&left.nativeStateSha256().equals(right.nativeStateSha256())&&left.publicRevision().equals(right.publicRevision())
                &&left.observationVersion()==right.observationVersion()&&left.source().equals(right.source())
                &&left.originalSemanticFields().equals(right.originalSemanticFields())&&left.semanticFactsEvidence().equals(right.semanticFactsEvidence());
    }
    private static Verified verify(ContinuityStorePort.Session borrowed,OpportunityJson.Obj semantic,
            ExactRef originalNativePacket,OriginalEvidencePort originals) throws IOException {
        ExactRef manifestRef=DriverObservationEvidenceReader.reference(semantic.get("java_driver_facts_evidence"));
        RawJson manifest=new RawJson(read(borrowed,manifestRef,originals,DriverJson.MAX_NATIVE_BYTES));
        var row=DriverJson.object(manifest.bytes(),DriverJson.MAX_NATIVE_BYTES);
        ExactRef driverRef=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        RawJson driver=new RawJson(read(borrowed,driverRef,originals,DriverJson.MAX_NATIVE_BYTES));
        ExactRef nativeRef=Objects.requireNonNull(originalNativePacket);
        byte[] nativeBytes=read(borrowed,nativeRef,originals,DriverJson.MAX_NATIVE_BYTES+4);
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,nativeBytes);
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,driver,nativeFrame);
        var joined=new DriverObservationAssembler().assemble(nativeFrame,facts,nativeRef);
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete,"archived planning producer is not a complete ordinary observation");
        var frame=(DriverObservationAssembler.Complete)joined;
        StrictJson.require(frame.semantic().equals(semantic),"complete semantic differs from the replayed original producer");
        return new Verified(frame,facts,row,nativeFrame);
    }
    private static byte[] read(ContinuityStorePort.Session borrowed,ExactRef actual,OriginalEvidencePort originals,int maximum) throws IOException {
        StrictJson.require(actual.bytes()>0&&actual.bytes()<=maximum,"bounded complete planning original required");
        byte[] bytes=originals.read(borrowed,actual,maximum);
        StrictJson.require(bytes.length==actual.bytes()&&DriverJson.sha256(bytes).equals(actual.sha256()),"planning original bytes/SHA differ");
        return bytes;
    }
}
