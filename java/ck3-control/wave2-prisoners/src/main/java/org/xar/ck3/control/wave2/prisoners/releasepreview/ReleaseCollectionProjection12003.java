package org.xar.ck3.control.wave2.prisoners.releasepreview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/**
 * Declared projection of the existing collection consumer's release input.
 * Other SDK fields are deliberately retained only in the original-byte SHA, not requalified here.
 * This does not validate ransom, kinship, war retention, submission, receipts or a saved outcome.
 */
public final class ReleaseCollectionProjection12003 {
    public static final int MAX_BYTES = 131_072;
    private static final String STEP = "query-player-prisoner-collection-private-v1";
    private static final String ORDINAL_PREFIX = STEP + "-ransom-ordinal-";

    private ReleaseCollectionProjection12003() { }

    public enum SupportedBuild {
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");

        private final String version;
        private final String executableSha256;
        SupportedBuild(String version, String executableSha256) {
            this.version = version;
            this.executableSha256 = executableSha256;
        }
        public String version() { return version; }
        public String executableSha256() { return executableSha256; }
        public static SupportedBuild exact(String version, String sha256) {
            for (SupportedBuild build : values()) {
                if (build.version.equals(version) && build.executableSha256.equalsIgnoreCase(sha256)) {
                    return build;
                }
            }
            throw new IllegalArgumentException("release preview requires an exact supported version/SHA pair");
        }
    }

    /** Missing lineage in schema 2 differs from measured null house/dynasty in schemas 3–7. */
    public sealed interface Lineage permits MissingLineage, MeasuredLineage { }
    public record MissingLineage() implements Lineage { }
    public record MeasuredLineage(BigInteger houseId, BigInteger dynastyId,
                                  boolean sameHouse, boolean sameDynasty) implements Lineage {
        public MeasuredLineage { validateLineage(houseId, dynastyId); }
    }

    /** Before schema 5 the child relation is absent; null is not a permitted measured value. */
    public sealed interface ChildRelation permits MissingChildRelation, MeasuredChildRelation { }
    public record MissingChildRelation() implements ChildRelation { }
    public record MeasuredChildRelation(boolean childOfPlayedCharacter) implements ChildRelation { }

    /** Measured null means no primary title, distinct from absence before schema 6. */
    public sealed interface TitleTier permits MissingTitleTier, MeasuredTitleTier { }
    public record MissingTitleTier() implements TitleTier { }
    public record MeasuredTitleTier(Integer raw) implements TitleTier {
        public MeasuredTitleTier {
            StrictJson.require(raw == null || raw >= 1 && raw <= 6, "primary title tier outside 1..6");
        }
    }

    public record Row(int sourceOrdinal, long prisonerCharacterId, Lineage lineage,
                      ChildRelation childRelation, TitleTier primaryTitleTier,
                      ReleasePreview12003 preview, NativeKinship12003 nativeKinship) {
        public Row {
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal <= 63, "collection ordinal outside 0..63");
            StrictJson.require(prisonerCharacterId > 0 && prisonerCharacterId <= ReleasePreviewValues12003.UINT32_MAX,
                    "prisoner full ID outside uint32");
            Objects.requireNonNull(lineage, "lineage");
            Objects.requireNonNull(childRelation, "childRelation");
            Objects.requireNonNull(primaryTitleTier, "primaryTitleTier");
            Objects.requireNonNull(preview, "preview");
            Objects.requireNonNull(nativeKinship, "nativeKinship");
        }
    }

    public record Observation(SupportedBuild build, int schemaVersion, BigInteger querySequence,
                              BigInteger proofEpoch, int selectedOrdinal, List<Row> rows,
                              String originalSha256) {
        public Observation {
            Objects.requireNonNull(build, "build");
            StrictJson.require(schemaVersion >= 2 && schemaVersion <= 7, "preview collection schema outside 2..7");
            ReleasePreviewValues12003.unsigned64(querySequence, "query sequence");
            ReleasePreviewValues12003.unsigned64(proofEpoch, "collection observation");
            rows = List.copyOf(rows);
            StrictJson.require(selectedOrdinal >= 0 && selectedOrdinal <= 63
                    && (rows.isEmpty() ? selectedOrdinal == 0 : selectedOrdinal < rows.size()),
                    "selected release row absent");
            StrictJson.require(originalSha256 != null && originalSha256.matches("[0-9a-f]{64}"),
                    "original collection SHA required");
        }
    }

    /** Read-only source projection. Expected binding comes from the actual paused semantic frame. */
    public static Observation decode(byte[] original, SupportedBuild build, FrameBinding selectedBinding) {
        Objects.requireNonNull(build, "build");
        Objects.requireNonNull(selectedBinding, "selectedBinding");
        JsonNode envelope = StrictJson.parse(original, MAX_BYTES);
        object(envelope);
        equalText(envelope.get("status"), "available");
        StrictJson.trueValue(envelope.get("accepted"));
        StrictJson.trueValue(envelope.get("private_build"));
        StrictJson.trueValue(envelope.get("read_only"));
        StrictJson.require(!bool(envelope.get("advertised")), "collection must remain unadvertised");
        equalText(envelope.get("backend_id"), "native-headless");
        sameRevision(envelope.get("snapshot_revision"), selectedBinding.nativeRevision());
        BigInteger query = uint64(envelope.get("query_sequence"));
        BigInteger epoch = uint64(envelope.get("observation_revision"));
        int selectedOrdinal = selectedOrdinal(StrictJson.text(envelope.get("step")));
        JsonNode value = envelope.get("player_prisoner_collection");
        object(value);
        equalText(value.get("schema"), "player-prisoner-collection-private-v1");
        int schema = (int) StrictJson.integer(value.get("schema_version"), 2, 7);
        equalText(value.get("status"), "available");
        StrictJson.require(value.has("unavailable_reason") && value.get("unavailable_reason").isNull(),
                "available collection must retain explicit null reason");
        sameRevision(value.get("snapshot_revision"), selectedBinding.nativeRevision());
        StrictJson.require(StrictJson.integer(value.get("played_character_id"), 1,
                        ReleasePreviewValues12003.UINT32_MAX) == selectedBinding.playerCharacterId()
                && StrictJson.integer(value.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)
                        == selectedBinding.dateRaw(), "collection differs from actual player/date");
        int count = (int) StrictJson.integer(value.get("total_count"), 0, 64);
        StrictJson.integer(value.get("returned_count"), count, count);
        StrictJson.trueValue(value.get("collection_complete"));
        JsonNode wireRows = value.get("prisoners");
        StrictJson.require(wireRows != null && wireRows.isArray() && wireRows.size() == count,
                "complete collection row count differs");
        if (selectedOrdinal > 0) {
            StrictJson.require(schema >= 4 && selectedOrdinal < count, "requested collection ordinal absent");
        }
        BigInteger playedHouse = schema >= 3 ? nullableId(value.get("played_house_id")) : null;
        BigInteger playedDynasty = schema >= 3 ? nullableId(value.get("played_dynasty_id")) : null;
        validateLineage(playedHouse, playedDynasty);
        if (schema >= 6) { nonnegative(value.get("played_dread_raw")); }
        List<Row> rows = new ArrayList<>();
        Set<Long> seen = new HashSet<>();
        for (int ordinal = 0; ordinal < count; ordinal++) {
            JsonNode row = wireRows.get(ordinal);
            object(row);
            StrictJson.integer(row.get("source_ordinal"), ordinal, ordinal);
            long prisoner = StrictJson.integer(row.get("prisoner_character_id"), 1,
                    ReleasePreviewValues12003.UINT32_MAX);
            StrictJson.require(prisoner != selectedBinding.playerCharacterId() && seen.add(prisoner),
                    "collection full prisoner ID is duplicate or player");
            StrictJson.integer(row.get("collection_owner_character_id"),
                    selectedBinding.playerCharacterId(), selectedBinding.playerCharacterId());
            StrictJson.integer(row.get("jailer_character_id"),
                    selectedBinding.playerCharacterId(), selectedBinding.playerCharacterId());
            StrictJson.trueValue(row.get("custody_relation_verified"));
            Lineage lineage = new MissingLineage();
            if (schema >= 3) {
                BigInteger house = nullableId(row.get("house_id"));
                BigInteger dynasty = nullableId(row.get("dynasty_id"));
                boolean sameHouse = bool(row.get("same_house"));
                boolean sameDynasty = bool(row.get("same_dynasty"));
                StrictJson.require(sameHouse == (house != null && house.equals(playedHouse))
                        && sameDynasty == (dynasty != null && dynasty.equals(playedDynasty)),
                        "prisoner family relation differs from source IDs");
                lineage = new MeasuredLineage(house, dynasty, sameHouse, sameDynasty);
            }
            ChildRelation child = schema >= 5
                    ? new MeasuredChildRelation(bool(row.get("is_child_of_played_character")))
                    : new MissingChildRelation();
            TitleTier tier = schema >= 6 ? new MeasuredTitleTier(nullableTier(row.get("primary_title_tier_raw")))
                    : new MissingTitleTier();
            FrameBinding binding = new FrameBinding(selectedBinding.nativeRevision(), selectedBinding.dateRaw(),
                    selectedBinding.playerCharacterId(), prisoner);
            ReleasePreview12003 preview = ReleasePreviewCodec12003.fromNode(row.get("unconditional_release_preview"), binding);
            if (preview instanceof ReleasePreview12003.Available available) {
                StrictJson.require(available.proofEpoch().equals(epoch),
                        "release preview differs from its collection observation");
            }
            NativeKinship12003 kinship = schema == 7
                    ? NativeKinshipCodec12003.fromNode(row.get("native_kinship"), binding, epoch,
                            ordinal, selectedOrdinal) : new NativeKinship12003.Missing();
            rows.add(new Row(ordinal, prisoner, lineage, child, tier, preview, kinship));
        }
        StrictJson.require(count == 0 || rows.get(selectedOrdinal).prisonerCharacterId()
                == selectedBinding.prisonerCharacterId(), "selected prisoner differs from queried full ID");
        return new Observation(build, schema, query, epoch, selectedOrdinal, rows, sha256(original));
    }

    private static void object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "collection projection object required");
    }
    private static void equalText(JsonNode node, String expected) {
        StrictJson.require(expected.equals(StrictJson.text(node)), "collection source text differs");
    }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual collection boolean required");
        return node.booleanValue();
    }
    private static BigInteger uint64(JsonNode node) {
        return StrictJson.integer(node, BigInteger.ONE, StrictJson.UINT64_MAX);
    }
    private static void sameRevision(JsonNode node, BigInteger expected) {
        StrictJson.require(uint64(node).equals(expected), "collection native revision differs");
    }
    private static BigInteger nonnegative(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber() && node.bigIntegerValue().signum() >= 0,
                "nonnegative collection integer required");
        return node.bigIntegerValue();
    }
    private static BigInteger nullableId(JsonNode node) {
        StrictJson.require(node != null, "measured lineage field is missing");
        return node.isNull() ? null : nonnegative(node);
    }
    private static Integer nullableTier(JsonNode node) {
        StrictJson.require(node != null, "measured title tier is missing");
        return node.isNull() ? null : (int) StrictJson.integer(node, 1, 6);
    }
    private static void validateLineage(BigInteger house, BigInteger dynasty) {
        StrictJson.require((house == null || house.signum() >= 0)
                && (dynasty == null || dynasty.signum() >= 0)
                && (house != null || dynasty == null), "lineage IDs are malformed");
    }
    private static int selectedOrdinal(String step) {
        if (STEP.equals(step)) { return 0; }
        StrictJson.require(step.startsWith(ORDINAL_PREFIX), "queried prisoner ordinal required");
        String suffix = step.substring(ORDINAL_PREFIX.length());
        StrictJson.require(suffix.matches("[1-9][0-9]?"), "canonical ASCII ordinal required");
        int ordinal = Integer.parseInt(suffix);
        StrictJson.require(ordinal <= 63, "queried prisoner ordinal outside 1..63");
        return ordinal;
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
