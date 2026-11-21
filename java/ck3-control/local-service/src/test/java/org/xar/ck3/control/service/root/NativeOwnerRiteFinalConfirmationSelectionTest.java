package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Config selection only. The actual two callbacks and persistence require independent native evidence. */
final class NativeOwnerRiteFinalConfirmationSelectionTest {
    private static ObjectNode configuration(){
        return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v18")
                .put("mode","current_rite_final_confirmation").put("expected_source_rite_id",152)
                .put("maximum_confirmation_polls",16).put("status_poll_interval_ms",500);
    }
    private static ObjectNode originalRite(String action){
        return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v16")
                .put("mode","current_rite_doctrine").put("rite_action",action).put("expected_source_rite_id",152);
    }
    @Test void onlyExplicitFixedFinalModeSelectsTheNewSequence(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_FINAL_CONFIRMATION,NativeOwnerSnapshotMain268.observationMode(configuration()));
        for(String mode:new String[]{"current_rite_doctrine","current_date_advance","confirm_edit","accept_final_confirmation",""})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("mode",mode)));
    }
    @Test void actualSourceRiteExpectationRetainsItsStrictIntegerContract(){
        for(long value:new long[]{0,152,4294967294L})
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_FINAL_CONFIRMATION,NativeOwnerSnapshotMain268.observationMode(configuration().put("expected_source_rite_id",value)));
        for(long value:new long[]{-1,4294967295L,Long.MAX_VALUE})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("expected_source_rite_id",value)));
        var missing=configuration();missing.remove("expected_source_rite_id");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
        for(String token:new String[]{"true","152.0","null","\"152\""}){
            var row=configuration();row.set("expected_source_rite_id",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
        }
    }
    @Test void finalModeCannotAcceptActionsTargetsPathsOrCallerAuthority(){
        for(String field:new String[]{"rite_action","expected_core","connection_generation","provider_generation","query_sequence","claim_sequence",
                "widget_id","window_name","root","child_path","target_key","group_key","force","can_confirm","deadline_unix_ms","operation_id",
                "navigation_action","control_step","core_prefix_only","checkpoint_archive_path","maximum_status_polls","unknown"}){
            var row=configuration().put(field,"forged");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row),field);
        }
    }
    @Test void originalV16KeepsExactlyItsFourActionsAndNeverGainsFinalAcceptance(){
        for(String action:new String[]{"query","open_dynastic_category","select_dynastic","confirm_edit"})
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_DOCTRINE,NativeOwnerSnapshotMain268.observationMode(originalRite(action)));
        for(String action:new String[]{"query_final_confirmation","accept_final_confirmation"})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(originalRite(action)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("rite_action","confirm_edit")));
    }
    @Test void oldReadOnlyNavigationAndDateModesCannotSelectTheFinalSequence(){
        var readOnly=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v13").put("mode","scripted_widget_controls").put("window_name","faith_window");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.GUI_CONTROLS_V2,NativeOwnerSnapshotMain268.observationMode(readOnly));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(readOnly.deepCopy().put("rite_action","accept_final_confirmation")));
        var nav=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v15").put("mode","current_gui_navigation").put("navigation_action","OPEN_FAITH");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.GUI_NAVIGATION_V2,NativeOwnerSnapshotMain268.observationMode(nav));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(nav.put("mode","current_rite_final_confirmation")));
    }
    @Test void currentV17AndLegacyV8DatePoliciesRemainSeparate(){
        var current=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v17").put("mode","current_date_advance")
                .put("maximum_status_polls",64).put("status_poll_interval_ms",500);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(current));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(current.deepCopy().put("mode","current_rite_final_confirmation")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(current.deepCopy().put("rite_action","accept_final_confirmation")));
        var legacy=current.deepCopy().put("schema","xar.native-owner-snapshot-config/v8").put("mode","date_sentinel_advance_one_day");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.DATE_ADVANCE,NativeOwnerSnapshotMain268.observationMode(legacy));
    }
    @Test void readonlyConfirmationWaitingHasFiniteTypedLimitsAndCannotLeakIntoOlderModes(){
        for(String field:new String[]{"maximum_confirmation_polls","status_poll_interval_ms"}){
            var missing=configuration();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
            for(String token:new String[]{"true","1.0","null","\"16\""}){
                var row=configuration();row.set(field,StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(row));
            }
        }
        for(int polls:new int[]{0,65})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("maximum_confirmation_polls",polls)));
        for(int interval:new int[]{99,5001})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(configuration().put("status_poll_interval_ms",interval)));
        for(int polls:new int[]{1,64})assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_FINAL_CONFIRMATION,
                NativeOwnerSnapshotMain268.observationMode(configuration().put("maximum_confirmation_polls",polls)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(originalRite("query").put("maximum_confirmation_polls",16)));
        var current=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v17").put("mode","current_date_advance")
                .put("maximum_status_polls",64).put("status_poll_interval_ms",500).put("maximum_confirmation_polls",16);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(current));
    }
}
