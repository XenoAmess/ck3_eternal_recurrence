package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerRiteDoctrineSelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config(String action){return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v16").put("mode","current_rite_doctrine").put("rite_action",action).put("expected_source_rite_id",152);}
    @Test void fixedFourActionsRequireTheExplicitCurrentMode(){
        for(String action:new String[]{"query","open_dynastic_category","select_dynastic","confirm_edit"})assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_DOCTRINE,NativeOwnerSnapshotMain268.observationMode(config(action)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("arbitrary-selector")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("query").put("mode","current_gui_navigation")));
    }
    @Test void configuredCoreLeasePathsAndOtherModesCannotSupplyAuthority(){
        for(String field:new String[]{"window_name","expected_core","connection_generation","provider_generation","query_sequence","widget_id","navigation_action","control_step","checkpoint_archive_path","core_prefix_only"})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("select_dynastic").put(field,"forged")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("query").put("expected_source_rite_id",true)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("query").put("expected_source_rite_id",4294967295L)));
    }
    @Test void oldReadonlyAndLiteralModesDoNotGainRiteEffects(){
        var old=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v13").put("mode","scripted_widget_controls").put("window_name","faith_window");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.GUI_CONTROLS_V2,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("rite_action","confirm_edit")));
        var nav=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v15").put("mode","current_gui_navigation").put("navigation_action","OPEN_FAITH").put("rite_action","select_dynastic");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(nav));
    }
}
