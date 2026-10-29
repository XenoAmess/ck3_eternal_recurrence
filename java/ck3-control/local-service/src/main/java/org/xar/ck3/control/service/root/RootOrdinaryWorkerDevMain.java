package org.xar.ck3.control.service.root;

import io.quarkus.arc.profile.IfBuildProfile;
import io.quarkus.runtime.LaunchMode;
import io.quarkus.runtime.Quarkus;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import io.quarkus.runtime.annotations.CommandLineArguments;
import io.quarkus.runtime.annotations.QuarkusMain;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.Arrays;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.eclipse.microprofile.config.ConfigProvider;
import org.xar.ck3.control.contracts.StrictJson;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Dev-only CDI lifecycle delegation. The existing worker owns every business transition. */
@QuarkusMain(name="ordinary-worker-dev")
@ApplicationScoped
@IfBuildProfile("dev")
public class RootOrdinaryWorkerDevMain implements QuarkusApplication {
    @Inject @CommandLineArguments String[] arguments;
    private final CompletableFuture<Integer> completion=new CompletableFuture<>();
    private final byte[] stopBody=("ordinary-worker-dev "+UUID.randomUUID()+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    private RootOrdinaryRuntimeConfiguration configuration;
    private volatile boolean started;
    private volatile boolean ownStop;
    private FileChannel lockChannel;
    private FileLock lockHandle;
    private final String instanceId = UUID.randomUUID().toString();

    private enum Phase { DELEGATE_STARTED, DELEGATE_COMPLETED }

    private static boolean enabled() {
        var config=ConfigProvider.getConfig();
        return config.getOptionalValue("xar.worker.dev.enabled",Boolean.class).orElse(false)
                &&config.getOptionalValue("quarkus.package.main-class",String.class).orElse("").equals("ordinary-worker-dev");
    }

    @Override public int run(String... unused) {
        if(LaunchMode.current()!=LaunchMode.DEVELOPMENT||!enabled())
            throw new IllegalStateException("select ordinary-worker-dev and explicitly enable xar.worker.dev.enabled in development mode");
        Quarkus.waitForExit();
        return 0;
    }

    void start(@Observes StartupEvent event) throws Exception {
        // Other Quarkus dev mains must not read worker arguments/configuration or create worker resources.
        if(LaunchMode.current()!=LaunchMode.DEVELOPMENT||!enabled())return;
        if(arguments.length!=2)throw new IllegalArgumentException("ordinary-worker-dev requires owner.json and existing business configuration; it only resumes");
        configuration=RootOrdinaryRuntimeConfiguration.read(Path.of(arguments[1]));
        String[] actual={arguments[0],arguments[1],"resume"};
        Files.createDirectories(configuration.stateDirectory());
        try {
            lockChannel=FileChannel.open(configuration.stateDirectory().resolve("ordinary-worker-dev.lock"),StandardOpenOption.CREATE,StandardOpenOption.WRITE);
            lockHandle=lockChannel.tryLock();
            if(lockHandle==null)throw new IOException("previous dev worker still owns its runtime lock");
        } catch(IOException|RuntimeException failure) {
            closeOwnership(failure); // Only this attempt's channel/lock; never the existing owner.
            throw failure;
        }
        started=true;
        try {
            Thread.ofPlatform().name("ordinary-worker-dev-business").start(()->execute(actual));
        } catch(RuntimeException|Error failure) {
            started=false;
            closeOwnership(failure);
            completion.completeExceptionally(failure);
            throw failure;
        }
    }

    private void execute(String[] actual) {
        int exit=4;
        Throwable failure=null;
        boolean delegateReturned=false;
        try {
            emitObservation(Phase.DELEGATE_STARTED, null, null);
            // This returns only after the existing Main's actual business-resource finally.
            exit=new RootOrdinaryWorkerMain().run(actual);
            delegateReturned=true;
        } catch(Throwable failed) {
            failure=failed;
            failed.printStackTrace();
        } finally {
            // Shutdown timeouts/observer exceptions NEVER run this cleanup on the old worker's behalf.
            synchronized(this) {
                // The adapter's stop ends with this delegate; failure/UNKNOWN stays in the original business result.
                try { removeOwnStop(); }
                catch(Throwable cleanup) { failure=merge(failure,cleanup); }
                failure=closeOwnership(failure);
                emitObservation(Phase.DELEGATE_COMPLETED, delegateReturned ? exit : null, failure);
                if(failure==null)completion.complete(exit);
                else completion.completeExceptionally(failure);
            }
        }
        if(failure!=null||exit!=0)System.err.println("ordinary-worker-dev retained worker failure/exit "+exit+"; development host stays available for explicit reload; no clean restart was claimed");
    }

    void shutdown(@Observes ShutdownEvent event) throws Exception {
        if(!started)return;
        synchronized(this) {
          if(!completion.isDone()) {
            try {
                Files.write(configuration.stopPath(),stopBody,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
                ownStop=true;
            } catch(java.nio.file.FileAlreadyExistsException operatorStop) {
                // A pre-existing operator request is never overwritten or removed by this adapter.
            }
          }
        }
        // No interrupt, cancel, forced Native close or Game STOP/START. Actual pending/canonical state stays original.
        Duration wait=configuration.loop().wallTime().plus(configuration.operationTimeout()).plusSeconds(90);
        final int exit;
        try { exit=completion.get(wait.toMillis(),TimeUnit.MILLISECONDS); }
        catch(java.util.concurrent.ExecutionException completedFailure) {
            System.err.println("ordinary-worker-dev retained completed worker failure; no clean restart was claimed: "+completedFailure.getCause());
            return;
        }
        if(exit!=0)System.err.println("ordinary-worker-dev retained non-clean worker exit "+exit+"; no clean restart was claimed");
    }

    // Called only after the actual worker has returned, before unlocking or notifying waiters.
    private void removeOwnStop() throws IOException {
        if(ownStop&&Files.exists(configuration.stopPath())
                &&Arrays.equals(Files.readAllBytes(configuration.stopPath()),stopBody))Files.delete(configuration.stopPath());
    }

    private Throwable closeOwnership(Throwable failure) {
        try {if(lockHandle!=null&&lockHandle.isValid())lockHandle.release();}
        catch(Throwable close) {failure=merge(failure,close);}
        finally {lockHandle=null;}
        try {if(lockChannel!=null)lockChannel.close();}
        catch(Throwable close) {failure=merge(failure,close);}
        finally {lockChannel=null;}
        return failure;
    }
    private static Throwable merge(Throwable failure,Throwable close) {
        if(failure==null)return close;
        if(failure!=close)failure.addSuppressed(close);
        return failure;
    }

    private void emitObservation(Phase phase, Integer exitCode, Throwable failure) {
        try {
            ObjectNode node = StrictJson.object();
            node.put("schema", "xar.java-ordinary-worker-dev-lifecycle/v1");
            node.put("machine_id", configuration.machineId());
            node.put("observed_at_utc", java.time.Instant.now().toString());
            node.put("instance_id", instanceId);
            node.put("host_pid", String.valueOf(ProcessHandle.current().pid()));
            node.put("runtime_classloader", String.valueOf(this.getClass().getClassLoader()) + "@" + Integer.toHexString(System.identityHashCode(this.getClass().getClassLoader())));
            node.put("business_classloader", String.valueOf(RootOrdinaryWorkerMain.class.getClassLoader()) + "@" + Integer.toHexString(System.identityHashCode(RootOrdinaryWorkerMain.class.getClassLoader())));
            node.put("status", phase.name());
            if (exitCode == null) {
                node.putNull("exit_code");
            } else {
                node.put("exit_code", exitCode);
            }
            if (failure == null) {
                node.putNull("failure_type");
            } else {
                node.put("failure_type", failure.getClass().getName());
            }
            byte[] json = StrictJson.canonical(node, StrictJson.OUTPUT_MAX_BYTES);
            System.out.println(new String(json, java.nio.charset.StandardCharsets.UTF_8));
        } catch (Throwable ignored) {
            // Best-effort observation: JSON/output failure must never skip delegate execution or ownership release
        }
    }
}
