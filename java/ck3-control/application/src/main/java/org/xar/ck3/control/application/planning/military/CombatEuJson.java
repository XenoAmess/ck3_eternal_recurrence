package org.xar.ck3.control.application.planning.military;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Narrow JSON adapter for the single EU field contract; public consumers share immutable OpportunityJson. */
final class CombatEuJson {
    private CombatEuJson() { }
    static final JsonNodeFactory J=JsonNodeFactory.instance;
    static final BigInteger SCALE=BigInteger.valueOf(100000),MIN=BigInteger.ONE.shiftLeft(63).negate(),MAX=BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    static ObjectNode obj(){return J.objectNode();}static ArrayNode arr(){return J.arrayNode();}
    static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    static boolean integral(JsonNode value){return value!=null&&value.isIntegralNumber();}
    static boolean raw(JsonNode value){return integral(value)&&value.bigIntegerValue().compareTo(MIN)>=0&&value.bigIntegerValue().compareTo(MAX)<=0;}
    static boolean nonnegative(JsonNode value){return integral(value)&&value.bigIntegerValue().signum()>=0;}
    static BigInteger n(JsonNode value){return value.bigIntegerValue();}
    static boolean text(JsonNode value){return value!=null&&value.isTextual()&&!value.textValue().isEmpty();}
    static boolean probability(JsonNode value){return nonnegative(value)&&n(value).compareTo(SCALE)<=0;}
    static List<String> words(String value){return List.of(value.split(" "));}
    static ArrayNode strings(List<String> values){ArrayNode out=arr();values.forEach(out::add);return out;}
    static JsonNode at(JsonNode value,String path){JsonNode current=value;for(String key:path.split("\\.")){if(current==null||!current.isObject())return null;current=current.get(key);}return current;}
    static Set<String> names(JsonNode value){if(value==null||!value.isObject())return Set.of();Set<String> out=new HashSet<>();value.fieldNames().forEachRemaining(out::add);return out;}
    static boolean schema(JsonNode value,List<String> fields){return value!=null&&value.isObject()&&names(value).equals(Set.copyOf(fields));}
    static boolean prefix(List<String> errors,String prefix){return errors.stream().anyMatch(e->e.startsWith(prefix));}
    static JsonNode canonical(JsonNode value){if(value.isObject()){ObjectNode out=obj();Set<String> names=new TreeSet<>();value.fieldNames().forEachRemaining(names::add);for(String key:names)out.set(key,canonical(value.get(key)));return out;}if(value.isArray()){ArrayNode out=arr();value.forEach(item->out.add(canonical(item)));return out;}return value.deepCopy();}
    static String digest(JsonNode value){try{return HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical(value).toString().getBytes(StandardCharsets.UTF_8)));}catch(NoSuchAlgorithmException e){throw new IllegalStateException(e);}}
    static void seal(ObjectNode value){value.remove("assessment_sha256");value.put("assessment_sha256",digest(value));}
    static Obj immutable(ObjectNode value){return OpportunityJson.object(OpportunityJson.parse(value.toString().getBytes(StandardCharsets.UTF_8)),"EU assessment");}
    static boolean same(JsonNode a,JsonNode b){if(a==null||b==null)return a==b;if(a.isIntegralNumber()||b.isIntegralNumber())return a.isIntegralNumber()&&b.isIntegralNumber()&&n(a).equals(n(b));if(a.isObject()&&b.isObject()){if(!names(a).equals(names(b)))return false;for(String key:names(a))if(!same(a.get(key),b.get(key)))return false;return true;}if(a.isArray()&&b.isArray()){if(a.size()!=b.size())return false;for(int i=0;i<a.size();i++)if(!same(a.get(i),b.get(i)))return false;return true;}return a.equals(b);}
    static BigInteger product(BigInteger a,BigInteger b){return a.multiply(b).divide(SCALE);}
    static void probability(JsonNode value,String path,List<String> errors){if(!probability(value))errors.add(path+"_invalid");}
    static void sha(JsonNode value,String path,List<String> errors){if(!text(value)||!value.textValue().matches("[0-9A-F]{64}"))errors.add(path+"_invalid");}
}
