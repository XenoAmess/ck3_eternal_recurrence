package org.xar.ck3.control.continuity.writer;

import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Finite real-filesystem software test admission. Never a production Root storage card or Game authority. */
public final class StorageWriteGuardTestSupport implements StorageWriteGuard {
    private static final Map<Path,StorageWriteGuardTestSupport> SCOPES=new HashMap<>();
    private static final long DEFAULT_LIMIT=67_108_864;
    private static final class Frame {
        final WritePlan plan;final List<Mutation> available;
        final Map<Path,FileIdentity> observedWrites=new HashMap<>();
        Frame(WritePlan plan){this.plan=plan;available=new ArrayList<>(plan.mutations());}
    }
    private final Path root,lock;
    private final Object rootId;
    private final FileIdentity lockId;
    private final Pin originalCard;
    private final long limit,unit;
    private final Instant expiry;
    private final ThreadLocal<ArrayDeque<Frame>> frames=ThreadLocal.withInitial(ArrayDeque::new);
    private boolean unknown;
    private volatile boolean closed;
    private long validations,successfulBatches;
    private StorageWriteGuardTestSupport(Path root,Path lock,long limit)throws IOException {
        this.root=root;this.lock=lock;this.limit=limit;
        var attributes=IdentityBearingFileAttributes.read(root);
        if(!attributes.isDirectory()||attributes.isSymbolicLink()||attributes.fileKey()==null)
            throw new IOException("actual ordinary native fixture root required");
        rootId=attributes.fileKey();lockId=LedgerFiles.identity(lock);
        unit=Files.getFileStore(root).getBlockSize();if(unit<1||unit>1_048_576)throw new IOException("actual finite allocation unit required");
        expiry=Instant.now().plusSeconds(3600);
        ObjectNode card=StrictJson.object();card.put("schema","xar.software-storage-fixture-card/v1");
        card.put("root",root.toString());card.put("original_lock",lock.toString());card.put("maximum_charged_bytes",limit);
        card.put("review_at_utc",expiry.toString());card.put("machine_id",WindowsJobProcess.currentMachineId());
        card.put("lock_file_id_decimal",lockId.fileIdDecimal());card.put("lock_creation_filetime_decimal",lockId.creationFiletimeDecimal());
        Path path=root.resolve("software-storage-card-"+java.util.UUID.randomUUID().toString().replace("-","")+".json");
        Files.write(path,StrictJson.canonical(card),java.nio.file.StandardOpenOption.CREATE_NEW);
        originalCard=LedgerFiles.read(path,65_536).pin();scan();
    }
    public static synchronized StorageWriteGuardTestSupport create(Path suppliedRoot,Path suppliedLock,long maxChargedBytes)throws IOException {
        Path root=suppliedRoot.toAbsolutePath().normalize(),lock=suppliedLock.toAbsolutePath().normalize();
        if(!lock.startsWith(root)||maxChargedBytes<4096||maxChargedBytes>1_073_741_824L)
            throw new IOException("finite exact software root/lock/cap required");
        StorageWriteGuardTestSupport known=SCOPES.get(lock);
        if(known!=null){if(!known.root.equals(root)||known.limit!=maxChargedBytes)throw new IOException("fixture scope cannot rebind root/cap");known.originals();return known;}
        if(SCOPES.size()>=2048)throw new IOException("finite software scope inventory exhausted");
        StorageWriteGuardTestSupport actual=new StorageWriteGuardTestSupport(root,lock,maxChargedBytes);SCOPES.put(lock,actual);return actual;
    }
    public static StorageWriteGuardTestSupport create(Layout layout)throws IOException {
        return create(layout.snapshot().getParent(),layout.lock(),DEFAULT_LIMIT);
    }
    public static synchronized StorageWriteGuardTestSupport forOriginalLock(Path path)throws IOException {
        StorageWriteGuardTestSupport result=SCOPES.get(path.toAbsolutePath().normalize());
        if(result==null)throw new IOException("software fixture must explicitly create its finite admission before constructors");
        result.originals();return result;
    }
    public static StorageWriteGuardTestSupport forLayout(Layout layout)throws IOException {return forOriginalLock(layout.lock());}
    public static synchronized StorageWriteGuardTestSupport forTarget(Path target)throws IOException {
        StorageWriteGuardTestSupport selected=null;
        for(StorageWriteGuardTestSupport candidate:SCOPES.values())if(target.toAbsolutePath().normalize().startsWith(candidate.root)){
            if(selected!=null&&!selected.root.equals(candidate.root))throw new IOException("ambiguous nested software storage roots");
            selected=candidate;
        }
        if(selected==null)throw new IOException("target has no explicitly created software admission");
        selected.originals();return selected;
    }
    public Path originalLock(){return lock;}
    /** Temporary persistence setup still uses the actual original lock and guarded primitive. */
    public static void atomic(Path target,byte[] canonical,boolean replace)throws IOException {
        StorageWriteGuardTestSupport scope=forTarget(target);boolean held;
        try{WindowsLedgerLock.requireHeld(scope.lock);held=true;}catch(IOException absent){held=false;}
        if(held)LedgerFiles.atomic(scope,scope.lock,target,canonical,replace);
        else {
            WindowsLedgerLock original=WindowsLedgerLock.acquire(scope.lock);
            try(original){
                WindowsLedgerLock.requireHeld(scope.lock);
                LedgerFiles.atomic(scope,scope.lock,target,canonical,replace);
            }
        }
    }
    @Override public synchronized void requireInitialization(Path originalLock,List<Path> exactManagedRoots)throws IOException {
        originals();if(!lock.equals(originalLock))throw new IOException("another fixture original lock");
        for(Path path:exactManagedRoots){
            if(!path.equals(root))owned(path);
            if(!Files.exists(path,LinkOption.NOFOLLOW_LINKS)){
                LedgerFiles.requireAbsent(path);continue; // Only the declared guarded DirectoryCreate may create it.
            }
            var attrs=IdentityBearingFileAttributes.read(path);
            if(!attrs.isDirectory()||attrs.isSymbolicLink())throw new IOException("ordinary managed directory required");
        }
        if(scan()>limit)throw new IOException("whole fixture allocation exceeds its finite card");
    }
    @Override public synchronized <T>T write(WritePlan plan,PhysicalWrite<T> actualIO)throws IOException {
        originals();Objects.requireNonNull(actualIO);
        if(unknown)throw new IOException("original software storage mutation remains UNKNOWN");
        if(!plan.originalLock().equals(lock))throw new IOException("another original storage lock");
        for(Mutation mutation:plan.mutations()){owned(mutation.target());if(mutation instanceof FileRename rename)owned(rename.source());}
        ArrayDeque<Frame> stack=frames.get();Frame parent=stack.peek();Frame frame=new Frame(plan);
        Map<Path,FileIdentity> observed=parent==null?frame.observedWrites:stack.getLast().observedWrites;
        if(parent==null){
            long peak=scan();for(Mutation mutation:plan.mutations()){
                if(mutation instanceof FileCreate create)peak=Math.addExact(peak,charge(create.maxLogicalBytes()));
                else if(mutation instanceof FileFillExistingEmpty fill)peak=Math.addExact(peak,charge(fill.maxLogicalBytes()));
                else if(mutation instanceof DirectoryCreate)peak=Math.addExact(peak,4096);
            }
            if(peak>limit)throw new IOException("whole physical plan rejected before first IO");
        }else remaining(parent,plan,false);
        Mutation leaf=plan.mutations().size()==1?plan.mutations().getFirst():null;
        FileIdentity original=null;
        if(leaf instanceof FileCreate create)LedgerFiles.requireAbsent(create.target());
        else if(leaf instanceof FileFillExistingEmpty fill){original=LedgerFiles.identity(fill.target());if(original.bytes()!=0)throw new IOException("fill requires original empty file");
            if(observed.containsKey(fill.target())&&!observed.get(fill.target()).equals(original))throw new IOException("created empty file identity changed before fill");}
        else if(leaf instanceof FileRename rename){original=LedgerFiles.identity(rename.source());if(!rename.replace())LedgerFiles.requireAbsent(rename.target());
            if(observed.containsKey(rename.source())&&!observed.get(rename.source()).equals(original))throw new IOException("created source native identity changed before rename");
            if(observed.containsKey(rename.target())&&!observed.get(rename.target()).equals(LedgerFiles.identity(rename.target())))throw new IOException("prior planned rename target changed");}
        else if(leaf instanceof DirectoryCreate directory)LedgerFiles.requireAbsent(directory.target());
        stack.push(frame);boolean complete=false;
        try {
            validations++;T result=actualIO.run();originals();
            if(leaf instanceof FileCreate create){FileIdentity after=LedgerFiles.identity(create.target());if(after.bytes()>create.maxLogicalBytes())throw new IOException("actual create exceeds quote");observed.put(create.target(),after);}
            else if(leaf instanceof FileFillExistingEmpty fill){FileIdentity after=LedgerFiles.identity(fill.target());
                if(after.bytes()>fill.maxLogicalBytes()||!sameFile(original,after))throw new IOException("empty fill native identity/quote drift");observed.put(fill.target(),after);}
            else if(leaf instanceof FileRename rename){LedgerFiles.requireAbsent(rename.source());
                if(!original.equals(LedgerFiles.identity(rename.target())))throw new IOException("rename did not retain actual original FileID");
                observed.remove(rename.source());observed.put(rename.target(),original);}
            else if(leaf instanceof DirectoryCreate directory){var attrs=IdentityBearingFileAttributes.read(directory.target());
                if(!attrs.isDirectory()||attrs.isSymbolicLink())throw new IOException("actual directory create absent");}
            if(leaf==null&&!frame.available.isEmpty())throw new IOException("whole plan returned without guarded execution of every physical phase");
            if(leaf!=null)frame.available.clear();
            if(scan()>limit)throw new IOException("actual accounted allocation exceeds finite card");
            if(parent!=null)remaining(parent,plan,true);successfulBatches++;complete=true;return result;
        }finally{
            stack.pop();if(!complete)unknown=true;if(stack.isEmpty())frames.remove();
        }
    }
    private static void remaining(Frame parent,WritePlan child,boolean consume)throws IOException {
        List<Mutation> available=new ArrayList<>(parent.available);
        for(Mutation expected:child.mutations()){
            int index=-1;for(int i=0;i<available.size();i++)if(admitted(available.get(i),expected)){index=i;break;}
            if(index<0)throw new IOException("nested physical plan is not an unused subset of its retained parent");
            available.remove(index);
        }
        if(consume){parent.available.clear();parent.available.addAll(available);}
    }
    private static boolean admitted(Mutation maximum,Mutation child){
        if(maximum instanceof FileCreate a&&child instanceof FileCreate b)return a.target().equals(b.target())&&b.maxLogicalBytes()<=a.maxLogicalBytes();
        if(maximum instanceof FileFillExistingEmpty a&&child instanceof FileFillExistingEmpty b)return a.target().equals(b.target())&&b.maxLogicalBytes()<=a.maxLogicalBytes();
        return maximum.equals(child);
    }
    private static boolean sameFile(FileIdentity a,FileIdentity b){return a.volumeSerialDecimal().equals(b.volumeSerialDecimal())&&a.fileIdDecimal().equals(b.fileIdDecimal())&&a.creationFiletimeDecimal().equals(b.creationFiletimeDecimal());}
    private void originals()throws IOException {
        if(closed)throw new IOException("software allocation scope is closed");
        if(!Instant.now().isBefore(expiry)||!rootId.equals(IdentityBearingFileAttributes.read(root).fileKey())
                ||!lockId.equals(LedgerFiles.identity(lock)))throw new IOException("software storage card/root/lock expired or changed");
        LedgerFiles.verify(originalCard);
    }
    private void owned(Path path)throws IOException {
        if(!path.isAbsolute()||!path.normalize().equals(path)||path.equals(root)||!path.startsWith(root))
            throw new IOException("fixture physical target outside its exact managed root");
        for(Path cursor=path.getParent();cursor!=null&&cursor.startsWith(root);cursor=cursor.getParent()){
            if(!Files.exists(cursor,LinkOption.NOFOLLOW_LINKS))continue;
            var attrs=IdentityBearingFileAttributes.read(cursor);if(!attrs.isDirectory()||attrs.isSymbolicLink())throw new IOException("fixture target parent changed");
        }
    }
    private long charge(long bytes){return Math.max(4096,Math.multiplyExact(Math.floorDiv(Math.addExact(bytes,unit-1),unit),unit));}
    private long scan()throws IOException {
        long total=0;int entries=0;
        try(var paths=Files.walk(root)){
            var iterator=paths.iterator();while(iterator.hasNext()){
                Path path=iterator.next();if(++entries>100_000)throw new IOException("finite complete fixture census exhausted");
                var attrs=IdentityBearingFileAttributes.read(path);
                if(attrs.isSymbolicLink()||attrs.fileKey()==null)throw new IOException("ordinary native fixture entry required");
                if(attrs.isDirectory())total=Math.addExact(total,4096);
                else if(attrs.isRegularFile()){
                    FileIdentity before=LedgerFiles.identity(path);var nativeFile=SharedSourceFiles.nativeFile(path);
                    if(nativeFile.logicalBytes()!=before.bytes()||!nativeFile.fileIdDecimal().equals(before.fileIdDecimal())
                            ||!nativeFile.volumeSerialDecimal().equals(before.volumeSerialDecimal())
                            ||!nativeFile.creationFiletimeDecimal().equals(before.creationFiletimeDecimal())
                            ||!before.equals(LedgerFiles.identity(path))||nativeFile.linkCount()!=1)
                        throw new IOException("actual native allocation/FileID/link inventory changed");
                    total=Math.addExact(total,Math.max(nativeFile.allocatedBytes(),charge(nativeFile.logicalBytes())));
                }
                else throw new IOException("unsupported fixture entry");
            }
        }
        return total;
    }
    /** Actual read-only whole-root accounting reconciliation; never resolves an action/ledger UNKNOWN. */
    public synchronized void reconcileStorageOnly()throws IOException {
        if(!frames.get().isEmpty())throw new IOException("cannot reconcile inside an active physical plan");
        boolean held;
        try{WindowsLedgerLock.requireHeld(lock);held=true;}catch(IOException absent){held=false;}
        if(held)reconcileHeld();
        else {
            WindowsLedgerLock original=WindowsLedgerLock.acquire(lock);
            try(original){
                WindowsLedgerLock.requireHeld(lock);
                reconcileHeld();
            }
        }
    }
    private void reconcileHeld()throws IOException {
        WindowsLedgerLock.requireHeld(lock);originals();
        if(scan()>limit)throw new IOException("actual whole fixture remains over cap");
        originals();unknown=false;
    }
    @Override public synchronized void close()throws IOException {
        if(closed)return;
        if(!frames.get().isEmpty())throw new IOException("cannot close an active physical storage scope");
        closed=true;frames.remove();
        synchronized(StorageWriteGuardTestSupport.class){SCOPES.remove(lock,this);}
    }
    public synchronized boolean hasUnknownWrite(){return unknown;}
    public synchronized long validations(){return validations;}
    public synchronized long successfulBatches(){return successfulBatches;}
}
