package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.lang.ref.WeakReference;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.lifecycle.SeedStore;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import static org.xar.ck3.control.service.root.RootRuntimeStorageContract.*;

/** Original-writer storage authority for one finite runtime package. No Game/action/Ready authority is minted here.
 * Initial/audit scans contain native metadata of declared runtime roots only; per-file writes settle exact allocation deltas. */
public final class RootRuntimeStorageGuard implements StorageWriteGuard,AutoCloseable {
    private static final Map<ContinuityWriter,Map<String,WeakReference<RootRuntimeStorageGuard>>> OWNERS=new WeakHashMap<>();
    @FunctionalInterface public interface WriterAccess {ContinuityWriter requireWriter()throws IOException;}
    public enum Status { PREPARED,ADMITTED,INCOMPLETE,UNKNOWN_WRITE }
    public record RootAccounting(String rootId,long measuredChargedUpperBytes,long outstandingPeakBytes,long maximumChargedBytes) { }
    public record Accounting(Status status,List<RootAccounting> roots,int unresolvedWrites) {
        public Accounting {roots=List.copyOf(roots);}
    }
    private record Cards(RootRuntimeDefinitionModel.StorageLease lease,RuntimeBinding binding,Declaration declaration,
            WholeCensus census,Capacity capacity,ReservationLedger ledger,List<SharedSourceFiles.Witness> originals) {
        private Cards {
            originals=originals.stream().distinct().toList();
            require(originals.size()<=256,"bounded complete runtime authority-original inventory required");
            long bytes=0;for(var original:originals)bytes=add(bytes,original.source().bytes());
            require(bytes<=16L*MAXIMUM_BYTES,"runtime authority revalidation exceeds its complete byte bound");
        }
    }
    private static final class RootState {
        final ManagedRoot definition;
        final SharedSourceFiles.DirectoryIdentity identity;
        final Map<Path,SharedSourceFiles.NativeFile> files=new HashMap<>();
        final Set<Path> directories=new HashSet<>();
        long charged;
        long pending;
        RootState(ManagedRoot definition,RootAllocation actual){this.definition=definition;identity=actual.directoryIdentity();charged=actual.chargedUpperBytes();}
        RootState(ManagedRoot definition,SharedSourceFiles.DirectoryIdentity actual){
            this.definition=definition;identity=actual;
            directories.add(Path.of(definition.path()));charged=DIRECTORY_GUARD;
        }
    }
    private record PendingWrite(long id,String rootId,Path target,long expectedBytes,String expectedSha256,long peakBytes,boolean legacyUnscoped,boolean directory) { }
    @FunctionalInterface private interface SessionWork<T>{T run(ContinuityStorePort.Session session)throws IOException;}
    @FunctionalInterface private interface FileWrite {FileWitness run()throws IOException;}
    private final Cards cards;
    private final OrdinaryBudget ordinaryBudget;
    private final WriterAccess access;
    private final Clock clock;
    private final Map<String,RootState> roots=new LinkedHashMap<>();
    private final Map<Long,PendingWrite> pending=new LinkedHashMap<>();
    private ContinuityWriter writer;
    private CheckpointFiles nativeFiles;
    private GuardedFiles wrappedFiles;
    private Status status=Status.PREPARED;
    private Instant auditedAt;
    private long nextWriteId;
    private Path expectedOriginalLock;
    private Path allocationLockPath;
    private SharedSourceFiles.NativeFile allocationLockIdentity;
    private SharedSourceFiles.NativeFile originalLockIdentity;
    private FileChannel allocationChannel;
    private FileLock allocationLock;
    private boolean closed;
    private final ThreadLocal<PhysicalPlan> activePhysical=new ThreadLocal<>();
    private final List<PhysicalPlan> unresolvedPhysical=new ArrayList<>();
    private static final class VirtualPath {
        final boolean directory;final long maximumBytes;final String identity;final boolean observed;
        VirtualPath(boolean directory,long maximumBytes,String identity){this(directory,maximumBytes,identity,false);}
        VirtualPath(boolean directory,long maximumBytes,String identity,boolean observed){this.directory=directory;this.maximumBytes=maximumBytes;this.identity=identity;this.observed=observed;}
    }
    private static final class PhysicalPlan {
        final WritePlan original;
        final Map<Integer,PendingWrite> reservations=new LinkedHashMap<>();
        final Map<Path,VirtualPath> after=new LinkedHashMap<>();
        final Map<Path,String> knownIdentities=new HashMap<>();
        final Map<Path,MeasuredPath> measured=new HashMap<>();
        boolean verifiedByChildren;
        final Set<Path> paths=new HashSet<>();
        final Set<Integer> consumed=new HashSet<>();
        final Set<Path> newRenameTargets=new HashSet<>();
        boolean failed;
        PhysicalPlan(WritePlan original){this.original=original;}
    }

    /** Actual finite allocation admission precedes construction of the canonical writer. It creates no writer session.
     * One counted ordinary lock file holds exclusive ownership of this exact window's mutable roots. */
    @Override public synchronized void requireInitialization(Path originalLock,List<Path> exactManagedRoots)throws IOException {
        normalized(Objects.requireNonNull(originalLock));Objects.requireNonNull(exactManagedRoots);
        if(exactManagedRoots.isEmpty()||exactManagedRoots.size()>64)throw new IOException("exact bounded persistent output roots required");
        if(expectedOriginalLock==null)expectedOriginalLock=originalLock;
        if(!expectedOriginalLock.equals(originalLock))throw new IOException("persistent outputs attempted another original writer lock");
        assertAllocationCurrent();
        if(cards!=null&&cards.census() instanceof IncompleteCensus incomplete)throw new IOException("INCOMPLETE_RUNTIME_STORAGE_CENSUS: "+incomplete.reasons());
        if(auditedAt==null)refresh(true);
        for(Path root:exactManagedRoots){normalized(root);SharedSourceFiles.plainAncestors(root);declared(root);
            if(Files.exists(root,LinkOption.NOFOLLOW_LINKS))RootRuntimeAllocationCensus.realDirectory(root);}
        declared(originalLock);
        if(allocationLock!=null){requireAllocationOwner();admitAllocation();requireOriginalLockFile();return;}
        RootState root=ordinaryBudget==null?defaultRoot():declared(expectedOriginalLock);
        allocationLockPath=allocationOwnerPath(root);
        PendingWrite reservation=null;
        try {
            if(Files.exists(allocationLockPath,LinkOption.NOFOLLOW_LINKS)) {
                var actual=SharedSourceFiles.nativeFile(allocationLockPath);
                if(actual.logicalBytes()!=0||actual.linkCount()!=1||!actual.equals(retainedFile(root,allocationLockPath,actual)))
                    throw new IOException("storage ownership lock is not the exact empty counted original");
                allocationChannel=FileChannel.open(allocationLockPath,StandardOpenOption.WRITE);
            }else{
                long quote=charge(0,Path.of(root.definition.path()));checkCapacity(quote,root);
                reservation=addPending(root,allocationLockPath,0,null,quote,false);
                allocationChannel=FileChannel.open(allocationLockPath,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
                allocationChannel.force(true);
            }
            try{allocationLock=allocationChannel.tryLock();}
            catch(java.nio.channels.OverlappingFileLockException occupied){throw new IOException("another live allocation owner already holds this runtime window",occupied);}
            if(allocationLock==null)throw new IOException("another live storage owner holds this exact runtime allocation window");
            allocationLockIdentity=SharedSourceFiles.nativeFile(allocationLockPath);
            if(allocationLockIdentity.logicalBytes()!=0||allocationLockIdentity.linkCount()!=1)
                throw new IOException("actual storage ownership file has unexpected payload or links");
            updateMeasured(allocationLockPath);
            if(reservation!=null)removePending(reservation);
            checkCapacity(0,null);status=Status.ADMITTED;requireOriginalLockFile();
        }catch(IOException|RuntimeException failure){
            status=reservation==null?Status.INCOMPLETE:Status.UNKNOWN_WRITE;
            if(allocationLock!=null){try{allocationLock.release();}catch(IOException close){failure.addSuppressed(close);}allocationLock=null;}
            if(allocationChannel!=null){try{allocationChannel.close();}catch(IOException close){failure.addSuppressed(close);}allocationChannel=null;}
            throw failure;
        }
    }
    /** Fixed-control cold bundles must count their existing allocation owner before their signed census.
     * This performs no create or lock acquisition and issues no writer/Game admission. */
    public synchronized void requireExistingAllocationOwner(Path originalLock)throws IOException {
        normalized(Objects.requireNonNull(originalLock));assertAllocationCurrent();
        if(expectedOriginalLock!=null&&!expectedOriginalLock.equals(originalLock))
            throw new IOException("fixed-control observation belongs to another original writer lock");
        if(cards!=null&&!(cards.census() instanceof CompleteCensus))throw new IOException("fixed-control observation requires its complete original census");
        if(auditedAt==null)refresh(true);
        declared(originalLock);var root=ordinaryBudget==null?defaultRoot():declared(originalLock);Path owner=allocationOwnerPath(root);
        if(!Files.exists(owner,LinkOption.NOFOLLOW_LINKS))throw new IOException("fixed-control census lacks its pre-existing allocation ownership file");
        var actual=SharedSourceFiles.nativeFile(owner);
        if(actual.logicalBytes()!=0||actual.linkCount()!=1||!actual.equals(retainedFile(root,owner,actual)))
            throw new IOException("fixed-control allocation ownership file differs from its exact counted original");
        expectedOriginalLock=originalLock;
    }
    private Path allocationOwnerPath(RootState root){
        return (ordinaryBudget==null?Path.of(root.definition.path()):expectedOriginalLock.getParent()).resolve(".runtime-storage-"+
                DriverJson.sha256(windowId().getBytes(java.nio.charset.StandardCharsets.UTF_8))+".lock");
    }
    /** WindowsLedgerLock may open an existing file, but never creates an unquoted root/lock file for bootstrap. */
    private void requireOriginalLockFile()throws IOException {
        if(originalLockIdentity!=null)return;
        if(!Files.exists(expectedOriginalLock,LinkOption.NOFOLLOW_LINKS)){
            var missing=new ArrayList<Path>();Path cursor=expectedOriginalLock.getParent();
            while(!Files.exists(cursor,LinkOption.NOFOLLOW_LINKS)){
                declared(cursor);if(missing.size()>=64)throw new IOException("original writer lock ancestry exceeds the bounded runtime declaration");
                missing.add(cursor);cursor=cursor.getParent();
            }
            RootRuntimeAllocationCensus.realDirectory(cursor);var mutations=new ArrayList<Mutation>();
            for(int index=missing.size()-1;index>=0;index--)mutations.add(new DirectoryCreate(missing.get(index)));
            mutations.add(new FileCreate(expectedOriginalLock,0));
            write(new WritePlan(expectedOriginalLock,mutations),()->{
                for(Mutation mutation:mutations)write(new WritePlan(expectedOriginalLock,List.of(mutation)),()->{
                    if(mutation instanceof DirectoryCreate)Files.createDirectory(mutation.target());
                    else try(var channel=FileChannel.open(mutation.target(),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){channel.force(true);}
                    return null;
                });
                return null;
            });
        }
        var actual=SharedSourceFiles.nativeFile(expectedOriginalLock);
        if(actual.logicalBytes()!=0||actual.linkCount()!=1||!actual.equals(retainedFile(declared(expectedOriginalLock),expectedOriginalLock,actual)))
            throw new IOException("the original writer lock is not the exact counted empty native file");
        originalLockIdentity=actual;
    }
    @Override public <T>T write(WritePlan plan,PhysicalWrite<T> actualIO)throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(actualIO);
        PhysicalPlan outer=activePhysical.get();
        if(outer!=null)return nested(outer,plan,actualIO);
        final PhysicalPlan retained;
        synchronized(this){
            requireAllocationOwner();requireLock(plan.originalLock());admitAllocation();
            retained=preflight(plan);reserve(retained);
        }
        activePhysical.set(retained);
        try {
            T result=actualIO.run();
            synchronized(this){
                if(retained.failed)throw new IOException("an original nested physical write failed even though its caller swallowed the return");
                requireAllocationOwner();verifyPhysical(retained,retained);
                for(int index=0;index<plan.mutations().size();index++)settle(retained,index);
                checkCapacity(0,null);
            }
            return result;
        }catch(IOException|RuntimeException failure){
            synchronized(this){status=Status.UNKNOWN_WRITE;unresolvedPhysical.add(retained);}
            throw failure;
        }finally{activePhysical.remove();}
    }
    private <T>T nested(PhysicalPlan outer,WritePlan child,PhysicalWrite<T> actualIO)throws IOException {
        final PhysicalPlan actual;final List<Integer> indices=new ArrayList<>();
        synchronized(this){
            requireAllocationOwner();requireLock(child.originalLock());
            int next=0;
            for(Mutation mutation:child.mutations()){
                int selected=-1;
                for(int index=next;index<outer.original.mutations().size();index++)
                    if(!outer.consumed.contains(index)&&subset(mutation,outer.original.mutations().get(index))){selected=index;break;}
                if(selected<0)throw new IOException("nested physical write is not an unconsumed ordered subset of its retained whole plan");
                indices.add(selected);next=selected+1;
            }
            actual=preflight(child);
        }
        final T result;
        try{result=actualIO.run();}
        catch(IOException|RuntimeException failure){synchronized(this){outer.failed=true;status=Status.UNKNOWN_WRITE;}throw failure;}
        try{synchronized(this){
            requireAllocationOwner();
            actual.verifiedByChildren=indices.stream().allMatch(outer.consumed::contains);
            verifyPhysical(actual,outer);
            for(int index:indices)settle(outer,index);
            checkCapacity(0,null);
        }}catch(IOException|RuntimeException failure){synchronized(this){outer.failed=true;status=Status.UNKNOWN_WRITE;}throw failure;}
        return result;
    }
    private synchronized void reserve(PhysicalPlan plan)throws IOException {
        try {
            for(int index=0;index<plan.original.mutations().size();index++){
                Mutation mutation=plan.original.mutations().get(index);RootState root=declared(mutation.target());
                long quote=mutation instanceof DirectoryCreate?DIRECTORY_GUARD:
                        mutation instanceof FileCreate file?charge(file.maxLogicalBytes(),Path.of(root.definition.path())):
                        mutation instanceof FileFillExistingEmpty file?charge(file.maxLogicalBytes(),Path.of(root.definition.path())):0;
                if(quote!=0){checkCapacity(quote,root);plan.reservations.put(index,addPending(root,null,0,null,quote,false));}
            }
        }catch(IOException|RuntimeException rejected){
            for(var reservation:plan.reservations.values())removePending(reservation);
            plan.reservations.clear();throw rejected;
        }
    }
    private record MeasuredPath(boolean directory,SharedSourceFiles.NativeFile file) { }
    private PhysicalPlan preflight(WritePlan plan)throws IOException {
        var result=new PhysicalPlan(plan);requireLock(plan.originalLock());
        for(Mutation mutation:plan.mutations()){
            Path target=mutation.target();checkPhysicalTarget(target);result.paths.add(target);
            VirtualPath before=virtual(result,target);parent(result,target);
            if(mutation instanceof DirectoryCreate){
                if(before!=null)throw new IOException("persistent directory CREATE_NEW target already exists");
                result.after.put(target,new VirtualPath(true,0,null));
            }else if(mutation instanceof FileCreate create){
                if(before!=null)throw new IOException("persistent file CREATE_NEW target already exists");
                result.after.put(target,new VirtualPath(false,create.maxLogicalBytes(),null));
            }else if(mutation instanceof FileFillExistingEmpty fill){
                if(before==null||before.directory||(before.identity!=null||before.observed)&&before.maximumBytes!=0)
                    throw new IOException("persistent fill requires the actual original empty file");
                // A preceding bounded CREATE_NEW may deliberately create zero bytes. Its real empty FileID
                // must then be captured by a primitive child before the fill, never inferred from the quote.
                if(before.identity==null)result.newRenameTargets.add(target);
                result.after.put(target,new VirtualPath(false,fill.maxLogicalBytes(),before.identity));
            }else if(mutation instanceof FileRename rename){
                checkPhysicalTarget(rename.source());result.paths.add(rename.source());
                VirtualPath source=virtual(result,rename.source());
                if(source==null||source.directory||before!=null&&(before.directory||!rename.replace()))
                    throw new IOException("persistent rename source/target does not match its complete plan");
                if(cards!=null&&!declared(rename.source()).identity.volumeSerialDecimal().equals(declared(target).identity.volumeSerialDecimal()))
                    throw new IOException("persistent rename cannot cross actual native volumes");
                result.after.put(rename.source(),null);result.after.put(target,source);
                result.newRenameTargets.remove(rename.source());if(source.identity==null)result.newRenameTargets.add(target);
            }else throw new IOException("unknown persistent physical mutation");
        }
        return result;
    }
    private VirtualPath virtual(PhysicalPlan plan,Path path)throws IOException {
        if(plan.after.containsKey(path))return plan.after.get(path);
        if(ordinaryBudget!=null){
            final java.nio.file.attribute.BasicFileAttributes actual;
            try{actual=Files.readAttributes(path,java.nio.file.attribute.BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);}
            catch(java.nio.file.NoSuchFileException absent){plan.after.put(path,null);return null;}
            if(!actual.isDirectory()&&!actual.isRegularFile())throw new IOException("ordinary physical target has an unsupported type");
            var known=new VirtualPath(actual.isDirectory(),actual.isDirectory()?0:actual.size(),null,true);
            plan.after.put(path,known);return known;
        }
        if(!Files.exists(path,LinkOption.NOFOLLOW_LINKS)){plan.after.put(path,null);return null;}
        SharedSourceFiles.plainAncestors(path);
        if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)){
            RootRuntimeAllocationCensus.realDirectory(path);var known=new VirtualPath(true,0,null);plan.after.put(path,known);return known;
        }
        var actual=SharedSourceFiles.nativeFile(path);RootState root=declared(path);
        if(actual.linkCount()!=1||!actual.equals(retainedFile(root,path,actual)))throw new IOException("persistent file native identity/allocation changed outside the retained controlled producer");
        var known=new VirtualPath(false,actual.logicalBytes(),actual.identityKey());plan.after.put(path,known);plan.knownIdentities.put(path,actual.identityKey());return known;
    }
    private SharedSourceFiles.NativeFile retainedFile(RootState root,Path path,SharedSourceFiles.NativeFile actual){
        if(ordinaryBudget!=null&&!root.files.containsKey(path)){
            root.files.put(path,actual);root.charged=add(root.charged,actual.allocatedBytes());
        }
        return root.files.get(path);
    }
    private void parent(PhysicalPlan plan,Path target)throws IOException {
        Path parent=target.getParent();
        if(ordinaryBudget!=null){declared(parent);return;}
        VirtualPath prior=plan.after.get(parent);
        if(prior!=null&&prior.directory)return;
        RootRuntimeAllocationCensus.realDirectory(parent);
        if(ordinaryBudget!=null)updateMeasured(parent);
    }
    private void verifyPhysical(PhysicalPlan plan,PhysicalPlan retained)throws IOException {
        assertAllocationCurrent();
        if(ordinaryBudget!=null){verifyOrdinaryPhysical(plan,retained);return;}
        for(Path target:plan.paths){
            VirtualPath expected=plan.after.get(target);
            if(expected==null){
                if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))throw new IOException("persistent original rename source still exists");
                retained.knownIdentities.remove(target);
                continue;
            }
            if(expected.directory){RootRuntimeAllocationCensus.realDirectory(target);continue;}
            var actual=SharedSourceFiles.nativeFile(target);
            String identity=expected.identity!=null?expected.identity:retained.knownIdentities.get(target);
            if(actual.linkCount()!=1||actual.logicalBytes()>expected.maximumBytes
                    ||identity!=null&&!actual.identityKey().equals(identity)
                    ||plan.newRenameTargets.contains(target)&&identity==null)
                throw new IOException("persistent post-write bytes/native FileID differ or a created-source rename lacked an observed intermediate phase");
            long maximum=charge(expected.maximumBytes,Path.of(declared(target).definition.path()));
            if(actual.allocatedBytes()>maximum)throw new IOException("actual persistent file allocation exceeds its finite original quote");
            retained.knownIdentities.put(target,actual.identityKey());
        }
    }
    @Override public synchronized OptionalLong enforcedAggregateMaximumBytes(Path originalLock,Path managedDirectory)throws IOException {
        if (ordinaryBudget == null) return OptionalLong.empty();
        requireAllocationOwner();
        requireLock(originalLock);
        declared(managedDirectory);
        return OptionalLong.of(ordinaryBudget.maximumChargedBytes());
    }
    private void settle(PhysicalPlan plan,int index)throws IOException {
        if(!plan.consumed.add(index))return; // A composite child returns after its already-verified primitive children.
        Mutation mutation=plan.original.mutations().get(index);
        if(ordinaryBudget!=null){
            settleOrdinaryMeasured(plan,mutation.target());
            if(mutation instanceof FileRename rename)settleOrdinaryMeasured(plan,rename.source());
        }else{updateMeasured(mutation.target());if(mutation instanceof FileRename rename)updateMeasured(rename.source());}
        PendingWrite original=plan.reservations.remove(index);if(original!=null)removePending(original);
    }
    private void updateMeasured(Path path)throws IOException {
        if(ordinaryBudget!=null){applyOrdinaryMeasured(path,observeOrdinary(path));return;}
        RootState root=declared(path);SharedSourceFiles.NativeFile previous=root.files.remove(path);
        if(previous!=null)root.charged=Math.subtractExact(root.charged,previous.allocatedBytes());
        boolean oldDirectory=root.directories.remove(path);if(oldDirectory)root.charged=Math.subtractExact(root.charged,DIRECTORY_GUARD);
        if(Files.exists(path,LinkOption.NOFOLLOW_LINKS)){
            if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)){
                RootRuntimeAllocationCensus.realDirectory(path);root.directories.add(path);root.charged=add(root.charged,DIRECTORY_GUARD);
            }else{var actual=SharedSourceFiles.nativeFile(path);root.files.put(path,actual);root.charged=add(root.charged,actual.allocatedBytes());}
        }
        if(roots.values().stream().mapToLong(value->value.files.size()+value.directories.size()).sum()>maximumEntries())
            throw new IOException("persistent controlled inventory exceeds the signed complete runtime bound");
    }
    /** Only a changed target is observed. Ordinary writes do not requalify its ancestors or native identity. */
    private MeasuredPath observeOrdinary(Path path)throws IOException {
        final java.nio.file.attribute.BasicFileAttributes actual;
        try{actual=Files.readAttributes(path,java.nio.file.attribute.BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);}
        catch(java.nio.file.NoSuchFileException absent){return null;}
        if(actual.isDirectory())return new MeasuredPath(true,null);
        if(!actual.isRegularFile())throw new IOException("ordinary physical result is not a regular file/directory");
        return new MeasuredPath(false,ordinaryFileResult(path));
    }
    private SharedSourceFiles.NativeFile ordinaryFileResult(Path path)throws IOException {
        var kernel=com.sun.jna.platform.win32.Kernel32.INSTANCE;
        var handle=kernel.CreateFile(path.toString(),0x80,7,null,3,0x00200000,null);
        if(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw new IOException("ordinary file result open Win32="+com.sun.jna.Native.getLastError()+" path="+path);
        try{return SharedSourceFiles.nativeHeldFile(handle);}
        finally{if(!kernel.CloseHandle(handle))throw new IOException("ordinary file result close Win32="+com.sun.jna.Native.getLastError());}
    }
    private void verifyOrdinaryPhysical(PhysicalPlan plan,PhysicalPlan retained)throws IOException {
        boolean reuse=plan.verifiedByChildren||plan==retained&&plan.consumed.size()==plan.original.mutations().size();
        for(Path target:plan.paths){
            MeasuredPath actual;
            if(reuse&&retained.measured.containsKey(target))actual=retained.measured.get(target);
            else actual=observeOrdinary(target);
            VirtualPath expected=plan.after.get(target);
            if(expected==null){if(actual!=null)throw new IOException("ordinary rename source still exists");}
            else if(actual==null||actual.directory()!=expected.directory)
                throw new IOException("ordinary write has no actual target result of the declared type");
            else if(!actual.directory()&&(actual.file().logicalBytes()>expected.maximumBytes
                    ||actual.file().allocatedBytes()>charge(expected.maximumBytes,Path.of(declared(target).definition.path()))))
                throw new IOException("ordinary write actual bytes/allocation exceed the finite declared result");
            plan.measured.put(target,actual);retained.measured.put(target,actual);
        }
    }
    private void settleOrdinaryMeasured(PhysicalPlan plan,Path path)throws IOException {
        if(!plan.measured.containsKey(path))throw new IOException("ordinary settlement lacks its actual changed-target observation");
        applyOrdinaryMeasured(path,plan.measured.get(path));
    }
    private void applyOrdinaryMeasured(Path path,MeasuredPath actual)throws IOException {
        RootState root=declared(path);var previous=root.files.remove(path);
        if(previous!=null)root.charged=Math.subtractExact(root.charged,previous.allocatedBytes());
        if(root.directories.remove(path))root.charged=Math.subtractExact(root.charged,DIRECTORY_GUARD);
        if(actual!=null){
            if(actual.directory()){root.directories.add(path);root.charged=add(root.charged,DIRECTORY_GUARD);}
            else{root.files.put(path,actual.file());root.charged=add(root.charged,actual.file().allocatedBytes());}
            Path parent=path.getParent();
            if(parent!=null&&parent.startsWith(Path.of(root.definition.path()))&&root.directories.add(parent))
                root.charged=add(root.charged,DIRECTORY_GUARD);
        }
        if(roots.values().stream().mapToLong(value->value.files.size()+value.directories.size()).sum()>maximumEntries())
            throw new IOException("ordinary controlled inventory exceeds its finite bound");
    }
    private static boolean subset(Mutation child,Mutation parent){
        if(!child.target().equals(parent.target()))return false;
        if(child instanceof FileCreate a&&parent instanceof FileCreate b)return a.maxLogicalBytes()<=b.maxLogicalBytes();
        if(child instanceof FileFillExistingEmpty a&&parent instanceof FileFillExistingEmpty b)return a.maxLogicalBytes()<=b.maxLogicalBytes();
        if(child instanceof FileRename a&&parent instanceof FileRename b)return a.source().equals(b.source())&&a.replace()==b.replace();
        return child instanceof DirectoryCreate&&parent instanceof DirectoryCreate;
    }
    private RootState declared(Path path)throws IOException {
        normalized(path);
        return roots.values().stream().filter(root->path.startsWith(Path.of(root.definition.path())))
                .findFirst().orElseThrow(()->new IOException("persistent output escaped every actual issuer-declared runtime root: "+path));
    }
    private void checkPhysicalTarget(Path path)throws IOException {
        normalized(path);if(cards!=null)SharedSourceFiles.plainAncestors(path);declared(path);
        if(path.equals(allocationLockPath)||roots.values().stream().anyMatch(root->path.equals(Path.of(root.definition.path()))))
            throw new IOException("persistent mutation cannot replace a runtime root or its exclusive allocation owner");
    }
    private void requireLock(Path lock)throws IOException {
        if(expectedOriginalLock==null||!expectedOriginalLock.equals(lock))throw new IOException("persistent plan belongs to another original writer lock");
    }
    private void requireAllocationOwner()throws IOException {
        assertAllocationCurrent();
        if(allocationLock==null||!allocationLock.isValid()||allocationChannel==null||!allocationChannel.isOpen())
            throw new IOException("actual exclusive runtime allocation owner is absent or changed");
        if(cards!=null){
            if(allocationLockIdentity==null||!allocationLockIdentity.identityKey().equals(SharedSourceFiles.nativeFile(allocationLockPath).identityKey()))
                throw new IOException("actual exclusive runtime allocation owner is absent or changed");
            if(originalLockIdentity!=null){var actual=SharedSourceFiles.nativeFile(expectedOriginalLock);
                if(!actual.identityKey().equals(originalLockIdentity.identityKey())||actual.logicalBytes()!=0||actual.linkCount()!=1)
                    throw new IOException("the counted original writer lock identity/shape changed");}
        }
    }
    private void admitAllocation()throws IOException {
        if(status==Status.UNKNOWN_WRITE||!unresolvedPhysical.isEmpty())throw new IOException("original persistent write outcome is unresolved; no replay or guessed storage release");
        if(auditedAt==null)throw new IOException("complete original runtime allocation census is not admitted");
        if(cards!=null&&!clock.instant().isBefore(auditedAt.plusMillis(cards.declaration().auditIntervalMillis())))refresh(false);
        checkCapacity(0,null);
    }
    /** Only the exact original full post-state can reconcile a lost return. Partial physical work is never replayed. */
    public synchronized void reconcilePersistentWrite(WritePlan original)throws IOException {
        requireAllocationOwner();PhysicalPlan retained=unresolvedPhysical.stream().filter(value->value.original.equals(original)).findFirst()
                .orElseThrow(()->new IOException("no retained unknown persistent plan matches this original"));
        verifyPhysical(retained,retained);
        for(int index=0;index<original.mutations().size();index++)settle(retained,index);
        unresolvedPhysical.remove(retained);status=unresolvedPhysical.isEmpty()&&pending.isEmpty()?Status.ADMITTED:Status.UNKNOWN_WRITE;
        checkCapacity(0,null);
    }
    /** Closing releases exclusive execution ownership only; the file, actual allocation and all finite holds remain. */
    @Override public synchronized void close()throws IOException {
        if(closed)return;closed=true;IOException failure=null;
        if(allocationLock!=null)try{allocationLock.release();}catch(IOException rejected){failure=rejected;}
        if(allocationChannel!=null)try{allocationChannel.close();}catch(IOException rejected){if(failure==null)failure=rejected;else failure.addSuppressed(rejected);}
        if(failure!=null)throw failure;
    }

    private RootRuntimeStorageGuard(Cards cards,WriterAccess access,Clock clock){
        this.cards=cards;this.ordinaryBudget=null;this.access=Objects.requireNonNull(access);this.clock=Objects.requireNonNull(clock);
        if(cards.census() instanceof IncompleteCensus)status=Status.INCOMPLETE;
    }

    /** Ordinary business limits; these are configured paths and bytes, never qualification cards. */
    private record OrdinaryBudget(List<ManagedRoot> roots,String defaultRootId,String windowId,long maximumChargedBytes) {
        OrdinaryBudget { roots=List.copyOf(roots); }
    }
    private RootRuntimeStorageGuard(OrdinaryBudget budget,WriterAccess access,Clock clock) {
        this.cards=null;this.ordinaryBudget=Objects.requireNonNull(budget);
        this.access=Objects.requireNonNull(access);this.clock=Objects.requireNonNull(clock);
    }
    /** One real aggregate byte budget for the application's ordinary persistent output paths. */
    public static RootRuntimeStorageGuard ordinary(RootApplicationConfiguration application,WriterAccess access,
            List<Path> actualManagedRoots,long maximumChargedBytes,Clock clock)throws IOException {
        Objects.requireNonNull(application);
        return ordinary(application.ledger().lock(), application.artifactRoot(), application.ledger().snapshot().getParent(), access, actualManagedRoots, maximumChargedBytes, clock);
    }

    public static RootRuntimeStorageGuard ordinary(org.xar.ck3.control.continuity.writer.WriterContracts.InitialLayout initialLayout,Path archiveRoot,WriterAccess access,
            List<Path> actualManagedRoots,long maximumChargedBytes,Clock clock)throws IOException {
        Objects.requireNonNull(initialLayout);
        Objects.requireNonNull(archiveRoot);
        return ordinary(initialLayout.lock(), archiveRoot, initialLayout.snapshot().getParent(), access, actualManagedRoots, maximumChargedBytes, clock);
    }

    private static RootRuntimeStorageGuard ordinary(Path originalLock,Path archiveRoot,Path ledgerParent,WriterAccess access,
            List<Path> actualManagedRoots,long maximumChargedBytes,Clock clock)throws IOException {
        Objects.requireNonNull(originalLock);Objects.requireNonNull(archiveRoot);Objects.requireNonNull(ledgerParent);Objects.requireNonNull(access);Objects.requireNonNull(clock);
        normalized(originalLock);
        Objects.requireNonNull(actualManagedRoots);
        if(actualManagedRoots.isEmpty()||actualManagedRoots.size()>64||maximumChargedBytes<=0||maximumChargedBytes>SAFE)
            throw new IOException("bounded actual runtime roots and one positive aggregate byte budget required");
        var requested=new ArrayList<Path>(actualManagedRoots);
        requested.add(archiveRoot);requested.add(ledgerParent);
        var normalizedRoots=new ArrayList<Path>();
        for(Path raw:requested){
            Path p=Objects.requireNonNull(raw).normalize();normalized(p);
            if(p.getParent()==null)throw new IOException("a whole volume is not an ordinary runtime output root");
            if(!normalizedRoots.contains(p))normalizedRoots.add(p);
        }
        Path preferred=actualManagedRoots.getFirst().normalize();var definitions=new ArrayList<ManagedRoot>();
        for(Path p:normalizedRoots){
            if(normalizedRoots.stream().anyMatch(other->!other.equals(p)&&p.startsWith(other)))continue;
            org.xar.ck3.control.build.ProjectStoragePolicy.requireBulkOutput(p);
            RootRuntimeAllocationCensus.realDirectory(p);
            definitions.add(new ManagedRoot("ordinary-"+definitions.size(),p.toString(),maximumChargedBytes,maximumChargedBytes));
        }
        String defaultId=definitions.stream().filter(r->preferred.startsWith(Path.of(r.path()))).findFirst().orElseThrow().rootId();
        String window=DriverJson.sha256(originalLock.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var guard=new RootRuntimeStorageGuard(new OrdinaryBudget(definitions,defaultId,window,maximumChargedBytes),access,clock);
        guard.expectedOriginalLock=originalLock;
        guard.requireDeclaredPaths(normalizedRoots);return guard;
    }
    private List<ManagedRoot> managedRoots(){return ordinaryBudget==null?cards.declaration().roots():ordinaryBudget.roots();}
    private String defaultWriteRootId(){return ordinaryBudget==null?cards.declaration().defaultWriteRootId():ordinaryBudget.defaultRootId();}
    private String windowId(){return ordinaryBudget==null?cards.binding().windowId():ordinaryBudget.windowId();}
    private int maximumEntries(){return ordinaryBudget==null?cards.declaration().maximumEntries():100000;}

    /** Legacy leased-budget overload retained for existing historical consumers. */
    public static RootRuntimeStorageGuard ordinary(RootRuntimeDefinitionModel.StorageLease lease,
            RootApplicationConfiguration application,WriterAccess access,List<Path> requiredOutputRoots,Clock clock)throws IOException {
        Objects.requireNonNull(lease);Objects.requireNonNull(application);Objects.requireNonNull(access);
        Objects.requireNonNull(requiredOutputRoots);Objects.requireNonNull(clock);
        RootRuntimeStorageGuard guard=readExact(lease,application.machineId(),access,clock);
        guard.expectedOriginalLock=application.ledger().lock();
        var required=new ArrayList<Path>();required.add(application.artifactRoot());required.add(application.ledger().snapshot().getParent());
        required.addAll(requiredOutputRoots);guard.requireDeclaredPaths(List.copyOf(required));
        return guard;
    }
    public static RootRuntimeStorageGuard readExact(RootRuntimeDefinitions.Inputs inputs,WriterAccess access,Clock clock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(clock);
        RootRuntimeStorageGuard guard=readExact(inputs.storageLease(),inputs.application().machineId(),access,clock);
        guard.expectedOriginalLock=inputs.application().ledger().lock();
        guard.requireDeclaredPaths(List.of(inputs.application().artifactRoot(),inputs.application().ledger().snapshot().getParent(),
                Path.of(inputs.configuration().incidents().incidentBase()),Path.of(inputs.configuration().incidents().scanBase())));
        return guard;
    }
    /** Package-level complete-card consumer for the real temporary-root/writer regression; grants no Game authority. */
    static RootRuntimeStorageGuard readExact(RootRuntimeDefinitionModel.StorageLease lease,String machine,WriterAccess access,Clock clock)throws IOException {
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        RuntimeBinding binding=read(lease.runtimeBindingRef(),RuntimeBinding.class,originals);
        Declaration declaration=read(binding.declarationRef(),Declaration.class,originals);
        byte[] censusBytes=readOriginal(binding.censusRef(),originals);WholeCensus census=decodeCensus(censusBytes);
        Capacity capacity=read(binding.capacityRef(),Capacity.class,originals);
        ReservationLedger ledger=read(binding.ledgerHeadRef(),ReservationLedger.class,originals);
        if(ledger.predecessorRef()!=null){
            ReservationLedger previous=read(ledger.predecessorRef(),ReservationLedger.class,originals);
            if(previous.generation()!=ledger.generation()-1||!previous.ledgerId().equals(ledger.ledgerId())
                    ||!previous.machineId().equals(ledger.machineId())||!previous.windowId().equals(ledger.windowId())
                    ||instant(previous.observedAtUtc()).isAfter(instant(ledger.observedAtUtc())))
                throw new IOException("runtime ledger predecessor does not prove this exact next generation");
        }
        readOriginal(binding.policyRef(),originals);readOriginal(census.existingWorkpackage().evidenceRef(),originals);
        for(var volume:ledger.volumes())for(var claim:volume.claims())readOriginal(claim.authorityRef(),originals);
        var cards=new Cards(lease,binding,declaration,census,capacity,ledger,originals);
        validateCards(cards,machine);
        if(!binding.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("storage cards belong to another actual execution machine");
        return new RootRuntimeStorageGuard(cards,access,clock);
    }

    /** Root creates one wrapped port before passing it to Stage, SeedStore, SAVE, restore and lifecycle producers. */
    public synchronized CheckpointFiles checkpointFiles(CheckpointFiles actualNativeFiles)throws IOException {
        Objects.requireNonNull(actualNativeFiles);
        if(wrappedFiles==null){nativeFiles=actualNativeFiles;wrappedFiles=new GuardedFiles();}
        else if(nativeFiles!=actualNativeFiles)throw new IOException("one runtime storage guard cannot replace its original file producer");
        return wrappedFiles;
    }
    public synchronized void requireFilePort(CheckpointFiles actual)throws IOException {
        if(actual!=wrappedFiles||wrappedFiles==null)throw new IOException("runtime writes require this guard's identical wrapped native file producer");
    }
    /** A read-only physical importer must hold this guard's actual original writer scope and file port.
     * This checks existing authority and its expiry; it does not admit storage, mutate a ledger or issue Game Ready. */
    public synchronized void requireReadScope(ContinuityStorePort.Session same,CheckpointFiles actual)throws IOException {
        requireFilePort(actual);assertCurrent(Objects.requireNonNull(same));requireAllocationOwner();
    }
    /** Retained DATA read authority is the open state of this guard.
     * Storage admission, writer scopes and Game permissions are handled separately. */
    public synchronized void requireReadAuthorityCurrent()throws IOException {
        if(closed)throw new IOException("the original runtime allocation owner is closed");
    }
    public void requireManagedRoots(List<Path> actualRoots)throws IOException {
        Objects.requireNonNull(actualRoots);assertOriginals();
        for(Path path:actualRoots){
            normalized(path);if(cards!=null)RootRuntimeAllocationCensus.realDirectory(path);
            if(managedRoots().stream().noneMatch(root->path.startsWith(Path.of(root.path()))))
                throw new IOException("actual runtime writer path is outside its issuer-declared allocation roots: "+path);
        }
    }
    /** Pre-construction path qualification permits missing descendants of the actual signed root.
     * Creating them still requires the exclusive allocation owner and a reserved DirectoryCreate plan. */
    public void requireDeclaredPaths(List<Path> actualPaths)throws IOException {
        Objects.requireNonNull(actualPaths);assertOriginals();
        if(actualPaths.isEmpty()||actualPaths.size()>64)throw new IOException("bounded explicit runtime output paths required");
        for(Path path:actualPaths){normalized(path);if(cards!=null)SharedSourceFiles.plainAncestors(path);
            if(managedRoots().stream().noneMatch(root->path.startsWith(Path.of(root.path()))))
                throw new IOException("actual runtime output path is outside its finite issuer-declared roots: "+path);}
    }
    public void requireCompleteAdmission()throws IOException {
        inWriter(same->{synchronized(this){admit(same);}return null;});
    }
    public void refreshManagedRoots()throws IOException {
        inWriter(same->{synchronized(this){admit(same);try{refresh(false);checkCapacity(0,null);}
            catch(IOException unavailable){status=Status.INCOMPLETE;throw unavailable;}}return null;});
    }
    /** Controlled creation of bounded descendants of one already admitted output root. No root/card is created here. */
    public void createManagedDirectories(Path target)throws IOException {
        Objects.requireNonNull(target);normalized(target);
        inWriter(same->{
            PendingWrite reservation;List<Path> missing=new ArrayList<>();RootState original;
            synchronized(this){
                admit(same);
                if(roots.values().stream().anyMatch(root->target.equals(Path.of(root.definition.path())))){
                    if(cards!=null)RootRuntimeAllocationCensus.realDirectory(target);return null;
                }
                original=targetRoot(target);
                Path owner=Path.of(original.definition.path()),cursor=target;
                while(!Files.exists(cursor,LinkOption.NOFOLLOW_LINKS)){
                    if(cursor.equals(owner)||!cursor.startsWith(owner)||missing.size()>=64)
                        throw new IOException("runtime directory creation exceeds its bounded admitted ancestry");
                    missing.add(cursor);cursor=cursor.getParent();
                }
                if(cards!=null)RootRuntimeAllocationCensus.realDirectory(cursor);
                if(missing.isEmpty())return null;
                if(roots.values().stream().mapToLong(root->root.files.size()+root.directories.size()).sum()+missing.size()
                        >maximumEntries())throw new IOException("runtime directory creation exceeds the complete census inventory bound");
                long peak=multiply(missing.size(),DIRECTORY_GUARD);checkCapacity(peak,original);
                reservation=addPending(original,target,0,null,peak,false,true);
            }
            try{
                for(int index=missing.size()-1;index>=0;index--){
                    Path directory=missing.get(index);if(cards!=null)RootRuntimeAllocationCensus.realDirectory(directory.getParent());
                    Files.createDirectory(directory);
                    if(cards!=null)RootRuntimeAllocationCensus.realDirectory(directory);
                    else if(!Files.isDirectory(directory,LinkOption.NOFOLLOW_LINKS))throw new IOException("ordinary directory create has no actual directory result");
                    synchronized(this){assertCurrent(same);RootState actual=owned(reservation.rootId());
                        if(!actual.directories.add(directory))throw new IOException("new runtime directory was already present in its retained allocation inventory");
                        actual.charged=add(actual.charged,DIRECTORY_GUARD);
                    }
                }
                synchronized(this){assertCurrent(same);removePending(reservation);checkCapacity(0,null);}return null;
            }catch(IOException|RuntimeException failure){synchronized(this){status=pending.containsKey(reservation.id())?Status.UNKNOWN_WRITE:Status.INCOMPLETE;}throw failure;}
        });
    }
    /** A lost directory-create return has storage-only reconciliation from the original exact target and a full bounded audit.
     * Missing descendants remain UNKNOWN; this never repeats mkdir or grants any Game/action qualification. */
    public void reconcileCreatedDirectories(Path originalTarget)throws IOException {
        Objects.requireNonNull(originalTarget);normalized(originalTarget);
        inWriter(same->{synchronized(this){assertCurrent(same);
            PendingWrite original=pending.values().stream().filter(write->write.directory()&&originalTarget.equals(write.target()))
                    .findFirst().orElseThrow(()->new IOException("no original unresolved controlled directory creation has this target"));
            if(ordinaryBudget!=null)updateMeasured(originalTarget);else{RootRuntimeAllocationCensus.realDirectory(originalTarget);refresh(false);}removePending(original);
            status=pending.values().stream().anyMatch(write->!write.legacyUnscoped())?Status.UNKNOWN_WRITE:Status.ADMITTED;
            try{checkCapacity(0,null);}catch(IOException unavailable){status=Status.INCOMPLETE;throw unavailable;}
        }return null;});
    }
    /** SeedStore's combined-copy quote is checked before actual writes; wrappedFiles reserves each exact target. */
    public void requireSeed(long fullCopyBytes)throws IOException {
        inWriter(same->{synchronized(this){admit(same);requireWrapped();RootState root=defaultRoot();checkCapacity(charge(fullCopyBytes,Path.of(root.definition.path())),root);}return null;});
    }
    public SeedStore.StorageGuard seedGuard(){return this::requireSeed;}
    /** Legacy direct incident writes have no target/post-read callback. Their reservations remain conservative and never guessed released. */
    public EpisodeIncidentJournal.IoGuard incidentGuard(){return this::reserveLegacyIncident;}
    public EpisodeIncidentJournal.IoGuard incidentGuard(List<Path> actualOutputRoots)throws IOException {
        requireManagedRoots(actualOutputRoots);Path defaultPath=Path.of(managedRoots().stream()
                .filter(root->root.rootId().equals(defaultWriteRootId())).findFirst().orElseThrow().path());
        for(Path root:actualOutputRoots)if(!root.startsWith(defaultPath))
            throw new IOException("legacy target-less incident guard requires all actual outputs inside its explicit default write root");
        return incidentGuard();
    }
    public void reserveLegacyIncident(long bytes)throws IOException {
        inWriter(same->{synchronized(this){admit(same);RootState root=defaultRoot();long peak=charge(bytes,Path.of(root.definition.path()));
            checkCapacity(peak,root);addPending(root,null,bytes,null,peak,true);}return null;});
    }
    public synchronized Accounting accounting(){return new Accounting(status,roots.values().stream().map(root->
            new RootAccounting(root.definition.rootId(),root.charged,root.pending,root.definition.maximumChargedBytes())).toList(),pending.size()+unresolvedPhysical.size());}

    /** An unknown file write is reconciled only from its exact original expected bytes and a real physical witness.
     * This releases storage accounting only; it never replays or settles a Game/action UNKNOWN. */
    public void reconcileWrite(FileWitness actual)throws IOException {
        Objects.requireNonNull(actual);
        inWriter(same->{synchronized(this){assertCurrent(same);requireWrapped();nativeFiles.verify(actual);
            Path target=Path.of(actual.reference().path());var selected=pending.values().stream()
                    .filter(write->!write.legacyUnscoped()&&!write.directory()&&target.equals(write.target())
                            &&write.expectedBytes()==actual.reference().bytes()&&write.expectedSha256().equalsIgnoreCase(actual.reference().sha256()))
                    .findFirst().orElseThrow(()->new IOException("actual file witness does not match an original unresolved storage write"));
            if(ordinaryBudget!=null)updateMeasured(target);else refresh(false);removePending(selected);status=pending.values().stream().anyMatch(write->!write.legacyUnscoped())?Status.UNKNOWN_WRITE:Status.ADMITTED;
            try{checkCapacity(0,null);}catch(IOException unavailable){status=Status.INCOMPLETE;throw unavailable;}}return null;});
    }

    private void admit(ContinuityStorePort.Session same)throws IOException {
        assertCurrent(same);requireAllocationOwner();
        synchronized(OWNERS){
            Map<String,WeakReference<RootRuntimeStorageGuard>> windows=OWNERS.computeIfAbsent(requireWriter(),ignored->new HashMap<>());
            WeakReference<RootRuntimeStorageGuard> retained=windows.get(windowId());
            if(retained!=null&&retained.get()!=null&&retained.get()!=this)
                throw new IOException("same original writer/runtime window already has its retained storage guard");
            windows.put(windowId(),new WeakReference<>(this));
        }
        if(cards!=null&&cards.census() instanceof IncompleteCensus incomplete){status=Status.INCOMPLETE;throw new IOException("INCOMPLETE_RUNTIME_STORAGE_CENSUS: "+incomplete.reasons());}
        if(status==Status.UNKNOWN_WRITE)throw new IOException("runtime storage has an original unresolved file write; exact reconciliation is required");
        if(auditedAt==null)refresh(true);
        else if(cards!=null&&!clock.instant().isBefore(auditedAt.plusMillis(cards.declaration().auditIntervalMillis())))refresh(false);
        try{checkCapacity(0,null);status=Status.ADMITTED;}
        catch(IOException rejected){status=Status.INCOMPLETE;throw rejected;}
    }
    private void refresh(boolean initial)throws IOException {
        if(ordinaryBudget!=null){
            // Live logs are not an immutable census. Account only for explicit output operations.
            for(ManagedRoot definition:managedRoots())if(!roots.containsKey(definition.rootId())){
                Path path=Path.of(definition.path());RootRuntimeAllocationCensus.realDirectory(path);
                roots.put(definition.rootId(),new RootState(definition,SharedSourceFiles.nativeDirectory(path)));
            }
            auditedAt=clock.instant();return;
        }
        RootRuntimeAllocationCensus.Capture capture=RootRuntimeAllocationCensus.capture(cards.declaration(),clock);
        if(initial&&cards!=null){
            CompleteCensus expected=(CompleteCensus)cards.census();
            if(!capture.roots().equals(expected.runtimeRoots()))throw new IOException("actual runtime root allocation/identity inventory differs from the signed complete census");
        }
        for(RootAllocation actual:capture.roots()){
            RootState old=roots.get(actual.rootId());ManagedRoot definition=managedRoots().stream().filter(r->r.rootId().equals(actual.rootId())).findFirst().orElseThrow();
            if(old!=null&&!old.identity.equals(actual.directoryIdentity()))throw new IOException("runtime root directory identity changed");
            RootState current=new RootState(definition,actual);if(old!=null)current.pending=old.pending;
            for(var file:capture.files())if(file.rootId().equals(actual.rootId()))current.files.put(Path.of(definition.path()).resolve(file.relativePath()),file.nativeFile());
            for(var directory:capture.directories())if(directory.rootId().equals(actual.rootId()))current.directories.add(Path.of(definition.path()).resolve(directory.relativePath()));
            roots.put(actual.rootId(),current);
        }
        auditedAt=clock.instant();
    }
    private void assertCurrent(ContinuityStorePort.Session same)throws IOException {
        ContinuityWriter actual=requireWriter();actual.requireSession(same);assertAllocationCurrent();
    }
    private void assertAllocationCurrent()throws IOException {
        if(closed)throw new IOException("the original runtime allocation owner is closed");
        assertOriginals();
        if(cards!=null){
        String machine=cards.binding().machineId(),window=windowId();
        for(var period:List.of(new Period(cards.binding().observedAtUtc(),cards.binding().reviewAtUtc()),
                new Period(cards.declaration().observedAtUtc(),cards.declaration().reviewAtUtc()),
                new Period(cards.census().observedAtUtc(),cards.census().reviewAtUtc()),
                new Period(cards.capacity().observedAtUtc(),cards.capacity().reviewAtUtc()),
                new Period(cards.ledger().observedAtUtc(),cards.ledger().reviewAtUtc()),
                new Period(cards.lease().observedAtUtc(),cards.lease().reviewAtUtc())))
            if(clock.instant().isBefore(instant(period.observed()))||!clock.instant().isBefore(instant(period.review())))
                throw new IOException("runtime storage authority for "+machine+"/"+window+" is future-dated or expired");
        for(RootState root:roots.values())if(!SharedSourceFiles.nativeDirectory(Path.of(root.definition.path())).equals(root.identity))
            throw new IOException("actual runtime allocation root identity drifted");
        }
    }
    private record Period(String observed,String review) { }
    private void assertOriginals()throws IOException {if(cards!=null)for(var original:cards.originals())SharedSourceFiles.assertUnchanged(original);}
    private synchronized ContinuityWriter requireWriter()throws IOException {
        ContinuityWriter actual=Objects.requireNonNull(access.requireWriter());
        if(writer==null)writer=actual;else if(writer!=actual)throw new IOException("runtime storage cannot replace its sole original writer");
        return actual;
    }
    private <T>T inWriter(SessionWork<T> work)throws IOException {
        ContinuityWriter actual=requireWriter();Optional<ContinuityStorePort.Session> active=actual.activeSession();
        if(active.isPresent()){actual.requireSession(active.orElseThrow());return work.run(active.orElseThrow());}
        return actual.locked(same->{actual.requireSession(same);return work.run(same);});
    }
    private RootState defaultRoot()throws IOException {return owned(defaultWriteRootId());}
    private RootState owned(String id)throws IOException {RootState result=roots.get(id);if(result==null)throw new IOException("runtime allocation root has not been actually admitted: "+id);return result;}
    private RootState targetRoot(Path target)throws IOException {
        normalized(target);if(cards!=null)SharedSourceFiles.plainAncestors(target);
        return roots.values().stream().filter(root->target.startsWith(Path.of(root.definition.path()))&&!target.equals(Path.of(root.definition.path())))
                .findFirst().orElseThrow(()->new IOException("file write escaped every actual managed runtime root: "+target));
    }
    private void requireWrapped()throws IOException {if(wrappedFiles==null)throw new IOException("the actual guarded CheckpointFiles producer is not bound");}

    private void checkCapacity(long prospective,RootState selected)throws IOException {
        nonnegative(prospective);long whole=0;
        for(RootState root:roots.values()){
            long projected=add(root.charged,root.pending);if(root==selected)projected=add(projected,prospective);
            if(projected>root.definition.maximumChargedBytes())throw new IOException("runtime root charged allocation plus pending writes exceeds its finite cap: "+root.definition.rootId());
            if(root==selected&&prospective>root.definition.maximumSingleWriteBytes())throw new IOException("runtime write exceeds the signed per-write peak cap");
            whole=add(whole,projected);
        }

        if(ordinaryBudget!=null){
            if(whole>ordinaryBudget.maximumChargedBytes())throw new IOException("runtime actual allocation plus pending writes exceeds its configured aggregate byte budget");
            var checked=new HashSet<java.nio.file.FileStore>();
            for(RootState root:roots.values()){
                var store=Files.getFileStore(Path.of(root.definition.path()));if(!checked.add(store))continue;
                long awaiting=0;for(RootState own:roots.values())
                    if(Files.getFileStore(Path.of(own.definition.path())).equals(store))awaiting=add(awaiting,own.pending);
                if(selected!=null&&Files.getFileStore(Path.of(selected.definition.path())).equals(store))awaiting=add(awaiting,prospective);
                if(store.getUsableSpace()<add(awaiting,safety(store.getTotalSpace())))
                    throw new IOException("actual runtime volume lacks pending writes plus ordinary policy safety");
            }
            return;
        }
        if(whole>cards.lease().wholeWorkpackageMaximumNativeBytes())throw new IOException("complete new runtime package exceeds the actual outer lease cap");
        for(var allowance:cards.capacity().volumes()){
            Path volume=Path.of(allowance.volumeRoot());long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
            long ownPending=0;for(RootState root:roots.values())if(Path.of(root.definition.path()).startsWith(volume))ownPending=add(ownPending,root.pending);
            if(selected!=null&&Path.of(selected.definition.path()).startsWith(volume))ownPending=add(ownPending,prospective);
            VolumeReservations reservations=cards.ledger().volumes().stream().filter(row->Path.of(row.volumeRoot()).equals(volume)).findFirst().orElseThrow();
            long other=0;for(var claim:reservations.claims())if(!claim.windowId().equals(windowId()))other=add(other,claim.unspentBytes());
            long signedMinimum=cards.lease().volumes().stream().filter(row->Path.of(row.root()).equals(volume)).findFirst().orElseThrow().minimumUsableBytes();
            long safety=Math.max(signedMinimum,safety(total));
            long required=add(add(ownPending,other),add(allowance.systemGrowthReserveBytes(),safety));
            if(free<required)throw new IOException("actual runtime volume lacks pending writes + other reservations + system reserve + policy safety");
            long upper=Math.max(cards.census().existingWorkpackage().conservativeUpperBytes(),Math.subtractExact(total,free));
            long quota=allowance.quotaOverrideMaximumBytes()==null?Math.min(100L<<30,percent(total,10)):allowance.quotaOverrideMaximumBytes();
            if(allowance.quotaReviewAtUtc()!=null&&!clock.instant().isBefore(instant(allowance.quotaReviewAtUtc())))throw new IOException("actual runtime quota override expired");
            if(add(add(upper,other),ownPending)>quota)throw new IOException("conservative whole-volume/project upper plus all unspent claims exceeds the finite quota");
        }
    }
    static long safety(long total){return Math.max(2L<<30,Math.min(20L<<30,percent(total,5)));}
    private static long percent(long total,int percentage){return BigInteger.valueOf(total).multiply(BigInteger.valueOf(percentage)).add(BigInteger.valueOf(99)).divide(BigInteger.valueOf(100)).longValueExact();}
    private static long charge(long bytes,Path directory)throws IOException {
        nonnegative(bytes);long unit;
        try{unit=Files.getFileStore(directory).getBlockSize();}catch(UnsupportedOperationException unavailable){throw new IOException("actual runtime allocation unit is unavailable",unavailable);}
        if(unit<=0||unit>(2L<<20))throw new IOException("actual runtime allocation unit is unavailable/out of bounds");
        return add(multiply(Math.floorDiv(add(bytes,unit-1),unit),unit),DIRECTORY_GUARD);
    }
    private PendingWrite addPending(RootState root,Path target,long bytes,String sha,long peak,boolean legacy)throws IOException {
        return addPending(root,target,bytes,sha,peak,legacy,false);
    }
    private PendingWrite addPending(RootState root,Path target,long bytes,String sha,long peak,boolean legacy,boolean directory)throws IOException {
        if(pending.size()>=4096)throw new IOException("bounded unresolved runtime writes require exact reconciliation");
        nextWriteId=add(nextWriteId,1);var result=new PendingWrite(nextWriteId,root.definition.rootId(),target,bytes,sha,peak,legacy,directory);
        root.pending=add(root.pending,peak);pending.put(result.id(),result);return result;
    }
    private void removePending(PendingWrite write)throws IOException {
        if(pending.remove(write.id())!=write)throw new IOException("runtime storage reservation cannot be settled twice");
        RootState root=owned(write.rootId());root.pending=Math.subtractExact(root.pending,write.peakBytes());
    }
    private FileWitness write(Path target,long bytes,String sha,boolean replace,FileWrite operation)throws IOException {
        if(activePhysical.get()!=null){
            if(replace)throw new IOException("nested physical replacement must declare its real temporary-file and rename phases");
            return write(new WritePlan(Objects.requireNonNull(expectedOriginalLock),List.of(new FileCreate(target,bytes))),()->{
                FileWitness actual=operation.run();nativeFiles.verify(actual);
                if(!Path.of(actual.reference().path()).equals(target)||actual.reference().bytes()!=bytes||!actual.reference().sha256().equalsIgnoreCase(sha))
                    throw new IOException("nested guarded file differs from its original exact target/body");
                return actual;
            });
        }
        return inWriter(same->{
            PendingWrite reservation;
            synchronized(this){admit(same);requireWrapped();RootState root=targetRoot(target);
                if(cards!=null){
                    RootRuntimeAllocationCensus.realDirectory(target.getParent());
                    if(!root.directories.contains(target.getParent())){refresh(false);root=targetRoot(target);}
                }
                if(cards!=null&&replace&&Files.exists(target,LinkOption.NOFOLLOW_LINKS)&&SharedSourceFiles.nativeFile(target).linkCount()!=1)
                    throw new IOException("runtime cannot replace a shared/hardlinked original file");
                long peak=charge(bytes,target.getParent());checkCapacity(peak,root);reservation=addPending(root,target,bytes,sha,peak,false);}
            try{
                FileWitness actual=operation.run();nativeFiles.verify(actual);
                if(!Path.of(actual.reference().path()).equals(target)||actual.reference().bytes()!=bytes||!actual.reference().sha256().equalsIgnoreCase(sha))
                    throw new IOException("physical runtime file result differs from the original reserved target/body");
                synchronized(this){assertCurrent(same);RootState root=owned(reservation.rootId());
                    if(ordinaryBudget!=null)applyOrdinaryMeasured(target,new MeasuredPath(false,ordinaryFileResult(target)));
                    else{SharedSourceFiles.NativeFile measured=SharedSourceFiles.nativeFile(target);var previous=root.files.put(target,measured);
                        root.charged=add(Math.subtractExact(root.charged,previous==null?0:previous.allocatedBytes()),measured.allocatedBytes());}
                    removePending(reservation);checkCapacity(0,null);}
                return actual;
            }catch(IOException|RuntimeException failure){synchronized(this){status=pending.containsKey(reservation.id())?Status.UNKNOWN_WRITE:Status.INCOMPLETE;}throw failure;}
        });
    }
    private final class GuardedFiles implements CheckpointFiles {
        @Override public Optional<FileWitness> observe(Path path)throws IOException{return nativeFiles.observe(path);}
        @Override public byte[] read(FileWitness expected,int maximumBytes)throws IOException{return nativeFiles.read(expected,maximumBytes);}
        @Override public FileWitness createNew(Path target,byte[] body)throws IOException{
            byte[] original=body.clone();return write(target,original.length,DriverJson.sha256(original),false,()->nativeFiles.createNew(target,original));}
        @Override public FileWitness replace(Path target,byte[] body)throws IOException{
            byte[] original=body.clone();return write(target,original.length,DriverJson.sha256(original),true,()->nativeFiles.replace(target,original));}
        @Override public FileWitness copyNew(FileWitness source,Path target)throws IOException{
            nativeFiles.verify(source);return write(target,source.reference().bytes(),source.reference().sha256(),false,()->nativeFiles.copyNew(source,target));}
    }

    private static void normalized(Path path)throws IOException {if(!path.isAbsolute()||!path.normalize().equals(path))throw new IOException("canonical absolute runtime target required");}
    private static <T>T read(FileRef ref,Class<T> type,List<SharedSourceFiles.Witness> originals)throws IOException{return decode(readOriginal(ref,originals),type);}
    private static byte[] readOriginal(FileRef ref,List<SharedSourceFiles.Witness> originals)throws IOException {
        SharedSourceFiles.Witness before=SharedSourceFiles.observe(Path.of(ref.path()));byte[] body=RootRuntimeDefinitions.read(ref,MAXIMUM_BYTES);
        SharedSourceFiles.assertUnchanged(before);originals.add(before);return body;
    }
    private static boolean same(FileRef a,FileRef b){return Path.of(a.path()).equals(Path.of(b.path()))&&a.bytes()==b.bytes()&&a.sha256().equalsIgnoreCase(b.sha256());}
    private static void validateCards(Cards c,String machine)throws IOException {
        try{
            var b=c.binding();var d=c.declaration();var n=c.census();var a=c.capacity();var l=c.ledger();
            positive(c.lease().wholeWorkpackageMaximumNativeBytes());
            for(var volume:c.lease().volumes()){nonnegative(volume.minimumUsableBytes());nonnegative(volume.systemGrowthReserveBytes());}
            require(List.of(b.machineId(),d.machineId(),n.machineId(),a.machineId(),l.machineId(),c.lease().machineId()).stream().allMatch(machine::equals),"one actual machine across runtime storage originals required");
            require(List.of(d.windowId(),n.windowId(),a.windowId(),l.windowId()).stream().allMatch(b.windowId()::equals),"one runtime declaration window across all originals required");
            List<String> observations=List.of(d.observedAtUtc(),n.observedAtUtc(),a.observedAtUtc(),l.observedAtUtc(),b.observedAtUtc(),c.lease().observedAtUtc());
            for(int i=1;i<observations.size();i++)require(!instant(observations.get(i)).isBefore(instant(observations.get(i-1))),
                    "runtime originals must follow their acyclic producer observation order");
            require(same(c.lease().policyRef(),b.policyRef())&&same(c.lease().capacityReleaseRef(),b.capacityRef())&&same(c.lease().wholeWorkpackageCensusRef(),b.censusRef()),"outer runtime lease selects other originals");
            require(same(n.declarationRef(),b.declarationRef())&&same(a.declarationRef(),b.declarationRef())&&same(l.declarationRef(),b.declarationRef())
                    &&same(a.censusRef(),b.censusRef())&&same(a.policyRef(),b.policyRef())&&same(l.policyRef(),b.policyRef())
                    &&same(l.capacityRef(),b.capacityRef())&&l.generation()==b.ledgerGeneration(),"runtime binding/census/capacity/ledger ancestry differs");
            require(d.roots().size()==c.lease().roots().size(),"outer lease must include every declared runtime root");
            for(var original:c.originals())require(d.roots().stream().noneMatch(root->Path.of(original.source().path()).startsWith(Path.of(root.path()))),
                    "runtime authority originals must be outside mutable output roots, including their census snapshot");
            for(var root:d.roots())require(c.lease().roots().stream().anyMatch(row->Path.of(row.path()).equals(Path.of(root.path()))
                    &&row.maximumNativeBytes()==root.maximumChargedBytes()),"runtime root caps differ from original outer lease");
            require(a.volumes().size()==l.volumes().size()&&a.volumes().size()==c.lease().volumes().size(),"all runtime volumes and reservations are mandatory");
            for(var volume:a.volumes()){
                Path path=Path.of(volume.volumeRoot());require(path.equals(path.getRoot()),"reservation volume must be the actual volume root");
                require(c.lease().volumes().stream().anyMatch(row->Path.of(row.root()).equals(path)&&row.systemGrowthReserveBytes()==volume.systemGrowthReserveBytes()),"outer volume/system reserve differs");
                VolumeReservations rows=l.volumes().stream().filter(row->Path.of(row.volumeRoot()).equals(path)).findFirst().orElseThrow();
                var own=rows.claims().stream().filter(claim->claim.windowId().equals(b.windowId())).toList();
                require(own.size()==1&&own.getFirst().ownerTask().equals("/root")&&own.getFirst().machineId().equals(machine)
                        &&own.getFirst().scope()==ClaimScope.CANONICAL_OUTPUT_ROOTS&&same(own.getFirst().authorityRef(),b.capacityRef())
                        &&own.getFirst().unspentBytes()>=volume.maximumRuntimeGrowthBytes(),"complete original runtime growth reservation is required");
                var expected=d.roots().stream().filter(root->Path.of(root.path()).startsWith(path)).map(ManagedRoot::path).sorted().toList();
                require(own.getFirst().canonicalOutputRoots().stream().sorted().toList().equals(expected),"runtime claim must own exactly its declared roots on this volume");
                long cap=0;for(var root:d.roots())if(Path.of(root.path()).startsWith(path))cap=add(cap,root.maximumChargedBytes());
                require(!expected.isEmpty()&&volume.maximumRuntimeGrowthBytes()>=cap,"runtime capacity must retain the complete peak, without guessing old allocation release");
            }
            for(var root:d.roots())require(a.volumes().stream().filter(volume->Path.of(root.path()).startsWith(Path.of(volume.volumeRoot()))).count()==1,
                    "each managed runtime root must belong to exactly one complete volume grant");
            if(n instanceof CompleteCensus complete)require(complete.runtimeRoots().stream().map(RootAllocation::rootId).sorted().toList()
                    .equals(d.roots().stream().map(ManagedRoot::rootId).sorted().toList()),"complete census must cover every declared runtime root");
            for(String review:List.of(d.reviewAtUtc(),n.reviewAtUtc(),a.reviewAtUtc(),l.reviewAtUtc(),b.reviewAtUtc()))
                require(!instant(c.lease().reviewAtUtc()).isAfter(instant(review)),"outer runtime lease cannot outlive any original authority");
            var policy=org.xar.ck3.control.contracts.StrictJson.parse(RootRuntimeDefinitions.read(b.policyRef(),MAXIMUM_BYTES),MAXIMUM_BYTES);
            require("1.0.0".equals(org.xar.ck3.control.contracts.StrictJson.text(policy.get("policy_version"))),"runtime storage implements exact common policy v1.0.0");
            var capacity=policy.get("capacity");
            require(org.xar.ck3.control.contracts.StrictJson.integer(capacity.get("safety_floor_bytes"),0,SAFE)==(2L<<30)
                    &&org.xar.ck3.control.contracts.StrictJson.integer(capacity.get("safety_ceiling_bytes"),0,SAFE)==(20L<<30)
                    &&org.xar.ck3.control.contracts.StrictJson.integer(capacity.get("default_project_quota_ceiling_bytes"),0,SAFE)==(100L<<30)
                    &&capacity.get("safety_volume_fraction").isNumber()
                    &&capacity.get("safety_volume_fraction").decimalValue().compareTo(new java.math.BigDecimal("0.05"))==0
                    &&capacity.get("default_project_quota_volume_fraction").isNumber()
                    &&capacity.get("default_project_quota_volume_fraction").decimalValue().compareTo(new java.math.BigDecimal("0.10"))==0,
                    "common safety/quota policy constants changed");
        }catch(IllegalArgumentException|java.util.NoSuchElementException failure){throw new IOException("INCOMPLETE_OR_INVALID_RUNTIME_STORAGE_ORIGINALS: "+failure.getMessage(),failure);}
    }
}
