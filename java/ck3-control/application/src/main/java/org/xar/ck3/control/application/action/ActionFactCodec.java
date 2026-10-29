package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** The existing producer and new planning wire use the same ExternalFact field contract. */
public final class ActionFactCodec {
    private ActionFactCodec() { }
    public static ObjectNode toJson(ExternalFact fact) { return ProposalLifecycleCodec.fact(fact); }
    public static ExternalFact fromJson(JsonNode value) { return ProposalLifecycleCodec.decodeFact(value); }
    /** Explicit historical lane only: original v1 shape, with SEND_CONFIRMED refused. */
    public static ExternalFact fromHistoricalV1Json(JsonNode value) { return ProposalLifecycleCodec.decodeHistoricalFactV1(value); }
}
