package org.xar.ck3.control.nativebridge.capabilities.activity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class ActivityJson {
    static final BigInteger U32 = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE), U64 = StrictJson.UINT64_MAX;
    static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate(), I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    static final String FRAME = "schema snapshot_revision date_raw actor_character_id";
    private ActivityJson() { }
    static ObjectNode parse(byte[] bytes) { JsonNode node = StrictJson.parse(bytes,StrictJson.EXPLICIT_MAX_BYTES); need(node.isObject(),"activity object required"); return (ObjectNode)node; }
    static ObjectNode exact(JsonNode node,String keys) { return StrictJson.object(node,keys.isEmpty() ? Set.of() : Set.of(keys.split(" "))); }
    static ObjectNode allowed(JsonNode node,String required,String optional) {
        need(node != null && node.isObject(),"activity object required"); Set<String> keys = new HashSet<>(); node.fieldNames().forEachRemaining(keys::add);
        Set<String> requiredKeys = required.isEmpty() ? Set.of() : Set.of(required.split(" ")); Set<String> allowed = new HashSet<>(requiredKeys); if(!optional.isEmpty())allowed.addAll(Set.of(optional.split(" ")));
        need(keys.containsAll(requiredKeys) && allowed.containsAll(keys),"activity missing or unknown fields"); return (ObjectNode)node;
    }
    static OpportunityJson.Obj app(JsonNode node) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(node,StrictJson.EXPLICIT_MAX_BYTES)),"validated activity body"); }
    static RawJson raw(JsonNode node) { return new RawJson(StrictJson.canonical(node,StrictJson.EXPLICIT_MAX_BYTES)); }
    static ObjectNode argument(OpportunityJson.Obj body) { return parse(OpportunityJson.encode(body)); }
    static String text(JsonNode row,String key) { return StrictJson.text(row.get(key)); }
    static void eq(JsonNode row,String key,String value) { need(text(row,key).equals(value),key+" differs"); }
    static BigInteger number(JsonNode row,String key,BigInteger minimum,BigInteger maximum) { return StrictJson.integer(row.get(key),minimum,maximum); }
    static BigInteger u64(JsonNode row,String key) { return number(row,key,BigInteger.ZERO,U64); }
    static BigInteger positive(JsonNode row,String key) { return number(row,key,BigInteger.ONE,U64); }
    static BigInteger signed(JsonNode row,String key) { return number(row,key,I64_MIN,I64_MAX); }
    static int integer(JsonNode row,String key,int minimum,int maximum) { return (int)StrictJson.integer(row.get(key),minimum,maximum); }
    static long id(JsonNode row,String key) { return number(row,key,BigInteger.ONE,U32).longValueExact(); }
    static boolean bool(JsonNode row,String key) { JsonNode node=row.get(key); need(node!=null && node.isBoolean(),"boolean required: "+key); return node.booleanValue(); }
    static void yes(JsonNode row,String key) { need(bool(row,key),key+" must be true"); }
    static void no(JsonNode row,String key) { need(!bool(row,key),key+" must be false"); }
    static void nil(JsonNode row,String key) { need(row.has(key) && row.get(key).isNull(),"explicit null required: "+key); }
    static void fingerprint(JsonNode row,String key) { need(text(row,key).matches("0x[0-9a-f]{16}"),"native source fingerprint"); }
    static void rule(String value) { need(value!=null && value.length()<=96 && value.matches("activity_invite_rule_[a-z0-9_]+"),"authored invitation rule"); }
    static void need(boolean condition,String reason) { if(!condition)throw new IllegalArgumentException(reason); }
}
