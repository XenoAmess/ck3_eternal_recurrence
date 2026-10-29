package org.xar.ck3.control.wave2.events.mandatoryreceipt;

import static org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptModel.*;

import java.util.Objects;
import java.util.Optional;

/** Pure capture_after body production: ACK and disappearance of that exact original instance remain separate. */
public final class MandatoryReceiptProducer implements MandatoryReceiptPort {
    @Override public AfterResponse produce(Input input) {
        Objects.requireNonNull(input); Ticket ticket = input.ticket(); Reply reply = input.reply();
        boolean advanced = reply.nativeCommandAcknowledged() && reply.postcondition().filter(post -> post.verified()
                && post.oldWindowId().equals(Optional.of(ticket.windowId()))
                && post.oldInstanceId().equals(Optional.of(ticket.instanceId()))
                && post.selectedChoiceId().equals(Optional.of(ticket.choiceId())) && post.oldWindowNoLongerBlocking()).isPresent();
        return new AfterResponse(ticket, reply.nativeCommandAcknowledged(), advanced, reply.originalResult(), input.error(), input.capturedAtUtc());
    }
}
