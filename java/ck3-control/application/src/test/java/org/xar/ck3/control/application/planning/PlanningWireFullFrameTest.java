package org.xar.ck3.control.application.planning;

import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

final class PlanningWireFullFrameTest {
    @Test void fullSnapshotAndHistoryAboveOldBothLimitsRoundTripWithoutInventingMissingOrNull() {
        var snapshot = snapshot().with("full_native_payload", new OpportunityJson.Text("x".repeat(150_000)))
                .with("explicit_null", OpportunityJson.Nil.INSTANCE);
        var history = List.of(new OpportunityJson.Obj(Map.of("original_payload", new OpportunityJson.Text("h".repeat(1_100_000)))));
        var original = request(snapshot, history, Set.of(new OperationKey("life-advance")));
        byte[] wire = PlanningWire.encodeRequest(original);
        assertTrue(wire.length > 1_048_576);
        var roundTrip = PlanningWire.decodeRequest(wire);
        assertEquals(original, roundTrip);
        assertFalse(roundTrip.observations().snapshot().members().containsKey("absent_field"));
        assertSame(OpportunityJson.Nil.INSTANCE, roundTrip.observations().snapshot().get("explicit_null"));
        assertEquals(List.of(), OpportunityJson.array(roundTrip.observations().snapshot().get("player_armies"), "armies"));
    }
    @Test void actualSnapshotIdentityRejectsBooleanAndFloatTokensBeforePlanning() {
        var request = request(snapshot(), List.of(), Set.of());
        String valid = new String(PlanningWire.encodeRequest(request), StandardCharsets.UTF_8);
        for (String invalid : List.of(valid.replace("\"native_revision\":1", "\"native_revision\":true"),
                valid.replace("\"native_revision\":1", "\"native_revision\":1.0"),
                valid.replace("\"revision\":1", "\"revision\":true"),
                valid.replace("\"snapshot_id\":\"snapshot-1\"", "\"wrong_snapshot_id\":\"snapshot-1\""))) {
            assertThrows(IllegalArgumentException.class, () -> PlanningWire.decodeRequest(invalid.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void aDifferentRealmLifecycleCannotBeRegisteredBehindThePlannersPublicationSlot() {
        var owner = new RealmLifecycle(SOURCE);
        var other = new RealmLifecycle(SOURCE);
        assertThrows(IllegalArgumentException.class, () -> new OrdinaryPlanner(List.of(other),
                Clock.fixed(NOW, ZoneOffset.UTC), owner));
        var actual = new OrdinaryPlanner(List.of(owner), Clock.fixed(NOW, ZoneOffset.UTC), owner);
        assertFalse(actual.missingStages().contains(PlanningStage.REALM_MEMBERSHIP_PUBLICATION));
        assertEquals(PlanningStage.values().length - 1, actual.missingStages().size());
    }
    @Test void incompleteMigrationSurvivesTheRealPlannerAndResultWireWithExactMissingStages() {
        var realm = new RealmLifecycle(SOURCE);
        var planner = new OrdinaryPlanner(List.of(realm), Clock.fixed(NOW, ZoneOffset.UTC), realm);
        var result = assertInstanceOf(PlanningResult.IncompleteMigration.class,
                planner.plan(request(snapshot(), List.of(), Set.of())));
        assertEquals(planner.missingStages(), result.missingStages());
        assertEquals(result, PlanningWire.decodeResult(PlanningWire.encodeResult(result)));
    }
}
