package org.xar.ck3.control.g2.common;

import java.util.Objects;
import java.util.Arrays;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

public record G2Request(String requestId, Milestone milestone, G2Source source, ProjectionJson payload) {
    public G2Request {
        requireId(requestId); Objects.requireNonNull(milestone); Objects.requireNonNull(source); Objects.requireNonNull(payload);
        if (!payload.isObject()) throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "G2 payload object required");
        G2Wire.requireBodyToken(payload);
    }
    static void requireId(String requestId) {
        if (requestId == null || !requestId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"))
            throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "bounded G2 request ID required");
    }
    static void requireUnicode(String value) {
        for(int index=0;index<value.length();index++) {
            char item=value.charAt(index);
            if(Character.isHighSurrogate(item)) {
                if(++index>=value.length()||!Character.isLowSurrogate(value.charAt(index)))
                    throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST,"unpaired G2 string surrogate rejected");
            } else if(Character.isLowSurrogate(item))throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST,"unpaired G2 string surrogate rejected");
        }
    }
    @Override public boolean equals(Object other) {
        return other instanceof G2Request row && requestId.equals(row.requestId) && milestone==row.milestone
            && source.equals(row.source) && Arrays.equals(payload.bytes(),row.payload.bytes());
    }
    @Override public int hashCode() { return 31*Objects.hash(requestId,milestone,source)+Arrays.hashCode(payload.bytes()); }
}
