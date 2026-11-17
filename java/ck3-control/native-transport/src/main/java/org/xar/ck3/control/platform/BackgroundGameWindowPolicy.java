package org.xar.ck3.control.platform;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;

/** Minimize-only policy for the exact held Game. No foreground, restore, input, capture or activation API exists here. */
public final class BackgroundGameWindowPolicy {
    interface Windows extends StdCallLibrary {
        boolean EnumWindows(WNDENUMPROC callback,Pointer data);
        boolean IsWindow(HWND window);
        boolean IsWindowVisible(HWND window);
        boolean IsIconic(HWND window);
        int GetWindowThreadProcessId(HWND window,IntByReference pid);
        int GetWindowLongW(HWND window,int index);
        boolean SetWindowPos(HWND window,HWND after,int x,int y,int width,int height,int flags);
        boolean ShowWindowAsync(HWND window,int command);
    }
    interface Access {
        List<Long> windows() throws IOException;
        long pid(long window) throws IOException;
        boolean visible(long window);
        boolean minimized(long window);
        boolean topmost(long window);
        void cancelTopmost(long window) throws IOException;
        void minimizeNoActivate(long window) throws IOException;
    }
    private BackgroundGameWindowPolicy() { }
    private static final class Actual {
        static final Access WINDOWS=new Access() {
            private final Windows api=Native.load("user32",Windows.class,W32APIOptions.DEFAULT_OPTIONS);
            private HWND handle(long id){return new HWND(Pointer.createConstant(id));}
            @Override public List<Long> windows()throws IOException {
                var found=new ArrayList<Long>();
                boolean ok=api.EnumWindows((window,data)->{
                    if(found.size()>=16384)return false;
                    found.add(Pointer.nativeValue(window.getPointer()));return true;
                },null);
                if(!ok||found.size()>=16384)throw new IOException("bounded Game window enumeration failed");
                return List.copyOf(found);
            }
            @Override public long pid(long id)throws IOException {
                var window=handle(id);var pid=new IntByReference();
                if(!api.IsWindow(window)||api.GetWindowThreadProcessId(window,pid)==0)return 0;
                return Integer.toUnsignedLong(pid.getValue());
            }
            @Override public boolean visible(long id){return api.IsWindowVisible(handle(id));}
            @Override public boolean minimized(long id){return api.IsIconic(handle(id));}
            @Override public boolean topmost(long id){return (api.GetWindowLongW(handle(id),-20)&8)!=0;}
            @Override public void cancelTopmost(long id)throws IOException {
                // HWND_NOTOPMOST; NOSIZE|NOMOVE|NOACTIVATE|NOOWNERZORDER.
                if(!api.SetWindowPos(handle(id),handle(-2),0,0,0,0,0x213))throw new IOException("Game NOTOPMOST/NOACTIVATE operation failed");
            }
            @Override public void minimizeNoActivate(long id)throws IOException {
                if(!api.ShowWindowAsync(handle(id),7))throw new IOException("Game minimize/NOACTIVATE operation failed");
            }
        };
    }
    public static void enforce(GameGeneration game,NativeProcessGuard held)throws IOException {
        enforce(game,held,Actual.WINDOWS);
    }
    /** Controlled Win32 seam only; neither its DATA nor successful software checks issue a physical Game role. */
    static void enforce(GameGeneration game,NativeProcessGuard held,Access windows)throws IOException {
        Objects.requireNonNull(game);Objects.requireNonNull(held);Objects.requireNonNull(windows);
        held.verify(game);
        for(long window:windows.windows()) {
            if(windows.pid(window)!=game.pid()||!windows.visible(window))continue;
            if(windows.topmost(window)) {
                held.verify(game);requirePid(windows,window,game);
                windows.cancelTopmost(window);
            }
            if(!windows.minimized(window)) {
                held.verify(game);requirePid(windows,window,game);
                windows.minimizeNoActivate(window);
            }
            held.verify(game);requirePid(windows,window,game);
            if(!windows.minimized(window)||windows.topmost(window))throw new IOException("Game background window policy has not yet been physically observed");
        }
        held.verify(game);
    }
    private static void requirePid(Access windows,long window,GameGeneration game)throws IOException {
        if(windows.pid(window)!=game.pid())throw new IOException("Game HWND crossed its exact held process");
    }
}
