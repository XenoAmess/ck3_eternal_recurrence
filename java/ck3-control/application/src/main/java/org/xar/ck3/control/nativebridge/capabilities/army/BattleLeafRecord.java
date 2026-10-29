package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Typed private schema descriptors for exact native leaf records; recursive fields are always parsed by their owner. */
final class BattleLeafRecord {
    enum Kind { I32,U32,U8,I64,U64,BOOL,TEXT,RAW }
    record Fields(Kind kind,boolean nullable,List<String> names) { Fields { names=List.copyOf(names); } }
    private BattleLeafRecord() { }
    static Fields f(Kind kind,boolean nullable,String... names) { return new Fields(kind,nullable,List.of(names)); }
    static ObjectNode parseRecord(JsonNode raw,String field,Fields... descriptors) {
        Set<String> names=new HashSet<>();
        for(Fields descriptor:descriptors)for(String name:descriptor.names())require(names.add(name),field,"duplicate schema field "+name);
        ObjectNode input=exact(raw,field,names),out=object();
        for(Fields descriptor:descriptors)for(String name:descriptor.names()) {
            JsonNode value=input.get(name);String path=field+"."+name;
            JsonNode parsed=switch(descriptor.kind()) {
                case I32 -> number(value,path,32,false,descriptor.nullable()); case U32 -> number(value,path,32,true,descriptor.nullable());
                case U8 -> number(value,path,8,true,descriptor.nullable()); case I64 -> number(value,path,64,false,descriptor.nullable());
                case U64 -> number(value,path,64,true,descriptor.nullable()); case BOOL -> bool(value,path,descriptor.nullable());
                case TEXT -> text(value,path,descriptor.nullable(),true); case RAW -> value;
            };out.set(name,parsed);
        }return out;
    }
    static BigInteger n(JsonNode row,String key) { return integer(row.get(key)); }
    static Boolean b(JsonNode row,String key) { return booleanValue(row.get(key)); }
    static String s(JsonNode row,String key) { return string(row.get(key)); }
    static boolean eq(JsonNode row,String key,long value) { return BigInteger.valueOf(value).equals(n(row,key)); }
    static boolean present(JsonNode row,String... keys) { return Arrays.stream(keys).allMatch(key->!nil(row.get(key))); }
    static boolean zeroReason(JsonNode row) { return nil(row.get("reason")); }
    static boolean pcReady(JsonNode raw) { return propertiesReady(raw)&&nil(raw.get("reason")); }
    static List<JsonNode> rows(JsonNode raw) { List<JsonNode> rows=new ArrayList<>();raw.forEach(rows::add);return rows; }
    static JsonNode ordered(JsonNode raw,String field,boolean nullable,ElementNormalizer normalize) {
        JsonNode result=array(raw,field,nullable,normalize);
        if(!nil(result))for(int index=0;index<result.size();index++)require(BigInteger.valueOf(index).equals(n(result.get(index),"native_index")),field,"native occurrence order differs");
        return result;
    }
}
