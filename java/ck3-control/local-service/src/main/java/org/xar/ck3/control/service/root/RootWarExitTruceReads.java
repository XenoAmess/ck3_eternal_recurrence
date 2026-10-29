package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarExitTruceReads;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;

/** Same installed Truce family in the actual canonical pending scope. It never starts a reconciliation or ordinary read. */
public final class RootWarExitTruceReads implements NativeWarExitEffects.TruceReadPort {
    private final RootRuntimeContext context;
    private final ArmyWarExitTruceReads reads;
    public RootWarExitTruceReads(RootRuntimeContext context,ArmyWarExitTruceReads sameInstalled) {
        this.context=Objects.requireNonNull(context);reads=Objects.requireNonNull(sameInstalled);
        // Root inventory is not yet bound here. No placeholder catalog/permission is manufactured.
    }
    public static boolean accepts(ActionCommand original) {
        Objects.requireNonNull(original);
        if(!(original.origin() instanceof CommandOrigin.Gameplay)
                ||!original.expected().observerSchema().equals(OrdinaryWarExitObservation.SCHEMA))return false;
        try { NativeWarExitEffects.warId(original.operation());return true; }
        catch(IllegalArgumentException|ArithmeticException invalid) {return false;}
    }
    @Override public Optional<PlanningReadReceipt> read(ActionCommand original,ActionState.Attempt attempt,Complete after,int toward) {
        if(!accepts(original))return Optional.empty();
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);
            // Initial dispatch has no original-pending Root lease: remain Pending, never fall back to gameplay-paused reads.
            if(!context.reconciliation().hasActiveFor(same,original))return Optional.empty();
            return context.reconciliation().currentForCommand(same,original,lease->{
                StrictJson.require(lease.attempt().equals(attempt)&&lease.complete().equals(after),"truce read changed actual pending Attempt or after-frame");
                var query=NativeWarExitEffects.truceQuery(original,lease.before(),after).orElseThrow();
                StrictJson.require(query.towardCharacterId()==toward,"truce read borrowed another opponent");
                Instant physical=lease.observationGuard().validUntil(),window=ActionObservationWindow.deadline(original);
                Instant deadline=physical.isBefore(window)?physical:window;
                StrictJson.require(context.clock().instant().isBefore(deadline),"original truce observation window expired");
                var selected=new ArmyWarExitTruceReads.Selection(lease.identity(),original,attempt,lease.before(),after,deadline);
                var result=reads.collect(same,context.readCatalog(),selected);lease.assertCurrent(same);
                if(!(result instanceof PlanningReadResult.Known<?> known))return Optional.empty();
                var receipt=known.receipt();
                // Same persisted receipt and same installed pure decoder are required by the observer and cold importer.
                NativeRecordedEvidenceVerifier.requireRead(receipt,context.archive().withSession(same));
                lease.assertCurrent(same);return Optional.of(receipt);
            });
        }catch(IOException unavailable){throw new UncheckedIOException("actual original-pending truce observation unavailable; no primitive replay",unavailable);}
    }
    @Override public void replay(Complete after,int toward,PlanningReadReceipt receipt) {
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
            var identity=receipt.request().origin().requireReconciliation();var canonical=original(identity,archive);
            var attempt=ActionTransitions.attempt(canonical.state()).orElseThrow();var before=before(same,attempt,archive);
            for(var guard:List.of(receipt.before(),receipt.after())) {
                var actual=context.reconciliation().verifyArchived(guard.binding(),archive,same,context.originals());
                StrictJson.require(actual.equals(after)&&actual.identity().equals(identity.factual())
                        &&NativeEffectEvidence.basis(actual).driverFacts().equals(identity.evidence().observationManifest()),"truce replay changed actual original factual Native/Driver frame");
            }
            var query=NativeWarExitEffects.truceQuery(canonical.command(),before,after).orElseThrow();
            StrictJson.require(query.towardCharacterId()==toward,"archived truce changed its original directed opponent");
            var selected=new ArmyWarExitTruceReads.Selection(identity,canonical.command(),attempt,before,after,receipt.request().deadline());
            reads.replay(context.readCatalog(),selected,receipt);
            context.writer().requireSession(same);
        }catch(IOException unavailable){throw new UncheckedIOException("actual installed original truce replay unavailable",unavailable);}
    }
    private Complete before(Session same,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive)throws IOException {
        RootGuardEvidence.requireHistory(attempt.guard(),archive,same);
        return RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
    }
    private static ActionReceipt original(ReconciliationIdentity identity,ActionPorts.OutcomeArchive archive) {
        var retained=archive.loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(archive.receiptReferenceOf(retained).equals(identity.pending().originalReceipt())&&!retained.settled()&&accepts(retained.command())&&retained.command().actionId().equals(identity.pending().actionId())
                &&retained.bodySha256().equals(identity.pending().bodySha256())&&ActionCodec.bodySha256(retained.command()).equals(retained.bodySha256())
                &&retained.command().before().equals(identity.pending().originalBefore())&&retained.command().source().equals(identity.source())
                &&retained.command().sessionId().equals(identity.sessionId())&&ActionTransitions.attempt(retained.state()).orElseThrow().requestId().equals(identity.pending().requestId()),
                "truce identity is not the exact retained canonical unresolved primitive");return retained;
    }
}
