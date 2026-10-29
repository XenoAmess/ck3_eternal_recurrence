package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.RawWindowCaptureContract.*;

/** Complete finite class census; native identity remains solely SharedSourceFiles. */
public final class RawWindowClassClosureMain {
    public static final String SCHEMA="xar.native-raw-class-closure/v2";
    private static final String PACKAGE="org/xar/ck3/control/build";
    private static final int MANIFEST_CAP=131072;
    private static final List<String> PREPARE=List.of("RawWindowPreparation","RawWindowPrepareMain","RawWindowPrepareRegressionMain","RawWindowClassClosureMain");
    private static final List<String> RAW_MAIN=List.of("RawWindowCaptureContract","RawWindowCaptureJson","RawWindowCollector",
        "RawWindowCollectorMain","RawWindowImageProof","RawWindowNativeIo","RawWindowLocatorContract","ExactRipRelativeLocator",
        "RawWindowPreparation","RawWindowPrepareMain","RawWindowPrepareRegressionMain","RawWindowClassClosureMain");
    private static final List<String> RAW_TEST=List.of("RawWindowCollectorTest","RawWindowLocatorTest","RawWindowImageProofTest","RawWindowSoftwareRegressionMain");
    public enum Mode { PREPARE, RAW_LIMITED }
    private RawWindowClassClosureMain() { }
    public record ClassFile(String relativePath,FileRef fileRef,SharedSourceFiles.NativeFile nativeFile) {
        public ClassFile {
            Objects.requireNonNull(fileRef);Objects.requireNonNull(nativeFile);
            require(fileRef.bytes()>0&&fileRef.bytes()<=524288&&fileRef.bytes()==nativeFile.logicalBytes(),"bounded actual class/native size required");
        }
    }
    public record Closure(String schema,Mode mode,String machineId,String observedAtUtc,String classesRoot,
                          SharedSourceFiles.DirectoryIdentity rootIdentity,List<ClassFile> classes,long totalBytes,long chargedClassBytes) {
        public Closure {
            require(SCHEMA.equals(schema),"exact class closure schema required");Objects.requireNonNull(mode);machine(machineId);Instant.parse(observedAtUtc);
            Path root=absolute(classesRoot);Objects.requireNonNull(rootIdentity);classes=List.copyOf(classes);
            require(!classes.isEmpty()&&classes.size()<=(mode==Mode.PREPARE?32:256),"complete finite class closure required");
            var seen=new HashSet<String>();long sum=0,charged=0;
            for(ClassFile entry:classes) {
                needName(mode,entry.relativePath());require(seen.add(entry.relativePath()),"duplicate compiled class path");
                require(root.resolve(entry.relativePath()).equals(Path.of(entry.fileRef().path())),"class FileRef differs from owned root/relative path");
                sum=Math.addExact(sum,entry.fileRef().bytes());charged=Math.addExact(charged,Math.max(round(entry.fileRef().bytes()),entry.nativeFile().allocatedBytes()));
            }
            require(sum==totalBytes&&sum<=(mode==Mode.PREPARE?262144:524288),"whole class byte count differs or exceeds cap");
            require(charged==chargedClassBytes&&charged<=(mode==Mode.PREPARE?393216:786432),"complete charged class extent exceeds root forecast");
        }
    }
    private static long round(long bytes){return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes,4095),4096),4096);}
    private static List<String> prefixes(Mode mode,String relative) {
        if(mode==Mode.PREPARE)return PREPARE;
        if(relative.startsWith("main/"))return RAW_MAIN;
        if(relative.startsWith("test/"))return RAW_TEST;
        throw new IllegalArgumentException("RAW_LIMITED requires distinct main/test class roots");
    }
    private static void needName(Mode mode,String relative) {
        require(relative!=null&&relative.indexOf('\\')<0,"normalized class path required");
        List<String> allowed=prefixes(mode,relative);String local=mode==Mode.PREPARE?relative:relative.substring(5);
        require(local.startsWith(PACKAGE+"/"),"exact compiled package path required");String file=local.substring(PACKAGE.length()+1);
        require(file.endsWith(".class")&&file.indexOf('/')<0,"class file only");String base=file.substring(0,file.length()-6);
        boolean found=false;for(String prefix:allowed)if(base.equals(prefix)||base.startsWith(prefix+"$")&&base.matches("[A-Za-z0-9_$]+"))found=true;
        require(found,"foreign compiled class outside exact source roster");
    }
    private static List<Path> inventory(Mode mode,Path root)throws IOException {
        SharedSourceFiles.plainAncestors(root);if(!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("ordinary compiled root required");
        List<Path> all;try(var walk=Files.walk(root)){all=walk.limit(301).toList();}
        if(all.size()>300)throw new IOException("bounded complete class tree exceeded");
        List<Path> packages=mode==Mode.PREPARE?List.of(root.resolve(PACKAGE)):List.of(root.resolve("main/"+PACKAGE),root.resolve("test/"+PACKAGE));
        var files=new ArrayList<Path>();
        for(Path entry:all) {
            SharedSourceFiles.plainAncestors(entry);
            if(Files.isDirectory(entry,LinkOption.NOFOLLOW_LINKS)) {
                boolean ancestor=false;for(Path packagePath:packages)if(packagePath.startsWith(entry))ancestor=true;
                if(!ancestor)throw new IOException("foreign compiled directory");
            }else if(Files.isRegularFile(entry,LinkOption.NOFOLLOW_LINKS)&&!Files.isSymbolicLink(entry)){
                needName(mode,root.relativize(entry).toString().replace('\\','/'));files.add(entry);
            }else throw new IOException("ordinary compiled classes only");
        }
        files.sort(Path::compareTo);if(files.isEmpty()||files.size()>(mode==Mode.PREPARE?32:256))throw new IOException("complete class count outside finite cap");
        List<String> main=mode==Mode.PREPARE?PREPARE:RAW_MAIN;
        for(String prefix:main)if(!files.contains(packages.get(0).resolve(prefix+".class")))throw new IOException("declared main source primary class missing");
        if(mode==Mode.RAW_LIMITED)for(String prefix:RAW_TEST)if(!files.contains(packages.get(1).resolve(prefix+".class")))throw new IOException("declared test source primary class missing");
        return List.copyOf(files);
    }
    public static FileRef capture(Path classesRoot,Path newManifest)throws IOException {return capture(Mode.PREPARE,classesRoot,newManifest);}
    public static FileRef capture(Mode mode,Path classesRoot,Path newManifest)throws IOException {
        Objects.requireNonNull(mode);Path root=absolute(classesRoot.toString());absolute(newManifest.toString());
        if(newManifest.startsWith(root)||newManifest.getParent()==null||Files.exists(newManifest,LinkOption.NOFOLLOW_LINKS))throw new IOException("new manifest must be outside class tree");
        SharedSourceFiles.plainAncestors(newManifest.getParent());var directory=SharedSourceFiles.nativeDirectory(root);
        List<Path> paths=inventory(mode,root);var entries=new ArrayList<ClassFile>();long total=0,charged=0;
        for(Path path:paths) {
            var before=SharedSourceFiles.nativeFile(path);var content=RawWindowCaptureJson.readOriginal(path,524288);var after=SharedSourceFiles.nativeFile(path);
            if(!before.equals(after)||content.reference().bytes()!=before.logicalBytes())throw new IOException("class changed during native/content observation");
            total=Math.addExact(total,content.reference().bytes());charged=Math.addExact(charged,Math.max(round(content.reference().bytes()),after.allocatedBytes()));
            if(total>(mode==Mode.PREPARE?262144:524288)||charged>(mode==Mode.PREPARE?393216:786432))throw new IOException("whole class extent exceeded");
            entries.add(new ClassFile(root.relativize(path).toString().replace('\\','/'),content.reference(),after));
        }
        if(!directory.equals(SharedSourceFiles.nativeDirectory(root))||!paths.equals(inventory(mode,root)))throw new IOException("class root/inventory changed");
        var closure=new Closure(SCHEMA,mode,WindowsJobProcess.currentMachineId(),Instant.now().toString(),root.toString(),directory,entries,total,charged);
        byte[] encoded=ControlBuild.strictMapper().writeValueAsBytes(closure);if(encoded.length>MANIFEST_CAP)throw new IOException("complete typed class manifest exceeded cap");
        try(var channel=FileChannel.open(newManifest,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){ByteBuffer buffer=ByteBuffer.wrap(encoded);while(buffer.hasRemaining())channel.write(buffer);channel.force(true);}
        var original=RawWindowCaptureJson.readOriginal(newManifest,MANIFEST_CAP);
        if(!closure.equals(read(original.reference())))throw new IOException("actual complete class readback differs");return original.reference();
    }
    public static Closure read(FileRef manifest)throws IOException {
        Closure value=ControlBuild.strictMapper().readValue(RawWindowCaptureJson.exactBytes(manifest,MANIFEST_CAP),Closure.class);
        Path root=Path.of(value.classesRoot());
        if(!value.machineId().equals(WindowsJobProcess.currentMachineId())||!value.rootIdentity().equals(SharedSourceFiles.nativeDirectory(root)))throw new IOException("class manifest machine/root changed");
        List<Path> paths=inventory(value.mode(),root);if(paths.size()!=value.classes().size())throw new IOException("complete class inventory count changed");
        for(int index=0;index<paths.size();index++) {
            ClassFile entry=value.classes().get(index);if(!paths.get(index).equals(Path.of(entry.fileRef().path())))throw new IOException("class inventory/order changed");
            RawWindowCaptureJson.exactBytes(entry.fileRef(),524288);
            if(!entry.nativeFile().equals(SharedSourceFiles.nativeFile(paths.get(index))))throw new IOException("actual class native identity changed");
        }
        if(!value.rootIdentity().equals(SharedSourceFiles.nativeDirectory(root))||!paths.equals(inventory(value.mode(),root)))throw new IOException("class root/inventory changed during readback");
        return value;
    }
    public static void main(String[] args)throws IOException {
        byte[] output;int exit=0;String machine="unknown";
        try {
            machine=WindowsJobProcess.currentMachineId();if(args.length!=3)throw new IllegalArgumentException("PREPARE|RAW_LIMITED absolute-classes-root absolute-CREATE_NEW-manifest required");
            FileRef ref=capture(Mode.valueOf(args[0]),Path.of(args[1]),Path.of(args[2]));
            output=ControlBuild.strictMapper().writeValueAsBytes(ref);
        }catch(IOException|RuntimeException failure){exit=2;output=RawWindowCaptureJson.encode(new RawWindowCaptureJson.CliFailure(CLI_FAILURE_SCHEMA,machine,Instant.now().toString(),"CLASS_CLOSURE_REJECTED",shortError(failure.toString())));}
        System.out.write(output);System.out.write('\n');System.out.flush();if(exit!=0)System.exit(exit);
    }
}



