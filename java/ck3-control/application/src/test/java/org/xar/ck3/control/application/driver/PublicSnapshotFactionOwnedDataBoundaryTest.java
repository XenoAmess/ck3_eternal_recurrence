package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;

/** Owner-written public DATA boundaries. These fixtures create no source or gameplay authority. */
final class PublicSnapshotFactionOwnedDataBoundaryTest {
    private static final int FIXTURE_LIMIT = 16_384;
    private static final int ACTOR = 701;
    private static final int DATE = 5088;
    private static final String FACTION = "player_faction_alerts";
    private static final BigInteger REVISION = StrictJson.UINT64_MAX;

    @Test
    void availableFactionRoundtripKeepsWideIdentityAndOriginalJsonValues() {
        RawJson numeric = material(snapshot(ACTOR, REVISION, "first-input"));
        byte[] originalBytes = numeric.bytes();
        var expected = model(numeric);

        RawJson publicForm = PublicSnapshotCodec.encodeSemanticData(numeric);
        RawJson restored = PublicSnapshotCodec.decodeSemanticData(publicForm);
        var actual = model(restored);

        assertEquals(expected, actual);
        assertArrayEquals(originalBytes, numeric.bytes());
        assertEquals(new OpportunityJson.Text(REVISION.toString()),
                faction(model(publicForm)).get("snapshot_revision"));
        assertEquals(new OpportunityJson.IntegerValue(REVISION),
                faction(actual).get("snapshot_revision"));
        assertEquals(new OpportunityJson.Text(REVISION.toString()),
                model(publicForm).get("native_revision"));
        var opaque = assertInstanceOf(OpportunityJson.Arr.class, actual.get("opaque_data")).items();
        assertEquals(new OpportunityJson.DecimalValue("-0.0"), opaque.get(0));
        assertEquals(new OpportunityJson.DecimalValue("1.2500e+2"), opaque.get(1));
        assertEquals(new OpportunityJson.Text("source \uD83C\uDF0B"), opaque.get(2));
    }

    @Test
    void interleavedCallsRetainTheirOwnActorsRevisionsAndCapturedBytes() {
        RawJson first = material(snapshot(ACTOR, REVISION, "first-input"));
        RawJson second = material(snapshot(ACTOR + 1, REVISION.subtract(BigInteger.ONE), "second-input"));
        byte[] firstBefore = first.bytes();
        byte[] secondBefore = second.bytes();
        var firstExpected = model(first);
        var secondExpected = model(second);
        assertNotEquals(firstExpected, secondExpected);

        RawJson firstPublic = PublicSnapshotCodec.encodeSemanticData(first);
        byte[] firstPublicBefore = firstPublic.bytes();
        assertEquals(firstExpected, model(PublicSnapshotCodec.decodeSemanticData(firstPublic)));
        RawJson secondPublic = PublicSnapshotCodec.encodeSemanticData(second);
        assertEquals(secondExpected, model(PublicSnapshotCodec.decodeSemanticData(secondPublic)));
        assertEquals(firstExpected, model(PublicSnapshotCodec.decodeSemanticData(firstPublic)));

        assertArrayEquals(firstBefore, first.bytes());
        assertArrayEquals(secondBefore, second.bytes());
        assertArrayEquals(firstPublicBefore, firstPublic.bytes());
    }

    @Test
    void decoderRejectsTheChangedPlayedActorWithTheOriginalExactFailure() {
        RawJson numeric = material(snapshot(ACTOR, REVISION, "actor-check"));
        RawJson publicForm = PublicSnapshotCodec.encodeSemanticData(numeric);
        assertEquals(model(numeric), model(PublicSnapshotCodec.decodeSemanticData(publicForm)));
        byte[] publicBefore = publicForm.bytes();

        ObjectNode changed = PublicDataJson.object(publicForm);
        ObjectNode played = assertInstanceOf(ObjectNode.class, changed.get("played_character"));
        played.put("character_id", ACTOR + 1);
        assertEquals(ACTOR, changed.path("episode_character_id").intValue());
        assertEquals(ACTOR, changed.path(FACTION).path("player_character_id").intValue());
        RawJson mismatched = material(changed);

        var failure = assertThrows(ContractViolationException.class,
                () -> PublicSnapshotCodec.decodeSemanticData(mismatched));
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals("faction semantic payload crossed the containing snapshot actor", failure.getMessage());
        assertArrayEquals(publicBefore, publicForm.bytes());
    }

    private static RawJson material(ObjectNode value) {
        return RawJson.fullMaterial(FullJsonTree.encode(value, FIXTURE_LIMIT));
    }

    private static OpportunityJson.Obj model(RawJson value) {
        return DriverJson.object(value.bytes(), RawJson.MAXIMUM_BYTES);
    }

    private static OpportunityJson.Obj faction(OpportunityJson.Obj snapshot) {
        return assertInstanceOf(OpportunityJson.Obj.class, snapshot.get(FACTION));
    }

    private static ObjectNode snapshot(int actor, BigInteger nativeRevision, String tag) {
        ObjectNode snapshot = StrictJson.object();
        snapshot.put("format_version", 1).put("snapshot_id", "owner-faction-data").put("revision", 23);
        snapshot.put("native_revision", nativeRevision).put("date_raw", DATE);
        snapshot.put("paused", true).put("map_ready", true).put("speed", 3);
        snapshot.put("episode_run_id", "owner-data-episode").put("episode_character_id", actor);
        snapshot.putObject("played_character").put("character_id", actor).put("alive", true);
        snapshot.putNull("active_event");
        snapshot.putNull("pending_character_interaction");
        snapshot.putNull("one_life_terminal_reason");
        snapshot.putArray("active_wars");
        snapshot.putArray("player_armies");
        snapshot.putArray("native_command_history");
        snapshot.putObject("diagnostics");
        snapshot.put("data_tag", tag);
        var opaque = snapshot.putArray("opaque_data");
        opaque.add(new DecimalTokenNode("-0.0"));
        opaque.add(new DecimalTokenNode("1.2500e+2"));
        opaque.add("source \uD83C\uDF0B");

        ObjectNode faction = snapshot.putObject(FACTION);
        faction.put("schema_version", 1).put("status", "available");
        faction.put("snapshot_revision", nativeRevision).put("date_raw", DATE);
        faction.put("player_character_id", actor).put("targeting_faction_count", 0);
        faction.putArray("targeting_factions");
        faction.putArray("county_exposures");
        faction.putNull("unavailable_reason");
        ObjectNode planner = faction.putObject("planner_projection");
        planner.put("status", "unavailable");
        planner.putNull("present");
        planner.putNull("dangerous");
        planner.putArray("dangerous_faction_ids");
        planner.putArray("watch_faction_ids");
        planner.putArray("war_handoff_faction_ids");
        planner.putArray("exposed_county_title_ids");
        planner.put("exact_ultimatum_timing_ready", false);
        ObjectNode readiness = faction.putObject("readiness");
        readiness.put("identity_ready", true).put("targeting_count_ready", true);
        readiness.put("targeting_rows_ready", false).put("county_exposure_ready", false);
        readiness.put("stock_dangerous_predicate_ready", false).put("same_frame_ready", true);
        readiness.put("alert_ready", false).put("exact_ultimatum_timing_ready", false);
        faction.putObject("component_unavailable_reasons")
                .put("targeting_rows", FactionAlertModel.ROWS_UNAVAILABLE)
                .put("county_exposure", FactionAlertModel.COUNTY_UNAVAILABLE);
        var build = FactionAlertModel.Build.CK3_12004;
        faction.putObject("provenance").put("game_version", build.version())
                .put("executable_sha256", build.sha256()).put("backend_id", build.backendId());
        return snapshot;
    }
}
