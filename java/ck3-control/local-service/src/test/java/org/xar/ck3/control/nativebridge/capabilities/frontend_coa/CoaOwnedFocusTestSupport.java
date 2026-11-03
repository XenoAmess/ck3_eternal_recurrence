package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinDef.POINT;
import com.sun.jna.platform.win32.WinDef.RECT;
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.GameGeneration;

/** Software IO only: calls the same package-private focus method as the real Managed wrapper.
 * No ManagedGameSession, permission, desktop, Native.load, Robot, capture or input is created. */
public final class CoaOwnedFocusTestSupport {
    private CoaOwnedFocusTestSupport() { }

    public enum Script { FOREGROUND, DIRECT, REMAINS_FOREIGN, WINDOW_DRIFT, AMBIGUOUS, GUARD_AFTER_WRITE }

    public record Harness(CoaWindowCapture capture, AtomicInteger show, AtomicInteger bring,
            AtomicInteger foreground, AtomicInteger captures, AtomicInteger guards) {
        public int writes() { return show.get() + bring.get() + foreground.get(); }
    }

    public static Harness create(GameGeneration game, Script script, Clock clock) {
        var show = new AtomicInteger(); var bring = new AtomicInteger(); var foreground = new AtomicInteger();
        var captures = new AtomicInteger(); var guards = new AtomicInteger();
        var windows = new Transcript(game, script, show, bring, foreground);
        var capture = new CoaWindowCapture(game, expected -> {
            guards.incrementAndGet();
            if (!game.equals(expected)) throw new IOException("software owner differs");
            if (script == Script.GUARD_AFTER_WRITE && windows.writes() > 0)
                throw new IOException("software owner revalidation failed after focus");
        }, windows, screen -> {
            captures.incrementAndGet();
            throw new AssertionError("focus must not capture pixels");
        }, () -> 1, clock);
        return new Harness(capture, show, bring, foreground, captures, guards);
    }

    public static CoaWindowCapture.Preflight focus(CoaWindowCapture capture, Instant deadline) throws IOException {
        return capture.focusOwnedWindowOnce(deadline);
    }

    private static final class Transcript implements CoaWindowCapture.Windows {
        private final GameGeneration game;
        private final Script script;
        private final AtomicInteger show, bring, foregroundCalls;
        private final HWND target = handle(9007199254740993L), second = handle(17), foreign = handle(9);
        private HWND foreground;

        Transcript(GameGeneration game, Script script, AtomicInteger show, AtomicInteger bring,
                AtomicInteger foregroundCalls) {
            this.game = game; this.script = script; this.show = show; this.bring = bring;
            this.foregroundCalls = foregroundCalls;
            foreground = script == Script.FOREGROUND ? target : foreign;
        }

        int writes() { return show.get() + bring.get() + foregroundCalls.get(); }
        @Override public boolean EnumWindows(WNDENUMPROC callback, Pointer data) {
            callback.callback(target, data);
            if (script == Script.AMBIGUOUS) callback.callback(second, data);
            return true;
        }
        @Override public boolean IsWindowVisible(HWND window) { return true; }
        @Override public boolean IsIconic(HWND window) { return false; }
        @Override public boolean IsWindow(HWND window) { return true; }
        @Override public boolean GetClientRect(HWND window, RECT rect) {
            rect.left = 0; rect.top = 0; rect.right = 2560; rect.bottom = 1440; return true;
        }
        @Override public boolean ClientToScreen(HWND window, POINT point) {
            point.x -= 2560;
            if (script == Script.WINDOW_DRIFT && writes() > 0) point.x++;
            return true;
        }
        @Override public boolean GetWindowRect(HWND window, RECT rect) {
            rect.left = -2560; rect.top = 0; rect.right = 0; rect.bottom = 1440; return true;
        }
        @Override public HWND GetAncestor(HWND window, int flags) { return window; }
        @Override public HWND GetForegroundWindow() { return foreground; }
        @Override public int GetWindowThreadProcessId(HWND window, IntByReference pid) {
            pid.setValue((int) game.pid()); return same(window, foreign) ? 2 : 3;
        }
        @Override public boolean ShowWindow(HWND window, int command) { show.incrementAndGet(); return true; }
        @Override public boolean BringWindowToTop(HWND window) { bring.incrementAndGet(); return true; }
        @Override public boolean SetForegroundWindow(HWND window) {
            foregroundCalls.incrementAndGet();
            if (script != Script.REMAINS_FOREIGN) foreground = target;
            return true;
        }
        @Override public HWND SetActiveWindow(HWND window) { throw new AssertionError("SetActiveWindow forbidden"); }
        @Override public boolean AttachThreadInput(int from, int to, boolean join) {
            throw new AssertionError("AttachThreadInput forbidden");
        }
        private static HWND handle(long value) { return new HWND(Pointer.createConstant(value)); }
        private static boolean same(HWND left, HWND right) {
            return Pointer.nativeValue(left.getPointer()) == Pointer.nativeValue(right.getPointer());
        }
    }
}
