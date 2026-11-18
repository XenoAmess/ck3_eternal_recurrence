package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Candidate DATA wrapper for the internal C++ CharacterManagerObservationV1.
 * No Native serializer, transport, capability, callback eligibility or live source role is installed here.
 * Repeated native transcripts do not grant a lock, pin, ABA/lifetime proof or complete gameplay observation.
 */
public final class CharacterManagerObservation1210 {
    public static final String SCHEMA = "xar.ck3.character-manager-observation1210-candidate/v1";
    public static final String SOURCE_ROLE = "internal_candidate_data";
    public static final String ADAPTER = "ck3-1.21.0-msvc-x64";
    public static final String BACKEND = "ck3-1.21.0-native-headless-main-thread";
    /** Author observation limit from the internal reader, not an engine population maximum. */
    public static final int MAX_MEMBERS = 131_072;
    /** Candidate material budget, independent of the author member-count bound. */
    public static final int MAX_PACKET_BYTES = 32 * 1024 * 1024;
    private static final Set<String> FIELDS = Set.of("schema", "source_role", "game_version", "executable_sha256",
            "adapter_id", "backend", "read_only", "available", "same_frame_ready", "manager_members_complete",
            "candidates_complete", "full_snapshot_available", "frame", "members", "unavailable_reason");
    private static final Set<String> FRAME = Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
            "has_played_character", "played_character_id", "played_character_alive");
    private static final Set<String> MEMBER = Set.of("character_id", "alive", "has_living_data");
    private CharacterManagerObservation1210() { }

    /** Copied CoreSnapshotPrefix, not CoreFrame/application-main qualification or an episode binding. */
    public record Prefix(int dateRaw, int speed, boolean paused, int localPlayerId, boolean mapReady,
            boolean hasPlayedCharacter, int playedCharacterId, boolean playedCharacterAlive) {
        public Prefix {
            if (hasPlayedCharacter) NativeCharacterId.of(playedCharacterId);
            else StrictJson.require(playedCharacterId == -1 && !playedCharacterAlive,
                    "absent copied played character must retain its native prefix sentinel");
        }
    }
    public static final Prefix EMPTY_PREFIX = new Prefix(0, 0, false, -1, false, false, -1, false);

    /** The lifecycle bits are independent original header observations. Neither makes this a chooser candidate. */
    public record Member(NativeCharacterId characterId, boolean alive, boolean hasLivingData) {
        public Member { Objects.requireNonNull(characterId); }
    }
    public sealed interface Observation permits CopiedManagerData, UnavailableManagerData {
        Prefix frame();
        List<Member> members();
        boolean available();
        String unavailableReason();
        default boolean sameFrameReady() { return available(); }
        default boolean managerMembersComplete() { return available(); }
        default boolean candidatesComplete() { return false; }
        default boolean fullSnapshotAvailable() { return false; }
    }
    /** Complete maintained manager vector only: dead rows and original order are retained.
     * It is neither all living characters, rulers, realm members nor interaction candidates.
     */
    public record CopiedManagerData(Prefix frame, List<Member> members) implements Observation {
        public CopiedManagerData {
            Objects.requireNonNull(frame); members = List.copyOf(members);
            StrictJson.require(frame.paused() && frame.mapReady() && frame.localPlayerId() >= 0
                    && frame.hasPlayedCharacter() && frame.playedCharacterAlive(),
                    "copied manager data requires its original paused living-player prefix");
            StrictJson.require(members.size() <= MAX_MEMBERS, "author member observation bound exceeded");
            Set<NativeCharacterId> unique = new HashSet<>();
            for (Member member : members) StrictJson.require(unique.add(member.characterId()),
                    "duplicate full character identity in copied manager data");
        }
        @Override public boolean available() { return true; }
        @Override public String unavailableReason() { return ""; }
    }
    /** Native failure output resets the prefix and vector. Its original reason is retained verbatim. */
    public record UnavailableManagerData(String unavailableReason) implements Observation {
        public UnavailableManagerData { StrictJson.text(unavailableReason); }
        @Override public Prefix frame() { return EMPTY_PREFIX; }
        @Override public List<Member> members() { return List.of(); }
        @Override public boolean available() { return false; }
    }

    /** Lookup results concern this copied manager vector; none grants action or complete-population eligibility. */
    public sealed interface MemberLookup permits MemberPresent, MemberAbsent, ManagerUnavailable, FrameMismatch { }
    public record MemberPresent(Member member) implements MemberLookup {
        public MemberPresent { Objects.requireNonNull(member); }
    }
    public record MemberAbsent(NativeCharacterId requestedId) implements MemberLookup {
        public MemberAbsent { Objects.requireNonNull(requestedId); }
    }
    public record ManagerUnavailable(NativeCharacterId requestedId, String originalReason) implements MemberLookup {
        public ManagerUnavailable { Objects.requireNonNull(requestedId); StrictJson.text(originalReason); }
    }
    public record FrameMismatch(NativeCharacterId requestedId, Prefix expected, Prefix actual) implements MemberLookup {
        public FrameMismatch { Objects.requireNonNull(requestedId); Objects.requireNonNull(expected); Objects.requireNonNull(actual); }
    }
    /** Exact full-generation membership only. Missing from this vector never means dead, nonexistent or ineligible. */
    public static MemberLookup lookup(Observation data, Prefix expected, NativeCharacterId requestedId) {
        Objects.requireNonNull(data); Objects.requireNonNull(expected); Objects.requireNonNull(requestedId);
        if (data instanceof UnavailableManagerData unavailable)
            return new ManagerUnavailable(requestedId, unavailable.unavailableReason());
        if (!expected.equals(data.frame())) return new FrameMismatch(requestedId, expected, data.frame());
        for (Member member : data.members()) if (member.characterId().equals(requestedId)) return new MemberPresent(member);
        return new MemberAbsent(requestedId);
    }

    public static Observation decode(byte[] candidate) {
        ObjectNode row = StrictJson.object(FullJsonTree.parse(candidate, MAX_PACKET_BYTES), FIELDS);
        StrictJson.require(SCHEMA.equals(text(row, "schema")) && SOURCE_ROLE.equals(text(row, "source_role"))
                && ExactCk3Build.CK3_1210.matches(text(row, "game_version"), text(row, "executable_sha256"))
                && ADAPTER.equals(text(row, "adapter_id")) && BACKEND.equals(text(row, "backend")),
                "explicit exact Florin candidate DATA identity required");
        StrictJson.require(bool(row.get("read_only")) && !bool(row.get("candidates_complete"))
                && !bool(row.get("full_snapshot_available")), "manager DATA cannot acquire broader source roles");
        boolean available = bool(row.get("available"));
        StrictJson.require(bool(row.get("same_frame_ready")) == available
                && bool(row.get("manager_members_complete")) == available, "native manager readiness flags disagree");
        Prefix frame = decodePrefix(row.get("frame"));
        JsonNode members = row.get("members");
        StrictJson.require(members.isArray() && members.size() <= MAX_MEMBERS, "bounded original manager vector required");
        JsonNode reason = row.get("unavailable_reason");
        StrictJson.require(reason.isTextual(), "original native reason string required, including empty success reason");
        if (!available) {
            StrictJson.require(members.isEmpty() && EMPTY_PREFIX.equals(frame),
                    "failed native manager read must retain its reset prefix and empty vector");
            return new UnavailableManagerData(StrictJson.text(reason));
        }
        StrictJson.require(reason.textValue().isEmpty(), "successful native manager reason must remain empty");
        List<Member> values = new java.util.ArrayList<>(members.size());
        for (JsonNode value : members) {
            ObjectNode member = StrictJson.object(value, MEMBER);
            values.add(new Member(NativeCharacterId.fromJson(member.get("character_id")),
                    bool(member.get("alive")), bool(member.get("has_living_data"))));
        }
        return new CopiedManagerData(frame, values);
    }
    /** Candidate wrapper roundtrip only; this is not a Native packet serializer or transport submission. */
    public static byte[] encode(Observation data) {
        Objects.requireNonNull(data);
        ObjectNode row = StrictJson.object().put("schema", SCHEMA).put("source_role", SOURCE_ROLE)
                .put("game_version", ExactCk3Build.CK3_1210.version())
                .put("executable_sha256", ExactCk3Build.CK3_1210.executableSha256())
                .put("adapter_id", ADAPTER).put("backend", BACKEND).put("read_only", true)
                .put("available", data.available()).put("same_frame_ready", data.sameFrameReady())
                .put("manager_members_complete", data.managerMembersComplete()).put("candidates_complete", false)
                .put("full_snapshot_available", false).put("unavailable_reason", data.unavailableReason());
        Prefix prefix = data.frame();
        row.putObject("frame").put("date_raw", prefix.dateRaw()).put("speed", prefix.speed()).put("paused", prefix.paused())
                .put("local_player_id", prefix.localPlayerId()).put("map_ready", prefix.mapReady())
                .put("has_played_character", prefix.hasPlayedCharacter()).put("played_character_id", prefix.playedCharacterId())
                .put("played_character_alive", prefix.playedCharacterAlive());
        var members = row.putArray("members");
        for (Member member : data.members()) {
            ObjectNode target = members.addObject();
            target.set("character_id", member.characterId().toJson());
            target.put("alive", member.alive()).put("has_living_data", member.hasLivingData());
        }
        return FullJsonTree.encode(row, MAX_PACKET_BYTES);
    }
    private static Prefix decodePrefix(JsonNode value) {
        ObjectNode row = StrictJson.object(value, FRAME);
        return new Prefix(int32(row.get("date_raw")), int32(row.get("speed")), bool(row.get("paused")),
                int32(row.get("local_player_id")), bool(row.get("map_ready")), bool(row.get("has_played_character")),
                int32(row.get("played_character_id")), bool(row.get("played_character_alive")));
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static int int32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "original boolean token required"); return value.booleanValue();
    }
}
