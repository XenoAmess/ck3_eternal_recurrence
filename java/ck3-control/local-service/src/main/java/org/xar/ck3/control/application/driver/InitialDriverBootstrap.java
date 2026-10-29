package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.service.root.RootNativeSourceAuthority;
import org.xar.ck3.control.service.root.RootOriginalDriverJournal;
import org.xar.ck3.control.service.root.RootFrozenRunProfile;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FixtureGameplayRoot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Sole first-episode producer. Provisional initial facts permit one scoped read, never gameplay writes. */
public final class InitialDriverBootstrap implements ReadinessAuthority {
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final ActionSnapshotReader actions;
    private final ManagedGameSession game;
    private final G2Source source;
    private final RootNativeSourceAuthority sources;
    private final NativeSemanticEvidenceVerifier semantics;
    private final InitialEpisodePolicy policy;
    private final Clock clock;
    private final Duration freshness;
    private final int retainedFrames;
    private final DynamicCapabilities.Configuration capabilityConfiguration;
    private final CapabilitySessionPresentation capabilitySession;
    private final RootOriginalDriverJournal.Prepared originalDriverImport;
    private Staged active;
    private final ThreadLocal<Instant> fixtureCutoff=new ThreadLocal<>();
    public InitialDriverBootstrap(ContinuityWriter writer, NativeOutcomeArchive archive, ActionSnapshotReader actions,
            ManagedGameSession game, G2Source source, RootNativeSourceAuthority sources,
            NativeSemanticEvidenceVerifier semantics, InitialEpisodePolicy policy, Clock clock,
            Duration freshness, int retainedFrames,DynamicCapabilities.Configuration actualCapabilityConfiguration,
            CapabilitySessionPresentation actualCapabilitySession,RootOriginalDriverJournal.Prepared actualOriginalDriverImport) {
        this.writer=Objects.requireNonNull(writer);this.archive=Objects.requireNonNull(archive);this.actions=Objects.requireNonNull(actions);
        this.game=Objects.requireNonNull(game);this.source=Objects.requireNonNull(source);this.sources=Objects.requireNonNull(sources);
        this.semantics=Objects.requireNonNull(semantics);this.policy=Objects.requireNonNull(policy);this.clock=Objects.requireNonNull(clock);
        this.freshness=Objects.requireNonNull(freshness);this.retainedFrames=retainedFrames;
        capabilityConfiguration=Objects.requireNonNull(actualCapabilityConfiguration);capabilitySession=Objects.requireNonNull(actualCapabilitySession);
        originalDriverImport=Objects.requireNonNull(actualOriginalDriverImport);
        StrictJson.require(originalDriverImport.frozenProfile().initialPolicy()==policy,"initial Driver and original import must retain the same frozen policy producer");
        StrictJson.require(archive.writer()==writer && !freshness.isZero() && !freshness.isNegative()
                && freshness.compareTo(Duration.ofMinutes(1))<=0 && retainedFrames>=1 && retainedFrames<=4096,"same writer/archive and finite first-frame custody required");
    }
    public Optional<PreparedFixture> fixture() { return originalDriverImport.frozenProfile().fixture(); }
    private Instant deadline(ActionCommand command){return fixture().isPresent()
            ?Optional.ofNullable(fixtureCutoff.get()).orElseGet(()->ActionObservationWindow.deadline(command)):command.deadline();}
    /**
     * Drains the held receiver for a short interval without requiring another Snapshot.
     * The returned frame is an original retained frame; only the caller's existing source/readiness
     * checks can prove that an actually received heartbeat advanced the paused pump.
     */
    public static NativeObservationPort.ObservedFrame collectPausedPump(
            NativeSnapshotWaitPort transport, Instant originalDeadline, Clock clock)
            throws IOException,InterruptedException {
        Objects.requireNonNull(transport);Objects.requireNonNull(originalDeadline);Objects.requireNonNull(clock);
        Instant now=clock.instant();
        if(!now.isBefore(originalDeadline))throw new IOException("original initial pump deadline elapsed");
        Instant waitUntil=now.plusMillis(50);
        if(!waitUntil.isBefore(originalDeadline))waitUntil=originalDeadline.minusNanos(1);
        return Objects.requireNonNull(transport.waitForSnapshot(waitUntil,originalDeadline)).frame();
    }

    public synchronized Staged stage(ActionCommand command, ActionState.Attempt attempt) throws IOException,InterruptedException {
        StrictJson.require(fixture().isEmpty(),"fixture Start requires its actual independent READ after the original ACK");
        return stageOriginal(command,attempt,Optional.empty());
    }
    public synchronized Staged stageFixture(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived originalStartAck)
            throws IOException,InterruptedException {
        StrictJson.require(fixture().isPresent(),"explicit source-bound prepared fixture required");
        Objects.requireNonNull(originalStartAck).custody().orElseThrow().verify(originalStartAck,attempt.guard());
        StrictJson.require(originalStartAck.requestId().equals(attempt.requestId())&&originalStartAck.nativeOk(),
                "fixture first Driver must retain the actual successful original Start ACK");
        return stageOriginal(command,attempt,Optional.of(originalStartAck));
    }
    private Staged stageOriginal(ActionCommand command,ActionState.Attempt attempt,Optional<NativeActionPort.AckReceived> fixtureAck)
            throws IOException,InterruptedException {
        var borrowed=writer.borrowedSession(); writer.requireSession(borrowed); policy.verifyGame(game.generation());
        StrictJson.require(command.source().equals(source) && command.origin() instanceof CommandOrigin.Frontend && command.origin().requireFrontend().frame() instanceof FrontendFrame.Menu,
                "first episode must originate at actual menu");
        if(active!=null) {
            StrictJson.require(active.command.equals(command) && active.attempt.requestId().equals(attempt.requestId()),"another initial Start already owns the first Driver");
            StrictJson.require(fixtureAck.isEmpty()||active.independentRead!=null
                    &&active.independentRead.acknowledgement().custody().orElseThrow().session()
                        .equals(fixtureAck.orElseThrow().custody().orElseThrow().session()),"fixture first READ custody changed");
            if(active.latest==null) active.capture(borrowed,game.nativeTransport().latestObservedSnapshot().orElseThrow(() -> new IOException("first actual native snapshot disappeared")),deadline(command));
            active.initializeCapabilities(borrowed);
            return active;
        }
        StrictJson.require(!borrowed.head().state().toJson().has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)
                && !borrowed.head().state().toJson().has(WriterContracts.GAMEPLAY_ENTRY_FIELD),"existing or null baseline cannot become an empty first episode");
        game.verify(); NativeGameTransport transport=game.nativeTransport();
        transport.awaitHello(deadline(command));
        var original=originalDriverImport.load(writer,borrowed,game.launchPlan());
        DriverBootstrap.requireOriginalAdoption(borrowed,transport,original);
        if(original.status()!=RootOriginalDriverJournal.Status.MISSING
                ||!((original.frozenProfile().importMode() instanceof RootFrozenRunProfile.DisabledFreshRobert&&fixture().isEmpty())
                    ||(original.frozenProfile().importMode() instanceof RootFrozenRunProfile.DisabledFreshFixture&&fixture().isPresent())))
            throw new IOException("an existing or explicitly enabled cold Driver input must use its actual resume path; it cannot create an empty first episode");
        original.requireRetained(borrowed);
        transport.startHandshake(deadline(command));
        NativeFreshSnapshotPort.Received independent=null;
        NativeObservationPort.ObservedFrame actual;
        if(fixtureAck.isPresent()) {
            if(!(transport instanceof NativeFreshSnapshotPort fresh))throw new IOException("actual fixture transport has no independent full-state READ");
            var read=fresh.readFreshFullState(deadline(command));
            if(!(read instanceof NativeFreshSnapshotPort.Received received))throw new IOException("actual first-map independent READ unavailable; original Start must not replay");
            NativeFreshSnapshotPort.verifyAfter(fixtureAck.orElseThrow(),received);independent=received;actual=received.originalFrame();
        } else actual=transport.observe(deadline(command));
        StrictJson.require(!actual.observedAt().isBefore(attempt.submittedAt()) && actual.session().game().equals(command.origin().game())
                && actual.session().machineId().equals(command.origin().machineId()) && actual.session().sessionId().equals(command.sessionId())
                && actual.session().connectionGeneration().equals(command.origin().requireFrontend().connectionGeneration()),"first map crossed original Start/session/connection");
        String episode="java-start-"+ActionCodec.bodySha256(command).substring(0,32);
        var initial=InitialDriverState.create(actual,transport.pipeName(),episode,policy);
        ExactRef full=archive.preserveArtifact(borrowed,initial.driver().encode(),ReadinessArchive.Role.DRIVER.maximumBytes());
        var stamp=new DriverSnapshotFacts.Stamp(0,0,game.generation(),episode,DriverJson.sha256(initial.driver().encode()));
        var known=new DriverSnapshotFacts.Known(initial.driver(),stamp,full,List.of(),initial.auxiliary(),Optional.empty(),Optional.empty());
        var repository=new DriverFactsRepository(known);
        var producer=new NativeDriverObservationProducer(repository,transport,source,wire -> {
            try { return archive.preserveArtifact(writer.borrowedSession(),wire,ReadinessArchive.Role.DRIVER.maximumBytes()); }
            catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        });
        var authority=new DriverStateAssembler(actions,repository,producer);
        var observations=new HeldDriverObservationPort(transport,authority,observed -> {
            try { return archive.withSession(writer.borrowedSession()).preserveNativeFrame(observed); }
            catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        },new DriverObservationAssembler(),retainedFrames);
        Staged staged=new Staged(command,attempt,repository,producer,authority,observations,full);
        active=staged;staged.independentRead=independent;staged.latestFixtureRead=independent;
        if(independent!=null){
            archive.withSession(borrowed).preserve(independent.acknowledgement());
            producer.bindNativeCampaignFixture(staged,borrowed,game,source,archive,policy,independent);
        }
        staged.capture(borrowed,actual,deadline(command));
        staged.initializeCapabilities(borrowed);
        // Record the sole producer before a subsequent native read/archive operation can fail.
        return staged;
    }
    public synchronized Staged current(String actionId) throws IOException {
        if(active==null || !active.command.actionId().equals(actionId))throw new IOException("actual initial Start producer unavailable; no inferred seed");
        return active;
    }
    @Override public <T> T current(ContinuityStorePort.Session borrowed,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work)throws IOException {
        Staged actual;
        synchronized(this) { actual=active; }
        if(actual==null)throw new IOException("real first Driver producer is not present");
        return actual.current(borrowed,expected,callerDeadline,work);
    }
    public final class Staged implements ReadinessAuthority {
        private final ActionCommand command;
        private final ActionState.Attempt attempt;
        private final DriverFactsRepository repository;
        private final NativeDriverObservationProducer producer;
        private final DriverStateAssembler authority;
        private final HeldDriverObservationPort observations;
        private final ExactRef fullDriver;
        private final ThreadLocal<ContinuityStorePort.Session> scope=new ThreadLocal<>();
        private NativeFreshSnapshotPort.Received independentRead;
        private NativeFreshSnapshotPort.Received latestFixtureRead;
        private Capture first;
        private Capture latest;
        private Capture fixturePumpBasis;
        private DriverBootstrap.Seed promotedFixtureSeed;
        private DriverBootstrap.Seed preparedFixtureSeed;
        private String preparedFixtureIdentity;
        private WriterContracts.Receipt verifiedFixtureEntry;
        private PlanningReadReceipt rootRead;
        private boolean promoted;
        private boolean capabilitiesInitialized;
        private DriverBootstrap.Adopted actualAdopted;
        private String committedIdentity;
        private Staged(ActionCommand command,ActionState.Attempt attempt,DriverFactsRepository repository,
                NativeDriverObservationProducer producer,DriverStateAssembler authority,HeldDriverObservationPort observations,ExactRef fullDriver) {
            this.command=command;this.attempt=attempt;this.repository=repository;this.producer=producer;this.authority=authority;this.observations=observations;this.fullDriver=fullDriver;
        }
        /** Retains the real provisional Driver owner, without constructing an adopted session or Ready. */
        public void requireFixtureProjectionOwner(ContinuityStorePort.Session same,ManagedGameSession identicalGame,G2Source identicalSource)throws IOException {
            writer.requireSession(same);
            StrictJson.require(fixture().isPresent()&&active==this&&!promoted&&identicalGame==game&&identicalSource.equals(source),
                    "native-campaign projection crossed its actual privately retained fixture producer");
            var prepared=fixture().orElseThrow();prepared.verifySources();policy.requireFixtureProjection(prepared);
            policy.verifyGame(game.generation());game.verify();same.verifyPin(same.capturePin(source.sourceRef(),WriterContracts.MAX_PIN_BYTES));
            var original=actions.withFrozen(same,view->view.find(command.actionId()).orElseThrow());
            StrictJson.require(original.command().equals(command)&&original.bodySha256().equals(ActionCodec.bodySha256(command))
                    &&independentRead!=null&&independentRead.originalFrame().session().game().equals(game.generation())
                    &&independentRead.originalFrame().session().sessionId().equals(game.sessionId()),
                    "native-campaign projection lost its original canonical Start or actual first READ");
        }
        public void requireFixtureOwner(ContinuityStorePort.Session same,ManagedGameSession identicalGame,G2Source identicalSource)throws IOException {
            writer.requireSession(same);
            StrictJson.require(fixture().isPresent()&&!promoted&&active==this&&identicalGame==game&&identicalSource.equals(source),
                    "fixture provisional Driver crossed its sole actual Game/source/producer or was retired");
            fixture().orElseThrow().verifySources();policy.verifyGame(game.generation());game.verify();
            Capture retained=Objects.requireNonNull(latest);
            retained.source.assertCurrent(same);if(retained.pin.isPresent())same.verifyPin(retained.pin.orElseThrow());
        }
        /** Observation-only custody survives the true Entry handoff; it grants no fixture action scope. */
        public void requireNativeCampaignObservationOwner(ContinuityStorePort.Session same,ManagedGameSession identicalGame,G2Source identicalSource)throws IOException {
            if(!promoted){requireFixtureProjectionOwner(same,identicalGame,identicalSource);return;}
            writer.requireSession(same);
            StrictJson.require(active==this&&identicalGame==game&&identicalSource.equals(source)&&actualAdopted!=null
                    &&actualAdopted.producer()==producer&&actualAdopted.repository()==repository&&actualAdopted.observations()==observations
                    &&actualAdopted.authority()==authority&&verifiedFixtureEntry!=null&&preparedFixtureSeed!=null
                    &&actualAdopted.session().game().equals(game.generation())&&actualAdopted.session().sessionId().equals(game.sessionId()),
                    "native-campaign observation lost its genuine same-producer Driver handoff");
            game.verify();policy.verifyGame(game.generation());var prepared=fixture().orElseThrow();prepared.verifySources();policy.requireFixtureProjection(prepared);
            same.requireHistoricalHead(verifiedFixtureEntry.head().sequence(),ContinuityJson.digest(verifiedFixtureEntry.head().toJson()));
            same.verifyPin(same.capturePin(source.sourceRef(),WriterContracts.MAX_PIN_BYTES));
        }
        public DriverStateAssembler fixtureAuthority(ContinuityStorePort.Session same)throws IOException {
            requireFixtureOwner(same,game,source);return authority;
        }
        public void requireFixtureBootstrap(ContinuityStorePort.Session same,InitialDriverBootstrap identical)throws IOException {
            requireFixtureOwner(same,game,source);
            StrictJson.require(InitialDriverBootstrap.this==identical,"fixture provisional Driver belongs to another actual bootstrap");
        }
        public DriverSnapshotFacts.Known fixtureDriver(ContinuityStorePort.Session same)throws IOException {
            requireFixtureOwner(same,game,source);
            return repository.locked(state->{
                StrictJson.require(state instanceof DriverSnapshotFacts.Known,"complete actual provisional Driver is unavailable");
                return (DriverSnapshotFacts.Known)state;
            });
        }
        public boolean fixtureRetired(){return promoted;}
        @FunctionalInterface public interface FixtureWork<T>{T run()throws IOException,InterruptedException;}
        /** The real private parent Held supplies the continuation cutoff, never the old Start deadline. */
        public <T>T withFixtureDeadline(ContinuityStorePort.Session same,ActionCommand exactParent,String handlerId,
                Instant requested,FixtureWork<T> work)throws IOException,InterruptedException {
            writer.requireSession(same);StrictJson.require(fixture().isPresent()&&fixtureCutoff.get()==null,
                    "fixture deadline scope cannot nest or authorize an ordinary episode");
            Instant actual=ActionChildPlanningScope.fixtureDeadline(same,same.head(),exactParent,handlerId);
            StrictJson.require(!requested.isAfter(actual)&&clock.instant().isBefore(requested),"fixture callback exceeds its actual private parent cutoff");
            fixtureCutoff.set(requested);try{return Objects.requireNonNull(work).run();}finally{fixtureCutoff.remove();}
        }
        private Instant requireFixtureDeadline(ContinuityStorePort.Session same,Instant requested)throws IOException {
            Instant actual=fixtureCutoff.get();
            if(actual==null&&ActionScope.currentActionId().filter(command.actionId()::equals).isPresent())actual=ActionObservationWindow.deadline(command);
            if(actual==null){
                var held=ActionChildPlanningScope.current(same,same.head()).orElseThrow(()->new IOException("fixture READ has no real parent Held"));
                var parent=ContinuityActionJournal.lookup(same.head().state(),held.actionId(),archive.withSession(same)).orElseThrow();
                actual=ActionChildPlanningScope.fixtureDeadline(same,same.head(),parent.command(),held.handlerId());
            }
            StrictJson.require(!requested.isAfter(actual)&&clock.instant().isBefore(requested),"fixture READ exceeds its actual private cutoff");return requested;
        }
        /** Retains the live producer's exact preview inputs. This private retention alone grants no adoption. */
        public void retainFixtureEntrySeed(ContinuityStorePort.Session same,WriterContracts.Request original)throws IOException {
            requireFixtureOwner(same,game,source);assertCurrent(same);
            StrictJson.require(WriterContracts.GAMEPLAY_ENTRY_KIND.equals(original.kind())&&original.detailsObject().has("fixture"),
                    "actual fixture Entry request required");
            var retained=seed();
            StrictJson.require(retained.fullDriver().equals(ExactRef.fromJson(original.detailsObject().get("full_driver"))),
                    "fixture preview changed its actual retained complete Driver");
            if(preparedFixtureSeed==null){preparedFixtureSeed=retained;preparedFixtureIdentity=original.identity();}
            StrictJson.require(preparedFixtureIdentity.equals(original.identity())&&preparedFixtureSeed.equals(retained),
                    "fixture cannot replace the original Entry preview's private Driver custody");
        }
        public ActionCommand command() { return command; }
        public ActionState.Attempt attempt() { return attempt; }
        public DriverBootstrap.Seed seed() throws IOException {
            if(promotedFixtureSeed!=null)return promotedFixtureSeed;
            if(verifiedFixtureEntry!=null)return Objects.requireNonNull(preparedFixtureSeed);
            Capture capture=Objects.requireNonNull(latest);
            ExactRef retainedFull=fullDriver;
            if(fixture().isPresent()){
                var same=writer.borrowedSession();requireFixtureOwner(same,game,source);
                retainedFull=archive.preserveArtifact(same,fixtureDriver(same).driver().encode(),ReadinessArchive.Role.DRIVER.maximumBytes());
            }
            return new DriverBootstrap.Seed(retainedFull,retainedFull,capture.lease.driver().stamp().driverVersion(),capture.lease.driver().stamp().episodeEpoch(),
                    game.nativeTransport().diagnostics().session().orElseThrow(),capture.lease.driver().auxiliary(),capture.lease.driver().loop());
        }
        public NativeFreshSnapshotPort.Received independentRead() {
            StrictJson.require(fixture().isPresent()&&independentRead!=null,"actual fixture first-map independent READ is absent");
            return independentRead;
        }
        public DriverObservationAssembler.Complete firstMapFrame(){return Objects.requireNonNull(first).lease.frame();}
        public NativeFreshSnapshotPort.Received latestFixtureRead(){
            StrictJson.require(fixture().isPresent()&&latestFixtureRead!=null,"actual fixture independent READ original is absent");
            return latestFixtureRead;
        }
        public SemanticEvidence firstMapSemantic(){return Objects.requireNonNull(first).lease.semantic();}
        public Optional<ExactRef> firstMapSourceQualification(){return Objects.requireNonNull(first).lease.originalSourceQualification();}
        public SemanticEvidence semantic() { return Objects.requireNonNull(latest).lease.semantic(); }
        public DriverObservationAssembler.Complete frame() { return Objects.requireNonNull(latest).lease.frame(); }
        public ExactRef firstHeartbeat() { return Objects.requireNonNull(first).lease.originalHeartbeat(); }
        public ExactRef lastHeartbeat() { return Objects.requireNonNull(latest).lease.originalHeartbeat(); }
        public ExactRef originalHello() { return Objects.requireNonNull(latest).lease.originalHello(); }
        public Optional<ExactRef> sourceQualification() { return Objects.requireNonNull(latest).lease.originalSourceQualification(); }
        public InitialEpisodePolicy policy() { return policy; }
        public String auxiliarySha256() { return DriverJson.sha256(DriverJson.encode(Objects.requireNonNull(latest).lease.driver().auxiliary())); }
        G2Source source() { return source; }
        DriverFactsRepository repository() { return repository; }
        DriverStateAssembler authority() { return authority; }
        NativeDriverObservationProducer producer() { return producer; }
        HeldDriverObservationPort observations() { return observations; }
        public PlanningReadReceipt rootRead() { return Objects.requireNonNull(rootRead); }
        private void initializeCapabilities(ContinuityStorePort.Session borrowed)throws IOException {
            if(capabilitiesInitialized)return;
            var known=repository.locked(state -> (DriverSnapshotFacts.Known)state);
            if(known.auxiliary().members().containsKey(DriverCapabilityStateProducer.STATE_SOURCE)) {
                Obj ref=object(known.auxiliary().get(DriverCapabilityStateProducer.STATE_SOURCE),"capability_state_source");
                ExactRef exact=new ExactRef(text(ref.get("path"),"path"),integer(ref.get("bytes"),"bytes").longValueExact(),text(ref.get("sha256"),"sha256"));
                Obj replayed=DriverCapabilityStateProducer.replay(frame(),known,exact,archive.withSession(borrowed));
                for(var entry:replayed.members().entrySet())StrictJson.require(entry.getValue().equals(known.auxiliary().get(entry.getKey())),"actual published first capability source differs");
            } else {
                byte[] policyWire=java.nio.file.Files.readAllBytes(java.nio.file.Path.of(policy.source().path()));policy.verify();
                ExactRef archivedPolicy=archive.withSession(borrowed).preserveMaterial(new RawJson(policyWire));
                var initialized=DriverCapabilityStateProducer.initializeNewEpisode(frame(),known,capabilityConfiguration,
                        capabilitySession,archivedPolicy,archive.withSession(borrowed));
                authority.publishCapabilityInputs(borrowed,initialized.expectedStamp(),initialized.expectedAuxiliarySha256(),initialized);
            }
            capabilitiesInitialized=true;
            capture(borrowed,game.nativeTransport().latestObservedSnapshot().orElseThrow(),deadline(command));
        }
        public void retainRoot(PlanningReadResult.Known<?> result)throws IOException {
            PlanningReadReceipt actual=result.receipt();
            GameplayEntryRoot decoded=decodeRoot(actual);
            StrictJson.require(actual.request().before().equals(frame().identity()) && actual.request().source().equals(source)
                    && actual.request().sessionId().equals(game.sessionId()) && decoded.player().equals(frame().identity().frame().identity().player()),"independent root crossed first native frame");
            rootRead=actual;
            var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
            var known=repository.locked(state -> (DriverSnapshotFacts.Known)state);
            var observed=DriverCapabilityStateProducer.observeRead(frame(),known,result,archive.withSession(borrowed));
            authority.publishCapabilityInputs(borrowed,observed.expectedStamp(),observed.expectedAuxiliarySha256(),observed);
            capture(borrowed,game.nativeTransport().latestObservedSnapshot().orElseThrow(),deadline(command));
        }
        @FunctionalInterface public interface ReadWork<T> { T run() throws IOException; }
        /** The same installed provisional cache observer has already published this actual READ. */
        public void retainFixtureRoot(PlanningReadResult.Known<?> result)throws IOException {
            var same=writer.borrowedSession();requireFixtureOwner(same,game,source);
            var original=result.receipt();var decoded=decodeRoot(original);
            StrictJson.require(original.request().before().equals(frame().identity())&&original.request().source().equals(source)
                    &&original.request().sessionId().equals(game.sessionId())&&decoded.player().equals(frame().identity().frame().identity().player()),
                    "fixture root crossed its actual original full frame/source/player");
            rootRead=original;
            capture(same,game.nativeTransport().latestObservedSnapshot().orElseThrow(),deadline(command));
        }
        public <T> T scopedRead(ReadWork<T> work) throws IOException {
            var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
            if(fixture().isPresent()&&!promoted&&scope.get()==borrowed)return work.run();
            StrictJson.require(!promoted && scope.get()==null,"initial query scope is already active or retired"); scope.set(borrowed);
            try { return work.run(); } finally { scope.remove(); }
        }
        @Override public <T> T current(ContinuityStorePort.Session borrowed,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work)throws IOException {
            writer.requireSession(borrowed);
            Objects.requireNonNull(callerDeadline);
            Instant originalDeadline=deadline(command);
            Instant effectiveDeadline=callerDeadline.isBefore(originalDeadline)?callerDeadline:originalDeadline;
            StrictJson.require(clock.instant().isBefore(effectiveDeadline),"caller first-frame readiness deadline expired before observation");
            StrictJson.require(!promoted && scope.get()==borrowed && expected.equals(frame().identity()),"no live exact first-frame read scope");
            var actual=game.nativeTransport().latestObservedSnapshot().orElseThrow(() -> new IOException("held first snapshot disappeared"));
            Capture fresh=capture(borrowed,actual,effectiveDeadline);
            Instant readyAt=clock.instant();
            StrictJson.require(readyAt.isBefore(effectiveDeadline) && readyAt.isBefore(fresh.lease.validUntil()),"first-frame observation exhausted its original caller deadline or freshness");
            StrictJson.require(expected.equals(fresh.lease.frame().identity()),"first native frame changed during independent query");
            fresh.source.assertCurrent(borrowed);if(fresh.pin.isPresent())borrowed.verifyPin(fresh.pin.orElseThrow());
            T result=work.apply(fresh.lease);fresh.source.assertCurrent(borrowed);if(fresh.pin.isPresent())borrowed.verifyPin(fresh.pin.orElseThrow());
            StrictJson.require(clock.instant().isBefore(effectiveDeadline),"first-frame readiness callback crossed its original caller deadline");
            return result;
        }
        private GameplayEntryRoot decodeRoot(PlanningReadReceipt original) {
            return fixture().isPresent()?FixtureGameplayRoot.decode(original,fixture().orElseThrow(),frame().semantic()):GameplayEntryRoot.decode(original);
        }
        /** Read-only continuation of the identical first Driver; never repeats its Start or creates another history. */
        public void pollFixture()throws IOException,InterruptedException {
            StrictJson.require(fixture().isPresent()&&!promoted,"explicit unpromoted fixture scope required");
            pollFixture(Optional.empty(),deadline(command));
        }
        public void pollFixture(NativeActionPort.AckReceived originalChildAck,Instant deadline)throws IOException,InterruptedException {
            pollFixture(Optional.of(Objects.requireNonNull(originalChildAck)),deadline);
        }
        private void pollFixture(Optional<NativeActionPort.AckReceived> originalAck,Instant deadline)throws IOException,InterruptedException {
            var borrowed=writer.borrowedSession();requireFixtureOwner(borrowed,game,source);
            deadline=requireFixtureDeadline(borrowed,deadline);
            if(!(game.nativeTransport() instanceof NativeFreshSnapshotPort fresh))throw new IOException("actual fixture transport has no independent full-state READ");
            var result=fresh.readFreshFullState(deadline);
            if(!(result instanceof NativeFreshSnapshotPort.Received received))throw new IOException("actual fixture independent READ unavailable; no old frame inference");
            if(originalAck.isPresent())NativeFreshSnapshotPort.verifyAfter(originalAck.orElseThrow(),received);
            archive.withSession(borrowed).preserve(received.acknowledgement());latestFixtureRead=received;
            capture(borrowed,received.originalFrame(),deadline);
        }
        public void awaitIndependentPausedPump(int maximumObservations) throws IOException,InterruptedException {
            StrictJson.require(maximumObservations>=1 && maximumObservations<=64,"finite initial pump observation bound required");
            var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
            Capture basis=first;
            if(fixture().isPresent()){
                if(fixturePumpBasis!=null&&latest.assessment.ready()&&latest.assessment.key().equals(fixturePumpBasis.assessment.key())
                        &&latest.assessment.pumpEpoch().orElseThrow().compareTo(fixturePumpBasis.assessment.pumpEpoch().orElseThrow())>0)return;
                fixturePumpBasis=Objects.requireNonNull(latest);basis=fixturePumpBasis;
            }
            if(latest!=null && latest.assessment.ready() && latest.assessment.key().equals(basis.assessment.key())
                    && latest.assessment.pumpEpoch().orElseThrow().compareTo(basis.assessment.pumpEpoch().orElseThrow())>0)return;
            for(int count=0;count<maximumObservations;count++) {
                Capture actual=capture(borrowed,collectPausedPump(game.nativeTransport(),deadline(command),clock),deadline(command));
                if(actual.assessment.key().equals(basis.assessment.key()) && actual.assessment.ready()
                        && actual.assessment.pumpEpoch().orElseThrow().compareTo(basis.assessment.pumpEpoch().orElseThrow())>0)return;
                StrictJson.require(actual.assessment.key().equals(basis.assessment.key()),"initial paused map changed before independent pump");
            }
            throw new IOException("actual paused application-main pump did not advance; Start remains unresolved");
        }
        public void assertCurrent(ContinuityStorePort.Session borrowed)throws IOException {
            writer.requireSession(borrowed);policy.verifyGame(game.generation());game.verify();
            StrictJson.require(capabilitiesInitialized,"full actual first capability state is not initialized");
            var actual=game.nativeTransport().latestObservedSnapshot().orElseThrow(() -> new IOException("first snapshot unavailable"));
            Capture current=capture(borrowed,actual,deadline(command));
            Capture entryBasis=fixture().isPresent()?Objects.requireNonNull(fixturePumpBasis,"fixture has no independent final paused pump"):first;
            StrictJson.require(current.assessment.ready() && current.assessment.key().equals(entryBasis.assessment.key())
                    && current.assessment.pumpEpoch().orElseThrow().compareTo(entryBasis.assessment.pumpEpoch().orElseThrow())>0,"first entry lost actual paused/pump/source binding");
            decodeRoot(rootRead());
            StrictJson.require(rootRead().request().before().equals(frame().identity()),"root proof no longer matches first actual frame");
        }
        private Capture capture(ContinuityStorePort.Session borrowed,NativeObservationPort.ObservedFrame actual,Instant deadline)throws IOException {
            writer.requireSession(borrowed);policy.verifyGame(game.generation());game.verify();
            if(fixture().isPresent()&&latestFixtureRead!=null&&latestFixtureRead.originalFrame()==actual){
                var original=actions.withFrozen(borrowed,view->view.find(command.actionId()).orElseThrow());
                InitialDriverState.publishFixtureActor(this,borrowed,game,source,archive,latestFixtureRead,original,deadline);
            }
            String head=borrowed.head().digest();
            DriverObservationFacts.Result produced=producer.read(actual);
            StrictJson.require(produced instanceof DriverObservationFacts.Known,"complete first Driver observation unavailable: "+produced);
            DriverObservationFacts facts=((DriverObservationFacts.Known)produced).facts();
            var known=repository.locked(state -> {
                StrictJson.require(state instanceof DriverSnapshotFacts.Known,"first Driver owner unavailable");
                var current=(DriverSnapshotFacts.Known)state;repository.replaceObservation(current.stamp(),facts);
                return (DriverSnapshotFacts.Known)repository.locked(value -> value);
            });
            ExactRef packet=archive.preserveArtifact(borrowed,actual.originalPacket(),ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());
            var assembled=new DriverObservationAssembler().assemble(actual,facts,packet);
            StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"first native/full Driver join incomplete: "+assembled);
            var frame=(DriverObservationAssembler.Complete)assembled;
            if(known.auxiliary().members().containsKey(DriverCapabilityStateProducer.STATE_SOURCE)) {
                var refresh=DriverCapabilityStateProducer.refresh(frame,known,archive.withSession(borrowed));
                if(refresh.isPresent()) {
                    var publication=refresh.orElseThrow();
                    authority.publishCapabilityInputs(borrowed,publication.expectedStamp(),publication.expectedAuxiliarySha256(),publication);
                    // Reissue the manifest for this same original packet and sole public-revision producer.
                    // This is an auxiliary publication, never a second native observation or a reset.
                    var refreshed=producer.read(actual);
                    StrictJson.require(refreshed instanceof DriverObservationFacts.Known,"refreshed first Driver facts unavailable");
                    var refreshedFacts=((DriverObservationFacts.Known)refreshed).facts();
                    known=repository.locked(state -> {
                        StrictJson.require(state instanceof DriverSnapshotFacts.Known,"first Driver owner unavailable after cache publication");
                        var current=(DriverSnapshotFacts.Known)state;repository.replaceObservation(current.stamp(),refreshedFacts);
                        return (DriverSnapshotFacts.Known)repository.locked(value -> value);
                    });
                    assembled=new DriverObservationAssembler().assemble(actual,refreshedFacts,packet);
                    StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"refreshed first native/full Driver join incomplete");
                    frame=(DriverObservationAssembler.Complete)assembled;
                }
            }
            Instant now=clock.instant();
            var process=game.inspect(game.generation(),deadline);
            StrictJson.require(process instanceof GameLifecycle.Running,"actual managed first Game is not running");
            var diagnostics=game.nativeTransport().diagnostics();
            var received=RootNativeCapabilities.project(frame,known,diagnostics,(GameLifecycle.Running)process,now,deadline,freshness);
            var qualified=sources.verify(borrowed,new SessionIdentity(game.machineId(),game.generation(),game.sessionId()),frame,known,diagnostics,(GameLifecycle.Running)process,deadline);
            Optional<WriterContracts.Pin> pin=Optional.empty();
            if(qualified.proof().isPresent())pin=Optional.of(borrowed.capturePin(qualified.proof().orElseThrow(),ReadinessArchive.Role.SOURCE_PROOF.maximumBytes()));
            qualified.assertCurrent(borrowed);if(pin.isPresent())borrowed.verifyPin(pin.orElseThrow());
            var assessment=NativeReadiness.assess(frame,received.capabilities(),new NativeReadiness.Policy(false,false,Optional.of(frame.identity().frame().identity().player()),Duration.ZERO,false));
            StrictJson.require(assessment.ready(),"first paused/living native readiness incomplete: "+assessment.reason());
            ExactRef semantic=archive.preserveArtifact(borrowed,DriverJson.encode(frame.semantic()),ReadinessArchive.Role.SEMANTIC.maximumBytes());
            ExactRef driver=archive.preserveArtifact(borrowed,known.driver().encode(),ReadinessArchive.Role.DRIVER.maximumBytes());
            ExactRef stamp=archive.preserveArtifact(borrowed,NativeDriverStamp.encode(frame,known),ReadinessArchive.Role.DRIVER_STAMP.maximumBytes());
            SemanticEvidence evidence=new SemanticEvidence(frame.identity(),semantic,packet,stamp,driver,frame.observedAt());
            semantics.verify(borrowed,new SessionIdentity(game.machineId(),game.generation(),game.sessionId()),evidence);
            ExactRef hello=archive.preserveArtifact(borrowed,diagnostics.originalHello().orElseThrow().original().packet().value(),ReadinessArchive.Role.HELLO.maximumBytes());
            ExactRef heartbeat=archive.preserveArtifact(borrowed,diagnostics.latestHeartbeat().orElseThrow().original().packet().value(),ReadinessArchive.Role.HEARTBEAT.maximumBytes());
            var lease=new ReadinessAuthority.LeaseSnapshot(frame,known,received.capabilities(),evidence,Set.of(),
                    Set.copyOf(diagnostics.originalHello().orElseThrow().original().capabilities()),hello,heartbeat,frame.observedAt().plus(freshness),qualified.proof());
            StrictJson.require(clock.instant().isBefore(lease.validUntil()) && head.equals(borrowed.head().digest()),"first source/SEM publication crossed actual freshness or writer head");
            var captured=new Capture(lease,qualified,pin,assessment);if(first==null)first=captured;latest=captured;return captured;
        }
        void requireCommitted(ContinuityStorePort.Session borrowed,WriterContracts.Prepared prepared,WriterContracts.Receipt receipt)throws IOException {
            writer.requireSession(borrowed);
            if(fixture().isPresent()){
                StrictJson.require(preparedFixtureSeed!=null&&preparedFixtureIdentity.equals(prepared.request().identity()),
                        "fixture adoption has no actual retained original Entry preview");
                borrowed.requireCommitted(prepared,receipt);game.verify();policy.verifyGame(game.generation());fixture().orElseThrow().verifySources();
                for(var pin:prepared.sources())borrowed.verifyPin(pin);
                for(var pin:prepared.evidence())borrowed.verifyPin(pin);
                verifiedFixtureEntry=receipt;
            }else assertCurrent(borrowed);
            StrictJson.require(WriterContracts.GAMEPLAY_ENTRY_KIND.equals(prepared.request().kind()) && receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                    && receipt.eventIdentity().equals(prepared.request().identity())
                    && (fixture().isPresent()?ContinuityJson.same(receipt.head().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD),
                            borrowed.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                        :receipt.head().sequence()==borrowed.head().state().sequence()
                            &&ContinuityJson.same(receipt.head().toJson(),borrowed.head().state().toJson())),
                    "initial Driver promotion lacks its actual surviving same-writer entry commit");
            var state=receipt.head().toJson();
            StrictJson.require(seed().fullDriver().equals(ExactRef.fromJson(state.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)))
                    && command.actionId().equals(StrictJson.text(state.get(WriterContracts.GAMEPLAY_ENTRY_FIELD).get("action_id"))),"committed initial baseline or Start identity differs");
        }
        public DriverBootstrap.Adopted promote(ContinuityStorePort.Session borrowed,WriterContracts.Prepared prepared,WriterContracts.Receipt receipt)throws IOException {
            requireCommitted(borrowed,prepared,receipt);
            if(actualAdopted!=null) {
                StrictJson.require(receipt.eventIdentity().equals(committedIdentity),"initial producer cannot adopt another entry event");
                return actualAdopted;
            }
            DriverBootstrap.Seed finalFixtureSeed=fixture().isPresent()?seed():null;
            DriverBootstrap.Adopted result=DriverBootstrap.initial(this,borrowed,prepared,receipt);
            promotedFixtureSeed=finalFixtureSeed;
            actualAdopted=result;committedIdentity=receipt.eventIdentity();promoted=true;return result;
        }
    }
    private record Capture(ReadinessAuthority.LeaseSnapshot lease,NativeReadinessCollector.SourceQualification source,
            Optional<WriterContracts.Pin> pin,NativeReadiness.Assessment assessment) { }
}

