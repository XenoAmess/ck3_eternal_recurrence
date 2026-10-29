package org.xar.ck3.control.g2.common;

import java.util.Objects;
import java.util.Arrays;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Pure domain result. A successful response is neither action submission nor a material postcondition. */
public record G2Response(String requestId, Milestone milestone, G2Source source, ProjectionJson result) {
    public G2Response {
        G2Request.requireId(requestId); Objects.requireNonNull(milestone); Objects.requireNonNull(source); Objects.requireNonNull(result);
        G2Wire.requireBodyToken(result);
    }
    @Override public boolean equals(Object other) {
        return other instanceof G2Response row && requestId.equals(row.requestId) && milestone==row.milestone
            && source.equals(row.source) && Arrays.equals(result.bytes(),row.result.bytes());
    }
    @Override public int hashCode() { return 31*Objects.hash(requestId,milestone,source)+Arrays.hashCode(result.bytes()); }
}
