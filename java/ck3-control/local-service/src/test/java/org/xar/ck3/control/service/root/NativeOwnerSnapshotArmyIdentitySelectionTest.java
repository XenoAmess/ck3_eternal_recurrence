package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport.NativeSourceMode;
import org.xar.ck3.control.service.root.NativeOwnerSnapshotMain268.ObservationMode;

/** Checks configuration and source selection without attachment. */
final class NativeOwnerSnapshotArmyIdentitySelectionTest {
    private static final String SCHEMA = "xar.native-owner-snapshot-config/v53";
    private static final String MODE = "current_army_identity_readonly";

    @Test
    void onlyExplicitIdentityModeSelectsTheReadonlyTransport() {
        var selected = NativeOwnerSnapshotMain268.observationMode(config().put("mode", MODE));
        assertEquals(ObservationMode.CURRENT_ARMY_IDENTITY_READONLY, selected);
        assertEquals(NativeSourceMode.CURRENT_IDENTITY_READONLY, NativeOwnerSnapshotMain268.nativeSourceMode(selected));

        var ordinary = NativeOwnerSnapshotMain268.observationMode(config().put("schema", "xar.native-owner-snapshot-config/v1"));
        assertEquals(ObservationMode.SAVED_FULL, ordinary);
        assertEquals(NativeSourceMode.DEFAULT_CONTROL, NativeOwnerSnapshotMain268.nativeSourceMode(ordinary));
    }

    @Test
    void identitySchemaRejectsControlAndMixedModes() {
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(config()));
        assertThrows(IllegalArgumentException.class,
                () -> NativeOwnerSnapshotMain268.observationMode(config().put("mode", "core_clock_control")));
        assertThrows(IllegalArgumentException.class,
                () -> NativeOwnerSnapshotMain268.observationMode(config().put("mode", MODE).put("control_step", "resume-map")));
        assertThrows(IllegalArgumentException.class,
                () -> NativeOwnerSnapshotMain268.observationMode(config().put("mode", MODE).put("core_prefix_only", false)));
        assertThrows(IllegalArgumentException.class,
                () -> NativeOwnerSnapshotMain268.observationMode(config().put("schema", "xar.native-owner-snapshot-config/v1").put("mode", MODE)));
    }

    @Test
    void identitySchemaRequiresTheCompleteConfig() {
        var incomplete = config().put("mode", MODE);
        incomplete.remove("read_timeout_seconds");
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(incomplete));
        assertThrows(IllegalArgumentException.class,
                () -> NativeOwnerSnapshotMain268.observationMode(config().put("mode", MODE).put("extra", true)));
    }

    @Test
    void heldDateStatusSelectsOnlyItsFixedReadMode() {
        var status = config().put("schema", "xar.native-owner-snapshot-config/v54").put("mode", "held_date_sentinel_status");
        assertEquals(ObservationMode.HELD_DATE_SENTINEL_STATUS, NativeOwnerSnapshotMain268.observationMode(status));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(status.deepCopy().put("mode", "date_sentinel_advance")));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(status.deepCopy().put("control_step", "resume-map")));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(status.deepCopy().put("maximum_status_polls", 4)));
    }

    @Test
    void heldFull111EventsHasNoCallerSelectedActionOrEvent() {
        var events = config().put("schema", "xar.native-owner-snapshot-config/v55").put("mode", "held_full111_ordinary_events");
        assertEquals(ObservationMode.HELD_FULL111_ORDINARY_EVENTS, NativeOwnerSnapshotMain268.observationMode(events));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(events.deepCopy().put("mode", "held_date_sentinel_status")));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(events.deepCopy().put("instance_id", 7)));
        assertThrows(IllegalArgumentException.class, () -> NativeOwnerSnapshotMain268.observationMode(events.deepCopy().put("control_step", "resume-map")));
    }

    private static ObjectNode config() {
        var config = StrictJson.object().put("schema", SCHEMA).put("overall_timeout_seconds", 30)
                .put("read_timeout_seconds", 10).put("maximum_frames_per_operation", 8);
        config.set("owner_descriptor", new ExactRef("fixture-owner.json", 1, "0".repeat(64)).toJson());
        return config;
    }
}
