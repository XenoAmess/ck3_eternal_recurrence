package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;

/** The original producer validators are ported here, before constructing domain values. */
public final class GuiDecoders {
    private GuiDecoders() { }
    static Availability availability(ObjectNode r){return new Availability(bool(r,"available"),text(r,"unavailable_reason"));}
    static List<Widget> widgets(ObjectNode r){
        int n=count(r,"widget_count",0,2048);JsonNode rows=required(r,"widgets");need(rows.isArray()&&rows.size()==n,"actual widget count mismatch");
        List<Widget> result=new ArrayList<>();Set<String> paths=new HashSet<>();
        for(JsonNode node:rows){ObjectNode w=obj(node);String name=text(w,"runtime_name"),path=childPath(text(w,"child_path"),false);
            int depth=count(w,"depth",0,64);need(depth==(path.isEmpty()?0:path.split("/").length),"actual path/depth mismatch");
            need(name.getBytes(StandardCharsets.UTF_8).length<=127&&paths.add(path),"widget name/path ambiguous");
            result.add(new Widget(name,path,depth,count(w,"child_count",0,4096),integer(w,"vtable_rva",BigInteger.ZERO,U64),bool(w,"effective_visible"),bool(w,"enabled")));}
        return List.copyOf(result);
    }
    public static WindowTree windowTree(ObjectNode r,TreeKind kind){
        equal(r,"step","inspect-gui-window-tree-v1");equal(r,"scope_root_name",kind.root());yes(r,"accepted");
        boolean available=bool(r,"root_available"),truncated=bool(r,"truncated");String status=text(r,"status");
        need(status.equals(available?"available":"unavailable"),"native census availability inconsistent");List<Widget> rows=widgets(r);
        if(available){List<Widget> roots=rows.stream().filter(w->w.childPath().isEmpty()).toList();need(roots.size()==1&&roots.getFirst().runtimeName().equals(kind.root()),"actual scoped root mismatch");}
        if(kind==TreeKind.TOPBAR||kind==TreeKind.DEATH_SUCCESSION||kind==TreeKind.DEATH_DESTINY)need(!truncated,"fixed census incomplete");
        return new WindowTree(kind,available,truncated,rows);
    }
    public static UiWindow uiWindow(ObjectNode r,Context c,WindowKind kind,Subject requested,Optional<TooltipKind> tooltip,Optional<ReceiptId> receipt){
        equal(r,"schema","ck3-ingame-ui-window-v1");equal(r,"window_kind",kind.wire());equal(r,"requested_subject_id",requested.value());
        equal(r,"native_revision",c.before().frame().identity().nativeRevision());equal(r,"date_raw",c.before().frame().identity().dateRaw());
        equal(r,"played_character_id",c.before().frame().identity().player());build(r,c.build());yes(r,"paused");
        boolean available=bool(r,"available");need(available==bool(r,"accepted"),"UI acceptance/availability mismatch");
        bool(r,"dispatch_invoked");bool(r,"verification_pending");boolean exists=bool(r,"window_exists"),visible=bool(r,"effective_visible");
        boolean selected=bool(r,"subject_id_available");Optional<BigInteger> subject=nullableInteger(r,"current_subject_id");
        need(!selected||subject.isPresent(),"selected subject lacks actual full ID");subject.ifPresent(v->range(v,BigInteger.ZERO,U32.subtract(BigInteger.ONE)));
        no(r,"rng_owner_is_ui_admission_gate");integer(r,"rng_owner_thread_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        BigInteger epoch=integer(r,"pump_epoch",BigInteger.ZERO,U64);integer(r,"thread_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        if(available){yes(r,"application_owner_thread_verified","gui_owner_binding_verified");
            need(integer(r,"gui_context_address").signum()>0&&integer(r,"gui_owner_address").signum()>0&&epoch.signum()>0,"UI owner identity unavailable");
            equal(r,"status","observed");no(r,"dispatch_invoked");
            need(bool(r,"verification_pending")==tooltip.isPresent() || kind==WindowKind.TOOLTIPS || r.hasNonNull("presentation_ui"),"query pending state differs");}
        ObjectNode tree=obj(required(r,"tree"));List<Widget> rows=widgets(tree);boolean root=bool(tree,"root_available");bool(tree,"truncated");
        if(exists&&available&&kind!=WindowKind.TOOLTIPS)need(root&&!rows.isEmpty(),"existing semantic window lacks its actual tree");
        if(root){Widget first=rows.getFirst();need(first.depth()==0&&first.visible()==visible&&first.runtimeName().equals(text(r,"window_name")),"semantic tree root differs");}
        Geometry geometry=geometry(obj(required(r,"combat_geometry")));
        Optional<ArmyTooltip> actual=Optional.empty();
        if(tooltip.isPresent())actual=Optional.of(armyTooltip(obj(required(r,"army_tooltip")),tooltip.orElseThrow(),receipt));
        else need(!r.hasNonNull("army_tooltip"),"unsolicited army tooltip");
        return new UiWindow(kind,new Availability(available,available?"":text(r,"unavailable_reason")),exists,visible,bool(r,"enabled"),selected?subject:Optional.empty(),epoch,geometry,actual,rows);
    }
    static Geometry geometry(ObjectNode r){
        boolean a=bool(r,"available"),inside=bool(r,"content_inside_viewport"),fit=bool(r,"fit_required");bool(r,"stock_margin_source_verified");
        equal(r,"coordinate_space","native_gui_absolute");equal(r,"scope","visible_widget_union_and_verified_stock_background_margins");no(r,"readback_is_pixels","full_panel_pixels_proven");
        count(r,"widget_count",0,512);integer(r,"combat_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        for(String name:List.of("viewport","window_rect","content_union")){ObjectNode rect=obj(required(r,name));keys(rect,Set.of("x","y","width","height"),Set.of());for(String k:List.of("x","y","width","height"))finite(rect,k);}
        ObjectNode d=obj(required(r,"proposed_translation"));keys(d,Set.of("x","y"),Set.of());finite(d,"x");finite(d,"y");return new Geometry(a,inside,fit);
    }
    static void finite(ObjectNode r,String name){JsonNode n=required(r,name);need(n.isNumber()&&Double.isFinite(n.doubleValue())&&Math.abs(n.doubleValue())<=1048576,"invalid actual geometry number");}
    static ArmyTooltip armyTooltip(ObjectNode r,TooltipKind kind,Optional<ReceiptId> requested){
        equal(r,"schema","ck3-army-tooltip-v1");equal(r,"semantic_kind",kind.wire());no(r,"available","text_refresh_verified","rendered_verified");
        need(required(r,"gui_update_epoch").isNull(),"cache cannot prove GUI update epoch");boolean pending=bool(r,"verification_pending");
        Optional<String> receipt=nullableText(r,"receipt_id");Optional<BigInteger> epoch=nullableInteger(r,"action_owner_epoch"),later=nullableInteger(r,"later_owner_epoch");
        String status=text(r,"status");boolean source=bool(r,"source_bound"),hover=bool(r,"hover_matches_source"),leave=bool(r,"leave_observed"),stack=bool(r,"active_stack_read"),root=bool(r,"active_root_available"),cache=bool(r,"cache_bytes_observed");
        Optional<CacheText> text=Optional.empty();
        if(status.equals("unavailable")){need(!text(r,"unavailable_reason").isEmpty()&&!pending&&!source&&!hover&&!leave&&!stack&&!root&&!cache&&receipt.isEmpty()&&epoch.isEmpty()&&later.isEmpty(),"unavailable tooltip leaked evidence");
            for(String k:List.of("active_count","active_top_index","active_top_locked","source_child_path","tooltip_text_child_path","observed_cache"))need(required(r,k).isNull(),"unavailable tooltip leaked value");}
        else{need(pending&&receipt.isPresent()&&epoch.isPresent()&&later.isPresent()&&source,"tooltip lacks exact later source evidence");
            new ReceiptId(receipt.orElseThrow());range(epoch.orElseThrow(),BigInteger.ONE,U64);range(later.orElseThrow(),epoch.orElseThrow().add(BigInteger.ONE),U64);
            requested.ifPresent(v->need(v.value().equals(receipt.orElseThrow()),"tooltip receipt drift"));
            if(cache){need(status.equals("cache_observed_verification_pending")&&hover&&stack&&root&&!leave,"cache source/stack unavailable");
                ObjectNode bytes=obj(required(r,"observed_cache"));keys(bytes,Set.of("text","utf8_bytes","sha256"),Set.of());String s=text(bytes,"text");byte[] data=s.getBytes(StandardCharsets.UTF_8);
                need(count(bytes,"utf8_bytes",0,RawLimit.VALUE)==data.length&&text(bytes,"sha256").equalsIgnoreCase(sha256(data)),"tooltip complete UTF8 digest differs");text=Optional.of(new CacheText(s,data.length,sha256(data)));}
            else need(required(r,"observed_cache").isNull()&&required(r,"tooltip_text_child_path").isNull(),"unobserved cache must be null");
            if(leave)need(status.equals("leave_observed_verification_pending")&&!hover&&stack,"leave lacks independent stack read");
        }
        return new ArmyTooltip(kind,receipt.map(ReceiptId::new),epoch.orElse(null),later.orElse(null),source,hover,leave,pending,text);
    }
    private static final class RawLimit{static final int VALUE=64*1024*1024;}
    public static DecisionItem decisionItem(ObjectNode r,Context c,DecisionKey key){
        equal(r,"schema","ck3-ingame-decision-item-v1");equal(r,"step","query-ingame-decision-item-v1");yes(r,"read_only");build(r,c.build());no(r,"row_widget_datacontext_verified","action_qualified");
        Availability a=availability(r);
        if(r.has("selected_terms")){
            var terms=GuiSelectedDecisionTerms.decode(obj(r.get("selected_terms")),c,key);
            if(terms instanceof GuiSelectedDecisionTerms.Available){
                need(a.available(),"available selected terms require available outer model");
                yes(r,"detail_definition_matches_target","detail_tree_complete","detail_root_visible","detail_actor_binding_verified");
                equal(r,"detail_actor_reference_key",c.before().frame().identity().player());
            }
        }
        if(!a.available())return new DecisionItem(key,a,false,false,false,false,null,0,0);
        binding(r,c);equal(r,"decision_key",key.value());yes(r,"owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","decisions_tree_complete","decisions_root_visible","row_owner_verified");
        need(count(r,"matching_row_count",0,2048)==1,"decision row not unique");integer(r,"row_context_reference_key",BigInteger.ZERO,U32.subtract(BigInteger.ONE));bool(r,"row_scope_reference_available");
        boolean defined=bool(r,"detail_definition_available"),matches=bool(r,"detail_definition_matches_target"),visible=bool(r,"detail_root_visible"),complete=bool(r,"detail_tree_complete");
        String detail=text(r,"detail_decision_key");if(defined)new DecisionKey(detail);else need(detail.isEmpty(),"absent detail leaked key");
        need(matches==(defined&&detail.equals(key.value()))&&(!visible||complete),"decision detail identity/complete mismatch");
        boolean actorBound=bool(r,"detail_actor_binding_verified");BigInteger actor=integer(r,"detail_actor_reference_key");
        return new DecisionItem(key,a,visible,complete,matches,actorBound,actor,count(r,"group_count",0,64),count(r,"row_count",0,2048));
    }
    public static Policies policies(ObjectNode r,Context c){
        equal(r,"schema","ck3-aub-policy-options-v1");equal(r,"step","query-aub-policy-options-v1");yes(r,"read_only");build(r,Build.CROZIER3);binding(r,c);
        no(r,"tooltip_available","enabled_available","rendered_down_available","production_confirmed");equal(r,"unavailable_reason","");
        for(String name:List.of("before_actual_model","after_actual_model"))need(decisionItem(obj(required(r,name)),c,new DecisionKey("enable_auto_build")).selectedFor(c.before().frame().identity().player()),"AUB actual selected detail/actor unqualified");
        ObjectNode p=obj(required(r,"policy"));yes(p,"ready");equal(p,"decision_key","enable_auto_build");equal(p,"played_character_id",c.before().frame().identity().player());equal(p,"unavailable_reason","");
        String selectedKey=text(p,"selected_key");Optional<Policy> selected=selectedKey.isEmpty()?Optional.empty():Optional.of(Policy.parse(selectedKey));int index=count(p,"selected_index",-1,5);need((index<0)==selected.isEmpty(),"AUB selection presence/index mismatch");JsonNode entries=required(p,"entries");need(entries.isArray()&&entries.size()==6,"actual six AUB entries required");
        List<PolicyEntry> rows=new ArrayList<>();Set<Policy> unique=new HashSet<>();int i=0;
        for(JsonNode n:entries){ObjectNode e=obj(n);Policy k=Policy.parse(text(e,"value_key"));boolean s=bool(e,"selected");need(unique.add(k)&&s==(i==index)&&s==selected.filter(k::equals).isPresent(),"AUB semantic selection ambiguous");rows.add(new PolicyEntry(k,s));i++;}
        return new Policies(selected,rows);
    }
    public static AubState aubState(ObjectNode r,Context c){
        equal(r,"schema","ck3-aub-business-state-v1");equal(r,"step","query-aub-business-state-v1");yes(r,"read_only");build(r,Build.CROZIER3);binding(r,c);
        yes(r,"available","owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","stable_two_pass_verified","detail_census_verified","detail_tree_complete");
        no(r,"rendered_text_available","rendered_down_available","product_acceptance_proven");equal(r,"unavailable_reason","");boolean root=bool(r,"detail_root_available"),visible=bool(r,"detail_effectively_visible");need(root||!visible,"absent AUB detail visible");
        String[] names={"enable_auto_build","aub_funding_treasury_only","aub_funding_personal_only","aub_pause_when_over_domain_limit"};JsonNode flags=required(r,"flags");need(flags.isArray()&&flags.size()==4,"four AUB flags required");List<Flag> values=new ArrayList<>();
        for(int i=0;i<4;i++){ObjectNode f=obj(flags.get(i));keys(f,Set.of("key","available","atom_registered","present","unavailable_reason"),Set.of());equal(f,"key",names[i]);yes(f,"available");equal(f,"unavailable_reason","");boolean atom=bool(f,"atom_registered"),present=bool(f,"present");need(atom||!present,"unregistered atom cannot carry flag");values.add(new Flag(names[i],atom,present));}
        return new AubState(root,visible,values);
    }
    public static WhiteBusiness whiteBusiness(ObjectNode r,Context c){
        keys(r,Set.of("schema","step","available","all_eight_numeric_integers","fields","fixed_scale","status","unavailable_reason",
                "owner_thread_verified","frame_verified","source_abi_pins_verified","player_scope_verified","stable_two_pass_values",
                "rendered_text_available","selected_down_available","scriptvalue_price_available","game_pid","native_revision","connection_generation",
                "played_character_id","date_raw","application_thread_id","application_pump_epoch","application_tls_context","variable_context","character_address"),Set.of("backend_id"));
        if(r.has("backend_id"))equal(r,"backend_id","native-headless");
        for(String proof:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","player_scope_verified","stable_two_pass_values"))bool(r,proof);
        whiteNumbers(r);integer(r,"application_thread_id",BigInteger.ZERO,U32.subtract(BigInteger.ONE));
        for(String n:List.of("application_pump_epoch","application_tls_context","variable_context","character_address"))integer(r,n,BigInteger.ZERO,U64);
        equal(r,"schema","ck3-native-white-player-business-variables-v1");equal(r,"step","query-white-player-business-variables-v1");bindingCore(r,c);
        no(r,"rendered_text_available","selected_down_available","scriptvalue_price_available");need(count(r,"fixed_scale",100000,100000)==100000,"Q100000 scale");
        Availability a=availability(r);ObjectNode f=obj(required(r,"fields"));Set<String> names=new HashSet<>();for(Variable k:Variable.values())names.add(k.wire());keys(f,names,Set.of());
        List<VariableValue> values=new ArrayList<>();boolean all=true;
        for(Variable key:Variable.values()){ObjectNode v=obj(required(f,key.wire()));keys(v,Set.of("present","actual_kind","actual_payload","fixed_raw","integer_value"),Set.of());
            if(!bool(v,"present")){for(String n:List.of("actual_kind","actual_payload","fixed_raw","integer_value"))need(required(v,n).isNull(),"absent variable leaked payload");values.add(new MissingVariable(key));all=false;continue;}
            int kind=count(v,"actual_kind",0,65535);BigInteger payload=integer(v,"actual_payload",BigInteger.ONE.shiftLeft(63).negate(),BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE));
            if(kind!=1){need(required(v,"fixed_raw").isNull()&&required(v,"integer_value").isNull(),"nonnumeric variable leaked number");values.add(new NonNumericVariable(key,kind,payload));all=false;}
            else{equal(v,"fixed_raw",payload);Optional<BigInteger> number=nullableInteger(v,"integer_value");BigInteger[] div=payload.divideAndRemainder(BigInteger.valueOf(100000));
                need(div[1].signum()==0?number.isPresent()&&number.orElseThrow().equals(div[0]):number.isEmpty(),"Q100000 integer projection differs");values.add(new NumericVariable(key,payload,number));all&=number.isPresent();}}
        boolean qualified=bool(r,"all_eight_numeric_integers");if(a.available()){binding(r,c);yes(r,"owner_thread_verified","frame_verified","source_abi_pins_verified","player_scope_verified","stable_two_pass_values");
            for(String n:List.of("application_thread_id","application_pump_epoch","application_tls_context","variable_context","character_address"))need(integer(r,n).signum()>0,"actual variable context unavailable");need(qualified==all,"all-eight qualification differs");equal(r,"status","observed_business_variables");}
        else{need(!qualified&&values.stream().allMatch(v->v instanceof MissingVariable),"unavailable business leaked variable");equal(r,"status","unavailable");whiteUnavailableBinding(r,c);}
        return new WhiteBusiness(a,values,qualified);
    }
    static void bindingCore(ObjectNode r,Context c){equal(r,"native_revision",c.before().frame().identity().nativeRevision());equal(r,"connection_generation",c.connectionGeneration());equal(r,"game_pid",BigInteger.valueOf(c.before().game().pid()));}
    public static WhiteText whiteText(ObjectNode r,Context c){
        keys(r,Set.of("schema","step","read_only","available","rendered_text_available","selected_down_available","owner_thread_verified",
                "source_abi_pins_verified","frame_verified","gui_owner_binding_verified","tree_complete","inner_modal_visible","stable_two_pass_text",
                "game_pid","native_revision","connection_generation","played_character_id","date_raw","widget_count","fields","text_source","unavailable_reason"),Set.of("backend_id"));
        if(r.has("backend_id"))equal(r,"backend_id","native-headless");
        whiteNumbers(r);for(String proof:List.of("owner_thread_verified","source_abi_pins_verified","frame_verified","gui_owner_binding_verified","tree_complete","inner_modal_visible","stable_two_pass_text"))bool(r,proof);
        equal(r,"schema","ck3-native-white-rendered-text-v1");equal(r,"step","query-white-rendered-text-v1");yes(r,"read_only");bindingCore(r,c);no(r,"selected_down_available");
        Availability a=availability(r);need(bool(r,"rendered_text_available")==a.available(),"text availability differs");equal(r,"text_source","actual_CPdxGuiTextbox_GetText_390");count(r,"widget_count",0,2048);
        ObjectNode f=obj(required(r,"fields"));Set<String> names=new HashSet<>();for(TextName k:TextName.values())names.add(k.wire());keys(f,names,Set.of());List<TextValue> values=new ArrayList<>();Set<String> paths=new HashSet<>();
        if(a.available()){need(integer(r,"widget_count").signum()>0,"available White text requires actual widgets");binding(r,c);yes(r,"owner_thread_verified","source_abi_pins_verified","frame_verified","gui_owner_binding_verified","tree_complete","inner_modal_visible","stable_two_pass_text");
            for(TextName k:TextName.values()){ObjectNode t=obj(required(f,k.wire()));keys(t,Set.of("child_path","text_utf8","effective_visible","enabled"),Set.of());String path=childPath(text(t,"child_path"),true),s=text(t,"text_utf8");
                need(paths.add(path)&&s.getBytes(StandardCharsets.UTF_8).length<=2048,"fixed text path/size invalid");yes(t,"effective_visible");values.add(new TextValue(k,path,s,bool(t,"enabled")));}}
        else{for(TextName k:TextName.values())need(required(f,k.wire()).isNull(),"unavailable text leaked value");whiteUnavailableBinding(r,c);}
        return new WhiteText(a,values);
    }
    private static void whiteNumbers(ObjectNode r){
        integer(r,"game_pid",BigInteger.ONE,U32.subtract(BigInteger.ONE));integer(r,"native_revision",BigInteger.ONE,U64);integer(r,"connection_generation",BigInteger.ONE,U64);
        integer(r,"played_character_id",BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MAX_VALUE));
        integer(r,"date_raw",BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE));
    }
    private static void whiteUnavailableBinding(ObjectNode r,Context c){
        BigInteger actor=integer(r,"played_character_id"),date=integer(r,"date_raw");
        need(actor.equals(BigInteger.valueOf(-1))||actor.equals(c.before().frame().identity().player()),"unavailable White crossed actor");
        need(date.signum()==0||date.equals(c.before().frame().identity().dateRaw()),"unavailable White crossed date");
    }
}
