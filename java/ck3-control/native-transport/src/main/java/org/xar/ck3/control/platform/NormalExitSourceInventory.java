package org.xar.ck3.control.platform;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.*;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Actual source inventory reader/builder. DATA output never substitutes for the private same-managed-Game qualification. */
public final class NormalExitSourceInventory {
    public static final String BASENAME="normal-exit-source-inventory-v1.json",PROJECTION_BASENAME="normal-exit-profile-binding-projection-v1.json",SCHEMA="ck3-normal-exit-source-inventory-v1";
    private static final int INVENTORY_MAX_BYTES=4<<20;
    public static final String JAVA_SETTINGS_RELATIVE="java-original-inputs/profile/pdx_settings.txt";
    private static final List<String> STOCK=List.of("gui/hud.gui","gui/frontend_ingame_menu.gui","gui/window_resign_confirmation.gui","gui/shared/buttons_icons.gui","gui/shared/buttons.gui","gui/shared/sounds.gui");
    private static final Set<String> PROJECTION=Set.of("schema_version","guard_profile","guard_profile_sha256","userdir","evidence_directory","game_version","state_directory","dll","injector");
    private static final Set<String> INVENTORY=Set.of("schema","userdir","profile_binding_sha256","settings_file","dlc_load","stock_game_root","source_executable","stock_gui","enabled_mods");
    public record Input(ExactRef inventory,ExactRef originalManagedProfile,ExactRef immutableOriginalSettingsSnapshot){public Input{Objects.requireNonNull(inventory);Objects.requireNonNull(originalManagedProfile);Objects.requireNonNull(immutableOriginalSettingsSnapshot);}}
    public record Built(RawJson inventory,RawJson profileProjection,List<ExactRef> originals){public Built{Objects.requireNonNull(inventory);Objects.requireNonNull(profileProjection);originals=List.copyOf(originals);}}
    /** Static projection only. The Bootstrap writer must first CREATE_NEW/read back this exact guard. */
    public static final class Projection {
        private final RawJson guard;private final ObjectNode fields;private final Path guardPath;
        private Projection(RawJson guard,ObjectNode fields,Path guardPath){this.guard=guard;this.fields=fields.deepCopy();this.guardPath=guardPath;}
        public RawJson guard(){return guard;}
        public RawJson managedProfile(ExactRef writtenGuard)throws IOException{
            require(Path.of(writtenGuard.path()).toRealPath().equals(guardPath)&&new RawJson(readExact(writtenGuard,1<<20)).equals(guard),"actual CREATE_NEW/read-back target binding required before profile projection");
            var result=fields.deepCopy().put("guard_profile",writtenGuard.path()).put("guard_profile_sha256",writtenGuard.sha256());return new RawJson(StrictJson.canonical(result));
        }
    }
    /** Java source provenance has its own schema; ENV is never labelled as a legacy public preparation/runtime manifest. */
    public static Projection project(ExactRef actualNativePlan,Path guardDestination,ExactRef originalSettingsSnapshot)throws IOException{
        var plan=NativeLaunchPlan.readExact(actualNativePlan,new NativeBridgeLaunchEvidence());plan.preparedProfile().verify(plan);
        var environment=org.xar.ck3.control.build.NativeRunProfileManifest.readOriginal(plan.preparedProfile().environmentManifest());
        require(Path.of(environment.profileDir()).toRealPath().equals(plan.profileDirectory().toRealPath())&&Path.of(environment.stateDir()).toRealPath().equals(plan.stateDirectory().toRealPath()),"actual environment/profile projection mismatch");
        require(guardDestination.isAbsolute()&&guardDestination.normalize().equals(guardDestination),"absolute new target binding destination required");SharedSourceFiles.plainAncestors(guardDestination.getParent());require(!Files.exists(guardDestination,LinkOption.NOFOLLOW_LINKS),"target binding must have its own new output path");
        Path settings=plan.profileDirectory().resolve("pdx_settings.txt").toRealPath();var originals=plan.preparedProfile().preparedInputs().stream().filter(ref->Path.of(ref.path()).toAbsolutePath().normalize().equals(settings)).toList();
        require(originals.size()==1&&Path.of(originalSettingsSnapshot.path()).toRealPath().equals(plan.evidenceRoot().resolve(JAVA_SETTINGS_RELATIVE).toRealPath())&&!Path.of(originalSettingsSnapshot.path()).toRealPath().equals(settings)&&originals.getFirst().bytes()==originalSettingsSnapshot.bytes()
                &&originals.getFirst().sha256().equals(originalSettingsSnapshot.sha256()),"independent actual immutable original-settings snapshot must precede the Java projection");readExact(originalSettingsSnapshot,16<<20);
        var target=plan.sources().review().gameExecutable();var guard=StrictJson.object().put("schema","xar.java.normal-exit-static-target-binding/v3").put("static_source_binding_only",true).put("launch_authority",false);
        guard.putObject("target").put("executable",target.path()).put("executable_sha256",target.sha256());guard.set("original_native_plan",actualNativePlan.toJson());
        var env=plan.preparedProfile().environmentManifest();guard.set("original_environment",new ExactRef(env.path(),env.bytes(),env.sha256()).toJson());
        guard.set("original_settings_snapshot",originalSettingsSnapshot.toJson());
        var profile=StrictJson.object().put("schema_version",1).put("userdir",plan.profileDirectory().toRealPath().toString()).put("state_directory",plan.stateDirectory().toRealPath().toString())
                .put("evidence_directory",plan.evidenceRoot().toRealPath().toString()).put("game_version",environment.game().rawVersion());
        for(var pair:List.of(Map.entry("dll",plan.sources().review().bridgeDll()),Map.entry("injector",plan.sources().review().injector())))profile.putObject(pair.getKey()).put("path",pair.getValue().path()).put("sha256",pair.getValue().sha256());
        return new Projection(new RawJson(StrictJson.canonical(guard)),profile,guardDestination);
    }
    /** Final profile references the actual fixed inventory; it never embeds an in-memory guard. */
    public static RawJson withInventory(RawJson actualProfile,ExactRef writtenInventory)throws IOException{
        var value=profile(actualProfile);require(Path.of(writtenInventory.path()).toRealPath().equals(path(value,"userdir").resolve(BASENAME).toRealPath()),"fixed actual inventory output required");
        var inventory=FullJsonTree.parse(readExact(writtenInventory,INVENTORY_MAX_BYTES),INVENTORY_MAX_BYTES);require(SCHEMA.equals(text(inventory,"schema")),"actual normal-exit inventory schema required");
        value.remove("guard");value.putObject("normal_exit_source_inventory").put("path",writtenInventory.path()).put("sha256",writtenInventory.sha256());return new RawJson(StrictJson.canonical(value));
    }
    public static final class Qualified {
        private final Input input;private final ManagedGameSession owner;private final Built original;private final List<CapturedSource> custody;
        private Qualified(Input input,ManagedGameSession owner,Built original)throws IOException{this.input=input;this.owner=owner;this.original=original;var captured=new ArrayList<CapturedSource>();for(var ref:originals())captured.add(new CapturedSource(ref,SharedSourceFiles.nativeFile(Path.of(ref.path()))));custody=List.copyOf(captured);}
        public String sha256(){return input.inventory().sha256();}public Input input(){return input;}
        public List<ExactRef> originals(){var refs=new LinkedHashSet<>(original.originals());refs.addAll(List.of(input.inventory(),input.originalManagedProfile(),input.immutableOriginalSettingsSnapshot()));return List.copyOf(refs);}
        public void requireCurrent(ManagedGameSession actual)throws IOException{require(owner==actual,"normal-exit inventory belongs to another actual managed Game");requireCustody();Built fresh=verify(input,actual);requireCustody();require(fresh.inventory().equals(original.inventory())&&fresh.profileProjection().equals(original.profileProjection()),"normal-exit source inventory changed");}
        private void requireCustody()throws IOException{for(var source:custody)require(source.nativeFile().equals(SharedSourceFiles.nativeFile(Path.of(source.ref().path()))),"normal-exit original native file identity/time changed");}
    }
    private record CapturedSource(ExactRef ref,SharedSourceFiles.NativeFile nativeFile){}
    private NormalExitSourceInventory(){}
    /** Sole prelaunch source producer. Bootstrap writes its bytes through the actual finite CREATE_NEW writer, never this reader. */
    public static Built build(RawJson originalManagedProfile,Path stockGameRoot)throws IOException{
        var profile=profile(originalManagedProfile);return scan(profile,absolute(stockGameRoot),Optional.empty(),true);
    }
    /** Static input check only; it does not mint a Game, loaded-source or dispatch proof. */
    public static void inspect(Input input)throws IOException{verifyStatic(input);}
    public static Qualified accept(Input input,ManagedGameSession actual)throws IOException{
        Objects.requireNonNull(actual).verify();Built read=verify(input,actual);var result=new Qualified(input,actual,read);result.requireCurrent(actual);actual.verify();return result;
    }
    private static Built verify(Input input,ManagedGameSession actual)throws IOException{
        var plan=actual.launchPlan();Path settings=plan.profileDirectory().resolve("pdx_settings.txt").toRealPath();
        Path snapshotPath=Path.of(input.immutableOriginalSettingsSnapshot().path());var snapshotBefore=SharedSourceFiles.nativeFile(snapshotPath);
        var gameBirth=new BigInteger(actual.identity().creationFiletimeDecimal());
        requireSnapshotBeforeGame(snapshotBefore,SharedSourceFiles.nativeFile(settings),gameBirth);
        Built read=verifyStatic(input);var profile=profile(new RawJson(readExact(input.originalManagedProfile(),1<<20)));
        require(path(profile,"userdir").equals(plan.profileDirectory().toRealPath())&&path(profile,"state_directory").equals(plan.stateDirectory().toRealPath()),"normal-exit original prepared profile differs from the actual allocated Java plan");
        var target=profile.path("guard").path("target");require(path(target,"executable").equals(Path.of(plan.sources().review().gameExecutable().path()).toRealPath())
                &&text(target,"executable_sha256").equalsIgnoreCase(plan.sources().review().gameExecutable().sha256()),"normal-exit executable differs from actual managed source");
        for(var pair:List.of(Map.entry("dll",plan.sources().review().bridgeDll()),Map.entry("injector",plan.sources().review().injector()))){var row=profile.get(pair.getKey());
            require(path(row,"path").equals(Path.of(pair.getValue().path()).toRealPath())&&text(row,"sha256").equalsIgnoreCase(pair.getValue().sha256()),"normal-exit binary differs from actual managed deployment");}
        var inventory=FullJsonTree.parse(read.inventory().bytes(),INVENTORY_MAX_BYTES);
        var launch=plan.preparedProfile().preparedInputs().stream().filter(ref->Path.of(ref.path()).toAbsolutePath().normalize().equals(settings)).toList();
        require(launch.size()==1&&launch.getFirst().bytes()==input.immutableOriginalSettingsSnapshot().bytes()
                &&launch.getFirst().sha256().equals(input.immutableOriginalSettingsSnapshot().sha256()),"immutable settings snapshot differs from actual original launch pin; current settings cannot be re-pinned");
        Path stock=Path.of(plan.sources().review().gameExecutable().path()).toRealPath().getParent().getParent().resolve("game").toRealPath();
        require(path(inventory,"stock_game_root").equals(stock),"stock normal-exit sources are outside actual installed Game");
        var snapshotAfter=SharedSourceFiles.nativeFile(snapshotPath);
        require(snapshotBefore.equals(snapshotAfter),"immutable original settings identity/time changed during actual Game qualification");
        requireSnapshotBeforeGame(snapshotAfter,SharedSourceFiles.nativeFile(settings),gameBirth);
        actual.verify();return read;
    }
    /** DATA comparison only. The private caller supplies the actual original Game birth and freshly read native files. */
    static void requireSnapshotBeforeGame(SharedSourceFiles.NativeFile snapshot,SharedSourceFiles.NativeFile live,BigInteger gameBirth){
        Objects.requireNonNull(snapshot);Objects.requireNonNull(live);Objects.requireNonNull(gameBirth);
        require(gameBirth.signum()>0&&gameBirth.compareTo(StrictJson.UINT64_MAX)<=0,"actual positive uint64 Game creation FILETIME required");
        require(!snapshot.identityKey().equals(live.identityKey()),"immutable original settings must be an independent native file, not the live output");
        var created=new BigInteger(snapshot.creationFiletimeDecimal());var written=new BigInteger(snapshot.lastWriteFiletimeDecimal());
        require(created.signum()>0&&written.signum()>0&&created.compareTo(gameBirth)<=0&&written.compareTo(gameBirth)<=0,
                "immutable original settings must actually exist with its final bytes before the original managed Game birth");
    }
    private static Built verifyStatic(Input input)throws IOException{
        Objects.requireNonNull(input);RawJson rawProfile=new RawJson(readExact(input.originalManagedProfile(),1<<20));var profile=profile(rawProfile);
        Path userdir=path(profile,"userdir");require(Path.of(input.inventory().path()).toRealPath().equals(userdir.resolve(BASENAME).toRealPath()),"normal-exit inventory is not the fixed managed-userdir original");
        var inventory=FullJsonTree.parse(readExact(input.inventory(),INVENTORY_MAX_BYTES),INVENTORY_MAX_BYTES);var keys=new HashSet<>(INVENTORY);boolean dependencies=inventory.has("stock_gui_dependencies");if(dependencies)keys.add("stock_gui_dependencies");StrictJson.object(inventory,keys);
        if(profile.path("guard").has("schema"))require(ExactRef.fromJson(profile.path("guard").get("original_settings_snapshot")).equals(input.immutableOriginalSettingsSnapshot()),"Java guard and configured immutable settings snapshot must be the identical original");
        if(profile.has("normal_exit_source_inventory")){var declared=StrictJson.object(profile.get("normal_exit_source_inventory"),Set.of("path","sha256"));require(path(declared,"path").equals(Path.of(input.inventory().path()).toRealPath())&&text(declared,"sha256").equals(input.inventory().sha256()),"final managed profile references another inventory original");}
        require(SCHEMA.equals(text(inventory,"schema"))&&path(inventory,"userdir").equals(userdir),"normal-exit source inventory identity differs");
        var settings=StrictJson.object(inventory.get("settings_file"),Set.of("path","bytes","sha256"));
        require(path(settings,"path").equals(userdir.resolve("pdx_settings.txt").toRealPath()),"only exact top-level launch settings can be game-owned output");
        byte[] snapshot=readExact(input.immutableOriginalSettingsSnapshot(),16<<20);
        require(snapshot.length==StrictJson.integer(settings.get("bytes"),0,16<<20)&&ActionCodec.sha256(snapshot).equals(text(settings,"sha256")),"retained immutable launch settings bytes changed");
        // The live output is observed separately; its current bytes are never used to repair the original pin.
        measured(userdir.resolve("pdx_settings.txt"),16<<20,new ArrayList<>());
        Built rebuilt=scan(profile,path(inventory,"stock_game_root"),Optional.of(settings),dependencies);
        require(FullJsonTree.parse(rebuilt.inventory().bytes(),INVENTORY_MAX_BYTES).equals(inventory),"actual normal-exit source files/order/full mod census differ from the original inventory");
        var originals=new ArrayList<>(rebuilt.originals());var projection=measured(userdir.resolve(PROJECTION_BASENAME),1<<20,originals);
        require(new RawJson(readExact(projection,1<<20)).equals(rebuilt.profileProjection()),"actual native fixed profile projection bytes differ from the original canonical nine fields");return new Built(rebuilt.inventory(),rebuilt.profileProjection(),originals);
    }
    private static ObjectNode profile(RawJson raw)throws IOException{
        var parsed=StrictJson.parse(raw.bytes(),1<<20);if(!(parsed instanceof ObjectNode value))throw new IllegalArgumentException("actual original managed profile object required");var keys=new HashSet<>(PROJECTION);if(value.has("guard"))keys.add("guard");if(value.has("normal_exit_source_inventory"))keys.add("normal_exit_source_inventory");StrictJson.object(value,keys);
        StrictJson.integer(value.get("schema_version"),1,1);for(String key:List.of("guard_profile","userdir","evidence_directory","state_directory"))path(value,key);
        for(String key:List.of("dll","injector")){var binary=StrictJson.object(value.get(key),Set.of("path","sha256"));path(binary,"path");sha(text(binary,"sha256"));}
        text(value,"game_version");sha(text(value,"guard_profile_sha256"));var refs=new ArrayList<ExactRef>();ExactRef guardRef=measured(path(value,"guard_profile"),1<<20,refs);
        require(guardRef.sha256().equals(text(value,"guard_profile_sha256")),"actual original target binding changed");var guard=StrictJson.parse(readExact(guardRef,1<<20));
        require(guard.isObject()&&guard.path("target").isObject()&&guard.path("static_source_binding_only").isBoolean()&&guard.path("static_source_binding_only").booleanValue()
                &&guard.path("launch_authority").isBoolean()&&!guard.path("launch_authority").booleanValue(),"static target binding is not launch authority");
        var target=StrictJson.object(guard.get("target"),Set.of("executable","executable_sha256"));path(target,"executable");sha(text(target,"executable_sha256"));
        if(guard.has("schema")){StrictJson.object(guard,Set.of("schema","target","static_source_binding_only","launch_authority","original_native_plan","original_environment","original_settings_snapshot"));
            require("xar.java.normal-exit-static-target-binding/v3".equals(text(guard,"schema")),"unknown versioned static target binding; never fall back to legacy");
            var plan=NativeLaunchPlanCodec.fromJson(StrictJson.parse(readExact(ExactRef.fromJson(guard.get("original_native_plan")),1<<20)));
            var envRef=ExactRef.fromJson(guard.get("original_environment"));var env=org.xar.ck3.control.build.NativeRunProfileManifest.readOriginal(new ControlBuild.FileRef(envRef.path(),envRef.bytes(),envRef.sha256()));
            var selected=plan.preparedProfile().environmentManifest();require(selected.path().equals(envRef.path())&&selected.bytes()==envRef.bytes()&&selected.sha256().equals(envRef.sha256())
                    &&plan.profileDirectory().toRealPath().equals(path(value,"userdir"))&&plan.stateDirectory().toRealPath().equals(path(value,"state_directory"))&&plan.evidenceRoot().toRealPath().equals(path(value,"evidence_directory"))
                    &&env.profileDir().equals(plan.profileDirectory().toString())&&env.stateDir().equals(plan.stateDirectory().toString())&&env.game().rawVersion().equals(text(value,"game_version"))
                    &&Path.of(plan.review().gameExecutable().path()).toRealPath().equals(path(guard.path("target"),"executable"))&&plan.review().gameExecutable().sha256().equals(text(guard.path("target"),"executable_sha256")),"Java target binding lost its actual NativePlan/environment origins");
            for(var pair:List.of(Map.entry("dll",plan.review().bridgeDll()),Map.entry("injector",plan.review().injector())))require(path(value.get(pair.getKey()),"path").equals(Path.of(pair.getValue().path()).toRealPath())&&text(value.get(pair.getKey()),"sha256").equals(pair.getValue().sha256()),"Java static profile binary origin changed");}
        if(guard.has("schema")){var snapshot=ExactRef.fromJson(guard.get("original_settings_snapshot"));readExact(snapshot,16<<20);var configuration=NativeLaunchPlanCodec.fromJson(StrictJson.parse(readExact(ExactRef.fromJson(guard.get("original_native_plan")),1<<20)));
            Path settings=path(value,"userdir").resolve("pdx_settings.txt").toRealPath();var originals=configuration.preparedProfile().preparedInputs().stream().filter(ref->Path.of(ref.path()).toAbsolutePath().normalize().equals(settings)).toList();
            require(originals.size()==1&&Path.of(snapshot.path()).toRealPath().equals(configuration.evidenceRoot().resolve(JAVA_SETTINGS_RELATIVE).toRealPath())&&!Path.of(snapshot.path()).toRealPath().equals(settings)&&originals.getFirst().bytes()==snapshot.bytes()&&originals.getFirst().sha256().equals(snapshot.sha256()),"Java immutable snapshot differs from its actual original NativePlan settings pin/path");}
        if(value.has("guard"))require(value.get("guard").equals(guard),"in-memory target differs from the actual original target binding");value.set("guard",guard);return value;
    }
    private static Built scan(ObjectNode profile,Path game,Optional<ObjectNode> retainedSettings,boolean withDependencies)throws IOException{
        var refs=new ArrayList<ExactRef>();measured(path(profile,"guard_profile"),1<<20,refs);var guard=profile.get("guard");
        for(String field:List.of("original_native_plan","original_environment","original_settings_snapshot","runtime_manifest","public_preparation"))if(guard.has(field)){var original=ExactRef.fromJson(guard.get(field));readExact(original,field.equals("original_settings_snapshot")?16<<20:1<<20);refs.add(original);}
        Path user=path(profile,"userdir");var projection=StrictJson.object();PROJECTION.stream().sorted().forEach(key->projection.set(key,profile.get(key)));
        var out=StrictJson.object().put("schema",SCHEMA).put("userdir",user.toString()).put("profile_binding_sha256",ActionCodec.sha256(StrictJson.canonical(projection)));
        out.set("settings_file",retainedSettings.isPresent()?retainedSettings.orElseThrow():row(measured(user.resolve("pdx_settings.txt"),16<<20,refs)));
        ExactRef dlc=measured(user.resolve("dlc_load.json"),1<<20,refs);out.set("dlc_load",row(dlc));var enabled=StrictJson.parse(readExact(dlc,1<<20)).get("enabled_mods");require(enabled!=null&&enabled.isArray()&&enabled.size()<=64,"actual bounded native enabled mod list required");
        var target=profile.path("guard").path("target");ExactRef exe=measured(path(target,"executable"),512<<20,refs);require(exe.sha256().equalsIgnoreCase(text(target,"executable_sha256")),"inventoried executable differs from original exact target");
        out.put("stock_game_root",game.toString());out.set("source_executable",StrictJson.object().put("path",exe.path()).put("sha256",exe.sha256()));
        var stock=out.putArray("stock_gui");for(String relative:STOCK)stock.add(row(measured(game.resolve(relative),16<<20,refs)));
        Gui closure=withDependencies?gui(game,refs):null;if(closure!=null){var dependencies=out.putArray("stock_gui_dependencies");for(String relative:closure.dependencies())dependencies.add(row(measured(game.resolve(relative),16<<20,refs)));}
        var mods=out.putArray("enabled_mods");Set<Path> roots=new HashSet<>();
        for(var name:enabled){require(name.isTextual(),"enabled registration must be text");String registration=relative(name.textValue());Path outer=user.resolve(registration).normalize();require(outer.startsWith(user),"mod registration escaped userdir");ExactRef outerRef=measured(outer,1<<20,refs);
            String descriptor=utf8(readExact(outerRef,1<<20));rejectDescriptor(descriptor);var matcher=Pattern.compile("(?m)^\\s*path\\s*=\\s*\"([^\"\\r\\n]+)\"").matcher(descriptor);require(matcher.find(),"outer mod descriptor lacks exact mount path");Path root=absolute(Path.of(matcher.group(1)));require(!matcher.find()&&roots.add(root),"ambiguous/duplicate enabled mod root");
            ExactRef inner=measured(root.resolve("descriptor.mod"),1<<20,refs);String inside=utf8(readExact(inner,1<<20));rejectDescriptor(inside);require(!Pattern.compile("(?m)^\\s*path\\s*=").matcher(inside).find(),"inner mod descriptor chooses a mount path");
            var mod=mods.addObject().put("registration",registration).put("root",root.toString());mod.set("outer_descriptor",row(outerRef));mod.set("inner_descriptor",row(inner));var files=mod.putArray("files");
            Set<String> unique=new HashSet<>();for(Path file:files(root)){String rel=root.relativize(file).toString().replace('\\','/');require(unique.add(rel.toLowerCase(Locale.ROOT)),"duplicate case-insensitive mod path");ExactRef original=measured(file,64<<20,refs);var entry=files.addObject().put("relative_path",rel).put("bytes",original.bytes()).put("sha256",original.sha256());
                if(rel.toLowerCase(Locale.ROOT).endsWith(".gui")){require(closure!=null,"GUI mod requires actual stock dependency inventory");closure.requireUnrelated(rel,utf8(readExact(original,64<<20)));}}
        }
        return new Built(new RawJson(FullJsonTree.encode(out,INVENTORY_MAX_BYTES)),new RawJson(StrictJson.canonical(projection)),List.copyOf(new LinkedHashSet<>(refs)));
    }
    private static void rejectDescriptor(String text){require(!Pattern.compile("(?m)^\\s*(replace_path|archive)\\s*=").matcher(text).find(),"mod descriptor replaces exit paths or uses an unverified archive");}
    private record Definition(String path,Set<String> references){}
    private record Gui(Set<String> symbols,List<String> dependencies,Set<String> protectedPaths){
        void requireUnrelated(String relative,String content)throws IOException{require(!protectedPaths.contains(relative.toLowerCase(Locale.ROOT)),"mod overrides protected normal-exit GUI path");var tokens=tokens(content);var pairs=pairs(tokens);
            for(String name:definitions(tokens,pairs).keySet())require(!symbols.contains(name),"mod overrides normal-exit GUI type/template");
            for(String root:List.of("timeline_widget","ingame_pausemenu","ingame_resign_confirmation"))require(named(tokens,pairs,root).isEmpty(),"mod redefines native fixed exit root");
            var callback=Pattern.compile("\\b(?:PauseMenu|ResignConfirmationWindow)\\s*\\.|\\bOnPauseMenu\\b");for(String token:tokens)require(!callback.matcher(value(token)).find(),"mod references native exit callbacks");}
    }
    private static Gui gui(Path root,List<ExactRef> originals)throws IOException{
        Map<String,List<Definition>> providers=new HashMap<>();Set<String> seeds=new HashSet<>();Map<String,String> fixed=Map.of("gui/hud.gui","timeline_widget","gui/frontend_ingame_menu.gui","ingame_pausemenu","gui/window_resign_confirmation.gui","ingame_resign_confirmation");
        for(Path source:files(root.resolve("gui"))){if(!source.toString().toLowerCase(Locale.ROOT).endsWith(".gui"))continue;String relative=root.relativize(source).toString().replace('\\','/');var t=tokens(utf8(readExact(measured(source,16<<20,originals),16<<20)));var p=pairs(t);
            for(var declaration:definitions(t,p).entrySet())providers.computeIfAbsent(declaration.getKey(),ignored->new ArrayList<>()).add(new Definition(relative,declaration.getValue()));
            if(fixed.containsKey(relative)){var blocks=named(t,p,fixed.get(relative));require(blocks.size()==1,"stock native exit root is not unique");var block=blocks.getFirst();seeds.addAll(references(t.subList(Math.max(0,block[0]-2),block[1]+1)));}}
        var pending=new ArrayDeque<String>();for(String seed:seeds)if(providers.containsKey(seed))pending.add(seed);Set<String> symbols=new HashSet<>(),paths=new HashSet<>();
        while(!pending.isEmpty()){String symbol=pending.removeFirst();if(!symbols.add(symbol))continue;for(Definition provider:providers.get(symbol)){paths.add(provider.path());for(String ref:provider.references())if(providers.containsKey(ref)&&!symbols.contains(ref))pending.add(ref);}}
        var dependencies=paths.stream().filter(path->!STOCK.contains(path)).sorted().toList();var protectedPaths=new HashSet<String>();paths.forEach(path->protectedPaths.add(path.toLowerCase(Locale.ROOT)));STOCK.forEach(path->protectedPaths.add(path.toLowerCase(Locale.ROOT)));return new Gui(Set.copyOf(symbols),dependencies,Set.copyOf(protectedPaths));
    }
    private static List<String> tokens(String content){var matcher=Pattern.compile("#[^\\r\\n]*|\"(?:\\\\.|[^\"\\\\])*\"|[{}=]|[^\\s{}=#]+").matcher(content);var result=new ArrayList<String>();while(matcher.find()){String token=matcher.group();if(!token.startsWith("#"))result.add(token);}return result;}
    private static Map<Integer,Integer> pairs(List<String> tokens){var stack=new ArrayDeque<Integer>();var pairs=new HashMap<Integer,Integer>();for(int i=0;i<tokens.size();i++){if(tokens.get(i).equals("{"))stack.push(i);else if(tokens.get(i).equals("}")){require(!stack.isEmpty(),"unmatched GUI closing brace");pairs.put(stack.pop(),i);}}require(stack.isEmpty(),"unmatched GUI opening brace");return pairs;}
    private static Map<String,Set<String>> definitions(List<String> tokens,Map<Integer,Integer> pairs){var out=new HashMap<String,Set<String>>();for(int i=0;i+2<tokens.size();i++){if(!Set.of("type","template").contains(tokens.get(i).toLowerCase(Locale.ROOT)))continue;String name=value(tokens.get(i+1)).toLowerCase(Locale.ROOT);if(!name.matches("[A-Za-z_][A-Za-z_0-9]*"))continue;int start=i+2;while(start<tokens.size()&&!Set.of("{","}").contains(tokens.get(start)))start++;require(start<tokens.size()&&tokens.get(start).equals("{"),"GUI declaration missing block");Set<String> refs=references(tokens.subList(i+2,pairs.get(start)+1));refs.remove(name);out.computeIfAbsent(name,ignored->new HashSet<>()).addAll(refs);}return out;}
    private static List<int[]> named(List<String> tokens,Map<Integer,Integer> pairs,String name){var stack=new ArrayDeque<Integer>();var out=new ArrayList<int[]>();for(int i=0;i<tokens.size();i++){String token=tokens.get(i);if(token.equals("{"))stack.push(i);else if(token.equals("}"))stack.pop();else if(!stack.isEmpty()&&token.equalsIgnoreCase("name")&&i+2<tokens.size()&&tokens.get(i+1).equals("=")&&value(tokens.get(i+2)).equalsIgnoreCase(name))out.add(new int[]{stack.peek(),pairs.get(stack.peek())});}return out;}
    private static Set<String> references(List<String> tokens){var out=new HashSet<String>();for(String token:tokens){String value=value(token);if(value.matches("[A-Za-z_][A-Za-z_0-9]*"))out.add(value.toLowerCase(Locale.ROOT));}return out;}
    private static String value(String token){return token.startsWith("\"")?token.substring(1,token.length()-1):token;}
    private static List<Path> files(Path root)throws IOException{root=absolute(root);var result=new ArrayList<Path>();try(var walk=Files.walk(root)){var it=walk.iterator();int count=0;while(it.hasNext()){Path file=it.next();require(++count<=32768,"finite complete source tree required");SharedSourceFiles.plainAncestors(file);if(Files.isRegularFile(file))result.add(file.toRealPath());}}result.sort(Comparator.comparing(path->path.toString().replace('\\','/')));return List.copyOf(result);}
    private static ExactRef measured(Path path,int maximum,List<ExactRef> refs)throws IOException{path=absolute(path);var before=SharedSourceFiles.nativeFile(path);
        require(before.logicalBytes()<=maximum,"bounded regular source required");var actual=ControlBuild.FileRef.measure(path);var after=SharedSourceFiles.nativeFile(path);
        require(actual.bytes()==before.logicalBytes()&&before.equals(after),"actual native source identity/content changed while hashing");
        ExactRef ref=new ExactRef(path.toString(),actual.bytes(),actual.sha256());refs.add(ref);return ref;}
    private static byte[] readExact(ExactRef ref,int maximum)throws IOException{Path path=Path.of(ref.path());var before=SharedSourceFiles.nativeFile(path);byte[] raw=bounded(path,maximum);require(raw.length==ref.bytes()&&ActionCodec.sha256(raw).equals(ref.sha256())&&before.equals(SharedSourceFiles.nativeFile(path)),"actual source bytes/native identity changed: "+ref.path());return raw;}
    private static byte[] bounded(Path path,int maximum)throws IOException{SharedSourceFiles.plainAncestors(path);long size=Files.size(path);require(size>=0&&size<=maximum,"bounded source required");try(var in=Files.newInputStream(path)){byte[] raw=in.readNBytes(maximum+1);require(raw.length==size,"source changed during read");return raw;}}
    private static ObjectNode row(ExactRef ref){return ref.toJson();}
    private static Path absolute(Path path)throws IOException{require(path.isAbsolute(),"absolute source path required");SharedSourceFiles.plainAncestors(path);return path.toRealPath();}
    private static Path path(JsonNode object,String key)throws IOException{return absolute(Path.of(text(object,key)));}
    private static String relative(String value){require(!value.isBlank()&&!value.contains("\\")&&!Path.of(value).isAbsolute(),"normalized relative source path required");for(Path component:Path.of(value))require(!Set.of(".","..").contains(component.toString()),"source path escaped root");return value;}
    private static String text(JsonNode value,String key){return StrictJson.text(value.get(key));}
    private static void sha(String value){require(value.matches("[0-9a-f]{64}"),"canonical SHA256 required");}
    private static String utf8(byte[] bytes)throws IOException{try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString().replaceFirst("^\\uFEFF","");}catch(java.nio.charset.CharacterCodingException invalid){throw new IOException("actual UTF8 GUI/descriptor required",invalid);}}
}
