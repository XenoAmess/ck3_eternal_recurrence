package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Archived projected originals, still not a canonical child/parent terminal.
 * Creation follows real scope close and the actual SDK frame's live projection.
 * Loading is historical full-frame replay and never creates a receiver token. */
public record PreparedCleanupParentProjection(ExactRef reference,ExactRef preparationReference,ExactRef captureReference,
        AdvanceObservationPort.Frame starting,AdvanceObservationPort.Frame ending) {
    public static final String SCHEMA="xar.prepared-cleanup-projected-parent-originals/v1";
    public PreparedCleanupParentProjection {
        Objects.requireNonNull(reference);Objects.requireNonNull(preparationReference);Objects.requireNonNull(captureReference);
        Objects.requireNonNull(starting);Objects.requireNonNull(ending);
    }
    public static PreparedCleanupParentProjection preserve(PreparedCleanupEvidence.Prepared prepared,ExactRef captureReference,
            AdvanceObservationPort.Frame starting,AdvanceObservationPort.Frame ending,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        requireProjection(prepared,PreparedCleanupEvidence.loadPostAckCaptured(captureReference,archive,frames),captureReference,starting,ending,archive);
        var row=StrictJson.object();row.put("schema",SCHEMA);row.set("preparation",prepared.reference().toJson());row.set("capture",captureReference.toJson());
        row.set("starting",toNode(LifeAdvanceEvidence.frame(LifeAdvanceEvidence.preserveFrame(starting,archive))));
        row.set("ending",toNode(LifeAdvanceEvidence.frame(LifeAdvanceEvidence.preserveFrame(ending,archive))));
        var reference=archive.preserveMaterial(new RawJson(StrictJson.canonical(row,64*1024)));
        var loaded=load(reference,archive,frames);
        require(loaded.starting().equals(starting)&&loaded.ending().equals(ending),"projected originals changed their actual complete frames");
        return loaded;
    }
    public static PreparedCleanupParentProjection load(ExactRef reference,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        require(reference.bytes()>0&&reference.bytes()<=64*1024,"bounded projected-originals reference required");
        byte[] bytes=archive.loadMaterial(reference).bytes();
        require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"projected parent original bytes changed");
        var row=DriverJson.object(bytes,64*1024);
        require(row.members().keySet().equals(Set.of("schema","preparation","capture","starting","ending"))
                &&new Text(SCHEMA).equals(row.get("schema")),"projected parent original schema differs");
        var preparation=ExactRef.fromJson(toNode(object(row.get("preparation"),"preparation")));
        var captureRef=ExactRef.fromJson(toNode(object(row.get("capture"),"capture")));
        var prepared=PreparedCleanupEvidence.loadPrepared(preparation,archive,Objects.requireNonNull(frames));
        var captured=PreparedCleanupEvidence.loadPostAckCaptured(captureRef,archive,frames);
        var parent=prepared.parentReceipt().command();
        var starting=LifeAdvanceEvidence.restore(parent,LifeAdvanceEvidence.decodeFrame(object(row.get("starting"),"starting"),false),archive,frames);
        var ending=LifeAdvanceEvidence.restore(parent,LifeAdvanceEvidence.decodeFrame(object(row.get("ending"),"ending"),false),archive,frames);
        requireProjection(prepared,captured,captureRef,starting,ending,archive);
        return new PreparedCleanupParentProjection(reference,preparation,captureRef,starting,ending);
    }
    private static void requireProjection(PreparedCleanupEvidence.Prepared prepared,PreparedCleanupEvidence.PostAckCaptured captured,
            ExactRef captureRef,AdvanceObservationPort.Frame starting,AdvanceObservationPort.Frame ending,ActionPorts.OutcomeArchive archive) {
        PreparedCleanupEvidence.requirePostAckCaptured(captured);var parent=prepared.parentReceipt().command();var raw=captured.afterFrame();
        require(captured.binding().prepared().reference().equals(prepared.reference())&&starting.identity().equals(parent.before())
                &&starting.source().equals(parent.source())&&starting.sessionId().equals(parent.sessionId()),"projected parent changed original prepared/start binding");
        require(ending.source().equals(parent.source())&&ending.sessionId().equals(parent.sessionId())
                &&ending.identity().machineId().equals(raw.session().machineId())&&ending.identity().game().equals(raw.session().game())
                &&ending.identity().frame().snapshotId().equals(raw.snapshotId())&&ending.identity().frame().identity().nativeRevision().equals(raw.nativeRevision())
                &&ending.observedAt().equals(raw.observedAt())&&ending.originalEvidence().bytes()==raw.originalPacket().length
                &&ending.originalEvidence().sha256().equals(ActionCodec.sha256(raw.originalPacket()))
                &&ending.identity().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                &&ending.identity().frame().identity().player().equals(parent.before().frame().identity().player())
                &&ending.identity().frame().identity().dateRaw().equals(prepared.command().before().frame().identity().dateRaw()),
                "projected parent is not the actual raw captured same-owner partial frame");
        require(ending.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,"projected parent needs its recorded fresh query");
        var query=(ObservationProvenance.FreshSnapshotQuery)ending.provenance();
        ObservationProvenance.FreshSnapshotBasis expectedBasis;
        if(PreparedCleanupSuccessorEvidence.isSuccessor(prepared)){
            var predecessor=(ActionState.PreparedCleanupNoEffectConfirmed)prepared.children().getLast().state();
            expectedBasis=new ObservationProvenance.PreparedCleanupSuccessorWatch(prepared.parentReference(),prepared.childReferences().getLast(),
                    predecessor.proofReference(),prepared.reference(),captureRef);
        }else expectedBasis=new ObservationProvenance.PreparedCleanupWatch(prepared.parentReference(),prepared.reference(),captureRef);
        require(query.basis().equals(expectedBasis)
                &&query.requestId().equals(captured.freshSnapshotAck().requestId())
                &&query.readAcknowledgement().equals(archive.referenceOf(captured.freshSnapshotAck()))
                &&query.snapshotReceived().equals(captured.snapshotReceived()),"projected parent changed actual capture provenance");
    }
}
