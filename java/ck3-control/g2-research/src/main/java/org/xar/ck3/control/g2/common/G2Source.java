package org.xar.ck3.control.g2.common;

import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;

/** Caller provenance only. This record never opens a path or grants native, file, action or writer access. */
public record G2Source(String machineId, String observedAtUtc, String exactBuild, ExactRef sourceRef) {
    public G2Source {
        if (machineId == null || !machineId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"))
            throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "explicit bounded source machine required");
        if (exactBuild == null || exactBuild.isBlank() || exactBuild.length() > 128)
            throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "bounded exact build required");
        Objects.requireNonNull(sourceRef, "sourceRef");
        G2Request.requireUnicode(exactBuild); G2Request.requireUnicode(sourceRef.path());
        try {
            if (observedAtUtc == null || !observedAtUtc.endsWith("Z")) throw new DateTimeParseException("UTC required", "", 0);
            Instant.parse(observedAtUtc);
        } catch (DateTimeParseException error) {
            throw new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, "explicit UTC observation instant required");
        }
    }
}
