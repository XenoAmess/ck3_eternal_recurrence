package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;

/** Typed view of the one existing canonical OwnerRecall codec, reused without a second policy validator. */
public final class ArmyStrengthsRecallCodec {
    private ArmyStrengthsRecallCodec() { }
    public enum SourceStatus { AVAILABLE, UNAVAILABLE }
    public enum UnitStatus { AVAILABLE, UNIT_UNRESOLVED, ARMY_UNRESOLVED }
    public enum Collection { FALLBACK_D8, MISSION_90 }
    public enum GovernmentStatus { AVAILABLE, UNAVAILABLE, INVALID_MAGIC, OWNER_LAND_ABSENT }
    public enum PlinSelection { OWNER_FIRST_MATCH, NATIVE_FALLBACK, UNRESOLVED }
    public enum PlinStatus { AVAILABLE, UNAVAILABLE, INVALID_IDENTITY_NATIVE_LITERAL5 }
    public record Recall(SourceStatus status, Optional<String> reason, boolean rawInputsReady, List<Owner> owners) {
        public Recall { Objects.requireNonNull(status);Objects.requireNonNull(reason);owners=List.copyOf(owners); }
    }
    public record Owner(FullId owner,Optional<Integer> land318CountRaw,Optional<FullId> targetSourceTitle,Optional<FullId> nativeRecallTargetProvince,
            String targetStatus,String rosterStatus,boolean rawInputsReady,List<Unit> units,Field<Activity> activity) {
        public Owner {Objects.requireNonNull(owner);Objects.requireNonNull(land318CountRaw);Objects.requireNonNull(targetSourceTitle);Objects.requireNonNull(nativeRecallTargetProvince);Objects.requireNonNull(targetStatus);Objects.requireNonNull(rosterStatus);units=List.copyOf(units);Objects.requireNonNull(activity);}
    }
    public record Unit(PublicUnitId unit,UnitStatus status,Optional<FullId> receiverOwner,Optional<FullId> nativeArmy,Optional<FullId> attachedCombat,Optional<FullId> currentProvince,
            Optional<Integer> army1d4Raw,Optional<Integer> army1ecRaw,Optional<Boolean> firstFallback,Optional<Boolean> secondFallback) {
        public Unit {Objects.requireNonNull(unit);Objects.requireNonNull(status);Objects.requireNonNull(receiverOwner);Objects.requireNonNull(nativeArmy);Objects.requireNonNull(attachedCombat);Objects.requireNonNull(currentProvince);Objects.requireNonNull(army1d4Raw);Objects.requireNonNull(army1ecRaw);Objects.requireNonNull(firstFallback);Objects.requireNonNull(secondFallback);}
    }
    public record Activity(SourceStatus status,Optional<String> reason,boolean membershipObserved,List<Match> matches,Field<OwnerPrefix> ownerPrefix) {
        public Activity {Objects.requireNonNull(status);Objects.requireNonNull(reason);matches=List.copyOf(matches);Objects.requireNonNull(ownerPrefix);}
    }
    public record Match(Collection collection,int storedIndex,int actorCharacterId,SourceStatus status,Optional<String> reason,Optional<Boolean> ePrefixAdmitted,
            Optional<Integer> contextStateRaw,Optional<Integer> context16Raw,Optional<Integer> context2eRaw,Optional<BigInteger> governmentFlags40Raw,Optional<Integer> plinFlags2f0Raw) {
        public Match {Objects.requireNonNull(collection);Objects.requireNonNull(status);Objects.requireNonNull(reason);Objects.requireNonNull(ePrefixAdmitted);Objects.requireNonNull(contextStateRaw);Objects.requireNonNull(context16Raw);Objects.requireNonNull(context2eRaw);Objects.requireNonNull(governmentFlags40Raw);Objects.requireNonNull(plinFlags2f0Raw);}
    }
    public record OwnerPrefix(SourceStatus status,Optional<String> reason,Optional<Boolean> ownerLandPresent,GovernmentStatus governmentStatus,Optional<BigInteger> governmentFlags40Raw,
            Optional<Boolean> governmentBit41,Optional<Boolean> ownerNecessaryCondition,PlinSelection plinSelection,PlinStatus plinStatus,Optional<Integer> plinFlags2f0Raw,Optional<Boolean> plinBit8) {
        public OwnerPrefix {Objects.requireNonNull(status);Objects.requireNonNull(reason);Objects.requireNonNull(ownerLandPresent);Objects.requireNonNull(governmentStatus);Objects.requireNonNull(governmentFlags40Raw);Objects.requireNonNull(governmentBit41);Objects.requireNonNull(ownerNecessaryCondition);Objects.requireNonNull(plinSelection);Objects.requireNonNull(plinStatus);Objects.requireNonNull(plinFlags2f0Raw);Objects.requireNonNull(plinBit8);}
    }
    private static <T> Optional<T> opt(ObjectNode n,String key,Function<JsonNode,T> parse) {JsonNode value=get(n,key);return value.isNull()?Optional.empty():Optional.of(parse.apply(value));}
    private static <E extends Enum<E>> E enumeration(JsonNode n,Class<E> type) {return ArmyStrengthsCodec.enumText(n,type);}
    private static <T> void put(ObjectNode n,String key,Optional<T> value,Function<T,JsonNode> encode) {if(value.isPresent())n.set(key,encode.apply(value.orElseThrow()));else n.putNull(key);}
    private static JsonNode s(String value){return empty().textNode(value);} private static JsonNode i(Integer value){return empty().numberNode(value);} private static JsonNode b(Boolean value){return empty().booleanNode(value);} private static JsonNode wide(BigInteger value){return empty().numberNode(value);} private static JsonNode fullNode(FullId value){return i(value.value());}
    public static Recall decode(JsonNode raw) {
        // The strengths producer explicitly calls lifecycle_status="available" even for an independently unavailable recall leaf.
        JsonNode actual=BattleOwnerRecallCodec.normalize(raw,true);if(actual.isNull())return null;ObjectNode n=object(actual);
        return new Recall(enumeration(n.get("status"),SourceStatus.class),opt(n,"unavailable_reason",ArmyJson::nonempty),bool(n.get("raw_inputs_ready")),array(n.get("owners_in_stored_order"),ArmyStrengthsRecallCodec::owner));
    }
    private static Owner owner(JsonNode raw) {ObjectNode n=object(raw);return new Owner(full(n.get("owner_character_id")),opt(n,"land_318_count_raw",ArmyJson::i32),opt(n,"owner_target_source_title_id",ArmyJson::full),opt(n,"owner_native_recall_target_province_id",ArmyJson::full),nonempty(n.get("target_status")),nonempty(n.get("owned_cunit_roster_status")),bool(n.get("raw_inputs_ready")),array(n.get("owned_cunits_in_stored_order"),ArmyStrengthsRecallCodec::unit),field(n,"native_activity_context_v1",ArmyStrengthsRecallCodec::activity));}
    private static Unit unit(JsonNode raw) {ObjectNode n=object(raw);return new Unit(ArmyJson.unit(n.get("public_cunit_id")),enumeration(n.get("status"),UnitStatus.class),opt(n,"receiver_owner_character_id",ArmyJson::full),opt(n,"native_carmy_id",ArmyJson::full),opt(n,"attached_combat_id",ArmyJson::full),opt(n,"current_province_id",ArmyJson::full),opt(n,"army_1d4_raw",ArmyJson::i32),opt(n,"army_1ec_raw",ArmyJson::i32),opt(n,"first_fallback_raw_condition",ArmyJson::bool),opt(n,"second_fallback_raw_condition",ArmyJson::bool));}
    private static Activity activity(JsonNode raw) {ObjectNode n=object(raw);return new Activity(enumeration(n.get("status"),SourceStatus.class),opt(n,"unavailable_reason",ArmyJson::nonempty),bool(n.get("membership_observed")),array(n.get("matched_contexts_in_native_order"),ArmyStrengthsRecallCodec::match),field(n,"owner_prefix_inputs",ArmyStrengthsRecallCodec::prefix));}
    private static Match match(JsonNode raw) {ObjectNode n=object(raw);return new Match(enumeration(n.get("collection"),Collection.class),i32(n.get("stored_index")),i32(n.get("actor_character_id")),enumeration(n.get("status"),SourceStatus.class),opt(n,"unavailable_reason",ArmyJson::nonempty),opt(n,"e_prefix_admitted",ArmyJson::bool),opt(n,"context_state_raw",ArmyJson::i32),opt(n,"context_16_raw",ArmyJson::i32),opt(n,"context_2e_raw",ArmyJson::i32),opt(n,"government_flags_40_raw",ArmyJson::integer),opt(n,"plin_flags_2f0_raw",ArmyJson::i32));}
    private static OwnerPrefix prefix(JsonNode raw) {ObjectNode n=object(raw);return new OwnerPrefix(enumeration(n.get("status"),SourceStatus.class),opt(n,"unavailable_reason",ArmyJson::nonempty),opt(n,"owner_land_present",ArmyJson::bool),enumeration(n.get("government_status"),GovernmentStatus.class),opt(n,"government_flags_40_raw",ArmyJson::integer),opt(n,"government_bit41",ArmyJson::bool),opt(n,"owner_necessary_condition",ArmyJson::bool),enumeration(n.get("plin_selection"),PlinSelection.class),enumeration(n.get("plin_status"),PlinStatus.class),opt(n,"plin_flags_2f0_raw",ArmyJson::i32),opt(n,"plin_bit8",ArmyJson::bool));}
    public static JsonNode encode(Recall m) {
        if(m==null)return empty().nullNode();ObjectNode n=empty().put("schema_version",1).put("status",ArmyStrengthsCodec.wire(m.status())).put("raw_inputs_ready",m.rawInputsReady()).put("native_context_prefix_status","unobserved_scheduler_context").putNull("native_context_prefix_admitted").put("native_selection_ready",false);put(n,"unavailable_reason",m.reason(),ArmyStrengthsRecallCodec::s);var owners=n.putArray("owners_in_stored_order");m.owners().forEach(owner->owners.add(ownerNode(owner)));return BattleOwnerRecallCodec.normalize(n,true);
    }
    private static ObjectNode ownerNode(Owner m) {ObjectNode n=empty().put("owner_character_id",m.owner().value()).put("target_status",m.targetStatus()).put("owned_cunit_roster_status",m.rosterStatus()).put("raw_inputs_ready",m.rawInputsReady());put(n,"land_318_count_raw",m.land318CountRaw(),ArmyStrengthsRecallCodec::i);put(n,"owner_target_source_title_id",m.targetSourceTitle(),ArmyStrengthsRecallCodec::fullNode);put(n,"owner_native_recall_target_province_id",m.nativeRecallTargetProvince(),ArmyStrengthsRecallCodec::fullNode);var units=n.putArray("owned_cunits_in_stored_order");m.units().forEach(unit->units.add(unitNode(unit)));ArmyStrengthsCodec.put(n,"native_activity_context_v1",m.activity(),ArmyStrengthsRecallCodec::activityNode);return n;}
    private static ObjectNode unitNode(Unit m) {ObjectNode n=empty().put("public_cunit_id",m.unit().value()).put("status",ArmyStrengthsCodec.wire(m.status()));put(n,"receiver_owner_character_id",m.receiverOwner(),ArmyStrengthsRecallCodec::fullNode);put(n,"native_carmy_id",m.nativeArmy(),ArmyStrengthsRecallCodec::fullNode);put(n,"attached_combat_id",m.attachedCombat(),ArmyStrengthsRecallCodec::fullNode);put(n,"current_province_id",m.currentProvince(),ArmyStrengthsRecallCodec::fullNode);put(n,"army_1d4_raw",m.army1d4Raw(),ArmyStrengthsRecallCodec::i);put(n,"army_1ec_raw",m.army1ecRaw(),ArmyStrengthsRecallCodec::i);put(n,"first_fallback_raw_condition",m.firstFallback(),ArmyStrengthsRecallCodec::b);put(n,"second_fallback_raw_condition",m.secondFallback(),ArmyStrengthsRecallCodec::b);return n;}
    private static ObjectNode activityNode(Activity m) {ObjectNode n=empty().put("schema_version",1).put("status",ArmyStrengthsCodec.wire(m.status())).put("membership_observed",m.membershipObserved());put(n,"unavailable_reason",m.reason(),ArmyStrengthsRecallCodec::s);var matches=n.putArray("matched_contexts_in_native_order");m.matches().forEach(match->matches.add(matchNode(match)));ArmyStrengthsCodec.put(n,"owner_prefix_inputs",m.ownerPrefix(),ArmyStrengthsRecallCodec::prefixNode);return n;}
    private static ObjectNode matchNode(Match m) {ObjectNode n=empty().put("collection",ArmyStrengthsCodec.wire(m.collection())).put("prefix_kind","e_1a781a0").put("stored_index",m.storedIndex()).put("actor_character_id",m.actorCharacterId()).put("status",ArmyStrengthsCodec.wire(m.status()));put(n,"unavailable_reason",m.reason(),ArmyStrengthsRecallCodec::s);put(n,"e_prefix_admitted",m.ePrefixAdmitted(),ArmyStrengthsRecallCodec::b);put(n,"context_state_raw",m.contextStateRaw(),ArmyStrengthsRecallCodec::i);put(n,"context_16_raw",m.context16Raw(),ArmyStrengthsRecallCodec::i);put(n,"context_2e_raw",m.context2eRaw(),ArmyStrengthsRecallCodec::i);put(n,"government_flags_40_raw",m.governmentFlags40Raw(),ArmyStrengthsRecallCodec::wide);put(n,"plin_flags_2f0_raw",m.plinFlags2f0Raw(),ArmyStrengthsRecallCodec::i);return n;}
    private static ObjectNode prefixNode(OwnerPrefix m) {ObjectNode n=empty().put("status",ArmyStrengthsCodec.wire(m.status())).put("government_status",ArmyStrengthsCodec.wire(m.governmentStatus())).put("plin_selection",ArmyStrengthsCodec.wire(m.plinSelection())).put("plin_status",ArmyStrengthsCodec.wire(m.plinStatus()));put(n,"unavailable_reason",m.reason(),ArmyStrengthsRecallCodec::s);put(n,"owner_land_present",m.ownerLandPresent(),ArmyStrengthsRecallCodec::b);put(n,"government_flags_40_raw",m.governmentFlags40Raw(),ArmyStrengthsRecallCodec::wide);put(n,"government_bit41",m.governmentBit41(),ArmyStrengthsRecallCodec::b);put(n,"owner_necessary_condition",m.ownerNecessaryCondition(),ArmyStrengthsRecallCodec::b);put(n,"plin_flags_2f0_raw",m.plinFlags2f0Raw(),ArmyStrengthsRecallCodec::i);put(n,"plin_bit8",m.plinBit8(),ArmyStrengthsRecallCodec::b);return n;}
}
