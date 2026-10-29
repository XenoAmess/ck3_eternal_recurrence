package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** The native component's exact seventeen fields. Null, zero and signed raw values are distinct. */
public record PlayerReligionContext(
        String schema, String gameVersion, String executableSha256, boolean available,
        String unavailableReason, BigInteger captureEpoch, int dateRaw, BigInteger playedCharacterId,
        BigInteger riteId, BigInteger faithId, BigInteger religionId, BigInteger faithMainRiteId,
        String faithKey, String religionKey, BigInteger faithFervorRaw,
        BigInteger spiritualFulfillmentRaw, int rawScale) {
    public enum Build {
        CROZIER2("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D", "ck3_12002_religion_context_v1"),
        CROZIER3("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6", "ck3_12003_religion_context_v1"),
        CROZIER4("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518", "ck3_12004_religion_context_v1");
        private final String version, sha256, schema;
        Build(String version, String sha256, String schema) {
            this.version = version; this.sha256 = sha256; this.schema = schema;
        }
        public String version() { return version; }
        public String sha256() { return sha256; }
        public String schema() { return schema; }
        public static Build exact(String version, String sha256) {
            Objects.requireNonNull(version); Objects.requireNonNull(sha256);
            for (Build build : values())
                if (build.version.equals(version) && build.sha256.equalsIgnoreCase(sha256)) return build;
            throw new IllegalArgumentException("religion context exact native version/SHA pair differs");
        }
    }
    private static final String FIELDS = "schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id rite_id faith_id religion_id faith_main_rite_id faith_key religion_key faith_fervor_raw spiritual_fulfillment_raw raw_scale";

    public PlayerReligionContext {
        Build build = Build.exact(gameVersion, executableSha256);
        need(build.schema().equals(schema), "religion context schema does not belong to exact build");
        range(captureEpoch, BigInteger.ONE, U64);
        range(playedCharacterId,I32_MIN,I32_MAX);
        if(available)NativeCharacterId.of(playedCharacterId);
        for (BigInteger reference : new BigInteger[] {riteId, faithId, religionId, faithMainRiteId})
            if (reference != null) range(reference, BigInteger.ZERO, U32);
        for (BigInteger raw : new BigInteger[] {faithFervorRaw, spiritualFulfillmentRaw})
            if (raw != null) range(raw, I64_MIN, I64_MAX);
        need(rawScale == 100000, "religion context native raw scale differs");
        need(available ? unavailableReason == null && spiritualFulfillmentRaw != null
                : unavailableReason != null && !unavailableReason.isEmpty(),
                "religion context availability lost its native reason/value");
    }
    public Build exactBuild() { return Build.exact(gameVersion, executableSha256); }
    public static PlayerReligionContext decode(byte[] nativeJson) {
        try { return decode(NativeWire.parse(Objects.requireNonNull(nativeJson))); }
        catch (IOException failure) { throw new IllegalArgumentException("malformed native religion context JSON", failure); }
    }
    public static PlayerReligionContext decode(JsonNode nativeValue) {
        exact(nativeValue, FIELDS);
        return new PlayerReligionContext(
                text(nativeValue, "schema"), text(nativeValue, "game_version"),
                text(nativeValue, "executable_sha256"), bool(nativeValue, "available"),
                nullableText(nativeValue, "unavailable_reason"),
                number(nativeValue, "capture_epoch", BigInteger.ONE, U64),
                i32(nativeValue, "date_raw"), number(nativeValue, "played_character_id", I32_MIN, I32_MAX),
                nullableNumber(nativeValue, "rite_id", BigInteger.ZERO, U32),
                nullableNumber(nativeValue, "faith_id", BigInteger.ZERO, U32),
                nullableNumber(nativeValue, "religion_id", BigInteger.ZERO, U32),
                nullableNumber(nativeValue, "faith_main_rite_id", BigInteger.ZERO, U32),
                nullableText(nativeValue, "faith_key"), nullableText(nativeValue, "religion_key"),
                nullableNumber(nativeValue, "faith_fervor_raw", I64_MIN, I64_MAX),
                nullableNumber(nativeValue, "spiritual_fulfillment_raw", I64_MIN, I64_MAX),
                number(nativeValue, "raw_scale", BigInteger.valueOf(100000), BigInteger.valueOf(100000)).intValueExact());
    }
    /** Native JSON representation, for Java/native use. An external JavaScript encoder must preserve raw64 precision. */
    public ObjectNode encode() {
        ObjectNode value = JsonNodeFactory.instance.objectNode();
        value.put("schema", schema).put("game_version", gameVersion).put("executable_sha256", executableSha256)
                .put("available", available).put("unavailable_reason", unavailableReason)
                .put("capture_epoch", captureEpoch).put("date_raw", dateRaw).put("played_character_id", playedCharacterId)
                .put("rite_id", riteId).put("faith_id", faithId).put("religion_id", religionId)
                .put("faith_main_rite_id", faithMainRiteId).put("faith_key", faithKey).put("religion_key", religionKey)
                .put("faith_fervor_raw", faithFervorRaw).put("spiritual_fulfillment_raw", spiritualFulfillmentRaw)
                .put("raw_scale", rawScale);
        return value;
    }
    /** Match Python's source-frame rule: unavailable observations retain their diagnostic native fields. */
    public void requireAvailableFrame(BigInteger queriedDateRaw, BigInteger queriedPlayer) {
        Objects.requireNonNull(queriedDateRaw); Objects.requireNonNull(queriedPlayer);
        if (available) need(BigInteger.valueOf(dateRaw).equals(queriedDateRaw)
                && playedCharacterId.equals(queriedPlayer), "religion context differs from its queried player frame");
    }
}
