package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import java.nio.file.Files;
import java.nio.file.Path;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

public final class NativeGameAttachment {
    public record Request(NativeLaunchPlan plan,GameGeneration expectedGame,List<NativePrivateActionPermission> privatePermissions,int maximumFramesPerOperation,int maximumSubmissions) {
        public Request {
            Objects.requireNonNull(plan);
            Objects.requireNonNull(expectedGame);
            Objects.requireNonNull(privatePermissions);
            if(maximumFramesPerOperation<1||maximumFramesPerOperation>65536)throw new IllegalArgumentException("maximumFramesPerOperation out of range");
            if(maximumSubmissions<1||maximumSubmissions>1000000)throw new IllegalArgumentException("maximumSubmissions out of range");
            privatePermissions=List.copyOf(privatePermissions);
        }
    }

    public static ManagedGameSession attach(Request request,Instant deadline) throws IOException,InterruptedException {
        return attachConfigured(request,deadline,Optional.empty());
    }
    public static ManagedGameSession attach(Request request,Instant deadline,Duration readOperationTimeout) throws IOException,InterruptedException {
        Objects.requireNonNull(readOperationTimeout);
        if(readOperationTimeout.isNegative()||readOperationTimeout.isZero())throw new IllegalArgumentException("readOperationTimeout must be positive");
        return attachConfigured(request,deadline,Optional.of(readOperationTimeout));
    }
    private static ManagedGameSession attachConfigured(Request request,Instant deadline,Optional<Duration> readOperationTimeout) throws IOException,InterruptedException {
        Win32Host.deadline(deadline);
        String machineId=WindowsJobProcess.currentMachineId();
        WindowsJobProcess.ReadOnlyProcessHandle handle=null;
        NativePipeEndpoint endpoint=null;
        NativeGameTransport transport=null;
        try {
            handle=WindowsJobProcess.retainReadOnlyProcess(request.expectedGame().pid());
            final WindowsJobProcess.ReadOnlyProcessHandle retainedHandle=handle;
            WindowsJobProcess.ProcessIdentity identity=retainedHandle.identity();
            GameGeneration actualGeneration=ManagedGameSession.generation(identity);
            if(!actualGeneration.equals(request.expectedGame()))throw new IOException("Expected Game generation mismatch before HELLO");
            if(retainedHandle.waitZero()!=258L)throw new IOException("Expected Game generation not running before HELLO");

            NativePipeEndpoint.Config config=new NativePipeEndpoint.Config(
                request.plan().pipeName(),
                machineId,
                actualGeneration,
                request.plan().sessionId(),
                request.plan().bridgeVersion(),
                request.plan().sources().review().gameExecutable().sha256(),
                request.plan().adapterId()
            );
            NativeProcessGuard guard=(GameGeneration expected)->{
                try{
                    if(retainedHandle.waitZero()!=258L)throw new IOException("Attached Game generation exited or changed");
                    if(!expected.equals(ManagedGameSession.generation(retainedHandle.identity())))throw new IOException("Attached Game generation exited or changed");
                }catch(RuntimeException failure){throw new IOException("Attached Game generation exited or changed",failure);}
            };
            endpoint=NativePipeEndpoint.create(config,guard);
            transport=readOperationTimeout.isPresent()?new NativeGameTransport(endpoint,request.maximumFramesPerOperation(),request.maximumSubmissions(),request.privatePermissions(),readOperationTimeout.get()):new NativeGameTransport(endpoint,request.maximumFramesPerOperation(),request.maximumSubmissions(),request.privatePermissions());
            
            Path root=request.plan().evidenceRoot();
            Files.createDirectories(root);
            Path child=root.resolve(UUID.randomUUID().toString());
            Files.createDirectory(child);
            LifecycleEvidence evidence=new LifecycleEvidence(request.plan(),child,machineId);
            
            transport.awaitHello(deadline);
            
            if(retainedHandle.waitZero()!=258L)throw new IOException("Expected Game generation not running after HELLO");
            if(!ManagedGameSession.generation(retainedHandle.identity()).equals(actualGeneration))throw new IOException("Expected Game generation changed after HELLO");
            guard.verify(actualGeneration);
            
            byte[] hello=transport.lastOriginalPacket();
            Files.write(child.resolve("hello.json"),hello,java.nio.file.StandardOpenOption.CREATE_NEW);
            evidence.write(LifecycleEvidence.Event.HELLO,identity,null,null,null,"Actual reconnected HELLO; observer only; no Job or Stop authority");
            
            guard.verify(actualGeneration);
            return new ManagedGameSession(request.plan,retainedHandle,identity,actualGeneration,transport,evidence,config,guard);
        } catch (IOException|InterruptedException|RuntimeException failure) {
            if(transport!=null)try{transport.close();}catch(IOException|RuntimeException suppressed){failure.addSuppressed(suppressed);}
            if(endpoint!=null)try{endpoint.close();}catch(IOException|RuntimeException suppressed){failure.addSuppressed(suppressed);}
            if(handle!=null)try{handle.close();}catch(RuntimeException suppressed){failure.addSuppressed(new IOException("Handle close failed",suppressed));}
            throw failure;
        }
    }
}