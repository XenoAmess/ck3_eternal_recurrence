package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatLeafWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Native diagnostic numeric domain. Never route these identities through double. */
final class CombatNativeValues {
    static final BigInteger U64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private CombatNativeValues() { }
    static BigInteger number(JsonNode value,int bits,boolean unsigned,boolean optional,String field,boolean strings,boolean hex){
        if(optional&&nil(value))return null;BigInteger n=null;
        if(value!=null&&value.isIntegralNumber())n=value.bigIntegerValue();
        else if(strings&&value!=null&&value.isTextual()){String token=value.textValue();try{if(hex&&(token.startsWith("0x")||token.startsWith("0X"))){require(token.substring(2).matches("[0-9a-fA-F]+"),field+" hexadecimal identity malformed");n=new BigInteger(token.substring(2),16);}else{require(token.matches(unsigned?"[0-9]+":"-?[0-9]+"),field+" decimal64 malformed");n=new BigInteger(token,10);}}catch(NumberFormatException e){throw new IllegalArgumentException(field+" numeric token malformed",e);}}
        BigInteger min=unsigned?BigInteger.ZERO:BigInteger.ONE.shiftLeft(bits-1).negate(),max=unsigned?BigInteger.ONE.shiftLeft(bits).subtract(BigInteger.ONE):BigInteger.ONE.shiftLeft(bits-1).subtract(BigInteger.ONE);require(n!=null&&n.compareTo(min)>=0&&n.compareTo(max)<=0,field+" must retain exact "+(unsigned?"uint":"int")+bits);return n;
    }
    static BigInteger field(ObjectNode row,String field,int bits,boolean unsigned,boolean optional,boolean strings,boolean hex){BigInteger n=number(row.get(field),bits,unsigned,optional,field,strings,hex);if(n==null)row.putNull(field);else row.set(field,BigIntegerNode.valueOf(n));return n;}
    static BigInteger raw(ObjectNode row,String f,boolean unsigned,boolean optional){return field(row,f,64,unsigned,optional,true,false);}
    static BigInteger ptr(ObjectNode row,String f,boolean optional){return field(row,f,64,true,optional,true,true);}
    static BigInteger integral(ObjectNode row,String f,int bits,boolean unsigned,boolean optional){return field(row,f,bits,unsigned,optional,false,false);}
    static void booleans(ObjectNode n,String names,boolean optional){for(String f:names.split(" "))if(optional)nb(n.get(f),f);else bool(n.get(f),f);}
    static void texts(ObjectNode n,String names,boolean optional){for(String f:names.split(" "))if(optional)nullableText(n.get(f),f);else text(n.get(f),f);}
    static void pointers(ObjectNode n,String names){for(String f:names.split(" "))ptr(n,f,true);}
    static void ints(ObjectNode n,String names,int bits,boolean unsigned,boolean optional){for(String f:names.split(" "))integral(n,f,bits,unsigned,optional);}
    static void raw64s(ObjectNode n,String names,boolean unsigned,boolean optional){for(String f:names.split(" "))raw(n,f,unsigned,optional);}
    static ArrayNode qvalues(JsonNode value,boolean optional,String name){if(optional&&nil(value))return null;ArrayNode a=array(value,name),out=JsonNodeFactory.instance.arrayNode();for(JsonNode v:a)out.add(number(v,64,false,false,name,true,false));return out;}
    static void exactBuild(ObjectNode n){eq(n.get("build_version"),"1.20.0.4","requires exact actual4 build");require(n.get("executable_sha256")!=null&&n.get("executable_sha256").isTextual()&&n.get("executable_sha256").textValue().equalsIgnoreCase(ACTUAL4_SHA),"requires exact actual4 executable");}
    static ObjectNode naturalEvent(JsonNode value){ObjectNode n=obj(value,"clock_identity sequence thread_id").deepCopy();ptr(n,"clock_identity",false);raw(n,"sequence",true,false);integral(n,"thread_id",32,true,true);return n;}
    static BigInteger value(JsonNode n){return nil(n)?null:n.bigIntegerValue();}
    static BigInteger value(ObjectNode n,String f){return value(n.get(f));}
    static boolean eqValue(JsonNode a,JsonNode b){return Objects.equals(value(a),value(b));}
    static boolean nz(JsonNode n){return !nil(n)&&n.isIntegralNumber()&&n.bigIntegerValue().signum()!=0;}
    static void requireSame(JsonNode a,JsonNode b,String message){require(Objects.equals(a,b)||a!=null&&b!=null&&a.isIntegralNumber()&&b.isIntegralNumber()&&a.bigIntegerValue().equals(b.bigIntegerValue()),message);}
    static BigInteger hexPointer(JsonNode value,boolean optional){if(optional&&nil(value))return null;String token=text(value,"native pointer");try{String digits=token.startsWith("0x")||token.startsWith("0X")?token.substring(2):token;require(digits.matches("[0-9a-fA-F]+"),"native pointer malformed");BigInteger n=new BigInteger(digits,16);require(n.signum()>=0&&n.compareTo(U64_MAX)<=0,"native pointer outside uint64");return n;}catch(NumberFormatException e){throw new IllegalArgumentException("native pointer malformed",e);}}
}
