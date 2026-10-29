package org.xar.ck3.control.contracts.presentation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One exact persistence boundary, not a physical source or submission authority. */
final class PresentationJson {
    private PresentationJson() { }
    static String u64(String value,boolean positive) {
        StrictJson.require(value!=null&&value.matches("0|[1-9][0-9]{0,19}"),"canonical uint64 decimal string required");
        BigInteger n=new BigInteger(value);
        StrictJson.require(n.compareTo(StrictJson.UINT64_MAX)<=0&&(!positive||n.signum()>0),"uint64 outside presentation range");
        return value;
    }
    static long u32(JsonNode value) { return StrictJson.integer(value,0,0xffff_ffffL); }
    static long u32(long value) { StrictJson.require(value>=0&&value<=0xffff_ffffL,"uint32 required"); return value; }
    static int i32(JsonNode value) { return (int)StrictJson.integer(value,Integer.MIN_VALUE,Integer.MAX_VALUE); }
    static Instant time(JsonNode value) {
        String text=StrictJson.text(value); Instant actual=Instant.parse(text);
        StrictJson.require(actual.toString().equals(text),"canonical UTC Instant required"); return actual;
    }
    static List<ExactRef> refs(JsonNode value) {
        StrictJson.require(value!=null&&value.isArray()&&value.size()<=32,"bounded exact evidence array required");
        List<ExactRef> result=new ArrayList<>(); for(JsonNode item:value) result.add(ExactRef.fromJson(item));
        return refs(result);
    }
    static List<ExactRef> refs(List<ExactRef> value) {
        List<ExactRef> result=List.copyOf(value);
        StrictJson.require(result.size()<=32&&new java.util.HashSet<>(result).size()==result.size(),"bounded unique evidence required");
        result.forEach(ref->StrictJson.require(ref.bytes()>0,"nonempty original evidence required")); return result;
    }
    static ArrayNode refs(ObjectNode parent,String name,List<ExactRef> values) {
        ArrayNode result=parent.putArray(name); values.forEach(ref->result.add(ref.toJson())); return result;
    }
    static ExactRef ref(JsonNode value,long bytes) {
        ExactRef ref=ExactRef.fromJson(value); sized(ref,bytes); return ref;
    }
    static void sized(ExactRef ref,long bytes) { StrictJson.require(ref!=null&&ref.bytes()==bytes,"exact native region byte size required"); }
    static void original(ExactRef ref,byte[] bytes) {
        sized(ref,bytes.length);
        try { StrictJson.require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(ref.sha256()),"original presentation bytes differ from exact reference"); }
        catch(java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    static ObjectNode envelope(String schema) {
        ObjectNode n=StrictJson.object(); n.put("schema",schema); n.put("transport",TransportKind.PRESENTATION_MMAP.name()); return n;
    }
    static ObjectNode envelope(JsonNode raw,Set<String> fields,String schema) {
        ObjectNode n=StrictJson.object(raw,fields);
        StrictJson.require(StrictJson.text(n.get("schema")).equals(schema)
                &&StrictJson.text(n.get("transport")).equals(TransportKind.PRESENTATION_MMAP.name()),"exact presentation schema/transport required"); return n;
    }
}
