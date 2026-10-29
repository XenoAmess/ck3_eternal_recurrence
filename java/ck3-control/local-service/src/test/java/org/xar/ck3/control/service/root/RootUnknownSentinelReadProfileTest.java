package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.reconciliation.LateOutcome;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** DATA/source-factory tests do not construct a private Root, lease or fake Gameplay qualification. */
public final class RootUnknownSentinelReadProfileTest {
    private static final String MAX="18446744073709551615";
    /** Shared finite software packet fixture uses the one existing typed status producer, not a second parser. */
    public static RawJson statusResult() {
        var status=new Status(LateOutcome.State.IDLE,new CrossJsDecimalUInt64(MAX),1000,1001,1000,0,2,
                LateOutcome.Mode.TERMINAL_OR_SENTINEL,0,0,0,0,0,List.of(),-1,-1,false,false,false,false);
        var row=StrictJson.object().put("step",ClockStatusRead.STEP).put("accepted",true).put("status","available");
        row.set("tactical_daily_sentinel",SentinelObservation.toJson(status));return PublicDataJson.encode(row);
    }
    /** Actual source/guard/coordinator/transport consumer hook; caller retains its genuine private
     * scope and archive. No constructor here grants a Root or substitutes a physical source. */
    public static RawJson assertActualRead(ReadContract<Status> actualProfile,PlanningReadResult.Known<Status> known,
            ActionPorts.OutcomeArchive archive)throws Exception {
        assertEquals(actualProfile.contractId(),known.receipt().contractId());
        if(actualProfile.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION)RootUnknownSentinelReadProfile.requireProfile(actualProfile);
        else if(actualProfile.guardMode()==ReadContract.GuardMode.STATUS_ONLY)RootUnknownSentinelReadProfile.requirePhysicalProfile(actualProfile);
        else RootUnknownSentinelReadProfile.requireTerminalProfile(actualProfile);
        assertEquals(known.originalReceipt(),archive.readReferenceOf(known.receipt()));
        var retained=archive.loadRead(known.originalReceipt());assertEquals(known.receipt(),retained);
        assertEquals(known.value(),actualProfile.replay(retained));assertEquals(known.value(),actualProfile.decode(known.receipt()));
        var evidence=archive.referenceOf(known.receipt().original());assertEquals(known.receipt().original(),archive.load(evidence));
        if(actualProfile.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION)
            assertEquals(known.value(),new RootUnknownSentinelReadProfile.ReconObservation(known.value(),known.receipt(),evidence).status());
        else if(actualProfile.guardMode()==ReadContract.GuardMode.STATUS_ONLY)assertEquals(known.value(),new RootUnknownSentinelReadProfile.PhysicalObservation(known.value(),known.receipt(),evidence).status());
        else assertEquals(known.value(),new RootUnknownSentinelReadProfile.TerminalObservation(known.value(),known.receipt(),evidence).status());
        byte[] original=known.receipt().original().originalResultToken().orElseThrow().bytes();
        RawJson result=RootDriverTransportPublicSupplier.sentinelResult(known.receipt(),known.value());
        var descriptor=RootPublicCatalogCodec.executableTool(RootOriginalPublicTestInputs.tools().stream()
                .filter(value->value.name().equals("ck3_read_tactical_daily_sentinel_status_private_v1")).findFirst().orElseThrow());
        descriptor.validateArguments(new org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments(
                org.xar.ck3.control.service.mcp.PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(new byte[]{'{','}'}))));
        var callResult=org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult.fromBusinessJson(result);descriptor.validateResult(callResult);
        var envelope=DriverJson.object(callResult.bytes(),RawJson.MAXIMUM_BYTES);
        var business=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(envelope.get("structuredContent"),"sentinel structured result");
        var content=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.array(envelope.get("content"),"content").getFirst(),"text content");
        assertEquals(business,DriverJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(content.get("text"),"text").getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        var status=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(business.get("tactical_daily_sentinel"),"sentinel status");
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(known.value().generation().decimal()),status.get("generation"));
        assertArrayEquals(original,known.receipt().original().originalResultToken().orElseThrow().bytes());return result;
    }
    private static ExactRef nativeDefinition()throws Exception {
        String root=System.getProperty("xar.repository.root");assertNotNull(root,"NOT_RUN_REQUIRED_ORIGINAL_REPOSITORY");
        var actual=SharedSourceFiles.observe(Path.of(root).resolve("ck3_autonomous_player/native_bridge/src/bridge.cpp"));
        assertEquals(1611813,actual.source().bytes());assertEquals("41a3e271793e59cb87469324f0ef04611cc0277bedcc06d6fe1043c10fb83953",actual.source().sha256());
        SharedSourceFiles.assertUnchanged(actual);return new ExactRef(actual.source().path(),actual.source().bytes(),actual.source().sha256());
    }
    @Test void twoPhaseFactoryUsesTheOneOriginalClockObjectAndCopiedMetadataNeverIssuesAProfile()throws Exception {
        var ordinary=ClockStatusRead.registeredContract(nativeDefinition());
        var recon=RootUnknownSentinelReadProfile.registeredContract(ordinary);var terminal=RootUnknownSentinelReadProfile.registeredTerminalContract(ordinary);var physical=RootUnknownSentinelReadProfile.registeredPhysicalContract(ordinary);
        assertSame(recon,RootUnknownSentinelReadProfile.registeredContract(ordinary));assertSame(terminal,RootUnknownSentinelReadProfile.registeredTerminalContract(ordinary));
        RootUnknownSentinelReadProfile.requireProfile(recon);RootUnknownSentinelReadProfile.requireTerminalProfile(terminal);RootUnknownSentinelReadProfile.requirePhysicalProfile(physical);
        assertSame(physical,RootUnknownSentinelReadProfile.registeredPhysicalContract(ordinary));assertEquals(PhysicalStatusIdentity.CONTRACT_ID,physical.contractId());
        assertEquals(ReadContract.GuardMode.STATUS_ONLY,physical.guardMode());assertEquals(ordinary.sourceRef(),physical.sourceRef());
        assertEquals(ordinary.sourceRef(),recon.sourceRef());assertEquals(ordinary.sourceRef(),terminal.sourceRef());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ordinary.guardMode());
        var catalog=RootReadContractCatalog.staticOnly(List.of(ordinary,recon,terminal,physical));
        assertTrue(catalog.containsIdentity(recon));assertTrue(catalog.containsIdentity(terminal));assertTrue(catalog.containsIdentity(physical));
        assertNotEquals(ordinary.contractId(),recon.contractId());assertNotEquals(ordinary.contractId(),terminal.contractId());
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.requireProfile(terminal));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.requireTerminalProfile(recon));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.requirePhysicalProfile(recon));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.requireProfile(physical));
        var copied=new ReadContract<Status>(ordinary.contractId(),ordinary.operation(),ordinary.requiredCapability(),ordinary.permissionKey(),
                ordinary.permissionMode(),ordinary.wireProfile(),ordinary.guardMode(),ordinary.sourceRef(),
                (request,id)->{throw new AssertionError("copied DATA cannot be dispatched");},receipt->ClockStatusRead.decode(receipt.original()),receipt->ClockStatusRead.decode(receipt.original()));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.registeredContract(copied));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.registeredTerminalContract(copied));
        assertThrows(IllegalArgumentException.class,()->RootUnknownSentinelReadProfile.registeredPhysicalContract(copied));
    }
    @Test void originalTypedStatusProducerAndRealFramingRetainFullGenerationAndRejectWrongTokenTypes()throws Exception {
        RawJson result=statusResult();var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","software-status").put("ok",true);
        frame.set("result",PublicDataJson.object(result));byte[] packet=NativeWire.packet(PublicDataJson.encode(frame).bytes());
        assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        var original=new NativeActionPort.AckReceived("software-status",true,Optional.of(result),PublicDataJson.encode(frame),packet);
        Status actual=ClockStatusRead.decode(original);assertEquals(MAX,actual.generation().decimal());
        assertEquals(actual,SentinelObservation.decode(SentinelObservation.toJson(actual)));
        assertEquals(DriverJson.object(result.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(PublicDataJson.encode(PublicDataJson.object(result)).bytes(),RawJson.MAXIMUM_BYTES));
        for(String wrong:List.of("true","1.0","\"1\"","-1","18446744073709551616")) {
            var invalid=PublicDataJson.object(result);((com.fasterxml.jackson.databind.node.ObjectNode)invalid.get("tactical_daily_sentinel")).set("generation",StrictJson.parse(("{\"v\":"+wrong+"}").getBytes(StandardCharsets.UTF_8)).get("v"));
            var bad=new NativeActionPort.AckReceived("software-status",true,Optional.of(PublicDataJson.encode(invalid)),PublicDataJson.encode(frame),packet);
            assertThrows(IllegalArgumentException.class,()->ClockStatusRead.decode(bad));
        }
    }
    @Test void unchangedOriginalPythonMethodKeepsInternalSemanticReadWithoutGameplayOrDateArguments()throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");assertNotNull(python,"NOT_RUN_REQUIRED_ORIGINAL_PYTHON");assertNotNull(repository,"NOT_RUN_REQUIRED_ORIGINAL_REPOSITORY");
        var source=SharedSourceFiles.observe(Path.of(repository).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"));
        assertEquals(1658471,source.source().bytes());assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",source.source().sha256());
        String program="""
                import ast,json,pathlib,sys,types
                path=pathlib.Path(sys.argv[1]);tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
                constants={'_TACTICAL_DAILY_SENTINEL_STATUS_STEP','_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY'}
                nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
                owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeHeadlessGameplayDriver')
                nodes.append(next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='read_tactical_daily_sentinel_status_private_v1'))
                ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
                calls=[]
                def original_primitive_boundary(step,**arguments):calls.append(dict(step=step,**arguments));return calls[-1]
                owner=types.SimpleNamespace(_execute_primitive_step=original_primitive_boundary)
                value=ns['read_tactical_daily_sentinel_status_private_v1'](owner);assert len(calls)==1
                print(json.dumps(value,sort_keys=True,separators=(',',':')))
                """;
        var builder=new ProcessBuilder(python,"-c",program,source.source().path()).redirectErrorStream(true);builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var child=builder.start();try {assertTrue(child.waitFor(10,TimeUnit.SECONDS));byte[] bytes=child.getInputStream().readNBytes(4097);assertTrue(bytes.length<=4096);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));
            var actual=StrictJson.object(StrictJson.parse(bytes),java.util.Set.of("step","expected_revision","required_capability","internal_semantic_snapshot","include_native_command_history"));
            assertEquals(ClockStatusRead.STEP,actual.get("step").textValue());assertEquals(ClockStatusRead.STATUS_CAP,actual.get("required_capability").textValue());
            assertTrue(actual.get("expected_revision").isNull());assertTrue(actual.get("internal_semantic_snapshot").booleanValue());assertFalse(actual.get("include_native_command_history").booleanValue());
        }finally{child.destroyForcibly();SharedSourceFiles.assertUnchanged(source);}
    }
}
