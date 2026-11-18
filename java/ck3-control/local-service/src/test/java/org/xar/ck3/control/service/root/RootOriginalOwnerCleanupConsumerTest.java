package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameLifecycle.TerminalKind;
import static org.junit.jupiter.api.Assertions.*;

/** Cleanup/result DATA only: no Started, CreatorOwnership, CreatorExit or Job proof is fabricated. */
final class RootOriginalOwnerCleanupConsumerTest {
    @Test void completedOwnerPrecedesAllIndependentReleases()throws Exception {
        var order=new ArrayList<String>();
        RootOrdinaryWorkerMain.finishOwnerCleanup(null,()->order.add("owner"),()->order.add("resources"),()->order.add("loaded"));
        assertEquals(List.of("owner","resources","loaded"),order);
    }
    @Test void originalOwnerFailureCannotSkipRemainingReleases() {
        var order=new ArrayList<String>();var owner=new IOException("original owner publication failure");
        var resource=new IOException("resource cleanup failure");var loaded=new IOException("loaded cleanup failure");
        var result=assertThrows(IOException.class,()->RootOrdinaryWorkerMain.finishOwnerCleanup(null,
                ()->{order.add("owner");throw owner;},()->{order.add("resources");throw resource;},
                ()->{order.add("loaded");throw loaded;}));
        assertSame(owner,result);assertEquals(List.of("owner","resources","loaded"),order);
        assertArrayEquals(new Throwable[]{resource,loaded},result.getSuppressed());
    }
    @Test void existingPrimaryKeepsFatalCleanupAndAllLaterReleases()throws Exception {
        var primary=new AssertionError("original business fatal error");var owner=new IOException("owner observer failed");
        var resource=new AssertionError("fatal resource cleanup");var order=new ArrayList<String>();
        RootOrdinaryWorkerMain.finishOwnerCleanup(primary,()->{order.add("owner");throw owner;},
                ()->{order.add("resources");throw resource;},()->order.add("loaded"));
        assertEquals(List.of("owner","resources","loaded"),order);
        assertArrayEquals(new Throwable[]{owner,resource},primary.getSuppressed());
        var fatal=new AssertionError("owner fatal error");
        assertSame(fatal,assertThrows(AssertionError.class,()->RootOrdinaryWorkerMain.finishOwnerCleanup(null,
                ()->{throw fatal;},()->order.add("second resources"),()->order.add("second loaded"))));
        assertEquals(List.of("owner","resources","loaded","second resources","second loaded"),order);
    }
    @Test void interruptionRemainsVisibleAfterBothReleases() {
        boolean prior=Thread.interrupted();var interrupted=new InterruptedException("original owner observer interrupted");
        try {
            var order=new ArrayList<String>();
            assertSame(interrupted,assertThrows(InterruptedException.class,()->RootOrdinaryWorkerMain.finishOwnerCleanup(null,
                    ()->{throw interrupted;},()->order.add("resources"),()->order.add("loaded"))));
            assertTrue(Thread.currentThread().isInterrupted());assertEquals(List.of("resources","loaded"),order);
        }finally{Thread.interrupted();if(prior)Thread.currentThread().interrupt();}
    }
    @Test void actualTerminalDataDoesNotEraseUnknownUnclosedOrNonzeroFailures()throws Exception {
        RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(0,TerminalKind.NATURAL_EXIT,true,List.of());
        RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(125,TerminalKind.OWNER_STOP,true,List.of());
        var original=new IOException("original owner read failure");
        assertSame(original,assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(
                0,TerminalKind.UNKNOWN,false,List.of(original))));
        assertEquals(2,original.getSuppressed().length);
        assertTrue(original.getSuppressed()[0].getMessage().contains("UNKNOWN"));
        assertTrue(original.getSuppressed()[1].getMessage().contains("unclosed"));
        assertTrue(assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(
                259,TerminalKind.NATURAL_EXIT,true,List.of())).getMessage().contains("failure 259"));
        var fatal=new AssertionError("actual original cleanup failure");
        assertSame(fatal,assertThrows(AssertionError.class,()->RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(
                0,TerminalKind.NATURAL_EXIT,true,List.of(fatal))));
        assertThrows(NullPointerException.class,()->RootOrdinaryRuntimeAssembly.requireCreatorOwnerResult(0,null,true,List.of()));
    }
}
