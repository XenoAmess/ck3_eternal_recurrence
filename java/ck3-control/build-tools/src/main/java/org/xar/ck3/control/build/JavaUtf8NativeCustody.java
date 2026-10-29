package org.xar.ck3.control.build;

import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.CiBootstrap.JavaUtf8Invocation;

/**
 * Explicit parent-side native custody for an already published JDK-only invocation.
 * No encoder, process launcher, admission, runtime qualification or Game authority.
 * Files remain open without write/delete sharing; all source/output ancestry remains
 * open without delete sharing. The same SharedSourceFiles decoder measures the held
 * handles and the original paths before, during and after the original owned Job.
 */
public final class JavaUtf8NativeCustody {
    private JavaUtf8NativeCustody() { }
    public static final int MAXIMUM_EVIDENCE_BYTES=4<<20;
    public static final String EVIDENCE_SCHEMA="xar.java-utf8-native-source-continuity/v1";
    private record HeldFile(HANDLE handle,SharedSourceFiles.Witness original) { }
    private record HeldDirectory(Path path,HANDLE handle,SharedSourceFiles.NativeFile original,boolean immutableContents) { }
    public enum DirectoryUse { IMMUTABLE_RUNTIME, MUTABLE_OUTPUT_OR_ANCESTOR }
    public record DirectoryWitness(String path,SharedSourceFiles.NativeFile nativeFile,DirectoryUse use) {
        public DirectoryWitness { if(path==null||!Path.of(path).isAbsolute())throw new IllegalArgumentException("Absolute original native directory required");Objects.requireNonNull(nativeFile);Objects.requireNonNull(use); }
    }
    /** A persisted observation, never a live Held capability or authority to repeat a process. */
    public record Evidence(String schema,String machineId,String observedAtUtc,ControlBuild.FileRef envelope,List<SharedSourceFiles.Witness> files,
            List<DirectoryWitness> directories,WindowsJobProcess.ProcessIdentity identity,WindowsJobProcess.CommandResult terminal) {
        public Evidence {
            if(!EVIDENCE_SCHEMA.equals(schema)||machineId==null||!machineId.matches("[a-z0-9][a-z0-9-]{1,80}"))throw new IllegalArgumentException("Exact version and actual machine required");java.time.Instant.parse(observedAtUtc);Objects.requireNonNull(envelope);files=List.copyOf(files);directories=List.copyOf(directories);Objects.requireNonNull(identity);Objects.requireNonNull(terminal);
            if(files.isEmpty()||files.size()>32768||directories.isEmpty()||directories.size()>8192||!identity.equals(terminal.identity())||terminal.accounting().activeProcesses()!=0)throw new IllegalArgumentException("Finite same-process Job0 source evidence required");
            var names=new java.util.HashSet<String>();for(var file:files){Objects.requireNonNull(file.source());Objects.requireNonNull(file.nativeFile());if(!names.add(file.source().path())||file.source().bytes()!=file.nativeFile().logicalBytes())throw new IllegalArgumentException("Unique consistent original native file witnesses required");}
            names.clear();for(var directory:directories)if(!names.add(directory.path()))throw new IllegalArgumentException("Unique original native directories required");
            if(files.stream().noneMatch(file->file.source().equals(envelope)))throw new IllegalArgumentException("Original actual envelope must belong to native source table");
        }
    }
    private record SourceTable(ControlBuild.FileRef envelope,List<SharedSourceFiles.Witness> files,List<DirectoryWitness> directories) { }
    public static byte[] encodeEvidence(Evidence evidence)throws IOException {
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(Objects.requireNonNull(evidence));if(bytes.length>MAXIMUM_EVIDENCE_BYTES)throw new IOException("Native source evidence exceeds its finite wire bound");return bytes;
    }
    public static Evidence decodeEvidence(byte[] original)throws IOException {
        if(original.length==0||original.length>MAXIMUM_EVIDENCE_BYTES)throw new IOException("Bounded versioned native source evidence required");return ControlBuild.strictMapper().readValue(original,Evidence.class);
    }
    private static LinkedHashMap<Path,Boolean> directoryPaths(JavaUtf8Invocation.JdkInputs original,JavaUtf8Invocation.Request request)throws IOException {
        var result=new LinkedHashMap<Path,Boolean>();Path evidence=Path.of(request.evidenceRoot().path());Path compiled=request.target() instanceof JavaUtf8Invocation.SourceTarget source?Path.of(source.compiledRoot().path()):null;
        for(var directory:original.directories()){Path path=Path.of(directory.path());result.merge(path,!path.equals(evidence)&&!path.equals(compiled),Boolean::logicalOr);}
        for(var file:original.files())for(Path parent=Path.of(file.path()).getParent();parent!=null;parent=parent.getParent())result.putIfAbsent(parent,false);
        for(var directory:original.directories())for(Path parent=Path.of(directory.path()).getParent();parent!=null;parent=parent.getParent())result.putIfAbsent(parent,false);
        if(result.size()>8192)throw new IOException("Finite complete native ancestry required");return result;
    }
    /** Cold readback checks actual source identities. It cannot recreate a held capability or prove a new execution. */
    public static void requireCurrent(Evidence evidence,JavaUtf8Invocation.Launch originalLaunch,JavaUtf8Invocation.Carrier expectedCarrier)throws IOException {
        if(!evidence.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("Native source evidence belongs to another machine");
        var inputs=JavaUtf8Invocation.inputSnapshot(originalLaunch,expectedCarrier);var envelope=originalLaunch.publication().envelope();
        if(!evidence.envelope().path().equals(envelope.path())||evidence.envelope().bytes()!=envelope.bytes()||!evidence.envelope().sha256().equals(envelope.sha256())||evidence.files().size()!=inputs.files().size())throw new IOException("Native evidence differs from original invocation envelope/complete file set");
        for(int index=0;index<inputs.files().size();index++){
            var expected=inputs.files().get(index);var actual=evidence.files().get(index);
            if(!expected.path().equals(actual.source().path())||expected.bytes()!=actual.source().bytes()||!expected.sha256().equals(actual.source().sha256()))throw new IOException("Recorded native file table differs from original JDK content closure");SharedSourceFiles.assertUnchanged(actual);
        }
        var directories=directoryPaths(inputs,originalLaunch.logicalRequest());if(directories.size()!=evidence.directories().size())throw new IOException("Original native ancestry table differs");int index=0;
        for(var entry:directories.entrySet()){
            var actual=evidence.directories().get(index++);var use=entry.getValue()?DirectoryUse.IMMUTABLE_RUNTIME:DirectoryUse.MUTABLE_OUTPUT_OR_ANCESTOR;
            if(!entry.getKey().toString().equals(actual.path())||actual.use()!=use)throw new IOException("Original native directory role/order differs");sameDirectory(actual.nativeFile(),SharedSourceFiles.nativeDirectory(entry.getKey()));
            if(use==DirectoryUse.IMMUTABLE_RUNTIME){HANDLE handle=open(entry.getKey(),true);try{var nativeCurrent=SharedSourceFiles.nativeHeldDirectory(handle);sameDirectory(actual.nativeFile(),new SharedSourceFiles.DirectoryIdentity(nativeCurrent.volumeSerialDecimal(),nativeCurrent.fileIdDecimal(),nativeCurrent.creationFiletimeDecimal()));if(!actual.nativeFile().lastWriteFiletimeDecimal().equals(nativeCurrent.lastWriteFiletimeDecimal()))throw new IOException("Recorded immutable runtime directory changed");}finally{if(!Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("Close cold directory readback Win32="+Native.getLastError());}}
        }
    }

    /** Continuous native source custody is obtained only by this actual OS acquisition. */
    public static Held acquire(JavaUtf8Invocation.Launch launch,JavaUtf8Invocation.Carrier carrier)throws IOException {
        Objects.requireNonNull(launch);Objects.requireNonNull(carrier);
        var original=JavaUtf8Invocation.inputSnapshot(launch,carrier);
        var files=new ArrayList<HeldFile>();var directories=new ArrayList<HeldDirectory>();
        try {
            var directoryPaths=directoryPaths(original,launch.logicalRequest());
            for(var entry:directoryPaths.entrySet()){
                SharedSourceFiles.plainAncestors(entry.getKey());HANDLE handle=open(entry.getKey(),true);
                try {
                    var measured=SharedSourceFiles.nativeHeldDirectory(handle);
                    sameDirectory(measured,SharedSourceFiles.nativeDirectory(entry.getKey()));
                    directories.add(new HeldDirectory(entry.getKey(),handle,measured,entry.getValue()));
                }catch(IOException|RuntimeException error){closeHandle(handle,error);throw error;}
            }
            for(var pin:original.files()){
                Path path=Path.of(pin.path());SharedSourceFiles.plainAncestors(path);HANDLE handle=open(path,false);
                try {
                    var witness=SharedSourceFiles.observe(path);var measured=SharedSourceFiles.nativeHeldFile(handle);
                    sameFile(witness.nativeFile(),measured);
                    if(witness.source().bytes()!=pin.bytes()||!witness.source().sha256().equals(pin.sha256()))throw new IOException("JDK content pin differs from actual held native input");
                    files.add(new HeldFile(handle,witness));
                }catch(IOException|RuntimeException error){closeHandle(handle,error);throw error;}
            }
            if(!original.equals(JavaUtf8Invocation.inputSnapshot(launch,carrier)))throw new IOException("Input closure changed during actual native acquisition");
            var result=new Held(launch,carrier,original,files,directories);result.requireCurrent();return result;
        }catch(IOException|RuntimeException error){release(files,directories,error);throw error;}
    }

    /** Pure finite quote, not native evidence: oversized inputs fail before any actual child can start. */
    static long evidenceUpperBound(long actualSourceTableBytes,Path actualExecutable)throws IOException {
        if(actualSourceTableBytes<=0||actualExecutable==null||!actualExecutable.isAbsolute())throw new IOException("Positive actual source-table quote and original executable required");
        try {
            long upper=Math.addExact(actualSourceTableBytes,Math.addExact(4L*actualExecutable.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length,16384));
            if(upper>MAXIMUM_EVIDENCE_BYTES)throw new IOException("Complete original native source evidence exceeds its wire cap before process launch");return upper;
        }catch(ArithmeticException error){throw new IOException("Native evidence complete quote overflow before process launch",error);}
    }
    private static HANDLE open(Path path,boolean directory)throws IOException {
        // Non-inheritable handles. Files deny writes/deletes; directories permit child output but deny their own replacement.
        HANDLE handle=Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path),directory?0x81:0x80000080,directory?3:1,null,3,0x00200000|(directory?0x02000000:0),null);
        if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle))throw new IOException("Acquire continuous UTF8 native custody Win32="+Native.getLastError()+" path="+path);
        return handle;
    }
    private static void sameFile(SharedSourceFiles.NativeFile expected,SharedSourceFiles.NativeFile actual)throws IOException {
        if(!expected.identityKey().equals(actual.identityKey())||!expected.legacyVolumeSerialDecimal().equals(actual.legacyVolumeSerialDecimal())||!expected.legacyFileIdHex().equals(actual.legacyFileIdHex())||expected.logicalBytes()!=actual.logicalBytes()||!expected.lastWriteFiletimeDecimal().equals(actual.lastWriteFiletimeDecimal()))throw new IOException("Continuously held original native file identity/content metadata drifted");
    }
    private static void sameDirectory(SharedSourceFiles.NativeFile expected,SharedSourceFiles.DirectoryIdentity actual)throws IOException {
        if(!expected.volumeSerialDecimal().equals(actual.volumeSerialDecimal())||!expected.fileIdDecimal().equals(actual.fileIdDecimal())||!expected.creationFiletimeDecimal().equals(actual.creationFiletimeDecimal()))throw new IOException("Continuously held original native directory identity drifted");
    }
    private static void closeHandle(HANDLE handle,Throwable failure){if(!Kernel32.INSTANCE.CloseHandle(handle))failure.addSuppressed(new IOException("Close UTF8 custody handle Win32="+Native.getLastError()));}
    private static IOException release(List<HeldFile> files,List<HeldDirectory> directories,Throwable failure){
        IOException own=null;for(int index=files.size()-1;index>=0;index--)if(!Kernel32.INSTANCE.CloseHandle(files.get(index).handle())){var error=new IOException("Close held file Win32="+Native.getLastError());if(failure!=null)failure.addSuppressed(error);else if(own==null)own=error;else own.addSuppressed(error);}
        for(int index=directories.size()-1;index>=0;index--)if(!Kernel32.INSTANCE.CloseHandle(directories.get(index).handle())){var error=new IOException("Close held directory Win32="+Native.getLastError());if(failure!=null)failure.addSuppressed(error);else if(own==null)own=error;else own.addSuppressed(error);}return own;
    }

    public static final class Held implements AutoCloseable {
        private final JavaUtf8Invocation.Launch launch;
        private final JavaUtf8Invocation.Carrier carrier;
        private final JavaUtf8Invocation.JdkInputs original;
        private final List<HeldFile> files;
        private final List<HeldDirectory> directories;
        private WindowsJobProcess child;
        private WindowsJobProcess.OwnedStdio stdioChild;
        private WindowsJobProcess.ProcessIdentity identity;
        private boolean terminalConsumed,closed;
        private Held(JavaUtf8Invocation.Launch launch,JavaUtf8Invocation.Carrier carrier,JavaUtf8Invocation.JdkInputs original,List<HeldFile> files,List<HeldDirectory> directories){this.launch=launch;this.carrier=carrier;this.original=original;this.files=List.copyOf(files);this.directories=List.copyOf(directories);}

        /** Invoke immediately after the original WJP.start, retaining that exact original owner, never a reconstructed identity. */
        public synchronized void attach(WindowsJobProcess actualChild)throws IOException {
            requireCurrent();if(child!=null||stdioChild!=null)throw new IOException("Native custody already attached to its original child");child=Objects.requireNonNull(actualChild);identity=actualChild.identity();
        }
        /** Retain the actual duplex owner. Its data-shaped identity cannot replace this capability. */
        public synchronized void attach(WindowsJobProcess.OwnedStdio actualChild)throws IOException {
            requireCurrent();if(child!=null||stdioChild!=null)throw new IOException("Native custody already attached to its original child");
            stdioChild=Objects.requireNonNull(actualChild);identity=actualChild.identity();
        }
        public synchronized void requireCurrent()throws IOException {
            if(closed)throw new IOException("Native UTF8 custody is closed");
            for(var held:files){sameFile(held.original().nativeFile(),SharedSourceFiles.nativeHeldFile(held.handle()));sameFile(held.original().nativeFile(),SharedSourceFiles.nativeFile(Path.of(held.original().source().path())));}
            for(var held:directories){var actual=SharedSourceFiles.nativeHeldDirectory(held.handle());sameDirectory(held.original(),SharedSourceFiles.nativeDirectory(held.path()));sameDirectory(held.original(),new SharedSourceFiles.DirectoryIdentity(actual.volumeSerialDecimal(),actual.fileIdDecimal(),actual.creationFiletimeDecimal()));if(held.immutableContents()&&!held.original().lastWriteFiletimeDecimal().equals(actual.lastWriteFiletimeDecimal()))throw new IOException("Original class-directory inventory changed during native custody");}
        }
        /** Compose with, rather than replace, the original quota/deadline/native guard. */
        public Runnable guard(Runnable originalGuard){Objects.requireNonNull(originalGuard);return ()->{try{requireCurrent();originalGuard.run();}catch(IOException error){throw new UncheckedIOException(error);}};}

        private SourceTable sourceTable(){var envelope=launch.publication().envelope();return new SourceTable(new ControlBuild.FileRef(envelope.path(),envelope.bytes(),envelope.sha256()),files.stream().map(HeldFile::original).toList(),directories.stream().map(held->new DirectoryWitness(held.path().toString(),held.original(),held.immutableContents()?DirectoryUse.IMMUTABLE_RUNTIME:DirectoryUse.MUTABLE_OUTPUT_OR_ANCESTOR)).toList());}
        /** Exact current source-table bytes plus a bounded original executable/terminal allowance; no 4MiB minimum quote. */
        public synchronized long maximumEvidenceBytes(Path actualExecutable)throws IOException {
            requireCurrent();return evidenceUpperBound(ControlBuild.strictMapper().writeValueAsBytes(sourceTable()).length,actualExecutable);
        }

        /** Actual sources continuity and drained identity only; exit/stop/limits are still the original caller's result. */
        public synchronized TerminalSources verifyTerminal(WindowsJobProcess.CommandResult actual)throws IOException {
            requireCurrent();if(child==null||terminalConsumed||!identity.equals(actual.identity())||!identity.equals(child.identity())||actual.accounting().activeProcesses()!=0||child.accounting().activeProcesses()!=0)throw new IOException("Original actual child terminal and Job0 required before native custody settlement");
            return terminalSources(actual);
        }
        /** Consume original held duplex retirement, while both native source and process handles remain owned. */
        public synchronized TerminalSources verifyTerminal(WindowsJobProcess.RetiredCustody retired,WindowsJobProcess.CommandResult actual)throws IOException {
            requireCurrent();Objects.requireNonNull(retired);Objects.requireNonNull(actual);
            if(stdioChild==null)throw new IOException("Original actual duplex owner required before native custody settlement");
            retired.requireOriginal(stdioChild,actual);
            var observed=retired.observation();
            if(stdioChild==null||terminalConsumed||retired.spec()!=stdioChild.spec()
                    ||!identity.equals(actual.identity())||!identity.equals(stdioChild.identity())||!identity.equals(observed.identity())
                    ||!stdioChild.sessionNonce().equals(observed.sessionNonce())||!WindowsJobProcess.currentMachineId().equals(observed.machineId())
                    ||actual.accounting().activeProcesses()!=0||observed.accounting().activeProcesses()!=0
                    ||Integer.toUnsignedLong(actual.exitCode())!=observed.exitCode()||!actual.accounting().equals(observed.accounting()))
                throw new IOException("Original actual duplex owner, held retirement and Job0 required before native custody settlement");
            var sources=terminalSources(actual);retired.requireCurrent();requireCurrent();return sources;
        }
        private TerminalSources terminalSources(WindowsJobProcess.CommandResult actual)throws IOException {
            if(!original.equals(JavaUtf8Invocation.inputSnapshot(launch,carrier)))throw new IOException("Original complete JDK input closure changed across the actual native Job");
            var table=sourceTable();var evidence=new Evidence(EVIDENCE_SCHEMA,WindowsJobProcess.currentMachineId(),java.time.Instant.now().toString(),table.envelope(),table.files(),table.directories(),identity,actual);
            if(encodeEvidence(evidence).length>maximumEvidenceBytes(Path.of(identity.executable())))throw new IOException("Actual native source evidence exceeded its quoted original terminal bound");
            terminalConsumed=true;return new TerminalSources(evidence);
        }
        @Override public synchronized void close()throws IOException {
            if(closed)return;IOException failure=(child!=null||stdioChild!=null)&&!terminalConsumed?new IOException("Native custody closed without consuming original Job0; no native source continuity qualification"):null;
            var closeFailure=release(files,directories,failure);closed=true;if(failure!=null)throw failure;if(closeFailure!=null)throw closeFailure;
        }
    }
    /** Private constructor prevents data-shaped records from granting a held lifecycle. */
    public static final class TerminalSources {
        private final Evidence evidence;
        private TerminalSources(Evidence evidence){this.evidence=evidence;}
        public WindowsJobProcess.ProcessIdentity identity(){return evidence.identity();}
        public WindowsJobProcess.CommandResult terminal(){return evidence.terminal();}
        public Evidence evidence(){return evidence;}
    }
}
