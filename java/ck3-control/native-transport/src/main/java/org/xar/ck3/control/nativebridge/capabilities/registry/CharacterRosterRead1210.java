package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Original readonly roster DATA and reported source proof, never a callback permit or live owner qualification.
 * A manager owner proof lacks model-source evidence and cannot qualify a Family query join.
 */
public final class CharacterRosterRead1210 {
    public static final String SCHEMA = "ck3_1210_character_roster_readonly_v1";
    public static final String STEP = "query-character-manager-roster-v1";
    public static final String ROLE = "actor_readonly_manager_roster";
    public static final int MAX_BYTES = NativeWire.MAXIMUM_FRAME_BYTES;
    private static final Set<String> FIELDS = Set.of("schema", "step", "game_version", "executable_sha256", "adapter_id",
            "source_role", "read_only", "roster_available", "application_main_observed", "source_kind",
            "model_source_observed", "model_source", "same_owner_family_join_available", "all_living_complete",
            "interaction_candidates_complete", "source_proof", "data", "unavailable_reason");
    private static final Set<String> PROOF = Set.of("source_domain", "native_revision", "connection_generation",
            "mailbox_sequence", "pump_epoch", "owner_thread_id", "date_raw", "played_character_id");
    private CharacterRosterRead1210() { }
    public enum SourceKind { OWNED_ACTOR, OFFLINE_FIXTURE, UNQUALIFIED }
    public record SourceProof(BigInteger nativeRevision, BigInteger connectionGeneration, BigInteger mailboxSequence,
            BigInteger pumpEpoch, long ownerThreadId, int dateRaw, NativeCharacterId actor) {
        public SourceProof {
            for (BigInteger value : List.of(nativeRevision, connectionGeneration, mailboxSequence, pumpEpoch))
                StrictJson.require(value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive native uint64 proof required");
            StrictJson.require(ownerThreadId > 0 && ownerThreadId <= 0xffffffffL, "positive native uint32 owner thread required");
            Objects.requireNonNull(actor);
        }
    }
    public record UnjoinedFamilyData(CharacterManagerRoster1210.PacketIdentity managerData, Optional<SourceProof> sourceProof) {
        public UnjoinedFamilyData { Objects.requireNonNull(managerData); sourceProof = Objects.requireNonNull(sourceProof); }
        public String reason() { return "transport_instance_and_model_source_not_observed"; }
        public boolean transportInstanceObserved() { return false; }
        public boolean modelSourceObserved() { return false; }
    }
    public record ScopedRoster(SourceKind sourceKind, CharacterManagerRoster1210.Roster managerMembers,
            UnjoinedFamilyData familyScope) {
        public ScopedRoster { Objects.requireNonNull(sourceKind); Objects.requireNonNull(managerMembers); Objects.requireNonNull(familyScope); }
    }
    public static final class Capture {
        private final RawJson result;
        private final Optional<RawJson> packet;
        private final SourceKind sourceKind;
        private final Optional<SourceProof> sourceProof;
        private final CharacterManagerRoster1210.Capture manager;
        private final String unavailableReason;
        private Capture(RawJson result, Optional<RawJson> packet, SourceKind kind, Optional<SourceProof> proof,
                CharacterManagerRoster1210.Capture manager, String reason) {
            this.result = result; this.packet = packet; sourceKind = kind; sourceProof = proof;
            this.manager = manager; unavailableReason = reason;
        }
        public RawJson originalResult() { return result; }
        public Optional<RawJson> originalPacket() { return packet; }
        public SourceKind sourceKind() { return sourceKind; }
        public Optional<SourceProof> sourceProof() { return sourceProof; }
        public CharacterManagerRoster1210.Capture manager() { return manager; }
        public String unavailableReason() { return unavailableReason; }
        public boolean applicationMainObserved() { return sourceKind == SourceKind.OWNED_ACTOR; }
        public boolean rosterAvailable() { return applicationMainObserved() && manager.observation().available(); }
        public UnjoinedFamilyData familyScope() { return new UnjoinedFamilyData(manager.identity(), sourceProof); }
        public ScopedRoster lookup(CharacterManagerObservation1210.Prefix expected, List<NativeCharacterId> ids) {
            return new ScopedRoster(sourceKind, CharacterManagerRoster1210.lookup(manager, expected, ids), familyScope());
        }
    }
    /** Strict packet correlation preserves original result bytes; it does not establish transport or executor custody. */
    public static Capture decodeCommandResult(byte[] original, String expectedRequestId) throws IOException {
        RawJson packet = new RawJson(original);
        ObjectNode row = StrictJson.object(FullJsonTree.parse(packet.bytes(), MAX_BYTES),
                Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require("command_result".equals(text(row, "type")) && StrictJson.integer(row.get("protocol_version"), 1, 1) == 1
                && StrictJson.text(expectedRequestId).equals(text(row, "request_id")) && bool(row.get("ok")),
                "original roster command result correlation differs");
        return decode(new RawJson(NativeWire.token(packet.bytes(), "result")), Optional.of(packet));
    }
    public static Capture decodeResult(byte[] original) throws IOException { return decode(new RawJson(original), Optional.empty()); }
    public static Capture replay(Capture retained) throws IOException {
        Objects.requireNonNull(retained);
        if (retained.originalPacket().isPresent()) {
            RawJson packet = retained.originalPacket().orElseThrow();
            ObjectNode row = (ObjectNode) FullJsonTree.parse(packet.bytes(), MAX_BYTES);
            return decodeCommandResult(packet.bytes(), text(row, "request_id"));
        }
        return decodeResult(retained.originalResult().bytes());
    }

    private static Capture decode(RawJson result, Optional<RawJson> packet) throws IOException {
        ObjectNode row = StrictJson.object(FullJsonTree.parse(result.bytes(), MAX_BYTES), FIELDS);
        StrictJson.require(SCHEMA.equals(text(row, "schema")) && STEP.equals(text(row, "step"))
                && ROLE.equals(text(row, "source_role"))
                && ExactCk3Build.CK3_1210.matches(text(row, "game_version"), text(row, "executable_sha256"))
                && CharacterManagerObservation1210.ADAPTER.equals(text(row, "adapter_id")), "exact roster source tuple differs");
        StrictJson.require(bool(row.get("read_only")) && !bool(row.get("model_source_observed"))
                && row.get("model_source").isNull() && !bool(row.get("same_owner_family_join_available"))
                && !bool(row.get("all_living_complete")) && !bool(row.get("interaction_candidates_complete")),
                "roster proof cannot acquire model, Family, population or interaction roles");
        SourceKind kind = switch (text(row, "source_kind")) {
            case "owned_actor" -> SourceKind.OWNED_ACTOR;
            case "offline_fixture" -> SourceKind.OFFLINE_FIXTURE;
            case "unqualified" -> SourceKind.UNQUALIFIED;
            default -> throw new IllegalArgumentException("unknown roster source kind");
        };
        boolean owned = kind == SourceKind.OWNED_ACTOR;
        StrictJson.require(bool(row.get("application_main_observed")) == owned, "roster source kind/main observation differs");
        Optional<SourceProof> proof;
        if (owned) proof = Optional.of(proof(row.get("source_proof")));
        else {
            StrictJson.require(row.get("source_proof").isNull(), "offline/unqualified roster cannot carry owner proof");
            proof = Optional.empty();
        }
        CharacterManagerRoster1210.Capture manager = CharacterManagerRoster1210.receive(NativeWire.token(result.bytes(), "data"));
        boolean available = owned && manager.observation().available();
        StrictJson.require(bool(row.get("roster_available")) == available, "roster public DATA and copied manager availability differ");
        String reason;
        if (available) {
            StrictJson.require(row.get("unavailable_reason").isNull(), "available owned roster reason must be null"); reason = null;
            var prefix = manager.observation().frame(); SourceProof actual = proof.orElseThrow();
            StrictJson.require(actual.dateRaw() == prefix.dateRaw() && actual.actor().value() == prefix.playedCharacterId(),
                    "owned roster proof crossed successful manager frame/full actor");
        } else {
            reason = text(row, "unavailable_reason");
            if (owned) StrictJson.require(reason.equals(manager.observation().unavailableReason()),
                    "owned read failure must retain the original manager reason");
            // On read failure the manager prefix resets; an independently observed owner proof need not reset with it.
        }
        return new Capture(result, packet, kind, proof, manager, reason);
    }
    private static SourceProof proof(JsonNode original) {
        ObjectNode row = StrictJson.object(original, PROOF);
        StrictJson.require("character_manager_maintained_members".equals(text(row, "source_domain")), "wrong owner proof source domain");
        return new SourceProof(u64(row.get("native_revision")), u64(row.get("connection_generation")),
                u64(row.get("mailbox_sequence")), u64(row.get("pump_epoch")),
                StrictJson.integer(row.get("owner_thread_id"), 1, 0xffffffffL),
                (int) StrictJson.integer(row.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                NativeCharacterId.fromJson(row.get("played_character_id")));
    }
    private static BigInteger u64(JsonNode value) {
        String decimal = StrictJson.text(value);
        StrictJson.require(decimal.matches("[1-9][0-9]{0,19}"), "canonical positive uint64 decimal string required");
        BigInteger exact = new BigInteger(decimal);
        StrictJson.require(exact.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 source proof overflow"); return exact;
    }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "original roster boolean token required"); return value.booleanValue();
    }
}
