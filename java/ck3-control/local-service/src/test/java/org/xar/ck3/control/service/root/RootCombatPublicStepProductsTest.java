package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/** Original software Driver/Service -> registered actual read/prepare/decode -> EXECUTE formatter.
 * Controlled ports are DATA fixtures, never a minted Root, admission, physical writer or live Game. */
final class RootCombatPublicStepProductsTest {
    private static final ExactRef SOURCE=new ExactRef("controlled-combat-step-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z"),END=NOW.plusSeconds(60);
    @Test void sevenPureOriginalParsersRetainDomainsAndRejectMalformedOrReservedSteps(){
        List<String> valid=List.of("query-battle-control-snapshot-v1-0","query-battle-transition-v1--2147483648",
                "query-battle-terminal-transition-v1--2-0-18446744073709551615:characters:9,7,9",
                "query-battle-reinforcement-assignment-v1-2147483647","query-combat-phase-event-trace-v1-1",
                "query-combat-simulation-inputs-v2-30-31-a-1-0-d-1-2","query-combat-simulation-inputs-v3-30-ctor0-a-1-0-d-1-2");
        var methods=new java.util.HashSet<PublicMethod>();
        for(String literal:valid){var call=ArmySteps.parseCombatRead(new OperationKey(literal),revision()).orElseThrow();assertTrue(methods.add(call.method()));assertTrue(RootCombatPublicStepProducts.matches(call.method(),new OperationKey(literal)));}
        assertEquals(7,methods.size());
        var terminal=(ArmyCalls.Terminal)ArmySteps.parseCombatRead(new OperationKey(valid.get(2)),revision()).orElseThrow();
        assertEquals(List.of(new PositiveId(9),new PositiveId(7)),terminal.effectiveCharacters());
        assertEquals(new BigInteger("18446744073709551615"),((Present<UInt64>)terminal.afterSequence()).value().value());
        for(String literal:List.of("query-battle-control-snapshot-v1-00","query-battle-control-snapshot-v1--1","query-battle-control-snapshot-v1-2147483648",
                "query-battle-transition-v1--1","query-battle-transition-v1--0","query-battle-transition-v1-+2","query-battle-transition-v1-２",
                "query-battle-terminal-transition-v1-none","query-battle-terminal-transition-v1-1-0-18446744073709551616",
                "query-battle-terminal-transition-v1-1-0-0:characters:0","query-battle-terminal-transition-v1-1-0-0:characters:1,",
                "query-combat-phase-event-trace-v1-0","query-combat-phase-event-trace-v1-01","query-combat-phase-event-trace-v1--2",
                "query-combat-simulation-inputs-v2-30-30-a-1-0-d-1-2","query-combat-simulation-inputs-v2-30-31-a-2-0-d-1-2",
                "query-combat-simulation-inputs-v2-30-31-a-1-0-d-1-0","query-combat-simulation-inputs-v3-test-30-31-a-1-0-d-1-2","resume-map"))
            assertTrue(ArmySteps.parseCombatRead(new OperationKey(literal),revision()).isEmpty(),literal);
    }
    @Test void terminalDuplicateLiteralUsesOneExistingFamilyAndOriginalNativeStepWithoutRebinding(){
        var h=new Harness(minimal());var reads=new ArmyBattleReads(SOURCE,SOURCE,h);var catalog=new RootReadContractCatalog(List.of(),reads.families());
        var literal=new OperationKey("query-battle-terminal-transition-v1--2-0-0:characters:9,7,9");
        var call=ArmySteps.parseCombatRead(literal,revision()).orElseThrow();
        var selected=new ArmyBattleReads.Selection(call,h.context,ArmyBattleReads.Capture.PUBLIC_QUERY,Optional.of(literal));
        var contract=reads.issue(catalog,selected);var request=reads.request(selected);var prepared=contract.prepare(request,"original-duplicate");
        assertEquals(literal.value(),prepared.step());assertEquals(new RawJson(new byte[]{'{','}'}),prepared.additionalFields());
        assertEquals(literal,request.operation());assertEquals(literal.value(),OpportunityJson.text(request.arguments().get("requested_literal"),"original literal"));
        assertEquals(3,catalog.families().size());assertSame(contract,reads.issue(catalog,selected));
        var canonical=new ArmyBattleReads.Selection(call,h.context,ArmyBattleReads.Capture.PUBLIC_QUERY);
        assertNotEquals(contract.contractId(),reads.issue(catalog,canonical).contractId());
        assertEquals("query-battle-terminal-transition-v1--2-0-0:characters:9,7",reads.issue(catalog,canonical).prepare(reads.request(canonical),"canonical").step());
        assertThrows(IllegalArgumentException.class,()->new ArmyBattleReads.Selection(call,h.context,ArmyBattleReads.Capture.PUBLIC_QUERY,
                Optional.of(new OperationKey("query-battle-terminal-transition-v1--2-0-0:characters:7,9"))));
        assertThrows(IllegalArgumentException.class,()->contract.prepare(new PlanningReadRequest(h.context.before(),h.context.source(),h.context.sessionId(),
                new OperationKey("query-battle-terminal-transition-v1--3-0-0:characters:9,7,9"),request.arguments(),END),"changed-step"));
        var domain=new ArmyRequests.Terminal(Optional.of(new FullId(-2)),Optional.of(new PublicUnitId(0)),Optional.empty(),List.of(new FullId(9),new FullId(7)));
        ArmySteps.requireTerminalLiteral(literal,domain);
        assertThrows(IllegalArgumentException.class,()->ArmySteps.requireTerminalLiteral(new OperationKey("query-battle-terminal-transition-v1--3-0-0:characters:9,7,9"),domain));
        var wrong=StrictJson.object().put("step","query-battle-terminal-transition-v1--3-0-0:characters:9,7,9").put("accepted",true);
        assertThrows(IllegalArgumentException.class,()->BattleTerminalCodec.terminal(StrictJson.canonical(wrong),h.context,domain,literal));
        assertEquals(0,h.calls);
    }
    @Test void originalSevenDriverResultsReachActualFamilyConsumersAndSourceBoundSerde()throws Exception{
        ObjectNode corpus=originalVectors();var seen=new java.util.HashSet<PublicMethod>();
        for(var row:corpus.withArray("cases")){
            var h=new Harness((ObjectNode)row.get("snapshot"));h.result=((ObjectNode)row.get("native")).deepCopy();
            var base=new org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec();
            var cache=new org.xar.ck3.control.wave2.military.forecast.CombatObservationCache(base,
                    new org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec(base,new org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime()));
            var battle=new ArmyBattleReads(SOURCE,SOURCE,h);var reinforcement=new ArmyReinforcementReads(SOURCE,SOURCE,h);
            var forecast=new ArmyForecastReads(SOURCE,SOURCE,h,cache,h::load,h.archive,()->h.same);
            var families=new java.util.ArrayList<RootReadContractCatalog.Family<?,?>>();families.addAll(battle.families());families.addAll(reinforcement.families());families.addAll(forecast.families());
            var catalog=new RootReadContractCatalog(List.of(),families);var ports=new RootCombatPublicStepProducts.Reads(catalog,battle,reinforcement,forecast,h::load);
            var caller=caller(row.path("expected").path("step").textValue());var call=ArmySteps.parseCombatRead(caller.step(),revision()).orElseThrow();seen.add(call.method());
            RawJson result=RootCombatPublicStepProducts.read(ports,h.complete,h.same,caller,h.archive,END);
            Obj restored=ArmyPublicWire.decodeExactSourceBound(result,h.context);
            assertEquals(immutable((ObjectNode)row.get("expected")),restored,call.method().pythonName());
            assertEquals(result,ArmyPublicWire.encodeExactSourceBound(restored,h.context));assertEquals(1,h.calls);
            assertFalse(restored.members().containsKey("source"));assertFalse(restored.members().containsKey("loaded_playset_proof"));
            assertFalse(restored.members().containsKey("queried_episode_run_id"));assertFalse(restored.members().containsKey("queried_connection_generation"));
            int before=h.calls;h.result.put("query_sequence",true);
            assertThrows(java.io.IOException.class,()->RootCombatPublicStepProducts.read(ports,h.complete,h.same,caller,h.archive,END));
            assertEquals(before+1,h.calls,"one original read; no fallback/retry after malformed result");
            h.unavailable=true;before=h.calls;
            assertThrows(java.io.IOException.class,()->RootCombatPublicStepProducts.read(ports,h.complete,h.same,caller,h.archive,END));
            assertEquals(before+1,h.calls,"unavailable/unknown is returned without another query or action");
        }
        assertEquals(7,seen.size());
    }
    @Test void differentContextFamilyCannotBeInjectedIntoInstalledReadRoster(){
        var a=new Harness(minimal());var b=new Harness(minimal());var ba=new ArmyBattleReads(SOURCE,SOURCE,a);var bb=new ArmyBattleReads(SOURCE,SOURCE,b);
        var r=new ArmyReinforcementReads(SOURCE,SOURCE,a);var base=new org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec();
        var cache=new org.xar.ck3.control.wave2.military.forecast.CombatObservationCache(base,new org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec(base,new org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime()));
        var f=new ArmyForecastReads(SOURCE,SOURCE,a,cache,a::load,a.archive,()->a.same);var families=new java.util.ArrayList<RootReadContractCatalog.Family<?,?>>();families.addAll(ba.families());families.addAll(r.families());families.addAll(f.families());
        assertThrows(IllegalArgumentException.class,()->new RootCombatPublicStepProducts.Reads(new RootReadContractCatalog(List.of(),families),bb,r,f,a::load));
    }
    private static ArmyCalls.Revision revision(){return new ArmyCalls.Revision(new Missing<>());}
    private static PublicPlanningCodec.ExecuteRequest caller(String step){return new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.FrameMissing());}
    private static ObjectNode minimal(){var n=StrictJson.object().put("snapshot_id","native:3").put("revision",3).put("native_revision",3).put("date_raw",77)
            .put("episode_run_id","controlled-combat-step").put("paused",true).put("map_ready",true);n.putObject("played_character").put("character_id",101).put("alive",true);n.putObject("diagnostics").put("connection_generation",1);return n;}
    private static Obj immutable(ObjectNode value){return DriverJson.object(StrictJson.canonical(value),DriverJson.MAX_NATIVE_BYTES);}
    private static final class Harness implements PlanningReadPort{
        final Context context;final Complete complete;final ContinuityStorePort.Session same;final ActionPorts.OutcomeArchive archive;
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> receipts=new HashMap<>();
        final ExactRef semantic,driver,capabilities;ObjectNode result;int calls;boolean unavailable;
        Harness(ObjectNode original){
            ObjectNode snapshot=original.deepCopy();snapshot.put("map_ready",true);((ObjectNode)snapshot.get("played_character")).put("alive",true);
            var source=new G2Source("controlled-combat-no-runtime",NOW.toString(),"controlled-original-driver-fixture",SOURCE);
            var key=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(),snapshot.path("native_revision").bigIntegerValue(),snapshot.path("date_raw").bigIntegerValue()),snapshot.path("snapshot_id").textValue(),snapshot.path("revision").bigIntegerValue(),snapshot.path("episode_run_id").textValue());
            context=new Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),key,1),source,"controlled-combat-step-session",END);
            same=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(p,m,args)->{throw new AssertionError("software read cannot mutate/mint Root writer authority: "+m.getName());});
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(p,m,args)->switch(m.getName()){
                case "withSession"->p;case "loadMaterial"->materials.get((ExactRef)args[0]);case "load"->outcomes.get((ExactRef)args[0]);case "loadRead"->receipts.get((ExactRef)args[0]);
                case "referenceOf"->outcomes.entrySet().stream().filter(e->e.getValue().equals(args[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                case "readReferenceOf"->receipts.entrySet().stream().filter(e->e.getValue().equals(args[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                default->throw new AssertionError("no fake physical Root archive authority: "+m.getName());});
            semantic=material("semantic",new RawJson(StrictJson.canonical(snapshot)));driver=material("driver",new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));capabilities=material("capabilities",new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            complete=new Complete(context.before(),source,context.sessionId(),snapshot.path("diagnostics").path("connection_generation").bigIntegerValue(),immutable(snapshot),semantic,NOW,"a".repeat(64));
        }
        ExactRef material(String name,RawJson body){var ref=new ExactRef("controlled-"+name+"-"+DriverJson.sha256(body.bytes()),body.bytes().length,DriverJson.sha256(body.bytes()));materials.put(ref,body);return ref;}
        Complete load(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive original){assertEquals(semantic,basis.nativeFrame());assertEquals(driver,basis.driverFacts());assertSame(archive,original);return complete;}
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){return read(same,contract,request);}
        @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session borrowed,ReadContract<T> contract,PlanningReadRequest request){
            assertSame(same,borrowed);String id="controlled-combat-"+(++calls);var prepared=contract.prepare(request,id);assertEquals(request.operation().value(),prepared.step());
            if(unavailable)return new PlanningReadResult.Unavailable<>("controlled unknown original read; no retry",Optional.empty());
            var top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);top.set("result",result);
            RawJson packet=new RawJson(StrictJson.canonical(top));byte[] framed;
            try{framed=NativeWire.packet(packet.bytes());}
            catch(java.io.IOException failure){throw new AssertionError("controlled combat fixture packet construction failed",failure);}
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),packet,framed);
            ExactRef dispatch=new ExactRef("controlled-dispatch-"+id,packet.bytes().length,DriverJson.sha256(packet.bytes()));outcomes.put(dispatch,ack);
            var n=StrictJson.object().put("schema",RootGuardEvidence.SCHEMA).put("operation",request.operation().value()).put("authority_id","controlled-data-not-root");
            n.set("native_frame",semantic.toJson());n.set("driver_facts",driver.toJson());n.set("semantic",semantic.toJson());
            for(String field:List.of("driver_stamp","original_driver","capabilities","hello","heartbeat","source_qualification"))n.set(field,capabilities.toJson());
            ExactRef basis=material("guard",new RawJson(StrictJson.canonical(n)));var g=new PlanningReadGuard(new GuardEvidence(context.before(),context.source(),context.sessionId(),complete.connectionGeneration(),request.operation(),semantic,capabilities,"controlled-data-not-root",NOW,END,List.of(basis)),true,true,true,"a".repeat(64));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,g,g,ack);var ref=new ExactRef("controlled-read-"+id,1,"b".repeat(64));receipts.put(ref,receipt);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
        }
    }
    private static ObjectNode originalVectors()throws Exception{
        verifySources();ObjectNode result=original("""
                import copy,json,runpy,sys
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                from xar_autoplayer.bridge.service import GameplayBridgeService as Service
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as Driver
                cases=[]
                for name in ('test_battle_control_snapshot_v1_bridge.py','test_battle_transition_v1_bridge.py','test_battle_terminal_transition_v1_bridge.py','test_battle_reinforcement_assignment_v1_bridge.py','test_combat_simulation_inputs_bridge.py','test_combat_phase_inputs_v3_bridge.py'):
                    m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/name));d,e=m['_native_driver']()
                    raw=m['_fixture_result']() if name.startswith('test_combat_') else m['_native_result']()
                    m['_answer_with'](e,lambda raw=raw:copy.deepcopy(raw))
                    try:
                        snapshot=d.take_snapshot();expected=Service.execute_step(type('Facade',(),{'driver':d})(),m['STEP'],expected_revision=snapshot['revision'])
                        if name.startswith('test_combat_'):raw['backend_id']='native-headless'
                        cases.append(dict(snapshot=snapshot,native=raw,expected=expected))
                    finally:d.close()
                m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_combat_phase_event_trace_query.py'));trace=m['available_trace']()
                snapshot=dict(snapshot_id='native:3',revision=3,native_revision=3,date_raw=trace['date_raw'],paused=True,map_ready=True,episode_run_id='controlled-phase-step',played_character=dict(character_id=29829,alive=True),diagnostics=dict(connection_generation=1),active_wars=[],player_armies=[])
                native=dict(step='query-combat-phase-event-trace-v1-'+str(trace['combat_id']),accepted=True,status='evaluator_probe_available',query_sequence=7,combat_phase_event_trace=trace,backend_id='native-headless')
                class Phase:
                    def take_snapshot(self):return copy.deepcopy(snapshot)
                    def _execute_primitive_step(self,*a,**kw):return copy.deepcopy(native)
                    def execute_step(self,step,**kw):return Driver._execute_combat_phase_event_trace_v1_query(self,step,expected_revision=kw.get('expected_revision'))
                expected=Service.execute_step(type('Facade',(),{'driver':Phase()})(),native['step'],expected_revision=3)
                cases.append(dict(snapshot=snapshot,native=native,expected=expected))
                print(json.dumps(dict(cases=cases),separators=(',',':'),allow_nan=False))
                """);verifySources();return result;
    }
    private static ObjectNode original(String body)throws Exception{
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        if(repository==null||python==null)throw new IllegalStateException("required original producer environment missing; NOT_RUN cannot become skipped/pass");
        Path root=Path.of(repository).toRealPath(),executable=Path.of(python).toRealPath();assertTrue(Files.isDirectory(root));assertTrue(Files.isRegularFile(executable));
        String prefix="import sys\nfrom pathlib import Path\nroot=Path(sys.argv[1])\nsys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))\n";
        var builder=new ProcessBuilder(executable.toString(),"-B","-I","-X","utf8","-c",prefix+body,root.toString()).directory(root.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");var process=builder.start();
        try(var readers=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()){
            var out=readers.submit(()->process.getInputStream().readNBytes(1048577));var err=readers.submit(()->process.getErrorStream().readNBytes(16385));
            try{process.getOutputStream().close();assertTrue(process.waitFor(60,java.util.concurrent.TimeUnit.SECONDS),"original Combat producer timeout");
                byte[] bytes=out.get(5,java.util.concurrent.TimeUnit.SECONDS),error=err.get(5,java.util.concurrent.TimeUnit.SECONDS);assertTrue(bytes.length<=1048576&&error.length<=16384);assertEquals(0,process.exitValue(),new String(error,java.nio.charset.StandardCharsets.UTF_8));
                return (ObjectNode)StrictJson.parse(bytes,1048576);
            }finally{if(process.isAlive()){process.destroyForcibly();process.waitFor(5,java.util.concurrent.TimeUnit.SECONDS);}}
        }
    }
    private static void verifySources()throws Exception{
        String repository=System.getProperty("xar.repository.root");if(repository==null)throw new IllegalStateException("actual pinned producer source root required");Path root=Path.of(repository).toRealPath();
        for(String[] pin:SOURCE_PINS){Path path=root.resolve(pin[0]).toRealPath();assertTrue(path.startsWith(root));assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))),pin[0]);}
    }
    private static final String[][] SOURCE_PINS={
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
        {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
        {"ck3_autonomous_player/tests/unit/test_battle_control_snapshot_v1_bridge.py","6f17e14e7b9e9f4fa3462dd5eb3b7c365fbd551369b00caa271d9ea346e93508"},
        {"ck3_autonomous_player/tests/unit/test_battle_transition_v1_bridge.py","c04b3910fb4aaaa92a4304406d2bd70cc35a88536be48b70cd20585a64b83219"},
        {"ck3_autonomous_player/tests/unit/test_battle_terminal_transition_v1_bridge.py","7ef0593f14e211a132eeb0a3d0fe67e604c98f97ea351803ed7599b8e9b0ec08"},
        {"ck3_autonomous_player/tests/unit/test_battle_reinforcement_assignment_v1_bridge.py","677efadca527be2280a77851054c280566ee87a1a25dd9981e5d10ecf74b7949"},
        {"ck3_autonomous_player/tests/unit/test_combat_simulation_inputs_bridge.py","02fbab4b90a5bcefca34669c2cff79ec89005d9640636a84779b71234480d5a8"},
        {"ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_bridge.py","2ab86c8ca0333156e3c9a55c4b443be17bf9b3c49fe1f3fbb924afaff2087999"},
        {"ck3_autonomous_player/tests/unit/test_combat_phase_event_trace_query.py","983b49395d8559b355bc28603d74850e9e2ce06993b3b0e5d0e4f24326f012b5"}
    };
}
