package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.NativeRunProfileManifest.*;

/**
 * The shared Java business-byte producer for a fresh isolated native run profile.
 * It never writes, launches Game, invokes Python, creates storage authority or fabricates actual files.
 * Root's existing finite bootstrap writer creates assets; finish consumes their actual native identities.
 */
public final class NativeRunProfileProducer {
    public static final String REQUEST_SCHEMA="xar.java-native-run-profile-request/v1";
    public static final String ENVIRONMENT_NAME="xar-autoplayer-environment.json";
    public static final String TOOL_COMPOSITION_SCHEMA="xar.java-native-profile-tool-composition/v1";
    public static final String TOOL_COMPOSITION_AUTHORITY_SCHEMA="xar.root-native-profile-tool-composition-authorization/v1";
    private static final java.util.Set<String> PATCH_FAMILIES=java.util.Set.of("ControlBuild","NativeRunProfileProducer","NativeRunProfileManifest");
    public record CompileEvidence(FileRef actual,FileRef outputs){
        public CompileEvidence{file(actual,MAXIMUM_BYTES);file(outputs,MAXIMUM_BYTES);}
    }
    /** The binary name is the original compiler manifest's slash-separated metadata.name. */
    public record PatchedClass(String binaryName,FileRef output){
        public PatchedClass{require(patchFamily(binaryName)!=null,"one of the three explicit compiled families required");file(output,4L<<20);}
    }
    public record RuntimeCopy(FileRef original,FileRef copy){
        public RuntimeCopy{file(original,64L<<20);file(copy,64L<<20);require(original.bytes()==copy.bytes()&&original.sha256().equals(copy.sha256()),"runtime copy must retain original bytes/SHA");}
    }
    /** Composition DATA alone never mints the private loaded-runtime qualification below. */
    public record ToolComposition(String schema,String machineId,String reviewAtUtc,FileRef baseToolsBuild,FileRef completionSource,
            FileRef rootAuthorization,FileRef sourceReady,List<CompileEvidence> compilations,List<FileRef> patchedSources,
            List<PatchedClass> patchedClasses,FileRef patchJar,List<RuntimeCopy> runtimeCopies,List<FileRef> completeRuntime){
        public ToolComposition{
            require(TOOL_COMPOSITION_SCHEMA.equals(schema),"exact explicit profile tool composition required");machine(machineId);Instant.parse(reviewAtUtc);
            for(var source:List.of(baseToolsBuild,completionSource,rootAuthorization,sourceReady))file(source,MAXIMUM_BYTES);
            compilations=List.copyOf(compilations);patchedSources=List.copyOf(patchedSources);patchedClasses=List.copyOf(patchedClasses);
            runtimeCopies=List.copyOf(runtimeCopies);completeRuntime=List.copyOf(completeRuntime);file(patchJar,16L<<20);
            require(!compilations.isEmpty()&&compilations.size()<=3,"finite actual staged compiler evidence required");
            require(patchedSources.size()==3&&patchedSources.stream().map(ref->Path.of(ref.path()).getFileName().toString()).collect(java.util.stream.Collectors.toSet())
                    .equals(PATCH_FAMILIES.stream().map(name->name+".java").collect(java.util.stream.Collectors.toSet())),"exact three patched source leaves required");
            for(var source:patchedSources)file(source,MAXIMUM_BYTES);
            require(patchedClasses.size()>=3&&patchedClasses.size()<=256&&patchedClasses.stream().map(PatchedClass::binaryName).distinct().count()==patchedClasses.size()
                    &&patchedClasses.stream().map(row->patchFamily(row.binaryName())).collect(java.util.stream.Collectors.toSet()).equals(PATCH_FAMILIES),"complete unique three-family compiled outputs required");
            require(runtimeCopies.size()==6&&runtimeCopies.stream().map(row->row.original().path()).distinct().count()==6
                    &&runtimeCopies.stream().map(row->row.copy().path()).distinct().count()==6,"six distinct original runtime files and byte copies required");
            require(completeRuntime.size()==7&&completeRuntime.stream().map(FileRef::path).distinct().count()==7,"explicit composed producer has exactly seven runtime files");
        }
    }
    private static String patchFamily(String binaryName){
        if(binaryName==null||!binaryName.startsWith("org/xar/ck3/control/build/"))return null;
        String name=binaryName.substring("org/xar/ck3/control/build/".length());int nested=name.indexOf('$');String family=nested<0?name:name.substring(0,nested);
        return PATCH_FAMILIES.contains(family)&&name.matches("[A-Za-z0-9_$]+")?family:null;
    }
    private static final class QualifiedComposition {
        private final FileRef original;private final ToolComposition data;private final List<SharedSourceFiles.Witness> originals;
        private QualifiedComposition(FileRef original,ToolComposition data,List<SharedSourceFiles.Witness> originals){
            this.original=original;this.data=data;this.originals=List.copyOf(originals);
        }
        private void requireCurrent(Clock clock)throws IOException{
            if(!clock.instant().isBefore(Instant.parse(data.reviewAtUtc())))throw new IOException("profile tool composition authorization expired");
            for(var held:originals)SharedSourceFiles.assertUnchanged(held);
            if(!sameRuntime(data.completeRuntime(),ControlBuild.producerClosure()))throw new IOException("actual composed profile runtime changed");
        }
    }
    private NativeRunProfileProducer(){ }
    public record Request(String schema,String machineId,String reviewAtUtc,String stateDir,String productionRoot,
            FileRef qualifiedToolsBuild,FileRef gameExecutable,FileRef vanillaRules,FileRef launcherSettings,
            FileRef productionManifest,NativeRunProfileRules.XarMode xarMode,Display display){
        public Request{require(REQUEST_SCHEMA.equals(schema),"exact Java native profile request required");machine(machineId);
            Instant.parse(reviewAtUtc);absolute(stateDir);absolute(productionRoot);
            require(Path.of(productionRoot).equals(Path.of(stateDir).resolve("profile/mod-content/xar-production")),
                    "actual production must be installed beneath the isolated profile");
            for(FileRef source:List.of(qualifiedToolsBuild,gameExecutable,vanillaRules,launcherSettings,productionManifest))Objects.requireNonNull(source);
            Objects.requireNonNull(xarMode);Objects.requireNonNull(display);}
        public Path profile(){return Path.of(stateDir).resolve("profile");}
    }
    public record PlannedAsset(AssetKind kind,String target,byte[] bytes){
        public PlannedAsset{Objects.requireNonNull(kind);absolute(target);bytes=bytes.clone();
            require(bytes.length>0&&bytes.length<=kind.maximumBytes(),"finite generated profile bytes required");}
        @Override public byte[] bytes(){return bytes.clone();}
        public FileRef expected(){return new FileRef(target,bytes.length,NativeRunProfileRules.sha(bytes));}
    }
    /** Contains observations from actual source files, not a public prepared=true switch. */
    public static final class Prepared {
        private final Request request;private final Game game;private final Mod mod;private final Dlc dlc;
        private final NativeRunProfileRules.Contract rules;private final List<FileRef> runtime;
        private final List<PlannedAsset> assets;private final List<SharedSourceFiles.Witness> originals;
        private Prepared(Request request,Game game,Mod mod,Dlc dlc,NativeRunProfileRules.Contract rules,List<FileRef> runtime,
                List<PlannedAsset> assets,List<SharedSourceFiles.Witness> originals){
            this.request=request;this.game=game;this.mod=mod;this.dlc=dlc;this.rules=rules;this.runtime=List.copyOf(runtime);
            this.assets=List.copyOf(assets);this.originals=List.copyOf(originals);}
        public Request request(){return request;}public List<PlannedAsset> assets(){return assets;}
        public ProductionTree productionTree(){return mod.productionTree();}
        public List<FileRef> expectedAssetFiles(){return assets.stream().map(PlannedAsset::expected).toList();}
        public void verifyOriginals()throws IOException{current(request,Clock.systemUTC());for(var held:originals)SharedSourceFiles.assertUnchanged(held);
            verifyProductionTree(mod.productionTree());}
    }
    public static Request readRequest(FileRef original)throws IOException{
        return ControlBuild.strictMapper().readValue(read(original,65536,new ArrayList<>()),Request.class);
    }
    public static Prepared prepare(Request request,Clock clock)throws IOException{
        current(request,clock);
        var receipt=ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuild());
        if(receipt.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!receipt.machineId().equals(request.machineId())
                ||!receipt.completeDeployment().equals(ControlBuild.producerClosure())
                ||receipt.compiledSourcePins().stream().filter(ref->Path.of(ref.path()).getFileName().toString()
                        .equals("NativeRunProfileProducer.java")).count()!=1)
            throw new IOException("actual loaded qualified Java profile producer runtime required");
        return derive(request,receipt.completeDeployment());
    }
    /** Single pure/source production core; tests exercise it without issuing runtime or storage authority. */
    static Prepared derive(Request request,List<FileRef> actualRuntime)throws IOException{
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        var launcher=ControlBuild.strictMapper().readTree(read(request.launcherSettings(),65536,originals));
        String raw=text(launcher,"rawVersion"),display=text(launcher,"version"),distribution=text(launcher,"distPlatform");
        observe(request.gameExecutable(),originals);
        var rules=NativeRunProfileRules.derive(request.vanillaRules(),read(request.vanillaRules(),4<<20,originals),request.xarMode());
        byte[] releaseBytes=read(request.productionManifest(),1<<20,originals);
        ReleaseManifest release=ControlBuild.strictMapper().readValue(releaseBytes,ReleaseManifest.class);
        Path production=Path.of(request.productionRoot());SharedSourceFiles.plainAncestors(production);
        ProductionTree productionTree=verifyProduction(production,release,originals);
        List<FileRef> files=productionTree.files().stream().map(SharedSourceFiles.Witness::source).toList();
        FileRef inner=files.stream().filter(ref->Path.of(ref.path()).equals(production.resolve("descriptor.mod"))).findFirst()
                .orElseThrow(()->new IOException("formal production descriptor is missing"));
        byte[] descriptor=read(inner,65536,originals);
        byte[] outer=renderOuter(descriptor,production);
        Game game=new Game(raw,display,distribution,request.launcherSettings().path(),request.launcherSettings().sha256(),
                request.gameExecutable().path(),request.gameExecutable().sha256(),request.vanillaRules().path(),request.vanillaRules().sha256(),false);
        Mod mod=new Mod("琉焰卿的永恒轮回",release.gitSha(),production.toString(),request.productionManifest().path(),
                request.productionManifest().sha256(),treeDigest(production,files),files.size(),release.modVersion(),release.gitTag(),release.workshopItemId(),files,productionTree);
        Path gameRoot=Path.of(request.gameExecutable().path()).getParent().getParent();
        Dlc dlc=observeDlc(gameRoot,originals);
        var mapper=ControlBuild.strictMapper();var load=mapper.createObjectNode();load.putArray("enabled_mods").add("mod/xar_autoplayer.mod");load.putArray("disabled_dlcs");
        var assets=List.of(asset(request,AssetKind.DLC_LOAD,canonical(load)),
                asset(request,AssetKind.SETTINGS,settingsBytes(request.display())),
                asset(request,AssetKind.TUTORIAL,"last_lesson_chain=\"reactive_advice\"\ncompleted_lessons={\n}\n".getBytes(StandardCharsets.UTF_8)),
                asset(request,AssetKind.OUTER_DESCRIPTOR,outer),asset(request,AssetKind.PRESETS,NativeRunProfileRules.renderPresets(rules)));
        for(var held:originals)SharedSourceFiles.assertUnchanged(held);
        return new Prepared(request,game,mod,dlc,rules,actualRuntime,assets,originals);
    }
    /** Stage two requires all actual first-stage writes. Expected content hashes alone are not custody. */
    public static Manifest finish(Prepared prepared,List<Asset> actualAssets,Clock clock)throws IOException{
        Objects.requireNonNull(prepared);current(prepared.request,clock);
        return finishDerived(prepared,actualAssets,clock);
    }
    private static Manifest finishDerived(Prepared prepared,List<Asset> actualAssets,Clock clock)throws IOException{
        verifyProductionTree(prepared.mod.productionTree());
        for(var held:prepared.originals)SharedSourceFiles.assertUnchanged(held);
        actualAssets=List.copyOf(actualAssets);if(actualAssets.size()!=AssetKind.values().length)throw new IOException("five actual profile outputs required");
        var byKind=new EnumMap<AssetKind,Asset>(AssetKind.class);
        for(Asset actual:actualAssets){
            if(byKind.putIfAbsent(actual.kind(),actual)!=null)throw new IOException("duplicate actual profile output role");
            PlannedAsset expected=prepared.assets.stream().filter(row->row.kind()==actual.kind()).findFirst().orElseThrow();
            if(!expected.expected().equals(actual.original()))throw new IOException("actual profile output differs from unique generated bytes");
            verifyAsset(prepared.request.profile(),actual);
            byte[] bytes=read(actual.original(),actual.kind().maximumBytes(),new ArrayList<>());
            if(!Arrays.equals(bytes,expected.bytes()))throw new IOException("actual profile file does not contain generated bytes");
        }
        Asset outer=byKind.get(AssetKind.OUTER_DESCRIPTOR),load=byKind.get(AssetKind.DLC_LOAD),
                presets=byKind.get(AssetKind.PRESETS),settings=byKind.get(AssetKind.SETTINGS);
        var loadProfile=new LoadProfile(List.of("mod/xar_autoplayer.mod"),List.of(),outer.original().path(),outer.original().sha256(),
                load.original().sha256(),presets.original().sha256(),settings.original().sha256(),settings(prepared.request.display()));
        Manifest body=new Manifest(SCHEMA,2,prepared.request.machineId(),clock.instant().toString(),prepared.request.stateDir(),
                prepared.request.profile().toString(),prepared.game,prepared.mod,loadProfile,prepared.rules,prepared.request.display(),prepared.dlc,
                List.copyOf(byKind.values()),prepared.request.qualifiedToolsBuild(),prepared.runtime,"0".repeat(64));
        Manifest result=seal(body);for(var held:prepared.originals)SharedSourceFiles.assertUnchanged(held);
        verifyProductionTree(prepared.mod.productionTree());return result;
    }
    /** Sole full v2 reader used by policy, frozen profile and the retained Native launch profile. */
    public static Manifest readVerified(FileRef original)throws IOException{
        var originalWitness=new ArrayList<SharedSourceFiles.Witness>();Manifest actual=decode(read(original,MAXIMUM_BYTES,originalWitness));
        if(!actual.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("profile source machine differs");
        var receipt=ControlBuild.verifiedCompletedReceipt(actual.producerToolsBuild());
        if(receipt.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                ||!receipt.machineId().equals(actual.machineId())||!receipt.completeDeployment().equals(actual.producerRuntime())
                ||receipt.compiledSourcePins().stream().filter(ref->Path.of(ref.path()).getFileName().toString()
                        .equals("NativeRunProfileProducer.java")).count()!=1)
            throw new IOException("profile producer historical complete runtime differs");
        var game=actual.game();
        Request request=new Request(REQUEST_SCHEMA,actual.machineId(),actual.observedAtUtc(),actual.stateDir(),
                actual.mod().productionPath(),actual.producerToolsBuild(),measure(game.executable(),game.executableSha256()),
                measure(game.vanillaRules(),game.vanillaRulesSha256()),measure(game.launcherSettings(),game.launcherSettingsSha256()),
                measure(actual.mod().productionManifest(),actual.mod().productionManifestSha256()),
                actual.rules().profile().get(actual.rules().declaredVanillaRuleCount()).setting().equals("xar_on")
                        ?NativeRunProfileRules.XarMode.XAR_ON:NativeRunProfileRules.XarMode.XAR_OFF,actual.display());
        Prepared prepared=derive(request,actual.producerRuntime());
        Manifest derived=finishDerived(prepared,actual.profileAssets(),Clock.fixed(Instant.parse(actual.observedAtUtc()),java.time.ZoneOffset.UTC));
        if(!Arrays.equals(encode(actual),encode(derived)))throw new IOException("profile is not the current exact original Java producer output");
        for(var held:originalWitness)SharedSourceFiles.assertUnchanged(held);return actual;
    }
    /** Public read-only adapter to the identical complete production consumer, with actual native witnesses. */
    public static ProductionTree verifyProduction(Path root,ReleaseManifest manifest)throws IOException{
        Objects.requireNonNull(root);Objects.requireNonNull(manifest);
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        ProductionTree actual=verifyProduction(root,manifest,originals);
        for(var original:originals)SharedSourceFiles.assertUnchanged(original);
        verifyProductionTree(actual);return actual;
    }
    private static ProductionTree verifyProduction(Path root,ReleaseManifest manifest,List<SharedSourceFiles.Witness> witnesses)throws IOException{
        var expected=new java.util.TreeMap<String,ReleaseEntry>();long logical=0;
        for(var entry:manifest.files()){
            logical=Math.addExact(logical,entry.size());
            if(entry.size()>MAXIMUM_PRODUCTION_FILE_BYTES||logical>MAXIMUM_PRODUCTION_LOGICAL_BYTES)
                throw new IOException("complete formal production input exceeds finite file/logical bounds");
            expected.put(entry.path(),entry);
        }
        var files=new ArrayList<SharedSourceFiles.Witness>();var directories=new ArrayList<TreeDirectory>();int count=0;long allocated=0;
        try(var walk=Files.walk(root)){var iterator=walk.iterator();while(iterator.hasNext()){
            Path path=iterator.next();if(++count>16384)throw new IOException("production tree entry bound exceeded");SharedSourceFiles.plainAncestors(path);
            if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS)){directories.add(new TreeDirectory(path.toString(),SharedSourceFiles.nativeDirectory(path)));continue;}
            if(!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("ordinary complete production tree required");
            String relative=root.relativize(path).toString().replace('\\','/');ReleaseEntry entry=expected.remove(relative);
            if(entry==null)throw new IOException("extra production file: "+relative);
            var ref=new FileRef(path.toString(),entry.size(),entry.sha256());observe(ref,witnesses);
            var held=witnesses.getLast();files.add(held);allocated=Math.addExact(allocated,held.nativeFile().allocatedBytes());
        }}
        if(!expected.isEmpty())throw new IOException("production manifest files are absent");
        files.sort(Comparator.comparing(row->row.source().path()));directories.sort(Comparator.comparing(TreeDirectory::path));
        long cluster=NativeStorageGeometry.read(root).clusterBytes();
        long directoryGuard=Math.max(4096,cluster);
        var tree=new ProductionTree(root.toString(),directories,files,allocated,directoryGuard,
                Math.addExact(allocated,Math.multiplyExact(directoryGuard,directories.size())));
        verifyProductionTree(tree);return tree;
    }
    /** Complete bounded immutable input custody for the sole hierarchical Bootstrap writer. No write authority. */
    public static byte[] encodeProductionTree(ProductionTree tree)throws IOException{
        verifyProductionTree(tree);
        byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(tree);
        if(bytes.length>MAXIMUM_BYTES)throw new IOException("complete production custody exceeds existing finite 1MiB original limit");
        return bytes;
    }
    public static ProductionTree readProductionTree(FileRef original)throws IOException{
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        ProductionTree tree=ControlBuild.strictMapper().readValue(read(original,MAXIMUM_BYTES,originals),ProductionTree.class);
        verifyProductionTree(tree);for(var held:originals)SharedSourceFiles.assertUnchanged(held);return tree;
    }
    public static void verifyProductionTree(ProductionTree tree)throws IOException{
        var directories=new ArrayList<TreeDirectory>();var files=new java.util.TreeSet<String>();int count=0;
        try(var walk=Files.walk(Path.of(tree.root()))){var iterator=walk.iterator();while(iterator.hasNext()){
            Path path=iterator.next();if(++count>16384)throw new IOException("retained production entry bound exceeded");SharedSourceFiles.plainAncestors(path);
            if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))directories.add(new TreeDirectory(path.toString(),SharedSourceFiles.nativeDirectory(path)));
            else if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))files.add(path.toString());else throw new IOException("retained nonordinary production input");
        }}
        directories.sort(Comparator.comparing(TreeDirectory::path));
        if(!directories.equals(tree.directories())||!files.equals(new java.util.TreeSet<>(tree.files().stream().map(row->row.source().path()).toList())))
            throw new IOException("complete retained production directory/file census changed");
        for(var held:tree.files())SharedSourceFiles.assertUnchanged(held);
    }

    /** Actual explicit profile facts. This port never copies a Save, writes ENV/profile files, or grants Started. */
    public static final class PreparedExplicit {
        private final ExplicitRequest request;private final ExplicitGame game;private final ExplicitProfile profile;
        private final List<SharedSourceFiles.Witness> assets,originals;private final Dlc dlc;private final List<FileRef> runtime;
        private final QualifiedComposition composition;
        private PreparedExplicit(ExplicitRequest request,ExplicitGame game,ExplicitProfile profile,List<SharedSourceFiles.Witness> assets,
                Dlc dlc,List<SharedSourceFiles.Witness> originals,List<FileRef> runtime,QualifiedComposition composition){
            this.request=request;this.game=game;this.profile=profile;this.assets=List.copyOf(assets);this.dlc=dlc;this.originals=List.copyOf(originals);this.runtime=List.copyOf(runtime);this.composition=composition;
        }
        public ExplicitRequest request(){return request;}public ExplicitProfile profile(){return profile;}
        public ExplicitCustody inputCustody(){return profile.custody();}
        public List<SharedSourceFiles.Witness> profileAssets(){return assets;}
        public List<String> productionRoots(){return profile.mountedMods().stream().map(MountedMod::productionRoot).distinct().toList();}
        public List<FileRef> requiredPreparedFileRefs(){return body(this,Clock.systemUTC()).requiredPreparedFileRefs();}
        public void verifyOriginals()throws IOException{currentExplicit(request,Clock.systemUTC());verifyExplicitSources(this);}
    }
    public static ExplicitRequest readExplicitRequest(FileRef original)throws IOException{
        return decodeExplicitRequest(read(original,MAXIMUM_BYTES,new ArrayList<>()));
    }
    public static PreparedExplicit prepareExplicit(ExplicitRequest request,Clock clock)throws IOException{
        currentExplicit(request,clock);
        if(COMPOSED_SAVED_REQUEST_SCHEMA.equals(request.schema())){
            var actual=qualifyComposition(request.qualifiedToolsBuild(),request.machineId(),clock);
            return deriveExplicit(request,actual.data.completeRuntime(),actual);
        }
        return deriveExplicit(request,qualifiedRuntime(request.qualifiedToolsBuild(),request.machineId()));
    }
    public static PreparedExplicit prepareSaved(ExplicitRequest request,Clock clock)throws IOException{
        if(!(request.source() instanceof SavedSource))throw new IOException("explicit Saved source request required");return prepareExplicit(request,clock);
    }
    public static PreparedExplicit prepareFixture(ExplicitRequest request,Clock clock)throws IOException{
        if(!(request.source() instanceof FixtureSource))throw new IOException("explicit frontend fixture source request required");return prepareExplicit(request,clock);
    }
    /** Completed producer record is historical provenance; it does not select the current consumer VM. */
    private static List<FileRef> recordedQualifiedRuntime(FileRef build,String machine)throws IOException{
        var receipt=ControlBuild.verifiedCompletedReceipt(build);
        if(receipt.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!receipt.machineId().equals(machine)
                ||receipt.compiledSourcePins().stream().filter(ref->Path.of(ref.path()).getFileName().toString().equals("NativeRunProfileProducer.java")).count()!=1)
            throw new IOException("actual complete source-bound profile producer runtime required");
        return receipt.completeDeployment();
    }
    private static List<FileRef> qualifiedRuntime(FileRef build,String machine)throws IOException{
        var runtime=recordedQualifiedRuntime(build,machine);
        if(!runtime.equals(ControlBuild.producerClosure()))
            throw new IOException("actual complete source-bound profile producer runtime required");
        if(NativeRunProfileProducer.class.getProtectionDomain().getCodeSource()==null||ControlBuild.class.getProtectionDomain().getCodeSource()==null
                ||!NativeRunProfileProducer.class.getProtectionDomain().getCodeSource().getLocation().equals(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation()))
            throw new IOException("profile and completed-build producer are not in the same actual runtime");
        return runtime;
    }
    private static QualifiedComposition qualifyComposition(FileRef original,String machine,Clock clock)throws IOException{
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        ToolComposition composition=ControlBuild.strictMapper().readValue(compositionRead(original,MAXIMUM_BYTES,witnesses),ToolComposition.class);
        if(!composition.machineId().equals(machine)||!machine.equals(WindowsJobProcess.currentMachineId())
                ||!clock.instant().isBefore(Instant.parse(composition.reviewAtUtc())))throw new IOException("current same-machine tool composition required");
        JsonNode authority=ControlBuild.strictMapper().readTree(compositionRead(composition.rootAuthorization(),MAXIMUM_BYTES,witnesses));
        JsonNode observed=authority.get("observed_at_utc");
        if(observed==null||!observed.isTextual())throw new IOException("independent Root composition observation required");
        Instant opened=Instant.parse(observed.textValue()),until=Instant.parse(composition.reviewAtUtc());
        var expectedAuthority=compositionAuthority(composition,observed.textValue());
        if(!expectedAuthority.equals(authority)||opened.isAfter(clock.instant())||!until.isAfter(opened)||until.isAfter(opened.plusSeconds(3600)))
            throw new IOException("Root composition authorization does not bind these exact original inputs and current finite window");
        observeComposition(composition.baseToolsBuild(),witnesses);observeComposition(composition.completionSource(),witnesses);
        var base=ControlBuild.verifiedCompletedReceipt(composition.baseToolsBuild());
        var completed=ControlBuild.verifyCompletionSource(composition.completionSource());
        if(base.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||!base.machineId().equals(machine)||base.completeDeployment().size()!=6
                ||!ControlBuild.strictMapper().valueToTree(base).equals(ControlBuild.strictMapper().valueToTree(completed)))
            throw new IOException("composition must consume the same normal successful Maven six-file receipt and mandatory completion source");
        var originalRuntime=composition.runtimeCopies().stream().map(RuntimeCopy::original).toList();
        if(!sameRuntime(base.completeDeployment(),originalRuntime))throw new IOException("composition replaced an original Maven runtime file");
        Path libraries=Path.of(composition.patchJar().path()).getParent().resolve("lib");
        var runtime=new ArrayList<FileRef>();runtime.add(composition.patchJar());
        for(var copy:composition.runtimeCopies()){
            if(!Path.of(copy.copy().path()).getParent().equals(libraries))throw new IOException("composed runtime copies must be its exact adjacent six-file lib");
            observeComposition(copy.original(),witnesses);observeComposition(copy.copy(),witnesses);runtime.add(copy.copy());
        }
        if(!sameRuntime(runtime,composition.completeRuntime())||!sameRuntime(ControlBuild.producerClosure(),composition.completeRuntime()))
            throw new IOException("composition differs from the actual complete seven-file loaded runtime");
        for(Class<?> anchor:List.of(ControlBuild.class,NativeRunProfileProducer.class,NativeRunProfileManifest.class)){
            if(anchor.getProtectionDomain().getCodeSource()==null)throw new IOException("actual composed reader/producer/manifest CodeSource required");
            try{if(!Path.of(anchor.getProtectionDomain().getCodeSource().getLocation().toURI()).equals(Path.of(composition.patchJar().path())))
                    throw new IOException("all three actual producer anchors must come from this one patch archive");
            }catch(java.net.URISyntaxException invalid){throw new IOException("invalid actual composition CodeSource",invalid);}
        }
        JsonNode ready=ControlBuild.strictMapper().readTree(compositionRead(composition.sourceReady(),MAXIMUM_BYTES,witnesses));
        for(FileRef source:composition.patchedSources()){
            if(!containsPin(ready,source))throw new IOException("composition SourceReady omitted an exact patched source");
        }
        verifyCompilationEvidence(composition,witnesses);
        observeComposition(composition.patchJar(),witnesses);verifyPatchArchive(composition);
        var result=new QualifiedComposition(original,composition,witnesses);result.requireCurrent(clock);return result;
    }
    /** Compare original JSON integers in one wire domain; this does not coerce floating point or booleans. */
    static com.fasterxml.jackson.databind.node.ObjectNode compositionAuthority(ToolComposition composition,String observedAtUtc)throws IOException{
        var mapper=ControlBuild.strictMapper();
        var expected=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(mapper.writeValueAsBytes(composition));
        expected.remove(List.of("schema","root_authorization"));expected.put("composition_schema",TOOL_COMPOSITION_SCHEMA);
        expected.put("schema",TOOL_COMPOSITION_AUTHORITY_SCHEMA);expected.put("issuer_task","/root/ck3-resume91-root-20261116-research");
        expected.put("observed_at_utc",observedAtUtc);return expected;
    }
    private static boolean sameFileRef(FileRef expected,FileRef actual){
        return expected!=null&&actual!=null&&Path.of(expected.path()).equals(Path.of(actual.path()))
                &&expected.bytes()==actual.bytes()&&expected.sha256().equals(actual.sha256());
    }
    private static void observeComposition(FileRef source,List<SharedSourceFiles.Witness> witnesses)throws IOException{
        var actual=SharedSourceFiles.observe(Path.of(source.path()));
        if(!sameFileRef(source,actual.source()))throw new IOException("composition original content differs from its actual file pin");witnesses.add(actual);
    }
    private static byte[] compositionRead(FileRef source,int maximum,List<SharedSourceFiles.Witness> witnesses)throws IOException{
        file(source,maximum);observeComposition(source,witnesses);byte[] bytes;
        try(var input=Files.newInputStream(Path.of(source.path()))){bytes=input.readNBytes(maximum+1);}
        if(bytes.length!=source.bytes()||!NativeRunProfileRules.sha(bytes).equals(source.sha256()))throw new IOException("composition original changed during bounded read");
        SharedSourceFiles.assertUnchanged(witnesses.getLast());return bytes;
    }
    private static boolean sameRuntime(List<FileRef> expected,List<FileRef> actual){
        if(expected.size()!=actual.size())return false;
        var remaining=new java.util.HashMap<Path,FileRef>();
        for(var ref:expected)if(remaining.put(Path.of(ref.path()),ref)!=null)return false;
        for(var ref:actual){var old=remaining.remove(Path.of(ref.path()));if(old==null||old.bytes()!=ref.bytes()||!old.sha256().equals(ref.sha256()))return false;}
        return remaining.isEmpty();
    }
    private static boolean containsPin(JsonNode value,FileRef expected){
        if(value==null)return false;
        if(value.isObject()&&value.has("path")&&value.has("bytes")&&value.has("sha256")
                &&value.get("path").isTextual()&&value.get("bytes").isIntegralNumber()&&value.get("sha256").isTextual()
                &&Path.of(value.get("path").textValue()).equals(Path.of(expected.path()))
                &&value.get("bytes").longValue()==expected.bytes()&&value.get("sha256").textValue().equals(expected.sha256()))return true;
        if(value.isContainerNode())for(JsonNode child:value)if(containsPin(child,expected))return true;
        return false;
    }
    private static FileRef evidencePin(JsonNode value)throws IOException{return ControlBuild.strictMapper().treeToValue(value,FileRef.class);}
    private static boolean exactBoolean(JsonNode value,boolean expected){return value!=null&&value.isBoolean()&&value.booleanValue()==expected;}
    static void verifyCompilationEvidence(ToolComposition composition,List<SharedSourceFiles.Witness> witnesses)throws IOException{
        var found=new java.util.TreeMap<String,FileRef>();var compiledSources=new java.util.HashSet<FileRef>();
        for(var source:composition.patchedSources())observeComposition(source,witnesses);
        for(var phase:composition.compilations()){
            JsonNode actual=ControlBuild.strictMapper().readTree(compositionRead(phase.actual(),MAXIMUM_BYTES,witnesses));
            JsonNode outputs=ControlBuild.strictMapper().readTree(compositionRead(phase.outputs(),MAXIMUM_BYTES,witnesses));
            if(!actual.path("schema").asText().equals("composite-operator-integration-actual/v1")||!actual.path("phase").asText().equals("prod")
                    ||!actual.path("exit_code").isIntegralNumber()||actual.path("exit_code").intValue()!=0
                    ||!exactBoolean(actual.get("timeout"),false)||!exactBoolean(actual.get("contract_accepted"),true)
                    ||!sameFileRef(evidencePin(actual.get("output_manifest")),phase.outputs())
                    ||!outputs.path("phase").asText().equals("prod")||!exactBoolean(outputs.get("success"),true)
                    ||!outputs.path("errors").isArray()||!outputs.path("errors").isEmpty()||!outputs.path("classes").isArray())
                throw new IOException("actual successful managed compilation and its exact complete output manifest required");
            FileRef configRef=evidencePin(actual.get("config"));
            JsonNode config=ControlBuild.strictMapper().readTree(compositionRead(configRef,2*MAXIMUM_BYTES,witnesses));
            JsonNode post=ControlBuild.strictMapper().readTree(compositionRead(evidencePin(actual.get("post")),MAXIMUM_BYTES,witnesses));
            if(!exactBoolean(post.get("inputs_unchanged"),true)||!exactBoolean(post.get("contract_accepted"),true)
                    ||!sameFileRef(evidencePin(post.get("output_manifest")),phase.outputs()))
                throw new IOException("managed compilation source postcheck or complete output reference changed");
            JsonNode sourceRows=config.path("phases").path("prod").path("sources");
            if(!sourceRows.isArray())throw new IOException("actual managed compiler source list required");
            var phaseSources=new java.util.HashMap<String,FileRef>();
            for(JsonNode sourceRow:sourceRows){
                FileRef source=evidencePin(sourceRow);String name=Path.of(source.path()).getFileName().toString();
                if(name.endsWith(".java")&&PATCH_FAMILIES.contains(name.substring(0,name.length()-5))){
                    if(phaseSources.putIfAbsent(name,source)!=null)throw new IOException("one managed phase has duplicate source family owners");
                    observeComposition(source,witnesses);
                }
            }
            for(var source:composition.patchedSources())if(containsPin(sourceRows,source))compiledSources.add(source);
            if(outputs.get("classes").size()>256)throw new IOException("bounded explicit three-family output census required");
            for(JsonNode row:outputs.get("classes")){
                String name=row.path("metadata").path("name").asText();String family=patchFamily(name);
                if(family==null)throw new IOException("composition compiler emitted an unrequested class family");
                String sourceFile=row.path("metadata").path("SourceFile").asText();
                FileRef source=composition.patchedSources().stream().filter(ref->Path.of(ref.path()).getFileName().toString().equals(family+".java")).findFirst().orElseThrow();
                FileRef phaseSource=phaseSources.get(family+".java");
                if(!sourceFile.equals(family+".java")||phaseSource==null)throw new IOException("compiled family differs from its actual source pin");
                FileRef pin=evidencePin(row.get("pin"));observeComposition(pin,witnesses);
                if(!sameFileRef(phaseSource,source)){
                    if(phaseSource.bytes()==source.bytes()&&phaseSource.sha256().equals(source.sha256()))
                        throw new IOException("selected source pin must name its actual compiler input, not an equivalent path alias");
                    // A retained earlier phase can also contain a superseded version of this family.
                    // Its original outputs stay checked and retained, but never enter the final patch census.
                    continue;
                }
                if(found.putIfAbsent(name,pin)!=null)throw new IOException("one composed class has duplicate compilation owners");
            }
        }
        var declared=new java.util.TreeMap<String,FileRef>();for(var row:composition.patchedClasses())declared.put(row.binaryName(),row.output());
        if(!found.keySet().equals(declared.keySet())||found.entrySet().stream().anyMatch(row->!sameFileRef(row.getValue(),declared.get(row.getKey())))
                ||!compiledSources.equals(new java.util.HashSet<>(composition.patchedSources())))
            throw new IOException("patched class/source census is not the complete exact managed compilation union");
    }
    /** Narrow archive-byte check for this exact repair; it does not qualify loaded runtime or source authority. */
    static void verifyPatchArchive(ToolComposition composition)throws IOException{
        var remaining=new java.util.HashMap<String,FileRef>();for(var row:composition.patchedClasses())remaining.put(row.binaryName()+".class",row.output());
        try(var archive=new java.util.zip.ZipFile(composition.patchJar().path())){
            var entries=archive.entries();var seen=new java.util.HashSet<String>();
            while(entries.hasMoreElements()){
                var entry=entries.nextElement();if(entry.isDirectory())continue;
                if(!seen.add(entry.getName()))throw new IOException("duplicate patched class archive entry");
                FileRef output=remaining.remove(entry.getName());if(output==null)throw new IOException("patch archive contains a class outside the exact three-family managed outputs");
                output.verify();byte[] bytes;try(var input=archive.getInputStream(entry)){bytes=input.readNBytes(Math.toIntExact(output.bytes())+1);}
                if(bytes.length!=output.bytes()||!NativeRunProfileRules.sha(bytes).equals(output.sha256()))throw new IOException("patch archive class bytes differ from the actual managed compiler output");
            }
        }
        if(!remaining.isEmpty())throw new IOException("patch archive omitted a managed class family member");
    }
    /** Same production derivation, exercised on owned software inputs; no build/capacity/Game qualification is minted here. */
    static PreparedExplicit deriveExplicit(ExplicitRequest request,List<FileRef> runtime)throws IOException{
        if(COMPOSED_SAVED_REQUEST_SCHEMA.equals(request.schema()))throw new IOException("composed profile needs its private actual runtime qualification, not request DATA");
        return deriveExplicit(request,runtime,null);
    }
    private static PreparedExplicit deriveExplicit(ExplicitRequest request,List<FileRef> runtime,QualifiedComposition composition)throws IOException{
        if(COMPOSED_SAVED_REQUEST_SCHEMA.equals(request.schema())&&(composition==null||!composition.original.equals(request.qualifiedToolsBuild())
                ||!sameRuntime(composition.data.completeRuntime(),runtime)))throw new IOException("actual composed profile qualification changed");
        var observed=new ExplicitObservation();Path profile=request.profile();SharedSourceFiles.plainAncestors(profile);
        if(!Files.isDirectory(profile,LinkOption.NOFOLLOW_LINKS))throw new IOException("actual explicit profile must already exist");
        var profileIdentity=SharedSourceFiles.nativeDirectory(profile);
        JsonNode launcher=ControlBuild.strictMapper().readTree(observed.read(request.launcherSettings(),65536));
        observed.hold(request.gameExecutable());observed.hold(request.vanillaRules());
        var game=new ExplicitGame(text(launcher,"rawVersion"),text(launcher,"version"),text(launcher,"distPlatform"),
                request.launcherSettings().path(),request.launcherSettings().sha256(),request.gameExecutable().path(),request.gameExecutable().sha256(),
                request.vanillaRules().path(),request.vanillaRules().sha256(),request.debugMode());
        FileRef loadRef=observed.hold(profile.resolve("dlc_load.json"),65536).source();
        JsonNode load=ControlBuild.strictMapper().readTree(observed.read(loadRef,65536));
        if(!load.isObject())throw new IOException("actual dlc_load object required");
        List<String> enabled=explicitStrings(load.get("enabled_mods"),128,"enabled_mods");
        var disabled=load.has("disabled_dlcs")?new DeclaredDlc(DlcDeclaration.DECLARED,explicitStrings(load.get("disabled_dlcs"),2048,"disabled_dlcs"))
                :new DeclaredDlc(DlcDeclaration.ABSENT,List.of());
        ExplicitLoad selection=new ExplicitLoad(loadRef,enabled,disabled);var mounts=new ArrayList<MountedMod>();
        var products=new java.util.TreeMap<String,SharedSourceFiles.Witness>();var directories=new java.util.TreeMap<String,ProductDirectory>();
        int entries=0;long logical=0;
        for(String entry:enabled){
            Path descriptor=explicitPath(entry,profile);
            if(!descriptor.startsWith(profile))throw new IOException("enabled descriptor escaped the exact profile");
            var held=observed.hold(descriptor,65536);byte[] raw=observed.read(held.source(),65536);
            var matcher=java.util.regex.Pattern.compile("(?m)^\\s*path\\s*=\\s*\"([^\"\\r\\n]+)\"\\s*(?:#.*)?$").matcher(utf8(raw));
            if(!matcher.find())throw new IOException("enabled descriptor lacks one directory product path");String declared=matcher.group(1);
            if(matcher.find())throw new IOException("enabled descriptor has multiple directory product paths");
            Path root=explicitPath(declared,Path.of(request.sourceWorkingDirectory()));
            if(!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("actual ordinary frozen product directory required");
            mounts.add(new MountedMod(entry,held,root.toString()));products.put(descriptor.toString(),held);
            try(var walk=Files.walk(root)){var iterator=walk.iterator();while(iterator.hasNext()){
                Path path=iterator.next();if(++entries>16384)throw new IOException("explicit product entry bound exceeded");SharedSourceFiles.plainAncestors(path);
                if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))directories.put(path.toString(),explicitDirectory(path));
                else if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))products.put(path.toString(),observed.hold(path,MAXIMUM_PRODUCTION_FILE_BYTES));
                else throw new IOException("nonordinary enabled product input");
                if(products.size()>4096)throw new IOException("explicit product file count bound exceeded");
            }}
        }
        long filesAllocation=0,dirsAllocation=0;
        for(var row:products.values()){logical=Math.addExact(logical,row.source().bytes());filesAllocation=Math.addExact(filesAllocation,row.nativeFile().allocatedBytes());}
        for(var row:directories.values())dirsAllocation=Math.addExact(dirsAllocation,Math.max(4096,row.nativeAllocatedBytes()));
        var custody=new ExplicitCustody(profile.toString(),profileIdentity,List.copyOf(directories.values()),List.copyOf(products.values()),logical,filesAllocation,dirsAllocation,Math.addExact(filesAllocation,dirsAllocation));
        ExplicitProfile typed;
        if(request.source() instanceof SavedSource saved){
            JsonNode inventory=ControlBuild.strictMapper().readTree(observed.read(saved.productInventory(),MAXIMUM_BYTES));
            explicitKeys(inventory,java.util.Set.of("schema","profile_path","enabled_mods","product_files"));
            String expected=saved.kind()==SavedKind.VANILLA?"ck3-saved-campaign-vanilla-profile-v1":"ck3-saved-campaign-product-only-profile-v1";
            if(!expected.equals(text(inventory,"schema"))||!explicitPath(text(inventory,"profile_path"),Path.of(request.sourceWorkingDirectory())).equals(profile)
                    ||!explicitStrings(inventory.get("enabled_mods"),128,"inventory enabled_mods").equals(enabled))
                throw new IOException("explicit Saved schema/profile/ordered mods differ from actual declared source");
            JsonNode rows=inventory.get("product_files");if(rows==null||!rows.isArray()||rows.size()>4096)throw new IOException("complete explicit Saved product file rows required");
            var declared=new java.util.HashMap<String,FileRef>();
            for(JsonNode row:rows){
                explicitKeys(row,java.util.Set.of("path","bytes","sha256"));JsonNode count=row.get("bytes");String hash=text(row,"sha256");
                if(count==null||!count.isIntegralNumber()||!count.canConvertToLong()||count.longValue()<0||!hash.matches("[0-9a-fA-F]{64}"))
                    throw new IOException("exact typed Saved product bytes/SHA required");
                Path path=explicitPath(text(row,"path"),Path.of(request.sourceWorkingDirectory()));
                FileRef expectedFile=new FileRef(path.toString(),count.longValue(),hash.toLowerCase(java.util.Locale.ROOT));
                if(declared.putIfAbsent(path.toString(),expectedFile)!=null)throw new IOException("duplicate Saved product original");
                var actual=products.get(path.toString());if(actual==null||!actual.source().equals(expectedFile))throw new IOException("Saved product inventory differs from complete actual enabled projection");
                if(path.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".txt")
                        &&utf8(observed.read(actual.source(),(int)MAXIMUM_PRODUCTION_FILE_BYTES)).contains("on_game_start_after_lobby"))
                    throw new IOException("Saved product profile contains a cold frontend registrar");
            }
            if(!declared.keySet().equals(products.keySet()))throw new IOException("Saved inventory is not the complete enabled descriptor/product projection");
            typed=new SavedProfile(saved.kind(),saved.productInventory(),selection,mounts,custody);
        }else{
            var fixture=(FixtureSource)request.source();for(var source:fixture.immutableInputs())observed.hold(source);
            if(!fixture.immutableInputs().contains(loadRef))throw new IOException("fixture private source closure omitted actual dlc_load");
            var mounted=new java.util.TreeSet<String>();
            for(String name:List.of("mod","mod-content")){Path top=profile.resolve(name);if(Files.exists(top,LinkOption.NOFOLLOW_LINKS)){
                SharedSourceFiles.plainAncestors(top);if(!Files.isDirectory(top,LinkOption.NOFOLLOW_LINKS))throw new IOException("ordinary mounted fixture directory required");
                try(var walk=Files.walk(top)){var iterator=walk.iterator();while(iterator.hasNext()){
                    Path path=iterator.next();if(++entries>16384)throw new IOException("fixture mounted entry bound exceeded");SharedSourceFiles.plainAncestors(path);
                    if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)){
                        var held=observed.hold(path,MAXIMUM_PRODUCTION_FILE_BYTES);mounted.add(profile.relativize(path).toString().replace('\\','/'));
                        if(!fixture.immutableInputs().contains(held.source()))throw new IOException("fixture source closure omitted a mounted original");
                    }else if(!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("nonordinary mounted fixture entry");
                }}
            }}
            if(!mounted.equals(new java.util.TreeSet<>(fixture.mountedRelativePaths())))throw new IOException("complete fixture mounted source paths changed");
            typed=new FreshFixtureProfile(fixture.policySource(),fixture.immutableInputs(),fixture.mountedRelativePaths(),selection,mounts,custody);
        }
        var assets=new ArrayList<SharedSourceFiles.Witness>();
        for(String name:List.of("pdx_settings.txt","tutorial.txt","player/game_rules/presets.txt")){
            Path path=profile.resolve(name);if(Files.exists(path,LinkOption.NOFOLLOW_LINKS))assets.add(observed.hold(path,262144));
        }
        var dlcWitnesses=new ArrayList<SharedSourceFiles.Witness>();Dlc dlc=observeDlc(Path.of(request.gameExecutable().path()).getParent().getParent(),dlcWitnesses);
        for(var held:dlcWitnesses)observed.hold(held.source());
        if(!SharedSourceFiles.nativeDirectory(profile).equals(profileIdentity))throw new IOException("explicit profile root identity changed during derivation");
        var result=new PreparedExplicit(request,game,typed,assets,dlc,observed.all(),runtime,composition);verifyExplicitSources(result);return result;
    }
    public static ExplicitManifest finishExplicit(PreparedExplicit prepared,Clock clock)throws IOException{
        Objects.requireNonNull(prepared);currentExplicit(prepared.request,clock);verifyExplicitSources(prepared);return sealExplicit(body(prepared,clock));
    }
    private static ExplicitManifest body(PreparedExplicit prepared,Clock clock){
        boolean retained=EXPLICIT_SAVED_LAYOUT_REQUEST_SCHEMA.equals(prepared.request.schema());
        boolean composed=COMPOSED_SAVED_REQUEST_SCHEMA.equals(prepared.request.schema());
        if(composed&&prepared.composition==null)throw new IllegalStateException("composed profile lacks its private producer qualification");
        return new ExplicitManifest(composed?COMPOSED_SAVED_SCHEMA:retained?EXPLICIT_SAVED_LAYOUT_SCHEMA:EXPLICIT_SCHEMA,composed?5:retained?4:3,prepared.request.machineId(),clock.instant().toString(),prepared.request.stateDir(),prepared.request.profile().toString(),
                prepared.game,prepared.request,prepared.profile,prepared.assets,prepared.dlc,prepared.originals,prepared.request.qualifiedToolsBuild(),prepared.runtime,"0".repeat(64));
    }
    /** Full physical prelaunch reader. After Game, immutable ENV readers use readEnvironmentOriginal instead. */
    public static ProfileEnvironment readEnvironmentVerified(FileRef original)throws IOException{
        ProfileEnvironment environment=readEnvironmentOriginal(original);
        if(environment instanceof Manifest)return readVerified(original);
        var actual=(ExplicitManifest)environment;
        if(!actual.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("explicit profile belongs to another machine");
        QualifiedComposition composition=COMPOSED_SAVED_SCHEMA.equals(actual.schema())?qualifyComposition(actual.producerToolsBuild(),actual.machineId(),Clock.systemUTC()):null;
        var runtime=composition==null?qualifiedRuntime(actual.producerToolsBuild(),actual.machineId()):composition.data.completeRuntime();
        if(!runtime.equals(actual.producerRuntime()))throw new IOException("explicit producer historical complete runtime changed");
        var derived=composition==null?deriveExplicit(actual.request(),runtime):deriveExplicit(actual.request(),runtime,composition);verifyExplicitSources(derived);
        var expected=sealExplicit(body(derived,Clock.fixed(Instant.parse(actual.observedAtUtc()),java.time.ZoneOffset.UTC)));
        if(!Arrays.equals(encodeEnvironment(actual),encodeEnvironment(expected)))throw new IOException("explicit profile is not the exact physical source-bound producer output");
        return actual;
    }
    /**
     * A qualified new consumer may recheck the physical inputs of a retained Saved ENV.
     * The completed original producer and its six-file runtime stay exact. They need not
     * be the current consumer's CodeSource. The ENV/request bytes and original review
     * are not rewritten; the caller's new request/plan owns its current finite window.
     * This reader neither creates an ENV nor grants a launch, storage or Game permission.
     */
    public static ExplicitManifest readSavedEnvironmentInputsVerified(FileRef original)throws IOException{
        ProfileEnvironment environment=readEnvironmentOriginal(original);
        if(!(environment instanceof ExplicitManifest actual)||!(actual.request().source() instanceof SavedSource))
            throw new IOException("retained explicit Saved environment required");
        // Keep the original composed-runtime qualification and lifetime contract intact.
        if(COMPOSED_SAVED_SCHEMA.equals(actual.schema()))return (ExplicitManifest)readEnvironmentVerified(original);
        if(!actual.machineId().equals(WindowsJobProcess.currentMachineId()))throw new IOException("explicit profile belongs to another machine");
        var recorded=recordedQualifiedRuntime(actual.producerToolsBuild(),actual.machineId());
        if(!recorded.equals(actual.producerRuntime()))throw new IOException("explicit producer historical complete runtime changed");
        var derived=deriveExplicit(actual.request(),recorded);verifyExplicitSources(derived);
        var expected=sealExplicit(body(derived,Clock.fixed(Instant.parse(actual.observedAtUtc()),java.time.ZoneOffset.UTC)));
        if(!Arrays.equals(encodeEnvironment(actual),encodeEnvironment(expected)))
            throw new IOException("retained Saved environment physical inputs differ from its exact original");
        return actual;
    }
    private static void verifyExplicitSources(PreparedExplicit value)throws IOException{
        if(value.composition!=null)value.composition.requireCurrent(Clock.systemUTC());
        for(var held:value.originals)SharedSourceFiles.assertUnchanged(held);
        var custody=value.profile.custody();if(!SharedSourceFiles.nativeDirectory(Path.of(custody.profileRoot())).equals(custody.profileIdentity()))
            throw new IOException("explicit profile root was replaced");
        var files=new java.util.TreeSet<String>();var dirs=new java.util.TreeMap<String,ProductDirectory>();int count=0;
        for(var mount:value.profile.mountedMods()){
            files.add(mount.descriptor().source().path());
            try(var walk=Files.walk(Path.of(mount.productionRoot()))){var iterator=walk.iterator();while(iterator.hasNext()){
                Path path=iterator.next();if(++count>16384)throw new IOException("revalidation product entry bound exceeded");SharedSourceFiles.plainAncestors(path);
                if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))dirs.put(path.toString(),explicitDirectory(path));
                else if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))files.add(path.toString());else throw new IOException("nonordinary retained product entry");
            }}
        }
        if(!files.equals(new java.util.TreeSet<>(custody.productFiles().stream().map(row->row.source().path()).toList()))
                ||!List.copyOf(dirs.values()).equals(custody.directories()))throw new IOException("complete immutable enabled product directory/file census changed");
        for(var held:custody.productFiles())SharedSourceFiles.assertUnchanged(held);
        if(value.profile instanceof FreshFixtureProfile fixture){
            var mounted=new java.util.TreeSet<String>();Path profile=Path.of(custody.profileRoot());
            for(String name:List.of("mod","mod-content")){Path top=profile.resolve(name);if(Files.exists(top,LinkOption.NOFOLLOW_LINKS)){
                SharedSourceFiles.plainAncestors(top);if(!Files.isDirectory(top,LinkOption.NOFOLLOW_LINKS))throw new IOException("fixture mounted root changed kind");
                try(var walk=Files.walk(top)){var iterator=walk.iterator();while(iterator.hasNext()){
                    Path path=iterator.next();if(++count>32768)throw new IOException("complete retained fixture entry bound exceeded");SharedSourceFiles.plainAncestors(path);
                    if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))mounted.add(profile.relativize(path).toString().replace('\\','/'));
                    else if(!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("nonordinary retained fixture entry");
                }}
            }}
            if(!mounted.equals(new java.util.TreeSet<>(fixture.mountedRelativePaths())))throw new IOException("complete retained fixture mounted census changed");
        }
    }
    private static ProductDirectory explicitDirectory(Path path)throws IOException{
        String text=path.toString();String nativePath=text.startsWith("\\\\?\\")?text:text.startsWith("\\\\")?"\\\\?\\UNC\\"+text.substring(2):"\\\\?\\"+text;
        var handle=com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(nativePath,0x80,7,null,3,0x02200000,null);
        if(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle))throw new IOException("explicit directory open Win32="+com.sun.jna.Native.getLastError()+" path="+path);
        try{var facts=SharedSourceFiles.nativeHeldDirectory(handle);return new ProductDirectory(path.toString(),
                new SharedSourceFiles.DirectoryIdentity(facts.volumeSerialDecimal(),facts.fileIdDecimal(),facts.creationFiletimeDecimal()),facts.allocatedBytes());}
        finally{if(!com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle))throw new IOException("explicit directory close Win32="+com.sun.jna.Native.getLastError());}
    }
    private static Path explicitPath(String original,Path base)throws IOException{
        Path path=Path.of(original);if(!path.isAbsolute())path=base.resolve(path);path=path.toAbsolutePath().normalize();
        SharedSourceFiles.plainAncestors(path);return path.toRealPath(LinkOption.NOFOLLOW_LINKS);
    }
    private static List<String> explicitStrings(JsonNode value,int maximum,String label)throws IOException{
        if(value==null||!value.isArray()||value.size()>maximum)throw new IOException("explicit ordered "+label+" array required");
        var result=new ArrayList<String>();for(JsonNode item:value){if(!item.isTextual()||item.textValue().isBlank())throw new IOException("actual "+label+" strings required");result.add(item.textValue());}return List.copyOf(result);
    }
    private static void explicitKeys(JsonNode value,java.util.Set<String> expected)throws IOException{
        if(value==null||!value.isObject()||value.size()!=expected.size())throw new IOException("closed explicit profile source required");
        var actual=new java.util.HashSet<String>();value.fieldNames().forEachRemaining(actual::add);if(!actual.equals(expected))throw new IOException("unknown/missing explicit profile source fields");
    }
    private static void currentExplicit(ExplicitRequest request,Clock clock)throws IOException{
        Objects.requireNonNull(request);Objects.requireNonNull(clock);
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("explicit profile request is foreign or expired");
    }
    private static final class ExplicitObservation {
        private final java.util.Map<String,SharedSourceFiles.Witness> held=new java.util.TreeMap<>();
        SharedSourceFiles.Witness hold(Path path,long maximum)throws IOException{
            var actual=SharedSourceFiles.observe(path);if(actual.source().bytes()>maximum)throw new IOException("explicit original exceeds finite bound");
            var prior=held.putIfAbsent(actual.source().path(),actual);if(prior!=null&&!prior.equals(actual))throw new IOException("explicit source identity changed");return prior==null?actual:prior;
        }
        SharedSourceFiles.Witness hold(FileRef source)throws IOException{
            var actual=hold(Path.of(source.path()),Long.MAX_VALUE);if(!actual.source().equals(source))throw new IOException("actual explicit source differs from exact input");return actual;
        }
        byte[] read(FileRef source,int maximum)throws IOException{
            Objects.requireNonNull(source);absolute(source.path());digest(source.sha256());require(source.bytes()>=0&&source.bytes()<=maximum,"bounded explicit original required");var actual=hold(source);byte[] raw;try(var input=Files.newInputStream(Path.of(source.path()))){raw=input.readNBytes(maximum+1);}
            if(raw.length!=source.bytes()||!NativeRunProfileRules.sha(raw).equals(source.sha256()))throw new IOException("explicit original changed during complete read");SharedSourceFiles.assertUnchanged(actual);return raw;
        }
        List<SharedSourceFiles.Witness> all(){return List.copyOf(held.values());}
    }

    private static Dlc observeDlc(Path gameRoot,List<SharedSourceFiles.Witness> witnesses)throws IOException{
        Path root=gameRoot.resolve("game/dlc");var files=new ArrayList<FileRef>();var mounts=new java.util.TreeSet<String>();
        if(!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("actual installed DLC declaration directory required");
        try(var walk=Files.walk(root,2)){var iterator=walk.iterator();int count=0;while(iterator.hasNext()){
            Path path=iterator.next();if(++count>8192)throw new IOException("DLC descriptor entry bound exceeded");
            if(root.relativize(path).getNameCount()==2&&path.getFileName().toString().endsWith(".dlc")){
                var ref=FileRef.measure(path);observe(ref,witnesses);files.add(ref);mounts.add(path.getParent().toString());
            }
        }}
        files.sort(Comparator.comparing(FileRef::path));return new Dlc(files,List.copyOf(mounts),"INSTALLED_DESCRIPTORS_ONLY_NOT_ACCOUNT_ENTITLEMENTS_OR_RUNTIME_MOUNTS");
    }
    private static String treeDigest(Path root,List<FileRef> files)throws IOException{
        var tree=ControlBuild.strictMapper().createObjectNode();
        for(var ref:files){var entry=tree.putObject(root.relativize(Path.of(ref.path())).toString().replace('\\','/'));entry.put("size",ref.bytes()).put("sha256",ref.sha256());}
        return NativeRunProfileRules.sha(canonical(tree));
    }
    private static byte[] renderOuter(byte[] bytes,Path production)throws IOException{
        String text=utf8(bytes);if(text.contains("remote_file_id")||java.util.regex.Pattern.compile("(?m)^\\s*path\\s*=").matcher(text).find())
            throw new IOException("formal inner descriptor contains a Workshop ID or path");
        String target=production.toString().replace('\\','/');if(target.indexOf('"')>=0||target.indexOf('\n')>=0||target.indexOf('\r')>=0)throw new IOException("unsafe descriptor path");
        return ("\ufeff"+text.replaceFirst("[\\r\\n]+$","")+"\npath=\""+target+"\"\n").getBytes(StandardCharsets.UTF_8);
    }
    private static PlannedAsset asset(Request request,AssetKind kind,byte[] bytes){return new PlannedAsset(kind,request.profile().resolve(kind.relative()).toString(),bytes);}
    public static Settings settings(Display mode){return new Settings(false,false,false,mode.wire(),"0","2560x1440",mode==Display.WINDOWED?"1280x720":null,"l_simp_chinese","screen_edge_scroll_mode_disabled");}
    public static byte[] settingsBytes(Display mode){
        String windowed=mode==Display.WINDOWED?"\t\"windowed_resolution\"={ version=0 value=\"1280x720\" }\n":"";
        return ("\"game\"={\n\t\"promt_for_tutorial\"={ version=0 enabled=no }\n\t\"prompt_for_china_tutorial\"={ version=0 enabled=no }\n\t\"cloud_save\"={ version=0 enabled=no }\n}\n"+
                "\"Graphics\"={\n\t\"display_mode\"={ version=0 value=\""+mode.wire()+"\" }\n\t\"display_index\"={ version=0 value=\"0\" }\n"+
                "\t\"fullscreen_resolution\"={ version=0 value=\"2560x1440\" }\n"+windowed+"}\n"+
                "\"System\"={\n\t\"language\"={ version=0 value=\"l_simp_chinese\" }\n\t\"screen_edge_scroll_mode\"={ version=0 value=\"screen_edge_scroll_mode_disabled\" }\n}\n").getBytes(StandardCharsets.UTF_8);
    }
    private static void verifyAsset(Path profile,Asset asset)throws IOException{
        Path path=profile.resolve(asset.kind().relative());if(!path.equals(Path.of(asset.original().path()))||!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("profile file escaped the exact closed role path");
        var observed=SharedSourceFiles.observe(path);
        if(!observed.source().equals(asset.original())||!observed.nativeFile().equals(asset.nativeFile()))throw new IOException("actual profile native identity changed");
        SharedSourceFiles.assertUnchanged(observed);
    }
    private static FileRef measure(String path,String hash)throws IOException{var result=FileRef.measure(Path.of(path));if(!result.sha256().equals(hash))throw new IOException("actual source hash differs");return result;}
    private static void observe(FileRef ref,List<SharedSourceFiles.Witness> held)throws IOException{
        var actual=SharedSourceFiles.observe(Path.of(ref.path()));if(!actual.source().equals(ref))throw new IOException("actual source content differs from its pin");held.add(actual);
    }
    private static byte[] read(FileRef ref,int maximum,List<SharedSourceFiles.Witness> held)throws IOException{
        file(ref,maximum);observe(ref,held);byte[] bytes;try(var input=Files.newInputStream(Path.of(ref.path()))){bytes=input.readNBytes(maximum+1);}
        if(bytes.length!=ref.bytes()||!NativeRunProfileRules.sha(bytes).equals(ref.sha256()))throw new IOException("actual source changed during bounded read");
        SharedSourceFiles.assertUnchanged(held.get(held.size()-1));return bytes;
    }
    private static String text(JsonNode value,String field)throws IOException{
        if(value==null||!value.isObject()||!value.has(field)||!value.get(field).isTextual()||value.get(field).textValue().isBlank())
            throw new IOException("actual launcher field missing: "+field);return value.get(field).textValue();
    }
    private static String utf8(byte[] bytes)throws IOException{
        try{String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(bytes)).toString();
            return text.startsWith("\ufeff")?text.substring(1):text;}
        catch(java.nio.charset.CharacterCodingException invalid){throw new IOException("exact UTF-8 source required",invalid);}
    }
    private static void current(Request request,Clock clock)throws IOException{
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!clock.instant().isBefore(Instant.parse(request.reviewAtUtc())))
            throw new IOException("profile request is foreign or expired");
    }
}

