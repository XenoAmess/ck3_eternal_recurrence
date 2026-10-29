package org.xar.ck3.control.wave3.development.constructionquery;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.StrictJson;

/** Compare the complete finalized quote while allowing only a new read identity and advancing probe counter. */
public final class ConstructionQuoteIdentity {
    private ConstructionQuoteIdentity() { }
    public static boolean same(byte[] planned, byte[] current) {
        ObjectNode before = object(planned), after = object(current);
        StrictJson.text(before.get("native_query_request_id")); StrictJson.text(after.get("native_query_request_id"));
        BigInteger first = StrictJson.integer(before.get("proof_epoch"), BigInteger.ONE, StrictJson.UINT64_MAX);
        BigInteger last = StrictJson.integer(after.get("proof_epoch"), BigInteger.ONE, StrictJson.UINT64_MAX);
        StrictJson.require(last.compareTo(first) >= 0, "fresh construction proof epoch regressed");
        // Keep every candidate, native world, source and extension field in the comparison.
        before.remove("native_query_request_id"); after.remove("native_query_request_id");
        before.remove("proof_epoch"); after.remove("proof_epoch");
        return before.equals(after);
    }
    private static ObjectNode object(byte[] raw) {
        var node = StrictJson.parse(raw, ConstructionQueryCodec.MAX_BYTES);
        StrictJson.require(node instanceof ObjectNode, "complete finalized construction quote required");
        return ((ObjectNode) node).deepCopy();
    }
}
