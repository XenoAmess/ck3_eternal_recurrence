package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** Only the existing opaque Python map v1 boundary uses integers. No alternate-type fallback. */
public final class PythonOpaqueGameGenerationV1 {
    private PythonOpaqueGameGenerationV1() { }
    public static PythonOnlyUInt64 filetime(JsonNode token) {
        return new PythonOnlyUInt64(StrictJson.integer(token, BigInteger.ONE, StrictJson.UINT64_MAX));
    }
    public static GameGeneration fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("pid", "creation_filetime"));
        return new GameGeneration(StrictJson.integer(row.get("pid"), 1, 0xffff_ffffL), filetime(row.get("creation_filetime")));
    }
    public static ObjectNode toJson(GameGeneration value) {
        StrictJson.require(value != null, "exact held Game value required");
        ObjectNode row = StrictJson.object(); row.put("pid", value.pid()); row.put("creation_filetime", value.creationFiletime().value());
        return row;
    }
}
