package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** Exact kernel process birth in 100 ns ticks; cross-language JSON uses a decimal string. */
public record GameGeneration(long pid, PythonOnlyUInt64 creationFiletime) {
    public GameGeneration {
        StrictJson.require(pid > 0 && pid <= 4_294_967_295L, "native PID range");
        StrictJson.require(creationFiletime != null && creationFiletime.value().signum() > 0,
                "positive exact native process FILETIME required");
    }
    public static GameGeneration fromJson(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("pid", "creation_filetime"));
        return new GameGeneration(StrictJson.integer(row.get("pid"), 1, 4_294_967_295L),
                parseCreationFiletime(row.get("creation_filetime")));
    }
    /** This boundary accepts no legacy number, timestamp, rounding or unit conversion. */
    public static PythonOnlyUInt64 parseCreationFiletime(JsonNode value) {
        String decimal = new CrossJsDecimalUInt64(StrictJson.text(value)).decimal();
        BigInteger exact = new BigInteger(decimal);
        StrictJson.require(exact.signum() > 0, "positive exact native process FILETIME required");
        return new PythonOnlyUInt64(exact);
    }
    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object();
        row.put("pid", pid);
        row.put("creation_filetime", creationFiletime.value().toString());
        return row;
    }
}
