package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Field;

/** Immutable identity of the complete UI JSON value, including numeric kind; no caller-supplied GREEN digest. */
public final class UiIdentity {
    private final String fingerprint;
    private final int memberCount;
    private final Field<BigInteger> instanceId;
    private final Field<BigInteger> optionCount;

    private UiIdentity(String fingerprint, int memberCount, Field<BigInteger> instanceId, Field<BigInteger> optionCount) {
        this.fingerprint = fingerprint; this.memberCount = memberCount;
        this.instanceId = instanceId; this.optionCount = optionCount;
    }

    static UiIdentity fromJson(JsonNode value, boolean event) {
        require(value.isObject(), "UI object required");
        MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA256 unavailable", error); }
        fingerprint(value, digest, 0);
        return new UiIdentity(HexFormat.of().formatHex(digest.digest()), value.size(),
                event ? TimelineOwnerCodec.integerField(value.get("instance_id")) : Field.missing(),
                event ? TimelineOwnerCodec.integerField(value.get("option_count")) : Field.missing());
    }

    public String fingerprint() { return fingerprint; }
    public boolean nonempty() { return memberCount > 0; }
    public boolean validEvent() {
        return instanceId.present() && optionCount.present() && instanceId.required().signum() > 0
                && optionCount.required().signum() > 0;
    }

    @Override public boolean equals(Object other) {
        return other instanceof UiIdentity value && fingerprint.equals(value.fingerprint)
                && instanceId.equals(value.instanceId) && optionCount.equals(value.optionCount);
    }
    @Override public int hashCode() { return Objects.hash(fingerprint, instanceId, optionCount); }
    @Override public String toString() { return "UiIdentity[sha256=" + fingerprint + "]"; }

    /** Typed length-framed identity encoding, not a JSON reserialization or an original-byte identity claim. */
    private static void fingerprint(JsonNode value, MessageDigest digest, int depth) {
        require(value != null && depth <= 128, "bounded complete UI JSON required");
        if (value.isObject()) {
            update(digest, "object"); update(digest, Integer.toString(value.size()));
            TreeSet<String> names = new TreeSet<>(); value.fieldNames().forEachRemaining(names::add);
            for (String name : names) { text(name); update(digest, name); fingerprint(value.get(name), digest, depth + 1); }
        } else if (value.isArray()) {
            update(digest, "array"); update(digest, Integer.toString(value.size()));
            for (JsonNode child : value) { fingerprint(child, digest, depth + 1); }
        } else if (value.isTextual()) {
            update(digest, "string"); text(value.textValue()); update(digest, value.textValue());
        } else if (value.isIntegralNumber()) {
            update(digest, "integer"); update(digest, value.bigIntegerValue().toString());
        } else if (value.isFloatingPointNumber()) {
            require(!(value.isDouble() || value.isFloat()) || Double.isFinite(value.doubleValue()), "finite UI decimal required");
            require(Math.abs((long) value.decimalValue().scale()) <= 100_000, "bounded UI decimal scale required");
            update(digest, "decimal"); update(digest, value.decimalValue().stripTrailingZeros().toString());
        } else if (value.isBoolean()) {
            update(digest, value.booleanValue() ? "true" : "false");
        } else {
            require(value.isNull(), "no missing UI JSON node"); update(digest, "null");
        }
    }

    private static void text(String value) { if (!value.isEmpty()) { StrictJson.text(value); } }
    private static void update(MessageDigest digest, String value) {
        byte[] raw = value.getBytes(StandardCharsets.UTF_8);
        digest.update((byte) (raw.length >>> 24)); digest.update((byte) (raw.length >>> 16));
        digest.update((byte) (raw.length >>> 8)); digest.update((byte) raw.length); digest.update(raw);
    }
}
