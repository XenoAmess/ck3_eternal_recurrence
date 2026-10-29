package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Only the software MCP boundary is exercised; no physical Root, action or Native readiness is created. */
final class PublicServiceFailureTest {
    private static final String NAME="ck3_change_steward_develop_county_task_v1";
    private static final String ARGUMENTS="{\"councillor_character_id\":1,\"target_county_title_id\":2,\"expected_revision\":\"1\",\"replace_existing_task\":false}";
    private record Input() { }
    private static PublicMcpDirectory directory(PublicServiceFailure fault,AtomicInteger invoked,AtomicInteger encoded)throws Exception {
        return directory(NAME,fault,invoked,encoded);
    }
    private static PublicMcpDirectory directory(String name,PublicServiceFailure fault,AtomicInteger invoked,AtomicInteger encoded)throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
        var bindings=PublicMcpBindingTest.oneAdmitted(name);
        bindings.registerDirect(RootPublicCatalogCodec.executableTool(descriptor),PublicMcpBindings.Kind.APPLICATION_COMPOSITE,
                Input.class,RawJson.class,request->{invoked.incrementAndGet();throw fault;},call->new Input(),
                result->{encoded.incrementAndGet();return CallResult.fromBusinessJson(result);},PublicMcpProtocolTest.target());
        return bindings.freezeSoftwareScope();
    }
    @Test void exactGiftSubtypeAndOriginalMessageRemainDistinctAtPlanDirectoryAndBothRpcVersions()throws Exception {
        String name="ck3_plan_turn";
        String message="private faction pending receipt has a newer same-date paused frame";
        var kind=PublicServiceFailure.Kind.exact("FactionGiftPendingFrameReadyError");
        assertEquals(PublicServiceFailure.Kind.FACTION_GIFT_PENDING_FRAME_READY,kind);
        assertNotEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,kind);
        assertNotEquals(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,kind);
        // Public error DATA only. The actual private wait/proof issuer and exhausted retry
        // producer are tested by Finance/Planner; no proof, receipt or private failure is minted here.
        var source=new PublicServiceFailure(kind,message,Optional.empty());
        var invoked=new AtomicInteger();var encoded=new AtomicInteger();
        var directory=directory(name,source,invoked,encoded);
        var failure=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(name,"{}")));
        assertSame(source,failure.getCause());assertEquals(message,failure.getMessage());
        assertTrue(source.originalCandidate().isEmpty(),"this actual subtype has no original READ request/result ref");
        for(String version:new String[]{"2025-11-25",PublicMcpSession.MODERN}) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+name+"\",\"arguments\":{}"));
                var response=peer.receive();assertFalse(response.has("error"));var result=response.get("result");
                assertTrue(result.get("isError").booleanValue());assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+name+": "+message,result.get("content").get(0).get("text").textValue());
            }
        }
        assertEquals(3,invoked.get());assertEquals(0,encoded.get());
    }
    @Test void exactGiftClassParentAndMessageMatchThePinnedOriginalPythonProducer()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"canonical repository required");assertNotNull(python,"canonical Python required");
        assertFalse(repository.isBlank());assertFalse(python.isBlank());
        String code="import ast,hashlib,json,pathlib,sys\n"
                +"p=pathlib.Path(sys.argv[1])/'ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py'\n"
                +"raw=p.read_bytes()\n"
                +"assert len(raw)==25674 and hashlib.sha256(raw).hexdigest()=='90d80bc2602095cfbf81e58e737089df20cde5d4eddb1af3f4d7f2544b7e4310'\n"
                +"tree=ast.parse(raw.decode('utf-8-sig'))\n"
                +"cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FactionGiftPendingFrameReadyError')\n"
                +"init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')\n"
                +"calls=[n for n in ast.walk(init) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='__init__' and isinstance(n.func.value,ast.Call) and isinstance(n.func.value.func,ast.Name) and n.func.value.func.id=='super']\n"
                +"assert len(cls.bases)==1 and isinstance(cls.bases[0],ast.Name) and len(calls)==1\n"
                +"print(json.dumps({'kind':cls.name,'parent':cls.bases[0].id,'message':ast.literal_eval(calls[0].args[0])},separators=(',',':')))\n";
        var process=new ProcessBuilder(python,"-B","-c",code,repository).directory(java.nio.file.Path.of(repository).toFile()).redirectErrorStream(true).start();
        try {
            if(!process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){process.destroyForcibly();fail("original gift subtype oracle timed out");}
        } catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new java.io.IOException(interrupted);}
        String output=new String(process.getInputStream().readAllBytes(),java.nio.charset.StandardCharsets.UTF_8);
        assertEquals(0,process.exitValue(),output);var actual=McpJson.parse(output.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertEquals(PublicServiceFailure.Kind.FACTION_GIFT_PENDING_FRAME_READY.pythonClassName(),actual.get("kind").textValue());
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH.pythonClassName(),actual.get("parent").textValue());
        assertEquals("private faction pending receipt has a newer same-date paused frame",actual.get("message").textValue());
        assertEquals(PublicServiceFailure.Kind.FACTION_GIFT_PENDING_FRAME_READY,
                PublicServiceFailure.Kind.exact(actual.get("kind").textValue()));
    }
    @Test void typedServiceFaultPreservesExactKindMessageAndOptionalEvidenceAtTheExistingToolBoundary()throws Exception {
        for(var kind:PublicServiceFailure.Kind.values()) {
            // Explicit synthetic DATA evidence only, never a source-qualified candidate or permission.
            var evidence=Optional.of(new ExactRef("D:/test-only/steward-candidate-receipt.json",1,"a".repeat(64)));
            var fault=new PublicServiceFailure(kind,"original service message\nwith detail",evidence);
            var invoked=new AtomicInteger();var encoded=new AtomicInteger();var directory=directory(fault,invoked,encoded);
            var actual=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(NAME,ARGUMENTS)));
            assertEquals(fault.getMessage(),actual.getMessage());assertSame(fault,actual.getCause());
            var retained=(PublicServiceFailure)actual.getCause();assertEquals(kind,retained.kind());assertEquals(evidence,retained.originalCandidate());
            assertEquals(kind,PublicServiceFailure.Kind.exact(kind.pythonClassName()));assertEquals(1,invoked.get());assertEquals(0,encoded.get());
        }
        assertThrows(IllegalArgumentException.class,()->PublicServiceFailure.Kind.exact("unknown failure"));
    }
    @Test void theActualRpcSessionUsesTheOriginalSdkToolErrorEnvelopeAndUnmodifiedServiceMessage()throws Exception {
        for(String version:new String[]{"2025-11-25",PublicMcpSession.MODERN}) for(var kind:PublicServiceFailure.Kind.values()) {
            var invoked=new AtomicInteger();var encoded=new AtomicInteger();
            var fault=new PublicServiceFailure(kind,"original typed service fault",Optional.empty());
            try(var peer=new PublicMcpProtocolTest.Peer(directory(fault,invoked,encoded))) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+NAME+"\",\"arguments\":"+ARGUMENTS));
                var response=peer.receive();var result=response.get("result");assertTrue(result.get("isError").booleanValue());
                assertEquals("Error executing tool "+NAME+": "+fault.getMessage(),result.get("content").get(0).get("text").textValue());
                assertFalse(result.has("structuredContent"));assertFalse(response.has("error"));
            }
            assertEquals(1,invoked.get());assertEquals(0,encoded.get());
        }
    }
    @Test void semanticDecoderFaultKeepsTheOriginalSdkErrorAndNeverDispatches()throws Exception {
        for(String version:new String[]{"2025-11-25",PublicMcpSession.MODERN}) {
            var invoked=new AtomicInteger();var encoded=new AtomicInteger();
            var fault=new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,"original nonce or law validation message",Optional.empty());
            var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(NAME)).findFirst().orElseThrow();
            var bindings=PublicMcpBindingTest.oneAdmitted(NAME);
            bindings.registerDirect(RootPublicCatalogCodec.executableTool(descriptor),PublicMcpBindings.Kind.APPLICATION_COMPOSITE,
                    Input.class,RawJson.class,request->{invoked.incrementAndGet();return new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));},call->{throw fault;},
                    result->{encoded.incrementAndGet();return CallResult.fromBusinessJson(result);},PublicMcpProtocolTest.target());
            var directory=bindings.freezeSoftwareScope();
            var actual=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(NAME,ARGUMENTS)));
            assertSame(fault,actual.getCause());assertEquals(fault.getMessage(),actual.getMessage());
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+NAME+"\",\"arguments\":"+ARGUMENTS));
                var response=peer.receive();var result=response.get("result");
                assertTrue(result.get("isError").booleanValue());assertFalse(response.has("error"));assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+NAME+": "+fault.getMessage(),result.get("content").get(0).get("text").textValue());
            }
            assertEquals(0,invoked.get());assertEquals(0,encoded.get());
        }
    }
    @Test void invalidPublicArgumentsStillFailBeforeServiceFaultOrAnyApplicationInvocation()throws Exception {
        var invoked=new AtomicInteger();var encoded=new AtomicInteger();
        var fault=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"original missing material",Optional.empty());
        var directory=directory(fault,invoked,encoded);
        var actual=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(NAME,ARGUMENTS.replace("\"expected_revision\":\"1\"","\"expected_revision\":true"))));
        assertEquals("invalid tool arguments; no application invocation occurred",actual.getMessage());assertEquals(0,invoked.get());assertEquals(0,encoded.get());
    }
}
