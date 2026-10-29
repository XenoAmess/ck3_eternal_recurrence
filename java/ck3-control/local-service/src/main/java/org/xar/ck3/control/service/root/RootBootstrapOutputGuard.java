package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real pre-Core finite immutable-file output. It never creates a continuity writer, launches Native or grants Game rights.
 * Ordinary output/control inventories stay <=64 entries. The explicit formal-release branch has its own closed plan,
 * finite file/directory/byte ceilings and independent issuer card. Unknown writes retain their original quote. */
public final class RootBootstrapOutputGuard implements RootBootstrapInputFiles,AutoCloseable {
    public enum Status { ADMITTED,INCOMPLETE,UNKNOWN_WRITE,CLOSED }
    public record Accounting(Status status,long assetChargedUpperBytes,long controlChargedUpperBytes,long unresolvedPeakBytes,int completedOutputs,long retainedAllocatedUpperBytes){
        public long completeAssetAllocatedUpperBytes(){return Math.addExact(assetChargedUpperBytes,retainedAllocatedUpperBytes);}
    }
    private record Scan(SharedSourceFiles.DirectoryIdentity directory,List<Entry> entries,long charged,List<DirectoryEntry> directories,long retained){ }
    private record Quote(Output output,Path target,long peak){ }
    private final Binding binding;private final Declaration declaration;private final AssetCensus census;private final CapacityRelease capacity;
    private final Clock clock;private final List<SharedSourceFiles.Witness> originals;
    private final NativeCheckpointFiles raw=new NativeCheckpointFiles();private final CheckpointFiles files=new ImmutableFiles();
    private final Map<Path,FileWitness> completed=new LinkedHashMap<>();private final Map<Path,Quote> pending=new LinkedHashMap<>();
    private final FileChannel lockChannel;private final FileLock lock;private final Path lockPath;private final SharedSourceFiles.NativeFile lockIdentity;
    private Status status=Status.ADMITTED;
    private final Map<Path,SharedSourceFiles.DirectoryIdentity> directories=new LinkedHashMap<>();
    private long pendingDirectoryPeak;
    private RootBootstrapOutputGuard(Binding binding,Declaration declaration,AssetCensus census,CapacityRelease capacity,
            List<SharedSourceFiles.Witness> originals,Clock clock)throws IOException {
        this.binding=binding;this.declaration=declaration;this.census=census;this.capacity=capacity;this.originals=List.copyOf(originals);this.clock=clock;
        validate();assertCurrent();Scan actual=assetScan(declaration);
        if(!actual.directory().equals(census.assetDirectory())||!actual.entries().equals(census.entries())||actual.charged()!=census.chargedUpperBytes()||!actual.directories().equals(census.directories())||actual.retained()!=census.retainedAllocatedUpperBytes())
            throw new IOException("actual complete bootstrap asset census differs from the exact issuer-selected original");
        for(var directory:actual.directories())directories.put(Path.of(declaration.assetRoot()).resolve(directory.relative()),directory.directory());
        for(Entry entry:actual.entries()){
            Path target=Path.of(declaration.assetRoot()).resolve(entry.fileName());Output expected=output(target);
            var witness=raw.observe(target).orElseThrow();verifyExpected(expected,witness);completed.put(target,witness);
        }
        checkCapacity(0,null);
        lockPath=Path.of(declaration.controlRoot()).resolve("bootstrap-"+DriverJson.sha256(declaration.windowId().getBytes(java.nio.charset.StandardCharsets.UTF_8))+".lock");
        SharedSourceFiles.plainAncestors(lockPath);
        if(Files.exists(lockPath,LinkOption.NOFOLLOW_LINKS)){
            var prior=SharedSourceFiles.nativeFile(lockPath);if(prior.logicalBytes()!=0||prior.linkCount()!=1)throw new IOException("bootstrap control lock must remain one plain zero-byte file");
        }
        FileChannel channel=FileChannel.open(lockPath,StandardOpenOption.CREATE,StandardOpenOption.READ,StandardOpenOption.WRITE);
        FileLock held=null;
        try{
            held=channel.tryLock();if(held==null)throw new IOException("another actual bootstrap output process holds this exact card window");
            lockIdentity=SharedSourceFiles.nativeFile(lockPath);if(lockIdentity.logicalBytes()!=0||lockIdentity.linkCount()!=1)throw new IOException("actual bootstrap lock native metadata differs");
            lockChannel=channel;lock=held;assertCurrent();checkCapacity(0,null);
        }catch(IOException|RuntimeException failure){if(held!=null)held.close();channel.close();throw failure;}
    }
    public static RootBootstrapOutputGuard readExact(FileRef exactBinding,Clock clock)throws IOException {
        Objects.requireNonNull(clock);var originals=new ArrayList<SharedSourceFiles.Witness>();
        Binding binding=read(exactBinding,Binding.class,originals);Declaration declaration=read(binding.declarationRef(),Declaration.class,originals);
        AssetCensus census=read(binding.censusRef(),AssetCensus.class,originals);CapacityRelease capacity=read(binding.capacityRef(),CapacityRelease.class,originals);
        retain(capacity.policyRef(),originals);retain(capacity.originalFinancialHeadRef(),originals);
        for(var input:declaration.retainedInputs())retain(input.productionInventory(),originals);
        for(var allocation:capacity.retainedAllocations()){retain(allocation.existingUsageEvidence(),originals);retain(allocation.heldCustodyEvidence(),originals);}
        for(Volume volume:capacity.volumes()){
            retain(volume.existingUsage().evidenceRef(),originals);for(OtherReservation reservation:volume.otherReservations())retain(reservation.authorityRef(),originals);
        }
        return new RootBootstrapOutputGuard(binding,declaration,census,capacity,originals,clock);
    }
    /** Issuer observation producer only: no capacity or write admission is granted by a census record. */
    public static AssetCensus observeAssetRoot(FileRef declarationRef,Clock clock)throws IOException {
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();Declaration declaration=read(declarationRef,Declaration.class,witnesses);
        if(!declaration.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("bootstrap declaration is for another actual machine");
        requireCurrentPeriod(declaration.observedAtUtc(),declaration.reviewAtUtc(),clock);Scan actual=assetScan(declaration);
        if(!actual.directory().equals(declaration.assetDirectory()))throw new IOException("bootstrap asset directory identity drifted before actual census");
        for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);
        boolean formal=declaration.branch()==Branch.FORMAL_RELEASE;
        return new AssetCensus(formal?FORMAL_CENSUS:CENSUS,"COMPLETE",formal?FORMAL_SCOPE:"BOOTSTRAP_ASSET_ROOT_WITH_EXPLICIT_RETAINED_INPUTS",declaration.machineId(),declaration.windowId(),clock.instant().toString(),
                declaration.reviewAtUtc(),declarationRef,actual.directory(),actual.entries(),actual.charged(),actual.directories(),actual.retained());
    }
    @Override public synchronized void requireTargets(List<Path> actualTargets)throws IOException {
        assertCurrent();Objects.requireNonNull(actualTargets);
        if(actualTargets.isEmpty()||actualTargets.size()>declaration.maximumEntries()||actualTargets.stream().distinct().count()!=actualTargets.size())
            throw new IOException("bounded distinct exact bootstrap targets required");
        for(Path target:actualTargets){output(target);SharedSourceFiles.plainAncestors(target);
            Path parent=target.getParent();while(!parent.equals(Path.of(declaration.assetRoot()))){
                var expected=directories.get(parent);if(expected==null||!expected.equals(SharedSourceFiles.nativeDirectory(parent)))
                    throw new IOException("bootstrap output parent was not captured by its directory plan");parent=parent.getParent();}
            FileWitness original=completed.get(target);if(original!=null)raw.verify(original);
        }
        checkCapacity(0,null);
        if(pending.isEmpty()&&pendingDirectoryPeak==0)status=Status.ADMITTED;
    }
    /** Reserves all missing closed directories before the first CREATE_NEW; UNKNOWN creation is not retried. */
    public synchronized void createOutputDirectories()throws IOException {
        assertCurrent();if(status!=Status.ADMITTED||pendingDirectoryPeak!=0)throw new IOException("unknown bootstrap creation requires original reconciliation");
        var planned=new ArrayList<Path>();Path root=Path.of(declaration.assetRoot());
        for(String relative:declaration.outputDirectories()){
            Path target=root.resolve(relative);if(directories.containsKey(target))continue;
            if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))throw new IOException("another creator supplied an uncaptured output directory");planned.add(target);
        }
        planned.sort(Comparator.comparingInt(Path::getNameCount));long unit=RootBootstrapAssetTree.directoryQuote(root);
        long peak=Math.multiplyExact(unit,planned.size());checkCapacity(peak,null);pendingDirectoryPeak=peak;
        try{
            for(Path target:planned){assertCurrent();SharedSourceFiles.plainAncestors(target);Files.createDirectory(target);
                directories.put(target,SharedSourceFiles.nativeDirectory(target));pendingDirectoryPeak=Math.subtractExact(pendingDirectoryPeak,unit);checkCapacity(0,null);}
            assertCurrent();
        }catch(IOException|RuntimeException failure){status=Status.UNKNOWN_WRITE;throw failure;}
    }
    public synchronized void requirePlan(Path root,List<Output> exactOutputs,List<String> exactDirectories,List<RetainedInput> exactRetained)throws IOException {
        assertCurrent();if(!Path.of(declaration.assetRoot()).equals(root)||!declaration.outputs().equals(exactOutputs)
                ||!declaration.outputDirectories().equals(exactDirectories)||!declaration.retainedInputs().equals(exactRetained))
            throw new IOException("actual staged bytes/roots/directories/retained inputs differ from the entire issuer-priced plan");checkCapacity(0,null);
    }
    @Override public CheckpointFiles files(){return files;}
    public synchronized Accounting accounting()throws IOException {
        assertCurrent();Scan assets=assetScan(declaration),controls=scan(Path.of(declaration.controlRoot()),declaration.maximumEntries());
        return new Accounting(status,assets.charged(),controls.charged(),add(pendingDirectoryPeak,pending.values().stream().mapToLong(Quote::peak).sum()),completed.size(),assets.retained());
    }
    /** Narrow issuer staging only. Two conservative charged names cover native private publication and
     * the later pending/final hard-link interval. The caller closes this lock before exposing final. */
    synchronized FileWitness stageFileReply(Path pendingTarget,Path finalTarget,RootBootstrapProtocol.FileReply reply)throws IOException {
        assertCurrent();if(status!=Status.ADMITTED||!pending.isEmpty()||pendingDirectoryPeak!=0)
            throw new IOException("file reply cannot publish from an unresolved output scope");
        Path controls=Path.of(declaration.controlRoot());
        if(!controls.equals(finalTarget.getParent())||!pendingTarget.equals(controls.resolve("phase-"+reply.phaseIndex()+"-reply.pending"))
                ||!finalTarget.getFileName().toString().equals("phase-"+reply.phaseIndex()+"-reply.json"))
            throw new IOException("file reply metadata must use its sole declared flat control names");
        SharedSourceFiles.plainAncestors(pendingTarget);SharedSourceFiles.plainAncestors(finalTarget);
        if(Files.exists(pendingTarget,LinkOption.NOFOLLOW_LINKS)||Files.exists(finalTarget,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("file reply staging/final already exists; failed or unknown publication cannot replay");
        byte[] bytes=RootBootstrapProtocol.encode(reply,65536);checkCapacity(0,null);
        Scan controlsNow=scan(controls,declaration.maximumEntries()),assets=assetScan(declaration);
        long peak=Math.multiplyExact(2,fileQuote(bytes.length,controls));
        if(controlsNow.entries().size()+2>declaration.maximumEntries()
                ||add(controlsNow.charged(),peak)>declaration.controlMaximumChargedBytes()
                ||add(add(assets.charged(),controlsNow.charged()),peak)>capacity.jointMaximumChargedBytes())
            throw new IOException("file reply complete pending/final metadata peak exceeds the original issuer control/joint budget");
        try{
            var staged=raw.createNew(pendingTarget,bytes);raw.verify(staged);
            if(!java.util.Arrays.equals(bytes,raw.read(staged,65536)))throw new IOException("staged file reply Native readback differs");
            assertCurrent();checkCapacity(0,null);return staged;
        }catch(IOException|RuntimeException failure){status=Status.UNKNOWN_WRITE;throw failure;}
    }
    /** Lost CREATE_NEW return reconciles only the original exact expected body and physical witness, never retries the write. */
    public synchronized void reconcile(FileWitness witness)throws IOException {
        assertCurrent();Objects.requireNonNull(witness);Path target=Path.of(witness.reference().path());Quote quote=pending.get(target);
        if(quote==null)throw new IOException("no original unknown bootstrap write has this exact target");
        raw.verify(witness);verifyExpected(quote.output(),witness);completed.put(target,witness);pending.remove(target);
        status=pending.isEmpty()&&pendingDirectoryPeak==0?Status.ADMITTED:Status.UNKNOWN_WRITE;checkCapacity(0,null);
    }
    @Override public synchronized void close()throws IOException {
        if(status==Status.CLOSED)return;status=Status.CLOSED;try{lock.release();}finally{lockChannel.close();}
    }
    private synchronized FileWitness create(Path target,byte[] original)throws IOException {
        requireTargets(List.of(target));if(status!=Status.ADMITTED)throw new IOException("original unknown bootstrap write must be reconciled before another write");
        byte[] bytes=original.clone();Output expected=output(target);
        if(bytes.length!=expected.bytes()||!DriverJson.sha256(bytes).equalsIgnoreCase(expected.sha256()))throw new IOException("actual typed bootstrap producer differs from its exact issuer-priced planned bytes");
        if(completed.containsKey(target)||Files.exists(target,LinkOption.NOFOLLOW_LINKS))throw new IOException("immutable bootstrap input already exists; no overwrite or implicit replay");
        long quote=charge(bytes.length,Path.of(declaration.assetRoot()));checkCapacity(quote,target);pending.put(target,new Quote(expected,target,quote));
        try{
            FileWitness actual=raw.createNew(target,bytes);raw.verify(actual);verifyExpected(expected,actual);assertCurrent();
            pending.remove(target);completed.put(target,actual);checkCapacity(0,null);return actual;
        }catch(IOException|RuntimeException failure){status=pending.containsKey(target)?Status.UNKNOWN_WRITE:Status.INCOMPLETE;throw failure;}
    }
    private Output output(Path target)throws IOException {
        Objects.requireNonNull(target);if(!target.isAbsolute()||!target.normalize().equals(target))throw new IOException("exact canonical bootstrap target required");
        try{return declaration.output(target);}catch(java.util.NoSuchElementException missing){throw new IOException("bootstrap target is not in the actual issuer-priced typed output plan",missing);}
    }
    private static void verifyExpected(Output expected,FileWitness actual)throws IOException {
        if(actual.reference().bytes()!=expected.bytes()||!actual.reference().sha256().equalsIgnoreCase(expected.sha256()))throw new IOException("actual bootstrap output differs from its original typed body");
    }
    private void assertCurrent()throws IOException {
        if(status==Status.CLOSED)throw new IOException("bootstrap input output scope is closed");
        if(!binding.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("bootstrap capacity is foreign to the actual execution machine");
        requireCurrentPeriod(binding.observedAtUtc(),binding.reviewAtUtc(),clock);requireCurrentPeriod(declaration.observedAtUtc(),declaration.reviewAtUtc(),clock);
        requireCurrentPeriod(census.observedAtUtc(),census.reviewAtUtc(),clock);requireCurrentPeriod(capacity.observedAtUtc(),capacity.reviewAtUtc(),clock);
        for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        for(var original:completed.values())raw.verify(original);
        for(var entry:directories.entrySet())if(!entry.getValue().equals(SharedSourceFiles.nativeDirectory(entry.getKey())))
            throw new IOException("captured output directory identity changed");
        if(!declaration.retainedInputs().isEmpty())assetScan(declaration);
        if(!SharedSourceFiles.nativeDirectory(Path.of(declaration.assetRoot())).equals(declaration.assetDirectory())
                ||!SharedSourceFiles.nativeDirectory(Path.of(declaration.controlRoot())).equals(declaration.controlDirectory()))throw new IOException("bootstrap original root directory identity drifted");
        if(lockChannel!=null&&(!lock.isValid()||!SharedSourceFiles.nativeFile(lockPath).equals(lockIdentity)))throw new IOException("actual bootstrap process lock or native lock-file identity drifted");
    }
    private void checkCapacity(long prospective,Path prospectiveTarget)throws IOException {
        Scan assets=assetScan(declaration),controls=scan(Path.of(declaration.controlRoot()),declaration.maximumEntries());
        long unknown=add(pendingDirectoryPeak,pending.values().stream().mapToLong(Quote::peak).sum());
        if(add(add(assets.charged(),unknown),prospective)>declaration.assetMaximumChargedBytes()||controls.charged()>declaration.controlMaximumChargedBytes()
                ||add(add(add(assets.charged(),controls.charged()),unknown),prospective)>capacity.jointMaximumChargedBytes())
            throw new IOException("complete bootstrap assets/control/unknown allocations exceed the finite original joint cap");
        for(Volume allowance:capacity.volumes()){
            Path volume=Path.of(allowance.volumeRoot());long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
            long ownRemaining=0;
            for(Output output:declaration.outputs()){
                Path target=Path.of(declaration.assetRoot()).resolve(output.fileName());
                if(target.startsWith(volume)&&!completed.containsKey(target))ownRemaining=add(ownRemaining,charge(output.bytes(),Path.of(declaration.assetRoot())));
            }
            if(Path.of(declaration.assetRoot()).startsWith(volume))for(String directory:declaration.outputDirectories())
                if(!directories.containsKey(Path.of(declaration.assetRoot()).resolve(directory)))ownRemaining=add(ownRemaining,RootBootstrapAssetTree.directoryQuote(Path.of(declaration.assetRoot())));
            if(Path.of(declaration.controlRoot()).startsWith(volume))ownRemaining=add(ownRemaining,Math.max(0,declaration.controlMaximumChargedBytes()-controls.charged()));
            long safety=Math.max(allowance.minimumUsableBytes(),RootRuntimeStorageGuard.safety(total));
            if(free<add(add(ownRemaining,allowance.otherUnspentBytes()),add(allowance.systemGrowthReserveBytes(),safety)))
                throw new IOException("actual bootstrap volume lacks the complete unspent outputs + other holds + system growth + policy safety");
            long upper=Math.max(allowance.existingUsage().conservativeUpperBytes(),Math.subtractExact(total,free));
            long quota=allowance.finiteQuotaOverrideBytes()==null?Math.min(100L<<30,BigInteger.valueOf(total).add(BigInteger.valueOf(9)).divide(BigInteger.TEN).longValueExact()):allowance.finiteQuotaOverrideBytes();
            if(allowance.quotaReviewAtUtc()!=null&&!clock.instant().isBefore(instant(allowance.quotaReviewAtUtc())))throw new IOException("actual bootstrap finite owner quota override expired");
            if(add(add(upper,allowance.otherUnspentBytes()),ownRemaining)>quota)throw new IOException("actual/unknown-conservative volume upper plus complete holds and remaining bootstrap outputs exceeds finite quota");
        }
    }
    private void validate()throws IOException {
        try{
            boolean formal=declaration.branch()==Branch.FORMAL_RELEASE;
            require(branch(binding.schema(),binding.purpose(),BINDING,FORMAL_BINDING)==declaration.branch()
                    &&branch(capacity.schema(),capacity.purpose(),CAPACITY,FORMAL_CAPACITY)==declaration.branch()
                    &&census.schema().equals(formal?FORMAL_CENSUS:CENSUS),"every issuer-selected original must use the identical explicit bootstrap branch");
            require(List.of(binding.machineId(),declaration.machineId(),census.machineId(),capacity.machineId()).stream().distinct().count()==1
                    &&List.of(binding.windowId(),declaration.windowId(),census.windowId(),capacity.windowId()).stream().distinct().count()==1,"one actual bootstrap machine/window required");
            require(same(binding.declarationRef(),capacity.declarationRef())&&same(binding.declarationRef(),census.declarationRef())&&same(binding.censusRef(),capacity.censusRef()),"bootstrap binding selected different original declaration/census/release");
            require(census.assetDirectory().equals(declaration.assetDirectory()),"bootstrap census changed original native root identity");
            long planned=census.chargedUpperBytes();
            for(String directory:declaration.outputDirectories())if(census.directories().stream().noneMatch(entry->entry.relative().equals(directory)))
                planned=add(planned,RootBootstrapAssetTree.directoryQuote(Path.of(declaration.assetRoot())));
            require(capacity.retainedAllocations().size()==declaration.retainedInputs().size(),"every retained input requires sole-issuer existing-allocation accounting");
            long retainedTotal=0;
            for(var input:declaration.retainedInputs()){
                var tree=org.xar.ck3.control.build.NativeRunProfileProducer.readProductionTree(input.productionInventory());
                long actual=add(tree.retainedAllocatedUpperBytes(),RootBootstrapAssetTree.directoryQuote(Path.of(declaration.assetRoot())));
                var allocation=capacity.retainedAllocations().stream().filter(row->same(row.productionInventory(),input.productionInventory())).findFirst().orElseThrow();
                require(allocation.allocatedUpperBytes()==actual,"retained production allocation differs from actual complete input census");
                require(allocation.retentionPurpose()==RetentionPurpose.ACTIVE_PROFILE_PRODUCTION_INPUT
                        &&!instant(allocation.reviewAtUtc()).isBefore(instant(binding.reviewAtUtc()))
                        &&clock.instant().isBefore(instant(allocation.reviewAtUtc())),"issued retention purpose/review cannot expire before the actual bootstrap window");
                var volume=capacity.volumes().stream().filter(row->Path.of(tree.root()).startsWith(Path.of(row.volumeRoot()))).findFirst().orElseThrow();
                require(same(allocation.existingUsageEvidence(),volume.existingUsage().evidenceRef())
                        &&volume.existingUsage().conservativeUpperBytes()>=actual,"retained input must be reflected in actual existing-usage upper, never unspent output growth");
                retainedTotal=add(retainedTotal,actual);
            }
            require(retainedTotal==census.retainedAllocatedUpperBytes(),"complete asset census omitted retained production allocation");
            for(Output output:declaration.outputs())if(census.entries().stream().noneMatch(entry->entry.fileName().equals(output.fileName())))
                planned=add(planned,charge(output.bytes(),Path.of(declaration.assetRoot())));
            require(planned<=declaration.assetMaximumChargedBytes(),"complete actual encoded bootstrap input plan exceeds its original asset-root peak cap");
            require(capacity.jointMaximumChargedBytes()==add(declaration.assetMaximumChargedBytes(),declaration.controlMaximumChargedBytes()),"bootstrap joint allocation authority must cover exactly both finite roots");
            var order=List.of(declaration.observedAtUtc(),census.observedAtUtc(),capacity.observedAtUtc(),binding.observedAtUtc());
            for(int index=1;index<order.size();index++)require(!instant(order.get(index)).isBefore(instant(order.get(index-1))),"bootstrap authority must follow declaration -> actual census -> release -> binding");
            for(String review:List.of(declaration.reviewAtUtc(),census.reviewAtUtc(),capacity.reviewAtUtc()))require(!instant(binding.reviewAtUtc()).isAfter(instant(review)),"bootstrap binding cannot outlive any original authority");
            for(Path root:List.of(Path.of(declaration.assetRoot()),Path.of(declaration.controlRoot())))
                require(capacity.volumes().stream().filter(volume->root.startsWith(Path.of(volume.volumeRoot()))).count()==1,"each bootstrap root requires exactly one actual volume release");
            for(Volume volume:capacity.volumes()){
                long roots=0;if(Path.of(declaration.assetRoot()).startsWith(Path.of(volume.volumeRoot())))roots=add(roots,declaration.assetMaximumChargedBytes());
                if(Path.of(declaration.controlRoot()).startsWith(Path.of(volume.volumeRoot())))roots=add(roots,declaration.controlMaximumChargedBytes());
                require(roots==volume.maximumBootstrapGrowthBytes(),"issuer bootstrap volume peak differs from its actual declared roots");
                for(OtherReservation other:volume.otherReservations())require(!other.windowId().equals(binding.windowId()),"bootstrap own reservation cannot be counted again among other holds");
            }
            for(var original:originals)require(!Path.of(original.source().path()).startsWith(Path.of(declaration.assetRoot())),"issuer originals cannot be mutable bootstrap data outputs");
            var policy=StrictJson.parse(RootRuntimeDefinitions.read(capacity.policyRef(),MAXIMUM_BYTES),MAXIMUM_BYTES);
            require("1.0.0".equals(StrictJson.text(policy.get("policy_version"))),"bootstrap uses the actual common storage policy version");
            var rules=policy.get("capacity");
            require(StrictJson.integer(rules.get("safety_floor_bytes"),0,StrictJson.MAX_SAFE_INTEGER)==2L<<30
                    &&StrictJson.integer(rules.get("safety_ceiling_bytes"),0,StrictJson.MAX_SAFE_INTEGER)==20L<<30
                    &&StrictJson.integer(rules.get("default_project_quota_ceiling_bytes"),0,StrictJson.MAX_SAFE_INTEGER)==100L<<30
                    &&rules.get("safety_volume_fraction").isNumber()&&rules.get("safety_volume_fraction").decimalValue().compareTo(new java.math.BigDecimal("0.05"))==0
                    &&rules.get("default_project_quota_volume_fraction").isNumber()&&rules.get("default_project_quota_volume_fraction").decimalValue().compareTo(new java.math.BigDecimal("0.10"))==0,
                    "actual common bootstrap safety/quota constants differ");
        }catch(IllegalArgumentException|java.util.NoSuchElementException failure){throw new IOException("invalid actual bootstrap authority originals",failure);}
    }
    private static Scan assetScan(Declaration declaration)throws IOException {
        var actual=RootBootstrapAssetTree.scan(declaration);
        return new Scan(actual.root(),actual.files(),actual.generatedCharged(),actual.directories(),actual.retainedAllocatedUpper());
    }
    private static Scan scan(Path root,int maximum)throws IOException {
        Scan first=scanOnce(root,maximum),second=scanOnce(root,maximum);
        if(!first.equals(second))throw new IOException("bootstrap complete native allocation inventory changed between bounded scans");return second;
    }
    private static Scan scanOnce(Path root,int maximum)throws IOException {
        var before=SharedSourceFiles.nativeDirectory(root);var entries=new ArrayList<Entry>();
        try(var stream=Files.newDirectoryStream(root)){
            for(Path path:stream){if(entries.size()>=maximum)throw new IOException("bootstrap flat root inventory exceeds signed bound");
                var first=SharedSourceFiles.nativeFile(path);var last=SharedSourceFiles.nativeFile(path);
                if(!first.equals(last))throw new IOException("bootstrap actual native allocation changed during bounded census");entries.add(new Entry(path.getFileName().toString(),first));
            }
        }
        entries.sort(Comparator.comparing(Entry::fileName));
        if(!before.equals(SharedSourceFiles.nativeDirectory(root)))throw new IOException("bootstrap directory identity changed during actual bounded census");
        long charged=RootBootstrapAssetTree.directoryQuote(root);for(Entry entry:entries)charged=add(charged,entry.nativeFile().allocatedBytes());return new Scan(before,List.copyOf(entries),charged,List.of(),0);
    }
    private static long charge(long bytes,Path root)throws IOException {return fileQuote(bytes,root);}
    /** Same actual cluster geometry as the persistent guard; no sector-sized allocation quote. */
    static long fileQuote(long bytes,Path root)throws IOException {
        nonnegative(bytes);long unit=org.xar.ck3.control.build.NativeStorageGeometry.read(root).clusterBytes();
        return add(Math.multiplyExact(Math.floorDiv(add(bytes,unit-1),unit),unit),4096);
    }
    private static void requireCurrentPeriod(String first,String last,Clock clock)throws IOException {if(clock.instant().isBefore(instant(first))||!clock.instant().isBefore(instant(last)))throw new IOException("bootstrap authority is future-dated or expired");}
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static <T>T read(FileRef ref,Class<T> type,List<SharedSourceFiles.Witness> originals)throws IOException {return decode(retain(ref,originals),type);}
    private static byte[] retain(FileRef ref,List<SharedSourceFiles.Witness> originals)throws IOException {
        file(ref);if(originals.size()>=256)throw new IOException("bootstrap original authority inventory exceeded");
        long bytes=ref.bytes();for(var prior:originals)bytes=add(bytes,prior.source().bytes());
        if(bytes>16L<<20)throw new IOException("bootstrap complete authority-original byte bound exceeded");
        var first=SharedSourceFiles.observe(Path.of(ref.path()));byte[] original=RootRuntimeDefinitions.read(ref,1<<20);SharedSourceFiles.assertUnchanged(first);originals.add(first);return original;
    }
    private final class ImmutableFiles implements CheckpointFiles {
        @Override public Optional<FileWitness> observe(Path path)throws IOException{return raw.observe(path);}
        @Override public byte[] read(FileWitness original,int maximum)throws IOException{return raw.read(original,maximum);}
        @Override public FileWitness createNew(Path target,byte[] original)throws IOException{return create(target,original);}
        @Override public FileWitness replace(Path target,byte[] original)throws IOException{throw new IOException("bootstrap input authority allows CREATE_NEW only");}
        @Override public FileWitness copyNew(FileWitness original,Path target)throws IOException {raw.verify(original);return create(target,raw.read(original,Math.toIntExact(declaration.maximumSingleWriteBytes())));}
    }
}
