package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;

/** Real frozen callable catalog and immutable capability input codecs, with controlled memory originals. No dispatch/writer/Game. */
final class PrivateGovernanceCapabilityProjectionTest {
    private static final String EXE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final ExactRef SOURCE=new ExactRef("D:/test-memory/governance-original-source.java",1,"a".repeat(64));
    private record Fixture(Complete frame,DriverSnapshotFacts.Known current,DynamicCapabilities.ActualDriverInputsSource inputs,Obj received){}
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef original(byte[] value){return new ExactRef("D:/test-memory/governance-caps/"+DriverJson.sha256(value)+".json",value.length,DriverJson.sha256(value));}
    private static Fixture fixture(boolean paused)throws Exception{
        var seed=GovernanceFixtures.request(9,true,List.of());var id=seed.before();var game=id.game();
        byte[] wire=bytes("{\"format_version\":2,\"pipe_name\":\"memory-governance-caps\",\"bridge_pid\":123,\"episode_character_id\":29829,\"episode_run_id\":\"unit-episode\",\"last_checkpoint\":null,\"command_history\":[],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":{\"campaign_id\":\"original\",\"anchor\":{\"character_id\":29829}},\"rollback_war_failures\":[]}");
        var imported=DriverFactsRepository.imported(original(wire),wire,3,7,game,new Obj(Map.of()));
        byte[] state=bytes("{\"paused\":"+paused+",\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,\"played_character\":{\"character_id\":29829,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal\":false,\"one_life_terminal_reason\":null,\"episode_identity_pending\":false,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":123,\"connection_generation\":5}}");
        var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",id.frame().snapshotId()).put("revision",9);packet.set("state",StrictJson.parse(state));
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(id.machineId(),game,BigInteger.valueOf(5),seed.sessionId()),id.frame().snapshotId(),BigInteger.valueOf(9),new RawJson(state),NativeWire.packet(StrictJson.canonical(packet)),GovernanceFixtures.NOW);
        var protocol=new Obj(Map.of("backend_id",new Text("native-headless"),"source",new Text("injected-dll-named-pipe"),"diagnostics",DriverJson.object(state,65536).get("diagnostics")));
        var driverBytes=new RawJson(imported.driver().encode());var manifest=DriverObservationEvidenceReader.encode(imported,actual,id.frame().revision(),1,seed.source(),protocol,original(driverBytes.bytes()));
        var facts=DriverObservationEvidenceReader.decode(original(manifest.bytes()),manifest,driverBytes,actual);
        var current=new DriverSnapshotFacts.Known(imported.driver(),imported.stamp(),imported.originalHistoryBasis(),imported.actionRows(),imported.auxiliary(),imported.loop(),Optional.of(facts));
        var assembled=new DriverObservationAssembler().assemble(actual,facts,original(actual.originalPacket()));
        var frame=assertInstanceOf(Complete.class,assembled,()->"actual frame join: "+assembled);
        assertEquals(seed.before().game(),frame.identity().game());assertEquals(id.frame().episodeRunId(),frame.identity().frame().episodeRunId());
        assertEquals(BigInteger.valueOf(53144328),frame.identity().frame().identity().dateRaw());
        var config=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
        var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        var fields=new DriverRuntimeCapabilities.Fields(List.of(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),config,Optional.empty(),session);
        var encoded=DriverRuntimeCapabilities.encode(frame,current,BigInteger.ZERO,fields);
        var input=DynamicCapabilities.DriverInputs.decode(frame,current,original(encoded.bytes()),encoded.bytes());
        DynamicCapabilities.ActualDriverInputsSource source=new DynamicCapabilities.ActualDriverInputsSource(){
            @Override public DynamicCapabilities.InputState capture(Complete supplied,DriverSnapshotFacts.Known known){assertSame(frame,supplied);assertSame(current,known);return new DynamicCapabilities.AvailableInputs(input);}
            @Override public boolean stillCurrent(DynamicCapabilities.DriverInputs captured,Complete supplied,DriverSnapshotFacts.Known known){return captured==input&&supplied==frame&&known==current;}
        };
        var hello=new Obj(Map.of("pid",new IntegerValue(BigInteger.valueOf(game.pid())),"connection_generation",new IntegerValue(BigInteger.valueOf(5)),"capabilities",new Arr(List.of(new Text("game.state.snapshot")))));
        var diagnostics=new Obj(Map.of("connected",new Bool(true),"semantic_state_available",new Bool(true),"transport_fatal_error",Nil.INSTANCE,"hello",hello));
        var received=new Obj(Map.of("mode",new Text("native-headless"),"backend_id",new Text("native-headless"),"visual_fallback",new Bool(false),"snapshot",new Bool(true),"wait_for_change",new Bool(false),"diagnostics",diagnostics));
        return new Fixture(frame,current,source,received);
    }
    private static RootExecutableBindings installed(Set<OperationKey> actions,ReadContract.GuardMode mode){
        var producer=new GovernanceActionPreparation("1.20.0.4",EXE,(same,c,id)->{throw new AssertionError("projection cannot refresh Council");},(same,c)->{throw new AssertionError("projection cannot acquire a writer");});
        var callable=GovernanceActionBindings.bindings(new GovernanceActionBindings.Sources(SOURCE,SOURCE,SOURCE),producer,
                (c,a,d)->{throw new AssertionError("projection must never execute a world action");},actions);
        var bindings=callable.stream().map(effect->new RootExecutableBindings.ActionBinding(effect,mode,
                effect.operation().value().equals(CouncilActionCodec.ASSIGN)?Optional.of("game.action.assign-councillor-v1"):Optional.empty(),SOURCE)).toList();
        var contracts=NativeGovernanceEffects.readContracts(SOURCE,SOURCE,SOURCE);
        var verifiers=actions.stream().map(operation->NativeGovernanceEffects.archivedVerifier(operation,SOURCE,(basis,archive)->{throw new AssertionError("projection cannot replay an effect");},contracts,(c,a,r,archive)->{throw new AssertionError("projection cannot verify preparation");})).toList();
        var reads=new GovernancePlanningReads(new GovernancePlanningReads.Sources(SOURCE,SOURCE),"1.20.0.4",EXE);
        var root=RootExecutableBindings.freeze(bindings,RootReadContractCatalog.staticOnly(reads.all()),List.of(),verifiers,List.of(),16);
        root.requireCompleteArchiveCoverage();return root;
    }
    private static DynamicCapabilities.CapabilitySnapshot project(Fixture fixture,RootExecutableBindings installed)throws Exception{
        var actual=DynamicCapabilities.project(fixture.frame(),fixture.current(),fixture.received(),installed,fixture.inputs(),null);
        return assertInstanceOf(DynamicCapabilities.Projected.class,actual,()->"actual immutable input projection: "+actual).snapshot();
    }
    @Test void actualInstalledPrivateFocusReachesOpeningWithoutAnAdvertisedCapability()throws Exception{
        var fixture=fixture(true);var bindings=installed(Set.of(GovernancePolicies.FOCUS),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        assertSame(bindings.actualActionBinding(GovernancePolicies.FOCUS).orElseThrow(),bindings.effects().installed().getFirst());
        var projected=project(fixture,bindings);
        assertTrue(projected.actionSteps().contains(GovernancePolicies.FOCUS),"actual installed private FOCUS must enter the capability candidates");
        assertEquals(Set.of("game.state.snapshot"),projected.bridgeCapabilities());assertTrue(projected.compositeActionSteps().isEmpty());
        var observation=new PlanningObservation(fixture.frame().semantic(),List.of(),projected.actionSteps(),projected.bridgeCapabilities(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),true);
        var request=new PlanningRequest(fixture.frame().identity(),fixture.frame().source(),fixture.frame().sessionId(),GovernanceFixtures.NOW.plusSeconds(30),observation);
        var supplier=new GovernanceFixtures.Supplier(request);
        var old=supplier.state;
        supplier.state=new GovernanceObservationSupplier.Durable(old.observed(),old.sessionId(),old.cadence(),
                Optional.of(new GovernanceObservationSupplier.OpeningGate(request.before().frame().episodeRunId(),request.before().frame().identity().dateRaw(),
                        GovernanceObservationSupplier.OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty())),old.council(),old.crown());
        var selected=assertInstanceOf(OrdinaryPolicy.Replace.class,new GovernancePolicies.Opening(supplier,SOURCE).evaluate(request,OrdinaryPolicy.Draft.empty()));
        var command=selected.draft().command().orElseThrow();assertEquals(GovernancePolicies.FOCUS,command.operation());
        assertEquals(OrdinaryPolicy.Kind.OPENING_FOCUS,selected.draft().kind());assertEquals(request.before(),command.before());
        assertEquals(request.source(),command.source());assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void absentWrongOriginReadAndMissingAdvertisedCapabilityDoNotBecomePrivateActions()throws Exception{
        var fixture=fixture(true);
        assertFalse(project(fixture,installed(Set.of(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)).actionSteps().contains(GovernancePolicies.FOCUS));
        assertFalse(project(fixture,installed(Set.of(GovernancePolicies.FOCUS),ReadContract.GuardMode.FRONTEND_SESSION)).actionSteps().contains(GovernancePolicies.FOCUS));
        var actual=project(fixture,installed(Set.of(new OperationKey(CouncilActionCodec.ASSIGN)),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP));
        assertFalse(actual.actionSteps().contains(new OperationKey(CouncilActionCodec.ASSIGN)));
        assertFalse(actual.actionSteps().contains(new OperationKey(GovernancePlanningReads.FORMAL)));
        assertFalse(project(fixture(false),installed(Set.of(GovernancePolicies.FOCUS),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)).actionSteps().contains(GovernancePolicies.FOCUS));
    }
}
