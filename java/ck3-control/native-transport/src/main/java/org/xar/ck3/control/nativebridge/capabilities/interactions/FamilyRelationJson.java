package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Narrow helpers for the registered relation boundary; parsing remains the sole InteractionJson parser. */
final class FamilyRelationJson {
    static final BigInteger I32_MIN=BigInteger.valueOf(Integer.MIN_VALUE),I32_MAX=BigInteger.valueOf(Integer.MAX_VALUE),
            I16_MIN=BigInteger.valueOf(Short.MIN_VALUE),I16_MAX=BigInteger.valueOf(Short.MAX_VALUE);
    private FamilyRelationJson() { }
    enum Status { AVAILABLE, PARTIAL, UNAVAILABLE, NOT_APPLICABLE, NOT_REQUIRED }
    record Availability(Status status,String unavailableReason) {
        Availability { Objects.requireNonNull(status);need(status==Status.AVAILABLE?unavailableReason==null:unavailableReason!=null&&!unavailableReason.isEmpty(),"relation availability/reason differs"); }
        boolean available(){return status==Status.AVAILABLE;}
    }
    /** The presence bit retains missing versus explicit null at optional legacy boundaries. */
    record Slot<T>(boolean present,java.util.Optional<T> value) {
        Slot {Objects.requireNonNull(value);need(present||value.isEmpty(),"missing optional leaf cannot have a value");}
    }
    static JsonNode maybe(JsonNode n,String key){object(n);return n.get(key);}
    static boolean absent(JsonNode n){return n==null||n.isNull();}
    static boolean isTrue(JsonNode n){return n!=null&&n.isBoolean()&&n.booleanValue();}
    static boolean isFalse(JsonNode n){return n!=null&&n.isBoolean()&&!n.booleanValue();}
    static boolean equal(JsonNode n,String key,Object expected){
        JsonNode actual=maybe(n,key);if(expected==null)return absent(actual);
        if(expected instanceof BigInteger number)return actual!=null&&actual.isIntegralNumber()&&actual.bigIntegerValue().equals(number);
        if(expected instanceof Integer number)return equal(n,key,BigInteger.valueOf(number));
        if(expected instanceof Long number)return equal(n,key,BigInteger.valueOf(number));
        if(expected instanceof Boolean flag)return actual!=null&&actual.isBoolean()&&actual.booleanValue()==flag;
        if(expected instanceof String text)return actual!=null&&actual.isTextual()&&actual.textValue().equals(text);
        throw new IllegalArgumentException("unsupported typed relation equality operand");
    }
    static BigInteger optionalNumber(JsonNode n,String key,BigInteger low,BigInteger high){JsonNode v=maybe(n,key);if(absent(v))return null;need(v.isIntegralNumber(),"exact relation integer required: "+key);return range(v.bigIntegerValue(),low,high);}
    static BigInteger nullableNumberRequired(JsonNode n,String key,BigInteger low,BigInteger high){field(n,key);return optionalNumber(n,key,low,high);}
    static Boolean optionalBoolean(JsonNode n,String key){JsonNode v=maybe(n,key);if(absent(v))return null;need(v.isBoolean(),"exact relation boolean required: "+key);return v.booleanValue();}
    static Boolean nullableBooleanRequired(JsonNode n,String key){field(n,key);return optionalBoolean(n,key);}
    static String optionalString(JsonNode n,String key){JsonNode v=maybe(n,key);if(absent(v))return null;need(v.isTextual(),"relation text required: "+key);return v.textValue();}
    static Availability availability(JsonNode n,Set<Status> allowed){Status status;try{status=Status.valueOf(text(n,"status").toUpperCase(java.util.Locale.ROOT));}catch(IllegalArgumentException bad){throw new IllegalArgumentException("relation status is unknown",bad);}need(allowed.contains(status),"relation status outside this leaf");return new Availability(status,optionalString(n,"unavailable_reason"));}
    static Availability observation(JsonNode n,String source,Set<Status> allowed){object(n);eq(n,"source",source);field(n,"unavailable_reason");return availability(n,allowed);}
    static List<JsonNode> rows(JsonNode n,String key,int maximum){return list(n,key,maximum,row->object(row));}
    static List<BigInteger> integers(JsonNode n,String key,int maximum,BigInteger low,BigInteger high){return list(n,key,maximum,row->{need(row.isIntegralNumber(),"relation ordered integer array required");return range(row.bigIntegerValue(),low,high);});}
    static List<String> strings(JsonNode n,String key,int maximum){return list(n,key,maximum,row->{need(row.isTextual(),"relation ordered string array required");return row.textValue();});}
    // The normalized education projection may exceed the original 8 MiB pipe
    // packet while remaining within the existing 64 MiB owned-material lane.
    static OpportunityJson.Obj retain(JsonNode n){return DriverJson.object(object(n).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);}
    static ObjectNode nativeObject(OpportunityJson.Obj value){return object(OpportunityJson.toNode(value));}
    static long fullBits(BigInteger signed){return range(signed,I32_MIN,U32).and(U32).longValueExact();}
    static BigInteger signedFull(BigInteger raw){range(raw,BigInteger.ZERO,U32);return raw.testBit(31)?raw.subtract(BigInteger.ONE.shiftLeft(32)):raw;}
    static void nilOptional(JsonNode n,String...keys){for(String key:keys)need(absent(maybe(n,key)),"unobserved relation value must remain null: "+key);}
    static void boundedReason(JsonNode n,String key){need(!text(n,key).isEmpty(),"relation unavailable reason required: "+key);}
    static void canonicalSubset(JsonNode n,String queried,String present,List<String> catalog,boolean available){need(strings(n,queried,catalog.size()).equals(catalog),"relation trait query catalog/order changed");if(!available){need(absent(maybe(n,present)),"unavailable traits became a known empty subset");return;}List<String> values=strings(n,present,catalog.size());need(values.equals(catalog.stream().filter(values::contains).toList()),"relation trait subset/order changed");}
    static List<BigInteger> indices(JsonNode n,String key){List<BigInteger> values=integers(n,key,4096,BigInteger.ZERO,U32);need(!values.isEmpty(),"nonempty occurrence group required");BigInteger previous=BigInteger.valueOf(-1);for(BigInteger v:values){need(v.compareTo(previous)>0,"occurrence group is not strictly ordered");previous=v;}return values;}
    static List<String> fields(JsonNode n){List<String> names=new ArrayList<>();object(n).fieldNames().forEachRemaining(names::add);return List.copyOf(names);}
}
