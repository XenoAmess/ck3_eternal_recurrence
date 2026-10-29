package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.application.readiness.RootNativeCapabilities;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One real physical snapshot serves public facts, terminal reads and explicitly qualified reconciliation. */
public final class RootLifecycleAuthority {
    @FunctionalInterface public interface SourcePort {
        SourceQualification verify(ContinuityStorePort.Session session, NativeObservationPort.TransportSession actualSession,
                G2Source actualSource, ExactRef actualOriginPacket, NativeGameTransport.TransportDiagnostics received,
                Instant deadline) throws IOException;
    }
    @FunctionalInterface public interface CheckedWork<T> { T apply(Lease actual) throws IOException; }
    @FunctionalInterface public interface SnapshotWork<T> { T apply(SnapshotLease actual) throws IOException; }
    @FunctionalInterface public interface ActualDriverAuthority {
        /** Root resolves its actually adopted Driver at use time; no pre-adoption repository or substitute is legal. */
        DriverStateAssembler resolve(ContinuityStorePort.Session borrowed) throws IOException;
    }

    /** Its private constructor and active writer scope distinguish source qualification from copied snapshot data. */
    public static final class SnapshotLease {
        private final RootLifecycleAuthority owner;
        private final DriverObservationAssembler.FullSnapshot full;
        private final Known known;
        private final DriverObservationFacts facts;
        private final Optional<DriverObservationAssembler.Complete> ordinary;
        private final Optional<LifecycleIdentity> terminal;
        private final Optional<LifecycleObservationPort.Snapshot> terminalSnapshot;
        private final Optional<ExactRef> terminalSemantic;
        private final ExactRef hello,heartbeat,driver,semantic;
        private final SourceQualification sources;
        private final Instant until;
        private final Set<String> capabilities;
        private final Supplier<DriverStateSnapshot> canonicalProjection;
        private SnapshotLease(RootLifecycleAuthority owner,DriverObservationAssembler.FullSnapshot full,Known known,
                DriverObservationFacts facts,Optional<DriverObservationAssembler.Complete> ordinary,Optional<LifecycleIdentity> terminal,
                Optional<LifecycleObservationPort.Snapshot> terminalSnapshot,Optional<ExactRef> terminalSemantic,
                ExactRef hello,ExactRef heartbeat,ExactRef driver,ExactRef semantic,SourceQualification sources,
                Instant until,Set<String> capabilities,Supplier<DriverStateSnapshot> canonicalProjection) {
            this.owner=owner;this.full=full;this.known=known;this.facts=facts;this.ordinary=ordinary;this.terminal=terminal;
            this.terminalSnapshot=terminalSnapshot;this.terminalSemantic=terminalSemantic;this.hello=hello;this.heartbeat=heartbeat;
            this.driver=driver;this.semantic=semantic;this.sources=sources;this.until=until;
            this.capabilities=Set.copyOf(capabilities);this.canonicalProjection=canonicalProjection;
        }
        public DriverObservationAssembler.FullSnapshot fullSnapshot() { return full; }
        public Known factsKnown() { return known; }
        public DriverObservationFacts freshFacts() { return facts; }
        /** Complete is actual joined data. This optional does not grant ordinary readiness, action or SAVE authority. */
        public Optional<DriverObservationAssembler.Complete> ordinary() { return ordinary; }
        public Optional<LifecycleIdentity> terminalIdentity() { return terminal; }
        public ExactRef originalHello() { return hello; }
        public ExactRef originalHeartbeat() { return heartbeat; }
        public ExactRef originalDriver() { return driver; }
        public ExactRef originalSemantic() { return semantic; }
        public SourceQualification sourceQualification() { return sources; }
        public Instant validUntil() { return until; }
        public Set<String> bridgeCapabilities() { return capabilities; }
        public void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException {
            Scope scope=owner.active.get();require(scope!=null&&scope.snapshot()==this,"detached physical snapshot has no live source authority");
            owner.assertScope(scope,borrowed,scope.deadline());
        }
    }

    /** Only withObserved can create this narrower canonical terminal admission inside the shared physical scope. */
    public static final class Lease {
        private final SnapshotLease physical;
        private Lease(SnapshotLease physical) { this.physical=physical; }
        public LifecycleIdentity identity() { return physical.terminal.orElseThrow(); }
        public LifecycleObservationPort.Snapshot snapshot() { return physical.terminalSnapshot.orElseThrow(); }
        public DriverObservationFacts freshFacts() { return physical.freshFacts(); }
        public ExactRef originalHello() { return physical.originalHello(); }
        public ExactRef originalHeartbeat() { return physical.originalHeartbeat(); }
        public ExactRef originalSemantic() { return physical.terminalSemantic.orElseThrow(); }
        public SourceQualification sourceQualification() { return physical.sourceQualification(); }
        public Instant validUntil() { return physical.validUntil(); }
        public Set<String> bridgeCapabilities() { return physical.bridgeCapabilities(); }
        public void assertCurrent(ContinuityStorePort.Session borrowed) throws IOException { physical.assertCurrent(borrowed); }
    }
    private record Scope(ContinuityStorePort.Session session,SnapshotLease snapshot,List<WriterContracts.Pin> pins,String head,Instant deadline) { }
    private static final int MAX_ORIGINAL=WriterContracts.MAX_PIN_BYTES;
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final NativeGameTransport transport;
    private final ActualDriverAuthority driver;
    private final DriverObservationAssembler assembler;
    private final G2Source source;
    private final SourcePort sources;
    private final Clock clock;
    private final Duration freshness;
    private final NativeSemanticEvidenceVerifier semantics;
    private final ThreadLocal<Scope> active=new ThreadLocal<>();
    public RootLifecycleAuthority(ContinuityWriter sameWriter,NativeOutcomeArchive sameArchive,NativeGameTransport sameTransport,
            DriverStateAssembler sameDriver,DriverObservationAssembler sameAssembler,G2Source actualSource,
            SourcePort actualSources,Clock clock,Duration freshness) {
        this(sameWriter,sameArchive,sameTransport,borrowed->{sameWriter.requireSession(borrowed);return Objects.requireNonNull(sameDriver);},
                sameAssembler,actualSource,actualSources,clock,freshness);
    }
    /** Constructed before catalog freeze; every actual read resolves the one adopted runtime Driver or explicitly refuses. */
    public RootLifecycleAuthority(ContinuityWriter sameWriter,NativeOutcomeArchive sameArchive,NativeGameTransport sameTransport,
            ActualDriverAuthority actualAdoptedDriver,DriverObservationAssembler sameAssembler,G2Source actualSource,
            SourcePort actualSources,Clock clock,Duration freshness) {
        writer=Objects.requireNonNull(sameWriter);archive=Objects.requireNonNull(sameArchive);transport=Objects.requireNonNull(sameTransport);
        driver=Objects.requireNonNull(actualAdoptedDriver);assembler=Objects.requireNonNull(sameAssembler);source=Objects.requireNonNull(actualSource);
        sources=Objects.requireNonNull(actualSources);this.clock=Objects.requireNonNull(clock);this.freshness=Objects.requireNonNull(freshness);
        semantics=new NativeSemanticEvidenceVerifier((borrowed,ref,maximum)->archive.readArtifact(borrowed,ref,maximum));
        require(archive.writer()==writer,"physical snapshot must share the sole writer/archive");
        require(!freshness.isNegative()&&!freshness.isZero()&&freshness.compareTo(Duration.ofMinutes(1))<=0,"finite physical snapshot freshness required");
    }

    /** No planning input, capability projection, onObserved domain hook, publication or second Native observe. */
    public <T>T withSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,SnapshotWork<T> work) throws IOException {
        return withSnapshot(borrowed,callerDeadline,Optional.empty(),work);
    }
    /**
     * Qualifies the exact original already accepted by the same transport's bounded wait. This branch
     * neither samples nor reads Native again, and DATA equality alone never bypasses the original full qualifier.
     */
    public <T>T withReceivedSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,
            NativeObservationPort.ObservedFrame exactFromWait,SnapshotWork<T> work)throws IOException {
        Objects.requireNonNull(exactFromWait);Objects.requireNonNull(work);
        Instant deadline=deadline(callerDeadline);
        return withSnapshot(borrowed,deadline,Optional.of(exactFromWait),physical->{
            requireSameReceived(exactFromWait,physical.fullSnapshot().actual());
            requireSameReceived(exactFromWait,transport.currentSnapshot(deadline));
            T result=work.apply(physical);
            requireSameReceived(exactFromWait,transport.currentSnapshot(deadline));
            return result;
        });
    }
    private <T>T withSnapshot(ContinuityStorePort.Session borrowed,Instant callerDeadline,
            Optional<NativeObservationPort.ObservedFrame> received,SnapshotWork<T> work)throws IOException {
        Objects.requireNonNull(work);Instant deadline=deadline(callerDeadline);Scope existing=active.get();
        if(existing!=null){
            if(received.isPresent())requireSameReceived(received.orElseThrow(),existing.snapshot().fullSnapshot().actual());
            return borrowed(existing,borrowed,deadline,work);
        }
        requireSession(borrowed);String head=borrowed.head().digest();
        DriverStateAssembler actualDriver=Objects.requireNonNull(driver.resolve(borrowed),"actual adopted Driver authority is unavailable");
        synchronized(transport) {
            final NativeObservationPort.ObservedFrame actual;
            if(received.isPresent()) {
                actual=received.orElseThrow();requireSameReceived(actual,transport.currentSnapshot(deadline));
            }else {
                try { transport.awaitHello(deadline);transport.verifyHeld(deadline);actual=transport.observe(deadline); }
                catch(InterruptedException failure){Thread.currentThread().interrupt();var interrupted=new InterruptedIOException("actual physical snapshot interrupted");interrupted.initCause(failure);throw interrupted;}
                catch(UncheckedIOException failure){throw failure.getCause();}
            }
            require(actual.session().machineId().equals(source.machineId()),"actual physical Native source machine differs");
            ExactRef packet=preserve(borrowed,actual.originalPacket(),MAX_ORIGINAL);
            return actualDriver.withFrozenRawObservation(actual,borrowed,frozen->{
                var facts=frozen.facts();var known=frozen.state();
                require(facts.source().equals(source),"physical original Driver source differs from the installed source");
                var full=assembler.projectFull(actual,facts,packet);
                var diagnostics=transport.diagnostics();
                require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED&&diagnostics.terminalFailure().isEmpty()
                        &&diagnostics.session().filter(actual.session()::equals).isPresent(),"actual held physical transport is unavailable");
                var hello=diagnostics.originalHello().orElseThrow(()->new IOException("actual original hello absent"));
                var heartbeat=diagnostics.latestHeartbeat().orElseThrow(()->new IOException("actual original heartbeat absent"));
                Instant now=clock.instant();
                require(!actual.observedAt().isAfter(now)&&actual.observedAt().plus(freshness).isAfter(now)
                        &&!hello.observedAt().isAfter(actual.observedAt())&&!heartbeat.observedAt().isBefore(hello.observedAt())
                        &&!heartbeat.observedAt().isAfter(now)&&heartbeat.observedAt().plus(freshness).isAfter(now),"physical snapshot or original heartbeat is stale/future/pre-hello");
                require(heartbeat.original().kind()==NativeWire.NoticeKind.HEARTBEAT&&hello.original().pid()==actual.session().game().pid()
                        &&hello.original().connectionGeneration().equals(actual.session().connectionGeneration())
                        &&hello.original().capabilities().contains("game.state.snapshot"),"physical hello does not bind actual Game/generation/snapshot support");
                var helloBody=RootNativeCapabilities.framedObject(hello.original().packet().value());
                require(OpportunityJson.bool(helloBody.get("ck3_build_match"),"ck3_build_match")
                        &&"ready".equals(OpportunityJson.text(helloBody.get("game_adapter_status"),"game_adapter_status")),"physical exact-build Native adapter unavailable");
                ExactRef helloRef=preserve(borrowed,hello.original().packet().value(),1<<20);
                ExactRef heartbeatRef=preserve(borrowed,heartbeat.original().packet().value(),1<<20);
                SourceQualification qualified=Objects.requireNonNull(sources.verify(borrowed,actual.session(),source,packet,diagnostics,deadline));
                qualified.assertCurrent(borrowed);
                RawJson manifest=RawJson.fullMaterial(archive.readArtifact(borrowed,facts.semanticFactsEvidence(),MAX_ORIGINAL));
                ExactRef originalDriver=DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest);
                RawJson driverBytes=RawJson.fullMaterial(archive.readArtifact(borrowed,originalDriver,MAX_ORIGINAL));
                var decoded=DriverObservationEvidenceReader.decode(facts.semanticFactsEvidence(),manifest,driverBytes,actual);
                require(Arrays.equals(decoded.driver().encode(),known.driver().encode())&&decoded.driverVersion()==known.stamp().driverVersion()
                        &&decoded.episodeEpoch()==known.stamp().episodeEpoch()&&decoded.publicRevision().equals(facts.publicRevision())
                        &&decoded.observationVersion()==facts.observationVersion()&&decoded.source().equals(source)
                        &&decoded.originalSemanticFields().equals(facts.originalSemanticFields()),"physical manifest/full Driver producer roundtrip differs");
                Optional<DriverObservationAssembler.Complete> ordinary=Optional.empty();
                Optional<LifecycleIdentity> terminal=Optional.empty();
                Optional<LifecycleObservationPort.Snapshot> terminalSnapshot=Optional.empty();
                Optional<ExactRef> terminalSemantic=Optional.empty();
                var player=LifecycleOriginFactory.currentPlayer(DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES));
                boolean living=player instanceof LifecycleIdentity.Character current
                        &&current.alive()&&current.characterId().equals(known.driver().session().actorId());
                if(living) {
                    var joined=assembler.assemble(actual,facts,packet);
                    require(joined instanceof DriverObservationAssembler.Complete,"actual living physical snapshot is not a complete data join: "+joined);
                    ordinary=Optional.of((DriverObservationAssembler.Complete)joined);
                } else {
                    var projected=LifecycleOriginFactory.project(full,helloRef,originalDriver,qualified.proof());
                    require(projected instanceof LifecycleOriginFactory.Projected,"actual current-player phase is neither same living subject nor a source-bound terminal projection: "+projected);
                    var phase=(LifecycleOriginFactory.Projected)projected;
                    terminal=Optional.of(phase.identity());
                    terminalSnapshot=Optional.of(new LifecycleObservationPort.Snapshot(actual,source,phase.semantic(),known,packet));
                    terminalSemantic=Optional.of(preserve(borrowed,DriverJson.encode(phase.semantic()),MAX_ORIGINAL));
                }
                ExactRef semantic=preserve(borrowed,DriverJson.encode(full.semantic()),MAX_ORIGINAL);
                Instant until=earliest(deadline,actual.observedAt().plus(freshness),heartbeat.observedAt().plus(freshness));
                var captured=new SnapshotLease(this,full,known,facts,ordinary,terminal,terminalSnapshot,terminalSemantic,helloRef,heartbeatRef,
                        originalDriver,semantic,qualified,until,Set.copyOf(hello.original().capabilities()),frozen::projection);
                List<WriterContracts.Pin> pins=new ArrayList<>();
                for(ExactRef ref:List.of(packet,helloRef,heartbeatRef,facts.semanticFactsEvidence(),originalDriver,semantic))
                    pins.add(borrowed.capturePin(ref,MAX_ORIGINAL));
                if(qualified.proof().isPresent())pins.add(borrowed.capturePin(qualified.proof().orElseThrow(),16<<20));
                if(terminalSemantic.isPresent())pins.add(borrowed.capturePin(terminalSemantic.orElseThrow(),MAX_ORIGINAL));
                Scope scope=new Scope(borrowed,captured,List.copyOf(pins),head,deadline);
                require(active.get()==null,"physical callback cannot replace another frozen observation");active.set(scope);
                try{return borrowed(scope,borrowed,deadline,work);}finally{active.remove();}
            });
        }
    }

    /** The same physical producer seals and independently replays four SEM originals, without ordinary eligibility or domain hooks. */
    public SessionPorts.SemanticEvidence semantic(ContinuityStorePort.Session borrowed,SessionPorts.SessionIdentity owner,
            Instant callerDeadline)throws IOException{
        Objects.requireNonNull(owner);
        return withSnapshot(borrowed,callerDeadline,physical->semantic(borrowed,owner,physical));
    }
    /** Seals the same held physical lease; another owner, session, thread or detached lease cannot recapture or mint SEM. */
    public SessionPorts.SemanticEvidence semantic(ContinuityStorePort.Session borrowed,SessionPorts.SessionIdentity owner,
            SnapshotLease physical)throws IOException{
            Objects.requireNonNull(owner);Objects.requireNonNull(physical);physical.assertCurrent(borrowed);
            require(physical.owner==this&&active.get()!=null&&active.get().snapshot()==physical,
                    "SEM must borrow this authority's exact active original physical snapshot");
            var actual=physical.fullSnapshot().actual().session();
            require(owner.machineId().equals(actual.machineId())&&owner.game().equals(actual.game())
                    &&owner.sessionId().equals(actual.sessionId()),"physical SEM belongs to another actual owned session");
            var frame=physical.ordinary().orElseThrow(()->new IOException("actual living actor/Driver data is unavailable for ordinary SEM"));
            ExactRef stamp=preserve(borrowed,NativeDriverStamp.encode(frame,physical.factsKnown()),16<<10);
            var evidence=new SessionPorts.SemanticEvidence(frame.identity(),physical.originalSemantic(),
                    physical.fullSnapshot().originalEvidence(),stamp,physical.originalDriver(),frame.observedAt());
            semantics.verify(borrowed,owner,evidence);physical.assertCurrent(borrowed);return evidence;
    }

    /** Canonical terminal admission remains stronger than a public physical snapshot. */
    public <T>T withObserved(ContinuityStorePort.Session borrowed,Instant callerDeadline,CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(work);
        return withSnapshot(borrowed,callerDeadline,physical->{
            require(physical.terminalIdentity().isPresent(),"actual same living subject is not a terminal lifecycle origin");
            physical.assertCurrent(borrowed);
            require(physical.canonicalProjection.get() instanceof DriverStateSnapshot.Complete,
                    "original complete canonical Driver or same active terminal action is unresolved; physical data alone grants no terminal admission");
            Lease terminal=new Lease(physical);
            T result=work.apply(terminal);terminal.assertCurrent(borrowed);return result;
        });
    }

    public <T>T current(ContinuityStorePort.Session borrowed,LifecycleIdentity expected,Instant callerDeadline,CheckedWork<T> work) throws IOException {
        Objects.requireNonNull(expected);Objects.requireNonNull(work);Instant deadline=deadline(callerDeadline);Scope scope=active.get();
        if(scope!=null)require(scope.snapshot().terminalIdentity().filter(expected::sameGuardFrame).isPresent(),"nested terminal query must retain the exact outer original frame");
        return withObserved(borrowed,deadline,actual->{
            require(expected.sameSession(actual.identity()),"terminal guard crossed the actual old episode/subject or physical session");
            return work.apply(actual);
        });
    }
    /** A domain writer must reject an enclosing observation before preview/commit, rather than detect its changed Head afterwards. */
    public void requireOutsideObservationScope(ContinuityStorePort.Session borrowed)throws IOException{
        requireSession(borrowed);
        require(active.get()==null,"domain publication must leave the actual physical observation scope before preview or commit");
        Objects.requireNonNull(driver.resolve(borrowed),"actual adopted Driver authority is unavailable").requireOutsideObservationScope(borrowed);
    }
    private <T>T borrowed(Scope scope,ContinuityStorePort.Session borrowed,Instant deadline,SnapshotWork<T> work)throws IOException{
        assertScope(scope,borrowed,deadline);T value=work.apply(scope.snapshot());assertScope(scope,borrowed,deadline);return value;
    }
    private void assertScope(Scope scope,ContinuityStorePort.Session borrowed,Instant deadline)throws IOException{
        requireSession(borrowed);require(scope.session()==borrowed&&active.get()==scope,"physical read escaped the original borrowed writer/frozen callback");
        require(scope.head().equals(borrowed.head().digest()),"writer changed inside observation-only physical scope");
        Instant now=clock.instant();require(!now.isBefore(scope.snapshot().fullSnapshot().actual().observedAt())&&now.isBefore(scope.snapshot().validUntil())
                &&now.isBefore(scope.deadline())&&now.isBefore(deadline),"actual physical lease/caller deadline expired");
        transport.verifyHeld(deadline);scope.snapshot().sourceQualification().assertCurrent(borrowed);
        for(var pin:scope.pins())borrowed.verifyPin(pin);
    }
    private void requireSession(ContinuityStorePort.Session borrowed)throws IOException{
        writer.requireSession(borrowed);borrowed.requireWriter(archive.artifactStore().originalWriterLock());
        require(borrowed.head().state().machineId().equals(source.machineId()),"physical writer/source machine differs");
    }
    private Instant deadline(Instant supplied){Objects.requireNonNull(supplied);Instant local=clock.instant().plus(freshness);Instant result=supplied.isBefore(local)?supplied:local;require(clock.instant().isBefore(result),"physical caller deadline expired before Native I/O");return result;}
    private ExactRef preserve(ContinuityStorePort.Session borrowed,byte[] actual,int limit)throws IOException{
        require(actual.length>0&&actual.length<=limit,"complete physical original exceeds its finite lane");
        ExactRef ref=archive.preserveArtifact(borrowed,actual,limit);require(Arrays.equals(actual,archive.readArtifact(borrowed,ref,limit)),"actual physical archive readback differs");return ref;
    }
    private static Instant earliest(Instant first,Instant second,Instant third){Instant result=first.isBefore(second)?first:second;return result.isBefore(third)?result:third;}
    private void requireSameReceived(NativeObservationPort.ObservedFrame expected,NativeObservationPort.ObservedFrame current)throws IOException{
        require(expected.session().equals(current.session())&&expected.snapshotId().equals(current.snapshotId())
                &&expected.nativeRevision().equals(current.nativeRevision())&&expected.observedAt().equals(current.observedAt())
                &&expected.state().equals(current.state())&&Arrays.equals(expected.originalPacket(),current.originalPacket()),
                "received physical snapshot differs from the actual held original accepted by this transport");
        // Equal DATA cannot identify a received occurrence: A/B/A can share all values and a fixed clock.
        // Only the sole transport producer can bind expected to its actual accepted frame, and its
        // retained historical token must still identify the actual current frame at every use.
        transport.acceptedSnapshotRevision(expected).requireOriginal(current);
    }
}
