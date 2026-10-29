package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared authored release operands; neither this model nor its codecs submit actions. */
public final class ReleasePreviewValues12003 {
    public static final String DEFINITION_KEY = "release_from_prison_interaction";
    public static final long UINT32_MAX = 0xffff_ffffL;
    public static final int RAW_SCALE = 100_000;

    private ReleasePreviewValues12003() { }

    public enum ReleaseOption {
        DEMAND_CONVERSION("demand_conversion"), RENOUNCE_CLAIMS("renounce_claims"),
        BANISH("banish"), GAIN_HOOK("gain_hook"), TAKE_VOWS("take_vows"),
        CHANGE_PRISON("change_prison"), MAKE_PUPPET("make_puppet"),
        BECOME_EXECUTIONER("become_executioner"), RECRUIT("recruit"),
        DISFIGURE("disfigure"), BLIND("blind"), CASTRATE("castrate"), DEMAND_ADMIN("demand_admin");

        private final String key;
        ReleaseOption(String key) { this.key = key; }
        public String key() { return key; }
        public static ReleaseOption fromKey(String key) {
            return Arrays.stream(values()).filter(value -> value.key.equals(key)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown release option"));
        }
    }

    public enum Resource {
        GOLD("gold"), PRESTIGE("prestige"), PIETY("piety"), RENOWN("renown"),
        INFLUENCE("influence"), HERD("herd"), TREASURY("treasury"),
        TREASURY_OR_GOLD("treasury_or_gold"), MERIT("merit"), BARTER_GOODS("barter_goods");

        private final String key;
        Resource(String key) { this.key = key; }
        public String key() { return key; }
        public static Resource fromKey(String key) {
            return Arrays.stream(values()).filter(value -> value.key.equals(key)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown release resource"));
        }
    }

    public record FrameBinding(BigInteger nativeRevision, int dateRaw,
                               long playerCharacterId, long prisonerCharacterId) {
        public FrameBinding {
            unsigned64(nativeRevision, "native revision");
            characterId(playerCharacterId);
            characterId(prisonerCharacterId);
            StrictJson.require(playerCharacterId != prisonerCharacterId, "release roles must differ");
        }
        public String snapshotId() { return "native:" + nativeRevision; }
        public Roles roles() { return new Roles(playerCharacterId, prisonerCharacterId); }
    }

    public record Definition(long deterministicKeyHash, int runtimeOrdinal) {
        public Definition {
            StrictJson.require(deterministicKeyHash >= 0 && deterministicKeyHash <= UINT32_MAX,
                    "definition hash must be uint32");
            StrictJson.require(runtimeOrdinal >= 0, "definition ordinal must be int32 nonnegative");
        }
        public String canonicalKey() { return DEFINITION_KEY; }
    }

    public record Roles(long actorCharacterId, long recipientCharacterId) {
        public Roles {
            characterId(actorCharacterId);
            characterId(recipientCharacterId);
            StrictJson.require(actorCharacterId != recipientCharacterId, "release roles must differ");
        }
    }

    public record CostEntry(Resource resource, long raw) {
        public CostEntry { Objects.requireNonNull(resource, "resource"); }
    }

    public record Costs(List<CostEntry> entries) {
        public Costs {
            entries = List.copyOf(entries);
            Resource[] ordered = Resource.values();
            StrictJson.require(entries.size() == ordered.length, "all ten on-send costs required");
            for (int index = 0; index < ordered.length; index++) {
                StrictJson.require(entries.get(index).resource() == ordered[index],
                        "release costs must retain authored resource order");
            }
        }
        public int rawScale() { return RAW_SCALE; }
        public String payerRole() { return "actor"; }
        public String applicationTiming() { return "on_send"; }
    }

    public static List<String> optionKeys() {
        return Arrays.stream(ReleaseOption.values()).map(ReleaseOption::key).toList();
    }

    public static List<String> resourceKeys() {
        return Arrays.stream(Resource.values()).map(Resource::key).toList();
    }

    public static Definition readDefinition(JsonNode node) {
        ObjectNode value = StrictJson.object(node,
                Set.of("canonical_key", "deterministic_key_hash", "runtime_ordinal"));
        StrictJson.require(DEFINITION_KEY.equals(StrictJson.text(value.get("canonical_key"))),
                "release definition identity differs");
        return new Definition(StrictJson.integer(value.get("deterministic_key_hash"), 0, UINT32_MAX),
                (int) StrictJson.integer(value.get("runtime_ordinal"), 0, Integer.MAX_VALUE));
    }

    public static Roles readRoles(JsonNode node) {
        ObjectNode value = StrictJson.object(node, Set.of("actor_character_id", "recipient_character_id"));
        return new Roles(StrictJson.integer(value.get("actor_character_id"), 1, UINT32_MAX),
                StrictJson.integer(value.get("recipient_character_id"), 1, UINT32_MAX));
    }

    public static Costs readCosts(JsonNode node) {
        ObjectNode value = StrictJson.object(node,
                Set.of("raw_scale", "payer_role", "application_timing", "entries"));
        StrictJson.require(StrictJson.integer(value.get("raw_scale"), RAW_SCALE, RAW_SCALE) == RAW_SCALE,
                "release raw scale differs");
        StrictJson.require("actor".equals(StrictJson.text(value.get("payer_role")))
                        && "on_send".equals(StrictJson.text(value.get("application_timing"))),
                "release cost payer or timing differs");
        JsonNode rows = value.get("entries");
        StrictJson.require(rows != null && rows.isArray() && rows.size() == Resource.values().length,
                "all ten release costs required");
        List<CostEntry> entries = new ArrayList<>();
        for (JsonNode row : rows) {
            ObjectNode entry = StrictJson.object(row, Set.of("resource_key", "raw"));
            entries.add(new CostEntry(Resource.fromKey(StrictJson.text(entry.get("resource_key"))),
                    StrictJson.integer(entry.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE)));
        }
        return new Costs(entries);
    }

    public static ObjectNode writeDefinition(Definition value) {
        ObjectNode node = StrictJson.object();
        node.put("canonical_key", value.canonicalKey());
        node.put("deterministic_key_hash", value.deterministicKeyHash());
        node.put("runtime_ordinal", value.runtimeOrdinal());
        return node;
    }

    public static ObjectNode writeRoles(Roles value) {
        ObjectNode node = StrictJson.object();
        node.put("actor_character_id", value.actorCharacterId());
        node.put("recipient_character_id", value.recipientCharacterId());
        return node;
    }

    public static ObjectNode writeCosts(Costs value) {
        ObjectNode node = StrictJson.object();
        node.put("raw_scale", value.rawScale());
        node.put("payer_role", value.payerRole());
        node.put("application_timing", value.applicationTiming());
        ArrayNode entries = node.putArray("entries");
        for (CostEntry entry : value.entries()) {
            ObjectNode row = entries.addObject();
            row.put("resource_key", entry.resource().key());
            row.put("raw", entry.raw());
        }
        return node;
    }

    public static void unsigned64(BigInteger value, String label) {
        StrictJson.require(value != null && value.signum() > 0
                && value.compareTo(StrictJson.UINT64_MAX) <= 0, label + " must be positive uint64");
    }

    private static void characterId(long value) {
        StrictJson.require(value > 0 && value <= UINT32_MAX, "character ID must be positive uint32");
    }
}
