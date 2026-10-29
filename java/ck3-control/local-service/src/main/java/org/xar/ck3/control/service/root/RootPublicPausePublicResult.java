package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact public representation of the original pause result and its finite recovery report. */
public final class RootPublicPausePublicResult {
    private RootPublicPausePublicResult() { }

    private static final Set<String> PRIMITIVE_COUNTERS=Set.of(
            "revision","snapshot_revision","native_revision","queried_revision","queried_native_revision");
    private static final Set<String> RECOVERY_COUNTERS=Set.of(
            "starting_revision","starting_native_revision","refreshed_revision","refreshed_native_revision",
            "ending_revision","ending_native_revision");

    public static RawJson present(RawJson numeric) {
        ObjectNode projected=PublicDataJson.object(numeric);
        primitive(projected);
        JsonNode recovery=projected.get("map_control_recovery");
        if(recovery!=null){
            ObjectNode fields=object(recovery,"actual pause recovery object required");
            counters(fields,RECOVERY_COUNTERS);
            JsonNode attempts=fields.get("attempts");
            if(attempts!=null){
                require(attempts.isArray(),"actual pause attempts array required");
                attempts.forEach(value->primitive(object(value,"actual pause attempt object required")));
            }
        }
        requireSafeUnclassifiedIntegers(projected);
        return PublicDataJson.encodePreservingDecimals(projected,numeric);
    }

    private static void primitive(ObjectNode value){
        counters(value,PRIMITIVE_COUNTERS);
        JsonNode postcondition=value.get("map_control_postcondition");
        if(postcondition!=null)counters(object(postcondition,"actual pause postcondition object required"),RECOVERY_COUNTERS);
    }

    private static ObjectNode object(JsonNode value,String reason){
        require(value instanceof ObjectNode,reason);return (ObjectNode)value;
    }

    private static void counters(ObjectNode object,Set<String> names){
        for(String name:names){
            JsonNode value=object.get(name);
            if(value!=null&&!value.isNull())object.put(name,
                    StrictJson.integer(value,BigInteger.ZERO,StrictJson.UINT64_MAX).toString());
        }
    }

    private static void requireSafeUnclassifiedIntegers(JsonNode node){
        if(node.isIntegralNumber())require(node.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,
                "unclassified original pause integer needs an explicit public field contract");
        else if(node.isContainerNode())node.forEach(RootPublicPausePublicResult::requireSafeUnclassifiedIntegers);
    }
}
