package org.xar.ck3.control.wave2.planning.scoretarget;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;

/** Presence and token type remain distinct even when the legacy proof rejects both. */
public sealed interface ScalarField permits ScalarField.Missing, ScalarField.NullValue,
        ScalarField.Text, ScalarField.Other {
    /** Shared saved-scalar integer semantics; no Boolean/fraction coercion. */
    default Optional<BigInteger> integer() {
        return this instanceof Text text ? PlayerWarDefence.savedInteger(text.value()) : Optional.empty();
    }
    record Missing() implements ScalarField { }
    record NullValue() implements ScalarField { }
    record Text(String value) implements ScalarField {
        public Text { Objects.requireNonNull(value, "text required"); }
    }
    record Other(TokenKind kind) implements ScalarField {
        public Other { Objects.requireNonNull(kind, "token kind required"); }
    }
    enum TokenKind { BOOLEAN, INTEGER, FRACTIONAL, ARRAY, OBJECT }
}
