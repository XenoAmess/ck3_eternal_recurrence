package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Real Win32 software peer/process only. No CK3, injection or native business result is claimed. */
@EnabledOnOs(OS.WINDOWS)
public final class NativeGameAttachmentTest {
    private static final String SHA="a".repeat(64);
    @TempDir Path temporary;

    private ControlBuild.FileRef ref(String name) {
        return new ControlBuild.FileRef(temporary.resolve(name).toAbsolutePath().toString(),1,SHA);
    }
    private NativeLaunchPlan plan(String pipe)throws IOException {
        Instant past=Instant.now().minusSeconds(60);
        String machine=WindowsJobProcess.currentMachineId();
        var review=new LaunchSourceBinding.Review(machine,past,ref("configured-game.exe"),ref("bridge.dll"),ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("env.json"),ref("build.json"),ref("register.json")),temporary,List.of(ref("runtime.jar")));
        var profile=new NativeLaunchPlan.PreparedProfile(ref("manifest.json"),temporary.resolve("mod"),"mod/example.mod",
                List.of(ref("input")),List.of(ref("mod/descriptor.mod")));
        return new NativeLaunchPlanCodec.Configuration("software-attachment","software-session",review,temporary,
                temporary.resolve("state"),temporary.resolve("evidence"),pipe,"attachment-test","attachment-adapter",
                new NativeLaunchPlan.NewGame(),false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),
                128L<<20,32L<<20,past,Duration.ofSeconds(1),Duration.ofSeconds(2),
                new SteamOfflineProbe.Plan(machine,ref("steam.exe"),past),profile,128).accept();
    }
    private WindowsJobProcess child(String pipe,boolean badFirst)throws IOException {
        Path root=Files.createDirectory(temporary.resolve("peer"));
        String cp=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        var args=new ArrayList<>(List.of("-Xms8m","-Xmx16m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=32m","-XX:ReservedCodeCacheSize=16m","-Xss256k",
                "-Djava.io.tmpdir="+System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir="+System.getProperty("jna.tmpdir",System.getProperty("java.io.tmpdir")),
                "-cp",cp,SoftwarePeer.class.getName(),pipe,Boolean.toString(badFirst)));
        var env=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        for(String name:List.of("JAVA_TOOL_OPTIONS","_JAVA_OPTIONS","JDK_JAVA_OPTIONS"))env.remove(name);
        return WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"),"bin/java.exe"),
                args,root,env,root.resolve("stdout.raw"),root.resolve("stderr.raw"),128L<<20));
    }
    private static Instant deadline(){return Instant.now().plusSeconds(10);}
    private static NativeGameAttachment.Request request(NativeLaunchPlan plan,WindowsJobProcess owner) {
        return new NativeGameAttachment.Request(plan,ManagedGameSession.generation(owner.identity()),List.of(),64,8);
    }
    private static void stopOwner(WindowsJobProcess owner)throws InterruptedException {
        if(owner.isRunning())owner.terminate(125);
        var terminal=owner.await(Duration.ofSeconds(3),Instant.now().plusSeconds(5),()->{});
        assertEquals(0,terminal.accounting().activeProcesses());
    }

    @Test void closeDisconnectsWithoutStopAndSameActualProcessAcceptsNewHello()throws Exception {
        String pipe="\\\\.\\pipe\\attachment-software-"+UUID.randomUUID();
        NativeLaunchPlan plan=plan(pipe);
        try(var owner=child(pipe,false)) {
            try {
                var identity=owner.identity();
                var first=NativeGameAttachment.attach(request(plan,owner),deadline());
                var firstTransport=first.nativeTransport();
                var firstHello=firstTransport.originalHello();
                assertEquals(ManagedGameSession.Mode.ATTACHED,first.mode());
                assertEquals(identity,first.identity());
                assertInstanceOf(GameLifecycle.Running.class,first.inspect(first.generation(),deadline()));
                assertThrows(IOException.class,()->first.stopTracked(first.generation(),deadline(),true));
                assertThrows(IOException.class,()->first.activateRuntime());
                first.close();first.close();
                assertTrue(owner.isRunning(),"worker close must not kill the actual target");
                assertEquals(identity,owner.identity());
                try(var second=NativeGameAttachment.attach(request(plan,owner),deadline())) {
                    assertEquals(identity,second.identity());
                    assertNotSame(firstTransport,second.nativeTransport());
                    assertTrue(second.nativeTransport().originalHello().connectionGeneration().compareTo(firstHello.connectionGeneration())>0);
                    assertInstanceOf(GameLifecycle.Running.class,second.inspect(second.generation(),deadline()));
                }
                assertTrue(owner.isRunning(),"second worker close must not kill the same target");
            } finally {stopOwner(owner);}
        }
    }

    @Test void failedHelloCleansOnlyAttachmentAndSameTargetCanReconnect()throws Exception {
        String pipe="\\\\.\\pipe\\attachment-failure-"+UUID.randomUUID();
        NativeLaunchPlan plan=plan(pipe);
        try(var owner=child(pipe,true)) {
            try {
                var identity=owner.identity();
                assertThrows(IOException.class,()->NativeGameAttachment.attach(request(plan,owner),deadline()));
                assertTrue(owner.isRunning(),"failed attachment must not stop the target");
                try(var recovered=NativeGameAttachment.attach(request(plan,owner),deadline())) {
                    assertEquals(identity,recovered.identity());
                    assertEquals(java.math.BigInteger.valueOf(2),recovered.nativeTransport().originalHello().connectionGeneration());
                    assertInstanceOf(GameLifecycle.Running.class,recovered.inspect(recovered.generation(),deadline()));
                }
                assertTrue(owner.isRunning());
            } finally {stopOwner(owner);}
        }
    }

    /** Actual pipe client in a separate ordinary Java process, with one monotonically increasing connection counter. */
    public static final class SoftwarePeer {
        public static void main(String[] args)throws Exception {
            if(args.length!=2)throw new IllegalArgumentException("pipe and first-HELLO mode required");
            String pipe=args[0];boolean badFirst=Boolean.parseBoolean(args[1]);long generation=0;
            Instant until=Instant.now().plusSeconds(30);
            while(Instant.now().isBefore(until)) {
                HANDLE client=Kernel32.INSTANCE.CreateFile(pipe,0xC0000000,0,null,3,0,null);
                if(client==null||WinBase.INVALID_HANDLE_VALUE.equals(client)){Thread.sleep(10);continue;}
                try {
                    generation++;
                    String bridge=badFirst&&generation==1?"wrong-bridge":"attachment-test";
                    String body="{\"type\":\"hello\",\"protocol_version\":1,\"pid\":"+ProcessHandle.current().pid()
                            +",\"connection_generation\":"+generation+",\"bridge_version\":\""+bridge
                            +"\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"attachment-adapter\","
                            +"\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}";
                    byte[] json=body.getBytes(StandardCharsets.UTF_8);
                    byte[] packet=ByteBuffer.allocate(4+json.length).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
                    int offset=0;
                    while(offset<packet.length) {
                        byte[] rest=java.util.Arrays.copyOfRange(packet,offset,packet.length);var written=new IntByReference();
                        if(!Kernel32.INSTANCE.WriteFile(client,rest,rest.length,written,null)||written.getValue()<=0)
                            throw new IOException("software HELLO write failed: "+Kernel32.INSTANCE.GetLastError());
                        offset+=written.getValue();
                    }
                    var received=new IntByReference();
                    while(Kernel32.INSTANCE.ReadFile(client,new byte[1],1,received,null)) {
                        if(received.getValue()<=0)break;
                    }
                } finally {Kernel32.INSTANCE.CloseHandle(client);}
            }
            throw new IOException("software peer bounded lifetime elapsed");
        }
    }
}
