package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;

/** Closed DATA/serde/reducer contracts only; no private Entry authority or physical Game is constructed. */
final class ObservedGameplayEntryTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String SESSION = "sess-001";
    private static final String EPISODE = "ep-001";
    private static final String SNAPSHOT = "snap-001";
    private static final BigInteger HIGH_UINT64 = new BigInteger("18446744073709551615"); // 2^64 - 1
    private static final long GAME_PID = 73L;
    private static final String GAME_CREATION = "9007199254740993";

    private static ContinuityState initial() throws Exception {
        var plan = new FreshContinuityGenesis.Plan(MACHINE, 1, OriginalWindowReducer.TARGET_DAYS);
        byte[] request = FreshContinuityGenesis.encode(plan);
        String digest = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(request));
        return FreshContinuityGenesis.initial(plan, new ExactRef("D:/software-fixture/genesis-request.json", request.length, digest));
    }

    private static ExactRef makeRef(String path, int len, String digest) {
        return new ExactRef("D:/software-fixture/"+path, len, "a".repeat(64));
    }

    private static GameGeneration makeGame() {
        return GameGeneration.fromJson(StrictJson.object().put("pid", GAME_PID).put("creation_filetime", GAME_CREATION));
    }

    private static ObservedGameplayEntry.Details makeDetails() {
        return new ObservedGameplayEntry.Details(
            MACHINE, SESSION, EPISODE, SNAPSHOT,
            makeGame(),
            1L, 100L, 1L,
            BigInteger.valueOf(2), HIGH_UINT64,
            makeRef("start.json", 10, "d1"),
            makeRef("read.json", 10, "d2"),
            makeRef("frame.json", 10, "d3"),
            makeRef("driver.json", 10, "d4"),
            makeRef("facts.json", 10, "d5")
        );
    }

    @Test void typedEncodeDecodeHighUint64ConnectionAndExactGameBirth() {
        var details = makeDetails();
        var json = details.toJson();
        var decoded = ObservedGameplayEntry.decode(json);
        
        // Verify high uint64 connection generation roundtrip
        assertEquals(HIGH_UINT64, decoded.connectionGeneration());
        assertEquals(BigInteger.valueOf(2), decoded.nativeRevision());
        
        // Verify exact Game birth > 2^53
        assertEquals(GAME_PID, decoded.game().pid());
        assertEquals(GAME_CREATION, decoded.game().creationFiletime().value().toString());
        
        // Verify byte array identity via assertArrayEquals on canonical bytes
        assertArrayEquals(ContinuityJson.canonical(json), ContinuityJson.canonical(decoded.toJson()));
    }

    @Test void preentryActualActorDateGameBaselineBindingAnd0CreditHistoricalReadback() throws Exception {
        var state = initial();
        var details = makeDetails();
        var request = details.request();
        
        // Reduce with sequenced=true to update sequence and active/pending fields
        var next = ObservedGameplayEntry.reduce(state, request, true);
        
        // Verify baseline field is set (actual WriterContracts field, not invented)
        var nextJson = next.toJson();
        assertTrue(nextJson.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD));
        assertTrue(nextJson.has(WriterContracts.GAMEPLAY_ENTRY_FIELD));
        
        // Verify sequence update
        assertEquals(state.sequence() + 1, next.sequence());
        
        // Verify 0 credit (no settled cycles yet)
        assertEquals(0, next.settledCycles());
        
        assertEquals(details.dateRaw(), next.origin().startDateRaw());
        assertEquals(details.dateRaw()+OriginalWindowReducer.TARGET_DAYS*24, next.origin().targetDateRaw());
        assertEquals(details.actorId(), nextJson.path("latest_binding").path("actor_character_id").longValue());
        assertEquals(details.episodeId(), nextJson.path("latest_binding").path("episode_run_id").textValue());
        assertEquals(details.fullDriver(), ExactRef.fromJson(nextJson.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)));
        var envelope=new ContinuityEvent(next.sequence(),"2026-10-28T18:20:00Z",request.kind(),request.details(),
                request.identity(),ContinuityJson.digest(state.toJson()),next);
        var reopened=ContinuityEvent.fromJson(envelope.toJson(),state);
        assertArrayEquals(next.canonicalBytes(),reopened.after().canonicalBytes());
        var falseCredit=envelope.toJson();((ObjectNode)falseCredit.get("after")).put("last_settled_cycles",1);
        assertThrows(IllegalArgumentException.class,()->ContinuityEvent.fromJson(falseCredit,state));
    }

    @Test void wrongTypeBoolFloatMissingNullExtraAllRefuse() {
        var details = makeDetails();
        var json = details.toJson();
        
        // Test missing field
        var missing = json.deepCopy();
        missing.remove("schema");
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(missing));
        
        // Test wrong type (bool instead of string for schema)
        var wrongType = json.deepCopy();
        wrongType.put("schema", true);
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(wrongType));
        
        // Test null value
        var nullVal = json.deepCopy();
        nullVal.putNull("episode_id");
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(nullVal));
        
        // Test extra field
        var extra = json.deepCopy();
        extra.put("extra_field", "value");
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(extra));
        
        // Test float instead of integer for revision
        var floatRev = json.deepCopy();
        ((ObjectNode)floatRev.get("frame")).put("revision", 1.5);
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(floatRev));
    }

    @Test void unknownRetainedRejectsAndCannotReplayAlreadyActiveOrNewBinding() throws Exception {
        var state = initial();
        var details = makeDetails();
        var request = details.request();
        
        // First reduce succeeds
        var next = ObservedGameplayEntry.reduce(state, request, true);
        
        // Replay same request on already active state fails
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.reduce(next, request, true));
        
        // Create a state with UNKNOWN retained
        var unknownStateJson = state.toJson();
        unknownStateJson.putArray("unknown_actions").add("retained-original-unknown");
        var unknownState = ContinuityState.fromJson(unknownStateJson, MACHINE);
        
        // Reduce on UNKNOWN state fails
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.reduce(unknownState, request, true));
        
        // New binding attempt on already bound state fails
        var newDetails = new ObservedGameplayEntry.Details(
            MACHINE, "new-session", "new-episode", "new-snapshot",
            makeGame(), 2L, 200L, 2L,
            BigInteger.valueOf(2), HIGH_UINT64,
            makeRef("start2.json", 10, "d6"),
            makeRef("read2.json", 10, "d7"),
            makeRef("frame2.json", 10, "d8"),
            makeRef("driver2.json", 10, "d9"),
            makeRef("facts2.json", 10, "d10")
        );
        var newRequest = newDetails.request();
        assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.reduce(next, newRequest, true));
    }
@Test void v2ExactRoundtripCommonEvidence4NoFakeStartAndStartAckThrowsIllegalState() {
    var d = makeDetails();
    var details = new ObservedGameplayEntry.Details(
        d.machineId(), d.sessionId(), d.episodeId(), d.snapshotId(),
        d.game(), d.revision(), d.dateRaw(), d.actorId(),
        d.nativeRevision(), d.connectionGeneration(),
        new ObservedGameplayEntry.Origin.CurrentMap(),
        d.readAck(), d.nativeFrame(), d.fullDriver(), d.driverFacts()
    );
    assertEquals(java.util.List.of(d.readAck(),d.nativeFrame(),d.fullDriver(),d.driverFacts()),details.evidence());
    var json = details.toJson();
    assertFalse(json.has("start_ack"));
    var decoded = ObservedGameplayEntry.decode(json);
    assertEquals("xar.java.observed-gameplay-entry/v2", json.path("schema").textValue());
    assertEquals("current_map_observation", json.path("entry_origin").textValue());
    assertEquals(d.readAck(), decoded.readAck());
    assertEquals(d.nativeFrame(), decoded.nativeFrame());
    assertEquals(d.fullDriver(), decoded.fullDriver());
    assertEquals(d.driverFacts(), decoded.driverFacts());
    assertEquals(d.game(), decoded.game());
    assertThrows(IllegalStateException.class, () -> decoded.startAck());
    assertArrayEquals(ContinuityJson.canonical(json), ContinuityJson.canonical(decoded.toJson()));
}
@Test void v2ForbiddenStartAckNullOriginWrongTypeMissingReadAckAndV1ExtraOriginAllIllegalArgument() {
    var d = makeDetails();
    var details = new ObservedGameplayEntry.Details(
        d.machineId(), d.sessionId(), d.episodeId(), d.snapshotId(),
        d.game(), d.revision(), d.dateRaw(), d.actorId(),
        d.nativeRevision(), d.connectionGeneration(),
        new ObservedGameplayEntry.Origin.CurrentMap(),
        d.readAck(), d.nativeFrame(), d.fullDriver(), d.driverFacts()
    );
    var json = details.toJson();
    
    var withStartAck = json.deepCopy();
    withStartAck.set("start_ack", d.startAck().toJson());
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(withStartAck));
    
    var nullOrigin = json.deepCopy();
    nullOrigin.putNull("entry_origin");
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(nullOrigin));
    
    var wrongType = json.deepCopy();
    wrongType.put("entry_origin", 123);
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(wrongType));
    
    var missingReadAck = json.deepCopy();
    missingReadAck.remove("read_ack");
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(missingReadAck));
    
    var v1ExtraOrigin = d.toJson();
    v1ExtraOrigin.put("schema", "xar.java.observed-gameplay-entry/v1");
    v1ExtraOrigin.put("entry_origin", "current_map_observation");
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.decode(v1ExtraOrigin));
}
@Test void v2RealReducerInitializesPreentryDateActorBaseline0SettledAndContinuityEventFromJsonSupportsNewSchemaReplayAndUnknownActionsRefuse() throws Exception {
    var state = initial();
    var d = makeDetails();
    var details = new ObservedGameplayEntry.Details(
        d.machineId(), d.sessionId(), d.episodeId(), d.snapshotId(),
        d.game(), d.revision(), d.dateRaw(), d.actorId(),
        d.nativeRevision(), d.connectionGeneration(),
        new ObservedGameplayEntry.Origin.CurrentMap(),
        d.readAck(), d.nativeFrame(), d.fullDriver(), d.driverFacts()
    );
    var request = details.request();
    var next = ObservedGameplayEntry.reduce(state, request, true);
    var nextJson = next.toJson();
    
    assertEquals(d.dateRaw(), next.origin().startDateRaw());
    assertEquals(d.actorId(), nextJson.path("latest_binding").path("actor_character_id").longValue());
    assertTrue(nextJson.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD));
    assertEquals(0, next.settledCycles());
    
    var envelope = new ContinuityEvent(next.sequence(), "2026-10-28T18:20:00Z", request.kind(), request.details(),
        request.identity(), ContinuityJson.digest(state.toJson()), next);
    var reopened = ContinuityEvent.fromJson(envelope.toJson(), state);
    assertArrayEquals(next.canonicalBytes(), reopened.after().canonicalBytes());
    
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.reduce(next, request, true));
    
    var unknownStateJson = state.toJson();
    unknownStateJson.putArray("unknown_actions").add("retained-original-unknown");
    var unknownState = ContinuityState.fromJson(unknownStateJson, MACHINE);
    assertThrows(IllegalArgumentException.class, () -> ObservedGameplayEntry.reduce(unknownState, request, true));
}
}
