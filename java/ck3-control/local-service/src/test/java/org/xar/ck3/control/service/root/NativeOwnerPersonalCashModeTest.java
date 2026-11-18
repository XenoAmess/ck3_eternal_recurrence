package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeOwnerPersonalCashModeTest {
    @Test void explicitPersonalCashModeIsReadOnlyAndSeparateFromSnapshotAndControl() {
        var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v9").put("mode","personal_cash_current");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.PERSONAL_CASH,NativeOwnerSnapshotMain268.observationMode(config));
        for(String field:new String[]{"core_prefix_only","control_step","maximum_status_polls","status_poll_interval_ms"}){
            var invalid=config.deepCopy();invalid.put(field,"unexpected");
            assertThrows(ContractViolationException.class,()->NativeOwnerSnapshotMain268.observationMode(invalid));
        }
    }
    @Test void PersonalCashModeCannotEnterAnotherVersionedOwnerMode() {
        var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v9").put("mode","personal_gold_frame");
        assertThrows(ContractViolationException.class,()->NativeOwnerSnapshotMain268.observationMode(config));
        config.put("mode","personal_cash_current").put("schema","xar.native-owner-snapshot-config/v5");
        assertThrows(ContractViolationException.class,()->NativeOwnerSnapshotMain268.observationMode(config));
    }
}
