package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;

/** Same-Ci captured six-stage and copied-transfer substitutions; identity equality alone never selects a PC. */
final class CombatKnightOwnedPreparation {
    private CombatKnightOwnedPreparation() { }
    record Override(Optional<BigInteger> value,Obj detail) { }
    record Owned(Map<Integer,Override> overrides,ArrayNode ledger) {Owned {overrides=Map.copyOf(overrides);ledger=ledger.deepCopy();}}
    record Transfer(Optional<ObjectNode> pc,Obj proof) {Transfer {pc=pc.map(ObjectNode::deepCopy);}}
    private record Composed(ObjectNode capture,ObjectNode post,ObjectNode owner) { }
    static Owned owned(ObjectNode event) {
        Map<Integer,Override> overrides=new LinkedHashMap<>();var ledger=obj().arrayNode();List<Composed> cached=new ArrayList<>();
        for(var raw:array(event.get("contexts"))) {
            ObjectNode row=object(raw);JsonNode lineage=row.get("preparation_stage_lineage"),capture=row.get("preparation_capture_at_consumption");
            if(lineage==null||!lineage.isObject()||!yes(lineage.get("completed_preparation_lineage_proven"))||capture==null||!capture.isObject())continue;
            JsonNode preparation=capture.get("preparation_model");if(!yes(capture.get("aggregate_postimage_comparison_ready"))||nil(preparation)||!yes(preparation.get("ready")))continue;
            Composed joined=cached.stream().filter(c->c.capture().equals(capture)).findFirst().orElse(null);
            if(joined==null) {
                var section=obj();section.set("character_id",capture.get("character_id").deepCopy());section.set(BattlePersonSixStageCaptureCodec.CAPTURE_FIELD,capture.deepCopy());
                var baseline=BattlePersonSixStageConsumers.emitPreSixAggregate(section);var requests=BattlePersonSixStageConsumers.emitRequests(section);var owner=BattlePersonSixStageConsumers.emitPreparationModel(section);
                var post=compose(baseline,requests,object(capture));joined=new Composed(object(capture),post,owner);cached.add(joined);
                var l=ledger.addObject();copy(capture,l,"capture_sequence capture_thread_id character_id character_identity context_identity");l.set("completion_thread_id",capture.get("query_thread_id").deepCopy());l.set("model_identity",owner.get("model_identity").deepCopy());l.set("completion_matches_composition",post.get("completion_matches_composition").deepCopy());l.put("source","same_ci_owned_preparation_capture_at_consumption");
            }
            if(!selects(row,event,joined.post(),joined.owner()))continue;
            int key=integer(row.get("property_key")).intValueExact();var p=joined.post();
            var context=CombatKnightKernel.container(p.get("keys_u16"),p.get("values_q64"),obj().numberNode(p.get("keys_u16").size()));
            var lookup=integer(row.get("operand_raw")).signum()==0?null:CombatKnightKernel.lookup(context,key);
            var detail=obj().put("property_key",key).put("branch","owned_historical_postimage_selected_at_consumed_ci");copy(row,detail,"operand_raw preparation_stage_lineage context_identity selected_character_id selected_character_identity");detail.set("capture_sequence",p.get("capture_sequence").deepCopy());detail.set("model_identity",row.get("preparation_model_identity").deepCopy());detail.set("lookups",lookup==null?obj().arrayNode():node(lookup.detail()).get("lookups"));detail.set("missing_inputs",lookup==null?obj().arrayNode():node(lookup.detail()).get("missing_inputs"));detail.set("consumed_pc_identity",row.get("consumed_pc").get("identity").deepCopy());detail.put("preparation_capture_source","same_ci_owned_preparation_capture_at_consumption");
            overrides.put(key,new Override(lookup==null?Optional.empty():lookup.value(),immutable(detail)));
        }
        return new Owned(overrides,ledger);
    }
    private static ObjectNode compose(ObjectNode baseline,ArrayNode requests,ObjectNode capture) {
        List<Integer> keys=new ArrayList<>();List<BigInteger> values=new ArrayList<>();
        var seed=obj().put("weight_q100000",100000);seed.set("property_block",baseline.get("property_block"));var all=obj().arrayNode().add(seed);requests.forEach(all::add);
        for(var request:all) {
            JsonNode block=request.get("property_block");int count=integer(block.get("keys_count")).intValueExact();if(count==0)continue;
            BigInteger weight=integer(request.get("weight_q100000"));JsonNode sk=block.get("keys_u16"),sv=block.get("values_q64");
            if(keys.isEmpty()){for(int i=0;i<count;i++){keys.add(integer(sk.get(i)).intValueExact());var v=integer(sv.get(i));values.add(weight.equals(BigInteger.valueOf(100000))?v:CombatKnightKernel.fixedMultiply(v,weight));}continue;}
            for(int i=0;i<count;i++) {
                int key=integer(sk.get(i)).intValueExact();var term=CombatKnightKernel.fixedMultiply(integer(sv.get(i)),weight);if(key==65535)continue;
                int first=0,remaining=keys.size();while(remaining>0){int half=remaining>>>1;if(keys.get(first+half)<key)first+=remaining-half;remaining=half;}
                if(first==keys.size()||keys.get(first)!=key){keys.add(first,key);values.add(first,BigInteger.ZERO);}values.set(first,CombatKnightKernel.wrap64(values.get(first).add(term)));
            }
        }
        var post=obj();var k=post.putArray("keys_u16");keys.forEach(k::add);values(post,"values_q64",values);copy(baseline,post,"character_id capture_sequence capture_date_raw capture_thread_id context_identity");post.put("historical_postimage_ready",true).put("completion_observation_ready",yes(capture.get("aggregate_postimage_comparison_ready")));
        JsonNode observed=capture.get("post_six_aggregate").get("pc").get("properties");if(yes(capture.get("aggregate_postimage_comparison_ready")))post.put("completion_matches_composition",eq(k,observed.get("keys_u16"))&&eq(post.get("values_q64"),observed.get("values_q64")));else post.putNull("completion_matches_composition");return post;
    }
    private static boolean selects(ObjectNode row,ObjectNode event,ObjectNode post,ObjectNode owner) {
        var lineage=row.get("preparation_stage_lineage");if(lineage==null||!lineage.isObject()||!yes(lineage.get("completed_preparation_lineage_proven")))return false;
        BigInteger context=identity(post.get("context_identity")),selected=identity(row.get("selected_character_id"));
        return yes(post.get("historical_postimage_ready"))&&yes(post.get("completion_observation_ready"))&&yes(post.get("completion_matches_composition"))&&yes(owner.get("historical_capture"))
                &&same(post.get("capture_sequence"),owner.get("capture_sequence"),row.get("preparation_capture_sequence"))&&context!=null&&context.equals(identity(owner.get("context_identity")))&&context.equals(identity(row.get("preparation_context_identity")))&&context.equals(identity(row.get("context_identity")))
                &&same(row.get("preparation_model_identity"),owner.get("model_identity"))&&selected!=null&&selected.equals(identity(post.get("character_id")))&&selected.equals(identity(owner.get("owner_character_id")))&&selected.equals(identity(row.get("preparation_owner_character_id")))
                &&same(row.get("selected_character_identity"),owner.get("owner_character_identity"))&&same(post.get("capture_thread_id"),owner.get("capture_thread_id"),event.get("thread_id"));
    }
    private static boolean same(JsonNode... ns) {BigInteger first=identity(ns[0]);if(first==null)return false;for(var n:ns)if(!first.equals(identity(n)))return false;return true;}
    private static boolean nonzero(JsonNode n) {var x=identity(n);return x!=null&&x.signum()!=0;}
    private static ObjectNode physicalPc(JsonNode copy) {
        JsonNode keys=copy.get("block78_keys"),values=copy.get("blocke0_values"),kr=keys.get("raw"),vr=values.get("raw"),ordered=kr.get("keys_u16"),bits=values.get("values_q64_raw_bits");
        BigInteger model=identity(copy.get("scope").get("model_identity"));JsonNode count=kr.get("count_i32");
        if(!yes(keys.get("payload_copy_complete"))||!yes(values.get("payload_copy_complete"))||!yes(kr.get("key_elements_ready"))||nil(count)||integer(count).signum()<0||!eq(count,vr.get("count_i32"))||nil(ordered)||nil(bits)||integer(count).compareTo(BigInteger.valueOf(ordered.size()))!=0||ordered.size()!=bits.size()||model==null||model.signum()==0
                ||!model.add(BigInteger.valueOf(0x78)).equals(identity(kr.get("storage_identity")))||!model.equals(identity(vr.get("model_identity")))||!model.add(BigInteger.valueOf(0xe0)).equals(identity(vr.get("block_identity")))||(integer(count).signum()>0&&(!nonzero(kr.get("data_identity"))||!nonzero(vr.get("data_identity")))))return null;
        var pc=obj().put("ready",true).put("admitted",true).putNull("reason").put("identity",model.add(BigInteger.valueOf(0x78))).put("weight_q100000",0);pc.set("count_i32",count.deepCopy());var properties=pc.putObject("properties");properties.set("keys_u16",ordered.deepCopy());var converted=properties.putArray("values_q64");for(var v:bits)converted.add(CombatKnightKernel.wrap64(integer(v)));return pc;
    }
    static Transfer transfer(ObjectNode row,JsonNode thread) {
        var proof=obj();copy(row,proof,"property_key");proof.put("ready",false).putNull("prepared_metadata_matches").putNull("b_before_to_a_after_payload_equal").putNull("b_before_matches_retained_preparation_pc").putNull("a_after_matches_consumed_pc").put("source","same_ci_owned_completed_preparation_pc_through_copied_transfer").put("later_current_query_used",false).put("generic_postimages_complete",false).put("full_person_ready",false).put("full_entry_ready",false);
        JsonNode lineage=row.get("installed_transfer_lineage");if(lineage==null||!lineage.isObject()||!yes(lineage.get("installed_identity_associated")))return absent(proof,"installed_identity_not_associated");
        JsonNode records=lineage.path("capture_at_consumption").get("records"),record=records!=null&&records.isArray()&&!records.isEmpty()?records.get(0):null,physical=record==null?null:record.get("physical_postimage"),capture=row.get("preparation_capture_at_consumption");
        if(physical==null||!physical.isObject()||capture==null||!capture.isObject())return absent(proof,"owned_physical_or_preparation_copy_unavailable");
        JsonNode stage=record.get("stage"),comparison=physical.get("comparison"),prepared=capture.get("preparation_model"),completed=capture.get("post_six_aggregate");
        var before=physicalPc(physical.get("before").get("b"));var after=physicalPc(physical.get("after").get("a"));
        if(before==null||after==null||nil(prepared)||nil(completed))return absent(proof,"independent_physical_pc_or_preparation_copy_partial");
        JsonNode post=completed.get("pc"),actual=row.get("consumed_pc"),descriptor=stage.get("preparation");BigInteger mb=identity(stage.get("model_b_identity")),ma=identity(stage.get("model_a_identity")),selected=identity(row.get("selected_character_identity")),full=identity(row.get("selected_character_id"));
        int mask=0;for(var s:array(capture.get("stages")))if(yes(s.get("observed")))mask+=1<<integer(s.get("index")).intValueExact();
        boolean metadata=yes(capture.get("configured"))&&yes(capture.get("historical_capture"))&&yes(capture.get("capture_observed"))&&yes(capture.get("capture_complete"))&&yes(capture.get("ready"))&&yes(capture.get("raw_counts_ready"))&&yes(capture.get("aggregate_postimage_comparison_ready"))&&nonzero(capture.get("capture_sequence"))
                &&same(capture.get("capture_sequence"),descriptor.get("preparation_capture_sequence"),row.get("preparation_capture_sequence"))&&BigInteger.valueOf(0x291cea9).equals(identity(capture.get("source_return_rva")))&&mask==0x3f
                &&yes(prepared.get("observed"))&&yes(prepared.get("ready"))&&yes(prepared.get("owner_matches_capture"))&&yes(descriptor.get("observed"))&&yes(descriptor.get("preparation_capture_complete"))&&mb!=null&&mb.signum()!=0&&ma!=null&&ma.signum()!=0&&selected!=null&&selected.signum()!=0&&full!=null
                &&same(capture.get("character_id"),row.get("selected_character_id"),prepared.get("owner_character_id"),descriptor.get("preparation_owner_character_id"))
                &&same(capture.get("character_identity"),row.get("selected_character_identity"),prepared.get("owner_character_identity"),descriptor.get("preparation_character_identity"),descriptor.get("preparation_owner_character_identity"))
                &&mb.equals(identity(prepared.get("model_identity")))&&mb.equals(identity(descriptor.get("preparation_model_identity")))&&mb.add(BigInteger.valueOf(0x10)).equals(identity(capture.get("context_identity")))&&same(capture.get("context_identity"),descriptor.get("preparation_context_identity"))
                &&mb.add(BigInteger.valueOf(0x78)).equals(identity(post.get("identity")))&&same(post.get("identity"),before.get("identity"))&&ma.add(BigInteger.valueOf(0x10)).equals(identity(row.get("context_identity")))&&ma.add(BigInteger.valueOf(0x78)).equals(identity(actual.get("identity")))&&same(actual.get("identity"),after.get("identity"))
                &&nonzero(thread)&&same(capture.get("capture_thread_id"),capture.get("query_thread_id"),thread,descriptor.get("preparation_capture_thread_id"),descriptor.get("preparation_completion_thread_id"))&&yes(comparison.get("preparation_descriptor_matches_before_b"))&&yes(comparison.get("preparation_threads_match_original"));
        proof.put("prepared_metadata_matches",metadata).put("b_before_to_a_after_payload_equal",payload(before,after));boolean complete=complete(post)&&yes(completed.get("observed")),consumed=complete(actual);
        if(complete)proof.put("b_before_matches_retained_preparation_pc",payload(before,post));if(consumed)proof.put("a_after_matches_consumed_pc",payload(after,actual));
        boolean ready=metadata&&yes(physical.get("before").get("configured"))&&yes(physical.get("after").get("configured"));for(String key:List.of("same_original_observation_ready","original_transfer_returned","model_pair_matches_transfer","snapshot_scopes_match_transfer","same_clock_and_thread","completion_after_begin"))ready&=yes(comparison.get(key));ready&=yes(comparison.get("block78_keys").get("a_payload_equals_b_before"))&&yes(comparison.get("blocke0_values").get("a_payload_equals_b_before"));for(String key:List.of("b_before_to_a_after_payload_equal","b_before_matches_retained_preparation_pc","a_after_matches_consumed_pc"))ready&=yes(proof.get(key));
        proof.put("ready",ready);copy(record,proof,"record_sequence");copy(capture,proof,"capture_sequence");proof.put("preparation_pc_identity",identity(post.get("identity"))).put("b_before_pc_identity",identity(before.get("identity"))).put("a_after_pc_identity",identity(after.get("identity"))).put("consumed_pc_identity",identity(actual.get("identity")));if(!ready)return absent(proof,"copied_preparation_transfer_ci_relation_unproven");proof.putNull("reason");
        var pc=obj().put("ready",true).put("admitted",true).putNull("reason").put("identity",identity(post.get("identity"))).put("weight_q100000",0);copy(post,pc,"count_i32 properties");return new Transfer(Optional.of(pc),immutable(proof));
    }
    private static boolean complete(JsonNode pc) {JsonNode props=pc.get("properties"),count=pc.get("count_i32");return yes(pc.get("ready"))&&yes(pc.get("admitted"))&&!nil(count)&&integer(count).signum()>=0&&!nil(props)&&!nil(props.get("keys_u16"))&&!nil(props.get("values_q64"))&&props.get("keys_u16").size()==props.get("values_q64").size()&&BigInteger.valueOf(props.get("keys_u16").size()).equals(integer(count));}
    private static boolean payload(JsonNode a,JsonNode b) {return eq(a.get("count_i32"),b.get("count_i32"))&&eq(a.get("properties"),b.get("properties"));}
    private static Transfer absent(ObjectNode proof,String reason) {proof.put("reason",reason);return new Transfer(Optional.empty(),immutable(proof));}
}
