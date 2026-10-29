package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.GameRestoreAdapter;
import org.xar.ck3.control.platform.GameRestoreNativeAdapter;
import org.xar.ck3.control.platform.ManagedGameSession;

/**
 * Public restoration uses the original physical lifecycle, private checkpoint materials and Core.
 * Retained UNKNOWN attempts query that same lifecycle request; no caller supplies a PID, path or pair.
 */
public final class RootPublicRestoreRuntime {
    /** Original Root capture under its call lock, physical freeze and existing writer. Data, not admission. */
    public record Captured(RestoreCheckpointService.Request original,DriverCheckpointStore drivers) {
        public Captured {Objects.requireNonNull(original);Objects.requireNonNull(drivers);}
    }
    /** Stable DATA identity of one exact starting writer/session/physical pair, shared with Root's capture. */
    public static String requestIdentity(SessionIdentity current,String headDigest,CheckpointPair pair) {
        Objects.requireNonNull(current);Objects.requireNonNull(pair);
        StrictJson.require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}"),"original public restore head digest required");
        StrictJson.require(current.machineId().equals(pair.frame().machineId()),"public restore pair belongs to another machine");
        var row=StrictJson.object();row.put("schema","xar.java-public-restore-request-identity/v1");
        row.set("current_session",OrdinaryCycleTransitions.sessionToJson(current));row.put("starting_head_sha256",headDigest);
        row.put("pair_sha256",ActionCodec.sha256(CheckpointPairCodec.encode(pair)));
        return "public-restore-"+ActionCodec.sha256(StrictJson.canonical(row));
    }
    private static final class Attempt {
        final RootCheckpointPublicCalls.Request publicRequest;
        final Captured captured;
        final RestoreCheckpointService service;
        final RetainedRuntimeCreation<RootRestoreAssemblyInputs> assembly=new RetainedRuntimeCreation<>();
        RestoreCheckpointService.Result result;
        RootApplicationSession successor;
        volatile boolean published;
        Attempt(RootCheckpointPublicCalls.Request request,Captured captured,RestoreCheckpointService service) {
            publicRequest=request;this.captured=captured;this.service=service;
        }
    }
    /** Retirement revokes ordinary work before the one existing lifecycle producer can enter STOP/CREATE. */
    private static final class RetiringLifecycle implements RestoreCheckpointService.LifecyclePort {
        final RootApplicationSession previous;
        final GameRestoreAdapter actual;
        RetiringLifecycle(RootApplicationSession previous,GameRestoreAdapter actual) {this.previous=previous;this.actual=actual;}
        @Override public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request)
                throws IOException,InterruptedException {
            if(previous.isRetired())throw new IOException("a new lifecycle dispatch cannot reuse an already retired public Root");
            previous.retire();return actual.replaceOnce(request);
        }
        @Override public RestoreCheckpointService.LaunchResult query(String requestId,Instant deadline)
                throws IOException,InterruptedException {
            return actual.query(requestId,deadline);
        }
    }
    private final RootStartupNextResources.Shared shared;
    private final Map<RootApplicationSession,Attempt> attempts=new IdentityHashMap<>();

    public RootPublicRestoreRuntime(RootStartupNextResources.Shared actual)throws IOException {
        shared=Objects.requireNonNull(actual);requireCore(actual.core());
    }
    public void requireCore(RootApplicationAssembly.Core actual)throws IOException {
        if(actual!=shared.core()||actual.archive().writer()!=actual.writer())
            throw new IOException("public restoration crossed its sole startup Core/writer/archive");
        shared.catalogs().requireBoundCore(actual);shared.storage().requireFilePort(shared.files());
        shared.episodes().requireCore(actual,shared.catalogs());
    }
    /** A narrow private-map fact for Core's retained-query route. It grants neither current readiness nor dispatch. */
    public boolean ownsPending(RootApplicationSession previous) {
        synchronized(attempts){var original=attempts.get(Objects.requireNonNull(previous));return original!=null&&!original.published;}
    }

    /** Called only by the actual Root while its original call lock is held, outside every writer freeze. */
    RootCheckpointPublicCalls.RestoreCall restore(RootApplicationSession previous,RootCheckpointPublicCalls.Request publicRequest,
            Instant callerDeadline)throws IOException,InterruptedException {
        Objects.requireNonNull(previous);Objects.requireNonNull(publicRequest);Objects.requireNonNull(callerDeadline);
        requireCore(shared.core());previous.requirePublicRestoreCall(this);
        if(shared.core().writer().activeSession().isPresent())
            throw new IOException("physical public restoration cannot run inside a borrowed writer freeze");
        if(!shared.clock().instant().isBefore(callerDeadline))throw new IOException("public restoration caller deadline expired");
        Attempt selected;
        synchronized(attempts){selected=attempts.get(previous);}
        if(selected==null){
            var captured=previous.capturePublicRestore(publicRequest,callerDeadline);
            selected=createAttempt(previous,publicRequest,captured,callerDeadline);
            synchronized(attempts){
                if(attempts.size()>=64)throw new IOException("bounded actual public restore attempts require original reconciliation");
                if(attempts.putIfAbsent(previous,selected)!=null)
                    throw new IOException("one Root cannot replace an entered public restore capture");
            }
        }
        Attempt original=selected;
        synchronized(original){
            if(!original.publicRequest.equals(publicRequest))
                throw new IOException("retained public restore request cannot change missing/null/exact expected revision");
            var request=original.captured.original();
            previous.requirePublicRestoreCall(this);
            if(original.result==null)original.result=original.service.restore(request);
            else if(!(original.result instanceof RestoreCheckpointService.Rejected))
                original.result=original.service.queryOriginal(request.requestId(),callerDeadline);
            var result=Objects.requireNonNull(original.result);
            if(!(result instanceof RestoreCheckpointService.Restored restored))
                return new RootCheckpointPublicCalls.RestoreCall(result,request.current(),Optional.empty());

            // queryOriginal retains the immutable body and privately renews only its finite read scope.
            // A cached binding is historical fact; current assembly and Host publication revalidate separately.
            ManagedGameSession replacement=shared.lifecycle().currentSession()
                    .orElseThrow(()->new IOException("actual private restored replacement disappeared"));
            if(!replacement.generation().equals(restored.binding().session().game())
                    ||!replacement.sessionId().equals(restored.binding().session().sessionId())
                    ||!replacement.machineId().equals(restored.binding().session().machineId()))
                throw new IOException("public restoration lost the actual lifecycle-owned replacement");
            var inputs=original.assembly.obtain(()->shared.core().writer().locked(same->
                    RootRestoreAssemblyInputs.create(same,shared,previous,original.service,restored.binding(),replacement)));
            if(original.successor==null)original.successor=inputs.assemble(callerDeadline);
            if(!original.published){
                original.successor.publishRestored(callerDeadline);
                // RestoreCall additionally requires the actual new Root/Host/session and real previous Game.
                var published=new RootCheckpointPublicCalls.RestoreCall(result,request.current(),Optional.of(original.successor));
                original.published=true;return published;
            }
            return new RootCheckpointPublicCalls.RestoreCall(result,request.current(),Optional.of(original.successor));
        }
    }

    private Attempt createAttempt(RootApplicationSession previous,RootCheckpointPublicCalls.Request request,
            Captured captured,Instant deadline)throws IOException {
        var core=shared.core();var original=captured.original();
        if(!previous.ownedBy(core)||previous.writer()!=core.writer()||previous.archive()!=core.archive()
                ||previous.isRetired()||!previous.hasInstalledHost()
                ||!original.current().observed().machineId().equals(previous.identity().machineId())
                ||!original.current().observed().game().equals(previous.identity().game())
                ||!original.current().sessionId().equals(previous.identity().sessionId())
                ||!original.current().source().equals(shared.source())||!original.deadline().equals(deadline)
                ||!original.requestId().equals(requestIdentity(previous.identity(),original.expectedHeadDigest(),original.pair())))
            throw new IOException("public restoration capture differs from its actual current Root/source/frame");
        previous.savedMaterials().requireOwn(original.savedMaterial());
        ManagedGameSession actual=shared.lifecycle().currentSession()
                .orElseThrow(()->new IOException("public restoration requires the lifecycle's actual current Managed Game"));
        actual.verify();
        if(!actual.generation().equals(previous.identity().game())||!actual.sessionId().equals(previous.identity().sessionId())
                ||!actual.machineId().equals(previous.identity().machineId()))
            throw new IOException("public restoration cannot borrow another full Game birth or native session");
        actual.launchPlan().sources().requireLoadedClass(RootPublicRestoreRuntime.class);
        actual.launchPlan().sources().requireLoadedClass(RootRestoreAssemblyInputs.class);
        var lifecycle=new RetiringLifecycle(previous,new GameRestoreAdapter(shared.lifecycle(),actual.launchPlan()));
        var nativeFrames=new GameRestoreNativeAdapter(shared.lifecycle(),shared.source(),original.pair().lineageId(),
                core.archive(),core.writer(),core.writer()::activeSession,core.writer()::requireSession);
        var service=new RestoreCheckpointService(shared.files(),captured.drivers(),lifecycle,nativeFrames,core.writer(),
                previous.savedMaterials(),previous.restoreAdapters(),previous.restoreAdapters(),shared.clock());
        return new Attempt(request,captured,service);
    }
}
