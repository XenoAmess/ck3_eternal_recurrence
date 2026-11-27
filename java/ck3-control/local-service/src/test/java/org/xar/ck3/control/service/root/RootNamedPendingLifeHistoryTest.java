package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.contracts.FullJsonTree;

class RootNamedPendingLifeHistoryTest {
    @Test void originalEventCoverageDoesNotHideTheCurrentInterruptedLife() throws Exception {
        try (var input = getClass().getResourceAsStream("full111-cadence-one-day-proposal.json")) {
            var row = FullJsonTree.parse(input.readAllBytes(), ActionCodec.MAX_COMMAND_BYTES);
            var command = ActionCodec.decodeCommand(FullJsonTree.encode(row.get("command"), ActionCodec.MAX_COMMAND_BYTES));
            String body = ActionCodec.bodySha256(command);
            var state = new ActionState.Unknown(Optional.empty(), Optional.empty(), "test membership", List.of());
            var recorded = new ActionReceipt(1, 80, command, body, state);
            var pending = new ActionReceipt(1, 142, command, body, state);
            var history = new ArrayList<>(List.of(
                    new DriverBootstrap.ExternalSavedActionHistory(recorded, true, Optional.empty())));
            RootApplicationAssembly.Core.admitUnrecordedNamedHistory(history, Optional.of(recorded), Optional.of(pending));
            RootApplicationAssembly.Core.admitUnrecordedNamedHistory(history, Optional.of(recorded), Optional.of(pending));
            assertEquals(List.of(recorded, pending), history.stream().map(DriverBootstrap.ExternalSavedActionHistory::receipt).toList());
            assertTrue(history.getLast().cyclePending());
            assertTrue(history.getLast().coverage().isEmpty());
        }
    }
}
