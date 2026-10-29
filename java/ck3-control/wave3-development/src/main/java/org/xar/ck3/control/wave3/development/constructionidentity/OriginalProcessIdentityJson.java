package org.xar.ck3.control.wave3.development.constructionidentity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.WmiFields;

/** Extensible old producer projection; arbitrary SDK fields remain in the original UTF-8 bytes. */
public final class OriginalProcessIdentityJson {
    public static final int MAX_ORIGINAL_BYTES = 262_144;
    private OriginalProcessIdentityJson() { }
    public static Optional<OriginalProcessIdentity> parse(byte[] raw) {
        JsonNode value = StrictJson.parse(raw, MAX_ORIGINAL_BYTES);
        if (value.isNull()) { return Optional.empty(); }
        StrictJson.require(value instanceof ObjectNode, "original identity must be object or null");
        BigInteger pid = integer(value.get("pid"));
        String executable = text(value.get("executable"));
        String creation = text(value.get("creation_date"));
        return Optional.of(new OriginalProcessIdentity(new WmiFields(pid, executable, creation), raw));
    }
    public static byte[] cached(long pid, String originalCreationDate) {
        StrictJson.require(pid >= 1 && pid <= 0xffff_ffffL, "positive DWORD cached PID required");
        StrictJson.text(originalCreationDate);
        ObjectNode out = StrictJson.object();
        out.put("pid", pid);
        out.put("creation_date", originalCreationDate);
        return StrictJson.canonical(out);
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "original identity PID must be exact integer");
        return value.bigIntegerValue();
    }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "original identity text must be string or null");
        return value.textValue().isEmpty() ? "" : StrictJson.text(value);
    }
}
