package org.xar.ck3.control.platform;

import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import static org.junit.jupiter.api.Assertions.*;

final class RootProcessAttachBoundaryTest {
    private static final long PARENT=100;
    private static final WindowsJobProcess.ProcessIdentity GAME=new WindowsJobProcess.ProcessIdentity(200,"134373474898765883","D:\\Game\\ck3.exe");
    private static Win32Host.ProcessObservation live(long pid,long parent,String birth,String image) {
        return new Win32Host.ProcessObservation(pid,parent,Win32Host.ProcessState.RUNNING,258L,258L,
                new Win32Host.ProcessTimes(birth,"0"),259L,image,List.of());
    }
    private static Win32Host.ProcessInventory inventory(Win32Host.ProcessObservation... rows) {
        return new Win32Host.ProcessInventory("ck3.exe","2026-10-25T00:00:00Z",List.of(rows));
    }
    @Test void soleExactActualCreatorQualifiesInventoryOnly()throws Exception {
        assertDoesNotThrow(()->RootProcessAttach.requireInventory(inventory(live(200,PARENT,GAME.creationFiletimeDecimal(),GAME.executable())),GAME,PARENT));
    }
    @Test void retainedSignalZeroExit259AndImageFailureCannotQualify() {
        var row=new Win32Host.ProcessObservation(200,PARENT,Win32Host.ProcessState.SIGNALLED,0L,0L,
                new Win32Host.ProcessTimes(GAME.creationFiletimeDecimal(),"0"),259L,null,
                List.of(new Win32Host.ProcessFailure(Win32Host.ProcessOperation.IMAGE,31,"retained exited process image unavailable")));
        assertThrows(IOException.class,()->RootProcessAttach.requireInventory(inventory(row),GAME,PARENT));
    }
    @Test void reusedPidBirthImageAndCreatorDriftReject() {
        for(var row:List.of(live(200,PARENT,"134373474898765884",GAME.executable()),
                live(200,PARENT,GAME.creationFiletimeDecimal(),"D:\\Other\\ck3.exe"),
                live(200,101,GAME.creationFiletimeDecimal(),GAME.executable())))
            assertThrows(IOException.class,()->RootProcessAttach.requireInventory(inventory(row),GAME,PARENT));
    }
    @Test void otherLiveOrUnreadableCandidateBlocks() {
        var exact=live(200,PARENT,GAME.creationFiletimeDecimal(),GAME.executable());
        assertThrows(IOException.class,()->RootProcessAttach.requireInventory(inventory(exact,live(201,101,"134373474898765884",GAME.executable())),GAME,PARENT));
        var unknown=new Win32Host.ProcessObservation(201,101,Win32Host.ProcessState.UNAVAILABLE,null,null,null,null,null,
                List.of(new Win32Host.ProcessFailure(Win32Host.ProcessOperation.OPEN,5,"access denied")));
        assertThrows(IOException.class,()->RootProcessAttach.requireInventory(inventory(exact,unknown),GAME,PARENT));
    }
    @Test void receiptRecordCannotImpersonateRetainedStarted() {
        var lifecycle=new JavaGameLifecycle(List.of());
        assertThrows(IOException.class,()->lifecycle.requireColdStarted(new JavaGameLifecycle.Started(null,null,null),java.time.Instant.now().plusSeconds(30)));
    }
}
