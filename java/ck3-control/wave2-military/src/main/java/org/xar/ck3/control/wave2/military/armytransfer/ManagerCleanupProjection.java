package org.xar.ck3.control.wave2.military.armytransfer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** First pre-mutation manager cleanup only. Full Army/destructor/queue continuation remains unqualified. */
public final class ManagerCleanupProjection {
    private ManagerCleanupProjection(){}
    public enum Offset { O50("50"),O68("68"),O80("80"),O98("98"),OC8("c8"),O158("158");
        private final String wire;Offset(String wire){this.wire=wire;}public String wire(){return wire;}}
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE }
    public enum Branch { NOT_CALLED,CLEANUP }
    public record IdList(Offset offset,List<Integer> ids){public IdList{Objects.requireNonNull(offset);ids=copy(ids);}}
    public record Record4(long a,long b,long c,long d){public Record4{require(valid(a)&&valid(b)&&valid(c)&&valid(d),"four uint32 words required");}private static boolean valid(long x){return x>=0&&x<=0xffff_ffffL;}}
    public record Input(Boolean candidateFound,Integer candidateStoredIndex,Integer argumentArmyId,
            Integer cleanupResolvedArmyId,Boolean cleanupUsedFallback,Integer selectedBucketIndex,
            List<IdList> idLists,List<ManagerBucketCleanup.Row> bucketRows,List<Record4> records) {
        public Input{idLists=List.copyOf(idLists);bucketRows=copy(bucketRows);records=copy(records);}
    }
    public record ListProjection(Offset offset,List<Integer> observed,List<Integer> entry,boolean ready,List<Integer> after,Integer removedCount){
        public ListProjection{observed=copy(observed);entry=copy(entry);after=copy(after);}}
    public record PassedIdentity(int resolvedArmyId,long armyMagic,boolean valid){}
    public record Result(Status status,boolean ready,Branch branch,boolean candidateReady,Integer storedIndex,Integer argument,
            Boolean queueMatches,PassedIdentity passed,List<ListProjection> lists,ManagerBucketCleanup.Result bucket,
            boolean recordsReady,List<Record4> recordsBefore,List<Record4> recordsAfter,Integer recordsRemoved,List<String> missing){
        public Result{lists=List.copyOf(lists);recordsBefore=copy(recordsBefore);recordsAfter=copy(recordsAfter);missing=List.copyOf(missing);}}
    public static Input decode(JsonNode raw){
        if(raw==null||raw.isNull())return new Input(null,null,null,null,null,null,List.of(),null,null);
        require(raw.isObject(),"manager cleanup object required");List<IdList> lists=new ArrayList<>();
        JsonNode components=raw.get("id_lists");if(components!=null&&!components.isNull()){require(components.isArray(),"six manager lists required");for(JsonNode c:components){
            String wire=StrictJson.text(c.get("manager_offset"));Offset offset=java.util.Arrays.stream(Offset.values()).filter(o->o.wire().equals(wire)).findFirst().orElseThrow(()->new IllegalArgumentException("manager offset differs"));
            lists.add(new IdList(offset,ints(c.get("ordered_army_ids"))));}}
        List<ManagerBucketCleanup.Row> rows=null;JsonNode bucket=raw.get("selected_bucket_rows");
        if(bucket!=null&&!bucket.isNull()){require(bucket.isArray(),"manager bucket rows required");rows=new ArrayList<>();for(JsonNode r:bucket)rows.add(new ManagerBucketCleanup.Row(i32(r.get("stored_index")),n32(r.get("observed_army_id")),bool(r.get("native_same_cleanup_army_pointer"))));}
        List<Record4> records=null;JsonNode words=raw.get("records_b0");if(words!=null&&!words.isNull()){require(words.isArray(),"manager records required");records=new ArrayList<>();for(JsonNode row:words){require(row.isArray()&&row.size()==4,"four manager words required");records.add(new Record4(u32(row.get(0)),u32(row.get(1)),u32(row.get(2)),u32(row.get(3))));}}
        return new Input(bool(raw.get("candidate_found")),n32(raw.get("candidate_stored_index")),n32(raw.get("argument_army_id")),n32(raw.get("cleanup_resolved_army_id")),bool(raw.get("cleanup_used_fallback")),n32(raw.get("selected_bucket_index")),lists,rows,records);
    }
    public static Result project(JsonNode army,DailyQueueTransferProjection.Result transfer){
        require(army!=null&&army.isObject(),"cleanup army required");
        return project(new com.fasterxml.jackson.databind.node.TextNode("available").equals(army.get("status")),decode(army.get("monthly_first_removal_cleanup_inputs_v1")),transfer);
    }
    public static Result project(boolean available,Input input,DailyQueueTransferProjection.Result transfer){
        if(!available)return absent("available_same_query_army_strength",null);
        List<Integer> source=transfer.transfer().map(t->t.sourceIds().stream().map(org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId::value).toList()).orElse(null);
        List<Integer> queue=input.idLists().stream().filter(l->l.offset()==Offset.O68).findFirst().map(IdList::ids).orElse(null);
        Boolean matches=queue!=null&&source!=null?queue.equals(source):null;
        if(Boolean.FALSE.equals(matches))return absent("manager_id_list_68_matches_transfer_source",matches);
        if(!transfer.selectionReady())return absent("first_initial_removal_selection",matches);
        if(!transfer.firstRemovalRequestReady()){
            if(!Boolean.TRUE.equals(input.candidateFound()))return new Result(Status.AVAILABLE,true,Branch.NOT_CALLED,true,null,null,matches,null,List.of(),null,false,null,null,null,List.of());
            return absent("native_candidate_disagrees_with_known_no_call",matches);
        }
        var request=transfer.firstRemovalRequest().orElseThrow();
        if(!Boolean.TRUE.equals(input.candidateFound())||!Integer.valueOf(request.occurrence().storedIndex()).equals(input.candidateStoredIndex())||!Integer.valueOf(request.resolvedArmy().value()).equals(input.argumentArmyId()))
            return absent("native_candidate_matches_first_removal_request",matches);
        int argument=input.argumentArmyId();List<String> missing=new ArrayList<>();List<ListProjection> lists=new ArrayList<>();
        for(Offset offset:Offset.values()){
            List<Integer> observed=input.idLists().stream().filter(l->l.offset()==offset).findFirst().map(IdList::ids).orElse(null);
            List<Integer> entry=offset==Offset.O68?(transfer.conditionalTransferReady()?List.of():null):observed;
            List<Integer> after=null;Integer removed=null;boolean ready=entry!=null;
            if(ready){after=new ArrayList<>(entry);removed=0;int index=after.indexOf(argument);if(index>=0){if(offset==Offset.O50)after.remove(index);else{after.set(index,after.getLast());after.removeLast();}removed=1;}}
            else missing.add("id_lists["+offset.wire()+"].ordered_army_ids");
            lists.add(new ListProjection(offset,observed,entry,ready,after,removed));
        }
        var bucket=ManagerBucketCleanup.project(new ManagerBucketCleanup.Input(input.cleanupResolvedArmyId(),input.cleanupUsedFallback(),input.selectedBucketIndex(),input.bucketRows()));missing.addAll(bucket.missingInputs());
        List<Record4> before=input.records(),after=null;Integer removed=null;boolean recordsReady=before!=null;
        if(recordsReady){after=new ArrayList<>(before);int index=0;while(index<after.size()){if(after.get(index).a()==Integer.toUnsignedLong(argument)){after.set(index,after.getLast());after.removeLast();}else index++;}removed=before.size()-after.size();}
        else missing.add("records_b0");
        boolean ready=lists.stream().allMatch(ListProjection::ready)&&bucket.ready()&&recordsReady;
        return new Result(ready?Status.AVAILABLE:Status.PARTIAL,ready,Branch.CLEANUP,true,input.candidateStoredIndex(),argument,matches,
            new PassedIdentity(argument,request.armyMagic().value(),request.nativeIdentityValid()),lists,bucket,recordsReady,before,after,removed,missing);
    }
    private static Result absent(String gap,Boolean matches){return new Result(Status.UNAVAILABLE,false,null,false,null,null,matches,null,List.of(),null,false,null,null,null,List.of(gap));}
    public static ObjectNode encode(Result result){
        ObjectNode n=StrictJson.object();n.put("projection_kind","conditional_first_removal_manager_cleanup");n.put("native_stage_rva","0x2A98200");n.put("source_contract_game_version","1.20.0.3");n.put("input_basis","same_query_first_pre_mutation_occurrence");n.put("status",result.status().name().toLowerCase(Locale.ROOT));n.put("conditional_manager_cleanup_ready",result.ready());
        if(result.branch()==null)n.putNull("conditional_cleanup_branch");else n.put("conditional_cleanup_branch",result.branch().name().toLowerCase(Locale.ROOT));n.put("candidate_selection_ready",result.candidateReady());put(n,"candidate_stored_index",result.storedIndex());put(n,"argument_army_id",result.argument());put(n,"observed_queue_matches_transfer",result.queueMatches());n.put("conditional_passed_army_identity_ready",result.passed()!=null);n.putNull("conditional_passed_army_identity_after_top_stage");
        if(result.passed()!=null){ObjectNode p=n.putObject("conditional_passed_army_identity_after_top_stage");p.put("resolved_army_id",result.passed().resolvedArmyId());p.put("army_magic_14_raw",result.passed().armyMagic());p.put("native_army_identity_valid",result.passed().valid());p.put("basis","top_stage_preserves_passed_army_identity");}
        ArrayNode lists=n.putArray("id_list_projections");for(var l:result.lists()){ObjectNode r=lists.addObject();r.put("manager_offset",l.offset().wire());ids(r,"observed_ordered_army_ids",l.observed());ids(r,"conditional_stage_entry_ordered_army_ids",l.entry());r.put("stage_input_basis",l.offset()==Offset.O68?"derived_post_transfer_source_queue":"same_query_manager_list");r.put("operation",l.offset()==Offset.O50?"first_match_stable_remove":"first_match_swap_last_remove");r.put("conditional_ready",l.ready());ids(r,"conditional_ordered_army_ids_after",l.after());put(r,"removed_count",l.removedCount());}
        n.putNull("cleanup_resolved_army_id");n.putNull("cleanup_used_fallback");n.putNull("selected_bucket_index");n.put("selected_bucket_cleanup_ready",false);n.putNull("selected_bucket_rows_before");n.putNull("conditional_selected_bucket_rows_after");n.putArray("selected_bucket_removed_stored_indices");
        if(result.bucket()!=null){var b=result.bucket();put(n,"cleanup_resolved_army_id",b.resolvedArmyId());put(n,"cleanup_used_fallback",b.usedFallback());put(n,"selected_bucket_index",b.selectedBucketIndex());n.put("selected_bucket_cleanup_ready",b.ready());if(b.before()!=null)bucketRows(n.putArray("selected_bucket_rows_before"),b.before());if(b.after()!=null)bucketRows(n.putArray("conditional_selected_bucket_rows_after"),b.after());ArrayNode removed=n.putArray("selected_bucket_removed_stored_indices");b.removedStoredIndices().forEach(removed::add);}
        n.put("records_b0_cleanup_ready",result.recordsReady());records(n,"records_b0_before",result.recordsBefore());records(n,"conditional_records_b0_after",result.recordsAfter());put(n,"records_b0_removed_count",result.recordsRemoved());
        n.put("actual_cleanup",false);n.put("actual_removal",false);n.putNull("actual_post_state");n.put("full_army_lifecycle_ready",false);n.put("full_monthly_lifecycle_ready",false);n.put("full_ordered_removal_requests_ready",false);ArrayNode missing=n.putArray("missing_inputs");result.missing().forEach(missing::add);return n;
    }
    private static void bucketRows(ArrayNode out,List<ManagerBucketCleanup.Row> rows){for(var r:rows){ObjectNode n=out.addObject();n.put("stored_index",r.storedIndex());put(n,"observed_army_id",r.observedArmyId());put(n,"native_same_cleanup_army_pointer",r.nativeSameCleanupPointer());}}
    private static void records(ObjectNode n,String key,List<Record4> rows){n.putNull(key);if(rows!=null){ArrayNode out=n.putArray(key);for(var r:rows)out.addArray().add(r.a()).add(r.b()).add(r.c()).add(r.d());}}
    private static void ids(ObjectNode n,String key,List<Integer> rows){n.putNull(key);if(rows!=null){ArrayNode a=n.putArray(key);rows.forEach(a::add);}}
    private static void put(ObjectNode n,String key,Integer value){if(value==null)n.putNull(key);else n.put(key,value.intValue());}
    private static void put(ObjectNode n,String key,Boolean value){if(value==null)n.putNull(key);else n.put(key,value.booleanValue());}
    private static int i32(JsonNode value){return(int)StrictJson.integer(value,Integer.MIN_VALUE,Integer.MAX_VALUE);}
    private static Integer n32(JsonNode value){return value==null||value.isNull()?null:i32(value);}
    private static long u32(JsonNode value){return StrictJson.integer(value,0,0xffff_ffffL);}
    private static Boolean bool(JsonNode value){if(value==null||value.isNull())return null;require(value.isBoolean(),"cleanup Boolean required");return value.booleanValue();}
    private static List<Integer> ints(JsonNode value){if(value==null||value.isNull())return null;require(value.isArray(),"cleanup IDs array required");List<Integer> out=new ArrayList<>();for(JsonNode v:value)out.add(i32(v));return List.copyOf(out);}
    private static <T> List<T> copy(List<T> values){return values==null?null:List.copyOf(values);}
    private static void require(boolean yes,String message){StrictJson.require(yes,message);}
}
