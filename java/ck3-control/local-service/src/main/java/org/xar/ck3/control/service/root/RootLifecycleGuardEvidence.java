package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.RootNativeCapabilities;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Immutable physical originals for the dedicated terminal phase; replay never acquires a current authority lease. */
public final class RootLifecycleGuardEvidence {
    public static final String SCHEMA="xar.java.root-lifecycle-guard-original-basis/v2";
    private static final Set<String> FIELDS=Set.of("schema","operation","authority_id","identity","source","semantic","heartbeat","bridge_capabilities","close_admission","writer_point");
    private RootLifecycleGuardEvidence() { }
    public record Replay(LifecycleIdentity identity,DriverObservationAssembler.FullSnapshot original,OpportunityJson.Obj semantic,
            Set<String> bridgeCapabilities,Optional<ExactRef> closeAdmission) {
        public Replay {bridgeCapabilities=Set.copyOf(bridgeCapabilities);java.util.Objects.requireNonNull(closeAdmission);}
    }
    static GuardEvidence binding(RootLifecycleAuthority.Lease lease,G2Source source,String sessionId,OperationKey operation,
            Instant deadline,WriterContracts.Head head,String authorityId,Clock clock,ContinuityStorePort.Session session,
            ActionPorts.OutcomeArchive archive,OriginalEvidencePort originals,Optional<ExactRef> closeAdmission) throws IOException {
        lease.assertCurrent(session);LifecycleIdentity actual=lease.identity();Instant now=clock.instant();
        require(actual.sessionId().equals(sessionId)&&actual.machineId().equals(head.state().machineId())&&lease.snapshot().source().equals(source),"terminal guard crossed actual source/writer/session");
        require(!now.isBefore(actual.observedAt())&&now.isBefore(lease.validUntil())&&now.isBefore(deadline),"terminal guard physical lease expired");
        for(ExactRef ref:List.of(actual.nativeEvidence(),actual.capabilityEvidence(),actual.evidence().observationManifest(),actual.evidence().originalDriver(),lease.originalSemantic(),lease.originalHeartbeat()))
            exact(ref,originals.read(session,ref,WriterContracts.MAX_PIN_BYTES));
        if(actual.evidence().completeSourceQualification().isPresent()) {
            ExactRef historical=actual.evidence().completeSourceQualification().orElseThrow();
            exact(historical,originals.read(session,historical,16<<20));
        }
        if(closeAdmission.isPresent())exact(closeAdmission.orElseThrow(),archive.loadMaterial(closeAdmission.orElseThrow()).bytes());
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("operation",operation.value());row.put("authority_id",authorityId);
        row.set("writer_point",StrictJson.object().put("sequence",head.state().sequence()).put("digest",head.digest()));
        row.set("identity",LifecycleIdentityCodec.encode(actual));row.set("source",source.sourceRef().toJson());
        row.set("semantic",lease.originalSemantic().toJson());row.set("heartbeat",lease.originalHeartbeat().toJson());
        var capabilities=row.putArray("bridge_capabilities");lease.bridgeCapabilities().stream().sorted().forEach(capabilities::add);
        if(closeAdmission.isPresent())row.set("close_admission",closeAdmission.orElseThrow().toJson());else row.putNull("close_admission");
        RawJson body=new RawJson(StrictJson.canonical(row,64<<10));ExactRef basis=archive.preserveMaterial(body);
        require(body.equals(archive.loadMaterial(basis)),"terminal original guard basis archive changed");
        GuardEvidence guard=new GuardEvidence(new CommandOrigin.LifecycleTerminal(actual),source,sessionId,actual.connectionGeneration(),operation,
                actual.nativeEvidence(),actual.capabilityEvidence(),authorityId,actual.observedAt(),lease.validUntil().isBefore(deadline)?lease.validUntil():deadline,List.of(basis));
        verify(guard,archive,session,originals);lease.assertCurrent(session);return guard;
    }
    public static void verify(GuardEvidence guard,ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session session,
            OriginalEvidencePort originals)throws IOException {replay(guard,archive,session,originals);}
    public static Replay replay(GuardEvidence guard,ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session session,
            OriginalEvidencePort originals)throws IOException {
        require(guard.origin() instanceof CommandOrigin.LifecycleTerminal&&guard.supportingEvidence().size()==1,"dedicated terminal originals are unavailable");
        ExactRef basis=guard.supportingEvidence().getFirst();RawJson body=archive.loadMaterial(basis);exact(basis,body.bytes());
        exact(basis,originals.read(session,basis,64<<10));
        var row=StrictJson.object(StrictJson.parse(body.bytes(),64<<10),FIELDS);
        var point=StrictJson.object(row.get("writer_point"),Set.of("sequence","digest"));
        long sequence=StrictJson.integer(point.get("sequence"),java.math.BigInteger.ZERO,java.math.BigInteger.valueOf(9_007_199_254_740_991L)).longValueExact();
        session.requireHistoricalState(sequence,StrictJson.text(point.get("digest")));
        LifecycleIdentity identity=LifecycleIdentityCodec.decode(row.get("identity"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&guard.operation().value().equals(StrictJson.text(row.get("operation")))
                &&guard.authorityId().equals(StrictJson.text(row.get("authority_id")))&&identity.equals(guard.origin().requireLifecycleTerminal())
                &&ExactRef.fromJson(row.get("source")).equals(guard.source().sourceRef()),"archived terminal guard origin/source/operation changed");
        byte[] packet=originals.read(session,identity.nativeEvidence(),WriterContracts.MAX_PIN_BYTES);exact(identity.nativeEvidence(),packet);
        ExactRef manifestRef=identity.evidence().observationManifest(),driverRef=identity.evidence().originalDriver();
        RawJson manifest=RawJson.fullMaterial(originals.read(session,manifestRef,WriterContracts.MAX_PIN_BYTES));exact(manifestRef,manifest.bytes());
        require(DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest).equals(driverRef),"terminal complete Driver is not the exact original manifest Driver");
        RawJson driver=RawJson.fullMaterial(originals.read(session,driverRef,WriterContracts.MAX_PIN_BYTES));exact(driverRef,driver.bytes());
        var actual=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,packet);
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,driver,actual);
        var full=new DriverObservationAssembler().projectFull(actual,facts,identity.nativeEvidence());
        var projection=LifecycleOriginFactory.project(full,identity.capabilityEvidence(),driverRef,identity.evidence().completeSourceQualification());
        require(projection instanceof LifecycleOriginFactory.Projected,"archived actual current-player/old-Driver join is not terminal");
        var projected=(LifecycleOriginFactory.Projected)projection;
        require(projected.identity().equals(identity)&&facts.source().equals(guard.source())&&identity.observedAt().equals(guard.observedAt())
                &&!guard.validUntil().isBefore(guard.observedAt()),"archived terminal original fields or derived phase differ");
        ExactRef semanticRef=ExactRef.fromJson(row.get("semantic"));byte[] semantic=originals.read(session,semanticRef,WriterContracts.MAX_PIN_BYTES);exact(semanticRef,semantic);
        require(DriverJson.object(semantic,DriverJson.MAX_NATIVE_BYTES).equals(projected.semantic()),"archived terminal semantic projection differs from full original native/Driver join");
        byte[] hello=originals.read(session,identity.capabilityEvidence(),1<<20);exact(identity.capabilityEvidence(),hello);
        var helloBody=RootNativeCapabilities.framedObject(hello);
        require(new OpportunityJson.Text("hello").equals(helloBody.get("type"))
                &&OpportunityJson.integer(helloBody.get("pid"),"pid").longValueExact()==identity.game().pid()
                &&OpportunityJson.integer(helloBody.get("connection_generation"),"connection_generation").equals(identity.connectionGeneration())
                &&OpportunityJson.bool(helloBody.get("ck3_build_match"),"ck3_build_match")
                &&"ready".equals(OpportunityJson.text(helloBody.get("game_adapter_status"),"game_adapter_status")),"archived terminal hello crossed actual physical Game/adapter");
        var actualCapabilities=new java.util.HashSet<String>();for(var cap:OpportunityJson.array(helloBody.get("capabilities"),"capabilities"))actualCapabilities.add(OpportunityJson.text(cap,"capability"));
        var caps=row.get("bridge_capabilities");require(caps!=null&&caps.isArray()&&caps.size()<=4096,"bounded original terminal capabilities required");
        var recordedCapabilities=new java.util.HashSet<String>();for(var cap:caps)require(recordedCapabilities.add(StrictJson.text(cap)),"duplicate terminal capability");
        require(recordedCapabilities.equals(actualCapabilities)&&actualCapabilities.contains("game.state.snapshot"),"terminal capabilities differ from the received original hello");
        ExactRef heartbeatRef=ExactRef.fromJson(row.get("heartbeat"));byte[] heartbeat=originals.read(session,heartbeatRef,1<<20);exact(heartbeatRef,heartbeat);
        require(new OpportunityJson.Text("heartbeat").equals(RootNativeCapabilities.framedObject(heartbeat).get("type")),"archived actual terminal heartbeat required");
        if(identity.evidence().completeSourceQualification().isPresent()) {
        ExactRef sourceProof=identity.evidence().completeSourceQualification().orElseThrow();byte[] proof=originals.read(session,sourceProof,16<<20);exact(sourceProof,proof);
        var qualified=DriverJson.object(proof,16<<20);
        require(new OpportunityJson.Text("xar.java-root-native-source-proof/v2").equals(qualified.get("schema"))
                &&new OpportunityJson.Text(identity.machineId()).equals(qualified.get("machine_id"))
                &&new OpportunityJson.Text(identity.sessionId()).equals(qualified.get("session_id"))
                &&DriverObservationEvidenceReader.reference(qualified.get("source")).equals(guard.source().sourceRef()),"archived complete source qualification binding differs");
        }
        Optional<ExactRef> admission=row.get("close_admission").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("close_admission")));
        require(admission.isPresent()==guard.operation().equals(LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL.key()),"terminal Close is missing its dedicated original legal-modal admission");
        if(admission.isPresent())exact(admission.orElseThrow(),archive.loadMaterial(admission.orElseThrow()).bytes());
        return new Replay(identity,full,projected.semantic(),recordedCapabilities,admission);
    }
    static void exact(ExactRef ref,byte[] raw){require(ref.bytes()==raw.length&&ref.sha256().equals(DriverJson.sha256(raw)),"terminal original bytes/SHA differ");}
}

