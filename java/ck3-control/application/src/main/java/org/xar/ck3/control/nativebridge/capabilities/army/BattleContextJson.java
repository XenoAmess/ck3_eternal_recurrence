package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;

/** Single strict JSON boundary shared by the exact native context and PERSON codecs. */
final class BattleContextJson {
    private BattleContextJson() { }
    @FunctionalInterface interface ElementNormalizer { JsonNode normalize(JsonNode raw,String field); }
    enum Status { AVAILABLE("available"), PARTIAL("partial"), UNAVAILABLE("unavailable");
        final String wire;Status(String wire) { this.wire=wire; }
        static Status decode(JsonNode raw,String field) {
            String value=string(text(raw,field,false,true));
            for(Status status:values())if(status.wire.equals(value))return status;
            throw bad(field,"unknown native availability status");
        }
    }
    record Availability(Status status,boolean ready,String reason) { }
    static ObjectNode object() { return JsonNodeFactory.instance.objectNode(); }
    static ArrayNode list() { return JsonNodeFactory.instance.arrayNode(); }
    static IllegalArgumentException bad(String field,String message) { return new IllegalArgumentException(field+": "+message); }
    static void require(boolean condition,String field,String message) { if(!condition)throw bad(field,message); }
    static ObjectNode exact(JsonNode raw,String field,Set<String> required) { return exact(raw,field,required,Set.of()); }
    static ObjectNode exact(JsonNode raw,String field,Set<String> required,Set<String> optional) {
        require(raw instanceof ObjectNode,field,"native object required");
        var keys=new HashSet<String>();raw.fieldNames().forEachRemaining(keys::add);
        var allowed=new HashSet<>(required);allowed.addAll(optional);
        require(keys.containsAll(required) && allowed.containsAll(keys),field,"exact fields disagree");
        return (ObjectNode)raw;
    }
    static boolean nil(JsonNode raw) { return raw!=null && raw.isNull(); }
    static JsonNode number(JsonNode raw,String field,int bits,boolean unsigned,boolean nullable) {
        require(bits>=1 && bits<=64,field,"supported native integer width required");
        if(nullable && nil(raw))return NullNode.instance;
        require(raw!=null && raw.isIntegralNumber(),field,"native integer token required");
        BigInteger value=raw.bigIntegerValue();
        BigInteger minimum=unsigned ? BigInteger.ZERO : BigInteger.ONE.shiftLeft(bits-1).negate();
        BigInteger maximum=BigInteger.ONE.shiftLeft(unsigned ? bits : bits-1).subtract(BigInteger.ONE);
        require(value.compareTo(minimum)>=0 && value.compareTo(maximum)<=0,field,"native "+(unsigned?"unsigned":"signed")+bits+" range");
        return BigIntegerNode.valueOf(value);
    }
    static JsonNode bool(JsonNode raw,String field,boolean nullable) {
        if(nullable && nil(raw))return NullNode.instance;
        require(raw!=null && raw.isBoolean(),field,"native Boolean token required");
        return BooleanNode.valueOf(raw.booleanValue());
    }
    static JsonNode text(JsonNode raw,String field,boolean nullable,boolean nonempty) {
        if(nullable && nil(raw))return NullNode.instance;
        require(raw!=null && raw.isTextual() && (!nonempty || !raw.textValue().isEmpty()),field,"string token"+(nonempty?" must be nonempty":" required"));
        return TextNode.valueOf(raw.textValue());
    }
    static JsonNode array(JsonNode raw,String field,boolean nullable,ElementNormalizer normalize) {
        if(nullable && nil(raw))return NullNode.instance;
        require(raw instanceof ArrayNode,field,"native-order array required");
        ArrayNode result=list();for(int index=0;index<raw.size();index++)result.add(normalize.normalize(raw.get(index),field+"["+index+"]"));
        return result;
    }
    static JsonNode numbers(JsonNode raw,String field,int bits,boolean unsigned,boolean nullable,boolean nullableItems) {
        return array(raw,field,nullable,(item,name)->number(item,name,bits,unsigned,nullableItems));
    }
    static BigInteger integer(JsonNode raw) { return nil(raw) ? null : raw.bigIntegerValue(); }
    static BigInteger integer(ObjectNode raw,String key) { return integer(raw.get(key)); }
    static Boolean booleanValue(JsonNode raw) { return nil(raw) ? null : raw.booleanValue(); }
    static Boolean booleanValue(ObjectNode raw,String key) { return booleanValue(raw.get(key)); }
    static String string(JsonNode raw) { return nil(raw) ? null : raw.textValue(); }
    static Availability availability(ObjectNode raw,String field,String reasonKey) {
        Status status=Status.decode(raw.get("status"),field+".status");
        boolean ready=bool(raw.get("ready"),field+".ready",false).booleanValue();
        String reason=string(text(raw.get(reasonKey),field+"."+reasonKey,true,true));
        require(ready==(status==Status.AVAILABLE) && (ready ? reason==null : reason!=null),field,"availability disagrees with reason");
        return new Availability(status,ready,reason);
    }
    static Availability availability(ObjectNode raw,String field) { return availability(raw,field,"reason"); }
    static void availabilityFields(ObjectNode result,Availability actual,String reasonKey) {
        result.put("status",actual.status().wire);result.put("ready",actual.ready());
        if(actual.reason()==null)result.putNull(reasonKey);else result.put(reasonKey,actual.reason());
    }
    static JsonNode properties(JsonNode raw,String field) {
        if(nil(raw))return NullNode.instance;
        ObjectNode row=exact(raw,field,Set.of("keys_count","values_count","keys_u16","values_q64","reason"));
        ObjectNode result=object();
        result.set("keys_count",number(row.get("keys_count"),field+".keys_count",32,false,true));
        result.set("values_count",number(row.get("values_count"),field+".values_count",32,false,true));
        result.set("keys_u16",numbers(row.get("keys_u16"),field+".keys_u16",16,true,true,false));
        result.set("values_q64",numbers(row.get("values_q64"),field+".values_q64",64,false,true,false));
        result.set("reason",text(row.get("reason"),field+".reason",true,true));return result;
    }
    static boolean propertiesReady(JsonNode raw) {
        if(raw==null || nil(raw))return false;
        BigInteger count=integer(raw.get("keys_count"));
        if(BigInteger.ZERO.equals(count))return true;
        if(count==null || count.signum()<0)return false;
        JsonNode keys=raw.get("keys_u16"),values=raw.get("values_q64");
        return keys.isArray() && values.isArray() && count.compareTo(BigInteger.valueOf(keys.size()))<=0 && count.compareTo(BigInteger.valueOf(values.size()))<=0;
    }
    static boolean trueValue(ObjectNode raw,String key) { return Boolean.TRUE.equals(booleanValue(raw,key)); }
    static boolean falseValue(ObjectNode raw,String key) { return Boolean.FALSE.equals(booleanValue(raw,key)); }
    static void sameActor(JsonNode section,BigInteger actor,String field) {
        if(!nil(section))require(actor.equals(integer(section.get("character_id"))),field,"nested character differs from enclosing native actor");
    }
}
