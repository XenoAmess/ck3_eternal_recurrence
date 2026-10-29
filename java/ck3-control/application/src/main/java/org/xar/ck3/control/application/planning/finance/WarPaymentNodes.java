package org.xar.ck3.control.application.planning.finance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;

/** Concentrated literal JSON boundary; every field has one declared scalar/nullable role. */
public final class WarPaymentNodes {
    private WarPaymentNodes() { }
    static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    static final BigInteger TWO64 = BigInteger.ONE.shiftLeft(64), TWO63 = BigInteger.ONE.shiftLeft(63);
    static final ObjectMapper JSON = new ObjectMapper();
    enum Role { U64,U32,U8,I64,I32,BOOL,TEXT,NEST,OU64,OU32,OU8,OI64,OBOOL }
    record Group(Role role, String names) { }
    static Group g(Role role,String names) { return new Group(role,names); }
    enum Direction { NATIVE, TO_PUBLIC, FROM_PUBLIC }
    private record WideField(ObjectNode object,String key) { }
    static final class Check {
        private final Direction direction;
        private final List<WideField> wide = new ArrayList<>();
        private final List<ArrayNode> arrays = new ArrayList<>();
        Check(Direction direction) { this.direction=direction; }
        void fields(JsonNode input,Group... groups) {
            ObjectNode value=obj(input); Set<String> keys=new HashSet<>();
            for(Group group:groups) for(String key:group.names().split(" ")) {
                if(key.isEmpty()) continue;
                need(keys.add(key),"duplicate schema field "+key);
                need(value.has(key),"missing field "+key);
                Role role=group.role(); JsonNode scalar=value.get(key);
                if(direction==Direction.FROM_PUBLIC && isWide(role) && !scalar.isNull()) {
                    BigInteger converted;
                    if(scalar.isTextual()) {
                        String text=scalar.textValue();
                        need(canonicalInteger(text),"noncanonical decimal field "+key);
                        converted=new BigInteger(text);
                    } else {
                        need(scalar.isIntegralNumber(),"public integer field "+key);
                        converted=scalar.bigIntegerValue();
                        need(converted.abs().compareTo(BigInteger.valueOf(9007199254740991L))<=0,"unsafe public numeric field "+key);
                    }
                    value.put(key,converted); scalar=value.get(key);
                }
                scalar(scalar,role,key);
                if(direction==Direction.TO_PUBLIC && isWide(role)) wide.add(new WideField(value,key));
            }
            Set<String> actual=new HashSet<>();value.fieldNames().forEachRemaining(actual::add);
            need(actual.equals(keys),"unknown schema field");
        }
        void u64Array(ArrayNode array) {
            for(int i=0;i<array.size();i++) {
                JsonNode item=array.get(i);
                if(direction==Direction.FROM_PUBLIC) {
                    BigInteger n;
                    if(item.isTextual()) {need(canonicalInteger(item.textValue()),"array decimal");n=new BigInteger(item.textValue());}
                    else {need(item.isIntegralNumber(),"array integer");n=item.bigIntegerValue();need(n.abs().compareTo(BigInteger.valueOf(9007199254740991L))<=0,"unsafe public array integer");}
                    array.set(i,JSON.getNodeFactory().numberNode(n));item=array.get(i);
                }
                scalar(item,Role.U64,"array");
            }
            if(direction==Direction.TO_PUBLIC) arrays.add(array);
        }
        void project() {
            for(WideField field:wide) {JsonNode n=field.object().get(field.key());if(!n.isNull())field.object().put(field.key(),n.bigIntegerValue().toString());}
            for(ArrayNode array:arrays)for(int i=0;i<array.size();i++)array.set(i,JSON.getNodeFactory().textNode(array.get(i).bigIntegerValue().toString()));
        }
    }
    private static boolean isWide(Role r) {return r==Role.U64||r==Role.I64||r==Role.OU64||r==Role.OI64;}
    private static void scalar(JsonNode n,Role r,String name) {
        boolean nullable=r==Role.OU64||r==Role.OU32||r==Role.OU8||r==Role.OI64||r==Role.OBOOL;
        if(nullable&&n.isNull())return;
        if(r==Role.NEST)return;
        if(r==Role.TEXT){need(n.isTextual(),name+" string");return;}
        if(r==Role.BOOL||r==Role.OBOOL){need(n.isBoolean(),name+" boolean");return;}
        need(n.isIntegralNumber(),name+" integer");
        int bits=switch(r){case U32,OU32,I32->32;case U8,OU8->8;default->64;};
        boolean signed=r==Role.I64||r==Role.OI64||r==Role.I32;
        BigInteger low=signed?BigInteger.ONE.shiftLeft(bits-1).negate():BigInteger.ZERO;
        BigInteger high=BigInteger.ONE.shiftLeft(signed?bits-1:bits).subtract(BigInteger.ONE);
        need(n.bigIntegerValue().compareTo(low)>=0&&n.bigIntegerValue().compareTo(high)<=0,name+" integer range");
    }
    private static boolean canonicalInteger(String text) {
        if(text==null||text.isEmpty())return false;
        if(text.equals("0"))return true;
        int at=text.charAt(0)=='-'?1:0;
        if(at>=text.length()||text.charAt(at)<'1'||text.charAt(at)>'9')return false;
        for(int i=at+1;i<text.length();i++)if(text.charAt(i)<'0'||text.charAt(i)>'9')return false;
        return text.length()<=21;
    }
    static ObjectNode parse(RawJson raw) {try{return obj(JSON.readTree(raw.bytes()));}catch(IOException e){throw new IllegalArgumentException("war payment JSON",e);}}
    static RawJson raw(JsonNode node) {try{return new RawJson(JSON.writeValueAsBytes(node));}catch(IOException e){throw new IllegalArgumentException("war payment JSON",e);}}
    static ObjectNode obj(JsonNode n){need(n!=null&&n.isObject(),"object required");return (ObjectNode)n;}
    static ArrayNode list(JsonNode n,int bound){need(n!=null&&n.isArray()&&n.size()<=bound,"bounded array required");return (ArrayNode)n;}
    static ObjectNode empty(){return JSON.createObjectNode();}
    static ArrayNode array(){return JSON.createArrayNode();}
    static BigInteger num(JsonNode n){need(n!=null&&n.isIntegralNumber(),"integer required");return n.bigIntegerValue();}
    static BigInteger n(JsonNode o,String k){return num(o.get(k));}
    static boolean yes(JsonNode o,String k){need(o.get(k)!=null&&o.get(k).isBoolean(),"boolean required");return o.get(k).booleanValue();}
    static boolean nz(JsonNode n){return n!=null&&!n.isNull()&&num(n).signum()!=0;}
    static boolean present(JsonNode o,String k){return o.has(k)&&!o.get(k).isNull();}
    static boolean eq(JsonNode a,JsonNode b){
        if(a==null||b==null)return a==b;
        if(a.isIntegralNumber()&&b.isIntegralNumber())return a.bigIntegerValue().equals(b.bigIntegerValue());
        if(a.isArray()&&b.isArray()){if(a.size()!=b.size())return false;for(int i=0;i<a.size();i++)if(!eq(a.get(i),b.get(i)))return false;return true;}
        if(a.isObject()&&b.isObject()){if(a.size()!=b.size())return false;Iterator<String> keys=a.fieldNames();while(keys.hasNext()){String k=keys.next();if(!b.has(k)||!eq(a.get(k),b.get(k)))return false;}return true;}
        return a.equals(b);
    }
    static boolean eq(JsonNode a,String ka,JsonNode b,String kb){return eq(a.get(ka),b.get(kb));}
    static boolean is(JsonNode o,String k,long n){return present(o,k)&&o.get(k).isIntegralNumber()&&num(o.get(k)).equals(BigInteger.valueOf(n));}
    static void put(ObjectNode o,String k,BigInteger n){o.put(k,n);}
    static void need(boolean ok,String message){if(!ok)throw new IllegalArgumentException("war payment "+message);}
}
