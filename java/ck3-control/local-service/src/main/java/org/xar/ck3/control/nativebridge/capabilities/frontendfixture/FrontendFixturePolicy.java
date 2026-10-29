package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Sole closed external fixture policy. Configuration is data, never a Game permission. */
public record FrontendFixturePolicy(Kind kind, Preparation preparation, Map<String,String> profileInputSha256,
        PostStart postStart, List<String> requiredLogMarkers, List<String> forbiddenLogMarkers) {
    public static final String ROBERT_KEY="bookmark_rags_to_riches_duke_robert";
    public static final String PROFILE_ID="faith-and-power-e01-abbasid-867";
    public static final String STARTUP_EVENT="xar_faith_h01_prepare.1";
    public enum Kind { ROBERT, SCENARIO }
    public record Preparation(String path,String sha256) {
        public Preparation { absolute(path);digest(sha256); }
    }
    public record Target(String bookmarkKey,String characterNameKey,String governmentKey,int startDateRaw,String bookmarkGroupKey) {
        public Target { StrictJson.text(bookmarkKey);StrictJson.text(characterNameKey);StrictJson.text(governmentKey);StrictJson.text(bookmarkGroupKey); }
        public ObjectNode toJson() {
            ObjectNode n=StrictJson.object();n.put("bookmark_key",bookmarkKey);n.put("character_name_key",characterNameKey);
            n.put("government_key",governmentKey);n.put("start_date_raw",startDateRaw);n.put("bookmark_group_key",bookmarkGroupKey);return n;
        }
    }
    public static final Target SCENARIO_TARGET=new Target("bm_xar_faith_h01_867","bookmark_xar_faith_h01_abbasid","clan_government",51394920,"bm_group_867");
    public record PostStart(String governmentKey,String primaryTitleTierKey,boolean independent) {
        public PostStart {
            StrictJson.require(Set.of("feudal_government","celestial_government","administrative_government",
                    "meritocratic_government","steppe_admin_government","clan_government").contains(governmentKey),"closed fixture government required");
            StrictJson.require(Set.of("barony","county","duchy","kingdom","empire","hegemony").contains(primaryTitleTierKey),"closed fixture title tier required");
        }
        public ObjectNode toJson() {
            ObjectNode n=StrictJson.object();n.put("government_key",governmentKey);n.put("primary_title_tier_key",primaryTitleTierKey);n.put("independent",independent);return n;
        }
    }
    /** Exact transport binding corresponding to the original host producer; not the policy itself. */
    public record Binding(String policySha256,String preparationSha256,Optional<Target> scenarioTarget) {
        public Binding { digest(policySha256);digest(preparationSha256);Objects.requireNonNull(scenarioTarget);
            StrictJson.require(scenarioTarget.isEmpty()||scenarioTarget.get().equals(SCENARIO_TARGET),"closed scenario target required"); }
        public Kind kind() { return scenarioTarget.isPresent()?Kind.SCENARIO:Kind.ROBERT; }
        public ObjectNode toJson() {
            ObjectNode n=StrictJson.object();n.put("policy_sha256",policySha256);n.put("preparation_sha256",preparationSha256);
            if(scenarioTarget.isPresent()){n.put("profile_id",PROFILE_ID);n.set("frontend_target",scenarioTarget.get().toJson());}return n;
        }
        public static Binding fromJson(JsonNode raw) {
            StrictJson.require(raw instanceof ObjectNode,"fixture policy binding object required");
            boolean scenario=raw.has("profile_id");
            ObjectNode n=StrictJson.object(raw,scenario?Set.of("policy_sha256","preparation_sha256","profile_id","frontend_target"):Set.of("policy_sha256","preparation_sha256"));
            if(scenario)requireScenario(n);
            return new Binding(StrictJson.text(n.get("policy_sha256")),StrictJson.text(n.get("preparation_sha256")),scenario?Optional.of(SCENARIO_TARGET):Optional.empty());
        }
    }
    public FrontendFixturePolicy {
        Objects.requireNonNull(kind);Objects.requireNonNull(preparation);Objects.requireNonNull(postStart);
        profileInputSha256=Map.copyOf(profileInputSha256);requiredLogMarkers=List.copyOf(requiredLogMarkers);forbiddenLogMarkers=List.copyOf(forbiddenLogMarkers);
        StrictJson.require(profileInputSha256.size()>=3&&profileInputSha256.size()<=4096
                &&profileInputSha256.keySet().containsAll(Set.of("dlc_load.json","pdx_settings.txt")),"actual profile config and mounted inputs required");
        profileInputSha256.forEach((path,sha)->{relative(path);digest(sha);});
        if(kind==Kind.SCENARIO)StrictJson.require(postStart.equals(new PostStart("clan_government","empire",true)),"scenario requires its declared independent clan empire");
        else StrictJson.require(!postStart.governmentKey().equals("clan_government"),"ordinary fixture v1 does not admit scenario government");
        List<String> all=new ArrayList<>();all.addAll(markers(requiredLogMarkers));all.addAll(markers(forbiddenLogMarkers));
        StrictJson.require(all.size()<=16&&new HashSet<>(all).size()==all.size(),"distinct markers within existing fixed log query limit required");
    }
    public String publicTool() { return kind==Kind.SCENARIO?"ck3_submit_frontend_fixture_scenario_start_v1":"ck3_submit_frontend_fixture_robert_start_v1"; }
    public Binding binding(String rawPolicySha256) {
        return new Binding(rawPolicySha256,preparation.sha256(),kind==Kind.SCENARIO?Optional.of(SCENARIO_TARGET):Optional.empty());
    }
    public List<String> allMarkers() { List<String> result=new ArrayList<>(requiredLogMarkers);result.addAll(forbiddenLogMarkers);return List.copyOf(result); }
    public ObjectNode toJson() {
        ObjectNode n=StrictJson.object();n.put("schema",kind==Kind.SCENARIO?"ck3-frontend-fixture-start-policy-v2":"ck3-frontend-fixture-start-policy-v1");
        n.put("schema_version",kind==Kind.SCENARIO?2:1);
        ObjectNode p=StrictJson.object();p.put("path",preparation.path());p.put("sha256",preparation.sha256());n.set("preparation",p);
        ObjectNode hashes=StrictJson.object();profileInputSha256.forEach(hashes::put);n.set("profile_input_sha256",hashes);n.set("post_start",postStart.toJson());
        var required=n.putArray("required_log_markers");requiredLogMarkers.forEach(required::add);
        var forbidden=n.putArray("forbidden_log_markers");forbiddenLogMarkers.forEach(forbidden::add);
        if(kind==Kind.SCENARIO){n.put("profile_id",PROFILE_ID);n.set("frontend_target",SCENARIO_TARGET.toJson());ObjectNode event=StrictJson.object();event.put("mode","observe_only");event.put("event_definition_key",STARTUP_EVENT);event.put("option_count",2);n.set("startup_event_admission",event);}return n;
    }
    public static FrontendFixturePolicy fromJson(JsonNode raw) {
        StrictJson.require(raw instanceof ObjectNode,"fixture policy object required");
        String schema=StrictJson.text(raw.get("schema"));boolean scenario=schema.equals("ck3-frontend-fixture-start-policy-v2");
        Set<String> fields=new HashSet<>(Set.of("schema","schema_version","preparation","profile_input_sha256","post_start","required_log_markers","forbidden_log_markers"));
        if(scenario)fields.addAll(Set.of("profile_id","frontend_target","startup_event_admission"));
        ObjectNode n=StrictJson.object(raw,fields);
        StrictJson.require(schema.equals(scenario?"ck3-frontend-fixture-start-policy-v2":"ck3-frontend-fixture-start-policy-v1"),"closed fixture policy schema required");
        StrictJson.integer(n.get("schema_version"),scenario?2:1,scenario?2:1);
        if(scenario){
            requireScenario(n);
            ObjectNode event=StrictJson.object(n.get("startup_event_admission"),Set.of("mode","event_definition_key","option_count"));
            StrictJson.require(StrictJson.text(event.get("mode")).equals("observe_only")&&StrictJson.text(event.get("event_definition_key")).equals(STARTUP_EVENT),"only original observe-only startup event admitted");
            StrictJson.integer(event.get("option_count"),2,2);
        }
        ObjectNode p=StrictJson.object(n.get("preparation"),Set.of("path","sha256"));
        StrictJson.require(n.get("profile_input_sha256") instanceof ObjectNode,"profile hash object required");
        Map<String,String> hashes=new LinkedHashMap<>();n.get("profile_input_sha256").fields().forEachRemaining(e->hashes.put(e.getKey(),StrictJson.text(e.getValue())));
        ObjectNode post=StrictJson.object(n.get("post_start"),Set.of("government_key","primary_title_tier_key","independent"));
        StrictJson.require(post.get("independent").isBoolean(),"exact independent boolean required");
        return new FrontendFixturePolicy(scenario?Kind.SCENARIO:Kind.ROBERT,new Preparation(StrictJson.text(p.get("path")),StrictJson.text(p.get("sha256"))),hashes,
                new PostStart(StrictJson.text(post.get("government_key")),StrictJson.text(post.get("primary_title_tier_key")),post.get("independent").booleanValue()),
                strings(n.get("required_log_markers")),strings(n.get("forbidden_log_markers")));
    }
    private static void requireScenario(ObjectNode n) {
        StrictJson.require(StrictJson.text(n.get("profile_id")).equals(PROFILE_ID),"only exact episode01 profile admitted");
        ObjectNode target=StrictJson.object(n.get("frontend_target"),Set.of("bookmark_key","character_name_key","government_key","start_date_raw","bookmark_group_key"));
        StrictJson.require(StrictJson.text(target.get("bookmark_key")).equals(SCENARIO_TARGET.bookmarkKey())
                &&StrictJson.text(target.get("character_name_key")).equals(SCENARIO_TARGET.characterNameKey())
                &&StrictJson.text(target.get("government_key")).equals(SCENARIO_TARGET.governmentKey())
                &&StrictJson.text(target.get("bookmark_group_key")).equals(SCENARIO_TARGET.bookmarkGroupKey()),"exact typed closed episode01 target required");
        StrictJson.integer(target.get("start_date_raw"),SCENARIO_TARGET.startDateRaw(),SCENARIO_TARGET.startDateRaw());
    }
    private static List<String> strings(JsonNode raw) {
        StrictJson.require(raw!=null&&raw.isArray(),"marker array required");List<String> result=new ArrayList<>();raw.forEach(n->result.add(StrictJson.text(n)));return List.copyOf(result);
    }
    private static List<String> markers(List<String> rows) {
        StrictJson.require(!rows.isEmpty()&&rows.size()<=16,"1..16 fixture markers required");
        for(String row:rows)StrictJson.require(row!=null&&row.codePointCount(0,row.length())>=1&&row.codePointCount(0,row.length())<=160
                &&row.indexOf('\r')<0&&row.indexOf('\n')<0&&row.indexOf(0)<0,"bounded literal log marker required");return rows;
    }
    public static void digest(String raw) { StrictJson.require(raw!=null&&raw.matches("[0-9a-f]{64}"),"lowercase SHA-256 required"); }
    private static void absolute(String raw) { StrictJson.text(raw);StrictJson.require(Path.of(raw).isAbsolute()||raw.matches("[A-Za-z]:[/\\\\].*")||raw.startsWith("\\\\"),"absolute original preparation path required"); }
    public static void relative(String raw) {
        StrictJson.text(raw);Path path=Path.of(raw);
        StrictJson.require(!path.isAbsolute()&&raw.indexOf('\\')<0&&raw.indexOf(':')<0&&path.getNameCount()>0,"relative profile input required");
        for(Path part:path)StrictJson.require(!part.toString().equals(".."),"profile input escapes bound profile");
    }
}
