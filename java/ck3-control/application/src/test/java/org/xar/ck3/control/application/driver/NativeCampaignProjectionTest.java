package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact native-campaign episode overlay semantics from the original isolated Python producer oracle. */
final class NativeCampaignProjectionTest {
    @Test void preservesMissingNullAndRetainedOriginalEpisodeFieldsWithoutOneLifeBinding() {
        for (String extra : List.of("", ",\"episode_run_id\":null,\"succession_lifecycle\":null",
                ",\"episode_run_id\":\"original-input\",\"succession_lifecycle\":{\"legacy\":\"retained\"}")) {
            String wire = DriverObservationAssemblerTest.STATE.strip();
            wire = wire.substring(0, wire.length() - 1) + extra + "}";
            var actual = DriverObservationAssemblerTest.actual(wire);
            var original = DriverObservationAssembler.originalNativeState(actual);
            var projected = NativeCampaignProjection.originalSnapshot(actual);
            var expected = new LinkedHashMap<>(original.members());
            expected.put("episode_projection", new OpportunityJson.Text("native_campaign"));
            assertEquals(new OpportunityJson.Obj(expected), projected);
            var encoded = NativeCampaignProjection.encodeOriginalSnapshot(actual);
            assertDoesNotThrow(() -> NativeCampaignProjection.requireOriginalSnapshot(actual, encoded));
            assertEquals(original.members().containsKey("episode_run_id"), projected.members().containsKey("episode_run_id"));
            assertEquals(original.get("episode_run_id"), projected.get("episode_run_id"));
            assertEquals(original.get("succession_lifecycle"), projected.get("succession_lifecycle"));
        }
    }

    @Test void followsActualCurrentActorAndRetainsOpaqueNativeValuesAndDecimalTokens() {
        var first = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE
                .replace("\"character_id\":73", "\"character_id\":311"));
        var after = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE
                .replace("\"character_id\":73", "\"character_id\":922")
                .replace("\"speed\":3", "\"speed\":3,\"original_metric\":-0.00"));
        var firstProjection = NativeCampaignProjection.originalSnapshot(first);
        var afterProjection = NativeCampaignProjection.originalSnapshot(after);
        assertEquals(new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(311)),
                OpportunityJson.object(firstProjection.get("played_character"), "played_character").get("character_id"));
        assertEquals(new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(922)),
                OpportunityJson.object(afterProjection.get("played_character"), "played_character").get("character_id"));
        assertEquals(new OpportunityJson.DecimalValue("-0.00"), afterProjection.get("original_metric"));
        assertThrows(IllegalArgumentException.class, () -> NativeCampaignProjection.requireOriginalSnapshot(
                after, NativeCampaignProjection.encodeOriginalSnapshot(first)));
    }

    @Test void originalPacketMismatchAndInjectedEpisodeProjectionAreRejectedByTheChecker() {
        var actual = DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        var fields = new LinkedHashMap<>(NativeCampaignProjection.originalSnapshot(actual).members());
        fields.put("episode_run_id", new OpportunityJson.Text("invented-one-life-episode"));
        assertThrows(IllegalArgumentException.class, () -> NativeCampaignProjection.requireOriginalSnapshot(
                actual, RawJson.fullMaterial(DriverJson.encode(new OpportunityJson.Obj(fields)))));
        byte[] broken = actual.originalPacket();
        broken[0] ^= 1;
        var invalid = new org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame(
                actual.session(), actual.snapshotId(), actual.nativeRevision(), actual.state(), broken, actual.observedAt());
        assertThrows(IllegalArgumentException.class, () -> NativeCampaignProjection.originalSnapshot(invalid));
    }
}
