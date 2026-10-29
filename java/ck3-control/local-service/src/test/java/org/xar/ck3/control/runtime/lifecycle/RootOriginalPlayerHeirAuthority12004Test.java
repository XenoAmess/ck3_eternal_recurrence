package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Component;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Core;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Lineage;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Observation;

/** Software original-packet producer to the actual Root guard; no Game, death or episode qualification. */
final class RootOriginalPlayerHeirAuthority12004Test {
    private static final Frame BEFORE = new Frame("held-preclock",
            StrictJson.UINT64_MAX.subtract(BigInteger.ONE),
            StrictJson.UINT64_MAX.subtract(BigInteger.TWO), 100, 2, 0);

    @Test void nativeSelectedHeirIsIndependentOfPrimaryTitleAndEstateRecipient() {
        ObjectNode original = root();
        ObjectNode nativeRoot = object(original.get("campaign_root_context"));
        nativeRoot.putArray("primary_title_succession_character_ids").add(3);
        nativeRoot.putArray("held_title_partition").addObject()
                .put("first_heir_character_id", 3).put("primary", true)
                .putObject("title").put("title_id", 10);
        byte[] exact = bytes(original);
        assertDoesNotThrow(() -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(exact, BEFORE, 7));
        assertThrows(IllegalArgumentException.class,
                () -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(exact, BEFORE, 3));
        assertArrayEquals(exact, bytes(original));
    }

    @Test void matchingTitleProjectionCannotReplaceMissingOrNullNativeObservation() {
        ObjectNode original = root();
        ObjectNode nativeRoot = object(original.get("campaign_root_context"));
        nativeRoot.putArray("primary_title_succession_character_ids").add(7);
        nativeRoot.remove(NativePlayerHeirObservation12004.COMPONENT);
        assertRejected(original);
        nativeRoot.putNull(NativePlayerHeirObservation12004.COMPONENT);
        assertRejected(original);
    }

    @Test void deadFixtureUnboundOrUnobservedCandidateCannotAcquireAuthority() {
        for (String field : List.of("source_fixture", "candidate_alive", "getter_observed", "identity_and_frame_stable")) {
            ObjectNode original = root();
            observation(original).put(field, field.equals("source_fixture"));
            assertRejected(original);
        }
        ObjectNode unbound = root();
        component(unbound).put("parent_frame_bound", false);
        assertRejected(unbound);
        assertThrows(IllegalArgumentException.class,
                () -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(bytes(root()), BEFORE, 2));
    }

    @Test void realWireRoundTripRetainsFullUnsignedRevisionsAndRejectsWrongTypesOrFrame() {
        byte[] original = bytes(root());
        JsonNode decoded = StrictJson.parse(original, NativePlayerHeirObservation12004.MAX_BYTES);
        assertEquals(BEFORE.nativeRevision(), decoded.get("snapshot_revision").bigIntegerValue());
        assertDoesNotThrow(() -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(
                StrictJson.canonical(decoded), BEFORE, 7));
        for (String wrong : List.of("true", "7.0", "\"7\"", "null")) {
            ObjectNode malformed = root();
            observation(malformed).set("candidate_character_id", StrictJson.parse(wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertRejected(malformed);
        }
        Frame otherFrame = new Frame(BEFORE.snapshotId(), BEFORE.publicRevision(),
                BEFORE.nativeRevision().subtract(BigInteger.ONE), BEFORE.dateRaw(), BEFORE.actorCharacterId(), BEFORE.localPlayerId());
        assertThrows(IllegalArgumentException.class,
                () -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(original, otherFrame, 7));
        ObjectNode wrongSource = root();
        object(object(wrongSource.get("campaign_root_context")).get("provenance")).put("executable_sha256", "a".repeat(64));
        assertRejected(wrongSource);
    }

    @Test void mutableAnyMoveHelpersCannotMasqueradeAsTheOriginalReadOnlyHeirGetter() {
        for (String helper : List.of("0xB1A7E0", "0xB1B710", "0xB19FE0", "0xB19D70")) {
            ObjectNode original = root();
            component(original).put("getter_rva", helper);
            assertRejected(original);
        }
    }

    @Test void nativePublicationAndHandlerLifecycleCannotSubstituteForThePreclockGetter() {
        assertDoesNotThrow(() -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(bytes(root()), BEFORE, 7));
        // These are observed publication, lifecycle or child-maintenance entries, not the original getter.
        for (String entry : List.of("0xAF1880", "0xB20270", "0xAEF650", "0xAEF9E0", "0xAF0340", "0xAF1BD0",
                "0x1111770", "0x111D790", "0x113C770", "0x113C880", "0xB00EF0", "0xAFE0F0", "0xAFC0F0",
                "0xAF34A0", "0xAF3950", "0xAF39E0", "0xAED250", "0xAED360",
                "0xAF3410", "0xAFB630", "0xAFBE70", "0xAF97F0")) {
            ObjectNode original = root();
            component(original).put("getter_rva", entry);
            assertRejected(original);
        }
        ObjectNode projectionOnly = root();
        ObjectNode nativeRoot = object(projectionOnly.get("campaign_root_context"));
        nativeRoot.remove(NativePlayerHeirObservation12004.COMPONENT);
        // Even matching values in a typed publication/modal projection do not recover a missing original.
        ObjectNode publication = nativeRoot.putObject("candidate_native_publication");
        publication.put("message_code", 0x2F22).put("event_type", "SSuccessionEventData")
                .put("subject_character_id", 2).put("estate_recipient_character_id", 3)
                .put("player_heir_character_id", 7).put("handler_optional_present", true)
                .put("modal_get_player_heir_character_id", 7);
        assertRejected(projectionOnly);
    }

    private static ObjectNode root() {
        ObjectNode packet = StrictJson.object().put("step", "query-campaign-root-context-v1")
                .put("accepted", true).put("status", "available").put("query_sequence", 5)
                .put("snapshot_revision", BEFORE.nativeRevision()).put("backend_id", "native-headless");
        ObjectNode nativeRoot = packet.putObject("campaign_root_context").put("status", "available")
                .put("snapshot_revision", BEFORE.nativeRevision()).put("date_raw", BEFORE.dateRaw())
                .put("player_character_id", BEFORE.actorCharacterId()).put("local_player_id", BEFORE.localPlayerId())
                .put("player_character_alive", true);
        nativeRoot.putObject("readiness").put("same_frame_ready", true);
        nativeRoot.putObject("provenance").put("executable_sha256", NativePlayerHeirObservation12004.EXE_SHA256);
        Core core = new Core(BEFORE.dateRaw(), true, 3, BEFORE.localPlayerId(), true, true, BEFORE.actorCharacterId(), true);
        Observation observed = new Observation(true, null, false, true, core, core, true, true,
                BEFORE.actorCharacterId(), 7, true, true, true, new Lineage(8, 9), null);
        nativeRoot.set(NativePlayerHeirObservation12004.COMPONENT,
                StrictJson.parse(NativePlayerHeirObservation12004.encodeComponent(new Component(BEFORE.nativeRevision(), true, observed))));
        return packet;
    }

    private static ObjectNode component(ObjectNode packet) {
        return object(packet.get("campaign_root_context").get(NativePlayerHeirObservation12004.COMPONENT));
    }
    private static ObjectNode observation(ObjectNode packet) { return object(component(packet).get("observation")); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, NativePlayerHeirObservation12004.MAX_BYTES); }
    private static void assertRejected(ObjectNode packet) {
        assertThrows(IllegalArgumentException.class,
                () -> RootOriginalNaturalSuccessionVerifier.requireOriginalPlayerHeir(bytes(packet), BEFORE, 7));
    }
    private static ObjectNode object(JsonNode value) {
        if (value instanceof ObjectNode object) return object;
        throw new IllegalArgumentException("fixture object required");
    }
}
