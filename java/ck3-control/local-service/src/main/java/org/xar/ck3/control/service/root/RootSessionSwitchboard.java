package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundCycle;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.OrdinarySessionHost;

/** One submit authority switches only after actual restore, cycle rebind and a fresh native source scope. */
final class RootSessionSwitchboard implements ActionPorts.GuardPort, PlanningReadCoordinator.ReadGuardPort, ActionPorts.RecordedEvidenceVerifier {
    record View(SessionIdentity identity, ActionPorts.GuardPort actions, PlanningReadCoordinator.ReadGuardPort reads,
            NativeRecordedEvidenceVerifier originals) {
        View { Objects.requireNonNull(identity); Objects.requireNonNull(actions); Objects.requireNonNull(reads); Objects.requireNonNull(originals); }
    }
    private final ContinuityWriter writer;
    private final Map<SessionIdentity, View> archived = new HashMap<>();
    private volatile View active;
    private record FirstSave(ContinuityStorePort.Session same,RootApplicationAssembly.Core core,
            RootNextEpisodeWindowRuntime.Begun begun,View candidate,ActionCommand original,ActionPorts.GuardPort dedicated) { }
    private final ThreadLocal<FirstSave> firstSave=new ThreadLocal<>();
    @FunctionalInterface interface FirstSaveWork<T> { T run() throws IOException,InterruptedException; }
    RootSessionSwitchboard(ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
    synchronized void installInitial(View initial) {
        StrictJson.require(active == null && archived.isEmpty(), "initial Game authority already installed");
        active = Objects.requireNonNull(initial); archived.put(initial.identity(), initial);
    }
    View current() { return Objects.requireNonNull(active, "actual Root Game authority is absent"); }
    @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
        FirstSave opening=firstSave.get();
        if(opening!=null&&sameOwner(opening.candidate(),command.origin().machineId(),command.origin().game(),command.sessionId())) {
            requireFirstSave(opening,command);
            return opening.dedicated().verify(head,command);
        }
        View view = owned(command.origin().machineId(), command.origin().game(), command.sessionId());
        return view.actions().verify(head, command);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
        FirstSave opening=firstSave.get();
        StrictJson.require(opening==null||!sameOwner(opening.candidate(),request.origin().machineId(),request.origin().game(),request.sessionId()),
                "the private first SAVE scope grants no candidate ordinary planning read");
        View view = owned(request.origin().machineId(), request.origin().game(), request.sessionId());
        return view.reads().verify(head, request, contract);
    }
    @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,
            ReadContract<?> contract,java.util.function.Supplier<T> work) {
        Objects.requireNonNull(work);
        FirstSave opening=firstSave.get();
        StrictJson.require(opening==null||!sameOwner(opening.candidate(),request.origin().machineId(),request.origin().game(),request.sessionId()),
                "the private first SAVE scope grants no candidate original-read source");
        View view=owned(request.origin().machineId(),request.origin().game(),request.sessionId());
        try { return view.reads().withOriginalReadSource(head,request,contract,work); }
        finally {
            StrictJson.require(active==view&&firstSave.get()==opening,
                    "original read source cannot outlive its identical active Game authority or first-SAVE scope");
            StrictJson.require(owned(request.origin().machineId(),request.origin().game(),request.sessionId())==view,
                    "original read source changed its actual active View");
        }
    }
    @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
        FirstSave opening=firstSave.get();
        StrictJson.require(opening==null||!sameOwner(opening.candidate(),request.origin().machineId(),request.origin().game(),request.sessionId()),
                "the private first SAVE scope grants no candidate current-original planning read");
        View view=owned(request.origin().machineId(),request.origin().game(),request.sessionId());
        return view.reads().verifyOriginalCurrent(head,request,contract);
    }
    @Override public void verifyFrontendReadContinuation(WriterContracts.Head head,PlanningReadRequest request,
            ReadContract<?> contract,PlanningReadGuard before,PlanningReadGuard after){
        FirstSave opening=firstSave.get();
        StrictJson.require(request.origin() instanceof CommandOrigin.Frontend
                &&(opening==null||!sameOwner(opening.candidate(),request.origin().machineId(),request.origin().game(),request.sessionId())),
                "the private first SAVE scope grants no candidate frontend continuation");
        View view=owned(request.origin().machineId(),request.origin().game(),request.sessionId());
        view.reads().verifyFrontendReadContinuation(head,request,contract,before,after);
    }
    @Override public void verify(WriterContracts.Head head, ActionReceipt receipt) {
        try {
            writer.requireSession(writer.borrowedSession());
            SessionIdentity identity = new SessionIdentity(receipt.command().origin().machineId(), receipt.command().origin().game(), receipt.command().sessionId());
            View original = archived.get(identity);
            FirstSave opening=firstSave.get();
            if(original==null&&opening!=null&&opening.candidate().identity().equals(identity)) {
                requireFirstSave(opening,receipt.command());original=opening.candidate();
            }
            StrictJson.require(original != null, "original action evidence has no retained actual session verifier"); original.originals().verify(head, receipt);
        } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    /** The sole coordinator can submit only this genuine first SAVE before the public host changes. */
    <T>T withFirstSave(ContinuityStorePort.Session same,RootApplicationAssembly.Core core,View expected,View candidate,
            RootNextEpisodeWindowRuntime.Begun begun,ActionCommand original,ActionPorts.GuardPort dedicated,FirstSaveWork<T> work)throws IOException,InterruptedException {
        writer.requireSession(same);Objects.requireNonNull(work);
        StrictJson.require(firstSave.get()==null&&active==expected&&candidate!=expected&&!archived.containsKey(candidate.identity()),
                "one private first SAVE scope must retain the unchanged original public Game authority");
        core.nextEpisodeWindows().requireBegun(same,begun);
        var driverSession=begun.stage().driver().session();
        StrictJson.require(begun.stage().previous().identity().equals(expected.identity())
                &&driverSession.machineId().equals(candidate.identity().machineId())
                &&driverSession.game().equals(candidate.identity().game())
                &&driverSession.sessionId().equals(candidate.identity().sessionId()),"first SAVE belongs to another private actual NEXT stage");
        FirstSave scope=new FirstSave(same,core,begun,candidate,Objects.requireNonNull(original),Objects.requireNonNull(dedicated));
        requireFirstSave(scope,original);firstSave.set(scope);
        try{return work.run();}
        finally{firstSave.remove();writer.requireSession(same);StrictJson.require(active==expected,"private first SAVE changed the public host authority");}
    }
    private void requireFirstSave(FirstSave scope,ActionCommand command) {
        try {
            writer.requireSession(scope.same());scope.core().nextEpisodeWindows().requireBegun(scope.same(),scope.begun());
            StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(scope.original()))
                    &&command.operation().equals(RootSaveRuntime.OPERATION)
                    &&command.origin() instanceof CommandOrigin.Gameplay
                    &&sameOwner(scope.candidate(),command.origin().machineId(),command.origin().game(),command.sessionId())
                    &&command.source().equals(scope.begun().stage().source())&&command.arguments().members().isEmpty()
                    &&command.expected().observerSchema().equals(org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory.OBSERVER_SCHEMA),
                    "a private first SAVE scope cannot prepare another command, reuse another source or replay ordinary actions");
        }catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private static boolean sameOwner(View view,String machine,org.xar.ck3.control.contracts.GameGeneration game,String session) {
        return view.identity().machineId().equals(machine)&&view.identity().game().equals(game)&&view.identity().sessionId().equals(session);
    }
    /** The host monitor excludes public selection until all private final switches have completed. */
    synchronized void publishNext(ContinuityStorePort.Session same,View expected,View successor,
            org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding baseline,
            org.xar.ck3.control.application.session.ContinuityBatchJournal batches,
            org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundNextBaseline rebound,
            OrdinarySessionHost host,SessionController previous,SessionController replacement,
            RootSavedAttachmentLoader saved,
            org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority.SourceLoader expectedLoader,
            org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority.SourceLoader replacementLoader,
            RootReadHistoryAuthority readHistory,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher previousReads,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher replacementReads,
            org.xar.ck3.control.application.driver.DriverCapabilityRuntime previousRuntime,
            org.xar.ck3.control.application.driver.DriverCapabilityRuntime candidate,
            RootApplicationAssembly.NextHostCommit rootPublication)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(rootPublication);Objects.requireNonNull(baseline);
        StrictJson.require(firstSave.get()==null&&active==expected&&previous.isRetired()&&!previous.isRunning()
                &&host.current().orElseThrow()==previous&&!replacement.isRetired()&&!replacement.isRunning()&&!replacement.isQuarantined(),
                "next publication requires the unchanged actual retired host and idle complete successor");
        StrictJson.require(rebound.binding()==baseline&&rebound.newSavedDayCredit()==0&&rebound.newCompletedCycleCredit()==0
                &&expected.identity().equals(baseline.beforeOwner())&&successor.identity().equals(baseline.afterOwner())
                &&replacement.identity().equals(successor.identity())&&!expected.identity().game().equals(successor.identity().game())
                &&!expected.identity().sessionId().equals(successor.identity().sessionId()),
                "the actual first SAVE/BASELINE and zero-credit cycle branch must own this new physical Game");
        batches.requireCurrent(same,rebound);baseline.requireCurrent(same);
        StrictJson.require(archived.size()<64&&!archived.containsKey(successor.identity()),"bounded unique next-session verifier retention required");
        var savedPublication=saved.preparePublication(same,expectedLoader,replacementLoader);
        var readPublication=readHistory.preparePublication(same,previousReads,replacementReads);
        StrictJson.require(candidate.readHistoryPublisher()==replacementReads&&previousRuntime.readHistoryPublisher()==previousReads,
                "next callback and read-history publication must retain their identical per-Game producers");
        archived.put(successor.identity(),successor);
        try {
            host.publishRetired(previous,replacement,()->{
                // Source18 validates everything, including its trailing frozen lease, before the callback assignment.
                candidate.activateNext(same,previousRuntime,baseline);
                savedPublication.commit();readPublication.commit();active=successor;rootPublication.commit();
            });
        }catch(IOException|RuntimeException failure){archived.remove(successor.identity());throw failure;}
    }
    private View owned(String machine, org.xar.ck3.control.contracts.GameGeneration game, String session) {
        View view = current();
        StrictJson.require(view.identity().machineId().equals(machine) && view.identity().game().equals(game)
                && view.identity().sessionId().equals(session), "original Game authority retired; no stale native submission or read"); return view;
    }
    /** Called from the successor collector's actual read-only lease while the same writer lock is held. */
    synchronized void publishRestored(ContinuityStorePort.Session borrowed, View expected, View successor,
            RestoreBinding restore, ReboundCycle rebound, OrdinarySessionHost host,
            SessionController previous, SessionController replacement, RootSavedAttachmentLoader saved,
            org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority.SourceLoader expectedLoader,
            org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority.SourceLoader replacementLoader,
            RootReadHistoryAuthority readHistory,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher previousReads,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher replacementReads) throws IOException {
        writer.requireSession(borrowed); Objects.requireNonNull(restore); Objects.requireNonNull(rebound);
        StrictJson.require(active == expected && previous.isRetired() && !previous.isRunning()
                && host.current().orElseThrow() == previous && !replacement.isRetired() && !replacement.isRunning() && !replacement.isQuarantined(),
                "retired-host and current Root authority changed before restored publication");
        StrictJson.require(rebound.restore() == restore && rebound.newSavedDayCredit() == 0 && restore.newSavedDayCredit() == 0
                && successor.identity().equals(restore.session()) && replacement.identity().equals(successor.identity())
                && expected.identity().equals(previous.identity()) && !successor.identity().game().equals(expected.identity().game())
                && !successor.identity().sessionId().equals(expected.identity().sessionId())
                && borrowed.head().digest().equals(ContinuityJson.digest(rebound.committed().head().toJson())),
                "actual committed restored cycle/source/head required for the unique authority switch");
        StrictJson.require(archived.size() < 64 && !archived.containsKey(successor.identity()), "bounded unique restored session verifier required");
        saved.requireCurrent(expectedLoader); Objects.requireNonNull(replacementLoader);
        readHistory.requireCurrent(borrowed,previousReads);Objects.requireNonNull(replacementReads);
        // Allocate the archived verifier first. A rejected host CAS leaves the old authority active.
        archived.put(successor.identity(), successor);
        try { host.replaceRetired(previous, replacement); }
        catch (RuntimeException rejected) { archived.remove(successor.identity()); throw rejected; }
        saved.publish(expectedLoader, replacementLoader);
        readHistory.publish(previousReads,replacementReads);
        active = successor;
    }
}
