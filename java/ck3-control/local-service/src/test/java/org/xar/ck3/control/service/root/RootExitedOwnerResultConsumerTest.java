package org.xar.ck3.control.service.root;

import org.junit.jupiter.api.Test;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

/** DATA-only callbacks exercise the real cleanup consumer; no Game or Retained is fabricated. */
final class RootExitedOwnerResultConsumerTest {
    @Test void successfulOwnerResultCompletesAfterBusinessAndTransportExactlyOnce()throws Exception {
        var calls=new ArrayList<String>();
        RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(
                ()->calls.add("business"),()->calls.add("transport"),()->{
                    calls.add("owner");RootOrdinaryRuntimeAssembly.requireOwnerTerminalSuccess(0);
                });
        assertEquals(List.of("business","transport","owner"),calls);
    }
    @Test void nonzeroResultIsVisibleAfterTheActualCleanupSequence() {
        for(int result:new int[]{1,-7}) {
            var calls=new ArrayList<String>();
            IOException failure=assertThrows(IOException.class,()->
                    RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(
                            ()->calls.add("business"),()->calls.add("transport"),()->{
                                calls.add("owner");RootOrdinaryRuntimeAssembly.requireOwnerTerminalSuccess(result);
                            }));
            assertEquals("original Saved owner terminal returned failure "+result,failure.getMessage());
            assertEquals(List.of("business","transport","owner"),calls);
            assertEquals(0,failure.getSuppressed().length);
        }
    }
    @Test void businessFailureRemainsPrimaryAndTerminalFailureFollowsTransportFailure() {
        var calls=new ArrayList<String>();
        var business=new IOException("original business failure");
        var transport=new IOException("original transport failure");
        IOException failure=assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(
                ()->{calls.add("business");throw business;},
                ()->{calls.add("transport");throw transport;},
                ()->{calls.add("owner");RootOrdinaryRuntimeAssembly.requireOwnerTerminalSuccess(1);}));
        assertSame(business,failure);
        assertEquals(List.of("business","transport","owner"),calls);
        List<Throwable> suppressed=Arrays.asList(failure.getSuppressed());
        assertEquals(2,suppressed.size());assertSame(transport,suppressed.get(0));
        assertInstanceOf(IOException.class,suppressed.get(1));
        assertEquals("original Saved owner terminal returned failure 1",suppressed.get(1).getMessage());
    }
}
