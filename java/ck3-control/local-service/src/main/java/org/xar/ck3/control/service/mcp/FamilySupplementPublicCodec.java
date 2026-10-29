package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** The four original Driver read signatures. Native projections remain owned by their shared producers. */
public final class FamilySupplementPublicCodec {
    private static final BigInteger SAFE=BigInteger.valueOf(9007199254740991L);
    private static final Set<String> WIDE=Set.of("query_sequence","observation_revision","snapshot_revision","native_revision",
            "queried_revision","queried_native_revision","legality_query_sequence");
    private FamilySupplementPublicCodec() {}
    public sealed interface Request permits Obligations,ChildSubject,ChildValue,Treatment {}
    public enum Presence {MISSING,NULL,VALUE}
    public record IdSelector(Presence presence,OptionalLong value) {
        public IdSelector {
            Objects.requireNonNull(presence);Objects.requireNonNull(value);
            StrictJson.require((presence==Presence.VALUE)==value.isPresent(),"selector presence and value differ");
            value.ifPresent(FamilySupplementPublicCodec::fullId);
        }
    }
    public record Obligations(BigInteger expectedRevision,IdSelector subject,IdSelector candidate,boolean matrilineal,
            IdSelector breakRecipient,IdSelector ally,boolean enumerateAllies) implements Request {
        public Obligations {
            revision(expectedRevision);Objects.requireNonNull(subject);Objects.requireNonNull(candidate);Objects.requireNonNull(breakRecipient);Objects.requireNonNull(ally);
            FamilySupplementPublicCodec.nativeRequest(expectedRevision,subject,candidate,matrilineal,breakRecipient,ally,enumerateAllies);
        }
        public FamilyObligations.Request nativeRequest(){return FamilySupplementPublicCodec.nativeRequest(expectedRevision,subject,candidate,matrilineal,breakRecipient,ally,enumerateAllies);}
    }
    public record ChildSubject(BigInteger expectedNativeRevision,int subjectCharacterId,boolean diagnoseFamilyArrays) implements Request {
        public ChildSubject {revision(expectedNativeRevision);positiveInt(subjectCharacterId);}
    }
    public record ChildValue(Obj legality,int candidateCharacterId,boolean requestMatrilineal) implements Request {
        public ChildValue {
            Objects.requireNonNull(legality);positiveInt(candidateCharacterId);
            ObjectNode row=nodeObject(OpportunityJson.toNode(legality));
            StrictJson.require("xar.ck3.player-child-marriage-subject.v1".equals(StrictJson.text(row.get("schema")))
                    &&"available".equals(StrictJson.text(row.get("status")))&&bool(row.get("player_child_verified"))
                    &&bool(row.get("read_only"))&&!bool(row.get("advertised")),
                    "child value requires a complete available native subject projection");
            revision(exactInternal(row.get("query_sequence")));revision(exactInternal(row.get("native_revision")));
        }
    }
    public record Treatment(BigInteger expectedRevision) implements Request {public Treatment {revision(expectedRevision);}}
    public static Obligations decodeObligations(RawJson raw) {
        ObjectNode row=fields(raw,Set.of("expected_revision","subject_character_id","candidate_character_id","request_matrilineal_option",
                "break_recipient_character_id","ally_character_id","enumerate_current_allies"),Set.of("expected_revision"));
        return new Obligations(uint64(row.get("expected_revision")),selector(row,"subject_character_id"),selector(row,"candidate_character_id"),
                option(row,"request_matrilineal_option"),selector(row,"break_recipient_character_id"),selector(row,"ally_character_id"),option(row,"enumerate_current_allies"));
    }
    public static ChildSubject decodeSubject(RawJson raw) {
        ObjectNode row=fields(raw,Set.of("expected_native_revision","subject_character_id","diagnose_family_arrays"),Set.of("expected_native_revision","subject_character_id"));
        return new ChildSubject(uint64(row.get("expected_native_revision")),positiveIntNode(row.get("subject_character_id")),option(row,"diagnose_family_arrays"));
    }
    public static ChildValue decodeValue(RawJson raw) {
        ObjectNode row=fields(raw,Set.of("legality","candidate_character_id","request_matrilineal_option"),Set.of("legality","candidate_character_id"));
        ObjectNode legality=nodeObject(row.get("legality")).deepCopy();McpJson.publicNumbers(legality);internalWide(legality);
        return new ChildValue(object(legality),positiveIntNode(row.get("candidate_character_id")),option(row,"request_matrilineal_option"));
    }
    public static Treatment decodeTreatment(RawJson raw) {
        ObjectNode row=fields(raw,Set.of("expected_revision"),Set.of("expected_revision"));return new Treatment(uint64(row.get("expected_revision")));
    }
    public static RawJson encodeRequest(Request request) {
        Objects.requireNonNull(request);ObjectNode row=StrictJson.object();
        if(request instanceof Obligations r) {
            row.put("expected_revision",r.expectedRevision().toString());put(row,"subject_character_id",r.subject());put(row,"candidate_character_id",r.candidate());
            row.put("request_matrilineal_option",r.matrilineal());put(row,"break_recipient_character_id",r.breakRecipient());put(row,"ally_character_id",r.ally());
            row.put("enumerate_current_allies",r.enumerateAllies());
        } else if(request instanceof ChildSubject r)row.put("expected_native_revision",r.expectedNativeRevision().toString()).put("subject_character_id",r.subjectCharacterId()).put("diagnose_family_arrays",r.diagnoseFamilyArrays());
        else if(request instanceof ChildValue r) {row.set("legality",publicNode(r.legality()));row.put("candidate_character_id",r.candidateCharacterId()).put("request_matrilineal_option",r.requestMatrilineal());}
        else if(request instanceof Treatment r)row.put("expected_revision",r.expectedRevision().toString());
        else throw new IllegalArgumentException("unknown family public read request");
        return raw(row);
    }
    /** Only actual native projection data arrives here; this formatter grants no read or action authority. */
    public static RawJson publicResult(Obj actual) {ObjectNode row=publicNode(actual);McpJson.publicNumbers(row);return raw(row);}
    private static ObjectNode publicNode(Obj actual) {ObjectNode row=nodeObject(OpportunityJson.toNode(actual)).deepCopy();publicWide(row);return row;}
    private static void publicWide(JsonNode node) {
        if(node.isObject()) {
            var row=(ObjectNode)node;var names=new java.util.ArrayList<String>();row.fieldNames().forEachRemaining(names::add);
            for(String key:names) {JsonNode value=row.get(key);
                if(WIDE.contains(key)&&!value.isNull()) {
                    BigInteger n=value.isIntegralNumber()?value.bigIntegerValue():canonical(value);
                    StrictJson.require(n.signum()>=0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"actual native uint64 projection changed");row.put(key,n.toString());
                } else if(value.isIntegralNumber()&&value.bigIntegerValue().abs().compareTo(SAFE)>0) {
                    BigInteger n=value.bigIntegerValue();StrictJson.require(n.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"actual wide native integer outside supported domain");row.put(key,n.toString());
                } else if(value.isArray()) {
                    var values=(com.fasterxml.jackson.databind.node.ArrayNode)value;
                    for(int i=0;i<values.size();i++){JsonNode item=values.get(i);if(item.isIntegralNumber()&&item.bigIntegerValue().abs().compareTo(SAFE)>0)values.set(i,com.fasterxml.jackson.databind.node.TextNode.valueOf(item.bigIntegerValue().toString()));else publicWide(item);}
                } else publicWide(value);
            }
        } else if(node.isArray())node.forEach(FamilySupplementPublicCodec::publicWide);
    }
    private static void internalWide(JsonNode node) {
        if(node.isObject()) {
            var row=(ObjectNode)node;var names=new java.util.ArrayList<String>();row.fieldNames().forEachRemaining(names::add);
            for(String key:names) {JsonNode value=row.get(key);if(WIDE.contains(key)&&!value.isNull())row.put(key,uint64(value));
                else if(key.equals("recipient_ai_accept_raw")&&value.isTextual()) {
                    StrictJson.require(value.textValue().matches("0|-?[1-9][0-9]*"),"canonical signed native acceptance required");BigInteger n=new BigInteger(value.textValue());
                    StrictJson.require(n.compareTo(BigInteger.valueOf(Long.MIN_VALUE))>=0&&n.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"native signed acceptance outside int64");row.put(key,n);
                } else internalWide(value);}
        } else if(node.isArray())node.forEach(FamilySupplementPublicCodec::internalWide);
    }
    private static FamilyObligations.Request nativeRequest(BigInteger revision,IdSelector subject,IdSelector candidate,boolean matrilineal,IdSelector recipient,IdSelector ally,boolean enumerate) {
        StrictJson.require(subject.value().isPresent()==candidate.value().isPresent(),"both distinct full family pair IDs are required together");
        Optional<FamilyObligations.Pair> pair=subject.value().isPresent()?Optional.of(new FamilyObligations.Pair(subject.value().getAsLong(),candidate.value().getAsLong())):Optional.empty();
        return new FamilyObligations.Request(revision,pair,matrilineal,recipient.value(),ally.value(),enumerate);
    }
    private static IdSelector selector(ObjectNode row,String key) {
        if(!row.has(key))return new IdSelector(Presence.MISSING,OptionalLong.empty());
        if(row.get(key).isNull())return new IdSelector(Presence.NULL,OptionalLong.empty());
        JsonNode value=row.get(key);StrictJson.require(value.isIntegralNumber(),"full character ID must be an exact bounded integer");
        BigInteger exact=value.bigIntegerValue();StrictJson.require(exact.signum()>0&&exact.compareTo(BigInteger.valueOf(0xffff_ffffL))<=0,"full uint32 selector required");long n=exact.longValue();fullId(n);return new IdSelector(Presence.VALUE,OptionalLong.of(n));
    }
    private static void put(ObjectNode row,String key,IdSelector selector) {
        if(selector.presence()==Presence.NULL)row.putNull(key);else if(selector.presence()==Presence.VALUE)row.put(key,selector.value().getAsLong());
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value!=null&&value.isBoolean(),"family public read flag must be an exact JSON boolean");
        return value.booleanValue();
    }
    private static boolean option(ObjectNode row,String key){return row.has(key)&&bool(row.get(key));}
    private static int positiveIntNode(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber(),"native child ID must be an exact integer");BigInteger exact=value.bigIntegerValue();StrictJson.require(exact.signum()>0&&exact.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"positive signed int32 child ID required");return exact.intValue();}
    private static void positiveInt(int n){StrictJson.require(n>0,"positive signed int32 child ID required");}
    private static void fullId(long n){StrictJson.require(n>0&&n<=0xffff_ffffL,"positive full uint32 family ID required");}
    private static BigInteger uint64(JsonNode value) {
        StrictJson.require(value!=null,"required revision is missing");BigInteger n;
        if(value.isTextual())n=canonical(value);
        else {StrictJson.require(value.isIntegralNumber(),"revision must be safe integer or canonical uint64 string");n=value.bigIntegerValue();StrictJson.require(n.compareTo(SAFE)<=0,"unsafe JSON revision must use decimal string");}
        revision(n);return n;
    }
    private static BigInteger canonical(JsonNode value){StrictJson.require(value.isTextual()&&value.textValue().matches("0|[1-9][0-9]*"),"canonical decimal uint64 string required");return new BigInteger(value.textValue());}
    private static BigInteger exactInternal(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber(),"internal native sequence must be exact");return value.bigIntegerValue();}
    private static void revision(BigInteger n){StrictJson.require(n!=null&&n.signum()>0&&n.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 revision required");}
    private static ObjectNode fields(RawJson raw,Set<String> allowed,Set<String> required) {
        ObjectNode row=nodeObject(StrictJson.parse(Objects.requireNonNull(raw).bytes(),1048576));
        row.fieldNames().forEachRemaining(k->StrictJson.require(allowed.contains(k),"unknown family public read field: "+k));
        for(String key:required)StrictJson.require(row.has(key),"missing family public read field: "+key);return row;
    }
    private static ObjectNode nodeObject(JsonNode value){if(value instanceof ObjectNode row)return row;throw new IllegalArgumentException("JSON object required");}
    private static Obj object(JsonNode row){return DriverJson.object(StrictJson.canonical(row,1048576),1048576);}
    private static RawJson raw(JsonNode row){return new RawJson(StrictJson.canonical(row,1048576));}
}

