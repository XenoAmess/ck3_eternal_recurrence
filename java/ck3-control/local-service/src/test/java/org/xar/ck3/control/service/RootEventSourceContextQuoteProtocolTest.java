package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.parallel.Isolated;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootBootstrapOutputContract;
import org.xar.ck3.control.service.root.RootBootstrapProtocol;
import org.xar.ck3.control.service.root.RootEventSourceContextProducer;
import org.xar.ck3.control.service.root.RootJavaBootstrapInputs;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Real source publisher and original request through the CLI consumed by the independent issuer.
 * The existing stock fixture supplies source bytes; no Native/Game observation is granted. */
@Isolated("the actual bootstrap CLI emits its protocol frame to System.out")
final class RootEventSourceContextQuoteProtocolTest {
    @TempDir Path directory;

    @Test void emptySourcePublisherThroughOriginalCliProducesTheExactIssuerQuoteWithoutWritingData()throws Exception {
        var sources=new OfflineInteractionCorpus(directory.resolve("sources"));
        Files.createDirectories(sources.grants.getParent());
        var publication=EvidenceGrantManifestPublisher.publish(sources.grants,List.of());
        assertEquals(0,publication.grants());
        var manifest=SharedSourceFiles.observe(sources.grants);
        assertEquals(publication.sha256(),manifest.source().sha256());
        Path asset=Files.createDirectory(directory.resolve("event"));
        Path target=asset.resolve("trusted-event-source-context.json");
        Instant now=Clock.systemUTC().instant();
        var request=new RootEventSourceContextProducer.Request(RootEventSourceContextProducer.SCHEMA,
                WindowsJobProcess.currentMachineId(),now.minusSeconds(1).toString(),now.plusSeconds(300).toString(),
                RootJavaBootstrapInputs.Mode.QUOTE,null,sources.state.toString(),sources.game.toString(),
                manifest.source(),target.toString().replace('\\','/'));
        byte[] originalBytes=RootEventSourceContextProducer.encode(request);
        Path requestPath=directory.resolve("event-request.json");Files.write(requestPath,originalBytes);
        var original=SharedSourceFiles.observe(requestPath);
        String forwardPath=original.source().path().replace('\\','/');
        assertEquals(Path.of(original.source().path()),Path.of(forwardPath));
        var wrongBytes=assertThrows(java.io.IOException.class,()->RootJavaBootstrapInputs.main(new String[]{
                forwardPath,Long.toString(original.source().bytes()+1),original.source().sha256()}));
        assertEquals("bootstrap input differs from its exact source",wrongBytes.getMessage());
        var wrongSha=assertThrows(java.io.IOException.class,()->RootJavaBootstrapInputs.main(new String[]{
                forwardPath,Long.toString(original.source().bytes()),"0".repeat(64)}));
        assertEquals("bootstrap input differs from its exact source",wrongSha.getMessage());
        byte[] canonicalWire=null;
        for(String argvPath:List.of(original.source().path(),forwardPath)){
            var stdout=new ByteArrayOutputStream();PrintStream prior=System.out;
            try(var capture=new PrintStream(stdout,true,StandardCharsets.UTF_8)){
                System.setOut(capture);
                try{RootJavaBootstrapInputs.main(new String[]{argvPath,Long.toString(original.source().bytes()),original.source().sha256()});}
                finally{System.setOut(prior);}
            }
            if(canonicalWire==null)canonicalWire=stdout.toByteArray();
            else assertArrayEquals(canonicalWire,stdout.toByteArray(),"Path spelling must preserve the exact issuer quote");
        }
        var quote=RootBootstrapProtocol.line(canonicalWire,RootBootstrapProtocol.Quote.class);
        assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals("xar.java-root-bootstrap-phase-quote/v1",quote.schema());
        assertEquals("TRUSTED_EVENT_SOURCE_CONTEXT",quote.phase());
        assertEquals(request.machineId(),quote.machineId());assertEquals(request.reviewAtUtc(),quote.reviewAtUtc());
        assertEquals(asset.toString(),quote.assetRoot());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",quote.authority());
        assertEquals(List.of(),quote.outputDirectories());assertEquals(List.of(),quote.retainedInputs());
        var prepared=RootEventSourceContextProducer.prepare(request,Clock.systemUTC());
        assertEquals(prepared.quote(),quote.outputs());
        assertEquals(RootBootstrapOutputContract.Kind.TRUSTED_EVENT_SOURCE_CONTEXT,quote.outputs().getFirst().kind());
        assertEquals(List.of(),prepared.context().evidenceGrants());
        assertFalse(Files.exists(target));
        try(var entries=Files.list(asset)){assertEquals(0,entries.count());}
        assertArrayEquals(originalBytes,Files.readAllBytes(requestPath));
        SharedSourceFiles.assertUnchanged(original);SharedSourceFiles.assertUnchanged(manifest);
    }
}
