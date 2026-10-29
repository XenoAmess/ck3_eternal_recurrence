package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyPlanningReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyPublicWire;
import org.xar.ck3.control.nativebridge.capabilities.army.CombatPublicProjection;
import org.xar.ck3.control.nativebridge.capabilities.army.CombatLoadedPlaysetProof;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatFrames;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyForecastReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyForecastService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyForecastPublicResultCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Existing original Python first-hop producer -> actual native read families -> full horizon consumer, including archived replay. */
final class ArmyPlanningReadOriginalTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic-native-read-source",1,"a".repeat(64));
    private static final int ORIGINAL_OUTPUT_BYTES=8*1024*1024;
    @Test void originalPreviewAndFullHostileH1ReachTheirActualRegisteredDecoders() throws Exception {
        Obj row=fixture();PlanningRequest request=request(row);
        var environment=new Held(request);var reads=new ArmyPlanningReads(SOURCE,SOURCE,environment,environment.archive,environment::load,()->environment.session);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());
        Obj historyPreview=result(request.observations().history().getFirst());Obj originalPreview=OpportunityJson.object(historyPreview.get("route_preview"),"original preview");
        var fields=new java.util.LinkedHashMap<>(originalPreview.members());fields.remove("previewed_date_raw");
        environment.result=obj(f("step",text("preview-move-army-11-to-31")),f("accepted",new Bool(true)),f("status",text("available")),f("route_preview",new Obj(fields)));
        var preview=reads.collect(environment.session,catalog,new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.ROUTE_PREVIEW,11,31,List.of()));
        var observed=assertInstanceOf(PlanningReadResult.Known.class,preview);assertEquals(originalPreview,((MilitaryReadObservation)observed.value()).normalizedResult().get("route_preview"));
        assertEquals(environment.archive.readReferenceOf(observed.receipt()),observed.originalReceipt());
        Obj historyHorizon=result(request.observations().history().get(1));
        environment.result=obj(f("step",text("query-route-contact-horizon-v1-11-to-31-h-1-21")),f("accepted",new Bool(true)),f("status",text("available")),
                f("query_sequence",number(9)),f("snapshot_revision",request.observations().snapshot().get("native_revision")),f("route_contact_horizon",historyHorizon.get("route_contact_horizon")));
        var horizon=assertInstanceOf(PlanningReadResult.Known.class,reads.collect(environment.session,catalog,new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.CONTACT_HORIZON,11,31,List.of(21))));
        Obj normalized=((MilitaryReadObservation)horizon.value()).normalizedResult();assertEquals(historyHorizon.get("route_contact_horizon"),normalized.get("route_contact_horizon"));
        assertEquals(request.observations().snapshot().get("diagnostics") instanceof Obj d?d.get("connection_generation"):null,normalized.get("queried_connection_generation"));
        ReadContract<?> installed=environment.last;assertTrue(installed.hasPureReplay());assertEquals(horizon.value(),installed.replay(horizon.receipt()));assertEquals(2,environment.nativeCalls);
        var renewed=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),installed.operation(),horizon.receipt().request().arguments(),request.deadline().plusSeconds(60));
        assertEquals(installed.prepare(horizon.receipt().request(),"old-budget"),installed.prepare(renewed,"renewed-budget"));
        requireOriginalReuse(installed,horizon.receipt(),renewed,request.observations().snapshot().with("command_history",new Arr(List.of(text("new-read-row")))));
        assertThrows(IllegalArgumentException.class,()->requireOriginalReuse(installed,horizon.receipt(),renewed,request.observations().snapshot().with("player_armies",new Arr(List.of()))));
        assertEquals(request.deadline(),horizon.receipt().request().deadline(),"original receipt budget is never relabeled");
        assertThrows(IllegalArgumentException.class,()->new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.CONTACT_HORIZON,11,31,List.of()));
    }
    @Test void h1BackendIdOptionalAndStrictEnvelopeValidation() throws Exception {
        Obj row=fixture();PlanningRequest request=request(row);
        var environment=new Held(request);var reads=new ArmyPlanningReads(SOURCE,SOURCE,environment,environment.archive,environment::load,()->environment.session);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());
        Obj historyHorizon=result(request.observations().history().get(1));
        var selection=new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.CONTACT_HORIZON,11,31,List.of(21));
        var base=obj(f("step",text("query-route-contact-horizon-v1-11-to-31-h-1-21")),f("accepted",new Bool(true)),f("status",text("available")),
                f("query_sequence",number(9)),f("snapshot_revision",request.observations().snapshot().get("native_revision")),f("route_contact_horizon",historyHorizon.get("route_contact_horizon")));
        // Source-derived Native shape and explicit adapter variant; this grants no Native authority.
        // Present nonblank backend_id is accepted and preserved
        environment.result=base.with("backend_id",text("native-headless"));
        var known=assertInstanceOf(PlanningReadResult.Known.class,reads.collect(environment.session,catalog,selection));
        assertEquals(new Text("native-headless"),((MilitaryReadObservation)known.value()).normalizedResult().get("backend_id"));
        // Absent backend_id is accepted
        environment.result=base;
        var absent=assertInstanceOf(PlanningReadResult.Known.class,reads.collect(environment.session,catalog,selection));
        assertNull(((MilitaryReadObservation)absent.value()).normalizedResult().get("backend_id"));
        // Invalid backend_id types/values rejected
        for(var bad:List.of(Nil.INSTANCE,new Bool(true),new IntegerValue(BigInteger.ONE),new Text(""),new Text(" "))) {
            environment.result=base.with("backend_id",bad);
            assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,selection));
        }
        // Unknown extra field rejected
        environment.result=base.with("unknown_field",new Bool(true));
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,selection));
        // Missing required field rejected
        var missing=new java.util.LinkedHashMap<>(base.members());missing.remove("accepted");environment.result=new Obj(missing);
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,selection));
        // Wrong sequence rejected
        environment.result=base.with("query_sequence",number(0));
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,selection));
        // Wrong revision rejected
        environment.result=base.with("snapshot_revision",new IntegerValue(OpportunityJson.integer(request.observations().snapshot().get("native_revision"),"native revision").add(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,selection));
    }
    @Test void originalPacketAndFullSourceMismatchRejectBeforeAnyUsableHorizon() throws Exception {
        Obj row=fixture();PlanningRequest request=request(row);
        var environment=new Held(request);var reads=new ArmyPlanningReads(SOURCE,SOURCE,environment,environment.archive,environment::load,()->environment.session);var catalog=new RootReadContractCatalog(List.of(),reads.families());
        Obj original=result(request.observations().history().getFirst());Obj preview=OpportunityJson.object(original.get("route_preview"),"preview");var fields=new java.util.LinkedHashMap<>(preview.members());fields.remove("previewed_date_raw");
        environment.result=obj(f("step",text("preview-move-army-11-to-31")),f("accepted",new Bool(true)),f("status",text("available")),f("route_preview",new Obj(fields)));
        environment.corruptPacket=true;
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.ROUTE_PREVIEW,11,31,List.of())));
        environment.corruptPacket=false;environment.result=environment.result.with("route_preview",new Obj(fields).with("army_id",new Bool(true)));
        assertThrows(IllegalArgumentException.class,()->reads.collect(environment.session,catalog,new ArmyPlanningReads.Selection(request,MilitaryReadObservation.Kind.ROUTE_PREVIEW,11,31,List.of())));
    }
    @Test void actualOriginalCombatV2AndV3GoThroughTheSharedRegisteredTransportAndPureReplay() throws Exception {
        Obj corpus=original("""
                import copy,json,pathlib,runpy,sys
                repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
                rows=[]
                for version in (2,3):
                    p=repo/'ck3_autonomous_player/tests/unit'/('test_combat_simulation_inputs_bridge.py' if version==2 else 'test_combat_phase_inputs_v3_bridge.py');m=runpy.run_path(str(p));driver,endpoint=m['_native_driver']()
                    try:
                        m['_answer_with'](endpoint,m['_fixture_result']);starting=driver.take_snapshot();result=driver.execute_step(m['STEP'],expected_revision=starting['revision'])
                        raw={k:copy.deepcopy(result[k]) for k in ('step','accepted','status','query_sequence','combat_simulation_inputs','backend_id')}
                        rows.append({'version':version,'snapshot':starting,'history':[],'result':raw})
                    finally:driver.close()
                print(json.dumps({'cases':rows},separators=(',',':')))
                """);
        for(Obj row:rows(corpus.get("cases"))) {
            PlanningRequest request=request(row);var environment=new Held(request);environment.result=OpportunityJson.object(row.get("result"),"actual original raw receipt");
            var base=new org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec();var cache=new org.xar.ck3.control.wave2.military.forecast.CombatObservationCache(base,new org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec(base,new org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime()));
            var actualReads=new ArmyForecastReads(SOURCE,SOURCE,environment,cache,environment::load,environment.archive,()->environment.session);
            var catalog=new RootReadContractCatalog(List.of(),actualReads.families());String step=OpportunityJson.text(environment.result.get("step"),"step");boolean v2=new IntegerValue(BigInteger.TWO).equals(row.get("version"));
            var encounter=(v2?org.xar.ck3.control.wave2.military.combatwire.CombatRequest.parseStep(step):org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec.parseStep(step)).orElseThrow();
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Field<Integer> ctor=encounter.constructorAdjacencyKindRaw()==null?new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Missing<>():new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Present<>(encounter.constructorAdjacencyKindRaw());
            var call=new ArmyCalls.Combat(v2?PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS:PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,
                    new ArmyCalls.Revision(new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Present<>(request.before().frame().revision())),encounter,ctor);
            var context=new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Context(request.before(),request.source(),request.sessionId(),request.deadline());
            var observed=actualReads.collect(environment.session,catalog,new ArmyForecastReads.Selection(call,context));
            if(!(observed instanceof PlanningReadResult.Known<ForecastReadObservation> known))throw new AssertionError("original combat producer returned no Known");
            var typed=assertInstanceOf(ForecastReadObservation.CombatInputs.class,known.value());assertEquals(environment.result.get("combat_simulation_inputs"),typed.normalizedResult().get("combat_simulation_inputs"));
            var held=new ArmyRetreatFrames.Current(environment.complete,request.deadline());
            Optional<CombatLoadedPlaysetProof.Evidence> proof=Optional.empty();
            if(!v2) {
                var missingManagedState=java.nio.file.Files.createTempDirectory("combat-service-observed-missing-").toAbsolutePath();
                try {
                    var source=CombatLoadedPlaysetProof.managed(missingManagedState,()->environment.complete);
                    proof=Optional.of(source.observe(new CombatPublicProjection.Input(environment.complete,environment.complete,known)));
                    assertEquals(new Text("unavailable"),proof.orElseThrow().value().get("status"));
                    assertNotNull(proof.orElseThrow().value().get("unavailable_reason"));
                } finally {java.nio.file.Files.delete(missingManagedState);}
                assertThrows(IllegalArgumentException.class,()->ArmyForecastService.encode(call.method(),new ArmyForecastService.Reply(held,held,known)),"full V3 must reject missing privately collected evidence");
                var forbiddenWriter=(ContinuityStorePort)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.class},
                        (proxy,method,args)->{throw new AssertionError("missing source cannot acquire writer/query authority");});
                var noObservation=new ArmyRetreatFrames(()->{throw new AssertionError("missing source must fail before observing or querying");});
                var noSourceService=new ArmyForecastService(forbiddenWriter,noObservation,actualReads,catalog,request::deadline);
                int beforeDenied=environment.nativeCalls;
                assertThrows(java.io.IOException.class,()->noSourceService.read(environment.session,call,request.deadline()));
                assertEquals(beforeDenied,environment.nativeCalls);
            }
            var reply=new ArmyForecastService.Reply(held,held,known,proof);
            var encoded=ArmyForecastService.encode(call.method(),reply);
            // The real source directory is already gone: repeated encoding consumes retained evidence and performs no file/native read.
            assertArrayEquals(encoded.bytes(),ArmyForecastService.encode(call.method(),reply).bytes());
            Obj publicResult=DriverJson.object(encoded.bytes(),DriverJson.MAX_NATIVE_BYTES);
            Obj restoredPublic=ArmyPublicWire.decodeExactSourceBound(encoded,context);
            assertEquals(publicResult,DriverJson.object(DriverJson.encode(publicResult),DriverJson.MAX_NATIVE_BYTES));
            assertNotNull(publicResult.get("combat_simulation_inputs"));
            if(v2) {
                assertTrue(publicResult.members().containsKey("knight_stat_consumption_projection_v1"));
                assertTrue(publicResult.members().containsKey("current_physical_entry_writeback_association_v1"));
            } else {
                assertEquals(proof.orElseThrow().value(),restoredPublic.get("loaded_playset_proof"));
                assertNotNull(publicResult.get("current_special_knight_initial_value"));
            }
            assertEquals(ArmyForecastPublicResultCodec.Profile.ORIGINAL_PUBLIC_RESULT,
                    ArmyForecastPublicResultCodec.profile(call.method()));
            assertFalse(new Bool(true).equals(publicResult.get("qualified_win_probability_available")),"public projection preserves the original qualification boundary");
            assertThrows(IllegalArgumentException.class,()->ArmyForecastService.encode(PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS,reply));
            assertTrue(MilitaryPlanInputs.sameLease(request,typed.normalizedResult()),"actual read must carry its full current episode and connection metadata to ordinary consumers");
            var fields=ForecastSemanticProjection.project(typed,known.receipt(),request.observations().snapshot(),empty());assertTrue(fields.semanticCache());assertEquals(9,fields.fields().members().size());
            assertEquals(typed.normalizedResult().get("combat_simulation_inputs"),fields.fields().get(v2?"combat_simulation_inputs":"combat_simulation_inputs_v3"));
            Obj diagnostics=OpportunityJson.object(request.observations().snapshot().get("diagnostics"),"diagnostics");var changed=request.observations().snapshot().with("diagnostics",diagnostics.with("connection_generation",new IntegerValue(OpportunityJson.integer(diagnostics.get("connection_generation"),"generation").add(BigInteger.ONE))));
            assertTrue(ForecastSemanticProjection.project(typed,known.receipt(),changed,fields.fields()).fields().members().values().stream().allMatch(value->value==Nil.INSTANCE));
            assertEquals(ForecastSemanticProjection.unavailable(typed.kind()).fields(),ForecastSemanticProjection.project(typed,known.receipt(),changed,fields.fields()).fields());
            cache.clear();assertEquals(typed,environment.last.replay(known.receipt()));
            assertTrue(cache.projectV2(OpportunityJson.toNode(request.observations().snapshot()),request.before().frame().episodeRunId()).isEmpty());assertTrue(cache.projectV3(OpportunityJson.toNode(request.observations().snapshot()),request.before().frame().episodeRunId()).isEmpty());
            requireOriginalReuse(environment.last,known.receipt(),new PlanningReadRequest(request.before(),request.source(),request.sessionId(),environment.last.operation(),known.receipt().request().arguments(),request.deadline().plusSeconds(60)),request.observations().snapshot());
            assertEquals(typed,actualReads.activateCanonical(new ArmyForecastReads.Selection(call,context),known.receipt(),request.observations().snapshot()));
            assertTrue(v2?cache.projectV2(OpportunityJson.toNode(request.observations().snapshot()),request.before().frame().episodeRunId()).isPresent():cache.projectV3(OpportunityJson.toNode(request.observations().snapshot()),request.before().frame().episodeRunId()).isPresent());
            environment.result=environment.result.with("query_sequence",new Bool(true));assertThrows(IllegalArgumentException.class,()->actualReads.collect(environment.session,catalog,new ArmyForecastReads.Selection(call,context)));
        }
    }
    private static <T>void requireOriginalReuse(ReadContract<T> installed,PlanningReadReceipt original,PlanningReadRequest actualCurrent,Obj semantic) {
        T value=installed.replay(original);installed.requireCanonicalReuse(original,value,actualCurrent,semantic);
    }
    private static Obj fixture()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(repository,"actual original repository required");assertNotNull(python,"actual original Python oracle required");
        String program="""
                import hashlib,json,pathlib,runpy,sys
                repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
                p=repo/'ck3_autonomous_player/tests/unit/test_general_battle_first_hop_before_endpoint_12004.py';before=hashlib.sha256(p.read_bytes()).hexdigest();m=runpy.run_path(str(p))
                value={'snapshot':m['_snapshot'](),'history':[m['_preview'](31,[30,40,31],1),m['_horizon'](31,[40,31],2)],'source_sha256':before}
                # Explicit test-only completion of the original partial Army wire; these are derived fixture identities.
                for army in value['snapshot']['player_armies']:army.update(owner_character_id=29829,controllable=True)
                for war in value['snapshot']['active_wars']:
                    for army in war['allied_armies']:army.update(owner_character_id=29829,controllable=True)
                    for army in war['enemy_armies']:army.update(owner_character_id=30001,controllable=False)
                assert hashlib.sha256(p.read_bytes()).hexdigest()==before
                print(json.dumps(value,separators=(',',':')))
                """;
        return original(program);
    }
    private static Obj original(String program)throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(repository,"actual original repository required");assertNotNull(python,"actual original Python oracle required");
        var builder=new ProcessBuilder(python,"-B","-X","utf8","-c",program,repository).directory(java.nio.file.Path.of(repository).toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");var process=builder.start();
        try(var readers=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var out=readers.submit(()->{byte[] data=process.getInputStream().readNBytes(ORIGINAL_OUTPUT_BYTES+1);if(data.length>ORIGINAL_OUTPUT_BYTES)process.destroyForcibly();return data;});
            var error=readers.submit(()->{byte[] data=process.getErrorStream().readNBytes(16385);if(data.length>16384)process.destroyForcibly();return data;});
            try{process.getOutputStream().close();assertTrue(process.waitFor(45,java.util.concurrent.TimeUnit.SECONDS),"original native read fixture timeout is RED");byte[] bytes=out.get(5,java.util.concurrent.TimeUnit.SECONDS),errors=error.get(5,java.util.concurrent.TimeUnit.SECONDS);
                assertTrue(bytes.length<=ORIGINAL_OUTPUT_BYTES&&errors.length<=16384,"bounded original producer output required");assertEquals(0,process.exitValue(),new String(errors,java.nio.charset.StandardCharsets.UTF_8));return DriverJson.object(bytes,ORIGINAL_OUTPUT_BYTES);}
            finally{if(process.isAlive())process.destroyForcibly();}
        }
    }
    private static PlanningRequest request(Obj row) {
        Obj snapshot=OpportunityJson.object(row.get("snapshot"),"original snapshot").with("map_ready",new Bool(true));if(!(snapshot.get("played_character") instanceof Obj))snapshot=snapshot.with("played_character",obj(f("character_id",number(29829)),f("alive",new Bool(true))));
        BigInteger actor=OpportunityJson.integer(OpportunityJson.object(snapshot.get("played_character"),"actor").get("character_id"),"actor");
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(actor,OpportunityJson.integer(snapshot.get("native_revision"),"native revision"),OpportunityJson.integer(snapshot.get("date_raw"),"date")),
                OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot"),OpportunityJson.integer(snapshot.get("revision"),"public revision"),OpportunityJson.text(snapshot.get("episode_run_id"),"episode"));
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity("synthetic-native-read-machine",new org.xar.ck3.control.contracts.GameGeneration(123,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new PlanningRequest(identity,new org.xar.ck3.control.g2.common.G2Source(identity.machineId(),"2026-10-24T00:00:00Z","synthetic-original-read",SOURCE),"actual-read-fixture-session",Instant.parse("2026-10-24T00:01:00Z"),
                new org.xar.ck3.control.application.planning.PlanningObservation(snapshot,rows(row.get("history")),java.util.Set.of(),java.util.Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static final class Held implements PlanningReadPort {
        final PlanningRequest request;final ActionPorts.OutcomeArchive archive;final ContinuityStorePort.Session session;
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> receipts=new HashMap<>();
        final ExactRef nativeFrame,driverFacts,hello;final Complete complete;Obj result;ReadContract<?> last;int nativeCalls;boolean corruptPacket;
        Held(PlanningRequest request) {
            this.request=request;
            session=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{throw new AssertionError("read family cannot mutate the writer in this fixture: "+method.getName());});
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)-> {
                return switch(method.getName()) {
                    case "withSession" -> proxy;
                    case "loadMaterial", "loadFullMaterial" -> materials.get((ExactRef)args[0]);
                    case "load" -> outcomes.get((ExactRef)args[0]);
                    case "loadRead" -> receipts.get((ExactRef)args[0]);
                    case "referenceOf" -> outcomes.entrySet().stream().filter(entry->entry.getValue().equals(args[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                    case "readReferenceOf" -> receipts.entrySet().stream().filter(entry->entry.getValue().equals(args[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                    default -> throw new AssertionError("unexpected archive mutation in decoder: "+method.getName());
                };
            });
            nativeFrame=material("native-frame",new RawJson(DriverJson.encode(request.observations().snapshot())));driverFacts=material("driver-facts",new RawJson("{\"kind\":\"original-driver-fixture\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            hello=material("hello",new RawJson("{\"kind\":\"actual-read-fixture-capabilities\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            Obj semantic=request.observations().snapshot();BigInteger generation=OpportunityJson.integer(OpportunityJson.object(semantic.get("diagnostics"),"diagnostics").get("connection_generation"),"generation");
            complete=new Complete(request.before(),request.source(),request.sessionId(),generation,semantic,nativeFrame,Instant.parse("2026-10-24T00:00:00Z"),"a".repeat(64));
        }
        private ExactRef material(String name,RawJson bytes){ExactRef ref=new ExactRef("synthetic-"+name+"-"+DriverJson.sha256(bytes.bytes()),bytes.bytes().length,DriverJson.sha256(bytes.bytes()));materials.put(ref,bytes);return ref;}
        Complete load(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive original){assertEquals(nativeFrame,basis.nativeFrame());assertEquals(driverFacts,basis.driverFacts());assertSame(archive,original);return complete;}
        GuardEvidence guard(OperationKey operation) {
            var basis=StrictJson.object().put("schema",RootGuardEvidence.SCHEMA).put("operation",operation.value()).put("authority_id","original-test-authority");
            basis.set("native_frame",nativeFrame.toJson());basis.set("driver_facts",driverFacts.toJson());basis.set("semantic",nativeFrame.toJson());
            for(String field:List.of("driver_stamp","original_driver","capabilities","hello","heartbeat","source_qualification"))basis.set(field,hello.toJson());
            basis.putObject("writer_point").put("sequence",0).put("digest","a".repeat(64));
            ExactRef ref=material("guard-basis",new RawJson(StrictJson.canonical(basis)));
            return new GuardEvidence(request.before(),request.source(),request.sessionId(),complete.connectionGeneration(),operation,nativeFrame,hello,"original-test-authority",complete.observedAt(),request.deadline(),List.of(ref));
        }
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest input){return read(session,contract,input);}
        @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session borrowed,ReadContract<T> contract,PlanningReadRequest input) {
            assertSame(session,borrowed);last=contract;String id="actual-query-"+(++nativeCalls);contract.prepare(input,id);
            var packet=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);packet.set("result",OpportunityJson.toNode(result));
            RawJson frame=new RawJson(DriverJson.encodeNode(packet));if(corruptPacket)packet.put("request_id","another-query");
            var original=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(DriverJson.encode(result))),new RawJson(DriverJson.encodeNode(packet)),new byte[]{1});
            ExactRef dispatch=new ExactRef("synthetic-dispatch-"+id,frame.bytes().length,DriverJson.sha256(frame.bytes()));outcomes.put(dispatch,original);
            var g=new PlanningReadGuard(guard(input.operation()),true,true,true,"a".repeat(64));var receipt=new PlanningReadReceipt(input,contract.contractId(),id,g,g,original);
            ExactRef reference=new ExactRef("synthetic-read-"+id,1,"b".repeat(64));receipts.put(reference,receipt);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,reference);
        }
    }
}
