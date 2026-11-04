package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinDef.HWND;
import com.sun.jna.platform.win32.WinDef.POINT;
import com.sun.jna.platform.win32.WinDef.RECT;
import com.sun.jna.platform.win32.WinUser.WNDENUMPROC;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** The real focus operation over software Win32 IO only, without a desktop, Managed owner or permit. */
final class OwnedIconicFocusWindowTest {
    private static final GameGeneration GAME=new GameGeneration(1234,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final long TARGET=9007199254740993L,SECOND=17,FOREIGN=9;
    private static final Instant NOW=Instant.parse("2026-11-04T22:00:00Z"),DEADLINE=NOW.plusSeconds(10);

    @Test void iconicZeroClientRestoresItsExactOwnedRootBeforeStrictFocus()throws Exception {
        var windows=new Transcript(Mode.ICONIC);var actual=capture(windows);
        var result=actual.focusOwnedWindowOnce(DEADLINE);
        assertEquals(GAME,result.game());assertEquals(Long.toUnsignedString(TARGET),result.window().hwnd());
        assertEquals(new CoaWindowCapture.ScreenRect(-2560,0,0,1440),result.window().clientRect());
        assertEquals(Long.toUnsignedString(TARGET),result.foregroundRoot());assertEquals(TARGET,id(windows.foreground));
        assertTrue(windows.guards>=2);assertTrue(windows.enumerations>=2);
        assertTrue(windows.firstShowWasIconic);assertEquals(0,windows.firstShowWidth);assertEquals(0,windows.firstShowHeight);
        assertTrue(windows.geometryReadsAfterRestore>0);assertEquals(2,windows.shows);
        assertEquals(1,windows.brings);assertEquals(1,windows.foregrounds);assertEquals(0,windows.captures);
        assertTrue(windows.events.indexOf("restore")<windows.events.indexOf("bring"));
        assertTrue(windows.events.indexOf("bring")<windows.events.indexOf("foreground"));
        assertEquals(List.of(TARGET,TARGET,TARGET,TARGET),windows.writtenHandles);
        System.out.println("SOFTWARE_OWNED_ICONIC_FOCUS_DATA iconic_zero_client=true original_hwnd_restored=true strict_geometry_foreground=true pixels=0");
    }

    @Test void ambiguousForeignDriftingIdentityBirthAndExpiredDeadlineNeverWrite()throws Exception {
        for(Mode mode:List.of(Mode.AMBIGUOUS,Mode.FOREIGN_ONLY,Mode.SECOND_ENUM_AMBIGUOUS,Mode.PID_DRIFT,Mode.ROOT_DRIFT,
                Mode.VANISHED,Mode.BIRTH_DRIFT,Mode.EXPIRED,Mode.SECOND_ENUM_EXPIRED)) {
            var windows=new Transcript(mode);var actual=capture(windows);
            if(mode==Mode.EXPIRED){windows.clock.now=DEADLINE;windows.faultFired=true;}
            Exception failure=assertThrows(Exception.class,()->actual.focusOwnedWindowOnce(DEADLINE),mode.name());
            assertTrue(failure instanceof IOException||failure instanceof IllegalArgumentException,mode.name());
            if(mode==Mode.BIRTH_DRIFT){assertSame(windows.birthFailure,failure);assertEquals(2,windows.guards);}
            assertTrue(windows.faultFired,mode.name());
            if(mode==Mode.SECOND_ENUM_AMBIGUOUS||mode==Mode.SECOND_ENUM_EXPIRED)assertTrue(windows.enumerations>=2,mode.name());
            assertEquals(0,windows.writes(),mode.name());assertEquals(0,windows.captures,mode.name());
            assertTrue(windows.writtenHandles.isEmpty(),mode.name());
        }
        System.out.println("SOFTWARE_OWNED_ICONIC_FOCUS_DATA ambiguous_foreign_identity_birth_deadline_rejected=true presentation_writes=0 pixels=0");
    }

    @Test void strictPostRestoreGeometryExpectedHandleAndReadOnlyGatesRemain()throws Exception {
        for(Mode mode:List.of(Mode.WRONG_SIZE,Mode.REPLACED_AFTER_RESTORE)) {
            var windows=new Transcript(mode);var actual=capture(windows);
            Exception failure=assertThrows(Exception.class,()->actual.focusOwnedWindowOnce(DEADLINE));
            assertTrue(failure instanceof IOException||failure instanceof IllegalArgumentException);
            assertTrue(windows.faultFired);assertEquals(1,windows.shows);assertEquals(0,windows.brings);
            assertEquals(0,windows.foregrounds);assertEquals(0,windows.captures);assertEquals(List.of(TARGET),windows.writtenHandles);
        }
        for(Mode mode:List.of(Mode.ICONIC,Mode.NONICONIC)) {
            var windows=new Transcript(mode);var actual=capture(windows);
            assertThrows(IllegalArgumentException.class,actual::captureReadOnly);
            assertEquals(0,windows.writes());assertEquals(0,windows.captures);
        }
        var normal=new Transcript(Mode.NONICONIC);var actual=capture(normal);
        var result=actual.focusOwnedWindowOnce(DEADLINE);
        assertEquals(Long.toUnsignedString(TARGET),result.window().hwnd());assertEquals(Long.toUnsignedString(TARGET),result.foregroundRoot());
        assertFalse(normal.firstShowWasIconic);assertEquals(2560,normal.firstShowWidth);assertEquals(1440,normal.firstShowHeight);
        assertTrue(normal.geometryReadsBeforeShow>0);assertEquals(1,normal.shows);assertEquals(1,normal.brings);assertEquals(1,normal.foregrounds);
        assertFalse(normal.events.contains("restore"));assertEquals(0,normal.captures);assertEquals(List.of(TARGET,TARGET,TARGET),normal.writtenHandles);
        System.out.println("SOFTWARE_OWNED_ICONIC_FOCUS_DATA wrong_size_replacement_rejected=true read_only_no_autofocus=true noniconic_original_focus=true pixels=0");
    }

    private static CoaWindowCapture capture(Transcript windows) {
        return new CoaWindowCapture(GAME,expected->{
            windows.guards++;assertEquals(GAME,expected);
            if(windows.mode==Mode.BIRTH_DRIFT&&windows.guards==2){windows.faultFired=true;throw windows.birthFailure;}
        },windows,screen->{windows.captures++;throw new AssertionError("focus/read-only rejection must not capture pixels");},()->1,windows.clock);
    }
    private enum Mode {ICONIC,AMBIGUOUS,FOREIGN_ONLY,SECOND_ENUM_AMBIGUOUS,PID_DRIFT,ROOT_DRIFT,VANISHED,BIRTH_DRIFT,EXPIRED,SECOND_ENUM_EXPIRED,WRONG_SIZE,REPLACED_AFTER_RESTORE,NONICONIC}
    private static final class TestClock extends Clock {
        Instant now=NOW;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){return Clock.fixed(now,zone);}
        @Override public Instant instant(){return now;}
    }
    private static final class Transcript implements CoaWindowCapture.Windows {
        final Mode mode;final TestClock clock=new TestClock();
        final IOException birthFailure=new IOException("original software process birth changed");
        final List<Long> writtenHandles=new ArrayList<>();final List<String> events=new ArrayList<>();
        HWND foreground=handle(FOREIGN);boolean hasTarget=true,hasSecond,live=true,owned=true,root=true,iconic=true,faultFired,firstShowWasIconic;
        int width,height,enumerations,guards,shows,brings,foregrounds,captures,geometryReadsAfterRestore,geometryReadsBeforeShow,firstShowWidth,firstShowHeight;
        Transcript(Mode mode) {
            this.mode=mode;
            if(mode==Mode.NONICONIC){iconic=false;width=2560;height=1440;}
            if(mode==Mode.AMBIGUOUS){hasSecond=true;faultFired=true;}
            if(mode==Mode.FOREIGN_ONLY){hasTarget=false;faultFired=true;}
        }
        int writes(){return shows+brings+foregrounds;}
        @Override public boolean EnumWindows(WNDENUMPROC callback,Pointer data) {
            enumerations++;
            if(enumerations>=2&&mode==Mode.SECOND_ENUM_AMBIGUOUS){hasSecond=true;faultFired=true;}
            if(enumerations>=2&&mode==Mode.SECOND_ENUM_EXPIRED){clock.now=DEADLINE;faultFired=true;}
            if(hasTarget)callback.callback(handle(TARGET),data);
            if(hasSecond)callback.callback(handle(SECOND),data);
            callback.callback(handle(FOREIGN),data);
            if(enumerations==1) {
                if(mode==Mode.PID_DRIFT){owned=false;faultFired=true;}
                if(mode==Mode.ROOT_DRIFT){root=false;faultFired=true;}
                if(mode==Mode.VANISHED){live=false;faultFired=true;}
            }
            return true;
        }
        @Override public boolean IsWindowVisible(HWND window){long value=id(window);return value==TARGET?hasTarget:value==SECOND?hasSecond:value==FOREIGN;}
        @Override public boolean IsIconic(HWND window){return id(window)==TARGET?iconic:id(window)==FOREIGN&&mode==Mode.FOREIGN_ONLY;}
        @Override public boolean IsWindow(HWND window){return id(window)==TARGET?hasTarget&&live:id(window)==SECOND?hasSecond:id(window)==FOREIGN;}
        @Override public boolean GetClientRect(HWND window,RECT rect) {
            boolean foreignIconic=id(window)==FOREIGN&&mode==Mode.FOREIGN_ONLY;
            rect.left=0;rect.top=0;rect.right=id(window)==TARGET?width:foreignIconic?0:2560;rect.bottom=id(window)==TARGET?height:foreignIconic?0:1440;
            if(id(window)==TARGET){if(shows==0)geometryReadsBeforeShow++;else geometryReadsAfterRestore++;}
            return true;
        }
        @Override public boolean ClientToScreen(HWND window,POINT point){point.x-=2560;return true;}
        @Override public boolean GetWindowRect(HWND window,RECT rect){rect.left=-2560;rect.top=0;rect.right=0;rect.bottom=1440;return true;}
        @Override public HWND GetAncestor(HWND window,int flags){return id(window)==TARGET&&!root?handle(FOREIGN):window;}
        @Override public HWND GetForegroundWindow(){return foreground;}
        @Override public int GetWindowThreadProcessId(HWND window,IntByReference pid) {
            boolean gameWindow=id(window)==TARGET?owned:id(window)==SECOND;
            pid.setValue(gameWindow?(int)GAME.pid():9999);return gameWindow?3:2;
        }
        @Override public boolean ShowWindow(HWND window,int command) {
            assertEquals(TARGET,id(window));assertEquals(9,command);writtenHandles.add(id(window));
            if(shows==0){firstShowWasIconic=iconic;firstShowWidth=width;firstShowHeight=height;}
            shows++;events.add(iconic?"restore":"show");iconic=false;width=2560;height=1440;
            if(mode==Mode.WRONG_SIZE){width=1920;height=1080;faultFired=true;}
            if(mode==Mode.REPLACED_AFTER_RESTORE){hasTarget=false;hasSecond=true;faultFired=true;}
            return true;
        }
        @Override public boolean BringWindowToTop(HWND window){assertEquals(TARGET,id(window));writtenHandles.add(id(window));brings++;events.add("bring");return true;}
        @Override public boolean SetForegroundWindow(HWND window){assertEquals(TARGET,id(window));writtenHandles.add(id(window));foregrounds++;events.add("foreground");foreground=window;return true;}
        @Override public HWND SetActiveWindow(HWND window){throw new AssertionError("owned focus must not call SetActiveWindow");}
        @Override public boolean AttachThreadInput(int from,int to,boolean join){throw new AssertionError("owned focus must not attach input threads");}
    }
    private static HWND handle(long value){return new HWND(Pointer.createConstant(value));}
    private static long id(HWND window){return window==null||window.getPointer()==null?0:Pointer.nativeValue(window.getPointer());}
}
