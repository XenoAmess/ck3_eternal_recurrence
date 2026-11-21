package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerCurrentDjcQuerySelectionTest {
    private static ObjectNode config(){
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v21").put("mode","current_djc_target_war_query").put("target_character_id",39957)
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/djc-query-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    @Test void onlyExplicitReadonlyTargetModeAndSignedTargetAreAccepted(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_TARGET_QUERY,NativeOwnerSnapshotMain268.observationMode(config()));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_TARGET_QUERY,NativeOwnerSnapshotMain268.observationMode(config().put("target_character_id",-16777215)));
        for(String s:new String[]{"declare-war","current_aub_observer_fixture","current_frontend_menu_quit",""})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",s)));
        for(long n:new long[]{-1,2147483648L,-2147483649L})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("target_character_id",n)));
    }
    @Test void targetConfigCannotSupplyCoreOwnerPermissionCostWarOrSelector(){
        for(String k:new String[]{"expected_core","date_raw","actor","provider_generation","query_sequence","ordinary_can_declare_war","total_debit","war_id","step","arguments","capability","casus_belli","owner_verified","core_control_deadline_unix_ms"})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(k,"forged")),k);
        for(String k:new String[]{"owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id","mode"}){var n=config();n.remove(k);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
    }
    @Test void newTargetCannotBeBorrowedByAnyOlderMode(){
        for(int version:new int[]{1,11,16,17,18,19,20})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema","xar.native-owner-snapshot-config/v"+version)));
    }
}
