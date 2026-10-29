package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One narrow JSON boundary for the original public combat algorithms. */
final class CombatProjectionJson {
    private CombatProjectionJson() { }
    static ObjectNode obj() { return ArmyJson.empty(); }
    static ObjectNode object(JsonNode n) { StrictJson.require(n instanceof ObjectNode,"original combat projection object required");return (ObjectNode)n; }
    static ArrayNode array(JsonNode n) { StrictJson.require(n instanceof ArrayNode,"original combat projection array required");return (ArrayNode)n; }
    static Obj immutable(ObjectNode n) { return DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES); }
    static ObjectNode node(Obj n) { return object(OpportunityJson.toNode(n)); }
    static boolean yes(JsonNode n) { return n!=null&&n.isBoolean()&&n.booleanValue(); }
    static boolean nil(JsonNode n) { return n==null||n.isNull(); }
    static BigInteger integer(JsonNode n) { StrictJson.require(n!=null&&n.isIntegralNumber(),"exact original combat integer required");return n.bigIntegerValue(); }
    static BigInteger identity(JsonNode n) {
        if(nil(n))return null;if(n.isIntegralNumber())return n.bigIntegerValue();
        if(n.isTextual()&&n.textValue().matches("0[xX][0-9a-fA-F]+"))return new BigInteger(n.textValue().substring(2),16);
        throw new IllegalArgumentException("exact original integer/hex identity required");
    }
    static String text(JsonNode n) { StrictJson.require(n!=null&&n.isTextual(),"original combat text required");return n.textValue(); }
    static void copy(JsonNode from,ObjectNode to,String fields) { for(String field:fields.split(" ")){StrictJson.require(from.has(field),"missing normalized combat field "+field);to.set(field,from.get(field).deepCopy());} }
    static void nullable(ObjectNode n,String key,Number value) {
        if(value==null)n.putNull(key);else if(value instanceof BigInteger b)n.put(key,b);else n.put(key,value.longValue());
    }
    static void strings(ObjectNode n,String key,Iterable<String> values) { ArrayNode a=n.putArray(key);values.forEach(a::add); }
    static void values(ObjectNode n,String key,List<BigInteger> values) { var a=n.putArray(key);for(var value:values)if(value==null)a.addNull();else a.add(value); }
    static JsonNode at(JsonNode n,int i) { return n!=null&&n.isArray()&&i<n.size()?n.get(i):null; }
    static boolean eq(JsonNode a,JsonNode b) { return nil(a)?nil(b):!nil(b)&&a.equals(b); }
}
