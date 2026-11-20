package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerLiteralNavigationSelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config(String action){return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v15").put("mode","current_gui_navigation").put("navigation_action",action);}
    @Test void onlyTwoClosedLiteralActionsUseTheNewExplicitMode(){
        for(String action:new String[]{"OPEN_FAITH","OPEN_RITE_EDITOR"})assertEquals(NativeOwnerSnapshotMain268.ObservationMode.GUI_NAVIGATION_V2,NativeOwnerSnapshotMain268.observationMode(config(action)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("custom-runtime-name")));
    }
    @Test void freeRootPathOrdinalCoreAndRiteSourcesAreRejected(){
        for(String field:new String[]{"window_name","widget_id","query_generation","expected_source_rite_id","expected_core","connection_generation","checkpoint_archive_path"}){
            var row=config("OPEN_FAITH").put(field,"forged");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
    }
    @Test void oldReadonlyModeDoesNotGainLayerActivation(){
        for(String root:new String[]{"hud_layer","windows_layer"}){
            var row=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v13").put("mode","scripted_widget_controls").put("window_name",root);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
        var old=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v13").put("mode","scripted_widget_controls").put("window_name","faith_window");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.GUI_CONTROLS_V2,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("navigation_action","OPEN_FAITH")));
    }
}
