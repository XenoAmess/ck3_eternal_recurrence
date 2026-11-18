package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerDateAdvanceModeTest {
    private static ObjectNode configuration(){
        return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v8")
                .put("mode","date_sentinel_advance_one_day").put("maximum_status_polls",64).put("status_poll_interval_ms",500);
    }
    @Test void oneDayModeRequiresItsExplicitBoundedPollingContract(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(configuration()));
        for(String field:new String[]{"maximum_status_polls","status_poll_interval_ms"}){
            for(String invalid:new String[]{"true","1.0","null"}){
                var row=configuration();row.set(field,StrictJson.parse(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
            }
            var row=configuration();row.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        for(int polls:new int[]{0,129}){var row=configuration().put("maximum_status_polls",polls);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));}
        for(int interval:new int[]{99,5001}){var row=configuration().put("status_poll_interval_ms",interval);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));}
    }
    @Test void oldModesCannotSilentlyBorrowDatePollingOrTheOneDaySequence(){
        for(int version=1;version<=7;version++){
            var row=configuration().put("schema","xar.native-owner-snapshot-config/v"+version);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        for(String forbidden:new String[]{"core_prefix_only","control_step"}){
            var row=configuration();row.put(forbidden,"resume-map");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.SAVED_FULL,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v1")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.FULL_CLOCK,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v7").put("mode","full_snapshot_clock_control").put("control_step","set-speed-1")));
    }
}
