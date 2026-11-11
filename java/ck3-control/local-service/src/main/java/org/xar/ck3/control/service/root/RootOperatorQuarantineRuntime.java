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
        var source=new CompositeOperatorQuarantineSource(configuredRequest,requestBytes,readExact(request.authorizedBy()),game.generation(),game.sessionId(),OrdinarySwayPolicy.OPERATION,SwayOrdinaryComposite.HANDLER,clock);
        core.bindOperatorQuarantineSource(source);
    }
    private static byte[] readExact(ExactRef reference)throws IOException {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=65536,"bounded explicit operator configuration required");
        byte[] raw;try(var stream=Files.newInputStream(Path.of(reference.path()))){raw=stream.readNBytes(65537);}
        if(raw.length!=reference.bytes()||!ActionCodec.sha256(raw).equals(reference.sha256()))throw new IOException("configured operator request/authorization exact bytes changed");
        return raw;
    }
}
