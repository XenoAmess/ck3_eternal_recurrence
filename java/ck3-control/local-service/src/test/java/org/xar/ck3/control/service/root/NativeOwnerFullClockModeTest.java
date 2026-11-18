package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerFullClockModeTest {
    @Test void exactV7FixedStepsAreIndependentOfCoreAndReadonlyModes(){
        for(String step:new String[]{"pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5","save-checkpoint"}){
            var row=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v7").put("mode","full_snapshot_clock_control").put("control_step",step);
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.FULL_CLOCK,NativeOwnerSnapshotMain268.observationMode(row));
        }
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.SAVED_FULL,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v1")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CORE_CONTROL,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v3").put("mode","core_clock_control").put("control_step","pause-map")));
    }
    @Test void fullClockCannotBorrowEarlierSchemasVariableStepsOrLegacyFlags(){
        for(int version=1;version<=6;version++){
            var row=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v"+version).put("mode","full_snapshot_clock_control").put("control_step","set-speed-1");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        for(String step:new String[]{"research-arm-tactical-daily-sentinel-v1-1-to-25-speed-1-mode-terminal-a-0","unknown","set-speed-0"}){
            var row=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v7").put("mode","full_snapshot_clock_control").put("control_step",step);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        var flag=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v7").put("mode","full_snapshot_clock_control").put("control_step","set-speed-1").put("core_prefix_only",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(flag));
    }
}
