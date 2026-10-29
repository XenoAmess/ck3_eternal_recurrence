package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRelationJson.*;

/** Same-query, source-qualified native child trait/culture observations; every unobserved educator value stays null. */
public final class FamilyRelationEducationProvider {
    public static final String LEAF="current_child_education_provider_inputs_v1",SOURCE_LEAF="current_child_education_provider_inputs_source_v1";
    private FamilyRelationEducationProvider() { }
    public enum State { AVAILABLE,PARTIAL,UNAVAILABLE }
    public record Child(long fullId,List<BigInteger> occurrenceIndices,boolean traitsAvailable,boolean cultureAvailable,OpportunityJson.Obj original){
        public Child{occurrenceIndices=List.copyOf(occurrenceIndices);Objects.requireNonNull(original);}
    }
    public static final class Observation{
        private final State state;private final List<Child> children;private final OpportunityJson.Obj original;
        private Observation(State state,List<Child> children,JsonNode original){this.state=state;this.children=List.copyOf(children);this.original=retain(original);}
        public State state(){return state;}public List<Child> children(){return children;}public OpportunityJson.Obj original(){return original;}
    }
    public static Optional<Observation> decode(JsonNode n,JsonNode family,boolean qualified,String requestId,BigInteger revision,long actor,long nativeHeir,BigInteger date){
        if(absent(n))return Optional.empty();
        closed(n,"schema_version","read_only","source","request_id","native_revision","date_raw","played_character_full_id","heir_character_full_id","status","unavailable_reason","roster_complete","collection_available","child_observation_complete","m6_inputs_complete","guardian_role_equivalence_qualified","queried_education_trait_keys","rows");
        need(n.toString().getBytes(StandardCharsets.UTF_8).length<=65536,"native education provider exceeds its 65536-byte UTF8 bound");need(qualified,"education provider lacks qualified actual same-query source");
        field(family,"heir_character_id");BigInteger heir=optionalNumber(family,"heir_character_id",I32_MIN,I32_MAX);need((heir==null?-1:heir.longValueExact())==nativeHeir,"education provider normalized heir differs");
        eq(n,"schema_version",BigInteger.ONE);yes(n,"read_only");eq(n,"source","same_query_actual4_child_education_inputs");no(n,"m6_inputs_complete");no(n,"guardian_role_equivalence_qualified");
        need(requestId!=null&&!requestId.isEmpty(),"education provider actual request is absent");eq(n,"request_id",requestId);eq(n,"native_revision",revision);need(revision.signum()>0&&revision.compareTo(U64)<=0,"positive native revision required");
        eq(n,"date_raw",range(date,I64_MIN,I64_MAX));eq(n,"played_character_full_id",BigInteger.valueOf(fullBits(BigInteger.valueOf(actor))));eq(n,"heir_character_full_id",BigInteger.valueOf(fullBits(BigInteger.valueOf(nativeHeir))));
        need(strings(n,"queried_education_trait_keys",25).equals(FamilyRelationDescendants.EDUCATION_TRAITS),"education provider queried trait catalog differs");
        Availability a=FamilyRelationJson.availability(n,Set.of(Status.AVAILABLE,Status.PARTIAL,Status.UNAVAILABLE));
        boolean roster=bool(n,"roster_complete"),collection=bool(n,"collection_available"),complete=bool(n,"child_observation_complete");List<JsonNode> rows=rows(n,"rows",256);
        need(a.status()==Status.AVAILABLE?roster&&collection&&complete:a.status()==Status.PARTIAL?roster&&collection&&!complete:!roster&&!collection&&!complete,"education provider status/completeness differs");
        if(a.status()==Status.UNAVAILABLE){need(rows.isEmpty(),"unavailable education provider acquired children");return Optional.of(new Observation(State.UNAVAILABLE,List.of(),n));}
        if(a.status()==Status.PARTIAL)eq(n,"unavailable_reason","education_child_inputs_partially_observed");
        LinkedHashMap<Long,List<BigInteger>> expected=expectedChildren(family,revision,actor,nativeHeir,date);need(rows.size()==expected.size(),"education provider selected child inventory incomplete");
        List<Child> children=new ArrayList<>();boolean all=true;int i=0;
        for(var entry:expected.entrySet()){
            JsonNode row=rows.get(i++);closed(row,"child_full_id","role_source","occurrence_indices","education_traits","culture_parameter","guardian_full_id","guardian_culture_parameter","guardian_unavailable_reason","rite_parameters","rite_unavailable_reason","education_type","education_progress","education_variables_unavailable_reason");
            eq(row,"child_full_id",BigInteger.valueOf(entry.getKey()));eq(row,"role_source","current_living_actual_child_of_first_heir");List<BigInteger> indices=indices(row,"occurrence_indices");need(indices.equals(entry.getValue()),"education child occurrence group differs");
            nil(row,"guardian_full_id","guardian_culture_parameter","rite_parameters","education_type","education_progress");
            eq(row,"guardian_unavailable_reason","authoritative_educator_identity_not_observed");eq(row,"rite_unavailable_reason","target_rite_education_parameters_not_observed");eq(row,"education_variables_unavailable_reason","typed_target_variable_value_access_not_wired");
            boolean traits=traits(field(row,"education_traits")),culture=culture(field(row,"culture_parameter"));all&=traits&&culture;children.add(new Child(entry.getKey(),indices,traits,culture,retain(row)));
        }
        need(a.available()==all,"education provider status differs from independent trait/culture reads");return Optional.of(new Observation(all?State.AVAILABLE:State.PARTIAL,children,n));
    }
    private static LinkedHashMap<Long,List<BigInteger>> expectedChildren(JsonNode family,BigInteger revision,long actor,long nativeHeir,BigInteger date){
        JsonNode descendants=field(family,FamilyRelationDescendants.LEAF),inputs=field(descendants,"child_inputs");
        need(Set.of("available","partial").contains(text(inputs,"status"))&&equal(descendants,"status","available")&&bool(descendants,"roster_complete")&&bool(descendants,"family_present"),"education provider lacks complete same-query descendant roster");
        for(JsonNode n:List.of(descendants,inputs)){eq(n,"native_revision",revision);eq(n,"played_character_id",BigInteger.valueOf(actor));eq(n,"date_raw",date);need(equal(n,"heir_character_id",nativeHeir==-1?null:BigInteger.valueOf(nativeHeir)),"education provider descendant heir binding differs");}
        List<JsonNode> occurrences=rows(descendants,"rows",4096);int count=integer(descendants,"native_child_count_raw",0,4096);boolean pointer=bool(descendants,"data_pointer_present");need(occurrences.size()==count&&(count==0||pointer),"education provider raw roster proof incomplete");
        LinkedHashMap<Long,List<BigInteger>> groups=new LinkedHashMap<>();java.util.Map<Long,List<Boolean>> classifications=new java.util.HashMap<>();
        for(int index=0;index<occurrences.size();index++){
            JsonNode row=occurrences.get(index);eq(row,"occurrence_index",BigInteger.valueOf(index));long raw=number(row,"raw_character_id",BigInteger.ZERO,U32).longValueExact();yes(row,"generation_valid");boolean alive=bool(row,"alive");Boolean child=optionalBoolean(row,"child_of_heir");need(!alive||child!=null,"education child classification unavailable");
            List<Boolean> classification=List.of(alive,alive&&Boolean.TRUE.equals(child));List<Boolean> previous=classifications.putIfAbsent(raw,classification);need(previous==null||previous.equals(classification),"duplicate education occurrence classification changed");
            if(alive&&Boolean.TRUE.equals(child))groups.computeIfAbsent(raw,ignored->new ArrayList<>()).add(BigInteger.valueOf(index));
        }
        List<JsonNode> selected=rows(inputs,"rows",256);need(selected.size()==groups.size(),"education selected child roster incomplete");int index=0;
        for(var entry:groups.entrySet()){
            JsonNode row=selected.get(index++);need(fullBits(number(row,"character_id",I32_MIN,I32_MAX))==entry.getKey(),"education selected child order/full generation differs");need(indices(row,"occurrence_indices").equals(entry.getValue()),"education selected occurrence group differs");
        }
        return groups;
    }
    private static boolean traits(JsonNode n){
        closed(n,"available","unavailable_reason","present_trait_keys");boolean available=bool(n,"available");if(available){nil(n,"unavailable_reason");List<String> present=strings(n,"present_trait_keys",25);need(present.equals(FamilyRelationDescendants.EDUCATION_TRAITS.stream().filter(present::contains).toList()),"education trait subset/order differs");}else{boundedReason(n,"unavailable_reason");nil(n,"present_trait_keys");}return available;
    }
    private static boolean culture(JsonNode n){
        closed(n,"key","available","culture_full_id","value","unavailable_reason");eq(n,"key","better_ward_education");boolean available=bool(n,"available");BigInteger culture=nullableNumberRequired(n,"culture_full_id",BigInteger.ZERO,U32);
        if(available){need(culture!=null,"available education culture lacks current full ID");bool(n,"value");nil(n,"unavailable_reason");}else{boundedReason(n,"unavailable_reason");nil(n,"value");}return available;
    }
}
