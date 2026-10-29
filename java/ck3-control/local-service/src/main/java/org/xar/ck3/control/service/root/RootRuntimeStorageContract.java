package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.DirectoryIdentity;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed storage originals. Declaration -> census -> capacity -> ledger -> binding -> outer lease is acyclic.
 * Decoding a COMPLETE record never grants runtime authority; the guard measures its managed roots independently. */
public final class RootRuntimeStorageContract {
    public static final String DECLARATION="xar.java-root-runtime-storage-declaration/v1";
    public static final String CENSUS="xar.java-root-runtime-storage-census/v1";
    public static final String CAPACITY="xar.java-root-runtime-storage-capacity/v1";
    public static final String LEDGER="xar.java-root-runtime-storage-ledger/v1";
    public static final String BINDING="xar.java-root-runtime-storage-binding/v1";
    public static final int MAXIMUM_BYTES=1<<20;
    public static final long DIRECTORY_GUARD=4096;
    public static final long SAFE=9_007_199_254_740_991L;
    public static final String ISSUER="/root/budget_fast_lane";
    private RootRuntimeStorageContract() { }

    public record ManagedRoot(String rootId,String path,long maximumChargedBytes,long maximumSingleWriteBytes) {
        public ManagedRoot {id(rootId);absolute(path);positive(maximumChargedBytes);positive(maximumSingleWriteBytes);
            require(maximumSingleWriteBytes<=maximumChargedBytes,"single write exceeds this root's complete cap");}
    }
    public record Declaration(String schema,String machineId,String ownerTask,String windowId,String observedAtUtc,
            String reviewAtUtc,List<ManagedRoot> roots,String defaultWriteRootId,int maximumEntries,long maximumScanMillis,
            long auditIntervalMillis,List<String> exclusiveWriters) {
        public Declaration {
            require(DECLARATION.equals(schema),"exact runtime declaration version required");scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);
            roots=List.copyOf(roots);require(!roots.isEmpty()&&roots.size()<=32,"bounded complete runtime root inventory required");
            unique(roots.stream().map(ManagedRoot::rootId).toList());unique(roots.stream().map(ManagedRoot::path).toList());
            for(int i=0;i<roots.size();i++)for(int j=0;j<i;j++){
                Path a=Path.of(roots.get(i).path()),b=Path.of(roots.get(j).path());
                require(!a.startsWith(b)&&!b.startsWith(a),"runtime allocation roots must not overlap");
            }
            require(roots.stream().anyMatch(root->root.rootId().equals(defaultWriteRootId)),"explicit default write root required");
            require(maximumEntries>0&&maximumEntries<=100000&&maximumScanMillis>0&&maximumScanMillis<=120000,
                    "common-policy bounded metadata census required");
            require(auditIntervalMillis>0&&auditIntervalMillis<=30000,"finite runtime allocation audit interval required");
            exclusiveWriters=List.copyOf(exclusiveWriters);require(!exclusiveWriters.isEmpty()&&exclusiveWriters.size()<=64,
                    "actual controlled/native writer inventory required");unique(exclusiveWriters);exclusiveWriters.forEach(StrictJson::text);
        }
    }
    public record RootAllocation(String rootId,DirectoryIdentity directoryIdentity,long files,long directories,
            long logicalBytes,long fileAllocatedSumBytes,long directoryGuardBytes,long chargedUpperBytes,String inventorySha256) {
        public RootAllocation {
            id(rootId);Objects.requireNonNull(directoryIdentity);nonnegative(files);positive(directories);nonnegative(logicalBytes);
            nonnegative(fileAllocatedSumBytes);nonnegative(directoryGuardBytes);nonnegative(chargedUpperBytes);digest(inventorySha256);
            require(directoryGuardBytes==multiply(directories,DIRECTORY_GUARD)
                    &&chargedUpperBytes==add(fileAllocatedSumBytes,directoryGuardBytes),"actual native file allocation plus explicit directory guards required");
        }
    }
    public enum ExistingUsageKind { ACTUAL,UNKNOWN_WITH_CONSERVATIVE_UPPER }
    public record ExistingUsage(ExistingUsageKind kind,Long actualAllocatedBytes,long conservativeUpperBytes,FileRef evidenceRef) {
        public ExistingUsage {
            Objects.requireNonNull(kind);nonnegative(conservativeUpperBytes);file(evidenceRef);
            if(kind==ExistingUsageKind.ACTUAL){require(actualAllocatedBytes!=null,"actual usage cannot be null");nonnegative(actualAllocatedBytes);
                require(conservativeUpperBytes>=actualAllocatedBytes,"usage upper is below actual usage");}
            else require(actualAllocatedBytes==null&&conservativeUpperBytes>0,"unknown old workpackage requires a sourced nonzero conservative upper, never zero");
        }
    }
    public sealed interface WholeCensus permits CompleteCensus,IncompleteCensus {
        String schema();String status();String machineId();String ownerTask();String windowId();
        String observedAtUtc();String reviewAtUtc();FileRef declarationRef();ExistingUsage existingWorkpackage();
    }
    public record CompleteCensus(String schema,String status,String machineId,String ownerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef declarationRef,String scope,List<RootAllocation> runtimeRoots,
            ExistingUsage existingWorkpackage) implements WholeCensus {
        public CompleteCensus {
            require(CENSUS.equals(schema)&&"COMPLETE".equals(status)&&"DECLARED_RUNTIME_ROOTS_ONLY".equals(scope),
                    "complete census covers only its explicitly declared runtime roots");
            RootRuntimeStorageContract.scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);file(declarationRef);Objects.requireNonNull(existingWorkpackage);
            runtimeRoots=List.copyOf(runtimeRoots);require(!runtimeRoots.isEmpty()&&runtimeRoots.size()<=32,"all actual runtime root allocations required");
            unique(runtimeRoots.stream().map(RootAllocation::rootId).toList());
        }
    }
    public record IncompleteCensus(String schema,String status,String machineId,String ownerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef declarationRef,List<String> reasons,
            ExistingUsage existingWorkpackage) implements WholeCensus {
        public IncompleteCensus {
            require(CENSUS.equals(schema)&&"INCOMPLETE".equals(status),"explicit incomplete census version/status required");
            scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);file(declarationRef);Objects.requireNonNull(existingWorkpackage);
            reasons=List.copyOf(reasons);require(!reasons.isEmpty()&&reasons.size()<=64,"actual missing census inputs required");reasons.forEach(StrictJson::text);
        }
    }
    public record VolumeAllowance(String volumeRoot,long maximumRuntimeGrowthBytes,long systemGrowthReserveBytes,
            Long quotaOverrideMaximumBytes,String quotaOverrideOwner,String quotaReviewAtUtc) {
        public VolumeAllowance {
            absolute(volumeRoot);positive(maximumRuntimeGrowthBytes);nonnegative(systemGrowthReserveBytes);
            if(quotaOverrideMaximumBytes==null)require(quotaOverrideOwner==null&&quotaReviewAtUtc==null,"missing quota override is explicit null in all three fields");
            else {positive(quotaOverrideMaximumBytes);require("/root".equals(quotaOverrideOwner),"actual Root quota override owner required");instant(quotaReviewAtUtc);}
        }
    }
    public record Capacity(String schema,String machineId,String ownerTask,String issuerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef policyRef,FileRef declarationRef,FileRef censusRef,
            List<VolumeAllowance> volumes) {
        public Capacity {
            require(CAPACITY.equals(schema)&&ISSUER.equals(issuerTask),"sole runtime capacity issuer and exact version required");
            scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);file(policyRef);file(declarationRef);file(censusRef);
            volumes=List.copyOf(volumes);require(!volumes.isEmpty()&&volumes.size()<=16,"complete bounded runtime volume inventory required");
            unique(volumes.stream().map(VolumeAllowance::volumeRoot).toList());
            for(var volume:volumes)if(volume.quotaReviewAtUtc()!=null)
                require(!instant(volume.quotaReviewAtUtc()).isAfter(instant(reviewAtUtc))
                        &&instant(observedAtUtc).isBefore(instant(volume.quotaReviewAtUtc())),"finite quota override cannot outlive capacity");
        }
    }
    public enum ClaimScope { CANONICAL_OUTPUT_ROOTS,EXTERNAL_CONSERVATIVE_EVIDENCE }
    public record ReservationClaim(String claimId,String ownerTask,String machineId,String windowId,ClaimScope scope,
            List<String> canonicalOutputRoots,long unspentBytes,FileRef authorityRef) {
        public ReservationClaim {
            id(claimId);StrictJson.text(ownerTask);StrictJson.text(machineId);id(windowId);Objects.requireNonNull(scope);
            canonicalOutputRoots=List.copyOf(canonicalOutputRoots);nonnegative(unspentBytes);file(authorityRef);unique(canonicalOutputRoots);
            canonicalOutputRoots.forEach(RootRuntimeStorageContract::absolute);
            require((scope==ClaimScope.CANONICAL_OUTPUT_ROOTS)==!canonicalOutputRoots.isEmpty(),
                    "external conservative evidence cannot invent canonical root ownership");
        }
    }
    public record VolumeReservations(String volumeRoot,List<ReservationClaim> claims,long totalUnspentBytes) {
        public VolumeReservations {
            absolute(volumeRoot);claims=List.copyOf(claims);require(!claims.isEmpty()&&claims.size()<=4096,"complete finite reservation claims required");
            unique(claims.stream().map(ReservationClaim::claimId).toList());nonnegative(totalUnspentBytes);
            List<Path> outputs=claims.stream().flatMap(claim->claim.canonicalOutputRoots().stream()).map(Path::of).toList();
            for(int i=0;i<outputs.size();i++){
                require(outputs.get(i).startsWith(Path.of(volumeRoot)),"canonical reservation root belongs to another volume");
                for(int j=0;j<i;j++)require(!outputs.get(i).startsWith(outputs.get(j))&&!outputs.get(j).startsWith(outputs.get(i)),
                        "canonical reservation output claims must not overlap");
            }
            long total=0;for(var claim:claims)total=add(total,claim.unspentBytes());require(total==totalUnspentBytes,"reservation summary must equal the complete claim table");
        }
    }
    public record ReservationLedger(String schema,String ledgerId,long generation,String machineId,String ownerTask,
            String issuerTask,String windowId,String observedAtUtc,String reviewAtUtc,FileRef policyRef,FileRef declarationRef,
            FileRef capacityRef,FileRef predecessorRef,List<VolumeReservations> volumes) {
        public ReservationLedger {
            require(LEDGER.equals(schema)&&ISSUER.equals(issuerTask),"sole runtime reservation ledger issuer and exact version required");
            id(ledgerId);positive(generation);scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);
            file(policyRef);file(declarationRef);file(capacityRef);
            require((generation==1)==(predecessorRef==null),"new ledger generation one has explicit null predecessor; later generations require their original predecessor");
            if(predecessorRef!=null)file(predecessorRef);
            volumes=List.copyOf(volumes);require(!volumes.isEmpty()&&volumes.size()<=16,"complete ledger volumes required");
            unique(volumes.stream().map(VolumeReservations::volumeRoot).toList());
        }
    }
    public record RuntimeBinding(String schema,String machineId,String ownerTask,String issuerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef policyRef,FileRef declarationRef,FileRef censusRef,FileRef capacityRef,
            FileRef ledgerHeadRef,long ledgerGeneration) {
        public RuntimeBinding {
            require(BINDING.equals(schema)&&ISSUER.equals(issuerTask),"sole runtime binding issuer and exact version required");
            scope(machineId,ownerTask,windowId,observedAtUtc,reviewAtUtc);
            for(var reference:List.of(policyRef,declarationRef,censusRef,capacityRef,ledgerHeadRef))file(reference);positive(ledgerGeneration);
        }
    }
    public static WholeCensus decodeCensus(byte[] original)throws IOException {
        var tree=StrictJson.parse(original,MAXIMUM_BYTES);var status=StrictJson.text(tree.get("status"));
        return switch(status){case "COMPLETE"->decode(original,CompleteCensus.class);case "INCOMPLETE"->decode(original,IncompleteCensus.class);
            default->throw new IOException("unknown runtime census branch");};
    }
    public static <T> T decode(byte[] original,Class<T> closedType)throws IOException {
        Objects.requireNonNull(closedType);
        if(!List.of(Declaration.class,CompleteCensus.class,IncompleteCensus.class,Capacity.class,
                ReservationLedger.class,RuntimeBinding.class).contains(closedType))
            throw new IOException("only a closed versioned runtime storage record can be decoded");
        StrictJson.parse(original,MAXIMUM_BYTES);
        return ControlBuild.strictMapper().readValue(original,closedType);
    }
    public static byte[] encode(Declaration value)throws IOException{return encodeRecord(value);}
    public static byte[] encode(WholeCensus value)throws IOException{return encodeRecord(value);}
    public static byte[] encode(Capacity value)throws IOException{return encodeRecord(value);}
    public static byte[] encode(ReservationLedger value)throws IOException{return encodeRecord(value);}
    public static byte[] encode(RuntimeBinding value)throws IOException{return encodeRecord(value);}
    /** The one narrow Jackson boundary accepts only the closed records exposed by the typed overloads above. */
    private static byte[] encodeRecord(Object closedRecord)throws IOException {
        Objects.requireNonNull(closedRecord);
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(closedRecord),MAXIMUM_BYTES);
    }
    static void scope(String machine,String owner,String window,String observed,String review) {
        require(machine!=null&&machine.matches("[a-z0-9][a-z0-9-]{0,127}")&&!"unknown".equals(machine),"actual storage machine identity required");
        require("/root".equals(owner),"sole Root runtime owner required");id(window);Instant from=instant(observed),until=instant(review);
        require(from.isBefore(until)&&Duration.between(from,until).compareTo(Duration.ofDays(7))<=0,"finite at-most-seven-day storage authority required");
    }
    static Instant instant(String value){return Instant.parse(StrictJson.utc(StrictJson.text(value)));}
    static void absolute(String value){StrictJson.text(value);Path path=Path.of(value);require(path.isAbsolute()&&path.normalize().equals(path),"canonical absolute storage path required");}
    static void file(FileRef value){Objects.requireNonNull(value);absolute(value.path());positive(value.bytes());require(value.bytes()<=MAXIMUM_BYTES,"bounded storage authority original required");digest(value.sha256());}
    static void id(String value){require(value!=null&&value.matches("[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}"),"explicit bounded storage identifier required");}
    static void digest(String value){require(value!=null&&value.matches("[0-9a-fA-F]{64}"),"exact storage inventory SHA-256 required");}
    static void nonnegative(long value){require(value>=0&&value<=SAFE,"exact safe nonnegative storage byte/count/generation required");}
    static void positive(long value){nonnegative(value);require(value>0,"positive exact storage byte/count/generation required");}
    static long add(long left,long right){long result=Math.addExact(left,right);nonnegative(result);return result;}
    static long multiply(long left,long right){long result=Math.multiplyExact(left,right);nonnegative(result);return result;}
    static void unique(List<String> values){require(new HashSet<>(values).size()==values.size(),"duplicate storage inventory identity");}
    static void require(boolean value,String reason){if(!value)throw new IllegalArgumentException(reason);}
}
