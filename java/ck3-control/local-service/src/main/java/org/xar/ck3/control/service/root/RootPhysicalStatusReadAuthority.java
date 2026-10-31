package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The actual per-Game raw Status observer. No Driver, player, episode, ordinary Ready or submit capability is created. */
public final class RootPhysicalStatusReadAuthority implements PhysicalStatusReadAuthority {
    private static final String SCHEMA="xar.java-root-physical-status-read-basis/v1";
    private static final String AUTHORITY="java.root.physical-sentinel-status/v1";
    private static final int PACKET=Math.min(DriverJson.MAX_NATIVE_BYTES+4,ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
    private static final int PROOF=16<<20, BASIS=128<<10;
    private final RootRuntimeContext context;
    private final Duration validity;
    private final ThreadLocal<Scope> active=new ThreadLocal<>();
    private static final class Guards { private PlanningReadRequest request;private int issued; }
    private record Scope(ContinuityStorePort.Session same,Lease lease,NativeReadinessCollector.SourceQualification source,
            Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata,WriterContracts.Head head,Instant deadline,List<WriterContracts.Pin> pins,Guards guards) { }

    public RootPhysicalStatusReadAuthority(RootRuntimeContext actual,Duration validity) {
        context=Objects.requireNonNull(actual);this.validity=Objects.requireNonNull(validity);
        require(!validity.isNegative()&&!validity.isZero()&&validity.compareTo(Duration.ofMinutes(1))<=0,
                "finite positive physical Status validity required");
    }
    public void requireContext(RootRuntimeContext actual)throws IOException {
        if(actual!=context)throw new IOException("physical Status observer belongs to another actual runtime context");
    }
    @Override public <T>T withObserved(ContinuityStorePort.Session same,Instant deadline,CheckedWork<T> work)throws IOException {
        Objects.requireNonNull(work);context.writer().requireSession(same);context.requireCurrent(deadline);
        require(same.head().state().machineId().equals(context.source().machineId()),"physical Status source differs from the original writer machine");
        Scope held=active.get();
        if(held!=null)return current(same,held.lease().identity(),deadline,work);
        // An ordinary frozen observation cannot be silently replaced by a raw read observation.
        if(context.optionalDriverProducer().isPresent())context.adopted().authority().requireOutsideObservationScope(same);
        var transport=context.transport();
        // Internal Status reads use the actual accepted state. Requiring an undelivered new snapshot can deadlock a paused Game.
        var frame=transport.currentSnapshot(deadline);
        require(!frame.observedAt().isAfter(context.clock().instant()),"actual native Status observation cannot be from the future");
        var diagnostics=transport.diagnostics();
        require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                &&diagnostics.session().orElseThrow().equals(frame.session()),"actual held physical Status HELLO/session absent");
        require(frame.session().game().equals(context.game().generation())&&frame.session().machineId().equals(context.game().machineId())
                &&frame.session().sessionId().equals(context.game().sessionId()),"physical Status snapshot crossed actual Managed Game");
        ExactRef nativeRef=preserve(same,frame.originalPacket(),PACKET);
        ExactRef hello=preserve(same,diagnostics.originalHello().orElseThrow().original().packet().value(),1<<20);
        ExactRef heartbeat=preserve(same,diagnostics.latestHeartbeat().orElseThrow().original().packet().value(),1<<20);
        var source=context.sources().verifyPhysicalOrigin(same,frame.session(),context.source(),nativeRef,diagnostics,deadline);
        var metadata=context.sources().optionalMetadata(same,source);
        var identity=new PhysicalStatusIdentity(frame.session(),frame.snapshotId(),frame.nativeRevision(),context.source(),nativeRef,
                hello,heartbeat,source.proof(),metadata.map(RootNativeSourceAuthority.QualifiedMetadata::epochManifest),frame.observedAt());
        Set<String> caps=requireOriginals(same,identity,context.originals());
        Instant until=context.clock().instant().plus(validity);if(deadline.isBefore(until))until=deadline;
        var lease=new Lease(frame,identity,caps,until);
        var pins=new java.util.ArrayList<WriterContracts.Pin>();
        for(ExactRef ref:List.of(nativeRef,hello,heartbeat))
            pins.add(same.capturePin(ref,ref==nativeRef?PACKET:WriterContracts.MAX_PIN_BYTES));
        for(ExactRef ref:java.util.stream.Stream.concat(identity.sourceQualification().stream(),identity.epochManifest().stream()).toList())
            pins.add(same.capturePin(ref,PROOF));
        var scope=new Scope(same,lease,source,metadata,same.head(),deadline,List.copyOf(pins),new Guards());
        active.set(scope);
        try { assertCurrent(scope,same,deadline);requireStatusCapability(same,identity,context.originals());
            T result=work.apply(lease);assertCurrent(scope,same,deadline);return result; }
        finally { active.remove(); }
    }
    @Override public <T>T current(ContinuityStorePort.Session same,PhysicalStatusIdentity expected,Instant deadline,CheckedWork<T> work)throws IOException {
        Objects.requireNonNull(expected);Objects.requireNonNull(work);Scope scope=active.get();
        if(scope==null||scope.same()!=same||!scope.lease().identity().equals(expected))
            throw new IOException("actual identical held physical Status scope is unavailable");
        assertCurrent(scope,same,deadline);T result=work.apply(scope.lease());assertCurrent(scope,same,deadline);return result;
    }
    @Override public void requireOutside(ContinuityStorePort.Session same)throws IOException {
        context.writer().requireSession(same);
        if(active.get()!=null)throw new IOException("mutation cannot run inside the actual source-bound physical Status read scope");
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
        Objects.requireNonNull(request);RootUnknownSentinelReadProfile.requirePhysicalProfile(contract);
        require(context.readCatalog().containsIdentity(contract)&&contract.operation().equals(request.operation())
                &&request.arguments().members().isEmpty()&&request.source().equals(context.source())
                &&request.sessionId().equals(context.game().sessionId()),"physical Status read is not the exact installed source/empty query");
        var scope=active.get();if(scope==null)throw new IOException("physical Status guard has no actual held source scope");
        var expected=request.origin().requirePhysicalStatusOnly();
        return current(scope.same(),expected,request.deadline(),lease->{
            require(sameHead(head,scope.same().head())&&sameHead(head,scope.head()),"physical Status guard lost the exact current writer Head");
            requireStatusCapability(scope.same(),lease.identity(),context.originals());
            var guards=scope.guards();
            if(guards.issued==0) {
                requireExactSnapshot(context.transport().currentSnapshot(request.deadline()),lease.frame());
                guards.request=request;
            } else require(guards.issued==1&&guards.request==request,
                    "physical Status scope admits only the before/after guards of one identical actual query");
            Instant validUntil=request.deadline().isBefore(lease.validUntil())?request.deadline():lease.validUntil();
            var body=StrictJson.object();body.put("schema",SCHEMA);body.set("identity",PhysicalStatusIdentityCodec.encode(expected));
            body.put("contract_id",contract.contractId()).put("operation",request.operation().value()).put("authority_id",AUTHORITY);
            body.put("writer_sequence",head.state().sequence()).put("writer_digest",head.digest());
            body.put("valid_until",validUntil.toString());
            ExactRef basis=preserve(scope.same(),StrictJson.canonical(body),BASIS);
            var binding=new GuardEvidence(new CommandOrigin.PhysicalStatusOnly(expected),context.source(),expected.sessionId(),
                    expected.connectionGeneration(),request.operation(),expected.nativeEvidence(),expected.helloEvidence(),AUTHORITY,
                    expected.observedAt(),validUntil,List.of(basis));
            guards.issued++;
            return new PlanningReadGuard(binding,new PlanningReadGuard.PhysicalStatus(expected),PhysicalStatusIdentityCodec.bindingSha256(expected));
        });
    }
    @Override public PhysicalStatusIdentity verifyArchived(GuardEvidence binding,ActionPorts.OutcomeArchive archive,
            ContinuityStorePort.Session same,OriginalEvidencePort originals)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(archive);Objects.requireNonNull(originals);
        require(originals==context.originals(),"physical Status replay must use the same installed original-evidence reader");
        var identity=binding.origin().requirePhysicalStatusOnly();
        require(identity.source().equals(context.source())&&identity.game().equals(context.game().generation())
                &&identity.sessionId().equals(context.game().sessionId()),"physical Status replay crossed its actual runtime Game/source/session");
        return verifyArchivedData(binding,same,originals);
    }
    /** Complete retained guard DATA replay; no live scope, current Game qualification or permission is minted. */
    public static PhysicalStatusIdentity verifyArchivedData(GuardEvidence binding,ContinuityStorePort.Session same,
            OriginalEvidencePort originals)throws IOException {
        Objects.requireNonNull(binding);Objects.requireNonNull(same);Objects.requireNonNull(originals);
        var identity=binding.origin().requirePhysicalStatusOnly();
        require(identity.machineId().equals(same.head().state().machineId())&&binding.source().equals(identity.source())
                &&binding.authorityId().equals(AUTHORITY)&&binding.operation().value().equals(PhysicalStatusIdentity.OPERATION)
                &&binding.nativeEvidence().equals(identity.nativeEvidence())&&binding.capabilityEvidence().equals(identity.helloEvidence())
                &&binding.observedAt().equals(identity.observedAt())&&binding.supportingEvidence().size()==1,
                "archived physical Status guard changed its actual source/origin/sole original basis");
        var body=StrictJson.object(StrictJson.parse(read(same,binding.supportingEvidence().getFirst(),BASIS,originals),BASIS),
                Set.of("schema","identity","contract_id","operation","authority_id","writer_sequence","writer_digest","valid_until"));
        require(SCHEMA.equals(StrictJson.text(body.get("schema")))&&PhysicalStatusIdentityCodec.decode(body.get("identity")).equals(identity)
                &&PhysicalStatusIdentity.CONTRACT_ID.equals(StrictJson.text(body.get("contract_id")))
                &&binding.operation().value().equals(StrictJson.text(body.get("operation")))
                &&binding.authorityId().equals(StrictJson.text(body.get("authority_id")))
                &&binding.validUntil().equals(Instant.parse(StrictJson.text(body.get("valid_until")))),
                "physical Status original basis changed its exact finite guard binding");
        long sequence=StrictJson.integer(body.get("writer_sequence"),0,StrictJson.MAX_SAFE_INTEGER);
        same.requireHistoricalHead(sequence,StrictJson.text(body.get("writer_digest")));
        require(requireOriginals(same,identity,originals).contains(PhysicalStatusIdentity.CAPABILITY),
                "archived physical Status original HELLO lost its required capability");return identity;
    }
    private void assertCurrent(Scope scope,ContinuityStorePort.Session same,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        require(active.get()==scope&&scope.same()==same&&context.clock().instant().isBefore(scope.deadline())
                &&context.clock().instant().isBefore(scope.lease().validUntil())&&sameHead(same.head(),scope.head()),
                "physical Status source scope escaped, expired or changed canonical history");
        scope.source().assertCurrent(same);
        if(scope.metadata().isPresent())scope.metadata().orElseThrow().requireCurrent(same);
        var actual=context.transport().currentSnapshot(deadline);var expected=scope.lease().frame();
        require(actual.session().equals(expected.session())&&!actual.observedAt().isBefore(expected.observedAt())
                &&actual.nativeRevision().compareTo(expected.nativeRevision())>=0,
                "actual Status transport/source session or native chronology regressed");
        if(actual.nativeRevision().equals(expected.nativeRevision()))requireExactSnapshot(actual,expected);
        var diagnostics=context.transport().diagnostics();
        require(diagnostics.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED
                &&diagnostics.session().orElseThrow().equals(expected.session()),"physical Status transport custody was lost");
        exact(scope.lease().identity().helloEvidence(),diagnostics.originalHello().orElseThrow().original().packet().value());
        // Later heartbeats are allowed; the originally received heartbeat remains pinned and replayed.
        for(var pin:scope.pins())same.verifyPin(pin);
    }
    private static Set<String> requireOriginals(ContinuityStorePort.Session same,PhysicalStatusIdentity identity,OriginalEvidencePort originals)throws IOException {
        var nativePacket=NativeWire.decode(read(same,identity.nativeEvidence(),PACKET,originals));
        require(nativePacket instanceof NativeWire.Snapshot,"physical Status original is not a complete native snapshot packet");
        var snapshot=(NativeWire.Snapshot)nativePacket;
        require(snapshot.snapshotId().equals(identity.snapshotId())&&snapshot.revision().equals(identity.nativeRevision()),
                "physical Status original snapshot header drift");
        DriverJson.object(snapshot.state().value(),DriverJson.MAX_NATIVE_BYTES);
        var originalHello=NativeWire.decode(read(same,identity.helloEvidence(),1<<20,originals));
        require(originalHello instanceof NativeWire.Hello,"physical Status original HELLO packet absent");
        var hello=(NativeWire.Hello)originalHello;
        require(hello.pid()==identity.game().pid()&&hello.connectionGeneration().equals(identity.connectionGeneration())
                &&hello.buildMatch()&&hello.adapterStatus().equals("ready")&&hello.capabilities().contains("game.state.snapshot"),
                "physical Status HELLO source/build/capability drift");
        var hb=NativeWire.decode(read(same,identity.heartbeatEvidence(),1<<20,originals));
        require(hb instanceof NativeWire.Notice notice&&notice.kind()==NativeWire.NoticeKind.HEARTBEAT,"physical Status original heartbeat absent");
        if(identity.sourceQualification().isEmpty())return Set.copyOf(hello.capabilities());
        ExactRef qualification=identity.sourceQualification().orElseThrow();
        ExactRef manifest=identity.epochManifest().orElseThrow(()->new IOException("supplied historical source proof lacks its original epoch manifest"));
        var proof=RootArchivedNativeSourceReader.readData(qualification,read(same,qualification,PROOF,originals));
        String observed=proof.observedAtUtc();
        require(Instant.parse(observed).toString().equals(observed)&&!Instant.parse(observed).isBefore(identity.observedAt()),
                "original physical source qualification predates its actual native observation");
        require(identity.machineId().equals(proof.machineId())&&identity.sessionId().equals(proof.sessionId())
                &&proof.source().equals(identity.source().sourceRef())&&proof.sourceEpochManifest().equals(manifest)
                &&manifest.sha256().equals(proof.ownerSourceEpoch())
                &&proof.gameExecutable().sha256().equals(hello.gameSha256())&&!proof.completeEvidenceClosure().isEmpty(),
                "physical Status original complete source qualification drift");
        RootArchivedNativeSourceReader.readEpochData(manifest,read(same,manifest,PROOF,originals),proof);
        return Set.copyOf(hello.capabilities());
    }
    private void requireStatusCapability(ContinuityStorePort.Session same,PhysicalStatusIdentity identity,OriginalEvidencePort originals)throws IOException {
        Scope scope=active.get();
        require(scope!=null&&scope.same()==same&&scope.lease().identity().equals(identity),
                "live Status capability refusal requires its actual source-bound writer scope");
        assertCurrent(scope,same,scope.deadline());
        try {
            StatusCapabilityFailure.requireAdvertised(new CommandOrigin.PhysicalStatusOnly(identity),identity.source(),identity.helloEvidence(),
                    read(same,identity.helloEvidence(),1<<20,originals));
        } catch(StatusCapabilityFailure failure) {
            // A real source, custody, Head or deadline failure takes precedence over an unsupported feature.
            assertCurrent(scope,same,scope.deadline());throw failure;
        }
    }

    private ExactRef preserve(ContinuityStorePort.Session same,byte[] bytes,int maximum)throws IOException {
        ExactRef ref=context.archive().preserveArtifact(same,bytes,maximum);exact(ref,context.archive().readArtifact(same,ref,maximum));return ref;
    }
    private static byte[] read(ContinuityStorePort.Session same,ExactRef ref,int maximum,OriginalEvidencePort originals)throws IOException {
        byte[] bytes=originals.read(same,ref,maximum);exact(ref,bytes);return bytes;
    }
    private static void exact(ExactRef ref,byte[] bytes)throws IOException {
        if(bytes.length!=ref.bytes()||!ActionCodec.sha256(bytes).equals(ref.sha256()))throw new IOException("physical Status immutable original bytes/SHA changed");
    }
    private static void requireExactSnapshot(NativeObservationPort.ObservedFrame actual,NativeObservationPort.ObservedFrame expected) {
        require(actual.session().equals(expected.session())&&actual.snapshotId().equals(expected.snapshotId())
                &&actual.nativeRevision().equals(expected.nativeRevision())&&actual.observedAt().equals(expected.observedAt())
                &&Arrays.equals(actual.originalPacket(),expected.originalPacket())&&Arrays.equals(actual.state().bytes(),expected.state().bytes()),
                "physical Status before guard requires its exact actual accepted original snapshot");
    }
    private static boolean sameHead(WriterContracts.Head left,WriterContracts.Head right) {
        return left.digest().equals(right.digest())&&left.documents().equals(right.documents())&&left.absent().equals(right.absent())
                &&left.indexRepairs().equals(right.indexRepairs())&&left.snapshotNeedsRecovery()==right.snapshotNeedsRecovery();
    }
    private static void require(boolean condition,String message){StrictJson.require(condition,message);}
}
