package org.xar.ck3.control.wave2.events.eventtraits;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Available;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Frame;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Traits;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Unavailable;

final class EventTraitMembershipTest {
    private static final Frame FRAME = new Frame(BigInteger.valueOf(51), 53144520, 29829);
    private static byte[] wire() {
        // Same wire emitted by SerializePlayerEventTraitMembershipV1; no native call or fabricated live evidence.
        return ("{\"schema\":\"xar.ck3.player-event-trait-membership/v1\",\"game_version\":\"1.20.0.4\","
            + "\"executable_sha256\":\"" + EventTraitMembership.EXECUTABLE_SHA256 + "\",\"status\":\"available\","
            + "\"snapshot_revision\":51,\"date_raw\":53144520,\"played_character_id\":29829,"
            + "\"traits\":{\"lifestyle_poet\":false,\"journaller\":true},\"unavailable_reason\":null}")
            .getBytes(StandardCharsets.UTF_8);
    }
    private static ObjectNode object() { return (ObjectNode) StrictJson.parse(wire()); }

    @Test void producerShapeRoundTripsWithoutConflatingFalseAndUnavailable() {
        Available available = new Available(FRAME, new Traits(false, true));
        assertEquals(available, EventTraitMembershipCodec.decode(wire(), FRAME));
        assertEquals(available, EventTraitMembershipCodec.decode(EventTraitMembershipCodec.encode(available), FRAME));
        Unavailable unavailable = new Unavailable(FRAME, "event_trait_membership_unavailable");
        assertEquals(unavailable, EventTraitMembershipCodec.decode(EventTraitMembershipCodec.encode(unavailable), FRAME));
        ObjectNode unavailableWire = (ObjectNode) StrictJson.parse(EventTraitMembershipCodec.encode(unavailable));
        assertTrue(unavailableWire.get("traits").isNull());
        assertFalse(available.traits().lifestylePoet());
    }

    @Test void identitiesRejectBooleanFloatingPointStringAndOverflowTokens() {
        for (String field : new String[]{"snapshot_revision", "date_raw", "played_character_id"}) {
            ObjectNode bool = object(); bool.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(bool), FRAME));
            ObjectNode text = object(); text.put(field, "51");
            assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(text), FRAME));
        }
        byte[] floating = new String(wire(), StandardCharsets.UTF_8).replace("\"snapshot_revision\":51", "\"snapshot_revision\":51.0")
            .getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(floating, FRAME));
        assertThrows(IllegalArgumentException.class, () -> new Frame(StrictJson.UINT64_MAX.add(BigInteger.ONE), 1, 1));
        Frame maximum = new Frame(StrictJson.UINT64_MAX, Integer.MIN_VALUE, Integer.MAX_VALUE);
        Available maximumFact = new Available(maximum, new Traits(false, false));
        assertEquals(maximumFact, EventTraitMembershipCodec.decode(EventTraitMembershipCodec.encode(maximumFact), maximum));
    }

    @Test void missingUnknownNullDuplicateAndWrongTraitTypesRejectAtBoundary() {
        ObjectNode missing = object(); missing.remove("traits");
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(missing), FRAME));
        ObjectNode unknown = object(); unknown.put("ill", false);
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(unknown), FRAME));
        ObjectNode nullTraits = object(); nullTraits.putNull("traits");
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(nullTraits), FRAME));
        ObjectNode wrongTrait = object(); ((ObjectNode) wrongTrait.get("traits")).put("journaller", 1);
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(wrongTrait), FRAME));
        String duplicate = new String(wire(), StandardCharsets.UTF_8).replace("\"snapshot_revision\":51", "\"snapshot_revision\":51,\"snapshot_revision\":51");
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8), FRAME));
        ObjectNode wrongBuild = object(); wrongBuild.put("game_version", "1.19.0.6");
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(StrictJson.canonical(wrongBuild), FRAME));
    }

    @Test void outerNativeRevisionPlayerAndDateMustMatchTheDeclaredSnapshot() {
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(wire(), new Frame(BigInteger.ONE, FRAME.dateRaw(), FRAME.playedCharacterId())));
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(wire(), new Frame(FRAME.nativeRevision(), FRAME.dateRaw() + 1, FRAME.playedCharacterId())));
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decode(wire(), new Frame(FRAME.nativeRevision(), FRAME.dateRaw(), FRAME.playedCharacterId() + 1)));
    }
}
