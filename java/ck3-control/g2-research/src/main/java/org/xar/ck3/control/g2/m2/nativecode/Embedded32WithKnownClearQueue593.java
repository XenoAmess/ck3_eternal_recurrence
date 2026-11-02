package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;

/** Owner integration scaffold: mature complete callees, no copied algorithms. */
public final class Embedded32WithKnownClearQueue593 {
    private Embedded32WithKnownClearQueue593() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,Embedded32Copy581Api.Calls fallback,
            EmbeddedElements578Api.Calls elements,EmbeddedClear587Api.Calls clear,
            EmbeddedQueue591Api.Calls queue) {
        var bound=bindKnown(input,memory,fallback,elements,clear,queue);
        return Embedded32FullState3727180.execute(input,memory,bound);
    }
    static Embedded32Copy581Api.Calls bindKnown(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,Embedded32Copy581Api.Calls fallback,
            EmbeddedElements578Api.Calls elements,EmbeddedClear587Api.Calls clear,
            EmbeddedQueue591Api.Calls queue) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(elements);
        Objects.requireNonNull(clear);
        Objects.requireNonNull(queue);

        // 1. Bind clear into elements: creates a 578 Calls that intercepts 0x37282E1 -> 0x889780
        //    and delegates to EmbeddedClearFullState889780, passing through other calls to 'elements'.
        EmbeddedElements578Api.Calls boundElements = EmbeddedElementsWithKnownClear588.bindClear(
            input, memory, elements, clear);

        // 2. Bind elements into fallback: creates a 581 Calls that intercepts 0x37272F0 -> 0x37282B0
        //    and delegates to EmbeddedElementsFullState37282B0 (using boundElements), passing through
        //    other calls to 'fallback'.
        Embedded32Copy581Api.Calls boundElementsInFallback = Embedded32WithKnownElements584.bindElements(
            input, memory, fallback, boundElements);

        // 3. Bind queue into the result: creates a 581 Calls that intercepts 0x37272F8 -> 0x3727EC0
        //    and delegates to EmbeddedQueueFullState3727EC0 (using 'queue'), passing through
        //    other calls to 'boundElementsInFallback'.
        Embedded32Copy581Api.Calls boundQueue = Embedded32WithKnownQueue592.bindQueue(
            input, memory, boundElementsInFallback, queue);

        return boundQueue;
    }
}
