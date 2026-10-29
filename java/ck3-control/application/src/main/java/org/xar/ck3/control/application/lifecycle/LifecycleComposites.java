package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual three-branch Java successor. Root installs this same instance in the coordinator and writer router. */
public final class LifecycleComposites implements CompositeActionPort.OriginalContinuation {
    public record SeedLaunch(String parentLifecycleIntentId,GameGeneration oldGame,SeedArtifact seed,Instant deadline){
        public SeedLaunch{StrictJson.text(parentLifecycleIntentId);Objects.requireNonNull(oldGame);Objects.requireNonNull(seed);Objects.requireNonNull(deadline);}
    }
    public sealed interface SeedReplacement permits SeedStarted,SeedRejected,SeedUnknown { }
    public record SeedStarted(GameGeneration oldGame,GameGeneration newGame,String pipeName,String sessionId,
            ExactRef launchEvidence,ExactRef helloEvidence,ExactRef lifecycleEvidence) implements SeedReplacement {
        public SeedStarted{Objects.requireNonNull(oldGame);Objects.requireNonNull(newGame);StrictJson.text(pipeName);StrictJson.text(sessionId);
            Objects.requireNonNull(launchEvidence);Objects.requireNonNull(helloEvidence);Objects.requireNonNull(lifecycleEvidence);StrictJson.require(!oldGame.equals(newGame),"actual distinct replacement Game required");}
    }
    public record SeedRejected(String reason) implements SeedReplacement {public SeedRejected{StrictJson.text(reason);}}
    public record SeedUnknown(String reason) implements SeedReplacement {public SeedUnknown{StrictJson.text(reason);}}
    /** Implemented by the platform's one private ManagedGameSession/replaceSavedOnce adapter. */
    public interface SeedLifecyclePort {
        SeedReplacement replaceOnce(SeedLaunch request)throws IOException,InterruptedException;
        SeedReplacement query(String parentLifecycleIntentId,Instant deadline)throws IOException;
        void requireOriginal(GameGeneration expected)throws IOException;
        void requireCurrent(SeedStarted actual)throws IOException;
        NativeObservationPort.ObservedFrame observe(SeedStarted actual,Instant deadline)throws IOException,InterruptedException;
    }
    /** Existing storage adapter verifies the full Win32 pin, including volume/FileID/creation/mtime and SHA. */
    @FunctionalInterface public interface RecordedPinVerifier { void requireCurrent(WriterContracts.Pin actual)throws IOException; }
    @FunctionalInterface public interface BorrowedWriter { ContinuityStorePort.Session current() throws IOException; }
    @FunctionalInterface public interface ActualDrivers { DriverStateAssembler require() throws IOException; }
    /** Resolves the actual current per-Game SeedStore after Root has installed the same staged SAVE store. */
    @FunctionalInterface public interface ActualSeeds { SeedStore require() throws IOException; }
    /** The actual registered Family producer borrows this same Session; it never opens another writer. */
    @FunctionalInterface public interface NaturalFamilyMigration {
        void initialize(ContinuityStorePort.Session same,CommittedNatural actual)throws IOException;
    }
    private final Map<SessionIdentity,NaturalFamilyMigration> naturalFamilyMigrations=new HashMap<>();
    public synchronized void bindNaturalFamilyMigration(SessionIdentity physicalOwner,NaturalFamilyMigration actual) {
        Objects.requireNonNull(physicalOwner);Objects.requireNonNull(actual);
        if(naturalFamilyMigrations.putIfAbsent(physicalOwner,actual)!=null)
            throw new IllegalStateException("actual natural Family producer already bound for this physical owner");
    }
    /** Private-mint post-publication DATA. Neither a decoded proof nor a caller-built episode creates this token. */
    public static final class CommittedNatural {
        private final LifecycleComposites issuer;
        private final PendingPublication publication;
        private final RecoveredPending recovered;
        private final ExactRef lifecycleMaterial;
        private CommittedNatural(LifecycleComposites issuer,PendingPublication publication,ExactRef lifecycleMaterial) {
            this.issuer=issuer;this.publication=publication;this.recovered=null;this.lifecycleMaterial=lifecycleMaterial;
        }
        private CommittedNatural(LifecycleComposites issuer,RecoveredPending recovered) {
            this.issuer=issuer;this.publication=null;this.recovered=recovered;this.lifecycleMaterial=recovered.edge.eventPin().reference();
        }
        private ActionCommand parent(){return publication!=null?publication.parent():recovered.edge.parent().command();}
        public SessionIdentity owner() {
            var original=parent().lifecycleBefore();
            return new SessionIdentity(original.machineId(),original.game(),original.sessionId());
        }
        public FamilyNextEpisodeMigration.Episode before() {
            var subject=parent().lifecycleBefore().subject();
            return new FamilyNextEpisodeMigration.Episode(subject.episodeRunId(),subject.characterId());
        }
        public FamilyNextEpisodeMigration.Episode after() {
            var current=(publication!=null?publication.child().replacement():recovered.edge.afterDriver()).session();
            return new FamilyNextEpisodeMigration.Episode(current.episodeRunId(),current.actorId());
        }
        public ExactRef lifecycleMaterial(){return lifecycleMaterial;}
        private org.xar.ck3.control.continuity.ContinuityState lifecycleHead() {
            if(publication!=null) {
                if(!(publication.proof() instanceof LifecycleTransitionProof.ContinueSuccessor proof))
                    throw new IllegalStateException("actual natural successor publication required");
                return proof.publication().after();
            }
            return recovered.edge.publication().after();
        }
        public long headSequence(){return lifecycleHead().sequence();}
        public String headDigest(){return ContinuityJson.digest(lifecycleHead().toJson());}
        /** The producer and its registered verifier both re-enter this check under the borrowed writer lock. */
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {issuer.requireCurrentNatural(same,this);}
    }
    private ActionPorts.OutcomeArchive terminalPlanningArchive;
    /** Factory binds the actual Core-lifetime archive before publishing its catalog. */
    public synchronized void bindTerminalPlanningArchive(ActionPorts.OutcomeArchive actual){
        if(terminalPlanningArchive!=null)throw new IllegalStateException("actual terminal planning archive already bound");
        terminalPlanningArchive=Objects.requireNonNull(actual);
    }
    private void requireCurrentTerminalStrategy(DriverSnapshotFacts.Known actual)throws IOException {
        ActionPorts.OutcomeArchive archive;
        synchronized(this){archive=terminalPlanningArchive;}
        if(archive==null)throw new IOException("actual Core terminal planning archive is not bound");
        var same=writer.current();
        org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.requireCurrentTerminalStrategy(same,actual,archive.withSession(same));
    }
    private final ActualDrivers actualDrivers;
    private DriverStateAssembler drivers()throws IOException {return Objects.requireNonNull(actualDrivers.require(),"actual admitted Driver authority is unavailable");}
    private final LifecycleObservationPort observations;
    private final CheckpointFiles files;
    private final ActualSeeds actualSeeds;
    private SeedStore seeds()throws IOException {
        SeedStore actual=actualSeeds.require();if(actual==null)throw new IOException("actual admitted SeedStore is unavailable");return actual;
    }
    private final SeedLifecyclePort games;
    private final LifecycleContinuityAuthority authority;
    private final Path tutorial,evidenceRoot;
    private final Clock clock;
    private final SeedStore.StorageGuard storage;
    private final RecordedPinVerifier recordedPins;
    private final NaturalSuccessionVerifier naturalSuccession;
    private final NaturalSuccessionPreparation naturalPreparation;
    private final BorrowedWriter writer;
    private final Map<String,LifecycleTransitionProof> finished=new HashMap<>();
    private final Map<String,LifecycleObservationPort.Snapshot> originalFrames=new HashMap<>();
    private final Map<String,SeedStarted> replacements=new HashMap<>();
    private final Map<String,NativeObservationPort.ObservedFrame> loadedFrames=new HashMap<>();
    private final Map<String,SeedArtifact> usedSeeds=new HashMap<>();
    private record EnteredSeed(SeedLaunch launch,LifecycleCommit originalIntent) { }
    private final Map<String,EnteredSeed> enteredSeeds=new HashMap<>();
    private final java.util.Set<String> finalDomainAttempted=new java.util.HashSet<>();
    private record PendingPublication(ActionCommand parent,LifecycleChild child,LifecycleCommit committed,LifecycleTransitionProof proof) { }
    private final Map<String,PendingPublication> pendingPublications=new HashMap<>();
    private final Map<String,CommittedNatural> committedNaturals=new HashMap<>();
    private record PendingDomain(ActionCommand parent,LifecycleChild child,List<ExactRef> evidence,byte[] result) {
        PendingDomain{evidence=List.copyOf(evidence);result=result.clone();}
        @Override public byte[] result(){return result.clone();}
    }
    private final Map<String,PendingDomain> attemptedDomains=new HashMap<>();
    private record DeathInputs(DeathSettlement.Ready settlement,DeathSettlement.Persistence persistence){ }
    private final Map<String,DeathInputs> deathInputs=new HashMap<>();
    private final Map<String,NaturalSuccessionPreparation.PendingToken> pendingNatural=new HashMap<>();
    private final Map<String,NaturalSuccessionPreparation.FinalToken> finalizedNatural=new HashMap<>();
    private record RecoveredPending(RecordedPendingEpisode edge,LifecycleTransitionProof.ContinueSuccessor proof) { }
    private final Map<String,RecoveredPending> recoveredPending=new HashMap<>();
    private final Map<String,RecordedPendingEpisode> committedWarmObservations=new HashMap<>();
    private long evidenceSequence;
    public LifecycleComposites(DriverStateAssembler drivers,LifecycleObservationPort observations,CheckpointFiles files,SeedStore seeds,
            SeedLifecyclePort games,LifecycleContinuityAuthority authority,Path exactTutorial,Path evidenceRoot,Clock clock,
            SeedStore.StorageGuard actualStorageReservation,RecordedPinVerifier actualOriginalPinVerifier,NaturalSuccessionVerifier naturalSuccession,NaturalSuccessionPreparation naturalPreparation,BorrowedWriter writer){
        this(()->Objects.requireNonNull(drivers),observations,files,seeds,games,authority,exactTutorial,evidenceRoot,clock,
                actualStorageReservation,actualOriginalPinVerifier,naturalSuccession,naturalPreparation,writer);
    }
    /** Menu may freeze the actual handler before Entry; the resolver never constructs or substitutes a Driver repository. */
    public LifecycleComposites(ActualDrivers drivers,LifecycleObservationPort observations,CheckpointFiles files,SeedStore seeds,
            SeedLifecyclePort games,LifecycleContinuityAuthority authority,Path exactTutorial,Path evidenceRoot,Clock clock,
            SeedStore.StorageGuard actualStorageReservation,RecordedPinVerifier actualOriginalPinVerifier,NaturalSuccessionVerifier naturalSuccession,NaturalSuccessionPreparation naturalPreparation,BorrowedWriter writer){
        this(drivers,observations,files,fixedSeeds(seeds),games,authority,exactTutorial,evidenceRoot,clock,actualStorageReservation,
                actualOriginalPinVerifier,naturalSuccession,naturalPreparation,writer);
    }
    public LifecycleComposites(DriverStateAssembler drivers,LifecycleObservationPort observations,CheckpointFiles files,ActualSeeds seeds,
            SeedLifecyclePort games,LifecycleContinuityAuthority authority,Path exactTutorial,Path evidenceRoot,Clock clock,
            SeedStore.StorageGuard actualStorageReservation,RecordedPinVerifier actualOriginalPinVerifier,NaturalSuccessionVerifier naturalSuccession,NaturalSuccessionPreparation naturalPreparation,BorrowedWriter writer){
        this(()->Objects.requireNonNull(drivers),observations,files,seeds,games,authority,exactTutorial,evidenceRoot,clock,
                actualStorageReservation,actualOriginalPinVerifier,naturalSuccession,naturalPreparation,writer);
    }
    public LifecycleComposites(ActualDrivers drivers,LifecycleObservationPort observations,CheckpointFiles files,ActualSeeds seeds,
            SeedLifecyclePort games,LifecycleContinuityAuthority authority,Path exactTutorial,Path evidenceRoot,Clock clock,
            SeedStore.StorageGuard actualStorageReservation,RecordedPinVerifier actualOriginalPinVerifier,NaturalSuccessionVerifier naturalSuccession,NaturalSuccessionPreparation naturalPreparation,BorrowedWriter writer){
        this.actualDrivers=Objects.requireNonNull(drivers);this.observations=Objects.requireNonNull(observations);this.files=Objects.requireNonNull(files);this.actualSeeds=Objects.requireNonNull(seeds);
        this.games=Objects.requireNonNull(games);this.authority=Objects.requireNonNull(authority);tutorial=Objects.requireNonNull(exactTutorial);this.evidenceRoot=Objects.requireNonNull(evidenceRoot);
        this.clock=Objects.requireNonNull(clock);storage=Objects.requireNonNull(actualStorageReservation);recordedPins=Objects.requireNonNull(actualOriginalPinVerifier);
        this.naturalSuccession=Objects.requireNonNull(naturalSuccession);
        this.naturalPreparation=Objects.requireNonNull(naturalPreparation);
        this.writer=Objects.requireNonNull(writer);
        StrictJson.require(tutorial.isAbsolute()&&evidenceRoot.isAbsolute(),"exact configured profile/evidence roots required");authority.bind(this::requireCurrentChild);
    }
    private static ActualSeeds fixedSeeds(SeedStore seeds){SeedStore actual=Objects.requireNonNull(seeds);return ()->actual;}
    @Override public String handlerId(){return "java-death-succession-next-episode/v1";}
    /** Classification only. It grants neither submission authority nor an episode/cycle proof. */
    public static Optional<LifecycleTransitionProof.Kind> parentKind(OperationKey operation){
        Objects.requireNonNull(operation);return switch(operation.value()){
            case "death-terminal"->Optional.of(LifecycleTransitionProof.Kind.DEATH);
            case "continue-as-reconciled-successor"->Optional.of(LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR);
            case "start-next-episode"->Optional.of(LifecycleTransitionProof.Kind.NEXT_EPISODE);
            default->Optional.empty();
        };
    }
    @Override public boolean supports(OperationKey operation){return parentKind(operation).isPresent();}
    @Override public void validate(ActionCommand parent){
        StrictJson.require(supports(parent.operation()),"unsupported lifecycle operation");
        StrictJson.require(parent.origin() instanceof CommandOrigin.LifecycleTerminal,"actual lifecycle terminal origin is required; ordinary gameplay cannot fabricate a missing or changed player");
        StrictJson.require(parent.arguments().members().keySet().equals(java.util.Set.of("expected_revision")),"lifecycle arguments require only actual expected_revision");
        StrictJson.require(OpportunityJson.integer(parent.arguments().get("expected_revision"),"expected_revision").signum()>=0,"strict original expected revision required");
    }
    /** Exact current scope checks for the root's registered lifecycle guard. This method grants no generic native action. */
    public static void validateScope(ActionCommand parent,LifecycleObservationPort.Snapshot frame){
        validateIdentityScope(parent,frame);
        StrictJson.require(OpportunityJson.integer(parent.arguments().get("expected_revision"),"expected_revision").equals(frame.revision()),"actual lifecycle initial public revision differs");
        var identity=parent.lifecycleBefore();
        StrictJson.require(identity.subject().driverVersion()==frame.facts().stamp().driverVersion()
                &&identity.frame().snapshotId().equals(frame.actual().snapshotId())&&identity.frame().nativeRevision().equals(frame.actual().nativeRevision())
                &&identity.frame().revision().equals(frame.revision())&&identity.frame().dateRaw().equals(frame.dateRaw())
                &&identity.frame().paused()==frame.paused()&&identity.frame().mapReady()==frame.mapReady()
                &&identity.nativeEvidence().equals(frame.originalEvidence())
                &&identity.evidence().originalDriver().sha256().equals(frame.facts().stamp().driverSha256())
                &&identity.evidence().originalDriver().bytes()==frame.facts().driver().encode().length,"actual initial terminal frame/Driver/source differs from the command origin");
        var raw=org.xar.ck3.control.application.driver.DriverJson.object(frame.actual().state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(identity.currentPlayer().equals(LifecycleOriginFactory.currentPlayer(raw))
                &&identity.terminalReason()==LifecycleOriginFactory.deriveReason(identity.currentPlayer(),identity.subject().characterId()),"terminal origin changed actual missing/null/dead/changed player facts");
    }
    private static void validateIdentityScope(ActionCommand parent,LifecycleObservationPort.Snapshot frame){
        var identity=parent.lifecycleBefore();
        StrictJson.require(parent.source().equals(frame.source())&&parent.origin().machineId().equals(frame.actual().session().machineId())
                && parent.origin().game().equals(frame.actual().session().game())&&parent.sessionId().equals(frame.actual().session().sessionId())
                && parent.lifecycleBefore().subject().episodeRunId().equals(frame.facts().driver().session().episodeRunId())
                &&identity.connectionGeneration().equals(frame.actual().session().connectionGeneration())
                &&identity.subject().characterId().equals(frame.facts().driver().session().actorId())
                &&identity.subject().episodeEpoch()==frame.facts().stamp().episodeEpoch()
                &&identity.subject().driverVersion()<=frame.facts().stamp().driverVersion()
                &&frame.revision().signum()>=0,"actual lifecycle Game/session/source/episode differs");
        if(!parent.operation().value().equals("death-terminal"))StrictJson.require(frame.paused()&&frame.mapReady(),"paused real map required for episode transition");
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent,Children children)throws InterruptedException{
        validate(parent);
        try{
            LifecycleObservationPort.Snapshot observed=observations.current(parent,parent.deadline());validateScope(parent,observed);games.requireOriginal(parent.origin().game());
            originalFrames.putIfAbsent(parent.actionId(),observed);
            drivers().withFrozenFacts(writer.current(),frozen->{
                StrictJson.require(frozen.activeActionId().filter(parent.actionId()::equals).isPresent(),"lifecycle execution requires actual coordinator parent scope");
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"full actual Driver predecessor unavailable");
                var known=(DriverSnapshotFacts.Known)frozen.state();StrictJson.require(known.stamp().equals(observed.facts().stamp()),"lifecycle initial Driver version drift");
                return null;
            });
            // The original writer remains held. Read-only fact freezes finish before a genuine
            // native child or canonical lifecycle transition changes the journal and Driver.
            return switch(parent.operation().value()){
                case "continue-as-reconciled-successor" -> continueNatural(parent,children,observed);
                case "death-terminal" -> death(parent,children,observed);
                case "start-next-episode" -> next(parent,children,observed);
                default -> throw new IllegalArgumentException("unsupported lifecycle operation");
            };
        }catch(IOException|IllegalArgumentException failure){if(Thread.currentThread().isInterrupted())throw new InterruptedException(failure.toString());return new ActionPorts.Pending("lifecycle remains unresolved; no replay: "+failure.getMessage(),evidence(parent.actionId()));}
    }
    private ActionPorts.PostconditionResult continueNatural(ActionCommand parent,Children children,LifecycleObservationPort.Snapshot observed)throws IOException,InterruptedException {
        var outcome=naturalPreparation.prepareOutcome(parent,observed,children);
        if(outcome instanceof NaturalSuccessionPreparation.PendingPreparation pending)
            return retainNaturalPending(parent,pending.token());
        if(outcome instanceof NaturalSuccessionPreparation.PendingFinalized finalized)
            return finishNaturalPending(parent,children,finalized.token());
        var prepared=((NaturalSuccessionPreparation.FinalSnapshot)outcome).actual();validateIdentityScope(parent,prepared);
        StrictJson.require(prepared.actual().session().equals(observed.actual().session())&&prepared.source().equals(observed.source())
                &&prepared.facts().driver().session().equals(observed.facts().driver().session())
                &&prepared.facts().stamp().episodeEpoch()==observed.facts().stamp().episodeEpoch()
                &&prepared.facts().stamp().driverVersion()>=observed.facts().stamp().driverVersion()&&prepared.revision().compareTo(observed.revision())>=0,
                "actual succession preparation crossed the original Game/source/Driver episode or moved revision backwards");
        var before=observed.facts().driver().commandHistory();var after=prepared.facts().driver().commandHistory();
        StrictJson.require(after.size()>=before.size(),"actual succession preparation discarded original history");
        for(int index=0;index<before.size();index++)StrictJson.require(java.util.Arrays.equals(before.get(index).originalRow().json(),after.get(index).originalRow().json()),"actual succession preparation rewrote original history");
        drivers().withFrozenFacts(writer.current(),frozen->{StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual prepared succession Driver unavailable");
            var actual=(DriverSnapshotFacts.Known)frozen.state();StrictJson.require(actual.stamp().equals(prepared.facts().stamp())
                    &&java.util.Arrays.equals(actual.driver().encode(),prepared.facts().driver().encode())
                    &&frozen.activeActionId().filter(parent.actionId()::equals).isPresent(),"prepared succession snapshot is not the actual same-parent repository Driver");return null;});
        originalFrames.put(parent.actionId(),prepared);
        return finish(parent,children,prepared,LifecycleChild.Phase.SUCCESSOR_COMMITTED,
                LifecycleReducer.continueSuccessor(prepared,newRun(OpportunityJson.integer(OpportunityJson.object(prepared.semantic().get("played_character"),"played_character").get("character_id"),"character_id")),clock.instant()),parent.origin().game(),List.of());
    }

    private static void sameNaturalParent(ActionCommand parent,NaturalSuccessionPreparation.PendingToken token){
        StrictJson.require(parent.operation().equals(LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR.key())
                &&java.util.Arrays.equals(ActionCodec.encodeCommand(parent),ActionCodec.encodeCommand(token.originalParent())),
                "pending successor token changed its complete original parent");
    }
    private ActionPorts.PostconditionResult retainNaturalPending(ActionCommand parent,NaturalSuccessionPreparation.PendingToken token)throws IOException{
        sameNaturalParent(parent,token);
        StrictJson.require(naturalPreparation instanceof NaturalSuccessionContinuationSource,
                "actual pending succession source has no finite child verifier");
        naturalPreparation.requireCurrent(parent,writer.current(),token);
        StrictJson.require(clock.instant().isBefore(token.deadline()),"actual finite pending successor deadline expired");
        pendingNatural.put(parent.actionId(),token);
        return new ActionPorts.Pending("actual pending successor is published; original parent is not finalized",token.evidence());
    }
    @Override public void requireContinuation(ActionCommand parent,CompositeExecution retained,CompositeContinuationToken token){
        try{
            StrictJson.require(token instanceof NaturalSuccessionPreparation.PendingToken
                    &&retained.handlerId().equals(handlerId()),
                    "actual original pending successor source/cursor is unavailable");
            var pending=(NaturalSuccessionPreparation.PendingToken)token;sameNaturalParent(parent,pending);
            StrictJson.require(clock.instant().isBefore(token.deadline()),"finite pending successor continuation deadline expired");
            var warmObservation=committedWarmObservations.get(parent.actionId());
            if(warmObservation!=null){
                var same=writer.current();naturalPreparation.requireCurrent(parent,same,pending);requireRecordedPending(same,warmObservation);
                ((NaturalSuccessionContinuationSource)naturalPreparation).requireCommittedPendingEpisode(canonicalParent(same,parent),same,warmObservation);
                StrictJson.require(finished.get(parent.actionId()) instanceof LifecycleTransitionProof.ContinueSuccessor,
                        "actual warm completed episode proof is unavailable");return;
            }
            var recovered=recoveredPending.get(parent.actionId());
            if(recovered!=null){
                var same=writer.current();naturalPreparation.requireCurrent(parent,same,pending);
                requireRecordedPending(same,recovered.edge);
                StrictJson.require(finished.get(parent.actionId())==recovered.proof,"recovered successor lost its actual private episode proof");
                ((NaturalSuccessionContinuationSource)naturalPreparation).requireCommittedPendingEpisode(canonicalParent(same,parent),same,recovered.edge);
                return;
            }
            // After a real lifecycle commit the sole operation available here is observe(), never another child.
            var domain=attemptedDomains.get(parent.actionId());
            if(domain!=null){
                StrictJson.require(originalFrames.containsKey(parent.actionId())&&pendingNatural.get(parent.actionId())==pending
                        &&domain.child().phase()==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED,
                        "original finalized pending lifecycle custody differs");
                domain.child().prepared().ifPresent(actual->StrictJson.require(actual.request().identity().equals(domain.child().request().identity()),
                        "original finalized lifecycle request changed"));
                return;
            }
            var finalized=finalizedNatural.get(parent.actionId());
            if(finalized!=null){
                StrictJson.require(originalFrames.containsKey(parent.actionId())&&pendingNatural.get(parent.actionId())==pending,"finalized continuation lost its original private carrier");
                naturalPreparation.requireFinalized(parent,writer.current(),finalized);return;
            }
            StrictJson.require(naturalPreparation instanceof NaturalSuccessionContinuationSource,
                    "actual pending source cannot qualify a finite child");
            var same=writer.current();naturalPreparation.requireCurrent(parent,same,pending);
            if(!originalFrames.containsKey(parent.actionId())){
                // A process restart has no Java map entry. Only the actual private cold source can
                // reopen the canonical parent's original terminal frame; token DATA never suffices.
                var source=(NaturalSuccessionContinuationSource)naturalPreparation;
                var original=Objects.requireNonNull(source.requireRetainedOriginalFrame(parent,same,pending));
                validateScope(parent,original);
                naturalPreparation.requireCurrent(parent,same,pending);
                originalFrames.put(parent.actionId(),original);
            }
            pendingNatural.put(parent.actionId(),pending);
        }catch(IOException failure){throw new UncheckedIOException("actual pending successor continuation unavailable",failure);}
    }
    @Override public void requireContinuationChild(ActionCommand parent,CompositeExecution retained,CompositeContinuationToken token,ActionCommand child){
        requireContinuation(parent,retained,token);
        StrictJson.require(!attemptedDomains.containsKey(parent.actionId())&&!finalizedNatural.containsKey(parent.actionId())&&!recoveredPending.containsKey(parent.actionId())&&!committedWarmObservations.containsKey(parent.actionId()),
                "finalized successor cannot authorize another native child");
        try{((NaturalSuccessionContinuationSource)naturalPreparation).requireChild(parent,writer.current(),
                (NaturalSuccessionPreparation.PendingToken)token,child);}
        catch(IOException failure){throw new UncheckedIOException("actual pending successor child source unavailable",failure);}
    }
    @Override public ActionPorts.PostconditionResult continueOriginal(ActionCommand parent,CompositeExecution retained,
            CompositeContinuationToken token,Children children)throws InterruptedException{
        requireContinuation(parent,retained,token);
        if(attemptedDomains.containsKey(parent.actionId())||recoveredPending.containsKey(parent.actionId())||committedWarmObservations.containsKey(parent.actionId()))return observe(parent,retained);
        try{
            var finalToken=finalizedNatural.get(parent.actionId());
            if(finalToken!=null)return finishNaturalPending(parent,children,finalToken);
            var outcome=naturalPreparation.resumeOutcome(parent,(NaturalSuccessionPreparation.PendingToken)token,children);
            if(outcome instanceof NaturalSuccessionPreparation.PendingPreparation pending)
                return retainNaturalPending(parent,pending.token());
            StrictJson.require(outcome instanceof NaturalSuccessionPreparation.PendingFinalized,
                    "already-published pending episode cannot use an old terminal final Snapshot");
            return finishNaturalPending(parent,children,((NaturalSuccessionPreparation.PendingFinalized)outcome).token());
        }catch(IOException|IllegalArgumentException failure){
            if(Thread.currentThread().isInterrupted())throw new InterruptedException(failure.toString());
            return new ActionPorts.Pending("actual same-parent pending successor remains unresolved; no replay: "+failure.getMessage(),
                    ((NaturalSuccessionPreparation.PendingToken)token).evidence());
        }
    }
    private LifecycleObservationPort.Snapshot requireFinalNaturalFrame(ActionCommand parent,NaturalSuccessionPreparation.FinalToken token)throws IOException{
        sameNaturalParent(parent,token);var same=writer.current();naturalPreparation.requireFinalized(parent,same,token);
        var known=token.publishedFinal();var frame=token.qualifiedFinalFrame();
        StrictJson.require(frame!=null&&frame.facts()!=null&&frame.facts().driverVersion()==known.stamp().driverVersion()
                &&frame.facts().episodeEpoch()==known.stamp().episodeEpoch()
                &&java.util.Arrays.equals(frame.facts().driver().encode(),known.driver().encode())
                &&frame.facts().source().equals(parent.source())
                &&frame.actual().session().game().equals(parent.origin().game()),
                "finalized pending successor requires its actual current post-publication full frame");
        StrictJson.require(java.util.Arrays.equals(token.finalReduction().driver().encode(),known.driver().encode())
                &&token.beforeFinal().stamp().episodeEpoch()==known.stamp().episodeEpoch()
                &&Math.addExact(token.beforeFinal().stamp().driverVersion(),1)==known.stamp().driverVersion()
                &&token.beforeFinal().stamp().game().equals(known.stamp().game())
                &&token.beforeFinal().driver().session().equals(known.driver().session()),
                "actual final projection changed the already-published successor episode/epoch");
        var previous=parent.lifecycleBefore().subject();
        StrictJson.require(known.stamp().episodeEpoch()==Math.addExact(previous.episodeEpoch(),1)
                &&!known.driver().session().actorId().equals(previous.characterId())
                &&!known.driver().session().episodeRunId().equals(previous.episodeRunId()),
                "final pending source must preserve the one genuine successor adoption from its original causal parent");
        drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.activeActionId().filter(parent.actionId()::equals).isPresent()
                    &&frozen.state() instanceof DriverSnapshotFacts.Known,
                    "final pending source is outside its actual original coordinator parent");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(current.stamp().equals(known.stamp())
                    &&java.util.Arrays.equals(current.driver().encode(),known.driver().encode())
                    &&current.auxiliary().equals(known.auxiliary()),"actual final pending publication is not the current exact Driver repository fact");return null;
        });
        return new LifecycleObservationPort.Snapshot(frame.actual(),frame.facts().source(),frame.semantic(),known,frame.originalEvidence());
    }
    private ActionPorts.PostconditionResult finishNaturalPending(ActionCommand parent,Children children,
            NaturalSuccessionPreparation.FinalToken token)throws IOException{
        var actual=requireFinalNaturalFrame(parent,token);
        StrictJson.require(pendingNatural.containsKey(parent.actionId()),
                "final pending token has no original retained pending successor carrier");
        finalizedNatural.put(parent.actionId(),token);originalFrames.put(parent.actionId(),actual);
        var known=token.publishedFinal();
        // FINALIZE already performed the only business CAS. Preserve its complete current provenance.
        var recorded=new LifecycleReducer.Reduction(known.driver(),known.auxiliary(),token.finalReduction().result());
        var evidence=new ArrayList<>(token.evidence());
        evidence.addAll(List.of(token.canonicalDomain(),token.actualPublishedDriver(),token.canonicalPublicationProof(),
                token.m3FinalizationProof(),token.canonicalFinalizationDomain()));
        var causal=parent.lifecycleBefore().evidence();
        evidence.addAll(causal.originals());
        var same=writer.current();long finalSequence=token.finalizationReceipt().head().sequence();
        String finalName=String.format(java.util.Locale.ROOT,"%08d.json",finalSequence);
        var finalEvent=same.head().documents().stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(finalName))
                .findFirst().orElseThrow(()->new IOException("actual canonical finalization receipt event FileID pin unavailable"));
        same.verifyPin(finalEvent);
        ObjectNode originalEvent=LifecycleJson.parse(same.readPinned(finalEvent,org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES),
                org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES);
        StrictJson.require(token.finalizationReceipt().eventIdentity().equals(LifecycleJson.text(originalEvent.get("identity"))),
                "actual finalization receipt differs from its canonical original event");same.verifyPin(finalEvent);evidence.add(finalEvent.reference());
        return finish(parent,children,actual,LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED,recorded,
                actual.actual().session().game(),List.copyOf(new java.util.LinkedHashSet<>(evidence)));
    }
    /** Versioned DATA conversion only; the actual observer/writer guard still owns physical qualification. */
    public static Optional<DeathSettlement.Ready> settlementFromSnapshot(LifecycleObservationPort.Snapshot actual)throws IOException {
        Objects.requireNonNull(actual);
        var facts=actual.facts().observation().orElseThrow(()->new IOException("actual settlement observation wire version is unavailable"));
        StrictJson.require(facts.transport().equals(actual.actual().session())&&facts.snapshotId().equals(actual.actual().snapshotId())
                &&facts.nativeRevision().equals(actual.actual().nativeRevision())&&facts.publicRevision().equals(actual.revision())
                &&facts.source().equals(actual.source())&&facts.driverVersion()==actual.facts().stamp().driverVersion()
                &&facts.episodeEpoch()==actual.facts().stamp().episodeEpoch()
                &&java.util.Arrays.equals(facts.driver().encode(),actual.facts().driver().encode())
                &&facts.nativeStateSha256().equals(org.xar.ck3.control.application.driver.DriverJson.sha256(actual.actual().state().bytes())),
                "settlement wire version crossed its actual source observation or complete Driver");
        String key=org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement.KEY;
        if(facts.observationVersion()==org.xar.ck3.control.application.driver.DriverObservationAssembler.LEGACY_OBSERVATION_VERSION
                ||facts.observationVersion()==org.xar.ck3.control.application.driver.DriverObservationAssembler.WAR_ARMY_OBSERVATION_VERSION){
            var original=org.xar.ck3.control.application.driver.DriverObservationAssembler.originalNativeState(actual.actual());
            var value=original.members().containsKey(key)?org.xar.ck3.control.application.driver.DriverJson.toNormalizedNode(original.get(key))
                    :com.fasterxml.jackson.databind.node.NullNode.getInstance();
            return DeathSettlement.normalize(value);
        }
        StrictJson.require(facts.observationVersion()==org.xar.ck3.control.application.driver.DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION,
                "unknown settlement semantic wire version");
        var projected=new org.xar.ck3.control.application.driver.DriverObservationAssembler().projectFull(actual.actual(),facts,actual.originalEvidence());
        StrictJson.require(projected.semantic().equals(actual.semantic()),"normalized settlement SEM differs from its sole original native/Driver projection");
        var semantic=projected.semantic();
        var value=semantic.members().containsKey(key)?org.xar.ck3.control.application.driver.DriverJson.toNormalizedNode(semantic.get(key))
                :com.fasterxml.jackson.databind.node.NullNode.getInstance();
        return DeathSettlement.fromNormalized(value);
    }
    private ActionPorts.PostconditionResult death(ActionCommand parent,Children children,LifecycleObservationPort.Snapshot observed)throws IOException,InterruptedException{
        StrictJson.require(LifecycleReducer.lifecycle(observed.facts().driver()).equals("rogue_one_life"),"ordinary succession cannot use death-terminal");
        Optional<DeathSettlement.Ready> settled=settlementFromSnapshot(observed);
        // Capability absence is distinct from a supported settlement that has not arrived yet.
        ObjectNode aux=LifecycleReducer.auxiliary(observed.facts());StrictJson.require(aux.has("native_capabilities"),"actual native capability source unavailable");
        boolean supported=false;for(var item:aux.path("native_capabilities"))if(item.isTextual()&&item.textValue().equals("game.state.xar-one-life-settlement"))supported=true;
        while(supported&&(settled.isEmpty()||!settled.orElseThrow().sourceCharacterId().equals(observed.facts().driver().session().actorId()))&&clock.instant().isBefore(parent.deadline())){
            var next=observations.next(parent,observed,parent.deadline());
            StrictJson.require(next.source().equals(observed.source())&&next.actual().session().equals(observed.actual().session())
                    &&next.facts().stamp().equals(observed.facts().stamp())&&next.revision().compareTo(observed.revision())>=0,"settlement wait crossed original source/Game/episode/Driver version");observed=next;
            settled=settlementFromSnapshot(observed);
        }
        if(supported&&settled.isEmpty())throw new IOException("actual native settlement did not become ready before deadline");
        DeathSettlement.Persistence persistence=settled.isPresent()?DeathSettlement.awaitPersistence(settled.orElseThrow(),files,tutorial,parent.deadline(),clock):
                new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.UNAVAILABLE,false,Optional.empty(),List.of());
        originalFrames.put(parent.actionId(),observed);deathInputs.put(parent.actionId(),new DeathInputs(settled.orElse(null),persistence));
        return finish(parent,children,observed,LifecycleChild.Phase.DEATH_RECORDED,
                LifecycleReducer.death(observed,settled.orElse(null),persistence,clock.instant()),parent.origin().game(),persistence.evidence());
    }
    private ActionPorts.PostconditionResult next(ActionCommand parent,Children children,LifecycleObservationPort.Snapshot observed)throws IOException,InterruptedException{
        LifecycleReducer.requireScoredTerminal(observed.facts().driver());requireCurrentTerminalStrategy(observed.facts());
        SeedAdoption available=seeds().read();if(!(available instanceof SeedAdoption.Available actual))throw new IOException("immutable first-life seed unavailable: "+available);
        SeedArtifact seed=actual.artifact();seed.requireCurrent(files);usedSeeds.put(parent.actionId(),seed);
        ObjectNode entered=LifecycleJson.row();String intent="next-episode-"+ActionCodec.sha256(parent.actionId().getBytes(StandardCharsets.UTF_8));entered.put("lifecycle_intent_id",intent);entered.put("source_run_id",observed.facts().driver().session().episodeRunId());entered.put("phase","relaunching_episode_seed");
        LifecycleChild before=new LifecycleChild(parent,LifecycleChild.Phase.NEXT_EPISODE_ENTERED,observed.facts().stamp(),observed.facts().driver(),observed.facts().auxiliary(),parent.origin().game(),entered,List.of(seed.save().reference(),seed.metadata().reference(),observed.originalEvidence()));
        authority.register(before);LifecycleCommit durable=children.lifecycle(before);StrictJson.require(!durable.committedDocuments().isEmpty(),"actual durable parent lifecycle intent evidence required before old stop");
        SeedLaunch launch=new SeedLaunch(intent,parent.origin().game(),seed,parent.deadline());enteredSeeds.put(parent.actionId(),new EnteredSeed(launch,durable));
        SeedReplacement outcome=games.replaceOnce(launch);
        if(!(outcome instanceof SeedStarted started))throw new IOException("original seed replacement is not proven; query only: "+outcome);
        StrictJson.require(started.oldGame().equals(parent.origin().game())&&started.pipeName().equals(observed.facts().driver().session().pipeName()),"replacement crossed original Game/pipe");
        replacements.put(parent.actionId(),started);NativeObservationPort.ObservedFrame loaded=awaitSeedMap(parent,started,seed);loadedFrames.put(parent.actionId(),loaded);
        ObjectNode state=LifecycleJson.parse(loaded.state().bytes(),16<<20);BigInteger actor=LifecycleJson.integer(LifecycleJson.object(state.get("played_character")).get("character_id"),BigInteger.ONE);
        requireCurrentTerminalStrategy(observed.facts());
        LifecycleReducer.Reduction reduction=LifecycleReducer.nextEpisode(observed.facts(),seed,started.newGame().pid(),actor,LifecycleJson.integer(state.get("date_raw"),BigInteger.ZERO),newRun(actor),clock.instant());
        finalDomainAttempted.add(parent.actionId());return finish(parent,children,observed,LifecycleChild.Phase.NEXT_EPISODE_COMMITTED,reduction,started.newGame(),
                List.of(seed.save().reference(),seed.metadata().reference(),started.launchEvidence(),started.helloEvidence(),started.lifecycleEvidence(),publish(parent.actionId(),loaded.originalPacket())));
    }
    private NativeObservationPort.ObservedFrame awaitSeedMap(ActionCommand parent,SeedStarted started,SeedArtifact seed)throws IOException,InterruptedException{
        BigInteger revision=null;String snapshotId=null,stateDigest=null;Instant stableSince=null;
        while(clock.instant().isBefore(parent.deadline())){
            games.requireCurrent(started);seed.requireCurrent(files);var frame=games.observe(started,parent.deadline());requireLoadedScope(started,frame);
            ObjectNode state=LifecycleJson.parse(frame.state().bytes(),16<<20);JsonNodeCheck.checkSeed(state,seed);
            String digest=LifecycleJson.sha(frame.state().bytes());
            StrictJson.require(frame.session().machineId().equals(parent.origin().machineId()),"seed load crossed original machine");
            if(frame.nativeRevision().equals(revision)&&frame.snapshotId().equals(snapshotId)&&digest.equals(stateDigest)){
                if(java.time.Duration.between(stableSince,clock.instant()).compareTo(java.time.Duration.ofMillis(500))>=0)return frame;
            }else{revision=frame.nativeRevision();snapshotId=frame.snapshotId();stateDigest=digest;stableSince=clock.instant();}
            Thread.sleep(Math.min(50,Math.max(1,java.time.Duration.between(clock.instant(),parent.deadline()).toMillis())));
        }throw new IOException("replacement did not prove stable paused seed map for original 0.5 second interval");
    }
    private static final class JsonNodeCheck {
        private JsonNodeCheck(){ }
        static void checkSeed(ObjectNode state,SeedArtifact seed){ObjectNode player=LifecycleJson.object(state.get("played_character"));
            StrictJson.require(LifecycleJson.bool(state.get("paused"))&&LifecycleJson.bool(state.get("map_ready"))&&LifecycleJson.bool(player.get("alive"))
                    &&LifecycleJson.integer(player.get("character_id"),BigInteger.ONE).equals(seed.characterId())&&LifecycleJson.integer(state.get("date_raw"),BigInteger.ZERO).equals(seed.dateRaw()),"actual seed map/player/date not yet confirmed");}
    }
    private static void requireLoadedScope(SeedStarted started,NativeObservationPort.ObservedFrame frame){StrictJson.require(frame.session().game().equals(started.newGame())&&frame.session().sessionId().equals(started.sessionId()),"loaded frame came from another private replacement transport");}
    @FunctionalInterface private interface DomainCommitter { LifecycleCommit commit(LifecycleChild child) throws IOException; }
    private ActionPorts.PostconditionResult finish(ActionCommand parent,Children children,LifecycleObservationPort.Snapshot original,LifecycleChild.Phase phase,LifecycleReducer.Reduction reduction,GameGeneration after,List<ExactRef> extra)throws IOException{
        return finish(parent,children::lifecycle,original,phase,reduction,after,extra);
    }
    private ActionPorts.PostconditionResult finish(ActionCommand parent,DomainCommitter committer,LifecycleObservationPort.Snapshot original,LifecycleChild.Phase phase,LifecycleReducer.Reduction reduction,GameGeneration after,List<ExactRef> extra)throws IOException{
        List<ExactRef> collected=new ArrayList<>(List.of(original.originalEvidence(),original.facts().originalHistoryBasis()));collected.addAll(extra);
        ExactRef beforeDriver;
        if(phase==LifecycleChild.Phase.NEXT_EPISODE_COMMITTED){
            // The actual terminal original already exists. Reuse it rather than publishing an equal-looking copy.
            var source=parent.lifecycleBefore().evidence();beforeDriver=source.originalDriver();var same=writer.current();
            var actualPin=same.capturePin(beforeDriver,retainedDriverBound(beforeDriver));
            StrictJson.require(java.util.Arrays.equals(same.readPinned(actualPin,retainedDriverBound(actualPin.reference())),
                    original.facts().driver().encode()),"NEXT original complete Driver differs from the canonical terminal source");
            same.verifyPin(actualPin);
            collected.addAll(source.originals());
        }else beforeDriver=publish(parent.actionId()+"-before-driver",original.facts().driver().encode());
        collected.add(beforeDriver);
        ExactRef afterDriver=publish(parent.actionId()+"-adopted-driver",reduction.driver().encode());collected.add(afterDriver);
        LifecycleHistoryBinding historyBinding=null;
        if(phase==LifecycleChild.Phase.DEATH_RECORDED){
            var actualRow=reduction.driver().commandHistory().getLast();ExactRef retainedRow=publish(parent.actionId()+"-terminal-history",actualRow.originalRow().json());
            historyBinding=LifecycleHistoryBinding.produced(parent,reduction.driver(),retainedRow);collected.add(retainedRow);
        }
        original.facts().observation().ifPresent(value->collected.add(value.semanticFactsEvidence()));List<ExactRef> evidence=List.copyOf(new java.util.LinkedHashSet<>(collected));
        ObjectNode delta=LifecycleJson.row();delta.set("result",LifecycleJson.parse(reduction.result(),LifecycleProofCodec.MAX_RESULT_BYTES));delta.put("original_native_sha256",original.originalEvidence().sha256());
        delta.set("original_native_ref",original.originalEvidence().toJson());delta.set("original_driver_ref",beforeDriver.toJson());
        delta.set("adopted_driver_ref",afterDriver.toJson());
        if(phase==LifecycleChild.Phase.NEXT_EPISODE_COMMITTED){
            var seed=Objects.requireNonNull(usedSeeds.get(parent.actionId()));var loaded=Objects.requireNonNull(loadedFrames.get(parent.actionId()));
            String loadedSha=LifecycleJson.sha(loaded.originalPacket());ExactRef loadedRef=extra.stream().filter(ref->ref.sha256().equals(loadedSha)&&ref.bytes()==loaded.originalPacket().length).findFirst()
                    .orElseThrow(()->new IOException("original loaded seed native packet not archived"));
            delta.set("loaded_native_ref",loadedRef.toJson());delta.set("episode_seed_ref",seed.save().reference().toJson());delta.set("episode_seed_metadata_ref",seed.metadata().reference().toJson());
        }
        if(historyBinding!=null)delta.set("history_binding",historyBinding.toJson());
        if(phase==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED){
            var token=Objects.requireNonNull(finalizedNatural.get(parent.actionId()));
            delta.set("causal_original_driver_ref",parent.lifecycleBefore().evidence().originalDriver().toJson());
            ObjectNode completed=delta.putObject("pending_ui_finalization");
            completed.set("m3_finalization_proof",token.m3FinalizationProof().toJson());
            completed.set("canonical_finalization_domain",token.canonicalFinalizationDomain().toJson());
            completed.set("canonical_pending_domain",token.canonicalDomain().toJson());
            completed.set("canonical_pending_publication_proof",token.canonicalPublicationProof().toJson());
            completed.set("actual_pending_driver",token.actualPublishedDriver().toJson());
            completed.put("finalization_event_identity",token.finalizationReceipt().eventIdentity());
            completed.put("finalization_sequence",token.finalizationReceipt().head().sequence());
            completed.put("before_final_driver_sha256",token.beforeFinal().stamp().driverSha256());
            completed.put("published_final_driver_sha256",token.publishedFinal().stamp().driverSha256());
        }
        if(phase==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED){
            var same=writer.current();var head=same.head();
            var auxiliaryRef=publish(parent.actionId()+"-pending-before-auxiliary",org.xar.ck3.control.application.driver.DriverJson.encode(original.facts().auxiliary()));
            var auxiliaryPin=same.capturePin(auxiliaryRef,org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            var knownRef=publish(parent.actionId()+"-pending-before-known",DriverSnapshotFacts.encodeKnownOriginal(original.facts()).bytes());
            var knownPin=same.capturePin(knownRef,DriverSnapshotFacts.MAX_ORIGINAL_BYTES);
            var auxiliaryEvidence=new ArrayList<>(evidence);auxiliaryEvidence.add(auxiliaryRef);auxiliaryEvidence.add(knownRef);evidence=List.copyOf(auxiliaryEvidence);
            var originals=new ArrayList<WriterContracts.Pin>();
            for(var ref:evidence)originals.add(same.capturePin(ref,retainedDriverBound(ref)));
            var archived=new LifecyclePendingOriginals(head.state().sequence(),head.digest(),auxiliaryPin,knownPin,same.captureSources(),originals);
            var reference=publish(parent.actionId()+"-pending-lifecycle-originals",archived.encode());
            var actualPin=same.capturePin(reference,LifecyclePendingOriginals.MAXIMUM_BYTES);
            delta.set("pending_episode_originals",LifecycleProofCodec.encodePin(actualPin));
            var complete=new ArrayList<>(evidence);complete.add(reference);evidence=List.copyOf(complete);
            StrictJson.require(head.digest().equals(same.head().digest()),"archiving lifecycle originals changed the original canonical head");
        }
        LifecycleChild child=new LifecycleChild(parent,phase,original.facts().stamp(),reduction.driver(),reduction.auxiliary(),after,delta,evidence);authority.register(child);
        PendingDomain pendingDomain=new PendingDomain(parent,child,evidence,reduction.result());
        StrictJson.require(attemptedDomains.putIfAbsent(parent.actionId(),pendingDomain)==null,"original lifecycle domain was already attempted; query only");
        return retainCommitted(pendingDomain,committer.commit(child));
    }
    private ActionPorts.PostconditionResult retainCommitted(PendingDomain domain,LifecycleCommit committed)throws IOException {
        var parent=domain.parent();var child=domain.child();var borrowed=writer.current();borrowed.requireCommitted(committed.prepared(),committed.receipt());
        StrictJson.require(child.prepared().filter(prepared->prepared==committed.prepared()).isPresent(),"actual lifecycle Prepared custody differs");
        StrictJson.require(!committed.committedDocuments().isEmpty(),"actual committed event document/native witnesses unavailable");
        List<ExactRef> originals=new ArrayList<>(domain.evidence());immutableCommitPins(committed).forEach(pin->originals.add(pin.reference()));
        LifecycleTransitionProof proof=switch(child.phase()){case DEATH_RECORDED->new LifecycleTransitionProof.Death(this,parent,committed,originals,domain.result());case SUCCESSOR_COMMITTED,SUCCESSOR_PENDING_FINALIZED->new LifecycleTransitionProof.ContinueSuccessor(this,parent,committed,originals,domain.result());case NEXT_EPISODE_COMMITTED->new LifecycleTransitionProof.NextEpisode(this,parent,committed,originals,domain.result());default->throw new IllegalArgumentException("entered is not an applied lifecycle result");};
        proof.validateParent(parent);PendingPublication pending=new PendingPublication(parent,child,committed,proof);
        StrictJson.require(pendingPublications.putIfAbsent(parent.actionId(),pending)==null,"original lifecycle publication already exists");
        return publishRetained(pending);
    }
    private String requireCurrentChild(WriterContracts.Head actualHead,LifecycleChild child)throws IOException{
        drivers().withFrozenFacts(writer.current(),frozen->{StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known&&((DriverSnapshotFacts.Known)frozen.state()).stamp().equals(child.expected()),"original locked lifecycle Driver CAS drift");
            StrictJson.require(frozen.activeActionId().filter(child.parentActionId()::equals).isPresent(),"original active parent lifecycle differs");return null;});
        LifecycleObservationPort.Snapshot original=originalFrames.get(child.parentActionId());if(original==null)throw new IOException("retained original actual frame unavailable");
        files.observe(Path.of(original.originalEvidence().path())).filter(file->file.reference().equals(original.originalEvidence())).orElseThrow(()->new IOException("original native evidence drift"));
        try{
            LifecycleReducer.Reduction rerun=null;String naturalDigest=null;
            ObjectNode result=child.request().detailsObject().has("delta")&&child.request().detailsObject().get("delta").has("result")?LifecycleJson.object(child.request().detailsObject().get("delta").get("result")):null;
            if(child.phase()==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED){
                var archivedPin=LifecycleProofCodec.decodePin(child.request().detailsObject().get("delta").get("pending_episode_originals"));
                var archived=LifecyclePendingOriginals.decode(writer.current().readPinned(archivedPin,LifecyclePendingOriginals.MAXIMUM_BYTES));
                writer.current().verifyPin(archivedPin);
                StrictJson.require(archived.beforeSequence()==actualHead.state().sequence()&&archived.beforeDigest().equals(actualHead.digest())
                        &&org.xar.ck3.control.application.driver.DriverJson.object(writer.current().readPinned(archived.beforeAuxiliaryPin(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES).equals(original.facts().auxiliary())
                        &&archived.sources().equals(writer.current().captureSources()),"actual pending lifecycle originals changed before commit");
                StrictJson.require(java.util.Arrays.equals(writer.current().readPinned(archived.beforeKnownPin(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES),
                        DriverSnapshotFacts.encodeKnownOriginal(original.facts()).bytes()),"original complete Known differs before lifecycle metadata commit");
                for(var pin:archived.originals())writer.current().verifyPin(pin);
                var token=finalizedNatural.get(child.parentActionId());if(token==null)throw new IOException("actual private final pending successor token unavailable");
                var actual=requireFinalNaturalFrame(child.parent(),token);
                StrictJson.require(actual.facts().stamp().equals(original.facts().stamp())
                        &&actual.semantic().equals(original.semantic())&&actual.actual().session().equals(original.actual().session())
                        &&actual.actual().snapshotId().equals(original.actual().snapshotId())
                        &&actual.actual().nativeRevision().equals(original.actual().nativeRevision())
                        &&java.util.Arrays.equals(actual.actual().originalPacket(),original.actual().originalPacket()),
                        "actual finalized pending successor frame changed inside the original writer lock");
                rerun=new LifecycleReducer.Reduction(token.publishedFinal().driver(),token.publishedFinal().auxiliary(),token.finalReduction().result());
            }else if(child.phase()==LifecycleChild.Phase.NEXT_EPISODE_COMMITTED){
                SeedStarted replacement=replacements.get(child.parentActionId());if(replacement==null)throw new IOException("private actual replacement session absent");games.requireCurrent(replacement);
                SeedArtifact seed=usedSeeds.get(child.parentActionId());if(seed==null)throw new IOException("private immutable seed absent");seed.requireCurrent(files);
                var retained=loadedFrames.get(child.parentActionId());if(retained==null)throw new IOException("actual seed map observation absent");
                var actual=games.observe(replacement,child.parent().deadline());requireLoadedScope(replacement,actual);ObjectNode state=LifecycleJson.parse(actual.state().bytes(),16<<20);JsonNodeCheck.checkSeed(state,seed);
                StrictJson.require(actual.nativeRevision().equals(retained.nativeRevision())&&actual.snapshotId().equals(retained.snapshotId()),"actual paused seed source frame changed before original writer commit");
                StrictJson.require(actual.session().machineId().equals(original.actual().session().machineId())
                        &&java.util.Arrays.equals(actual.state().bytes(),retained.state().bytes()),"actual seed state/machine drift inside original writer lock");
                requireCurrentTerminalStrategy(original.facts());
                rerun=LifecycleReducer.nextEpisode(original.facts(),seed,replacement.newGame().pid(),seed.characterId(),seed.dateRaw(),LifecycleJson.text(result.get("episode_run_id")),Instant.parse(LifecycleJson.text(result.get("observed_at"))));
            }else{
                games.requireOriginal(child.parent().origin().game());var actual=observations.current(child.parent(),child.parent().deadline());validateIdentityScope(child.parent(),actual);
                StrictJson.require(actual.actual().session().equals(original.actual().session())&&actual.facts().stamp().equals(original.facts().stamp())
                        &&actual.actual().snapshotId().equals(original.actual().snapshotId())&&actual.actual().nativeRevision().equals(original.actual().nativeRevision())
                        &&actual.semantic().equals(original.semantic()),"fresh actual source frame changed inside original writer lock");
                if(child.phase()==LifecycleChild.Phase.SUCCESSOR_COMMITTED){
                    naturalDigest=naturalSuccession.verify(child.parent(),actual,actualHead);WriterContracts.requireDigest(naturalDigest);
                    rerun=LifecycleReducer.continueSuccessor(actual,LifecycleJson.text(result.get("episode_run_id")),Instant.parse(LifecycleJson.text(result.get("observed_at"))));
                }
                if(child.phase()==LifecycleChild.Phase.DEATH_RECORDED){var inputs=deathInputs.get(child.parentActionId());if(inputs==null)throw new IOException("actual settlement/persistence producer absent");for(ExactRef ref:inputs.persistence.evidence()){var file=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("actual tutorial persistence disappeared"));StrictJson.require(file.reference().equals(ref),"settlement tutorial persistence changed");files.verify(file);}rerun=LifecycleReducer.death(actual,inputs.settlement,inputs.persistence,Instant.parse(LifecycleJson.text(result.get("observed_at"))));}
                if(child.phase()==LifecycleChild.Phase.NEXT_EPISODE_ENTERED){LifecycleReducer.requireScoredTerminal(actual.facts().driver());usedSeeds.get(child.parentActionId()).requireCurrent(files);}
            }
            if(rerun!=null)StrictJson.require(java.util.Arrays.equals(rerun.driver().encode(),child.replacement().encode())
                    &&rerun.auxiliary().equals(child.auxiliary())
                    &&LifecycleJson.same(LifecycleJson.parse(rerun.result(),LifecycleProofCodec.MAX_RESULT_BYTES),result),"shared lifecycle reducer changed between preview and actual original writer lock");
            if(child.phase()!=LifecycleChild.Phase.NEXT_EPISODE_ENTERED){
                ObjectNode delta=LifecycleJson.object(child.request().detailsObject().get("delta"));ExactRef beforeRef=ExactRef.fromJson(delta.get("original_driver_ref"));
                StrictJson.require(beforeRef.sha256().equals(child.expected().driverSha256())
                        &&ExactRef.fromJson(delta.get("original_native_ref")).equals(original.originalEvidence()),"actual original Driver/native source refs differ");
                var beforeFile=files.observe(Path.of(beforeRef.path())).orElseThrow(()->new IOException("actual original lifecycle Driver source disappeared"));
                StrictJson.require(beforeFile.reference().equals(beforeRef)&&java.util.Arrays.equals(files.read(beforeFile,org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES),original.facts().driver().encode()),"original lifecycle full Driver bytes differ");
            }
            ObjectNode checked=LifecycleJson.row();checked.put("original_native_sha256",original.originalEvidence().sha256());
            checked.put("actual_driver_before_sha256",original.facts().stamp().driverSha256());checked.put("actual_driver_after_sha256",LifecycleJson.sha(child.replacement().encode()));
            checked.put("child_identity",child.request().identity());if(naturalDigest!=null)checked.put("natural_succession_sha256",naturalDigest);
            return ContinuityJson.digest(checked);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("original locked lifecycle revalidation interrupted",interrupted);}
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution retained){
        LifecycleTransitionProof proof=finished.get(parent.actionId());if(proof!=null){
            proof.validateParent(parent);
            // Cold/current probes only restore private custody. Canonical Family imports belong
            // to this existing writable original-parent continuation, outside a physical read lease.
            if(proof instanceof LifecycleTransitionProof.ContinueSuccessor)try {
                var same=writer.current();var recovered=recoveredPending.get(parent.actionId());
                if(recovered!=null)initializeRecoveredNaturalFamily(same,recovered);
                else {
                    var warm=pendingPublications.get(parent.actionId());
                    if(warm==null)throw new IOException("actual natural publication custody is unavailable");
                    initializeNaturalFamily(same,warm);
                }
            }catch(IOException|RuntimeException failure){return new ActionPorts.Pending(
                    "actual natural Family domain publication remains unresolved; no lifecycle or native replay: "+failure.getMessage(),proof.originalEvidence());}
            return new ActionPorts.LifecycleObserved(proof);
        }
        PendingPublication pending=pendingPublications.get(parent.actionId());
        if(pending!=null){try{pending.proof().validateParent(parent);return publishRetained(pending);}
            catch(IOException|RuntimeException failure){return new ActionPorts.Pending("actual committed lifecycle Driver publication remains unresolved; no launch or child replay: "+failure.getMessage(),pending.proof().originalEvidence());}}
        PendingDomain domain=attemptedDomains.get(parent.actionId());
        if(domain!=null){try{
            var prepared=domain.child().prepared().orElseThrow(()->new IOException("original lifecycle preview was not retained; no reissue"));var borrowed=writer.current();
            var found=borrowed.queryCommitted(prepared);if(found.isEmpty())return new ActionPorts.Pending("original lifecycle event is not yet proven canonical; no commit replay",domain.evidence());
            borrowed.requireCommitted(prepared,found.orElseThrow());return retainCommitted(domain,new LifecycleCommit(prepared,found.orElseThrow(),borrowed.head().documents()));
        }catch(IOException|RuntimeException failure){return new ActionPorts.Pending("original lifecycle commit observation remains unresolved; no domain or native replay: "+failure.getMessage(),domain.evidence());}}
        if(enteredSeeds.containsKey(parent.actionId())&&!finalDomainAttempted.contains(parent.actionId())) {
            try{return completeKnownSeed(parent);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();return new ActionPorts.Pending("seed completion observation interrupted; original launch not replayed",evidence(parent.actionId()));}
            catch(IOException|RuntimeException failure){return new ActionPorts.Pending("read-only original seed reconciliation remains unresolved; no replacement replay: "+failure.getMessage(),evidence(parent.actionId()));}
        }
        // No Children, launch or seed-copy capability is supplied on reconciliation.
        return new ActionPorts.Pending("original lifecycle not yet durably proved; read/query existing resources only, never replay",evidence(parent.actionId()));
    }
    private ActionPorts.PostconditionResult completeKnownSeed(ActionCommand parent)throws IOException,InterruptedException {
        StrictJson.require(clock.instant().isBefore(parent.deadline()),"original lifecycle deadline expired; no new query or domain transition");
        EnteredSeed entered=enteredSeeds.get(parent.actionId());Objects.requireNonNull(entered);var borrowed=writer.current();
        borrowed.requireCommitted(entered.originalIntent().prepared(),entered.originalIntent().receipt());
        var registry=LifecycleJson.object(borrowed.head().state().toJson().get(LifecycleContinuityAuthority.STATE_FIELD));
        var original=LifecycleJson.object(LifecycleJson.object(registry.get("transitions")).get(parent.actionId()));
        StrictJson.require(LifecycleChild.Phase.NEXT_EPISODE_ENTERED.name().equals(LifecycleJson.text(original.get("phase")))
                &&ActionCodec.bodySha256(parent).equals(LifecycleJson.text(original.get("parent_body_sha256")))
                &&entered.launch().parentLifecycleIntentId().equals(LifecycleJson.text(LifecycleJson.object(original.get("delta")).get("lifecycle_intent_id"))),
                "original entered seed event is not the current surviving lifecycle intent");
        for(var pin:immutableCommitPins(entered.originalIntent())){StrictJson.require(borrowed.head().documents().contains(pin),"original durable seed intent event absent");recordedPins.requireCurrent(pin);}
        SeedReplacement outcome=games.query(entered.launch().parentLifecycleIntentId(),parent.deadline());
        if(!(outcome instanceof SeedStarted started))return new ActionPorts.Pending("original seed replacement is still unknown; query only",evidence(parent.actionId()));
        LifecycleObservationPort.Snapshot observed=Objects.requireNonNull(originalFrames.get(parent.actionId()));
        StrictJson.require(started.oldGame().equals(parent.origin().game())&&started.pipeName().equals(observed.facts().driver().session().pipeName()),"queried seed replacement crossed original process/pipe");
        SeedArtifact seed=entered.launch().seed();seed.requireCurrent(files);replacements.put(parent.actionId(),started);
        var loaded=awaitSeedMap(parent,started,seed);loadedFrames.put(parent.actionId(),loaded);usedSeeds.put(parent.actionId(),seed);
        requireCurrentTerminalStrategy(observed.facts());
        var reduction=LifecycleReducer.nextEpisode(observed.facts(),seed,started.newGame().pid(),seed.characterId(),seed.dateRaw(),newRun(seed.characterId()),clock.instant());
        finalDomainAttempted.add(parent.actionId());
        return finish(parent,child->{var actual=writer.current();var prepared=actual.preview(child.request());child.rememberPrepared(prepared);var receipt=actual.commit(prepared);
            return new LifecycleCommit(prepared,receipt,actual.head().documents());},observed,LifecycleChild.Phase.NEXT_EPISODE_COMMITTED,reduction,started.newGame(),
            List.of(seed.save().reference(),seed.metadata().reference(),started.launchEvidence(),started.helloEvidence(),started.lifecycleEvidence(),publish(parent.actionId(),loaded.originalPacket())));
    }
    private ActionPorts.PostconditionResult publishRetained(PendingPublication pending)throws IOException {
        var borrowed=writer.current();verifyRecorded(pending.parent(),pending.proof(),borrowed.head());
        var child=pending.child();var committed=pending.committed();
        // This same original commit may now be an immutable ancestor of a later UNKNOWN parent event.
        // The sole assembler validates that canonical event and performs an idempotent after-state CAS.
        drivers().publishCommitted(borrowed,child.expected(),child.replacement(),child.auxiliary(),committed.prepared(),committed.receipt());
        initializeNaturalFamily(borrowed,pending);
        finished.put(pending.parent().actionId(),pending.proof());return new ActionPorts.LifecycleObserved(pending.proof());
    }
    private void initializeNaturalFamily(ContinuityStorePort.Session same,PendingPublication pending)throws IOException {
        if(!(pending.proof() instanceof LifecycleTransitionProof.ContinueSuccessor))return;
        CommittedNatural natural=committedNaturals.get(pending.parent().actionId());
        if(natural==null) {
            StrictJson.require(pending.child().phase()==LifecycleChild.Phase.SUCCESSOR_COMMITTED
                    ||pending.child().phase()==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED,
                    "natural Family publication requires the actual successor branch");
            StrictJson.require(GameGeneration.fromJson(pending.child().request().detailsObject().get("driver_after_game"))
                    .equals(pending.parent().lifecycleBefore().game()),"natural Family publication cannot initialize another physical Game");
            var pins=immutableCommitPins(pending.committed());
            StrictJson.require(pins.size()==1,"one original canonical natural lifecycle event required");
            natural=new CommittedNatural(this,pending,pins.getFirst().reference());
            committedNaturals.put(pending.parent().actionId(),natural);
        }
        applyNaturalFamily(same,natural);
    }
    private void initializeRecoveredNaturalFamily(ContinuityStorePort.Session same,RecoveredPending recovered)throws IOException {
        var id=recovered.edge.parent().command().actionId();var natural=committedNaturals.get(id);
        if(natural==null){natural=new CommittedNatural(this,recovered);committedNaturals.put(id,natural);}
        applyNaturalFamily(same,natural);
    }
    private void applyNaturalFamily(ContinuityStorePort.Session same,CommittedNatural natural)throws IOException {
        NaturalFamilyMigration actual;
        synchronized(this){actual=naturalFamilyMigrations.get(natural.owner());}
        if(actual==null)throw new IOException("actual registered natural Family producer is not bound for this physical owner");
        natural.requireCurrent(same);actual.initialize(same,natural);natural.requireCurrent(same);
    }
    private void requireCurrentNatural(ContinuityStorePort.Session same,CommittedNatural actual)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(actual);
        StrictJson.require(actual.issuer==this&&writer.current()==same
                &&committedNaturals.get(actual.parent().actionId())==actual,
                "natural Family input belongs to another actual lifecycle/writer");
        if(actual.recovered!=null) {
            var recovered=actual.recovered;var edge=recovered.edge;
            StrictJson.require(recoveredPending.get(actual.parent().actionId())==recovered,
                    "natural Family input lost its actual privately recovered successor source");
            requireRecordedPending(same,edge);
            var canonical=canonicalParent(same,actual.parent());recovered.proof.validateParent(canonical.command());
            if(!(naturalPreparation instanceof NaturalSuccessionContinuationSource source))
                throw new IOException("actual private retained natural source is not installed");
            source.requireCommittedPendingEpisode(canonical,same,edge);requireRecordedPublishedDriver(same,edge);
            StrictJson.require(GameGeneration.fromJson(edge.publication().detailsObject().get("driver_after_game")).equals(actual.owner().game()),
                    "recovered natural Family input crossed its actual physical Game");
            same.verifyPin(edge.eventPin());return;
        }
        var pending=actual.publication;var child=pending.child();
        StrictJson.require(pendingPublications.get(pending.parent().actionId())==pending
                &&pending.proof() instanceof LifecycleTransitionProof.ContinueSuccessor,
                "natural Family input is not this lifecycle's actual private successor publication");
        same.requireCommitted(pending.committed().prepared(),pending.committed().receipt());
        verifyRecorded(pending.parent(),pending.proof(),same.head());
        StrictJson.require(immutableCommitPins(pending.committed()).stream()
                .anyMatch(pin->pin.reference().equals(actual.lifecycleMaterial)),"natural Family material is not the actual canonical lifecycle event");
        drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual published natural Driver unavailable");
            var known=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(java.util.Arrays.equals(known.driver().encode(),child.replacement().encode())
                    &&known.stamp().driverVersion()>child.expected().driverVersion()
                    &&known.stamp().episodeEpoch()==LifecycleJson.integer(child.request().detailsObject().get("driver_snapshot").get("next_epoch"),BigInteger.ZERO).longValueExact()
                    &&known.stamp().game().equals(actual.owner().game()),
                    "natural Family migration lost the actual published complete Driver/Game/episode");
            return null;
        });
    }
    /** Read-only custody for a canonical UNKNOWN parent after its real domain/Driver publication.
     * The original identity is historical reconciliation scope, never authority for a new command. */
    public Optional<LifecycleIdentity> retainedReconciliation(ContinuityStorePort.Session borrowed,ActionReceipt actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(writer.current()==borrowed,"retained lifecycle observation must use the exact original Session");
        if(actual.settled()||!(actual.command().origin() instanceof CommandOrigin.LifecycleTerminal))return Optional.empty();
        PendingPublication pending=pendingPublications.get(actual.command().actionId());if(pending==null)return Optional.empty();
        StrictJson.require(ActionCodec.bodySha256(pending.parent()).equals(actual.bodySha256()),"retained parent differs from canonical original command");
        borrowed.requireCommitted(pending.committed().prepared(),pending.committed().receipt());verifyRecorded(actual.command(),pending.proof(),borrowed.head());
        drivers().withFrozenFacts(borrowed,frozen->{
            StrictJson.require(frozen.actions().actions().stream().anyMatch(row->row.command().actionId().equals(actual.command().actionId())
                    &&row.sequence()==actual.sequence()&&row.bodySha256().equals(actual.bodySha256())&&!row.settled()),"original unresolved parent is not the current canonical receipt");
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"retained lifecycle complete Driver unavailable");
            var known=(DriverSnapshotFacts.Known)frozen.state();var child=pending.child();
            boolean before=known.stamp().equals(child.expected());
            var details=child.request().detailsObject();var delta=LifecycleJson.object(details.get("driver_snapshot"));
            boolean after=known.stamp().driverVersion()==Math.addExact(child.expected().driverVersion(),1)
                    &&known.stamp().episodeEpoch()==LifecycleJson.integer(delta.get("next_epoch"),BigInteger.ZERO).longValueExact()
                    &&known.stamp().game().equals(GameGeneration.fromJson(details.get("driver_after_game")))
                    &&java.util.Arrays.equals(known.driver().encode(),child.replacement().encode());
            StrictJson.require(before||after,"retained lifecycle original no longer owns the actual before/after complete Driver");return null;
        });
        return Optional.of(actual.command().lifecycleBefore());
    }
    /** Read-only retrieval for M7. A decoded Recorded proof never recreates this service's private episode authority. */
    public LifecycleTransitionProof.Base requireCommittedEpisode(ContinuityStorePort.Session borrowed,ActionReceipt actual)throws IOException {
        Objects.requireNonNull(borrowed);Objects.requireNonNull(actual);
        StrictJson.require(writer.current()==borrowed,"episode proof must borrow this service's exact current original writer Session");
        LifecycleTransitionProof proof=finished.get(actual.command().actionId());
        if(recoveredPending.containsKey(actual.command().actionId()))return requireRecoveredEpisode(borrowed,actual,true);
        StrictJson.require(proof instanceof LifecycleTransitionProof.ContinueSuccessor||proof instanceof LifecycleTransitionProof.NextEpisode,
                "no privately minted and fully published episode transition exists");
        proof.validateParent(actual.command());
        StrictJson.require(actual.state() instanceof ActionState.CompositeSettled composite&&composite.settlement() instanceof ActionState.LifecycleApplied applied
                &&java.util.Arrays.equals(applied.proof().encode(),proof.encode()),"actual canonical parent does not carry the same recorded lifecycle proof");
        verifyRecorded(actual.command(),proof,borrowed.head());PendingPublication publication=pendingPublications.get(actual.command().actionId());
        StrictJson.require(publication!=null&&publication.proof()==proof,"original lifecycle publication custody unavailable");
        drivers().withFrozenFacts(borrowed,frozen->{
            StrictJson.require(frozen.actions().headSha256().equals(borrowed.head().digest())
                    &&frozen.actions().actions().stream().anyMatch(receipt->receipt.equals(actual)),"episode parent receipt is not in the actual canonical action snapshot");
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual complete published episode Driver unavailable");
            var known=(DriverSnapshotFacts.Known)frozen.state();var child=publication.child();
            StrictJson.require(java.util.Arrays.equals(known.driver().encode(),child.replacement().encode())
                    &&known.stamp().driverVersion()>child.expected().driverVersion()
                    &&known.stamp().episodeEpoch()==LifecycleJson.integer(child.request().detailsObject().get("driver_snapshot").get("next_epoch"),BigInteger.ZERO).longValueExact()
                    &&known.stamp().game().equals(GameGeneration.fromJson(child.request().detailsObject().get("driver_after_game"))),
                    "private episode proof is stale or its complete Driver/Game was never published");return null;
        });
        return (LifecycleTransitionProof.Base)proof;
    }
    /** Historical private lifecycle custody after a genuine SAVE advanced the complete Driver.
     * This proves only the original published episode. A caller must independently prove the exact
     * first-SAVE projection before using a later Driver; it is not current episode authority. */
    public LifecycleTransitionProof.Base requireRetainedEpisode(ContinuityStorePort.Session borrowed,ActionReceipt actual,
            LifecycleTransitionProof.Base expectedPrivateProof)throws IOException {
        Objects.requireNonNull(expectedPrivateProof);Objects.requireNonNull(actual);
        StrictJson.require(writer.current()==borrowed,"retained episode must borrow the same original writer Session");
        var proof=finished.get(actual.command().actionId());
        if(recoveredPending.containsKey(actual.command().actionId())){
            var recovered=requireRecoveredEpisode(borrowed,actual,false);
            StrictJson.require(recovered==expectedPrivateProof,"retained cold episode requires its identical private issuer proof");return recovered;
        }
        StrictJson.require(proof==expectedPrivateProof&&(proof instanceof LifecycleTransitionProof.NextEpisode||proof instanceof LifecycleTransitionProof.ContinueSuccessor),
                "retained episode requires its original private issuer object");
        proof.validateParent(actual.command());
        StrictJson.require(actual.state() instanceof ActionState.CompositeSettled composite&&composite.settlement() instanceof ActionState.LifecycleApplied applied
                &&java.util.Arrays.equals(applied.proof().encode(),proof.encode()),"retained canonical parent differs from private lifecycle proof");
        verifyRecorded(actual.command(),proof,borrowed.head());
        var publication=pendingPublications.get(actual.command().actionId());
        StrictJson.require(publication!=null&&publication.proof()==proof,"retained episode original publication is unavailable");
        borrowed.requireCommitted(publication.committed().prepared(),publication.committed().receipt());
        ExactRef adopted=ExactRef.fromJson(publication.child().request().detailsObject().get("delta").get("adopted_driver_ref"));
        var pin=publication.committed().committedDocuments().stream().filter(item->item.reference().equals(adopted)).findFirst()
                .orElseThrow(()->new IOException("retained adopted Driver original identity pin unavailable"));
        byte[] original=borrowed.readPinned(pin,retainedDriverBound(pin.reference()));borrowed.verifyPin(pin);
        StrictJson.require(java.util.Arrays.equals(original,publication.child().replacement().encode())
                &&publication.committed().prepared().request().evidence().contains(adopted)&&proof.originalEvidence().contains(adopted),
                "retained episode original complete Driver differs from canonical publication");
        drivers().withFrozenFacts(borrowed,frozen->{
            StrictJson.require(frozen.actions().headSha256().equals(borrowed.head().digest())
                    &&frozen.actions().actions().stream().anyMatch(actual::equals),"retained episode parent is absent from the canonical action snapshot");return null;
        });
        return (LifecycleTransitionProof.Base)proof;
    }
    /** Canonical historical DATA, distinct from a private M3 qualification or episode grant. */
    public static final class RecordedPendingEpisode {
        private final LifecycleComposites issuer;
        private final ActionReceipt parent;
        private final LifecycleTransitionProof.Recorded proof;
        private final LifecyclePublication.RecordedEvent publication;
        private final LifecyclePendingOriginals originals;
        private final OpportunityJson.Obj beforeAuxiliary;
        private final org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete beforeDriver,afterDriver;
        private RecordedPendingEpisode(LifecycleComposites issuer,ActionReceipt parent,LifecycleTransitionProof.Recorded proof,
                LifecyclePublication.RecordedEvent publication,LifecyclePendingOriginals originals,OpportunityJson.Obj beforeAuxiliary,
                org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete beforeDriver,
                org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete afterDriver) {
            this.issuer=issuer;this.parent=parent;this.proof=proof;this.publication=publication;this.originals=originals;
            this.beforeDriver=beforeDriver;this.afterDriver=afterDriver;this.beforeAuxiliary=beforeAuxiliary;
        }
        public ActionReceipt parent(){return parent;}
        public LifecycleTransitionProof.Recorded proof(){return proof;}
        public WriterContracts.Pin eventPin(){return publication.committedDocuments().getFirst();}
        public LifecyclePublication.RecordedEvent publication(){return publication;}
        public OpportunityJson.Obj beforeAuxiliary(){return beforeAuxiliary;}
        public ExactRef beforeKnownOriginal(){return originals.beforeKnownPin().reference();}
        public ExactRef beforeNativeOriginal(){return ExactRef.fromJson(publication.detailsObject().get("delta").get("original_native_ref"));}
        public org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete beforeDriver(){return beforeDriver;}
        public org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete afterDriver(){return afterDriver;}
        /** Reopens actual originals and the sole pure projection; this grants no episode authority. */
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException{issuer.requireRecordedPending(same,this);}
        /** Verifies actual post-metadata publication DATA; it grants no retained M3 or episode authority. */
        public void requirePublishedCurrent(ContinuityStorePort.Session same)throws IOException{
            requireCurrent(same);issuer.requireRecordedPublishedDriver(same,this);
        }
    }
    public RecordedPendingEpisode recordedPendingEpisode(ContinuityStorePort.Session same,ActionReceipt actualParent)throws IOException {
        StrictJson.require(writer.current()==same,"recorded pending episode must use the exact original writer Session");
        ActionCommand parent=actualParent.command();
        StrictJson.require(parent.operation().value().equals("continue-as-reconciled-successor")
                &&(actualParent.state() instanceof ActionState.CompositeUnknown
                ||actualParent.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied),
                "only the actual retained Continue parent can reopen its final metadata edge");
        requireCanonicalParent(same,actualParent);
        var head=same.head();var registry=LifecycleJson.object(head.state().toJson().get(LifecycleContinuityAuthority.STATE_FIELD));
        var details=LifecycleJson.object(LifecycleJson.object(registry.get("transitions")).get(parent.actionId()));
        StrictJson.require(LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(LifecycleJson.text(details.get("phase"))),
                "cold episode recovery requires the explicit final pending metadata phase");
        var delta=LifecycleJson.object(details.get("delta"));
        if(!delta.has("pending_episode_originals"))throw new IOException("historical hash-only pending lifecycle has no original auxiliary/source pins");
        var inputPin=LifecycleProofCodec.decodePin(delta.get("pending_episode_originals"));
        var originals=LifecyclePendingOriginals.decode(same.readPinned(inputPin,LifecyclePendingOriginals.MAXIMUM_BYTES));same.verifyPin(inputPin);
        var beforeAuxiliary=org.xar.ck3.control.application.driver.DriverJson.object(
                same.readPinned(originals.beforeAuxiliaryPin(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);same.verifyPin(originals.beforeAuxiliaryPin());
        StrictJson.require(originals.originals().contains(originals.beforeAuxiliaryPin()),"original auxiliary FileID must be retained in the exact lifecycle evidence closure");
        StrictJson.require(originals.originals().contains(originals.beforeKnownPin()),"original Known FileID must be retained in the exact lifecycle evidence closure");
        DriverSnapshotFacts.originalKnownJson(same.readPinned(originals.beforeKnownPin(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES));same.verifyPin(originals.beforeKnownPin());
        var before=same.requireHistoricalState(originals.beforeSequence(),originals.beforeDigest());
        long sequence=Math.addExact(originals.beforeSequence(),1);
        String name=String.format(java.util.Locale.ROOT,"%08d.json",sequence);
        var eventPin=head.documents().stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(name))
                .findFirst().orElseThrow(()->new IOException("original final lifecycle event is absent from the canonical chain"));
        var event=same.readHistoricalTransition(eventPin);
        StrictJson.require(event.sequence()==sequence&&event.kind().equals(LifecycleChild.KIND)
                &&LifecycleJson.same(LifecycleJson.parse(event.details(),ContinuityJson.DOCUMENT_MAX_BYTES),details)
                &&ContinuityJson.same(event.before().toJson(),before.toJson()),"actual historical lifecycle event differs from its saved original inputs");
        var evidence=new ArrayList<ExactRef>();originals.originals().forEach(pin->evidence.add(pin.reference()));evidence.add(inputPin.reference());
        var request=new WriterContracts.Request(event.kind(),event.details(),evidence);
        StrictJson.require(request.identity().equals(event.eventIdentity()),"actual historical lifecycle request identity differs");
        var pins=new java.util.LinkedHashSet<WriterContracts.Pin>();pins.add(eventPin);pins.addAll(originals.sources());pins.addAll(originals.originals());pins.add(inputPin);
        for(var pin:pins)same.verifyPin(pin);
        var beforeRef=ExactRef.fromJson(delta.get("original_driver_ref"));var afterRef=ExactRef.fromJson(delta.get("adopted_driver_ref"));
        var beforeDriver=readRecordedDriver(same,pins,beforeRef);var afterDriver=readRecordedDriver(same,pins,afterRef);
        var stamp=LifecycleJson.object(details.get("driver_snapshot"));
        StrictJson.require(beforeRef.sha256().equals(LifecycleJson.text(stamp.get("before_sha256")))
                &&afterRef.sha256().equals(LifecycleJson.text(stamp.get("after_sha256")))
                &&java.util.Arrays.equals(beforeDriver.encode(),afterDriver.encode())
                &&LifecycleJson.sha(org.xar.ck3.control.application.driver.DriverJson.encode(beforeAuxiliary))
                    .equals(LifecycleJson.text(stamp.get("auxiliary_after_sha256"))),
                "recorded final metadata must preserve its actual complete Driver and original auxiliary");
        var projected=LifecycleContinuityAuthority.project(before,request,afterDriver).toJson();
        projected.put("sequence",sequence);projected.put("last_event_identity",event.eventIdentity());
        StrictJson.require(ContinuityJson.same(projected,event.after().toJson()),"sole lifecycle reducer does not reproduce the exact canonical historical after state");
        evidence.add(eventPin.reference());
        var proof=new LifecycleTransitionProof.Recorded(LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,parent.actionId(),
                ActionCodec.bodySha256(parent),parent.operation().value(),event.eventIdentity(),List.copyOf(pins),evidence,
                LifecycleJson.bytes(LifecycleJson.object(delta.get("result"))));
        verifyRecorded(parent,proof,head);
        StrictJson.require(head.digest().equals(same.head().digest()),"recorded lifecycle read changed the original canonical head");
        var publication=new LifecyclePublication.RecordedEvent(request,event.before(),event.after(),eventPin,List.copyOf(pins));
        return new RecordedPendingEpisode(this,actualParent,proof,publication,originals,beforeAuxiliary,beforeDriver,afterDriver);
    }
    /** Preserve the named full Driver role while giving the storage port the exact finite original size.
     * An original above that port's physical pin ceiling remains unavailable; this does not enlarge Native limits. */
    private static int retainedDriverBound(ExactRef reference) {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES,
                "bounded original full Driver/material role required");
        return Math.toIntExact(reference.bytes());
    }
    private static org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete readRecordedDriver(
            ContinuityStorePort.Session same,java.util.Set<WriterContracts.Pin> originals,ExactRef ref)throws IOException {
        var pin=originals.stream().filter(value->value.reference().equals(ref)).findFirst()
                .orElseThrow(()->new IOException("original complete Driver FileID pin is absent"));
        var result=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                same.readPinned(pin,retainedDriverBound(pin.reference())));
        same.verifyPin(pin);return result;
    }
    private void requireCanonicalParent(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException {
        drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.actions().headSha256().equals(same.head().digest())
                    &&frozen.actions().actions().stream().anyMatch(actual::equals),"actual retained lifecycle parent is absent from the canonical action snapshot");return null;
        });
    }
    private ActionReceipt canonicalParent(ContinuityStorePort.Session same,ActionCommand original)throws IOException {
        return drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.actions().headSha256().equals(same.head().digest()),"canonical action snapshot changed");
            return frozen.actions().actions().stream().filter(row->java.util.Arrays.equals(ActionCodec.encodeCommand(row.command()),ActionCodec.encodeCommand(original)))
                    .findFirst().orElseThrow(()->new IOException("actual original parent command is absent"));
        });
    }
    private void requireRecordedPending(ContinuityStorePort.Session same,RecordedPendingEpisode exact)throws IOException {
        StrictJson.require(exact.issuer==this,"recorded pending edge belongs to another actual lifecycle reader");
        var current=recordedPendingEpisode(same,canonicalParent(same,exact.parent.command()));
        StrictJson.require(java.util.Arrays.equals(current.proof.encode(),exact.proof.encode())
                &&current.publication.eventIdentity().equals(exact.publication.eventIdentity())
                &&current.beforeAuxiliary().equals(exact.beforeAuxiliary()),"recorded pending originals changed");
    }
    /** Only the actual registered Root/M3 private source may reissue the completed episode proof. No publication or commit occurs. */
    public LifecycleTransitionProof.ContinueSuccessor recoverCommittedPendingEpisode(ContinuityStorePort.Session same,
            ActionReceipt actualParent,RecordedPendingEpisode exact)throws IOException {
        StrictJson.require(writer.current()==same&&exact.issuer==this,"cold episode requires the actual original lifecycle reader and writer");
        requireRecordedPending(same,exact);requireCanonicalParent(same,actualParent);
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(actualParent.command()),ActionCodec.encodeCommand(exact.parent.command())),
                "cold episode crossed its original complete Continue command");
        if(!(naturalPreparation instanceof NaturalSuccessionContinuationSource source))throw new IOException("actual private retained natural source is not installed");
        source.requireCommittedPendingEpisode(actualParent,same,exact);
        var warm=pendingPublications.get(actualParent.command().actionId());
        if(warm!=null){
            StrictJson.require(warm.child().phase()==LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED
                    &&warm.proof() instanceof LifecycleTransitionProof.ContinueSuccessor
                    &&java.util.Arrays.equals(warm.proof().encode(),exact.proof.encode()),"actual original warm publication differs from the retained canonical metadata edge");
            same.requireCommitted(warm.committed().prepared(),warm.committed().receipt());requireRecordedPublishedDriver(same,exact);
            source.requireCommittedPendingEpisode(actualParent,same,exact);requireRecordedPending(same,exact);
            StrictJson.require(!finished.containsKey(actualParent.command().actionId())||finished.get(actualParent.command().actionId())==warm.proof(),
                    "another actual private proof already owns the original warm parent");
            StrictJson.require(committedWarmObservations.size()<16384||committedWarmObservations.containsKey(actualParent.command().actionId()),
                    "finite actual warm completed-observation registry is exhausted");
            finished.put(actualParent.command().actionId(),warm.proof());committedWarmObservations.put(actualParent.command().actionId(),exact);
            return (LifecycleTransitionProof.ContinueSuccessor)warm.proof();
        }
        var prior=recoveredPending.get(actualParent.command().actionId());
        if(prior!=null){StrictJson.require(java.util.Arrays.equals(prior.edge.proof.encode(),exact.proof.encode()),"private recovered publication changed");return prior.proof;}
        StrictJson.require(!finished.containsKey(actualParent.command().actionId())&&!pendingPublications.containsKey(actualParent.command().actionId()),
                "a genuine warm lifecycle already owns this original parent");
        StrictJson.require(recoveredPending.size()<16384,"finite actual recovered lifecycle registry is exhausted");
        requireRecordedPublishedDriver(same,exact);
        var proof=new LifecycleTransitionProof.ContinueSuccessor(this,actualParent.command(),exact.publication,
                exact.proof.originalEvidence(),exact.proof.encodedResult());proof.validateParent(actualParent.command());
        source.requireCommittedPendingEpisode(actualParent,same,exact);requireRecordedPending(same,exact);
        recoveredPending.put(actualParent.command().actionId(),new RecoveredPending(exact,proof));finished.put(actualParent.command().actionId(),proof);return proof;
    }
    private void requireRecordedPublishedDriver(ContinuityStorePort.Session same,RecordedPendingEpisode exact)throws IOException {
        var details=exact.publication.detailsObject();var stamp=LifecycleJson.object(details.get("driver_snapshot"));
        // This receipt is original historical DATA, never a Prepared or a commit request.
        var historical=new WriterContracts.Receipt(WriterContracts.Disposition.ALREADY_COMMITTED,
                exact.publication.after(),exact.publication.eventIdentity(),0,true);
        var request=new WriterContracts.Request(LifecycleChild.KIND,LifecycleJson.bytes(details),exact.originals.originals().stream().map(WriterContracts.Pin::reference).toList());
        var auxiliary=DriverStateAssembler.lifecyclePublishedAuxiliary(exact.beforeAuxiliary(),request,historical);
        drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual post-metadata complete Driver is unavailable");
            var known=(DriverSnapshotFacts.Known)frozen.state();
            StrictJson.require(java.util.Arrays.equals(known.driver().encode(),exact.afterDriver.encode())
                    &&known.auxiliary().equals(auxiliary)
                    &&known.stamp().driverVersion()==Math.addExact(LifecycleJson.integer(stamp.get("expected_version"),BigInteger.ZERO).longValueExact(),1)
                    &&known.stamp().episodeEpoch()==LifecycleJson.integer(stamp.get("next_epoch"),BigInteger.ZERO).longValueExact()
                    &&known.stamp().game().equals(GameGeneration.fromJson(details.get("driver_after_game"))),
                    "canonical final metadata was not actually published into this current Driver owner");return null;
        });
    }
    private LifecycleTransitionProof.ContinueSuccessor requireRecoveredEpisode(ContinuityStorePort.Session same,ActionReceipt actual,
            boolean currentDriver)throws IOException {
        var retained=recoveredPending.get(actual.command().actionId());StrictJson.require(retained!=null&&finished.get(actual.command().actionId())==retained.proof,
                "private recovered episode custody is absent");
        retained.proof.validateParent(actual.command());requireCanonicalParent(same,actual);requireRecordedPending(same,retained.edge);
        StrictJson.require(actual.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied
                &&java.util.Arrays.equals(applied.proof().encode(),retained.proof.encode()),"canonical parent does not carry the identical recovered episode proof");
        if(currentDriver){((NaturalSuccessionContinuationSource)naturalPreparation).requireCommittedPendingEpisode(actual,same,retained.edge);
            requireRecordedPublishedDriver(same,retained.edge);}
        return retained.proof;
    }
    /** Actual one-replacement custody for Root to transfer the existing owner into a new per-Game graph. */
    public static final class NextEpisodeAdoption {
        private final LifecycleComposites issuer;private final SeedStarted replacement;
        private final ActionReceipt parent;private final LifecycleTransitionProof.NextEpisode proof;
        private final DriverSnapshotFacts.Known published;private final ExactRef driver;
        private final NativeObservationPort.ObservedFrame loaded;
        private final DriverSnapshotFacts.Known originalParent;
        private NextEpisodeAdoption(LifecycleComposites issuer,SeedStarted replacement,ActionReceipt parent,
                LifecycleTransitionProof.NextEpisode proof,DriverSnapshotFacts.Known published,ExactRef driver,
                NativeObservationPort.ObservedFrame loaded,DriverSnapshotFacts.Known originalParent){
            this.issuer=issuer;this.replacement=replacement;this.parent=parent;this.proof=proof;this.published=published;this.driver=driver;this.loaded=loaded;this.originalParent=originalParent;
        }
        public SeedStarted replacement(){return replacement;}
        public ActionReceipt parent(){return parent;}
        public LifecycleTransitionProof.NextEpisode proof(){return proof;}
        public LifecycleCommit commit(){return proof.commit();}
        public DriverSnapshotFacts.Known published(){return published;}
        public ExactRef driverReference(){return driver;}
        public NativeObservationPort.ObservedFrame loadedObservation(){return loaded;}
        /** The actual original terminal facts instance, retained for old-owner presentation only. */
        public DriverSnapshotFacts.Known originalParentFacts(){return originalParent;}
        /** Exact issuer, actual canonical parent and real physical replacement are rechecked, never relaunched. */
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException{issuer.requireNextAdoption(same,this);}
    }
    public NextEpisodeAdoption requireNextEpisodeAdoption(ContinuityStorePort.Session same,ActionReceipt parent)throws IOException {
        var actual=requireCommittedEpisode(same,parent);
        StrictJson.require(actual instanceof LifecycleTransitionProof.NextEpisode,"actual committed next-episode branch required");
        var proof=(LifecycleTransitionProof.NextEpisode)actual;var started=replacements.get(parent.command().actionId());
        StrictJson.require(started!=null&&started.oldGame().equals(parent.command().origin().game()),"original private replacement custody missing");
        games.requireCurrent(started);var publication=pendingPublications.get(parent.command().actionId());
        ExactRef ref=ExactRef.fromJson(publication.child().request().detailsObject().get("delta").get("adopted_driver_ref"));
        var pin=publication.committed().committedDocuments().stream().filter(item->item.reference().equals(ref)).findFirst()
                .orElseThrow(()->new IOException("actual adopted Driver original identity pin unavailable"));
        byte[] raw=same.readPinned(pin,retainedDriverBound(pin.reference()));same.verifyPin(pin);
        StrictJson.require(java.util.Arrays.equals(raw,publication.child().replacement().encode())
                &&publication.committed().prepared().request().evidence().contains(ref)
                &&proof.originalEvidence().contains(ref),"next episode lacks its actual committed full-Driver original");
        var known=drivers().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"next episode full published Driver missing");
            return (DriverSnapshotFacts.Known)frozen.state();
        });
        StrictJson.require(known.stamp().game().equals(started.newGame())&&known.driver().session().bridgePid()==started.newGame().pid()
                &&known.driver().session().pipeName().equals(started.pipeName()),"published next episode belongs to another actual replacement transport");
        var loaded=loadedFrames.get(parent.command().actionId());
        StrictJson.require(loaded!=null&&loaded.session().game().equals(started.newGame())&&loaded.session().sessionId().equals(started.sessionId()),
                "private original loaded native observation unavailable");
        ExactRef nativeRef=ExactRef.fromJson(publication.child().request().detailsObject().get("delta").get("loaded_native_ref"));
        var nativePin=publication.committed().committedDocuments().stream().filter(item->item.reference().equals(nativeRef)).findFirst()
                .orElseThrow(()->new IOException("actual loaded native original identity pin unavailable"));
        StrictJson.require(java.util.Arrays.equals(same.readPinned(nativePin,org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES+4),loaded.originalPacket())
                &&proof.originalEvidence().contains(nativeRef),"private loaded observation differs from actual canonical NEXT native original");same.verifyPin(nativePin);
        var originalFrame=originalFrames.get(parent.command().actionId());
        StrictJson.require(originalFrame!=null,"actual original NEXT terminal frame custody unavailable");
        var originalParent=originalFrame.facts();var parentDriver=parent.command().lifecycleBefore().evidence().originalDriver();
        ExactRef originalRef=ExactRef.fromJson(publication.child().request().detailsObject().get("delta").get("original_driver_ref"));
        StrictJson.require(parentDriver.equals(originalRef)&&originalParent.stamp().game().equals(started.oldGame())
                &&originalParent.driver().encode().length==parentDriver.bytes()
                &&org.xar.ck3.control.application.action.ActionCodec.sha256(originalParent.driver().encode()).equals(parentDriver.sha256()),
                "actual original NEXT parent full Driver identity differs from canonical terminal source");
        var originalPin=publication.committed().committedDocuments().stream().filter(item->item.reference().equals(originalRef)).findFirst()
                .orElseThrow(()->new IOException("original NEXT parent Driver identity pin unavailable"));
        StrictJson.require(java.util.Arrays.equals(same.readPinned(originalPin,retainedDriverBound(originalPin.reference())),originalParent.driver().encode()),
                "original NEXT parent complete Driver bytes differ");same.verifyPin(originalPin);
        return new NextEpisodeAdoption(this,started,parent,proof,known,ref,loaded,originalParent);
    }
    private void requireNextAdoption(ContinuityStorePort.Session same,NextEpisodeAdoption binding)throws IOException {
        StrictJson.require(binding.issuer==this,"foreign next episode adoption issuer");
        var actual=requireNextEpisodeAdoption(same,binding.parent);
        StrictJson.require(actual.replacement==binding.replacement&&actual.proof==binding.proof
                &&actual.loaded==binding.loaded
                &&actual.originalParent==binding.originalParent
                &&actual.driver.equals(binding.driver)&&actual.published.stamp().equals(binding.published.stamp())
                &&java.util.Arrays.equals(actual.published.driver().encode(),binding.published.driver().encode())
                &&actual.published.auxiliary().equals(binding.published.auxiliary()),"next episode actual owner/fullDriver publication changed");
    }
    /** Historical DATA only. It carries no private NextEpisodeAdoption or permission for another Game. */
    public static final class ArchivedNextOrigins {
        private final ActionReceipt parent;private final LifecycleTransitionProof.Recorded proof;
        private final org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete predecessor;
        private final org.xar.ck3.control.application.session.SessionPorts.SessionIdentity before,saved;
        private ArchivedNextOrigins(ActionReceipt parent,LifecycleTransitionProof.Recorded proof,
                org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete predecessor,
                org.xar.ck3.control.application.session.SessionPorts.SessionIdentity before,
                org.xar.ck3.control.application.session.SessionPorts.SessionIdentity saved){
            this.parent=parent;this.proof=proof;this.predecessor=predecessor;this.before=before;this.saved=saved;
        }
        public ActionReceipt parent(){return parent;}
        public LifecycleTransitionProof.Recorded proof(){return proof;}
        public org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete predecessorDriver(){return predecessor;}
        public org.xar.ck3.control.application.session.SessionPorts.SessionIdentity beforeSession(){return before;}
        /** The original FIRST SAVE session, never the current RESTORED replacement session. */
        public org.xar.ck3.control.application.session.SessionPorts.SessionIdentity savedSession(){return saved;}
    }
    /** Root obtains actualCanonicalParent from its same-writer ActionSnapshotReader before calling this readonly reader. */
    public ArchivedNextOrigins archivedNextOrigins(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore.BaselinedMaterial material,
            ActionReceipt actualCanonicalParent)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(material);Objects.requireNonNull(actualCanonicalParent);
        StrictJson.require(writer.current()==same,"archived NEXT origins require the actual original writer Session");
        String initial=same.head().digest();material.requireRetained(same);
        var first=material.firstMaterial().checkpoint();var begin=first.begin().begin();var before=begin.before();var saved=begin.after();
        var parent=actualCanonicalParent.command();
        StrictJson.require(parent.origin() instanceof CommandOrigin.LifecycleTerminal&&parent.operation().value().equals("start-next-episode")
                &&actualCanonicalParent.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&parent.actionId().equals(begin.parentActionId())&&parent.origin().machineId().equals(before.machineId())
                &&parent.origin().game().equals(before.game())&&parent.sessionId().equals(before.sessionId()),
                "first BASELINE must retain its exact original canonical NEXT parent and prior full Game/session");
        StrictJson.require(actualCanonicalParent.state() instanceof ActionState.CompositeSettled composite
                &&composite.settlement() instanceof ActionState.LifecycleApplied,"actual NEXT parent has no recorded lifecycle settlement");
        var applied=(ActionState.LifecycleApplied)((ActionState.CompositeSettled)actualCanonicalParent.state()).settlement();
        var recorded=(LifecycleTransitionProof.Recorded)LifecycleProofCodec.decodeRecorded(applied.proof().encode());
        StrictJson.require(recorded.kind()==LifecycleTransitionProof.Kind.NEXT_EPISODE,"first origin cannot consume another lifecycle branch");
        verifyRecorded(parent,recorded,same.head());
        StrictJson.require(recorded.eventIdentity.equals(begin.lifecycleEventIdentity()),"BEGIN refers to another original NEXT event identity");
        var eventPin=recorded.documents.stream().filter(pin->pin.reference().equals(begin.lifecycleEventRef())).findFirst()
                .orElseThrow(()->new IOException("BEGIN original NEXT event pin is absent from recorded proof"));
        StrictJson.require(same.head().documents().contains(eventPin),"BEGIN original NEXT event is not a canonical retained ancestor");
        var event=LifecycleJson.parse(same.readPinned(eventPin,ContinuityJson.DOCUMENT_MAX_BYTES),ContinuityJson.DOCUMENT_MAX_BYTES);
        same.verifyPin(eventPin);
        StrictJson.require(LifecycleJson.integer(event.get("sequence"),BigInteger.ONE).longValueExact()==begin.lifecycleSequence()
                &&recorded.eventIdentity.equals(LifecycleJson.text(event.get("identity")))
                &&LifecycleChild.KIND.equals(LifecycleJson.text(event.get("kind"))),"BEGIN original NEXT event sequence/kind differs");
        var transition=LifecycleJson.object(event.get("details"));
        var originalRegistry=LifecycleJson.object(material.originalHead().toJson().get(LifecycleContinuityAuthority.STATE_FIELD));
        var originalTransition=LifecycleJson.object(LifecycleJson.object(originalRegistry.get("transitions")).get(parent.actionId()));
        StrictJson.require(LifecycleJson.same(originalTransition,transition),"first BASELINE changed its exact original NEXT registry ancestor");
        var delta=LifecycleJson.object(transition.get("delta"));var stamp=LifecycleJson.object(transition.get("driver_snapshot"));
        ExactRef oldRef=ExactRef.fromJson(delta.get("original_driver_ref")),adoptedRef=ExactRef.fromJson(delta.get("adopted_driver_ref"));
        StrictJson.require(oldRef.equals(parent.lifecycleBefore().evidence().originalDriver())
                &&adoptedRef.equals(begin.adoptedDriverRef())&&recorded.evidence.contains(oldRef)&&recorded.evidence.contains(adoptedRef)
                &&saved.game().equals(GameGeneration.fromJson(transition.get("driver_after_game"))),
                "original NEXT Driver references or actual adopted Game differ from BEGIN and terminal parent");
        for(ExactRef ref:java.util.stream.Stream.concat(List.of(parent.lifecycleBefore().evidence().nativePacket(),parent.lifecycleBefore().evidence().helloPacket(),
                parent.lifecycleBefore().evidence().observationManifest(),oldRef).stream(),parent.lifecycleBefore().evidence().completeSourceQualification().stream()).toList())
            requireRecordedOriginalPin(same,recorded,ref,org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        var oldPin=requireRecordedOriginalPin(same,recorded,oldRef,org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        byte[] oldRaw=same.readPinned(oldPin,retainedDriverBound(oldPin.reference()));same.verifyPin(oldPin);
        var old=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(oldRaw);
        var adoptedPin=requireRecordedOriginalPin(same,recorded,adoptedRef,org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES);
        var adopted=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                same.readPinned(adoptedPin,retainedDriverBound(adoptedPin.reference())));same.verifyPin(adoptedPin);
        var subject=parent.lifecycleBefore().subject();
        StrictJson.require(subject.characterId().longValueExact()==before.actorId()&&subject.episodeRunId().equals(before.episodeRunId())
                &&subject.episodeEpoch()==before.epoch()&&parent.lifecycleBefore().frame().dateRaw().longValueExact()==before.dateRaw()
                &&old.session().bridgePid()==before.game().pid()&&old.session().actorId().equals(subject.characterId())
                &&old.session().episodeRunId().equals(before.episodeRunId())
                &&oldRef.bytes()==oldRaw.length&&oldRef.sha256().equals(ActionCodec.sha256(oldRaw))
                &&oldRef.sha256().equals(LifecycleJson.text(stamp.get("before_sha256")))
                &&subject.driverVersion()==LifecycleJson.integer(stamp.get("expected_version"),BigInteger.ZERO).longValueExact()
                &&before.epoch()==LifecycleJson.integer(stamp.get("expected_epoch"),BigInteger.ZERO).longValueExact()
                &&saved.epoch()==Math.addExact(before.epoch(),1)
                &&saved.epoch()==LifecycleJson.integer(stamp.get("next_epoch"),BigInteger.ZERO).longValueExact(),
                "old terminal Driver/subject/epoch does not match the original canonical NEXT and BEGIN");
        StrictJson.require(adoptedRef.sha256().equals(LifecycleJson.text(stamp.get("after_sha256")))
                &&adopted.session().bridgePid()==saved.game().pid()&&adopted.session().actorId().longValueExact()==saved.actorId()
                &&adopted.session().episodeRunId().equals(saved.episodeRunId())
                &&material.session().game().equals(saved.game())&&material.session().sessionId().equals(saved.sessionId())
                &&material.session().machineId().equals(saved.machineId()),"FIRST saved session must retain its actual adopted NEXT Driver scope");
        LifecycleReducer.requireScoredTerminal(old);
        same.requireHistoricalEpisodeWindowBaseline(material.baseline());
        StrictJson.require(initial.equals(same.head().digest()),"archived NEXT original reader changed the canonical writer");
        return new ArchivedNextOrigins(actualCanonicalParent,recorded,old,
                new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(before.machineId(),before.game(),before.sessionId()),
                material.session());
    }
    private static WriterContracts.Pin requireRecordedOriginalPin(ContinuityStorePort.Session same,LifecycleTransitionProof.Recorded proof,
            ExactRef reference,int maximum)throws IOException{
        StrictJson.require(proof.evidence.contains(reference),"canonical NEXT proof must retain every original parent source role");
        var pin=proof.documents.stream().filter(original->original.reference().equals(reference)).findFirst()
                .orElseThrow(()->new IOException("actual original lifecycle source FileID pin is unavailable: "+reference.path()));
        StrictJson.require(reference.bytes()<=maximum,"bounded lifecycle original source required");same.verifyPin(pin);return pin;
    }
    public void verifyRecorded(ActionCommand parent,LifecycleTransitionProof proof,WriterContracts.Head actualLockedHead)throws IOException{
        proof.validateParent(parent);LifecycleTransitionProof.Recorded recorded=(LifecycleTransitionProof.Recorded)LifecycleProofCodec.decodeRecorded(proof.encode());
        ObjectNode registry=LifecycleJson.object(actualLockedHead.state().toJson().get(LifecycleContinuityAuthority.STATE_FIELD));ObjectNode transition=LifecycleJson.object(LifecycleJson.object(registry.get("transitions")).get(parent.actionId()));
        LifecycleTransitionProof.Kind expectedKind=switch(LifecycleChild.Phase.valueOf(LifecycleJson.text(transition.get("phase")))){
            case DEATH_RECORDED->LifecycleTransitionProof.Kind.DEATH;
            case SUCCESSOR_COMMITTED,SUCCESSOR_PENDING_FINALIZED->LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR;
            case NEXT_EPISODE_COMMITTED->LifecycleTransitionProof.Kind.NEXT_EPISODE;
            case NEXT_EPISODE_ENTERED->throw new IOException("durable entered intent cannot settle a lifecycle parent");
        };
        StrictJson.require(recorded.kind()==expectedKind,"recorded lifecycle branch differs from actual canonical transition");
        StrictJson.require(LifecycleJson.text(transition.get("parent_body_sha256")).equals(ActionCodec.bodySha256(parent))
                &&LifecycleJson.same(LifecycleJson.object(transition.get("delta")).get("result"),LifecycleJson.parse(proof.encodedResult(),LifecycleProofCodec.MAX_RESULT_BYTES))
                &&new WriterContracts.Request(LifecycleChild.KIND,LifecycleJson.bytes(transition),List.of()).identity().equals(recorded.eventIdentity),"proof differs from actual original canonical lifecycle event");
        boolean originalEvent=false;
        for(var pin:recorded.documents){
            if(!actualLockedHead.documents().contains(pin)||!Path.of(pin.reference().path()).getFileName().toString().matches("[0-9]{8}\\.json"))continue;
            recordedPins.requireCurrent(pin);var physical=files.observe(Path.of(pin.reference().path())).orElseThrow(()->new IOException("original lifecycle event disappeared"));
            StrictJson.require(physical.reference().equals(pin.reference()),"original lifecycle event bytes changed");
            ObjectNode event=LifecycleJson.parse(files.read(physical,org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES),org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES);
            if(recorded.eventIdentity.equals(LifecycleJson.text(event.get("identity")))&&LifecycleChild.KIND.equals(LifecycleJson.text(event.get("kind")))
                    &&LifecycleJson.same(event.get("details"),transition))originalEvent=true;
            recordedPins.requireCurrent(pin);
        }
        StrictJson.require(originalEvent,"exact canonical lifecycle event, complete details and physical identity required");
        ObjectNode committedDelta=LifecycleJson.object(transition.get("delta"));
        List<ExactRef> required=new ArrayList<>(List.of(ExactRef.fromJson(committedDelta.get("original_native_ref")),ExactRef.fromJson(committedDelta.get("original_driver_ref"))));
        if(expectedKind==LifecycleTransitionProof.Kind.NEXT_EPISODE)for(String field:List.of("loaded_native_ref","episode_seed_ref","episode_seed_metadata_ref"))required.add(ExactRef.fromJson(committedDelta.get(field)));
        if(LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name().equals(LifecycleJson.text(transition.get("phase")))){
            var causal=parent.lifecycleBefore().evidence();
            StrictJson.require(ExactRef.fromJson(committedDelta.get("causal_original_driver_ref")).equals(causal.originalDriver()),
                    "final pending lifecycle must preserve the actual old parent causal Driver original");
            required.addAll(causal.originals());
            ObjectNode finalized=LifecycleJson.object(committedDelta.get("pending_ui_finalization"));
            LifecycleJson.exact(finalized,java.util.Set.of("m3_finalization_proof","canonical_finalization_domain","canonical_pending_domain",
                    "canonical_pending_publication_proof","actual_pending_driver","finalization_event_identity","finalization_sequence",
                    "before_final_driver_sha256","published_final_driver_sha256"));
            for(String field:List.of("m3_finalization_proof","canonical_finalization_domain","canonical_pending_domain",
                    "canonical_pending_publication_proof","actual_pending_driver"))required.add(ExactRef.fromJson(finalized.get(field)));
            WriterContracts.requireDigest(LifecycleJson.text(finalized.get("finalization_event_identity")));
            WriterContracts.requireDigest(LifecycleJson.text(finalized.get("before_final_driver_sha256")));
            ObjectNode stamp=LifecycleJson.object(transition.get("driver_snapshot"));
            StrictJson.require(LifecycleJson.text(finalized.get("published_final_driver_sha256")).equals(LifecycleJson.text(stamp.get("before_sha256")))
                    &&LifecycleJson.text(stamp.get("before_sha256")).equals(LifecycleJson.text(stamp.get("after_sha256")))
                    &&LifecycleJson.integer(stamp.get("expected_epoch"),BigInteger.ZERO).equals(LifecycleJson.integer(stamp.get("next_epoch"),BigInteger.ZERO)),
                    "final pending lifecycle must preserve its already-canonical complete Driver and episode epoch");
            long finalSequence=LifecycleJson.integer(finalized.get("finalization_sequence"),BigInteger.ONE).longValueExact();
            StrictJson.require(finalSequence<actualLockedHead.state().sequence(),"actual finalization event must precede the lifecycle settlement");
            String finalIdentity=LifecycleJson.text(finalized.get("finalization_event_identity"));boolean finalEvent=false;
            for(var pin:recorded.documents){
                if(!actualLockedHead.documents().contains(pin)||!Path.of(pin.reference().path()).getFileName().toString().equals(String.format(java.util.Locale.ROOT,"%08d.json",finalSequence)))continue;
                recordedPins.requireCurrent(pin);var physical=files.observe(Path.of(pin.reference().path())).orElseThrow(()->new IOException("original M3 finalization event disappeared"));
                StrictJson.require(physical.reference().equals(pin.reference()),"original M3 finalization event bytes changed");
                ObjectNode event=LifecycleJson.parse(files.read(physical,org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES),org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES);
                if(finalIdentity.equals(LifecycleJson.text(event.get("identity"))))finalEvent=true;recordedPins.requireCurrent(pin);
            }
            StrictJson.require(finalEvent,"canonical final pending publication receipt and original FileID event required");
        }
        StrictJson.require(proof.originalEvidence().containsAll(required)&&required.stream().allMatch(ref->recorded.documents.stream().anyMatch(pin->pin.reference().equals(ref))),"recorded proof does not retain the canonical lifecycle original sources");
        for(var pin:recorded.documents)recordedPins.requireCurrent(pin);
        for(ExactRef ref:proof.originalEvidence()){var actual=files.observe(Path.of(ref.path())).orElseThrow(()->new IOException("original lifecycle evidence missing"));StrictJson.require(actual.reference().equals(ref),"lifecycle evidence changed");files.verify(actual);}
    }
    static List<WriterContracts.Pin> immutableCommitPins(LifecycleCommit commit){String name=String.format(java.util.Locale.ROOT,"%08d.json",Math.addExact(commit.prepared().predecessor().state().sequence(),1));return commit.committedDocuments().stream().filter(pin->Path.of(pin.reference().path()).getFileName().toString().equals(name)).toList();}
    private List<ExactRef> evidence(String id){var original=originalFrames.get(id);return original==null?List.of():List.of(original.originalEvidence());}
    private ExactRef publish(String id,byte[] bytes)throws IOException{storage.require(bytes.length+4096L);String name=ActionCodec.sha256(id.getBytes(StandardCharsets.UTF_8))+"-"+(++evidenceSequence)+".json";return files.createNew(evidenceRoot.resolve(name),bytes).reference();}
    private static String newRun(BigInteger actor){return "native-"+actor+"-"+UUID.randomUUID().toString().replace("-","").substring(0,12);}
}
