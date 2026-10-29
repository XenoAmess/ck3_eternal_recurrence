package org.xar.ck3.control.wave3.runtime.processcustody;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.LegacyProcessIdentityCodecV1;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ErrorStage;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ObservationError;

/** Historical Python-only opaque observation bytes. Decoding never creates a retained handle. */
public final class LegacyProcessObservationCodecV1 {
    private static final Set<String> FIELDS = Set.of("pid", "creation_filetime", "executable",
            "kernel_exit_observed", "wait_result", "exit_code", "observation_error");
    private static final Set<String> ERROR_FIELDS = Set.of("stage", "type", "message");
    private static final ObjectMapper WRITER = new ObjectMapper();

    private LegacyProcessObservationCodecV1() { }

    public static ProcessObservationV1 decode(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw), FIELDS);
        ObjectNode identity = StrictJson.object(); identity.put("role", "archived-observation");
        identity.set("pid", value.get("pid")); identity.set("creation_filetime", value.get("creation_filetime"));
        identity.set("executable", value.get("executable"));
        // Reject an original 17.0 token before a normalized DecimalNode can be emitted as 17.
        var parsed = LegacyProcessIdentityCodecV1.decode(StrictJson.canonical(identity));
        JsonNode signal = value.get("kernel_exit_observed");
        StrictJson.require(signal.isNull() || signal.isBoolean(), "explicit nullable native wait signal required");
        KernelSignal state = signal.isNull() ? KernelSignal.UNKNOWN
                : signal.booleanValue() ? KernelSignal.SIGNALED : KernelSignal.UNSIGNALED;
        OptionalLong wait = nullableInteger(value.get("wait_result"), Long.MIN_VALUE, Long.MAX_VALUE);
        OptionalLong exit = nullableInteger(value.get("exit_code"), 0, 0xffff_ffffL);
        Optional<ObservationError> error = Optional.empty();
        if (!value.get("observation_error").isNull()) {
            ObjectNode failure = StrictJson.object(value.get("observation_error"), ERROR_FIELDS);
            ErrorStage stage = switch (StrictJson.text(failure.get("stage"))) {
                case "closed" -> ErrorStage.CLOSED;
                case "wait" -> ErrorStage.WAIT;
                case "exit_code" -> ErrorStage.EXIT_CODE;
                default -> throw new ContractViolationException("exact observation error stage required");
            };
            JsonNode message = failure.get("message");
            StrictJson.require(message.isTextual(), "actual error message string required");
            error = Optional.of(new ObservationError(stage, StrictJson.text(failure.get("type")), message.textValue()));
        }
        return new ProcessObservationV1(parsed.identity(), wait, state, exit, error);
    }

    public static byte[] encode(ProcessObservationV1 value) {
        StrictJson.require(value != null, "validated observation required");
        ObjectNode identity = StrictJson.object(StrictJson.parse(LegacyProcessIdentityCodecV1.encode(
                new LegacyProcessIdentityCodecV1.RoleIdentity("archived-observation", value.identity()))),
                Set.of("role", "pid", "creation_filetime", "executable"));
        identity.remove("role");
        if (value.signal() == KernelSignal.UNKNOWN) { identity.putNull("kernel_exit_observed"); }
        else { identity.put("kernel_exit_observed", value.signal() == KernelSignal.SIGNALED); }
        if (value.waitResult().isPresent()) { identity.put("wait_result", value.waitResult().getAsLong()); }
        else { identity.putNull("wait_result"); }
        if (value.exitCode().isPresent()) { identity.put("exit_code", value.exitCode().getAsLong()); }
        else { identity.putNull("exit_code"); }
        if (value.error().isPresent()) {
            ObservationError error = value.error().orElseThrow();
            ObjectNode failure = identity.putObject("observation_error");
            failure.put("stage", switch (error.stage()) {
                case CLOSED -> "closed"; case WAIT -> "wait"; case EXIT_CODE -> "exit_code";
            });
            failure.put("type", error.type()); failure.put("message", error.message());
        } else { identity.putNull("observation_error"); }
        return write(identity);
    }

    private static OptionalLong nullableInteger(JsonNode value, long minimum, long maximum) {
        return value.isNull() ? OptionalLong.empty() : OptionalLong.of(StrictJson.integer(value, minimum, maximum));
    }

    private static byte[] write(JsonNode node) {
        try {
            byte[] raw = WRITER.writeValueAsBytes(node);
            StrictJson.require(raw.length <= StrictJson.INPUT_MAX_BYTES, "observation exceeds byte budget");
            return raw;
        } catch (IOException error) {
            throw new ContractViolationException("observation JSON encoding failed", error);
        }
    }
}
