package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Four original optional route families. Observations grant no Move, actual loss or unobserved Q result. */
public final class ArmyRouteOptionalCodec {
    private ArmyRouteOptionalCodec() { }
    private static final BigInteger I64_MIN=BigInteger.valueOf(Long.MIN_VALUE),I64_MAX=BigInteger.valueOf(Long.MAX_VALUE),
            U64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE,TRUNCATED }
    /** Missing and observed JSON null remain different, including optional child families. */
    public sealed interface Field<T> permits Missing,ObservedNull,Present { }
    public record Missing<T>() implements Field<T> { }
    public record ObservedNull<T>() implements Field<T> { }
    public record Present<T>(T value) implements Field<T> { public Present { Objects.requireNonNull(value); } }
    public record NativeIdentity(String value) {
        public NativeIdentity {
            need(value!=null&&value.matches("native:[1-9][0-9]*"),"canonical opaque native identity required");
            BigInteger exact=new BigInteger(value.substring(7));need(exact.signum()>0&&exact.compareTo(U64_MAX)<=0,"native identity outside uint64");
        }
    }
    public record LossOperands(Status status,boolean ready,String reason,Boolean fallback,Integer rawCommander,Integer resolvedCommander,
            BigInteger commanderModifier,BigInteger excessSlope,BigInteger minimumLoss,BigInteger maximumLoss,BigInteger divisorFloor) { }
    public record Supply(Status status,Integer army,Integer carmy,Integer owner,Integer province,BigInteger componentRaw,BigInteger loadedGainRaw,
            Boolean componentApplicable,Boolean resupplyEligible,boolean ready,boolean componentReady,boolean resupplyReady,
            String reason,String componentReason,String resupplyReason,Field<LossOperands> loss) { public Supply { Objects.requireNonNull(loss); } }
    public record AdjacencyRow(int occurrence,int targetProvince) { }
    public record OriginAdjacency(Status status,String reason,int sourceProvince,NativeIdentity sourceIdentity,NativeIdentity nodeIdentity,
            NativeIdentity dataIdentity,Integer nativeCount,int observedCount,boolean complete,boolean truncated,boolean stable,
            List<AdjacencyRow> rows) { public OriginAdjacency { if(rows!=null)rows=List.copyOf(rows); } }
    public record Relation(Status status,String reason,long count,boolean argumentMatched,boolean sameThread,Boolean stable,
            BigInteger actualReturn,Long receiver,Long actor,Boolean returned,NativeIdentity auxiliary,
            boolean sampleAvailable,String sampleReason,NativeIdentity relationIdentity,Integer warId,NativeIdentity selectedWar,
            Boolean selectedFallback,Integer selectedByte,Boolean matchesAuxiliary,Boolean directGate) { }
    public record Stage(long count,BigInteger actualReturn,Boolean argumentMatched,Boolean returned,Optional<Relation> relation) {
        public Stage { Objects.requireNonNull(relation); }
    }
    public record Trace(Status status,String reason,boolean hookInstalled,boolean scopeEntered,boolean sameThread,boolean orderValid,
            boolean predicateReturned,Boolean finalPasses,long ignoredForeign,long ignoredNested,List<Stage> stages) {
        public Trace { stages=List.copyOf(stages); }
    }
    public record County(Status status,String reason,Integer army,Integer requestedTarget,Integer sourceProvince,Integer targetProvince,
            Integer carmy,Integer actor,Integer mode,Integer army1d4,Integer sourceDefinition,Integer targetDefinition,Long targetMagic,
            Boolean sourcePresent,Boolean targetPresent,Boolean objectsDiffer,Boolean passes,boolean inputsReady,boolean called,boolean stable,
            boolean internalsObserved,NativeIdentity sourceCounty,NativeIdentity targetCounty,Field<OriginAdjacency> adjacency,
            Optional<Trace> trace) { public County { Objects.requireNonNull(adjacency);Objects.requireNonNull(trace); } }
    public record Decoded(OpportunityJson.Obj original,Field<Supply> capturedSupply,Field<County> county) {
        public Decoded { Objects.requireNonNull(original);Objects.requireNonNull(capturedSupply);Objects.requireNonNull(county); }
    }
    /** Preserve all legacy/optional bytes in the immutable JSON type domain after complete child validation. */
    public static OpportunityJson.Obj normalize(OpportunityJson.Obj completeNativeRoutePreview) { return decode(completeNativeRoutePreview).original(); }
    public static Decoded decode(OpportunityJson.Obj completeNativeRoutePreview) {
        Objects.requireNonNull(completeNativeRoutePreview);JsonNode preview=OpportunityJson.toNode(completeNativeRoutePreview);
        Field<Supply> supply=new Missing<>();JsonNode provinceSupply=preview.get("province_supply");
        JsonNode target=provinceSupply!=null&&provinceSupply.isObject()?provinceSupply.get("target"):null;
        if(target!=null&&target.isObject()&&target.has("captured_target_land_supply_inputs_v1")) {
            supply=nullable(target.get("captured_target_land_supply_inputs_v1"),ArmyRouteOptionalCodec::supply);
            if(supply instanceof Present<Supply> observed) {
                Supply family=observed.value();
                bound(family.army(),preview.get("army_id"));bound(family.carmy(),provinceSupply.get("native_carmy_id"));
                bound(family.owner(),provinceSupply.get("owner_character_id"));bound(family.province(),target.get("province_id"));
                eqText(target,"role","target");need(Objects.equals(target.get("province_id"),preview.get("target_province_id")),"captured supply target Province differs from requested target");
            }
        }
        Field<County> county=new Missing<>();
        if(preview.has("county_entry_condition_v1")) {
            county=nullable(preview.get("county_entry_condition_v1"),ArmyRouteOptionalCodec::county);
            if(county instanceof Present<County> observed) {
                County family=observed.value();JsonNode route=preview.get("route_province_ids");need(route!=null&&route.isArray(),"county preview requires actual route");
                int first=!route.isEmpty()&&Objects.equals(route.get(0),preview.get("origin_province_id"))?1:0;
                JsonNode expected=first<route.size()?route.get(first):null;
                exactBound(family.army(),preview.get("army_id"));exactBound(family.requestedTarget(),preview.get("target_province_id"));
                exactBound(family.sourceProvince(),preview.get("origin_province_id"));exactBound(family.targetProvince(),expected);
                need(expected!=null&& !expected.isNull()||family.status()!=Status.AVAILABLE,"county preview without remaining edge cannot be available");
            }
        }
        return new Decoded(completeNativeRoutePreview,supply,county);
    }
    private static final Set<String> SUPPLY_KEYS=Set.of("source","input_basis","scale","status","subject_army_id","subject_carmy_id","owner_character_id","province_id",
            "province_component_raw","loaded_gain_raw","native_province_component_applicable","native_resupply_eligible","current_inputs_ready",
            "province_component_observation_ready","resupply_observation_ready","unavailable_reason","province_component_unavailable_reason","resupply_unavailable_reason");
    private static Supply supply(JsonNode n) {
        closed(n,SUPPLY_KEYS,Set.of("loss_adjustment_operands_v1"));eqText(n,"source","native_captured_target_land_supply_inputs");
        eqText(n,"input_basis","captured_owner_and_target_province");constant(n,"scale",100000);
        Integer army=i32(n,"subject_army_id"),carmy=i32(n,"subject_carmy_id"),owner=i32(n,"owner_character_id"),province=i32(n,"province_id");
        BigInteger raw=i64(n,"province_component_raw"),gain=i64(n,"loaded_gain_raw");
        Boolean applicable=optionalBool(n,"native_province_component_applicable"),eligible=optionalBool(n,"native_resupply_eligible");
        boolean ready=bool(n,"current_inputs_ready"),component=bool(n,"province_component_observation_ready"),resupply=bool(n,"resupply_observation_ready");
        String reason=reason(n,"unavailable_reason"),componentReason=reason(n,"province_component_unavailable_reason"),resupplyReason=reason(n,"resupply_unavailable_reason");
        Status status=status(n);need(ready==(component&&resupply)&&status==(ready?Status.AVAILABLE:component||resupply?Status.PARTIAL:Status.UNAVAILABLE),"captured supply status/readiness differ");
        if(component)need(componentReason==null&&applicable!=null&&raw!=null,"ready target component requires operands and null reason");
        else need(componentReason!=null,"unavailable target component requires reason");
        if(resupply)need(resupplyReason==null&&eligible!=null,"ready target resupply requires operand and null reason");
        else need(resupplyReason!=null,"unavailable target resupply requires reason");
        if(component&&Boolean.FALSE.equals(applicable))need(BigInteger.ZERO.equals(raw),"false target component requires native zero");
        need(Objects.equals(reason,ready?null:componentReason!=null?componentReason:resupplyReason),"captured supply reason differs from branch reasons");
        if(component||resupply)need(army!=null&&carmy!=null&&owner!=null&&province!=null,"ready supply branch requires actual IDs");
        Field<LossOperands> loss=n.has("loss_adjustment_operands_v1")?nullable(n.get("loss_adjustment_operands_v1"),ArmyRouteOptionalCodec::loss):new Missing<>();
        return new Supply(status,army,carmy,owner,province,raw,gain,applicable,eligible,ready,component,resupply,reason,componentReason,resupplyReason,loss);
    }
    private static LossOperands loss(JsonNode n) {
        closed(n,Set.of("source","scale","status","observation_ready","unavailable_reason","commander_used_native_fallback","commander_raw_full_id","commander_resolved_full_id",
                "commander_modifier_1a9_raw","loaded_excess_slope_raw","loaded_min_loss_raw","loaded_max_loss_raw","loaded_divisor_floor_raw"),Set.of());
        eqText(n,"source","native_captured_target_loss_operands");constant(n,"scale",100000);Status status=status(n);
        boolean ready=bool(n,"observation_ready");Boolean fallback=optionalBool(n,"commander_used_native_fallback");String reason=reason(n,"unavailable_reason");
        Integer raw=i32(n,"commander_raw_full_id"),resolved=i32(n,"commander_resolved_full_id");
        BigInteger modifier=i64(n,"commander_modifier_1a9_raw"),slope=i64(n,"loaded_excess_slope_raw"),minimum=i64(n,"loaded_min_loss_raw"),
                maximum=i64(n,"loaded_max_loss_raw"),floor=i64(n,"loaded_divisor_floor_raw");
        if(ready)need(status==Status.AVAILABLE&&reason==null&&fallback!=null&&raw!=null&&resolved!=null&&modifier!=null&&slope!=null&&minimum!=null&&maximum!=null&&floor!=null,"ready target loss operands incomplete");
        else need(status==Status.UNAVAILABLE&&reason!=null,"unavailable target loss operands require reason");
        if(modifier!=null)need(fallback!=null&&raw!=null&&resolved!=null,"observed target modifier requires commander witness");
        if(Boolean.FALSE.equals(fallback)&&resolved!=null)need(Objects.equals(raw,resolved),"commander FullIDs differ without native fallback");
        return new LossOperands(status,ready,reason,fallback,raw,resolved,modifier,slope,minimum,maximum,floor);
    }
    private static OriginAdjacency adjacency(JsonNode n,Integer expectedSource) {
        closed(n,Set.of("schema_version","source","input_basis","status","unavailable_reason","source_province_id","source_province_identity","source_map_node_identity",
                "adjacency_data_identity","native_count","published_row_limit","observed_count","collection_complete","truncated","identity_before_after_match","rows",
                "native_condition_evaluated_for_rows","route_legality_evaluated_for_rows"),Set.of());
        constant(n,"schema_version",1);eqText(n,"source","native_origin_province_map_node_rows_12004");eqText(n,"input_basis","preview_origin_province_native_adjacency_rows");
        int source=requiredI32(n,"source_province_id");need(source>0&&Objects.equals(source,expectedSource),"origin adjacency differs from preview origin");
        NativeIdentity sourceIdentity=identity(n,"source_province_identity"),nodeIdentity=identity(n,"source_map_node_identity"),dataIdentity=identity(n,"adjacency_data_identity");
        Integer count=i32(n,"native_count");constant(n,"published_row_limit",64);int observed=integer(n,"observed_count",0,64).intValueExact();
        boolean complete=bool(n,"collection_complete"),truncated=bool(n,"truncated"),stable=bool(n,"identity_before_after_match");
        need(!bool(n,"native_condition_evaluated_for_rows")&&!bool(n,"route_legality_evaluated_for_rows"),"origin rows do not evaluate route legality or native county condition");
        Status status=status(n);String reason=reason(n,"unavailable_reason");JsonNode rows=field(n,"rows");
        if(status==Status.UNAVAILABLE) {
            need(reason!=null&&rows.isNull()&&observed==0&&!complete&&!truncated&&!stable,"unavailable adjacency requires unknown rows and explicit reason");
            return new OriginAdjacency(status,reason,source,sourceIdentity,nodeIdentity,dataIdentity,count,observed,complete,truncated,stable,null);
        }
        need(status==Status.AVAILABLE||status==Status.TRUNCATED,"origin adjacency status malformed");
        need(stable&&count!=null&&count>=0&&sourceIdentity!=null&&nodeIdentity!=null&&rows.isArray()&&observed==rows.size()&&observed==Math.min(count,64),"readable origin adjacency lacks stable complete prefix arithmetic");
        need(count==0?dataIdentity==null:dataIdentity!=null,"origin adjacency data pointer differs from empty/nonempty count");
        boolean expectedTruncated=count>64;need(truncated==expectedTruncated&&complete==!expectedTruncated
                &&status==(expectedTruncated?Status.TRUNCATED:Status.AVAILABLE)
                &&Objects.equals(reason,expectedTruncated?"origin_adjacency_row_budget_exhausted":null),"origin adjacency completeness differs from native count");
        List<AdjacencyRow> parsed=new ArrayList<>();for(int index=0;index<rows.size();index++) {
            JsonNode row=rows.get(index);closed(row,Set.of("occurrence_index","target_province_id"),Set.of());constant(row,"occurrence_index",index);
            int target=requiredI32(row,"target_province_id");need(target>0,"positive origin neighbor Province required");parsed.add(new AdjacencyRow(index,target));
        }
        return new OriginAdjacency(status,reason,source,sourceIdentity,nodeIdentity,dataIdentity,count,observed,complete,truncated,stable,parsed);
    }
    private static final Set<String> COUNTY_KEYS=Set.of("schema_version","source","input_basis","predicate_rva","status","unavailable_reason","target_county_magic_3e0_u32",
            "subject_army_id","requested_target_province_id","source_province_id","target_province_id","native_carmy_id","actor_character_id","mode","army_1d4_raw",
            "source_definition_1b_u8","target_definition_1b_u8","source_county_present","target_county_present","county_objects_differ","native_condition_passes",
            "inputs_observation_ready","native_condition_called","identity_before_after_match","internal_subpredicates_observed","actual_loss_observed","source_county_identity","target_county_identity");
    private static County county(JsonNode n) {
        closed(n,COUNTY_KEYS,Set.of("predicate_trace_v1","origin_adjacency_v1"));constant(n,"schema_version",1);
        eqText(n,"source","native_preview_first_edge_county_entry_condition");eqText(n,"input_basis","current_unit_and_preview_first_remaining_province");constant(n,"predicate_rva",0x24E2230);
        Integer army=i32(n,"subject_army_id"),requested=i32(n,"requested_target_province_id"),source=i32(n,"source_province_id"),target=i32(n,"target_province_id"),
                carmy=i32(n,"native_carmy_id"),actor=i32(n,"actor_character_id"),mode=i32(n,"mode"),army1d4=u8(n,"army_1d4_raw"),sourceDef=u8(n,"source_definition_1b_u8"),targetDef=u8(n,"target_definition_1b_u8");
        Long magic=u32(n,"target_county_magic_3e0_u32");Boolean sourcePresent=optionalBool(n,"source_county_present"),targetPresent=optionalBool(n,"target_county_present"),
                differ=optionalBool(n,"county_objects_differ"),passes=optionalBool(n,"native_condition_passes");
        boolean ready=bool(n,"inputs_observation_ready"),called=bool(n,"native_condition_called"),stable=bool(n,"identity_before_after_match"),internals=bool(n,"internal_subpredicates_observed");
        need(!bool(n,"actual_loss_observed"),"county preview does not observe actual loss");
        NativeIdentity sourceCounty=identity(n,"source_county_identity"),targetCounty=identity(n,"target_county_identity");Status status=status(n);String reason=reason(n,"unavailable_reason");
        if(ready&&called&&stable)need(status==Status.AVAILABLE&&reason==null&&passes!=null,"available county preview requires returned native boolean");
        else need(status==Status.UNAVAILABLE&&reason!=null&&passes==null&&!stable,"unavailable county preview requires reason and unknown native result");
        if(ready) {
            need(army!=null&&requested!=null&&source!=null&&target!=null&&carmy!=null&&actor!=null&&mode!=null&&army1d4!=null&&sourceDef!=null&&targetDef!=null
                    &&sourcePresent!=null&&targetPresent!=null&&differ!=null,"ready county preview requires all actual gate inputs");
            need(mode==(army1d4==0?1:0),"county mode differs from raw Army1D4");
            need(sourcePresent==(sourceCounty!=null)&&targetPresent==(targetCounty!=null)&&differ!=Objects.equals(sourceCounty,targetCounty),"county pointer presence/comparison differs");
            need(targetPresent==(magic!=null),"target magic availability differs from county pointer");
        }
        if(Boolean.TRUE.equals(passes))need(sourceDef!=null&&sourceDef!=0&&targetDef!=null&&targetDef!=0&&Boolean.TRUE.equals(sourcePresent)
                &&Boolean.TRUE.equals(targetPresent)&&Boolean.TRUE.equals(differ)&&Long.valueOf(0x436F4461L).equals(magic),"native true contradicts source-proven common gates");
        Field<OriginAdjacency> origin=n.has("origin_adjacency_v1")?nullable(n.get("origin_adjacency_v1"),child->adjacency(child,source)):new Missing<>();
        Optional<Trace> trace=n.has("predicate_trace_v1")?Optional.of(trace(n.get("predicate_trace_v1"),n)):Optional.empty();
        boolean observed=trace.filter(value->value.status()==Status.AVAILABLE).stream().flatMap(value->value.stages().stream()).anyMatch(stage->stage.count()==1);
        need(internals==observed,"county internal observation flag differs from actual P trace");
        return new County(status,reason,army,requested,source,target,carmy,actor,mode,army1d4,sourceDef,targetDef,magic,sourcePresent,targetPresent,differ,passes,ready,called,stable,internals,sourceCounty,targetCounty,origin,trace);
    }
    private static Trace trace(JsonNode n,JsonNode parent) {
        closed(n,Set.of("schema_version","source","status","unavailable_reason","hook_installed","scope_entered","same_thread","order_valid","native_predicate_returned",
                "final_condition_passes","ignored_foreign_calls","ignored_nested_calls","stages","additional_native_predicate_calls","neighbor_Q_observed"),Set.of());
        constant(n,"schema_version",1);eqText(n,"source","same_preview_native_P_returns_12004");constant(n,"additional_native_predicate_calls",0);
        need(!bool(n,"neighbor_Q_observed"),"county P trace does not observe neighbor Q");
        boolean hook=bool(n,"hook_installed"),scope=bool(n,"scope_entered"),thread=bool(n,"same_thread"),ordered=bool(n,"order_valid"),returned=bool(n,"native_predicate_returned");
        long foreign=requiredU32(n,"ignored_foreign_calls"),nested=requiredU32(n,"ignored_nested_calls");Boolean finalPasses=optionalBool(n,"final_condition_passes");
        if(finalPasses!=null)need(Objects.equals(finalPasses,optionalBool(parent,"native_condition_passes")),"county trace final boolean differs from native parent");
        JsonNode rows=field(n,"stages");need(rows.isArray()&&rows.size()==3,"county P trace requires three fixed stages");
        List<Stage> stages=new ArrayList<>();long[] sites={0x24E22B3L,0x24E22F1L,0x24E2348L};
        for(int index=0;index<3;index++) {
            JsonNode row=rows.get(index);closed(row,Set.of("call_count","actual_caller_return_rva","argument_identity_matched","returned"),Set.of("relation_inputs_v1"));
            long count=requiredU32(row,"call_count");Boolean matched=optionalBool(row,"argument_identity_matched"),value=optionalBool(row,"returned");
            BigInteger actual=nullableNumber(row,"actual_caller_return_rva",BigInteger.ZERO,U64_MAX);
            if(count==0)need(actual==null&&matched==null&&value==null,"uncalled county stage has no caller/arguments/result");
            else need(BigInteger.valueOf(sites[index]).equals(actual),"county P caller return differs from native source");
            Optional<Relation> relation=row.has("relation_inputs_v1")?Optional.of(relation(row.get("relation_inputs_v1"),row)):Optional.empty();
            stages.add(new Stage(count,actual,matched,value,relation));
        }
        Status status=status(n);String reason=reason(n,"unavailable_reason");
        if(status==Status.AVAILABLE) {
            need(reason==null&&hook&&scope&&thread&&ordered&&returned&&status(parent)==Status.AVAILABLE&&Integer.valueOf(1).equals(i32(parent,"mode"))&&finalPasses!=null,"available P trace requires complete same-preview mode1 evidence");
            for(Stage stage:stages)need(stage.count()<=1&&(stage.count()==0||stage.returned()!=null&&Boolean.TRUE.equals(stage.argumentMatched())),"available P stage requires one complete original return");
            boolean[] expected={nonzero(u8(parent,"source_definition_1b_u8"))&&nonzero(u8(parent,"target_definition_1b_u8"))&&Boolean.TRUE.equals(optionalBool(parent,"source_county_present"))&&Boolean.TRUE.equals(optionalBool(parent,"county_objects_differ")),
                    Boolean.TRUE.equals(stages.get(0).returned())&&Boolean.TRUE.equals(optionalBool(parent,"target_county_present")),
                    Boolean.TRUE.equals(stages.get(1).returned())&&Long.valueOf(0x436F4461L).equals(u32(parent,"target_county_magic_3e0_u32"))};
            for(int index=0;index<3;index++)need((stages.get(index).count()==1)==expected[index],"P trace differs from source short-circuit order");
            if(finalPasses)need(stages.stream().allMatch(stage->Boolean.TRUE.equals(stage.returned())),"native true contradicts actual P returns");
        } else need(status==Status.UNAVAILABLE&&reason!=null,"unavailable P trace requires reason");
        return new Trace(status,reason,hook,scope,thread,ordered,returned,finalPasses,foreign,nested,stages);
    }
    private static Relation relation(JsonNode n,JsonNode parent) {
        closed(n,Set.of("schema_version","source","status","unavailable_reason","call_count","actual_bridge_caller_return_rva","receiver_full_id","actor_full_id",
                "sampled_relation_full_war_id","sampled_selected_war_byte_358_u8","sampled_relation_unavailable_reason","argument_identity_matched","same_thread","sampled_relation_available","unknown_or_inputs",
                "identity_before_after_match","returned","sampled_selected_war_used_fallback","sampled_direct_war_matches_aux","sampled_direct_war_gate","auxiliary_identity","sampled_relation_identity","sampled_selected_war_identity"),Set.of());
        constant(n,"schema_version",1);eqText(n,"source","native_original_relation_entry_return_12004");
        boolean matched=bool(n,"argument_identity_matched"),thread=bool(n,"same_thread"),sample=bool(n,"sampled_relation_available");need(bool(n,"unknown_or_inputs"),"unobserved relation OR inputs must stay unknown");
        Boolean stable=optionalBool(n,"identity_before_after_match"),returned=optionalBool(n,"returned"),fallback=optionalBool(n,"sampled_selected_war_used_fallback"),
                matches=optionalBool(n,"sampled_direct_war_matches_aux"),gate=optionalBool(n,"sampled_direct_war_gate");
        long count=requiredU32(n,"call_count");Long receiver=u32(n,"receiver_full_id"),actor=u32(n,"actor_full_id");
        BigInteger actual=nullableNumber(n,"actual_bridge_caller_return_rva",BigInteger.ZERO,U64_MAX);Integer war=i32(n,"sampled_relation_full_war_id"),selectedByte=u8(n,"sampled_selected_war_byte_358_u8");
        NativeIdentity auxiliary=identity(n,"auxiliary_identity"),relation=identity(n,"sampled_relation_identity"),selected=identity(n,"sampled_selected_war_identity");
        Status status=status(n);String reason=reason(n,"unavailable_reason"),sampleReason=reason(n,"sampled_relation_unavailable_reason");
        if(status==Status.AVAILABLE) {
            need(reason==null&&count==1&&matched&&thread&&Boolean.TRUE.equals(stable)&&actual!=null&&receiver!=null&&actor!=null&&returned!=null,"available relation needs one stable original return");
            if(receiver.equals(actor))need(Boolean.FALSE.equals(returned),"same FullID native relation immediately returns false");
            need(requiredU32(parent,"call_count")==1&&Boolean.TRUE.equals(optionalBool(parent,"argument_identity_matched"))&&Objects.equals(returned,optionalBool(parent,"returned")),"relation original return differs from enclosing P stage");
        } else need(status==Status.UNAVAILABLE&&reason!=null,"unavailable relation requires reason");
        if(sample) {
            need(sampleReason==null&&gate!=null&&relation!=null&&war!=null,"available pure relation sample requires direct gate/identity/full WarID");
            need(receiver==null||!receiver.equals(actor),"same FullID native early return skips relation sampler");
            if(war==-1)need(Boolean.FALSE.equals(gate)&&selected==null&&fallback==null&&selectedByte==null&&matches==null,"sentinel pair WarID skips selected War and has false gate");
            else {
                need(selected!=null&&fallback!=null&&selectedByte!=null&&matches!=null,"direct War sample requires complete selected operands");
                boolean expected=auxiliary==null||auxiliary.equals(selected);need(matches==expected,"sampled auxiliary comparison differs from identities");
                need(gate==(selectedByte==0&&expected),"direct gate differs from actual selected War operands");
            }
        } else need(sampleReason!=null,"unavailable pure relation sample requires its own reason");
        if(count==0)need(actual==null&&receiver==null&&actor==null&&auxiliary==null&&returned==null,"uncalled relation has no actual arguments/return");
        return new Relation(status,reason,count,matched,thread,stable,actual,receiver,actor,returned,auxiliary,sample,sampleReason,relation,war,selected,fallback,selectedByte,matches,gate);
    }
    private static boolean nonzero(Integer value) { return value!=null&&value!=0; }
    private static <T> Field<T> nullable(JsonNode n,Function<JsonNode,T> decoder) { return n.isNull()?new ObservedNull<>():new Present<>(decoder.apply(n)); }
    private static void bound(Integer actual,JsonNode expected) { if(actual!=null)exactBound(actual,expected); }
    private static void exactBound(Integer actual,JsonNode expected) {
        if(actual==null)need(expected==null||expected.isNull(),"route-bound unknown integer differs from preview");
        else need(expected!=null&&expected.isIntegralNumber()&&BigInteger.valueOf(actual).equals(expected.bigIntegerValue()),"optional family integer differs from actual route context");
    }
    private static JsonNode field(JsonNode n,String key) { need(n!=null&&n.isObject()&&n.has(key),"missing optional family field "+key);return n.get(key); }
    private static void closed(JsonNode n,Set<String> required,Set<String> optional) {
        need(n!=null&&n.isObject(),"optional family must be object");Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);
        Set<String> allowed=new HashSet<>(required);allowed.addAll(optional);need(actual.containsAll(required)&&allowed.containsAll(actual),"optional family fields differ from strict contract");
    }
    private static boolean bool(JsonNode n,String key) { JsonNode v=field(n,key);need(v.isBoolean(),"actual boolean required: "+key);return v.booleanValue(); }
    private static Boolean optionalBool(JsonNode n,String key) { return field(n,key).isNull()?null:bool(n,key); }
    private static String reason(JsonNode n,String key) { JsonNode v=field(n,key);if(v.isNull())return null;need(v.isTextual()&&!v.textValue().isEmpty(),"nonempty reason or observed null required: "+key);return v.textValue(); }
    private static void eqText(JsonNode n,String key,String expected) { JsonNode v=field(n,key);need(v.isTextual()&&v.textValue().equals(expected),"optional family source differs: "+key); }
    private static BigInteger integer(JsonNode n,String key,long low,long high) { return number(field(n,key),BigInteger.valueOf(low),BigInteger.valueOf(high),key); }
    private static BigInteger number(JsonNode v,BigInteger low,BigInteger high,String key) { need(v!=null&&v.isIntegralNumber(),"exact integer required: "+key);BigInteger exact=v.bigIntegerValue();need(exact.compareTo(low)>=0&&exact.compareTo(high)<=0,"integer width differs: "+key);return exact; }
    private static BigInteger nullableNumber(JsonNode n,String key,BigInteger low,BigInteger high) { JsonNode v=field(n,key);return v.isNull()?null:number(v,low,high,key); }
    private static Integer i32(JsonNode n,String key) { BigInteger v=nullableNumber(n,key,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE));return v==null?null:v.intValueExact(); }
    private static int requiredI32(JsonNode n,String key) { return integer(n,key,Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact(); }
    private static BigInteger i64(JsonNode n,String key) { return nullableNumber(n,key,I64_MIN,I64_MAX); }
    private static Integer u8(JsonNode n,String key) { BigInteger v=nullableNumber(n,key,BigInteger.ZERO,BigInteger.valueOf(255));return v==null?null:v.intValueExact(); }
    private static Long u32(JsonNode n,String key) { BigInteger v=nullableNumber(n,key,BigInteger.ZERO,BigInteger.valueOf(4294967295L));return v==null?null:v.longValueExact(); }
    private static long requiredU32(JsonNode n,String key) { return integer(n,key,0,4294967295L).longValueExact(); }
    private static void constant(JsonNode n,String key,long value) { need(integer(n,key,value,value).longValueExact()==value,"fixed native contract value differs"); }
    private static NativeIdentity identity(JsonNode n,String key) { JsonNode v=field(n,key);if(v.isNull())return null;need(v.isTextual(),"opaque native identity must be text");return new NativeIdentity(v.textValue()); }
    private static Status status(JsonNode n) { JsonNode v=field(n,"status");need(v.isTextual(),"native status required");return switch(v.textValue()) { case "available"->Status.AVAILABLE;case "partial"->Status.PARTIAL;case "unavailable"->Status.UNAVAILABLE;case "truncated"->Status.TRUNCATED;default->throw new IllegalArgumentException("unknown optional native status"); }; }
    private static void need(boolean condition,String reason) { StrictJson.require(condition,reason); }
}
