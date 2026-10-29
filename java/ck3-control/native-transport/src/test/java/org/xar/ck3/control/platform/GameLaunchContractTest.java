package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

final class GameLaunchContractTest {
    @TempDir Path temporary;
    @Test void actualSharedArgumentProducerKeepsOriginalNativeNewAndSavedModes()throws Exception{
        assertEquals(List.of("-gdpr-compliant","-userdir="+temporary),NativeLaunchPlan.arguments(temporary,new NativeLaunchPlan.NewGame(),false));
        Path save=temporary.resolve("罗贝尔 1066.ck3");Files.writeString(save,"software-only");
        var load=new NativeLaunchPlan.SavedGame("罗贝尔 1066",ControlBuild.FileRef.measure(save));
        assertEquals(List.of("-debug_mode","-gdpr-compliant","-userdir="+temporary,"-loadsave=罗贝尔 1066"),NativeLaunchPlan.arguments(temporary,load,true));
    }
    @Test void ambiguousOrPathSaveOperandsRejectBeforeAnyCreatorExists()throws Exception{
        Path save=temporary.resolve("name.ck3");Files.writeString(save,"software-only");var ref=ControlBuild.FileRef.measure(save);
        for(String invalid:List.of("name.ck3","../name","path\\name","", "name.other"))assertThrows(IllegalArgumentException.class,()->new NativeLaunchPlan.SavedGame(invalid,ref));
        // A fresh owner may be observing a previous process's unresolved CREATE; absence is not rejection.
        var freshOwner=new JavaGameLifecycle(List.of());
        var first=assertInstanceOf(JavaGameLifecycle.Unknown.class,freshOwner.query("prior-process-launch"));
        assertEquals("prior-process-launch",first.requestId());assertNull(first.lastEvidence());
        assertEquals(first,freshOwner.query("prior-process-launch"));assertTrue(freshOwner.currentSession().isEmpty());
    }
    @Test void explicitGuiPoliciesRetainOldHiddenStdioModes(){
        assertEquals(WindowsJobProcess.ConsoleMode.NO_WINDOW,WindowsJobProcess.ConsoleMode.valueOf("NO_WINDOW"));
        assertEquals(WindowsJobProcess.ConsoleMode.DETACHED,WindowsJobProcess.ConsoleMode.valueOf("DETACHED"));
        assertNotEquals(WindowsJobProcess.ConsoleMode.GUI_MINIMIZED_NO_ACTIVATE,WindowsJobProcess.ConsoleMode.GUI_SHOWN_NO_ACTIVATE);
    }
    @Test void actualCreatorRetainsAnImmutableUniquePermissionSetBeforeAnyGameExists(){
        var permission=new NativePrivateActionPermission(new OperationKey("controlled-private-action"),"controlled-permission",
                new ExactRef("controlled-source",1,"a".repeat(64)),request->{},
                (config,hello,guard,request)->{throw new java.io.IOException("no physical qualification in this data-only test");});
        var supplied=new java.util.ArrayList<NativePrivateActionPermission>();supplied.add(permission);
        var owner=new JavaGameLifecycle(supplied);supplied.clear();
        assertEquals(1,owner.privateActions().size());assertSame(permission,owner.privateActions().getFirst());
        assertThrows(UnsupportedOperationException.class,()->owner.privateActions().clear());
        assertThrows(IllegalArgumentException.class,()->new JavaGameLifecycle(List.of(permission,permission)));
        assertTrue(owner.currentSession().isEmpty());
    }
}
