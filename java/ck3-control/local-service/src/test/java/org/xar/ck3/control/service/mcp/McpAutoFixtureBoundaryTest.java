package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.ServiceLoader;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.service.root.FixtureCompositeActualTest;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** Real fixture coordinator/writer -> the encoder's identical origin guard -> Directory and both RPCs.
 * This tests rejection without manufacturing the gameplay Known required by a full AUTO report.
 * The software projection binding grants no Root, Ready, fixture, day or SAVE qualification. */
final class McpAutoFixtureBoundaryTest {
    private static final String NAME="ck3_auto_turn";

    @Test void actualCompletedFixtureCannotBecomeAnOrdinaryAutoSuccess() throws Exception {
        verify(FixtureCompositeActualTest.Scenario.COMPLETE);
    }

    @Test void actualUnknownFixtureIsRejectedWithoutReplayingItsOriginalChild() throws Exception {
        verify(FixtureCompositeActualTest.Scenario.START_UNKNOWN);
    }

    private static void verify(FixtureCompositeActualTest.Scenario scenario) throws Exception {
        var producers=ServiceLoader.load(FixtureCompositeActualTest.InputsProducer.class).stream().toList();
        if(producers.size()!=1)
            throw new IllegalStateException("MISSING_ACTUAL_ROOT_FIXTURE_COMPOSITE_INPUTS_NOT_RUN: public AUTO "+scenario);
        var input=producers.getFirst().get().open(scenario);
        FixturePlan.requireParent(input.parent());
        var receipt=input.menu().execute(input.parent());
        if(scenario==FixtureCompositeActualTest.Scenario.COMPLETE) {
            var settled=assertInstanceOf(ActionState.CompositeSettled.class,receipt.state());
            var proof=assertInstanceOf(ActionState.FixtureBusinessCompleted.class,settled.settlement()).observation();
            proof.validateParent(input.parent());
        } else assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());
        assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        var context=input.catalog().context();
        context.writer().locked(same->{
            var archive=context.archive().withSession(same);
            var before=context.core().actions().withFrozen(same,lease->lease.snapshot());
            String head=same.head().digest();
            assertEquals(receipt,archive.loadReceipt(archive.receiptReferenceOf(receipt)));
            byte[] wire=ActionReceiptCodec.encodeReceipt(receipt,archive);
            var restored=ActionReceiptCodec.decodeReceipt(wire,archive);
            assertEquals(receipt,restored);
            var failure=assertThrows(PublicServiceFailure.class,
                    ()->McpAutoTurnEncoder.requireOrdinaryOrigin(restored,archive));
            assertFault(failure,restored,archive);
            try { assertPublicBoundary(restored,archive); }
            catch(Exception problem) { throw new IOException("actual fixture public projection regression failed",problem); }
            assertEquals(head,same.head().digest());
            assertEquals(before,context.core().actions().withFrozen(same,lease->lease.snapshot()),
                    "public projection must not submit, reconcile or replace any original child attempt");
            return null;
        });
    }

    private static void assertFault(PublicServiceFailure actual,ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,actual.kind());
        assertEquals("native DLL does not implement gameplay step "+receipt.command().operation().value(),actual.getMessage());
        assertEquals(archive.receiptReferenceOf(receipt),actual.originalCandidate().orElseThrow());
    }

    private static void assertPublicBoundary(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) throws Exception {
        var original=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(NAME)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+NAME));
        var bindings=PublicMcpBindingTest.oneAdmitted(NAME);var calls=new AtomicInteger();
        // Actual retained DATA is returned to the real encoder guard. No success payload or Root is substituted.
        bindings.registerDirect(RootPublicCatalogCodec.executableTool(original),PublicMcpBindings.Kind.APPLICATION_COMPOSITE,
                RootMcpAutoTurn.Request.class,ActionReceipt.class,request->{calls.incrementAndGet();return receipt;},
                call->new RootMcpAutoTurn.Request(),response->{
                    McpAutoTurnEncoder.requireOrdinaryOrigin(response,archive);
                    throw new AssertionError("fixture was admitted by the ordinary AUTO public origin guard");
                },PublicMcpProtocolTest.target());
        var directory=bindings.freezeSoftwareScope();
        var error=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(NAME,"{}")));
        var originalFault=assertInstanceOf(PublicServiceFailure.class,error.getCause());
        assertFault(originalFault,receipt,archive);assertEquals(originalFault.getMessage(),error.getMessage());
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+NAME+"\",\"arguments\":{}"));
                var response=peer.receive();assertFalse(response.has("error"));var result=response.get("result");
                assertTrue(result.path("isError").booleanValue());assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+NAME+": "+originalFault.getMessage(),
                        result.get("content").get(0).get("text").textValue());
                var reparsed=McpJson.parseResult(new CallResult(McpJson.encode(result)).bytes());
                assertEquals(result,reparsed);
            }
        }
        assertEquals(3,calls.get());
    }

    @Test void unsupportedFixtureMessageMatchesTheOriginalPythonRaiseExpression() throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"canonical repository required");assertNotNull(python,"canonical Python required");
        assertFalse(repository.isBlank());assertFalse(python.isBlank());
        String code="import ast,hashlib,json,pathlib,sys\n"
                +"p=pathlib.Path(sys.argv[1])/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'\n"
                +"raw=p.read_bytes()\n"
                +"assert len(raw)==1658471 and hashlib.sha256(raw).hexdigest()=='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603'\n"
                +"tree=ast.parse(raw.decode('utf-8-sig'))\n"
                +"method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_execute_primitive_step')\n"
                +"raises=[n.exc for n in ast.walk(method) if isinstance(n,ast.Raise) and isinstance(n.exc,ast.Call) and isinstance(n.exc.func,ast.Name) and n.exc.func.id=='UnsupportedStepError']\n"
                +"message=next(n.args[0] for n in raises if isinstance(n.args[0],ast.JoinedStr) and isinstance(n.args[0].values[0],ast.Constant) and n.args[0].values[0].value=='native DLL does not implement gameplay step ')\n"
                +"expression=compile(ast.Expression(message),str(p),'eval')\n"
                +"print(json.dumps([{'kind':'UnsupportedStepError','message':eval(expression,{'step':step})} for step in sys.argv[2:]],separators=(',',':')))\n";
        var command=new java.util.ArrayList<String>(List.of(python,"-B","-c",code,repository));
        for(var kind:FixturePlan.Kind.values())command.add(kind.parentOperation().value());
        var process=new ProcessBuilder(command).directory(Path.of(repository).toFile()).redirectErrorStream(true).start();
        try {
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();fail("original Python unsupported-step oracle timed out");}
        } catch(InterruptedException interrupted) {Thread.currentThread().interrupt();throw new IOException(interrupted);}
        String output=new String(process.getInputStream().readAllBytes(),StandardCharsets.UTF_8);
        assertEquals(0,process.exitValue(),output);var rows=McpJson.parse(output.getBytes(StandardCharsets.UTF_8));
        assertEquals(FixturePlan.Kind.values().length,rows.size());
        for(int index=0;index<rows.size();index++) {
            assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP.pythonClassName(),rows.get(index).get("kind").textValue());
            assertEquals("native DLL does not implement gameplay step "+FixturePlan.Kind.values()[index].parentOperation().value(),
                    rows.get(index).get("message").textValue());
        }
    }
}
