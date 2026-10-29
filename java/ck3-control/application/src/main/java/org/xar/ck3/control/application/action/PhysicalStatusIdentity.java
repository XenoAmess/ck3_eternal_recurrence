package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;

/** Actual raw physical observation facts for one finite read. This contains no Driver, actor, episode or action authority. */
public record PhysicalStatusIdentity(NativeObservationPort.TransportSession transport,String snapshotId,BigInteger nativeRevision,
        G2Source source,ExactRef nativeEvidence,ExactRef helloEvidence,ExactRef heartbeatEvidence,java.util.Optional<ExactRef> sourceQualification,
        java.util.Optional<ExactRef> epochManifest,Instant observedAt) {
    public static final String CONTRACT_ID="java.tactical-daily-sentinel.status.physical-observation.v1";
    public static final String OPERATION="research-query-tactical-daily-sentinel-v1";
    public static final String PERMISSION="tactical-daily-sentinel-status-v1";
    public static final String CAPABILITY="game.command.research-query-tactical-daily-sentinel-v1";
    public PhysicalStatusIdentity {
        Objects.requireNonNull(transport);StrictJson.text(snapshotId);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(source);
        StrictJson.require(nativeRevision.signum()>=0&&nativeRevision.compareTo(StrictJson.UINT64_MAX)<=0,"actual uint64 native revision required");
        StrictJson.require(source.machineId().equals(transport.machineId()),"physical read source crossed its actual machine");
        Objects.requireNonNull(sourceQualification);Objects.requireNonNull(epochManifest);
        for(ExactRef original:List.of(nativeEvidence,helloEvidence,heartbeatEvidence))
            StrictJson.require(original.bytes()>0,"actual nonempty physical read original required");
        for(ExactRef original:java.util.stream.Stream.concat(sourceQualification.stream(),epochManifest.stream()).toList())
            StrictJson.require(original.bytes()>0,"nonempty supplied physical source metadata required");
        Objects.requireNonNull(observedAt);
    }
    public PhysicalStatusIdentity(NativeObservationPort.TransportSession transport,String snapshotId,BigInteger nativeRevision,
            G2Source source,ExactRef nativeEvidence,ExactRef helloEvidence,ExactRef heartbeatEvidence,ExactRef sourceQualification,
            ExactRef epochManifest,Instant observedAt) {
        this(transport,snapshotId,nativeRevision,source,nativeEvidence,helloEvidence,heartbeatEvidence,
                java.util.Optional.of(sourceQualification),java.util.Optional.of(epochManifest),observedAt);
    }
    public String machineId(){return transport.machineId();}
    public GameGeneration game(){return transport.game();}
    public String sessionId(){return transport.sessionId();}
    public BigInteger connectionGeneration(){return transport.connectionGeneration();}
    public boolean sameGuardFrame(PhysicalStatusIdentity other) {
        return other!=null&&transport.equals(other.transport)&&snapshotId.equals(other.snapshotId)&&nativeRevision.equals(other.nativeRevision)
                &&source.equals(other.source)&&nativeEvidence.equals(other.nativeEvidence)&&helloEvidence.equals(other.helloEvidence)
                &&heartbeatEvidence.equals(other.heartbeatEvidence)&&sourceQualification.equals(other.sourceQualification)&&epochManifest.equals(other.epochManifest);
    }
    public static void requireProfile(ReadContract<?> actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(actual.contractId().equals(CONTRACT_ID)&&actual.operation().value().equals(OPERATION)
                &&actual.permissionKey().equals(PERMISSION)&&actual.requiredCapability().equals(java.util.Optional.of(CAPABILITY))
                &&actual.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&actual.guardMode()==ReadContract.GuardMode.STATUS_ONLY,
                "only the exact installed source-owned Sentinel physical Status profile is allowed");
    }
}
