package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.Arrays;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;

/** Archive-only binder for the exact retained once-Close. It grants a finite read profile, never Close or Control. */
public final class RootPendingUiCloseReconciliation {
    public static final String CONTRACT="lifecycle/pending-successor-close-reconciliation12004/v1";
    private RootPendingUiCloseReconciliation(){ }
    public static void requireProfile(ReadContract<?> actual){
        require(actual.contractId().equals(CONTRACT)&&actual.operation().value().equals(NativeTimelineBlocker12004.QUERY_STEP)
                &&actual.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION&&actual.requiredCapability().isEmpty()
                &&actual.permissionKey().equals("allow_private_current_timeline_blocker_query")
                &&actual.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&actual.hasPureReplay(),"exact source-owned pure Close reconciliation profile required");
    }
    public static void requireRequest(PlanningReadRequest request,ActionReceipt original,ActionState.Attempt attempt,
            Complete before,Complete actual,ActionPorts.OutcomeArchive originals)throws IOException {
        require(request.origin() instanceof CommandOrigin.Reconciliation&&request.arguments().members().isEmpty()
                &&request.operation().value().equals(NativeTimelineBlocker12004.QUERY_STEP),"Close reconciliation changed its exact read profile/arguments");
        var identity=request.origin().requireReconciliation();var pending=identity.pending();var command=original.command();
        require(command.origin() instanceof CommandOrigin.Gameplay&&command.operation().value().equals(NativeTimelineBlocker12004.CLOSE_STEP)
                &&command.expected().observerSchema().equals("xar.java.pending-successor-modal-close/v1")
                &&command.actionId().equals(pending.actionId())&&original.bodySha256().equals(pending.bodySha256())
                &&attempt.requestId().equals(pending.requestId())&&command.before().equals(pending.originalBefore())
                &&ActionTransitions.attempt(original.state()).orElseThrow().equals(attempt)
                &&before.identity().equals(command.before())&&actual.identity().equals(identity.factual())
                &&command.source().equals(actual.source())&&command.sessionId().equals(actual.sessionId())
                &&request.source().equals(actual.source())&&request.sessionId().equals(actual.sessionId())
                &&actual.connectionGeneration().equals(attempt.guard().connectionGeneration()),"reconciliation changed actual original Close/Attempt/Game/source/session/connection");
        var prepared=attempt.preparedRequest();require(prepared.step().equals(command.operation().value())&&prepared.requiredCapability().isEmpty()
                &&prepared.preparationEvidence().size()==5,"original Close preparation roles differ");
        var refs=prepared.preparationEvidence();var body=originals.loadMaterial(refs.get(0));
        require(body.bytes().length==refs.get(0).bytes()&&DriverDigest.sha(body.bytes()).equals(refs.get(0).sha256()),"original pending domain archive copy changed");
        var document=NaturalClockOriginals.decode(body.bytes());var projection=document.pendingProjection().orElseThrow();
        var obligation=SuccessorUiObligationCodec.decode(originals.loadMaterial(projection.currentObligation()).bytes());var intent=obligation.closeAttempt().orElseThrow();
        require(intent.receipt().isEmpty()&&intent.actionId().equals(command.actionId())&&intent.commandBodySha256().equals(original.bodySha256())
                &&intent.originalCommand().equals(refs.get(3))&&Arrays.equals(originals.loadMaterial(refs.get(3)).bytes(),ActionCodec.encodeCommand(command))
                &&obligation.binding().qualifiedCause().equals(refs.get(1))&&obligation.observation().orElseThrow().timelineRead().equals(refs.get(2))
                &&attempt.guard().authorityId().equals("root-pending-successor-ui:"+obligation.binding().causeDigest())
                &&obligation.binding().successorCharacterId().equals(actual.identity().frame().identity().player())
                &&obligation.binding().successorEpisodeRunId().equals(actual.identity().frame().episodeRunId()),"original once intent/cause/actual successor differs");
        // The archived copy is compared with the actual canonical domain at the original guard's writer point.
        require(originals instanceof NativeOutcomeArchive,"Close replay requires the actual Root archive/writer custody");
        var bound=(NativeOutcomeArchive)originals;var same=bound.writer().borrowedSession();var point=RootGuardEvidence.writerPoint(attempt.guard(),originals);
        var state=same.requireHistoricalState(point.sequence(),point.digest());var canonical=DomainBodies.reference(state,DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS).orElseThrow();
        require(canonical.contractSchema().equals(NaturalClockOriginals.SCHEMA)&&canonical.payload().bytes()==refs.get(0).bytes()
                &&canonical.payload().sha256().equals(refs.get(0).sha256()),"archive copy is not the genuine committed original pending domain");
        RootGuardEvidence.requireHistory(attempt.guard(),originals,same);
        var first=originals.loadRead(refs.get(4));require(first.request().operation().value().equals(NativeTimelineBlocker12004.QUERY_STEP)
                &&first.request().source().equals(command.source())&&first.request().sessionId().equals(command.sessionId()),"original Close admission query changed source/operation");
        var dispatch=ActionTransitions.dispatch(original.state()).orElseThrow();
        byte[] outbound=dispatch instanceof NativeActionPort.AckReceived ack?ack.outbound().orElseThrow().originalPacket()
                :((NativeActionPort.Unknown)dispatch).originalRequestPacket();
        var wire=NativeWire.decodeExecuteRequest(outbound);
        require(wire.requestId().equals(attempt.requestId())&&wire.step().equals(command.operation().value())
                &&wire.expectedRevision().orElseThrow().equals(command.before().frame().identity().nativeRevision())
                &&StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(StrictJson.parse(prepared.additionalFields().bytes())),"retained actual outbound is not the original once-Close request");
    }
    private static final class DriverDigest {private static String sha(byte[] bytes){return org.xar.ck3.control.application.driver.DriverJson.sha256(bytes);}}
}
