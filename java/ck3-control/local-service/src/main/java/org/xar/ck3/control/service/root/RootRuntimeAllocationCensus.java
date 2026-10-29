package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.RootRuntimeStorageContract.*;

/** Bounded native-metadata producer for the newly declared runtime package, never an old J-tree census.
 * Per-path file allocation is summed conservatively: hard links never create physical-release credit. */
public final class RootRuntimeAllocationCensus {
    private RootRuntimeAllocationCensus() { }
    record FileEntry(String rootId,String relativePath,SharedSourceFiles.NativeFile nativeFile) { }
    record DirectoryEntry(String rootId,String relativePath,SharedSourceFiles.DirectoryIdentity identity,String modifiedAt) { }
    record Capture(List<RootAllocation> roots,List<FileEntry> files,List<DirectoryEntry> directories) {
        Capture {roots=List.copyOf(roots);files=List.copyOf(files);directories=List.copyOf(directories);}
    }

    /** Only actual observation can produce COMPLETE; any missing/unstable root becomes an explicit INCOMPLETE branch. */
    public static WholeCensus observe(FileRef declarationRef,ExistingUsage existingWorkpackage,Clock clock)throws IOException {
        var original=SharedSourceFiles.observe(Path.of(declarationRef.path()));
        var declaration=decode(RootRuntimeDefinitions.read(declarationRef,MAXIMUM_BYTES),Declaration.class);
        if(!declaration.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("runtime declaration belongs to another actual machine");
        current(declaration,clock);
        try {
            current(declaration,clock);
            Capture measured=capture(declaration,clock);
            SharedSourceFiles.assertUnchanged(original);
            return new CompleteCensus(CENSUS,"COMPLETE",declaration.machineId(),declaration.ownerTask(),declaration.windowId(),
                    clock.instant().toString(),declaration.reviewAtUtc(),declarationRef,"DECLARED_RUNTIME_ROOTS_ONLY",measured.roots(),existingWorkpackage);
        }catch(IOException unavailable){
            SharedSourceFiles.assertUnchanged(original);
            // An expired observation cannot manufacture a fresh INCOMPLETE record that outlives its declaration.
            current(declaration,clock);
            String reason=unavailable.getMessage()==null?unavailable.getClass().getSimpleName():unavailable.getMessage();
            if(reason.length()>8192)reason=reason.substring(0,8192);
            return new IncompleteCensus(CENSUS,"INCOMPLETE",declaration.machineId(),declaration.ownerTask(),declaration.windowId(),
                    clock.instant().toString(),declaration.reviewAtUtc(),declarationRef,List.of(reason),existingWorkpackage);
        }
    }

    static Capture capture(List<ManagedRoot> managedRoots,int maximumEntries,long maximumScanMillis,Clock clock)throws IOException {
        return capture(managedRoots,maximumEntries,maximumScanMillis,null,clock);
    }

    static Capture capture(Declaration declaration,Clock clock)throws IOException {
        current(declaration,clock);
        return capture(declaration.roots(),declaration.maximumEntries(),declaration.maximumScanMillis(),declaration,clock);
    }

    private static Capture capture(List<ManagedRoot> managedRoots,int maximumEntries,long maximumScanMillis,Declaration nullableLegacy,Clock clock)throws IOException {
        long started=System.nanoTime();
        var files=new ArrayList<FileEntry>();var directories=new ArrayList<DirectoryEntry>();
        for(ManagedRoot root:managedRoots) {
            Path path=Path.of(root.path());realDirectory(path);
            Files.walkFileTree(path,new SimpleFileVisitor<Path>() {
                private void bound()throws IOException {
                    if(files.size()+directories.size()>=maximumEntries
                            ||System.nanoTime()-started>maximumScanMillis*1_000_000L)
                        throw new IOException("runtime metadata census exceeded its explicit entry/time bound");
                    if(nullableLegacy!=null)current(nullableLegacy,clock);
                }
                @Override public FileVisitResult preVisitDirectory(Path directory,BasicFileAttributes attributes)throws IOException {
                    bound();realDirectory(directory);
                    directories.add(new DirectoryEntry(root.rootId(),path.relativize(directory).toString(),
                            SharedSourceFiles.nativeDirectory(directory),Files.getLastModifiedTime(directory,LinkOption.NOFOLLOW_LINKS).toString()));
                    return FileVisitResult.CONTINUE;
                }
                @Override public FileVisitResult visitFile(Path file,BasicFileAttributes attributes)throws IOException {
                    bound();SharedSourceFiles.plainAncestors(file);
                    if(!attributes.isRegularFile()||Files.isSymbolicLink(file))throw new IOException("runtime census refuses reparse/nonregular entries: "+file);
                    files.add(new FileEntry(root.rootId(),path.relativize(file).toString(),SharedSourceFiles.nativeFile(file)));
                    return FileVisitResult.CONTINUE;
                }
            });
        }
        // A complete result does not combine an old file observation with a later changed directory inventory.
        for(FileEntry entry:files){
            bounded(nullableLegacy,clock,started,maximumScanMillis);
            ManagedRoot root=root(managedRoots,entry.rootId());Path path=Path.of(root.path()).resolve(entry.relativePath());
            if(!SharedSourceFiles.nativeFile(path).equals(entry.nativeFile()))throw new IOException("runtime file changed during allocation census: "+path);
        }
        for(DirectoryEntry entry:directories){
            bounded(nullableLegacy,clock,started,maximumScanMillis);
            Path path=Path.of(root(managedRoots,entry.rootId()).path()).resolve(entry.relativePath());
            if(!SharedSourceFiles.nativeDirectory(path).equals(entry.identity())
                    ||!Files.getLastModifiedTime(path,LinkOption.NOFOLLOW_LINKS).toString().equals(entry.modifiedAt()))
                throw new IOException("runtime directory changed during allocation census: "+path);
        }
        var allocations=new ArrayList<RootAllocation>();
        for(ManagedRoot root:managedRoots){
            List<FileEntry> ownFiles=files.stream().filter(file->file.rootId().equals(root.rootId())).sorted(Comparator.comparing(FileEntry::relativePath)).toList();
            List<DirectoryEntry> ownDirs=directories.stream().filter(directory->directory.rootId().equals(root.rootId())).sorted(Comparator.comparing(DirectoryEntry::relativePath)).toList();
            long logical=0,allocated=0;for(FileEntry entry:ownFiles){logical=add(logical,entry.nativeFile().logicalBytes());allocated=add(allocated,entry.nativeFile().allocatedBytes());}
            long guard=multiply(ownDirs.size(),DIRECTORY_GUARD);MessageDigest digest=sha();
            for(DirectoryEntry entry:ownDirs)update(digest,entry);
            for(FileEntry entry:ownFiles)update(digest,entry);
            DirectoryEntry original=ownDirs.stream().filter(directory->directory.relativePath().isEmpty()).findFirst().orElseThrow();
            allocations.add(new RootAllocation(root.rootId(),original.identity(),ownFiles.size(),ownDirs.size(),logical,allocated,guard,
                    add(allocated,guard),HexFormat.of().formatHex(digest.digest())));
        }
        if(nullableLegacy!=null)current(nullableLegacy,clock);
        return new Capture(allocations,files,directories);
    }
    static ManagedRoot root(Declaration declaration,String id)throws IOException {
        return root(declaration.roots(),id);
    }
    private static ManagedRoot root(List<ManagedRoot> managedRoots,String id)throws IOException {
        return managedRoots.stream().filter(root->root.rootId().equals(id)).findFirst()
                .orElseThrow(()->new IOException("runtime allocation root ID is not declared: "+id));
    }
    static void realDirectory(Path path)throws IOException {
        SharedSourceFiles.plainAncestors(path);
        if(!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)||!path.toRealPath().equals(path))
            throw new IOException("actual canonical runtime directory required: "+path);
    }
    static void current(Declaration declaration,Clock clock)throws IOException {
        if(clock.instant().isBefore(instant(declaration.observedAtUtc()))||!clock.instant().isBefore(instant(declaration.reviewAtUtc())))
            throw new IOException("actual runtime declaration is future-dated or expired");
    }
    private static void bounded(Declaration nullableLegacy,Clock clock,long started,long maximumScanMillis)throws IOException {
        if(nullableLegacy!=null)current(nullableLegacy,clock);
        if(System.nanoTime()-started>maximumScanMillis*1_000_000L)
            throw new IOException("runtime metadata revalidation exceeded the common scan deadline");
    }
    private static MessageDigest sha(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}}
    /** Narrow metadata-only Jackson boundary; payload bytes are never read or hashed by allocation census. */
    private static void update(MessageDigest digest,Object metadata){
        digest.update(StrictJson.canonical(ControlBuild.strictMapper().valueToTree(metadata),8192));digest.update((byte)'\n');
    }
}
