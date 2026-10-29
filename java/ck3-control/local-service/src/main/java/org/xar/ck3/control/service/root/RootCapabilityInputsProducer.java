package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.Kind;

/** First DATA08/09 publication, through the existing immutable output authority. FRESH_NEW_EPISODE
 * selects the startup configuration consumed by InitialDriverBootstrap; it does not mint an episode
 * binding, Driver state, capability cache or native observation. The original first-frame initializer
 * must still prove its real fresh Driver/native branch before it mints ACTIVE_NEW runtime facts. */
public final class RootCapabilityInputsProducer {
    public static final String SCHEMA="xar.java-root-capability-inputs-request/v1";
    public static final int MAXIMUM_BYTES=1<<20;
    private RootCapabilityInputsProducer(){ }
    public enum InitialBinding { FRESH_NEW_EPISODE }
    public record Configuration(String stateDirectory,String saveDirectory,int routeContactTimelineSpeed,
            int routeContactEffectiveTimelineSpeed,boolean allowRouteContactHighSpeedAb,
            boolean stationaryObjectiveHoldCanaryRequested) {
        public Configuration {
            absolute(stateDirectory);absolute(saveDirectory);
            new DynamicCapabilities.Configuration(Optional.of(Path.of(stateDirectory)),Optional.of(Path.of(saveDirectory)),
                    routeContactTimelineSpeed,routeContactEffectiveTimelineSpeed,allowRouteContactHighSpeedAb,
                    stationaryObjectiveHoldCanaryRequested);
        }
        public DynamicCapabilities.Configuration value(){
            return new DynamicCapabilities.Configuration(Optional.of(Path.of(stateDirectory)),Optional.of(Path.of(saveDirectory)),
                    routeContactTimelineSpeed,routeContactEffectiveTimelineSpeed,allowRouteContactHighSpeedAb,
                    stationaryObjectiveHoldCanaryRequested);
        }
    }
    public record FreshSession(InitialBinding initialBinding,String queueDirectory,String driverStatePath) {
        public FreshSession {
            require(initialBinding==InitialBinding.FRESH_NEW_EPISODE,"explicit first new-episode configuration required");
            absolute(queueDirectory);absolute(driverStatePath);
            require(Path.of(driverStatePath).getParent()!=null,"actual Driver state parent required");
        }
        public CapabilitySessionPresentation value(){
            // These are the fixed fresh-start branch parameters required by initializeNewEpisode,
            // rather than observations of a running Game or a claim that the new cache already exists.
            return new CapabilitySessionPresentation(false,Optional.empty(),
                    Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),
                    Optional.of(Path.of(queueDirectory)),Optional.of(Path.of(driverStatePath)));
        }
    }
    public record Request(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            RootJavaBootstrapInputs.Mode mode,FileRef bindingRef,String outputRoot,
            Configuration configuration,FreshSession session) {
        public Request {
            require(SCHEMA.equals(schema),"exact initial capability request schema required");
            RootRuntimeDefinitionModel.machine(machineId);absolute(outputRoot);Objects.requireNonNull(mode);
            Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,
                    "finite reviewed actual capability request required");
            require((mode==RootJavaBootstrapInputs.Mode.CREATE_NEW)==(bindingRef!=null),
                    "only actual CREATE_NEW has an independent output binding");
            Objects.requireNonNull(configuration);Objects.requireNonNull(session);
            session.value().validateConfiguration(configuration.value());
            Path output=Path.of(outputRoot);
            for(Path directory:directories(configuration,session))
                require(!directory.startsWith(output),"configured path custody cannot be hidden in the priced output root");
            require(!Path.of(session.driverStatePath()).startsWith(output),"Driver state cannot be an immutable configuration output");
        }
    }
    public static byte[] encodeRequest(Request request)throws IOException {
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(Objects.requireNonNull(request)),MAXIMUM_BYTES);
    }
    public static Request decodeRequest(byte[] original)throws IOException {
        try{
            var node=StrictJson.parse(original,MAXIMUM_BYTES);
            require(node.isObject()&&node.has("binding_ref"),"explicit nullable binding_ref is required");
            return ControlBuild.strictMapper().readValue(original,Request.class);
        }catch(IllegalArgumentException invalid){throw new IOException("invalid strict initial capability request",invalid);}
    }
    public static List<RootJavaBootstrapInputs.PreparedFile> encodeFiles(Request request)throws IOException {
        Objects.requireNonNull(request);Path output=Path.of(request.outputRoot());
        byte[] configuration=encodeConfiguration(request.configuration().value());
        byte[] session=encodeSession(request.session().value());
        var decoded=DynamicCapabilities.decodeConfiguration(DriverJson.object(configuration,MAXIMUM_BYTES));
        var presented=CapabilitySessionPresentation.decode(DriverJson.object(session,MAXIMUM_BYTES));
        presented.validateConfiguration(decoded);
        require(decoded.equals(request.configuration().value())&&presented.equals(request.session().value()),
                "the actual existing capability codecs must round trip unchanged");
        return List.of(new RootJavaBootstrapInputs.PreparedFile(Kind.CAPABILITY_CONFIGURATION,
                        output.resolve("capability-configuration.json").toString(),configuration),
                new RootJavaBootstrapInputs.PreparedFile(Kind.CAPABILITY_SESSION_PRESENTATION,
                        output.resolve("capability-session-presentation.json").toString(),session));
    }
    /** Canonical JSON order is stable across the independent QUOTE and CREATE_NEW JVMs. */
    public static byte[] encodeConfiguration(DynamicCapabilities.Configuration actual){
        return StrictJson.canonical(DriverJson.toNode(DynamicCapabilities.encodeConfiguration(actual),MAXIMUM_BYTES),MAXIMUM_BYTES);
    }
    public static byte[] encodeSession(CapabilitySessionPresentation actual){
        return StrictJson.canonical(DriverJson.toNode(Objects.requireNonNull(actual).original(),MAXIMUM_BYTES),MAXIMUM_BYTES);
    }
    private record Directory(Path path,SharedSourceFiles.DirectoryIdentity identity) { }
    public static Prepared prepare(FileRef original,Clock clock)throws IOException {
        Objects.requireNonNull(original);absolute(original.path());
        if(original.bytes()<=0||original.bytes()>MAXIMUM_BYTES||!original.sha256().matches("[0-9a-f]{64}"))
            throw new IOException("bounded exact capability request original required");
        var witness=SharedSourceFiles.observe(Path.of(original.path()));
        if(!witness.source().equals(original))throw new IOException("initial capability request exact identity differs");
        byte[] raw;try(var input=Files.newInputStream(Path.of(original.path()))){raw=input.readNBytes(MAXIMUM_BYTES+1);}
        if(raw.length!=original.bytes()||!DriverJson.sha256(raw).equals(original.sha256()))throw new IOException("initial capability request changed during complete read");
        SharedSourceFiles.assertUnchanged(witness);Request request=decodeRequest(raw);
        if(Path.of(original.path()).startsWith(Path.of(request.outputRoot())))
            throw new IOException("capability request must remain outside its priced immutable output root");
        return prepare(request,clock,List.of(witness));
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException {
        return prepare(request,clock,List.of());
    }
    private static Prepared prepare(Request request,Clock clock,List<SharedSourceFiles.Witness> originals)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(clock);current(request,clock);
        var captured=new ArrayList<Directory>();
        for(Path path:directories(request.configuration(),request.session())){
            SharedSourceFiles.plainAncestors(path);captured.add(new Directory(path,SharedSourceFiles.nativeDirectory(path)));
        }
        requireAbsent(Path.of(request.session().driverStatePath()));
        var result=new Prepared(request,encodeFiles(request),captured,originals,clock);result.requireCurrent();return result;
    }
    public static final class Prepared {
        private final Request request;private final List<RootJavaBootstrapInputs.PreparedFile> files;
        private final List<Directory> directories;private final List<SharedSourceFiles.Witness> originals;
        private final Clock clock;private boolean attempted;
        private Prepared(Request request,List<RootJavaBootstrapInputs.PreparedFile> files,List<Directory> directories,List<SharedSourceFiles.Witness> originals,Clock clock){
            this.request=request;this.files=List.copyOf(files);this.directories=List.copyOf(directories);this.originals=List.copyOf(originals);this.clock=clock;
        }
        public Request request(){return request;}
        public List<RootJavaBootstrapInputs.PreparedFile> files(){return files;}
        public List<RootBootstrapOutputContract.Output> quote()throws IOException {
            requireCurrent();return files.stream().map(RootJavaBootstrapInputs.PreparedFile::output).toList();
        }
        public void requireCurrent()throws IOException {
            current(request,clock);
            for(var original:originals)SharedSourceFiles.assertUnchanged(original);
            for(var directory:directories){
                SharedSourceFiles.plainAncestors(directory.path());
                if(!directory.identity().equals(SharedSourceFiles.nativeDirectory(directory.path())))
                    throw new IOException("actual initial capability directory custody changed");
            }
            requireAbsent(Path.of(request.session().driverStatePath()));
        }
        public synchronized List<RootJavaBootstrapInputs.Created> createNew(Clock actualClock)throws IOException {
            if(attempted)throw new IOException("initial capability publication already attempted; unknown writes cannot replay");
            if(request.mode()!=RootJavaBootstrapInputs.Mode.CREATE_NEW)throw new IOException("QUOTE does not grant a write");
            requireCurrent();current(request,actualClock);var outputs=quote();
            try(var authority=RootBootstrapOutputGuard.readExact(request.bindingRef(),actualClock)){
                authority.requirePlan(Path.of(request.outputRoot()),outputs,List.of(),List.of());
                var targets=files.stream().map(row->Path.of(row.target())).toList();authority.requireTargets(targets);
                var same=authority.files();attempted=true;var created=new ArrayList<RootJavaBootstrapInputs.Created>();
                for(var file:files){
                    requireCurrent();current(request,actualClock);var actual=same.createNew(Path.of(file.target()),file.bytes());same.verify(actual);
                    if(!actual.reference().equals(exact(file.expected()))||!Arrays.equals(file.bytes(),same.read(actual,MAXIMUM_BYTES)))
                        throw new IOException("initial capability immutable output differs from its sole codec");
                    var nativeBefore=SharedSourceFiles.nativeFile(Path.of(file.target()));
                    var witness=SharedSourceFiles.observe(Path.of(file.target()));
                    if(!witness.source().equals(file.expected())||!nativeBefore.equals(witness.nativeFile()))
                        throw new IOException("initial capability output identity changed during readback");
                    SharedSourceFiles.assertUnchanged(witness);same.verify(actual);
                    created.add(new RootJavaBootstrapInputs.Created(file.kind(),witness.source(),witness.nativeFile()));
                }
                requireCurrent();current(request,actualClock);authority.requireTargets(targets);
                if(authority.files()!=same||authority.accounting().completedOutputs()!=files.size())
                    throw new IOException("initial capability output authority or complete inventory differs");
                return List.copyOf(created);
            }
        }
    }
    private static List<Path> directories(Configuration configuration,FreshSession session){
        return List.of(Path.of(configuration.stateDirectory()),Path.of(configuration.saveDirectory()),
                Path.of(session.queueDirectory()),Path.of(session.driverStatePath()).getParent()).stream().distinct().toList();
    }
    private static void requireAbsent(Path driver)throws IOException {
        SharedSourceFiles.plainAncestors(driver);
        try{Files.readAttributes(driver,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);}
        catch(NoSuchFileException absent){return;}
        throw new IOException("explicit fresh capability initialization cannot adopt an existing Driver state path");
    }
    private static void current(Request request,Clock clock)throws IOException {
        Instant now=Objects.requireNonNull(clock).instant();
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||now.isBefore(instant(request.observedAtUtc()))
                ||!now.isBefore(instant(request.reviewAtUtc())))throw new IOException("initial capability request is foreign, future or expired");
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void absolute(String raw){
        Path path=Path.of(Objects.requireNonNull(raw));require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized actual configuration path required");
    }
    private static Instant instant(String raw){
        Instant value=Instant.parse(raw);require(value.toString().equals(raw),"canonical UTC request time required");return value;
    }
}
