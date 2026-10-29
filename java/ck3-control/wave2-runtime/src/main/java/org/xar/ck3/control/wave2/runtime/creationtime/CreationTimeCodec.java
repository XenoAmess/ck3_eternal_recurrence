package org.xar.ck3.control.wave2.runtime.creationtime;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Versioned raw JSON boundary; it neither reads a process nor manufactures an identity. */
public final class CreationTimeCodec {
    public static final String SCHEMA = "g2.wave2-runtime.creationtime-request/v1";
    private CreationTimeCodec() { }
    public static byte[] evaluate(byte[] raw) {
        try {
            ObjectNode request = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "operation", "arguments"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "creation time request schema differs");
            String operation = StrictJson.text(request.get("operation"));
            ObjectNode result = StrictJson.object();
            switch (operation) {
                case "process_creation_utc" -> {
                    ObjectNode args = StrictJson.object(request.get("arguments"), Set.of("value"));
                    result.put("utc", ProcessCreationTime.parse(StrictJson.text(args.get("value"))).utcIsoformat());
                }
                case "same_process_creation_time" -> {
                    ObjectNode args = StrictJson.object(request.get("arguments"), Set.of("first", "second"));
                    result.put("same", ProcessCreationTime.same(observedText(args.get("first")), observedText(args.get("second"))));
                }
                default -> throw new ContractViolationException("unknown process creation time operation");
            }
            return StrictJson.canonical(result, 1024);
        } catch (ContractViolationException error) { throw error; }
        catch (IllegalArgumentException error) { throw new ContractViolationException("invalid process birth contract: " + error.getMessage(), error); }
    }
    /** A non-text observation is unavailable, never a successfully parsed or unequal process identity. */
    private static String observedText(JsonNode value) { return value != null && value.isTextual() ? value.textValue() : null; }
}
