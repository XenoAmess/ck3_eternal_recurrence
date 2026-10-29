package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite dynamic boundary for the ten historical Person JSON contracts. Every field is consumed once. */
final class PersonCurrentJson {
    static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    static final BigInteger UNIT=BigInteger.valueOf(100000);
    private PersonCurrentJson() { }
    @FunctionalInterface interface Parser { JsonNode parse(JsonNode value,String field); }
    static final class Row {
        final ObjectNode raw,out=StrictJson.object();final Set<String> consumed=new HashSet<>();final String field;
        Row(JsonNode raw,String field){need(raw!=null&&raw.isObject(),field+" must be an object");this.raw=(ObjectNode)raw;this.field=field;}
        JsonNode take(String name){need(consumed.add(name)&&raw.has(name),field+" missing/repeated field "+name);return raw.get(name);}
        Row strings(boolean nullable,String names){for(String k:keys(names))out.set(k,text(take(k),field+"."+k,nullable,false));return this;}
        Row numbers(int bits,boolean unsigned,boolean nullable,String names){for(String k:keys(names))out.set(k,number(take(k),field+"."+k,bits,unsigned,nullable));return this;}
        Row booleans(boolean nullable,String names){for(String k:keys(names))out.set(k,BattleContextJson.bool(take(k),field+"."+k,nullable));return this;}
        Row child(String name,Parser parser){out.set(name,parser.parse(take(name),field+"."+name));return this;}
        Row children(String name,Parser parser,boolean ordered){JsonNode n=take(name);need(n.isArray(),field+" ordered array required: "+name);ArrayNode a=out.putArray(name);int index=0;for(JsonNode value:n){JsonNode child=parser.parse(value,field+"."+name+"["+index+"]");if(ordered)need(eq(i(child,"native_index"),BigInteger.valueOf(index)),field+" physical order changed");a.add(child);index++;}return this;}
        ObjectNode done(){Set<String> actual=new HashSet<>();raw.fieldNames().forEachRemaining(actual::add);need(actual.equals(consumed),field+" unexpected/missing fields: "+actual+" / "+consumed);return out;}
    }
    static Row base(JsonNode raw,String field,String schema){Row b=new Row(raw,field);b.strings(false,"schema build_version executable_sha256");need(schema.equals(s(b.out,"schema"))&&"1.20.0.4".equals(s(b.out,"build_version"))&&EXE.equalsIgnoreCase(s(b.out,"executable_sha256")),field+" requires exact actual4 source");b.out.put("executable_sha256",EXE);return b;}
    static JsonNode text(JsonNode n,String field,boolean nullable,boolean empty){return BattleContextJson.text(n,field,nullable,!empty);}
    static JsonNode number(JsonNode n,String field,int bits,boolean unsigned,boolean nullable){return BattleContextJson.number(n,field,bits,unsigned,nullable);}
    static JsonNode q64(JsonNode n,String field,boolean nullable){if(nullable&&n.isNull())return n;if(n.isTextual()){need(n.textValue().matches("-?[0-9]+"),field+" native signed64 decimal required");n=StrictJson.object().put("v",new BigInteger(n.textValue())).get("v");}return number(n,field,64,false,false);}
    static JsonNode pcValues(JsonNode raw,String field){if(raw.isNull())return raw;Row b=new Row(raw,field);for(String name:List.of("keys_u16","values_q64")){JsonNode values=b.take(name);if(values.isNull())b.out.putNull(name);else{need(values.isArray(),field+" property array required");ArrayNode a=b.out.putArray(name);int index=0;for(JsonNode n:values)a.add(name.equals("keys_u16")?number(n,field+"["+index+++"]",16,true,false):q64(n,field+"["+index+++"]",false));}}return b.done();}
    static void need(boolean value,String message){StrictJson.require(value,message);}
    static List<String> keys(String names){return names.isEmpty()?List.of():List.of(names.split(" "));}
    static BigInteger i(JsonNode n,String k){JsonNode v=n.get(k);return v==null||v.isNull()?null:v.bigIntegerValue();}
    static String s(JsonNode n,String k){JsonNode v=n.get(k);return v==null||v.isNull()?null:v.textValue();}
    static Boolean b(JsonNode n,String k){JsonNode v=n.get(k);return v==null||v.isNull()?null:v.booleanValue();}
    static boolean yes(JsonNode n,String k){return Boolean.TRUE.equals(b(n,k));}
    static boolean eq(Object a,Object b){return Objects.equals(a,b);}
    static boolean num(JsonNode n,String k,long v){return BigInteger.valueOf(v).equals(i(n,k));}
    static boolean exists(JsonNode n,String k){return n.has(k)&&!n.get(k).isNull();}
    static int count(JsonNode n,String k){return n.get(k).size();}
    static boolean nonnegative(BigInteger n){return n!=null&&n.signum()>=0;}
    static void state(JsonNode n,String ready,String reason,String field){need(yes(n,ready)?s(n,reason)==null:s(n,reason)!=null&&!s(n,reason).isEmpty(),field+" readiness/reason disagree");}
    static boolean allReady(JsonNode values){for(JsonNode n:values)if(!yes(n,"ready"))return false;return true;}
    static void exactCount(JsonNode n,String count,String rows,String field){need(nonnegative(i(n,count))&&eq(i(n,count),BigInteger.valueOf(n.get(rows).size())),field+" physical count mismatch");}
    static boolean selected(String value,String... allowed){for(String v:allowed)if(eq(value,v))return true;return false;}
    static JsonNode nil(){return NullNode.instance;}
}
