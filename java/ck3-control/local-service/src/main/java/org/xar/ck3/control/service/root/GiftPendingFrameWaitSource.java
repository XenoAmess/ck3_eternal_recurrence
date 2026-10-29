package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.ReadonlyPlanningRetry;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.Frame;

/** The source-owned post-freeze wait. It only receives Native snapshots; no business or receipt-query request is prepared. */
final class GiftPendingFrameWaitSource {
    @FunctionalInterface interface OriginalPending { void require(Session same)throws IOException; }
    private final RootRuntimeContext context;
    private final PlanningRequest original;
    private final PendingAction pending;
    private final Frame source;
    private final ObservedFrame nativeSource;
    private final List<Pin> pins;
    private final OriginalPending originalPending;
    private final String capturedHead;
    private final Thread thread=Thread.currentThread();
    private boolean consumed;
    GiftPendingFrameWaitSource(RootRuntimeContext context,PlanningRequest original,PendingAction pending,Frame source,
            ObservedFrame nativeSource,List<Pin> pins,OriginalPending originalPending,String capturedHead) {
        this.context=Objects.requireNonNull(context);this.original=Objects.requireNonNull(original);
        this.pending=Objects.requireNonNull(pending);this.source=Objects.requireNonNull(source);
        this.nativeSource=Objects.requireNonNull(nativeSource);this.pins=List.copyOf(pins);
        this.originalPending=Objects.requireNonNull(originalPending);this.capturedHead=Objects.requireNonNull(capturedHead);
    }
    static Frame frame(Obj snapshot) {
        StrictJson.require(snapshot.members().containsKey("active_event")&&snapshot.members().containsKey("pending_character_interaction"),
                "Gift actual complete frame is missing its foreground fields");
        return GiftPendingFrameCodec.decodeSnapshot(OpportunityJson.encode(snapshot));
    }
    void afterPlanning(PlanningResult planned)throws IOException,InterruptedException {
        Objects.requireNonNull(planned);
        synchronized(this) {
            StrictJson.require(!consumed&&thread==Thread.currentThread(),"Gift pending wait token is single-use on its original public planning thread");consumed=true;
        }
        StrictJson.require(planned.trace().before().equals(original.before()),"Gift wait crossed its actual completed original plan");
        if(!ReadonlyPlanningRetry.sink().active()||planned instanceof PlanningResult.ActionSelected
                ||planned instanceof PlanningResult.Stopped||planned instanceof PlanningResult.IncompleteMigration)return;
        try {
            context.withSession(same->{
                context.writer().requireSession(same);context.requireCurrent(original.deadline());
                // A real READ flush may change the head. Keep that call's result: a stale token cannot grant a retry.
                if(!same.head().digest().equals(capturedHead))return null;
                requirePending(same);
                var physical=context.remainingDomains().lifecycle().physical();physical.requireOutsideObservationScope(same);
                var transport=context.transport();
                synchronized(transport) {
                    requireSameNative(nativeSource,transport.currentSnapshot(original.deadline()));
                    Instant now=context.clock().instant();Instant waitUntil=now.plus(GiftPendingFramePolicy.WAIT_TIMEOUT);
                    if(!waitUntil.isBefore(original.deadline()))waitUntil=original.deadline().minusNanos(1);
                    if(!now.isBefore(waitUntil))throw new IOException("original Gift planning deadline cannot contain its bounded native wait");
                    while(context.clock().instant().isBefore(waitUntil)) {
                        NativeSnapshotWaitPort.WaitResult result;
                        try {result=transport.waitForSnapshot(waitUntil,original.deadline());}
                        catch(InterruptedException interrupted) {
                            Thread.currentThread().interrupt();var failure=new InterruptedIOException("original Gift bounded native wait interrupted");failure.initCause(interrupted);throw failure;
                        }
                        if(result instanceof NativeSnapshotWaitPort.Elapsed)throw new IOException("private faction pending same-date paused revision did not arrive");
                        physical.withReceivedSnapshot(same,original.deadline(),result.frame(),fresh->{
                            consumeFresh(same,original,pending,source,fresh,()->{
                                StrictJson.require(thread==Thread.currentThread(),"Gift proof lost its actual source planning thread");
                                context.requireCurrent(original.deadline());requirePending(same);
                                requireSameNative(result.frame(),transport.currentSnapshot(original.deadline()));
                            });return null;
                        });
                    }
                    throw new IOException("private faction pending same-date paused revision did not arrive");
                }
            });
        } catch(InterruptedIOException failure) {
            if(failure.getCause() instanceof InterruptedException interrupted)throw interrupted;throw failure;
        }
    }
    private void requirePending(Session same)throws IOException {
        context.writer().requireSession(same);originalPending.require(same);for(Pin pin:pins)same.verifyPin(pin);
    }
    /** The same production physical-to-private-marker boundary is exercised by finite original-packet/writer tests. */
    static void consumeFresh(Session same,PlanningRequest original,PendingAction pending,Frame source,
            RootLifecycleAuthority.SnapshotLease fresh,GiftPendingFrameReadyFailure.Original originalSource)throws IOException {
        Objects.requireNonNull(originalSource).require();Objects.requireNonNull(fresh).assertCurrent(same);
        var complete=fresh.ordinary().orElseThrow(()->new IOException("Gift wait changed the actual living-player native/Driver join"));
        StrictJson.require(complete.source().equals(original.source())&&complete.sessionId().equals(original.sessionId())
                &&complete.identity().game().equals(original.before().game())
                &&complete.identity().machineId().equals(original.before().machineId()),"Gift bounded wait crossed its original current Game/source/session");
        Frame current=frame(complete.semantic());
        StrictJson.require(org.xar.ck3.control.application.planning.finance.GiftProcessIdentity.compare(pending.sourceProcess(),complete.identity().game())
                    ==org.xar.ck3.control.application.planning.finance.GiftProcessIdentity.Relation.SAME
                &&current.bridgePid().equals(source.bridgePid())&&current.connectionGeneration().equals(source.connectionGeneration()),
                "Gift bounded wait changed its actual process or Native connection owner");
        if(!GiftPendingFramePolicy.changedOrReady(pending,source,current))return;
        var proof=GiftPendingFramePolicy.acceptFresh(pending,source,current);boolean[] live={true};
        try {
            var failure=GiftPendingFrameReadyFailure.issue(same,original,proof,()->{
                StrictJson.require(live[0],"Gift proof left its actual source callback");
                originalSource.require();fresh.assertCurrent(same);
                StrictJson.require(proof.equals(GiftPendingFramePolicy.acceptFresh(pending,source,frame(complete.semantic()))),
                        "Gift original full pending/frame proof changed before retry consumption");
            });
            ReadonlyPlanningRetry.giftPendingFrameFailed(failure);
            throw new IOException("actual Gift pending source retry sink returned without consuming its private marker");
        } finally {live[0]=false;}
    }
    private static void requireSameNative(ObservedFrame expected,ObservedFrame actual) {
        StrictJson.require(expected.session().equals(actual.session())&&expected.snapshotId().equals(actual.snapshotId())
                &&expected.nativeRevision().equals(actual.nativeRevision())&&expected.observedAt().equals(actual.observedAt())
                &&Arrays.equals(expected.state().bytes(),actual.state().bytes())&&Arrays.equals(expected.originalPacket(),actual.originalPacket()),
                "Gift wait source is not the exact retained accepted original Native packet");
    }
}
