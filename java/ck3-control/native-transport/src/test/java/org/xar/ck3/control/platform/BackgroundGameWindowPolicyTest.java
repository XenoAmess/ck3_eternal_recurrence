package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Controlled Win32 observations only; these fixtures grant no real process, HWND or desktop authority. */
final class BackgroundGameWindowPolicyTest {
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final class Windows implements BackgroundGameWindowPolicy.Access {
        final List<String> writes=new ArrayList<>();
        long pid=42;boolean shown=true,iconic=false,topmost=true,completeMinimize=true;
        int reads;boolean changeOwner;
        @Override public List<Long> windows(){return List.of(101L);}
        @Override public long pid(long window){return changeOwner&&++reads>1?99:pid;}
        @Override public boolean visible(long window){return shown;}
        @Override public boolean minimized(long window){return iconic;}
        @Override public boolean topmost(long window){return topmost;}
        @Override public void cancelTopmost(long window){writes.add("NOTOPMOST_NOACTIVATE");topmost=false;}
        @Override public void minimizeNoActivate(long window){writes.add("MINIMIZE_7_NOACTIVATE");if(completeMinimize)iconic=true;}
    }
    @Test void aLaterShownOwnedWindowIsMinimizedWithoutAnActivationOperation()throws Exception {
        var windows=new Windows();var guards=new AtomicInteger();
        org.xar.ck3.control.nativebridge.NativeProcessGuard guard=expected->{assertEquals(GAME,expected);guards.incrementAndGet();};
        BackgroundGameWindowPolicy.enforce(GAME,guard,windows);
        assertEquals(List.of("NOTOPMOST_NOACTIVATE","MINIMIZE_7_NOACTIVATE"),windows.writes);
        assertTrue(windows.iconic);assertFalse(windows.topmost);assertTrue(guards.get()>=4);
        BackgroundGameWindowPolicy.enforce(GAME,guard,windows);assertEquals(2,windows.writes.size());
        windows.iconic=false; // A subsequent shown state; its real-world cause is not assumed.
        BackgroundGameWindowPolicy.enforce(GAME,guard,windows);
        assertEquals(List.of("NOTOPMOST_NOACTIVATE","MINIMIZE_7_NOACTIVATE","MINIMIZE_7_NOACTIVATE"),windows.writes);
    }
    @Test void foreignOrInvisibleWindowsReceiveZeroMutations()throws Exception {
        var foreign=new Windows();foreign.pid=99;
        BackgroundGameWindowPolicy.enforce(GAME,expected->assertEquals(GAME,expected),foreign);
        assertTrue(foreign.writes.isEmpty());
        var hidden=new Windows();hidden.shown=false;
        BackgroundGameWindowPolicy.enforce(GAME,expected->assertEquals(GAME,expected),hidden);
        assertTrue(hidden.writes.isEmpty());
    }
    @Test void anAsyncMinimizeRequestDoesNotSubstituteForObservedMinimizedState()throws Exception {
        var windows=new Windows();windows.topmost=false;windows.completeMinimize=false;
        assertThrows(IOException.class,()->BackgroundGameWindowPolicy.enforce(GAME,expected->{},windows));
        assertEquals(List.of("MINIMIZE_7_NOACTIVATE"),windows.writes);
        windows.iconic=true;
        BackgroundGameWindowPolicy.enforce(GAME,expected->{},windows);
        assertEquals(1,windows.writes.size());
    }
    @Test void lostBirthOrChangedHwndOwnerRejectsBeforeAnyMutation() {
        var windows=new Windows();var checks=new AtomicInteger();
        assertThrows(IOException.class,()->BackgroundGameWindowPolicy.enforce(GAME,expected->{
            if(checks.incrementAndGet()>1)throw new IOException("original birth is no longer alive");
        },windows));
        assertTrue(windows.writes.isEmpty());
        var changed=new Windows();changed.changeOwner=true;
        assertThrows(IOException.class,()->BackgroundGameWindowPolicy.enforce(GAME,expected->{},changed));
        assertTrue(changed.writes.isEmpty());
    }
}
