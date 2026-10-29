package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.require;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinDef.POINT;
import com.sun.jna.platform.win32.WinDef.RECT;
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.awt.AWTException;
import java.awt.Rectangle;
import java.awt.Robot;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.time.Instant;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.SubmissionPermit;
import org.xar.ck3.control.application.action.FrontendWindowCapturePermit;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;

/** The original Win32 presentation path. Screenshot pixels never substitute for native route or state truth. */
public final class CoaWindowCapture {
    interface Windows extends StdCallLibrary {
        boolean EnumWindows(WNDENUMPROC callback, Pointer data);
        boolean IsWindowVisible(HWND window); boolean IsIconic(HWND window); boolean IsWindow(HWND window);
        boolean GetClientRect(HWND window, RECT rect); boolean ClientToScreen(HWND window, POINT point);
        boolean GetWindowRect(HWND window, RECT rect); HWND GetAncestor(HWND window, int flags);
        HWND GetForegroundWindow(); int GetWindowThreadProcessId(HWND window, IntByReference processId);
        boolean ShowWindow(HWND window, int command); boolean BringWindowToTop(HWND window); boolean SetForegroundWindow(HWND window);
        HWND SetActiveWindow(HWND window); boolean AttachThreadInput(int attach, int attachTo, boolean join);
    }
    public enum ActivationMode { ALREADY_FOREGROUND, DIRECT, ATTACHED_FOREGROUND_THREAD }
    public record ScreenRect(int left, int top, int right, int bottom) {
        public ScreenRect { require((long)right-left==2560 && (long)bottom-top==1440, "exact original client screen rectangle required"); }
        public int width() { return right - left; } public int height() { return bottom - top; }
    }
    public record WindowIdentity(String hwnd, ScreenRect clientRect) {
        public WindowIdentity { require(hwnd != null && hwnd.matches("[1-9][0-9]*"), "canonical HWND decimal identity required"); Objects.requireNonNull(clientRect); }
    }
    public record Preparation(long bridgePid, WindowIdentity window, String foregroundRootBefore, String foregroundRootAfter,
            ActivationMode mode, long attachedForegroundThread, long attachedTargetThread, Optional<Boolean> detachSucceeded,
            Instant observedAt, String actionId, String requestId) {
        public Preparation { Objects.requireNonNull(window); Objects.requireNonNull(mode); detachSucceeded = Objects.requireNonNull(detachSucceeded); Objects.requireNonNull(observedAt); }
        public boolean presentationOnly() { return true; } public boolean usesOcr() { return false; }
        public boolean usesKeyboard() { return false; } public boolean usesMouse() { return false; }
    }
    public record Captured(long bridgePid, WindowIdentity window, Instant observedAt, CoaFramebuffer.Image image) {
        public Captured { Objects.requireNonNull(window); Objects.requireNonNull(observedAt); Objects.requireNonNull(image); }
    }
    @FunctionalInterface interface PixelCapture {BufferedImage capture(Rectangle screen)throws AWTException;}
    private final GameGeneration game; private final NativeProcessGuard process; private final Windows windows; private final Clock clock;
    private final PixelCapture pixels;private final java.util.function.IntSupplier currentThread;
    public CoaWindowCapture(GameGeneration game, NativeProcessGuard process) { this(game,process,Clock.systemUTC()); }
    public CoaWindowCapture(GameGeneration game,NativeProcessGuard process,Clock clock) {
        this(game,process,actualWindows(),screen->new Robot().createScreenCapture(screen),()->Kernel32.INSTANCE.GetCurrentThreadId(),clock);
    }
    /** Package-local software IO fixture seam; it grants no private central permit or physical Game qualification. */
    CoaWindowCapture(GameGeneration game,NativeProcessGuard process,Windows windows,PixelCapture pixels,
            java.util.function.IntSupplier currentThread,Clock clock){
        this.game=Objects.requireNonNull(game);this.process=Objects.requireNonNull(process);this.windows=Objects.requireNonNull(windows);
        this.pixels=Objects.requireNonNull(pixels);this.currentThread=Objects.requireNonNull(currentThread);this.clock=Objects.requireNonNull(clock);
    }
    private static Windows actualWindows(){require(System.getProperty("os.name", "").startsWith("Windows"),"CK3 framebuffer requires Windows");return Native.load("user32",Windows.class,W32APIOptions.DEFAULT_OPTIONS);}
    public record Preflight(GameGeneration game,WindowIdentity window,String foregroundRoot,Instant observedAt) {
        public Preflight {Objects.requireNonNull(game);Objects.requireNonNull(window);Objects.requireNonNull(foregroundRoot);Objects.requireNonNull(observedAt);}
        public FrontendWindowCaptureRequest.Window requestWindow(){return windowData(window);}
    }
    /** Reads the actual process birth, unique visible client and foreground; no presentation write. */
    public synchronized Preflight preflightReadOnly()throws IOException {
        process.verify(game);WindowIdentity actual=unique();String foreground=rootId(windows.GetForegroundWindow());process.verify(game);
        require(actual.equals(unique()),"client changed during actual presentation preflight");return new Preflight(game,actual,foreground,clock.instant());
    }
    /** Only the new central private WindowCapture permit authorizes this physical plane. */
    public synchronized FrontendWindowCaptureOutcome present(FrontendWindowCaptureRequest request,ExactRef originalRequest,
            FrontendWindowCapturePermit permit)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(originalRequest);Objects.requireNonNull(permit);
        require(request.owner().processId()==game.pid()&&request.owner().processBirthFiletime().equals(game.creationFiletime().value().toString()),"presentation crossed actual process birth");
        byte[] raw=request.encode();require(originalRequest.bytes()==raw.length&&originalRequest.sha256().equals(CoaData.sha256(raw)),"original prepared request identity differs");
        var before=preflightReadOnly();require(before.requestWindow().equals(request.window())&&before.foregroundRoot().equals(request.foregroundRootBefore()),"client/foreground drifted before private permit consumption");
        require(clock.instant().isBefore(request.deadline()),"foreground preparation deadline expired");
        permit.consume(request,request.deadline());
        // Every later failure retains the consumed once boundary. No retry or fallback action is minted.
        Instant entered=clock.instant();var mode=FrontendWindowCaptureOutcome.ActivationMode.ALREADY_FOREGROUND;
        int foregroundThread=0,targetThread=0;Optional<Boolean> detached=Optional.empty();
        Optional<String> directError=Optional.empty(),attachedError=Optional.empty(),failure=Optional.empty();
        Optional<FrontendWindowCaptureRequest.Window> after=Optional.empty();Optional<String> foregroundAfter=Optional.empty();
        HWND hwnd=handle(before.window().hwnd());
        try {
            if(!before.foregroundRoot().equals(before.window().hwnd())) {
                mode=FrontendWindowCaptureOutcome.ActivationMode.DIRECT;
                windows.ShowWindow(hwnd,9);
                boolean brought=windows.BringWindowToTop(hwnd),focused=windows.SetForegroundWindow(hwnd);
                if(!brought||!focused)directError=Optional.of("direct foreground returned false; win32_error="+Integer.toUnsignedString(Native.getLastError()));
                if(!rootId(windows.GetForegroundWindow()).equals(before.window().hwnd())) {
                    if(directError.isEmpty())directError=Optional.of("direct activation did not acquire the exact target foreground");
                    mode=FrontendWindowCaptureOutcome.ActivationMode.ATTACHED_FOREGROUND_THREAD;
                    int current=currentThread.getAsInt();
                    foregroundThread=windows.GetWindowThreadProcessId(windows.GetForegroundWindow(),new IntByReference());
                    targetThread=windows.GetWindowThreadProcessId(hwnd,new IntByReference());
                    require(foregroundThread!=0&&foregroundThread!=current&&targetThread!=0,"foreground thread unavailable for bounded activation");
                    boolean foregroundAttached=false,targetAttached=false;
                    try {
                        require(windows.AttachThreadInput(current,foregroundThread,true),"foreground AttachThreadInput failed");foregroundAttached=true;
                        if(targetThread!=current&&targetThread!=foregroundThread){require(windows.AttachThreadInput(current,targetThread,true),"target AttachThreadInput failed");targetAttached=true;}
                        windows.ShowWindow(hwnd,9);windows.BringWindowToTop(hwnd);windows.SetActiveWindow(hwnd);windows.SetForegroundWindow(hwnd);
                    }catch(RuntimeException attachFailure){attachedError=Optional.of(detail(attachFailure));throw attachFailure;}
                    finally {
                        boolean targetDetached=!targetAttached||windows.AttachThreadInput(current,targetThread,false);
                        boolean foregroundDetached=!foregroundAttached||windows.AttachThreadInput(current,foregroundThread,false);
                        if(targetAttached||foregroundAttached)detached=Optional.of(targetDetached&&foregroundDetached);
                    }
                    require(detached.equals(Optional.of(true)),"AttachThreadInput detach failed");
                }
            }
            process.verify(game);var observed=unique();after=Optional.of(windowData(observed));foregroundAfter=Optional.of(rootId(windows.GetForegroundWindow()));
            require(observed.equals(before.window())&&foregroundAfter.orElseThrow().equals(before.window().hwnd()),"exact client did not obtain stable foreground");
            require(clock.instant().isBefore(request.deadline()),"foreground outcome arrived after deadline");
        }catch(IOException|RuntimeException unresolved){failure=Optional.of(detail(unresolved));}
        Instant observed=clock.instant();if(observed.isBefore(entered))throw new IOException("presentation clock moved backwards after once boundary; never replay");
        return new FrontendWindowCaptureOutcome(request,originalRequest,failure.isEmpty()?FrontendWindowCaptureOutcome.Status.VERIFIED:FrontendWindowCaptureOutcome.Status.UNKNOWN,
                Optional.of(entered),observed,request.window(),after,before.foregroundRoot(),foregroundAfter,Optional.of(mode),
                Integer.toUnsignedLong(foregroundThread),Integer.toUnsignedLong(targetThread),detached,directError,attachedError,failure,List.of(originalRequest));
    }
    private static String detail(Exception failure){String text=failure.getClass().getName()+": "+String.valueOf(failure.getMessage());return text.length()>2048?text.substring(0,2048):text;}
    private static FrontendWindowCaptureRequest.Window windowData(WindowIdentity actual){var r=actual.clientRect();return new FrontendWindowCaptureRequest.Window(actual.hwnd(),new FrontendWindowCaptureRequest.ScreenRect(r.left(),r.top(),r.right(),r.bottom()));}
    /** Only the same global coordinator's durable permit may request foreground. No caller string authorizes it. */
    public synchronized Preparation prepare(SubmissionPermit permit) throws IOException {
        Objects.requireNonNull(permit); require(permit.origin() instanceof CommandOrigin.Frontend, "CoA foreground requires the coordinator's real frontend origin");
        CommandOrigin.Frontend origin = (CommandOrigin.Frontend) permit.origin(); require(origin.identity().game().equals(game), "presentation permit belongs to another Game");
        require(permit.preparedRequest().step().equals("prepare-frontend-coat-of-arms-framebuffer-v1"), "permit is not the registered CoA presentation action");
        process.verify(game); WindowIdentity target = unique(); HWND hwnd = handle(target.hwnd()); String before = rootId(windows.GetForegroundWindow());
        // No presentation API runs before consumption; an exception after this boundary is UNKNOWN and must never be replayed.
        permit.consumeOnce(); ActivationMode mode = ActivationMode.ALREADY_FOREGROUND; int foregroundThread = 0, targetThread = 0; Optional<Boolean> detached = Optional.empty();
        if (!before.equals(target.hwnd())) {
            mode = ActivationMode.DIRECT; windows.ShowWindow(hwnd, 9); windows.BringWindowToTop(hwnd); windows.SetForegroundWindow(hwnd);
            if (!rootId(windows.GetForegroundWindow()).equals(target.hwnd())) {
                mode = ActivationMode.ATTACHED_FOREGROUND_THREAD; int current = currentThread.getAsInt();
                foregroundThread = windows.GetWindowThreadProcessId(windows.GetForegroundWindow(), new IntByReference()); targetThread = windows.GetWindowThreadProcessId(hwnd, new IntByReference());
                require(foregroundThread != 0 && foregroundThread != current && targetThread != 0, "foreground thread unavailable for bounded activation");
                require(windows.AttachThreadInput(current, foregroundThread, true), "foreground AttachThreadInput failed"); boolean targetAttached = false;
                try {
                    if (targetThread != current && targetThread != foregroundThread) { require(windows.AttachThreadInput(current, targetThread, true), "target AttachThreadInput failed"); targetAttached = true; }
                    windows.ShowWindow(hwnd, 9); windows.BringWindowToTop(hwnd); windows.SetActiveWindow(hwnd); windows.SetForegroundWindow(hwnd);
                } finally {
                    boolean targetDetached = !targetAttached || windows.AttachThreadInput(current, targetThread, false);
                    boolean foregroundDetached = windows.AttachThreadInput(current, foregroundThread, false);
                    detached = Optional.of(targetDetached && foregroundDetached); require(detached.orElseThrow(), "AttachThreadInput detach failed");
                }
            }
        }
        process.verify(game); WindowIdentity after = unique(); String foregroundAfter = rootId(windows.GetForegroundWindow());
        require(target.equals(after) && foregroundAfter.equals(target.hwnd()), "exact CK3 client did not obtain stable foreground");
        return new Preparation(game.pid(), target, before, foregroundAfter, mode, Integer.toUnsignedLong(foregroundThread), Integer.toUnsignedLong(targetThread), detached, clock.instant(), permit.actionId(), permit.requestId());
    }
    /** Read-only capture refuses a hidden client. Any needed foreground action must first use prepare through the one coordinator. */
    public synchronized Captured captureReadOnly() throws IOException {
        process.verify(game); WindowIdentity before = unique(); require(rootId(windows.GetForegroundWindow()).equals(before.hwnd()), "bound CK3 client is not foreground; coordinator presentation action required"); unobscured(before);
        ScreenRect rect = before.clientRect(); CoaFramebuffer.Image image;
        try { image = new CoaFramebuffer.Image(pixels.capture(new Rectangle(rect.left(), rect.top(), rect.width(), rect.height()))); }
        catch (AWTException failure) { throw new IOException("authenticated CK3 client capture failed", failure); }
        process.verify(game); WindowIdentity after = unique(); require(before.equals(after) && rootId(windows.GetForegroundWindow()).equals(before.hwnd()), "CK3 client binding changed during capture"); unobscured(after);
        require(image.size().equals(new CoaFramebuffer.Size(2560, 1440)), "captured client differs from original exact client size"); return new Captured(game.pid(), after, clock.instant(), image);
    }
    public synchronized boolean foregroundReady() throws IOException { process.verify(game); WindowIdentity target = unique(); return rootId(windows.GetForegroundWindow()).equals(target.hwnd()); }
    private WindowIdentity unique() {
        List<WindowIdentity> candidates = new ArrayList<>(); require(windows.EnumWindows((hwnd, data) -> {
            IntByReference pid = new IntByReference(); windows.GetWindowThreadProcessId(hwnd, pid);
            if (Integer.toUnsignedLong(pid.getValue()) == game.pid() && windows.IsWindowVisible(hwnd)) {
                RECT client = new RECT(); require(windows.GetClientRect(hwnd, client), "GetClientRect failed");
                if (client.right - client.left == 2560 && client.bottom - client.top == 1440) { POINT origin = new POINT(0, 0), extent = new POINT(2560, 1440); require(windows.ClientToScreen(hwnd, origin) && windows.ClientToScreen(hwnd, extent), "ClientToScreen failed"); candidates.add(new WindowIdentity(id(hwnd), new ScreenRect(origin.x, origin.y, extent.x, extent.y))); }
            } return true;
        }, null), "EnumWindows failed"); candidates.sort(Comparator.comparing(WindowIdentity::hwnd)); require(candidates.size() == 1, "expected one exact-PID CK3 client"); return candidates.get(0);
    }
    private void unobscured(WindowIdentity target) {
        boolean[] reached = {false}; List<String> blockers = new ArrayList<>(); ScreenRect client = target.clientRect();
        require(windows.EnumWindows((hwnd, data) -> { HWND root = windows.GetAncestor(hwnd, 2); String candidate = id(root);
            if (candidate.equals(target.hwnd())) { reached[0] = true; return true; }
            if (reached[0] || !windows.IsWindowVisible(root) || windows.IsIconic(root)) return true; RECT rect = new RECT(); require(windows.GetWindowRect(root, rect), "GetWindowRect failed");
            if (rect.right - rect.left <= 1 && rect.bottom - rect.top <= 1) return true;
            if (Math.max(client.left(), rect.left) < Math.min(client.right(), rect.right) && Math.max(client.top(), rect.top) < Math.min(client.bottom(), rect.bottom)) blockers.add(candidate); return true;
        }, null), "Z-order EnumWindows failed"); require(reached[0] && blockers.isEmpty(), "bound CK3 client disappeared or is obscured: " + blockers);
    }
    private String rootId(HWND hwnd) { return id(hwnd == null ? null : windows.GetAncestor(hwnd, 2)); }
    private static String id(HWND hwnd) { return hwnd == null || hwnd.getPointer() == null ? "0" : Long.toUnsignedString(Pointer.nativeValue(hwnd.getPointer())); }
    private static HWND handle(String id) { return new HWND(Pointer.createConstant(Long.parseUnsignedLong(id))); }
}
