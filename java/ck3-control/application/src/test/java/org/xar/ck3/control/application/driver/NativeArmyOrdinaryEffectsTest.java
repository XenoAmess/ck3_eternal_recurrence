package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software native-frame producer -> complete Driver -> effect -> archive -> same domain replay. No live CK3 credit. */
final class NativeArmyOrdinaryEffectsTest {
    private static final Instant DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final String BASE="""
      {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
       "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"active_wars":[],
       "player_armies":[{"army_id":0,"owner_character_id":73,"controllable":true}],"diagnostics":{}}
      """;
    private static ObjectNode node(String json) { return (ObjectNode)StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    private static OpportunityJson.Obj obj(ObjectNode value) { return DriverJson.object(StrictJson.canonical(value),RawJson.MAXIMUM_BYTES); }
    private static ObjectNode state(boolean extra,boolean keepZero) {
        ObjectNode state=node(BASE);var armies=state.putArray("player_armies");
        if(keepZero)armies.addObject().put("army_id",0).put("owner_character_id",73).put("controllable",true);
        if(extra)armies.addObject().put("army_id",4).put("owner_character_id",73).put("controllable",true);
        return state;
    }
    private static NativeObservationPort.ObservedFrame frame(int revision,ObjectNode state) {
        ObjectNode body=StrictJson.object().put("protocol_version",1).put("type","state_snapshot").put("snapshot_id","snapshot-"+revision).put("revision",revision);body.set("state",state);
        byte[] raw=StrictJson.canonical(body),packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),BigInteger.valueOf(5),"held-session"),
                "snapshot-"+revision,BigInteger.valueOf(revision),new RawJson(StrictJson.canonical(state)),packet,Instant.parse("2026-10-23T16:00:00Z").plusSeconds(revision));
    }
    private static DriverObservationFacts facts(NativeObservationPort.ObservedFrame actual,FixtureArchive archive,DriverSnapshotFacts.Known known) {
        RawJson full=new RawJson(known.driver().encode());ExactRef fullRef=archive.preserveMaterial(full);
        RawJson manifest=DriverObservationEvidenceReader.encode(known,actual,actual.nativeRevision(),DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION,DriverStateAssemblerTest.source(),new OpportunityJson.Obj(Map.of()),fullRef);
        ExactRef manifestRef=archive.preserveMaterial(manifest);return DriverObservationEvidenceReader.decode(manifestRef,manifest,full,actual);
    }
    private record Fixture(FixtureArchive archive,HeldDriverObservationPort held,DriverObservationAssembler.Complete before,NativeArmyOrdinaryEffects observer) { }
    private static Fixture fixture(ObjectNode before,ObjectNode after) throws InterruptedException {
        return fixture(before,after,DriverStateAssemblerTest.known());
    }
    private static Fixture fixture(ObjectNode before,ObjectNode after,DriverSnapshotFacts.Known known) throws InterruptedException {
        FixtureArchive archive=new FixtureArchive();AtomicInteger index=new AtomicInteger();
        var held=new HeldDriverObservationPort(deadline->frame(index.getAndIncrement()==0?9:10,index.get()==1?before:after),
                actual->new DriverObservationFacts.Known(facts(actual,archive,known)),archive::preserveNativeFrame,new DriverObservationAssembler(),8);
        var observed=held.observe(DEADLINE);var observer=new NativeArmyOrdinaryEffects(new NativeEffectSnapshots(held,archive),
                (query,command,attempt,current)->Optional.empty(),new DriverFrameEvidenceLoader(new DriverObservationAssembler()),Optional.empty());
        return new Fixture(archive,held,observed,observer);
    }
    private static ActionCommand command(Fixture fixture,Kind kind,String operation,ObjectNode publicArguments) {
        publicArguments.put("expected_revision",fixture.before().identity().frame().revision().toString());
        var args=new ArmyOrdinaryActionArguments(kind,new RawJson(StrictJson.canonical(publicArguments)),List.of());var key=new OperationKey(operation);
        var command=new ActionCommand("ordinary-"+kind.wire(),fixture.before().identity(),fixture.before().source(),fixture.before().sessionId(),key,args.encode(),
                NativeArmyOrdinaryEffects.expected(fixture.before().identity(),fixture.before().source(),key,args.raw()),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        var roundTrip=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,roundTrip);return roundTrip;
    }
    /** Typed source DATA only; the global physical source/history qualification is deliberately unavailable here. */
    private static GuardEvidence originalGuard(Fixture fixture,DriverObservationAssembler.Complete frame,OperationKey operation) {
        var archive=fixture.archive();ExactRef manifestRef=DriverObservationEvidenceReader.reference(frame.semantic().get("java_driver_facts_evidence"));
        RawJson manifest=archive.loadMaterial(manifestRef);ExactRef fullRef=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        var raw=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,archive.loadNativeFrame(frame.originalEvidence()));
        var observed=DriverObservationEvidenceReader.decode(manifestRef,manifest,archive.loadMaterial(fullRef),raw);
        var stamp=new DriverSnapshotFacts.Stamp(observed.driverVersion(),observed.episodeEpoch(),frame.identity().game(),
                frame.identity().frame().episodeRunId(),DriverJson.sha256(observed.driver().encode()));
        var known=new DriverSnapshotFacts.Known(observed.driver(),stamp,fullRef,List.of(),new OpportunityJson.Obj(Map.of()),Optional.empty(),Optional.of(observed));
        ExactRef semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
        ExactRef driverStamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
        ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",frame.identity().game().pid())
                .put("connection_generation",frame.connectionGeneration()).put("bridge_version","software-domain-fixture")
                .put("expected_ck3_sha256","0".repeat(64)).put("game_adapter_id","unqualified-software-fixture")
                .put("game_adapter_status","unsupported_fixture").put("ck3_build_match",false);hello.putArray("capabilities");
        ExactRef originalHello=archive.retainPacket(framed(hello));
        ObjectNode heartbeat=StrictJson.object().put("type","heartbeat").put("protocol_version",1)
                .put("pid",frame.identity().game().pid()).put("sequence",0).put("monotonic_ms",0);
        ExactRef originalHeartbeat=archive.retainPacket(framed(heartbeat));
        var capabilities=new OpportunityJson.Obj(Map.of());
        ExactRef capRef=archive.preserveMaterial(new RawJson(DriverJson.encode(capabilities)));
        ExactRef unqualified=archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("status","unqualified-software-fixture"))));
        var evidence=new SessionPorts.SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),driverStamp,fullRef,frame.observedAt());
        var lease=new ReadinessAuthority.LeaseSnapshot(frame,known,capabilities,evidence,Set.of(),Set.of(),
                originalHello,originalHeartbeat,DEADLINE,unqualified);
        ObjectNode state=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",frame.identity().machineId())
                .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10)
                .put("start_date_raw",53144328).put("target_date_raw",53144328+240).put("last_settled_date_raw",53144328).put("last_settled_cycles",0);
        state.putObject("UNKNOWN");
        var head=new WriterContracts.Head(ContinuityState.fromJson(state,frame.identity().machineId()),List.of(),List.of(),List.of(),false);
        String authority="software-fixture-domain-only";
        ExactRef basis=RootGuardEvidence.preserve(lease,operation,authority,capRef,archive,head);
        return new GuardEvidence(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),frame.connectionGeneration(),operation,
                frame.originalEvidence(),originalHello,authority,frame.observedAt(),DEADLINE,List.of(basis));
    }
    private static ActionState.Attempt attempt(Fixture fixture,ActionCommand command) {
        var before=fixture.before();var guard=originalGuard(fixture,before,command.operation());
        return new ActionState.Attempt("original-native-request",before.observedAt(),guard,new NativeRequest(command.operation().value(),Optional.empty(),new RawJson(new byte[]{'{','}'})));
    }
    private static NativeActionPort.AckReceived dispatch(Fixture fixture,ActionCommand command,ActionState.Attempt attempt) {
        return dispatch(fixture,command,attempt,new RawJson("{\"accepted\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    private static NativeActionPort.AckReceived dispatch(Fixture fixture,ActionCommand command,ActionState.Attempt attempt,RawJson token) {
        ObjectNode outbound=StrictJson.object().put("type","execute_step").put("protocol_version",1).put("request_id",attempt.requestId())
                .put("step",command.operation().value()).put("expected_revision",command.before().frame().identity().nativeRevision());
        byte[] raw=StrictJson.canonical(outbound),packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
        ObjectNode frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);frame.set("result",StrictJson.parse(token.bytes()));
        byte[] response=StrictJson.canonical(frame),responsePacket=ByteBuffer.allocate(response.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(response.length).put(response).array();
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(token),new RawJson(response),responsePacket,
                Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),packet)));
        fixture.archive().preserve(ack);return ack;
    }
    private static ActionReceipt receipt(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,NativeEffectRegistry.Projected projected) {
        var effect=assertInstanceOf(ActionPorts.EffectObserved.class,projected.result());
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.Applied(effect.observation())));
    }
    private static void replay(Fixture fixture,ActionReceipt receipt) {
        var loader=new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        fixture.observer().archivedVerifier(receipt.command().operation(),DriverStateAssemblerTest.ref(new byte[]{1}),loader).verifier().verify(null,receipt,fixture.archive());
    }
    @Test void actualNewOwnedArmyAndOriginalOutboundSurviveArchiveReplay() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(true,true));var command=command(fixture,Kind.RAISE_TROOPS_DEFAULT,"raise-troops-default",StrictJson.object());
        var attempt=attempt(fixture,command);var dispatch=dispatch(fixture,command,attempt);var projected=fixture.observer().observe(command,attempt,dispatch);
        var receipt=receipt(command,attempt,dispatch,projected);assertTrue(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        var body=StrictJson.parse(projected.compatibleResult().orElseThrow().bytes());assertEquals(4,body.get("war_action").get("raised_army_ids").get(0).intValue());
        assertDoesNotThrow(()->replay(fixture,receipt));
        ExactRef after=((ActionState.Applied)((ActionState.Settled)receipt.state()).settlement()).observation().originalEvidence();
        fixture.archive().nativeFrames.get(after)[4]^=1;assertThrows(IllegalArgumentException.class,()->replay(fixture,receipt));
    }
    @Test void successfulAckUnchangedRosterAndMissingOutboundNeverBecomeMilitarySuccess() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(false,true));var command=command(fixture,Kind.RAISE_TROOPS_DEFAULT,"raise-troops-default",StrictJson.object());
        var attempt=attempt(fixture,command);var dispatch=dispatch(fixture,command,attempt);
        assertInstanceOf(ActionPorts.Pending.class,fixture.observer().observe(command,attempt,dispatch).result());
        var noOutbound=new NativeActionPort.AckReceived(dispatch.requestId(),true,dispatch.originalResultToken(),dispatch.originalFrame(),dispatch.originalPacket());
        assertInstanceOf(ActionPorts.Pending.class,fixture.observer().observe(command,attempt,noOutbound).result());
        ObjectNode unowned=state(true,true);((ObjectNode)unowned.get("player_armies").get(1)).put("owner_character_id",74);
        Fixture other=fixture(state(false,true),unowned);var otherCommand=command(other,Kind.RAISE_TROOPS_DEFAULT,"raise-troops-default",StrictJson.object());
        var otherAttempt=attempt(other,otherCommand);assertInstanceOf(ActionPorts.Pending.class,other.observer().observe(otherCommand,otherAttempt,dispatch(other,otherCommand,otherAttempt)).result());
        ObjectNode farOwner=state(true,true);((ObjectNode)farOwner.get("player_armies").get(1)).put("owner_character_id",BigInteger.ONE.shiftLeft(70));
        Fixture large=fixture(state(false,true),farOwner);var largeCommand=command(large,Kind.RAISE_TROOPS_DEFAULT,"raise-troops-default",StrictJson.object());
        var largeAttempt=attempt(large,largeCommand);assertInstanceOf(ActionPorts.Pending.class,large.observer().observe(largeCommand,largeAttempt,dispatch(large,largeCommand,largeAttempt)).result());
    }
    @Test void exactPublicArmyZeroDisappearsWhileSameCountAndMissingBeforeStayPending() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(false,false));var command=command(fixture,Kind.DISBAND_ARMY,"disband-army-0",StrictJson.object().put("army_id",0));
        var attempt=attempt(fixture,command);var dispatch=dispatch(fixture,command,attempt);var projected=fixture.observer().observe(command,attempt,dispatch);
        assertDoesNotThrow(()->replay(fixture,receipt(command,attempt,dispatch,projected)));
        Fixture unchanged=fixture(state(false,true),state(false,true));var same=command(unchanged,Kind.DISBAND_ARMY,"disband-army-0",StrictJson.object().put("army_id",0));
        var sameAttempt=attempt(unchanged,same);assertInstanceOf(ActionPorts.Pending.class,unchanged.observer().observe(same,sameAttempt,dispatch(unchanged,same,sameAttempt)).result());
        Fixture equalCount=fixture(state(false,true),state(true,false));var exact=command(equalCount,Kind.DISBAND_ARMY,"disband-army-0",StrictJson.object().put("army_id",0));
        var exactAttempt=attempt(equalCount,exact);assertInstanceOf(ActionPorts.EffectObserved.class,equalCount.observer().observe(exact,exactAttempt,dispatch(equalCount,exact,exactAttempt)).result());
    }
    private static ObjectNode assault(boolean active,int siege,int province) {
        ObjectNode state=state(false,true);ObjectNode war=state.withArray("active_wars").addObject().put("war_id",88)
                .put("player_side","attacker").put("player_relative_war_score",0);
        war.putArray("war_objective_province_ids").add(province);
        ObjectNode holding=war.putArray("objective_province_states").addObject().put("province_id",province)
                .put("occupation_observable",false).put("siege_observable",true);
        ObjectNode current=holding.putObject("active_siege").put("siege_id",siege).put("assault_observable",true)
                .put("assault_in_progress",active).put("can_start_assault",!active).put("can_stop_assault",active)
                .put("player_army_besieging",true).put("breach_level",1).put("assault_daily_casualties",0);
        for(String key:List.of("progress_fraction","current_work","total_work","assault_daily_progress"))
            current.putObject(key).put("raw",key.equals("total_work")?100000:0).put("scale",100000);
        return state;
    }
    @Test void assaultUsesSameWarProvinceAndSiegeTransitionThenTheSameArchiveReducer() throws InterruptedException {
        Fixture fixture=fixture(assault(false,22,300),assault(true,22,300));var command=command(fixture,Kind.START_ASSAULT,"start-assault-22",StrictJson.object().put("siege_id",22));
        var attempt=attempt(fixture,command);var dispatch=dispatch(fixture,command,attempt);var projected=fixture.observer().observe(command,attempt,dispatch);
        assertDoesNotThrow(()->replay(fixture,receipt(command,attempt,dispatch,projected)));
        Fixture replaced=fixture(assault(false,22,300),assault(true,23,300));var changed=command(replaced,Kind.START_ASSAULT,"start-assault-22",StrictJson.object().put("siege_id",22));
        var changedAttempt=attempt(replaced,changed);assertInstanceOf(ActionPorts.Pending.class,replaced.observer().observe(changed,changedAttempt,dispatch(replaced,changed,changedAttempt)).result());
        Fixture stop=fixture(assault(true,22,300),assault(false,22,300));var stopCommand=command(stop,Kind.STOP_ASSAULT,"stop-assault-22",StrictJson.object().put("siege_id",22));
        var stopAttempt=attempt(stop,stopCommand);var stopDispatch=dispatch(stop,stopCommand,stopAttempt);
        assertDoesNotThrow(()->replay(stop,receipt(stopCommand,stopAttempt,stopDispatch,stop.observer().observe(stopCommand,stopAttempt,stopDispatch))));
    }
    @Test void objectivePriorityAndAmbiguousWholeGraphCannotBorrowAConvenientHolding() {
        var wrong=new ArmyAssaultSelection.Siege(22,true,true,false,true,true);
        var holding=new ArmyAssaultSelection.Holding(88,300,true,Optional.of(wrong));
        var selected=ArmyAssaultSelection.select(obj(assault(false,22,300)),List.of(holding),22).orElseThrow();
        assertEquals(ArmyAssaultSelection.Source.OBJECTIVE,selected.source());assertFalse(selected.siege().inProgress());
        ObjectNode ambiguous=assault(false,22,300);ObjectNode second=ambiguous.withArray("active_wars").addObject().put("war_id",89);
        second.putArray("objective_province_states").add(ambiguous.get("active_wars").get(0).get("objective_province_states").get(0).deepCopy());
        assertTrue(ArmyAssaultSelection.select(obj(ambiguous),List.of(),22).isEmpty());
        assertDoesNotThrow(()->new ArmyAssaultSelection.Siege(0,true,false,false,false,false));
        ObjectNode wrongType=assault(false,22,300);((ObjectNode)wrongType.get("active_wars").get(0).get("objective_province_states").get(0).get("active_siege")).put("assault_in_progress",1);
        assertThrows(IllegalArgumentException.class,()->ArmyAssaultSelection.select(obj(wrongType),List.of(),22));
    }
    @Test void originalOutboundStepMismatchIsRejectedAndMaaQueuedResultStaysPending() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(true,true));var command=command(fixture,Kind.RAISE_TROOPS_DEFAULT,"raise-troops-default",StrictJson.object());
        var attempt=attempt(fixture,command);var original=dispatch(fixture,command,attempt);byte[] changed=original.outbound().orElseThrow().originalPacket();
        // Same-sized valid UTF-8 JSON mutation changes the actual operation, not a caller-side alias.
        String literal=new String(changed,4,changed.length-4,java.nio.charset.StandardCharsets.UTF_8).replace("raise-troops-default","raise-troops-defaulx");
        byte[] raw=literal.getBytes(java.nio.charset.StandardCharsets.UTF_8);var packet=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
        var tampered=new NativeActionPort.AckReceived(original.requestId(),true,original.originalResultToken(),original.originalFrame(),original.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(original.requestId(),packet)));
        fixture.archive().preserve(tampered);assertThrows(IllegalArgumentException.class,()->fixture.observer().observe(command,attempt,tampered));
        Fixture maa=maaFixture();var queued=retainedMaa(maa);
        assertInstanceOf(ActionPorts.Pending.class,maa.observer().observe(queued.command(),queued.attempt(),queued.ack()).result());
        var missing=new NativeActionPort.AckReceived(queued.ack().requestId(),true,queued.ack().originalResultToken(),
                queued.ack().originalFrame(),queued.ack().originalPacket(),queued.ack().outbound());
        maa.archive().preserve(missing);
        assertThrows(IllegalArgumentException.class,()->maa.observer().observe(queued.command(),queued.attempt(),missing));
    }
    @Test void captureCountersCannotSubstituteForTheGateEpochAndClearTransition() {
        String before="{\"step\":\"query-army-gathering-research-sampling-v1\",\"accepted\":true,\"status\":\"disabled\",\"backend_id\":\"native-headless\",\"army_gathering_research_sampling_v1\":{\"capture_enabled\":false,\"busy\":false,\"clear_completed\":true,\"epoch\":4,\"active_captures\":0,\"retained_records\":0,\"qualified_records\":0,\"readiness\":\"off\"}}";
        var previous=ArmyGatheringCodec.decode(before.getBytes(java.nio.charset.StandardCharsets.UTF_8),ArmyGatheringCodec.QUERY);
        String enabled=before.replace("\"status\":\"disabled\"","\"status\":\"enabled\"").replace("\"capture_enabled\":false","\"capture_enabled\":true").replace("\"clear_completed\":true","\"clear_completed\":false").replace("\"epoch\":4","\"epoch\":5").replace("\"readiness\":\"off\"","\"readiness\":\"awaiting_sample\"");
        var observed=ArmyGatheringCodec.decode(enabled.getBytes(java.nio.charset.StandardCharsets.UTF_8),ArmyGatheringCodec.QUERY);
        assertTrue(NativeArmyOrdinaryEffects.samplingTransition(previous,observed,true));assertFalse(NativeArmyOrdinaryEffects.samplingTransition(previous,previous,true));
        var wrongEpoch=ArmyGatheringCodec.decode(enabled.replace("\"epoch\":5","\"epoch\":4").getBytes(java.nio.charset.StandardCharsets.UTF_8),ArmyGatheringCodec.QUERY);
        assertFalse(NativeArmyOrdinaryEffects.samplingTransition(previous,wrongEpoch,true));
    }
    @Test void durableArgumentsRejectWrongFieldsTypesAndCanonicalRevisionBeforeProjection() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(false,true));var before=fixture.before();
        for(ObjectNode wrong:List.of(StrictJson.object().put("siege_id",true),StrictJson.object().putNull("siege_id"),
                StrictJson.object().put("siege_id",22).put("invented",1),StrictJson.object().put("siege_id",22).put("expected_revision","+9"))) {
            var args=new ArmyOrdinaryActionArguments(Kind.START_ASSAULT,new RawJson(StrictJson.canonical(wrong)),List.of());
            assertThrows(IllegalArgumentException.class,()->NativeArmyOrdinaryEffects.expected(before.identity(),before.source(),new OperationKey("start-assault-22"),args.raw()));
        }
        var original=new ArmyOrdinaryActionArguments(Kind.DISBAND_ARMY,new RawJson("{\"army_id\":0}".getBytes(java.nio.charset.StandardCharsets.UTF_8)),List.of());
        assertEquals(original,ArmyOrdinaryActionArguments.decode(original.raw()));
        assertThrows(IllegalArgumentException.class,()->NativeArmyOrdinaryEffects.expected(before.identity(),before.source(),new OperationKey("disband-army-1"),original.raw()));
    }
    private static final UUID CUSTODY_EPOCH=UUID.fromString("cf539187-7770-46fc-b99d-a9e12285a067");
    private static NativeActionPort.AckReceived withChronology(NativeActionPort.AckReceived ack,DriverObservationAssembler.Complete frame,
            long order,Instant entered,UUID epoch) {
        var session=new NativeObservationPort.TransportSession(frame.identity().machineId(),frame.identity().game(),frame.connectionGeneration(),frame.sessionId());
        var chronology=new NativeRequestChronology(session,epoch,ack.requestId(),
                NativeRequestChronology.PacketIdentity.of(ack.outbound().orElseThrow().originalPacket()),
                NativeRequestChronology.PacketIdentity.of(ack.originalPacket()),
                new NativeRequestChronology.Event(BigInteger.valueOf(order),entered),
                new NativeRequestChronology.Event(BigInteger.valueOf(order+1),entered.plusMillis(1)),
                new NativeRequestChronology.Event(BigInteger.valueOf(order+2),entered.plusMillis(2)));
        // Domain fixture explicitly round-trips the same production custody codec; endpoint-minted chronology
        // and physical cold archive coverage are owned by transport06/NativeArchiveChronologyTest.
        chronology=NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(chronology));
        return new NativeActionPort.AckReceived(ack.requestId(),ack.nativeOk(),ack.originalResultToken(),ack.originalFrame(),
                ack.originalPacket(),ack.outbound(),Optional.of(chronology));
    }
    private static byte[] framed(ObjectNode value) {
        byte[] raw=StrictJson.canonical(value);return ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
    }
    private static PlanningReadReceipt samplingRead(Fixture fixture,String requestId,boolean enabled,long epoch,long order,Instant entered,UUID custodyEpoch,boolean heldCustody) {
        var frame=fixture.before();var operation=new OperationKey(ArmyGatheringCodec.QUERY);
        ObjectNode result=StrictJson.object().put("step",ArmyGatheringCodec.QUERY).put("accepted",true)
                .put("status",enabled?"enabled":"disabled").put("backend_id","native-headless");
        result.putObject("army_gathering_research_sampling_v1").put("capture_enabled",enabled).put("busy",false)
                .put("clear_completed",!enabled).put("epoch",epoch).put("active_captures",0).put("retained_records",0)
                .put("qualified_records",0).put("readiness",enabled?"awaiting_sample":"off");
        ObjectNode incoming=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",true);
        incoming.set("result",result);ObjectNode outgoing=StrictJson.object().put("type","execute_step").put("protocol_version",1)
                .put("request_id",requestId).put("step",ArmyGatheringCodec.QUERY).put("expected_revision",frame.identity().frame().identity().nativeRevision());
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(StrictJson.canonical(result))),
                new RawJson(StrictJson.canonical(incoming)),framed(incoming),Optional.of(new NativeActionPort.OutboundPacket(requestId,framed(outgoing))));
        if(heldCustody)ack=withChronology(ack,frame,order,entered,custodyEpoch);fixture.archive().preserve(ack);
        var binding=originalGuard(fixture,frame,operation);
        var guard=new PlanningReadGuard(binding,true,true,true,frame.fullBindingSha256());
        var request=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),operation,new OpportunityJson.Obj(Map.of()),DEADLINE);
        var read=new PlanningReadReceipt(request,"actual-sampling-domain-fixture/v1",requestId,guard,guard,ack);
        fixture.archive().preserveRead(read);return read;
    }
    private static ActionCommand samplingCommand(Fixture fixture,PlanningReadReceipt pre) {
        var arguments=new ArmyOrdinaryActionArguments(Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1,
                new RawJson(StrictJson.canonical(StrictJson.object().put("enabled",true).put("expected_revision",fixture.before().identity().frame().revision().toString()))),
                List.of(fixture.archive().readReferenceOf(pre)));
        var operation=new OperationKey(ArmyGatheringCodec.ENABLE);
        return new ActionCommand("sampling-control",fixture.before().identity(),fixture.before().source(),fixture.before().sessionId(),operation,
                arguments.encode(),NativeArmyOrdinaryEffects.expected(fixture.before().identity(),fixture.before().source(),operation,arguments.raw()),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
    }
    private static NativeArmyOrdinaryEffects samplingObserver(Fixture fixture,PlanningReadReceipt post) {
        return new NativeArmyOrdinaryEffects(new NativeEffectSnapshots(fixture.held(),fixture.archive()),
                (query,command,attempt,current)->Optional.of(post),new DriverFrameEvidenceLoader(new DriverObservationAssembler()),Optional.empty());
    }
    private static ActionState.Attempt samplingAttempt(Fixture fixture,ActionCommand command) {
        var original=attempt(fixture,command);
        return new ActionState.Attempt(original.requestId(),fixture.before().observedAt().plusSeconds(2),original.guard(),original.preparedRequest());
    }
    private static NativeActionPort.AckReceived samplingDispatch(Fixture fixture,ActionCommand command,ActionState.Attempt attempt,boolean custody) {
        var original=dispatch(fixture,command,attempt);
        if(!custody)return original;
        var with=withChronology(original,fixture.before(),4,attempt.submittedAt().plusMillis(1),CUSTODY_EPOCH);fixture.archive().preserve(with);return with;
    }
    @Test void actualOrderedQueryUsesUnchangedOldSemanticFrameAndOnlyControlSurvivesPairedArchiveReplay() throws InterruptedException {
        Fixture fixture=fixture(state(false,true),state(false,true));var time=fixture.before().observedAt();
        var pre=samplingRead(fixture,"independent-before",false,4,1,time.plusSeconds(1),CUSTODY_EPOCH,true);
        var command=samplingCommand(fixture,pre);var attempt=samplingAttempt(fixture,command);
        var dispatch=samplingDispatch(fixture,command,attempt,true);
        var post=samplingRead(fixture,"independent-after",true,5,7,attempt.submittedAt().plusMillis(4),CUSTODY_EPOCH,true);
        assertTrue(post.before().binding().observedAt().isBefore(attempt.submittedAt()));
        var observer=samplingObserver(fixture,post);var projected=observer.observe(command,attempt,dispatch);
        var observed=assertInstanceOf(ActionPorts.ControlObserved.class,projected.result()).observation();
        assertEquals(time,post.before().binding().observedAt());assertEquals(pre.before().binding().nativeEvidence(),post.before().binding().nativeEvidence());
        assertThrows(IllegalArgumentException.class,()->ActionEffects.validate(command,attempt,observed));
        assertDoesNotThrow(()->ActionEffects.validate(command,attempt,dispatch,observed));
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,observed));
        assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        assertDoesNotThrow(()->observer.archivedVerifier(command.operation(),DriverStateAssemblerTest.ref(new byte[]{1}),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler())).verifier().verify(null,receipt,fixture.archive()));
        var changed=withChronology(post.original(),fixture.before(),7,attempt.submittedAt().plusMillis(4),UUID.fromString("291afee4-9873-41a3-a8d5-1c2b3164f7b0"));
        fixture.archive().reads.put(fixture.archive().readReferenceOf(post),new PlanningReadReceipt(post.request(),post.contractId(),post.requestId(),post.before(),post.after(),changed));
        assertThrows(IllegalArgumentException.class,()->observer.archivedVerifier(command.operation(),DriverStateAssemblerTest.ref(new byte[]{1}),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler())).verifier().verify(null,receipt,fixture.archive()));
    }
    @Test void missingOriginalChronologyStaysPendingEvenWhenGateEpochAndAckLookCorrect() throws InterruptedException {
        for(boolean missingSubmission:List.of(false,true)) {
            Fixture fixture=fixture(state(false,true),state(false,true));var time=fixture.before().observedAt();
            var pre=samplingRead(fixture,"independent-before",false,4,1,time.plusSeconds(1),CUSTODY_EPOCH,true);
            var command=samplingCommand(fixture,pre);var attempt=samplingAttempt(fixture,command);
            var dispatch=samplingDispatch(fixture,command,attempt,!missingSubmission);
            var post=samplingRead(fixture,"independent-after",true,5,7,attempt.submittedAt().plusMillis(4),CUSTODY_EPOCH,missingSubmission);
            assertInstanceOf(ActionPorts.Pending.class,samplingObserver(fixture,post).observe(command,attempt,dispatch).result());
        }
    }
    @Test void staleOrForeignEndpointEpochCannotBecomeFreshAndCorrectChronologyCannotInventGateTransition() throws InterruptedException {
        for(int mode:List.of(0,1,2)) {
            Fixture fixture=fixture(state(false,true),state(false,true));var time=fixture.before().observedAt();
            var pre=samplingRead(fixture,"independent-before",false,4,1,time.plusSeconds(1),CUSTODY_EPOCH,true);
            var command=samplingCommand(fixture,pre);var attempt=samplingAttempt(fixture,command);var dispatch=samplingDispatch(fixture,command,attempt,true);
            var post=samplingRead(fixture,"independent-after",mode!=2,mode==2?4:5,mode==0?2:7,
                    attempt.submittedAt().plusMillis(4),mode==1?UUID.fromString("291afee4-9873-41a3-a8d5-1c2b3164f7b0"):CUSTODY_EPOCH,true);
            if(mode<2)assertThrows(IllegalArgumentException.class,()->samplingObserver(fixture,post).observe(command,attempt,dispatch));
            else assertInstanceOf(ActionPorts.Pending.class,samplingObserver(fixture,post).observe(command,attempt,dispatch).result());
        }
    }


    /** Original retained current4 HELLO DATA only; it opens no Root/source-capture permission. */
    private static ObjectNode originalCurrent4Hello() {
        try (var in=NativeArmyOrdinaryEffectsTest.class.getResourceAsStream("/declarationcontinuity/original-coalition-base.json")) {
            assertNotNull(in,"original current4 source fixture is mandatory");byte[] raw=in.readAllBytes();
            assertEquals("29df7a646c21cbd79ac8915604430b85935474be52c36afe2835e40268e067c4",DriverJson.sha256(raw));
            return ((ObjectNode)node(new String(raw,java.nio.charset.StandardCharsets.UTF_8)).path("base").path("snapshot").path("diagnostics").path("hello")).deepCopy();
        } catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    private static Fixture maaFixture() throws InterruptedException {
        ObjectNode before=state(false,true),after=state(true,true);
        for(ObjectNode actual:List.of(before,after)) {
            ((ObjectNode)actual.get("played_character")).put("character_id",29829);
            actual.get("player_armies").forEach(army->((ObjectNode)army).put("owner_character_id",29829));
        }
        byte[] bytes=DriverStateAssemblerTest.bytes(DriverStateAssemblerTest.WIRE
                .replace("\"episode_character_id\":73","\"episode_character_id\":29829")
                .replace("\"anchor\":{\"character_id\":73}","\"anchor\":{\"character_id\":29829}"));
        assertTrue(new String(bytes,java.nio.charset.StandardCharsets.UTF_8).contains("\"scale\":1.0"),"retain the original Driver floating token");
        var known=DriverFactsRepository.imported(DriverStateAssemblerTest.ref(bytes),bytes,3,7,DriverStateAssemblerTest.game(),new OpportunityJson.Obj(Map.of()));
        return fixture(before,after,known);
    }
    private record MaaVector(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack) { }
    /** Retained historical Python DTO (machine unknown), with explicit software wire chronology; no native/Root qualification. */
    private static MaaVector retainedMaa(Fixture fixture) {
        byte[] raw;
        try (var in=NativeArmyOrdinaryEffectsTest.class.getResourceAsStream("/maa/retained-python-create-queued.json")) {
            assertNotNull(in,"retained original MAA producer fixture is mandatory");raw=in.readAllBytes();
        } catch(java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
        assertEquals("10e308b4914627326d3b1b1fbb9fc80ae2e849d8f33f8588d0569a77fafdf93e",DriverJson.sha256(raw));
        ObjectNode original=(ObjectNode)node(new String(raw,java.nio.charset.StandardCharsets.UTF_8)).path("packet").get("structuredContent");
        var archive=fixture.archive();var before=fixture.before();var now=before.observedAt();var game=before.identity().game();
        archive.preserveMaterial(new RawJson(raw));
        var source=before.source();String session=before.sessionId();var identity=before.identity();
        BigInteger nativeRevision=identity.frame().identity().nativeRevision(),publicRevision=identity.frame().revision(),date=identity.frame().identity().dateRaw();
        ObjectNode publicArgs=StrictJson.object().put("type_index",original.get("type_index").intValue()).put("action_id",original.get("action_id").textValue());
        var operation=new OperationKey(NativeRegularMaaSubmission.STEP);
        var command=command(fixture,Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,operation.value(),publicArgs);
        ObjectNode fields=StrictJson.object().put("expected_snapshot_revision",nativeRevision).put("expected_public_revision",publicRevision).put("expected_date_raw",date)
                .put("expected_player_character_id",29829).put("type_index",original.get("type_index").intValue()).put("action_id",original.get("action_id").textValue());
        var request=new NativeRequest(operation.value(),Optional.empty(),new RawJson(StrictJson.canonical(fields)));NativeRegularMaaSubmission.validateRequest(request);archive.preserveRequest(request);
        var guard=originalGuard(fixture,before,operation);
        var attempt=new ActionState.Attempt(original.get("request_id").textValue(),now,guard,request);
        ObjectNode outbound=fields.deepCopy().put("type","execute_step").put("protocol_version",1).put("request_id",attempt.requestId()).put("step",operation.value()).put("expected_revision",nativeRevision);
        ObjectNode result=StrictJson.object().put("step",operation.value()).put("accepted",true).put("private_build",true).put("advertised",false)
                .put("backend_id","native-headless").put("game_version",original.get("exact_ck3_build").textValue()).put("executable_sha256",original.get("exe_sha256").textValue())
                .put("read_only",false).put("status",original.get("status").textValue()).put("snapshot_revision",nativeRevision).put("public_revision",publicRevision).put("date_raw",date)
                .put("capture_epoch",original.get("capture_epoch").bigIntegerValue()).put("action_id",original.get("action_id").textValue());
        result.set("submission",original.get("native_submission").deepCopy());
        ObjectNode top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);top.set("result",result);
        byte[] sent=framed(outbound),received=framed(top);
        var custody=new NativeRequestChronology(new NativeObservationPort.TransportSession(source.machineId(),game,BigInteger.valueOf(5),session),CUSTODY_EPOCH,attempt.requestId(),
                NativeRequestChronology.PacketIdentity.of(sent),NativeRequestChronology.PacketIdentity.of(received),
                new NativeRequestChronology.Event(BigInteger.ONE,now.plusMillis(1)),new NativeRequestChronology.Event(BigInteger.TWO,now.plusMillis(2)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3),now.plusMillis(3)));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(StrictJson.canonical(top)),received,
                Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),sent)),Optional.of(custody));archive.preserve(ack);
        assertArrayEquals(StrictJson.canonical(original,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(NativeRegularMaaSubmission.original(command,attempt,ack,archive).pythonProjection(),StrictJson.EXPLICIT_MAX_BYTES));
        return new MaaVector(command,attempt,ack);
    }
    private static ObjectNode terminalState(boolean active) {
        ObjectNode value = state(false, true);
        var diagnostics=(ObjectNode)value.get("diagnostics");
        diagnostics.put("bridge_pid",DriverStateAssemblerTest.game().pid()).put("connection_generation",5);
        diagnostics.set("hello", originalCurrent4Hello());
        value.putObject("played_character_gold").put("raw", 10000000).put("scale", 100000);
        value.putObject("played_character_prestige").put("raw", 20000000).put("scale", 100000);
        if (active) {
            var war = value.withArray("active_wars").addObject().put("war_id", 77).put("player_side", "attacker")
                    .put("player_is_primary_war_leader", true).put("primary_opponent_character_id", 74).put("player_relative_war_score", 5);
            war.putArray("targeted_title_ids");
        }
        return value;
    }
    private static OpportunityJson.Obj frozenTerminalPlan(String route) {
        ObjectNode plan = StrictJson.object().put("schema_version", 1).put("route", route)
                .put("verified", false).put("gen034_completion_eligible", true);
        var requirements = plan.putArray("requirements");
        org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.TERMINATE.forEach(requirements::add);
        ObjectNode expected = plan.putObject("expectations").put("war_id", 77).put("played_character_id", 73).put("opponent_character_id", 74);
        ObjectNode resources = expected.putObject("resources").put("scale", 100000);
        resources.putObject("gold").put("pre_raw", 10000000).put("delta_raw", 0).put("post_raw", 10000000);
        resources.putObject("prestige").put("pre_raw", 20000000).put("delta_raw", 0).put("post_raw", 20000000);
        expected.putObject("truce").put("owner_character_id", 73).put("toward_character_id", 74)
                .put("evaluated_days", 365).put("persisted_expiry_required", true);
        expected.putObject("source_specific_loss").put("war_id", 77).put("required_cleanup_status", "destroyed_or_untracked");
        expected.putObject("checkpoint").put("cold_restore_required", true);
        return obj(plan);
    }
    private static ActionCommand originalTerminalProposal(Fixture fixture, String route, Optional<OpportunityJson.Obj> plan) {
        var before = fixture.before();
        var observation = new org.xar.ck3.control.application.planning.PlanningObservation(before.semantic(), List.of(), Set.of(), Set.of(),
                Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        var request = new org.xar.ck3.control.application.planning.PlanningRequest(before.identity(), before.source(), before.sessionId(), DEADLINE, observation);
        var war = org.xar.ck3.control.application.planning.warexit.WarExitEvidence.wars(
                (ObjectNode) DriverJson.toNode(before.semantic())).get(0);
        return org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy.terminalCommand(request, war, route, plan);
    }
    private static ActionCommand canonicalTerminal(Fixture fixture, ActionCommand proposal) {
        var selected = ArmyOrdinaryPlannerSelection.decode(proposal.operation(), proposal.arguments(), proposal.before().frame().revision());
        var args = new ArmyOrdinaryActionArguments(selected.kind(), selected.publicArguments(), List.of())
                .withTerminalSelection(selected.terminalSelection());
        ArmyOrdinaryPlannerSelection.requirePrepared(proposal.operation(), proposal.arguments(), proposal.before().frame().revision(), args);
        var command = new ActionCommand(proposal.actionId(), proposal.origin(), proposal.source(), proposal.sessionId(), proposal.operation(),
                args.encode(), proposal.expectation(), proposal.claims(), proposal.deadline(), proposal.protocolIdentity());
        var cold = ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
        assertEquals(command, cold); assertEquals(ActionCodec.bodySha256(command), ActionCodec.bodySha256(cold)); return cold;
    }
    @Test void actualTerminalProducerPlanReachesCanonicalEffectsAndSameArchivedReducerWithoutFullPostwarCredit() throws InterruptedException {
        for (String route : List.of("white_peace", "surrender")) {
            Fixture fixture = fixture(terminalState(true), terminalState(false));
            var plan = frozenTerminalPlan(route);
            var proposal = originalTerminalProposal(fixture, route, Optional.of(plan));
            var command = canonicalTerminal(fixture, proposal);
            assertEquals(plan, ArmyOrdinaryActionArguments.decode(command.arguments()).terminalSelection().orElseThrow().encode().get("postcondition_plan"));
            var attempt = attempt(fixture, command); fixture.archive().preserveRequest(attempt.preparedRequest());
            var result = StrictJson.object().put("step", command.operation().value()).put("accepted", true).put("status", "submitted");
            var originalWireAck = dispatch(fixture, command, attempt, new RawJson(StrictJson.canonical(result)));
            var ack = withChronology(originalWireAck, fixture.before(), 40, attempt.submittedAt().plusMillis(1), CUSTODY_EPOCH);
            fixture.archive().preserve(ack);
            var observer = new NativeWarExitEffects(new NativeEffectSnapshots(fixture.held(), fixture.archive()));
            var projected = observer.observe(command, attempt, ack);
            assertInstanceOf(ActionPorts.EffectObserved.class, projected.result(), "initial ordinary war absence must still settle");
            ObjectNode compatible = node(new String(projected.compatibleResult().orElseThrow().bytes(), java.nio.charset.StandardCharsets.UTF_8));
            assertFalse(compatible.has("backend_id"), "raw three-field result must not acquire a backend field");
            assertArrayEquals(StrictJson.canonical(result), ack.originalResultToken().orElseThrow().bytes());
            var formal = compatible.get("raiktor_three_way_exit_postcondition_v3");
            assertNotNull(formal, "the ordinary typed envelope must retain the actual proposal plan");
            assertEquals("evidence_required", formal.get("status").textValue());
            assertEquals(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.NATIVE_SUBMISSION_SCHEMA,formal.path("schema").textValue());
            assertTrue(formal.path("action_submitted").booleanValue());
            assertTrue(formal.path("postcondition_receipt").path("action_submitted").booleanValue());
            assertTrue(formal.path("postcondition_receipt").path("checks").isObject() && formal.path("postcondition_receipt").path("checks").isEmpty());
            assertTrue(formal.path("postcondition_receipt").path("evidence").isObject() && formal.path("postcondition_receipt").path("evidence").isEmpty());
            for (String field : List.of("postcondition_verified", "checkpoint_cold_restore_verified", "gen034_closed"))
                assertFalse(formal.get(field).booleanValue(), "a frozen plan grants no full postwar or cold credit");
            var unavailable = observer.observe(command, attempt, originalWireAck);
            var unavailableRaw = StrictJson.parse(unavailable.compatibleResult().orElseThrow().bytes());
            assertFalse(unavailableRaw.path("raiktor_three_way_exit_postcondition_v3").path("action_submitted").booleanValue(),
                    "ACK type and retained outbound alone do not prove native custody");
            rejectNativeSubmissionOriginalMismatches(fixture, command, attempt, observer, ack);
            var retained = receipt(command, attempt, ack, projected);
            var cold = ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(retained, fixture.archive()), fixture.archive());
            assertEquals(retained, cold);
            var verifier = NativeWarExitEffects.archivedVerifier(command.operation(), command.source().sourceRef(),
                    new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
            verifier.verifier().verify(null, cold, fixture.archive());
            rejectCrossProfilePackets(cold,fixture.archive(),"v3");
            for(String corruption:List.of("both_versions","unknown_provider","missing_formal")) {
                var malformed=compatible.deepCopy();
                if(corruption.equals("both_versions"))malformed.set("raiktor_three_way_exit_postcondition_v1",formal.deepCopy());
                else if(corruption.equals("unknown_provider"))((ObjectNode)malformed.get("raiktor_three_way_exit_postcondition_v3")).put("provider","unknown");
                else malformed.remove("raiktor_three_way_exit_postcondition_v3");
                var wrongRaw=new RawJson(StrictJson.canonical(malformed));
                var original=NativeEffectEvidence.load(cold,fixture.archive(),new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
                var evidence=new NativeEffectSnapshots(fixture.held(),fixture.archive()).evidence(command,attempt,original.frames(),List.of(),wrongRaw);
                var wrong=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(projected.result(),Optional.of(wrongRaw)),List.of(evidence));
                var wrongReceipt=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt(command,attempt,ack,wrong),fixture.archive()),fixture.archive());
                var rejected=assertThrows(IllegalArgumentException.class,()->verifier.verifier().verify(null,wrongReceipt,fixture.archive()),corruption);
                assertTrue(rejected.getMessage().contains(corruption.equals("both_versions")?"ambiguous archived formal":"original material history projection"),rejected.getMessage());
            }

            ObjectNode changedPlan = (ObjectNode) DriverJson.toNode(plan); ((ObjectNode) changedPlan.get("expectations")).put("played_character_id", 75);
            var originalArguments = ArmyOrdinaryActionArguments.decode(command.arguments());
            var changedOrigin = new ArmyOrdinaryActionArguments.TerminalSelection(BigInteger.valueOf(77),
                    ArmyOrdinaryActionArguments.TerminalOutcome.exact(route), Optional.of(new RawJson(StrictJson.canonical(changedPlan))));
            var changedCommand = new ActionCommand(command.actionId(), command.origin(), command.source(), command.sessionId(), command.operation(),
                    originalArguments.withTerminalSelection(Optional.of(changedOrigin)).encode(), command.expectation(), command.claims(), command.deadline(), command.protocolIdentity());
            var forged = new ActionReceipt(cold.version(), cold.sequence(), changedCommand, ActionCodec.bodySha256(changedCommand), cold.state());
            assertThrows(IllegalArgumentException.class, () -> verifier.verifier().verify(null, forged, fixture.archive()),
                    "same archive cannot accept a rewritten original plan");
            ObjectNode wrongWar = (ObjectNode) DriverJson.toNode(plan); ((ObjectNode) wrongWar.get("expectations")).put("war_id", true);
            assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments.TerminalSelection(BigInteger.valueOf(77),
                    ArmyOrdinaryActionArguments.TerminalOutcome.exact(route), Optional.of(new RawJson(StrictJson.canonical(wrongWar)))));
            ObjectNode wrongRoute = (ObjectNode) DriverJson.toNode(plan); wrongRoute.put("route", "continue");
            assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments.TerminalSelection(BigInteger.valueOf(77),
                    ArmyOrdinaryActionArguments.TerminalOutcome.exact(route), Optional.of(new RawJson(StrictJson.canonical(wrongRoute)))));
        }
    }
    @Test void ordinaryThreeWayExplicitNullPlansStayDistinctFromMissingTerminalOrigin() throws InterruptedException {
        for (String route : List.of("player_victory", "surrender", "white_peace")) {
            Fixture fixture = fixture(terminalState(true), terminalState(false));
            var proposal = originalTerminalProposal(fixture, route, Optional.empty());
            var command = canonicalTerminal(fixture, proposal);
            var retained = ArmyOrdinaryActionArguments.decode(command.arguments());
            assertTrue(retained.terminalSelection().isPresent()); assertTrue(retained.terminalSelection().orElseThrow().postconditionPlan().isEmpty());
            assertSame(OpportunityJson.Nil.INSTANCE, retained.terminalSelection().orElseThrow().encode().get("postcondition_plan"));
            var attempt = attempt(fixture, command);
            var ack = dispatch(fixture, command, attempt, new RawJson(StrictJson.canonical(StrictJson.object().put("step", command.operation().value()).put("accepted", true))));
            var observer = new NativeWarExitEffects(new NativeEffectSnapshots(fixture.held(), fixture.archive()));
            var projected = observer.observe(command, attempt, ack);
            assertInstanceOf(ActionPorts.EffectObserved.class, projected.result());
            var compatible = node(new String(projected.compatibleResult().orElseThrow().bytes(), java.nio.charset.StandardCharsets.UTF_8));
            assertFalse(compatible.has("raiktor_three_way_exit_postcondition_v1"));
            assertFalse(compatible.has("raiktor_three_way_exit_postcondition_v2"));
            assertFalse(compatible.has("raiktor_three_way_exit_postcondition_v3"));
        }
    }

    @Test void retainedOriginalV1ArchiveReplaysStrictlyWithoutBorrowingTheCurrentSubmissionProjection() throws Exception {
        assertRetainedProjection("/legacy-v1-projection.json","d8e1a28f25a092e93b4fab3b160169e801de9d03b4d1c900871ae93faba0a9fd",1,false);
        assertRetainedProjection("/legacy-v2-projection.json","3110d7222e63f1e7a3db817d5692eef0ff6eb148437bf9061674afc2ae896f47",2,true);
    }
    private void assertRetainedProjection(String resource,String sha256,int version,boolean submitted) throws Exception {
        try (var stream=getClass().getResourceAsStream(resource)) {
            assertNotNull(stream,"actual pre-fix producer archive is mandatory");
            byte[] raw=stream.readAllBytes();
            assertEquals(sha256,DriverJson.sha256(raw));
            var rows=StrictJson.parse(raw,StrictJson.EXPLICIT_MAX_BYTES);
            assertTrue(rows.isArray());assertEquals(2,rows.size());
            for(var row:rows) {
                var archive=new FixtureArchive();
                for(var item:row.get("materials")) {
                    var ref=ExactRef.fromJson(item.get("ref"));byte[] bytes=legacyBytes(item,"base64",ref);
                    archive.materials.put(ref,new RawJson(bytes));
                }
                for(var item:row.get("native_frames")) {
                    var ref=ExactRef.fromJson(item.get("ref"));archive.nativeFrames.put(ref,legacyBytes(item,"base64",ref));
                }
                for(var item:row.get("requests")) {
                    var ref=ExactRef.fromJson(item.get("ref"));
                    var original=new NativeRequest(StrictJson.text(item.get("step")),item.get("capability").isNull()?Optional.empty():Optional.of(StrictJson.text(item.get("capability"))),
                            new RawJson(java.util.Base64.getDecoder().decode(StrictJson.text(item.get("fields")))));
                    assertEquals(ref.sha256(),DriverJson.sha256(FixtureArchive.requestBytes(original)));
                    archive.requests.put(ref,original);
                }
                for(var item:row.get("outcomes")) {
                    var ref=ExactRef.fromJson(item.get("ref"));
                    byte[] received=java.util.Base64.getDecoder().decode(StrictJson.text(item.get("received")));
                    byte[] sent=java.util.Base64.getDecoder().decode(StrictJson.text(item.get("sent")));
                    assertEquals(received.length-4,ByteBuffer.wrap(received).order(ByteOrder.LITTLE_ENDIAN).getInt());
                    var frame=StrictJson.parse(java.util.Arrays.copyOfRange(received,4,received.length));
                    String id=StrictJson.text(frame.get("request_id"));
                    var original=new NativeActionPort.AckReceived(id,frame.get("ok").booleanValue(),Optional.of(new RawJson(StrictJson.canonical(frame.get("result")))),
                            new RawJson(java.util.Arrays.copyOfRange(received,4,received.length)),received,Optional.of(new NativeActionPort.OutboundPacket(id,sent)));
                    assertEquals(ref.sha256(),DriverJson.sha256(FixtureArchive.dispatchBytes(original)));
                    archive.outcomes.put(ref,original);
                }
                byte[] bytes=StrictJson.canonical(row.get("receipt"),StrictJson.EXPLICIT_MAX_BYTES);
                var receipt=ActionReceiptCodec.decodeReceipt(bytes,archive);
                assertArrayEquals(bytes,ActionReceiptCodec.encodeReceipt(receipt,archive));
                var loaded=NativeEffectEvidence.load(receipt,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
                var compatible=StrictJson.parse(loaded.compatibleResult().bytes());
                var old=compatible.get("raiktor_three_way_exit_postcondition_v"+version);
                assertEquals("evidence_required",old.path("status").textValue());
                assertEquals(submitted,old.path("action_submitted").booleanValue());
                assertEquals(submitted,old.path("postcondition_receipt").path("action_submitted").booleanValue());
                var verify=NativeWarExitEffects.archivedVerifier(receipt.command().operation(),receipt.command().source().sourceRef(),
                        new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
                verify.verifier().verify(null,receipt,archive);
                rejectCrossProfilePackets(receipt,archive,"v"+version);
                var originalRef=archive.materialReferenceOf(loaded.compatibleResult());
                var forged=(ObjectNode)compatible.deepCopy();
                ((ObjectNode)forged.get("raiktor_three_way_exit_postcondition_v"+version)).put("action_submitted",!submitted);
                archive.materials.put(originalRef,new RawJson(StrictJson.canonical(forged)));
                assertThrows(IllegalArgumentException.class,()->verify.verifier().verify(null,receipt,archive),"unchanged refs cannot hide a rewritten old projection");
            }
        }
    }
    private static void rejectNativeSubmissionOriginalMismatches(Fixture fixture, ActionCommand command,
            ActionState.Attempt attempt, NativeWarExitEffects observer, NativeActionPort.AckReceived original) {
        for (String mutation : List.of("packet", "outbound", "frame", "token")) {
            byte[] packet = original.originalPacket();
            var outbound = original.outbound();
            RawJson frame = original.originalFrame(), token = original.originalResultToken().orElseThrow();
            switch (mutation) {
                case "packet" -> packet[packet.length - 2] ^= 1;
                case "outbound" -> {
                    byte[] bytes = outbound.orElseThrow().originalPacket(); bytes[bytes.length - 2] ^= 1;
                    outbound = Optional.of(new NativeActionPort.OutboundPacket(original.requestId(), bytes));
                }
                case "frame" -> frame = new RawJson(new byte[]{'{','}'});
                case "token" -> {
                    ObjectNode changed = (ObjectNode) StrictJson.parse(token.bytes()); changed.put("status", "queued");
                    token = new RawJson(StrictJson.canonical(changed));
                }
                default -> throw new AssertionError(mutation);
            }
            var corrupted = new NativeActionPort.AckReceived(original.requestId(), original.nativeOk(), Optional.of(token),
                    frame, packet, outbound, original.custody());
            assertThrows(IllegalArgumentException.class, () -> observer.observe(command, attempt, corrupted), mutation);
        }
        var negative = new NativeActionPort.AckReceived(original.requestId(), false, original.originalResultToken(),
                original.originalFrame(), original.originalPacket(), original.outbound(), original.custody());
        var result = observer.observe(command, attempt, negative);
        assertFalse(StrictJson.parse(result.compatibleResult().orElseThrow().bytes())
                .path("raiktor_three_way_exit_postcondition_v3").path("action_submitted").booleanValue());
        ObjectNode claimedBackend = (ObjectNode) StrictJson.parse(original.originalResultToken().orElseThrow().bytes());
        claimedBackend.put("backend_id", "native-headless");
        var unproven = dispatch(fixture, command, attempt, new RawJson(StrictJson.canonical(claimedBackend)));
        var unprovenResult = StrictJson.parse(observer.observe(command, attempt, unproven).compatibleResult().orElseThrow().bytes());
        assertFalse(unprovenResult.has("raiktor_three_way_exit_postcondition_v2"));
        assertFalse(unprovenResult.path("raiktor_three_way_exit_postcondition_v3").path("action_submitted").booleanValue(),
                "live missing custody cannot borrow the retained v2 backend assertion");
        for (String backendKind : List.of("foreign", "null", "boolean", "array")) {
            switch (backendKind) {
                case "foreign" -> claimedBackend.put("backend_id", "foreign-backend");
                case "null" -> claimedBackend.putNull("backend_id");
                case "boolean" -> claimedBackend.put("backend_id", true);
                case "array" -> claimedBackend.putArray("backend_id");
                default -> throw new AssertionError(backendKind);
            }
            var foreign = withChronology(dispatch(fixture, command, attempt, new RawJson(StrictJson.canonical(claimedBackend))),
                    fixture.before(), 80, attempt.submittedAt().plusMillis(1), CUSTODY_EPOCH);
            fixture.archive().preserve(foreign);
            assertFalse(StrictJson.parse(observer.observe(command, attempt, foreign).compatibleResult().orElseThrow().bytes())
                    .path("raiktor_three_way_exit_postcondition_v3").path("action_submitted").booleanValue(),
                    "an explicit non-native backend cannot become native merely because custody is present: " + backendKind);
        }
    }

    private static byte[] legacyBytes(com.fasterxml.jackson.databind.JsonNode row,String field,ExactRef ref) {
        byte[] value=java.util.Base64.getDecoder().decode(StrictJson.text(row.get(field)));
        assertEquals(ref.bytes(),value.length);assertEquals(ref.sha256(),DriverJson.sha256(value));return value;
    }


    private static ObjectNode actualTerminalGate(Fixture fixture,String route) {
        var before=(ObjectNode)DriverJson.toNode(fixture.before().semantic());
        var frame=StrictJson.object().put("war_id",77).put("primary_attacker_character_id",73).put("primary_defender_character_id",74);
        for(String field:List.of("snapshot_id","date_raw"))frame.set(field,before.get(field));
        frame.set("snapshot_revision",before.get("revision"));frame.set("native_revision",before.get("native_revision"));frame.set("episode_id",before.get("episode_run_id"));
        frame.set("ck3_pid",before.path("diagnostics").get("bridge_pid"));frame.put("connection_id","connection-generation:"+before.path("diagnostics").get("connection_generation").asText());
        return org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.bindFrozenPlan(frame,DriverJson.toNode(frozenTerminalPlan(route)),
                route.equals("surrender")?"surrender-war-77":"offer-white-peace-77",route);
    }
    @Test void currentSubmissionVersionKeepsMissingAndMalformedInputsSeparateFromAProvenFullPostwarOutcome() throws InterruptedException {
        for(String route:List.of("white_peace","surrender")) {
            var fixture=fixture(terminalState(true),terminalState(false));
            var gate=actualTerminalGate(fixture,route);
            var post=(ObjectNode)DriverJson.toNode(fixture.held().observe(DEADLINE).semantic());
            String literal=route.equals("surrender")?"surrender-war-77":"offer-white-peace-77";
            var action=StrictJson.object().put("step",literal).put("accepted",true).put("status","submitted").put("backend_id","native-headless");
            var current=org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,action,post,null,null);
            assertTrue(current.path("action_submitted").booleanValue());assertEquals("evidence_required",current.path("status").textValue());
            assertEquals(2,current.path("postcondition_receipt").path("schema_version").intValue());
            for(String flag:List.of("postcondition_verified","checkpoint_cold_restore_verified","gen034_closed"))assertFalse(current.path(flag).booleanValue());
            assertFalse(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provide(gate,action,post,null,null).path("action_submitted").booleanValue());
            for(var missing:List.of(
                    org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(null,StrictJson.parse(new byte[]{'1'}),post,null,null),
                    org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,null,StrictJson.parse(new byte[]{'1'}),null,null),
                    org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,StrictJson.parse(new byte[]{'1'}),null,null,null))) {
                assertFalse(missing.path("action_submitted").booleanValue());
            }
            for(String raw:List.of("false","null","1","1.0","\"true\"")) {
                var wrong=action.deepCopy();wrong.set("accepted",StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertFalse(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,wrong,post,null,null).path("action_submitted").booleanValue());
            }
            for(String field:List.of("step","status","backend_id")) {
                var wrong=action.deepCopy();wrong.put(field,"wrong");
                assertFalse(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,wrong,post,null,null).path("action_submitted").booleanValue());
            }
            var term=action.putObject("war_termination_result").put("status","applied").put("war_id",77)
                    .put("outcome",route.equals("surrender")?"attacker_defeat":route).put("command_acknowledged",true);
            term.set("episode_run_id",gate.path("authorization").path("frame").get("episode_id"));
            term.set("starting_snapshot_id",gate.path("authorization").path("frame").get("snapshot_id"));term.set("observed_snapshot_id",post.get("snapshot_id"));
            assertTrue(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,action,post,null,null).path("action_submitted").booleanValue());
            for(String field:List.of("war_id","outcome","episode_run_id","starting_snapshot_id","observed_snapshot_id","command_acknowledged")) {
                var wrong=action.deepCopy();((ObjectNode)wrong.get("war_termination_result")).put(field,"wrong");
                assertFalse(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,wrong,post,null,null).path("action_submitted").booleanValue(),field);
            }
            term.put("status","submitted_pending").put("observed_snapshot_id","actual-pending-read").put("war_id_absent_after_ack",false);
            assertTrue(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,action,post,null,null).path("action_submitted").booleanValue());
            term.put("war_id_absent_after_ack",true);
            assertFalse(org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,action,post,null,null).path("action_submitted").booleanValue());
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,action,StrictJson.object(),null,null));
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.provideSubmissionFacts(gate,StrictJson.parse(new byte[]{'1'}),post,null,null));
        }
    }


    private static void rejectCrossProfilePackets(ActionReceipt original,FixtureArchive archive,String profile) {
        var basis=NativeEffectEvidence.load(original,archive,new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var compatible=(ObjectNode)StrictJson.parse(basis.compatibleResult().bytes());
        String field="raiktor_three_way_exit_postcondition_"+profile;
        String other="raiktor_three_way_exit_postcondition_"+(profile.equals("v1")?"v2":"v1");
        var verifier=NativeWarExitEffects.archivedVerifier(original.command().operation(),original.command().source().sourceRef(),new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        for(String kind:List.of("both","explicit_null","boolean","float","array","empty","third_version","inner_version","inner_contract","outer_schema","outer_provider","opposite_key","submitted_flag","action_step","backend")) {
            ObjectNode changed=compatible.deepCopy();
            ObjectNode formal=(ObjectNode)changed.get(field);
            switch(kind) {
                case "both" -> changed.set(other,formal.deepCopy());
                case "third_version" -> changed.set("raiktor_three_way_exit_postcondition_"+(profile.equals("v3")?"v2":"v3"),formal.deepCopy());
                case "explicit_null" -> changed.putNull(field);
                case "boolean" -> changed.put(field,true);
                case "float" -> changed.put(field,"__RAW_FLOAT_TOKEN__");
                case "array" -> changed.putArray(field);
                case "empty" -> changed.set(field,StrictJson.object());
                case "inner_version" -> ((ObjectNode)formal.get("postcondition_receipt")).put("schema_version",profile.equals("v1")?2:1);
                case "inner_contract" -> ((ObjectNode)formal.get("postcondition_receipt")).put("contract",profile.equals("v1")
                        ?org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.SUBMISSION_CONTRACT:org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.CONTRACT);
                case "outer_schema" -> formal.put("schema",profile.equals("v1")
                        ?org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.SUBMISSION_SCHEMA:org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.SCHEMA);
                case "outer_provider" -> formal.put("provider",profile.equals("v1")
                        ?org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.SUBMISSION_PROVIDER:org.xar.ck3.control.g2.m0.RaiktorExitPostcondition.PROVIDER);
                case "opposite_key" -> {changed.remove(field);changed.set(other,formal);}
                case "submitted_flag" -> {
                    boolean opposite=!formal.path("action_submitted").booleanValue();
                    formal.put("action_submitted",opposite);((ObjectNode)formal.get("postcondition_receipt")).put("action_submitted",opposite);
                }
                case "action_step" -> changed.put("step",original.command().operation().value()+"-other");
                case "backend" -> changed.put("backend_id","different-native-source");
                default -> throw new AssertionError(kind);
            }
            byte[] encoded=StrictJson.canonical(changed);
            if(kind.equals("float"))encoded=new String(encoded,java.nio.charset.StandardCharsets.UTF_8).replace("\"__RAW_FLOAT_TOKEN__\"","1.0").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            RawJson packet=new RawJson(encoded);
            var settled=(ActionState.Settled)original.state();var applied=(ActionState.Applied)settled.settlement();
            var ref=NativeEffectEvidence.preserve(original.command(),settled.attempt(),basis.frames(),List.of(),packet,archive);
            var forged=NativeEffectSnapshots.withEvidence(new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(applied.observation()),Optional.of(packet)),List.of(ref));
            ActionReceipt candidate=receipt(original.command(),settled.attempt(),settled.dispatch(),forged);
            candidate=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(candidate,archive),archive);
            ActionReceipt retained=candidate;
            var failure=assertThrows(IllegalArgumentException.class,()->verifier.verifier().verify(null,retained,archive),profile+":"+kind);
            assertTrue(failure.getMessage().contains((kind.equals("both")||kind.equals("third_version"))?"ambiguous archived formal":"original material history projection"),failure.getMessage());
            System.out.println("CROSS_PROFILE_REJECT "+profile+":"+kind+" "+failure.getMessage());
        }
        var settled=(ActionState.Settled)original.state();var attempt=settled.attempt();var effect=((ActionState.Applied)settled.settlement()).observation();
        var wrongAttempt=new ActionState.Attempt(attempt.requestId()+"-other",attempt.submittedAt(),attempt.guard(),attempt.preparedRequest());
        var requestFailure=assertThrows(IllegalArgumentException.class,()->{
            var wrongRequest=new ActionReceipt(original.version(),original.sequence(),original.command(),original.bodySha256(),new ActionState.Settled(wrongAttempt,settled.dispatch(),settled.settlement()));
            verifier.verifier().verify(null,wrongRequest,archive);
        });
        System.out.println("CROSS_PROFILE_REJECT "+profile+":request "+requestFailure.getMessage());
        var source=effect.source();
        var wrongSource=new org.xar.ck3.control.g2.common.G2Source(source.machineId(),source.observedAtUtc(),"other-source",source.sourceRef());
        var changedEffect=new ActionState.EffectObservation(effect.after(),wrongSource,effect.sessionId(),effect.observerSchema(),effect.actual(),effect.provenance(),
                effect.observedAt(),effect.originalEvidence(),effect.supportingEvidence());
        var wrongSourceReceipt=new ActionReceipt(original.version(),original.sequence(),original.command(),original.bodySha256(),
                new ActionState.Settled(attempt,settled.dispatch(),new ActionState.Applied(changedEffect)));
        var sourceFailure=assertThrows(IllegalArgumentException.class,()->verifier.verifier().verify(null,wrongSourceReceipt,archive));
        System.out.println("CROSS_PROFILE_REJECT "+profile+":source "+sourceFailure.getMessage());
        var afterFailure=assertThrows(IllegalArgumentException.class,()->{
            var changedAfter=new ActionState.EffectObservation(effect.after(),effect.source(),effect.sessionId(),effect.observerSchema(),effect.actual(),effect.provenance(),
                    effect.observedAt(),basis.frames().before().originalEvidence(),effect.supportingEvidence());
            var wrongAfterReceipt=new ActionReceipt(original.version(),original.sequence(),original.command(),original.bodySha256(),
                    new ActionState.Settled(attempt,settled.dispatch(),new ActionState.Applied(changedAfter)));
            verifier.verifier().verify(null,wrongAfterReceipt,archive);
        });
        System.out.println("CROSS_PROFILE_REJECT "+profile+":after "+afterFailure.getMessage());
    }

    private static final class FixtureArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,RawJson> materials=new HashMap<>();private final Map<ExactRef,byte[]> nativeFrames=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private static ExactRef ref(String kind,byte[] bytes) {return new ExactRef(java.nio.file.Path.of(System.getProperty("java.io.tmpdir"),"ordinary-effect-domain-fixture",kind,DriverJson.sha256(bytes)).toAbsolutePath().toString(),bytes.length,DriverJson.sha256(bytes));}
        private <T> ExactRef findStoredRef(Map<ExactRef,T> map, T original, byte[] actualBytes) {
            var matches = new java.util.ArrayList<ExactRef>();
            var expectedSha = DriverJson.sha256(actualBytes);
            for (var entry : map.entrySet()) {
                var key = entry.getKey();
                var value = entry.getValue();
                if (value.equals(original) && key.bytes() == actualBytes.length && key.sha256().equals(expectedSha)) {
                    matches.add(key);
                }
            }
            StrictJson.require(matches.size() == 1, "fixture archived original not uniquely found or integrity mismatch");
            return matches.get(0);
        }
        private static byte[] dispatchBytes(NativeActionPort.DispatchOutcome original) {
            if(original instanceof NativeActionPort.AckReceived ack && ack.custody().isPresent()) {
                var row=StrictJson.object().put("request_packet_sha256",DriverJson.sha256(ack.outbound().orElseThrow().originalPacket()))
                        .put("response_packet_sha256",DriverJson.sha256(ack.originalPacket()));
                row.set("custody",NativeRequestChronologyCodec.encode(ack.custody().orElseThrow()));return StrictJson.canonical(row);
            }
            return original instanceof NativeActionPort.AckReceived ack?ack.outbound().map(NativeActionPort.OutboundPacket::originalPacket).orElse(ack.originalPacket())
                    :((NativeActionPort.Unknown)original).originalRequestPacket();
        }
        private byte[] readBytes(PlanningReadReceipt read) {
            return StrictJson.canonical(StrictJson.object().put("request_id",read.requestId()).put("contract_id",read.contractId())
                    .put("original_dispatch_sha256",referenceOf(read.original()).sha256())
                    .put("before",read.before().originalBindingSha256()).put("after",read.after().originalBindingSha256()));
        }
        @Override public ExactRef preserveMaterial(RawJson original) {var ref=ref("material",original.bytes());materials.putIfAbsent(ref,original);return ref;}
        @Override public RawJson loadMaterial(ExactRef original) {return java.util.Objects.requireNonNull(materials.get(original));}
        @Override public RawJson loadFullMaterial(ExactRef original) {
            var value=loadMaterial(original);
            StrictJson.require(original.bytes()>0 && original.bytes()<=DriverJson.MAX_NATIVE_BYTES
                    && value.bytes().length==original.bytes() && DriverJson.sha256(value.bytes()).equals(original.sha256()),
                    "original complete Driver material changed");
            return value;
        }
        @Override public ExactRef materialReferenceOf(RawJson original) {return findStoredRef(materials, original, original.bytes());}
        private ExactRef retainPacket(byte[] original) {var ref=ref("packet",original);nativeFrames.putIfAbsent(ref,original.clone());return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) {var ref=ref("native",original.originalPacket());nativeFrames.putIfAbsent(ref,original.originalPacket());return ref;}
        @Override public byte[] loadNativeFrame(ExactRef original) {return java.util.Objects.requireNonNull(nativeFrames.get(original)).clone();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) {byte[] bytes=dispatchBytes(original);var ref=ref("dispatch",bytes);outcomes.putIfAbsent(ref,original);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) {return java.util.Objects.requireNonNull(outcomes.get(original));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) {return findStoredRef(outcomes, original, dispatchBytes(original));}
        private static byte[] requestBytes(NativeRequest original) {
            return StrictJson.canonical(StrictJson.object().put("step",original.step()).put("capability",original.requiredCapability().orElse(""))
                    .put("fields_sha256",DriverJson.sha256(original.additionalFields().bytes())));
        }
        @Override public ExactRef preserveRequest(NativeRequest original) {var ref=ref("request",requestBytes(original));requests.putIfAbsent(ref,original);return ref;}
        @Override public NativeRequest loadRequest(ExactRef original) {return java.util.Objects.requireNonNull(requests.get(original));}
        @Override public ExactRef requestReferenceOf(NativeRequest original) {return findStoredRef(requests, original, requestBytes(original));}
        @Override public ExactRef preserveRead(PlanningReadReceipt original) {var ref=ref("read",readBytes(original));reads.putIfAbsent(ref,original);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef original) {return java.util.Objects.requireNonNull(reads.get(original));}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) {return findStoredRef(reads, original, readBytes(original));}
        @Override public ExactRef preserveRecord(ActionRecord original) {throw new UnsupportedOperationException();}
        @Override public ActionRecord loadRecord(ExactRef original) {throw new UnsupportedOperationException();}
        @Override public ExactRef recordReferenceOf(ActionRecord original) {throw new UnsupportedOperationException();}
        @Override public ExactRef preserveReceipt(ActionReceipt original) {throw new UnsupportedOperationException();}
        @Override public ActionReceipt loadReceipt(ExactRef original) {throw new UnsupportedOperationException();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) {throw new UnsupportedOperationException();}
    }
}
