package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure admission against the actual canonical action chain; no separate nonce registry exists. */
public final class ProtocolIdentityAdmission {
    private ProtocolIdentityAdmission() { }
    public static void requireUnique(List<ActionReceipt> canonical, ActionCommand proposed) {
        Objects.requireNonNull(proposed); String id = RequestIds.forCommand(proposed);
        String body = ActionCodec.bodySha256(proposed);
        for (ActionReceipt previous : List.copyOf(canonical)) {
            ActionCommand original = previous.command();
            if (!original.origin().machineId().equals(proposed.origin().machineId())
                    || !original.origin().game().equals(proposed.origin().game())) continue;
            if (RequestIds.forCommand(original).equals(id))
                StrictJson.require(original.actionId().equals(proposed.actionId()) && previous.bodySha256().equals(body)
                        && java.util.Arrays.equals(ActionCodec.encodeCommand(original), ActionCodec.encodeCommand(proposed)),
                        "original native protocol request ID is already bound to another complete canonical command");
        }
    }
}
