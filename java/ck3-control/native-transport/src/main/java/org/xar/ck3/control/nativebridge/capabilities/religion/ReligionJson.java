package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels.*;

/** Jackson trees live only at this validated serialization boundary, never in domain return values. */
final class ReligionJson {
    static final BigInteger U32 = new BigInteger("4294967295"), U64 = new BigInteger("18446744073709551615");
    static final BigInteger I32_MIN = BigInteger.valueOf(Integer.MIN_VALUE), I32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    static final BigInteger I64_MIN = BigInteger.valueOf(Long.MIN_VALUE), I64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private ReligionJson() { }
    static void need(boolean good, String message) { if (!good) throw new IllegalArgumentException(message); }
    static BigInteger range(BigInteger value, BigInteger low, BigInteger high) { need(value != null && value.compareTo(low) >= 0 && value.compareTo(high) <= 0, "integer outside native range"); return value; }
    static ObjectNode object(JsonNode node) { need(node instanceof ObjectNode, "native object required"); return (ObjectNode) node; }
    static ObjectNode parse(RawJson token) { try { return object(NativeWire.parse(token.bytes())); } catch (IOException failure) { throw new IllegalArgumentException("malformed native JSON", failure); } }
    static ObjectNode result(PlanningReadReceipt receipt) { return parse(receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("native result absent"))); }
    static JsonNode field(JsonNode row, String key) { need(row != null && row.isObject() && row.has(key), "missing native field: " + key); return row.get(key); }
    static boolean bool(JsonNode row, String key) { JsonNode n = field(row,key); need(n.isBoolean(), "native boolean required: " + key); return n.booleanValue(); }
    static Boolean nullableBool(JsonNode row, String key) { return field(row,key).isNull() ? null : bool(row,key); }
    static BigInteger number(JsonNode row, String key, BigInteger low, BigInteger high) { JsonNode n=field(row,key); need(n.isIntegralNumber(), "native integer token required: " + key); return range(n.bigIntegerValue(),low,high); }
    static BigInteger nullableNumber(JsonNode row, String key, BigInteger low, BigInteger high) { return field(row,key).isNull()?null:number(row,key,low,high); }
    static int i32(JsonNode row,String key) { return number(row,key,I32_MIN,I32_MAX).intValueExact(); }
    static Integer nullableI32(JsonNode row,String key) { return field(row,key).isNull()?null:i32(row,key); }
    static BigInteger id(JsonNode row,String key) { return number(row,key,BigInteger.ZERO,U32.subtract(BigInteger.ONE)); }
    static BigInteger nullableId(JsonNode row,String key) { return field(row,key).isNull()?null:id(row,key); }
    static String text(JsonNode row,String key) { JsonNode n=field(row,key); need(n.isTextual(), "native string required: "+key); return n.textValue(); }
    static String nullableText(JsonNode row,String key) { return field(row,key).isNull()?null:text(row,key); }
    static String nonempty(JsonNode row,String key) { String v=text(row,key); need(!v.isEmpty(), "nonempty native text required: "+key); return v; }
    static void equal(JsonNode row,String key,String expected) { need(text(row,key).equals(expected),"native constant differs: "+key); }
    static void equal(JsonNode row,String key,BigInteger expected) { need(number(row,key,I64_MIN.max(expected.min(I64_MIN)),U64.max(expected)).equals(expected),"native bound integer differs: "+key); }
    static void yes(JsonNode row,String key) { need(bool(row,key),"required native true: "+key); }
    static void no(JsonNode row,String key) { need(!bool(row,key),"read cannot claim action credit: "+key); }
    static void nil(JsonNode row,String key) { need(field(row,key).isNull(),"unobserved native field must remain null: "+key); }
    static void exact(JsonNode row,String fields) { Set<String> expected=fields.isEmpty()?Set.of():Set.of(fields.split(" +")); Set<String> actual=new HashSet<>(); object(row).fieldNames().forEachRemaining(actual::add); need(actual.equals(expected),"native object fields differ: expected "+expected+", actual "+actual); }
    static <T> List<T> array(JsonNode row,String key,int maximum,Function<JsonNode,T> decoder) { JsonNode n=field(row,key); need(n.isArray()&&n.size()<=maximum,"native array required: "+key); List<T> items=new ArrayList<>(); for(JsonNode item:n) items.add(decoder.apply(item)); return List.copyOf(items); }
    static List<BigInteger> ids(JsonNode row,String key,int maximum) { List<BigInteger> items=array(row,key,maximum,n->{ need(n.isIntegralNumber(),"integer ID token required"); return range(n.bigIntegerValue(),BigInteger.ZERO,U32.subtract(BigInteger.ONE)); }); need(new HashSet<>(items).size()==items.size(),"duplicate full native identities"); return items; }
    static List<BigInteger> nullableIds(JsonNode row,String key,int maximum) { return field(row,key).isNull()?null:ids(row,key,maximum); }
    static Availability availability(JsonNode row,String reasonKey) { boolean available=bool(row,"available"); String reason=nullableText(row,reasonKey); need(available?(reason==null||reason.equals("none")):(reason!=null&&!reason.isEmpty()&&!reason.equals("none")),"native source availability/reason differs"); return new Availability(available,reason); }
    static Build build(JsonNode row) { String v=text(row,"game_version"),s=text(row,"executable_sha256"); for(Build b:Build.values())if(b.version().equals(v)&&b.sha256().equalsIgnoreCase(s))return b; throw new IllegalArgumentException("native exact version/SHA pair differs"); }
    static org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity factual(org.xar.ck3.control.application.action.PlanningReadRequest request) {
        if(request.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation) {
            need(request.operation().value().equals("query-player-religion-conversion-result-private-v1")||request.operation().value().equals("county-conversion-task-result-private-v1"),"ordinary Religion reads cannot adopt a reconciliation origin");
            return request.reconciliationBefore();
        }
        return request.before();
    }
    static BigInteger nativeRevision(PlanningReadReceipt receipt) { return factual(receipt.request()).frame().identity().nativeRevision(); }
    static BigInteger date(PlanningReadReceipt receipt) { return factual(receipt.request()).frame().identity().dateRaw(); }
    static BigInteger player(PlanningReadReceipt receipt) { return factual(receipt.request()).frame().identity().player(); }
    static Frame frame(JsonNode value,PlanningReadReceipt receipt,String schema,Build required,boolean signedActor) {
        equal(value,"schema",schema); Build b=build(value); need((required==null||required==b)&&b==boundBuild(receipt),"operation is not implemented for connected exact build");
        BigInteger actor=number(value,"played_character_id",signedActor?I32_MIN:BigInteger.ZERO,signedActor?I32_MAX:U32.subtract(BigInteger.ONE));
        BigInteger bound=player(receipt); if(signedActor&&bound.compareTo(I32_MAX)>0)bound=bound.subtract(U32.add(BigInteger.ONE));
        need(actor.equals(bound),"native actor differs from held frame"); equal(value,"date_raw",date(receipt));
        return new Frame(b,number(value,"capture_epoch",BigInteger.ONE,U64),nativeRevision(receipt),date(receipt),actor,availability(value,"unavailable_reason"));
    }
    static Frame partialFrame(JsonNode value,PlanningReadReceipt receipt,String schema) {
        equal(value,"schema",schema);Build b=build(value);need(b==boundBuild(receipt),"partial collector connected build differs");
        BigInteger actor=number(value,"played_character_id",I32_MIN,I32_MAX),bound=player(receipt);if(bound.compareTo(I32_MAX)>0)bound=bound.subtract(U32.add(BigInteger.ONE));need(actor.equals(bound),"partial native actor drift");equal(value,"date_raw",date(receipt));
        return new Frame(b,number(value,"capture_epoch",BigInteger.ONE,U64),nativeRevision(receipt),date(receipt),actor,new Availability(bool(value,"available"),nullableText(value,"unavailable_reason")));
    }
    static byte[] originalPacket(org.xar.ck3.control.contracts.ExactRef expected) {
        try {
            need(expected.bytes()>0&&expected.bytes()<=NativeWire.MAXIMUM_FRAME_BYTES+4L,"bounded original guarded packet required");
            var witness=org.xar.ck3.control.build.SharedSourceFiles.observe(java.nio.file.Path.of(expected.path()));
            need(witness.source().bytes()==expected.bytes()&&witness.source().sha256().equals(expected.sha256()),"original guarded packet bytes/SHA differ");
            byte[] bytes=java.nio.file.Files.readAllBytes(java.nio.file.Path.of(expected.path()));
            need(bytes.length==expected.bytes()&&java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)).equals(expected.sha256()),"original packet changed while reading");
            org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(witness);return bytes;
        }catch(java.security.NoSuchAlgorithmException failure){throw new IllegalStateException("SHA256 unavailable",failure);
        }catch(IOException failure){throw new IllegalArgumentException("original guarded packet unavailable",failure);}
    }
    static Build boundBuild(PlanningReadReceipt receipt) {
        try {
            var original=NativeWire.decode(originalPacket(receipt.before().binding().capabilityEvidence()));
            need(original instanceof NativeWire.Hello,"guard must bind original Native hello");var hello=(NativeWire.Hello)original;
            need(hello.pid()==factual(receipt.request()).game().pid()&&hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration())&&hello.buildMatch()&&hello.adapterStatus().equals("ready"),"original collector hello process/session drift");
            for(Build b:Build.values())if(b.sha256().equalsIgnoreCase(hello.gameSha256()))return b;
            throw new IllegalArgumentException("original connected exact build unrecognized");
        }catch(IOException failure){throw new IllegalArgumentException("original Native hello malformed",failure);}
    }
    static ObjectNode envelope(PlanningReadReceipt receipt,String domain,String nested,String suffix,Build required) {
        ObjectNode raw=result(receipt); equal(raw,"step",receipt.request().operation().value()); yes(raw,"accepted"); yes(raw,"private_build"); yes(raw,"read_only"); no(raw,"advertised");
        Build b=build(raw); need((required==null||required==b)&&b==boundBuild(receipt),"wrong connected build for private collector"); equal(raw,"backend_id","ck3-"+b.version()+"-native-"+suffix);
        equal(raw,"domain_key",domain); equal(raw,"snapshot_revision",nativeRevision(receipt)); equal(raw,"date_raw",date(receipt));
        ObjectNode value=object(field(raw,nested)); need(build(value)==b,"nested/native envelope build mismatch"); return value;
    }
    static void status(PlanningReadReceipt receipt,Availability available) { equal(result(receipt),"status",available.available()?"observed":"unavailable"); }
    static <T> Sample<T> sample(JsonNode row,String observed,String key,Function<JsonNode,T> decoder) { boolean flag=bool(row,observed); JsonNode n=field(row,key); if(!flag){need(n.isNull(),"unobserved native sample must remain null");return new Sample<>(false,null);} need(!n.isNull(),"observed native sample cannot be null");return new Sample<>(true,decoder.apply(n)); }
    static BigInteger scalar(JsonNode n,BigInteger low,BigInteger high) { need(n.isIntegralNumber(),"exact integer JSON token required"); return range(n.bigIntegerValue(),low,high); }
    static Boolean scalarBoolean(JsonNode n) { need(n.isBoolean(),"exact boolean JSON token required"); return n.booleanValue(); }
    static String scalarText(JsonNode n) { need(n.isTextual(),"exact text JSON token required"); return n.textValue(); }
}
