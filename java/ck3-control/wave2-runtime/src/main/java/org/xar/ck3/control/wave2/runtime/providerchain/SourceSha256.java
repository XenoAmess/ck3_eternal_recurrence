package org.xar.ck3.control.wave2.runtime.providerchain;

import org.xar.ck3.control.contracts.StrictJson;

/** A lowercase source-content digest, never a source-custody token. */
public record SourceSha256(String value) {
    public SourceSha256 {
        StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "exact source SHA-256 required");
    }
}
