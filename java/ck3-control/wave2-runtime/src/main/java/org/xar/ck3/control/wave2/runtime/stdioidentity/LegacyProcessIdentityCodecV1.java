package org.xar.ck3.control.wave2.runtime.stdioidentity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Explicit compatibility codec for RetainedProcessGeneration.identity(role).
 * Its Python-only creation_filetime remains an exact numeric uint64. The new
 * measurement-plan codec has a distinct decimal-string field and version.
 */
public final class LegacyProcessIdentityCodecV1 {
    private static final Set<String> FIELDS = Set.of("role", "pid", "creation_filetime", "executable");
    private static final ObjectMapper WRITER = new ObjectMapper();

    public record RoleIdentity(String role, ProcessIdentityClaimV1 identity) {
        public RoleIdentity {
            StrictJson.require(role != null && !role.isEmpty(), "nonempty process role required");
            StrictJson.require(StandardCharsets.UTF_8.newEncoder().canEncode(role), "well-formed process role Unicode required");
            StrictJson.require(identity != null, "validated process identity required");
        }
    }

    private LegacyProcessIdentityCodecV1() { }

    public static RoleIdentity decode(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw), FIELDS);
        String role = text(value.get("role"));
        try {
            return new RoleIdentity(role, new ProcessIdentityClaimV1(
                    StrictJson.integer(value.get("pid"), 1, 0xffff_ffffL),
                    StrictJson.integer(value.get("creation_filetime"), BigInteger.ONE, StrictJson.UINT64_MAX).toString(),
                    Path.of(text(value.get("executable")))));
        } catch (InvalidPathException error) {
            throw new ContractViolationException("absolute process image path required", error);
        }
    }

    public static byte[] encode(RoleIdentity value) {
        StrictJson.require(value != null, "validated process role identity required");
        ObjectNode output = StrictJson.object();
        output.put("creation_filetime", new BigInteger(value.identity().creationFiletimeDecimal()));
        output.put("executable", value.identity().executable().toString());
        output.put("pid", value.identity().pid()); output.put("role", value.role());
        try {
            byte[] raw = WRITER.writeValueAsBytes(output);
            StrictJson.require(raw.length <= StrictJson.INPUT_MAX_BYTES, "legacy process identity exceeds byte budget");
            return raw;
        } catch (IOException error) {
            throw new ContractViolationException("legacy process identity encoding failed", error);
        }
    }

    private static String text(JsonNode value) {
        StrictJson.require(value != null && value.isTextual() && !value.textValue().isEmpty(), "nonempty string required");
        return value.textValue();
    }
}
