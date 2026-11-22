package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual binary32 scrollbar DATA and the separately sampled production route predicates. No price or display interpretation. */
public record CurrentXqolThresholdSource(CurrentXqolPromptSource prompt,boolean scrollbarFound,boolean handleFound,
        boolean nativeFixedRouteFound,Optional<Boolean> nativeShown,Optional<Boolean> nativeValid,
        Optional<Long> valueBitsU32,Optional<Long> minimumBitsU32,Optional<Long> maximumBitsU32,Optional<Long> stepBitsU32,
        int targetThreshold,boolean setAdmissible) {
    public CurrentXqolThresholdSource {
        Objects.requireNonNull(prompt);Objects.requireNonNull(nativeShown);Objects.requireNonNull(nativeValid);
        Objects.requireNonNull(valueBitsU32);Objects.requireNonNull(minimumBitsU32);Objects.requireNonNull(maximumBitsU32);Objects.requireNonNull(stepBitsU32);
        CurrentXqolThreshold.requireTarget(targetThreshold);for(var bits:java.util.List.of(valueBitsU32,minimumBitsU32,maximumBitsU32,stepBitsU32))bits.ifPresent(n->StrictJson.require(n>=0&&n<=0xffff_ffffL,"Actual UInt32 float bits required"));
        if(prompt.event().isEmpty())StrictJson.require(!scrollbarFound&&!handleFound&&!nativeFixedRouteFound&&nativeShown.isEmpty()&&nativeValid.isEmpty()&&valueBitsU32.isEmpty()&&minimumBitsU32.isEmpty()&&maximumBitsU32.isEmpty()&&stepBitsU32.isEmpty()&&!setAdmissible,"Absent known prompt retains null scrollbar/predicate roles");
        else {
            StrictJson.require(scrollbarFound&&handleFound&&valueBitsU32.isPresent()&&minimumBitsU32.filter(n->n==0).isPresent()&&maximumBitsU32.filter(n->n==0x42c80000L).isPresent()&&stepBitsU32.filter(n->n==0x3f800000L).isPresent(),"Actual scrollbar range0/100/step1 bits required");
            float value=Float.intBitsToFloat(valueBitsU32.orElseThrow().intValue());StrictJson.require(Float.isFinite(value)&&value>=0&&value<=100,"Finite actual scrollbar value0..100 required");
            StrictJson.require(nativeFixedRouteFound?nativeShown.isPresent()&&nativeValid.isPresent():nativeShown.isEmpty()&&nativeValid.isEmpty(),"Actual fixed-route predicate null roles differ");
            if(setAdmissible){var e=prompt.event().orElseThrow();StrictJson.require(e.windowVisible()&&e.windowEnabled()&&nativeFixedRouteFound&&nativeShown.filter(Boolean::booleanValue).isPresent()&&nativeValid.filter(Boolean::booleanValue).isPresent(),"Known native shown/valid and current visible enabled source required for set");}
        }
    }
    public Optional<Float> observedValue(){return valueBitsU32.map(n->Float.intBitsToFloat(n.intValue()));}
    static CurrentXqolThresholdSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","prompt","scrollbar_found","handle_found","native_fixed_route_found","native_shown","native_valid","value_bits_u32","minimum_bits_u32","maximum_bits_u32","step_bits_u32","target_threshold","set_admissible"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentXqolThreshold.SOURCE_SCHEMA))throw new IOException("Exact XQOL threshold source schema required");
        return new CurrentXqolThresholdSource(CurrentXqolPromptSource.decode(r.get("prompt")),bool(r,"scrollbar_found"),bool(r,"handle_found"),bool(r,"native_fixed_route_found"),maybeBool(r.get("native_shown")),maybeBool(r.get("native_valid")),bits(r.get("value_bits_u32")),bits(r.get("minimum_bits_u32")),bits(r.get("maximum_bits_u32")),bits(r.get("step_bits_u32")),NativeWire.integer(r.get("target_threshold"),BigInteger.ZERO,BigInteger.valueOf(100)).intValueExact(),bool(r,"set_admissible"));
    }
    ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentXqolThreshold.SOURCE_SCHEMA).put("scrollbar_found",scrollbarFound).put("handle_found",handleFound).put("native_fixed_route_found",nativeFixedRouteFound).put("target_threshold",targetThreshold).put("set_admissible",setAdmissible);r.set("prompt",prompt.encode());putBool(r,"native_shown",nativeShown);putBool(r,"native_valid",nativeValid);putBits(r,"value_bits_u32",valueBitsU32);putBits(r,"minimum_bits_u32",minimumBitsU32);putBits(r,"maximum_bits_u32",maximumBitsU32);putBits(r,"step_bits_u32",stepBitsU32);return r;
    }
    private static Optional<Long> bits(JsonNode n)throws IOException{
        if(n.isNull())return Optional.empty();String s=NativeWire.text(n);if(!s.matches("0|[1-9][0-9]{0,9}"))throw new IOException("Canonical actual UInt32 bits string required");return Optional.of(NativeWire.integer(new com.fasterxml.jackson.databind.node.BigIntegerNode(new BigInteger(s)),BigInteger.ZERO,BigInteger.valueOf(0xffff_ffffL)).longValueExact());
    }
    private static Optional<Boolean> maybeBool(JsonNode n)throws IOException{if(n.isNull())return Optional.empty();if(!n.isBoolean())throw new IOException("Actual bool or unobserved null required");return Optional.of(n.booleanValue());}
    private static boolean bool(ObjectNode r,String key)throws IOException{return maybeBool(r.get(key)).orElseThrow(()->new IOException("Actual threshold bool required: "+key));}
    private static void putBool(ObjectNode r,String k,Optional<Boolean> v){if(v.isPresent())r.put(k,v.orElseThrow());else r.putNull(k);}
    private static void putBits(ObjectNode r,String k,Optional<Long> v){if(v.isPresent())r.put(k,Long.toUnsignedString(v.orElseThrow()));else r.putNull(k);}
}
