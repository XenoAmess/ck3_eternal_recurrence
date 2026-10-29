package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Single closed native-copy boundary for owned historical Army observations. */
final class ArmyOwnedJson {
    private ArmyOwnedJson() { }
    static final JsonNodeFactory J=JsonNodeFactory.instance;
    static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE),U32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    static void need(boolean condition,String message){if(!condition)throw new IllegalArgumentException("owned Army "+message);}
    static ObjectNode obj(){return J.objectNode();}static ArrayNode arr(){return J.arrayNode();}
    static ObjectNode object(JsonNode value){need(value instanceof ObjectNode,"object required");return (ObjectNode)value;}
    static ArrayNode array(JsonNode value){need(value instanceof ArrayNode,"array required");return (ArrayNode)value;}
    static Set<String> names(JsonNode value){Set<String> out=new HashSet<>();object(value).fieldNames().forEachRemaining(out::add);return out;}
    static void keys(JsonNode value,String names){need(names(value).equals(Set.of(names.split(" "))),"exact owned shape differs");}
    static JsonNode get(JsonNode row,String key){JsonNode value=row.get(key);need(value!=null,"missing "+key);return value;}
    static String text(JsonNode value){need(value!=null&&value.isTextual(),"text required");return value.textValue();}
    static boolean bool(JsonNode value){need(value!=null&&value.isBoolean(),"boolean required");return value.booleanValue();}
    static Boolean maybeBool(JsonNode value){return getNil(value)?null:bool(value);}
    static boolean getNil(JsonNode value){need(value!=null,"missing nullable field");return value.isNull();}
    static BigInteger integer(JsonNode value,int bits,boolean signed,boolean nullable){if(nullable&&getNil(value))return null;need(value!=null&&value.isIntegralNumber(),"integer token required");BigInteger n=value.bigIntegerValue(),lower=signed?BigInteger.ONE.shiftLeft(bits-1).negate():BigInteger.ZERO,upper=BigInteger.ONE.shiftLeft(signed?bits-1:bits);need(n.compareTo(lower)>=0&&n.compareTo(upper)<0,"raw integer width differs");return n;}
    static BigInteger u64(JsonNode value){return integer(value,64,false,false);}static BigInteger nu64(JsonNode value){return integer(value,64,false,true);}
    static long u32(JsonNode value){return integer(value,32,false,false).longValueExact();}static Long nu32(JsonNode value){BigInteger n=integer(value,32,false,true);return n==null?null:n.longValueExact();}
    static int i32(JsonNode value){return integer(value,32,true,false).intValueExact();}static Integer ni32(JsonNode value){BigInteger n=integer(value,32,true,true);return n==null?null:n.intValueExact();}
    static int u16(JsonNode value){return integer(value,16,false,false).intValueExact();}static Integer nu16(JsonNode value){BigInteger n=integer(value,16,false,true);return n==null?null:n.intValueExact();}
    static Integer nu8(JsonNode value){BigInteger n=integer(value,8,false,true);return n==null?null:n.intValueExact();}
    static void put(ObjectNode out,String key,BigInteger value){if(value==null)out.putNull(key);else out.put(key,value);}static void put(ObjectNode out,String key,Integer value){if(value==null)out.putNull(key);else out.put(key,value);}static void put(ObjectNode out,String key,Long value){if(value==null)out.putNull(key);else out.put(key,value);}static void put(ObjectNode out,String key,Boolean value){if(value==null)out.putNull(key);else out.put(key,value);}
    static boolean eq(JsonNode a,JsonNode b){if(a==null||b==null)return a==b;if(a.isIntegralNumber()||b.isIntegralNumber())return a.isIntegralNumber()&&b.isIntegralNumber()&&a.bigIntegerValue().equals(b.bigIntegerValue());if(a.isObject()&&b.isObject()){if(!names(a).equals(names(b)))return false;for(String key:names(a))if(!eq(a.get(key),b.get(key)))return false;return true;}if(a.isArray()&&b.isArray()){if(a.size()!=b.size())return false;for(int i=0;i<a.size();i++)if(!eq(a.get(i),b.get(i)))return false;return true;}return a.equals(b);}
    static BigInteger n(JsonNode value){need(value!=null&&value.isIntegralNumber(),"validated integer required");return value.bigIntegerValue();}
    static boolean is(JsonNode row,String key,boolean expected){return get(row,key).isBoolean()&&row.get(key).booleanValue()==expected;}
    static boolean hasNumber(JsonNode row,String key,long expected){return get(row,key).isIntegralNumber()&&n(row.get(key)).equals(BigInteger.valueOf(expected));}
    static boolean nil(JsonNode row,String key){return get(row,key).isNull();}
    static boolean anyNil(JsonNode row,String fields){for(String key:fields.split(" "))if(nil(row,key))return true;return false;}
    static boolean allNil(JsonNode row,String fields){for(String key:fields.split(" "))if(!nil(row,key))return false;return true;}
    static boolean contains(JsonNode rows,BigInteger id){for(JsonNode item:array(rows))if(item.isIntegralNumber()&&n(item).equals(id))return true;return false;}
    static void same(JsonNode a,JsonNode b,String message){need(eq(a,b),message);}
    static void tokenShape(JsonNode token){keys(token,"clock_identity sequence thread_id");u64(token.get("clock_identity"));u64(token.get("sequence"));nu32(token.get("thread_id"));}
    static boolean ordered(JsonNode a,JsonNode b){return n(a.get("clock_identity")).signum()!=0&&eq(a.get("clock_identity"),b.get("clock_identity"))&&n(a.get("sequence")).signum()>0&&n(a.get("sequence")).compareTo(n(b.get("sequence")))<0&&!a.get("thread_id").isNull()&&eq(a.get("thread_id"),b.get("thread_id"));}
    static void retained(JsonNode value,String latest,String oldest,String overwritten,int capacity){BigInteger end=n(get(value,latest));need(n(get(value,oldest)).equals(end.signum()==0?BigInteger.ZERO:end.subtract(BigInteger.valueOf(capacity-1)).max(BigInteger.ONE)),"oldest retained sequence differs");need(n(get(value,overwritten)).equals(end.subtract(BigInteger.valueOf(capacity)).max(BigInteger.ZERO)),"overwritten retained count differs");}
    static List<String> fields(String fields){return List.of(fields.split(" "));}
}
