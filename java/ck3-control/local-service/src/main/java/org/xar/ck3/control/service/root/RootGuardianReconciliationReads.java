package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Actual Guardian installer query supplier and original admission. It never queries, submits, publishes or reconciles independently. */
public final class RootGuardianReconciliationReads implements GuardianReconciliationQueries.CanonicalAdmission {
    private final RootRuntimeContext context;
    private final ReadContract<OrdinaryContext> ordinary;
    private final GuardianReconciliationQueries queries;
    private final ExactRef decoder;
    private final KnownInteractionsRuntimeInstaller currentInteractions;
    private GuardianOutgoingInstaller installer;
    RootGuardianReconciliationReads(RootRuntimeContext actual,ReadContract<OrdinaryContext> sameOrdinary,Build actualBuild,
            ExactRef actualProfileSource,ExactRef actualDecoderSource) {
        context=Objects.requireNonNull(actual);ordinary=Objects.requireNonNull(sameOrdinary);decoder=Objects.requireNonNull(actualDecoderSource);
        StrictJson.require(decoder.bytes()>0,"actual guardian decoder source required");
        currentInteractions=null;
        queries=new GuardianReconciliationQueries(ordinary,actualBuild,actualProfileSource,this);
    }
    RootGuardianReconciliationReads(RootRuntimeContext actual,ReadContract<OrdinaryContext> sameOrdinary,
            KnownInteractionsRuntimeInstaller sameInteractions,ExactRef actualProfileSource,ExactRef actualDecoderSource) {
        context=Objects.requireNonNull(actual);ordinary=Objects.requireNonNull(sameOrdinary);decoder=Objects.requireNonNull(actualDecoderSource);
        StrictJson.require(decoder.bytes()>0,"actual guardian decoder source required");
        currentInteractions=Objects.requireNonNull(sameInteractions);currentInteractions.requireContext(context);
        StrictJson.require(ordinary==currentInteractions.definitions().ordinaryQuery(),"guardian must retain its identical Known ordinary query");
        queries=createQueries(ordinary,currentInteractions.sources().configuredBuild(),actualProfileSource,this);
    }
    static GuardianReconciliationQueries createQueries(ReadContract<OrdinaryContext> sameOrdinary,
            KnownInteractionsRuntimeInstaller.ConfiguredBuild configuredBuild,ExactRef profile,
            GuardianReconciliationQueries.CanonicalAdmission admission) {
        Objects.requireNonNull(configuredBuild);
        return configuredBuild.qualified()
                ?new GuardianReconciliationQueries(sameOrdinary,configuredBuild.requireQualified(),profile,admission)
                :GuardianReconciliationQueries.historicalCrozier4(sameOrdinary,profile,admission);
    }
    /** Current projection and genuine ordinary READ are distinct stages; no Known receipt is manufactured. */
    PlanningReadResult<OrdinaryContext> liveContextRead(Complete actual,ActionCommand command,Instant deadline) {
        try{return liveContextReadChecked(actual,command,deadline);}
        catch(IOException failure){throw new UncheckedIOException("actual guardian current context unavailable",failure);}
    }
    private PlanningReadResult<OrdinaryContext> liveContextReadChecked(Complete actual,ActionCommand command,Instant deadline)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(command);Objects.requireNonNull(deadline);
        StrictJson.require(currentInteractions!=null,"guardian current context source is not bound");
        context.requireCurrent(deadline);var same=context.borrowedSession();context.writer().requireSession(same);
        StrictJson.require(actual.identity().machineId().equals(command.before().machineId())
                &&actual.identity().game().equals(command.before().game())
                &&actual.identity().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                &&actual.source().equals(command.source())&&actual.sessionId().equals(command.sessionId()),
                "guardian current context crossed its actual command Game/source/session/episode");
        var result=currentInteractions.readCurrentFrame(actual,deadline);
        return currentResult(result,frame->{
            var intent=org.xar.ck3.control.application.action.ordinary.OrdinaryInitiationIntent.fromJson(command.arguments());
            var education=intent.education().map(value->new EducationIntent(
                    java.util.Optional.of(new CharacterId(value.childId())),java.util.Optional.of(new CharacterId(value.guardianId())),
                    java.util.Optional.of(value.optionKeys().stream().map(InteractionKey::new).toList())));
            return currentInteractions.capabilities().queryCharacterInteractionOrdinaryV1(frame,
                    new OrdinaryRequest(new InteractionKey(intent.interactionKey()),new CharacterId(intent.recipientId()),education));
        });
    }
    static PlanningReadResult<OrdinaryContext> currentResult(KnownPendingInteractionPolicy.ContextRead actual,
            java.util.function.Function<Context,PlanningReadResult<OrdinaryContext>> realOrdinaryRead) {
        Objects.requireNonNull(actual);Objects.requireNonNull(realOrdinaryRead);
        if(actual instanceof KnownPendingInteractionPolicy.Unavailable missing)return unavailable(missing.result());
        return Objects.requireNonNull(realOrdinaryRead.apply(((KnownPendingInteractionPolicy.Available)actual).context()));
    }
    static PlanningReadResult.Unavailable<OrdinaryContext> unavailable(PlanningReadResult.Unavailable<Context> actual) {
        Objects.requireNonNull(actual);
        return new PlanningReadResult.Unavailable<>(actual.reason(),actual.original(),actual.decodeFailure(),actual.observedFailure());
    }
    synchronized void bind(GuardianOutgoingInstaller actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(installer==null&&actual.reconciliationQueries()==queries,"actual guardian query/preparer/effect products bind once");
        installer=actual;
    }
    private synchronized GuardianOutgoingInstaller installer() {
        StrictJson.require(installer!=null,"actual guardian installer is not bound");return installer;
    }
    public GuardianReconciliationQueries queries(){return queries;}
    public void requireContext(RootRuntimeContext actual){StrictJson.require(context==actual,"guardian read provider belongs to another physical Root");}
    public List<RootReadContractCatalog.InstalledRead> installedReads(){return List.of(new RootReadContractCatalog.InstalledRead(queries.contract(),decoder));}
    public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return this::allowedReads;}
    private void requireInstalled(){
        StrictJson.require(context.readCatalog().containsIdentity(ordinary)&&context.readCatalog().containsIdentity(queries.contract()),
                "guardian provider did not retain the identical installed ordinary/canonical read objects");installer();
    }
    private List<RootReconciliationAuthority.AllowedRead> allowedReads(ActionReceipt original,ReconciliationIdentity identity,
            Complete actual,Instant deadline)throws IOException {
        if(!GuardianOutgoingEffects.accepts(original.command()))return List.of();
        var same=context.borrowedSession();context.writer().requireSession(same);requireInstalled();
        if(!queries.liveReadsEnabled()) {
            // The archive profile remains installed, but cannot issue a current native query.
            // Resolve the actual current typed negative result; unresolved originals stay pending.
            var current=currentInteractions.readCurrentFrame(actual,deadline);
            StrictJson.require(current instanceof KnownPendingInteractionPolicy.Unavailable,
                    "archive-only guardian profile cannot acquire a live context");
            return List.of();
        }
        var archive=context.archive().withSession(same);
        ActionReceipt retained=original(identity,archive);
        StrictJson.require(retained.equals(original),"guardian query policy changed the exact retained canonical original");
        var attempt=ActionTransitions.attempt(retained.state()).orElseThrow();
        var dispatch=ActionTransitions.dispatch(retained.state()).orElseThrow();
        // Family send observation requires the original successful response custody.
        // Transport UNKNOWN remains unresolved and is never resubmitted or promoted.
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.custody().isEmpty())return List.of();
        preparation(same,retained,attempt,archive);
        var issued=queries.issue(identity,retained.command(),attempt,actual,deadline);
        return List.of(new RootReconciliationAuthority.AllowedRead(issued.contract(),issued.request().arguments(),
                RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION));
    }
    private static ActionReceipt original(ReconciliationIdentity identity,ActionPorts.OutcomeArchive archive) {
        ActionReceipt retained=archive.loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(!retained.settled()&&GuardianOutgoingEffects.accepts(retained.command())
                &&retained.command().actionId().equals(identity.pending().actionId())&&retained.bodySha256().equals(identity.pending().bodySha256())
                &&ActionCodec.bodySha256(retained.command()).equals(retained.bodySha256())
                &&retained.command().before().equals(identity.pending().originalBefore())
                &&retained.command().source().equals(identity.source())&&retained.command().sessionId().equals(identity.sessionId()),
                "guardian pending is not the exact retained canonical education action");
        return retained;
    }
    private void preparation(Session same,ActionReceipt retained,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive)throws IOException {
        RootGuardEvidence.requireHistory(attempt.guard(),archive,same);
        var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
        installer().effects().loadPreparation(same,retained.command(),attempt.requestId(),attempt.preparedRequest(),before,archive);
    }
    @Override public void verifyCurrent(PlanningReadRequest request) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);requireInstalled();
            var identity=request.origin().requireReconciliation();
            context.reconciliation().current(same,identity,request.deadline(),lease->{
                GuardianReconciliationQueries.requireOriginalRequest(request,lease.canonical().command(),lease.attempt());
                queries.requireFrame(request,lease.complete());
                var archive=context.archive().withSession(same);
                StrictJson.require(original(identity,archive).equals(lease.canonical()),"guardian current read changed its actual canonical pending receipt");
                preparation(same,lease.canonical(),lease.attempt(),archive);lease.assertCurrent(same);return null;
            });
        }catch(IOException failure){throw new UncheckedIOException("actual canonical guardian current admission unavailable",failure);}
    }
    @Override public void verifyOriginal(PlanningReadReceipt read) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);requireInstalled();
            var archive=context.archive().withSession(same);var identity=read.request().origin().requireReconciliation();
            var retained=original(identity,archive);var attempt=ActionTransitions.attempt(retained.state()).orElseThrow();
            GuardianReconciliationQueries.requireOriginalRequest(read.request(),retained.command(),attempt);preparation(same,retained,attempt,archive);
            // Actual decode precedes preserveRead; the profile checks original packet/
            // custody now, and effect/archive consumers require the persisted read later.
            for(var guard:List.of(read.before(),read.after())) {
                Complete actual=context.reconciliation().verifyArchived(guard.binding(),archive,same,context.originals());
                queries.requireFrame(read.request(),actual);
                StrictJson.require(actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())
                        &&actual.sessionId().equals(identity.sessionId())&&actual.connectionGeneration().equals(identity.connectionGeneration())
                        &&NativeEffectEvidence.basis(actual).driverFacts().equals(identity.evidence().observationManifest()),
                        "guardian archived read changed its original full native/Driver factual frame");
            }
        }catch(IOException failure){throw new UncheckedIOException("actual canonical guardian original admission unavailable",failure);}
    }
}

