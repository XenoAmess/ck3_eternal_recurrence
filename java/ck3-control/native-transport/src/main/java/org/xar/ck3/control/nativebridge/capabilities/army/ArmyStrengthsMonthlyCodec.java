package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthlyModel.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;

/** One exact JSON/native model conversion; all encoders rebuild JSON from typed values. */
public final class ArmyStrengthsMonthlyCodec {
    private ArmyStrengthsMonthlyCodec() { }
    private static final BigInteger U32_MAX = new BigInteger("4294967295");
    private static boolean nil(JsonNode n) { require(n != null,"missing monthly field"); return n.isNull(); }
    private static <T> Optional<T> opt(ObjectNode n,String key,Function<JsonNode,T> decode) { JsonNode value=get(n,key);return value.isNull()?Optional.empty():Optional.of(decode.apply(value)); }
    private static <T> Optional<List<T>> list(ObjectNode n,String key,Function<JsonNode,T> decode) { return opt(n,key,value->array(value,decode)); }
    private static <E extends Enum<E>> E enumeration(JsonNode n,Class<E> type) { return ArmyStrengthsCodec.enumText(n,type); }
    private static Readiness readiness(ObjectNode n) { return new Readiness(enumeration(get(n,"status"),Availability.class),bool(get(n,"ready")),opt(n,"unavailable_reason",ArmyJson::nonempty)); }
    private static void putReady(ObjectNode n,Readiness r) { n.put("status",ArmyStrengthsCodec.wire(r.status())).put("ready",r.ready());put(n,"unavailable_reason",r.reason(),value->empty().textNode(value)); }
    private static <T> void put(ObjectNode n,String key,Optional<T> value,Function<T,JsonNode> encode) { if(value.isPresent())n.set(key,encode.apply(value.orElseThrow()));else n.putNull(key); }
    private static <T> void putList(ObjectNode n,String key,Optional<List<T>> value,Function<T,JsonNode> encode) { put(n,key,value,items->{var out=empty().arrayNode();items.forEach(item->out.add(encode.apply(item)));return out;}); }
    private static JsonNode integerNode(Integer n) { return empty().numberNode(n); }
    private static JsonNode longNode(Long n) { return empty().numberNode(n); }
    private static JsonNode boolNode(Boolean n) { return empty().booleanNode(n); }
    private static JsonNode stringNode(String n) { return empty().textNode(n); }
    public static MaaRecruitment decodeMaa(JsonNode raw) {
        if(nil(raw))return null;
        ObjectNode n=closed(raw,"schema_version","status","unavailable_reason","owner_character_id","creation_kind","creation_scope","command_class","title_id","requested_quantity","pay_cost","catalog_observed","types_in_native_order","missing_type_keys");
        require(i32(n.get("schema_version"))==1&&i32(n.get("creation_kind"))==1&&i32(n.get("title_id"))==-1&&i32(n.get("requested_quantity"))==-1,"MAA constant operands differ");equal(n.get("creation_scope"),"regular_personal");equal(n.get("command_class"),"CCreateMAARegimentCommand");
        return new MaaRecruitment(enumeration(n.get("status"),Status.class),opt(n,"unavailable_reason",ArmyJson::nonempty),opt(n,"owner_character_id",ArmyJson::i32),bool(n.get("pay_cost")),bool(n.get("catalog_observed")),array(n.get("types_in_native_order"),ArmyStrengthsMonthlyCodec::maaType),array(n.get("missing_type_keys"),ArmyJson::nonempty));
    }
    private static MaaType maaType(JsonNode raw) {
        ObjectNode n=closed(raw,"type_key","type_index","inputs_ready","unavailable_reason","effective_quantity","can_create","regular_personal_quote");
        return new MaaType(nonempty(n.get("type_key")),i32(n.get("type_index")),bool(n.get("inputs_ready")),opt(n,"unavailable_reason",ArmyJson::nonempty),opt(n,"effective_quantity",ArmyJson::i32),opt(n,"can_create",ArmyJson::bool),quote(n.get("regular_personal_quote")));
    }
    private static Quote quote(JsonNode raw) {
        ObjectNode n=closed(raw,"context","status","unavailable_reason","resource_scale","resources_raw");equal(n.get("context"),"regular_personal_create");require(i32(n.get("resource_scale"))==100000,"MAA raw resource scale");
        return new Quote(enumeration(n.get("status"),Availability.class),opt(n,"unavailable_reason",ArmyJson::nonempty),list(n,"resources_raw",ArmyJson::i64));
    }
    public static JsonNode encodeMaa(MaaRecruitment m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty().put("schema_version",1).put("status",ArmyStrengthsCodec.wire(m.status())).put("creation_kind",1).put("creation_scope","regular_personal").put("command_class","CCreateMAARegimentCommand").put("title_id",-1).put("requested_quantity",-1).put("pay_cost",m.payCost()).put("catalog_observed",m.catalogObserved());
        put(n,"unavailable_reason",m.reason(),ArmyStrengthsMonthlyCodec::stringNode);put(n,"owner_character_id",m.ownerCharacterId(),ArmyStrengthsMonthlyCodec::integerNode);
        var types=n.putArray("types_in_native_order");for(MaaType type:m.types()) {ObjectNode row=empty().put("type_key",type.typeKey()).put("type_index",type.typeIndex()).put("inputs_ready",type.inputsReady());put(row,"unavailable_reason",type.reason(),ArmyStrengthsMonthlyCodec::stringNode);put(row,"effective_quantity",type.effectiveQuantity(),ArmyStrengthsMonthlyCodec::integerNode);put(row,"can_create",type.canCreate(),ArmyStrengthsMonthlyCodec::boolNode);ObjectNode q=empty().put("context","regular_personal_create").put("status",ArmyStrengthsCodec.wire(type.quote().status())).put("resource_scale",100000);put(q,"unavailable_reason",type.quote().reason(),ArmyStrengthsMonthlyCodec::stringNode);putList(q,"resources_raw",type.quote().resourcesRaw(),ArmyStrengthsMonthlyCodec::longNode);row.set("regular_personal_quote",q);types.add(row);}var missing=n.putArray("missing_type_keys");m.missingTypeKeys().forEach(missing::add);return n;
    }
    public static OwnedRegiments decodeOwned(JsonNode raw) {
        if(nil(raw))return null;ObjectNode n=closed(raw,"schema","scope","status","actor_character_id","source_count","collection_complete","regiments","unavailable_reason");equal(n.get("schema"),"ck3_12003_owned_regiments_v1");equal(n.get("scope"),"current-player-direct-owned-regiments");
        return new OwnedRegiments(enumeration(n.get("status"),Status.class),i32(n.get("actor_character_id")),opt(n,"source_count",ArmyJson::i32),bool(n.get("collection_complete")),list(n,"regiments",ArmyStrengthsMonthlyCodec::ownedRegiment),opt(n,"unavailable_reason",ArmyJson::nonempty));
    }
    private static OwnedRegiment ownedRegiment(JsonNode raw) {
        ObjectNode n=closed(raw,"persistent_regiment_id","available","owner_character_id","native_capacity_raw","maa_type_status","maa_type_key","siege_tier_observable","siege_tier","composition_unavailable_reason","chunks","unavailable_reason");
        ArmyStrengths.Composition composition=new ArmyStrengths.Composition(enumeration(n.get("maa_type_status"),ArmyStrengths.MaaStatus.class),nullable(n,"maa_type_key",ArmyJson::nonempty),nullable(n,"siege_tier",ArmyJson::i32),bool(n.get("siege_tier_observable")),nullable(n,"composition_unavailable_reason",ArmyJson::nonempty));
        return new OwnedRegiment(i32(n.get("persistent_regiment_id")),bool(n.get("available")),opt(n,"owner_character_id",ArmyJson::i32),opt(n,"native_capacity_raw",ArmyJson::i32),composition,list(n,"chunks",ArmyStrengthsMonthlyCodec::ownedChunk),opt(n,"unavailable_reason",ArmyJson::nonempty));
    }
    private static OwnedChunk ownedChunk(JsonNode raw) {ObjectNode n=closed(raw,"chunk_index","maximum_soldiers","current_soldiers","persistent_regiment_id","native_chunk_index","army_regiment_id","pending_raw","pending","state_raw");return new OwnedChunk(i32(n.get("chunk_index")),i32(n.get("maximum_soldiers")),i32(n.get("current_soldiers")),i32(n.get("persistent_regiment_id")),i32(n.get("native_chunk_index")),i32(n.get("army_regiment_id")),i32(n.get("pending_raw")),bool(n.get("pending")),i32(n.get("state_raw")));}
    public static JsonNode encodeOwned(OwnedRegiments m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty().put("schema","ck3_12003_owned_regiments_v1").put("scope","current-player-direct-owned-regiments").put("status",ArmyStrengthsCodec.wire(m.status())).put("actor_character_id",m.actorCharacterId()).put("collection_complete",m.collectionComplete());put(n,"source_count",m.sourceCount(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"unavailable_reason",m.reason(),ArmyStrengthsMonthlyCodec::stringNode);
        putList(n,"regiments",m.regiments(),r->{ObjectNode row=empty().put("persistent_regiment_id",r.persistentRegimentId()).put("available",r.available());put(row,"owner_character_id",r.ownerCharacterId(),ArmyStrengthsMonthlyCodec::integerNode);put(row,"native_capacity_raw",r.nativeCapacityRaw(),ArmyStrengthsMonthlyCodec::integerNode);put(row,"unavailable_reason",r.reason(),ArmyStrengthsMonthlyCodec::stringNode);ArmyStrengths.Composition c=r.composition();row.put("maa_type_status",ArmyStrengthsCodec.wire(c.status())).put("siege_tier_observable",c.siegeTierObservable());ArmyStrengthsCodec.put(row,"maa_type_key",c.key(),ArmyStrengthsMonthlyCodec::stringNode);ArmyStrengthsCodec.put(row,"siege_tier",c.siegeTier(),ArmyStrengthsMonthlyCodec::integerNode);ArmyStrengthsCodec.put(row,"composition_unavailable_reason",c.reason(),ArmyStrengthsMonthlyCodec::stringNode);putList(row,"chunks",r.chunks(),k->empty().put("chunk_index",k.chunkIndex()).put("maximum_soldiers",k.maximumSoldiers()).put("current_soldiers",k.currentSoldiers()).put("persistent_regiment_id",k.persistentRegimentId()).put("native_chunk_index",k.nativeChunkIndex()).put("army_regiment_id",k.armyRegimentId()).put("pending_raw",k.pendingRaw()).put("pending",k.pending()).put("state_raw",k.stateRaw()));return row;});return n;
    }
    public static FirstRemoval decodeCleanup(JsonNode raw) {
        if(nil(raw))return null;ObjectNode n=closed(raw,"status","ready","unavailable_reason","candidate_found","candidate_stored_index","argument_army_id","cleanup_resolved_army_id","cleanup_used_fallback","selected_bucket_index","id_lists","selected_bucket_rows","records_b0");
        List<ManagerIds> components=array(n.get("id_lists"),v->{ObjectNode c=closed(v,"manager_offset","ordered_army_ids");ManagerOffset offset=java.util.Arrays.stream(ManagerOffset.values()).filter(o->o.wire().equals(text(c.get("manager_offset")))).findFirst().orElseThrow(()->new IllegalArgumentException("unknown cleanup component"));return new ManagerIds(offset,list(c,"ordered_army_ids",ArmyJson::i32));});
        Optional<List<CleanupBucket>> buckets=list(n,"selected_bucket_rows",v->{ObjectNode row=closed(v,"stored_index","observed_army_id","native_same_cleanup_army_pointer");return new CleanupBucket(i32(row.get("stored_index")),opt(row,"observed_army_id",ArmyJson::i32),bool(row.get("native_same_cleanup_army_pointer")));});
        if(buckets.isPresent())for(int i=0;i<buckets.orElseThrow().size();i++)require(buckets.orElseThrow().get(i).storedIndex()==i,"cleanup bucket native order");
        return new FirstRemoval(readiness(n),opt(n,"candidate_found",ArmyJson::bool),opt(n,"candidate_stored_index",ArmyJson::i32),opt(n,"argument_army_id",ArmyJson::i32),opt(n,"cleanup_resolved_army_id",ArmyJson::i32),opt(n,"cleanup_used_fallback",ArmyJson::bool),opt(n,"selected_bucket_index",ArmyStrengthsMonthlyCodec::u32),components,buckets,list(n,"records_b0",v->{List<Long> a=array(v,ArmyStrengthsMonthlyCodec::u32);require(a.size()==4,"four cleanup DWORDs");return new Dwords(a.get(0),a.get(1),a.get(2),a.get(3));}));
    }
    public static JsonNode encodeCleanup(FirstRemoval m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty();putReady(n,m.readiness());put(n,"candidate_found",m.candidateFound(),ArmyStrengthsMonthlyCodec::boolNode);put(n,"candidate_stored_index",m.candidateStoredIndex(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"argument_army_id",m.argumentArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"cleanup_resolved_army_id",m.cleanupResolvedArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"cleanup_used_fallback",m.cleanupUsedFallback(),ArmyStrengthsMonthlyCodec::boolNode);put(n,"selected_bucket_index",m.selectedBucketIndex(),ArmyStrengthsMonthlyCodec::longNode);var components=n.putArray("id_lists");for(ManagerIds c:m.idLists()){ObjectNode row=empty().put("manager_offset",c.offset().wire());putList(row,"ordered_army_ids",c.ids(),ArmyStrengthsMonthlyCodec::integerNode);components.add(row);}putList(n,"selected_bucket_rows",m.selectedBucketRows(),r->{ObjectNode row=empty().put("stored_index",r.storedIndex()).put("native_same_cleanup_army_pointer",r.sameCleanupArmyPointer());put(row,"observed_army_id",r.observedArmyId(),ArmyStrengthsMonthlyCodec::integerNode);return row;});putList(n,"records_b0",m.recordsB0(),r->{var a=empty().arrayNode();a.add(r.first()).add(r.second()).add(r.third()).add(r.fourth());return a;});return n;
    }
    private static long u32(JsonNode n) { return range(n,BigInteger.ZERO,U32_MAX).longValueExact(); }
    private static <E extends Enum<E>&WireField,T> Map<E,Optional<T>> fields(ObjectNode n,E[] keys,Function<JsonNode,T> parse) {EnumMap<E,Optional<T>> result=new EnumMap<>(keys[0].getDeclaringClass());for(E key:keys)result.put(key,opt(n,key.wire(),parse));return result;}
    private static Set<String> fieldNames(WireField[]... groups) {Set<String> result=new HashSet<>();for(WireField[] group:groups)for(WireField key:group)require(result.add(key.wire()),"duplicate typed schema field");return result;}
    private static ObjectNode exact(JsonNode raw,Set<String> fields,String... rest) {Set<String> expected=new HashSet<>(fields);expected.addAll(List.of(rest));ObjectNode n=object(raw);require(names(n).equals(expected),"wrong/missing helper fields");return n;}
    private static <E extends Enum<E>&WireField,T> void putFields(ObjectNode n,Map<E,Optional<T>> fields,Function<T,JsonNode> encode) {fields.forEach((key,value)->put(n,key.wire(),value,encode));}
    public static HelperDomain decodeDomain(JsonNode raw) {
        if(nil(raw))return null;ObjectNode n=closed(raw,"status","ready","unavailable_reason","entry_army_id","group_count_5c_raw","rows");
        return new HelperDomain(readiness(n),opt(n,"entry_army_id",ArmyJson::i32),opt(n,"group_count_5c_raw",ArmyJson::i32),list(n,"rows",ArmyStrengthsMonthlyCodec::domainRow));
    }
    private static DomainRow domainRow(JsonNode raw) {
        ObjectNode n=exact(raw,fieldNames(DomainI32.values(),DomainU32.values(),DomainBool.values()),"domain_flag_17e_raw","domain_value_48_raw64","count_records");
        return new DomainRow(fields(n,DomainI32.values(),ArmyJson::i32),fields(n,DomainU32.values(),ArmyStrengthsMonthlyCodec::u32),fields(n,DomainBool.values(),ArmyJson::bool),opt(n,"domain_flag_17e_raw",ArmyJson::i32),opt(n,"domain_value_48_raw64",ArmyJson::i64),list(n,"count_records",v->{ObjectNode c=closed(v,"stored_index","count_00_raw","count_04_raw","state_18_raw");return new DomainCount(i32(c.get("stored_index")),opt(c,"count_00_raw",ArmyJson::i32),opt(c,"count_04_raw",ArmyJson::i32),opt(c,"state_18_raw",ArmyJson::i32));}));
    }
    public static JsonNode encodeDomain(HelperDomain m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty();putReady(n,m.readiness());put(n,"entry_army_id",m.entryArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"group_count_5c_raw",m.groupCount5cRaw(),ArmyStrengthsMonthlyCodec::integerNode);putList(n,"rows",m.rows(),r->{ObjectNode row=empty();putFields(row,r.signed(),ArmyStrengthsMonthlyCodec::integerNode);putFields(row,r.unsigned(),ArmyStrengthsMonthlyCodec::longNode);putFields(row,r.predicates(),ArmyStrengthsMonthlyCodec::boolNode);put(row,"domain_flag_17e_raw",r.domainFlag17eRaw(),ArmyStrengthsMonthlyCodec::integerNode);put(row,"domain_value_48_raw64",r.domainValue48Raw64(),ArmyStrengthsMonthlyCodec::longNode);putList(row,"count_records",r.countRecords(),c->{ObjectNode out=empty().put("stored_index",c.storedIndex());put(out,"count_00_raw",c.count00Raw(),ArmyStrengthsMonthlyCodec::integerNode);put(out,"count_04_raw",c.count04Raw(),ArmyStrengthsMonthlyCodec::integerNode);put(out,"state_18_raw",c.state18Raw(),ArmyStrengthsMonthlyCodec::integerNode);return out;});return row;});return n;
    }
    public static HelperPointStore decodePoint(JsonNode raw) {
        if(nil(raw))return null;ObjectNode n=closed(raw,"status","ready","unavailable_reason","entry_army_id","helper_resolved_army_id","helper_used_fallback","helper_same_current_army_pointer","group_count_5c_raw","groups");
        return new HelperPointStore(readiness(n),opt(n,"entry_army_id",ArmyJson::i32),opt(n,"helper_resolved_army_id",ArmyJson::i32),opt(n,"helper_used_fallback",ArmyJson::bool),opt(n,"helper_same_current_army_pointer",ArmyJson::bool),opt(n,"group_count_5c_raw",ArmyJson::i32),list(n,"groups",ArmyStrengthsMonthlyCodec::pointGroup));
    }
    private static PointGroup pointGroup(JsonNode raw) {
        ObjectNode n=closed(raw,"group_index","record_count_14_raw","character_count_2c_raw","record_rows","character_rows");
        return new PointGroup(i32(n.get("group_index")),opt(n,"record_count_14_raw",ArmyJson::i32),opt(n,"character_count_2c_raw",ArmyJson::i32),list(n,"record_rows",v->{ObjectNode r=exact(v,fieldNames(PointRecordI32.values(),PointRecordBool.values()),"record_regiment_magic_14_raw","data_byte_14_raw","ordered_persistent_regiment_ids_2a8");return new PointRecord(fields(r,PointRecordI32.values(),ArmyJson::i32),fields(r,PointRecordBool.values(),ArmyJson::bool),opt(r,"record_regiment_magic_14_raw",ArmyStrengthsMonthlyCodec::u32),opt(r,"data_byte_14_raw",ArmyJson::i32),list(r,"ordered_persistent_regiment_ids_2a8",ArmyJson::i32));}),list(n,"character_rows",v->{ObjectNode r=exact(v,fieldNames(PointCharacterI32.values(),PointCharacterBool.values()),"child_byte_108_raw");return new PointCharacter(fields(r,PointCharacterI32.values(),ArmyJson::i32),fields(r,PointCharacterBool.values(),ArmyJson::bool),opt(r,"child_byte_108_raw",ArmyJson::i32));}));
    }
    public static JsonNode encodePoint(HelperPointStore m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty();putReady(n,m.readiness());put(n,"entry_army_id",m.entryArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"helper_resolved_army_id",m.helperResolvedArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"helper_used_fallback",m.helperUsedFallback(),ArmyStrengthsMonthlyCodec::boolNode);put(n,"helper_same_current_army_pointer",m.helperSameCurrentArmyPointer(),ArmyStrengthsMonthlyCodec::boolNode);put(n,"group_count_5c_raw",m.groupCount5cRaw(),ArmyStrengthsMonthlyCodec::integerNode);
        putList(n,"groups",m.groups(),g->{ObjectNode group=empty().put("group_index",g.groupIndex());put(group,"record_count_14_raw",g.recordCount14Raw(),ArmyStrengthsMonthlyCodec::integerNode);put(group,"character_count_2c_raw",g.characterCount2cRaw(),ArmyStrengthsMonthlyCodec::integerNode);putList(group,"record_rows",g.recordRows(),r->{ObjectNode row=empty();putFields(row,r.signed(),ArmyStrengthsMonthlyCodec::integerNode);putFields(row,r.predicates(),ArmyStrengthsMonthlyCodec::boolNode);put(row,"record_regiment_magic_14_raw",r.recordRegimentMagic14Raw(),ArmyStrengthsMonthlyCodec::longNode);put(row,"data_byte_14_raw",r.dataByte14Raw(),ArmyStrengthsMonthlyCodec::integerNode);putList(row,"ordered_persistent_regiment_ids_2a8",r.orderedPersistentRegimentIds2a8(),ArmyStrengthsMonthlyCodec::integerNode);return row;});putList(group,"character_rows",g.characterRows(),r->{ObjectNode row=empty();putFields(row,r.signed(),ArmyStrengthsMonthlyCodec::integerNode);putFields(row,r.predicates(),ArmyStrengthsMonthlyCodec::boolNode);put(row,"child_byte_108_raw",r.childByte108Raw(),ArmyStrengthsMonthlyCodec::integerNode);return row;});return group;});return n;
    }
    public static MonthFirst decodeMonthFirst(JsonNode raw) {
        if(nil(raw))return null;ObjectNode n=closed(raw,"source","status","ready","unavailable_reason","subject_army_id","subject_carmy_id","game_state_calendar_flags_raw_u8","month_first_mask_2_set","actual_pre_date_prepare_observed","actual_post_date_refill_observed","actual_after","full_monthly_ready");equal(n.get("source"),"native_current_month_first_refill_call_inputs");
        for(String key:List.of("actual_pre_date_prepare_observed","actual_post_date_refill_observed","actual_after","full_monthly_ready"))no(n.get(key));
        return new MonthFirst(readiness(n),opt(n,"subject_army_id",ArmyJson::i32),opt(n,"subject_carmy_id",ArmyJson::i32),opt(n,"game_state_calendar_flags_raw_u8",ArmyJson::i32),opt(n,"month_first_mask_2_set",ArmyJson::bool));
    }
    public static JsonNode encodeMonthFirst(MonthFirst m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty().put("source","native_current_month_first_refill_call_inputs").put("actual_pre_date_prepare_observed",false).put("actual_post_date_refill_observed",false).put("actual_after",false).put("full_monthly_ready",false);putReady(n,m.readiness());put(n,"subject_army_id",m.subjectArmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"subject_carmy_id",m.subjectCarmyId(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"game_state_calendar_flags_raw_u8",m.calendarFlagsU8(),ArmyStrengthsMonthlyCodec::integerNode);put(n,"month_first_mask_2_set",m.monthFirstMask2Set(),ArmyStrengthsMonthlyCodec::boolNode);return n;
    }
}
