package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.wave2.military.combatwire.PersonSixStageCaptureCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleTerminalJson.*;

/** Original separate six-stage query boundary. Capture leaf validation has exactly one shared producer. */
public final class BattlePersonSixStageCaptureCodec {
    public static final String QUERY_FIELD = "person_six_stage_captures";
    public static final String QUERY_SCHEMA = "xar.ck3.person-native-six-stage-query-12004-v1";
    public static final String CAPTURE_FIELD = "following_six_attribute_captured_stages";
    private BattlePersonSixStageCaptureCodec() { }

    /** Nullable native owner facts; ID zero and the high bit remain actual unsigned32 values. DATA only. */
    public record CaptureOwner(Long characterId, String characterIdentity, String contextIdentity,
            BigInteger captureSequence, Integer captureDateRaw, Long captureThreadId, Long queryThreadId,
            String sourceReturnRva, boolean captureObserved, boolean captureComplete, boolean ready, boolean rawCountsReady) {
        public CaptureOwner {
            unsigned(characterId, "capture CharacterID"); unsigned(captureThreadId, "capture thread"); unsigned(queryThreadId, "query thread");
            require(captureSequence != null && captureSequence.signum() >= 0 && captureSequence.compareTo(U64) <= 0, "capture sequence uint64");
            for (String pointer : new String[] {characterIdentity, contextIdentity, sourceReturnRva})
                require(pointer == null || !pointer.isEmpty(), "optional original pointer string must be nonempty");
        }
    }
    /** Immutable normalized DATA. This serialization is not the original Native packet/evidence closure. */
    public static final class NormalizedQuery {
        private final BigInteger nativeRevision;
        private final int observedDateRaw;
        private final List<CaptureOwner> owners;
        private final byte[] normalizedWire;
        private NormalizedQuery(BigInteger nativeRevision, int observedDateRaw, List<CaptureOwner> owners, ObjectNode normalized) {
            this.nativeRevision = nativeRevision; this.observedDateRaw = observedDateRaw;
            this.owners = List.copyOf(owners); this.normalizedWire = ArmyJson.bytes(normalized);
        }
        public BigInteger nativeRevision() { return nativeRevision; }
        public int observedDateRaw() { return observedDateRaw; }
        public List<CaptureOwner> owners() { return owners; }
        public ObjectNode toJson() { return ArmyJson.parse(normalizedWire); }
        public byte[] normalizedBytes() { return normalizedWire.clone(); }
    }
    public static JsonNode normalize(JsonNode sidecar, String field, BigInteger expectedNativeRevision,
            int expectedDateRaw, List<Long> expectedCharacters) {
        return decode(sidecar, field, expectedNativeRevision, expectedDateRaw, expectedCharacters).toJson();
    }
    public static NormalizedQuery decode(JsonNode sidecar, String field, BigInteger expectedNativeRevision,
            int expectedDateRaw, List<Long> expectedCharacters) {
        require(expectedNativeRevision != null && expectedNativeRevision.signum() >= 0 && expectedNativeRevision.compareTo(U64) <= 0,
                "expected snapshot revision unsigned64");
        require(expectedCharacters != null, "requested full CharacterID order required");
        for (Long character : expectedCharacters) { require(character != null, "requested CharacterID cannot be null"); unsigned(character, "requested CharacterID"); }
        ObjectNode row = object(sidecar, field, "schema", "snapshot_revision", "observed_date_raw", "character_captures");
        require(QUERY_SCHEMA.equals(text(row.get("schema"), field + ".schema")), field + ": query schema");
        BigInteger revision = integer(row.get("snapshot_revision"), field + ".snapshot_revision", BigInteger.ZERO, U64);
        int date = Math.toIntExact(integer(row.get("observed_date_raw"), field + ".observed_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE));
        require(revision.equals(expectedNativeRevision) && date == expectedDateRaw, field + ": requested snapshot frame differs");
        ArrayNode rawCaptures = array(row.get("character_captures"), field + ".character_captures");
        require(rawCaptures.size() == expectedCharacters.size(), field + ": requested CharacterID order differs");
        ObjectNode normalized = row.deepCopy(); ArrayNode captures = normalized.putArray("character_captures");
        List<CaptureOwner> owners = new ArrayList<>();
        for (int index = 0; index < rawCaptures.size(); index++) {
            JsonNode leaf = PersonSixStageCaptureCodec.normalize(rawCaptures.get(index));
            require(leaf != null && leaf.isObject(), field + ": capture cannot be null");
            CaptureOwner owner = owner(leaf);
            require(java.util.Objects.equals(owner.characterId(), expectedCharacters.get(index)), field + ": full CharacterID order differs");
            captures.add(leaf); owners.add(owner);
        }
        return new NormalizedQuery(revision, date, owners, normalized);
    }
    /** Standalone leaf owner retains explicit null. Query binding imposes its own requested nonnull ID order. */
    public static CaptureOwner captureOwner(JsonNode capture) {
        JsonNode normalized = PersonSixStageCaptureCodec.normalize(capture);
        require(normalized != null && normalized.isObject(), "actual capture owner required");
        return owner(normalized);
    }
    private static CaptureOwner owner(JsonNode capture) {
        return new CaptureOwner(optionalInteger(capture.get("character_id"), "capture.character_id", 0, 0xffff_ffffL),
                optionalText(capture.get("character_identity")), optionalText(capture.get("context_identity")),
                integer(capture.get("capture_sequence"), "capture_sequence", BigInteger.ZERO, U64),
                i32(capture.get("capture_date_raw"), "capture_date_raw"),
                optionalInteger(capture.get("capture_thread_id"), "capture_thread_id", 0, 0xffff_ffffL),
                optionalInteger(capture.get("query_thread_id"), "query_thread_id", 0, 0xffff_ffffL),
                optionalText(capture.get("source_return_rva")), bool(capture.get("capture_observed"), "capture_observed"),
                bool(capture.get("capture_complete"), "capture_complete"), bool(capture.get("ready"), "capture.ready"),
                bool(capture.get("raw_counts_ready"), "raw_counts_ready"));
    }
    private static String optionalText(JsonNode value) { return nil(value) ? null : text(value, "original pointer"); }
    private static void unsigned(Long value, String field) { require(value == null || value >= 0 && value <= 0xffff_ffffL, field + ": unsigned32"); }

    /** Original selector self-validates its sidecar; external frame authority remains the outer query caller's job. */
    public static ObjectNode select(JsonNode sidecar, long characterId) {
        unsigned(characterId, "selected CharacterID");
        ObjectNode row = object(sidecar, QUERY_FIELD, "schema", "snapshot_revision", "observed_date_raw", "character_captures");
        ArrayNode raw = array(row.get("character_captures"), "character_captures"); List<Long> requested = new ArrayList<>();
        for (JsonNode leaf : raw) {
            require(leaf.isObject(), "capture object required");
            requested.add(integer(leaf.get("character_id"), "capture CharacterID", 0, 0xffff_ffffL));
        }
        NormalizedQuery normalized = decode(row, QUERY_FIELD,
                integer(row.get("snapshot_revision"), "snapshot_revision", BigInteger.ZERO, U64),
                Math.toIntExact(integer(row.get("observed_date_raw"), "observed_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE)), requested);
        JsonNode selected = null;
        for (JsonNode leaf : normalized.toJson().get("character_captures")) if (leaf.get("character_id").longValue() == characterId) {
            require(selected == null, "full CharacterID selection is ambiguous"); selected = leaf;
        }
        require(selected != null, "Required native input unavailable: full CharacterID selection");
        ObjectNode section = ArmyJson.empty(); section.put("character_id", characterId); section.set(CAPTURE_FIELD, selected.deepCopy()); return section;
    }
}
