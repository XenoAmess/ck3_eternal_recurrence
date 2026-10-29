package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** JSON exists only at the strict native boundary and shared immutable command envelope. */
final class GuiJson {
    private GuiJson() { }
    static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE),U32=BigInteger.ONE.shiftLeft(32);
    static final ObjectMapper MAPPER=new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    static void need(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    static void range(BigInteger value,BigInteger min,BigInteger max){need(value!=null&&value.compareTo(min)>=0&&value.compareTo(max)<=0,"integer outside native range");}
    static ObjectNode obj(JsonNode node){need(node!=null&&node.isObject(),"actual object required");return (ObjectNode)node;}
    static ObjectNode parse(RawJson raw){
        try(var parser=MAPPER.createParser(raw.bytes())){
            JsonNode node=MAPPER.readTree(parser);need(parser.nextToken()==null,"one native JSON document required");return obj(node);
        }catch(IOException failure){throw new IllegalArgumentException("malformed native JSON",failure);}
    }
    static ObjectNode result(PlanningReadReceipt read){
        need(read.original().nativeOk(),"native query failed");
        return parse(read.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("native result token absent")));
    }
    static ObjectNode fields(){return MAPPER.createObjectNode();}
    static OpportunityJson.Obj arguments(ObjectNode row){return OpportunityJson.object(OpportunityJson.parse(bytes(row)),"GUI command");}
    static ObjectNode arguments(OpportunityJson.Obj row){return obj(OpportunityJson.toNode(row));}
    static RawJson raw(ObjectNode row){return new RawJson(bytes(row));}
    static byte[] bytes(ObjectNode row){try{return MAPPER.writeValueAsBytes(row);}catch(IOException failure){throw new IllegalArgumentException("GUI JSON encode failed",failure);}}
    static JsonNode required(ObjectNode row,String name){JsonNode n=row.get(name);need(n!=null,"missing actual field "+name);return n;}
    static boolean bool(ObjectNode row,String name){JsonNode n=required(row,name);need(n.isBoolean(),"boolean required "+name);return n.booleanValue();}
    static void yes(ObjectNode row,String... names){for(String n:names)need(bool(row,n),"native proof missing "+n);}
    static void no(ObjectNode row,String... names){for(String n:names)need(!bool(row,n),"unsupported native credit "+n);}
    static String text(ObjectNode row,String name){JsonNode n=required(row,name);need(n.isTextual(),"text required "+name);String v=n.textValue();need(v.indexOf(0)<0,"NUL in actual text");return v;}
    static BigInteger integer(ObjectNode row,String name){JsonNode n=required(row,name);need(n.isIntegralNumber(),"integer token required "+name);return n.bigIntegerValue();}
    static BigInteger integer(ObjectNode row,String name,BigInteger min,BigInteger max){BigInteger n=integer(row,name);range(n,min,max);return n;}
    static int count(ObjectNode row,String name,int min,int max){return integer(row,name,BigInteger.valueOf(min),BigInteger.valueOf(max)).intValueExact();}
    static Optional<BigInteger> nullableInteger(ObjectNode row,String name){JsonNode n=required(row,name);return n.isNull()?Optional.empty():Optional.of(integer(row,name));}
    static Optional<String> nullableText(ObjectNode row,String name){JsonNode n=required(row,name);return n.isNull()?Optional.empty():Optional.of(text(row,name));}
    static void equal(ObjectNode row,String name,String value){need(text(row,name).equals(value),"native "+name+" drift");}
    static void equal(ObjectNode row,String name,BigInteger value){need(integer(row,name).equals(value),"native "+name+" drift");}
    static void keys(ObjectNode row,Set<String> required,Set<String> optional){
        Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);
        need(actual.containsAll(required)&&actual.stream().allMatch(n->required.contains(n)||optional.contains(n)),"unexpected/missing native fields");
    }
    static void binding(ObjectNode row,GuiModels.Context context){
        equal(row,"native_revision",context.before().frame().identity().nativeRevision());
        equal(row,"connection_generation",context.connectionGeneration());
        equal(row,"game_pid",BigInteger.valueOf(context.before().game().pid()));
        equal(row,"played_character_id",context.before().frame().identity().player());
        equal(row,"date_raw",context.before().frame().identity().dateRaw());
    }
    static void build(ObjectNode row,GuiModels.Build expected){
        equal(row,"game_version",expected.version());
        if(expected!=GuiModels.Build.LEGACY)need(text(row,"executable_sha256").equalsIgnoreCase(expected.sha256()),"native executable source drift");
    }
    static ObjectNode boundFields(GuiModels.Context context){
        ObjectNode fields=fields();fields.put("expected_player_character_id",context.before().frame().identity().player());
        fields.put("expected_game_pid",context.before().game().pid());fields.put("expected_connection_generation",context.connectionGeneration());return fields;
    }
    static String childPath(String path,boolean inner){
        need(path.length()<=383 && (path.isEmpty()||path.matches("[0-9]+(?:/[0-9]+)*")),"invalid native child path");
        if(inner)need(path.startsWith("0/"),"fixed White control must be inside actual modal");
        if(!path.isEmpty()){String[] parts=path.split("/");need(parts.length<=64,"child path depth");
            for(String part:parts)need(new BigInteger(part).compareTo(BigInteger.valueOf(inner?2048:4096))<=0,"child path index bound");}
        return path;
    }
    static String sha256(byte[] data){try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(data));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
}
