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
        StrictJson.require(request.exitedLife().isEmpty() && request.machineId().equals(game.machineId()),
                "a running or historical Game cannot install the exited-only administrative decision");
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
        StrictJson.require(request.matchesExitedOwner(exited.machineId(),exited.generation(),exited.sourceSessionId(),
                        java.util.Optional.of(exited.terminalReference())),
                "exited administrative source requires its exact original supervisor owner");
        java.util.Optional<org.xar.ck3.control.application.action.RawJson> terminal = java.util.Optional.empty();
        if (request.exitedLife().isPresent()) {
            StrictJson.require(!request.issuedAt().isBefore(exited.terminalObservedAt()),
                    "exited Life decision predates the original supervisor exit");
            terminal=java.util.Optional.of(new org.xar.ck3.control.application.action.RawJson(readExact(exited.terminalReference(),262144)));
        }
        var source=new CompositeOperatorQuarantineSource(configuredRequest,requestBytes,readExact(request.authorizedBy()),
                exited.generation(),request.episodeRunId(),new org.xar.ck3.control.application.action.OperationKey("life-advance"),
                org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER,clock,terminal);
        exited.requireOwner(lifecycle,deadline);core.bindOperatorQuarantineSource(source);
    }
    /** The loaded role supplies only the old canonical subject; this path never captures or appends a decision. */
    static void installLoaded(RootApplicationAssembly.Core core,
            org.xar.ck3.control.platform.RootProcessAttach.LoadedReplacement loaded,
            ExactRef configuredRequest,Clock clock,java.time.Instant deadline)throws IOException {
        loaded.requireCurrent(deadline);
        var terminal = loaded.cachedAck().importedSaveTransfer().isPresent()
                ? java.util.Optional.of(loaded.oldTerminal()) : java.util.Optional.<ExactRef>empty();
        var source = departedSource(loaded.previousOwner(), terminal, loaded.oldTerminalObservedAt(), configuredRequest, clock);
        loaded.requireCurrent(deadline);
        core.bindOperatorQuarantineSource(source);
    }

    /** The named-save role verifies the actual departed supervisor independently of the current Game. */
    static void installExternalSaved(RootApplicationAssembly.Core core,
            org.xar.ck3.control.platform.RootProcessAttach.ExternalSavedPredecessor predecessor,
            ExactRef configuredRequest, Clock clock, java.time.Instant deadline) throws IOException {
        predecessor.requireCurrent(deadline);
        var source = departedSource(predecessor.previousOwner(), java.util.Optional.of(predecessor.oldTerminal()),
                predecessor.oldTerminalObservedAt(), configuredRequest, clock);
        predecessor.requireCurrent(deadline);
        core.bindOperatorQuarantineSource(source);
    }

    private static CompositeOperatorQuarantineSource departedSource(
            org.xar.ck3.control.application.session.SessionPorts.SessionIdentity departed,
            java.util.Optional<ExactRef> terminalRef, java.time.Instant terminalObservedAt,
            ExactRef configuredRequest, Clock clock) throws IOException {
        var bytes = readExact(configuredRequest);
        var request = CompositeOperatorQuarantineRequest.decode(bytes);
        StrictJson.require(terminalRef.isPresent() == request.exitedLife().isPresent()
                && request.matchesExitedOwner(departed.machineId(), departed.game(), departed.sessionId(), terminalRef),
                "loaded recovery requires its actual old configured Life terminal source");
        var terminal = java.util.Optional.<org.xar.ck3.control.application.action.RawJson>empty();
        if (terminalRef.isPresent()) {
            StrictJson.require(!request.issuedAt().isBefore(terminalObservedAt),
                    "exited Life decision predates the original supervisor exit");
            terminal = java.util.Optional.of(new org.xar.ck3.control.application.action.RawJson(readExact(terminalRef.orElseThrow(), 262144)));
        }
        return new CompositeOperatorQuarantineSource(configuredRequest, bytes, readExact(request.authorizedBy()), departed.game(),
                request.episodeRunId(), new org.xar.ck3.control.application.action.OperationKey("life-advance"),
                org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER, clock, terminal);
    }

    static void requireRestorableOperatorRequest(ExactRef configuredRequest,boolean imported)throws IOException {
        boolean exitedLife=readConfigured(configuredRequest).exitedLife().isPresent();
        if (exitedLife!=imported) throw new IOException(imported
                ?"imported Saved recovery requires its own exited positive-RESUME operator decision"
                :"exited positive-RESUME recovery requires its explicit original imported Saved source");
    }
    static CompositeOperatorQuarantineRequest readConfigured(ExactRef configuredRequest)throws IOException {
        return CompositeOperatorQuarantineRequest.decode(readExact(configuredRequest));
    }
    private static byte[] readExact(ExactRef reference)throws IOException {
        return readExact(reference,65536);
    }
    private static byte[] readExact(ExactRef reference,int limit)throws IOException {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=limit,"bounded explicit operator original required");
        byte[] raw;try(var stream=Files.newInputStream(Path.of(reference.path()))){raw=stream.readNBytes(limit+1);}
        if(raw.length!=reference.bytes()||!ActionCodec.sha256(raw).equals(reference.sha256()))throw new IOException("configured operator request/authorization exact bytes changed");
        return raw;
    }
}
