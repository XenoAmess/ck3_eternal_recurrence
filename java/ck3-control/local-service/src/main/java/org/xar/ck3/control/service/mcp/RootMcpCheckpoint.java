package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.root.RootApplicationSession;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls.Request;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls.SaveCall;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls.RestoreCall;
import org.xar.ck3.control.service.root.RootSaveRuntime;
import org.xar.ck3.control.service.root.RootSessionAccess;

/** Public adapters follow the actual current catalog's SAVE owner across genuine Root publication. */
public final class RootMcpCheckpoint {
    @FunctionalInterface public interface Resolver {RootSaveRuntime current(RootApplicationSession actual)throws IOException;}
    private final RootSessionAccess sessions;private final Resolver resolver;
    private final Clock clock;private final Duration timeout;
    public RootMcpCheckpoint(RootSessionAccess sessions,Resolver currentSave,Clock clock,Duration timeout){
        this.sessions=Objects.requireNonNull(sessions);this.resolver=Objects.requireNonNull(currentSave);
        this.clock=Objects.requireNonNull(clock);this.timeout=Objects.requireNonNull(timeout);
        StrictJson.require(!timeout.isZero()&&!timeout.isNegative()&&timeout.compareTo(Duration.ofMinutes(30))<=0,
                "bounded actual public checkpoint timeout required");
    }
    public SaveCall save(Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->Objects.requireNonNull(resolver.current(root)).publicSave(root,request,deadline));}
        catch(IOException unavailable){throw new UncheckedIOException("actual Root SAVE unavailable",unavailable);}
    }
    public RestoreCall restore(Request request)throws InterruptedException {
        Objects.requireNonNull(request);var deadline=clock.instant().plus(timeout);
        try{return sessions.withCurrent(root->Objects.requireNonNull(resolver.current(root)).publicRestore(root,request,deadline));}
        catch(IOException unavailable){throw new UncheckedIOException("actual Root checkpoint restoration unavailable",unavailable);}
    }
    /** Only the actual SAVE service is admitted; the catalog preserves RESTORE as a required missing product. */
    public List<PublicBindings.BoundBinding> registerSaveOnly(PublicBindings registry,ExactRef actualThisSource){
        return bindSaveOnly(registry,actualThisSource,this::save);
    }
    static List<PublicBindings.BoundBinding> bindSaveOnly(PublicBindings registry,ExactRef actualThisSource,PublicRoutes.Handler<Request,SaveCall> actualSave){
        Objects.requireNonNull(registry);Objects.requireNonNull(actualThisSource);
        var save=registry.register(PublicMethod.SAVE_CHECKPOINT,Request.class,SaveCall.class,Objects.requireNonNull(actualSave),
                CheckpointPublicCodec::decode,CheckpointPublicCodec::save,
                new PublicRoutes.Target(RootMcpCheckpoint.class.getName(),"save",actualThisSource),PublicRoutes.Status.IMPLEMENTED,
                "actual current Root SAVE service, original once-only contexts, canonical result and physical paired Driver; UNKNOWN is not resubmitted");
        return List.of(save);
    }
}
