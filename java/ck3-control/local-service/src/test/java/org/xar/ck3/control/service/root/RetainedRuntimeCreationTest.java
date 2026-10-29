package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

/** Executes the same guard used around actual capability-observer/catalog construction.
 * These software tests do not produce a Game, Driver adoption, SEM or runtime qualification. */
final class RetainedRuntimeCreationTest {
    @Test void successfulProducerIsRetainedAndTheAlternateProducerIsNeverInvoked() throws Exception {
        var creation = new RetainedRuntimeCreation<Object>();
        Object original = new Object(); AtomicInteger calls = new AtomicInteger();
        assertSame(original, creation.obtain(() -> { calls.incrementAndGet(); return original; }));
        assertSame(original, creation.obtain(() -> { fail("another runtime must not be constructed"); return new Object(); }));
        assertEquals(1, calls.get());
    }
    @Test void checkedFailureAfterBindingCannotReplayTheActualCreationCallback() {
        var creation = new RetainedRuntimeCreation<Object>(); AtomicInteger bindings = new AtomicInteger();
        IOException original = new IOException("controlled failure after original observer binding entered");
        assertSame(original, assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); throw original; })));
        assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); }));
        assertEquals(1, bindings.get());
    }
    @Test void runtimeFailureCannotBeConvertedIntoAnotherRegistrationAttempt() {
        var creation = new RetainedRuntimeCreation<Object>(); AtomicInteger bindings = new AtomicInteger();
        assertThrows(IllegalStateException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); throw new IllegalStateException("entered"); }));
        assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); }));
        assertEquals(1, bindings.get());
    }
    @Test void errorLeavesTheOriginalAttemptUnknownAndRejectsAnySecondCallback() {
        var creation = new RetainedRuntimeCreation<Object>(); AtomicInteger bindings = new AtomicInteger();
        assertThrows(AssertionError.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); throw new AssertionError("controlled original source error"); }));
        assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); }));
        assertEquals(1, bindings.get());
    }
    @Test void nullResultAfterEntryDoesNotResetTheAttempt() {
        var creation = new RetainedRuntimeCreation<Object>(); AtomicInteger bindings = new AtomicInteger();
        assertThrows(NullPointerException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return null; }));
        assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); }));
        assertEquals(1, bindings.get());
    }
    @Test void recursiveCreationIsRejectedBeforeTheInnerProducerCanBind() {
        var creation = new RetainedRuntimeCreation<Object>(); AtomicInteger bindings = new AtomicInteger();
        assertThrows(IOException.class, () -> creation.obtain(() -> {
            bindings.incrementAndGet();
            return creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); });
        }));
        assertThrows(IOException.class, () -> creation.obtain(() -> { bindings.incrementAndGet(); return new Object(); }));
        assertEquals(1, bindings.get());
    }
}
