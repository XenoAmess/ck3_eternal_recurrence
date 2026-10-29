package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.HashSet;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.Config;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ControlBuild.AttemptCapacityRelease;

/** Prepares a strictly typed manual wire and invokes ControlBuild's actual reader.
 * It never executes Maven, allocates a resource reservation or verifies an issuer's delegation.
 * The caller retains its actual financial/authorization domain and must separately hold authority to issue the file.
 */
public final class ManualBuildCapacityReleaseProducer {
    public static final String SCHEMA="xar.java-phase1.manual-capacity-release/v1";
    public enum ManualStatus { RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE }
    public static final ManualStatus STATUS=ManualStatus.RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE;
    public static final String WIRE_STATUS=STATUS.name();
    private static final int MAXIMUM_BYTES=128*1024;
    private static final ObjectMapper JSON=ControlBuild.strictMapper();
    private ManualBuildCapacityReleaseProducer() {}

    /** Provenance supplied by the real issuer, never a new approval token minted by this preparation utility. */
    public record IssuerDomain(String owner,String issuerTask,FileRef authorizationSource,String authorization,String scope) {
        public IssuerDomain {
            text(owner);text(issuerTask);Objects.requireNonNull(authorizationSource);text(authorization);text(scope);
        }
    }
    /** Exact six existing manual schema part names; each amount is a finite positive caller-supplied cap. */
    public record Parts(long m2,long build,long tools,long scratch,long metadataLogs,long artifacts) {
        public Parts {for(long value:new long[]{m2,build,tools,scratch,metadataLogs,artifacts})positive(value);}
    }
    /** Values remain issuer observations. The required-free formula is derived exactly, never accepted as narrative. */
    public record Volume(Path root,long totalVolumeBytes,long availableBytes,long currentProjectUsageConservativeUpper,
            long thisWritePeak,long otherUnspentReservations,long systemGrowthReserve,long safetyReserve,long effectiveProjectQuota) {
        public Volume {
            root=absolute(root);positive(totalVolumeBytes);nonnegative(availableBytes);positive(currentProjectUsageConservativeUpper);
            positive(thisWritePeak);nonnegative(otherUnspentReservations);positive(systemGrowthReserve);positive(safetyReserve);positive(effectiveProjectQuota);
            if(availableBytes>totalVolumeBytes)throw new IllegalArgumentException("available bytes exceed the observed volume");
            ManualBuildCapacityReleaseProducer.requiredFree(thisWritePeak,otherUnspentReservations,systemGrowthReserve,safetyReserve);
            if(Math.addExact(currentProjectUsageConservativeUpper,thisWritePeak)>effectiveProjectQuota)
                throw new IllegalArgumentException("manual project usage and write peak exceed the issuer's finite quota");
        }
        public long requiredFree(){return ManualBuildCapacityReleaseProducer.requiredFree(thisWritePeak,otherUnspentReservations,systemGrowthReserve,safetyReserve);}
    }
    public record Memory(long jointHardBytes,long mavenHeapBytes) {
        public Memory {positive(jointHardBytes);positive(mavenHeapBytes);if(mavenHeapBytes>=jointHardBytes)throw new IllegalArgumentException("Maven heap must fit the joint hard memory cap");}
    }
    public record Request(Config config,String machineId,Instant observedAt,Instant reviewAt,IssuerDomain issuer,
            FileRef policyRef,List<Path> approvedOutputRoots,Parts parts,List<Volume> volumes,Memory memory) {
        public Request {
            Objects.requireNonNull(config);text(machineId);Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);
            Objects.requireNonNull(issuer);Objects.requireNonNull(policyRef);Objects.requireNonNull(parts);Objects.requireNonNull(memory);
            if(!observedAt.isBefore(reviewAt))throw new IllegalArgumentException("finite original observation/review interval required");
            approvedOutputRoots=List.copyOf(approvedOutputRoots);volumes=List.copyOf(volumes);
            if(approvedOutputRoots.isEmpty()||approvedOutputRoots.size()>16||volumes.isEmpty()||volumes.size()>16)
                throw new IllegalArgumentException("finite manual output roots and volume observations required");
            var roots=new HashSet<Path>();for(Path root:approvedOutputRoots)if(!roots.add(absolute(root)))throw new IllegalArgumentException("duplicate approved output root");
            var volumeRoots=new HashSet<Path>();for(Volume volume:volumes)if(!volumeRoots.add(Objects.requireNonNull(volume).root()))throw new IllegalArgumentException("duplicate volume reservation root");
            absolute(config.sourceRoot());absolute(config.workRoot());absolute(config.capacityRelease());
        }
    }
    public enum PreparationStatus { PREPARED_EXISTING_MANUAL_READER_ACCEPTED }
    /** This is prepared-input evidence only. The live build must re-read the file and revalidate its authority window. */
    public record Prepared(FileRef release,PreparationStatus status,Instant readerCheckedAt,IssuerDomain issuer) {
        public Prepared {
            Objects.requireNonNull(release);Objects.requireNonNull(status);Objects.requireNonNull(readerCheckedAt);Objects.requireNonNull(issuer);
        }
    }
    /** A CREATE_NEW candidate is retained on failed actual-reader preflight; it cannot be overwritten or reused as PASS. */
    public static final class PreparationRejectedException extends IOException {
        private static final long serialVersionUID=1L;
        // FileRef is versioned JSON evidence, not a Java Serialization contract. Keep the actual in-process pin only.
        private final transient FileRef retainedCandidate;
        private PreparationRejectedException(FileRef retainedCandidate,Exception cause) {
            super("manual preparation or existing ControlBuild reader rejected the retained candidate: "+retainedCandidate.path(),cause);
            this.retainedCandidate=retainedCandidate;
        }
        public FileRef retainedCandidate(){
            if(retainedCandidate==null)throw new IllegalStateException("Candidate evidence is unavailable after Java exception deserialization; reacquire the exact file reference");
            return retainedCandidate;
        }
    }

    /** Encoding has no side effects and cannot select a different schema, status, writer or derived workspace paths. */
    public static byte[] encode(Request request)throws IOException {
        Objects.requireNonNull(request);Config config=request.config();
        ObjectNode root=JSON.createObjectNode();
        root.put("schema",SCHEMA).put("status",WIRE_STATUS).put("machine_id",request.machineId());
        root.put("owner",request.issuer().owner()).put("issuer_task",request.issuer().issuerTask());
        root.put("observed_at_utc",request.observedAt().toString()).put("review_at_utc",request.reviewAt().toString());
        root.put("single_Maven_writer",config.ownerTask());
        root.put("Maven_repository",config.workRoot().resolve("m2").toString());
        root.put("build_root",config.workRoot().resolve("build").toString());
        root.put("temporary_root",config.workRoot().resolve("scratch").toString());
        root.put("test_RAM_joint_hard_bytes",request.memory().jointHardBytes()).put("Maven_heap_bytes",request.memory().mavenHeapBytes());
        root.set("policy_ref",JSON.valueToTree(request.policyRef()));
        var approved=root.putArray("approved_output_roots");request.approvedOutputRoots().forEach(path->approved.add(path.toString()));
        Parts parts=request.parts();
        root.putObject("parts").put("m2",parts.m2()).put("build",parts.build()).put("tools",parts.tools())
                .put("scratch",parts.scratch()).put("metadata_logs",parts.metadataLogs()).put("artifacts",parts.artifacts());
        var volumes=root.putObject("volumes");
        for(Volume volume:request.volumes())volumes.putObject(volume.root().toString())
                .put("total_volume_bytes",volume.totalVolumeBytes()).put("available_bytes",volume.availableBytes())
                .put("current_project_usage_conservative_upper",volume.currentProjectUsageConservativeUpper())
                .put("this_write_peak",volume.thisWritePeak()).put("other_unspent_reservations",volume.otherUnspentReservations())
                .put("system_growth_reserve",volume.systemGrowthReserve()).put("safety_reserve",volume.safetyReserve())
                .put("required_free",volume.requiredFree()).put("effective_project_quota",volume.effectiveProjectQuota());
        var narrative=root.putObject("preparation_narrative");
        narrative.put("authorization",request.issuer().authorization()).put("scope",request.issuer().scope());
        narrative.set("original_authorization_ref",JSON.valueToTree(request.issuer().authorizationSource()));
        byte[] bytes=JSON.writeValueAsBytes(root);
        if(bytes.length>MAXIMUM_BYTES)throw new IOException("prepared legacy manual exceeds the actual reader's 128KiB bound");
        return bytes;
    }

    /** No replacement, directory creation, budget increment, financial CAS, Maven invocation or new admission mode. */
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        Objects.requireNonNull(request);
        return publish(request.config(),request.machineId(),request.observedAt(),request.reviewAt(),request.issuer(),
                List.of(request.policyRef(),request.issuer().authorizationSource()),encode(request),clock);
    }

    /** Uses only ControlBuild's versioned DTO and strict serializer; it adds no undeclared wire fields. */
    public static byte[] encode(AttemptCapacityRelease release)throws IOException {
        Objects.requireNonNull(release);
        byte[] bytes=JSON.writeValueAsBytes(release);
        if(bytes.length>MAXIMUM_BYTES)throw new IOException("prepared attempt manual exceeds the actual reader's 128KiB bound");
        return bytes;
    }

    /** The same actual reader validates conservative volume coverage and the separate logical/native caps.
     * This method neither inventories the shared repository nor substitutes a zero for unknown repository use.
     * Issuer provenance is retained in Prepared; only the shared DTO defines the versioned file.
     */
    public static Prepared prepare(Config config,AttemptCapacityRelease release,Clock clock,IssuerDomain issuer)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(release);Objects.requireNonNull(issuer);
        var sources=new ArrayList<FileRef>();
        sources.add(release.policyRef());sources.add(issuer.authorizationSource());
        sources.add(release.workpackageAccounting().financialSourceRef());
        sources.addAll(release.workpackageAccounting().reservationSourceRefs());
        for(var override:release.quotaOverrides().values()) {
            var reference=override.sourceRef();
            sources.add(new FileRef(reference.path(),reference.bytes(),reference.sha256()));
        }
        return publish(config,release.machineId(),Instant.parse(release.observedAtUtc()),Instant.parse(release.reviewAtUtc()),
                issuer,sources,encode(release),clock);
    }

    private static Prepared publish(Config config,String machineId,Instant observedAt,Instant reviewAt,
            IssuerDomain issuer,List<FileRef> sources,byte[] bytes,Clock clock)throws IOException {
        Objects.requireNonNull(config);text(machineId);Objects.requireNonNull(issuer);Objects.requireNonNull(clock);
        Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);sources=List.copyOf(sources);
        Objects.requireNonNull(bytes);Instant checkedAt=clock.instant();
        if(!observedAt.isBefore(reviewAt)||checkedAt.isBefore(observedAt)||!checkedAt.isBefore(reviewAt))
            throw new IOException("manual preparation outside the issuer's observed/review interval");
        if(bytes.length>MAXIMUM_BYTES)throw new IOException("prepared manual exceeds the actual reader's 128KiB bound");
        for(FileRef source:sources)source.verify();
        Path target=absolute(config.capacityRelease());Path parent=target.getParent();
        if(parent==null||!Files.isDirectory(parent,LinkOption.NOFOLLOW_LINKS)||!parent.toRealPath().equals(parent))
            throw new IOException("existing canonical ordinary prepared-file parent required");
        try(var file=FileChannel.open(target,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            var buffer=ByteBuffer.wrap(bytes);while(buffer.hasRemaining())file.write(buffer);file.force(true);
        }
        FileRef retained=FileRef.measure(target);
        Instant readerCheckedAt;
        try {
            if(retained.bytes()!=bytes.length)throw new IOException("prepared file length changed");
            try(var input=Files.newInputStream(target)){
                if(!Arrays.equals(bytes,input.readNBytes(MAXIMUM_BYTES+1)))throw new IOException("prepared content differs from the typed issuer request");
            }
            for(FileRef source:sources)source.verify();retained.verify();
            readerCheckedAt=clock.instant();
            if(readerCheckedAt.isBefore(checkedAt)||!readerCheckedAt.isBefore(reviewAt))
                throw new IOException("manual preparation expired or clock moved backwards before actual reader preflight");
            // Intentionally ignore the private Lease return type: the one existing production reader owns validation.
            ControlBuild.readLeaseAt(config,machineId,readerCheckedAt);
            retained.verify();for(FileRef source:sources)source.verify();
            Instant completedAt=clock.instant();
            if(completedAt.isBefore(readerCheckedAt)||!completedAt.isBefore(reviewAt))
                throw new IOException("manual preparation expired or clock moved backwards before returning evidence");
        } catch(IOException|RuntimeException failure) {throw new PreparationRejectedException(retained,failure);}
        return new Prepared(retained,PreparationStatus.PREPARED_EXISTING_MANUAL_READER_ACCEPTED,readerCheckedAt,issuer);
    }
    private static long requiredFree(long peak,long other,long growth,long safety) {
        return Math.addExact(Math.addExact(peak,other),Math.addExact(growth,safety));
    }
    private static Path absolute(Path value) {
        Objects.requireNonNull(value);if(!value.isAbsolute()||!value.normalize().equals(value))throw new IllegalArgumentException("absolute normalized manual input path required");return value;
    }
    private static void positive(long value){if(value<=0)throw new IllegalArgumentException("positive finite manual budget amount required");}
    private static void nonnegative(long value){if(value<0)throw new IllegalArgumentException("nonnegative finite manual budget amount required");}
    private static void text(String value){if(value==null||value.isBlank())throw new IllegalArgumentException("nonempty actual issuer text required");}
}

