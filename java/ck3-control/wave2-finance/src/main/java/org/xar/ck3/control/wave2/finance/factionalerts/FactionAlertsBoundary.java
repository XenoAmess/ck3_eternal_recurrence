package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionthreat.ExistingFactionAlertAdapter;
import org.xar.ck3.control.wave2.finance.giftoutcome.ExistingGiftOutcomeAdapter;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;

/** Validates the shared native producer before projecting to the two active gift consumers. */
public final class FactionAlertsBoundary {
    /** Exact result token emitted by SerializePlayerFactionAlertsWhole12004, before SDK projections. */
    public static final Set<String> CURRENT_NATIVE_RESULT_FIELDS = Set.of("step", "accepted", "status", "query_sequence",
            "snapshot_revision", "player_faction_alerts", "player_faction_alerts_ready", "backend_id");
    private FactionAlertsBoundary() { }
    public record CurrentNativeResult(BigInteger querySequence, Projection projection) {
        public CurrentNativeResult {
            StrictJson.require(querySequence != null && querySequence.signum() > 0 && querySequence.bitLength() <= 64,
                    "positive native faction query sequence required");
            Objects.requireNonNull(projection);
        }
    }
    public static final class Projection {
        private final FactionAlertsCodec.Normalized normalized;
        private final String originalSha256; private final byte[] json;
        private Projection(FactionAlertsCodec.Normalized normalized, String originalSha256, byte[] json) {
            this.normalized = normalized; this.originalSha256 = originalSha256; this.json = json.clone();
        }
        public Frame frame() { return normalized.frame(); }
        public byte[] normalizedAlertJson() { return normalized.json(); }
        public String originalSha256() { return originalSha256; }
        public byte[] consumerProjectionJson() { return json.clone(); }
    }
    /** Current native producer admission shared by public reads, ordinary finance and archived finance.
     * A validated result token remains distinct from the owning transport receipt and actual game outcome.
     */
    public static CurrentNativeResult normalizeCurrentNativeResult(byte[] originalResult, ExpectedFrame expected,
                                                                  byte[] sameFrameActiveWars) {
        Objects.requireNonNull(expected);
        StrictJson.require(originalResult != null, "original current faction result required");
        byte[] original = originalResult.clone();
        StrictJson.require(expected.connectedBuild().orElse(null) == Build.CK3_12004,
                "current native faction result requires exact 1.20.0.4 source");
        JsonNode parsed = StrictJson.parse(original, FactionAlertsCodec.MAX_BYTES);
        StrictJson.require(parsed instanceof ObjectNode, "current native faction result object required");
        ObjectNode root = (ObjectNode) parsed;
        Set<String> fields = new HashSet<>(); root.fieldNames().forEachRemaining(fields::add);
        StrictJson.require(fields.equals(CURRENT_NATIVE_RESULT_FIELDS), "wrong, missing or extra native faction result fields");
        StrictJson.require(root.get("step").isTextual() && root.get("step").textValue().equals(STEP), "native faction step drift");
        StrictJson.require(root.get("accepted").isBoolean() && root.get("accepted").booleanValue(), "native faction query not accepted");
        StrictJson.require(root.get("backend_id").isTextual() && root.get("backend_id").textValue().equals("native-headless"),
                "native faction backend drift");
        BigInteger sequence = nativeUInt64(root.get("query_sequence"), true);
        StrictJson.require(nativeUInt64(root.get("snapshot_revision"), true).equals(expected.nativeRevision()),
                "native faction result revision drift");
        Projection projection = normalizeExistingDriverResult(original, expected, sameFrameActiveWars);
        JsonNode normalized = StrictJson.parse(projection.normalizedAlertJson(), FactionAlertsCodec.MAX_BYTES);
        StrictJson.require(root.get("status").isTextual() && root.get("status").equals(normalized.get("status")),
                "native faction status mirror drift");
        StrictJson.require(root.get("player_faction_alerts_ready").isBoolean()
                && root.get("player_faction_alerts_ready").booleanValue() == projection.frame().readiness().alertReady(),
                "native faction readiness mirror drift");
        return new CurrentNativeResult(sequence, projection);
    }
    public static Projection normalizeExistingDriverResult(byte[] originalResult, ExpectedFrame expected, byte[] sameFrameActiveWars) {
        StrictJson.require(originalResult != null, "original existing-driver packet required");
        byte[] original = originalResult.clone();
        JsonNode root = StrictJson.parse(original, FactionAlertsCodec.MAX_BYTES);
        StrictJson.require(root.isObject(), "existing driver result object required");
        JsonNode value = root.get("player_faction_alerts"); StrictJson.require(value != null, "existing player_faction_alerts required");
        FactionAlertsCodec.Normalized normalized = FactionAlertsCodec.normalize(StrictJson.canonical(value, FactionAlertsCodec.MAX_BYTES), expected);
        FactionAlertsCodec.validateWarHandoffs(normalized.frame(), sameFrameActiveWars);
        String originalSha = sha256(original); ObjectNode projection = StrictJson.object();
        projection.set("player_faction_alerts", StrictJson.parse(normalized.json(), FactionAlertsCodec.MAX_BYTES));
        projection.put("projection_not_original", true); projection.put("original_source_sha256", originalSha);
        projection.put("original_schema", "player-faction-alerts-v1");
        return new Projection(normalized, originalSha, StrictJson.canonical(projection, FactionAlertsCodec.MAX_BYTES));
    }
    public static ExistingFactionAlertAdapter.ObserverPacket forThreatObserver(Projection projection) {
        return new ExistingFactionAlertAdapter.ObserverPacket(projection.consumerProjectionJson());
    }
    public static ExistingGiftOutcomeAdapter.Packet forResolvedGiftOutcome(Projection projection) {
        return new ExistingGiftOutcomeAdapter.Packet(projection.consumerProjectionJson());
    }
    private static BigInteger nativeUInt64(JsonNode value, boolean positive) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact original faction integer required");
        BigInteger number = value.bigIntegerValue();
        StrictJson.require(number.signum() >= (positive ? 1 : 0) && number.bitLength() <= 64, "native faction uint64 range");
        return number;
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
