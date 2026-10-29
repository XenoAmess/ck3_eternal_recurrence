package org.xar.ck3.control.service;

import jakarta.enterprise.context.ApplicationScoped;
import java.util.Objects;
import java.io.IOException;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionController;

/** Same Quarkus host, one retained controller, one already-owned Game across all batch RPCs. */
@ApplicationScoped
public class OrdinarySessionHost {
    private final AtomicReference<SessionController> installed = new AtomicReference<>();
    private org.xar.ck3.control.service.root.RootSessionAccess root;
    /** Root's in-process assembly installs the qualified full graph. HTTP payloads cannot install authority. */
    public synchronized void install(SessionController controller) {
        if (!installed.compareAndSet(null, Objects.requireNonNull(controller)))
            throw new IllegalStateException("ordinary Game/session authority is already installed; no replacement or repeated launch");
    }
    public synchronized Optional<SessionController> current() { return Optional.ofNullable(installed.get()); }
    /** Root holds this exact controller; no HTTP unbind, null reset or later installation is permitted. */
    public synchronized void retire(SessionController expected) {
        if (installed.get() != Objects.requireNonNull(expected)) throw new IllegalArgumentException("retirement requires the original installed controller");
        expected.retire();
    }
    /** Root invokes this only after its actual restore binding and new authority have qualified. */
    public synchronized void replaceRetired(SessionController expected, SessionController successor) {
        requireRetiredReplacement(expected,successor);
        if (!installed.compareAndSet(expected, successor))
            throw new IllegalStateException("original installed owner changed before restored authority publication");
    }
    @FunctionalInterface public interface Publication { void publish() throws IOException; }
    /** Root's final candidate activation occurs after host preflight and before any caller can observe the successor. */
    public synchronized void publishRetired(SessionController expected,SessionController successor,Publication beforeVisible)throws IOException {
        Objects.requireNonNull(beforeVisible);requireRetiredReplacement(expected,successor);
        beforeVisible.publish();
        // All host mutations use this same monitor. No source validation or callback remains after the private publication returns.
        installed.set(successor);
    }
    private void requireRetiredReplacement(SessionController expected,SessionController successor) {
        Objects.requireNonNull(expected); Objects.requireNonNull(successor);
        if (!expected.isRetired() || expected.isRunning() || successor.isRetired() || successor.isRunning() || successor.isQuarantined()
                || !expected.identity().machineId().equals(successor.identity().machineId())
                || expected.identity().game().equals(successor.identity().game())
                || expected.identity().sessionId().equals(successor.identity().sessionId()))
            throw new IllegalArgumentException("replacement requires an inactive retired owner and a distinct qualified restored Game/session on the same machine");
        if (installed.get()!=expected)
            throw new IllegalStateException("original installed owner changed before restored authority publication");
    }
    /** Only the original Core can route public batches through its calls lock and post-turn publication. */
    public void bindRoot(org.xar.ck3.control.service.root.RootSessionAccess actual)throws IOException {
        Objects.requireNonNull(actual).requireHost(this);
        synchronized(this){
            if(root!=null&&root!=actual)throw new IOException("public batch routing cannot replace the original Core access");
            root=actual;
        }
        // Core publication holds Core before Host; never acquire that monitor while holding this Host monitor.
        actual.requireHost(this);
    }
    public BatchReport batch(String sessionId, BatchLimits limits) {
        org.xar.ck3.control.service.root.RootSessionAccess actual;
        synchronized(this){actual=root;}
        if(actual==null)throw new IllegalStateException("actual Root batch publication route has not been installed");
        try{return actual.batch(sessionId,Objects.requireNonNull(limits));}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("actual Root batch interrupted; retained work is not replayed",interrupted);}
        catch(IOException unavailable){throw new IllegalStateException("actual Root batch publication is unavailable",unavailable);}
    }
    public void requestStop(String sessionId) { selected(sessionId).requestStop(); }
    private SessionController selected(String sessionId) {
        SessionController value = current().orElseThrow(() -> new IllegalStateException("actual full ordinary session has not been installed by Root"));
        if (value.isRetired()) throw new IllegalStateException("original ordinary session has retired; transport authority cannot be reused");
        if (!value.identity().sessionId().equals(sessionId)) throw new IllegalArgumentException("request is bound to another session");
        return value;
    }
}
