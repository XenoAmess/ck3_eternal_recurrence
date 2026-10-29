package org.xar.ck3.control.nativebridge.publicmethods.gui;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Python unit census port for software writer/read/observer tests. DATA only; creates no Guard, permission or Game. */
public final class MilitaryReceiverFixture {
    private static final String LOCAL="local_definition_entry_only",PREFIX="definition_chain_prefix_depth8";
    private static final String TAIL="definition_frontier_continuation_depth8_12",SWITCH="static_direct_owner_switch_12004";
    private MilitaryReceiverFixture(){ }
    public static RawJson census(Binding binding,int rawSwitch,long ticketSequence){
        return census(binding,OptionalInt.of(rawSwitch),BigInteger.valueOf(ticketSequence));
    }
    public static RawJson census(Binding binding,OptionalInt rawSwitch,BigInteger ticketSequence){
        Objects.requireNonNull(binding);Objects.requireNonNull(rawSwitch);Objects.requireNonNull(ticketSequence);
        require(rawSwitch.isEmpty()||rawSwitch.getAsInt()>=0&&rawSwitch.getAsInt()<=255,"fixture native byte is uint8 or genuinely absent");
        require(ticketSequence.signum()>0&&ticketSequence.compareTo(U64)<=0,"fixture original ticket is a positive uint64");
        return new RawJson(DriverJson.encodeNode(censusData(binding,rawSwitch.isPresent()?rawSwitch.getAsInt():null,ticketSequence)));
    }
    /** Reinforcement ACK fixture only. Source flags remain pending; the actual pipeline must independently observe its result. */
    public static RawJson acknowledgement(Control control,Binding binding,BeforeObservation before){
        Objects.requireNonNull(control);Objects.requireNonNull(binding);Objects.requireNonNull(before);
        require(control!=Control.OPEN,"a refill before-observation cannot stand in for the opener visibility profile");
        before.frame().requireBinding(binding);boolean attempted=before.sourceSwitch().enabled()!=control.desiredEnabled();
        ObjectNode row=StrictJson.object().put("schema","ck3-military-reinforcement-set-12004-v1").put("step",control.operation().value())
                .put("accepted",true).put("status",attempted?"acknowledged_verification_pending":"noaction_already_desired")
                .putNull("unavailable_reason").put("desired_enabled",control.desiredEnabled()).put("game_version","1.20.0.4")
                .put("executable_sha256",binding.context().build().sha256()).put("native_revision",binding.nativeRevision())
                .put("connection_generation",binding.generation()).put("game_pid",binding.pid()).put("played_character_id",binding.actor())
                .put("date_raw",binding.dateRaw()).put("source_child_path",before.sourceChildPath()).put("source_gui_sha256",REFILL_GUI)
                .put("dispatch_attempted",attempted).put("dispatch_invoked",attempted).put("native_handled",false)
                .put("postcondition_verified",false).put("verification_pending",true);
        for(String field:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified",
                "source_profile_verified","current_tree_complete","no_blocking_modal_verified"))row.put(field,true);
        for(String field:List.of("current_variable_table_observed","native_receiver_selected","provider_invoked"))row.put(field,false);
        row.set("before_switch",DriverJson.toNode(DriverJson.object(before.sourceSwitch().original().bytes(),RawJson.MAXIMUM_BYTES)));
        return new RawJson(DriverJson.encodeNode(row));
    }
    private static ObjectNode entry(int depth){return StrictJson.object().put("ancestor_depth",depth).put("entry_type_48",635).put("entry_mode_40",0).put("entry_flag_4c",0)
            .put("direct_value_present",false).put("provider_present",false).putNull("provider_vtable_rva").putNull("provider_slot2_rva")
            .putNull("direct_owner_full_id").put("direct_owner_identity_verified",false);}
    private static ObjectNode source(){return StrictJson.object().put("executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
            .put("button_base_slot13_rva",0x3aa0d20).put("group_dispatch_rva",0x3a9fa30).put("input_modifier",0)
            .put("indirect_target_thunk_rva",0x3aa30e0).put("indirect_target_thunk_bytes_sha256","7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563")
            .put("expression_target_bridge_rva",0x3a9f960).put("expression_builder_rva",0x3ac38c0).put("expression_eval_rva",0x3e4c090)
            .put("expression_layout_bytes_sha256","7412efd136e722993b71a8810f5d585347cde53104ba0a107551eb324ff18963")
            .put("receiver_definition_parent_rva",0x3ac3ef0).put("receiver_typed_entry_rva",0x3ac1c00)
            .put("receiver_definition_parent_bytes_sha256","476ac96745e7088e7dd2073cfc00e023d8a1102a8d154a51434886d6d5b5a2a7")
            .put("receiver_typed_entry_bytes_sha256","8efccb736158d04c2847d98e8aa6d3400ae8591467d2628726a1f1c396e43cfc");}
    private static ObjectNode switchRow(Integer value,int owner){ObjectNode row=StrictJson.object().put("source","native_gui_type635_static_direct_owner_switch_12004")
            .put("scope","static_direct_source_candidate").put("status","available").putNull("unavailable_reason")
            .put("current_variable_table_observed",false).put("native_receiver_selected",false).put("provider_invoked",false)
            .put("ancestor_depth",8).put("owner_full_id",owner).put("military_component_present",value!=null)
            .put("enabled",value!=null&&value!=0).put("value_basis",value==null?"native_null_military_zero":"raw_military_byte").put("stable_double_read",true);
        if(value==null)row.putNull("raw_byte_4a9");else row.put("raw_byte_4a9",value);return row;}
    private static ObjectNode candidates(Integer value,int owner){
        ObjectNode local=StrictJson.object().put("source","native_gui_type635_local_definition_entry_only_12004").put("scope","local_definition_entry_only")
                .put("status","available").putNull("unavailable_reason").put("receiver_type_id",635).put("ancestor_depth",0)
                .put("current_variable_table_observed",false).put("native_receiver_selected",false).put("receiver_variable_index",0).put("declared_type_id",635)
                .put("raw_definition_entry_count",1).put("local_definition_active_raw",1).put("definition_present",true).put("local_entry_present",true).put("stable_double_read",true);
        local.putArray("entries").add(entry(0));
        ObjectNode prefix=StrictJson.object().put("source","native_gui_type635_definition_chain_prefix_depth8_12004").put("scope","visited_definition_prefix_depth8")
                .put("status","available").putNull("unavailable_reason").put("receiver_type_id",635).put("depth_limit",8).put("walk_complete",false)
                .put("current_variable_table_observed",false).put("native_receiver_selected",false).put("receiver_variable_index",0).put("declared_type_id",635)
                .put("frontier_depth",8).put("frontier_context_present",true).put("stable_double_read",true);
        ArrayNode prefixRows=prefix.putArray("rows");for(int depth=0;depth<8;depth++){ObjectNode row=StrictJson.object().put("ancestor_depth",depth).put("definition_present",true)
                .put("raw_definition_entry_count",depth==0?1:0).put("parent_edge","context_e8").put("parent_present",true);ArrayNode entries=row.putArray("entries");if(depth==0)entries.add(entry(0));prefixRows.add(row);}
        ObjectNode direct=entry(8).put("entry_mode_40",1).put("entry_flag_4c",1).put("direct_value_present",true).put("direct_owner_full_id",owner).put("direct_owner_identity_verified",true);
        ObjectNode tail=StrictJson.object().put("source","native_gui_type635_frontier_continuation_depth8_12_12004").put("scope","definition_frontier_depth8_through11")
                .put("status","available").putNull("unavailable_reason").put("receiver_type_id",635).put("start_depth",8).put("depth_limit",12)
                .put("current_variable_table_observed",false).put("native_receiver_selected",false).put("provider_invoked",false)
                .put("receiver_variable_index",0).put("declared_type_id",635).put("stop_depth",8).put("stop_reason","static_direct_terminal")
                .putNull("next_context_present").put("stable_double_read",true);
        ObjectNode stop=StrictJson.object().put("ancestor_depth",8).put("definition_present",true).put("raw_definition_entry_count",3).put("first_match_entry_index",0)
                .put("parent_edge","not_read_native_static_stop").putNull("parent_present");stop.putArray("entries").add(direct);tail.putArray("rows").add(stop);tail.set(SWITCH,switchRow(value,owner));
        ObjectNode diagnostic=StrictJson.object().put("stage","parent_walk").put("kind","parent_depth_exhausted").put("capture_pass",1).put("read_ordinal",51)
                .put("ancestor_depth",8).put("raw_declaration_count",1).put("raw_index_count",1).putNull("raw_definition_entry_count")
                .put("context_present",true).putNull("definition_present").put("local_definition_active_raw",1);
        ObjectNode candidate=StrictJson.object().put("source","native_gui_type635_definition_candidates_12004").put("status","unavailable")
                .put("unavailable_reason","candidate_parent_depth_exhausted").put("receiver_type_id",635).put("current_variable_table_observed",false)
                .put("native_receiver_selected",false).putNull("receiver_variable_index").putNull("declared_type_id").put("stable_double_read",false);
        candidate.putArray("entries");candidate.set("failure_diagnostic",diagnostic);candidate.set(LOCAL,local);candidate.set(PREFIX,prefix);candidate.set(TAIL,tail);return candidate;
    }
    private static ObjectNode censusData(Binding binding,Integer value,BigInteger ticket){
        ObjectNode expression=StrictJson.object().put("chain_count_24_raw",0).put("final_type_id_30",1).put("final_kind_34_raw",3).put("final_target_38_rva",0x1303d40)
                .put("final_user_data_40_present",true).put("receiver_type_id_48",635).put("receiver_flag_4c_raw",0);expression.putArray("chain_calls");expression.set("receiver_entry_candidates_12004",candidates(value,binding.actor()));
        ObjectNode payload=StrictJson.object().put("native_target_8_rva",0x3a9f960).put("receiver_f0_present",true);payload.set("expression_3a9f960",expression);
        ObjectNode callback=StrictJson.object().put("index",0).put("callback_vtable_rva",0x40000).put("callback_slot2_rva",0x3aa30e0);callback.set("indirect_target_3aa30e0",payload);
        ObjectNode tree=StrictJson.object().put("step","inspect-gui-window-tree-v1").put("accepted",true).put("status","available")
                .put("scope_root_name","military_view").put("root_available",true).put("truncated",false).put("widget_count",9);
        String target="0/0/0/2/3/0/0/0";String[] segments=target.split("/");ArrayNode rows=tree.putArray("widgets");
        for(int depth=0;depth<=segments.length;depth++){String path=depth==0?"":String.join("/",java.util.Arrays.copyOf(segments,depth));
            String name=path.isEmpty()?"military_view":path.equals("0/0/0/2")?"tab_your_armies":path.equals("0/0/0/2/3")?"footer":"";
            ObjectNode row=StrictJson.object().put("runtime_name",name).put("child_path",path).put("depth",depth).put("child_count",path.equals(target)?0:1)
                    .put("vtable_rva",0x50000).put("effective_visible",true).put("enabled",true);
            ObjectNode click=StrictJson.object().put("button_base_slot13",path.equals(target)).put("group",path.equals(target)?"fallback":"not_button_base");
            ArrayNode callbacks=click.putArray("callbacks");if(path.equals(target))callbacks.add(callback);row.set("standard_click_binding_12004",click);rows.add(row);
        }
        tree.set("callback_binding_source_12004",source());tree.set("refill_receiver_frame_12004",StrictJson.object().put("native_revision",binding.nativeRevision()).put("connection_generation",binding.generation())
                .put("pump_epoch",96426).put("ticket_sequence",ticket).put("game_pid",binding.pid()).put("thread_id",29904).put("played_character_full_id",binding.actor()).put("date_raw",binding.dateRaw())
                .put("owner_thread_verified",true).put("frame_stable",true).put("gui_owner_stable",true));return tree;
    }
}
