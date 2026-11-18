package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerActorFoundationModeTest {
    @Test void actorFoundationIsAnExplicitReadOnlyV6ModeAndPreservesEarlierGoldMode(){
        var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v6").put("mode","actor_foundation_frame");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.ACTOR_FOUNDATION,NativeOwnerSnapshotMain268.observationMode(config));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.PERSONAL_GOLD,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v5").put("mode","personal_gold_frame")));
    }
    @Test void foundationCannotBorrowOlderModeSchemasOrControlFields(){
        for(int version=1;version<=5;version++){
            var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v"+version).put("mode","actor_foundation_frame");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config));
        }
        for(String field:new String[]{"core_prefix_only","control_step"}){
            var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v6").put("mode","actor_foundation_frame");
            config.put(field,"incompatible");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v6").put("mode","core_clock_control")));
    }
}
