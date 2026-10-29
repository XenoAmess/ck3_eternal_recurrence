package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.*;
import org.xar.ck3.control.application.planning.family.FamilyNaturalEpisodeMigration;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;

/**
 * Acceptance assertions over an already installed, genuinely pending Root. This is not an InputsProducer.
 * No Managed Game, private Current, M3 cause, native packet, permission or lease is constructed here.
 * The caller must supply the actual managed scenario; absent stages fail MISSING_NOT_RUN, never skip.
 */
public final class RootPendingUiProductionChainFixture {
    public enum Stage { ENTRY, QUERY, RESUME, PRIVATE_COPY_REFUSED, ONCE_CLOSE, UNKNOWN_RETAINED,
        DATE, EVENT, FINAL, COLD_CONTROL, LATE_ACK_CONTROL, COLD_NON_CONTROL_REFUSED, PAUSED_FALSE_REFUSED, MAP_FALSE_REFUSED,
        COLD_PRIVATE_REOPEN, ADMITTED_CURRENT_READ, ADMITTED_PUBLIC_RESUME,
        PAUSED_FALSE_RESUME_REFUSED, MAP_FALSE_RESUME_REFUSED, UNKNOWN_RESUME_TWICE_RETAINED,
        NONFINALIZED_PENDING_RETAINED, UNKNOWN_PENDING_RETAINED, COMPLETED_PAIRED_SAVE,
        COMPLETED_SAVE_UNKNOWN_RETAINED, COMPLETED_RESTORE_UNKNOWN_RETAINED,
        COMPLETED_COLD_RESTORE, COMPLETED_COLD_NEXT_INHERITANCE, COMPLETED_COLD_NEXT_FINAL }
    /** References supplied by the actual managed reopening scenario; constructing this carrier grants no authority. */
    public record ColdInputs(RootApplicationAssembly.Core core,RootApplicationSession root,RootInstalledCatalog installed) {
        public ColdInputs { Objects.requireNonNull(core);Objects.requireNonNull(root);Objects.requireNonNull(installed); }
    }
    @FunctionalInterface public interface ActualColdReopen { ColdInputs reopen() throws IOException,InterruptedException; }
    private record Captured(ActionReceipt parent,List<ActionReceipt> rows,DriverSnapshotFacts.Known known,
            WriterContracts.Head head) { }
    private final RootApplicationAssembly.Core core;
    private final RootApplicationSession root;
    private final RootRuntimeContext context;
    private final RootLifecycleRuntimeFactory.Installed lifecycle;
    private final RootPendingUiRuntime pending;
    private final ActionCommand parent;
    private final EnumSet<Stage> observed;
    private ExactRef originalUnknownClose;
    private ActionReceipt retainedUnknownClose;
    private String onceCloseId;
    private Captured completedBeforeSave;
    private RootCheckpointPublicCalls.SaveCall completedPairedSave;
    private CompletedRestoration completedRestoration;
    private ActionCommand restoredNextParent;
    private DriverStateSnapshot.Slot restoredNextGoal;
    /** Test custody of real returned objects only; this record is never a production permission. */
    private record CompletedRestoration(RootApplicationSession root,RootInstalledCatalog installed,
            RestoreCheckpointService.RestoreBinding binding,Captured afterProbes,SuccessorUiObligation completed) { }
    private record CanonicalActions(List<ActionReceipt> rows,WriterContracts.Head head) { }

    private RootPendingUiProductionChainFixture(RootApplicationAssembly.Core core,RootApplicationSession root,
            RootInstalledCatalog installed,Instant deadline)throws IOException {
        this(core,root,installed,deadline,EnumSet.noneOf(Stage.class));
    }
    private RootPendingUiProductionChainFixture(RootApplicationAssembly.Core core,RootApplicationSession root,
            RootInstalledCatalog installed,Instant deadline,EnumSet<Stage> sharedCoverage)throws IOException {
        observed=Objects.requireNonNull(sharedCoverage);
        this.core=core;this.root=root;context=installed.context();lifecycle=installed.remainingDomains().lifecycle();
        require(context.core()==core&&context.writer()==core.writer()&&context.archive()==core.archive()
                &&root.ownedBy(core)&&root.writer()==core.writer()&&root.archive()==core.archive()
                &&context.actions()==root&&context.adopted()==root.driver()
                &&context.source().equals(root.driver().source())
                &&context.game().generation().equals(root.identity().game())
                &&context.game().sessionId().equals(root.identity().sessionId()),"actual Core/Root/installed context mismatch");
        lifecycle.requireContext(context);pending=lifecycle.natural().pendingRuntime();pending.requireContext(context);
        var current=requireCurrent(deadline);parent=current.originalParent();
        require(capture().parent().state() instanceof ActionState.CompositeUnknown,"actual original pending parent is not UNKNOWN");
    }

    public static RootPendingUiProductionChainFixture attach(RootApplicationAssembly.Core core,
            RootApplicationSession root,RootInstalledCatalog installed,Instant deadline)throws IOException {
        if(core==null||root==null||installed==null||deadline==null)
            throw missing("actual managed Core, Root, installed catalog and finite deadline are required");
        return new RootPendingUiProductionChainFixture(core,root,installed,deadline);
    }

    /**
     * Runs the genuine same-connection cold issuer before any continuation. The scenario owns actual reopening;
     * this helper creates neither Managed inputs nor a runtime, cause, publication, token, native packet or lease.
     * The callback runs outside both writer scopes. A fresh catalog must be supplied before its first pending query.
     */
    public RootPendingUiProductionChainFixture coldReopen(ActualColdReopen actualReopen,Instant freshDeadline)
            throws IOException,InterruptedException {
        if(actualReopen==null||freshDeadline==null)throw missing("actual managed cold reopen provider and deadline required");
        var warm=requireCurrent(freshDeadline);var before=capture();
        var originalKnown=warm.actualKnown();var originalParent=warm.originalParent();
        var originalObligation=warm.obligation();var originalDomain=warm.canonicalDomain();
        var originalDriver=warm.originalDriver();var originalHistory=warm.originalHistoryBasis();
        var originalPublication=warm.originalPendingPublication();var originalEvidence=warm.evidence();
        ColdInputs inputs=actualReopen.reopen();
        if(inputs==null)throw missing("actual managed cold reopen provider returned no installed inputs");
        var coldContext=inputs.installed().context();var coldLifecycle=inputs.installed().remainingDomains().lifecycle();
        require(inputs.core()!=core&&inputs.root()!=root&&coldContext!=context
                &&coldLifecycle.natural().pendingRuntime()!=pending,"cold scenario reused its warm Core/Root/private issuer");
        require(coldContext.core()==inputs.core()&&inputs.root().ownedBy(inputs.core())
                &&coldContext.writer()==inputs.core().writer()&&coldContext.actions()==inputs.root()
                &&coldContext.adopted()==inputs.root().driver()&&inputs.core().sessionAccess().current()==inputs.root(),
                "actual cold Core/Root/catalog were not installed together");
        require(coldContext.source().equals(context.source())&&inputs.root().identity().equals(root.identity())
                &&coldContext.game().generation().equals(context.game().generation())
                &&coldContext.game().sessionId().equals(context.game().sessionId()),
                "same-connection cold recovery crossed physical Game/source/session");
        coldLifecycle.requireContext(coldContext);coldLifecycle.natural().pendingRuntime().requireContext(coldContext);
        Captured beforeIssuer=coldContext.withSession(same->inputs.root().driver().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw missing("actual cold Driver facts unavailable");
            var rows=List.copyOf(frozen.actions().actions());var retained=rows.stream()
                    .filter(row->row.command().actionId().equals(parent.actionId())).findFirst()
                    .orElseThrow(()->missing("actual cold original pending parent absent"));
            require(retained.command().equals(parent),"cold reopening replaced original pending parent");
            return new Captured(retained,rows,known,same.head());}));
        require(before.rows().equals(beforeIssuer.rows())&&before.parent().equals(beforeIssuer.parent())
                &&before.head().digest().equals(beforeIssuer.head().digest()),
                "actual cold reopening changed canonical actions or writer Head");
        requireSameDriver(before.known(),beforeIssuer.known());
        var cold=new RootPendingUiProductionChainFixture(inputs.core(),inputs.root(),inputs.installed(),freshDeadline,observed);
        var recovered=cold.requireCurrent(freshDeadline);var afterIssuer=cold.capture();
        requireReadOnly(beforeIssuer,afterIssuer);requireSameDriver(beforeIssuer.known(),afterIssuer.known());
        requireSameDriver(originalKnown,recovered.actualKnown());
        require(cold.parent.equals(parent)&&recovered.originalParent().equals(originalParent)
                &&recovered.obligation().equals(originalObligation)&&recovered.canonicalDomain().equals(originalDomain)
                &&recovered.originalDriver().equals(originalDriver)&&recovered.originalHistoryBasis().equals(originalHistory)
                &&recovered.originalPendingPublication().equals(originalPublication)&&recovered.evidence().equals(originalEvidence),
                "cold private issuer changed cause/epoch/obligation/parent or original Driver/history/publication evidence");
        cold.originalUnknownClose=originalUnknownClose;cold.retainedUnknownClose=retainedUnknownClose;cold.onceCloseId=onceCloseId;
        observed.add(Stage.COLD_PRIVATE_REOPEN);return cold;
    }

    private static void requireSameDriver(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after)throws IOException {
        require(before.stamp().equals(after.stamp())&&Arrays.equals(before.driver().encode(),after.driver().encode())
                &&before.originalHistoryBasis().equals(after.originalHistoryBasis())&&before.actionRows().equals(after.actionRows())
                &&before.auxiliary().equals(after.auxiliary()),"cold read recovery changed actual Driver/history/auxiliary or repeated CAS");
    }

    /** Executes the real Controller private pending probe/entry, not an ordinary planning fallback. */
    public SessionController.TurnReport entryTurn(Instant deadline)throws IOException,InterruptedException {
        var before=capture();var actual=requireCurrent(deadline);
        var result=root.pendingSuccessorUiTurn(deadline);var after=capture();
        require(result.execution().session().equals(root.identity()),"entry report crossed its real Root session");
        requireProgress(before,after);inspect(actual,before,after,deadline);observed.add(Stage.ENTRY);return result;
    }

    public RootDriverLifecyclePublicCodec.Timeline query(RootDriverLifecyclePublicCodec.Query input,
            Instant deadline)throws IOException {
        Objects.requireNonNull(input);requireCurrent(deadline);var before=capture();
        require(RootDriverLifecyclePublicCodec.query(RootDriverLifecyclePublicCodec.encode(input)).equals(input),
                "public query input lost its original revision during serde");
        var result=pending.publicTimeline(input,deadline);var after=capture();requireReadOnly(before,after);
        var encoded=RootDriverLifecyclePublicCodec.encode(result);
        var decoded=RootDriverLifecyclePublicCodec.decodeTimelineData(encoded);
        require(decoded.machineId().equals(root.identity().machineId())
                &&Arrays.equals(encoded.bytes(),RootDriverLifecyclePublicCodec.encodeTimelineData(decoded).bytes()),
                "actual timeline original/public serde changed machine or bytes");
        observed.add(Stage.QUERY);return result;
    }

    /** Legacy metadata-only projection retained for existing callers; it earns no full public RESUME coverage. */
    public RootDriverLifecyclePublicCodec.View resume(RootDriverLifecyclePublicCodec.Resume input,
            Instant deadline)throws IOException {
        Objects.requireNonNull(input);var actual=requireCurrent(deadline);var before=capture();
        require(RootDriverLifecyclePublicCodec.resume(RootDriverLifecyclePublicCodec.encode(input)).equals(input),
                "public resume request changed optional/exact revision semantics");
        var result=pending.publicResume(input,deadline);var after=capture();requireProgress(before,after);
        var encoded=RootDriverLifecyclePublicCodec.encode(result);
        var decoded=RootDriverLifecyclePublicCodec.decodeView(encoded);
        require(decoded.status()==result.status()&&decoded.pending()==result.pending()
                &&decoded.close().equals(result.close())&&decoded.transition().equals(result.transition()),
                "public successor result lost original obligation/UNKNOWN reconciliation during serde");
        inspect(actual,before,after,deadline);return result;
    }

    /** Actual installed full-material producer consumed by Supplier20; decoding remains DATA, never a private token. */
    public RootDriverLifecycleResumeCodec.ResumeResult resumeMaterial(RootDriverLifecyclePublicCodec.Resume input,
            Instant deadline)throws IOException {
        Objects.requireNonNull(input);var actual=requireCurrent(deadline);var before=capture();
        require(RootDriverLifecyclePublicCodec.resume(RootDriverLifecyclePublicCodec.encode(input)).equals(input),
                "full public resume request changed optional/exact revision semantics");
        var result=pending.publicResumeMaterial(input,deadline);var after=capture();requireProgress(before,after);
        var encoded=RootDriverLifecycleResumeCodec.encode(result);var decoded=RootDriverLifecycleResumeCodec.decode(encoded);
        require(Arrays.equals(encoded.bytes(),RootDriverLifecycleResumeCodec.encode(decoded).bytes()),
                "actual full public resume material lost fields or original numeric JSON during wire serde");
        inspect(actual,before,after,deadline);observed.add(Stage.RESUME);return result;
    }

    /**
     * After the genuine FINAL, execute the installed public READ and supply its actual admitted-current
     * originals to the existing mandatory Host assertion while the identical writer Session is held.
     * The native receipt and private issuer are measured here; a caller-supplied READ/BATCH label is insufficient.
     */
    public RootDriverLifecyclePublicCodec.Timeline admittedTimeline(RootDriverLifecyclePublicCodec.Query input,
            Instant deadline,RootHostBatchAndCloseActualTest.CurrentAdoptionCheck actualCheck)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);Objects.requireNonNull(actualCheck);
        requireAdmittedFinal();var before=capture();
        var result=context.withSession(same->{
            var timeline=RootPendingUiAdmittedEpisodeAssertions.publicTimelineIsReadOnly(same,context,lifecycle,input,deadline);
            var actual=RootPendingUiAdmittedEpisodeAssertions.afterActualReadOrBatch(same,context,lifecycle,root,before.parent(),deadline);
            actualCheck.require(same,actual.producer(),actual.current(),actual.journal(),actual.admitted(),actual.known());
            core.writer().requireSession(same);return timeline;
        });
        var after=capture();requireReadOnly(before,after);requireSameDriver(before.known(),after.known());
        observed.add(Stage.ADMITTED_CURRENT_READ);return result;
    }

    /** Actual no-pending public RESUME after the prior admitted READ; it cannot repeat finalization or Driver CAS. */
    public void admittedResume(RootDriverLifecyclePublicCodec.Resume input,Instant deadline)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);requireAdmittedFinal();
        require(observed.contains(Stage.ADMITTED_CURRENT_READ),"actual admitted-current READ must precede the no-pending public RESUME");
        var before=capture();context.withSession(same->{
            RootPendingUiAdmittedEpisodeAssertions.publicResumeIsReadOnly(same,context,lifecycle,input,deadline);
            core.writer().requireSession(same);return null;
        });
        var after=capture();requireReadOnly(before,after);requireSameDriver(before.known(),after.known());
        observed.add(Stage.ADMITTED_PUBLIC_RESUME);
    }

    private void requireAdmittedFinal()throws IOException {
        requireOwner();require(observed.contains(Stage.FINAL),"actual pending FINAL must be observed before current readoption");
        var actual=capture().parent();
        require(actual.state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                "actual original pending parent has no settled successor finalization");
    }

    /** Actual pending producers remain pending; no caller-supplied phase or missing completion authorizes retirement. */
    public void nonFinalizedPendingRetainsItsOriginals(Instant deadline)throws IOException {
        var actual=requireCurrent(deadline);var before=capture();
        require(actual.obligation().phase()!=SuccessorUiObligation.Phase.FINALIZED,
                "non-finalized coverage requires a genuine incomplete obligation");
        requirePendingTwice(deadline,actual.obligation());
        var after=capture();requireReadOnly(before,after);requireSameDriver(before.known(),after.known());
        observed.add(Stage.NONFINALIZED_PENDING_RETAINED);
    }

    /** Uses the original unresolved Close receipt and the real probe, never a fabricated UNKNOWN result. */
    public void unknownPendingCannotBecomeCompleted(Instant deadline)throws IOException {
        var actual=requireCurrent(deadline);var before=capture();
        var receipt=actual.obligation().closeAttempt().flatMap(SuccessorUiObligation.CloseAttempt::receipt)
                .orElseThrow(()->missing("actual original UNKNOWN Close is required"));
        require(receipt.outcome()==ActionReceipt.Outcome.UNRESOLVED
                &&receipt.effectiveMaterialClearance().isEmpty()&&receipt.effectiveDateAdvance().isEmpty(),
                "UNKNOWN completion coverage requires the genuine unresolved postcondition");
        context.withSession(same->{
            var original=context.archive().withSession(same).loadReceipt(receipt.canonicalReceipt());
            require(original.outcome()==ActionReceipt.Outcome.UNRESOLVED
                    &&before.rows().stream().anyMatch(row->row.command().equals(original.command())
                    &&row.bodySha256().equals(original.bodySha256())),"UNKNOWN Close lost its actual canonical original");
            return null;
        });
        requirePendingTwice(deadline,actual.obligation());
        var after=capture();requireReadOnly(before,after);requireSameDriver(before.known(),after.known());
        observed.add(Stage.UNKNOWN_PENDING_RETAINED);
    }

    private void requirePendingTwice(Instant deadline,SuccessorUiObligation original)throws IOException {
        context.withSession(same->{
            for(int attempt=0;attempt<2;attempt++) {
                require(pending.pendingSuccessorUi(same,root.identity(),deadline).isPresent(),
                        "incomplete/UNKNOWN original was incorrectly retired");
                require(pending.hasPending(),"incomplete/UNKNOWN original lost its actual public pending gate");
                var current=pending.current(same,deadline).orElseThrow(()->missing("original pending Current disappeared"));
                current.requireCurrent(same);
                require(current.originalParent().equals(parent)&&current.obligation().equals(original),
                        "pending probe replaced or replayed its original incomplete transition");
            }
            return null;
        });
    }

    /** Invoke the original public SAVE producer after actual finalization. Only its confirmed private pair earns coverage. */
    public RootCheckpointPublicCalls.SaveCall completedCheckpointSave(RootCheckpointPublicCalls.Request originalRequest,
            Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(originalRequest);Objects.requireNonNull(deadline);requireAdmittedFinal();
        var before=capture();var marker=completedMarker(before.known());
        require(marker.binding().parentActionId().equals(parent.actionId())
                &&marker.binding().parentBodySha256().equals(before.parent().bodySha256()),
                "completed SAVE does not descend from this fixture's actual finalized parent");
        if(completedBeforeSave==null)completedBeforeSave=before;
        else require(completedBeforeSave.parent().equals(before.parent())
                &&sameSlot(completedBeforeSave.known().driver().campaignGoal(),before.known().driver().campaignGoal()),
                "querying the original completed SAVE changed its settled parent or full goal");
        var call=root.saveCheckpointPublic(originalRequest,deadline);
        if(call.actual() instanceof CheckpointResult.Confirmed confirmed) {
            var saved=call.savedDriver().orElseThrow(()->missing("actual confirmed SAVE did not retain its full Driver"));
            var after=capture();requireOldActionsRetained(completedBeforeSave.rows(),after.rows());
            require(confirmed.pair().frame().game().equals(root.identity().game())
                    &&confirmed.pair().frame().frame().episodeRunId().equals(saved.session().episodeRunId())
                    &&confirmed.pair().frame().frame().identity().player().equals(saved.session().actorId())
                    &&confirmed.pair().saveActionId().equals(confirmed.action().command().actionId())
                    &&confirmed.action().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,
                    "completed SAVE lacks its genuine same-episode physical pair and confirmed original action");
            require(sameSlot(saved.campaignGoal(),completedBeforeSave.known().driver().campaignGoal())
                    &&sameSlot(saved.successionLifecycle(),completedBeforeSave.known().driver().successionLifecycle())
                    &&marker.equals(completedMarker(after.known())),
                    "completed SAVE changed its high-level intent, lifecycle or resolved obligation");
            requireHistoryPrefix(completedBeforeSave.known().driver(),saved);
            completedPairedSave=call;observed.add(Stage.COMPLETED_PAIRED_SAVE);
        } else {
            require(call.savedDriver().isEmpty(),"unconfirmed SAVE acquired a completed full Driver");
        }
        return call;
    }

    /** Both calls enter the original retained SAVE attempt; a real unresolved native outcome must remain unresolved. */
    public void completedSaveUnknownTwiceRetained(RootCheckpointPublicCalls.Request originalRequest,
            Instant deadline)throws IOException,InterruptedException {
        var first=completedCheckpointSave(originalRequest,deadline);
        if(!(first.actual() instanceof CheckpointResult.Unknown original))
            throw missing("actual first completed SAVE must be UNKNOWN for this stage");
        var firstAction=RootCheckpointPublicCalls.action(first.actual()).orElseThrow(()->missing("actual entered UNKNOWN SAVE receipt required"));
        require(firstAction.outcome()==ActionReceipt.Outcome.UNRESOLVED
                &&original.actionId().equals(firstAction.command().actionId()),"actual original SAVE is not the bound unresolved action");
        var before=canonicalActions();var second=completedCheckpointSave(originalRequest,deadline);var after=canonicalActions();
        require(second.actual() instanceof CheckpointResult.Unknown repeated&&repeated.actionId().equals(original.actionId())
                &&second.savedDriver().isEmpty(),
                "actual repeated original SAVE query acquired a completed pair");
        var secondAction=RootCheckpointPublicCalls.action(second.actual()).orElseThrow(()->missing("retained UNKNOWN SAVE receipt required"));
        requireSameUnknownAttempt(firstAction,secondAction);requireSameActionBodies(before.rows(),after.rows());
        var retained=capture();requireOldActionsRetained(completedBeforeSave.rows(),retained.rows());
        require(completedMarker(retained.known()).equals(completedMarker(completedBeforeSave.known()))
                &&sameSlot(completedBeforeSave.known().driver().campaignGoal(),retained.known().driver().campaignGoal())
                &&sameSlot(completedBeforeSave.known().driver().successionLifecycle(),retained.known().driver().successionLifecycle()),
                "UNKNOWN SAVE retired or changed the original FINALIZED history/goal/lifecycle");
        context.withSession(same->{
            var archivedUnknown=context.archive().withSession(same).loadReceipt(first.canonicalReceipt().orElseThrow());
            require(archivedUnknown.equals(firstAction),"original UNKNOWN SAVE archive bytes were replaced");return null;
        });
        observed.add(Stage.COMPLETED_SAVE_UNKNOWN_RETAINED);
    }

    /** The real Core keeps querying its one original lifecycle request; no binding or replacement owner is synthesized. */
    public void completedRestoreUnknownTwiceRetained(RootCheckpointPublicCalls.Request originalRequest,
            Instant deadline)throws IOException,InterruptedException {
        requireCompletedPair();Objects.requireNonNull(originalRequest);Objects.requireNonNull(deadline);
        var first=core.restoreCheckpointPublic(originalRequest,deadline);
        if(!(first.actual() instanceof RestoreCheckpointService.Unknown original))
            throw missing("actual first completed-checkpoint restoration must remain UNKNOWN");
        require(first.published().isEmpty(),"UNKNOWN restoration published a replacement Root");
        var before=canonicalActions();var second=core.restoreCheckpointPublic(originalRequest,deadline);var after=canonicalActions();
        require(second.actual() instanceof RestoreCheckpointService.Unknown repeated
                &&repeated.requestId().equals(original.requestId())&&second.published().isEmpty(),
                "UNKNOWN restoration was replaced, replayed or converted into an invented binding");
        requireSameActionBodies(before.rows(),after.rows());
        requireOldActionsRetained(completedBeforeSave.rows(),after.rows());
        require(completedRestoration==null&&core.sessionAccess().current()==root,
                "UNKNOWN restoration acquired a replacement Root or successful-completion fixture stage");
        context.withSession(same->root.driver().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw missing("UNKNOWN restore lost its original canonical Driver");
            require(completedMarker(known).equals(completedMarker(completedBeforeSave.known())),
                    "UNKNOWN restore removed or replaced its original completed marker without a private RestoreBinding");return null;
        }));
        observed.add(Stage.COMPLETED_RESTORE_UNKNOWN_RETAINED);
    }

    /**
     * Calls the original SAVE-to-LOAD producer and consumes its actual published Root/catalog. The catalog callback
     * only returns that installed object; it is not a startup factory, Managed fixture or proof issuer.
     */
    public RootCheckpointPublicCalls.RestoreCall completedCheckpointRestore(RootCheckpointPublicCalls.Request originalRequest,
            RootHostBatchAndCloseActualTest.OriginalAfterCatalog originalCatalog,Instant deadline)
            throws IOException,InterruptedException {
        requireCompletedPair();Objects.requireNonNull(originalRequest);Objects.requireNonNull(originalCatalog);Objects.requireNonNull(deadline);
        require(completedRestoration==null,"completed restoration coverage cannot be submitted twice");
        var result=core.restoreCheckpointPublic(originalRequest,deadline);
        if(!(result.actual() instanceof RestoreCheckpointService.Restored restored))
            throw missing("actual confirmed restoration and private RestoreBinding are required; UNKNOWN earns no cold completion");
        var replacement=result.published().orElseThrow(()->missing("actual restored Root was not host-published"));
        var installed=Objects.requireNonNull(originalCatalog.readOriginal(replacement),"actual restored installed catalog required");
        var afterContext=installed.context();var afterLifecycle=installed.remainingDomains().lifecycle();
        var afterPending=afterLifecycle.natural().pendingRuntime();var binding=restored.binding();
        require(root.isRetired()&&replacement!=root&&replacement.ownedBy(core)&&replacement.hasInstalledHost()
                &&core.sessionAccess().current()==replacement&&afterContext.core()==core
                &&afterContext.writer()==core.writer()&&afterContext.archive()==core.archive()
                &&afterContext.actions()==replacement&&afterContext.adopted()==replacement.driver()
                &&binding.session().equals(replacement.identity())&&!binding.session().game().equals(root.identity().game()),
                "completed restoration did not publish the actual distinct-Game Root in this original Core");
        afterLifecycle.requireContext(afterContext);afterPending.requireContext(afterContext);
        var confirmed=(CheckpointResult.Confirmed)completedPairedSave.actual();var marker=completedMarker(completedBeforeSave.known());
        require(binding.pair().equals(confirmed.pair())&&binding.savedMaterial().session().equals(root.identity())
                &&binding.savedMaterial().pair().equals(binding.pair())
                &&Arrays.equals(binding.savedMaterial().savedDriver().encode(),completedPairedSave.savedDriver().orElseThrow().encode()),
                "actual restoration consumed a different paired SAVE or original complete saved Driver");
        afterContext.withSession(same->{
            var origin=afterContext.requireRestoredOrigin(same);origin.requireOriginal(same);
            require(origin==binding.requireReboundOrigin(same)&&origin.evidence().restoredOwner().equals(replacement.identity())
                    &&origin.evidence().savedOwner().equals(root.identity())&&origin.evidence().pair().equals(binding.pair())
                    &&origin.newSavedDayCredit()==0&&origin.newCycleCredit()==0&&binding.newSavedDayCredit()==0,
                    "completed restoration lost its original private issuer, physical pair or zero-credit provenance");
            binding.savedMaterial().requireRetained(same);
            requireCompletedSemantic(afterContext,same,binding.savedMaterial().sourceSemantic(),binding.savedMaterial().savedDriver(),marker);
            requireCompletedSemantic(afterContext,same,binding.semantic(),binding.driver(),marker);
            origin.requireOriginal(same);return null;
        });
        var beforeProbe=captureAt(replacement,installed,parent);
        requireOldActionsRetained(completedBeforeSave.rows(),beforeProbe.rows());
        require(beforeProbe.parent().equals(completedBeforeSave.parent())&&marker.equals(completedMarker(beforeProbe.known()))
                &&sameSlot(binding.driver().campaignGoal(),beforeProbe.known().driver().campaignGoal())
                &&sameSlot(binding.driver().successionLifecycle(),beforeProbe.known().driver().successionLifecycle()),
                "actual restored Driver changed its resolved original, full high-level goal or lifecycle");
        afterContext.withSession(same->{
            for(int attempt=0;attempt<2;attempt++) {
                require(afterPending.pendingSuccessorUi(same,replacement.identity(),deadline).isEmpty()
                        &&afterPending.current(same,deadline).isEmpty()&&!afterPending.hasPending(),
                        "the real restored pending probe retained or replayed the completed old-Game obligation");
            }
            afterContext.requireRestoredOrigin(same).requireOriginal(same);return null;
        });
        var afterProbe=captureAt(replacement,installed,parent);
        requireReadOnly(beforeProbe,afterProbe);requireSameDriver(beforeProbe.known(),afterProbe.known());
        completedRestoration=new CompletedRestoration(replacement,installed,binding,afterProbe,marker);
        observed.add(Stage.COMPLETED_COLD_RESTORE);return result;
    }

    /** Called only after the actual ordinary planner has encountered the following natural inheritance. */
    public RootPendingUiProductionChainFixture nextInheritanceAfterCompletedRestore(Instant deadline)throws IOException {
        var restored=completedRestoration;
        if(restored==null)throw missing("actual completed paired SAVE, private restoration and empty probes are required before the next inheritance");
        require(!observed.contains(Stage.COMPLETED_COLD_NEXT_INHERITANCE),"next inherited parent was already checked");
        var next=new RootPendingUiProductionChainFixture(core,restored.root(),restored.installed(),deadline,observed);
        var actual=next.requireCurrent(deadline);var captured=next.capture();var predecessor=next.parent.lifecycleBefore();
        require(!next.parent.actionId().equals(parent.actionId())&&next.parent.origin() instanceof CommandOrigin.LifecycleTerminal
                &&next.parent.operation().value().equals("continue-as-reconciled-successor")
                &&predecessor.game().equals(restored.root().identity().game())
                &&predecessor.subject().characterId().equals(restored.afterProbes().known().driver().session().actorId())
                &&predecessor.subject().episodeRunId().equals(restored.afterProbes().known().driver().session().episodeRunId())
                &&actual.obligation().binding().predecessor().sameGuardFrame(predecessor)
                &&actual.obligation().binding().parentActionId().equals(next.parent.actionId())
                &&!actual.obligation().binding().successorEpisodeRunId().equals(restored.completed().binding().successorEpisodeRunId()),
                "next actual pending producer did not descend from the restored ruler/run on the replacement Game");
        restored.installed().context().withSession(same->{
            actual.requireCurrent(same);requireRestoredPreclockOrigin(restored.installed().context(),same,actual,restored.binding());return null;
        });
        requireOldActionsRetained(restored.afterProbes().rows(),captured.rows());
        require(captured.rows().stream().anyMatch(action->action.sequence()>restored.afterProbes().head().state().sequence()
                &&action.command().origin() instanceof CommandOrigin.Gameplay
                &&action.command().origin().game().equals(restored.root().identity().game())
                &&Set.of("life-advance","life-advance-one-day","resume-map").contains(action.command().operation().value())
                &&action.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED),
                "the following inheritance needs an actual canonical ordinary advance on the replacement Game");
        requireFollowingGoal(restored,captured.known().driver().campaignGoal());
        require(sameSlot(restored.afterProbes().known().driver().successionLifecycle(),captured.known().driver().successionLifecycle()),
                "next pre-final inheritance lost or prematurely credited the restored high-level goal/lifecycle");
        restoredNextParent=next.parent;restoredNextGoal=captured.known().driver().campaignGoal();
        observed.add(Stage.COMPLETED_COLD_NEXT_INHERITANCE);return next;
    }

    /** Actual second finalization must advance the retained goal once using the original complete M3 result. */
    public void nextInheritanceFinalizedAfterCompletedRestore(Instant deadline)throws IOException {
        var restored=completedRestoration;
        if(restored==null||restoredNextParent==null||!observed.contains(Stage.COMPLETED_COLD_NEXT_INHERITANCE))
            throw missing("the genuine following pending inheritance must precede its actual finalization");
        var finalState=captureAt(restored.root(),restored.installed(),restoredNextParent);
        if(!(finalState.parent().state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR))
            throw missing("the actual next inherited parent has not completed its canonical lifecycle");
        applied.proof().validateParent(restoredNextParent);var marker=completedMarker(finalState.known());
        require(marker.binding().parentActionId().equals(restoredNextParent.actionId())
                &&applied.proof().originalEvidence().contains(marker.finalization().orElseThrow().finalM3Proof()),
                "next finalization lost its true new-parent private M3 evidence");
        requireOldActionsRetained(restored.afterProbes().rows(),finalState.rows());
        if(!(restoredNextGoal instanceof DriverStateSnapshot.Value retainedGoal
                &&finalState.known().driver().campaignGoal() instanceof DriverStateSnapshot.Value continuedGoal))
            throw missing("actual ordinary goal is required before and after the next inherited ruler");
        var originalGoal=GoalCodec.decodeGoal(retainedGoal.json());var actualGoal=GoalCodec.decodeGoal(continuedGoal.json());
        // The real reducer deliberately clears its transient auxiliary reconciliation. Consume the
        // complete original M3 result retained in the actual canonical lifecycle proof instead.
        var finalResult=OpportunityJson.object(OpportunityJson.parse(applied.proof().encodedResult()),"actual next lifecycle result");
        var result=finalResult.get("succession_reconciliation");
        if(result==null||result==OpportunityJson.Nil.INSTANCE)throw missing("actual next final complete M3 reconciliation is absent");
        var reconciliation=GoalCodec.decodeReconciliation(DriverJson.encode(result));
        require(actualGoal.equals(OrdinaryCampaignGoal.continueGoal(originalGoal,reconciliation))
                &&actualGoal.currentCharacterId()==finalState.known().driver().session().actorId().longValueExact()
                &&sameSlot(restored.afterProbes().known().driver().successionLifecycle(),finalState.known().driver().successionLifecycle()),
                "next canonical inheritance changed campaign origin, lost the original goal or credited it more than once");
        var context=restored.installed().context();var lifecycle=restored.installed().remainingDomains().lifecycle();
        context.withSession(same->{
            require(lifecycle.natural().pendingRuntime().pendingSuccessorUi(same,restored.root().identity(),deadline).isEmpty()
                    &&!lifecycle.natural().pendingRuntime().hasPending(),
                    "next actual finalized inheritance still blocks ordinary continuation");
            context.requireRestoredOrigin(same).requireOriginal(same);
            requireCompletedSemantic(context,same,restored.binding().savedMaterial().sourceSemantic(),
                    restored.binding().savedMaterial().savedDriver(),restored.completed());
            requireCompletedSemantic(context,same,restored.binding().semantic(),restored.binding().driver(),restored.completed());return null;
        });
        var after=captureAt(restored.root(),restored.installed(),restoredNextParent);
        requireReadOnly(finalState,after);requireSameDriver(finalState.known(),after.known());
        observed.add(Stage.COMPLETED_COLD_NEXT_FINAL);
    }

    /** Reuses the sole existing real-Root continuation assertion helper, with this issuer's private token. */
    public RootPendingSuccessorChainFixture.Step continueOnce(Instant deadline)throws IOException {
        var actual=requireCurrent(deadline);var before=capture();
        var result=RootPendingSuccessorChainFixture.continueOnce(core,root,actual);
        var after=capture();requireProgress(before,after);inspect(actual,before,after,deadline);return result;
    }

    public void copiedCarrierCannotAuthorize(Instant deadline)throws IOException {
        var actual=requireCurrent(deadline);var before=capture();
        RootPendingSuccessorChainFixture.copiedCarrierCannotAuthorizeAChild(core,root,actual);
        requireReadOnly(before,capture());observed.add(Stage.PRIVATE_COPY_REFUSED);
    }

    /** Pins the real UNKNOWN archive before a later ACK/control settlement, without changing the canonical row. */
    public void requireRetainedUnknownClose(Instant deadline)throws IOException {
        var actual=requireCurrent(deadline);var receipt=actual.obligation().closeAttempt().orElseThrow(
                ()->missing("actual once Close intent absent")).receipt().orElseThrow(
                ()->missing("actual UNKNOWN child was not retained in the pending obligation"));
        context.withSession(same->{var archive=context.archive().withSession(same);var original=archive.loadReceipt(receipt.canonicalReceipt());
            require(original.state() instanceof ActionState.Unknown&&original.outcome()==ActionReceipt.Outcome.UNRESOLVED,
                    "retained once Close original is not canonical UNKNOWN");
            require(original.command().actionId().equals(actual.obligation().closeAttempt().orElseThrow().actionId()),
                    "retained UNKNOWN is not the original once Close action");
            if(originalUnknownClose!=null)require(originalUnknownClose.equals(receipt.canonicalReceipt())
                    &&retainedUnknownClose.equals(original),"original UNKNOWN archive was replaced");
            originalUnknownClose=receipt.canonicalReceipt();retainedUnknownClose=original;return null;});
        var now=capture();inspect(actual,now,now,deadline);observed.add(Stage.UNKNOWN_RETAINED);
    }

    /** Cold replay uses the actual archive and the production verifier, including both original read guards. */
    public void coldClose(ExactRef actualConfirmedClose)throws IOException {
        Objects.requireNonNull(actualConfirmedClose);var before=capture();
        context.withSession(same->{var archive=context.archive().withSession(same);var receipt=archive.loadReceipt(actualConfirmedClose);
            require(onceCloseId!=null&&receipt.command().actionId().equals(onceCloseId),"cold receipt is not this real once Close");
            pending.verifyCloseControl(receipt,archive);
            var encoded=ActionReceiptCodec.encodeReceipt(receipt,archive);var decoded=ActionReceiptCodec.decodeReceipt(encoded,archive);
            require(decoded.equals(receipt),"canonical Close receipt changed across cold serde");pending.verifyCloseControl(decoded,archive);
            if(originalUnknownClose!=null){var old=archive.loadReceipt(originalUnknownClose);require(old.equals(retainedUnknownClose)
                    &&old.state() instanceof ActionState.Unknown&&old.command().equals(receipt.command()),
                    "confirmed Close replaced its original UNKNOWN archive");
                var settled=(ActionState.Settled)receipt.state();var control=(ActionState.ControlApplied)settled.settlement();
                if(control.reconciledAck().isPresent()){
                    var unknown=(ActionState.Unknown)old.state();require(unknown.attempt().equals(Optional.of(settled.attempt()))
                            &&unknown.dispatch().equals(Optional.of(settled.dispatch())),"late ACK rewrote original UNKNOWN attempt/dispatch");
                    control.reconciledAck().orElseThrow().requireMatches(receipt.command(),settled.attempt(),settled.dispatch());
                    observed.add(Stage.LATE_ACK_CONTROL);
                }
            }
            return null;});
        requireReadOnly(before,capture());observed.add(Stage.COLD_CONTROL);
    }

    /** The genuine archived lifecycle parent cannot be misread as a generic Close control receipt. */
    public void coldParentCannotBecomeClose()throws IOException {
        var before=capture();context.withSession(same->{var archive=context.archive().withSession(same);
            var original=archive.preserveReceipt(before.parent());var cold=archive.loadReceipt(original);
            boolean refused=false;try{pending.verifyCloseControl(cold,archive);}
            catch(IOException|IllegalArgumentException|IllegalStateException expected){refused=true;}
            require(refused,"cold non-Control original was accepted as material Close clearance");return null;});
        requireReadOnly(before,capture());observed.add(Stage.COLD_NON_CONTROL_REFUSED);
    }

    /** False predicates are read from the real held physical producer; no synthetic snapshot or token is supplied. */
    public void actualUnavailableFrameCannotQuery(RootDriverLifecyclePublicCodec.Query input,Instant deadline)throws IOException {
        Objects.requireNonNull(input);requireCurrent(deadline);var before=capture();
        context.withSession(same->lifecycle.physical().withSnapshot(same,deadline,lease->{
            lease.assertCurrent(same);var semantic=lease.fullSnapshot().semantic();
            boolean paused=OpportunityJson.bool(semantic.get("paused"),"actual paused");
            boolean map=OpportunityJson.bool(semantic.get("map_ready"),"actual map ready");
            if(paused&&map)throw missing("actual retained source must supply paused=false or map_ready=false");
            require(input.expectedRevision().equals(lease.fullSnapshot().facts().publicRevision()),
                    "false-predicate test must retain the actual physical revision, not induce stale-input refusal");
            boolean refused=false;try{pending.publicTimeline(input,deadline);}
            catch(IOException|IllegalArgumentException|IllegalStateException expected){refused=expected.getMessage()!=null
                    &&expected.getMessage().contains("pending UI requires its actual physical map/paused predicate");}
            require(refused,"actual false map/paused source reached a successful pending query");lease.assertCurrent(same);
            if(!paused)observed.add(Stage.PAUSED_FALSE_REFUSED);if(!map)observed.add(Stage.MAP_FALSE_REFUSED);return null;}));
        requireReadOnly(before,capture());
    }

    /** The real public RESUME must expose its original physical refusal; an unresolved result cannot hide a failed predicate. */
    public void actualUnavailableFrameCannotResume(RootDriverLifecyclePublicCodec.Resume input,Instant deadline)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);requireCurrent(deadline);var before=capture();
        context.withSession(same->lifecycle.physical().withSnapshot(same,deadline,lease->{
            lease.assertCurrent(same);var semantic=lease.fullSnapshot().semantic();
            boolean paused=OpportunityJson.bool(semantic.get("paused"),"actual paused");
            boolean map=OpportunityJson.bool(semantic.get("map_ready"),"actual map ready");
            if(paused&&map)throw missing("actual public RESUME refusal needs a genuine paused=false or map_ready=false source");
            require(input.original().expected().filter(lease.fullSnapshot().facts().publicRevision()::equals).isPresent(),
                    "false-predicate RESUME must bind its actual current revision, not an unrelated stale-input failure");
            boolean refused=false;
            try{pending.publicResumeMaterial(input,deadline);}
            catch(IOException|IllegalArgumentException|IllegalStateException expected){refused=expected.getMessage()!=null
                    &&expected.getMessage().contains("pending UI requires its actual physical map/paused predicate");}
            require(refused,"actual false map/paused RESUME was swallowed into a successful or ui_unresolved result");
            lease.assertCurrent(same);
            if(!paused)observed.add(Stage.PAUSED_FALSE_RESUME_REFUSED);if(!map)observed.add(Stage.MAP_FALSE_RESUME_REFUSED);return null;
        }));
        var after=capture();requireReadOnly(before,after);requireSameDriver(before.known(),after.known());
    }

    /** Retain the genuine once Close UNKNOWN while two actual public calls may append observation evidence only. */
    public void unknownResumeTwice(RootDriverLifecyclePublicCodec.Resume input,Instant deadline)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);requireRetainedUnknownClose(deadline);
        var before=capture();var close=unknownClose(before);var children=ActionTransitions.composite(before.parent().state()).orElseThrow().children();
        var first=resumeMaterial(input,deadline);require(!first.dateAdvanced(),"first actual UNKNOWN RESUME claimed date advance");
        requireSameUnknownActions(before,capture(),close,children);
        var second=resumeMaterial(input,deadline);require(!second.dateAdvanced(),"second actual UNKNOWN RESUME claimed date advance");
        requireSameUnknownActions(before,capture(),close,children);
        // These are actual canonical no-resubmit invariants. A Managed wire capture remains separately required
        // to prove the physical transport sent no duplicate bytes; canonical equality alone is not that evidence.
        observed.add(Stage.UNKNOWN_RESUME_TWICE_RETAINED);
    }

    private ActionReceipt unknownClose(Captured actual)throws IOException {
        require(onceCloseId!=null&&originalUnknownClose!=null&&retainedUnknownClose!=null,"actual retained once Close UNKNOWN must be pinned first");
        var close=actual.rows().stream().filter(row->row.command().actionId().equals(onceCloseId)).findFirst()
                .orElseThrow(()->missing("actual canonical once Close UNKNOWN is absent"));
        require(close.state() instanceof ActionState.Unknown&&close.outcome()==ActionReceipt.Outcome.UNRESOLVED,
                "actual once Close is no longer canonical UNKNOWN");return close;
    }
    private void requireSameUnknownActions(Captured before,Captured after,ActionReceipt original,
            List<CompositeExecution.Child> children)throws IOException {
        var current=unknownClose(after);var old=(ActionState.Unknown)original.state();var now=(ActionState.Unknown)current.state();
        require(original.command().equals(current.command())&&original.bodySha256().equals(current.bodySha256())
                &&old.attempt().equals(now.attempt())&&old.dispatch().equals(now.dispatch()),
                "actual public RESUME replaced or repeated its original once Close command/body/Attempt/dispatch");
        require(before.rows().size()==after.rows().size()
                &&children.equals(ActionTransitions.composite(after.parent().state()).orElseThrow().children()),
                "actual UNKNOWN RESUME created a new action or child reservation");
        for(int index=0;index<before.rows().size();index++) {
            var a=before.rows().get(index);var b=after.rows().get(index);
            require(a.command().equals(b.command())&&a.bodySha256().equals(b.bodySha256()),
                    "actual UNKNOWN RESUME changed the canonical action identities or bodies");
        }
        long oldCount=before.rows().stream().filter(row->row.command().operation().value().equals(NativeTimelineBlocker12004.CLOSE_STEP)).count();
        long newCount=after.rows().stream().filter(row->row.command().operation().value().equals(NativeTimelineBlocker12004.CLOSE_STEP)).count();
        require(oldCount==newCount,"actual UNKNOWN RESUME added another Close row");
    }

    public Set<Stage> observedStages(){return Set.copyOf(observed);}
    /** A CI/managed caller must invoke this gate; merely compiling or discovering this helper is not acceptance. */
    public void requireFullCoverage()throws IOException {
        var absent=EnumSet.allOf(Stage.class);absent.removeAll(observed);
        if(!absent.isEmpty())throw missing("actual pending UI stages absent: "+absent);
    }

    private void requireCompletedPair()throws IOException {
        require(completedBeforeSave!=null&&completedPairedSave!=null
                &&completedPairedSave.actual() instanceof CheckpointResult.Confirmed
                &&completedPairedSave.savedDriver().isPresent()&&observed.contains(Stage.COMPLETED_PAIRED_SAVE),
                "only the original confirmed completed SAVE can enter actual restoration; UNKNOWN supplies no pair");
    }
    private static SuccessorUiObligation completedMarker(DriverSnapshotFacts.Known known)throws IOException {
        var value=known.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY);
        if(value==null)throw missing("actual full Driver lacks its original completed UI obligation");
        var state=SuccessorUiObligationCodec.decode(DriverJson.encode(value));
        require(state.phase()==SuccessorUiObligation.Phase.FINALIZED,"actual completed checkpoint must retain FINALIZED, never UNKNOWN/non-finalized state");
        return state;
    }
    private static boolean sameSlot(DriverStateSnapshot.Slot before,DriverStateSnapshot.Slot after) {
        if(before instanceof DriverStateSnapshot.Value first&&after instanceof DriverStateSnapshot.Value second)
            return OpportunityJson.parse(first.json()).equals(OpportunityJson.parse(second.json()));
        return before.getClass().equals(after.getClass());
    }
    private static void requireHistoryPrefix(DriverStateSnapshot.Complete before,DriverStateSnapshot.Complete after)throws IOException {
        var prefix=before.commandHistory();var retained=after.commandHistory();
        require(retained.size()>=prefix.size(),"actual paired SAVE discarded original full Driver history");
        for(int index=0;index<prefix.size();index++)
            require(Arrays.equals(prefix.get(index).originalRow().json(),retained.get(index).originalRow().json()),
                    "actual paired SAVE rewrote the original Driver history prefix");
    }
    private static void requireOldActionsRetained(List<ActionReceipt> old,List<ActionReceipt> current)throws IOException {
        for(var original:old)require(current.stream().anyMatch(original::equals),
                "completed restoration or next inheritance changed an original canonical action/once marker");
    }
    private static void requireSameActionBodies(List<ActionReceipt> before,List<ActionReceipt> after)throws IOException {
        require(before.size()==after.size(),"querying an UNKNOWN original submitted another canonical action");
        for(var original:before)require(after.stream().anyMatch(current->current.command().equals(original.command())
                &&current.bodySha256().equals(original.bodySha256())),"UNKNOWN query changed its original command identity/body");
    }
    private static void requireSameUnknownAttempt(ActionReceipt before,ActionReceipt after)throws IOException {
        require(before.outcome()==ActionReceipt.Outcome.UNRESOLVED&&after.outcome()==ActionReceipt.Outcome.UNRESOLVED
                &&before.command().equals(after.command())&&before.bodySha256().equals(after.bodySha256()),
                "UNKNOWN SAVE query replaced its original action or invented an outcome");
        var first=ActionTransitions.attempt(before.state()).orElseThrow(()->missing("original entered UNKNOWN SAVE attempt is absent"));
        var second=ActionTransitions.attempt(after.state()).orElseThrow(()->missing("retained entered UNKNOWN SAVE attempt is absent"));
        require(first.requestId().equals(second.requestId()),"UNKNOWN SAVE was resubmitted under a new native request identity");
    }
    private CanonicalActions canonicalActions()throws IOException {
        return core.writer().locked(same->new CanonicalActions(List.copyOf(ContinuityActionJournal.receipts(
                same.head().state(),core.archive().withSession(same))),same.head()));
    }
    private static Captured captureAt(RootApplicationSession actualRoot,RootInstalledCatalog installed,
            ActionCommand originalParent)throws IOException {
        var context=installed.context();
        require(context.core().sessionAccess().current()==actualRoot&&actualRoot.ownedBy(context.core())
                &&!actualRoot.isRetired()&&context.actions()==actualRoot&&context.adopted()==actualRoot.driver(),
                "restored fixture must use the identical installed current Root and Driver");
        return context.withSession(same->actualRoot.driver().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw missing("actual restored complete Driver unavailable");
            var rows=List.copyOf(frozen.actions().actions());var original=rows.stream()
                    .filter(row->row.command().actionId().equals(originalParent.actionId())).findFirst()
                    .orElseThrow(()->missing("actual restored canonical completed parent absent"));
            require(original.command().equals(originalParent),"restoration replaced the original settled lifecycle command");
            return new Captured(original,rows,known,same.head());
        }));
    }
    private static void requireCompletedSemantic(RootRuntimeContext context,ContinuityStorePort.Session same,
            org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence actual,
            DriverStateSnapshot.Complete fullDriver,SuccessorUiObligation completed)throws IOException {
        var snapshot=OpportunityJson.object(OpportunityJson.parse(context.archive().withSession(same)
                .loadMaterial(actual.semantic()).bytes()),"original complete saved/restored semantic");
        var marker=snapshot.get(SuccessorUiObligation.AUXILIARY_KEY);
        require(marker!=null&&SuccessorUiObligationCodec.decode(DriverJson.encode(marker)).equals(completed),
                "actual paired SAVE/restored full SEM lost or substituted its original FINALIZED obligation");
        var player=OpportunityJson.object(snapshot.get("played_character"),"actual saved/restored living player");
        require(OpportunityJson.bool(snapshot.get("paused"),"paused")&&OpportunityJson.bool(snapshot.get("map_ready"),"map_ready")
                &&OpportunityJson.bool(player.get("alive"),"alive")
                &&OpportunityJson.integer(player.get("character_id"),"actual actor").equals(fullDriver.session().actorId())
                &&OpportunityJson.integer(snapshot.get("date_raw"),"actual saved date").equals(actual.frame().frame().identity().dateRaw())
                &&OpportunityJson.text(snapshot.get("episode_run_id"),"actual episode").equals(fullDriver.session().episodeRunId())
                &&snapshot.get("active_event")==OpportunityJson.Nil.INSTANCE
                &&snapshot.get("pending_character_interaction")==OpportunityJson.Nil.INSTANCE,
                "actual accepted SAVE/restoration frame is not the independently clear paused living successor episode");
        requireSemanticSlot(fullDriver.campaignGoal(),snapshot,"campaign_goal");
        requireSemanticSlot(fullDriver.successionLifecycle(),snapshot,"succession_lifecycle");
    }
    /** Null is retained through restore/raw probes; only an actual later ordinary read may establish its original count-zero goal. */
    private static void requireFollowingGoal(CompletedRestoration restored,DriverStateSnapshot.Slot actual)throws IOException {
        var before=restored.afterProbes().known().driver().campaignGoal();
        if(!(before instanceof DriverStateSnapshot.NullValue)) {
            require(sameSlot(before,actual),"following inheritance changed its existing saved complete goal before final credit");return;
        }
        if(!(actual instanceof DriverStateSnapshot.Value initialized))
            throw missing("actual ordinary post-admission read has not initialized the restored null goal");
        var goal=GoalCodec.decodeGoal(initialized.json());var session=restored.afterProbes().known().driver().session();
        require(goal.campaignId().equals(session.episodeRunId())&&goal.originCharacterId()==session.actorId().longValueExact()
                &&goal.currentCharacterId()==session.actorId().longValueExact()
                &&goal.progress().reconciledSuccessions()==0&&goal.progress().lastSuccession().isEmpty(),
                "ordinary null-goal initialization changed its restored episode/actor or invented inheritance credit");
    }

    /** Replay the actual clock's retained source proof; a test-side producer call cannot supply this canonical consumer chain. */
    private static void requireRestoredPreclockOrigin(RootRuntimeContext context,ContinuityStorePort.Session same,
            RootPendingUiRuntime.Current actual,RestoreCheckpointService.RestoreBinding binding)throws IOException {
        var archive=context.archive().withSession(same);
        var capture=NaturalClockOriginals.decode(archive.loadMaterial(actual.canonicalDomain()).bytes()).capture();
        require(capture.machineId().equals(binding.session().machineId())&&capture.sessionId().equals(binding.session().sessionId())
                &&capture.gamePid()==binding.session().game().pid()
                &&capture.gameBirthFiletime().equals(binding.session().game().creationFiletime().value().toString())
                &&capture.episodeRunId().equals(binding.driver().session().episodeRunId())
                &&capture.predecessorFrame().actorCharacterId()==binding.driver().session().actorId().intValueExact(),
                "next actual preclock source did not descend from the privately restored ruler and Game");
        var clock=context.remainingDomains().lifecycle().natural().requireRetainedClock(same,capture);
        require(clock.command().before().game().equals(binding.session().game()),
                "next inheritance did not consume the actual ordinary clock from this replacement Game");
        var preclockDriver=DriverStateSnapshot.decodeComplete(archive.loadMaterial(capture.driver()).bytes());
        require(sameSlot(preclockDriver.campaignGoal(),actual.actualKnown().driver().campaignGoal()),
                "pending publication changed the actual ordinary preclock goal before finalization");
        var proof=capture.replacementProof().orElseThrow(()->missing("actual replacement clock has no retained ordinary restore source proof"));
        var row=org.xar.ck3.control.contracts.StrictJson.object(org.xar.ck3.control.contracts.StrictJson.parse(
                archive.loadMaterial(proof).bytes(),NaturalClockOriginals.MAX_BYTES),
                Set.of("schema","kind","event_identity","actual_game","canonical_attachment_head","restored_origin",
                        "history_basis","semantic","native_packet","original_driver"));
        require(org.xar.ck3.control.contracts.StrictJson.text(row.get("schema")).equals("xar.java.natural-new-game-original-admission/v2")
                &&org.xar.ck3.control.contracts.StrictJson.text(row.get("kind")).equals("restored")
                &&org.xar.ck3.control.contracts.StrictJson.text(row.get("event_identity")).equals(binding.attachment().eventIdentity())
                &&row.get("actual_game").equals(binding.session().game().toJson())
                &&ExactRef.fromJson(row.get("history_basis")).equals(binding.originalHistoryBasis())
                &&ExactRef.fromJson(row.get("semantic")).equals(binding.semantic().semantic())
                &&ExactRef.fromJson(row.get("native_packet")).equals(binding.semantic().originalNativePacket())
                &&ExactRef.fromJson(row.get("original_driver")).equals(binding.semantic().originalDriver()),
                "actual preclock retained a different restoration producer, complete Driver or native origin");
        var origin=org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData.decode(
                archive.loadMaterial(ExactRef.fromJson(row.get("restored_origin"))).bytes());
        require(origin.equals(binding.requireReboundOrigin(same).evidence())&&origin.pair().equals(binding.pair()),
                "actual preclock source proof changed the original private paired SAVE restoration");
        require(Arrays.equals(archive.loadMaterial(ExactRef.fromJson(row.get("canonical_attachment_head"))).bytes(),
                org.xar.ck3.control.contracts.StrictJson.canonical(binding.attachment().head().toJson(),
                        org.xar.ck3.control.contracts.StrictJson.EXPLICIT_MAX_BYTES)),
                "actual preclock source changed its original canonical restore attachment");
    }

    private static void requireSemanticSlot(DriverStateSnapshot.Slot original,OpportunityJson.Obj snapshot,String field)throws IOException {
        var value=snapshot.get(field);
        if(original instanceof DriverStateSnapshot.Value present)
            require(value!=null&&OpportunityJson.parse(present.json()).equals(value),"actual full Driver and original SEM differ: "+field);
        else if(original instanceof DriverStateSnapshot.NullValue)
            require(value==OpportunityJson.Nil.INSTANCE,"explicit null became missing or a synthetic value: "+field);
        else require(!snapshot.members().containsKey(field),"missing field became synthetic at completed checkpoint: "+field);
    }

    private RootPendingUiRuntime.Current requireCurrent(Instant deadline)throws IOException {
        requireOwner();return context.withSession(same->{var actual=pending.current(same,deadline).orElseThrow(
                ()->missing("genuine installed pending Current is absent"));actual.requireCurrent(same);return actual;});
    }
    private void requireOwner()throws IOException {
        require(root.ownedBy(core)&&!root.isRetired()&&core.sessionAccess().current()==root
                &&context.actions()==root&&context.adopted()==root.driver(),"actual Root is no longer the current installed owner");
        context.game().verify();lifecycle.requireContext(context);pending.requireContext(context);
    }
    private Captured capture()throws IOException {
        requireOwner();return context.withSession(same->root.driver().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw missing("actual complete canonical Driver unavailable");
            var rows=List.copyOf(frozen.actions().actions());var original=rows.stream().filter(row->row.command().actionId().equals(parent.actionId()))
                    .findFirst().orElseThrow(()->missing("actual canonical original parent absent"));
            require(original.command().equals(parent),"actual original parent body/deadline was replaced");
            return new Captured(original,rows,known,same.head());}));
    }
    private void inspect(RootPendingUiRuntime.Current before,Captured capturedBefore,Captured after,Instant deadline)throws IOException {
        if(before.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT){
            var old=ActionTransitions.composite(capturedBefore.parent().state()).orElseThrow().children();
            var now=ActionTransitions.composite(after.parent().state()).orElseThrow().children();
            if(now.size()==old.size()+1){var child=now.getLast();var actual=after.rows().stream()
                    .filter(row->row.command().actionId().equals(child.actionId())).findFirst()
                    .orElseThrow(()->missing("actual Event child canonical receipt absent"));
                require(actual.bodySha256().equals(child.bodySha256()),"actual Event child body differs from original reservation");
                if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED)observed.add(Stage.EVENT);
            }
        }
        Optional<RootPendingUiRuntime.Current> current=context.withSession(same->pending.current(same,deadline));
        if(current.isPresent()){
            var state=current.orElseThrow().obligation();if(state.closeAttempt().isPresent()){
                var intent=state.closeAttempt().orElseThrow();if(onceCloseId==null)onceCloseId=intent.actionId();
                require(onceCloseId.equals(intent.actionId()),"same pending transition attempted a second Close identity");
                if(intent.receipt().isPresent()){
                    var receipt=intent.receipt().orElseThrow();context.withSession(same->{
                        var actual=context.archive().withSession(same).loadReceipt(receipt.canonicalReceipt());
                        require(actual.command().actionId().equals(intent.actionId())&&actual.bodySha256().equals(intent.commandBodySha256())
                                &&actual.command().operation().value().equals(NativeTimelineBlocker12004.CLOSE_STEP),
                                "retained once Close differs from its genuine canonical intent/body/operation");
                        require(ActionTransitions.composite(after.parent().state()).orElseThrow().children().stream()
                                .anyMatch(child->child.actionId().equals(intent.actionId())&&child.bodySha256().equals(actual.bodySha256())),
                                "once Close has no actual original parent child reservation");
                        require(after.rows().stream().anyMatch(row->row.command().equals(actual.command())
                                &&row.bodySha256().equals(actual.bodySha256())),"once Close has no same canonical writer child row");
                        return null;});observed.add(Stage.ONCE_CLOSE);
                    if(originalUnknownClose!=null)require(receipt.canonicalReceipt().equals(originalUnknownClose),"once Close rewrote original UNKNOWN ref");
                    if(receipt.effectiveDateAdvance().isPresent()){
                        context.withSession(same->{var actual=context.archive().withSession(same).loadReceipt(receipt.effectiveDateAdvance().orElseThrow());
                            require(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"date evidence is not an actual applied child");return null;});observed.add(Stage.DATE);
                    }
                }
            }
        }else if(after.parent().state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied applied){
            applied.proof().validateParent(parent);require(applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,
                    "final pending parent settled through a different lifecycle transition");
            requireNaturalFamilyDomains(after);observed.add(Stage.FINAL);
        }
        var children=ActionTransitions.composite(after.parent().state()).orElseThrow().children();
        long count=after.rows().stream().filter(row->row.command().operation().value().equals(NativeTimelineBlocker12004.CLOSE_STEP)
                &&children.stream().anyMatch(child->child.actionId().equals(row.command().actionId()))).count();
        require(count<=1,"same actual pending parent has multiple canonical Close actions");
    }
    /** Reads the real post-publication domains and retained pre-import originals; never creates a lifecycle token. */
    private void requireNaturalFamilyDomains(Captured after)throws IOException {
        context.withSession(same->{
            var proof=lifecycle.composite().requireCommittedEpisode(same,after.parent());
            require(proof instanceof LifecycleTransitionProof.ContinueSuccessor,"actual private successor publication required");
            var publication=proof.publication();var events=publication.committedDocuments();
            require(events.size()==1,"actual natural lifecycle event pin required");
            var event=events.getFirst();same.verifyPin(event);
            var edge=same.readHistoricalTransition(event);
            require(edge.eventIdentity().equals(publication.eventIdentity())&&edge.kind().equals(LifecycleChild.KIND)
                    &&edge.sequence()==publication.eventSequence(),"Family migration material is not the original canonical natural event");
            var before=parent.lifecycleBefore().subject();var current=after.known().driver().session();
            for(var slot:List.of(DomainBodies.Slot.FAMILY,DomainBodies.Slot.CHILD_MATRILINEAL,DomainBodies.Slot.DEFAULT_MARRIAGE)) {
                var original=DomainBodies.reference(publication.after(),slot)
                        .orElseThrow(()->missing("actual pre-migration Family slot unavailable: "+slot));
                var pin=new WriterContracts.Pin(original.payload(),original.identity());
                var bytes=same.readPinned(pin,org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES);same.verifyPin(pin);
                var read=same.readDomain(slot);
                if(!(read instanceof DomainBodies.Available available))throw missing("actual migrated Family slot unavailable: "+slot);
                var body=org.xar.ck3.control.contracts.StrictJson.parse(available.canonicalBody(),org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES);
                var transition=FamilyNaturalEpisodeMigration.Transition.fromJson(body.get(FamilyNaturalEpisodeMigration.FIELD));
                require(transition.owner().equals(root.identity())&&transition.before().runId().equals(before.episodeRunId())
                        &&transition.before().player().equals(before.characterId())&&transition.after().runId().equals(current.episodeRunId())
                        &&transition.after().player().equals(current.actorId())&&transition.previousBody().equals(original.payload())
                        &&transition.lifecycleMaterial().equals(event.reference()),
                        "actual Family slot lost its same-Game original episode/event/body binding: "+slot);
                require(Arrays.equals(available.canonicalBody(),FamilyNaturalEpisodeMigration.derive(slot,bytes,transition)),
                        "actual Family migration did not preserve the complete original pending/resolved history: "+slot);
            }
            return null;
        });
    }
    private static void requireProgress(Captured before,Captured after)throws IOException {
        require(before.parent().command().equals(after.parent().command()),"continuation replaced original parent");
        var old=ActionTransitions.composite(before.parent().state()).orElseThrow().children();
        var now=ActionTransitions.composite(after.parent().state()).orElseThrow().children();
        require(now.size()>=old.size()&&now.size()<=old.size()+1&&now.subList(0,old.size()).equals(old),
                "one finite continuation discarded/reordered old children or added more than one top-level child");
        require(before.known().stamp().game().equals(after.known().stamp().game())
                &&before.known().stamp().episodeEpoch()==after.known().stamp().episodeEpoch()
                &&before.known().driver().session().equals(after.known().driver().session()),
                "pending continuation repeated adoption or changed its actual actor/run/epoch");
        var oldHistory=before.known().driver().commandHistory();var nowHistory=after.known().driver().commandHistory();
        require(nowHistory.size()>=oldHistory.size(),"pending continuation discarded actual Driver history");
        for(int index=0;index<oldHistory.size();index++)require(Arrays.equals(oldHistory.get(index).originalRow().json(),
                nowHistory.get(index).originalRow().json()),"pending continuation rewrote original Driver history");
    }
    private static void requireReadOnly(Captured before,Captured after)throws IOException {
        var a=before.head();var b=after.head();require(before.rows().equals(after.rows())&&before.parent().equals(after.parent())
                &&a.digest().equals(b.digest())&&a.documents().equals(b.documents())&&a.absent().equals(b.absent())
                &&a.indexRepairs().equals(b.indexRepairs())&&a.snapshotNeedsRecovery()==b.snapshotNeedsRecovery(),
                "read-only/rejected path changed canonical actions or writer Head");
    }
    private static IOException missing(String detail){return new IOException("MISSING_NOT_RUN: "+detail);}
    private static void require(boolean condition,String detail)throws IOException {if(!condition)throw new IOException(detail);}
}
