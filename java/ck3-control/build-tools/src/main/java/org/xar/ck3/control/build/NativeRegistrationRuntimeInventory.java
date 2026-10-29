package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/**
 * Complete existing Python/base/venv/helper inventory, represented by bounded immutable chunks.
 * Quote is metadata only; DIGEST reads every original byte. Neither mode registers an EXE.
 * No global native source/evidence bound is increased and no installed file is copied or modified.
 */
public final class NativeRegistrationRuntimeInventory {
    public static final String REQUEST_SCHEMA="xar.native-register-runtime-inventory-request/v1";
    public static final String MACHINE_IDENTITY_SOURCE="tools/ck3_live_run_id.py";
    public static final String QUOTE_SCHEMA="xar.native-register-runtime-inventory-quote/v1";
    public static final String CHUNK_SCHEMA="xar.native-register-runtime-inventory-chunk/v1";
    public static final String MANIFEST_SCHEMA="xar.native-register-runtime-inventory/v1";
    public static final int CHUNK_FILES=512,CHUNK_JSON_LIMIT=1<<20,METADATA_JSON_LIMIT=32<<20;
    private NativeRegistrationRuntimeInventory(){ }
    public enum Mode { QUOTE,DIGEST }
    public record Roots(String repository,String pythonBase,String venv,String broker,FileRef python,FileRef helper,FileRef client){
        public Roots{
            for(String path:List.of(repository,pythonBase,venv,broker))absolute(path);
            Objects.requireNonNull(python);Objects.requireNonNull(helper);Objects.requireNonNull(client);
            Path repo=Path.of(repository),base=Path.of(pythonBase),virtual=Path.of(venv);
            require(!overlap(base,virtual)&&virtual.equals(repo.resolve("tools/.venv"))
                    &&Path.of(broker).equals(repo.resolve("tools/project_exe_broker"))
                    &&Path.of(python.path()).equals(virtual.resolve("Scripts/python.exe"))
                    &&Path.of(helper.path()).equals(repo.resolve("tools/register_project_exe_exclusions.py"))
                    &&Path.of(client.path()).equals(repo.resolve("tools/project_exe_exclusion_broker_client.py")),
                    "exact existing canonical Python/base/venv/helper/broker roots required");
        }
        public List<Path> directories(){return List.of(Path.of(pythonBase),Path.of(venv),Path.of(broker));}
    }
    /** DIGEST uses the exact quote extent, not an unexplained larger global inventory limit. */
    public record Bounds(int maximumFiles,int maximumDirectories,long maximumLogicalBytes,long maximumSerializedBytes,int maximumReadSeconds){
        public Bounds{require(maximumFiles>0&&maximumFiles<=200000&&maximumDirectories>=3&&maximumDirectories<=100000
                &&maximumLogicalBytes>0&&maximumLogicalBytes<=1L<<40&&maximumSerializedBytes>0&&maximumSerializedBytes<=64L<<20
                &&maximumReadSeconds>=1&&maximumReadSeconds<=1800,"explicit finite inventory count/bytes/JSON/read-time bounds required");}
    }
    public record Request(String schema,String machineId,Mode mode,Roots roots,Bounds bounds,String outputRoot,
            FileRef quoteRef,FileRef qualifiedToolsBuild,FileRef capacityRef){
        public Request{require(REQUEST_SCHEMA.equals(schema),"exact inventory producer version required");machine(machineId);
            Objects.requireNonNull(mode);Objects.requireNonNull(roots);Objects.requireNonNull(bounds);absolute(outputRoot);
            require((mode==Mode.DIGEST)==(quoteRef!=null),"DIGEST requires exact real quote; QUOTE requires explicit null");
            Objects.requireNonNull(qualifiedToolsBuild);Objects.requireNonNull(capacityRef);
            for(Path source:roots.directories())require(!overlap(source,Path.of(outputRoot)),"runtime source and output must be disjoint");
            require(!Path.of(outputRoot).getRoot().equals(Path.of(outputRoot)),"whole-volume output forbidden");}
    }
    public record Directory(String path,SharedSourceFiles.DirectoryIdentity identity){
        public Directory{absolute(path);Objects.requireNonNull(identity);}
    }
    public record Metadata(String path,SharedSourceFiles.NativeFile nativeFile){
        public Metadata{absolute(path);Objects.requireNonNull(nativeFile);}
    }
    public record Quote(String schema,String machineId,String observedAtUtc,Roots roots,List<Directory> directories,
            List<Metadata> files,long logicalBytes,long nativeAllocatedBytes){
        public Quote{
            require(QUOTE_SCHEMA.equals(schema),"exact complete inventory quote required");machine(machineId);Instant.parse(observedAtUtc);
            Objects.requireNonNull(roots);directories=List.copyOf(directories);files=List.copyOf(files);
            require(!files.isEmpty()&&files.size()<=200000&&directories.size()>=3&&directories.size()<=100000
                    &&files.stream().map(Metadata::path).distinct().count()==files.size()
                    &&directories.stream().map(Directory::path).distinct().count()==directories.size(),"complete finite distinct source inventory required");
            long logical=0,allocated=0;for(var file:files){logical=Math.addExact(logical,file.nativeFile().logicalBytes());allocated=Math.addExact(allocated,file.nativeFile().allocatedBytes());}
            require(logical==logicalBytes&&allocated==nativeAllocatedBytes,"quote totals differ from actual native metadata");}
    }
    public record Chunk(String schema,String machineId,int index,List<SharedSourceFiles.Witness> files){
        public Chunk{require(CHUNK_SCHEMA.equals(schema)&&index>=0,"exact numbered runtime chunk required");machine(machineId);files=List.copyOf(files);
            require(!files.isEmpty()&&files.size()<=CHUNK_FILES&&files.stream().map(row->row.source().path()).distinct().count()==files.size(),
                    "finite unique complete original file witnesses required");}
    }
    public record Manifest(String schema,String machineId,String startedAtUtc,String observedAtUtc,FileRef requestRef,
            FileRef quoteRef,FileRef capacityRef,FileRef qualifiedToolsBuild,Bounds bounds,Roots roots,List<Directory> directories,
            int fileCount,long logicalBytes,long nativeAllocatedBytes,List<FileRef> chunks,long serializedChunkBytes){
        public Manifest{require(MANIFEST_SCHEMA.equals(schema),"exact complete runtime inventory version required");machine(machineId);
            require(!Instant.parse(observedAtUtc).isBefore(Instant.parse(startedAtUtc)),"actual source observation chronology required");
            for(FileRef ref:List.of(requestRef,quoteRef,capacityRef,qualifiedToolsBuild))Objects.requireNonNull(ref);
            Objects.requireNonNull(bounds);Objects.requireNonNull(roots);directories=List.copyOf(directories);chunks=List.copyOf(chunks);
            require(fileCount==bounds.maximumFiles()&&directories.size()==bounds.maximumDirectories()&&logicalBytes==bounds.maximumLogicalBytes()
                    &&chunks.size()>=(fileCount+CHUNK_FILES-1)/CHUNK_FILES&&chunks.size()<=fileCount
                    &&chunks.stream().map(FileRef::path).distinct().count()==chunks.size(),
                    "DIGEST must preserve the whole exact admitted quote extent");
            long serialized=0;for(FileRef ref:chunks){require(ref.bytes()>0&&ref.bytes()<=CHUNK_JSON_LIMIT,"finite raw noncompressed runtime chunk required");serialized=Math.addExact(serialized,ref.bytes());}
            require(serialized==serializedChunkBytes&&serialized<=bounds.maximumSerializedBytes(),"complete raw chunk byte denominator required");}
    }
    public static final class Verified {
        private final Manifest manifest;private final List<FileRef> references;
        private Verified(Manifest manifest,List<FileRef> references){this.manifest=manifest;this.references=List.copyOf(references);}
        public Manifest manifest(){return manifest;}public List<FileRef> references(){return references;}
    }
    /** Root uses an admitted metadata-only pass once; this is more than repeating the known base count. */
    public static Quote quote(Roots roots,Bounds bounds)throws IOException{
        long start=System.nanoTime();var directories=new ArrayList<Directory>();var files=new ArrayList<Metadata>();
        var names=new HashSet<String>();long logical=0,allocated=0;
        for(Path root:roots.directories()){
            SharedSourceFiles.plainAncestors(root);if(!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("complete runtime root absent");
            try(var walk=Files.walk(root)){var iterator=walk.iterator();while(iterator.hasNext()){
                tick(start,bounds);Path path=iterator.next();SharedSourceFiles.plainAncestors(path);
                if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)){directories.add(new Directory(path.toString(),SharedSourceFiles.nativeDirectory(path)));
                    if(directories.size()>bounds.maximumDirectories())throw new IOException("runtime directory quote exceeds explicit admission");}
                else{
                    if(!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("nonordinary complete runtime source rejected");
                    if(!names.add(key(path.toString())))throw new IOException("runtime path alias/duplicate");
                    var actual=SharedSourceFiles.nativeFile(path);files.add(new Metadata(path.toString(),actual));
                    logical=Math.addExact(logical,actual.logicalBytes());allocated=Math.addExact(allocated,actual.allocatedBytes());
                    if(files.size()>bounds.maximumFiles()||logical>bounds.maximumLogicalBytes())throw new IOException("runtime quote exceeds explicit file/byte admission");
                }
            }}
        }
        for(FileRef source:List.of(roots.helper(),roots.client(),
                FileRef.measure(Path.of(roots.repository()).resolve(MACHINE_IDENTITY_SOURCE)))){
            tick(start,bounds);source.verify();SharedSourceFiles.plainAncestors(Path.of(source.path()));
            if(!names.add(key(source.path())))throw new IOException("helper source repeated in runtime roots");
            var actual=SharedSourceFiles.nativeFile(Path.of(source.path()));
            if(actual.logicalBytes()!=source.bytes())throw new IOException("actual helper metadata differs");
            files.add(new Metadata(source.path(),actual));logical=Math.addExact(logical,actual.logicalBytes());allocated=Math.addExact(allocated,actual.allocatedBytes());
        }
        if(files.size()>bounds.maximumFiles()||logical>bounds.maximumLogicalBytes())throw new IOException("complete helper quote exceeds explicit bounds");
        directories.sort(Comparator.comparing(Directory::path));files.sort(Comparator.comparing(Metadata::path));
        roots.python().verify();tick(start,bounds);
        return new Quote(QUOTE_SCHEMA,WindowsJobProcess.currentMachineId(),Instant.now().toString(),roots,directories,files,logical,allocated);
    }
    /** Produces only source metadata, guarded by the existing actual Root capacity/census implementation. */
    public static FileRef execute(FileRef requestRef)throws IOException{
        Request request=ControlBuild.strictMapper().readValue(read(requestRef,65536),Request.class);
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("inventory request machine differs");
        var tools=ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        if(tools.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!tools.completeDeployment().equals(ControlBuild.producerClosure()))
            throw new IOException("complete actually loaded qualified inventory producer required");
        requireProducerSource(tools);
        try(var guard=new Publication(request,requestRef)){
            Quote observed=quote(request.roots(),request.bounds());Path output=Path.of(request.outputRoot());
            if(request.mode()==Mode.QUOTE){
                byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(observed);
                if(bytes.length>METADATA_JSON_LIMIT||bytes.length>request.bounds().maximumSerializedBytes())throw new IOException("complete raw quote exceeds admission");
                return guard.write(output.resolve("runtime-quote.json"),bytes);
            }
            Quote admitted=ControlBuild.strictMapper().readValue(read(request.quoteRef(),METADATA_JSON_LIMIT),Quote.class);
            sameQuote(admitted,observed);
            if(request.bounds().maximumFiles()!=admitted.files().size()||request.bounds().maximumDirectories()!=admitted.directories().size()
                    ||request.bounds().maximumLogicalBytes()!=admitted.logicalBytes())
                throw new IOException("DIGEST ceilings must equal actual quote, no blind growth allowance");
            String started=Instant.now().toString();long start=System.nanoTime(),serialized=0;
            var chunks=new ArrayList<FileRef>();var held=new ArrayList<SharedSourceFiles.Witness>();int index=0;long estimated=0;
            for(Metadata entry:admitted.files()){
                tick(start,request.bounds());var original=SharedSourceFiles.observe(Path.of(entry.path()));
                if(!original.nativeFile().equals(entry.nativeFile()))throw new IOException("runtime native metadata changed since exact quote");
                int entryBytes=ControlBuild.strictMapper().writeValueAsBytes(original).length;
                if(!held.isEmpty()&&(held.size()==CHUNK_FILES||estimated+entryBytes+1>CHUNK_JSON_LIMIT)){
                    byte[] bytes=chunkBytes(request.machineId(),index++,held);serialized=Math.addExact(serialized,bytes.length);
                    if(serialized>request.bounds().maximumSerializedBytes())throw new IOException("complete runtime chunks exceed admitted raw bytes");
                    chunks.add(guard.write(output.resolve(String.format(java.util.Locale.ROOT,"runtime-%06d.json",index-1)),bytes));held.clear();estimated=0;
                }
                if(held.isEmpty())estimated=chunkBytes(request.machineId(),index,List.of(original)).length-entryBytes;
                estimated+=entryBytes+(held.isEmpty()?0:1);
                if(estimated>CHUNK_JSON_LIMIT)throw new IOException("single complete runtime witness exceeds explicit raw chunk bound");
                held.add(original);
            }
            if(!held.isEmpty()){byte[] bytes=chunkBytes(request.machineId(),index,held);serialized=Math.addExact(serialized,bytes.length);
                chunks.add(guard.write(output.resolve(String.format(java.util.Locale.ROOT,"runtime-%06d.json",index)),bytes));}
            if(serialized>request.bounds().maximumSerializedBytes())throw new IOException("runtime raw chunks exceed admitted bytes");
            sameQuote(admitted,quote(request.roots(),request.bounds()));
            var manifest=new Manifest(MANIFEST_SCHEMA,request.machineId(),started,Instant.now().toString(),requestRef,request.quoteRef(),
                    request.capacityRef(),request.qualifiedToolsBuild(),request.bounds(),request.roots(),admitted.directories(),admitted.files().size(),
                    admitted.logicalBytes(),admitted.nativeAllocatedBytes(),chunks,serialized);
            byte[] wire=ControlBuild.strictMapper().writeValueAsBytes(manifest);
            if(wire.length>METADATA_JSON_LIMIT||Math.addExact(serialized,wire.length)>request.bounds().maximumSerializedBytes())
                throw new IOException("complete manifest plus raw chunks exceeds exact serialized bound");
            FileRef result=guard.write(output.resolve("runtime-inventory.json"),wire);verify(result);return result;
        }
    }
    /** Reopens every original byte/native identity and compares the complete fresh file/directory set. */
    public static Verified verify(FileRef manifestRef)throws IOException{
        Manifest manifest=ControlBuild.strictMapper().readValue(read(manifestRef,METADATA_JSON_LIMIT),Manifest.class);
        if(!manifest.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("runtime inventory source machine differs");
        Request request=ControlBuild.strictMapper().readValue(read(manifest.requestRef(),65536),Request.class);
        if(request.mode()!=Mode.DIGEST||!request.roots().equals(manifest.roots())||!request.bounds().equals(manifest.bounds())
                ||!request.capacityRef().equals(manifest.capacityRef())||!request.quoteRef().equals(manifest.quoteRef())
                ||!request.qualifiedToolsBuild().equals(manifest.qualifiedToolsBuild())
                ||!Path.of(request.outputRoot()).resolve("runtime-inventory.json").equals(Path.of(manifestRef.path())))
            throw new IOException("runtime source request and actual manifest differ");
        var release=capacity(manifest.capacityRef());
        Instant started=Instant.parse(manifest.startedAtUtc()),observed=Instant.parse(manifest.observedAtUtc());
        if(started.isBefore(Instant.parse(release.observedAtUtc()))||!observed.isBefore(Instant.parse(release.reviewAtUtc())))
            throw new IOException("runtime inventory was not produced inside original capacity window");
        Quote admitted=ControlBuild.strictMapper().readValue(read(manifest.quoteRef(),METADATA_JSON_LIMIT),Quote.class);
        if(!admitted.roots().equals(manifest.roots())||admitted.files().size()!=manifest.fileCount()
                ||!admitted.directories().equals(manifest.directories())||admitted.logicalBytes()!=manifest.logicalBytes()
                ||admitted.nativeAllocatedBytes()!=manifest.nativeAllocatedBytes())throw new IOException("full source denominator differs");
        var actualMetadata=new ArrayList<Metadata>();var seen=new HashSet<String>();int index=0;long raw=0,start=System.nanoTime();
        for(FileRef pin:manifest.chunks()){
            tick(start,manifest.bounds());if(!Path.of(pin.path()).getParent().equals(Path.of(manifestRef.path()).getParent())
                    ||!Path.of(pin.path()).getFileName().toString().equals(String.format(java.util.Locale.ROOT,"runtime-%06d.json",index)))
                throw new IOException("runtime chunk escaped exact ordered output package");
            byte[] bytes=read(pin,CHUNK_JSON_LIMIT);raw=Math.addExact(raw,bytes.length);
            Chunk chunk=ControlBuild.strictMapper().readValue(bytes,Chunk.class);
            if(chunk.index()!=index++||!chunk.machineId().equals(manifest.machineId()))throw new IOException("runtime chunk order/machine drift");
            for(var source:chunk.files()){
                tick(start,manifest.bounds());if(!seen.add(key(source.source().path())))throw new IOException("duplicate cross-chunk source");
                SharedSourceFiles.assertUnchanged(source);actualMetadata.add(new Metadata(source.source().path(),source.nativeFile()));
            }
        }
        if(raw!=manifest.serializedChunkBytes()||actualMetadata.size()!=manifest.fileCount())throw new IOException("runtime chunks are incomplete");
        actualMetadata.sort(Comparator.comparing(Metadata::path));
        if(!actualMetadata.equals(admitted.files()))throw new IOException("runtime chunk/native quote attribution differs");
        sameQuote(admitted,quote(manifest.roots(),manifest.bounds()));tick(start,manifest.bounds());
        var tools=ControlBuild.verifiedCompletedReceipt(manifest.qualifiedToolsBuild());
        if(tools.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!tools.machineId().equals(manifest.machineId()))
            throw new IOException("runtime inventory original Java producer is not qualified");
        requireProducerSource(tools);
        var refs=new ArrayList<FileRef>(List.of(manifestRef,manifest.requestRef(),manifest.quoteRef(),manifest.capacityRef(),release.policyRef(),manifest.qualifiedToolsBuild()));
        refs.addAll(manifest.chunks());refs.addAll(tools.completeDeployment());for(var ref:refs)ref.verify();
        return new Verified(manifest,List.copyOf(refs));
    }
    /** Closed immutable references only. This method deliberately grants no runtime content qualification.
     * Actual REGISTER/checkedEvidence readers must invoke verify, which reads every original byte. */
    public static List<FileRef> evidenceReferences(FileRef manifestRef)throws IOException{
        Manifest manifest=ControlBuild.strictMapper().readValue(read(manifestRef,METADATA_JSON_LIMIT),Manifest.class);
        Request request=ControlBuild.strictMapper().readValue(read(manifest.requestRef(),65536),Request.class);
        if(!Path.of(request.outputRoot()).resolve("runtime-inventory.json").equals(Path.of(manifestRef.path()))
                ||!request.roots().equals(manifest.roots())||!request.bounds().equals(manifest.bounds()))
            throw new IOException("runtime evidence package attribution differs");
        var release=capacity(manifest.capacityRef());var tools=ControlBuild.verifiedCompletedReceipt(manifest.qualifiedToolsBuild());
        var refs=new ArrayList<FileRef>(List.of(manifestRef,manifest.requestRef(),manifest.quoteRef(),manifest.capacityRef(),
                manifest.qualifiedToolsBuild(),release.policyRef()));refs.addAll(manifest.chunks());refs.addAll(tools.completeDeployment());
        int index=0;for(FileRef chunk:manifest.chunks()){
            if(!Path.of(chunk.path()).getParent().equals(Path.of(manifestRef.path()).getParent())
                    ||!Path.of(chunk.path()).getFileName().toString().equals(String.format(java.util.Locale.ROOT,"runtime-%06d.json",index++)))
                throw new IOException("ordered complete runtime evidence chunk escaped package");
        }
        for(FileRef ref:refs)ref.verify();return List.copyOf(refs);
    }
    private static void requireProducerSource(ControlBuild.BuildReceipt receipt)throws IOException{
        if(receipt.compiledSourcePins().stream().filter(ref->Path.of(ref.path()).getFileName().toString()
                .equals("NativeRegistrationRuntimeInventory.java")).count()!=1)
            throw new IOException("qualified build did not compile the single runtime inventory producer");
    }
    private static byte[] chunkBytes(String machine,int index,List<SharedSourceFiles.Witness> files)throws IOException{
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(new Chunk(CHUNK_SCHEMA,machine,index,files));
        if(bytes.length>CHUNK_JSON_LIMIT)throw new IOException("complete uncompressed runtime chunk exceeds 1MiB; no truncation");
        return bytes;
    }
    private static void sameQuote(Quote first,Quote second)throws IOException{
        if(!first.machineId().equals(second.machineId())||!first.roots().equals(second.roots())
                ||!first.directories().equals(second.directories())||!first.files().equals(second.files())
                ||first.logicalBytes()!=second.logicalBytes()||first.nativeAllocatedBytes()!=second.nativeAllocatedBytes())
            throw new IOException("complete ordinary runtime inventory changed");
    }
    private static ControlBuild.CapacityRelease capacity(FileRef ref)throws IOException{
        var release=ControlBuild.strictMapper().readValue(read(ref,131072),ControlBuild.CapacityRelease.class);
        if(!"RELEASED".equals(release.status())||!"/root".equals(release.ownerTask())
                ||!release.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("actual sole Root runtime inventory capacity required");
        release.policyRef().verify();var policy=CiBootstrap.readPolicy(read(release.policyRef(),131072));
        for(var row:release.volumes().entrySet()){
            var value=row.getValue();var override=release.quotaOverrides().get(row.getKey());
            if(override!=null){
                if(!override.task().equals(release.ownerTask())||Instant.parse(override.reviewAtUtc()).isAfter(Instant.parse(release.reviewAtUtc())))
                    throw new IOException("runtime inventory override owner/window differs");
                new FileRef(override.sourceRef().path(),override.sourceRef().bytes(),override.sourceRef().sha256()).verify();
            }
            if(!value.equals(CiBootstrap.calculate(policy,value.totalVolumeBytes(),value.availableBytes(),value.thisWritePeak(),
                    value.otherUnspentReservations(),value.systemGrowthReserve(),value.currentProjectUsageConservativeUpper(),
                    override,Instant.parse(release.observedAtUtc()),Instant.parse(release.reviewAtUtc()))))
                throw new IOException("runtime inventory capacity is not the shared storage calculation");
        }
        return release;
    }
    private static final class Publication implements AutoCloseable{
        private final Request request;private final FileRef requestRef;private final ControlBuild.CapacityRelease release;
        private final List<Path> scopes;private final Instant deadline;private final java.nio.channels.FileChannel channel;
        private final java.nio.channels.FileLock lock;
        Publication(Request request,FileRef requestRef)throws IOException{
            this.request=request;this.requestRef=requestRef;release=capacity(request.capacityRef());deadline=Instant.parse(release.reviewAtUtc());
            scopes=release.approvedOutputRoots().stream().map(Path::of).filter(path->release.approvedOutputRoots().stream().map(Path::of)
                    .noneMatch(other->!other.equals(path)&&path.startsWith(other))).toList();
            Path output=Path.of(request.outputRoot());
            for(Path scope:scopes)if(!scope.isAbsolute()||!scope.normalize().equals(scope)||scope.equals(scope.getRoot()))
                throw new IOException("exact finite inventory output roots required");
            if(scopes.stream().noneMatch(Path.of(release.temporaryRoot())::startsWith))
                throw new IOException("inventory entire temporary root lacks output admission");
            if(scopes.stream().noneMatch(output::startsWith)||Files.exists(output,LinkOption.NOFOLLOW_LINKS))
                throw new IOException("absent runtime inventory child output in exact admitted scope required");
            for(Path scope:scopes)for(Path source:request.roots().directories())if(overlap(scope,source))
                throw new IOException("inventory output scope overlaps existing runtime input");
            for(String option:List.of("java.io.tmpdir","jna.tmpdir")){
                String raw=System.getProperty(option);if(raw==null||!Path.of(raw).startsWith(Path.of(release.temporaryRoot())))
                    throw new IOException("runtime inventory JVM temporary path escaped original capacity");
            }
            if(request.bounds().maximumSerializedBytes()>release.parts().getOrDefault("artifacts",0L)-(16L<<20))
                throw new IOException("complete raw inventory and 16MiB original terminal reserve exceed capacity");
            guard(0);SharedSourceFiles.plainAncestors(output.getParent());Files.createDirectory(output);
            channel=java.nio.channels.FileChannel.open(output.resolve("INVENTORY.lock"),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            java.nio.channels.FileLock held;
            try{held=channel.tryLock();}catch(IOException|RuntimeException failure){channel.close();throw failure;}
            if(held==null){channel.close();throw new IOException("inventory already has another actual owner");}
            lock=held;
            try{guard(0);}catch(IOException|RuntimeException failure){lock.release();channel.close();throw failure;}
        }
        FileRef write(Path path,byte[] bytes)throws IOException{
            if(!path.getParent().equals(Path.of(request.outputRoot())))throw new IOException("inventory output escaped exact fresh child");
            long cluster=NativeStorageGeometry.read(path.getParent()).clusterBytes();
            long pending=Math.multiplyExact(Math.floorDiv(Math.addExact(bytes.length,cluster-1),cluster),cluster);
            guard(pending);Files.write(path,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            FileRef actual=FileRef.measure(path);if(actual.bytes()!=bytes.length||!actual.sha256().equals(sha(bytes)))throw new IOException("inventory write/readback drift");
            guard(0);return actual;
        }
        private void guard(long pending)throws IOException{
            requestRef.verify();request.capacityRef().verify();release.policyRef().verify();
            if(!Instant.now().isBefore(deadline))throw new IOException("runtime inventory admission expired");
            for(var entry:release.volumes().entrySet())if(Files.getFileStore(Path.of(entry.getKey())).getUsableSpace()<entry.getValue().requiredFree())
                throw new IOException("runtime inventory shared free-space reserve unavailable");
            long allocated=NativeBridgeRootGate.allocation(scopes,deadline);
            if(Math.addExact(Math.addExact(allocated,pending),16L<<20)>release.parts().getOrDefault("artifacts",0L))
                throw new IOException("runtime inventory allocation/pending/terminal reserve exceed original aggregate");
        }
        @Override public void close()throws IOException{IOException failure=null;try{guard(0);}catch(IOException error){failure=error;}
            try{lock.release();}catch(IOException error){if(failure==null)failure=error;else failure.addSuppressed(error);}
            try{channel.close();}catch(IOException error){if(failure==null)failure=error;else failure.addSuppressed(error);}
            if(failure!=null)throw failure;}
    }
    private static byte[] read(FileRef ref,int maximum)throws IOException{
        if(ref==null||ref.bytes()<1||ref.bytes()>maximum)throw new IOException("bounded exact inventory original required");
        var held=SharedSourceFiles.observe(Path.of(ref.path()));if(!held.source().equals(ref))throw new IOException("inventory original differs");
        byte[] bytes;try(var input=Files.newInputStream(Path.of(ref.path()))){bytes=input.readNBytes(maximum+1);}
        if(bytes.length!=ref.bytes()||!sha(bytes).equals(ref.sha256()))throw new IOException("inventory original changed during read");
        SharedSourceFiles.assertUnchanged(held);return bytes;
    }
    private static void tick(long start,Bounds bounds)throws IOException{if(System.nanoTime()-start>(long)bounds.maximumReadSeconds()*1000000000L)
        throw new IOException("complete runtime inventory exceeded finite read time");}
    private static String key(String path){return Path.of(path).toAbsolutePath().normalize().toString().toLowerCase(java.util.Locale.ROOT);}
    private static boolean overlap(Path first,Path second){return first.startsWith(second)||second.startsWith(first);}
    private static void absolute(String text){require(text!=null&&Path.of(text).isAbsolute()&&Path.of(text).normalize().equals(Path.of(text)),"canonical absolute inventory path required");}
    private static void machine(String text){require(text!=null&&text.matches("[a-z0-9][a-z0-9-]{0,127}")&&!text.equals("unknown"),"known inventory machine required");}
    private static String sha(byte[] bytes){try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    public static void main(String[] args)throws IOException{
        if(args.length!=3||!args[1].matches("[1-9][0-9]{0,7}")||!args[2].matches("[0-9a-f]{64}"))throw new IOException("exact inventory request path/bytes/SHA required");
        FileRef actual=execute(new FileRef(args[0],Long.parseLong(args[1]),args[2]));
        System.out.println(ControlBuild.strictMapper().writeValueAsString(actual));
    }
}
