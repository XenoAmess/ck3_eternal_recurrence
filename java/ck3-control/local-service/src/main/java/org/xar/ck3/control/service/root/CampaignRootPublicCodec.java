package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.PublicRevision;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Original complete campaign-root Service DATA, retaining the original ROOT reader and its typed normalization. */
public final class CampaignRootPublicCodec {
    private CampaignRootPublicCodec(){ }
    private static final BigInteger MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Set<String> NATIVE=Set.of("step","accepted","status","query_sequence","snapshot_revision","campaign_root_context","backend_id");
    private static final Set<String> MIRRORS=Set.of("schema_version","date_raw","local_player_id","player_character_id","player_character_alive",
            "player_monthly_gold_income","player_health","player_domain_size","player_domain_limit","player_targeting_faction_count","council",
            "primary_title","primary_title_succession_character_ids","held_title_partition","capital_province_id","immediate_liege_character_id",
            "top_liege_character_id","independent","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids",
            "related_character_contexts","government","selected_game_rule_tokens","native_selected_game_rule_token_count","readiness","unavailable_reason","provenance");
    private static final Set<String> UINT64=Set.of("query_sequence","snapshot_revision","queried_native_revision","native_revision");

    private static final Set<String> PUBLIC_REVISIONS=Set.of("queried_revision","revision","expected_revision");
    public record Request(BigInteger expectedRevision){public Request{new PublicRevision(expectedRevision);}}
    public static final class Result {
        private final Obj body;
        private Result(Obj body){validate(body);this.body=body;}
        public Obj body(){return body;}
    }
    public static Request decodeRequest(PublicBindings.Arguments arguments){
        if(!(arguments instanceof PublicBindings.Value present))throw new IllegalArgumentException("present non-null campaign-root argument object required");
        Obj row=DriverJson.object(present.original().bytes(),65536);
        require(row.members().keySet().equals(Set.of("expected_revision")),"exact campaign-root expected_revision required");
        return new Request(PublicRevision.parse(DriverJson.toNode(row.get("expected_revision"))).value());
    }
    public static RawJson encodeRequest(Request request){return new RawJson(DriverJson.encode(new Obj(Map.of("expected_revision",new Text(new PublicRevision(request.expectedRevision()).canonical())))));}

    /** Called only on the current Root-held frame and the identical installed ROOT read/canonical witness. */
    public static Result fromActual(Complete frame,Request request,FinanceReadContracts.Packet actual){
        Objects.requireNonNull(frame);Objects.requireNonNull(request);Objects.requireNonNull(actual);
        var current=frame.identity();var f=current.frame();var read=actual.receipt();var original=read.request().before();var old=original.frame();
        require(f.revision().equals(request.expectedRevision())&&new Bool(true).equals(frame.semantic().get("paused")),"campaign-root expected_revision or paused frame differs");
        require(read.request().operation().equals(FinanceReadContracts.Query.ROOT.operation())
                &&read.request().source().equals(frame.source())&&read.request().sessionId().equals(frame.sessionId())
                &&current.machineId().equals(original.machineId())&&current.game().equals(original.game())
                &&current.observationVersion()==original.observationVersion()&&f.snapshotId().equals(old.snapshotId())
                &&f.episodeRunId().equals(old.episodeRunId())&&f.identity().equals(old.identity()),
                "actual campaign-root original crossed the current native frame/source/session");
        // Canonical reuse may retain an older public revision. The actual read port independently owns its unchanged-native/READ-only proof.
        Obj normalized=CampaignRootContextJson.normalizeNativeResult(actual.originalResult(),f.identity().dateRaw(),f.identity().nativeRevision());
        require(normalized.equals(actual.result()),"actual installed campaign-root decoder projection differs");
        Obj root=object(normalized.get("campaign_root_context"),"normalized campaign root");
        if(new Text("available").equals(root.get("status")))require(new IntegerValue(f.identity().player()).equals(root.get("player_character_id")),"campaign root belongs to another actual player");
        Obj provenance=object(root.get("provenance"),"campaign root provenance");
        Obj diagnostics=object(frame.semantic().get("diagnostics"),"actual current diagnostics");
        Obj hello=object(diagnostics.get("hello"),"actual current hello");
        Value version=hello.members().containsKey("expected_ck3_version")?hello.get("expected_ck3_version"):hello.get("game_version");
        Value sha=hello.members().containsKey("expected_ck3_sha256")?hello.get("expected_ck3_sha256"):hello.get("executable_sha256");
        String build=text(version,"actual hello game version"),digest=text(sha,"actual hello executable SHA256").toUpperCase(java.util.Locale.ROOT);
        require(digest.matches("[0-9A-F]{64}")&&new Text(build).equals(provenance.get("game_version"))
                &&digest.equals(text(provenance.get("executable_sha256"),"root executable SHA256").toUpperCase(java.util.Locale.ROOT)),
                "campaign-root build differs from the actual current hello");
        var out=new LinkedHashMap<String,Value>(normalized.members());
        for(String field:MIRRORS)if(root.members().containsKey(field))out.put(field,root.get(field));
        out.put("queried_snapshot_id",new Text(f.snapshotId()));out.put("queried_revision",new IntegerValue(f.revision()));
        out.put("queried_native_revision",new IntegerValue(f.identity().nativeRevision()));
        out.put("schema_version",new IntegerValue(BigInteger.ONE));out.put("scope",new Text("exact-campaign-root-context"));
        out.put("build",new Obj(Map.of("version",new Text(build),"exe_sha256",provenance.get("executable_sha256"))));
        out.put("source",new Obj(Map.of("game_version",new Text(build),"executable_sha256",new Text(digest),"snapshot_id",new Text(f.snapshotId()),
                "revision",new IntegerValue(f.revision()),"native_revision",new IntegerValue(f.identity().nativeRevision()),
                "date_raw",new IntegerValue(f.identity().dateRaw()),"paused",new Bool(true),"backend_id",new Text(text(frame.semantic().get("backend_id"),"actual snapshot backend")))));
        out.put("binding",new Obj(Map.of("snapshot_id",new Text(f.snapshotId()),"revision",new IntegerValue(f.revision()),
                "native_revision",new IntegerValue(f.identity().nativeRevision()),"date_raw",new IntegerValue(f.identity().dateRaw()),"expected_revision",new IntegerValue(request.expectedRevision()))));
        out.put("campaign_root_context_ready",object(root.get("readiness"),"root readiness").get("ready"));
        var cache=DriverCapabilityStateProducer.campaignRootFromOriginal(read);
        if(cache.members().containsKey("player_heir_fixed_dynasty_projection_v1"))out.put("player_heir_fixed_dynasty_projection_v1",cache.get("player_heir_fixed_dynasty_projection_v1"));
        return new Result(new Obj(out));
    }
    public static RawJson encode(Result result){return new RawJson(DriverJson.encode(convert(result.body(),true,null)));}
    public static Result decode(RawJson publicWire){return new Result(object(convert(DriverJson.object(publicWire.bytes(),RawJson.MAXIMUM_BYTES),false,null),"public campaign root response"));}

    /** Original NativeHeadlessGameplayDriver execute_step ROOT result, retaining its complete mirrors,
     * readiness and optional existing-heir diagnostic. The dedicated MCP tool's wrappers are separate. */
    public static RawJson executeFromActual(Complete frame,BigInteger expectedRevision,FinanceReadContracts.Packet actual) {
        Result qualified=fromActual(frame,new Request(expectedRevision),actual);
        var fields=new LinkedHashMap<String,Value>(qualified.body().members());
        for(String extra:Set.of("scope","build","source","binding"))fields.remove(extra);
        Obj root=object(qualified.body().get("campaign_root_context"),"campaign root");
        if(root.members().containsKey("schema_version"))fields.put("schema_version",root.get("schema_version"));
        else fields.remove("schema_version");
        Obj original=new Obj(fields);validateExecution(original);
        return new RawJson(DriverJson.encode(convert(original,true,null)));
    }
    /** Strict complete generic-result wire roundtrip, using the same explicit ROOT numeric roles. */
    public static Obj decodeExecution(RawJson original) {
        Obj numeric=object(convert(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),false,null),"execute ROOT result");
        validateExecution(numeric);return numeric;
    }
    private static void validateExecution(Obj result) {
        Obj root=object(result.get("campaign_root_context"),"campaign_root_context");
        var allowed=new java.util.HashSet<String>(NATIVE);
        allowed.addAll(Set.of("queried_snapshot_id","queried_revision","queried_native_revision","campaign_root_context_ready"));
        for(String field:MIRRORS)if(root.members().containsKey(field))allowed.add(field);
        boolean candidate=root.members().containsKey("player_heir_candidate_v1");
        require(result.members().containsKey("player_heir_fixed_dynasty_projection_v1")==candidate,"original optional candidate presence differs");
        if(candidate){allowed.add("player_heir_fixed_dynasty_projection_v1");requireUnqualifiedProjection(result.get("player_heir_fixed_dynasty_projection_v1"));}
        require(result.members().keySet().equals(allowed),"complete original execute ROOT fields required");
        var nativeFields=new LinkedHashMap<String,Value>();for(String key:NATIVE)nativeFields.put(key,result.get(key));
        BigInteger nativeRevision=integer(result.get("queried_native_revision"),"queried_native_revision");uint64(nativeRevision);
        require(nativeRevision.signum()>0,"original native revision must be positive");
        Obj normalized=CampaignRootContextJson.normalizeNativeResult(new Obj(nativeFields),integer(root.get("date_raw"),"date_raw"),nativeRevision);
        require(normalized.get("campaign_root_context").equals(root),"original execute ROOT normalization differs");
        for(String field:MIRRORS)if(root.members().containsKey(field))require(root.get(field).equals(result.get(field)),"original ROOT mirror differs: "+field);
        new PublicRevision(integer(result.get("queried_revision"),"queried_revision"));text(result.get("queried_snapshot_id"),"queried_snapshot_id");
        require(object(root.get("readiness"),"readiness").get("ready").equals(result.get("campaign_root_context_ready")),"execute ROOT readiness mirror differs");
    }

    private static void validate(Obj result){
        Obj root=object(result.get("campaign_root_context"),"campaign_root_context");var allowed=new java.util.HashSet<String>(NATIVE);
        allowed.addAll(Set.of("queried_snapshot_id","queried_revision","queried_native_revision","schema_version","scope","build","source","binding","campaign_root_context_ready"));
        for(String field:MIRRORS)if(root.members().containsKey(field))allowed.add(field);
        require(result.members().containsKey("player_heir_fixed_dynasty_projection_v1")==root.members().containsKey("player_heir_candidate_v1"),"original optional candidate projection presence differs");
        if(result.members().containsKey("player_heir_fixed_dynasty_projection_v1")){
            requireUnqualifiedProjection(result.get("player_heir_fixed_dynasty_projection_v1"));allowed.add("player_heir_fixed_dynasty_projection_v1");
        }
        require(result.members().keySet().equals(allowed),"complete exact campaign-root Service fields required");
        Obj binding=exact(result.get("binding"),Set.of("snapshot_id","revision","native_revision","date_raw","expected_revision"),"binding");
        BigInteger revision=integer(binding.get("revision"),"revision"),nativeRevision=integer(binding.get("native_revision"),"native_revision");new PublicRevision(revision);uint64(nativeRevision);
        require(nativeRevision.signum()>0&&revision.equals(integer(binding.get("expected_revision"),"expected_revision")),"campaign-root revision binding differs");
        BigInteger date=integer(binding.get("date_raw"),"date_raw");require(date.compareTo(BigInteger.valueOf(Integer.MIN_VALUE))>=0&&date.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"campaign-root signed int32 date required");
        var nativeFields=new LinkedHashMap<String,Value>();for(String key:NATIVE)nativeFields.put(key,result.get(key));
        Obj normalized=CampaignRootContextJson.normalizeNativeResult(new Obj(nativeFields),date,nativeRevision);
        require(normalized.get("campaign_root_context").equals(root),"campaign-root response normalized body differs");
        for(String field:MIRRORS)if(root.members().containsKey(field))require(root.get(field).equals(result.get(field)),"campaign-root mirror differs: "+field);
        require(new IntegerValue(BigInteger.ONE).equals(result.get("schema_version"))&&new Text("exact-campaign-root-context").equals(result.get("scope"))
                &&binding.get("snapshot_id").equals(result.get("queried_snapshot_id"))&&new IntegerValue(revision).equals(result.get("queried_revision"))
                &&new IntegerValue(nativeRevision).equals(result.get("queried_native_revision"))
                &&object(root.get("readiness"),"readiness").get("ready").equals(result.get("campaign_root_context_ready")),"campaign-root complete frame/ready envelope differs");
        Obj source=exact(result.get("source"),Set.of("game_version","executable_sha256","snapshot_id","revision","native_revision","date_raw","paused","backend_id"),"source");
        Obj build=exact(result.get("build"),Set.of("version","exe_sha256"),"build"),provenance=object(root.get("provenance"),"provenance");
        require(source.get("snapshot_id").equals(binding.get("snapshot_id"))&&source.get("revision").equals(binding.get("revision"))
                &&source.get("native_revision").equals(binding.get("native_revision"))&&source.get("date_raw").equals(binding.get("date_raw"))
                &&new Bool(true).equals(source.get("paused"))&&build.get("version").equals(provenance.get("game_version"))
                &&build.get("exe_sha256").equals(provenance.get("executable_sha256"))&&source.get("game_version").equals(build.get("version"))
                &&text(source.get("executable_sha256"),"source executable SHA").equals(text(build.get("exe_sha256"),"build executable SHA").toUpperCase(java.util.Locale.ROOT)),"campaign-root source/build mirrors differ");
        text(source.get("backend_id"),"source backend");text(result.get("backend_id"),"read backend");text(binding.get("snapshot_id"),"snapshot_id");
    }
    /** The currently installed sole mapper has no retained fixed anchor/loaded provider and only emits this unknown DATA branch. */
    private static void requireUnqualifiedProjection(Value value){
        Obj projection=exact(value,Set.of("status","reason","fixed_dynasty_id_raw","candidate_character_id","candidate_same_fixed_dynasty",
                "positive_same_dynasty_legal_witness","k","b","H_interval","complete_backup_domain","scope"),"unqualified original candidate projection");
        require(new Text("unknown").equals(projection.get("status"))&&new Bool(false).equals(projection.get("positive_same_dynasty_legal_witness"))
                &&new Bool(false).equals(projection.get("complete_backup_domain"))&&new Text("pure_current_candidate_projection").equals(projection.get("scope"))
                &&projection.get("fixed_dynasty_id_raw") instanceof Nil&&projection.get("candidate_character_id") instanceof Nil
                &&projection.get("candidate_same_fixed_dynasty") instanceof Nil&&projection.get("k") instanceof Nil&&projection.get("b") instanceof Nil
                &&new Arr(java.util.List.of(new IntegerValue(BigInteger.ZERO),new IntegerValue(BigInteger.valueOf(100)))).equals(projection.get("H_interval")),
                "unqualified original candidate diagnostic cannot grant a fixed-dynasty witness");
        String reason=text(projection.get("reason"),"original candidate diagnostic");require(reason.codePointCount(0,reason.length())<=1024,"bounded original candidate diagnostic required");
    }
    private static Obj exact(Value value,Set<String> fields,String name){Obj row=object(value,name);require(row.members().keySet().equals(fields),"exact "+name+" fields required");return row;}
    private static Value convert(Value value,boolean encode,String field){
        if(field!=null&&PUBLIC_REVISIONS.contains(field)){
            if(encode)return new Text(new PublicRevision(integer(value,field)).canonical());
            if(!(value instanceof Text decimal))throw new IllegalArgumentException("public campaign-root revision fields require decimal strings");
            return new IntegerValue(PublicRevision.decimal(decimal.value()).value());
        }
        if(field!=null&&UINT64.contains(field)){
            if(encode){BigInteger number=integer(value,field);uint64(number);return new Text(number.toString());}
            if(!(value instanceof Text decimal))throw new IllegalArgumentException("public campaign-root uint64 fields require decimal strings");return new IntegerValue(decimal(decimal.value()));
        }
        if(value instanceof Obj object){var out=new LinkedHashMap<String,Value>();object.members().forEach((key,item)->out.put(key,convert(item,encode,key)));return new Obj(out);}
        if(value instanceof Arr array)return new Arr(array.items().stream().map(item->convert(item,encode,null)).toList());
        return value;
    }
    private static BigInteger decimal(String value){require(value.matches("0|[1-9][0-9]*")&&value.length()<=20,"canonical uint64 decimal text required");BigInteger result=new BigInteger(value);uint64(result);return result;}
    private static void uint64(BigInteger value){require(value!=null&&value.signum()>=0&&value.compareTo(MAX)<=0,"uint64 campaign-root identity required");}
}
