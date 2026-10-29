package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.advance.LifeAdvanceEvidence;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One concrete runtime adapter shared by ordinary/native reads, readiness, public get and resource. */
public final class DriverCapabilityRuntime implements PlanningReadCoordinator.KnownReadObserver,NativeReadinessCollector.CapabilitiesPort {
    @FunctionalInterface public interface RetreatDomainSource {
        ExactRef current(ContinuityStorePort.Session original) throws IOException;
    }
    private final DriverStateAssembler authority;
    private final ActionPorts.OutcomeArchive archive;
    private final Supplier<ContinuityStorePort.Session> originalSession;
    private final ExecutableStepBindings bindings;
    private final CapabilityFileProbe files;
    private final RetreatDomainSource retreat;
    private enum State { ACTIVE, NEXT_CANDIDATE, INVALIDATED }
    @FunctionalInterface public interface CurrentOptions { java.util.Set<OperationKey> issue(Complete actual,java.util.Set<String> originalNativeCapabilities); }
    private volatile State state;
    private CurrentOptions currentOptions;
    private final DriverStateAssembler.CapabilityObservation observation;
    private DriverStateAssembler.NextCapabilityTransfer nextTransfer;
    private DriverCapabilityRuntime previousRuntime;
    private DriverReadHistoryPublisher readHistory;
    private org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Source windowAttempts;
    private record PlanningPorts(CheckpointFiles files,ActionPorts.RecordedEvidenceVerifier evidence,LifeAdvanceEvidence.BoundFrameVerifier lifeFrames) {
        private PlanningPorts { Objects.requireNonNull(files);Objects.requireNonNull(evidence);Objects.requireNonNull(lifeFrames); }
    }
    private PlanningPorts planning;
    private volatile boolean planningInitialized;
    public enum NativeCampaignConstructor { FRESH_FIXTURE, SAVED }
    /** Original constructor facts only. This public DATA record cannot mint the private live capture. */
    public record NativeCampaignConstructorFacts(NativeCampaignConstructor constructor,
            org.xar.ck3.control.contracts.GameGeneration game,String sessionId,org.xar.ck3.control.g2.common.G2Source source,
            ExactRef policySource,ExactRef environmentSource,java.util.List<ExactRef> sourceClosure,String headDigest) {
        public NativeCampaignConstructorFacts {
            Objects.requireNonNull(constructor);Objects.requireNonNull(game);StrictJson.text(sessionId);Objects.requireNonNull(source);
            Objects.requireNonNull(policySource);Objects.requireNonNull(environmentSource);sourceClosure=java.util.List.copyOf(sourceClosure);
            StrictJson.require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}")&&sourceClosure.size()<=DriverCapabilityStateProducer.MAX_PUBLIC_PLANNING_SOURCE_REFS&&sourceClosure.stream().distinct().count()==sourceClosure.size()
                    &&sourceClosure.containsAll(java.util.List.of(policySource,environmentSource,source.sourceRef()))
                    &&policySource.bytes()>0&&environmentSource.bytes()>0&&source.sourceRef().bytes()>0
                    &&sourceClosure.stream().allMatch(ref->ref.bytes()>=0),"actual constructor policy/environment/Native source closure required");
        }
    }
    /** Actual private Stage/Frozen issuer. Owner/current checks retain every original full native witness
     * before and after use, including zero-byte and large physical evidence. No APP dependency points back to LS. */
    public interface PublicPlanningLifecycleSource {
        java.util.List<ExactRef> sources();
        void requireOwner(ContinuityStorePort.Session same,DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive actualArchive,
                ExecutableStepBindings actualBindings)throws IOException;
        NativeCampaignConstructorFacts capture(ContinuityStorePort.Session same,DriverObservationAssembler.FullSnapshot full,Known actual)throws IOException;
        void requireCurrent(ContinuityStorePort.Session same,DriverObservationAssembler.FullSnapshot full,Known actual,
                NativeCampaignConstructorFacts identical)throws IOException;
    }
    private volatile LifecycleBinding publicPlanningLifecycle;
    public interface PublicPlanningTerminalRootReadScope {
        void requireCurrent(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> unavailable,PlanningReadCoordinator.FailedReadAttempt original,
                ActionPorts.OutcomeArchive archive)throws IOException;
    }
    public interface PublicPlanningTerminalRootReadSource {
        java.util.List<ExactRef> sources();
        void requireOwner(ContinuityStorePort.Session same,DriverStateAssembler authority,ActionPorts.OutcomeArchive archive,
                ExecutableStepBindings bindings)throws IOException;
        Optional<PublicPlanningTerminalRootReadScope> current(ContinuityStorePort.Session same)throws IOException;
    }
    private record TerminalRootReadBinding(PublicPlanningTerminalRootReadSource source,java.util.List<ExactRef> sources){ }
    private volatile TerminalRootReadBinding publicTerminalRootRead;
    public synchronized void bindPublicPlanningTerminalRootReadSource(PublicPlanningTerminalRootReadSource actual)throws IOException {
        requireActive();Objects.requireNonNull(actual);var same=Objects.requireNonNull(originalSession.get());
        actual.requireOwner(same,authority,archive,bindings);var refs=java.util.List.copyOf(actual.sources());
        StrictJson.require(!refs.isEmpty()&&refs.size()<=DriverCapabilityStateProducer.MAX_PUBLIC_PLANNING_SOURCE_REFS&&refs.stream().distinct().count()==refs.size()
                &&refs.stream().allMatch(ref->ref.bytes()>0),"bounded actual terminal ROOT read source required");
        for(var ref:refs)same.verifyPin(same.capturePin(ref,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES));
        StrictJson.require(publicTerminalRootRead==null||publicTerminalRootRead.source()==actual&&publicTerminalRootRead.sources().equals(refs),
                "terminal ROOT read belongs to another actual installed source");
        if(publicTerminalRootRead==null)publicTerminalRootRead=new TerminalRootReadBinding(actual,refs);
    }
    public synchronized void bindPublicPlanningLifecycleSource(PublicPlanningLifecycleSource actual)throws IOException {
        requireActive();Objects.requireNonNull(actual);var same=Objects.requireNonNull(originalSession.get());
        actual.requireOwner(same,authority,archive,bindings);var refs=java.util.List.copyOf(actual.sources());
        StrictJson.require(!refs.isEmpty()&&refs.size()<=DriverCapabilityStateProducer.MAX_PUBLIC_PLANNING_SOURCE_REFS&&refs.stream().distinct().count()==refs.size()
                &&refs.stream().allMatch(ref->ref.bytes()>=0),"bounded actual private constructor source closure required");
        // The actual source owns full native witnesses, including empty originals and saves larger than transactional Pins.
        actual.requireOwner(same,authority,archive,bindings);
        StrictJson.require(refs.equals(actual.sources()),"actual constructor physical source closure changed during binding");
        StrictJson.require(publicPlanningLifecycle==null||publicPlanningLifecycle.source==actual&&publicPlanningLifecycle.sources.equals(refs),
                "private constructor source belongs to another actual installed issuer");
        if(publicPlanningLifecycle==null)publicPlanningLifecycle=new LifecycleBinding(actual,refs);
    }
    public PublicPlanningLifecycleSource actualPublicPlanningLifecycleSource(ContinuityStorePort.Session same)throws IOException {
        requireActive();StrictJson.require(originalSession.get()==same,"constructor source read crossed the actual borrowed writer");
        var binding=Objects.requireNonNull(publicPlanningLifecycle,"actual private constructor source is not installed");
        StrictJson.require(binding.sources.equals(binding.source.sources()),"actual constructor source closure changed");
        binding.source.requireOwner(same,authority,archive,bindings);
        StrictJson.require(binding.sources.equals(binding.source.sources()),"actual constructor physical source closure changed during validation");
        return binding.source;
    }
    private final class LifecycleBinding {
        private final PublicPlanningLifecycleSource source;private final java.util.List<ExactRef> sources;
        private LifecycleBinding(PublicPlanningLifecycleSource source,java.util.List<ExactRef> sources){this.source=source;this.sources=sources;}
    }
    /** Private construction binds source-owned facts to the identical actual raw frame, writer and Driver. */
    final class LifecycleCapture implements DriverCapabilityStateProducer.SourceLifecycleCapture {
        private final LifecycleBinding binding;private final ContinuityStorePort.Session same;
        private final DriverObservationAssembler.FullSnapshot full;private final Known known;private final NativeCampaignConstructorFacts facts;
        private LifecycleCapture(LifecycleBinding binding,ContinuityStorePort.Session same,DriverObservationAssembler.FullSnapshot full,
                Known known,NativeCampaignConstructorFacts facts){this.binding=binding;this.same=same;this.full=full;this.known=known;this.facts=facts;}
        @Override public void requireCurrent(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,DriverObservationAssembler.FullSnapshot actual,Known current)throws IOException {
            requireActive();scope.requireInputs(actual,current);
            StrictJson.require(actual==full&&current==known&&same==originalSession.get()&&publicPlanningLifecycle==binding
                    &&binding.sources.equals(binding.source.sources())&&facts.sourceClosure().equals(binding.sources)
                    &&same.head().digest().equals(facts.headDigest())&&facts.game().equals(full.actual().session().game())
                    &&facts.game().equals(known.stamp().game())&&facts.sessionId().equals(full.actual().session().sessionId())
                    &&facts.source().equals(full.facts().source())&&full.facts().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                    &&new OpportunityJson.Text("native_campaign").equals(full.semantic().get("episode_projection")),
                    "private constructor DATA left its actual source/writer/Native profile/Driver objects");
            binding.source.requireOwner(same,authority,archive,bindings);binding.source.requireCurrent(same,full,known,facts);
            // Metadata Pins remain in the raw scope. Physical constructor originals are revalidated by their actual source owner.
            StrictJson.require(binding.sources.equals(binding.source.sources()),"actual constructor physical source closure changed during capture");
            scope.requireInputs(actual,current);
        }
        @Override public DriverCapabilityStateProducer.PublicTerminalLifecycleData data(){
            var semantic=full.semantic();boolean present=semantic.members().containsKey("succession_lifecycle");
            OpportunityJson.Value declared=present?semantic.get("succession_lifecycle"):OpportunityJson.Nil.INSTANCE;
            var presence=!present?DriverCapabilityStateProducer.DeclaredLifecyclePresence.MISSING:
                    declared==OpportunityJson.Nil.INSTANCE?DriverCapabilityStateProducer.DeclaredLifecyclePresence.NULL:DriverCapabilityStateProducer.DeclaredLifecyclePresence.VALUE;
            var mode=switch(facts.constructor()){
                case FRESH_FIXTURE->DriverCapabilityStateProducer.PublicTerminalLifecycleMode.NATIVE_CAMPAIGN_FIXTURE_NULL_CONSTRUCTOR;
                case SAVED->DriverCapabilityStateProducer.PublicTerminalLifecycleMode.NATIVE_CAMPAIGN_SAVED_NULL_CONSTRUCTOR;
            };
            return new DriverCapabilityStateProducer.PublicTerminalLifecycleData(mode,presence,declared,
                    DriverCapabilityStateProducer.privateNullConstructorLifecycle(),Optional.of(facts.policySource()),Optional.of(facts.environmentSource()),
                    Optional.of(facts.source().sourceRef()),facts.sourceClosure());
        }
    }
    private Optional<DriverCapabilityStateProducer.SourceLifecycleCapture> capturePublicLifecycle(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
            DriverObservationAssembler.FullSnapshot full,Known known)throws IOException {
        var binding=publicPlanningLifecycle;if(binding==null)return Optional.empty();
        var same=Objects.requireNonNull(originalSession.get());binding.source.requireOwner(same,authority,archive,bindings);
        var facts=Objects.requireNonNull(binding.source.capture(same,full,known));
        var captured=new LifecycleCapture(binding,same,full,known,facts);captured.requireCurrent(scope,full,known);return Optional.of(captured);
    }
    private volatile org.xar.ck3.control.application.planning.ReadonlyPlanningRetry.FailureSink publicPlanningRetry;
    /** The sole public PLAN wrapper owns this private classifier; ordinary observers keep their original path. */
    public synchronized void bindPublicPlanningRetry(org.xar.ck3.control.application.planning.ReadonlyPlanningRetry.FailureSink actual){
        StrictJson.require(actual==org.xar.ck3.control.application.planning.ReadonlyPlanningRetry.sink(),"actual public planning retry singleton required");
        StrictJson.require(publicPlanningRetry==null||publicPlanningRetry==actual,"another public planning retry classifier is already bound");
        publicPlanningRetry=actual;
    }
    private NativeObservationPort.ObservedFrame preparedNextPacket;
    private Complete preparedNextFrame;
    public DriverCapabilityRuntime(DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive actualArchive,
            Supplier<ContinuityStorePort.Session> currentOriginalSession,ExecutableStepBindings actualBindings,CapabilityFileProbe actualFiles,
            RetreatDomainSource actualRetreatDomain) {
        this(actualAuthority,actualArchive,currentOriginalSession,actualBindings,actualFiles,actualRetreatDomain,true);
    }
    private DriverCapabilityRuntime(DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive actualArchive,
            Supplier<ContinuityStorePort.Session> currentOriginalSession,ExecutableStepBindings actualBindings,CapabilityFileProbe actualFiles,
            RetreatDomainSource actualRetreatDomain,boolean install) {
        authority=Objects.requireNonNull(actualAuthority);archive=Objects.requireNonNull(actualArchive);
        originalSession=Objects.requireNonNull(currentOriginalSession);bindings=Objects.requireNonNull(actualBindings);files=Objects.requireNonNull(actualFiles);
        retreat=Objects.requireNonNull(actualRetreatDomain);
        state=install?State.ACTIVE:State.NEXT_CANDIDATE;
        observation=(actual,known) -> {
            requireUsable();
            var borrowed=Objects.requireNonNull(originalSession.get());ActionPorts.OutcomeArchive originals=archive.withSession(borrowed);
            ExactRef nativeSource=originals.preserveNativeFrame(actual);
            var projected=new DriverObservationAssembler().assemble(actual,known.observation().orElseThrow(),nativeSource);
            // Death/changed/missing-player continuation owns a separate qualified LifecycleIdentity. Old capability inputs stay factual and stale.
            if(!(projected instanceof Complete frame))return Optional.empty();
            // The pending canonical UI source owns its mutations. Physical observations cannot refresh ordinary planning inputs under that gate.
            if(known.auxiliary().members().containsKey(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY)
                    &&org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.decode(DriverJson.encode(known.auxiliary().get(
                            org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.AUXILIARY_KEY))).blocksOrdinaryActionsAndSave())return Optional.empty();
            if(!OpportunityJson.bool(OpportunityJson.object(frame.semantic().get("played_character"),"played_character").get("alive"),"alive")
                    ||frame.semantic().get("one_life_terminal_reason")!=OpportunityJson.Nil.INSTANCE)return Optional.empty();
            ExactRef domain;
            try { domain=retreat.current(borrowed); }
            catch(IOException failure) { throw new UncheckedIOException("actual sole retreat domain state unavailable",failure); }
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts;
            try { attempts=windowAttempts().current(borrowed,frame); }
            catch(IOException failure) { throw new UncheckedIOException("actual fixed-window query attempts unavailable",failure); }
            var token=org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatTokens.capabilityToken(
                    org.xar.ck3.control.application.planning.military.ActiveRetreatState.decode(DriverJson.object(originals.loadMaterial(domain).bytes(),DriverJson.MAX_NATIVE_BYTES)));
            Optional<DriverPersistentPlanningState.Publication> persistent=Optional.empty();
            if(planningInitialized)try {
                persistent=authority.withFrozenFacts(borrowed,frozen -> capturePersistent(borrowed,frame,known,frozen.actions(),originals));
            }catch(IOException failure){throw new UncheckedIOException("actual persistent planning source projection unavailable",failure);}
            Optional<ExactRef> drop=readHistory==null?Optional.empty():readHistory.armyCoreUnavailable(known.auxiliary());
            return DriverCapabilityStateProducer.observeCurrentFrame(frame,known,persistent,token,domain,attempts,drop,originals);
        };
        if(install) { authority.bindHistoryArchive(archive,currentOriginalSession);authority.bindCapabilityObservation(observation); }
    }
    public synchronized void bindReadHistoryPublisher(DriverReadHistoryPublisher actual) {
        StrictJson.require(readHistory==null,"one actual per-Game read-history publisher required");
        Objects.requireNonNull(actual).requireOwner(authority,archive,actual.catalog());
        actual.bindArmyCorePublication(authority,archive,originalSession);readHistory=actual;
    }
    public synchronized DriverReadHistoryPublisher readHistoryPublisher() {
        StrictJson.require(readHistory!=null,"actual per-Game read-history publisher is not installed");return readHistory;
    }
    public synchronized void bindWindowAttempts(org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Source actual) {
        StrictJson.require(windowAttempts==null,"one actual fixed-window attempt store required");windowAttempts=Objects.requireNonNull(actual);
    }
    private synchronized org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Source windowAttempts() {
        StrictJson.require(windowAttempts!=null,"actual fixed-window query-attempt source is not installed");return windowAttempts;
    }
    public synchronized void bindCurrentOptions(CurrentOptions actual) {
        requireUsable();StrictJson.require(currentOptions==null,"one actual current event-option inventory producer required");currentOptions=Objects.requireNonNull(actual);
    }
    private synchronized CurrentOptions currentOptions() {
        requireUsable();StrictJson.require(currentOptions!=null,"actual current event-option inventory producer is not installed");return currentOptions;
    }
    private synchronized void requireUsable() { StrictJson.require(state!=State.INVALIDATED,"old per-Game capability runtime was invalidated by actual NEXT activation"); }
    private synchronized void requireActive() { StrictJson.require(state==State.ACTIVE,"formal reads require the active per-Game capability runtime"); }
    public synchronized void bindPlanningPorts(CheckpointFiles actualFiles,ActionPorts.RecordedEvidenceVerifier evidence,
            LifeAdvanceEvidence.BoundFrameVerifier lifeFrames) {
        requireUsable();StrictJson.require(planning==null,"one actual persistent planning producer dependency set required");
        planning=new PlanningPorts(actualFiles,evidence,lifeFrames);
    }
    private synchronized PlanningPorts planningPorts(){StrictJson.require(planning!=null,"actual persistent planning dependencies are not installed");return planning;}
    /** Root calls after every private initial domain import, before ordinary planning or first SAVE. */
    public void initializePlanning(ContinuityStorePort.Session same,Complete actual) throws IOException {
        requireUsable();publishPersistent(same,actual);synchronized(this){planningInitialized=true;}
    }
    /** Also used after the genuine terminal cross-run publisher; never fabricates a strategy file. */
    public void refreshCanonicalStrategy(ContinuityStorePort.Session same,Complete actual) throws IOException {
        requireUsable();StrictJson.require(planningInitialized,"persistent planning has not completed its actual initial capture");publishPersistent(same,actual);
    }
    private record TerminalCapture(DriverObservationAssembler.FullSnapshot full,Known known,LifecycleIdentity terminal,
            java.util.List<org.xar.ck3.control.continuity.writer.WriterContracts.Pin> pins,String head,Instant until) { }
    /** Source-bound terminal data refresh, after canonical score publication and outside every physical read scope. */
    public void refreshTerminalCanonicalStrategy(ContinuityStorePort.Session same,
            org.xar.ck3.control.service.root.RootLifecycleAuthority physical,
            org.xar.ck3.control.application.session.SessionPorts.SessionIdentity expected,Instant deadline) throws IOException {
        requireActive();Objects.requireNonNull(physical);Objects.requireNonNull(expected);Objects.requireNonNull(deadline);
        authority.requireOutsideObservationScope(same);physical.requireOutsideObservationScope(same);
        TerminalCapture captured=physical.withSnapshot(same,deadline,lease->{
            var full=lease.fullSnapshot();var actual=full.actual();
            StrictJson.require(expected.machineId().equals(actual.session().machineId())&&expected.game().equals(actual.session().game())
                    &&expected.sessionId().equals(actual.session().sessionId())&&lease.ordinary().isEmpty(),"terminal strategy refresh crossed its actual physical owner/phase");
            var terminal=lease.terminalIdentity().orElseThrow(()->new IOException("actual source-bound terminal phase is unavailable"));
            var refs=new java.util.LinkedHashSet<ExactRef>(terminal.supportingEvidence());
            refs.add(terminal.nativeEvidence());refs.add(lease.originalHello());refs.add(lease.originalHeartbeat());refs.add(lease.originalSemantic());refs.add(full.facts().source().sourceRef());
            var pins=new java.util.ArrayList<org.xar.ck3.control.continuity.writer.WriterContracts.Pin>();
            for(ExactRef ref:refs)pins.add(same.capturePin(ref,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES));
            lease.assertCurrent(same);return new TerminalCapture(full,lease.factsKnown(),terminal,java.util.List.copyOf(pins),same.head().digest(),lease.validUntil());
        });
        physical.requireOutsideObservationScope(same);authority.requireOutsideObservationScope(same);
        StrictJson.require(Instant.now().isBefore(deadline)&&Instant.now().isBefore(captured.until())&&captured.head().equals(same.head().digest()),"terminal strategy capture expired or writer changed before publication");
        for(var pin:captured.pins())same.verifyPin(pin);
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof Known,"terminal strategy lost the actual full Driver");Known current=(Known)frozen.state();
            StrictJson.require(current.stamp().equals(captured.known().stamp())&&java.util.Arrays.equals(current.driver().encode(),captured.known().driver().encode())
                    &&current.auxiliary().equals(captured.known().auxiliary())&&current.observation().equals(captured.known().observation()),"terminal strategy capture left its exact Driver/native/auxiliary version");
            var canonical=DriverPersistentPlanningState.crossRun(same,current,originals);
            if(canonical.auxiliary().equals(current.auxiliary())&&current.auxiliary().get(DriverRuntimeCapabilities.AUXILIARY_KEY)==OpportunityJson.Nil.INSTANCE)return null;
            var publication=DriverCapabilityStateProducer.observeTerminalStrategy(captured.full(),captured.terminal(),current,canonical,originals);
            authority.publishCapabilityInputs(same,current.stamp(),publication.expectedAuxiliarySha256(),publication);return null;
        });
    }
    private Optional<DriverPersistentPlanningState.Publication> capturePersistent(ContinuityStorePort.Session same,Complete actual,Known current,
            ActionJournal.Snapshot canonical,ActionPorts.OutcomeArchive originals) throws IOException {
        PlanningPorts ports=planningPorts();
        return DriverPersistentPlanningState.capture(same,actual,current,ports.files(),canonical.actions(),ports.evidence(),ports.lifeFrames(),originals);
    }
    private void publishPersistent(ContinuityStorePort.Session same,Complete actual) throws IOException {
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        authority.withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof Known,"persistent planning requires the actual complete Driver");Known current=(Known)frozen.state();
            var captured=capturePersistent(same,actual,current,frozen.actions(),originals);
            if(captured.isPresent()) {
                var publication=DriverCapabilityStateProducer.observePersistentPlanning(actual,current,captured.orElseThrow(),originals);
                if(state==State.NEXT_CANDIDATE)authority.publishNextCapabilityInputs(same,nextTransfer,publication);
                else authority.publishCapabilityInputs(same,current.stamp(),publication.expectedAuxiliarySha256(),publication);
            }
            return null;
        });
    }

    /** Stage before the bootstrap's first new raw observation. This does not seize the installed old callback. */
    public DriverCapabilityRuntime nextCandidate(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption actual,
            ActionPorts.OutcomeArchive newArchive,Supplier<ContinuityStorePort.Session> newSession,
            ExecutableStepBindings newBindings,CapabilityFileProbe newFiles,RetreatDomainSource newRetreat) throws IOException {
        requireActive();StrictJson.require(!readHistoryPublisher().hasPending(same),"NEXT cannot abandon actual pending public read rows");
        var proof=authority.prepareNextCapabilityTransfer(same,actual,observation,archive,originalSession);
        var candidate=new DriverCapabilityRuntime(authority,newArchive,newSession,newBindings,newFiles,newRetreat,false);
        candidate.nextTransfer=proof;candidate.previousRuntime=this;return candidate;
    }
    /** Exact opaque adoption identity only; this does not grant planning or native readiness. */
    public void requireNextCandidate(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption actual,DriverStateAssembler expectedAuthority) throws IOException {
        StrictJson.require(state==State.NEXT_CANDIDATE&&nextTransfer!=null,"actual staged NEXT runtime required");
        authority.requireNextCandidate(same,nextTransfer,actual,expectedAuthority);
    }
    /** Runs candidate collector/SAVE/SEM work on this exact borrowed writer without installing it as the active host. */
    public <T>T withCandidateScope(ContinuityStorePort.Session same,DriverStateAssembler.CandidateWork<T> work) throws IOException {
        StrictJson.require(state==State.NEXT_CANDIDATE&&nextTransfer!=null,"candidate observation requires an actual staged NEXT runtime");
        return authority.withCandidateScope(same,nextTransfer,observation,archive,originalSession,work);
    }
    /** A genuinely later packet for pre-BEGIN or post-SAVE SEM, never a new timestamp on the retained load packet. */
    public <T>T withCandidateObservation(ContinuityStorePort.Session same,NativeObservationPort.ObservedFrame actual,
            DriverStateAssembler.ObservationWork<T> work) throws IOException {
        return withCandidateScope(same,()->authority.withFrozenObservation(actual,same,work));
    }
    /** Actual new packet and sole producer, with the old hook excluded; only private typed cache publication may follow. */
    public synchronized Complete prepareNextObservation(ContinuityStorePort.Session same,NativeObservationPort.ObservedFrame actual) throws IOException {
        StrictJson.require(state==State.NEXT_CANDIDATE&&nextTransfer!=null,"actual staged NEXT candidate required");authority.requireNextPacket(same,nextTransfer,actual);
        Objects.requireNonNull(actual);
        if(preparedNextPacket!=null)StrictJson.require(preparedNextPacket.session().equals(actual.session())
                &&preparedNextPacket.snapshotId().equals(actual.snapshotId())&&preparedNextPacket.nativeRevision().equals(actual.nativeRevision())
                &&preparedNextPacket.observedAt().equals(actual.observedAt())&&preparedNextPacket.state().equals(actual.state())
                &&java.util.Arrays.equals(preparedNextPacket.originalPacket(),actual.originalPacket()),"NEXT retry changed its first actual native packet");
        else preparedNextPacket=actual;
        if(preparedNextFrame!=null)return preparedNextFrame;
        var publication=authority.withFrozenRawObservation(actual,same,frozen -> observation.observe(actual,frozen.state()));
        if(publication.isPresent()) {
            var value=publication.orElseThrow();authority.publishNextCapabilityInputs(same,nextTransfer,value);
        }
        preparedNextFrame=authority.withFrozenRawObservation(actual,same,frozen -> {
            ExactRef original=archive.withSession(same).preserveNativeFrame(actual);return complete(actual,frozen.state(),original);
        });
        return preparedNextFrame;
    }
    /** Root calls this only in the actual qualified host-CAS transaction; this transfers ownership, never readiness. */
    public void activateNext(ContinuityStorePort.Session same,DriverCapabilityRuntime old,
            org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.NextBaselineBinding baseline) throws IOException {
        StrictJson.require(state==State.NEXT_CANDIDATE&&previousRuntime==old&&nextTransfer!=null,"NEXT candidate belongs to another runtime");
        old.requireActive();StrictJson.require(!old.readHistoryPublisher().hasPending(same),"NEXT old runtime acquired pending reads");
        readHistoryPublisher();windowAttempts();currentOptions();planningPorts();StrictJson.require(planningInitialized,"NEXT persistent planning has not been initialized");
        authority.activateNextCapabilityTransfer(same,nextTransfer,baseline,observation,archive,originalSession);
        synchronized(old) { old.state=State.INVALIDATED; }
        synchronized(this) { state=State.ACTIVE; }
    }
    @Override public void afterUnavailable(ContinuityStorePort.Session borrowed,ReadContract<?> identicalInstalled,
            PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual) {
        requireActive();if(!(request.origin() instanceof CommandOrigin.Gameplay))return;
        try { windowAttempts().recordUnavailable(borrowed,identicalInstalled,request,actual);refreshWindowAttempts(borrowed); }
        catch(IOException failure) { throw new UncheckedIOException("original failed query retained; fixed-window attempt publication unavailable",failure); }
    }
    @Override public void afterUnavailable(ContinuityStorePort.Session borrowed,ReadContract<?> identicalInstalled,
            PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual,
            Optional<PlanningReadCoordinator.FailedReadAttempt> original) {
        requireActive();
        var terminalSource=publicTerminalRootRead;var terminalSink=publicPlanningRetry;
        if(request.origin() instanceof CommandOrigin.LifecycleTerminal
                &&request.operation().value().equals("query-campaign-root-context-v1")
                &&identicalInstalled.guardMode()==ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION
                &&terminalSink!=null&&terminalSink.active()&&terminalSource!=null&&original.isPresent())try {
            StrictJson.require(originalSession.get()==borrowed&&terminalSource.sources().equals(terminalSource.source().sources()),
                    "terminal ROOT failure crossed its actual writer/source binding");
            terminalSource.source().requireOwner(borrowed,authority,archive,bindings);
            var current=terminalSource.source().current(borrowed);
            if(current.isPresent()){
                var proof=original.orElseThrow();var originals=archive.withSession(borrowed);
                proof.requireOriginal(borrowed,identicalInstalled,request,actual,originals);
                for(var ref:terminalSource.sources())borrowed.verifyPin(borrowed.capturePin(ref,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES));
                current.orElseThrow().requireCurrent(borrowed,identicalInstalled,request,actual,proof,originals);
                terminalSink.failed(borrowed,identicalInstalled,request,actual,proof,originals);
                current.orElseThrow().requireCurrent(borrowed,identicalInstalled,request,actual,proof,originals);
            }
            return;
        }catch(IOException failure){throw new UncheckedIOException("actual terminal ROOT failed-read source is unavailable",failure);}
        if(!(request.origin() instanceof CommandOrigin.Gameplay))return;
        if(request.operation().value().equals("query-army-strengths-v1"))try{
            StrictJson.require(originalSession.get()==borrowed,"Army writer drift");var originals=archive.withSession(borrowed);
            if(original.isPresent())original.orElseThrow().requireOriginal(borrowed,identicalInstalled,request,actual,originals);
            authority.withFrozenFacts(borrowed,f->{if(f.state() instanceof DriverSnapshotFacts.Known k)
                DriverSemanticReadState.armyCoreUnavailableSource(k.auxiliary(),request,originals).ifPresent(readHistoryPublisher()::armyCoreUnavailable);return null;});
        }catch(IOException e){throw new UncheckedIOException(e);}
        try {
            var sink=publicPlanningRetry;var callback=authority.currentPlanningReadCallback(borrowed);
            if(sink!=null&&sink.active()&&callback.isPresent()) {
                // An absent Attempt proves nothing. This branch preserves the original Unavailable without a cache/row publication.
                if(original.isPresent()) {
                    var proof=original.orElseThrow();var originals=archive.withSession(borrowed);
                    callback.orElseThrow().requireCurrent(borrowed);
                    proof.requireOriginal(borrowed,identicalInstalled,request,actual,originals);
                    sink.failed(borrowed,identicalInstalled,request,actual,proof,originals);
                    callback.orElseThrow().requireCurrent(borrowed);
                }
                return;
            }
        }catch(IOException failure){throw new UncheckedIOException("actual public planning failed-read provenance is unavailable",failure);}
        readHistoryPublisher().retainUnavailable(borrowed,identicalInstalled,request,actual,original);
        afterUnavailable(borrowed,identicalInstalled,request,actual);
    }
    @Override public void afterKnown(ContinuityStorePort.Session borrowed,ReadContract<?> identicalInstalled,PlanningReadResult.Known<?> actual) {
        requireActive();StrictJson.require(identicalInstalled.contractId().equals(actual.receipt().contractId()),"actual read observer crossed its installed contract");
        if(!(actual.receipt().request().origin() instanceof CommandOrigin.Gameplay))return;
        if(identicalInstalled.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)
            readHistoryPublisher().enqueue(borrowed,identicalInstalled,actual);
        // Core is published only after the installed Army service selects and validates its final component.
        if(actual.value() instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue)return;
        String step=actual.receipt().request().operation().value();
        boolean declaration=actual.value() instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReadCodec.Declarations;
        if(!(step.equals("query-arrange-marriage-choices") || step.equals("query-campaign-root-context-v1")||DriverSemanticReadState.supports(actual)||declaration))return;
        ActionPorts.OutcomeArchive originals=archive.withSession(borrowed);
        try {
            authority.withFrozenFacts(borrowed,frozen -> {
                StrictJson.require(frozen.state() instanceof Known,"actual current Driver owner unavailable after original read");
                Known known=(Known)frozen.state();var observed=known.observation().orElseThrow();
                ExactRef evidence=actual.receipt().after().binding().nativeEvidence();
                RawJson manifest=originals.loadMaterial(observed.semanticFactsEvidence());
                var nativeFrame=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),manifest,originals.loadNativeFrame(evidence));
                Complete frame=complete(nativeFrame,known,evidence);
                DriverCapabilityStateProducer.InitialAuxiliary publication;
                if(declaration) {
                    var declarationState=DriverPersistentPlanningState.declaration(frame,known,identicalInstalled,actual,originals);
                    if(declarationState.auxiliary().equals(known.auxiliary()))return null;
                    publication=DriverCapabilityStateProducer.observePersistentPlanning(frame,known,declarationState,originals);
                }else if(DriverSemanticReadState.supports(actual))publication=DriverCapabilityStateProducer.observeSemanticRead(frame,known,identicalInstalled,actual,windowAttempts().current(borrowed,frame),originals);
                else publication=DriverCapabilityStateProducer.observeRead(frame,known,actual,originals);
                authority.publishCapabilityInputs(borrowed,known.stamp(),publication.expectedAuxiliarySha256(),publication);return null;
            });
        } catch(IOException failure) { throw new UncheckedIOException("actual query cache publication failed after preserving the original read",failure); }
    }
    private void refreshWindowAttempts(ContinuityStorePort.Session same) throws IOException {
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        authority.withFrozenFacts(same,frozen -> {
            StrictJson.require(frozen.state() instanceof Known,"window attempt publication requires complete Driver");Known current=(Known)frozen.state();
            ExactRef nativeSource=DriverObservationEvidenceReader.reference(current.auxiliary().get("capability_observed_native_source"));
            var observed=current.observation().orElseThrow();RawJson manifest=originals.loadMaterial(observed.semanticFactsEvidence());
            var actual=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),manifest,originals.loadNativeFrame(nativeSource));
            Complete frame=complete(actual,current,nativeSource);
            var publication=DriverCapabilityStateProducer.refresh(frame,current,originals,windowAttempts().current(same,frame));
            if(publication.isPresent()){var value=publication.orElseThrow();authority.publishCapabilityInputs(same,current.stamp(),value.expectedAuxiliarySha256(),value);}
            return null;
        });
    }
    @Override public NativeReadinessCollector.ExecutableCapabilities collect(ContinuityStorePort.Session borrowed,Complete frame,
            Known known,OpportunityJson.Obj received,Instant deadline) throws IOException {
        StrictJson.require(Instant.now().isBefore(deadline),"capability projection deadline expired");
        requireUsable();
        var pending=authority.pendingChildPhysical(borrowed,frame,known);
        if(pending.isPresent()) {
            OpportunityJson.Obj diagnostics=OpportunityJson.object(received.get("diagnostics"),"actual pending diagnostics");
            OpportunityJson.Obj hello=OpportunityJson.object(diagnostics.get("hello"),"actual pending HELLO");
            StrictJson.require(OpportunityJson.integer(hello.get("pid"),"pid").equals(java.math.BigInteger.valueOf(frame.identity().game().pid()))
                    &&OpportunityJson.integer(hello.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"pending physical HELLO crossed the actual frame");
            var nativeCaps=new java.util.LinkedHashSet<String>();
            for(var value:OpportunityJson.array(hello.get("capabilities"),"capabilities"))nativeCaps.add(OpportunityJson.text(value,"capability"));
            // No executable operation is advertised. The actual physical assessment and private derived-child guard remain mandatory.
            return new NativeReadinessCollector.ExecutableCapabilities(java.util.Set.of(),java.util.Set.copyOf(nativeCaps),Optional.empty());
        }
        DynamicCapabilities.Result result=read(frame,known,borrowed,received);
        if(result instanceof DynamicCapabilities.Incomplete missing)throw new IOException("actual complete capability state unavailable: "+String.join(",",missing.reasons()));
        var snapshot=((DynamicCapabilities.Projected)result).snapshot();
        return new NativeReadinessCollector.ExecutableCapabilities(snapshot.actionSteps(),snapshot.bridgeCapabilities(),snapshot.battleSpeedReadiness());
    }
    public Optional<org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsReadValue.CoreAvailabilityInvalidation> armyCoreInvalidation(
            ContinuityStorePort.Session same,Complete frame,Known known)throws IOException {
        requireUsable();StrictJson.require(originalSession.get()==same,"Core planning writer drift");
        return authority.withFrozenFacts(same,f->{StrictJson.require(f.state()==known,"Core planning owner drift");
            return DriverSemanticReadState.coreInvalidation(frame,known,readHistoryPublisher().armyCoreUnavailable(known.auxiliary()),archive.withSession(same));});
    }
    /** Current public planning DATA before terminal/window/ordinary selection. The raw scope is
     * private and short lived. Archival input preparation never publishes Driver/cache or ledger. */
    public NativeReadinessCollector.ExecutableCapabilities collectPublicPlanningInputs(ContinuityStorePort.Session same,Complete frame,
            Known known,OpportunityJson.Obj received,Instant deadline)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(frame);Objects.requireNonNull(known);Objects.requireNonNull(received);
        requireActive();StrictJson.require(planningInitialized,"actual persistent planning inputs have not been initialized");
        StrictJson.require(originalSession.get()==same,"public planning inputs crossed the runtime's actual borrowed writer");
        var scope=authority.openReadOnlyPlanningScope(same,frame,known,deadline);
        var receivedDiagnostics=OpportunityJson.object(received.get("diagnostics"),"actual public planning diagnostics");
        var hello=OpportunityJson.object(receivedDiagnostics.get("hello"),"actual public planning HELLO");
        var frameDiagnostics=OpportunityJson.object(frame.semantic().get("diagnostics"),"actual raw frame diagnostics");
        StrictJson.require(hello.equals(OpportunityJson.object(frameDiagnostics.get("hello"),"actual raw frame HELLO")),
                "public planning capabilities did not come from this actual raw frame's HELLO source");
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        ExactRef domain=retreat.current(same);
        var token=org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatTokens.capabilityToken(
                org.xar.ck3.control.application.planning.military.ActiveRetreatState.decode(DriverJson.object(originals.loadMaterial(domain).bytes(),DriverJson.MAX_NATIVE_BYTES)));
        var attempts=windowAttempts().current(same,frame);
        var persistent=authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==known,"public planning inputs lost their identical frozen Driver");
            return capturePersistent(same,frame,known,frozen.actions(),originals);
        });
        Optional<DriverCapabilityStateProducer.PublicTerminalInputs> terminalInputs=Optional.empty();
        if(frame.identity().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)
            terminalInputs=Optional.of(capturePublicTerminalInputs(same,frame.originalProjection().orElseThrow(),known,deadline));
        var inputs=DriverCapabilityStateProducer.publicPlanningInputs(scope,frame,known,persistent,token,domain,attempts,terminalInputs,originals);
        var projected=DynamicCapabilities.projectPublicPlanning(frame,known,received,bindings,inputs,files);
        if(projected instanceof DynamicCapabilities.Incomplete missing)
            throw new IOException("actual read-only public planning capability inputs unavailable: "+String.join(",",missing.reasons()));
        scope.requireCurrent();
        StrictJson.require(domain.equals(retreat.current(same))&&attempts.equals(windowAttempts().current(same,frame)),
                "public planning domain inputs changed during the actual frozen projection");
        var snapshot=((DynamicCapabilities.Projected)projected).snapshot();
        return new NativeReadinessCollector.ExecutableCapabilities(snapshot.actionSteps(),snapshot.bridgeCapabilities(),snapshot.battleSpeedReadiness());
    }
    /** Original terminal planner's finite read-only inventory, preserving the actual changed/missing actor. */
    public NativeReadinessCollector.ExecutableCapabilities collectPublicTerminalInputs(ContinuityStorePort.Session same,
            DriverObservationAssembler.FullSnapshot full,Known known,OpportunityJson.Obj received,Instant deadline)throws IOException {
        var inputs=capturePublicTerminalInputs(same,full,known,deadline);
        var scope=authority.openReadOnlyTerminalPlanningScope(same,full,known,deadline);
        var inventory=DynamicCapabilities.projectPublicTerminal(full,known,received,bindings,inputs,scope,files);
        scope.requireCurrent();inputs.requireScope(full,known);
        return new NativeReadinessCollector.ExecutableCapabilities(inventory.steps(),inventory.nativeCapabilities(),Optional.empty());
    }
    /** Actual input originals for the same private terminal pipeline and its genuine regression caller. */
    public DriverCapabilityStateProducer.PublicTerminalInputs capturePublicTerminalInputs(ContinuityStorePort.Session same,
            DriverObservationAssembler.FullSnapshot full,Known known,Instant deadline)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(full);Objects.requireNonNull(known);
        requireActive();StrictJson.require(planningInitialized,"actual terminal persistent planning inputs have not been initialized");
        StrictJson.require(originalSession.get()==same,"terminal planning inputs crossed the runtime's actual borrowed writer");
        var scope=authority.openReadOnlyTerminalPlanningScope(same,full,known,deadline);
        ActionPorts.OutcomeArchive originals=archive.withSession(same);
        var canonical=authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==known,"terminal planning inventory lost its identical actual Driver");
            return DriverPersistentPlanningState.crossRun(same,known,originals);
        });
        var inputs=DriverCapabilityStateProducer.publicTerminalInputs(scope,full,known,canonical,capturePublicLifecycle(scope,full,known),originals);
        scope.requireCurrent();inputs.requireScope(full,known);return inputs;
    }
    /** Sole coordinator finally hook. It consumes the actual canonical attempt under that same writer Session. */
    public void afterMarriageAttempt(ContinuityStorePort.Session borrowed,ActionReceipt actual) {
        Objects.requireNonNull(actual);
        if(!actual.command().operation().value().matches("arrange-marriage-[0-9]+-[0-9]+"))return;
        requireActive();
        ActionPorts.OutcomeArchive originals=archive.withSession(borrowed);
        try {
            authority.withFrozenFacts(borrowed,frozen -> {
                StrictJson.require(frozen.state() instanceof Known&&frozen.actions().actions().stream().anyMatch(actual::equals),"marriage cache invalidation requires its actual canonical attempt");
                Known known=(Known)frozen.state();var observed=known.observation().orElseThrow();
                ExactRef nativeSource=DriverObservationEvidenceReader.reference(known.auxiliary().get("capability_observed_native_source"));
                RawJson manifest=originals.loadMaterial(observed.semanticFactsEvidence());
                var nativeFrame=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),manifest,originals.loadNativeFrame(nativeSource));
                Complete frame=complete(nativeFrame,known,nativeSource);
                var publication=DriverCapabilityStateProducer.observeMarriageAttempt(frame,known,actual,originals);
                authority.publishCapabilityInputs(borrowed,known.stamp(),publication.expectedAuxiliarySha256(),publication);return null;
            });
        } catch(IOException failure) { throw new UncheckedIOException("actual marriage attempt retained; cache invalidation unavailable, no replay",failure); }
    }
    public DynamicCapabilities.Result read(Complete frame,Known known,ContinuityStorePort.Session borrowed,OpportunityJson.Obj received) {
        requireUsable();
        if(!planningInitialized)return new DynamicCapabilities.Incomplete(java.util.List.of("actual_persistent_planning_initial_capture_not_completed"));
        if(state==State.NEXT_CANDIDATE)try { authority.requireCandidateScope(borrowed,nextTransfer); }catch(IOException failure){throw new UncheckedIOException(failure);}
        OpportunityJson.Obj diagnostics=OpportunityJson.object(received.get("diagnostics"),"actual diagnostics");
        OpportunityJson.Obj hello=OpportunityJson.object(diagnostics.get("hello"),"actual HELLO");
        StrictJson.require(OpportunityJson.integer(hello.get("pid"),"pid").equals(java.math.BigInteger.valueOf(frame.identity().game().pid()))
                &&OpportunityJson.integer(hello.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"event inventory HELLO crossed actual physical frame");
        var caps=new java.util.LinkedHashSet<String>();for(var raw:OpportunityJson.array(hello.get("capabilities"),"capabilities"))caps.add(OpportunityJson.text(raw,"capability"));
        currentOptions().issue(frame,java.util.Set.copyOf(caps));
        var result=new DriverRuntimeCapabilities(authority,archive,borrowed).read(frame,known,received,bindings,files);
        if(result instanceof DynamicCapabilities.Incomplete)return result;
        return DriverPersistenceCapabilities.withStatus(result,DriverCapabilityStateProducer.sessionPresentation(known.auxiliary()),
                readHistoryPublisher().statusSnapshot());
    }
    /** Object ownership only; readiness and original source validation remain mandatory at every actual call. */
    public void requireOwner(DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive actualArchive,ExecutableStepBindings actualBindings) {
        StrictJson.require(authority==actualAuthority&&archive==actualArchive&&bindings==actualBindings,"capability runtime crossed its exact Driver/archive/bindings owner");
    }
    private static Complete complete(NativeObservationPort.ObservedFrame actual,Known known,ExactRef evidence) {
        var observed=known.observation().orElseThrow(() -> new IllegalArgumentException("actual current Driver observation unavailable"));
        var joined=new DriverObservationAssembler().assemble(actual,observed,evidence);
        StrictJson.require(joined instanceof Complete,"actual cache producer cannot reconstruct the original complete Driver/native frame");
        return (Complete)joined;
    }
}
