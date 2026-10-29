package org.xar.ck3.control.wave3.development.constructionidentity;

import java.util.Objects;
import org.xar.ck3.control.wave3.development.constructionidentity.ConstructionIdentityPolicy.WmiFields;

/** Validated declared WMI fields plus the unchanged producer bytes; no kernel qualification is implied. */
public final class OriginalProcessIdentity {
    private final WmiFields fields;
    private final byte[] originalUtf8;
    OriginalProcessIdentity(WmiFields fields, byte[] originalUtf8) {
        this.fields = Objects.requireNonNull(fields);
        this.originalUtf8 = Objects.requireNonNull(originalUtf8).clone();
    }
    public WmiFields fields() { return fields; }
    public byte[] originalUtf8() { return originalUtf8.clone(); }
}
