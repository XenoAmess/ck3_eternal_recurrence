package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing step-ID syntax is required by retained typed failure consumers; IDs remain opaque to the DLL. */
public final class RequestIds {
    private static final AtomicLong READ_SEQUENCE = new AtomicLong();
    private RequestIds() { }
    /** Pure durable identity selection. It grants neither source admission nor permission to submit. */
    public static String forCommand(ActionCommand command) {
        java.util.Objects.requireNonNull(command);
        if (command.protocolIdentity() instanceof ExplicitOriginalProtocolId explicit) return explicit.value();
        return forActionBody(ActionCodec.bodySha256(command));
    }
    public static String forActionBody(String bodySha256) {
        StrictJson.require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}"), "canonical body digest required");
        return "step-" + new BigInteger(bodySha256.substring(0, 13), 16).add(BigInteger.ONE) + "-" + bodySha256.substring(13, 25);
    }
    public static String nextRead() {
        long sequence = READ_SEQUENCE.incrementAndGet(); StrictJson.safe(sequence, 1);
        return "step-" + sequence + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
    }
}
