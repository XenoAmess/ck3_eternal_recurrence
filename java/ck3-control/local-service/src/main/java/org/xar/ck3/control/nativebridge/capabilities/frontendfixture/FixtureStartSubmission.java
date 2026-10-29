package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;

/** Original public pending receipt, with one strict Java contract for both real producers. */
public record FixtureStartSubmission(FrontendFixturePolicy.Kind kind,FrontendRulesData.Binding binding,
        FrontendFixturePolicy.Binding policyBinding,RawJson before,Selected selectedCandidate,
        Optional<RawJson> bookmarkAcknowledgement,Optional<RawJson> selectionAcknowledgement,RawJson acknowledgement) {
    public record SelectedDiagnostics(Optional<String> step,Optional<String> route,Optional<BigInteger> querySequence,
            Optional<String> backendId,boolean acceptedPresent) {
        public SelectedDiagnostics { Objects.requireNonNull(step);Objects.requireNonNull(route);Objects.requireNonNull(querySequence);Objects.requireNonNull(backendId);
            step.ifPresent(StrictJson::text);route.ifPresent(v->StrictJson.require(v.equals("bookmarks"),"selected model route required"));
            backendId.ifPresent(v->StrictJson.require(v.equals("native-headless"),"selected native backend required"));
            querySequence.ifPresent(FrontendRulesData::positiveU64); }
        void write(ObjectNode n) {step.ifPresent(v->n.put("step",v));route.ifPresent(v->n.put("route",v));querySequence.ifPresent(v->n.put("query_sequence",v));backendId.ifPresent(v->n.put("backend_id",v));if(acceptedPresent)n.put("accepted",true);}
    }
    public record Selected(FrontendFixturePolicy.Kind kind,Optional<String> bookmarkGroupKey,String bookmarkKey,
            String characterNameKey,String governmentKey,int startDateRaw,Optional<RawJson> nativeModel,Optional<SelectedDiagnostics> diagnostics) {
        public Selected {
            Objects.requireNonNull(kind);Objects.requireNonNull(bookmarkGroupKey);Objects.requireNonNull(nativeModel);Objects.requireNonNull(diagnostics);
            nativeModel=nativeModel.map(FixtureStartSubmission::jsonDomain);
            boolean scenario=kind==FrontendFixturePolicy.Kind.SCENARIO;var target=FrontendFixturePolicy.SCENARIO_TARGET;
            StrictJson.require(bookmarkKey.equals(scenario?target.bookmarkKey():"bm_1066_rags_to_riches")
                    &&characterNameKey.equals(scenario?target.characterNameKey():FrontendFixturePolicy.ROBERT_KEY)
                    &&governmentKey.equals(scenario?target.governmentKey():"feudal_government")
                    &&(bookmarkGroupKey.isEmpty()||bookmarkGroupKey.get().equals(scenario?target.bookmarkGroupKey():"bm_group_1066"))
                    &&(!scenario||startDateRaw==target.startDateRaw()),"actual selected fixture target required");
        }
        public ObjectNode toJson() {
            boolean scenario=kind==FrontendFixturePolicy.Kind.SCENARIO;ObjectNode n=StrictJson.object();
            n.put("schema",scenario?"ck3-frontend-selected-fixture-scenario-candidate-v1":"ck3-frontend-selected-1066-feudal-candidate-v1");
            n.put("status","ready");n.put("read_only",true);
            if(scenario)n.put("profile_id",FrontendFixturePolicy.PROFILE_ID);
            if(bookmarkGroupKey.isPresent())n.put("selected_bookmark_group_key",bookmarkGroupKey.get());else n.putNull("selected_bookmark_group_key");
            n.put("selected_bookmark_key",bookmarkKey);n.put("selected_character_name_key",characterNameKey);
            n.put("selected_character_government_key",governmentKey);n.put("selected_bookmark_start_date_raw",startDateRaw);
            nativeModel.ifPresent(raw->n.set("native_model",StrictJson.parse(raw.bytes(),1<<20)));diagnostics.ifPresent(d->d.write(n));return n;
        }
        public static Selected fromJson(JsonNode n,FrontendFixturePolicy.Kind kind) {
            StrictJson.require(n instanceof ObjectNode,"selected fixture object required");boolean scenario=kind==FrontendFixturePolicy.Kind.SCENARIO;
            Set<String> fields=new java.util.HashSet<>(Set.of("schema","status","read_only","selected_bookmark_group_key","selected_bookmark_key","selected_character_name_key","selected_character_government_key","selected_bookmark_start_date_raw"));
            if(scenario)fields.add("profile_id");if(n.has("native_model"))fields.add("native_model");
            // The ordinary original native selected-model producer also carries these typed diagnostics.
            for(String optional:java.util.List.of("step","accepted","route","query_sequence","backend_id"))if(n.has(optional))fields.add(optional);
            StrictJson.object(n,fields);StrictJson.require(StrictJson.text(n.get("schema")).equals(scenario?"ck3-frontend-selected-fixture-scenario-candidate-v1":"ck3-frontend-selected-1066-feudal-candidate-v1")
                    &&StrictJson.text(n.get("status")).equals("ready"),"selected fixture schema/status required");StrictJson.trueValue(n.get("read_only"));
            if(scenario)StrictJson.require(StrictJson.text(n.get("profile_id")).equals(FrontendFixturePolicy.PROFILE_ID),"closed scenario profile required");
            JsonNode group=n.get("selected_bookmark_group_key");StrictJson.require(group!=null,"explicit nullable bookmark group required");
            if(n.has("query_sequence"))StrictJson.integer(n.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX);
            if(n.has("accepted"))StrictJson.trueValue(n.get("accepted"));
            return new Selected(kind,group.isNull()?Optional.empty():Optional.of(StrictJson.text(group)),StrictJson.text(n.get("selected_bookmark_key")),
                    StrictJson.text(n.get("selected_character_name_key")),StrictJson.text(n.get("selected_character_government_key")),
                    Math.toIntExact(StrictJson.integer(n.get("selected_bookmark_start_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)),
                    n.has("native_model")?Optional.of(new RawJson(StrictJson.canonical(n.get("native_model"),1<<20))):Optional.empty(),
                    n.has("step")||n.has("route")||n.has("query_sequence")||n.has("backend_id")||n.has("accepted")?Optional.of(new SelectedDiagnostics(
                            optionalText(n,"step"),optionalText(n,"route"),n.has("query_sequence")?Optional.of(StrictJson.integer(n.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX)):Optional.empty(),
                            optionalText(n,"backend_id"),n.has("accepted"))):Optional.empty());
        }
        private static Optional<String> optionalText(JsonNode n,String key) {return n.has(key)?Optional.of(StrictJson.text(n.get(key))):Optional.empty();}
    }
    public FixtureStartSubmission {
        Objects.requireNonNull(kind);Objects.requireNonNull(binding);Objects.requireNonNull(policyBinding);Objects.requireNonNull(before);
        Objects.requireNonNull(selectedCandidate);Objects.requireNonNull(bookmarkAcknowledgement);Objects.requireNonNull(selectionAcknowledgement);Objects.requireNonNull(acknowledgement);
        before=jsonDomain(before);bookmarkAcknowledgement=bookmarkAcknowledgement.map(FixtureStartSubmission::jsonDomain);
        selectionAcknowledgement=selectionAcknowledgement.map(FixtureStartSubmission::jsonDomain);acknowledgement=jsonDomain(acknowledgement);
        StrictJson.require(policyBinding.kind()==kind&&selectedCandidate.kind()==kind,"fixture receipt crossed its actual policy branch");
        JsonNode route=StrictJson.parse(before.bytes());StrictJson.require(route.isObject()&&StrictJson.text(route.get("route")).equals("bookmarks"),"actual pre-Start bookmarks route required");
        StrictJson.require(kind==FrontendFixturePolicy.Kind.SCENARIO||bookmarkAcknowledgement.isEmpty(),"Robert does not submit scenario bookmark selection");
        requireAck(acknowledgement,kind==FrontendFixturePolicy.Kind.SCENARIO?Primitive.SCENARIO_START:Primitive.START_BOOKMARK);
    }
    public boolean postconditionVerified() { return false; }
    public boolean fixtureTargetIdentityProven() { return false; }
    /** Embedded JSON domain only; the actual immutable native packets remain in their original Action/Read receipts. */
    private static RawJson jsonDomain(RawJson raw){return new RawJson(StrictJson.canonical(StrictJson.parse(raw.bytes(),1<<20),1<<20));}
    public ObjectNode toJson() {
        boolean scenario=kind==FrontendFixturePolicy.Kind.SCENARIO;ObjectNode n=StrictJson.object();
        n.put("schema",scenario?"ck3-frontend-fixture-scenario-start-submission-v1":"ck3-frontend-fixture-robert-start-submission-v1");n.put("schema_version",1);
        if(scenario)n.put("profile_id",FrontendFixturePolicy.PROFILE_ID);
        n.put("accepted",true);n.put("status","acknowledged_verification_pending");n.put("requested_character_name_key",selectedCandidate.characterNameKey());
        n.put("pre_start_identity_proven",true);n.put("postcondition_verified",false);n.put("fixture_target_identity_proven",false);
        ObjectNode b=StrictJson.object();b.put("bridge_pid",binding.bridgePid());b.put("connection_generation",binding.connectionGeneration());n.set("binding",b);
        n.set("policy_binding",policyBinding.toJson());n.set("before",StrictJson.parse(before.bytes()));n.set("selected_candidate",selectedCandidate.toJson());
        if(scenario)setOptional(n,"bookmark_acknowledgement",bookmarkAcknowledgement);
        setOptional(n,"selection_acknowledgement",selectionAcknowledgement);n.set("acknowledgement",StrictJson.parse(acknowledgement.bytes()));
        n.put("uses_ocr",false);n.put("uses_keyboard",false);n.put("uses_mouse",false);return n;
    }
    public static FixtureStartSubmission fromJson(JsonNode raw) {
        StrictJson.require(raw instanceof ObjectNode,"fixture submission object required");String schema=StrictJson.text(raw.get("schema"));
        boolean scenario=schema.equals("ck3-frontend-fixture-scenario-start-submission-v1");
        StrictJson.require(scenario||schema.equals("ck3-frontend-fixture-robert-start-submission-v1"),"closed fixture submission schema required");
        Set<String> fields=new java.util.HashSet<>(Set.of("schema","schema_version","accepted","status","requested_character_name_key","pre_start_identity_proven",
                "postcondition_verified","fixture_target_identity_proven","binding","policy_binding","before","selected_candidate","selection_acknowledgement","acknowledgement","uses_ocr","uses_keyboard","uses_mouse"));
        if(scenario)fields.addAll(Set.of("profile_id","bookmark_acknowledgement"));ObjectNode n=StrictJson.object(raw,fields);
        StrictJson.integer(n.get("schema_version"),1,1);StrictJson.trueValue(n.get("accepted"));StrictJson.trueValue(n.get("pre_start_identity_proven"));
        StrictJson.require(StrictJson.text(n.get("status")).equals("acknowledged_verification_pending"),"fixture Start must retain verification pending");
        for(String key:java.util.List.of("postcondition_verified","fixture_target_identity_proven","uses_ocr","uses_keyboard","uses_mouse"))falseValue(n.get(key));
        if(scenario)StrictJson.require(StrictJson.text(n.get("profile_id")).equals(FrontendFixturePolicy.PROFILE_ID),"closed fixture profile required");
        var kind=scenario?FrontendFixturePolicy.Kind.SCENARIO:FrontendFixturePolicy.Kind.ROBERT;Selected selected=Selected.fromJson(n.get("selected_candidate"),kind);
        StrictJson.require(StrictJson.text(n.get("requested_character_name_key")).equals(selected.characterNameKey()),"fixture request differs from selected model");
        ObjectNode b=StrictJson.object(n.get("binding"),Set.of("bridge_pid","connection_generation"));
        var binding=new FrontendRulesData.Binding(StrictJson.integer(b.get("bridge_pid"),1,0xffff_ffffL),StrictJson.integer(b.get("connection_generation"),BigInteger.ONE,StrictJson.UINT64_MAX));
        return new FixtureStartSubmission(kind,binding,FrontendFixturePolicy.Binding.fromJson(n.get("policy_binding")),raw(n.get("before")),selected,
                scenario?optional(n.get("bookmark_acknowledgement")):Optional.empty(),optional(n.get("selection_acknowledgement")),raw(n.get("acknowledgement")));
    }
    public static void requireAck(RawJson raw,Primitive step) {
        JsonNode n=StrictJson.parse(raw.bytes());StrictJson.require(n.isObject(),"actual native fixture ACK object required");
        StrictJson.trueValue(n.get("accepted"));StrictJson.require(StrictJson.text(n.get("step")).equals(step.operation().value())
                &&StrictJson.text(n.get("backend_id")).equals("native-headless")&&StrictJson.text(n.get("status")).equals("acknowledged_verification_pending"),"original fixture ACK binding required");
    }
    private static void falseValue(JsonNode n) { StrictJson.require(n!=null&&n.isBoolean()&&!n.booleanValue(),"actual JSON false required"); }
    private static RawJson raw(JsonNode n) { StrictJson.require(n!=null&&n.isObject(),"original fixture evidence object required");return new RawJson(StrictJson.canonical(n,1<<20)); }
    private static Optional<RawJson> optional(JsonNode n) { StrictJson.require(n!=null,"explicit nullable original ACK required");return n.isNull()?Optional.empty():Optional.of(raw(n)); }
    private static void setOptional(ObjectNode n,String key,Optional<RawJson> raw) { if(raw.isPresent())n.set(key,StrictJson.parse(raw.get().bytes()));else n.putNull(key); }
}
