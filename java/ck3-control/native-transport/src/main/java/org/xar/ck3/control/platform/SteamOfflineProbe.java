package org.xar.ck3.control.platform;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.PointerByReference;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import java.util.Optional;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;
import java.nio.file.LinkOption;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;

/** Shared background producer: exact native byte first, then the original already-owned CEF getter. */
public final class SteamOfflineProbe {
    public record Plan(String machineId,ControlBuild.FileRef steamExecutable,Instant deadline) {
        public Plan {
            Objects.requireNonNull(machineId);Objects.requireNonNull(steamExecutable);Objects.requireNonNull(deadline);
            if(machineId.isBlank()||machineId.equals("unknown")||!Path.of(steamExecutable.path()).getFileName().toString().equalsIgnoreCase("steam.exe"))
                throw new IllegalArgumentException("Exact Steam source and machine required");
        }
    }
    public static final class UnavailableException extends IOException {
        private static final long serialVersionUID=1L;
        // In-process typed provenance; this exception has no Java object-serialization contract.
        @SuppressWarnings("serial")
        private final ExactRef evidence;
        UnavailableException(String reason,Throwable cause,ExactRef evidence){super(reason,cause);this.evidence=Objects.requireNonNull(evidence);}
        public String status(){return "unavailable";}
        public ExactRef evidence(){return evidence;}
    }
    public static final class OnlineException extends IOException {
        private static final long serialVersionUID=1L;
        // In-process typed provenance; this exception has no Java object-serialization contract.
        @SuppressWarnings("serial")
        private final ExactRef evidence;
        private OnlineException(ExactRef evidence){super("Actual CEF getter observed online; no offline Game admission");this.evidence=evidence;}
        public ExactRef evidence(){return evidence;}
    }
    interface ObservationLease extends AutoCloseable {
        void verify() throws IOException;
        @Override void close() throws IOException;
    }
    private interface VersionApi extends StdCallLibrary {
        int GetFileVersionInfoSizeW(WString path,IntByReference ignored);
        boolean GetFileVersionInfoW(WString path,int ignored,int size,Pointer data);
        boolean VerQueryValueW(Pointer data,WString subBlock,PointerByReference value,IntByReference length);
    }
    private SteamOfflineProbe(){ }
    public static final class QualifiedOffline implements AutoCloseable {
        private final Plan plan;
        private final ObservationLease lease;
        private final SteamOfflineObservation.Offline observation;
        private final Instant observed;
        private final long observedMonotonicNanos;
        private final ControlBuild.FileRef evidence;
        private boolean consumed,closed;
        private QualifiedOffline(Plan plan,ObservationLease lease,SteamOfflineObservation.Offline observation,ControlBuild.FileRef evidence){
            this.plan=plan;this.lease=lease;this.observation=observation;
            this.observed=Instant.parse(observation.common().observedAtUtc());this.observedMonotonicNanos=System.nanoTime();this.evidence=evidence;
        }
        public ControlBuild.FileRef evidence(){return evidence;}
        public SteamOfflineObservation.Offline observation(){return observation;}
        public synchronized void verify() throws IOException {
            if(closed)throw new IOException("Steam observation resource closed");
            Win32Host.deadline(plan.deadline());plan.steamExecutable().verify();lease.verify();
        }
        public synchronized void consumeBeforeGameCreate() throws IOException {
            if(consumed)throw new IOException("Fresh Steam observation already consumed");
            consumed=true;
            if(!Instant.now().isBefore(observed.plusSeconds(10))||System.nanoTime()-observedMonotonicNanos>=10_000_000_000L)
                throw new IOException("Steam observation stale before CREATE");
            evidence.verify();verify();
        }
        @Override public synchronized void close() throws IOException {if(!closed){closed=true;lease.close();}}
    }
    private static final class NativeLease implements ObservationLease {
        private final Plan plan;
        private final Win32Host.ReadProcess process;
        private final WindowsJobProcess.ProcessIdentity identity;
        private final SharedSourceFiles.Witness source;
        private final SteamOfflineObservation.Source sourceIdentity;
        private final Win32Host.Module module;
        private final SteamOfflineProfiles.Profile profile;
        private NativeLease(Plan plan,Win32Host.ReadProcess process,WindowsJobProcess.ProcessIdentity identity,
                SharedSourceFiles.Witness source,SteamOfflineObservation.Source sourceIdentity,Win32Host.Module module,SteamOfflineProfiles.Profile profile){
            this.plan=plan;this.process=process;this.identity=identity;this.source=source;this.sourceIdentity=sourceIdentity;this.module=module;this.profile=profile;
        }
        @Override public void verify() throws IOException {
            SharedSourceFiles.assertUnchanged(source);
            if(!sourceIdentity.equals(sourceIdentity(source))||!identity.equals(process.identity()))throw new IOException("Steam incarnation/source changed");
            if(!module.equals(Win32Host.module(identity.pid(),Path.of(source.source().path()),plan.deadline())))throw new IOException("SteamUI loaded mapping changed");
            anchors(process,module,profile,plan.deadline());samples(process,module,profile,plan.deadline());
        }
        @Override public void close() throws IOException {process.close();}
    }
    /** Only this live producer can mint admission. Persisted JSON cannot reconstruct QualifiedOffline. */
    public static QualifiedOffline observe(Plan plan,Path newEvidenceFile) throws IOException {
        return observe(plan,newEvidenceFile,java.time.Duration.ofSeconds(2));
    }
    /** Explicit original --timeout range for the bounded CEF query stage; no process or UI is created. */
    public static QualifiedOffline observe(Plan plan,Path newEvidenceFile,java.time.Duration queryTimeout) throws IOException {
        Objects.requireNonNull(plan);Objects.requireNonNull(newEvidenceFile);
        Objects.requireNonNull(queryTimeout);
        if(queryTimeout.compareTo(java.time.Duration.ofMillis(100))<0||queryTimeout.compareTo(java.time.Duration.ofSeconds(10))>0)
            throw new IllegalArgumentException("Original CEF query timeout range is100ms through10s");
        ProjectStoragePolicy.requireBulkOutput(newEvidenceFile);SharedSourceFiles.plainAncestors(newEvidenceFile.getParent());
        if(Files.exists(newEvidenceFile,LinkOption.NOFOLLOW_LINKS))throw new IOException("Fresh Steam receipt already exists; do not replay unknown observation");
        String nonce=java.util.HexFormat.of().formatHex(randomBytes(16)),started=Instant.now().toString();
        List<String> diagnostics=new ArrayList<>();
        try{return observeCurrent(plan,newEvidenceFile,nonce);}
        catch(IOException|RuntimeException nativeFailure){
            if(Files.exists(newEvidenceFile,LinkOption.NOFOLLOW_LINKS))throw new IOException("Native observation publication exists without retained token; no second provider write",nativeFailure);
            diagnostics.add(bounded("native_provider_unavailable="+nativeFailure));
            SteamOfflineCefProvider.Observation actual=SteamOfflineCefProvider.observe(plan,nonce,started,diagnostics,queryTimeout);
            ObservationLease lease=actual.lease().orElse(null);
            try{
                ControlBuild.FileRef ref=publish(newEvidenceFile,actual.result());
                if(actual.result() instanceof SteamOfflineObservation.Offline offline){
                    if(lease==null)throw new IOException("Actual CEF offline observation has no retained live lease");
                    return new QualifiedOffline(plan,lease,offline,ref);
                }
                if(lease!=null){lease.close();lease=null;}
                if(actual.result() instanceof SteamOfflineObservation.Online)throw new OnlineException(LifecycleEvidence.exact(ref));
                throw new UnavailableException(String.join("; ",actual.result().common().diagnostics()),nativeFailure,LifecycleEvidence.exact(ref));
            }catch(IOException|RuntimeException failure){
                if(lease!=null)try{lease.close();}catch(IOException closeFailure){failure.addSuppressed(closeFailure);}
                throw failure;
            }
        }
    }
    private static QualifiedOffline observeCurrent(Plan plan,Path newEvidenceFile,String nonce) throws IOException {
        Objects.requireNonNull(plan);Win32Host.deadline(plan.deadline());
        if(!plan.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("Steam observation machine differs");
        plan.steamExecutable().verify();
        List<Win32Host.ProcessRow> rows=Win32Host.processes("steam.exe",plan.deadline());
        if(rows.size()!=1)throw new IOException("Exactly one actual Steam incarnation required");
        WindowsJobProcess.ProcessIdentity expected=rows.get(0).identity();
        if(!Path.of(expected.executable()).toRealPath().equals(Path.of(plan.steamExecutable().path()).toRealPath()))throw new IOException("Actual Steam executable differs");
        Win32Host.ReadProcess process=Win32Host.open(expected.pid());
        try {
            if(!expected.equals(process.identity()))throw new IOException("Steam changed before native read");
            Path ui=Path.of(expected.executable()).getParent().resolve("steamui.dll");
            SharedSourceFiles.Witness source=SharedSourceFiles.observe(ui);
            SteamOfflineObservation.Source sourceBefore=sourceIdentity(source);
            String version=version(Path.of(expected.executable()));
            SteamOfflineProfiles.Profile profile;
            try{profile=SteamOfflineProfiles.select(version,source.source().bytes(),source.source().sha256());}
            catch(IllegalArgumentException unavailable){throw new IOException(unavailable.getMessage(),unavailable);}
            if(!version.equals(version(ui)))throw new IOException("Steam and SteamUI file versions differ");
            fileAnchors(ui,profile);
            Win32Host.Module module=Win32Host.module(expected.pid(),ui,plan.deadline());
            if(module.base()<0x10000||module.base()>0x7fff_ffff_ffffL-profile.imageSize()||module.size()!=profile.imageSize())throw new IOException("SteamUI memory image layout differs");
            anchors(process,module,profile,plan.deadline());State actual=samples(process,module,profile,plan.deadline());
            anchors(process,module,profile,plan.deadline());
            if(!module.equals(Win32Host.module(expected.pid(),ui,plan.deadline()))||!expected.equals(process.identity()))throw new IOException("Steam mapping/incarnation changed during observation");
            SharedSourceFiles.assertUnchanged(source);plan.steamExecutable().verify();
            SteamOfflineObservation.Source sourceAfter=sourceIdentity(source);
            SteamOfflineObservation.SteamProcess steam=processIdentity(expected,version);
            String observed=Instant.now().toString();SteamOfflineProfiles.Anchor producer=profile.anchors().get(0);
            var nativeValue=new SteamOfflineObservation.NativeEvidence(plan.machineId(),observed,nonce,Long.toUnsignedString(module.base()),module.size(),
                    Integer.toString(profile.valueRva()),Long.toUnsignedString(module.base()+profile.valueRva()),Integer.toString(producer.rva()),producer.hex(),
                    SteamOfflineObservation.hash(producer.bytes()),List.of(actual.raw(),actual.raw()),steam,steam,sourceBefore,sourceAfter,
                    Integer.toString(profile.managerRva()),Long.toUnsignedString(actual.manager()),"340",List.of(actual.tray(),actual.tray()));
            var common=new SteamOfflineObservation.Common(plan.machineId(),observed,nonce,Optional.of(steam),Optional.of(sourceAfter),Optional.empty(),List.of());
            var value=new SteamOfflineObservation.Offline(common,SteamOfflineObservation.Method.NATIVE_CURRENT_USER_BYTE,Optional.of(nativeValue));
            ControlBuild.FileRef ref=publish(newEvidenceFile,value);
            return new QualifiedOffline(plan,new NativeLease(plan,process,expected,source,sourceAfter,module,profile),value,ref);
        }catch(IOException|RuntimeException failure){try{process.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    private record State(long manager,int raw,int tray){ }
    private static State samples(Win32Host.ReadProcess process,Win32Host.Module module,SteamOfflineProfiles.Profile profile,Instant deadline)throws IOException{
        State first=sample(process,module,profile,deadline),second=sample(process,module,profile,deadline);
        if(!first.equals(second))throw new IOException("Steam mode/tray/manager changed between samples");return first;
    }
    private static State sample(Win32Host.ReadProcess process,Win32Host.Module module,SteamOfflineProfiles.Profile profile,Instant deadline)throws IOException{
        long manager=ByteBuffer.wrap(process.read(module.base()+profile.managerRva(),8,deadline)).order(ByteOrder.LITTLE_ENDIAN).getLong();
        if(manager<0x10000||manager>0x7fff_ffff_ffffL-0x158||(manager&7)!=0)throw new IOException("Invalid current Steam tray manager");
        int raw=Byte.toUnsignedInt(process.read(module.base()+profile.valueRva(),1,deadline)[0]);
        int tray=ByteBuffer.wrap(process.read(manager+0x154,4,deadline)).order(ByteOrder.LITTLE_ENDIAN).getInt();
        requirePositive(raw,tray);return new State(manager,raw,tray);
    }
    static void requirePositive(int raw,int tray)throws IOException{
        if(raw!=1||tray!=4)throw new IOException("Explicit native offline(1,4) required; zero/unknown is not online or offline qualification");
    }
    private static void anchors(Win32Host.ReadProcess process,Win32Host.Module module,SteamOfflineProfiles.Profile profile,Instant deadline)throws IOException{
        for(SteamOfflineProfiles.Anchor anchor:profile.anchors())if(!Arrays.equals(anchor.bytes(),process.read(module.base()+anchor.rva(),anchor.bytes().length,deadline)))throw new IOException("Loaded SteamUI instruction anchor differs");
    }
    static String version(Path path)throws IOException{
        VersionApi api=Native.load("version",VersionApi.class);WString name=new WString(path.toString());
        int size=api.GetFileVersionInfoSizeW(name,new IntByReference());if(size<52||size>1048576)throw Win32Host.failure("file version size");
        try(Memory data=new Memory(size)){
            if(!api.GetFileVersionInfoW(name,0,size,data))throw Win32Host.failure("file version read");
            PointerByReference value=new PointerByReference();IntByReference length=new IntByReference();
            if(!api.VerQueryValueW(data,new WString("\\"),value,length)||length.getValue()<52)throw Win32Host.failure("file version root");
            Pointer p=value.getValue();if(p==null||p.getInt(0)!=0xFEEF04BD)throw new IOException("Invalid file version signature");
            int high=p.getInt(8),low=p.getInt(12);return (high>>>16)+"."+(high&65535)+"."+(low>>>16)+"."+(low&65535);
        }
    }
    static SteamOfflineObservation.SteamProcess processIdentity(WindowsJobProcess.ProcessIdentity identity,String version){
        return new SteamOfflineObservation.SteamProcess(identity.pid(),identity.creationFiletimeDecimal(),identity.executable(),version);
    }
    static SteamOfflineObservation.Source sourceIdentity(SharedSourceFiles.Witness witness)throws IOException{
        var file=witness.source();Instant stamp=Files.getLastModifiedTime(Path.of(file.path()),LinkOption.NOFOLLOW_LINKS).toInstant();
        java.math.BigInteger nanos=java.math.BigInteger.valueOf(stamp.getEpochSecond()).multiply(java.math.BigInteger.valueOf(1000000000L)).add(java.math.BigInteger.valueOf(stamp.getNano()));
        if(nanos.signum()<0||nanos.bitLength()>64)throw new IOException("Steam source timestamp outside original unsigned nanosecond domain");
        return new SteamOfflineObservation.Source(file.path(),file.bytes(),file.sha256(),witness.nativeFile().fileIdDecimal(),nanos.toString());
    }
    static ControlBuild.FileRef publish(Path path,SteamOfflineObservation.Result value)throws IOException{
        byte[] raw=SteamOfflineObservationCodec.encode(value);
        if(!SteamOfflineObservationCodec.decode(raw).equals(value))throw new IOException("Steam observation typed codec roundtrip differs");
        ProjectStoragePolicy.requireBulkOutput(path);SharedSourceFiles.plainAncestors(path.getParent());
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        try(FileChannel channel=FileChannel.open(path,StandardOpenOption.WRITE)){channel.force(true);}
        if(!Arrays.equals(raw,Files.readAllBytes(path)))throw new IOException("Steam observation create/readback differs");
        return ControlBuild.FileRef.measure(path);
    }
    public static void requireReviewedSources(List<ControlBuild.FileRef> accepted)throws IOException{
        for(Class<?> type:List.of(SteamOfflineProbe.class,SteamOfflineProfiles.class,SteamOfflineObservation.class,
                SteamOfflineObservationCodec.class,SteamOfflineCefProvider.class,SteamOfflineCefWire.class,Win32Host.class)){
            try{
                Path location=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
                Path actual=Files.isDirectory(location)?location.resolve(type.getName().replace('.','/')+".class"):location;
                boolean found=false;
                for(var ref:accepted)if(Path.of(ref.path()).toRealPath().equals(actual.toRealPath())){ref.verify();found=true;break;}
                if(!found)throw new IOException("Loaded Steam producer class outside accepted deployment: "+type.getName());
            }catch(java.net.URISyntaxException|NullPointerException failure){throw new IOException("Actual Steam producer code source unavailable",failure);}
        }
    }
    static byte[] randomBytes(int count){byte[] value=new byte[count];new java.security.SecureRandom().nextBytes(value);return value;}
    static String bounded(String value){return value.substring(0,Math.min(2048,value.length()));}
    static void fileAnchors(Path path,SteamOfflineProfiles.Profile profile)throws IOException{
        try(FileChannel channel=FileChannel.open(path,StandardOpenOption.READ)){
            ByteBuffer dos=read(channel,0,64);int pe=dos.getInt(0x3c);
            if(dos.getShort(0)!=0x5a4d||pe<64||pe>1048576)throw new IOException("Invalid DOS/PE offset");
            ByteBuffer header=read(channel,pe,24);int sections=Short.toUnsignedInt(header.getShort(6)),optional=Short.toUnsignedInt(header.getShort(20));
            if(header.getInt(0)!=0x4550||Short.toUnsignedInt(header.getShort(4))!=0x8664||sections<1||sections>32||optional<64||optional>4096)throw new IOException("Qualified x64 SteamUI PE required");
            ByteBuffer opt=read(channel,pe+24,optional);
            if(Short.toUnsignedInt(opt.getShort(0))!=0x20b||opt.getInt(56)!=profile.imageSize())throw new IOException("SteamUI PE image size differs");
            ByteBuffer table=read(channel,(long)pe+24+optional,sections*40);
            for(SteamOfflineProfiles.Anchor anchor:profile.anchors()){
                boolean found=false;byte[] expected=anchor.bytes();
                for(int i=0;i<sections;i++){
                    int offset=i*40;long virtual=Integer.toUnsignedLong(table.getInt(offset+12)),size=Integer.toUnsignedLong(table.getInt(offset+16)),raw=Integer.toUnsignedLong(table.getInt(offset+20));
                    if(virtual<=anchor.rva()&&(long)anchor.rva()+expected.length<=virtual+size){
                        if(!Arrays.equals(expected,read(channel,raw+anchor.rva()-virtual,expected.length).array()))throw new IOException("SteamUI file instruction anchor differs");found=true;break;
                    }
                }
                if(!found)throw new IOException("SteamUI anchor has no raw PE bytes");
            }
        }
    }
    private static ByteBuffer read(FileChannel channel,long offset,int count)throws IOException{
        if(offset<0||count<1||offset>channel.size()-count)throw new IOException("PE bounded read outside source");
        ByteBuffer data=ByteBuffer.allocate(count).order(ByteOrder.LITTLE_ENDIAN);
        while(data.hasRemaining()){int read=channel.read(data,offset+data.position());if(read<=0)throw new IOException("PE source made no read progress");}
        return data.flip();
    }
}
