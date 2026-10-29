package org.xar.ck3.control.recovery;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact, finite metadata only. No filesystem access, Driver/SAVE bytes or truncation. */
public final class RecoveryEvidence {
    public static final int MAX_BYTES = 65_536;
    private final ExactRef reference;
    private final byte[] bytes;

    public RecoveryEvidence(ExactRef reference, byte[] bytes) {
        this.reference = Objects.requireNonNull(reference);
        Objects.requireNonNull(bytes);
        StrictJson.require(bytes.length > 0 && bytes.length <= MAX_BYTES, "small complete metadata required");
        String name = reference.path().replace('\\', '/').toLowerCase(Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3")
                && !name.endsWith(".sav"), "Driver/SAVE bodies are outside this port");
        StrictJson.require(reference.bytes() == bytes.length && reference.sha256().equals(sha256(bytes)),
                "exact original metadata length and SHA required");
        StrictJson.require(StrictJson.parse(bytes) instanceof ObjectNode, "complete original JSON object required");
        this.bytes = bytes.clone();
    }

    public ExactRef reference() { return reference; }
    public byte[] bytes() { return bytes.clone(); }
    ObjectNode object() { return (ObjectNode) StrictJson.parse(bytes); }

    public static String sha256(byte[] bytes) {
        Objects.requireNonNull(bytes);
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 unavailable", error);
        }
    }

    @Override public boolean equals(Object value) {
        return value instanceof RecoveryEvidence other && reference.equals(other.reference)
                && Arrays.equals(bytes, other.bytes);
    }
    @Override public int hashCode() { return 31 * reference.hashCode() + Arrays.hashCode(bytes); }
}
