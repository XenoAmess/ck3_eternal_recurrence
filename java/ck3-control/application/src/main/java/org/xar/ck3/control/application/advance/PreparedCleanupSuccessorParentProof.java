package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Pure parent DATA replay for the distinct sixth prepared cleanup child. No live
 * receiver token, Guard, parent continuation or checkpoint/day credit is issued.
 * The installed Root must independently replay actual source/backend qualification. */
public final class PreparedCleanupSuccessorParentProof {
    private PreparedCleanupSuccessorParentProof() { }
    public static void requirePrefix(PreparedCleanupParentEvidence.Originals data,ActionPorts.OutcomeArchive archive) {
        var prepared=data.prepared();var original=prepared.parentReceipt();var children=data.children();
        require(PreparedCleanupSuccessorEvidence.isSuccessor(prepared),"successor parent requires its distinct C5 NoEffect preparation");
        var strict=PreparedCleanupSuccessorEvidence.loadPreparedOriginals(prepared.reference(),archive);
        require(strict.parentReceipt().equals(original)&&strict.parentReference().equals(prepared.parentReference())
                &&strict.children().equals(prepared.children())&&strict.childReferences().equals(prepared.childReferences())
                &&strict.command().equals(prepared.command())&&strict.nativePrepared().equals(prepared.nativePrepared())
                &&strict.preparationNonce().equals(prepared.preparationNonce())&&strict.deadline().equals(prepared.deadline())
                &&strict.aProofReference().equals(prepared.aProofReference())&&strict.authorizationReference().equals(prepared.authorizationReference()),
                "successor parent substituted its strict v2 preparation originals");
        require(original.state() instanceof ActionState.CompositeUnknown&&children.size()==6&&data.childReferences().size()==6
                &&data.childReferences().stream().distinct().count()==6,"prepared parent requires all six distinct actual original children");
        require(children.subList(0,5).equals(prepared.children())&&data.childReferences().subList(0,5).equals(prepared.childReferences())
                &&children.stream().allMatch(ActionReceipt::settled),"prepared parent changed or omitted its original five settled children");
        var previous=((ActionState.CompositeUnknown)original.state()).execution();var execution=data.execution();
        require(execution.handlerId().equals(previous.handlerId())&&execution.startedAt().equals(previous.startedAt())
                &&execution.guard().equals(previous.guard())&&execution.children().size()==6
                &&execution.children().subList(0,5).equals(previous.children()),"prepared parent changed original execution/guard/deadline/prefix");
        for(int i=0;i<6;i++) {var child=children.get(i);var bound=execution.children().get(i);
            require(bound.actionId().equals(child.command().actionId())&&bound.bodySha256().equals(child.bodySha256()),"prepared parent child ordinal/body differs");}
        var sixth=children.getLast();require(sixth.state() instanceof PreparedCleanupAction,"prepared parent final child is not its explicit new-role state");
        var state=(PreparedCleanupAction)sixth.state();
        require(state.phase()==PreparedCleanupAction.Phase.CONFIRMED&&state.preparationReference().equals(prepared.reference())
                &&state.capturedPostAcknowledgement().filter(data.captureReference()::equals).isPresent()
                &&state.lateBindingReference().filter(data.lateBindingReference()::equals).isPresent()
                &&state.originalDispatch().filter(data.capture().cancellationAcknowledgement()::equals).isPresent()
                &&sixth.command().equals(prepared.command())&&sixth.bodySha256().equals(ActionCodec.bodySha256(prepared.command()))
                &&sixth.sequence()>children.get(4).sequence(),"prepared parent lacks exact confirmed sixth child/preparation/capture originals");
        var replayed=PreparedCleanupReplay.verifyOriginals(sixth,archive);
        require(replayed.reference().equals(prepared.reference())&&data.capture().binding().prepared().reference().equals(prepared.reference()),
                "prepared parent borrowed another actual preparation or post-ACK capture");
        PreparedCleanupEvidence.requirePostAckCaptured(data.capture());
    }
    public static void requireFrames(PreparedCleanupParentEvidence.Loaded loaded,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var data=loaded.originals();requirePrefix(data,archive);var prepared=data.prepared();var parent=prepared.parentReceipt().command();
        var replayed=PreparedCleanupReplay.verify(data.children().getLast(),archive,Objects.requireNonNull(frames));
        require(replayed.reference().equals(prepared.reference()),"prepared parent complete sixth-child replay differs");
        var starting=loaded.starting();var ending=loaded.ending();var raw=data.capture().afterFrame();
        require(starting.identity().equals(parent.before())&&starting.source().equals(parent.source())&&starting.sessionId().equals(parent.sessionId()),
                "prepared parent starting frame differs from the exact original command");
        require(ending.source().equals(parent.source())&&ending.sessionId().equals(parent.sessionId())
                &&ending.identity().machineId().equals(raw.session().machineId())&&ending.identity().game().equals(raw.session().game())
                &&ending.identity().frame().snapshotId().equals(raw.snapshotId())&&ending.identity().frame().identity().nativeRevision().equals(raw.nativeRevision())
                &&ending.observedAt().equals(raw.observedAt())&&ending.originalEvidence().bytes()==raw.originalPacket().length
                &&ending.originalEvidence().sha256().equals(ActionCodec.sha256(raw.originalPacket()))
                &&ending.identity().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                &&ending.identity().frame().identity().player().equals(parent.before().frame().identity().player()),
                "prepared parent strict projected frame crossed actual captured packet/source/owner/episode");
        var nativeState=DriverJson.object(raw.state().bytes(),RawJson.MAXIMUM_BYTES);
        require(ending.identity().frame().identity().dateRaw().equals(integer(nativeState.get("date_raw"),"date_raw"))
                &&ending.identity().frame().identity().dateRaw().equals(prepared.command().before().frame().identity().dateRaw())
                &&new Bool(true).equals(ending.semantic().get("paused"))&&new Bool(true).equals(ending.semantic().get("map_ready"))
                &&new Bool(true).equals(object(ending.semantic().get("played_character"),"played_character").get("alive")),
                "prepared parent semantic projection changed its real alive paused partial date");
        var delta=ending.identity().frame().identity().dateRaw().subtract(AdvancePlan.decode(parent).startingDateRaw());
        require(delta.signum()>0&&delta.mod(AdvancePlan.DAY).signum()==0
                &&ending.identity().frame().identity().dateRaw().compareTo(AdvancePlan.decode(parent).targetDateRaw())<0,
                "prepared parent accepts only the actual positive partial interval, never target completion");
        requireProvenance(data,ending,archive);
    }

    public static void requireProvenance(PreparedCleanupParentEvidence.Originals data,AdvanceObservationPort.Frame ending,
            ActionPorts.OutcomeArchive archive) {
        require(ending.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,"prepared parent requires its actual independent final full-state READ");
        var query=(ObservationProvenance.FreshSnapshotQuery)ending.provenance();
        require(query.basis() instanceof ObservationProvenance.PreparedCleanupSuccessorWatch,"prepared parent may not relabel an old same-Game/pause watch");
        var basis=(ObservationProvenance.PreparedCleanupSuccessorWatch)query.basis();
        var predecessor=data.prepared().children().get(4);
        require(predecessor.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed,"successor provenance predecessor is not C5 NoEffect");
        var predecessorState=(ActionState.PreparedCleanupNoEffectConfirmed)predecessor.state();
        var acknowledgement=data.capture().freshSnapshotAck();acknowledgement.custody().orElseThrow().verify(acknowledgement);
        require(basis.originalParentReceipt().equals(data.prepared().parentReference())
                &&basis.predecessorNoEffectReceipt().equals(data.prepared().childReferences().get(4))
                &&basis.predecessorNoEffectProof().equals(predecessorState.proofReference())
                &&basis.preparationReference().equals(data.prepared().reference())&&basis.captureReference().equals(data.captureReference())
                &&query.requestId().equals(data.capture().freshSnapshotAck().requestId())
                &&query.readAcknowledgement().equals(archive.referenceOf(data.capture().freshSnapshotAck()))
                &&query.snapshotReceived().equals(data.capture().snapshotReceived()),"prepared parent provenance substituted parent/C5 terminal/C5 proof/preparation/capture or actual final READ originals");
        require(archive.load(query.readAcknowledgement()).equals(data.capture().freshSnapshotAck()),"prepared parent final fresh ACK original changed");
    }
    /** Exact existing partial-progress observation algorithm; checkpoint_eligible stays false. */
    public static ActionState.EffectObservation expectedEffect(ActionCommand parent,AdvanceObservationPort.Frame ending,ExactRef basisReference) {
        return LifeAdvanceComposite.observation(parent,AdvancePlan.decode(parent),ending,
                AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS,null,List.of(basisReference));
    }
    public static void verifyReceipt(ActionReceipt receipt,PreparedCleanupParentEvidence.Loaded loaded,
            ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        requireFrames(loaded,archive,frames);var data=loaded.originals();var original=data.prepared().parentReceipt();
        require(receipt.command().equals(original.command())&&receipt.bodySha256().equals(original.bodySha256())
                &&receipt.sequence()>data.children().getLast().sequence()&&receipt.state() instanceof ActionState.CompositeSettled,
                "prepared parent terminal changed its immutable command/body or original child ordering");
        var settled=(ActionState.CompositeSettled)receipt.state();
        require(settled.execution().equals(data.execution())&&settled.settlement() instanceof ActionState.Applied,
                "prepared parent terminal must retain its exact six original children and ordinary partial-progress effect type");
        var actual=((ActionState.Applied)settled.settlement()).observation();
        require(actual.equals(expectedEffect(receipt.command(),loaded.ending(),data.reference()))
                &&!receipt.eligibleAdvance(),"prepared parent terminal changed the existing partial-progress values or invented checkpoint credit");
    }
}
