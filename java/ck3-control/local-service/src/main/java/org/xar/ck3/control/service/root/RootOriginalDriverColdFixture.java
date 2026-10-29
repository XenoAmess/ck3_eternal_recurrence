package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativePrelaunchInputs;

/** One DATA codec for finite original-Driver cold/adoption inputs. No JSON object issues private qualification. */
public final class RootOriginalDriverColdFixture {
    public static final String SCHEMA="xar.java-original-driver-cold-fixture/v2";
    public static final String ADOPTION_SCHEMA="xar.java-original-driver-adoption-fixture/v1";
    public static final String COLD_PROPERTY="xar.original.driver.cold.fixture";
    public static final String ADOPTION_PROPERTY="xar.original.driver.adoption.fixture";
    public static final int MAXIMUM_BYTES=65536;
    private RootOriginalDriverColdFixture() { }

    public record Fixture(String schema,String machineId,List<Case> cases) {
        public Fixture {
            require(SCHEMA.equals(schema),"exact cold v2 schema required; v1 is not a fixed-writer input");
            machine(machineId);cases=List.copyOf(cases);require(!cases.isEmpty()&&cases.size()<=16,"finite nonempty cold cases required");
            require(cases.stream().map(Case::name).distinct().count()==cases.size(),"distinct cold case names required");
        }
    }
    public record Case(String name,ExactRef launchPlan,ExactRef runRequest,ExactRef episodePolicy,ExactRef storageLease,
            RootOriginalDriverJournal.Status expectedStatus,String expectedFullPayloadSha256,Integer expectedHistoryRows,Control control) {
        public Case {
            RootOriginalDriverColdFixture.name(name);reference(launchPlan,1<<20);reference(runRequest,MAXIMUM_BYTES);reference(episodePolicy,1<<20);reference(storageLease,1<<20);
            Objects.requireNonNull(expectedStatus);Objects.requireNonNull(control);
            boolean available=switch(expectedStatus){case BASE_ONLY,ALREADY_CONSOLIDATED,REPLAYED->true;case MISSING,JOURNAL_INVALID->false;};
            require(available==(expectedFullPayloadSha256!=null)&&available==(expectedHistoryRows!=null),"actual available payload requires both digest and history count");
            if(available){digest(expectedFullPayloadSha256);require(expectedHistoryRows>=0,"nonnegative actual history count required");}
        }
    }
    /** Existing persistent software writer, prepared before its signed complete storage census. */
    public record Control(Path snapshotPath,ExactRef anchorRef,List<ExactRef> sourceRefs,String expectedHeadDigest) {
        public Control {
            absolute(snapshotPath);reference(anchorRef,1<<20);sourceRefs=List.copyOf(sourceRefs);digest(expectedHeadDigest);
            require(!sourceRefs.isEmpty()&&sourceRefs.size()<=64&&sourceRefs.stream().distinct().count()==sourceRefs.size(),"finite exact trusted writer source closure required");
            for(var source:sourceRefs)reference(source,WriterContracts.MAX_PIN_BYTES);
        }
        private ContinuityWriter openReadOnlyWriter(String machineId,Clock clock,RootRuntimeStorageGuard storage)throws IOException {
            machine(machineId);Objects.requireNonNull(clock);
            if(!WindowsJobProcess.currentMachineId().equals(machineId))throw new IOException("readonly control belongs to another machine");
            SharedSourceFiles.plainAncestors(snapshotPath);new ControlBuild.FileRef(anchorRef.path(),anchorRef.bytes(),anchorRef.sha256()).verify();
            var layout=new WriterContracts.Layout(snapshotPath,anchorRef,machineId);
            for(Path file:List.of(snapshotPath,Path.of(anchorRef.path()),layout.lock()))
                if(!Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS))throw new IOException("fixed control file is missing or not regular: "+file);
            if(!Files.isDirectory(layout.events(),LinkOption.NOFOLLOW_LINKS))throw new IOException("fixed readonly control events directory is missing");
            var implementation=codeSource(ReadOnlyAuthority.class);
            require(sourceRefs.stream().anyMatch(source->sameReference(source,implementation)),"readonly writer source closure must pin its actually loaded authority");
            for(var source:sourceRefs)new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256()).verify();
            storage.requireExistingAllocationOwner(layout.lock());
            var writer=new ContinuityWriter(layout,sourceRefs,new ReadOnlyAuthority(),clock,storage);
            writer.locked(same->{if(!expectedHeadDigest.equals(same.head().digest()))throw new IOException("fixed readonly control head differs from its original input");return null;});
            return writer;
        }
    }
    /** One actual pre-writer storage admission and its identical readonly writer/file port. Closing releases ownership only. */
    public static final class ReadOnlyScope implements AutoCloseable {
        private final ContinuityWriter writer;private final RootRuntimeStorageGuard storage;
        private final org.xar.ck3.control.application.checkpoint.CheckpointFiles files;
        private ReadOnlyScope(ContinuityWriter writer,RootRuntimeStorageGuard storage,
                org.xar.ck3.control.application.checkpoint.CheckpointFiles files){this.writer=writer;this.storage=storage;this.files=files;}
        public ContinuityWriter writer(){return writer;}
        public RootRuntimeStorageGuard storage(){return storage;}
        public org.xar.ck3.control.application.checkpoint.CheckpointFiles files(){return files;}
        @Override public void close()throws IOException {storage.close();}
    }
    public static ReadOnlyScope openReadOnlyScope(Control control,ExactRef storageLease,String machine,Clock clock)throws IOException {
        Objects.requireNonNull(control);Objects.requireNonNull(clock);
        var lease=record(storageLease,1<<20,RootRuntimeDefinitionModel.StorageLease.class);
        var actualWriter=new java.util.concurrent.atomic.AtomicReference<ContinuityWriter>();
        var storage=RootRuntimeStorageGuard.readExact(lease,machine,()->{
            var known=actualWriter.get();if(known==null)throw new IOException("actual readonly writer has not yet been constructed");return known;
        },clock);
        try {
            var writer=control.openReadOnlyWriter(machine,clock,storage);actualWriter.set(writer);
            var files=storage.checkpointFiles(new org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles());
            return new ReadOnlyScope(writer,storage,files);
        }catch(IOException|RuntimeException|Error rejected){
            try{storage.close();}catch(IOException close){rejected.addSuppressed(close);}throw rejected;
        }
    }
    private static final class ReadOnlyAuthority implements WriterContracts.TransitionAuthority {
        @Override public String revalidate(ContinuityState before,WriterContracts.Request request)throws IOException {
            throw new IOException("original Driver fixture reader has no transition authority");
        }
        @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request)throws IOException {
            throw new IOException("original Driver fixture reader cannot create a transition");
        }
    }
    public record AdoptionFixture(String schema,String machineId,List<Expected> cases) {
        public AdoptionFixture {
            require(ADOPTION_SCHEMA.equals(schema),"exact adoption fixture schema required");machine(machineId);cases=List.copyOf(cases);
            require(!cases.isEmpty()&&cases.size()<=32,"finite adoption cases required");
            var reasons=EnumSet.noneOf(AdoptionRefusalReason.class);int positive=0;
            for(var value:cases)if(value.expectedReason()==null)positive++;else reasons.add(value.expectedReason());
            require(positive>0&&reasons.equals(EnumSet.allOf(AdoptionRefusalReason.class)),"all original refusal kinds and a positive DATA case are mandatory");
            require(cases.stream().map(Expected::caseName).distinct().count()==cases.size(),"distinct adoption case names required");
        }
    }
    public record Expected(String caseName,ExactRef originalFramedHello,long gamePid,String gameCreationFiletime,AdoptionRefusalReason expectedReason) {
        public Expected {
            name(caseName);reference(originalFramedHello,1<<20);require(gamePid>0&&gamePid<=0xffff_ffffL,"exact positive Game PID required");
            var birth=new CrossJsDecimalUInt64(gameCreationFiletime);require(!birth.decimal().equals("0"),"positive canonical Game birth required");
        }
    }
    public static Fixture readRequiredSystemProperties()throws IOException {
        return readExact(requiredReference(COLD_PROPERTY),Fixture.class);
    }
    public static AdoptionFixture readAdoptionRequiredSystemProperties()throws IOException {
        return readExact(requiredReference(ADOPTION_PROPERTY),AdoptionFixture.class);
    }
    public static Fixture readExact(ExactRef source)throws IOException {return readExact(source,Fixture.class);}
    public static byte[] encode(Fixture fixture)throws IOException {
        Objects.requireNonNull(fixture);byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(fixture);
        StrictJson.parse(raw,MAXIMUM_BYTES);return raw;
    }
    static <T>T readExact(ExactRef source,Class<T> type)throws IOException {
        return record(source,MAXIMUM_BYTES,type);
    }
    static <T>T record(ExactRef source,int maximum,Class<T> type)throws IOException {
        Objects.requireNonNull(type);reference(source,maximum);
        var original=SharedSourceFiles.observe(Path.of(source.path()));
        new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256()).verify();
        byte[] raw;try(var input=Files.newInputStream(Path.of(source.path()))){raw=input.readNBytes(maximum+1);}
        if(raw.length!=source.bytes()||!OriginalDriverJournal.sha256(raw).equals(source.sha256()))throw new IOException("exact fixture input changed during complete read");
        StrictJson.parse(raw,maximum);
        try {var parsed=ControlBuild.strictMapper().readValue(raw,type);SharedSourceFiles.assertUnchanged(original);return parsed;}
        catch(IllegalArgumentException invalid){throw new IOException("strict fixture record contract rejected",invalid);}
    }
    public static void requirePrelaunch(NativeLaunchPlan actual,Clock clock)throws IOException {
        NativePrelaunchInputs.requireCurrent(actual,clock);
        for(Class<?> type:reviewedClasses())actual.sources().requireLoadedClass(type);
    }
    public static List<ExactRef> requiredWriterSources(NativeLaunchPlan actual)throws IOException {
        var sources=new ArrayList<ExactRef>();
        for(Class<?> type:reviewedClasses()){actual.sources().requireLoadedClass(type);var source=codeSource(type);if(!sources.contains(source))sources.add(source);}
        return List.copyOf(sources);
    }
    public static void requireStorage(NativeLaunchPlan actual,Control control,RootRuntimeStorageGuard storage)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(control);Objects.requireNonNull(storage);
        storage.requireManagedRoots(List.of(actual.stateDirectory(),control.snapshotPath().getParent()));
        storage.requireCompleteAdmission();
    }
    static ExactRef codeSource(Class<?> type)throws IOException {
        try{
            Path location=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path file=Files.isDirectory(location)?location.resolve(type.getName().replace('.','/')+".class"):location;
            var source=ControlBuild.FileRef.measure(file);return new ExactRef(source.path(),source.bytes(),source.sha256());
        }catch(java.net.URISyntaxException|NullPointerException unavailable){throw new IOException("actual fixture class source unavailable",unavailable);}
    }
    private static List<Class<?>> reviewedClasses(){return List.of(RootOriginalDriverColdFixture.class,ReadOnlyAuthority.class,ReadOnlyScope.class,
            RootOriginalDriverColdFixtureProducer.class,RootOriginalDriverJournal.class,RootFrozenRunProfile.class,
            RootRuntimeStorageGuard.class,InitialEpisodePolicy.class,ContinuityWriter.class,NativePrelaunchInputs.class);}
    static ExactRef requiredReference(String property)throws IOException {
        String path=System.getProperty(property),bytes=System.getProperty(property+".bytes"),sha=System.getProperty(property+".sha256");
        if(path==null||bytes==null||sha==null)throw new IOException("NOT_RUN: complete mandatory fixture path/bytes/sha256 properties missing: "+property);
        if(!bytes.matches("[1-9][0-9]{0,5}"))throw new IOException("canonical bounded fixture byte count required");
        try{var source=new ExactRef(path,Long.parseLong(bytes),sha);reference(source,MAXIMUM_BYTES);return source;}
        catch(IllegalArgumentException invalid){throw new IOException("strict fixture reference rejected",invalid);}
    }
    static boolean sameReference(ExactRef left,ExactRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equals(right.sha256());}
    static void reference(ExactRef source,long maximum){Objects.requireNonNull(source);absolute(Path.of(source.path()));require(source.bytes()>0&&source.bytes()<=maximum,"bounded nonempty exact source required");}
    static void absolute(Path path){require(path!=null&&path.isAbsolute()&&path.normalize().equals(path),"absolute normalized source path required");}
    private static void machine(String value){require(value!=null&&value.matches("[a-z0-9][a-z0-9-]{0,127}")&&!value.equals("unknown"),"actual machine ID required");}
    private static void name(String value){require(value!=null&&value.matches("[A-Za-z0-9_-]{1,64}"),"bounded exact case name required");}
    private static void digest(String value){require(value!=null&&value.matches("[a-f0-9]{64}"),"exact SHA256 digest required");}
    private static void require(boolean valid,String detail){if(!valid)throw new IllegalArgumentException(detail);}
}
