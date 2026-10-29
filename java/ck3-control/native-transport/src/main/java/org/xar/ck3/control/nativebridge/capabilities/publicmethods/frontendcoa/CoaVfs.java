package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCapture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Read-scope guard for the sole original VFS projection. It does not grant Native authority or implement a resolver. */
public final class CoaVfs {
    public static final long MAXIMUM_ASSET_BYTES=16L*1024*1024;
    private CoaVfs() { }
    /** Explicit pre-Core source budget, never a caller argument or an artifact-write lease. */
    public record Limits(long maximumSourceBytes,long maximumArchiveBytes) {
        public Limits {need(maximumSourceBytes>0&&maximumSourceBytes<=16L*1024*1024*1024&&maximumArchiveBytes>0&&maximumArchiveBytes<=maximumSourceBytes,"finite explicit VFS source-read limits required");}
    }
    public static RawJson encodeLimits(Limits value){Objects.requireNonNull(value);var row=StrictJson.object().put("schema","xar.java-coa-vfs-source-read-limits/v1").put("maximum_source_bytes",value.maximumSourceBytes()).put("maximum_archive_bytes",value.maximumArchiveBytes());return new RawJson(StrictJson.canonical(row,4096));}
    public static Limits decodeLimits(RawJson original){var row=StrictJson.parse(original.bytes(),4096);StrictJson.object(row,java.util.Set.of("schema","maximum_source_bytes","maximum_archive_bytes"));need(StrictJson.text(row.get("schema")).equals("xar.java-coa-vfs-source-read-limits/v1"),"exact VFS source-read limits schema required");return new Limits(StrictJson.integer(row.get("maximum_source_bytes"),1,16L*1024*1024*1024),StrictJson.integer(row.get("maximum_archive_bytes"),1,16L*1024*1024*1024));}
    /** DATA binding only. The actual Root owner supplies and guards this session/source/diagnostic capture. */
    public record Input(Vfs request,ExactRef profileExecutable,BridgeDiagnostics.Received received,
            TransportSession sameSession,G2Source source,Limits limits) {
        public Input {Objects.requireNonNull(request);Objects.requireNonNull(profileExecutable);Objects.requireNonNull(received);Objects.requireNonNull(sameSession);Objects.requireNonNull(source);Objects.requireNonNull(limits);need(source.machineId().equals(sameSession.machineId()),"VFS source/session machine differs");Path executable=Path.of(profileExecutable.path());need(executable.isAbsolute()&&executable.normalize().equals(executable)&&profileExecutable.bytes()>0,"exact absolute Root profile executable required");}
    }
    private record FileGuard(Path path,SharedSourceFiles.NativeFile nativeFile) {
        private void requireCurrent()throws IOException{if(!nativeFile.equals(SharedSourceFiles.nativeFile(path)))throw new IOException("VFS original source identity/metadata changed during projection");}
    }
    private record DirectoryGuard(Path path,SharedSourceFiles.DirectoryIdentity identity) {
        private void requireCurrent()throws IOException{if(!identity.equals(SharedSourceFiles.nativeDirectory(path)))throw new IOException("VFS original mounted directory identity changed");}
    }
    private record Absent(Path path) {private void requireCurrent()throws IOException{SharedSourceFiles.plainAncestors(path);if(Files.exists(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("VFS absent source candidate appeared during projection");}}
    private static final class Scope {
        private final List<FileGuard> files=new ArrayList<>();private final List<DirectoryGuard> directories=new ArrayList<>();private final List<Absent> absent=new ArrayList<>();private final Limits limits;private long reserved;
        private Scope(Limits limits){this.limits=limits;}
        private void reserve(long bytes)throws IOException{if(bytes<0||bytes>limits.maximumSourceBytes()-reserved)throw new IOException("VFS complete source-read reservation exceeds actual configured budget");reserved+=bytes;}
        private SharedSourceFiles.NativeFile file(Path path)throws IOException{var actual=SharedSourceFiles.nativeFile(path);files.add(new FileGuard(path,actual));return actual;}
        private void directory(Path path)throws IOException{directories.add(new DirectoryGuard(path,SharedSourceFiles.nativeDirectory(path)));}
        private void requireCurrent()throws IOException{for(var row:directories)row.requireCurrent();for(var row:files)row.requireCurrent();for(var row:absent)row.requireCurrent();}
    }
    public static Response project(Input input)throws IOException {
        Objects.requireNonNull(input);var received=input.received();
        if(!received.equals(BridgeDiagnosticsCapture.capture(received.pipeName(),received.original(),received.retainedSnapshot())))throw new IOException("VFS diagnostics differ from the actual original packet capture");
        if(received.original().receivedState()!=NativeGameTransport.ReceivedState.HELLO_VERIFIED||!received.session().filter(input.sameSession()::equals).isPresent())throw new IOException("VFS diagnostics are not the identical current native transport session");
        var hello=received.original().originalHello().orElseThrow(()->new IOException("VFS original HELLO absent")).original();
        if(!hello.gameSha256().equalsIgnoreCase(FrontendCoaService.EXE_SHA)||!input.profileExecutable().sha256().equalsIgnoreCase(FrontendCoaService.EXE_SHA))throw new IOException("original VFS provider supports exact CK3 1.19.0.6 only; current build has no qualified mount projection");
        Path executable=Path.of(input.profileExecutable().path()).toAbsolutePath().normalize();SharedSourceFiles.plainAncestors(executable);
        if(!executable.getFileName().toString().equalsIgnoreCase("ck3.exe")||executable.getParent()==null||!executable.getParent().getFileName().toString().equalsIgnoreCase("binaries"))throw new IOException("VFS requires the same actual launch profile executable");
        Path root=executable.getParent().getParent();SharedSourceFiles.plainAncestors(input.request().directory().toAbsolutePath().normalize());
        if(!input.request().directory().toRealPath().equals(root.toRealPath()))throw new IOException("caller game_directory differs from the actual retained Root launch profile");
        var observer=received.privateObservers().physfsMountedData().orElseThrow(()->new IOException("actual current transport has no original physfs mounted-data observer"));
        var rows=OpportunityJson.array(observer.get("rows"),"actual VFS source rows");
        if(rows.isEmpty()||rows.size()>128)throw new IOException("VFS observed source count exceeds original finite limits");
        Scope scope=new Scope(input.limits());scope.directory(root);var exe=scope.file(executable);
        if(exe.logicalBytes()!=input.profileExecutable().bytes())throw new IOException("actual Root executable identity/size differs");scope.reserve(exe.logicalBytes());
        for(var value:rows){var row=OpportunityJson.object(value,"original VFS source row");Path mount=Path.of(OpportunityJson.text(row.get("path"),"observed mounted path")).toAbsolutePath().normalize();SharedSourceFiles.plainAncestors(mount);
            if(Files.isDirectory(mount,LinkOption.NOFOLLOW_LINKS)){
                scope.directory(mount);Path candidate=mount.resolve(input.request().logicalPath()).normalize();if(!candidate.startsWith(mount))throw new IOException("VFS logical candidate escapes observed mount");SharedSourceFiles.plainAncestors(candidate);
                if(Files.exists(candidate,LinkOption.NOFOLLOW_LINKS)){var file=scope.file(candidate);if(file.logicalBytes()<128||file.logicalBytes()>MAXIMUM_ASSET_BYTES)throw new IOException("VFS observed DDS outside original byte limits");scope.reserve(file.logicalBytes());}
                else scope.absent.add(new Absent(candidate));
            }else{
                var archive=scope.file(mount);if(archive.logicalBytes()>input.limits().maximumArchiveBytes())throw new IOException("VFS observed archive exceeds configured source limit");
                // Reserve its complete ZIP metadata/file bound plus the original maximum decompressed member.
                // The unique original algorithm enforces <=50,000 members and reads at most one <=16MiB match.
                scope.reserve(archive.logicalBytes());scope.reserve(MAXIMUM_ASSET_BYTES);
            }
        }
        var fields=new LinkedHashMap<String,OpportunityJson.Value>();fields.put("connected",new OpportunityJson.Bool(true));fields.put("hello",received.hello().orElseThrow(()->new IOException("VFS original HELLO tree absent")));
        fields.put("private_observers",new OpportunityJson.Obj(java.util.Map.of("physfs_mounted_data_observer_v1",observer)));
        RawJson diagnostic=new RawJson(DriverJson.encode(new OpportunityJson.Obj(fields)));
        if(diagnostic.bytes().length>1_048_576)throw new IOException("bounded VFS diagnostic source required");
        scope.requireCurrent();Response result;Throwable failure=null;
        try{result=FrontendCoaService.projectVfs(new Vfs(Method.VFS,root,input.request().logicalPath()),diagnostic);}
        catch(IOException|RuntimeException|Error originalFailure){failure=originalFailure;throw originalFailure;}
        finally{try{scope.requireCurrent();}catch(IOException drift){if(failure!=null)failure.addSuppressed(drift);else throw drift;}}
        if(result.original().bytes().length>1_048_576)throw new IOException("bounded VFS projection result required");
        return result;
    }
}
