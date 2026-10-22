package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** Native launch fields use numeric uint64 FILETIME in the Python-only JSON lane. */
public record GameGeneration(long pid, PythonOnlyUInt64 creationFiletime) {
    public GameGeneration {
        StrictJson.require(pid > 0 && pid <= 4_294_967_295L, "native PID range");
        StrictJson.require(creationFiletime != null && creationFiletime.value().signum() > 0,
                "positive native process FILETIME required");
    }
    public static GameGeneration fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("pid", "creation_filetime"));
        return new GameGeneration(StrictJson.integer(row.get("pid"), 1, 4_294_967_295L),
                new PythonOnlyUInt64(StrictJson.integer(row.get("creation_filetime"), BigInteger.ONE, StrictJson.UINT64_MAX)));
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("pid", pid);
        row.put("creation_filetime", creationFiletime.value());
        return row;
    }
}
