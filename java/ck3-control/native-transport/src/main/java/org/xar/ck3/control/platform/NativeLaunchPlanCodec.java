package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Ordinary typed launch configuration; parsing does not attest build, source or process qualification. */
public final class NativeLaunchPlanCodec {
    public static final int MAXIMUM_BYTES=1048576;
    public record Configuration(String requestId,String sessionId,LaunchSourceBinding.Review review,
            Path profileDirectory,Path stateDirectory,Path evidenceRoot,String pipeName,String bridgeVersion,String adapterId,
            NativeLaunchPlan.Load load,boolean debugMode,NativeLaunchPlan.WindowPolicy windowPolicy,Map<String,String> environment,
            long gameMemoryBytes,long injectorMemoryBytes,Instant deadline,Duration injectorTimeout,Duration startupTimeout,
            SteamOfflineProbe.Plan steam,NativeLaunchPlan.PreparedProfile preparedProfile,int maximumEvidenceRows){
        public Configuration{
            Objects.requireNonNull(review);Objects.requireNonNull(load);Objects.requireNonNull(windowPolicy);
            Objects.requireNonNull(steam);Objects.requireNonNull(preparedProfile);
            environment=NativeLaunchPolicy.requireEnvironment(environment,pipeName);
            if(preparedProfile.explicit().isPresent()) {
                var kind=preparedProfile.kind();boolean saved=kind==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.SAVED_VANILLA
                        ||kind==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.SAVED_PRODUCT_ONLY;
                if(saved!=(load instanceof NativeLaunchPlan.SavedGame)||(!saved&&debugMode))
                    throw new IllegalArgumentException("Explicit profile requires its actual Saved/fresh/debug domain");
            }
        }
        public NativeLaunchPlan accept() throws IOException {
            var effectiveReview = review.machineId() == null
                    ? new LaunchSourceBinding.Review(steam.machineId(), review.expiresAt(), review.gameExecutable(),
                            review.bridgeDll(), review.injector(), review.nativeEvidence(), review.nativeSourceRoot(),
                            review.completeRuntimeSources())
                    : review;
            return new NativeLaunchPlan(requestId,sessionId,LaunchSourceBinding.accept(effectiveReview),profileDirectory,stateDirectory,evidenceRoot,
                    pipeName,bridgeVersion,adapterId,load,debugMode,windowPolicy,environment,gameMemoryBytes,injectorMemoryBytes,
                    deadline,injectorTimeout,startupTimeout,steam,preparedProfile,maximumEvidenceRows);
        }
        public NativeLaunchPlan accept(NativeLaunchEvidence.Port nativeReader) throws IOException {
            return accept();
        }
    }
    private NativeLaunchPlanCodec(){ }
    public static NativeLaunchPlan readExact(ExactRef source,NativeLaunchEvidence.Port nativeReader)throws IOException {
        return readExact(source);
    }
    public static NativeLaunchPlan readExact(ExactRef source)throws IOException {
        return read(Path.of(Objects.requireNonNull(source).path()));
    }
    public static NativeLaunchPlan read(Path source)throws IOException {
        Objects.requireNonNull(source);
        byte[] raw;
        try(var input=Files.newInputStream(source)) { raw=input.readNBytes(MAXIMUM_BYTES+1); }
        if(raw.length==0||raw.length>MAXIMUM_BYTES)throw new IOException("Bounded Java launch configuration required");
        try {
            return fromJson(StrictJson.parse(raw,MAXIMUM_BYTES)).accept();
        } catch(IllegalArgumentException|java.time.DateTimeException invalid) {
            throw new IOException("Invalid Java launch configuration",invalid);
        }
    }
    public static Configuration describe(NativeLaunchPlan plan){
        return new Configuration(plan.requestId(),plan.sessionId(),plan.sources().review(),plan.profileDirectory(),plan.stateDirectory(),plan.evidenceRoot(),
                plan.pipeName(),plan.bridgeVersion(),plan.adapterId(),plan.load(),plan.debugMode(),plan.windowPolicy(),plan.environment(),plan.gameMemoryBytes(),
                plan.injectorMemoryBytes(),plan.deadline(),plan.injectorTimeout(),plan.startupTimeout(),plan.steam(),plan.preparedProfile(),plan.maximumEvidenceRows());
    }
    public static ObjectNode toJson(Configuration data){
        ObjectNode root=StrictJson.object();String schema=data.preparedProfile().declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods?"xar.java-game-launch-plan/v4":data.preparedProfile().kind()==org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.ORDINARY_PRODUCTION?"xar.java-game-launch-plan/v2":"xar.java-game-launch-plan/v3";root.put("schema",schema);
        root.put("request_id",data.requestId());root.put("session_id",data.sessionId());root.set("review",review(data.review()));
        root.put("profile_directory",data.profileDirectory().toString());root.put("state_directory",data.stateDirectory().toString());root.put("evidence_root",data.evidenceRoot().toString());
        root.put("pipe_name",data.pipeName());root.put("bridge_version",data.bridgeVersion());root.put("adapter_id",data.adapterId());
        ObjectNode load=StrictJson.object();if(data.load() instanceof NativeLaunchPlan.SavedGame saved){load.put("kind","SAVED_GAME");load.put("basename",saved.basename());load.set("save",ref(saved.save()));}else load.put("kind","NEW_GAME");root.set("load",load);
        root.put("debug_mode",data.debugMode());root.put("window_policy",data.windowPolicy().name());
        ObjectNode environment=StrictJson.object();data.environment().forEach(environment::put);root.set("environment",environment);
        root.put("game_memory_bytes",data.gameMemoryBytes());root.put("injector_memory_bytes",data.injectorMemoryBytes());root.put("deadline",data.deadline().toString());
        root.put("injector_timeout_millis",data.injectorTimeout().toMillis());root.put("startup_timeout_millis",data.startupTimeout().toMillis());
        ObjectNode steam=StrictJson.object();steam.put("machine_id",data.steam().machineId());steam.set("executable",ref(data.steam().steamExecutable()));steam.put("deadline",data.steam().deadline().toString());root.set("steam",steam);
        NativeLaunchPlan.PreparedProfile prepared=data.preparedProfile();
        if(!(prepared.declaration() instanceof NativeLaunchPlan.PreparedProfile.NoMods)) {
            ObjectNode profile=StrictJson.object();
            profile.set("environment_manifest",ref(prepared.environmentManifest()));profile.set("prepared_inputs",refs(prepared.preparedInputs()));
            if(prepared.ordinary().isPresent()) {
                profile.put("production_root",prepared.productionRoot().toString());profile.put("enabled_outer_descriptor_ref",prepared.enabledOuterDescriptorRef());
                profile.set("complete_production_files",refs(prepared.completeProductionFiles()));
            } else {
                profile.put("kind",prepared.kind().name());ArrayNode roots=profile.putArray("production_roots");
                for(Path path:prepared.productionRoots())roots.add(path.toString());
            }
            root.set("prepared_profile",profile);
        }
        root.put("maximum_evidence_rows",data.maximumEvidenceRows());return root;
    }
    public static Configuration fromJson(JsonNode value){
        String schema=text(value,"schema");
        boolean v4=schema.equals("xar.java-game-launch-plan/v4");
        boolean ordinary=schema.equals("xar.java-game-launch-plan/v2");
        StrictJson.require(ordinary||schema.equals("xar.java-game-launch-plan/v3")||v4,"exact launch schema required");
        Set<String> fields=new java.util.HashSet<>(Set.of("schema","request_id","session_id","review","profile_directory","state_directory","evidence_root","pipe_name","bridge_version","adapter_id","load","debug_mode","window_policy","environment","game_memory_bytes","injector_memory_bytes","deadline","injector_timeout_millis","startup_timeout_millis","steam","maximum_evidence_rows"));
        if(!v4)fields.add("prepared_profile");
        ObjectNode root=StrictJson.object(value,fields);
        JsonNode loadNode=root.get("load");String kind=text(loadNode,"kind");NativeLaunchPlan.Load load;
        if(kind.equals("NEW_GAME")){StrictJson.object(loadNode,Set.of("kind"));load=new NativeLaunchPlan.NewGame();}
        else{StrictJson.require(kind.equals("SAVED_GAME"),"known launch load kind required");StrictJson.object(loadNode,Set.of("kind","basename","save"));load=new NativeLaunchPlan.SavedGame(text(loadNode,"basename"),ref(loadNode.get("save")));}
        JsonNode envNode=root.get("environment");StrictJson.require(envNode!=null&&envNode.isObject()&&envNode.size()<=256,"bounded environment object required");
        Map<String,String> environment=new LinkedHashMap<>();envNode.properties().forEach(entry->{String key=StrictJson.text(entry.getKey());StrictJson.require(key.indexOf('=')<0&&key.indexOf('\0')<0,"valid environment key required");JsonNode item=entry.getValue();StrictJson.require(item.isTextual()&&item.textValue().length()<=32768&&item.textValue().indexOf('\0')<0,"environment string required");environment.put(key,item.textValue());});
        JsonNode steam=StrictJson.object(root.get("steam"),Set.of("machine_id","executable","deadline"));
        NativeLaunchPlan.PreparedProfile prepared=v4?NativeLaunchPlan.PreparedProfile.vanilla():prepared(root.get("prepared_profile"),ordinary);
        StrictJson.require(root.get("debug_mode").isBoolean(),"debug mode must be an actual boolean");
        return new Configuration(text(root,"request_id"),text(root,"session_id"),review(root.get("review")),path(root,"profile_directory"),path(root,"state_directory"),path(root,"evidence_root"),
                text(root,"pipe_name"),text(root,"bridge_version"),text(root,"adapter_id"),load,root.get("debug_mode").booleanValue(),NativeLaunchPlan.WindowPolicy.valueOf(text(root,"window_policy")),environment,
                StrictJson.integer(root.get("game_memory_bytes"),0,StrictJson.MAX_SAFE_INTEGER),StrictJson.integer(root.get("injector_memory_bytes"),0,StrictJson.MAX_SAFE_INTEGER),instant(root,"deadline"),
                Duration.ofMillis(StrictJson.integer(root.get("injector_timeout_millis"),0,StrictJson.MAX_SAFE_INTEGER)),Duration.ofMillis(StrictJson.integer(root.get("startup_timeout_millis"),0,StrictJson.MAX_SAFE_INTEGER)),
                new SteamOfflineProbe.Plan(text(steam,"machine_id"),ref(steam.get("executable")),instant(steam,"deadline")),
                prepared,
                (int)StrictJson.integer(root.get("maximum_evidence_rows"),0,Integer.MAX_VALUE));
    }
    private static NativeLaunchPlan.PreparedProfile prepared(JsonNode value,boolean ordinary) {
        if(ordinary) {
            JsonNode profile=StrictJson.object(value,Set.of("environment_manifest","production_root","enabled_outer_descriptor_ref","prepared_inputs","complete_production_files"));
            return new NativeLaunchPlan.PreparedProfile(ref(profile.get("environment_manifest")),path(profile,"production_root"),
                    text(profile,"enabled_outer_descriptor_ref"),refs(profile.get("prepared_inputs"),8192),refs(profile.get("complete_production_files"),8192));
        }
        JsonNode profile=StrictJson.object(value,Set.of("kind","environment_manifest","production_roots","prepared_inputs"));
        var kind=org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.valueOf(text(profile,"kind"));
        StrictJson.require(kind!=org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.ORDINARY_PRODUCTION,"v3 requires its explicit domain");
        JsonNode array=profile.get("production_roots");StrictJson.require(array!=null&&array.isArray()&&array.size()<=128,"finite explicit real production roots required");
        List<Path> roots=new ArrayList<>();for(JsonNode item:array) {
            Path root=Path.of(StrictJson.text(item));StrictJson.require(root.isAbsolute()&&root.normalize().equals(root),"normalized actual root required");roots.add(root);
        }
        return NativeLaunchPlan.PreparedProfile.explicit(ref(profile.get("environment_manifest")),kind,roots,refs(profile.get("prepared_inputs"),16384));
    }
    private static ObjectNode review(LaunchSourceBinding.Review data) {
        ObjectNode value=StrictJson.object();
        if(data.machineId()!=null)value.put("machine_id",data.machineId());
        if(data.expiresAt()!=null)value.put("expires_at",data.expiresAt().toString());
        value.set("game_executable",ref(data.gameExecutable()));value.set("bridge_dll",ref(data.bridgeDll()));
        value.set("injector",ref(data.injector()));
        if(data.nativeEvidence()!=null) {
            ObjectNode evidence=StrictJson.object();
            evidence.set("environment_actual",ref(data.nativeEvidence().environmentActual()));
            evidence.set("build_actual",ref(data.nativeEvidence().buildActual()));
            evidence.set("registration_actual",ref(data.nativeEvidence().registrationActual()));
            value.set("native_evidence",evidence);
        }
        if(data.nativeSourceRoot()!=null)value.put("native_source_root",data.nativeSourceRoot().toString());
        value.set("complete_runtime_sources",refs(data.completeRuntimeSources()));return value;
    }
    private static LaunchSourceBinding.Review review(JsonNode value) {
        StrictJson.require(value!=null&&value.isObject(),"launch executable configuration required");
        Set<String> fields=Set.of("machine_id","expires_at","game_executable","bridge_dll","injector",
                "native_evidence","native_source_root","complete_runtime_sources");
        value.properties().forEach(entry->StrictJson.require(fields.contains(entry.getKey()),"unknown launch executable field"));
        NativeLaunchEvidence.Inputs evidence=null;
        if(value.hasNonNull("native_evidence")) {
            JsonNode data=StrictJson.object(value.get("native_evidence"),Set.of("environment_actual","build_actual","registration_actual"));
            evidence=new NativeLaunchEvidence.Inputs(ref(data.get("environment_actual")),ref(data.get("build_actual")),ref(data.get("registration_actual")));
        }
        List<ControlBuild.FileRef> runtime=List.of();
        if(value.hasNonNull("complete_runtime_sources")) {
            JsonNode data=value.get("complete_runtime_sources");StrictJson.require(data.isArray(),"runtime source metadata must be an array");
            var refs=new ArrayList<ControlBuild.FileRef>();for(JsonNode item:data)refs.add(ref(item));runtime=List.copyOf(refs);
        }
        return new LaunchSourceBinding.Review(value.hasNonNull("machine_id")?text(value,"machine_id"):null,
                value.hasNonNull("expires_at")?instant(value,"expires_at"):null,
                ref(value.get("game_executable")),ref(value.get("bridge_dll")),ref(value.get("injector")),evidence,
                value.hasNonNull("native_source_root")?path(value,"native_source_root"):null,runtime);
    }
    private static ObjectNode ref(ControlBuild.FileRef value){ObjectNode node=StrictJson.object();node.put("path",value.path());node.put("bytes",value.bytes());node.put("sha256",value.sha256());return node;}
    private static ControlBuild.FileRef ref(JsonNode node){StrictJson.object(node,Set.of("path","bytes","sha256"));return new ControlBuild.FileRef(text(node,"path"),StrictJson.integer(node.get("bytes"),0,StrictJson.MAX_SAFE_INTEGER),text(node,"sha256"));}
    private static ArrayNode refs(List<ControlBuild.FileRef> values){ArrayNode array=StrictJson.object().arrayNode();for(ControlBuild.FileRef value:values)array.add(ref(value));return array;}
    private static List<ControlBuild.FileRef> refs(JsonNode value,int maximum){StrictJson.require(value!=null&&value.isArray(),"source metadata array required");List<ControlBuild.FileRef> result=new ArrayList<>();for(JsonNode item:value)result.add(ref(item));return List.copyOf(result);}
    private static String text(JsonNode value,String field){StrictJson.require(value!=null&&value.isObject(),"object field source required");return StrictJson.text(value.get(field));}
    private static Path path(JsonNode value,String field){Path path=Path.of(text(value,field));StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute path required");return path;}
    private static Instant instant(JsonNode value,String field){String raw=text(value,field);StrictJson.require(raw.endsWith("Z"),"canonical UTC instant required");Instant result=Instant.parse(raw);StrictJson.require(result.toString().equals(raw),"canonical UTC instant required");return result;}
}

