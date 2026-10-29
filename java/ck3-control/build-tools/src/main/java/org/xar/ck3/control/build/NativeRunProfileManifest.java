package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Sole typed Java profile wire. Its v2 digest is distinct from legacy Python v1 fingerprints. */
public final class NativeRunProfileManifest {
    public static final String SCHEMA="xar.java-native-run-profile-environment/v2";
    public static final int MAXIMUM_BYTES=1<<20;
    public static final long MAXIMUM_PRODUCTION_FILE_BYTES=64L<<20,MAXIMUM_PRODUCTION_LOGICAL_BYTES=512L<<20;
    private NativeRunProfileManifest(){ }

    public static final String EXPLICIT_SCHEMA="xar.java-native-run-profile-environment/v3";
    public static final String EXPLICIT_REQUEST_SCHEMA="xar.java-explicit-native-profile-request/v1";
    public enum ProfileKind { ORDINARY_PRODUCTION,SAVED_VANILLA,SAVED_PRODUCT_ONLY,FRESH_FRONTEND_FIXTURE }
    public enum SavedKind { VANILLA,PRODUCT_ONLY }
    public enum DlcDeclaration { ABSENT,DECLARED }
    public sealed interface GameIdentity permits Game,ExplicitGame {
        String rawVersion();String displayVersion();String distribution();String launcherSettings();String launcherSettingsSha256();
        String executable();String executableSha256();String vanillaRules();String vanillaRulesSha256();boolean debugMode();
    }
    /** A declared Saved debug flag is data, not permission; the ordinary Game constructor remains false-only. */
    public record ExplicitGame(String rawVersion,String displayVersion,String distribution,String launcherSettings,
            String launcherSettingsSha256,String executable,String executableSha256,String vanillaRules,
            String vanillaRulesSha256,boolean debugMode) implements GameIdentity {
        public ExplicitGame {new Game(rawVersion,displayVersion,distribution,launcherSettings,launcherSettingsSha256,
                executable,executableSha256,vanillaRules,vanillaRulesSha256,false);}
    }
    public sealed interface ProfileEnvironment permits Manifest,ExplicitManifest {
        String schema();int formatVersion();String machineId();String observedAtUtc();String stateDir();String profileDir();
        GameIdentity game();FileRef producerToolsBuild();List<FileRef> producerRuntime();String environmentSha256();
        @com.fasterxml.jackson.annotation.JsonIgnore ProfileKind kind();
    }
    @com.fasterxml.jackson.annotation.JsonTypeInfo(use=com.fasterxml.jackson.annotation.JsonTypeInfo.Id.NAME,include=com.fasterxml.jackson.annotation.JsonTypeInfo.As.PROPERTY,property="profile_domain")
    @com.fasterxml.jackson.annotation.JsonSubTypes({
        @com.fasterxml.jackson.annotation.JsonSubTypes.Type(value=SavedSource.class,name="SAVED_NATIVE"),
        @com.fasterxml.jackson.annotation.JsonSubTypes.Type(value=FixtureSource.class,name="FRESH_FRONTEND_FIXTURE")})
    public sealed interface ExplicitSource permits SavedSource,FixtureSource { }
    public record SavedSource(SavedKind kind,FileRef productInventory) implements ExplicitSource {
        public SavedSource {Objects.requireNonNull(kind);file(productInventory,MAXIMUM_BYTES);}
    }
    /** Data exported by the sole PreparedFixture owner; this producer verifies physical custody, not fixture policy semantics. */
    public record FixtureSource(FileRef policySource,List<FileRef> immutableInputs,List<String> mountedRelativePaths) implements ExplicitSource {
        public FixtureSource {
            file(policySource,MAXIMUM_BYTES);immutableInputs=List.copyOf(immutableInputs);mountedRelativePaths=List.copyOf(mountedRelativePaths);
            require(!immutableInputs.isEmpty()&&immutableInputs.size()<=8192&&immutableInputs.stream().map(FileRef::path).distinct().count()==immutableInputs.size()
                    &&immutableInputs.contains(policySource),"exact sole fixture source closure required");
            for(var source:immutableInputs){Objects.requireNonNull(source);absolute(source.path());digest(source.sha256());require(source.bytes()>=0&&source.bytes()<=MAXIMUM_PRODUCTION_FILE_BYTES,"bounded actual fixture original required");}
            require(!mountedRelativePaths.isEmpty()&&mountedRelativePaths.size()<=8192
                    &&mountedRelativePaths.stream().distinct().count()==mountedRelativePaths.size(),"complete explicit fixture mounted input paths required");
            for(String path:mountedRelativePaths){relative(path);require(path.startsWith("mod/")||path.startsWith("mod-content/"),"mounted fixture path must belong to its explicit profile");}
        }
    }
    public record ExplicitRequest(String schema,String machineId,String reviewAtUtc,String stateDir,String sourceWorkingDirectory,
            FileRef qualifiedToolsBuild,FileRef gameExecutable,FileRef vanillaRules,FileRef launcherSettings,
            boolean debugMode,ExplicitSource source) {
        public ExplicitRequest {
            require(EXPLICIT_REQUEST_SCHEMA.equals(schema),"exact explicit profile request required");machine(machineId);Instant.parse(reviewAtUtc);
            absolute(stateDir);absolute(sourceWorkingDirectory);file(qualifiedToolsBuild,16L<<20);file(gameExecutable,64L<<30);
            file(vanillaRules,4L<<20);file(launcherSettings,65536);Objects.requireNonNull(source);require(!debugMode||source instanceof SavedSource,"debug is an explicit Saved-only option");
        }
        public Path profile(){return Path.of(stateDir).resolve("profile");}
    }
    public record DeclaredDlc(DlcDeclaration declaration,List<String> disabledDlcs) {
        public DeclaredDlc {Objects.requireNonNull(declaration);disabledDlcs=List.copyOf(disabledDlcs);
            require(disabledDlcs.size()<=2048,"finite declared DLC list required");
            require(declaration!=DlcDeclaration.ABSENT||disabledDlcs.isEmpty(),"absent DLC declaration cannot invent disabled DLC");
            for(String value:disabledDlcs)require(value!=null&&!value.isBlank()&&value.length()<=1024,"actual DLC declaration string required");}
    }
    public record ExplicitLoad(FileRef dlcLoad,List<String> enabledMods,DeclaredDlc declaredDlc) {
        public ExplicitLoad {file(dlcLoad,65536);enabledMods=List.copyOf(enabledMods);Objects.requireNonNull(declaredDlc);
            require(enabledMods.size()<=128,"finite actual ordered mods required");for(String value:enabledMods)require(value!=null&&!value.isBlank()&&value.length()<=1024,"actual ordered descriptor spelling required");}
    }
    public record MountedMod(String enabledDescriptor,SharedSourceFiles.Witness descriptor,String productionRoot) {
        public MountedMod {require(enabledDescriptor!=null&&!enabledDescriptor.isBlank(),"actual enabled descriptor required");Objects.requireNonNull(descriptor);absolute(productionRoot);}
    }
    public record ProductDirectory(String path,SharedSourceFiles.DirectoryIdentity identity,long nativeAllocatedBytes) {
        public ProductDirectory {absolute(path);Objects.requireNonNull(identity);require(nativeAllocatedBytes>=0,"actual directory allocation required");}
    }
    /** Only real enabled product roots/files are retained here. Vanilla has exactly zero roots/files; profileDir is never an alias. */
    public record ExplicitCustody(String profileRoot,SharedSourceFiles.DirectoryIdentity profileIdentity,List<ProductDirectory> directories,
            List<SharedSourceFiles.Witness> productFiles,long logicalBytes,long nativeFileAllocatedBytes,long nativeDirectoryAllocatedBytes,long retainedAllocatedUpperBytes) {
        public ExplicitCustody {
            absolute(profileRoot);Objects.requireNonNull(profileIdentity);directories=List.copyOf(directories);productFiles=List.copyOf(productFiles);
            require(productFiles.size()<=4096&&directories.size()+productFiles.size()<=16384
                    &&directories.stream().map(ProductDirectory::path).distinct().count()==directories.size()
                    &&productFiles.stream().map(row->row.source().path()).distinct().count()==productFiles.size(),"complete finite unique explicit product custody required");
            long logical=0,files=0,dirs=0;for(var row:productFiles){require(row.source().bytes()<=MAXIMUM_PRODUCTION_FILE_BYTES,"bounded actual product file required");logical=Math.addExact(logical,row.source().bytes());files=Math.addExact(files,row.nativeFile().allocatedBytes());}
            for(var row:directories)dirs=Math.addExact(dirs,Math.max(4096,row.nativeAllocatedBytes()));
            require(logical==logicalBytes&&logical<=MAXIMUM_PRODUCTION_LOGICAL_BYTES&&files==nativeFileAllocatedBytes
                    &&dirs==nativeDirectoryAllocatedBytes&&retainedAllocatedUpperBytes==Math.addExact(files,dirs),"actual explicit retained allocation must cover files and all observed directories");
        }
    }
    @com.fasterxml.jackson.annotation.JsonTypeInfo(use=com.fasterxml.jackson.annotation.JsonTypeInfo.Id.NAME,include=com.fasterxml.jackson.annotation.JsonTypeInfo.As.PROPERTY,property="profile_domain")
    @com.fasterxml.jackson.annotation.JsonSubTypes({
        @com.fasterxml.jackson.annotation.JsonSubTypes.Type(value=SavedProfile.class,name="SAVED_NATIVE"),
        @com.fasterxml.jackson.annotation.JsonSubTypes.Type(value=FreshFixtureProfile.class,name="FRESH_FRONTEND_FIXTURE")})
    public sealed interface ExplicitProfile permits SavedProfile,FreshFixtureProfile {
        ExplicitLoad loadProfile();List<MountedMod> mountedMods();ExplicitCustody custody();
    }
    public record SavedProfile(SavedKind kind,FileRef productInventory,ExplicitLoad loadProfile,List<MountedMod> mountedMods,ExplicitCustody custody) implements ExplicitProfile {
        public SavedProfile {
            Objects.requireNonNull(kind);file(productInventory,MAXIMUM_BYTES);Objects.requireNonNull(loadProfile);mountedMods=List.copyOf(mountedMods);Objects.requireNonNull(custody);
            require(mountedMods.stream().map(MountedMod::enabledDescriptor).toList().equals(loadProfile.enabledMods()),"actual ordered descriptor list changed");
            require(kind==SavedKind.VANILLA?mountedMods.isEmpty()&&custody.productFiles().isEmpty()&&custody.directories().isEmpty()
                    :!mountedMods.isEmpty()&&!custody.productFiles().isEmpty(),"explicit Saved inventory kind differs from its actual product domain");
        }
    }
    public record FreshFixtureProfile(FileRef policySource,List<FileRef> immutableInputs,List<String> mountedRelativePaths,
            ExplicitLoad loadProfile,List<MountedMod> mountedMods,ExplicitCustody custody) implements ExplicitProfile {
        public FreshFixtureProfile {
            immutableInputs=List.copyOf(immutableInputs);mountedRelativePaths=List.copyOf(mountedRelativePaths);new FixtureSource(policySource,immutableInputs,mountedRelativePaths);
            Objects.requireNonNull(loadProfile);Objects.requireNonNull(custody);mountedMods=List.copyOf(mountedMods);
            require(!mountedMods.isEmpty()&&mountedMods.stream().map(MountedMod::enabledDescriptor).toList().equals(loadProfile.enabledMods()),"explicit fixture actual ordered mod projection required");
        }
    }
    public record ExplicitManifest(String schema,int formatVersion,String machineId,String observedAtUtc,String stateDir,String profileDir,
            ExplicitGame game,ExplicitRequest request,ExplicitProfile profile,List<SharedSourceFiles.Witness> profileAssets,Dlc dlc,
            List<SharedSourceFiles.Witness> originals,FileRef producerToolsBuild,List<FileRef> producerRuntime,String environmentSha256) implements ProfileEnvironment {
        public ExplicitManifest {
            require(EXPLICIT_SCHEMA.equals(schema)&&formatVersion==3,"exact explicit profile v3 required");machine(machineId);Instant.parse(observedAtUtc);
            absolute(stateDir);absolute(profileDir);require(Path.of(profileDir).equals(Path.of(stateDir).resolve("profile")),"same actual isolated profile required");
            Objects.requireNonNull(game);Objects.requireNonNull(request);Objects.requireNonNull(profile);Objects.requireNonNull(dlc);
            profileAssets=List.copyOf(profileAssets);originals=List.copyOf(originals);producerRuntime=List.copyOf(producerRuntime);file(producerToolsBuild,16L<<20);digest(environmentSha256);
            require(request.machineId().equals(machineId)&&request.stateDir().equals(stateDir)&&request.qualifiedToolsBuild().equals(producerToolsBuild)
                    &&request.gameExecutable().path().equals(game.executable())&&request.gameExecutable().sha256().equals(game.executableSha256())
                    &&request.vanillaRules().path().equals(game.vanillaRules())&&request.vanillaRules().sha256().equals(game.vanillaRulesSha256())
                    &&request.launcherSettings().path().equals(game.launcherSettings())&&request.launcherSettings().sha256().equals(game.launcherSettingsSha256())
                    &&request.debugMode()==game.debugMode()&&profile.custody().profileRoot().equals(profileDir),"explicit common source facts differ from the same request");
            require(producerRuntime.size()==6&&producerRuntime.stream().map(FileRef::path).distinct().count()==6,"same actual complete producer runtime required");
            require(!originals.isEmpty()&&originals.size()<=16384&&originals.stream().map(row->row.source().path()).distinct().count()==originals.size(),"explicit original source closure required");
            if(request.source() instanceof SavedSource saved)require(profile instanceof SavedProfile actual&&actual.kind()==saved.kind()&&actual.productInventory().equals(saved.productInventory()),"Saved source/projection differs");
            else {var fixture=(FixtureSource)request.source();require(profile instanceof FreshFixtureProfile actual&&actual.policySource().equals(fixture.policySource())
                    &&actual.immutableInputs().equals(fixture.immutableInputs())&&actual.mountedRelativePaths().equals(fixture.mountedRelativePaths()),"fixture source/projection differs");}
        }
        @Override public ProfileKind kind(){return profile instanceof SavedProfile saved?(saved.kind()==SavedKind.VANILLA?ProfileKind.SAVED_VANILLA:ProfileKind.SAVED_PRODUCT_ONLY):ProfileKind.FRESH_FRONTEND_FIXTURE;}
        public List<String> productionRoots(){return profile.mountedMods().stream().map(MountedMod::productionRoot).distinct().toList();}
        public List<FileRef> requiredPreparedFileRefs(){
            var refs=new java.util.LinkedHashMap<String,FileRef>();refs.put(profile.loadProfile().dlcLoad().path(),profile.loadProfile().dlcLoad());
            for(var asset:profileAssets)refs.put(asset.source().path(),asset.source());
            if(profile instanceof SavedProfile saved)refs.put(saved.productInventory().path(),saved.productInventory());
            else {var fixture=(FreshFixtureProfile)profile;for(var source:fixture.immutableInputs())refs.put(source.path(),source);}
            return List.copyOf(refs.values());
        }
    }

    public enum Display { FULLSCREEN("fullscreen"),WINDOWED("windowed");
        private final String wire;Display(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public enum AssetKind {
        DLC_LOAD("dlc_load.json",65536),SETTINGS("pdx_settings.txt",65536),TUTORIAL("tutorial.txt",65536),
        OUTER_DESCRIPTOR("mod/xar_autoplayer.mod",65536),PRESETS("player/game_rules/presets.txt",262144);
        private final String relative;private final int maximum;
        AssetKind(String relative,int maximum){this.relative=relative;this.maximum=maximum;}
        public String relative(){return relative;}public int maximumBytes(){return maximum;}
    }
    public record Asset(AssetKind kind,FileRef original,SharedSourceFiles.NativeFile nativeFile){
        public Asset{Objects.requireNonNull(kind);file(original,kind.maximumBytes());Objects.requireNonNull(nativeFile);
            require(nativeFile.logicalBytes()==original.bytes()&&nativeFile.linkCount()==1,
                    "actual ordinary private profile file required");}
    }
    public record Game(String rawVersion,String displayVersion,String distribution,String launcherSettings,
            String launcherSettingsSha256,String executable,String executableSha256,String vanillaRules,
            String vanillaRulesSha256,boolean debugMode) implements GameIdentity{
        public Game{for(String value:List.of(rawVersion,displayVersion,distribution))require(value!=null&&!value.isBlank(),"actual installed launcher identity required");
            for(String value:List.of(launcherSettings,executable,vanillaRules))absolute(value);
            for(String value:List.of(launcherSettingsSha256,executableSha256,vanillaRulesSha256))digest(value);
            require(!debugMode,"production profile cannot silently enable debug");}
    }
    public record ReleaseEntry(String path,long size,String sha256){
        public ReleaseEntry{relative(path);require(size>=0,"actual release size required");digest(sha256);}
    }
    public record ReleaseManifest(int formatVersion,String modVersion,String gitTag,String gitSha,String workshopItemId,List<ReleaseEntry> files){
        public ReleaseManifest{require(formatVersion==2&&modVersion!=null&&modVersion.matches("[0-9]+(?:\\.[0-9]+){1,3}"),"actual formal release version required");
            require(gitSha!=null&&gitSha.matches("[0-9a-f]{40}")&&"3784706360".equals(workshopItemId),"actual original mod release identity required");
            require(gitTag==null||gitTag.equals("v"+modVersion),"release tag differs from actual version");
            files=List.copyOf(files);require(!files.isEmpty()&&files.size()<=4096&&files.stream().map(ReleaseEntry::path).distinct().count()==files.size(),
                    "finite complete unique formal release inventory required");}
    }
    public record TreeDirectory(String path,SharedSourceFiles.DirectoryIdentity identity){
        public TreeDirectory{absolute(path);Objects.requireNonNull(identity);}
    }
    /** Retained immutable input subtree; never charged as six generated profile outputs or omitted from census. */
    public record ProductionTree(String root,List<TreeDirectory> directories,List<SharedSourceFiles.Witness> files,
            long nativeFileAllocatedBytes,long directoryGuardBytes,long retainedAllocatedUpperBytes){
        public ProductionTree{
            absolute(root);directories=List.copyOf(directories);files=List.copyOf(files);
            require(!directories.isEmpty()&&!files.isEmpty()&&files.size()<=4096&&directories.size()+files.size()<=16384,
                    "complete bounded installed production input tree required");
            require(directories.stream().map(TreeDirectory::path).distinct().count()==directories.size()
                    &&files.stream().map(row->row.source().path()).distinct().count()==files.size()
                    &&directories.stream().anyMatch(row->Path.of(row.path()).equals(Path.of(root))),"complete unique directory/file custody required");
            long allocated=0,logical=0;for(var row:files){require(Path.of(row.source().path()).startsWith(Path.of(root))
                        &&row.source().bytes()<=MAXIMUM_PRODUCTION_FILE_BYTES,"production file escaped subtree or finite single-file bound");
                allocated=Math.addExact(allocated,row.nativeFile().allocatedBytes());logical=Math.addExact(logical,row.source().bytes());}
            for(var row:directories)require(Path.of(row.path()).startsWith(Path.of(root)),"production directory escaped subtree");
            require(logical<=MAXIMUM_PRODUCTION_LOGICAL_BYTES&&allocated==nativeFileAllocatedBytes&&directoryGuardBytes>=4096
                    &&retainedAllocatedUpperBytes<=1L<<30
                    &&retainedAllocatedUpperBytes==Math.addExact(allocated,Math.multiplyExact(directoryGuardBytes,directories.size())),
                    "actual retained file allocation and finite directory hold required");
        }
    }
    public record Mod(String name,String gitRevision,String productionPath,String productionManifest,
            String productionManifestSha256,String productionTreeSha256,int productionFileCount,
            String modVersion,String gitTag,String workshopItemId,List<FileRef> completeProductionFiles,ProductionTree productionTree){
        public Mod{require("琉焰卿的永恒轮回".equals(name),"exact production mod required");absolute(productionPath);absolute(productionManifest);
            digest(productionManifestSha256);digest(productionTreeSha256);
            require(gitRevision!=null&&gitRevision.matches("[0-9a-f]{40}"),"actual source revision required");
            completeProductionFiles=List.copyOf(completeProductionFiles);
            Objects.requireNonNull(productionTree);
            require(productionTree.root().equals(productionPath)
                    &&productionTree.files().stream().map(SharedSourceFiles.Witness::source).toList().equals(completeProductionFiles),
                    "production manifest projection and complete native input custody differ");
            require(productionFileCount==completeProductionFiles.size()&&productionFileCount>0&&productionFileCount<=4096,
                    "actual complete production files required");
            new ReleaseManifest(2,modVersion,gitTag,gitRevision,workshopItemId,
                    completeProductionFiles.stream().map(ref->new ReleaseEntry(Path.of(productionPath).relativize(Path.of(ref.path())).toString().replace('\\','/'),ref.bytes(),ref.sha256())).toList());}
    }
    public record Settings(boolean promtForTutorial,boolean promptForChinaTutorial,boolean cloudSave,String displayMode,
            String displayIndex,String fullscreenResolution,String windowedResolution,String language,String screenEdgeScrollMode){
        public Settings{require(!promtForTutorial&&!promptForChinaTutorial&&!cloudSave&&"0".equals(displayIndex)
                &&"2560x1440".equals(fullscreenResolution)&&"l_simp_chinese".equals(language)
                &&"screen_edge_scroll_mode_disabled".equals(screenEdgeScrollMode),"exact managed settings required");
            require((displayMode.equals("fullscreen")&&windowedResolution==null)||(displayMode.equals("windowed")&&"1280x720".equals(windowedResolution)),
                    "explicit matching display settings required");}
    }
    public record LoadProfile(List<String> enabledMods,List<String> disabledDlcs,String outerDescriptor,
            String outerDescriptorSha256,String dlcLoadSha256,String presetsSha256,String pdxSettingsPreparedSha256,Settings pdxSettingsContract){
        public LoadProfile{enabledMods=List.copyOf(enabledMods);disabledDlcs=List.copyOf(disabledDlcs);
            require(enabledMods.equals(List.of("mod/xar_autoplayer.mod"))&&disabledDlcs.isEmpty(),"singleton approved mod and all owned DLC required");
            absolute(outerDescriptor);for(String hash:List.of(outerDescriptorSha256,dlcLoadSha256,presetsSha256,pdxSettingsPreparedSha256))digest(hash);
            Objects.requireNonNull(pdxSettingsContract);}
    }
    public record Dlc(List<FileRef> installedDescriptors,List<String> allowedMountRoots,String scope){
        public Dlc{installedDescriptors=List.copyOf(installedDescriptors);allowedMountRoots=List.copyOf(allowedMountRoots);
            require(installedDescriptors.size()<=2048&&installedDescriptors.stream().map(FileRef::path).distinct().count()==installedDescriptors.size()
                    &&allowedMountRoots.stream().distinct().count()==allowedMountRoots.size(),"finite actual installed DLC descriptor inventory required");
            for(String path:allowedMountRoots)absolute(path);
            require("INSTALLED_DESCRIPTORS_ONLY_NOT_ACCOUNT_ENTITLEMENTS_OR_RUNTIME_MOUNTS".equals(scope),"DLC observation scope changed");}
    }
    public record Manifest(String schema,int formatVersion,String machineId,String observedAtUtc,String stateDir,String profileDir,
            Game game,Mod mod,LoadProfile loadProfile,NativeRunProfileRules.Contract rules,Display display,Dlc dlc,
            List<Asset> profileAssets,FileRef producerToolsBuild,List<FileRef> producerRuntime,String environmentSha256) implements ProfileEnvironment{
        public Manifest{require(SCHEMA.equals(schema)&&formatVersion==2,"exact Java run profile v2 required");machine(machineId);Instant.parse(observedAtUtc);
            absolute(stateDir);absolute(profileDir);require(Path.of(profileDir).equals(Path.of(stateDir).resolve("profile")),"profile must be the exact isolated state child");
            Objects.requireNonNull(game);Objects.requireNonNull(mod);Objects.requireNonNull(loadProfile);Objects.requireNonNull(rules);Objects.requireNonNull(display);Objects.requireNonNull(dlc);
            profileAssets=List.copyOf(profileAssets);producerRuntime=List.copyOf(producerRuntime);
            file(producerToolsBuild,16L<<20);
            require(profileAssets.size()==AssetKind.values().length&&profileAssets.stream().map(Asset::kind).distinct().count()==AssetKind.values().length,
                    "all five actual profile assets required");
            require(producerRuntime.size()==6&&producerRuntime.stream().map(FileRef::path).distinct().count()==6,"complete actual qualified Java producer runtime required");
            digest(environmentSha256);}
        @Override public ProfileKind kind(){return ProfileKind.ORDINARY_PRODUCTION;}
    }

    private static com.fasterxml.jackson.databind.ObjectMapper manifestMapper(){
        var mapper=ControlBuild.strictMapper().enable(com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES,
                com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES,com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_TRAILING_TOKENS,
                com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
                .disable(com.fasterxml.jackson.databind.DeserializationFeature.ACCEPT_FLOAT_AS_INT);
        for(var shape:List.of(com.fasterxml.jackson.databind.cfg.CoercionInputShape.Integer,com.fasterxml.jackson.databind.cfg.CoercionInputShape.Float,
                com.fasterxml.jackson.databind.cfg.CoercionInputShape.Boolean))
            mapper.coercionConfigFor(com.fasterxml.jackson.databind.type.LogicalType.Textual).setCoercion(shape,com.fasterxml.jackson.databind.cfg.CoercionAction.Fail);
        for(var shape:List.of(com.fasterxml.jackson.databind.cfg.CoercionInputShape.String,com.fasterxml.jackson.databind.cfg.CoercionInputShape.Float,
                com.fasterxml.jackson.databind.cfg.CoercionInputShape.Boolean))
            mapper.coercionConfigFor(com.fasterxml.jackson.databind.type.LogicalType.Integer).setCoercion(shape,com.fasterxml.jackson.databind.cfg.CoercionAction.Fail);
        for(var shape:List.of(com.fasterxml.jackson.databind.cfg.CoercionInputShape.String,com.fasterxml.jackson.databind.cfg.CoercionInputShape.Integer,
                com.fasterxml.jackson.databind.cfg.CoercionInputShape.Float))
            mapper.coercionConfigFor(com.fasterxml.jackson.databind.type.LogicalType.Boolean).setCoercion(shape,com.fasterxml.jackson.databind.cfg.CoercionAction.Fail);
        return mapper;
    }
    public static ExplicitRequest decodeExplicitRequest(byte[] raw)throws IOException {
        bounded(raw);try{return manifestMapper().readValue(raw,ExplicitRequest.class);}catch(IllegalArgumentException invalid){throw new IOException("invalid explicit profile request",invalid);}
    }
    public static byte[] encodeExplicitRequest(ExplicitRequest request)throws IOException{return canonical(manifestMapper().valueToTree(request));}
    public static byte[] encodeEnvironment(ProfileEnvironment value)throws IOException {
        if(value instanceof Manifest ordinary)return encode(ordinary);
        ObjectNode tree=manifestMapper().valueToTree((ExplicitManifest)value);
        require(digestOf(tree).equals(value.environmentSha256()),"explicit environment digest differs");byte[] bytes=canonical(tree);bounded(bytes);return bytes;
    }
    public static ObjectNode environmentJson(ProfileEnvironment value)throws IOException{return (ObjectNode)manifestMapper().readTree(encodeEnvironment(value));}
    public static ExplicitManifest sealExplicit(ExplicitManifest value)throws IOException {
        ObjectNode tree=manifestMapper().valueToTree(value);tree.put("environment_sha256",digestOf(tree));
        return (ExplicitManifest)decodeEnvironment(canonical(tree));
    }
    public static ProfileEnvironment decodeEnvironment(byte[] raw)throws IOException {
        bounded(raw);JsonNode tree=manifestMapper().readTree(raw);if(tree==null||!tree.isObject())throw new IOException("profile environment object required");requireSupported(tree);
        if(tree.has("schema")&&EXPLICIT_SCHEMA.equals(tree.get("schema").textValue())){
            ExplicitManifest value=manifestMapper().readValue(raw,ExplicitManifest.class);
            if(!digestOf(tree).equals(value.environmentSha256()))throw new IOException("explicit environment digest differs from original bytes");return value;
        }
        return decode(raw);
    }
    public static ProfileEnvironment readEnvironmentOriginal(FileRef original)throws IOException{return decodeEnvironment(readOriginalBytes(original));}
    private static void bounded(byte[] raw)throws IOException{if(raw==null||raw.length==0||raw.length>MAXIMUM_BYTES)throw new IOException("bounded complete profile wire required");}

    public static byte[] encode(Manifest value)throws IOException{
        ObjectNode object=manifestMapper().valueToTree(value);
        require(digestOf(object).equals(value.environmentSha256()),"environment digest is not the exact typed producer output");
        byte[] raw=canonical(object);require(raw.length<=MAXIMUM_BYTES,"profile environment exceeds explicit 1MiB boundary");return raw;
    }
    public static Manifest seal(Manifest value)throws IOException{
        ObjectNode tree=manifestMapper().valueToTree(value);tree.put("environment_sha256",digestOf(tree));
        return decode(canonical(tree));
    }
    public static Manifest decode(byte[] original)throws IOException{
        if(original==null||original.length==0||original.length>MAXIMUM_BYTES)throw new IOException("bounded exact Java profile required");
        try{Manifest value=manifestMapper().readValue(original,Manifest.class);
            JsonNode tree=manifestMapper().readTree(original);
            if(!digestOf(tree).equals(value.environmentSha256()))throw new IOException("Java environment digest differs from original bytes");
            return value;
        }catch(IllegalArgumentException invalid){throw new IOException("invalid strict Java profile manifest",invalid);}
    }
    /** Immutable data read after launch; settings/tutorial may legitimately be modified by Game.
     * Prepared-file custody is checked separately by NativeRunProfileProducer.readVerified before launch. */
    public static Manifest readOriginal(FileRef original)throws IOException{return decode(readOriginalBytes(original));}
    private static byte[] readOriginalBytes(FileRef original)throws IOException{
        file(original,MAXIMUM_BYTES);var held=SharedSourceFiles.observe(Path.of(original.path()));
        if(!held.source().equals(original))throw new IOException("environment original differs from the selected pin");
        byte[] bytes;try(var input=java.nio.file.Files.newInputStream(Path.of(original.path()))){bytes=input.readNBytes(MAXIMUM_BYTES+1);}
        if(bytes.length!=original.bytes()||!NativeRunProfileRules.sha(bytes).equals(original.sha256()))throw new IOException("environment original changed during complete read");
        SharedSourceFiles.assertUnchanged(held);return bytes;
    }
    public static boolean isCurrentVersion(JsonNode value){return value!=null&&value.isObject()&&value.has("schema")&&value.get("schema").isTextual()&&(SCHEMA.equals(value.get("schema").textValue())||EXPLICIT_SCHEMA.equals(value.get("schema").textValue()));}
    /** The original Python v1 producer had no schema property; unknown versioned wires cannot fall back to it. */
    public static void requireSupported(JsonNode value)throws IOException{
        if(value!=null&&value.isObject()&&value.has("schema")&&!isCurrentVersion(value))
            throw new IOException("unsupported versioned native run profile; no legacy fallback");
        if(value!=null&&value.isObject()&&!value.has("schema")){
            JsonNode version=value.get("format_version");
            if((version!=null&&(!version.isIntegralNumber()||!version.canConvertToInt()||version.intValue()!=1))
                    ||value.has("producer_tools_build")||value.has("producer_runtime")||value.has("profile_assets"))
                throw new IOException("missing current native profile schema cannot downgrade to historical Python data");
        }
    }
    public static byte[] canonical(JsonNode value)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(sorted(value));}
    private static JsonNode sorted(JsonNode value){
        if(value.isObject()){ObjectNode result=ControlBuild.strictMapper().createObjectNode();var values=new TreeMap<String,JsonNode>();value.properties().forEach(e->values.put(e.getKey(),e.getValue()));values.forEach((k,v)->result.set(k,sorted(v)));return result;}
        if(value.isArray()){var result=ControlBuild.strictMapper().createArrayNode();value.forEach(v->result.add(sorted(v)));return result;}return value;
    }
    private static String digestOf(JsonNode value)throws IOException{
        ObjectNode stable=((ObjectNode)value).deepCopy();stable.remove(List.of("observed_at_utc","environment_sha256"));return NativeRunProfileRules.sha(canonical(stable));
    }
    static void absolute(String path){require(path!=null&&Path.of(path).isAbsolute()&&Path.of(path).normalize().equals(Path.of(path)),"normalized absolute source path required");}
    static void relative(String path){require(path!=null&&!path.isBlank()&&!path.contains("\\")&&!Path.of(path).isAbsolute()
            &&Path.of(path).normalize().equals(Path.of(path))&&!path.equals(".")&&!Path.of(path).startsWith(".."),"canonical relative production path required");}
    static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"canonical source digest required");}
    static void machine(String value){require(value!=null&&value.matches("[a-z0-9][a-z0-9-]{0,127}")&&!value.equals("unknown"),"known actual machine required");}
    static void file(FileRef ref,long max){Objects.requireNonNull(ref);absolute(ref.path());digest(ref.sha256());require(ref.bytes()>0&&ref.bytes()<=max,"bounded source file required");}
    static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
}
