package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** NoGame config DATA: no owner or menu occurrence is issued by this selector. */
final class NativeOwnerCurrentFrontendMenuSelectionTest {
    private static ObjectNode config(String mode){
        var row=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v19").put("mode",mode)
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        row.putObject("owner_descriptor").put("path","D:/current-menu-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return row;
    }
    @Test void explicitVersionSelectsOnlyTheTwoFixedCurrentMenuModes(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FRONTEND_MENU,NativeOwnerSnapshotMain268.observationMode(config("current_frontend_menu")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FRONTEND_MENU_QUIT,NativeOwnerSnapshotMain268.observationMode(config("current_frontend_menu_quit")));
        for(String value:new String[]{"menu_core_prefix","quit_menu","current_rite_doctrine","current_date_advance","start_robert_1066","continue_last",""})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(value)));
    }
    @Test void configCannotSupplyCoreOwnerRouteLeaseActorTargetOrArbitraryAction(){
        for(String field:new String[]{"core_prefix_only","expected_core","date_raw","actor","history_id","world_core","route","menu_action","control_step","connection_generation","provider_generation","query_sequence","no_world","owner_verified","root","address","widget_id","ordinal","target","deadline_unix_ms","maximum_status_polls","unknown"}){
            var row=config("current_frontend_menu_quit").put(field,"forged");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row),field);
        }
    }
    @Test void fixedModeKeepsItsExplicitOwnerAndFiniteCommonInputShape(){
        for(String field:new String[]{"owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","mode"}){
            var row=config("current_frontend_menu");row.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
    }
    @Test void oldWorldCoreAndDateModesDoNotBecomeTheNewNoWorldMenuRoute(){
        var legacy=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v2").put("mode","menu_core_prefix");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.MENU_CORE,NativeOwnerSnapshotMain268.observationMode(legacy));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(legacy.put("mode","current_frontend_menu_quit")));
        var date=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v17").put("mode","current_date_advance").put("maximum_status_polls",16).put("status_poll_interval_ms",500);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(date));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(date.put("mode","current_frontend_menu_quit")));
    }
}
