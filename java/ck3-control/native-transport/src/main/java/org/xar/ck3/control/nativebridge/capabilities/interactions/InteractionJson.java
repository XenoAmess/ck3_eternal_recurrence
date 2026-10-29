package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** The sole scoped JSON boundary; no trees, raw JSON, or unconstrained maps escape into domain records. */
final class InteractionJson {
    static final BigInteger U32=new BigInteger("4294967295"), U64=new BigInteger("18446744073709551615"),
            I64_MIN=BigInteger.valueOf(Long.MIN_VALUE), I64_MAX=BigInteger.valueOf(Long.MAX_VALUE);
    static final JsonNodeFactory F=JsonNodeFactory.instance;
    private InteractionJson() { }
    static void need(boolean ok,String message) { if(!ok) throw new IllegalArgumentException(message); }
    static BigInteger range(BigInteger n,BigInteger low,BigInteger high) { need(n!=null && n.compareTo(low)>=0 && n.compareTo(high)<=0,"native integer outside field range"); return n; }
    static ObjectNode object(JsonNode n) { need(n instanceof ObjectNode,"native object required"); return (ObjectNode)n; }
    static ObjectNode parse(RawJson raw) { try { return object(NativeWire.parse(raw.bytes())); } catch(IOException e) { throw new IllegalArgumentException("invalid original native JSON",e); } }
    static ObjectNode result(PlanningReadReceipt r) { need(r.original().nativeOk(),"successful native query required"); return parse(r.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("original native result absent"))); }
    static RawJson encode(ObjectNode n) { try { return new RawJson(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)); } catch(RuntimeException e) { throw new IllegalArgumentException("domain native serialization rejected",e); } }
    static JsonNode field(JsonNode n,String key) { need(n!=null && n.isObject() && n.has(key),"missing native field: "+key); return n.get(key); }
    static void closed(JsonNode n,String... names) { closed(n,Set.of(names)); }
    static void closed(JsonNode n,Set<String> expected) { object(n); Set<String> actual=new HashSet<>(); n.fieldNames().forEachRemaining(actual::add); need(actual.equals(expected),"native DTO fields differ: "+actual); }
    static boolean bool(JsonNode n,String k) { JsonNode v=field(n,k); need(v.isBoolean(),"actual boolean required: "+k); return v.booleanValue(); }
    static Boolean nullableBool(JsonNode n,String k) { return field(n,k).isNull()?null:bool(n,k); }
    static String text(JsonNode n,String k) { JsonNode v=field(n,k); need(v.isTextual(),"actual string required: "+k); return v.textValue(); }
    static String nullableText(JsonNode n,String k) { return field(n,k).isNull()?null:text(n,k); }
    static String reason(JsonNode n,String k) { String s=text(n,k); need(!s.isEmpty() && s.length()<=512,"bounded nonempty native reason required"); return s; }
    static BigInteger number(JsonNode n,String k,BigInteger low,BigInteger high) { JsonNode v=field(n,k); need(v.isIntegralNumber(),"exact native integer required; boolean/float/string refused: "+k); return range(v.bigIntegerValue(),low,high); }
    static BigInteger u64(JsonNode n,String k) { return number(n,k,BigInteger.ZERO,U64); }
    static BigInteger positive64(JsonNode n,String k) { return number(n,k,BigInteger.ONE,U64); }
    static long id(JsonNode n,String k) { return number(n,k,BigInteger.ZERO,U32.subtract(BigInteger.ONE)).longValueExact(); }
    static Long nullableId(JsonNode n,String k) { return field(n,k).isNull()?null:id(n,k); }
    static Long nullablePlayer(JsonNode n,String k) { return field(n,k).isNull()?null:number(n,k,BigInteger.ZERO,U32).longValueExact(); }
    static Integer nullableInt32(JsonNode n,String k) { return field(n,k).isNull()?null:number(n,k,BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact(); }
    static BigInteger nullableNumber(JsonNode n,String k,BigInteger low,BigInteger high) { return field(n,k).isNull()?null:number(n,k,low,high); }
    static int integer(JsonNode n,String k,int low,int high) { return number(n,k,BigInteger.valueOf(low),BigInteger.valueOf(high)).intValueExact(); }
    static void eq(JsonNode n,String k,String v) { need(text(n,k).equals(v),"native constant differs: "+k); }
    static void eq(JsonNode n,String k,BigInteger v) { JsonNode a=field(n,k); need(a.isIntegralNumber() && a.bigIntegerValue().equals(v),"native identity differs: "+k); }
    static void yes(JsonNode n,String k) { need(bool(n,k),"required native true: "+k); }
    static void no(JsonNode n,String k) { need(!bool(n,k),"required native false: "+k); }
    static void nil(JsonNode n,String... fields) { for(String k:fields) need(field(n,k).isNull(),"unknown native field must remain null: "+k); }
    static <T> List<T> list(JsonNode n,String k,int maximum,Function<JsonNode,T> decode) {
        JsonNode a=field(n,k); need(a.isArray() && a.size()<=maximum,"bounded native array required: "+k);
        List<T> out=new ArrayList<>(); for(JsonNode row:a) out.add(decode.apply(row)); return List.copyOf(out);
    }
    static List<Long> ids(JsonNode n,String k,int maximum) { return list(n,k,maximum,v->{ need(v.isIntegralNumber(),"full integer identity required"); return range(v.bigIntegerValue(),BigInteger.ZERO,U32.subtract(BigInteger.ONE)).longValueExact(); }); }
    static <T> void unique(List<T> values,int maximum) { need(values.size()<=maximum && new HashSet<>(values).size()==values.size(),"bounded unique ordered native identities required"); }
    static Build build(JsonNode n,String version,String sha,Context c) {
        eq(n,version,c.build().version()); need(text(n,sha).equalsIgnoreCase(c.build().sha256()),"native executable differs from held session"); return c.build();
    }
    static Frame frame(JsonNode n,Context c) {
        eq(n,"snapshot_revision",c.revision()); eq(n,"date_raw",c.date());
        return new Frame(c.revision(),c.date(),c.actor(),c.build(),positive64(n,"query_sequence"));
    }
    static Availability availability(JsonNode n) {
        boolean available=bool(n,"available"); eq(n,"status",available?"available":"unavailable");
        String reason=available?nullableText(n,"unavailable_reason"):reason(n,"unavailable_reason");
        return new Availability(available,reason);
    }
    static ObjectNode common(Context c) {
        return F.objectNode().put("expected_player_character_id",c.actor()).put("expected_game_pid",c.before().game().pid()).put("expected_connection_generation",c.connectionGeneration());
    }
    static RawJson empty() { return encode(F.objectNode()); }
    static Set<String> union(Set<String> base, String... additions) { Set<String> out=new HashSet<>(base); out.addAll(List.of(additions)); return Set.copyOf(out); }
    static <E extends Enum<E>> E enumeration(JsonNode n,String k,Class<E> type) {
        try { return Enum.valueOf(type,text(n,k).toUpperCase(java.util.Locale.ROOT)); }
        catch(IllegalArgumentException bad) { throw new IllegalArgumentException("native enum differs: "+k,bad); }
    }
    static String csv(List<FullId> ids) { return ids.stream().map(i->Long.toString(i.value())).collect(java.util.stream.Collectors.joining(",")); }
    static ObjectNode nativeFields(NativeRequest request) { return parse(request.additionalFields()); }
}
