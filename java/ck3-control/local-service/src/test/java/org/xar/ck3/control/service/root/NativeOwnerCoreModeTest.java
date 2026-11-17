package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerCoreModeTest {
    @Test void existingConfigurationKeepsItsSavedOnlyObservationModes() {
        var input=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v1");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.SAVED_FULL,NativeOwnerSnapshotMain268.observationMode(input));
        input.put("core_prefix_only",true);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.SAVED_CORE,NativeOwnerSnapshotMain268.observationMode(input));
        input.put("mode","menu_core_prefix");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(input));
    }
    @Test void menuObservationIsAnExplicitVersionedCoreOnlyMode() {
        var input=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v2").put("mode","menu_core_prefix");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.MENU_CORE,NativeOwnerSnapshotMain268.observationMode(input));
        input.put("core_prefix_only",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(input));
    }
    @Test void malformedOrFutureModesCannotEnableMenuObservation() {
        for(String schema:new String[]{"xar.native-owner-snapshot-config/v1","xar.native-owner-snapshot-config/v2","xar.native-owner-snapshot-config/v3"}) {
            var input=StrictJson.object().put("schema",schema).put("mode","full_snapshot");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(input));
        }
        var wrong=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v1").put("core_prefix_only","true");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(wrong));
    }
    @Test void coreControlRequiresExplicitV3AndAFixedStandardStep() {
        for(String step:new String[]{"pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5","save-checkpoint"}) {
            var input=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v3").put("mode","core_clock_control").put("control_step",step);
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CORE_CONTROL,NativeOwnerSnapshotMain268.observationMode(input));
            input.put("schema","xar.native-owner-snapshot-config/v2");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(input));
        }
        for(String step:new String[]{"query-state","set-speed-6","stop","SAVE",""}) {
            var input=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v3").put("mode","core_clock_control").put("control_step",step);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(input));
        }
    }
}
