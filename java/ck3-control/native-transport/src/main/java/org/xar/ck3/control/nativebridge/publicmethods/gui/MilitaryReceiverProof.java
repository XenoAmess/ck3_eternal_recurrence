package org.xar.ck3.control.nativebridge.publicmethods.gui;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiDecoders;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;

/** Exact-.4 full census validation. Static definition candidates never claim a selected native receiver or a permit. */
public final class MilitaryReceiverProof {
    private static final int IMAGE=0x61c5000,THUNK=0x3aa30e0,BRIDGE=0x3a9f960,REFILL=0x1303d40;
    private static final String CANDIDATE="native_gui_type635_definition_candidates_12004";
    private static final String LOCAL="local_definition_entry_only",PREFIX="definition_chain_prefix_depth8";
    private static final String TAIL="definition_frontier_continuation_depth8_12",SWITCH="static_direct_owner_switch_12004";
    private static final Set<String> CANDIDATE_FIELDS=Set.of("source","status","unavailable_reason","receiver_type_id",
            "current_variable_table_observed","native_receiver_selected","receiver_variable_index","declared_type_id","stable_double_read","entries");
    private static final Set<String> ENTRY_FIELDS=Set.of("ancestor_depth","entry_type_48","entry_mode_40","entry_flag_4c",
            "direct_value_present","provider_present","provider_vtable_rva","provider_slot2_rva","direct_owner_full_id","direct_owner_identity_verified");
    private static final Set<String> SWITCH_FIELDS=Set.of("source","scope","status","unavailable_reason","current_variable_table_observed",
            "native_receiver_selected","provider_invoked","ancestor_depth","owner_full_id","military_component_present","raw_byte_4a9","enabled","value_basis","stable_double_read");
    private enum Profile { BASE,INDIRECT,EXPRESSION,RECEIVER }
    private MilitaryReceiverProof(){ }

    /** Validates the actual full result token, retaining each original callback and candidate branch after scalar projection. */
    public static RawJson normalizeTree(RawJson actualResult,Binding binding) {
        Objects.requireNonNull(binding);ObjectNode original=fullNode(Objects.requireNonNull(actualResult));
        var basic=GuiDecoders.windowTree(original,GuiModels.TreeKind.MILITARY);
        require(!basic.truncated(),"military callback census is incomplete");
        require(basic.rootAvailable()||basic.widgets().isEmpty(),"missing military window cannot contain callback targets");
        Profile profile=source(obj(original.get("callback_binding_source_12004")));
        ArrayNode input=array(original,"widgets",2048);require(input.size()==basic.widgets().size(),"full census projection lost a native row");
        ObjectNode result=StrictJson.object().put("schema","ck3-native-gui-window-tree-inspection-v1").put("schema_version",1)
                .put("step","inspect-gui-window-tree-v1").put("accepted",true).put("status",basic.rootAvailable()?"available":"unavailable")
                .put("window_kind","military").put("scope_root_name","military_view").put("root_available",basic.rootAvailable())
                .put("truncated",false).put("widget_count",input.size());
        ArrayNode output=result.putArray("widgets");
        for(int index=0;index<input.size();index++){
            var projected=basic.widgets().get(index);require(projected.vtableRva().compareTo(BigInteger.ONE)>=0
                    &&projected.vtableRva().compareTo(BigInteger.valueOf(IMAGE-112))<=0,"military widget vtable is outside the exact image");
            ObjectNode nativeRow=obj(input.get(index));ObjectNode callbacks=obj(nativeRow.get("standard_click_binding_12004"));
            callback(callbacks,profile);
            ObjectNode clean=StrictJson.object().put("runtime_name",projected.runtimeName()).put("child_path",projected.childPath())
                    .put("depth",projected.depth()).put("child_count",projected.childCount()).put("vtable_rva",projected.vtableRva())
                    .put("effective_visible",projected.visible()).put("enabled",projected.enabled());
            clean.set("standard_click_binding_12004",callbacks.deepCopy());output.add(clean);
        }
        result.set("callback_binding_source_12004",expectedSource(profile));
        if(profile==Profile.RECEIVER){
            ObjectNode nativeFrame=obj(original.get("refill_receiver_frame_12004"));frame(nativeFrame).requireBinding(binding);
            result.set("refill_receiver_frame_12004",nativeFrame.deepCopy());
        }else require(!original.has("refill_receiver_frame_12004"),"receiver frame lacks exact receiver source pins");
        JsonNode backend=original.get("backend_id");require(backend==null||backend.isNull()||backend.isTextual(),"backend label must remain textual or null");
        if(backend==null)result.putNull("backend_id");else result.set("backend_id",backend.deepCopy());
        for(String field:List.of("read_only"))result.put(field,true);
        for(String field:List.of("uses_ocr","uses_keyboard","uses_mouse","rendered_text_available","selected_state_available",
                "tooltip_state_available","business_model_available","callback_method_name_available","click_action_available"))result.put(field,false);
        return fullRaw(result);
    }

    /** Revalidates normalized DATA and joins the unique visible stock callback to its original static owner rows. */
    public static BeforeObservation observeFixedReinforcement(RawJson normalized,Binding binding) {
        ObjectNode tree=fullNode(normalizeTree(normalized,binding));require(bool(tree,"root_available")&&!bool(tree,"truncated")&&bool(tree,"read_only"),
                "reinforcement needs a complete actual military census");
        CensusFrame actualFrame=frame(obj(tree.get("refill_receiver_frame_12004")));actualFrame.requireBinding(binding);
        Map<String,ObjectNode> byPath=new HashMap<>();ArrayNode rows=array(tree,"widgets",2048);
        for(JsonNode value:rows){ObjectNode row=obj(value);require(byPath.put(string(row,"child_path"),row)==null,"duplicate actual military child path");}
        ObjectNode root=byPath.get("");require(root!=null&&string(root,"runtime_name").equals("military_view")&&bool(root,"effective_visible"),"actual military root is not visible");
        List<BeforeObservation> matches=new ArrayList<>();
        for(JsonNode value:rows){ObjectNode row=obj(value);if(!bool(row,"effective_visible")||!bool(row,"enabled"))continue;
            for(JsonNode target:array(obj(row.get("standard_click_binding_12004")),"callbacks",256)){
                ObjectNode cb=obj(target);JsonNode indirect=cb.get("indirect_target_3aa30e0");if(indirect==null)continue;
                ObjectNode payload=obj(indirect);JsonNode expressionNode=payload.get("expression_3a9f960");if(expressionNode==null)continue;
                ObjectNode expression=obj(expressionNode);if(!number(expression,"final_target_38_rva").equals(BigInteger.valueOf(REFILL)))continue;
                String path=string(row,"child_path");String tab,tabName,footer;
                if(path.equals("0/0/0/2/3/0/0/0")){tab="0/0/0/2";tabName="tab_your_armies";footer="0/0/0/2/3";}
                else if(path.equals("0/0/0/3/5/0/0/0")){tab="0/0/0/3";tabName="imperial_armies_ra_uses_this";footer="0/0/0/3/5";}
                else throw new IllegalArgumentException("reinforcement final target is outside the fixed source path");
                require(string(row,"runtime_name").isEmpty()&&number(cb,"callback_slot2_rva").intValueExact()==THUNK
                        &&number(payload,"native_target_8_rva").intValueExact()==BRIDGE&&bool(payload,"receiver_f0_present")
                        &&number(expression,"chain_count_24_raw").signum()==0&&number(expression,"final_kind_34_raw").intValueExact()==3
                        &&number(expression,"receiver_type_id_48").equals(BigInteger.valueOf(635))&&number(expression,"receiver_flag_4c_raw").signum()==0
                        &&bool(expression,"final_user_data_40_present"),"reinforcement final target is outside its exact callback source profile");
                require(byPath.containsKey(tab)&&string(byPath.get(tab),"runtime_name").equals(tabName)
                        &&byPath.containsKey(footer)&&string(byPath.get(footer),"runtime_name").equals("footer"),"reinforcement source ancestors differ from the stock profile");
                ObjectNode candidate=obj(expression.get("receiver_entry_candidates_12004")),tail=obj(candidate.get(TAIL));
                ObjectNode sourceSwitch=obj(tail.get(SWITCH));staticSwitch(sourceSwitch,array(tail,"rows",4));
                SwitchObservation observed=switchObservation(sourceSwitch,binding.actor());
                ObjectNode publicFrame=StrictJson.object().put("snapshot_id",binding.context().before().frame().snapshotId())
                        .put("revision",binding.publicRevision()).put("native_revision",binding.nativeRevision())
                        .put("episode_run_id",binding.context().before().frame().episodeRunId());
                matches.add(new BeforeObservation(path,observed,actualFrame,raw(publicFrame)));
            }
        }
        require(matches.size()==1,"reinforcement requires exactly one visible enabled stock source control");return matches.getFirst();
    }

    private static ObjectNode expectedSource(Profile profile){
        ObjectNode source=StrictJson.object().put("executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("button_base_slot13_rva",0x3aa0d20).put("group_dispatch_rva",0x3a9fa30).put("input_modifier",0);
        if(profile.ordinal()>=Profile.INDIRECT.ordinal())source.put("indirect_target_thunk_rva",THUNK)
                .put("indirect_target_thunk_bytes_sha256","7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563");
        if(profile.ordinal()>=Profile.EXPRESSION.ordinal())source.put("expression_target_bridge_rva",BRIDGE).put("expression_builder_rva",0x3ac38c0)
                .put("expression_eval_rva",0x3e4c090).put("expression_layout_bytes_sha256","7412efd136e722993b71a8810f5d585347cde53104ba0a107551eb324ff18963");
        if(profile==Profile.RECEIVER)source.put("receiver_definition_parent_rva",0x3ac3ef0).put("receiver_typed_entry_rva",0x3ac1c00)
                .put("receiver_definition_parent_bytes_sha256","476ac96745e7088e7dd2073cfc00e023d8a1102a8d154a51434886d6d5b5a2a7")
                .put("receiver_typed_entry_bytes_sha256","8efccb736158d04c2847d98e8aa6d3400ae8591467d2628726a1f1c396e43cfc");
        return source;
    }
    private static Profile source(ObjectNode source){
        for(Profile profile:Profile.values()){ObjectNode expected=expectedSource(profile);if(!names(source).equals(names(expected)))continue;
            for(String field:names(expected)){JsonNode want=expected.get(field),actual=source.get(field);
                require(want.isIntegralNumber()?actual.isIntegralNumber()&&actual.bigIntegerValue().equals(want.bigIntegerValue()):actual.isTextual()&&actual.textValue().equals(want.textValue()),
                        "callback has no exact .4 source identity: "+field);}
            return profile;
        }
        throw new IllegalArgumentException("callback source profile fields differ from exact .4 producer");
    }
    private static void callback(ObjectNode binding,Profile profile){
        keys(binding,Set.of("button_base_slot13","group","callbacks"),Set.of());boolean button=bool(binding,"button_base_slot13");
        String group=string(binding,"group");ArrayNode callbacks=array(binding,"callbacks",256);
        require(button?(group.equals("primary")||group.equals("fallback"))&&(!group.equals("primary")||!callbacks.isEmpty()):group.equals("not_button_base")&&callbacks.isEmpty(),
                "standard click group differs from observed source selection");
        for(int index=0;index<callbacks.size();index++){
            ObjectNode target=obj(callbacks.get(index));boolean indirect=profile!=Profile.BASE&&number(target,"callback_slot2_rva").equals(BigInteger.valueOf(THUNK));
            keys(target,Set.of("index","callback_vtable_rva","callback_slot2_rva"),indirect?Set.of("indirect_target_3aa30e0"):Set.of());
            integer(target,"index",index,index);integer(target,"callback_vtable_rva",1,IMAGE-24);integer(target,"callback_slot2_rva",1,IMAGE-1);
            if(indirect){require(target.has("indirect_target_3aa30e0"),"original indirect target is missing");ObjectNode payload=obj(target.get("indirect_target_3aa30e0"));
                boolean expression=profile.ordinal()>=Profile.EXPRESSION.ordinal()&&number(payload,"native_target_8_rva").equals(BigInteger.valueOf(BRIDGE));
                keys(payload,Set.of("native_target_8_rva","receiver_f0_present"),expression?Set.of("expression_3a9f960"):Set.of());
                integer(payload,"native_target_8_rva",1,IMAGE-1);bool(payload,"receiver_f0_present");
                if(expression){require(payload.has("expression_3a9f960"),"original expression target is missing");expression(obj(payload.get("expression_3a9f960")),profile==Profile.RECEIVER);}
            }
        }
    }
    private static void expression(ObjectNode expression,boolean receiverSource){
        boolean candidates=expression.has("receiver_entry_candidates_12004");
        require(!candidates||receiverSource,"receiver candidates lack exact new source pins");
        keys(expression,Set.of("chain_count_24_raw","final_type_id_30","final_kind_34_raw","final_target_38_rva","final_user_data_40_present","receiver_type_id_48","receiver_flag_4c_raw","chain_calls"),
                candidates?Set.of("receiver_entry_candidates_12004"):Set.of());
        for(String field:List.of("final_type_id_30","final_kind_34_raw","receiver_type_id_48"))integer(expression,field,BigInteger.ZERO,U32);
        integer(expression,"receiver_flag_4c_raw",0,255);bool(expression,"final_user_data_40_present");
        int count=integer(expression,"chain_count_24_raw",0,16).intValueExact();ArrayNode chain=array(expression,"chain_calls",16);require(chain.size()==count,"expression receiver chain is incomplete");
        BigInteger kind=number(expression,"final_kind_34_raw");boolean callable=kind.equals(BigInteger.valueOf(3))||kind.equals(BigInteger.valueOf(4));
        integer(expression,"final_target_38_rva",callable?1:0,callable?IMAGE-1:0);
        for(int index=0;index<chain.size();index++){ObjectNode row=obj(chain.get(index));keys(row,Set.of("index","type_id_0","kind_4_raw","native_target_8_rva","user_data_10_present"),Set.of());
            integer(row,"index",index,index);integer(row,"type_id_0",BigInteger.ZERO,U32);integer(row,"kind_4_raw",BigInteger.ZERO,U32);
            integer(row,"native_target_8_rva",1,IMAGE-1);bool(row,"user_data_10_present");}
        if(candidates){require(number(expression,"receiver_type_id_48").equals(BigInteger.valueOf(635))&&number(expression,"receiver_flag_4c_raw").signum()==0
                &&count==0&&kind.equals(BigInteger.valueOf(3))&&number(expression,"final_target_38_rva").intValueExact()==REFILL,"receiver candidates are outside the fixed refill callback");
            candidates(obj(expression.get("receiver_entry_candidates_12004")));}
    }

    private static void candidates(ObjectNode raw){
        keys(raw,CANDIDATE_FIELDS,Set.of("failure_diagnostic",LOCAL,PREFIX,TAIL));eq(raw,"source",CANDIDATE);integer(raw,"receiver_type_id",635,635);
        no(raw,"current_variable_table_observed","native_receiver_selected");bool(raw,"stable_double_read");ArrayNode entries=array(raw,"entries",8);
        ObjectNode local=raw.has(LOCAL)?obj(raw.get(LOCAL)):null,prefix=raw.has(PREFIX)?obj(raw.get(PREFIX)):null,tail=raw.has(TAIL)?obj(raw.get(TAIL)):null;
        if(local!=null){local(local);if(available(raw)&&available(local))sameDeclaration(raw,local);}
        if(prefix!=null){prefix(prefix);eq(raw,"status","unavailable");eq(raw,"unavailable_reason","candidate_parent_depth_exhausted");
            ObjectNode failure=obj(raw.get("failure_diagnostic"));integer(failure,"capture_pass",1,1);integer(failure,"ancestor_depth",8,8);eq(failure,"kind","parent_depth_exhausted");
            if(available(prefix)){require(local!=null&&available(local),"definition prefix lacks independent stable local view");sameDeclaration(prefix,local);
                ObjectNode first=obj(array(prefix,"rows",8).get(0));for(String field:List.of("entries","raw_definition_entry_count","definition_present"))same(first,local,field);}}
        if(tail!=null){require(prefix!=null,"frontier continuation lacks original depth8 prefix");continuation(tail);
            if(available(tail)){require(available(prefix),"frontier continuation crossed unavailable prefix");sameDeclaration(tail,prefix);}}
        if(raw.has("failure_diagnostic")){require(!available(raw),"failure diagnostic cannot qualify available candidates");failure(obj(raw.get("failure_diagnostic")),8);}
        if(!available(raw)){unavailable(raw,List.of("receiver_variable_index","declared_type_id"),entries);return;}
        declaration(raw);int previous=-1;
        for(JsonNode value:entries){ObjectNode entry=obj(value);entry(entry,previous+1,7);previous=number(entry,"ancestor_depth").intValueExact();}
        if(local!=null&&available(local)){ArrayNode zero=StrictJson.object().putArray("entries");for(JsonNode value:entries)if(number(obj(value),"ancestor_depth").signum()==0)zero.add(value);
            require(zero.equals(local.get("entries")),"independent local entries differ from full depth0 candidates");}
    }
    private static void entry(ObjectNode entry,int minimumDepth,int maximumDepth){
        keys(entry,ENTRY_FIELDS,Set.of());integer(entry,"ancestor_depth",minimumDepth,maximumDepth);integer(entry,"entry_type_48",635,635);
        int mode=integer(entry,"entry_mode_40",-128,127).intValueExact();integer(entry,"entry_flag_4c",0,255);
        boolean directPresent=bool(entry,"direct_value_present"),provider=bool(entry,"provider_present"),verified=bool(entry,"direct_owner_identity_verified");
        nullableInteger(entry,"provider_vtable_rva",1,IMAGE-24);nullableInteger(entry,"provider_slot2_rva",1,IMAGE-1);
        if(mode<2||!provider)require(isNull(entry,"provider_vtable_rva")&&isNull(entry,"provider_slot2_rva"),"provider RVA on a branch that does not dispatch");
        require(isNull(entry,"provider_slot2_rva")||!isNull(entry,"provider_vtable_rva"),"provider target lacks actual image vtable");
        nullableInteger(entry,"direct_owner_full_id",Integer.MIN_VALUE,Integer.MAX_VALUE);boolean direct=mode==1&&directPresent;
        require(direct||(isNull(entry,"direct_owner_full_id")&&!verified),"direct owner on a non-direct source branch");
        require(!verified||!isNull(entry,"direct_owner_full_id")&&!number(entry,"direct_owner_full_id").equals(BigInteger.valueOf(-1)),"verified direct owner has no full identity");
    }
    private static void local(ObjectNode raw){
        keys(raw,Set.of("source","scope","status","unavailable_reason","receiver_type_id","ancestor_depth","current_variable_table_observed","native_receiver_selected",
                "receiver_variable_index","declared_type_id","raw_definition_entry_count","local_definition_active_raw","definition_present","local_entry_present","stable_double_read","entries"),Set.of("failure_diagnostic"));
        eq(raw,"source","native_gui_type635_local_definition_entry_only_12004");eq(raw,"scope","local_definition_entry_only");integer(raw,"receiver_type_id",635,635);integer(raw,"ancestor_depth",0,0);
        no(raw,"current_variable_table_observed","native_receiver_selected");bool(raw,"stable_double_read");ArrayNode entries=array(raw,"entries",1);
        if(raw.has("failure_diagnostic")){require(!available(raw),"local failure cannot qualify available prefix");failure(obj(raw.get("failure_diagnostic")),8);}
        if(!available(raw)){unavailable(raw,List.of("receiver_variable_index","declared_type_id","raw_definition_entry_count","local_definition_active_raw","definition_present","local_entry_present"),entries);return;}
        declaration(raw);int count=integer(raw,"raw_definition_entry_count",0,256).intValueExact();integer(raw,"local_definition_active_raw",1,255);
        require(bool(raw,"definition_present")&&bool(raw,"local_entry_present")==!entries.isEmpty()&&(entries.isEmpty()||count>0),"local declaration/lookup is incomplete");
        for(JsonNode value:entries)entry(obj(value),0,0);
    }
    private static void prefix(ObjectNode raw){
        keys(raw,Set.of("source","scope","status","unavailable_reason","receiver_type_id","depth_limit","walk_complete","current_variable_table_observed","native_receiver_selected",
                "receiver_variable_index","declared_type_id","frontier_depth","frontier_context_present","stable_double_read","rows"),Set.of());
        eq(raw,"source","native_gui_type635_definition_chain_prefix_depth8_12004");eq(raw,"scope","visited_definition_prefix_depth8");integer(raw,"receiver_type_id",635,635);integer(raw,"depth_limit",8,8);
        no(raw,"walk_complete","current_variable_table_observed","native_receiver_selected");bool(raw,"stable_double_read");ArrayNode rows=array(raw,"rows",8);
        if(!available(raw)){unavailable(raw,List.of("receiver_variable_index","declared_type_id","frontier_depth","frontier_context_present"),rows);return;}
        declaration(raw);integer(raw,"frontier_depth",8,8);require(bool(raw,"frontier_context_present")&&rows.size()==8,"definition prefix boundary is incomplete");
        for(int depth=0;depth<rows.size();depth++){ObjectNode row=obj(rows.get(depth));
            keys(row,Set.of("ancestor_depth","definition_present","raw_definition_entry_count","entries","parent_edge","parent_present"),Set.of());integer(row,"ancestor_depth",depth,depth);
            boolean definition=bool(row,"definition_present");require(bool(row,"parent_present"),"prefix parent is absent");String edge=string(row,"parent_edge");
            require(edge.equals("definition_108")||edge.equals("context_e8"),"prefix edge differs from native source");ArrayNode entries=array(row,"entries",1);
            definition(row,definition,entries);if(!definition)require(edge.equals("context_e8")&&depth>0,"null prefix definition cannot supply definition edge/local root");
            for(JsonNode value:entries){ObjectNode item=obj(value);entry(item,depth,depth);int flag=number(item,"entry_flag_4c").intValueExact(),mode=number(item,"entry_mode_40").intValueExact();
                require(depth==0?flag==0:flag==0||mode<0||mode>1,"definition prefix continues beyond native static stop");
                if(depth>0&&flag==0)filtered(item);}
        }
    }
    private static void continuation(ObjectNode raw){
        keys(raw,Set.of("source","scope","status","unavailable_reason","receiver_type_id","start_depth","depth_limit","current_variable_table_observed","native_receiver_selected","provider_invoked",
                "receiver_variable_index","declared_type_id","stop_depth","stop_reason","next_context_present","stable_double_read","rows"),Set.of("failure_diagnostic",SWITCH));
        eq(raw,"source","native_gui_type635_frontier_continuation_depth8_12_12004");eq(raw,"scope","definition_frontier_depth8_through11");integer(raw,"receiver_type_id",635,635);integer(raw,"start_depth",8,8);integer(raw,"depth_limit",12,12);
        no(raw,"current_variable_table_observed","native_receiver_selected","provider_invoked");bool(raw,"stable_double_read");ArrayNode rows=array(raw,"rows",4);
        if(raw.has(SWITCH))require(available(raw),"static switch requires independently available continuation");
        if(raw.has("failure_diagnostic")){require(!available(raw),"available continuation contains a failed capture");failure(obj(raw.get("failure_diagnostic")),12);}
        if(!available(raw)){unavailable(raw,List.of("receiver_variable_index","declared_type_id","stop_depth","stop_reason","next_context_present"),rows);return;}
        declaration(raw);int stop=integer(raw,"stop_depth",8,12).intValueExact();String reason=string(raw,"stop_reason");
        require(Set.of("null_end","cycle","static_direct_terminal","depth_limit").contains(reason),"unknown native continuation stop");nullableBool(raw,"next_context_present");
        for(int ordinal=0;ordinal<rows.size();ordinal++){int depth=8+ordinal;ObjectNode row=obj(rows.get(ordinal));
            keys(row,Set.of("ancestor_depth","definition_present","raw_definition_entry_count","first_match_entry_index","entries","parent_edge","parent_present"),Set.of());integer(row,"ancestor_depth",depth,depth);
            boolean definition=bool(row,"definition_present");ArrayNode entries=array(row,"entries",1);definition(row,definition,entries);
            String edge=string(row,"parent_edge");require(Set.of("definition_108","context_e8","not_read_native_static_stop").contains(edge),"unknown continuation parent edge");nullableBool(row,"parent_present");
            if(!definition)require(edge.equals("context_e8"),"null continuation definition supplies a definition edge");
            if(!entries.isEmpty())integer(row,"first_match_entry_index",0,number(row,"raw_definition_entry_count").intValueExact()-1);
            else require(isNull(row,"first_match_entry_index"),"no-match row claims an entry index");
            if(edge.equals("definition_108"))require(Boolean.TRUE.equals(nullableBool(row,"parent_present")),"definition parent edge has no actual parent");
            boolean terminal=false;
            for(JsonNode value:entries){ObjectNode item=obj(value);entry(item,depth,depth);int flag=number(item,"entry_flag_4c").intValueExact(),mode=number(item,"entry_mode_40").intValueExact();
                if(flag==0)filtered(item);terminal=flag>0&&mode>=0&&mode<=1;}
            boolean last=ordinal==rows.size()-1;
            if(terminal)require(last&&reason.equals("static_direct_terminal")&&edge.equals("not_read_native_static_stop")&&isNull(row,"parent_present"),"continuation reads beyond native static direct stop");
            else require(!edge.equals("not_read_native_static_stop")&&!isNull(row,"parent_present"),"continuation fabricates a static stop");
            if(!last)require(Boolean.TRUE.equals(nullableBool(row,"parent_present")),"continuation continues beyond a null parent");
        }
        int count=rows.size();Boolean next=nullableBool(raw,"next_context_present");ObjectNode last=count==0?null:obj(rows.get(count-1));boolean valid=switch(reason){
            case "depth_limit"->count==4&&stop==12&&Boolean.TRUE.equals(next)&&Boolean.TRUE.equals(nullableBool(last,"parent_present"));
            case "null_end"->count>=1&&stop==8+count&&Boolean.FALSE.equals(next)&&Boolean.FALSE.equals(nullableBool(last,"parent_present"));
            case "cycle"->count<=3&&stop==8+count&&Boolean.TRUE.equals(next)&&(last==null||Boolean.TRUE.equals(nullableBool(last,"parent_present")));
            case "static_direct_terminal"->count>=1&&stop==7+count&&next==null&&string(last,"parent_edge").equals("not_read_native_static_stop");
            default->false;};
        require(valid,"continuation stop reason contradicts original rows/frontier");if(raw.has(SWITCH))staticSwitch(obj(raw.get(SWITCH)),rows);
    }
    private static void staticSwitch(ObjectNode raw,ArrayNode rows){
        keys(raw,SWITCH_FIELDS,Set.of());eq(raw,"source","native_gui_type635_static_direct_owner_switch_12004");eq(raw,"scope","static_direct_source_candidate");
        no(raw,"current_variable_table_observed","native_receiver_selected","provider_invoked");bool(raw,"stable_double_read");
        if(!available(raw)){require(!string(raw,"unavailable_reason").isEmpty()&&!bool(raw,"stable_double_read"),"unavailable static switch qualification differs");
            for(String field:List.of("ancestor_depth","owner_full_id","military_component_present","raw_byte_4a9","enabled","value_basis"))require(isNull(raw,field),"unavailable static switch leaked an observation");return;}
        int depth=integer(raw,"ancestor_depth",8,11).intValueExact();int owner=NativeCharacterId.of(integer(raw,"owner_full_id",Integer.MIN_VALUE,Integer.MAX_VALUE)).value();
        switchObservation(raw,owner);long matches=0;
        for(JsonNode value:rows){ObjectNode row=obj(value);if(number(row,"ancestor_depth").intValueExact()!=depth)continue;
            for(JsonNode candidate:array(row,"entries",1)){ObjectNode item=obj(candidate);
                if(number(item,"entry_mode_40").intValueExact()==1&&number(item,"entry_flag_4c").signum()!=0&&bool(item,"direct_value_present")
                        &&bool(item,"direct_owner_identity_verified")&&!isNull(item,"direct_owner_full_id")&&number(item,"direct_owner_full_id").equals(BigInteger.valueOf(owner)))matches++;}}
        require(matches==1,"static switch lacks its unique verified source owner entry");
    }
    private static CensusFrame frame(ObjectNode raw){
        keys(raw,Set.of("native_revision","connection_generation","pump_epoch","ticket_sequence","game_pid","thread_id","played_character_full_id","date_raw","owner_thread_verified","frame_stable","gui_owner_stable"),Set.of());
        for(String key:List.of("owner_thread_verified","frame_stable","gui_owner_stable"))require(bool(raw,key),"receiver frame owner/world binding unverified");
        return new CensusFrame(integer(raw,"native_revision",BigInteger.ONE,U64),integer(raw,"connection_generation",BigInteger.ONE,U64),
                integer(raw,"pump_epoch",BigInteger.ONE,U64),integer(raw,"ticket_sequence",BigInteger.ONE,U64),
                integer(raw,"game_pid",1,0xffff_ffffL).longValueExact(),integer(raw,"thread_id",1,0xffff_ffffL).longValueExact(),
                NativeCharacterId.of(integer(raw,"played_character_full_id",Integer.MIN_VALUE,Integer.MAX_VALUE)).value(),integer(raw,"date_raw",Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact());
    }
    private static void failure(ObjectNode raw,int maxDepth){
        keys(raw,Set.of("stage","kind","capture_pass","read_ordinal","ancestor_depth","raw_declaration_count","raw_index_count","raw_definition_entry_count","context_present","definition_present","local_definition_active_raw"),Set.of());
        for(String field:List.of("stage","kind"))require(string(raw,field).matches("[a-z0-9_]{1,64}"),"receiver failure diagnostic label");
        integer(raw,"capture_pass",1,2);integer(raw,"read_ordinal",0,4097);nullableInteger(raw,"ancestor_depth",0,maxDepth);
        for(String field:List.of("raw_declaration_count","raw_index_count","raw_definition_entry_count"))nullableInteger(raw,field,Integer.MIN_VALUE,Integer.MAX_VALUE);
        nullableBool(raw,"context_present");nullableBool(raw,"definition_present");nullableInteger(raw,"local_definition_active_raw",0,255);
    }
    private static void definition(ObjectNode row,boolean present,ArrayNode entries){
        if(!present)require(isNull(row,"raw_definition_entry_count")&&entries.isEmpty(),"null definition cannot supply a table or entry");
        else {int count=integer(row,"raw_definition_entry_count",0,256).intValueExact();require(entries.isEmpty()||count>0,"entry appears in an empty definition table");}
    }
    private static void filtered(ObjectNode entry){for(String field:List.of("provider_vtable_rva","provider_slot2_rva","direct_owner_full_id"))require(isNull(entry,field),"filtered parent entry leaked provider/owner");
        require(!bool(entry,"direct_owner_identity_verified"),"filtered parent entry claimed a verified owner");}
    private static void declaration(ObjectNode raw){require(available(raw)&&isNull(raw,"unavailable_reason")&&bool(raw,"stable_double_read"),"available candidate declaration lacks stable double read");
        integer(raw,"receiver_variable_index",0,255);integer(raw,"declared_type_id",635,635);}
    private static void unavailable(ObjectNode raw,List<String> fields,ArrayNode rows){require(!available(raw)&&!string(raw,"unavailable_reason").isEmpty()
            &&!bool(raw,"stable_double_read")&&rows.isEmpty(),"unavailable receiver must retain unknown values");for(String field:fields)require(isNull(raw,field),"unavailable receiver leaked "+field);}
    private static boolean available(ObjectNode raw){String status=string(raw,"status");require(status.equals("available")||status.equals("unavailable"),"closed receiver availability required");return status.equals("available");}
    private static void sameDeclaration(ObjectNode first,ObjectNode second){same(first,second,"receiver_variable_index");same(first,second,"declared_type_id");}
    private static void same(ObjectNode first,ObjectNode second,String field){require(required(first,field).equals(required(second,field)),"independent source observations differ: "+field);}
    private static void no(ObjectNode raw,String... fields){for(String field:fields)require(!bool(raw,field),"candidate must preserve unknown/non-invoked "+field);}
    private static ObjectNode obj(JsonNode node){require(node instanceof ObjectNode,"original receiver object required");return (ObjectNode)node;}
    private static ObjectNode fullNode(RawJson raw){return obj(DriverJson.toNode(DriverJson.object(raw.bytes(),RawJson.MAXIMUM_BYTES)));}
    private static RawJson fullRaw(JsonNode node){return new RawJson(DriverJson.encodeNode(node));}
    private static Set<String> names(ObjectNode row){Set<String> fields=new HashSet<>();row.fieldNames().forEachRemaining(fields::add);return fields;}
    private static void keys(ObjectNode row,Set<String> mandatory,Set<String> optional){Set<String> actual=names(row),allowed=new HashSet<>(mandatory);allowed.addAll(optional);
        require(actual.containsAll(mandatory)&&allowed.containsAll(actual),"closed original receiver fields differ");}
    private static JsonNode required(ObjectNode row,String field){JsonNode value=row.get(field);require(value!=null,"missing original receiver field: "+field);return value;}
    private static boolean isNull(ObjectNode row,String field){return required(row,field).isNull();}
    private static String string(ObjectNode row,String field){JsonNode value=required(row,field);require(value.isTextual(),"original string required: "+field);return value.textValue();}
    private static BigInteger number(ObjectNode row,String field){return StrictJson.integer(required(row,field),BigInteger.valueOf(Long.MIN_VALUE),U64);}
    private static ArrayNode array(ObjectNode row,String field,int bound){JsonNode value=required(row,field);require(value.isArray()&&value.size()<=bound,"bounded original array required: "+field);return (ArrayNode)value;}
    private static void nullableInteger(ObjectNode row,String field,long low,long high){if(!isNull(row,field))integer(row,field,low,high);}
    private static Boolean nullableBool(ObjectNode row,String field){return isNull(row,field)?null:bool(row,field);}
}
