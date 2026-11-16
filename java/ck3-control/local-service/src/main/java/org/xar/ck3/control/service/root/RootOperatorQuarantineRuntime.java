package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineSource;
import org.xar.ck3.control.application.planning.sway.OrdinarySwayPolicy;
import org.xar.ck3.control.application.planning.sway.SwayOrdinaryComposite;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Explicit per-owner configuration only. Ordinary startup never appends an operator decision. */
final class RootOperatorQuarantineRuntime {
    private RootOperatorQuarantineRuntime() { }
    static void install(RootApplicationAssembly.Core core,ManagedGameSession game,ExactRef configuredRequest,Clock clock)throws IOException {
        byte[] requestBytes=readExact(configuredRequest);var request=CompositeOperatorQuarantineRequest.decode(requestBytes);
        StrictJson.require(request.machineId().equals(game.machineId()),"operator request belongs to another runtime machine");
        if(!request.game().equals(game.generation())) {
            game.verify();
            var historical=new CompositeOperatorQuarantineSource(configuredRequest,requestBytes,readExact(request.authorizedBy()),
                    request.game(),request.episodeRunId(),request.lifeInterruption()?new org.xar.ck3.control.application.action.OperationKey("life-advance"):OrdinarySwayPolicy.OPERATION,
                    request.lifeInterruption()?org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER:SwayOrdinaryComposite.HANDLER,clock);
            core.bindHistoricalOperatorQuarantineSource(game,historical);return;
        }
        var source=new CompositeOperatorQuarantineSource(configuredRequest,requestBytes,readExact(request.authorizedBy()),game.generation(),game.sessionId(),request.lifeInterruption()?new org.xar.ck3.control.application.action.OperationKey("life-advance"):OrdinarySwayPolicy.OPERATION,request.lifeInterruption()?org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER:SwayOrdinaryComposite.HANDLER,clock);
        core.bindOperatorQuarantineSource(source);
    }
    /** Only the actual lifecycle's source-qualified original exit can install this archive-only administrative source. */
    static void installExited(RootApplicationAssembly.Core core,
            org.xar.ck3.control.platform.JavaGameLifecycle lifecycle,
            org.xar.ck3.control.platform.JavaGameLifecycle.ExitedGeneration exited,
            ExactRef configuredRequest,Clock clock,java.time.Instant deadline)throws IOException {
        exited.requireOwner(lifecycle,deadline);
        byte[] requestBytes=readExact(configuredRequest);
        var request=CompositeOperatorQuarantineRequest.decode(requestBytes);
        StrictJson.require(request.lifeInterruption()&&!request.reservedTailInterruption()
                        &&request.machineId().equals(exited.machineId())&&request.game().equals(exited.generation())
                        &&request.episodeRunId().equals(exited.sourceSessionId()),
                "exited administrative source requires its exact v2 Life request and original owner");
        var source=new CompositeOperatorQuarantineSource(configuredRequest,requestBytes,readExact(request.authorizedBy()),
                exited.generation(),exited.sourceSessionId(),new org.xar.ck3.control.application.action.OperationKey("life-advance"),
                org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER,clock);
        exited.requireOwner(lifecycle,deadline);core.bindOperatorQuarantineSource(source);
    }
    /** The loaded role supplies only the old canonical subject; this path never captures or appends a decision. */
    static void installLoaded(RootApplicationAssembly.Core core,
            org.xar.ck3.control.platform.RootProcessAttach.LoadedReplacement loaded,
            ExactRef configuredRequest,Clock clock,java.time.Instant deadline)throws IOException {
        loaded.requireCurrent(deadline);
        byte[] bytes=readExact(configuredRequest);var request=CompositeOperatorQuarantineRequest.decode(bytes);
        var old=loaded.previousOwner();
        StrictJson.require(request.lifeInterruption()&&!request.reservedTailInterruption()
                &&request.machineId().equals(old.machineId())&&request.game().equals(old.game())
                &&request.episodeRunId().equals(old.sessionId()),"loaded recovery requires its actual old configured Life terminal source");
        var source=new CompositeOperatorQuarantineSource(configuredRequest,bytes,readExact(request.authorizedBy()),old.game(),old.sessionId(),
                new org.xar.ck3.control.application.action.OperationKey("life-advance"),
                org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER,clock);
        loaded.requireCurrent(deadline);core.bindOperatorQuarantineSource(source);
    }
    private static byte[] readExact(ExactRef reference)throws IOException {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=65536,"bounded explicit operator configuration required");
        byte[] raw;try(var stream=Files.newInputStream(Path.of(reference.path()))){raw=stream.readNBytes(65537);}
        if(raw.length!=reference.bytes()||!ActionCodec.sha256(raw).equals(reference.sha256()))throw new IOException("configured operator request/authorization exact bytes changed");
        return raw;
    }
}
