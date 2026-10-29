package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileManifest.Asset;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.FormalReleaseProducer;
import org.xar.ck3.control.build.FormalReleaseGit;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NormalExitSourceInventory;

/** Actual profile business producers feed the one finite CREATE_NEW authority. No Native/Game authority is issued. */
public final class RootProfileBootstrapInputs {
    private RootProfileBootstrapInputs(){ }
    @FunctionalInterface private interface Current { void verify()throws IOException; }
    private record Body(Kind kind,Path target,byte[] bytes) {
        private Body {Objects.requireNonNull(kind);Objects.requireNonNull(target);bytes=bytes.clone();}
        @Override public byte[] bytes(){return bytes.clone();}
        Output output(Path root){return new Output(kind,root.relativize(target).toString().replace('\\','/'),bytes.length,DriverJson.sha256(bytes));}
    }
    public record Created(Kind kind,FileRef original,SharedSourceFiles.NativeFile nativeFile) {
        public Created {Objects.requireNonNull(kind);Objects.requireNonNull(original);Objects.requireNonNull(nativeFile);}
        public ExactRef exact(){return new ExactRef(original.path(),original.bytes(),original.sha256());}
    }
    public static final class Prepared {
        private final Path root;private final List<Body> writes;private final List<Output> allOutputs;
        private final List<String> directories;private final List<RetainedInput> retained;private final Current current,beforeWrite,afterReadback;
        private Prepared(Path root,List<Body> writes,List<Output> existing,List<String> directories,List<RetainedInput> retained,Current current){
            this(root,writes,existing,directories,retained,current,current,current);
        }
        private Prepared(Path root,List<Body> writes,List<Output> existing,List<String> directories,List<RetainedInput> retained,Current current,Current beforeWrite,Current afterReadback){
            this.root=root;this.writes=List.copyOf(writes);this.directories=List.copyOf(directories);this.retained=List.copyOf(retained);
            this.current=current;this.beforeWrite=beforeWrite;this.afterReadback=afterReadback;
            var outputs=new ArrayList<>(existing);for(var write:writes)outputs.add(write.output(root));allOutputs=List.copyOf(outputs);
        }
        public Path assetRoot(){return root;}public List<Output> quote(){return allOutputs;}
        public List<String> outputDirectories(){return directories;}public List<RetainedInput> retainedInputs(){return retained;}
        public Branch branch(){return allOutputs.stream().anyMatch(output->output.kind()==Kind.FORMAL_RELEASE_PAYLOAD)?Branch.FORMAL_RELEASE:Branch.IMMUTABLE_INPUTS;}
        public FormalReleaseProducer.Layout formalLayout()throws IOException {
            if(branch()!=Branch.FORMAL_RELEASE)throw new IOException("formal layout requires the actual formal preparation");
            return RootBootstrapOutputContract.formalLayout(allOutputs);
        }
        public long formalAssetPeakUpperBytes()throws IOException {
            if(branch()!=Branch.FORMAL_RELEASE)throw new IOException("formal quote requires the actual formal preparation");
            current.verify();long peak=Math.multiplyExact(RootBootstrapAssetTree.directoryQuote(root),directories.size()+1L);
            for(Output output:allOutputs)peak=Math.addExact(peak,RootBootstrapOutputGuard.fileQuote(output.bytes(),root));
            if(peak>FORMAL_MAXIMUM_ASSET_BYTES)throw new IOException("actual complete formal payload exceeds its explicit branch ceiling");
            current.verify();return peak;
        }
        public List<Created> createNew(RootBootstrapOutputGuard authority)throws IOException {
            Objects.requireNonNull(authority);current.verify();authority.requirePlan(root,allOutputs,directories,retained);beforeWrite.verify();
            authority.createOutputDirectories();authority.requireTargets(writes.stream().map(Body::target).toList());
            var files=authority.files();var result=new ArrayList<Created>();
            for(var body:writes){current.verify();FileWitness written=files.createNew(body.target(),body.bytes());files.verify(written);
                if(!Arrays.equals(body.bytes(),files.read(written,Math.max(1<<20,body.bytes().length))))throw new IOException("actual staged bootstrap producer/readback changed");
                var ref=written.reference();var observed=SharedSourceFiles.observe(body.target());
                if(!observed.source().equals(new FileRef(ref.path(),ref.bytes(),ref.sha256())))throw new IOException("staged output exact source changed");
                result.add(new Created(body.kind(),observed.source(),observed.nativeFile()));
            }
            current.verify();authority.requireTargets(writes.stream().map(Body::target).toList());
            if(authority.files()!=files)throw new IOException("staged bootstrap changed its one actual file producer");
            afterReadback.verify();current.verify();return List.copyOf(result);
        }
    }
    /** The private pure release preparation supplies every body; the existing Guard owns all physical writes. */
    public static Prepared formalRelease(FormalReleaseProducer.Prepared actual)throws IOException {
        Objects.requireNonNull(actual);actual.verifyOriginals();Path root=actual.outputRoot();
        var bodies=actual.payload().stream().map(file->new Body(switch(file.role()){
            case PRODUCTION_FILE->Kind.FORMAL_RELEASE_PAYLOAD;case MANIFEST->Kind.FORMAL_RELEASE_MANIFEST;},file.target(),file.bytes())).toList();
        var outputs=bodies.stream().map(body->body.output(root)).toList();formalPlan(outputs,actual.outputDirectories());
        if(RootBootstrapOutputContract.formalLayout(outputs)!=actual.request().layout())throw new IOException("formal payload paths differ from their sole explicit producer layout");
        actual.verifyOriginals();
        return new Prepared(root,bodies,List.of(),actual.outputDirectories(),List.of(),actual::verifyOriginals,
                ()->{actual.verifyOriginals();verifyGit(actual,FormalReleaseGit.Phase.BEFORE_WRITE);actual.verifyOriginals();},
                ()->{actual.verifyCreatedPayload();verifyGit(actual,FormalReleaseGit.Phase.AFTER_READBACK);actual.verifyOriginals();});
    }
    private static void verifyGit(FormalReleaseProducer.Prepared actual,FormalReleaseGit.Phase phase)throws IOException {
        try{actual.verifyGitCurrent(phase);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("formal Git phase interrupted; no successful stage completion",interrupted);}
    }
    public static Prepared productionInventory(NativeRunProfileProducer.Prepared actual,Path target)throws IOException {
        Objects.requireNonNull(actual);actual.verifyOriginals();
        return flat(Kind.PROFILE_PRODUCTION_INVENTORY,target,NativeRunProfileProducer.encodeProductionTree(actual.productionTree()),actual::verifyOriginals);
    }
    /** The sole typed initial-driver producer supplies bytes; the existing Body/Guard performs the only write. */
    public static Prepared originalDriverRunProfile(RootOriginalDriverRunProfileProducer.Prepared actual)throws IOException {
        Objects.requireNonNull(actual);actual.verifyOriginals();Path target=actual.target();
        var body=new Body(Kind.ORIGINAL_DRIVER_RUN_PROFILE,target,actual.bytes());
        return new Prepared(target.getParent(),List.of(body),List.of(),List.of(),List.of(),actual::verifyOriginals,
                actual::verifyOriginals,actual::verifyCreated);
    }
    public static Prepared assets(NativeRunProfileProducer.Prepared actual,FileRef productionInventory)throws IOException {
        actual.verifyOriginals();Path root=actual.request().profile();RetainedInput retained=retained(actual,productionInventory);
        var bodies=actual.assets().stream().map(asset->new Body(kind(asset.kind()),Path.of(asset.target()),asset.bytes())).toList();
        return new Prepared(root,bodies,List.of(),profileDirectories(),List.of(retained),actual::verifyOriginals);
    }
    /** All five first-stage files are actually reopened before the environment can be encoded or quoted. */
    public static Prepared environment(NativeRunProfileProducer.Prepared actual,FileRef productionInventory,Clock clock)throws IOException {
        actual.verifyOriginals();var assets=new ArrayList<Asset>();var existing=new ArrayList<Output>();Path root=actual.request().profile();
        for(var planned:actual.assets()){
            var witness=SharedSourceFiles.observe(Path.of(planned.target()));
            if(!witness.source().equals(planned.expected()))throw new IOException("actual first-stage profile file differs from its sole producer");
            assets.add(new Asset(planned.kind(),witness.source(),witness.nativeFile()));existing.add(new Body(kind(planned.kind()),Path.of(planned.target()),planned.bytes()).output(root));
        }
        var manifest=NativeRunProfileProducer.finish(actual,assets,clock);
        byte[] bytes=NativeRunProfileManifest.encode(manifest);var body=new Body(Kind.PROFILE_ENVIRONMENT,root.resolve(NativeRunProfileProducer.ENVIRONMENT_NAME),bytes);
        return new Prepared(root,List.of(body),existing,profileDirectories(),List.of(retained(actual,productionInventory)),actual::verifyOriginals);
    }
    /** Existing explicit profiles stay immutable inputs; only ENV is written in a disjoint admitted output root. */
    public static Prepared explicitEnvironment(NativeRunProfileProducer.PreparedExplicit actual,FileRef producerRequest,Path target,Clock clock)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(clock);var held=pins(List.of(Objects.requireNonNull(producerRequest)));
        if(!NativeRunProfileProducer.readExplicitRequest(producerRequest).equals(actual.request()))
            throw new IOException("exact explicit producer request differs from the identical private preparation");
        held.verify();actual.verifyOriginals();
        requireExplicitEnvironmentTarget(actual.request(),actual.productionRoots(),target);
        var manifest=NativeRunProfileProducer.finishExplicit(actual,clock);
        byte[] bytes=NativeRunProfileManifest.encodeEnvironment(manifest);
        Clock observed=Clock.fixed(java.time.Instant.parse(manifest.observedAtUtc()),java.time.ZoneOffset.UTC);
        held.verify();actual.verifyOriginals();
        return flat(Kind.PROFILE_ENVIRONMENT,target,bytes,()->{
            held.verify();actual.verifyOriginals();
            if(!Arrays.equals(bytes,NativeRunProfileManifest.encodeEnvironment(NativeRunProfileProducer.finishExplicit(actual,observed))))
                throw new IOException("explicit profile producer changed before immutable ENV publication");
            held.verify();actual.verifyOriginals();
        });
    }
    static void requireExplicitEnvironmentTarget(NativeRunProfileManifest.ExplicitRequest request,List<String> productionRoots,Path target)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(productionRoots);
        if(target==null||!target.isAbsolute()||!target.normalize().equals(target)||target.getParent()==null
                ||!target.getFileName().toString().equals(NativeRunProfileProducer.ENVIRONMENT_NAME))
            throw new IOException("explicit ENV requires its fixed filename in a normalized absolute output root");
        Path root=target.getParent();
        var inputs=new ArrayList<Path>();inputs.add(request.profile());
        for(String production:productionRoots)inputs.add(Path.of(production));
        for(Path input:inputs)if(root.startsWith(input)||input.startsWith(root))
            throw new IOException("explicit ENV output root must be disjoint from every actual profile/product input");
    }
    /** The original planned settings are copied before Game launch to the Native contract's fixed immutable location. */
    public static Prepared originalSettings(ExactRef actualNativePlan)throws IOException {
        var plan=NativeLaunchPlan.readExact(actualNativePlan,new NativeBridgeLaunchEvidence());
        Path live=plan.profileDirectory().resolve("pdx_settings.txt").toRealPath();
        var selected=plan.preparedProfile().preparedInputs().stream().filter(ref->Path.of(ref.path()).toAbsolutePath().normalize().equals(live)).toList();
        if(selected.size()!=1)throw new IOException("one actual original planned settings input required");
        FileRef original=selected.getFirst();byte[] bytes=RootRuntimeDefinitions.read(original,1<<20);
        var current=pins(List.of(file(actualNativePlan),original));
        return flat(Kind.ORIGINAL_SETTINGS_SNAPSHOT,plan.evidenceRoot().resolve(NormalExitSourceInventory.JAVA_SETTINGS_RELATIVE),bytes,current);
    }
    /** Private projection stays in this actual process across the finite quote -> issuer -> CREATE_NEW phases. */
    public static final class NormalExitPrepared {
        private final NativeLaunchPlan plan;private final ExactRef snapshot;private final Path guardTarget;
        private final NormalExitSourceInventory.Projection projection;private final Current current;
        private NormalExitPrepared(NativeLaunchPlan plan,ExactRef snapshot,Path guardTarget,NormalExitSourceInventory.Projection projection,Current current){
            this.plan=plan;this.snapshot=snapshot;this.guardTarget=guardTarget;this.projection=projection;this.current=current;}
        public Prepared targetBinding()throws IOException {current.verify();return flat(Kind.NORMAL_EXIT_TARGET_BINDING,guardTarget,projection.guard().bytes(),current);}
        public Prepared inventory(Created actualGuard,FileRef productionInventory,Path stockGameRoot)throws IOException {
            current.verify();requireKind(actualGuard,Kind.NORMAL_EXIT_TARGET_BINDING);
            RawJson profile=projection.managedProfile(actualGuard.exact());
            var built=NormalExitSourceInventory.build(profile,stockGameRoot);var inputs=pins(built.originals().stream().map(RootProfileBootstrapInputs::file).toList());
            var manifest=NativeRunProfileProducer.readVerified(plan.preparedProfile().environmentManifest());
            Path root=plan.profileDirectory();var bodies=List.of(
                    new Body(Kind.NORMAL_EXIT_SOURCE_INVENTORY,root.resolve(NormalExitSourceInventory.BASENAME),built.inventory().bytes()),
                    new Body(Kind.NORMAL_EXIT_PROFILE_PROJECTION,root.resolve(NormalExitSourceInventory.PROJECTION_BASENAME),built.profileProjection().bytes()));
            return new Prepared(root,bodies,existingProfile(manifest,plan.preparedProfile().environmentManifest()),profileDirectories(),
                    List.of(retained(manifest,productionInventory)),()->{current.verify();inputs.verify();});
        }
        public Prepared managedProfile(Created actualGuard,Created actualInventory,Path newTarget)throws IOException {
            current.verify();requireKind(actualGuard,Kind.NORMAL_EXIT_TARGET_BINDING);requireKind(actualInventory,Kind.NORMAL_EXIT_SOURCE_INVENTORY);
            RawJson original=projection.managedProfile(actualGuard.exact());
            RawJson finished=NormalExitSourceInventory.withInventory(original,actualInventory.exact());
            var custody=pins(List.of(actualGuard.original(),actualInventory.original(),file(snapshot)));
            return flat(Kind.NORMAL_EXIT_MANAGED_PROFILE,newTarget,finished.bytes(),()->{current.verify();custody.verify();});
        }
        public NormalExitSourceInventory.Input input(Created actualInventory,Created actualProfile)throws IOException {
            requireKind(actualInventory,Kind.NORMAL_EXIT_SOURCE_INVENTORY);requireKind(actualProfile,Kind.NORMAL_EXIT_MANAGED_PROFILE);
            var result=new NormalExitSourceInventory.Input(actualInventory.exact(),actualProfile.exact(),snapshot);
            NormalExitSourceInventory.inspect(result);current.verify();return result;
        }
    }
    public static NormalExitPrepared normalExit(ExactRef actualNativePlan,ExactRef actualSnapshot,Path guardTarget)throws IOException {
        var plan=NativeLaunchPlan.readExact(actualNativePlan,new NativeBridgeLaunchEvidence());
        var projection=NormalExitSourceInventory.project(actualNativePlan,guardTarget,actualSnapshot);
        return new NormalExitPrepared(plan,actualSnapshot,guardTarget,projection,pins(List.of(file(actualNativePlan),file(actualSnapshot),plan.preparedProfile().environmentManifest())));
    }
    public static Prepared initialPolicy(FileRef actualEnvironment,org.xar.ck3.control.application.driver.InitialEpisodePolicy.Lifecycle lifecycle,
            org.xar.ck3.control.application.driver.InitialEpisodePolicy.FreshPact fresh,Path target)throws IOException {
        byte[] bytes=org.xar.ck3.control.application.driver.InitialEpisodePolicy.produce(actualEnvironment,lifecycle,fresh).bytes();
        var held=pins(List.of(actualEnvironment));return flat(Kind.INITIAL_POLICY,target,bytes,()->{
            held.verify();if(!Arrays.equals(bytes,org.xar.ck3.control.application.driver.InitialEpisodePolicy.produce(actualEnvironment,lifecycle,fresh).bytes()))
                throw new IOException("actual pure initial policy producer changed before immutable publication");});
    }
    /** Explicit fixture bytes use the identical private preparation across quote, admitted write and readback. */
    public static Prepared initialFixturePolicy(FileRef actualEnvironment,
            org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture identical,Path target)throws IOException {
        Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(identical);identical.verifySources();
        var originals=new ArrayList<FileRef>();originals.add(actualEnvironment);
        for(ExactRef original:identical.inputClosure())originals.add(file(original));
        var held=pins(originals);
        byte[] bytes=org.xar.ck3.control.application.driver.InitialEpisodePolicy.produceFixture(actualEnvironment,identical).bytes();
        held.verify();identical.verifySources();
        return flat(Kind.INITIAL_POLICY,target,bytes,()->{
            held.verify();identical.verifySources();
            if(!Arrays.equals(bytes,org.xar.ck3.control.application.driver.InitialEpisodePolicy.produceFixture(actualEnvironment,identical).bytes()))
                throw new IOException("actual fixture policy producer changed before immutable publication");
            held.verify();identical.verifySources();
        });
    }
    /** Explicit Saved projection keeps both original file witnesses through the existing admitted writer. */
    public static Prepared initialSavedNativePolicy(FileRef actualEnvironment,FileRef actualSave,Path target)throws IOException {
        return savedPolicy(actualEnvironment,actualSave,List.of(),target);
    }
    /** The real CLI also pins the exact plan original used by its sole Saved reader. */
    public static Prepared initialSavedNativePolicy(FileRef actualEnvironment,FileRef actualSave,ExactRef actualNativePlan,Path target)throws IOException {
        return savedPolicy(actualEnvironment,actualSave,List.of(file(Objects.requireNonNull(actualNativePlan))),target);
    }
    private static Prepared savedPolicy(FileRef actualEnvironment,FileRef actualSave,List<FileRef> actualPlanOriginals,Path target)throws IOException {
        Objects.requireNonNull(actualEnvironment);Objects.requireNonNull(actualSave);
        var originals=new ArrayList<>(List.of(actualEnvironment,actualSave));originals.addAll(actualPlanOriginals);var held=pins(originals);
        byte[] bytes=org.xar.ck3.control.application.driver.InitialEpisodePolicy.produceSaved(actualEnvironment,actualSave).bytes();
        held.verify();
        return flat(Kind.INITIAL_POLICY,target,bytes,()->{
            held.verify();
            if(!Arrays.equals(bytes,org.xar.ck3.control.application.driver.InitialEpisodePolicy.produceSaved(actualEnvironment,actualSave).bytes()))
                throw new IOException("actual Saved policy producer changed before immutable publication");
            held.verify();
        });
    }
    private static List<Output> existingProfile(NativeRunProfileManifest.Manifest manifest,FileRef environment){
        var result=new ArrayList<Output>();for(var asset:manifest.profileAssets())result.add(new Output(kind(asset.kind()),asset.kind().relative(),asset.original().bytes(),asset.original().sha256()));
        result.add(new Output(Kind.PROFILE_ENVIRONMENT,NativeRunProfileProducer.ENVIRONMENT_NAME,environment.bytes(),environment.sha256()));return List.copyOf(result);
    }
    private static RetainedInput retained(NativeRunProfileProducer.Prepared actual,FileRef inventory)throws IOException {
        var held=NativeRunProfileProducer.readProductionTree(inventory);
        if(!held.equals(actual.productionTree()))throw new IOException("actual production inventory is not the original prepared complete tree");
        return retained(actual.request().profile(),inventory);
    }
    private static RetainedInput retained(NativeRunProfileManifest.Manifest actual,FileRef inventory)throws IOException {
        var held=NativeRunProfileProducer.readProductionTree(inventory);
        if(!held.equals(actual.mod().productionTree()))throw new IOException("actual production inventory differs from the verified environment");
        return retained(Path.of(actual.profileDir()),inventory);
    }
    private static RetainedInput retained(Path root,FileRef inventory)throws IOException {
        Path parent=root.resolve("mod-content");return new RetainedInput("mod-content",SharedSourceFiles.nativeDirectory(parent),inventory,
                SharedSourceFiles.nativeFile(Path.of(inventory.path())));
    }
    private static List<String> profileDirectories(){return List.of("mod","player","player/game_rules");}
    private static Prepared flat(Kind kind,Path target,byte[] bytes,Current current)throws IOException {
        if(target==null||!target.isAbsolute()||!target.normalize().equals(target)||target.getParent()==null)
            throw new IOException("actual absolute staged immutable output target required");
        var body=new Body(kind,target,bytes);body.output(target.getParent());current.verify();
        return new Prepared(target.getParent(),List.of(body),List.of(),List.of(),List.of(),current);
    }
    private static Current pins(List<FileRef> refs)throws IOException {
        var unique=new java.util.LinkedHashMap<Path,FileRef>();
        for(var source:refs){Path path=Path.of(source.path());var old=unique.putIfAbsent(path,source);
            if(old!=null&&!old.equals(source))throw new IOException("one staged input has conflicting exact originals");}
        if(unique.size()>16384)throw new IOException("staged original custody exceeds its complete bounded source inventory");
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        for(var source:unique.values()){
            var nativeBefore=SharedSourceFiles.nativeFile(Path.of(source.path()));var actual=SharedSourceFiles.observe(Path.of(source.path()));
            if(!actual.source().equals(source)||!actual.nativeFile().equals(nativeBefore))throw new IOException("staged original changed during capture");witnesses.add(actual);
        }
        return ()->{for(var original:witnesses){if(!SharedSourceFiles.nativeFile(Path.of(original.source().path())).equals(original.nativeFile()))
                throw new IOException("staged original file identity drifted");SharedSourceFiles.assertUnchanged(original);}};
    }
    private static Kind kind(NativeRunProfileManifest.AssetKind kind){return switch(kind){
        case DLC_LOAD->Kind.PROFILE_DLC_LOAD;case SETTINGS->Kind.PROFILE_SETTINGS;case TUTORIAL->Kind.PROFILE_TUTORIAL;
        case OUTER_DESCRIPTOR->Kind.PROFILE_OUTER_DESCRIPTOR;case PRESETS->Kind.PROFILE_PRESETS;};}
    private static FileRef file(ExactRef actual){return new FileRef(actual.path(),actual.bytes(),actual.sha256());}
    private static void requireKind(Created actual,Kind expected)throws IOException {
        if(Objects.requireNonNull(actual).kind()!=expected||!SharedSourceFiles.nativeFile(Path.of(actual.original().path())).equals(actual.nativeFile()))
            throw new IOException("actual staged immutable original has another producer role or native identity");actual.original().verify();
    }
}

