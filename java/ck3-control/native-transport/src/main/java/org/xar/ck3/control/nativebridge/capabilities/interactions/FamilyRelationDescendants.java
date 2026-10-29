package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRelationJson.*;

/** Complete original occurrence roster and optional child subreads; no birth, educator or succession inference. */
public final class FamilyRelationDescendants {
    public static final String LEAF="current_first_heir_descendants_v1",SUMMARY="current_first_heir_descendants_summary_v1";
    public static final List<String> CHILDHOOD=List.of("curious","rowdy","bossy","pensive","charming");
    public static final List<String> POINT_TRAITS=List.of("intellect_good_1","intellect_good_2","intellect_good_3","intellect_bad_1","intellect_bad_2","intellect_bad_3","shrewd","dull","inbred");
    public static final List<String> EDUCATION_TRAITS=java.util.stream.Stream.of("diplomacy","martial","stewardship","intrigue","learning")
            .flatMap(skill->java.util.stream.IntStream.rangeClosed(1,5).mapToObj(rank->"education_"+skill+"_"+rank)).toList();
    private static final Set<Status> STATUSES=Set.of(Status.AVAILABLE,Status.PARTIAL,Status.UNAVAILABLE);
    private FamilyRelationDescendants() { }
    public record Occurrence(int index,long rawCharacterId,boolean generationValid,Boolean alive,Boolean childOfHeir,OpportunityJson.Obj original) {
        public Occurrence {Objects.requireNonNull(original);}
    }
    public record Child(int signedCharacterId,List<BigInteger> occurrenceIndices,OpportunityJson.Obj original) {
        public Child {occurrenceIndices=List.copyOf(occurrenceIndices);Objects.requireNonNull(original);}
        public long fullId(){return Integer.toUnsignedLong(signedCharacterId);}
    }
    public static final class Observation {
        private final OpportunityJson.Obj original;
        private final Status status;
        private final boolean complete;
        private final List<Occurrence> occurrences;
        private final List<Child> children;
        private Observation(JsonNode original,Status status,boolean complete,List<Occurrence> occurrences,List<Child> children){
            this.original=retain(original);this.status=status;this.complete=complete;this.occurrences=List.copyOf(occurrences);this.children=List.copyOf(children);
        }
        public OpportunityJson.Obj original(){return original;}
        public String status(){return status.name().toLowerCase(java.util.Locale.ROOT);}
        public boolean rosterComplete(){return complete;}
        public List<Occurrence> occurrences(){return occurrences;}
        public List<Child> children(){return children;}
    }
    public static Optional<Observation> decode(JsonNode value,long actor,Long heir,BigInteger revision,BigInteger date){
        if(absent(value))return Optional.empty();object(value);Availability availability=FamilyRelationJson.availability(value,STATUSES);
        boolean unavailable=availability.status()==Status.UNAVAILABLE;
        eq(value,"native_revision",revision);
        for(String key:List.of("played_character_id","heir_character_id")){
            BigInteger expected=key.equals("played_character_id")?BigInteger.valueOf(actor):heir==null?null:BigInteger.valueOf(heir);
            BigInteger observed=optionalNumber(value,key,BigInteger.ONE,I32_MAX);
            need(unavailable?observed==null||Objects.equals(observed,expected):expected!=null&&expected.equals(observed),"descendant actor/heir differs from the actual root");
        }
        BigInteger observedDate=optionalNumber(value,"date_raw",I64_MIN,I64_MAX);
        need((observedDate==null&&unavailable)||Objects.equals(observedDate,date),"descendant date differs");
        Boolean family=optionalBoolean(value,"family_present"),pointer=optionalBoolean(value,"data_pointer_present");
        BigInteger count=optionalNumber(value,"native_child_count_raw",I32_MIN,I32_MAX);
        boolean complete=bool(value,"roster_complete");List<JsonNode> rows=rows(value,"rows",4096);
        need(availability.available()==complete,"descendant availability and roster completeness differ");
        if(complete)need(Boolean.TRUE.equals(family)&&count!=null&&count.signum()>=0&&count.intValueExact()==rows.size()&&pointer!=null
                &&(count.signum()==0||pointer),"descendant complete whole-roster proof differs");
        else need(rows.isEmpty(),"incomplete descendant roster acquired observed rows");
        lineage(field(value,"played_lineage"));lineage(field(value,"heir_lineage"));
        List<Occurrence> copied=new ArrayList<>();
        for(int index=0;index<rows.size();index++){
            JsonNode row=rows.get(index);eq(row,"occurrence_index",BigInteger.valueOf(index));
            long raw=number(row,"raw_character_id",BigInteger.ZERO,U32).longValueExact();boolean generation=bool(row,"generation_valid");
            Boolean alive=optionalBoolean(row,"alive"),parent=optionalBoolean(row,"parent_family_present"),child=optionalBoolean(row,"child_of_heir");
            BigInteger p0=optionalNumber(row,"parent_0_character_id_raw",BigInteger.ZERO,U32),p4=optionalNumber(row,"parent_4_character_id_raw",BigInteger.ZERO,U32);
            if(Boolean.TRUE.equals(parent))need(p0!=null&&p4!=null&&child!=null&&child==(heir!=null&&(p0.equals(BigInteger.valueOf(heir))||p4.equals(BigInteger.valueOf(heir)))),"descendant parent slots or actual child predicate differ");
            else if(Boolean.FALSE.equals(parent))need(p0==null&&p4==null&&Boolean.FALSE.equals(child),"absent descendant family became a parent observation");
            else need(p0==null&&p4==null&&child==null,"unobserved descendant parents became known");
            lineage(field(row,"lineage"));
            if(!generation)need(alive==null&&parent==null&&child==null&&equal(field(row,"lineage"),"status","unavailable"),"unresolved descendant acquired observed values");
            copied.add(new Occurrence(index,raw,generation,alive,child,retain(row)));
        }
        List<Child> children=value.has("child_inputs")?childInputs(field(value,"child_inputs"),value,copied):List.of();
        return Optional.of(new Observation(value,availability.status(),complete,copied,children));
    }
    private static void lineage(JsonNode n){Availability a=FamilyRelationJson.availability(n,Set.of(Status.AVAILABLE,Status.UNAVAILABLE));for(String key:List.of("house_id_raw","dynasty_id_raw")){BigInteger v=optionalNumber(n,key,I32_MIN,I32_MAX);need(a.available()?v!=null:v==null,"descendant lineage lost known/unknown values");}}
    private static void childValues(JsonNode n){Availability a=observation(n,"native_character_age_and_sex",Set.of(Status.AVAILABLE,Status.UNAVAILABLE));BigInteger age=optionalNumber(n,"age_measure_raw",I16_MIN,I16_MAX),sex=optionalNumber(n,"sex_selector_raw",BigInteger.ZERO,BigInteger.ONE);need(a.available()?age!=null&&sex!=null:age==null&&sex==null,"child age/sex lost native availability");}
    private static void traits(JsonNode n,List<String> keys,boolean closed){if(closed)closed(n,"source","status","unavailable_reason","queried_trait_keys","present_trait_keys");Availability a=observation(n,"native_character_has_trait",Set.of(Status.AVAILABLE,Status.UNAVAILABLE));canonicalSubset(n,"queried_trait_keys","present_trait_keys",keys,a.available());}
    private static void focus(JsonNode n){Availability a=observation(n,"native_character_current_focus",Set.of(Status.AVAILABLE,Status.UNAVAILABLE));if(!a.available()){nilOptional(n,"presence","key");return;}String presence=text(n,"presence");need(Set.of("present","absent").contains(presence),"current child focus presence differs");if(presence.equals("present"))need(!text(n,"key").isEmpty(),"present native focus key absent");else nilOptional(n,"key");}
    private static List<Child> childInputs(JsonNode n,JsonNode descendants,List<Occurrence> occurrences){
        Availability a=observation(n,"native_current_heir_child_inputs",STATUSES);
        for(String key:List.of("native_revision","played_character_id","heir_character_id","date_raw"))need(Objects.equals(maybe(n,key),maybe(descendants,key)),"child inputs crossed descendant frame");
        List<JsonNode> rows=rows(n,"rows",256);
        if(n.has("typed_windows"))typedWindows(field(n,"typed_windows"),number(descendants,"native_revision",BigInteger.ONE,U64));
        if(n.has("character_window_identity"))characterWindow(field(n,"character_window_identity"));
        if(a.status()==Status.UNAVAILABLE){need(rows.isEmpty(),"unavailable child inputs contain rows");return List.of();}
        yes(descendants,"roster_complete");LinkedHashMap<Integer,List<BigInteger>> groups=new LinkedHashMap<>();
        for(Occurrence occurrence:occurrences)if(occurrence.generationValid()&&Boolean.TRUE.equals(occurrence.alive())&&Boolean.TRUE.equals(occurrence.childOfHeir()))
            groups.computeIfAbsent((int)occurrence.rawCharacterId(),ignored->new ArrayList<>()).add(BigInteger.valueOf(occurrence.index()));
        need(rows.size()==groups.size(),"selected child inputs omit complete occurrence groups");List<Child> children=new ArrayList<>();boolean all=true;int index=0;
        for(var entry:groups.entrySet()){
            JsonNode row=rows.get(index++);eq(row,"character_id",BigInteger.valueOf(entry.getKey()));
            List<BigInteger> indices=integers(row,"occurrence_indices",4096,BigInteger.ZERO,U32);need(indices.equals(entry.getValue()),"selected child occurrence order or duplicates differ");
            childValues(field(row,"values"));traits(field(row,"childhood_traits"),CHILDHOOD,false);
            if(row.has("education_point_traits"))traits(field(row,"education_point_traits"),POINT_TRAITS,false);
            if(row.has("education_traits"))traits(field(row,"education_traits"),EDUCATION_TRAITS,true);
            if(row.has("native_focus"))focus(field(row,"native_focus"));
            if(row.has("court_owner_source"))courtOwner(field(row,"court_owner_source"),entry.getKey(),number(n,"native_revision",BigInteger.ONE,U64));
            all&=equal(field(row,"values"),"status","available")&&equal(field(row,"childhood_traits"),"status","available");
            children.add(new Child(entry.getKey(),indices,retain(row)));
        }
        need(a.available()==all,"selected child input status differs from age/trait subreads");return List.copyOf(children);
    }
    static void courtOwner(JsonNode n,int child,BigInteger revision){
        if(absent(n))return;
        closed(n,"schema","status","unavailable_reason","child_character_id","native_revision","court_owner_present","court_owner_id","child_address","court_owner_address","getter_return_address","fallback_address","fallback_full_id_raw","relation_owner_id_raw","source_path","fallback_reached","getter_projection_complete","identity_round_trip","sample_stable","source_qualified");
        eq(n,"schema","xar.ck3.current-child-court-owner-readonly/1.20.0.4/v1");eq(n,"child_character_id",BigInteger.valueOf(Integer.toUnsignedLong(child)));eq(n,"native_revision",revision);
        String status=text(n,"status"),reason=text(n,"unavailable_reason"),path=text(n,"source_path");need(Set.of("resolved","known_null","unavailable").contains(status),"child court-owner status differs");
        for(String key:List.of("fallback_reached","getter_projection_complete","identity_round_trip","sample_stable","source_qualified"))bool(n,key);
        for(String key:List.of("court_owner_id","fallback_full_id_raw","relation_owner_id_raw"))optionalNumber(n,key,BigInteger.ZERO,U32);
        for(String key:List.of("child_address","court_owner_address","getter_return_address","fallback_address"))optionalNumber(n,key,BigInteger.ZERO,U64);
        Boolean present=optionalBoolean(n,"court_owner_present");BigInteger owner=optionalNumber(n,"court_owner_id",BigInteger.ZERO,U32),address=optionalNumber(n,"court_owner_address",BigInteger.ZERO,U64),childAddress=optionalNumber(n,"child_address",BigInteger.ZERO,U64);
        if(status.equals("unavailable")){need(!reason.isEmpty()&&!bool(n,"source_qualified")&&present==null&&owner==null&&address==null,"unavailable court owner became known");return;}
        need(reason.isEmpty()&&bool(n,"source_qualified")&&bool(n,"getter_projection_complete")&&bool(n,"identity_round_trip")&&bool(n,"sample_stable")&&childAddress!=null&&childAddress.signum()!=0&&child!=-1,"known court owner lacks actual current child bookends");
        if(status.equals("resolved")){
            need(Boolean.TRUE.equals(present)&&owner!=null&&!owner.equals(U32)&&address!=null&&address.signum()!=0&&Objects.equals(maybe(n,"getter_return_address"),maybe(n,"court_owner_address"))&&!bool(n,"fallback_reached")&&absent(maybe(n,"fallback_address"))&&absent(maybe(n,"fallback_full_id_raw"))&&Set.of("landed_noncharacter_context_returns_child","landed_invalid_context_returns_child","landed_character_context","unlanded_current_relation_owner").contains(path),"resolved court owner lost actual getter result");
            if(Set.of("landed_noncharacter_context_returns_child","landed_invalid_context_returns_child").contains(path))need(owner.equals(BigInteger.valueOf(Integer.toUnsignedLong(child)))&&address.equals(childAddress),"self court-owner result changed full identity");
        }else{
            BigInteger fallback=optionalNumber(n,"fallback_address",BigInteger.ZERO,U64);
            need(Boolean.FALSE.equals(present)&&owner==null&&address==null&&bool(n,"fallback_reached")&&fallback!=null&&Objects.equals(maybe(n,"getter_return_address"),maybe(n,"fallback_address"))&&Set.of("unlanded_relation_absent_fallback","unlanded_storage_null_fallback","unlanded_index_out_of_bounds_fallback","unlanded_object_null_fallback","unlanded_generation_mismatch_fallback").contains(path),"known-null court owner lacks completed fallback");
            need(fallback.signum()==0?absent(maybe(n,"fallback_full_id_raw")):equal(n,"fallback_full_id_raw",U32),"known-null court owner fallback identity differs");
        }
    }
    private static void typedWindows(JsonNode n,BigInteger revision){
        eq(n,"source","native_fixed_window_type_diagnostic");eq(n,"native_revision",revision);String status=text(n,"window_handler_status");need(Set.of("available","unavailable").contains(status),"window handler status differs");boolean handler=status.equals("available");need(handler?absent(maybe(n,"window_handler_unavailable_reason")):optionalString(n,"window_handler_unavailable_reason")!=null&&!text(n,"window_handler_unavailable_reason").isEmpty(),"window handler reason differs");
        List<JsonNode> rows=rows(n,"rows",7);need(rows.size()==7,"seven fixed typed window rows required");int[] types={13092,11010,11399,14350,14351,15450,10602};
        for(int i=0;i<rows.size();i++){
            JsonNode row=rows.get(i);eq(row,"slot_index",BigInteger.valueOf(i));eq(row,"handler_member_offset",BigInteger.valueOf(152+i*8));eq(row,"type_identifier",BigInteger.valueOf(types[i]));
            String named=text(row,"registered_name_status"),presence=text(row,"window_presence"),objectStatus=text(row,"object_type_status");
            need(Set.of("available","unavailable").contains(named)&&Set.of("present","absent","unavailable").contains(presence)&&Set.of("available","unavailable","not_applicable").contains(objectStatus),"window diagnostic state differs");
            boolean nameAvailable=named.equals("available");need(nameAvailable?absent(maybe(row,"registered_name_unavailable_reason"))&&optionalString(row,"registered_name")!=null:!text(row,"registered_name_unavailable_reason").isEmpty()&&absent(maybe(row,"registered_name")),"window registered name differs");
            for(String key:List.of("object_vtable_rva","object_col_rva","object_type_descriptor_rva"))optionalNumber(row,key,BigInteger.ZERO,U64);
            optionalString(row,"object_type_decorated_name");
            need((handler||presence.equals("unavailable"))&&(!presence.equals("absent")||objectStatus.equals("not_applicable"))&&(!presence.equals("unavailable")||objectStatus.equals("unavailable"))&&(!presence.equals("present")||!objectStatus.equals("not_applicable")),"window presence/type relation differs");
            need(objectStatus.equals("unavailable")?!text(row,"object_type_unavailable_reason").isEmpty():absent(maybe(row,"object_type_unavailable_reason")),"window object reason differs");
            if(objectStatus.equals("available"))for(String key:List.of("object_vtable_rva","object_col_rva","object_type_descriptor_rva","object_type_decorated_name"))need(!absent(maybe(row,key)),"available window RTTI incomplete");
            else if(!presence.equals("present"))nilOptional(row,"object_vtable_rva","object_col_rva","object_type_descriptor_rva","object_type_decorated_name");
        }
    }
    private static void characterWindow(JsonNode n){
        boolean receiver=bool(n,"receiver_available"),character=bool(n,"character_available");String receiverReason=text(n,"receiver_unavailable_reason"),characterReason=text(n,"character_unavailable_reason");BigInteger raw=optionalNumber(n,"raw_character_id",I32_MIN,I32_MAX),id=optionalNumber(n,"character_id",I32_MIN,I32_MAX);
        need(receiverReason.isEmpty()==receiver&&characterReason.isEmpty()==character&&(receiver||raw==null&&!character)&&(character?id!=null&&!id.equals(BigInteger.valueOf(-1))&&id.equals(raw):id==null),"CharacterWindow receiver and full identity states differ");
    }
    public static OpportunityJson.Obj summary(Observation observed){
        Objects.requireNonNull(observed);JsonNode original=nativeObject(observed.original);List<Occurrence> direct=observed.occurrences.stream().filter(row->Boolean.TRUE.equals(row.childOfHeir())).toList(),living=direct.stream().filter(row->Boolean.TRUE.equals(row.alive())).toList();
        boolean directComplete=observed.complete&&observed.occurrences.stream().allMatch(row->row.childOfHeir()!=null),livingComplete=directComplete&&direct.stream().allMatch(row->row.alive()!=null);
        ObjectNode out=F.objectNode().put("source","derived_native_descendant_roster").put("native_roster_status",observed.status()).put("roster_complete",observed.complete).put("known_direct_child_occurrence_count",direct.size()).put("direct_child_count_complete",directComplete).put("known_living_direct_child_occurrence_count",living.size()).put("living_direct_child_count_complete",livingComplete);
        ids(out,"known_direct_child_character_ids",direct);ids(out,"known_living_direct_child_character_ids",living);nullableTruth(out,"actual_direct_child_exists",!direct.isEmpty(),directComplete);nullableTruth(out,"living_actual_direct_child_exists",!living.isEmpty(),livingComplete);
        out.set("current_heir_dynasty_matches",dynasty(field(original,"heir_lineage"),living,livingComplete));out.set("played_dynasty_matches",dynasty(field(original,"played_lineage"),living,livingComplete));return retain(out);
    }
    private static void ids(ObjectNode out,String key,List<Occurrence> values){var a=out.putArray(key);values.stream().map(Occurrence::rawCharacterId).distinct().forEach(a::add);}
    private static void nullableTruth(ObjectNode out,String key,boolean any,boolean complete){if(any||complete)out.put(key,any);else out.putNull(key);}
    private static ObjectNode dynasty(JsonNode reference,List<Occurrence> living,boolean livingComplete){
        JsonNode dynasty=maybe(reference,"dynasty_id_raw");boolean available=equal(reference,"status","available");ObjectNode out=F.objectNode();out.set("reference_dynasty_id_raw",dynasty==null?F.nullNode():dynasty);
        if(!available||equal(reference,"dynasty_id_raw",BigInteger.valueOf(-1))){out.put("status",available?"not_applicable":"unavailable");JsonNode reason=maybe(reference,"unavailable_reason");out.set("unavailable_reason",reason==null?F.nullNode():reason);out.putNull("known_living_direct_child_occurrence_count").putNull("known_living_direct_child_character_ids").put("all_living_direct_children_classified",false).putNull("living_direct_child_exists");return out;}
        List<Occurrence> matches=living.stream().filter(row->{JsonNode lineage=field(nativeObject(row.original()),"lineage");return equal(lineage,"status","available")&&Objects.equals(maybe(lineage,"dynasty_id_raw"),dynasty);}).toList();boolean classified=livingComplete&&living.stream().allMatch(row->equal(field(nativeObject(row.original()),"lineage"),"status","available"));
        out.put("status",classified?"available":"partial").putNull("unavailable_reason").put("known_living_direct_child_occurrence_count",matches.size()).put("all_living_direct_children_classified",classified);ids(out,"known_living_direct_child_character_ids",matches);nullableTruth(out,"living_direct_child_exists",!matches.isEmpty(),classified);return out;
    }
}
