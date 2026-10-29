package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;

/** Exercises the real Main lifetime gate only; this grants no Game or native acceptance. */
public final class RootStartupInputsLifetimeTest {
    @Test public void acceptedCloseStopsInputProductionBeforeCleanupAndNeverReplaysCleanup() throws Exception {
        var cleanupCalls=new AtomicInteger();
        var original=new AtomicReference<RootStartupInputsProducer.Lifetime>();
        var lifetime=new RootStartupInputsProducer.Lifetime(()->{
            cleanupCalls.incrementAndGet();
            var refused=assertThrows(IOException.class,original.get()::requireOpen);
            assertEquals("original Root startup lifetime is CLOSING; no new retained inputs",refused.getMessage());
            assertThrows(IOException.class,original.get()::close);
        });
        original.set(lifetime);
        lifetime.requireOpen();
        lifetime.close();
        var refused=assertThrows(IOException.class,lifetime::requireOpen);
        assertEquals("original Root startup lifetime is CLOSED; no new retained inputs",refused.getMessage());
        lifetime.close();
        lifetime.finish(null);
        assertEquals(1,cleanupCalls.get());
    }

    @Test public void failedCleanupRetainsItsOriginalFailureAndClosesInputsWithoutRetry() throws Exception {
        var cleanupCalls=new AtomicInteger();
        var originalFailure=new IOException("actual original cleanup unresolved");
        var lifetime=new RootStartupInputsProducer.Lifetime(()->{
            cleanupCalls.incrementAndGet();
            throw originalFailure;
        });
        assertSame(originalFailure,assertThrows(IOException.class,lifetime::close));
        assertSame(originalFailure,assertThrows(IOException.class,lifetime::close));
        assertThrows(IOException.class,lifetime::requireOpen);
        var consumerFailure=new IOException("actual admitted consumer failed");
        lifetime.finish(consumerFailure);
        assertArrayEquals(new Throwable[]{originalFailure},consumerFailure.getSuppressed());
        assertEquals(1,cleanupCalls.get());
    }
}
