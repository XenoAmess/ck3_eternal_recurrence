package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerCurrentSuccessionSelectionTest {
    private static ObjectNode config(String mode){var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v22").put("mode",mode).put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);n.putObject("owner_descriptor").put("path","D:/succession-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;}
    @Test void onlyTwoFixedOfficialDefaultModesAreAccepted(){
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUCCESSION_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_succession_default")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUCCESSION_CONTINUE,NativeOwnerSnapshotMain268.observationMode(config("current_succession_default_continue")));
        for(String s:new String[]{"SetPlayer","click","core_application_exit","current_frontend_menu_quit","continue_default",""})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(s)));
    }
    @Test void SourceIdsCoreWorldOwnerOrWidgetsCannotBeConfigured(){
        for(String k:new String[]{"expected_dead_character_id","expected_continue_character_id","played_character_id","world_before","expected_core","played_character_alive","map_ready","widget","selector","provider_generation","query_sequence","owner_verified","capability","action","target_character_id"})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_succession_default_continue").put(k,"forged")),k);
        for(String k:new String[]{"mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"}){var n=config("current_succession_default");n.remove(k);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
    }
    @Test void defaultContinueCannotBorrowOldMenuLivingCoreOrTargetSchema(){
        for(int v:new int[]{1,16,19,20,21})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_succession_default_continue").put("schema","xar.native-owner-snapshot-config/v"+v)));
    }
}
