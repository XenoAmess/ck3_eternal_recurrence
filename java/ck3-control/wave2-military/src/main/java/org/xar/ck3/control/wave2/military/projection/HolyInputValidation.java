package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Input guards only. Never wrap an algorithm, output builder, serializer or complete projection in this boundary. */
public final class HolyInputValidation {
    private HolyInputValidation() { }
    public static void require(boolean condition, String reason) {
        if (!condition) { throw new ProjectionDomainRejection(reason); }
    }
    public static ObjectNode object(JsonNode value, Set<String> fields) {
        Objects.requireNonNull(fields);
        try { return StrictJson.object(value, fields); }
        catch (ContractViolationException refusal) { throw new ProjectionDomainRejection(refusal.getMessage()); }
    }
    public static ObjectNode parseObject(byte[] raw, int maximumBytes, Set<String> fields) {
        if (maximumBytes < 1 || maximumBytes > StrictJson.EXPLICIT_MAX_BYTES) {
            throw new IllegalArgumentException("internal input guard byte budget invalid");
        }
        JsonNode value;
        try { value = StrictJson.parse(raw, maximumBytes); }
        catch (ContractViolationException refusal) { throw new ProjectionDomainRejection(refusal.getMessage()); }
        return object(value, fields);
    }
    public static long integer(JsonNode value, long minimum, long maximum) {
        if (minimum > maximum) { throw new IllegalArgumentException("internal input guard range inverted"); }
        try { return StrictJson.integer(value, minimum, maximum); }
        catch (ContractViolationException refusal) { throw new ProjectionDomainRejection(refusal.getMessage()); }
    }
    public static String text(JsonNode value) {
        try { return StrictJson.text(value); }
        catch (ContractViolationException refusal) { throw new ProjectionDomainRejection(refusal.getMessage()); }
    }
}
