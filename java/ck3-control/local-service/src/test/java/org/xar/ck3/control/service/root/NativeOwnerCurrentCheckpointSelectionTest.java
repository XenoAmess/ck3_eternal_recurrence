package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerCurrentCheckpointSelectionTest {
    @TempDir Path dir;
    private com.fasterxml.jackson.databind.node.ObjectNode config(){return StrictJson.object().put("schema","xar.native-owner-snapshot-config/v14")
            .put("mode","current_core_checkpoint_save").put("checkpoint_archive_path",dir.resolve("e1.ck3").toString())
            .put("maximum_checkpoint_bytes",32L<<20).put("checkpoint_observation_attempts",5).put("checkpoint_poll_interval_ms",100);}
    @Test void onlyExplicitV14SelectsOneNarrowCheckpointWithBoundedArchive() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CORE_CHECKPOINT_SAVE,NativeOwnerSnapshotMain268.observationMode(config()));
        assertFalse(java.nio.file.Files.exists(dir.resolve("e1.ck3")));
    }
    @Test void callerCoreOldClockFieldsAndUnpairedPreviousArchiveCannotBuySaveMode() {
        var core=config();core.set("expected_core",StrictJson.object());assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(core));
        var clock=config().put("control_step","save-checkpoint");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(clock));
        var previous=config();previous.set("previous_checkpoint_source",StrictJson.object());assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(previous));
        var nulls=config().putNull("previous_checkpoint_source").putNull("previous_checkpoint_archive");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(nulls));
    }
    @Test void OtherVersionCannotBorrowSaveFieldsAndNoCurrentCoreCanComeFromConfig() {
        var other=config().put("schema","xar.native-owner-snapshot-config/v13").put("mode","scripted_widget_controls");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(other));
        var wrong=config().put("checkpoint_observation_attempts",0);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(wrong));
        var fake=config().put("connection_generation",1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(fake));
    }
}
