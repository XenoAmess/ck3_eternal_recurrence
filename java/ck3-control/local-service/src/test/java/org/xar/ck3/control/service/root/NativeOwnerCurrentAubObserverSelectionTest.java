package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Finite config DATA only; no Core, file contents or fixture execution authority is minted here. */
final class NativeOwnerCurrentAubObserverSelectionTest {
    private static ObjectNode config(String mode){
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v20").put("mode",mode)
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        c.putObject("owner_descriptor").put("path","D:/aub-observer-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    @Test void onlyExplicitFixedObserverModeUsesTheNewVersion(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_AUB_OBSERVER_FIXTURE,NativeOwnerSnapshotMain268.observationMode(config("current_aub_observer_fixture")));
        for(String mode:new String[]{"run-current-aub-observer-fixture-v1","current_frontend_menu_quit","current_core_checkpoint_save","console",""})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)));
    }
    @Test void configCannotSupplyConsoleTextPathBodyHashOwnerOrExpectedCore(){
        for(String key:new String[]{"command","content","path","sha256","inbox_filename","core_prefix_only","expected_core","date_raw","actor","owner_verified","core_control_deadline_unix_ms","capability","observer_markers_confirmed","maximum_status_polls"}) {
            var c=config("current_aub_observer_fixture").put(key,"forged");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c),key);
        }
    }
    @Test void fixedModeKeepsExactCommonFieldsAndCannotBorrowOldMenuSchema(){
        for(String key:new String[]{"owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","mode"}) {
            var c=config("current_aub_observer_fixture");c.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));
        }
        var old=config("current_aub_observer_fixture").put("schema","xar.native-owner-snapshot-config/v19");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old));
    }
}
