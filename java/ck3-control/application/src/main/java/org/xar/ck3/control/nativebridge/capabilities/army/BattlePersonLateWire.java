package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/** Narrow normalized-JSON boundary shared by the eleven actual late PERSON contracts. */
final class BattlePersonLateWire {
    private BattlePersonLateWire() { }
    static final BigInteger U32MAX = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    static ObjectNode shape(JsonNode raw,String field,String... fields) { return exact(raw,field,Set.of(fields)); }
    static ObjectNode start(JsonNode raw,String field,String... fields) {
        var keys=new HashSet<>(Arrays.asList(fields));keys.addAll(Set.of("status","ready","reason"));
        ObjectNode actual=exact(raw,field,keys),result=object();availabilityFields(result,availability(actual,field),"reason");return result;
    }
    static void nums(JsonNode raw,ObjectNode out,String field,int bits,boolean unsigned,String... keys) {
        for(String key:keys)out.set(key,number(raw.get(key),field+"."+key,bits,unsigned,true));
    }
    static void texts(JsonNode raw,ObjectNode out,String field,String... keys) {
        for(String key:keys)out.set(key,text(raw.get(key),field+"."+key,true,true));
    }
    static void bools(JsonNode raw,ObjectNode out,String field,String... keys) {
        for(String key:keys)out.set(key,bool(raw.get(key),field+"."+key,true));
    }
    static JsonNode word(JsonNode value,String field) {
        if(value!=null && value.isTextual()) {
            String token=value.textValue();
            require(token.matches("0[xX][0-9a-fA-F]{1,16}"),field,"native uint64 or hexadecimal pointer required");
            value=BigIntegerNode.valueOf(new BigInteger(token.substring(2),16));
        }
        return number(value,field,64,true,true);
    }
    static void words(JsonNode raw,ObjectNode out,String field,String... keys) {
        for(String key:keys)out.set(key,word(raw.get(key),field+"."+key));
    }
    static void index(JsonNode raw,ObjectNode out,String field,boolean unsigned) {
        out.set("native_index",number(raw.get("native_index"),field+".native_index",32,unsigned,false));
    }
    static void order(JsonNode rows,String field) {
        if(nil(rows))return;
        for(int i=0;i<rows.size();i++)require(BigInteger.valueOf(i).equals(integer(rows.get(i).get("native_index"))),field,"native physical row order differs");
    }
    static void prefix(JsonNode count,JsonNode rows,String field) {
        BigInteger n=integer(count);
        if(n!=null && !nil(rows))require(BigInteger.valueOf(rows.size()).compareTo(n.max(BigInteger.ZERO))<=0,field,"rows exceed actual physical count");
    }
    static JsonNode pc(JsonNode raw,String field) {
        ObjectNode row=shape(raw,field,"property_identity","property_block","reason"),out=object();
        texts(row,out,field,"property_identity","reason");out.set("property_block",properties(row.get("property_block"),field+".property_block"));return out;
    }
    static boolean pcReady(JsonNode pc) {
        return !nil(pc.get("property_identity")) && nil(pc.get("reason")) && propertiesReady(pc.get("property_block")) && nil(pc.get("property_block").get("reason"));
    }
    static boolean absentPc(JsonNode pc) { return nil(pc.get("property_identity")) && nil(pc.get("property_block")); }
    static boolean allNull(JsonNode row,String... keys) { for(String key:keys)if(!nil(row.get(key)))return false;return true; }
    static boolean eq(JsonNode value,long expected) { return BigInteger.valueOf(expected).equals(integer(value)); }
    static boolean is(JsonNode value,String expected) { return Objects.equals(string(value),expected); }
    static boolean positive(JsonNode value) { BigInteger number=integer(value);return number!=null && number.signum()>0; }
    static boolean zero(JsonNode value) { return eq(value,0); }
    static Boolean compare(JsonNode first,JsonNode second) {
        return nil(first)||nil(second) ? null : integer(first).equals(integer(second));
    }
    static void same(JsonNode actual,Object expected,String field,String message) {
        Object value=expected instanceof Boolean || actual!=null&&actual.isBoolean() ? booleanValue(actual)
                : expected instanceof String || actual!=null&&actual.isTextual() ? string(actual) : integer(actual);
        require(Objects.equals(value,expected),field,message);
    }
    static void rowReason(JsonNode row,boolean ready,String field) {
        require(row.get("ready").booleanValue()==ready && (ready ? nil(row.get("reason")) : !nil(row.get("reason"))),field,"independent readiness/reason differs from demanded operands");
    }
    static void ready(JsonNode row,boolean complete,String field) {
        require(row.get("ready").booleanValue()==(complete&&nil(row.get("reason"))),field,"readiness differs from demanded source inputs");
    }
    static BigInteger wrap(BigInteger value,int bits) {
        BigInteger mask=BigInteger.ONE.shiftLeft(bits);value=value.mod(mask);return value.testBit(bits-1)?value.subtract(mask):value;
    }
}
