package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyManagersModel.Field.*;

/** Same-capture source inverses and their declaration guards. These functions execute no native calls. */
public final class ArmyManagersCurrent {
    private ArmyManagersCurrent() { }
    public record Derived(boolean ready,Integer value) {
        public Derived { require(ready==(value!=null)&&(value==null||value==0||value==1),"current value/readiness association"); }
    }
    public record ActiveCombat(boolean ready,Boolean active) { }
    public record Projection(Kind kind,Inputs observed,List<Derived> occurrences) {
        public Projection { Objects.requireNonNull(kind);occurrences=List.copyOf(occurrences);require(observed==null||observed.kind()==kind,"current projection kind"); }
    }
    private static final Derived UNKNOWN=new Derived(false,null);
    private static final List<Field> LIMITS=List.of(ACTUAL_REFRESH_EXECUTION_READY,ACTUAL_NEXT_OCCURRENCE_READY,FULL_CALLBACK_READY,FULL_DAILY_ASSAULT_READY,FULL_MONTHLY_READY);
    private static final List<Field> SELECTION_FIELDS=List.of(REGISTRY_LOADED,USED_FALLBACK,REQUESTED_FULL_ID_U32,REGISTRY_CAPACITY_U32,REGISTRY_INDEX_U32,INDEXED_FULL_ID_U32,INDEXED_IDENTITY,SELECTION,OBJECT_IDENTITY);
    private static final List<Field> HEADER_FIELDS=List.of(ARMY_124_RAW_U32,UNIT_OWNER_174_RAW_U32,OWNER_CHARACTER_CARRIER_1C0_PRESENT,OWNER_CHARACTER_CARRIER_IDENTITY,HEADER_SELECTION,HEADER_IDENTITY,HEADER_0C_RAW_I32);
    private static final List<Field> CONDITION_FIELDS=List.of(ARMY_124_RAW_U32,UNIT_OWNER_174_RAW_U32,CONDITION_OWNER_IDENTITY,INLINE_CONDITION_IDENTITY,ROOT_KIND,ROOT_SUBTYPE,ROOT_PAYLOAD_U64,ROOT_CONSTRUCTION,NATIVE_CURRENT_CONDITION_PASSED);
    private static final List<Field> OWNER_RULE_FIELDS=List.of(ARMY_124_RAW_U32,UNIT_OWNER_174_RAW_U32,SELECTED_CHARACTER_18_RAW_U32,RULE_PROVIDER_IDENTITY,RULE_ARRAY_IDENTITY,INLINE_RULE_IDENTITY,ROOT_KIND,ROOT_SUBTYPE,ROOT_PAYLOAD_U64,NATIVE_CURRENT_RULE24_PASSED);
    public static void validate(Inputs input) {
        Document raw=input.value(); Kind kind=input.kind();require(Set.of(Kind.CONDITION30,Kind.FLAG20,Kind.FLAG21,Kind.HOLDER_RELATION,Kind.FLAG31).contains(kind),"current manager kind");
        references(raw.object(ORIGINAL_ROSTER),"original_roster");sameOccurrences(raw.object(ORIGINAL_ROSTER),raw.rows(OCCURRENCES),RAW_FULL_ID_U32);
        for(Document row:raw.rows(OCCURRENCES)) {
            resolution(row.object(ORIGINAL_ARMY_RESOLUTION),row.integer(RAW_FULL_ID_U32),"original_army_resolution");
            switch(kind) {
                case CONDITION30 -> {
                    selection(row.object(UNIT_RESOLUTION),row.integer(ARMY_124_RAW_U32));
                    if(!row.nil(ROOT_CONSTRUCTION))require(row.text(ROOT_CONSTRUCTION).equals("9F9E20_normal_return")&&eq(row.integer(ROOT_KIND),4)&&eq(row.integer(ROOT_SUBTYPE),0)&&!row.nil(UNIT_OWNER_174_RAW_U32)&&same(row,ROOT_PAYLOAD_U64,UNIT_OWNER_174_RAW_U32),"condition30 exact root ownerDWORD");
                    if(eq(row.integer(ARMY_1D4_RAW_U8),0))allNull(row,CONDITION_FIELDS,"condition30 zero1D4 undemanded fields");
                }
                case FLAG20 -> {
                    zeroOrOne(row.integer(NATIVE_GETTER_20_RAW_U8));require(row.yes(NATIVE_GETTER_RETURNED)==!row.nil(NATIVE_GETTER_20_RAW_U8),"flag20 returned/value");
                    if(eq(row.integer(ARMY_1D4_RAW_U8),0))require(!row.yes(NATIVE_GETTER_RETURNED)&&row.nil(NATIVE_GETTER_20_RAW_U8),"flag20 undemanded call");
                }
                case FLAG21 -> {
                    selection(row.object(UNIT_RESOLUTION),row.integer(ARMY_124_RAW_U32));selection(row.object(CHARACTER_RESOLUTION),row.integer(UNIT_OWNER_174_RAW_U32));zeroOrOne(row.integer(NATIVE_SHARED_TAIL_21_RAW_U8));
                    require(nullableMember(row.text(HEADER_SELECTION),Set.of("carrier_inline","native_static")),"flag21 header source");
                    boolean header=headerReady(row);require(row.yes(OWNER_HEADER_INPUTS_READY)==header,"flag21 header readiness");require(row.yes(NATIVE_SHARED_TAIL_RETURNED)==!row.nil(NATIVE_SHARED_TAIL_21_RAW_U8),"flag21 returned/value");
                    Long qword=row.i64(ARMY_1F0_RAW_I64);boolean zero=eq(row.integer(ARMY_1EC_RAW_U8),0);
                    if(zero||(qword!=null&&qword>0)){allNull(row,HEADER_FIELDS,"flag21 undemanded header");require(row.object(UNIT_RESOLUTION).nil(SELECTION)&&row.object(CHARACTER_RESOLUTION).nil(SELECTION),"flag21 undemanded selection");}
                    if(zero||(header&&eq(row.integer(HEADER_0C_RAW_I32),0)))require(!row.yes(NATIVE_SHARED_TAIL_RETURNED),"flag21 sourcezero native call");
                    if(zero)require(qword==null,"flag21 zero1EC signedQWORD undemanded");
                }
                case HOLDER_RELATION -> validateHolder(row);
                case FLAG31 -> validateFlag31(row);
                default -> throw new IllegalArgumentException("current manager kind");
            }
            Derived derived=derive(kind,row);require(row.yes(READY)==derived.ready()&&row.yes(readyField(kind))==derived.ready()&&Objects.equals(row.i32(valueField(kind)),derived.value()),"current manager declared value/readiness");
        }
        Document refs=raw.object(ORIGINAL_ROSTER);Integer count=refs.i32(COUNT_RAW_I32);List<Document> rows=raw.rows(OCCURRENCES);
        boolean covered=refs.yes(REFERENCES_READY)&&count!=null&&count>=0&&rows.size()==count;
        boolean selected=covered&&rows.stream().allMatch(row->row.yes(SAME_QUERY_ARMY_SELECTION_MATCHED));
        boolean ready=selected&&rows.stream().allMatch(row->derive(kind,row).ready());
        require(raw.yes(RAW_ROSTER_REFERENCES_READY)==refs.yes(REFERENCES_READY)&&raw.yes(ORIGINAL_ARMY_SELECTIONS_READY)==selected&&raw.yes(readyField(kind))==ready&&raw.yes(READY)==ready,"current manager global readiness");
        LIMITS.forEach(field->require(!raw.yes(field),"current manager cannot claim later callback"));
        if(kind==Kind.HOLDER_RELATION)require(!raw.yes(CHANGED_SELECTION_CONTEXT_READY)&&!raw.yes(CHANGED_RELATIONSHIP_CONTEXT_READY),"holder changed context credit");
    }
    public static Derived derive(Kind kind,Document row) {
        if(!row.yes(SAME_QUERY_ARMY_SELECTION_MATCHED))return UNKNOWN;
        return switch(kind) {
            case CONDITION30 -> {
                if(row.nil(ARMY_1D4_RAW_U8))yield UNKNOWN;if(eq(row.integer(ARMY_1D4_RAW_U8),0))yield new Derived(true,0);
                boolean ready=selected(row.object(UNIT_RESOLUTION))&&!row.nil(UNIT_OWNER_174_RAW_U32)&&!row.nil(CONDITION_OWNER_IDENTITY)&&!row.nil(INLINE_CONDITION_IDENTITY)&&eq(row.integer(ROOT_KIND),4)&&eq(row.integer(ROOT_SUBTYPE),0)&&same(row,ROOT_PAYLOAD_U64,UNIT_OWNER_174_RAW_U32)&&"9F9E20_normal_return".equals(row.text(ROOT_CONSTRUCTION))&&!row.nil(NATIVE_CURRENT_CONDITION_PASSED);
                yield ready?new Derived(true,row.yes(NATIVE_CURRENT_CONDITION_PASSED)?0:1):UNKNOWN;
            }
            case FLAG20 -> row.nil(ARMY_1D4_RAW_U8)?UNKNOWN:eq(row.integer(ARMY_1D4_RAW_U8),0)?new Derived(true,0):row.yes(NATIVE_GETTER_RETURNED)&&!row.nil(NATIVE_GETTER_20_RAW_U8)?new Derived(true,row.i32(NATIVE_GETTER_20_RAW_U8)):UNKNOWN;
            case FLAG21 -> {
                if(row.nil(ARMY_1EC_RAW_U8))yield UNKNOWN;if(eq(row.integer(ARMY_1EC_RAW_U8),0))yield new Derived(true,0);
                Long qword=row.i64(ARMY_1F0_RAW_I64);if(qword==null)yield UNKNOWN;
                if(qword<=0){if(!headerReady(row))yield UNKNOWN;if(eq(row.integer(HEADER_0C_RAW_I32),0))yield new Derived(true,0);}
                yield row.yes(NATIVE_SHARED_TAIL_RETURNED)&&!row.nil(NATIVE_SHARED_TAIL_21_RAW_U8)?new Derived(true,row.i32(NATIVE_SHARED_TAIL_21_RAW_U8)):UNKNOWN;
            }
            case HOLDER_RELATION -> {
                BigInteger tag=firstTag(row);if(tag==null)yield UNKNOWN;if(!eq(tag,0x50726f76L))yield new Derived(true,0);if(Boolean.TRUE.equals(row.bool(HOLDER_OWNER_EQUAL)))yield new Derived(true,1);if(!Boolean.FALSE.equals(row.bool(HOLDER_OWNER_EQUAL)))yield UNKNOWN;
                yield row.yes(NATIVE_RELATION_DEMANDED)&&row.yes(NATIVE_RELATION_RETURNED)&&!row.nil(NATIVE_HOLDER_OWNER_RELATION)?new Derived(true,row.yes(NATIVE_HOLDER_OWNER_RELATION)?1:0):UNKNOWN;
            }
            case FLAG31 -> {
                if(row.nil(ARMY_1D4_RAW_U8))yield UNKNOWN;if(eq(row.integer(ARMY_1D4_RAW_U8),0))yield new Derived(true,0);ActiveCombat combat=activeCombat(row);if(!combat.ready())yield UNKNOWN;if(Boolean.TRUE.equals(combat.active()))yield new Derived(true,0);
                yield ruleReady(row)?new Derived(true,row.yes(NATIVE_CURRENT_RULE24_PASSED)?0:1):UNKNOWN;
            }
            default -> throw new IllegalArgumentException("not current manager kind");
        };
    }
    static boolean headerReady(Document row) {
        Document character=row.object(CHARACTER_RESOLUTION);if(!selected(character))return false;
        if(Boolean.TRUE.equals(character.bool(REGISTRY_LOADED))){if(!row.object(UNIT_RESOLUTION).yes(SELECTED_OBJECT_READY)||row.nil(UNIT_OWNER_174_RAW_U32))return false;}else if(!Boolean.FALSE.equals(character.bool(REGISTRY_LOADED)))return false;
        Boolean carrier=row.bool(OWNER_CHARACTER_CARRIER_1C0_PRESENT);return carrier!=null&&!row.nil(HEADER_IDENTITY)&&!row.nil(HEADER_0C_RAW_I32)&&(carrier?"carrier_inline":"native_static").equals(row.text(HEADER_SELECTION))&&(!carrier||!row.nil(OWNER_CHARACTER_CARRIER_IDENTITY));
    }
    static ActiveCombat activeCombat(Document row) {
        if(row.nil(ARMY_1D4_RAW_U8)||eq(row.integer(ARMY_1D4_RAW_U8),0)||!selectionReady(row.object(COMBAT_RESOLUTION),row.integer(ARMY_128_RAW_U32))||row.nil(SELECTED_COMBAT_MAGIC_0C_RAW_U32))return new ActiveCombat(false,null);
        if(!eq(row.integer(SELECTED_COMBAT_MAGIC_0C_RAW_U32),0x436f6d62L))return new ActiveCombat(true,false);
        if(row.nil(SELECTED_COMBAT_FULL_ID_08_RAW_U32))return new ActiveCombat(false,null);return new ActiveCombat(true,!eq(row.integer(SELECTED_COMBAT_FULL_ID_08_RAW_U32),0xffffffffL));
    }
    static boolean ruleReady(Document row) {
        return selectionReady(row.object(UNIT_RESOLUTION),row.integer(ARMY_124_RAW_U32))&&selectionReady(row.object(CHARACTER_RESOLUTION),row.integer(UNIT_OWNER_174_RAW_U32))&&!row.nil(SELECTED_CHARACTER_18_RAW_U32)&&!row.nil(RULE_PROVIDER_IDENTITY)&&!row.nil(RULE_ARRAY_IDENTITY)&&!row.nil(INLINE_RULE_IDENTITY)&&"9F9E20_normal_return".equals(row.text(ROOT_CONSTRUCTION))&&eq(row.integer(ROOT_KIND),4)&&eq(row.integer(ROOT_SUBTYPE),0)&&same(row,ROOT_PAYLOAD_U64,SELECTED_CHARACTER_18_RAW_U32)&&row.yes(NATIVE_RULE_EVALUATION_RETURNED)&&!row.nil(NATIVE_CURRENT_RULE24_PASSED);
    }
    private static boolean selectionReady(Document resolution,BigInteger requested) {
        return selected(resolution)&&(Boolean.FALSE.equals(resolution.bool(REGISTRY_LOADED))||(Boolean.TRUE.equals(resolution.bool(REGISTRY_LOADED))&&requested!=null));
    }
    private static void validateHolder(Document row) {
        Boolean relation=row.bool(NATIVE_HOLDER_OWNER_RELATION);require(row.yes(NATIVE_RELATION_RETURNED)==(relation!=null)&&(!row.yes(NATIVE_RELATION_RETURNED)||row.yes(NATIVE_RELATION_DEMANDED)),"holder native relation association");
        BigInteger holder=row.integer(HOLDER_CHARACTER_FULL_ID_U32),owner=row.integer(SELECTED_UNIT_OWNER_174_RAW_U32);Boolean equal=holder==null||owner==null?null:holder.equals(owner);require(Objects.equals(row.bool(HOLDER_OWNER_EQUAL),equal),"holder fullDWORD equality");
        BigInteger tag=firstTag(row);if((tag!=null&&!eq(tag,0x50726f76L))||Boolean.TRUE.equals(equal))require(!row.yes(NATIVE_RELATION_DEMANDED)&&!row.yes(NATIVE_RELATION_RETURNED)&&relation==null,"holder short circuit native call");
        if(Boolean.FALSE.equals(equal)&&eq(tag,0x50726f76L))require(row.yes(NATIVE_RELATION_DEMANDED),"holder demanded relation missing");
    }
    private static BigInteger firstTag(Document row){List<Document> selections=row.rows(UNIT_SELECTIONS);return selections.isEmpty()?null:selections.getFirst().integer(PROVINCE_MAGIC_85C_RAW_U32);}
    private static void validateFlag31(Document row) {
        selection(row.object(COMBAT_RESOLUTION),row.integer(ARMY_128_RAW_U32));selection(row.object(UNIT_RESOLUTION),row.integer(ARMY_124_RAW_U32));selection(row.object(CHARACTER_RESOLUTION),row.integer(UNIT_OWNER_174_RAW_U32));
        String construction=row.text(ROOT_CONSTRUCTION);require(Set.of("not_demanded","9F9E20_normal_return").contains(construction),"flag31 root construction");
        if(construction.equals("9F9E20_normal_return"))require(eq(row.integer(ROOT_KIND),4)&&eq(row.integer(ROOT_SUBTYPE),0)&&!row.nil(SELECTED_CHARACTER_18_RAW_U32)&&same(row,ROOT_PAYLOAD_U64,SELECTED_CHARACTER_18_RAW_U32),"flag31 complete Character18 root");
        if(row.has(RULE24_SOURCE_PINS_V1)){Document pins=row.object(RULE24_SOURCE_PINS_V1);validatePins(pins);require(Objects.equals(pins.text(RULE_RECEIVER_IDENTITY),row.text(INLINE_RULE_IDENTITY)),"flag31 borrowed rule receiver identity");}
        ActiveCombat combat=activeCombat(row);require(row.yes(ACTIVE_COMBAT_INPUTS_READY)==combat.ready()&&Objects.equals(row.bool(SOURCE_ACTIVE_COMBAT),combat.active()),"flag31 active combat declaration");
        require(row.yes(NATIVE_RULE_EVALUATION_RETURNED)==!row.nil(NATIVE_CURRENT_RULE24_PASSED),"flag31 actual verdict association");
        if(construction.equals("not_demanded"))allNull(row,List.of(ROOT_KIND,ROOT_SUBTYPE,ROOT_PAYLOAD_U64),"flag31 undemanded root");
        if(row.yes(NATIVE_RULE_EVALUATION_RETURNED))require(ruleReady(row),"flag31 native returned without actual demanded root");
        if(!row.nil(SELECTED_COMBAT_MAGIC_0C_RAW_U32)&&!eq(row.integer(SELECTED_COMBAT_MAGIC_0C_RAW_U32),0x436f6d62L))require(row.nil(SELECTED_COMBAT_FULL_ID_08_RAW_U32),"flag31 wrong combat tag short circuit");
        if(row.nil(ARMY_1D4_RAW_U8)||eq(row.integer(ARMY_1D4_RAW_U8),0)){allNull(row,List.of(ARMY_128_RAW_U32,SELECTED_COMBAT_MAGIC_0C_RAW_U32,SELECTED_COMBAT_FULL_ID_08_RAW_U32),"flag31 undemanded combat");undemandedSelection(row.object(COMBAT_RESOLUTION));}
        if(row.nil(ARMY_1D4_RAW_U8)||eq(row.integer(ARMY_1D4_RAW_U8),0)||!combat.ready()||Boolean.TRUE.equals(combat.active())){allNull(row,OWNER_RULE_FIELDS,"flag31 undemanded owner/rule");undemandedSelection(row.object(UNIT_RESOLUTION));undemandedSelection(row.object(CHARACTER_RESOLUTION));require(construction.equals("not_demanded")&&!row.yes(NATIVE_RULE_EVALUATION_RETURNED),"flag31 undemanded native rule");}
    }
    static void selection(Document value,BigInteger requested) {
        require(Objects.equals(value.integer(REQUESTED_FULL_ID_U32),requested),"selection wholeDWORD request");String source=value.text(SELECTION);require(nullableMember(source,Set.of("registry_full_id","native_fallback")),"selection exact source");
        if(source!=null)require(Objects.equals(value.bool(USED_FALLBACK),source.equals("native_fallback")),"selection fallback association");
        if(!value.nil(REGISTRY_INDEX_U32))require(requested!=null&&value.integer(REGISTRY_INDEX_U32).equals(requested.and(BigInteger.valueOf(0xffffff))),"selection low24 index");
        if(Boolean.FALSE.equals(value.bool(REGISTRY_LOADED)))require(requested==null&&value.nil(REGISTRY_INDEX_U32),"selection store-null undemanded request");
        if("registry_full_id".equals(source)&&value.yes(SELECTED_OBJECT_READY))require(requested!=null&&Objects.equals(value.integer(INDEXED_FULL_ID_U32),requested)&&Objects.equals(value.text(OBJECT_IDENTITY),value.text(INDEXED_IDENTITY)),"selection full generation and physical object");
        if(value.yes(SELECTED_OBJECT_READY))require(!value.nil(OBJECT_IDENTITY)&&source!=null,"selected object source association");require(value.yes(READY)==value.yes(SELECTED_OBJECT_READY),"selection independent readiness");
    }
    private static void undemandedSelection(Document value){require(!value.yes(READY)&&!value.yes(SELECTED_OBJECT_READY),"undemanded selection readiness");allNull(value,SELECTION_FIELDS,"undemanded selection fields");}
    public static void validatePins(Document pins) {
        availability(pins,PINS_CAPTURED_READY,"rule24_source_pins_v1");require(pins.yes(VTABLE_READ_READY)==!pins.nil(RULE_VTABLE_IDENTITY)&&pins.yes(MODE_READ_READY)==!pins.nil(CONDITION_MODE_RAW_U8),"Rule24 captured value/read status");
        List<Field> flags=List.of(EXPECTED_SCOPE_PIN_READ_READY,SCOPE_MASK_PIN_READ_READY,RULE_EVALUATOR_PIN_READ_READY);List<Field> identities=List.of(EXPECTED_SCOPE_FUNCTION_IDENTITY,SCOPE_MASK_FUNCTION_IDENTITY,RULE_EVALUATOR_FUNCTION_IDENTITY);List<Field> rvas=List.of(EXPECTED_SCOPE_FUNCTION_RVA,SCOPE_MASK_FUNCTION_RVA,RULE_EVALUATOR_FUNCTION_RVA);
        boolean vtable=pins.yes(VTABLE_READ_READY)&&!"native:0".equals(pins.text(RULE_VTABLE_IDENTITY));int requested=9+(vtable?24:0),captured=(pins.yes(VTABLE_READ_READY)?8:0)+(pins.yes(MODE_READ_READY)?1:0);boolean ready=pins.yes(VTABLE_READ_READY)&&pins.yes(MODE_READ_READY);
        for(int i=0;i<flags.size();i++){boolean read=pins.yes(flags.get(i));require(read==!pins.nil(identities.get(i))&&(read||pins.nil(rvas.get(i))),"Rule24 pin actual read association");if(!vtable)require(!read,"Rule24 null vtable virtual slot demand");if(read)captured+=8;ready&=read;}
        require(eq(pins.integer(PIN_REQUESTED_BYTES_U32),requested)&&eq(pins.integer(PIN_CAPTURED_BYTES_U32),captured)&&captured<=requested&&requested<=33&&pins.yes(PINS_CAPTURED_READY)==ready,"Rule24 pin byte accounting/readiness");
    }
    public static Projection project(Kind kind,Inputs input){if(input==null)return new Projection(kind,null,List.of());validate(input);return new Projection(kind,input,input.value().rows(OCCURRENCES).stream().map(row->derive(kind,row)).toList());}
    public static ObjectNode encodeProjection(Projection projection,JsonNode provenance,boolean publicV2) {
        Kind kind=projection.kind();String base=base(kind);ObjectNode result=JsonNodeFactory.instance.objectNode();result.put("schema_version",1).put("source","source_bound_"+base).put("stage","observed_"+base+(kind==Kind.HOLDER_RELATION?"_inputs":"")).put("source_contract_game_version","1.20.0.3").put("status","unavailable").put("ready",false).put("unavailable_reason",base+"_unavailable").put(readyField(kind).wire(),false).put("native_calls_executed",0).put("native_writes_executed",0).put("actual_post_stage_observed",false).put("future_tick_ready",false);
        result.set("occurrences",JsonNodeFactory.instance.arrayNode());result.set("source_provenance",provenance==null?JsonNodeFactory.instance.nullNode():provenance.deepCopy());result.set("observed_"+base+(kind==Kind.HOLDER_RELATION?"_inputs":""),projection.observed()==null?JsonNodeFactory.instance.nullNode():encode(projection.observed().value(),publicV2));LIMITS.forEach(field->result.put(field.wire(),false));
        if(kind==Kind.HOLDER_RELATION)result.put("context_basis","same_query_selected_title_holder_and_unit_owner").put("changed_selection_context_ready",false).put("changed_relationship_context_ready",false);
        if(projection.observed()==null)return result;Document raw=projection.observed().value();result.put("status",raw.text(STATUS)).put("ready",raw.yes(READY)).put(readyField(kind).wire(),raw.yes(readyField(kind)));reason(result,raw.yes(READY)?null:raw.text(UNAVAILABLE_REASON));ArrayNode rows=(ArrayNode)result.get("occurrences");
        List<Field> subset=kind==Kind.CONDITION30?List.of(NATIVE_INDEX,RAW_FULL_ID_U32,ORIGINAL_ARMY_RESOLUTION,SAME_QUERY_ARMY_SELECTION_MATCHED,ACTUAL_ARMY_30_RAW_U8,NATIVE_CURRENT_CONDITION_PASSED):List.of(NATIVE_INDEX,RAW_FULL_ID_U32,ORIGINAL_ARMY_RESOLUTION,SAME_QUERY_ARMY_SELECTION_MATCHED,ACTUAL_ARMY_20_RAW_U8,ARMY_1D4_RAW_U8,NATIVE_GETTER_RETURNED,NATIVE_GETTER_20_RAW_U8);
        for(int i=0;i<raw.rows(OCCURRENCES).size();i++){Document row=raw.rows(OCCURRENCES).get(i);Derived derived=projection.occurrences().get(i);ObjectNode out;
            if(kind==Kind.CONDITION30||kind==Kind.FLAG20){out=JsonNodeFactory.instance.objectNode();for(Field field:subset)out.set(field.wire(),encode(row.get(field),publicV2));}else out=(ObjectNode)encode(row,publicV2);
            out.put("ready",derived.ready()).put(readyField(kind).wire(),derived.ready());if(derived.value()==null)out.putNull(valueField(kind).wire());else out.put(valueField(kind).wire(),derived.value());reason(out,derived.ready()?null:row.text(UNAVAILABLE_REASON));
            if(kind==Kind.FLAG31&&row.has(RULE24_SOURCE_PINS_V1))out.set("rule24_source_pins_projection_v1",encodePinsProjection(row.object(RULE24_SOURCE_PINS_V1),provenance,publicV2));rows.add(out);
        }return result;
    }
    public static ObjectNode encodePinsProjection(Document pins,JsonNode provenance,boolean publicV2){validatePins(pins);ObjectNode result=JsonNodeFactory.instance.objectNode();result.put("schema_version",1).put("source","source_bound_current_rule24_source_pins").put("stage","observed_current_rule24_source_pins").put("source_contract_game_version","1.20.0.3").put("status",pins.text(STATUS)).put("ready",pins.yes(PINS_CAPTURED_READY)).put("pins_captured_ready",pins.yes(PINS_CAPTURED_READY)).put("native_calls_executed",0).put("native_writes_executed",0);reason(result,pins.yes(PINS_CAPTURED_READY)?null:pins.text(UNAVAILABLE_REASON));result.set("source_provenance",provenance==null?JsonNodeFactory.instance.nullNode():provenance.deepCopy());result.set("observed_current_rule24_source_pins",encode(pins,publicV2));for(Field field:List.of(PROVIDER_ARRAY_BORROWED,RULE_RECEIVER_IDENTITY,RULE_VTABLE_IDENTITY,CONDITION_MODE_RAW_U8,VTABLE_READ_READY,MODE_READ_READY,EXPECTED_SCOPE_PIN_READ_READY,SCOPE_MASK_PIN_READ_READY,RULE_EVALUATOR_PIN_READ_READY,PIN_REQUESTED_BYTES_U32,PIN_CAPTURED_BYTES_U32,EXPECTED_SCOPE_FUNCTION_IDENTITY,EXPECTED_SCOPE_FUNCTION_RVA,SCOPE_MASK_FUNCTION_IDENTITY,SCOPE_MASK_FUNCTION_RVA,RULE_EVALUATOR_FUNCTION_IDENTITY,RULE_EVALUATOR_FUNCTION_RVA))result.set(field.wire(),encode(pins.get(field),publicV2));return result;}
    static Field readyField(Kind kind){return switch(kind){case CONDITION30->CURRENT_CONDITION_30_INPUTS_READY;case FLAG20->CURRENT_FLAG20_INPUTS_READY;case FLAG21->CURRENT_FLAG21_INPUTS_READY;case HOLDER_RELATION->CURRENT_SHARED_TAIL_INPUTS_READY;case FLAG31->CURRENT_FLAG31_INPUTS_READY;default->throw new IllegalArgumentException("current kind");};}
    static Field valueField(Kind kind){return switch(kind){case CONDITION30->DERIVED_CURRENT_30_RAW_U8;case FLAG20->DERIVED_CURRENT_20_RAW_U8;case FLAG21->DERIVED_CURRENT_21_RAW_U8;case HOLDER_RELATION->DERIVED_CURRENT_SHARED_TAIL_RAW_U8;case FLAG31->DERIVED_CURRENT_31_RAW_U8;default->throw new IllegalArgumentException("current kind");};}
    private static String base(Kind kind){return switch(kind){case CONDITION30->"current_army_condition30_inputs";case FLAG20->"current_army_flag20_inputs";case FLAG21->"current_army_flag21_inputs";case HOLDER_RELATION->"current_selected_title_holder_owner_relation";case FLAG31->"current_army_flag31_inputs";default->throw new IllegalArgumentException("current kind");};}
    static boolean selected(Document value){return value.yes(SELECTED_OBJECT_READY)&&!value.nil(OBJECT_IDENTITY);}
    static boolean eq(BigInteger value,long expected){return value!=null&&value.equals(BigInteger.valueOf(expected));}
    static boolean same(Document row,Field left,Field right){return Objects.equals(row.integer(left),row.integer(right));}
    static boolean nullableMember(String value,Set<String> allowed){return value==null||allowed.contains(value);}
    static void allNull(Document row,List<Field> fields,String message){require(fields.stream().allMatch(row::nil),message);}
    static void zeroOrOne(BigInteger value){require(value==null||eq(value,0)||eq(value,1),"native getter value must be 0 or 1");}
    static void reason(ObjectNode output,String reason){if(reason==null)output.putNull("unavailable_reason");else output.put("unavailable_reason",reason);}
    static void resolution(Document value,BigInteger requested,String name){ArmyStrengthsRosterContract.validateResolution(ArmyStrengthsRosterContract.decodeOperandResolution(encode(value,false),name),requested==null?null:requested.longValueExact(),name);}
    static void references(Document value,String name){ArmyStrengthsRosterContract.validateReferences(ArmyStrengthsRosterContract.decodeRawReferences(encode(value,false),name),name);}
    static void sameOccurrences(Document references,List<Document> rows,Field request){List<Document> expected=references.rows(OCCURRENCES);require(expected.size()==rows.size(),"original raw occurrences retained");for(int i=0;i<rows.size();i++)require(Objects.equals(expected.get(i).i32(NATIVE_INDEX),rows.get(i).i32(NATIVE_INDEX))&&Objects.equals(expected.get(i).integer(RAW_FULL_ID_U32),rows.get(i).integer(request)),"original raw index/fullDWORD/order retained");}
}
