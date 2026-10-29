package org.xar.ck3.control.g2.common;

import java.util.Objects;

public final class G2Exception extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    private final G2HttpError.Code code;
    public G2Exception(G2HttpError.Code code, String message) { super(message); this.code = Objects.requireNonNull(code); }
    public G2HttpError.Code code() { return code; }
}
