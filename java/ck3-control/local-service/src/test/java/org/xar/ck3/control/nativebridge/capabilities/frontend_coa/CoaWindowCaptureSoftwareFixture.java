package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinDef.POINT;
import com.sun.jna.platform.win32.WinDef.RECT;
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC;
import com.sun.jna.ptr.IntByReference;
import java.awt.image.BufferedImage;
import java.time.Clock;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.GameGeneration;

/** Software Win32 transcript for actual central-private-permit -> present -> archive tests.
 * It never opens a desktop, observes a physical Game or mints a permit/VERIFIED outcome. */
public final class CoaWindowCaptureSoftwareFixture {
    private CoaWindowCaptureSoftwareFixture(){ }
    public enum Script {ALREADY_FOREGROUND,DIRECT,ATTACHED,ATTACH_FAILURE,DETACH_FAILURE,WINDOW_DRIFT,DIRECT_REMAINS_FOREIGN}
    public record Harness(CoaWindowCapture capture,AtomicInteger writes,AtomicInteger captures){ }
    public static Harness create(GameGeneration game,Script script,Clock clock){
        var writes=new AtomicInteger();var captures=new AtomicInteger();var windows=new Transcript(game,script,writes);
        var actual=new CoaWindowCapture(game,expected->{if(!game.equals(expected))throw new java.io.IOException("software transcript process birth differs");},windows,
                screen->{captures.incrementAndGet();return new BufferedImage(screen.width,screen.height,BufferedImage.TYPE_INT_RGB);},()->1,clock);
        return new Harness(actual,writes,captures);
    }
    private static final class Transcript implements CoaWindowCapture.Windows {
        private final GameGeneration game;private final Script script;private final AtomicInteger writes;
        private final HWND target=handle(9007199254740993L),foreign=handle(9);
        private HWND foreground;private boolean attached;
        Transcript(GameGeneration game,Script script,AtomicInteger writes){this.game=game;this.script=script;this.writes=writes;foreground=script==Script.ALREADY_FOREGROUND?target:foreign;}
        public boolean EnumWindows(WNDENUMPROC callback,Pointer data){callback.callback(target,data);return true;}
        public boolean IsWindowVisible(HWND window){return true;}
        public boolean IsIconic(HWND window){return false;}
        public boolean IsWindow(HWND window){return true;}
        public boolean GetClientRect(HWND window,RECT rect){rect.left=0;rect.top=0;rect.right=2560;rect.bottom=1440;return true;}
        public boolean ClientToScreen(HWND window,POINT point){point.x-=2560;if(script==Script.WINDOW_DRIFT&&writes.get()>0)point.x++;return true;}
        public boolean GetWindowRect(HWND window,RECT rect){rect.left=-2560;rect.top=0;rect.right=0;rect.bottom=1440;return true;}
        public HWND GetAncestor(HWND window,int flags){return window;}
        public HWND GetForegroundWindow(){return foreground;}
        public int GetWindowThreadProcessId(HWND window,IntByReference pid){pid.setValue((int)game.pid());return same(window,target)?3:2;}
        public boolean ShowWindow(HWND window,int command){writes.incrementAndGet();return true;}
        public boolean BringWindowToTop(HWND window){writes.incrementAndGet();return true;}
        public boolean SetForegroundWindow(HWND window){writes.incrementAndGet();if(script==Script.DIRECT||script==Script.WINDOW_DRIFT||(attached&&script!=Script.DIRECT_REMAINS_FOREIGN))foreground=target;return true;}
        public HWND SetActiveWindow(HWND window){writes.incrementAndGet();return window;}
        public boolean AttachThreadInput(int from,int to,boolean join){writes.incrementAndGet();if(join&&script==Script.ATTACH_FAILURE)return false;if(!join&&script==Script.DETACH_FAILURE)return false;attached=join;return true;}
        private static HWND handle(long value){return new HWND(Pointer.createConstant(value));}
        private static boolean same(HWND left,HWND right){return Pointer.nativeValue(left.getPointer())==Pointer.nativeValue(right.getPointer());}
    }
}
