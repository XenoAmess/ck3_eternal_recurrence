package org.xar.ck3.control.wave2.military.combatwire.phaseevent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import java.util.TreeSet;

/** The only dynamic boundary is the pinned normalized AST and its explicitly validated state paths. */
final class PhaseJson {
    private PhaseJson() { }
    static final JsonNodeFactory J = JsonNodeFactory.instance;
    static final ObjectMapper JSON = new ObjectMapper();
    static final BigInteger SCALE = BigInteger.valueOf(100_000);
    static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    static ObjectNode object(JsonNode value, String name) { require(value instanceof ObjectNode, name + " must be an object"); return (ObjectNode) value; }
    static ArrayNode array(JsonNode value, String name) { require(value instanceof ArrayNode, name + " must be an array"); return (ArrayNode) value; }
    static String text(JsonNode value, String name) { require(value != null && value.isTextual() && !value.textValue().isEmpty(), name + " must be nonempty text"); return value.textValue(); }
    static boolean bool(JsonNode value, String name) { require(value != null && value.isBoolean(), name + " must be boolean"); return value.booleanValue(); }
    static BigInteger integer(JsonNode value, String name) { require(value != null && value.isIntegralNumber(), name + " must be an integer"); return value.bigIntegerValue(); }
    static long signed(JsonNode value, String name) { try { return integer(value,name).longValueExact(); } catch (ArithmeticException e) { throw new IllegalArgumentException(name + " must be signed int64",e); } }
    static long checked(BigInteger value, String name) { try { return value.longValueExact(); } catch (ArithmeticException e) { throw new IllegalArgumentException(name + " exceeded signed int64",e); } }
    static long positive(JsonNode value, String name) { long result=signed(value,name); require(result>0,name+" must be positive"); return result; }
    static int side(JsonNode value, String name) { long result=signed(value,name); require(result==0||result==1,name+" must be side 0 or 1"); return (int)result; }
    static void keys(JsonNode value,String expected,String name) { ObjectNode row=object(value,name); Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add); require(actual.equals(Set.of(expected.split(" "))),name+" schema is malformed: "+actual); }
    static Set<String> strings(JsonNode value,String name) { Set<String> result=new HashSet<>(); for(JsonNode item:array(value,name)) require(result.add(text(item,name+" item")),name+" repeats item"); return Set.copyOf(result); }
    static ObjectNode obj() { return J.objectNode(); }
    static ArrayNode arr() { return J.arrayNode(); }
    static JsonNode parse(String value) { try { return JSON.readTree(value); } catch(java.io.IOException e) { throw new IllegalArgumentException("invalid static JSON",e); } }
    static ArrayNode words(String text) { ArrayNode out=arr(); if(!text.isEmpty()) for(String token:text.split(" ")) out.add(token); return out; }
    static ObjectNode absent() { return obj().put("status","absent").putNull("value"); }
    static JsonNode canonical(JsonNode value) { if(value.isObject()) { ObjectNode out=obj();Set<String> keys=new TreeSet<>();value.fieldNames().forEachRemaining(keys::add);for(String key:keys)out.set(key,canonical(value.get(key)));return out;} if(value.isArray()){ArrayNode out=arr();value.forEach(child->out.add(canonical(child)));return out;}return value.deepCopy(); }
    static String digest(JsonNode value) { return digest(canonical(value).toString().getBytes(StandardCharsets.UTF_8)); }
    static String digest(byte[] value) { try{return HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}catch(NoSuchAlgorithmException e){throw new IllegalStateException(e);} }
    static void seal(ObjectNode value,String field){value.put(field,digest(value));}
    static long multiply(long left,long right){return checked(BigInteger.valueOf(left).multiply(BigInteger.valueOf(right)).divide(SCALE),"fixed multiply");}
    static long divide(long left,long right){require(right!=0,"fixed divide by zero");return checked(BigInteger.valueOf(left).multiply(SCALE).divide(BigInteger.valueOf(right)),"fixed divide");}
    static long add(long left,long right){return checked(BigInteger.valueOf(left).add(BigInteger.valueOf(right)),"fixed add");}
    static long subtract(long left,long right){return checked(BigInteger.valueOf(left).subtract(BigInteger.valueOf(right)),"fixed subtract");}
    static void unique(ArrayNode rows,JsonNode value){for(JsonNode row:rows)if(row.equals(value))return;rows.add(value.deepCopy());}
    static void unique(ArrayNode rows,long value){unique(rows,J.numberNode(value));}
    static void unique(ArrayNode rows,String value){unique(rows,J.textNode(value));}
}
