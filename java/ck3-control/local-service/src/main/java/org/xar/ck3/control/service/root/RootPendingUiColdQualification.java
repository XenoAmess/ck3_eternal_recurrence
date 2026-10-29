package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.runtime.lifecycle.NaturalEngineClockProof;
import org.xar.ck3.control.runtime.lifecycle.PendingNaturalCauseProof;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Originals;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Packet;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.CauseOriginals;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.EstateOriginals;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.PendingCause;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.RetainedOriginals;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.RootCausePort;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.RootRetainedCausePort;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/**
 * Reopens the actual ancestor that issued a retained pending cause. This port neither decodes a
 * PendingCause nor adopts a Driver. M3 reuses its private issuer after this historical port succeeds;
 * the pending-publication owner separately restores the canonical publication and current UI gate.
 */
public final class RootPendingUiColdQualification implements RootRetainedCausePort {
    private final RootRuntimeContext context;
    private final RootNaturalSuccessionOriginals natural;
    @FunctionalInterface interface PhysicalContinuity {
        void require(ContinuityStorePort.Session same,NaturalClockOriginals.Capture capture,SourceQualification source)throws IOException;
    }
    @FunctionalInterface interface SourceContinuity {
        void require(ContinuityStorePort.Session same,Optional<ExactRef> historical,SourceQualification source)throws IOException;
    }
    private final PhysicalContinuity physical;
    private final SourceContinuity sources;
    private record QualifiedRecovery(HistoricalScope scope,PendingCause cause) { }
    private final ThreadLocal<QualifiedRecovery> qualified=new ThreadLocal<>();

    public RootPendingUiColdQualification(RootRuntimeContext context,RootNaturalSuccessionOriginals identicalNatural) {
        this(context,identicalNatural,identicalNatural::requireRetainedPhysical,
                (same,historical,actual)->{context.writer().requireSession(same);actual.assertCurrent(same);});
    }
    RootPendingUiColdQualification(RootRuntimeContext context,RootNaturalSuccessionOriginals identicalNatural,
            PhysicalContinuity physical,SourceContinuity sources) {
        this.context=Objects.requireNonNull(context);natural=Objects.requireNonNull(identicalNatural);
        this.physical=Objects.requireNonNull(physical);this.sources=Objects.requireNonNull(sources);
        StrictJson.require(natural.core()==context.core(),"cold qualification must retain the identical natural Root/Core");
    }

    @Override public RetainedOriginals openRetainedQualified(ExactRef retainedProof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,Head currentHead)throws IOException {
        qualified.remove();
        try {
            requireCurrentSource(same,current,source,currentHead);
            var live=currentDocument(same);
            var pending=live.pendingProjection().orElseThrow(()->new IOException("no actual canonical pending projection exists"));
            var pins=new ArrayList<Pin>();
            var obligation=SuccessorUiObligationCodec.decode(read(same,pending.currentObligation(),pins));
            StrictJson.require(pending.value().qualifiedCause().equals(retainedProof)
                    &&obligation.binding().qualifiedCause().equals(retainedProof)
                    &&obligation.binding().causeDigest().equals(retainedProof.sha256()),
                    "retained cause is not the exact canonical pending obligation");
            var proof=PendingNaturalCauseProof.decode(read(same,retainedProof,pins));
            Head historical=same.requireHistoricalHead(proof.writerHeadSequence(),proof.writerHeadSha256());
            DomainBodies.BodyRef body=requireHistoricalDomain(same,historical,natural.registration());
            var previous=NaturalClockOriginals.decode(read(same,body.payload(),pins));
            physical.require(same,previous.capture(),source);
            var ready=previous.ready().orElseThrow(()->new IOException("retained ancestor lacks completed natural originals"));
            StrictJson.require(previous.pendingProjection().isEmpty()&&ready.closeReceipt().isEmpty()
                    &&ready.subsequentTimeline().isEmpty()&&previous.capture().equals(live.capture())
                    &&ready.equals(live.ready().orElseThrow()),"cause ancestor must be the exact pre-pending, pre-Close domain");
            var binding=obligation.binding();
            StrictJson.require(binding.preclockDocument().equals(body.payload())
                    &&binding.parentActionId().equals(ready.parentActionId())
                    &&binding.parentBodySha256().equals(ready.parentBodySha256())
                    &&binding.originalParentCommand().equals(ready.parentCommand()),"canonical pending parent/ancestor binding drift");
            ActionCommand parent=ActionCodec.decodeCommand(read(same,ready.parentCommand(),pins));
            StrictJson.require(parent.actionId().equals(ready.parentActionId())
                    &&ActionCodec.bodySha256(parent).equals(ready.parentBodySha256())
                    &&ActionCodec.bodySha256(parent).equals(proof.parentBodySha256()),"historical parent command/body differs");
            var scoped=context.archive().withSession(same);
            ActionReceipt historicalParent=ContinuityActionJournal.lookup(historical.state(),parent.actionId(),scoped)
                    .orElseThrow(()->new IOException("natural parent is absent from the verified historical action chain"));
            StrictJson.require(Arrays.equals(ActionCodec.encodeCommand(historicalParent.command()),ActionCodec.encodeCommand(parent))
                    &&historicalParent.state() instanceof ActionState.CompositeRunning running
                    &&running.execution().handlerId().equals("java-death-succession-next-episode/v1"),
                    "historical cause was not prepared by the actual running natural continuation");

            var death=scoped.loadRead(ready.predecessorDeath());
            var replay=RootLifecycleGuardEvidence.replay(death.after().binding(),scoped,same,context.originals());
            RawJson originalKnownBytes=DriverSnapshotFacts.originalKnownJson(read(same,proof.originalKnown(),pins));
            var observation=DriverSnapshotFacts.observationOriginalReference(originalKnownBytes);
            StrictJson.require(observation.isEmpty()||observation.orElseThrow().equals(replay.original().facts().semanticFactsEvidence()),
                    "retained Known observation reference differs from the actual old guard manifest");
            var originalKnown=DriverSnapshotFacts.decodeKnownOriginal(originalKnownBytes,
                    observation.isPresent()?Optional.of(replay.original().facts()):Optional.empty());
            var oldTerminal=new LifecycleObservationPort.Snapshot(replay.original().actual(),parent.source(),replay.semantic(),
                    originalKnown,ready.finalNativePacket());
            requireOldTerminal(proof,previous,parent,oldTerminal,replay,read(same,ready.finalDriver(),pins),
                    read(same,ready.finalSemantic(),pins));

            ActionReceipt clock=natural.requireRetainedClock(same,previous.capture());
            var engine=NaturalEngineClockProof.decode(read(same,proof.engineClockProof(),pins));
            engine.requireBoundTo(proof.machineId(),oldTerminal.actual().observedAt(),historical.digest(),
                    previous.capture().rootResult(),oldTerminal.originalEvidence());
            ActionReceipt retainedClock=scoped.loadReceipt(engine.clockReceipt());
            ContinuityActionJournal.requireHistoricalReceipt(historical.state(),retainedClock,scoped);
            StrictJson.require(engine.originalDomain().equals(body.payload())
                    &&engine.clockCommand().equals(previous.capture().clockCommand())
                    &&engine.clockOutcome()==retainedClock.outcome()
                    &&Arrays.equals(ActionCodec.encodeCommand(clock.command()),ActionCodec.encodeCommand(retainedClock.command()))
                    &&ActionTransitions.attempt(clock.state()).equals(ActionTransitions.attempt(retainedClock.state()))
                    &&ActionTransitions.dispatch(clock.state()).equals(ActionTransitions.dispatch(retainedClock.state())),
                    "retained engine proof has no identical canonical clock command/attempt/dispatch");
            var engineSource=engine.completeSourceQualification();
            if(engineSource.isPresent())read(same,engineSource.orElseThrow(),pins);
            if(source.proof().isPresent())read(same,source.proof().orElseThrow(),pins);
            sources.require(same,engineSource,source);
            var currentMetadata=context.sources().optionalMetadata(same,source);
            if(currentMetadata.isPresent()&&binding.sourceEpochSha256().isPresent())
                StrictJson.require(currentMetadata.orElseThrow().ownerSourceEpoch().equals(binding.sourceEpochSha256().orElseThrow()),
                        "pending source epoch differs from the real current loaded sources");

            read(same,proof.successorRootRead(),pins);
            var successorRead=natural.requireRetainedRoot(same,proof.successorRootRead());
            var successorGuard=RootLifecycleGuardEvidence.replay(successorRead.after().binding(),scoped,same,context.originals());
            byte[] successorResult=read(same,proof.successorRootResult(),pins);
            byte[] successorSemantic=read(same,proof.successorSemantic(),pins);
            StrictJson.require(successorRead.request().source().equals(parent.source())
                    &&successorRead.request().sessionId().equals(parent.sessionId())
                    &&successorRead.request().origin().requireLifecycleTerminal().sameGuardFrame(replay.identity())
                    &&successorRead.original().originalResultToken().orElseThrow().equals(new RawJson(successorResult))
                    &&Arrays.equals(DriverJson.encode(successorGuard.semantic()),successorSemantic)
                    &&successorGuard.semantic().equals(oldTerminal.semantic())
                    &&successorGuard.original().actual().session().equals(oldTerminal.actual().session()),
                    "retained successor ROOT receipt/result/complete SEM crossed its real old-terminal frame");
            var frozen=SuccessionNativeEstate12004.freeze(read(same,previous.capture().rootResult(),pins),
                    read(same,previous.capture().semantic(),pins));
            var estate=SuccessionNativeEstate12004.reconcile(frozen,successorResult,successorSemantic);
            StrictJson.require(DriverJson.sha256(estate.wire()).equals(proof.estateReconciliationSha256())
                    &&DriverJson.sha256(death.original().originalPacket()).equals(proof.retainedDeathOriginalSha256()),
                    "replayed estate/death differs from the exact retained cause proof");
            Packet initial=natural.timeline().packet(ready.initialTimeline());
            var originals=new Originals(RootNaturalSuccessionOriginals.session(previous.capture()),previous.capture().predecessorFrame(),
                    previous.capture().rootResult(),proof.engineClockProof(),death,initial,Optional.empty(),List.of());
            var estateOriginals=new EstateOriginals(successorRead,proof.successorRootRead(),proof.successorRootResult(),
                    proof.successorSemantic(),proof.originalKnown());
            var scope=new HistoricalScope(same,current,currentHead,source,retainedProof,historical,body,previous,parent,
                    oldTerminal,new CauseOriginals(originals,estate,estateOriginals),List.copyOf(pins));
            scope.requirePinned();
            return new RetainedOriginals(parent,oldTerminal,historical,scope);
        } catch(IllegalArgumentException|ArithmeticException|UncheckedIOException invalid) {
            throw new IOException("retained pending cause remains unqualified: "+invalid.getMessage(),invalid);
        }
    }

    @Override public void requireRetainedCurrent(RetainedOriginals originals,ExactRef retainedProof,PendingCause rederived,
            FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,Head currentHead)throws IOException {
        Objects.requireNonNull(originals);Objects.requireNonNull(rederived);
        if(!(originals.historicalPort() instanceof HistoricalScope scope)||scope.owner()!=this
                ||scope.same!=same||scope.current!=current||scope.source!=source||scope.currentHead!=currentHead
                ||scope.parent!=originals.parent()||scope.oldTerminal!=originals.oldTerminal()||scope.historical!=originals.precommitHead())
            throw new IOException("retained cause escaped its original private historical Root scope");
        StrictJson.require(scope.retained.equals(retainedProof)&&rederived.causeDigest().equals(retainedProof.sha256())
                &&Arrays.equals(rederived.originalProof(),read(same,retainedProof,new ArrayList<>()))
                &&rederived.precommitHead()==scope.historical,"M3 rederived a different exact historical cause/head");
        scope.requirePinned();
        qualified.set(new QualifiedRecovery(scope,rederived));
    }

    /** Same private M3 object and active original writer only; these retained DATA do not adopt a publication. */
    RetainedOriginals requireRetainedMaterial(ContinuityStorePort.Session same,PendingCause identical)throws IOException {
        HistoricalScope scope=requireRecovery(same,identical);
        return new RetainedOriginals(scope.parent,scope.oldTerminal,scope.historical,scope);
    }
    CauseOriginals requireRetainedCauseOriginals(ContinuityStorePort.Session same,PendingCause identical)throws IOException {
        return requireRecovery(same,identical).originals;
    }
    /** The original composite entry guard is distinct from its later predecessor-death Ready frame. */
    LifecycleObservationPort.Snapshot requireParentOriginalFrame(ContinuityStorePort.Session same,PendingCause identical)throws IOException {
        HistoricalScope scope=requireRecovery(same,identical);var archive=context.archive().withSession(same);
        ActionReceipt parent=ContinuityActionJournal.lookup(scope.historical.state(),scope.parent.actionId(),archive)
                .orElseThrow(()->new IOException("historical parent entry is absent"));
        var execution=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("historical parent composite guard is absent"));
        var original=RootLifecycleGuardEvidence.replay(execution.guard(),archive,same,context.originals());
        StrictJson.require(original.identity().equals(scope.parent.lifecycleBefore()),
                "original composite entry guard differs from the exact parent lifecycle origin");
        ExactRef originalKnown=natural.requireRetainedParentKnown(same,identical);
        var pins=new ArrayList<Pin>();RawJson raw=DriverSnapshotFacts.originalKnownJson(read(same,originalKnown,pins));
        var reference=DriverSnapshotFacts.observationOriginalReference(raw);
        if(reference.isPresent()&&!reference.orElseThrow().equals(original.original().facts().semanticFactsEvidence()))
            throw new IOException("the exact initial-parent Known observation is missing; Ready-frame facts cannot replace it");
        var known=DriverSnapshotFacts.decodeKnownOriginal(raw,reference.isPresent()?Optional.of(original.original().facts()):Optional.empty());
        StrictJson.require(known.stamp().driverVersion()==original.identity().subject().driverVersion()
                &&known.stamp().episodeEpoch()==original.identity().subject().episodeEpoch()
                &&Arrays.equals(known.driver().encode(),original.original().facts().driver().encode())
                &&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),raw.bytes()),
                "the complete retained Known is not the exact initial-parent Driver/version/auxiliary history");
        var result=new LifecycleObservationPort.Snapshot(original.original().actual(),scope.parent.source(),original.semantic(),known,
                original.original().originalEvidence());
        for(Pin pin:pins)same.verifyPin(pin);scope.requirePinned();return result;
    }
    private HistoricalScope requireRecovery(ContinuityStorePort.Session same,PendingCause identical)throws IOException {
        QualifiedRecovery held=qualified.get();
        if(held==null||held.cause()!=identical||held.scope().same!=same)
            throw new IOException("no same-thread private M3 retained qualification exists for this writer/cause");
        held.scope().requirePinned();return held.scope();
    }

    private final class HistoricalScope implements RootCausePort {
        private final ContinuityStorePort.Session same;private final FullSnapshot current;private final Head currentHead;
        private final SourceQualification source;private final ExactRef retained;private final Head historical;
        private final DomainBodies.BodyRef body;private final NaturalClockOriginals.Document document;
        private final ActionCommand parent;private final LifecycleObservationPort.Snapshot oldTerminal;
        private final CauseOriginals originals;private final List<Pin> pins;
        private HistoricalScope(ContinuityStorePort.Session same,FullSnapshot current,Head currentHead,SourceQualification source,
                ExactRef retained,Head historical,DomainBodies.BodyRef body,NaturalClockOriginals.Document document,
                ActionCommand parent,LifecycleObservationPort.Snapshot oldTerminal,CauseOriginals originals,List<Pin> pins) {
            this.same=same;this.current=current;this.currentHead=currentHead;this.source=source;this.retained=retained;
            this.historical=historical;this.body=body;this.document=document;this.parent=parent;this.oldTerminal=oldTerminal;
            this.originals=originals;this.pins=pins;
        }
        private RootPendingUiColdQualification owner(){return RootPendingUiColdQualification.this;}
        private void requirePinned()throws IOException {
            requireCurrentSource(same,current,source,currentHead);
            var live=currentDocument(same);var pending=live.pendingProjection().orElseThrow();
            StrictJson.require(pending.value().qualifiedCause().equals(retained)
                    &&live.capture().equals(document.capture())&&live.ready().equals(document.ready()),
                    "canonical pending causal domain changed during retained qualification");
            Head again=same.requireHistoricalHead(historical.state().sequence(),historical.digest());
            StrictJson.require(requireHistoricalDomain(same,again,natural.registration()).equals(body),
                    "retained original domain changed in the exact canonical ancestor");
            for(Pin pin:historical.documents())same.verifyPin(pin);
            for(Pin pin:pins)same.verifyPin(pin);
        }
        @Override public CauseOriginals openQualified(ActionCommand actual,LifecycleObservationPort.Snapshot terminal,Head head)throws IOException {
            requireArguments(actual,terminal,head);requirePinned();return originals;
        }
        @Override public byte[] readExact(ExactRef reference)throws IOException {
            context.writer().requireSession(same);
            StrictJson.require(same.head().digest().equals(currentHead.digest()),"private historical read escaped its original current writer head");
            if(pins.stream().noneMatch(pin->pin.reference().equals(reference)))
                throw new IOException("historical cause tried to read outside its qualified finite original bundle");
            return read(same,reference,new ArrayList<>());
        }
        @Override public void requireCurrent(CauseOriginals actual,ActionCommand command,LifecycleObservationPort.Snapshot terminal,Head head)throws IOException {
            if(actual!=originals)throw new IOException("historical cause originals escaped their private issuer");
            requireArguments(command,terminal,head);requirePinned();
        }
        private void requireArguments(ActionCommand command,LifecycleObservationPort.Snapshot terminal,Head head)throws IOException {
            if(command!=parent||terminal!=oldTerminal||head!=historical)
                throw new IOException("historical Root port accepts only its actual retained parent/old snapshot/head");
        }
    }

    private void requireCurrentSource(ContinuityStorePort.Session same,FullSnapshot current,SourceQualification source,Head expected)throws IOException {
        context.writer().requireSession(same);source.assertCurrent(same);
        StrictJson.require(same.head().digest().equals(expected.digest())&&!expected.snapshotNeedsRecovery()&&expected.indexRepairs().isEmpty(),
                "cold qualification must retain the exact clean actual writer head");
        var actual=current.actual().session();
        StrictJson.require(actual.machineId().equals(context.game().machineId())&&actual.game().equals(context.game().generation())
                &&actual.sessionId().equals(context.game().sessionId())&&current.facts().source().equals(context.source()),
                "retained qualification crossed the currently owned physical Game/source");
        var held=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual current Managed transport snapshot is absent"));
        StrictJson.require(held.session().equals(actual)&&Arrays.equals(held.originalPacket(),current.actual().originalPacket()),
                "cold qualification did not receive the actual Managed transport's current original packet");
        context.adopted().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw new IOException("actual canonical Driver is unavailable");
            StrictJson.require(known.stamp().driverVersion()==current.facts().driverVersion()
                    &&known.stamp().episodeEpoch()==current.facts().episodeEpoch()
                    &&Arrays.equals(known.driver().encode(),current.facts().driver().encode()),
                    "cold current frame differs from the real canonical Driver/version");return null;
        });
        source.assertCurrent(same);
    }
    private NaturalClockOriginals.Document currentDocument(ContinuityStorePort.Session same)throws IOException {
        var domain=same.readDomain(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS);
        if(!(domain instanceof DomainBodies.Available actual))throw new IOException("actual canonical natural domain unavailable");
        StrictJson.require(actual.reference().contractSchema().equals(natural.registration().contractSchema())
                &&actual.reference().producerSources().equals(natural.registration().producerSources()),"natural domain actual registration/source closure changed");
        return NaturalClockOriginals.decode(actual.canonicalBody());
    }
    /** Read-only validated ancestor body; neither this DATA nor Head constructs a private cause. */
    static DomainBodies.BodyRef requireHistoricalDomain(ContinuityStorePort.Session same,Head actual,
            DomainBodies.Registration registration)throws IOException {
        StrictJson.require(!actual.snapshotNeedsRecovery()&&actual.indexRepairs().isEmpty(),"historical writer proof needs unresolved repair");
        DomainBodies.BodyRef body=DomainBodies.reference(actual.state(),registration.slot())
                .orElseThrow(()->new IOException("actual ancestor lacks the registered natural domain"));
        StrictJson.require(body.contractSchema().equals(registration.contractSchema())
                &&body.producerSources().equals(registration.producerSources()),"historical domain contract/source closure differs");
        for(Pin pin:actual.documents())same.verifyPin(pin);
        Pin payload=same.capturePin(body.payload(),registration.maximumBodyBytes());
        StrictJson.require(payload.identity().equals(body.identity()),"historical domain file identity changed");
        same.readPinned(payload,registration.maximumBodyBytes());
        return body;
    }
    private static byte[] read(ContinuityStorePort.Session same,ExactRef ref,List<Pin> pins)throws IOException {
        StrictJson.require(ref.bytes()>0&&ref.bytes()<=WriterContracts.MAX_PIN_BYTES,"retained original exceeds its actual finite archive lane");
        Pin pin=same.capturePin(ref,Math.toIntExact(ref.bytes()));byte[] bytes=same.readPinned(pin,Math.toIntExact(ref.bytes()));
        same.verifyPin(pin);pins.add(pin);return bytes;
    }
    private static void requireOldTerminal(PendingNaturalCauseProof.Document proof,NaturalClockOriginals.Document document,
            ActionCommand parent,LifecycleObservationPort.Snapshot terminal,RootLifecycleGuardEvidence.Replay replay,
            byte[] driver,byte[] semantic) {
        var capture=document.capture();var ready=document.ready().orElseThrow();
        StrictJson.require(proof.actualPrecommitSnapshot().equals(terminal.originalEvidence())
                &&ready.finalNativePacket().equals(replay.original().originalEvidence())
                &&Arrays.equals(driver,terminal.facts().driver().encode())&&Arrays.equals(semantic,DriverJson.encode(terminal.semantic()))
                &&terminal.facts().stamp().driverVersion()==proof.driverVersion()
                &&terminal.facts().stamp().episodeEpoch()==proof.episodeEpoch()
                &&terminal.facts().stamp().episodeRunId().equals(proof.oldEpisodeRunId())
                &&terminal.facts().driver().session().actorId().intValueExact()==proof.predecessorCharacterId()
                &&parent.lifecycleBefore().sameGuardFrame(replay.identity())&&parent.source().equals(capture.source())
                &&capture.predecessorFrame().actorCharacterId()==proof.predecessorCharacterId()
                &&capture.rootResult().equals(proof.predecessorRoot())&&capture.machineId().equals(proof.machineId()),
                "complete retained old Driver/guard/SEM differs from the canonical cause ancestor");
    }
}
