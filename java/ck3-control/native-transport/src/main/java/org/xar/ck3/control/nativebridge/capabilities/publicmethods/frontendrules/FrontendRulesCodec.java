package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesPostconditions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.LoadedFeaturesCodec;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

/** Original Python public result projection over the installed native producer's typed original receipts. */
public final class FrontendRulesCodec {
    private FrontendRulesCodec() { }
    public static Request decode(Method method,PublicBindings.Arguments arguments) {
        ObjectNode object;
        if(arguments instanceof PublicBindings.Missing) {
            StrictJson.require(method.emptyArguments(),"missing required original frontend arguments");object=StrictJson.object();
        } else {
            StrictJson.require(arguments instanceof PublicBindings.Value,"frontend arguments must be an object; explicit null is distinct");
            object=object(((PublicBindings.Value)arguments).original());
        }
        if(method.emptyArguments()) { StrictJson.object(object,Set.of());return new Empty(method); }
        return switch(method) {
            case SELECT_RULE->{ StrictJson.object(object,Set.of("rule_key","expected_current_setting_key","desired_setting_key"));yield new Select(new ScriptKey(text(object,"rule_key")),new ScriptKey(text(object,"expected_current_setting_key")),new ScriptKey(text(object,"desired_setting_key"))); }
            case START_1066->{ StrictJson.object(object,Set.of("character_name_key"));yield new Start(text(object,"character_name_key")); }
            case LOADED_FEATURES->{ StrictJson.object(object,Set.of("expected_revision"));yield new Features(PublicUnsigned64.parse(object.get("expected_revision"),PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL)); }
            default->throw new IllegalArgumentException("original frontend request profile absent");
        };
    }
    public static RawJson encodeRequest(Request request) {
        ObjectNode result=StrictJson.object();
        if(request instanceof Select value) { result.put("rule_key",value.ruleKey().value());result.put("expected_current_setting_key",value.expectedCurrentSettingKey().value());result.put("desired_setting_key",value.desiredSettingKey().value()); }
        else if(request instanceof Start value)result.put("character_name_key",value.characterNameKey());
        else if(request instanceof Features value)result.put("expected_revision",decimal(value.expectedRevision(),false));
        return raw(result);
    }
    public static RawJson encode(Response result) {
        if(result instanceof ReadResponse value)return raw(read(value.observation()));
        if(result instanceof Selected value)return raw(selected(value));
        if(result instanceof Closed value)return raw(closed(value));
        if(result instanceof Opened value) { value.action().ifPresent(action->requireAction(action,"activate-frontend-game-rules-v1",action.ack().orElseThrow().originalResultToken().orElseThrow(),value.observation().receipt()));ObjectNode out=StrictJson.object();out.put("status","observed");out.put("dispatch_invoked",value.action().isPresent());out.set("observation",read(value.observation()));return raw(out); }
        if(result instanceof Transition value)return raw(transition(value));
        if(result instanceof Prepared value)return raw(prepared(value));
        if(result instanceof Started value)return encodeStarted(value);
        throw new IllegalArgumentException("unknown typed frontend result");
    }
    public static ObjectNode read(ReadEvidence evidence) {
        ObjectNode original=original(evidence.receipt());
        if(evidence instanceof Selections value) {
            RuleSelections typed=value.actual().value();
            requireFrontendRead(value.receipt(),typed.source(),typed.querySequence(),value.appliedInstance()?"query-frontend-applied-game-rules-v1":"query-frontend-game-rule-selections-v1");
            StrictJson.require(org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.selections(raw(original),typed.source(),typed.querySequence(),value.appliedInstance()).equals(typed),"actual rule read changed during public encoding");
            original.set("binding",binding(typed.source()));original.put("query_sequence",decimal(typed.querySequence(),true));return original;
        }
        if(evidence instanceof Window value) {
            RuleWindow typed=value.actual().value();
            requireFrontendRead(value.receipt(),typed.source(),typed.querySequence(),"query-frontend-game-rules-window-v1");
            StrictJson.require(org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.window(raw(original),typed.source(),typed.querySequence()).equals(typed),"actual rule-window read changed during public encoding");
            original.set("binding",binding(typed.source()));original.put("query_sequence",decimal(typed.querySequence(),true));return original;
        }
        if(evidence instanceof RouteRead value) {
            ObservedRoute typed=value.actual().value();
            requireFrontendRead(value.receipt(),typed.source(),typed.querySequence(),"query-frontend-gui-route-v1");
            StrictJson.require(org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.route(raw(original),typed.source(),typed.querySequence()).equals(typed),"actual route read changed during public encoding");
            ObjectNode out=header("ck3-frontend-gui-route-v1");out.put("step","query-frontend-gui-route-v1");out.put("accepted",true);out.put("route",typed.route().wire());copyNullable(original,out,"backend_id");return out;
        }
        if(evidence instanceof Tree value) {
            GuiTree typed=value.actual().value();
            requireFrontendRead(value.receipt(),typed.source(),typed.querySequence(),"inspect-frontend-gui-tree-v1");
            StrictJson.require(org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.tree(raw(original),typed.source(),typed.querySequence()).equals(typed),"actual tree read changed during public encoding");
            ObjectNode out=header("ck3-frontend-gui-tree-inspection-v1");
            for(String field:List.of("step","accepted","status","scope_root_name","root_available","truncated","widget_count","widgets"))out.set(field,original.get(field).deepCopy());
            copyNullable(original,out,"backend_id");out.put("read_only",true);noInput(out);return out;
        }
        return features((FeaturesRead)evidence,original);
    }
    private static ObjectNode features(FeaturesRead value,ObjectNode original) {
        var typed=value.actual().value();var manifest=typed.manifest();var decoded=LoadedFeaturesCodec.decode(raw(original),manifest.build(),manifest.nativeRevision(),manifest.dateRaw());
        StrictJson.require(decoded.manifest().equals(manifest)&&decoded.querySequence().equals(typed.querySequence()),"loaded-feature original differs from actual coordinator decoder");
        var before=value.receipt().request().before().frame();
        StrictJson.require(before.snapshotId().equals(typed.snapshotId())&&before.revision().equals(typed.revision())&&before.identity().nativeRevision().equals(manifest.nativeRevision())&&before.identity().dateRaw().intValueExact()==manifest.dateRaw(),"loaded-feature source is another physical frame");
        ObjectNode frame=(ObjectNode)original.get("loaded_feature_manifest");ObjectNode publicFrame=frame.deepCopy();nativeIdentity(publicFrame,"snapshot_revision");
        ObjectNode out=original.deepCopy();out.put("schema_version",1);out.put("scope","exact-loaded-feature-manifest");out.put("query_sequence",decimal(typed.querySequence(),true));
        nativeIdentity(out,"snapshot_revision");out.set("loaded_feature_manifest",publicFrame);
        out.put("loaded_feature_manifest_ready",manifest.readiness().actionableReady());out.put("queried_snapshot_id",typed.snapshotId());out.put("queried_revision",decimal(typed.revision(),false));out.put("queried_native_revision",decimal(manifest.nativeRevision(),true));
        for(String key:List.of("schema","date_raw","unavailable_reason","build","effective_feature_flags","script_dlc_keys","entitlements","readiness","provenance"))out.set(key,frame.get(key).deepCopy());
        ObjectNode source=StrictJson.object();source.put("game_version",manifest.build().version());source.put("executable_sha256",manifest.build().sha256());source.put("snapshot_id",typed.snapshotId());source.put("revision",decimal(typed.revision(),false));source.put("native_revision",decimal(manifest.nativeRevision(),true));source.put("date_raw",manifest.dateRaw());source.put("paused",true);source.put("backend_id",typed.sourceBackendId());out.set("source",source);
        ObjectNode binding=StrictJson.object();binding.put("snapshot_id",typed.snapshotId());binding.put("revision",decimal(typed.revision(),false));binding.put("native_revision",decimal(manifest.nativeRevision(),true));binding.put("date_raw",manifest.dateRaw());binding.put("expected_revision",decimal(value.expectedRevision(),false));out.set("binding",binding);return out;
    }
    private static ObjectNode selected(Selected value) {
        var initial=value.before().actual().value();var after=value.observation().actual().value();var ack=rulesAck(value.acknowledgement(),initial.source(),RulesAction.SELECT);
        var request=new FrontendRulesRequests.SelectRule(value.request().ruleKey(),value.request().expectedCurrentSettingKey(),value.request().desiredSettingKey());
        FrontendRulesPostconditions.selected(initial,value.windowBefore().actual().value(),request,ack,actionSequence(value.action()),after);
        requireAction(value.action(),"select-frontend-game-rule-v1",value.acknowledgement(),value.observation().receipt());
        ObjectNode out=StrictJson.object();out.put("status","observed");out.put("rule_key",value.request().ruleKey().value());out.put("selected_setting_key",value.request().desiredSettingKey().value());out.set("acknowledgement",object(value.acknowledgement()));out.set("before",read(value.before()));out.set("observation",read(value.observation()));out.put("applied_settings_proven",false);return out;
    }
    private static ObjectNode closed(Closed value) {
        var initial=value.before().actual().value();var action=value.apply()?RulesAction.APPLY_AND_HIDE:RulesAction.HIDE;
        FrontendRulesPostconditions.closed(initial,rulesAck(value.acknowledgement(),initial.source(),action),actionSequence(value.action()),value.observation().actual().value());
        requireAction(value.action(),value.apply()?"apply-and-hide-frontend-game-rules-v1":"hide-frontend-game-rules-v1",value.acknowledgement(),value.observation().receipt());
        ObjectNode out=StrictJson.object();out.put("status","observed");out.set("acknowledgement",object(value.acknowledgement()));out.set("before",read(value.before()));out.set("window_observation",read(value.observation()));out.put("window_closed_proven",true);out.put("applied_settings_proven",false);return out;
    }
    private static ObjectNode transition(Transition value) {
        String step=switch(value.method()) { case NEW_GAME->"activate-frontend-new-game-v1";case PICK_ANY->"activate-frontend-pick-any-character-v1";case RULER_DESIGNER->"activate-frontend-ruler-designer-v1";default->throw new IllegalArgumentException("route action absent"); };
        Route before=value.method()==Method.NEW_GAME?Route.MAIN_MENU:value.method()==Method.PICK_ANY?Route.BOOKMARKS:Route.LOBBY;
        Route after=value.method()==Method.NEW_GAME?Route.BOOKMARKS:value.method()==Method.PICK_ANY?Route.LOBBY:Route.RULER_DESIGNER;
        FrontendRulesPostconditions.route(value.before().actual().value(),nativeAck(value.acknowledgement(),step),actionSequence(value.action()),value.after().actual().value(),before,after,step);
        requireAction(value.action(),step,value.acknowledgement(),value.after().receipt());
        if(value.method()==Method.RULER_DESIGNER)StrictJson.require(value.beforeInspection().isPresent()&&value.beforeInspection().orElseThrow().actual().value().defaultDesignerReady(),"actual default designer target was unavailable before submit");
        ObjectNode out=actionHeader(step,switch(value.method()) { case NEW_GAME->"open_new_game";case PICK_ANY->"pick_any_character";default->"open_ruler_designer"; });out.set("before",read(value.before()));out.set("after",read(value.after()));out.set("acknowledgement",object(value.acknowledgement()));value.beforeInspection().ifPresent(tree->out.set("before_inspection",read(tree)));return out;
    }
    private static ObjectNode prepared(Prepared value) {
        ObjectNode pick=transition(value.pickAny());GuiTree target=value.selectionTarget().actual().value(),after=value.lobbyInspection().actual().value();
        StrictJson.require(target.randomPlayableReady()&&after.defaultDesignerReady()&&target.source().equals(after.source()),"custom ruler preparation lacks actual actionable lobby observations");
        for(int index=0;index<value.selections().size();index++)nativeAck(value.selectionAcknowledgements().get(index),"activate-frontend-select-random-playable-v1");
        requireAction(value.selections().getLast(),"activate-frontend-select-random-playable-v1",value.selectionAcknowledgements().getLast(),value.lobbyInspection().receipt());
        ObjectNode out=actionHeader("prepare-frontend-custom-ruler-v1","prepare_custom_ruler");out.set("before",pick.get("before"));out.set("after",pick.get("after"));out.set("pick_any_acknowledgement",pick.get("acknowledgement"));out.set("selection_target_inspection",read(value.selectionTarget()));out.set("selection_acknowledgement",object(value.selectionAcknowledgements().getLast()));out.set("lobby_inspection",read(value.lobbyInspection()));out.put("selection_attempt_count",value.selections().size());var rows=out.putArray("selection_acknowledgements");value.selectionAcknowledgements().forEach(ack->rows.add(object(ack)));return out;
    }
    private static ObjectNode started(Started value) {
        var candidate=value.candidate();ObjectNode snapshot=object(value.material().afterSnapshot()),root=campaignRoot(value.material());
        StrictJson.trueValue(snapshot.get("paused"));StrictJson.trueValue(snapshot.get("map_ready"));ObjectNode played=requiredObject(snapshot,"played_character");ObjectNode government=requiredObject(root,"government");
        BigInteger player=publicInteger(played.get("character_id"),true),nativeRevision=publicInteger(snapshot.get("native_revision"),true);int date=Math.toIntExact(StrictJson.integer(snapshot.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE));
        FrontendRulesPostconditions.started(value.before().actual().value(),candidate,nativeAck(value.acknowledgement(),"activate-frontend-start-selected-bookmark-v1"),new FrontendRulesPostconditions.MapPost(text(snapshot,"snapshot_id"),nativeRevision,date,player,true,true),new FrontendRulesPostconditions.CampaignRootPost(bool(root,"campaign_root_context_ready"),publicInteger(root.get("queried_native_revision"),true),Math.toIntExact(StrictJson.integer(root.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)),publicInteger(root.get("player_character_id"),true),text(government,"key")));
        StrictJson.require(value.material().action().ack().orElseThrow().originalResultToken().orElseThrow().equals(value.acknowledgement()),"Start public ACK is not its original coordinator dispatch");
        ObjectNode selected=header("ck3-frontend-selected-1066-feudal-candidate-v1");selected.put("step","query-frontend-selected-1066-feudal-candidate-v1");selected.put("accepted",true);selected.put("status","ready");selected.put("route","bookmarks");selected.put("backend_id","native-headless");selected.put("query_sequence",decimal(candidate.querySequence(),true));selected.put("read_only",true);candidate.bookmarkGroupKey().ifPresentOrElse(key->selected.put("selected_bookmark_group_key",key),()->selected.putNull("selected_bookmark_group_key"));selected.put("selected_bookmark_key",candidate.bookmarkKey());selected.put("selected_character_name_key",candidate.characterNameKey());selected.put("selected_character_government_key",candidate.governmentKey());selected.put("selected_bookmark_start_date_raw",candidate.dateRaw());
        ObjectNode out=actionHeader("activate-frontend-start-selected-bookmark-v1","select_and_start_1066_bookmark_character");out.put("schema","ck3-frontend-1066-bookmark-character-start-v1");out.put("requested_character_name_key",value.request().characterNameKey());out.set("before",read(value.before()));out.set("selected_candidate",selected);out.set("acknowledgement",object(value.acknowledgement()));out.set("after_snapshot",snapshot);out.set("campaign_root",root);value.selectionAcknowledgement().ifPresentOrElse(ack->out.set("selection_acknowledgement",object(ack)),()->out.putNull("selection_acknowledgement"));return out;
    }
    private static ObjectNode actionHeader(String step,String action) { ObjectNode out=header("ck3-frontend-gui-action-v1");out.put("step",step);out.put("accepted",true);out.put("status","verified");out.put("action",action);out.put("input_backend","native_gui_semantic_activation");out.put("postcondition_verified",true);out.put("backend_id","native-headless");noInput(out);return out; }
    /** Preserve full Driver numeric tokens, including 1.0 and -0.0, in their original public producer subtree. */
    private static RawJson encodeStarted(Started value) {
        ObjectNode output=started(value);output.remove("after_snapshot");output.remove("campaign_root");byte[] prefix=raw(output).bytes();
        var bytes=new java.io.ByteArrayOutputStream();bytes.write(prefix,0,prefix.length-1);
        bytes.writeBytes(",\"after_snapshot\":".getBytes(java.nio.charset.StandardCharsets.UTF_8));bytes.writeBytes(value.material().afterSnapshot().bytes());
        bytes.writeBytes(",\"campaign_root\":".getBytes(java.nio.charset.StandardCharsets.UTF_8));bytes.writeBytes(raw(campaignRoot(value.material())).bytes());bytes.write('}');
        byte[] result=bytes.toByteArray();StrictJson.parse(result,StrictJson.EXPLICIT_MAX_BYTES);return new RawJson(result);
    }
    private static BigInteger actionSequence(ActionReceipt action) { return ((ActionState.Settled)action.state()).attempt().guard().origin().requireFrontend().frame().querySequence(); }
    private static ObjectNode campaignRoot(StartMaterial material) {
        var read=material.campaignRootRead();var frame=read.request().before().frame();
        var normalized=CampaignRootContextJson.normalizeNativeResult(OpportunityJson.object(OpportunityJson.parse(read.original().originalResultToken().orElseThrow().bytes()),"original campaign root result"),frame.identity().dateRaw(),frame.identity().nativeRevision());
        ObjectNode result=object(new RawJson(OpportunityJson.encode(normalized)));ObjectNode root=requiredObject(result,"campaign_root_context");
        for(String key:List.of("schema_version","date_raw","local_player_id","player_character_id","player_character_alive","player_monthly_gold_income","player_health","player_domain_size","player_domain_limit","player_targeting_faction_count","council","primary_title","primary_title_succession_character_ids","held_title_partition","capital_province_id","immediate_liege_character_id","top_liege_character_id","independent","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids","related_character_contexts","government","selected_game_rule_tokens","native_selected_game_rule_token_count","readiness","unavailable_reason","provenance"))if(root.has(key))result.set(key,root.get(key).deepCopy());
        result.put("campaign_root_context_ready",bool(requiredObject(root,"readiness"),"ready"));result.put("queried_snapshot_id",frame.snapshotId());result.put("queried_revision",decimal(frame.revision(),false));result.put("queried_native_revision",decimal(frame.identity().nativeRevision(),true));
        nativeIdentity(result,"query_sequence");nativeIdentity(result,"snapshot_revision");nativeIdentity(root,"snapshot_revision");return result;
    }
    private static void requireAction(ActionReceipt action,String step,RawJson ack,PlanningReadReceipt read) {
        confirmed(action);var state=(ActionState.Settled)action.state();var observed=((ActionState.FrontendApplied)state.settlement()).observation();observed.validate(action.command(),state.attempt());
        StrictJson.require(action.command().operation().value().equals(step)&&action.ack().orElseThrow().originalResultToken().orElseThrow().equals(ack)&&observed.readRequestId().equals(read.requestId())&&observed.after().equals(read.after().binding().origin().requireFrontend()),"public frontend action crossed its actual dispatch/later original read");
    }
    private static RulesAck rulesAck(RawJson ack,Source source,RulesAction action) { return org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.rulesAck(ack,source,action); }
    private static void requireFrontendRead(PlanningReadReceipt read,Source source,BigInteger sequence,String operation) {
        var actual=read.after().binding().origin().requireFrontend();
        StrictJson.require(actual.frame() instanceof FrontendFrame.Menu&&actual.bridgePid()==source.binding().bridgePid()&&actual.connectionGeneration().equals(source.binding().connectionGeneration())&&actual.frame().querySequence().equals(sequence)&&read.request().operation().value().equals(operation),"public frontend value differs from its actual menu/process/connection/query receipt");
    }
    private static NativeAck nativeAck(RawJson ack,String step) { return org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.nativeAck(ack,step); }
    public static ObjectNode original(PlanningReadReceipt read) { StrictJson.require(read.original().nativeOk(),"original native query was rejected");return object(read.original().originalResultToken().orElseThrow()); }
    public static ObjectNode object(RawJson raw) { JsonNode value=StrictJson.parse(raw.bytes(),StrictJson.EXPLICIT_MAX_BYTES);StrictJson.require(value instanceof ObjectNode,"bounded original JSON object required");return (ObjectNode)value; }
    private static ObjectNode requiredObject(ObjectNode parent,String field) { JsonNode value=parent.get(field);StrictJson.require(value instanceof ObjectNode,"required actual object: "+field);return (ObjectNode)value; }
    private static ObjectNode binding(Source source) { ObjectNode value=StrictJson.object();value.put("bridge_pid",source.binding().bridgePid());value.put("connection_generation",decimal(source.binding().connectionGeneration(),true));return value; }
    private static ObjectNode header(String schema) { ObjectNode value=StrictJson.object();value.put("schema",schema);value.put("schema_version",1);return value; }
    private static void noInput(ObjectNode value) { value.put("uses_ocr",false);value.put("uses_keyboard",false);value.put("uses_mouse",false); }
    private static void copyNullable(ObjectNode source,ObjectNode target,String field) { if(source.has(field))target.set(field,source.get(field).deepCopy());else target.putNull(field); }
    private static String text(ObjectNode value,String field) { return StrictJson.text(value.get(field)); }
    private static boolean bool(ObjectNode value,String field) { JsonNode raw=value.get(field);StrictJson.require(raw!=null&&raw.isBoolean(),"required actual boolean: "+field);return raw.booleanValue(); }
    private static BigInteger publicInteger(JsonNode value,boolean positive) { return PublicUnsigned64.parse(value,positive?PublicUnsigned64.Minimum.ONE:PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL); }
    private static String decimal(BigInteger value,boolean positive) { return PublicUnsigned64.canonical(value,positive?PublicUnsigned64.Minimum.ONE:PublicUnsigned64.Minimum.ZERO); }
    /** Native/archive integers remain original; only these proved public identity roles change representation. */
    private static void nativeIdentity(ObjectNode value,String field) { BigInteger actual=StrictJson.integer(value.get(field),BigInteger.ONE,PublicUnsigned64.MAXIMUM);value.put(field,decimal(actual,true)); }
    public static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value,StrictJson.EXPLICIT_MAX_BYTES)); }
}
