package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedInit560;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedVector574;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownFourEmbedded583;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Copy581Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32WithKnownElements584;

/**
 * Tiny composition for the 233-byte context constructor 373ACF0.
 * Uses the existing 583 composition (which handles init, elements, vector, and copy32)
 * but replaces the opaque copy32 calls with the 584 composition that resolves the
 * internal 394->322 call site (0x37272F0 -> 0x37282B0) using the known elements implementation.
 */
public final class ContextConstructorWithKnownNestedElements585 {
    private ContextConstructorWithKnownNestedElements585() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls fallback,
            ContextConstructorWithKnownEmbeddedInit560.EmbeddedCalls embedded,
            ContextConstructorWithKnownEmbeddedVector574.VectorCalls vector,
            EmbeddedElements578Api.Calls elements,
            Embedded32Copy581Api.Calls copy32) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(embedded);
        Objects.requireNonNull(vector);
        Objects.requireNonNull(elements);
        Objects.requireNonNull(copy32);

        // Create the bound copy32 calls that intercepts the internal 394->322 call
        // using the existing 584 bindElements helper.
        Embedded32Copy581Api.Calls boundCopy32 = Embedded32WithKnownElements584.bindElements(
            input, memory, copy32, elements
        );

        // Execute the mature 583 composition (which handles init, elements, vector, and copy32)
        // using the bound copy32 calls instead of the original opaque copy32 calls.
        return ContextConstructorWithKnownFourEmbedded583.execute(
            input, memory, fallback, embedded, vector, elements, boundCopy32
        );
    }
}