package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;

/** Checked original exact .4 Faith/presentation DTO, including unknown/null native observations. */
public final class GuiPresentationResult {
    private static final List<String> FLAGS=List.of("requested","available","source_bound","tab_observed","picker_observed",
            "preview_observed","hover_source_matches","tooltip_stack_observed","tooltip_root_visible","leave_observed","cache_complete","rendered_pixels_observed");
    private static final Set<String> SELECTORS=Set.of("presentation_target","presentation_index","presentation_tab","presentation_receipt");
    private GuiPresentationResult() { }
    public static boolean requested(String operation,WindowKind kind,ObjectNode fields){
        return !Set.of("query","open_faith").contains(operation)||kind!=WindowKind.FAITH
                ||SELECTORS.stream().anyMatch(k->fields.hasNonNull(k));
    }
    public static boolean tooltipQuery(String operation,ObjectNode fields){
        String target=fields.hasNonNull("presentation_target")?text(fields,"presentation_target"):"";
        return operation.equals("query")&&!target.isEmpty()&&!Set.of("clerical_puppet","external_clerical_puppet").contains(target)
                &&fields.hasNonNull("presentation_receipt");
    }
    public static void validate(ObjectNode value,Context context,String operation,WindowKind kind,Subject subject,ObjectNode fields){
        need(context.build()==Build.CROZIER4,"original Faith/presentation DTO requires exact .4");
        GuiValidation.semantic(context,operation,kind,subject,fields);
        boolean active=requested(operation,kind,fields),query=operation.equals("query");
        envelope(value,context,operation,kind,subject,active,fields);
        JsonNode node=value.get("presentation_ui");
        if(!active){need(node==null||node.isNull(),"unsolicited presentation observation");return;}
        ObjectNode leaf=obj(node);equal(leaf,"schema","ck3-presentation-ui-v1");
        if(kind==WindowKind.TOOLTIPS){tooltipStack(value,leaf,operation,nullableField(fields,"presentation_receipt"));return;}
        for(String key:FLAGS)bool(leaf,key);
        yes(leaf,"requested");no(leaf,"rendered_pixels_observed");
        need(bool(leaf,"available")==bool(value,"available")&&text(leaf,"status").equals(text(value,"status")),"presentation envelope/leaf status changed");
        JsonNode reason=required(leaf,"unavailable_reason");
        need(bool(leaf,"available")?reason.isNull():reason.isTextual()&&!reason.textValue().isEmpty(),"presentation reason/availability changed");
        for(String k:List.of("subject_id","target_index","receipt_id","active_tab","target_kind","action_owner_epoch","observation_owner_epoch",
                "post_window_visible","tooltip_active_count","tooltip_top_locked","cache_texts","targets"))required(leaf,k);
        nullableNumber(leaf,"subject_id",BigInteger.ZERO,U32.subtract(BigInteger.TWO));nullableNumber(leaf,"target_index",BigInteger.ZERO,BigInteger.valueOf(127));
        if(Set.of(WindowKind.HOLDING,WindowKind.PERSONAL_BELIEFS).contains(kind)&&!leaf.get("subject_id").isNull())
            need(integer(leaf,"subject_id").signum()>0,"observed Province/Character zero");
        if(kind==WindowKind.HOLDING&&!leaf.get("subject_id").isNull())range(integer(leaf,"subject_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
        for(String k:List.of("action_owner_epoch","observation_owner_epoch"))nullableNumber(leaf,k,BigInteger.ONE,U64);
        nullableNumber(leaf,"tooltip_active_count",BigInteger.ZERO,BigInteger.valueOf(32));nullableNumber(leaf,"tooltip_top_locked",BigInteger.ZERO,BigInteger.valueOf(255));
        JsonNode visible=leaf.get("post_window_visible");need(visible.isNull()||visible.isBoolean()&&visible.booleanValue()==bool(value,"effective_visible"),"presentation visibility changed");
        String tab=nullableField(leaf,"active_tab"),target=nullableField(leaf,"target_kind"),receipt=nullableField(leaf,"receipt_id");
        if(tab!=null)need((kind==WindowKind.FAITH?Set.of("beliefs","holy_sites"):kind==WindowKind.PERSONAL_BELIEFS?Set.of("tenets","doctrines"):Set.of()).contains(tab),"observed tab belongs to another window");
        need(bool(leaf,"tab_observed")== (tab!=null),"observed tab cannot infer null");
        if(target!=null)need(GuiValidation.targetKind(target)==kind,"observed target belongs to another window");
        if(receipt!=null)new ReceiptId(receipt);
        if(bool(leaf,"source_bound")){
            need(bool(value,"subject_id_available")&&leaf.get("subject_id").equals(value.get("current_subject_id")),"presentation source differs from actual selected subject");
            if(subject.value().signum()!=0||!query||fields.hasNonNull("presentation_target")&&!text(fields,"presentation_target").isEmpty())equal(leaf,"subject_id",subject.value());
            if(kind==WindowKind.PERSONAL_BELIEFS)equal(leaf,"subject_id",context.before().frame().identity().player());
            if(fields.hasNonNull("presentation_target")&&!text(fields,"presentation_target").isEmpty()){
                equal(leaf,"target_kind",text(fields,"presentation_target"));if(fields.hasNonNull("presentation_index"))equal(leaf,"target_index",integer(fields,"presentation_index"));else need(leaf.get("target_index").isNull(),"clerical query has no row selector");}
        }
        if(!bool(value,"window_exists")&&bool(leaf,"available")){
            need(query||bool(value,"dispatch_invoked"),"absent window neither independently observed nor opening");
            need(!bool(leaf,"source_bound")&&visible.isBoolean()&&!visible.booleanValue(),"absent window grants visible source");}
        if(!query&&bool(leaf,"available")){
            yes(value,"dispatch_invoked","native_dispatch_attempted","verification_pending");
            if(!Set.of("open_holding","open_personal_beliefs","open_clerical_preview").contains(operation))yes(leaf,"source_bound");
            if(Set.of("open_rite_core_picker","show_building_details","open_building_track").contains(operation)){
                equal(leaf,"target_kind",operation.equals("open_rite_core_picker")?"rite_core_tenet_slot":operation.equals("show_building_details")?"holding_building_preview":"holding_building");
                equal(leaf,"target_index",integer(fields,"presentation_index"));}
        }
        if(Set.of("close_presentation_window","close_clerical_preview").contains(operation)&&bool(leaf,"available"))
            need(visible.isNull()&&!leaf.get("action_owner_epoch").isNull(),"close ACK cannot claim known postvisibility");
        if(Set.of("hover_presentation_tooltip","leave_presentation_tooltip").contains(operation)&&bool(leaf,"available"))
            need(receipt!=null&&!leaf.get("action_owner_epoch").isNull()&&bool(leaf,"source_bound"),"tooltip ACK lacks newly minted bound receipt");
        if(tooltipQuery(operation,fields)&&bool(leaf,"available")){
            need(receipt!=null&&receipt.equals(text(fields,"presentation_receipt"))&&!leaf.get("action_owner_epoch").isNull()&&!leaf.get("observation_owner_epoch").isNull()
                    &&integer(leaf,"observation_owner_epoch").compareTo(integer(leaf,"action_owner_epoch"))>0&&bool(leaf,"source_bound")&&bool(leaf,"tooltip_stack_observed"),"tooltip lacks independent later exact receipt/source/stack");
            if(!bool(leaf,"leave_observed"))need(bool(leaf,"hover_source_matches")&&bool(leaf,"tooltip_root_visible")&&!leaf.get("tooltip_active_count").isNull()
                    &&integer(leaf,"tooltip_active_count").signum()>0&&BigInteger.ZERO.equals(leaf.get("tooltip_top_locked").isNull()?null:integer(leaf,"tooltip_top_locked")),"tooltip lacks visible unlocked source");
            else no(leaf,"hover_source_matches");
        }
        clerical(value,leaf,context,operation,kind,subject,fields);holding(leaf,kind);cacheAndTargets(leaf,kind);
    }

    private static void envelope(ObjectNode r,Context c,String op,WindowKind kind,Subject subject,boolean active,ObjectNode fields){
        equal(r,"schema","ck3-ingame-ui-window-v1");equal(r,"window_kind",kind.wire());equal(r,"requested_subject_id",subject.value());
        equal(r,"native_revision",c.before().frame().identity().nativeRevision());equal(r,"date_raw",c.before().frame().identity().dateRaw());equal(r,"played_character_id",c.before().frame().identity().player());yes(r,"paused");build(r,c.build());
        for(String k:List.of("accepted","available","dispatch_invoked","verification_pending","window_exists","effective_visible","enabled","subject_id_available","application_owner_thread_verified","gui_owner_binding_verified"))bool(r,k);
        need(bool(r,"accepted")==bool(r,"available"),"presentation acceptance/availability changed");
        bool(r,"owner_character_id_available");need(!bool(r,"owner_character_id_available")&&required(r,"owner_character_id").isNull(),"presentation cannot claim selected Unit owner");
        for(String k:List.of("current_subject_id","native_army_id"))if(!required(r,k).isNull()||bool(r,"subject_id_available"))integer(r,k,BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        need(!bool(r,"subject_id_available")||!r.get("current_subject_id").isNull()&&integer(r,"current_subject_id").compareTo(U32.subtract(BigInteger.ONE))<0,"invalid selected full subject");
        equal(r,"native_army_id",BigInteger.ZERO);integer(r,"thread_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));integer(r,"pump_epoch",BigInteger.ZERO,U64);
        no(r,"rng_owner_is_ui_admission_gate");integer(r,"rng_owner_thread_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        integer(r,"gui_context_address",BigInteger.ZERO,U64);integer(r,"gui_owner_address",BigInteger.ZERO,U64);
        String root=switch(kind){case FAITH->"faith_window";case HOLDING->"holding_view";case PERSONAL_BELIEFS->"window_personal_beliefs";case RITE_CREATION->"rite_creation_window";case CLERICAL_INTERACTION->"character_interaction_confirmation_window";case TOOLTIPS->"tooltip_stack";default->throw new IllegalArgumentException("unowned Faith/presentation window");};
        equal(r,"window_name",root);boolean attempted=bool(r,"native_dispatch_attempted");need(!op.equals("query")||!attempted,"query cannot invoke original callback");need(!bool(r,"dispatch_invoked")||attempted,"invocation lacks actual attempt");
        boolean absentQuery=active&&op.equals("query")&&bool(r,"available")&&!bool(r,"window_exists");
        boolean unopened=Set.of("open_faith","open_holding","open_personal_beliefs").contains(op)&&bool(r,"available")&&!bool(r,"window_exists")
                &&text(r,"status").equals("acknowledged_verification_pending")&&bool(r,"dispatch_invoked")&&bool(r,"verification_pending")&&!bool(r,"effective_visible")&&!bool(r,"subject_id_available");
        if(bool(r,"available")){
            yes(r,"application_owner_thread_verified","gui_owner_binding_verified");need(integer(r,"gui_context_address").signum()>0&&integer(r,"gui_owner_address").signum()>0&&integer(r,"thread_id").signum()>0&&integer(r,"pump_epoch").signum()>0,"actual GUI owner unavailable");
            need(bool(r,"window_exists")||unopened||absentQuery,"target window not observed");
            if(op.equals("query")){equal(r,"status","observed");no(r,"dispatch_invoked");need(bool(r,"verification_pending")==tooltipQuery(op,fields),"query pending flag differs from exact tooltip request");}
            else need(bool(r,"verification_pending")&&Set.of("acknowledged_verification_pending","already_visible_verification_pending").contains(text(r,"status")),"ACK cannot grant completed UI postcondition");
        }else{equal(r,"status","unavailable");need(!text(r,"unavailable_reason").isEmpty(),"unavailable UI reason required");}
        ObjectNode tree=obj(required(r,"tree"));boolean rooted=bool(tree,"root_available"),truncated=bool(tree,"truncated");List<Widget> widgets=GuiDecoders.widgets(tree);
        if(kind==WindowKind.TOOLTIPS)need(!rooted&&widgets.isEmpty()&&!truncated&&(text(tree,"scope_root_name").equals(root)||!bool(r,"available")&&text(tree,"scope_root_name").isEmpty()),"global stack must retain empty virtual census");
        else if(unopened||absentQuery)need(!rooted&&widgets.isEmpty()&&!truncated&&text(tree,"scope_root_name").equals(root),"unopened/absent window retains invented tree");
        else if(bool(r,"available"))need(rooted&&!widgets.isEmpty()&&text(tree,"scope_root_name").equals(root)&&widgets.getFirst().runtimeName().equals(root)&&widgets.getFirst().depth()==0&&widgets.getFirst().visible()==bool(r,"effective_visible"),"native target census changed");
        equal(r,"knights_list_scope","military_eligible_not_active_combat_roster");no(r,"combat_knights_read_available","combat_roster_full_ids_available","hover_state_available","hover_readback_is_pixels");
        for(String k:List.of("left_knight_breakdown","right_knight_breakdown","hovered_widget_name","hovered_ui_side"))equal(r,k,"");
        equal(r,"left_knight_count",BigInteger.valueOf(-1));equal(r,"right_knight_count",BigInteger.valueOf(-1));equal(r,"hovered_combat_id",BigInteger.ZERO);
        ObjectNode g=obj(required(r,"combat_geometry"));GuiDecoders.geometry(g);no(g,"available","content_inside_viewport","fit_required");
        need(!text(g,"unavailable_reason").isEmpty(),"unavailable geometry reason required");
        equal(g,"stock_margin_source_sha256",bool(g,"stock_margin_source_verified")?"7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236":"");
        for(String rect:List.of("viewport","window_rect","content_union","proposed_translation")){ObjectNode v=obj(required(g,rect));v.elements().forEachRemaining(n->need(n.isNumber()&&n.doubleValue()==0.0,"unavailable geometry retained coordinates"));}
        need(!r.hasNonNull("army_tooltip"),"unsolicited Army tooltip on Faith wrapper");
        if(r.has("backend_id"))equal(r,"backend_id","native-headless");
    }
    private static void nullableNumber(ObjectNode r,String key,BigInteger min,BigInteger max){if(!required(r,key).isNull())integer(r,key,min,max);}
    private static String nullableField(ObjectNode r,String key){JsonNode n=r.get(key);return n==null||n.isNull()?null:text(r,key);}
    private static String literalText(ObjectNode r,String key){JsonNode value=required(r,key);need(value.isTextual(),"original presentation text required");String text=value.textValue();need(StandardCharsets.UTF_8.newEncoder().canEncode(text),"presentation text must have exact UTF8 bytes");return text;}
    private static String nullableLiteral(ObjectNode r,String key){return required(r,key).isNull()?null:literalText(r,key);}
    private static void cacheAndTargets(ObjectNode leaf,WindowKind kind){
        JsonNode texts=required(leaf,"cache_texts"),targets=required(leaf,"targets");need(texts.isArray()&&texts.size()<=64&&targets.isArray()&&targets.size()<=128,"finite presentation cache/target count");
        int total=0;for(JsonNode n:texts){ObjectNode item=obj(n);keys(item,Set.of("runtime_name","text","sha256"),Set.of());literalText(item,"runtime_name");byte[] bytes=literalText(item,"text").getBytes(StandardCharsets.UTF_8);total+=bytes.length;need(bytes.length<=16384&&total<=262144&&text(item,"sha256").equals(sha256(bytes)),"presentation cache UTF8/SHA differs");}
        Set<String> seen=new HashSet<>();for(JsonNode n:targets){ObjectNode item=obj(n);keys(item,Set.of("index","kind","runtime_name","definition_key","label","effective_visible","enabled"),Set.of());
            int index=count(item,"index",0,127);String target=text(item,"kind");need(GuiValidation.targetKind(target)==kind&&seen.add(target+":"+index),"duplicate/wrong presentation target row");
            literalText(item,"runtime_name");nullableLiteral(item,"definition_key");nullableLiteral(item,"label");bool(item,"effective_visible");bool(item,"enabled");}
    }
    private static void holding(ObjectNode leaf,WindowKind kind){
        if(!leaf.hasNonNull("holding_tracks"))return;ObjectNode t=obj(leaf.get("holding_tracks"));need(kind==WindowKind.HOLDING,"holding tracks belongs to another window");
        keys(t,Set.of("available","unavailable_reason","owner_bound","window_exists","root_exists","effective_visible","selection_category_id","selection_mode","selection_action_raw","selected_building_key"),Set.of());
        bool(t,"owner_bound");boolean available=bool(t,"available");need(available?required(t,"unavailable_reason").isNull():!text(t,"unavailable_reason").isEmpty(),"holding tracks reason changed");
        for(String k:List.of("window_exists","root_exists","effective_visible"))need(required(t,k).isNull()||t.get(k).isBoolean(),"holding tracks nullable visibility type");
        for(String k:List.of("selection_category_id","selection_mode","selection_action_raw"))nullableNumber(t,k,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE));
        String key=nullableField(t,"selected_building_key");if(key!=null)need(!key.isEmpty()&&key.getBytes(StandardCharsets.UTF_8).length<=1024,"holding selected key malformed");
        if(bool(t,"owner_bound")||t.get("root_exists").isBoolean()&&t.get("root_exists").booleanValue())need(t.get("window_exists").isBoolean()&&bool(t,"window_exists"),"holding owner/root without actual window");
        if(t.get("effective_visible").isBoolean()&&bool(t,"effective_visible"))need(bool(t,"owner_bound")&&t.get("root_exists").isBoolean()&&bool(t,"root_exists")&&bool(leaf,"source_bound")&&leaf.get("post_window_visible").isBoolean()&&bool(leaf,"post_window_visible"),"holding visibility lacks actual owned main window");
    }
    private static void tooltipStack(ObjectNode value,ObjectNode leaf,String operation,String receipt){
        ObjectNode sample=obj(required(leaf,"tooltip_clear"));keys(sample,Set.of("available","cleared","phase","active_count","deferred","locked","source_null"),Set.of());
        bool(sample,"cleared");need(bool(sample,"available")==bool(leaf,"available")&&Set.of("","observed","pending","cleared").contains(text(sample,"phase")),"global stack availability/phase changed");
        for(String k:List.of("source_bound","hover_source_matches","tooltip_root_visible","tooltip_stack_observed","leave_observed","cache_complete","rendered_pixels_observed"))no(leaf,k);
        for(String k:List.of("subject_id","target_kind","target_index","post_window_visible"))need(required(leaf,k).isNull(),"global stack invented target/window");
        need(required(leaf,"cache_texts").isArray()&&leaf.get("cache_texts").isEmpty()&&required(leaf,"targets").isArray()&&leaf.get("targets").isEmpty(),"global stack invented cache/targets");
        need(!bool(sample,"cleared")||bool(leaf,"available")&&operation.equals("query"),"stack ACK cannot prove clearance");if(!bool(leaf,"available"))return;
        String actual=text(leaf,"receipt_id");new ReceiptId(actual);nullableNumber(leaf,"action_owner_epoch",BigInteger.ONE,U64);nullableNumber(leaf,"observation_owner_epoch",BigInteger.ONE,U64);
        if(operation.equals("close_tooltips")){need(actual.equals(receipt)&&text(sample,"phase").equals("pending")&&!bool(sample,"cleared")&&!leaf.get("action_owner_epoch").isNull()&&leaf.get("observation_owner_epoch").isNull()
                &&required(sample,"active_count").isNull()&&required(sample,"deferred").isNull()&&required(sample,"locked").isArray()&&sample.get("locked").isEmpty()&&required(sample,"source_null").isArray()&&sample.get("source_null").isEmpty(),"stack clear ACK must retain unknown result");yes(value,"dispatch_invoked","native_dispatch_attempted","verification_pending");return;}
        int count=count(sample,"active_count",0,32);bool(sample,"deferred");need(!leaf.get("observation_owner_epoch").isNull(),"stack lacks actual later query");
        for(String k:List.of("locked","source_null")){JsonNode rows=required(sample,k);need(rows.isArray()&&rows.size()==count,"stack row count differs");for(JsonNode row:rows)need(row.isBoolean(),"stack row boolean required");}
        if(receipt==null)need(text(sample,"phase").equals("observed")&&!bool(sample,"cleared")&&leaf.get("action_owner_epoch").isNull(),"initial stack cannot claim prior clearance");
        else need(actual.equals(receipt)&&!leaf.get("action_owner_epoch").isNull()&&integer(leaf,"observation_owner_epoch").compareTo(integer(leaf,"action_owner_epoch"))>0&&text(sample,"phase").equals("cleared")&&bool(sample,"cleared")&&count==0&&!bool(sample,"deferred"),"clearance lacks later exact receipt and empty stack");
    }
    private static void clerical(ObjectNode value,ObjectNode leaf,Context context,String op,WindowKind kind,Subject subject,ObjectNode fields){
        JsonNode raw=leaf.get("clerical_preview");if(kind!=WindowKind.CLERICAL_INTERACTION){need(raw==null||raw.isNull(),"unsolicited clerical preview");return;}
        if((raw==null||raw.isNull())&&!bool(leaf,"available"))return;ObjectNode c=obj(raw);
        keys(c,Set.of("available","root_bound","window_visible","phase","default_context","window_context","command_submitted","options_mutated","business_outcome_observed"),Set.of());
        bool(c,"root_bound");no(c,"command_submitted","options_mutated","business_outcome_observed");need(bool(c,"available")==bool(leaf,"available"),"clerical availability changed");
        for(String k:List.of("default_context","window_context"))if(!required(c,k).isNull())clericalContext(obj(c.get(k)),text(fields,"presentation_target"),context.before().frame().identity().player(),subject.value());
        if(!bool(leaf,"available"))return;String receipt=nullableField(fields,"presentation_receipt");
        need(bool(c,"root_bound")&&bool(value,"window_exists")&&!c.get("default_context").isNull()&&!leaf.get("receipt_id").isNull()&&(receipt==null||receipt.equals(text(leaf,"receipt_id"))),"clerical preview lacks bound default/query context");
        if(op.equals("query")){boolean visible=bool(c,"window_visible");need(visible==bool(value,"effective_visible")&&leaf.get("post_window_visible").isBoolean()&&visible==bool(leaf,"post_window_visible")&&!leaf.get("observation_owner_epoch").isNull(),"clerical query lacks independent visibility");
            if(visible)need(text(c,"phase").equals("visible_observed")&&bool(leaf,"source_bound")&&bool(leaf,"preview_observed")&&c.get("window_context").equals(c.get("default_context")),"clerical visible context/default options differ");
            else need(Set.of("default_observed","hidden_observed").contains(text(c,"phase"))&&!bool(leaf,"source_bound")&&!bool(leaf,"preview_observed"),"hidden clerical query claims visible source");
            if(text(c,"phase").equals("hidden_observed"))need(receipt!=null&&!leaf.get("action_owner_epoch").isNull(),"hidden clerical query lacks close receipt");
            if(!leaf.get("action_owner_epoch").isNull())need(integer(leaf,"observation_owner_epoch").compareTo(integer(leaf,"action_owner_epoch"))>0,"clerical postcondition not later");
        }else need(text(c,"phase").equals(op.equals("open_clerical_preview")?"open_pending":"close_pending")&&c.get("window_visible").isNull()&&c.get("window_context").isNull()&&leaf.get("post_window_visible").isNull()&&leaf.get("observation_owner_epoch").isNull()&&!leaf.get("action_owner_epoch").isNull()&&!bool(leaf,"preview_observed"),"clerical ACK claims completed preview");
    }
    private static void clericalContext(ObjectNode c,String target,BigInteger actor,BigInteger recipient){
        keys(c,Set.of("interaction_key","definition_hash","actor_id","recipient_id","effective_actor_id","interface_kind","needs_confirmation","declared_option_count","selected_option_count","roles","options"),Set.of());
        equal(c,"interaction_key",switch(target){case "clerical_puppet"->"make_clerical_puppet_interaction";case "external_clerical_puppet"->"make_external_clerical_puppet_interaction";default->throw new IllegalArgumentException("finite clerical target required");});
        integer(c,"definition_hash",BigInteger.ZERO,U32.subtract(BigInteger.ONE));equal(c,"actor_id",actor);equal(c,"recipient_id",recipient);equal(c,"effective_actor_id",actor);range(actor,BigInteger.ONE,U32.subtract(BigInteger.TWO));range(recipient,BigInteger.ONE,U32.subtract(BigInteger.TWO));
        equal(c,"interface_kind",BigInteger.ZERO);yes(c,"needs_confirmation");equal(c,"declared_option_count",BigInteger.valueOf(6));equal(c,"selected_option_count",BigInteger.ZERO);
        JsonNode roles=required(c,"roles"),options=required(c,"options");need(roles.isArray()&&roles.size()==6&&options.isArray()&&options.size()==6,"clerical requires six roles/options");
        for(JsonNode role:roles)need(role.isNull()||role.isIntegralNumber()&&role.bigIntegerValue().signum()>=0&&role.bigIntegerValue().compareTo(U32.subtract(BigInteger.ONE))<0,"clerical native role type/domain");
        need(roles.get(0).isIntegralNumber()&&roles.get(0).bigIntegerValue().equals(actor)&&roles.get(1).isIntegralNumber()&&roles.get(1).bigIntegerValue().equals(recipient)&&roles.get(5).isIntegralNumber()&&roles.get(5).bigIntegerValue().equals(actor),"clerical native role identity changed");
        List<String> names=List.of("hook","skill_support","piety_support","dread_support","friendly_support","lunacy_support");Set<BigInteger> ids=new HashSet<>();int index=0;
        for(JsonNode n:options){ObjectNode option=obj(n);keys(option,Set.of("key","flag_id","bank_value","selected"),Set.of());equal(option,"key",names.get(index++));need(ids.add(integer(option,"flag_id",BigInteger.ZERO,U32.subtract(BigInteger.TWO))),"duplicate clerical flag");equal(option,"bank_value",BigInteger.ZERO);no(option,"selected");}
    }
}
