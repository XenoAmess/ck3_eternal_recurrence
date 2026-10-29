package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.continuity.writer.DriverReadHistoryTestSupport.Fixture;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReadCodec;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.WarSide;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions.Truth;
import org.xar.ck3.control.nativebridge.capabilities.army.BattleResponses;

/** Real archived receipt/packet/row chain with an explicitly installed pure fixture decoder. Does not grant Game authority. */
class DriverReadHistoryRowProducerTest {
    @TempDir Path temporary;
    private static final String STEP=DriverReadHistoryTestSupport.STEP;
    @Test void originalReceiptPureReplayCreatesCompatibleFullRowWithoutWorldAdvanceOrCanonicalPublication() throws Exception {
        var f=fixture(true);String head=f.archive().writer().locked(session->session.head().digest());
        var candidate=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),3);
        assertEquals(3,candidate.historyEntry().index());assertEquals(STEP,candidate.row().command());assertTrue(candidate.row().ok());
        assertEquals(f.known().value().normalizedResult(),candidate.row().result());assertEquals(f.known().originalReceipt(),candidate.readReference());
        assertEquals(DriverReadHistoryRowProducer.Kind.ROUTE_PREVIEW,candidate.provenance().kind());assertTrue(candidate.provenance().querySequence().isEmpty());
        assertFalse(DriverSurvivingHistory.isLifeAdvanceStep(candidate.row().command()));DriverSurvivingHistory.row(candidate.row().toJson());
        assertEquals(head,f.archive().writer().locked(session->session.head().digest()));assertEquals(0,f.decodes().get());assertEquals(1,f.replays().get());
        assertEquals(candidate.row(),DriverReadHistoryRowProducer.decode(f.archive().loadMaterial(candidate.rowReference()).bytes()));
    }
    @Test void actualReplayReturnsSamePrivateCandidateAndDoesNotCallMutableDecode() throws Exception {
        var f=fixture(true);var original=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1);
        assertSame(original,DriverReadHistoryRowProducer.replay(f.archive(),f.catalog(),f.contract(),f.known(),original));
        assertEquals(0,f.decodes().get());assertEquals(2,f.replays().get());
        assertArrayEquals(original.row().encode(),f.archive().loadMaterial(original.rowReference()).bytes());
    }
    @Test void absentExplicitPureDecoderIsUnavailableRatherThanAliasingMutableDecode() throws Exception {
        var f=fixture(false);assertThrows(IllegalStateException.class,()->DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1));
        assertEquals(0,f.decodes().get());assertEquals(0,f.replays().get());
    }
    @Test void changedTypedKnownResultAndMissingQueriedSourceNeverBecomeHistory() throws Exception {
        var f=fixture(true);Obj actual=f.known().value().normalizedResult();
        for(Obj altered:List.of(actual.with("queried_revision",new IntegerValue(BigInteger.valueOf(4))),actual.with("queried_episode_run_id",new Text("foreign-episode")),
                actual.with("route_preview",json("{\"army_id\":1}")))) {
            var forged=new PlanningReadResult.Known<>(new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW,altered),f.known().receipt(),f.known().originalReceipt());
            assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),forged,1));
        }
    }
    @Test void aDifferentCatalogContractObjectAndChangedDecoderSourceCannotReplayOriginalRow() throws Exception {
        var f=fixture(true);var original=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1);
        var other=fixture(true);assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),other.contract(),f.known(),1));
        ExactRef otherSource=f.archive().preserveMaterial(new RawJson("{\"different_decoder\":true}".getBytes(StandardCharsets.UTF_8)));
        var alteredCatalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(f.contract(),otherSource)),List.of());
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.replay(f.archive(),alteredCatalog,f.contract(),f.known(),original));
    }
    @Test void serializerRejectsBooleanIndexAndChangedSourceFieldBindingAndKeepsUint64IdentityExact() throws Exception {
        var f=fixture(true);var original=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1);
        String wire=new String(original.row().encode(),StandardCharsets.UTF_8);
        for(String altered:List.of(wire.replace("\"index\":1","\"index\":true"),wire.replace("\"payload_field\":\"route_preview\"","\"payload_field\":\"campaign_root_context\""),
                wire.replace("\"queried_native_revision\":2","\"queried_native_revision\":2.0"),wire.replace("\"connection_generation\":4","\"connection_generation\":true")))
            assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(altered.getBytes(StandardCharsets.UTF_8)));
        assertTrue(wire.contains("134373229053165471"));
        assertEquals(f.known().receipt().request().before(),DriverReadHistoryRowProducer.decode(original.row().encode()).provenance().sourceFrame());
        var reversed=new java.util.TreeMap<String,Value>(java.util.Comparator.reverseOrder());reversed.putAll(original.row().result().members());
        var reordered=new DriverReadHistoryRowProducer.RawHistoryRow(1,STEP,true,new Obj(reversed),original.provenance());
        assertArrayEquals(original.row().encode(),reordered.encode());
    }
    @Test void sameBytesReplacedArchivedReceiptAndMissingOriginalRowAreRejected() throws Exception {
        var f=fixture(true);var original=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1);
        byte[] receipt=Files.readAllBytes(Path.of(f.known().originalReceipt().path()));Path changed=temporary.resolve("same-bytes-receipt.json");Files.write(changed,receipt);
        Files.move(changed,Path.of(f.known().originalReceipt().path()),StandardCopyOption.REPLACE_EXISTING);
        assertThrows(UncheckedIOException.class,()->DriverReadHistoryRowProducer.replay(f.archive(),f.catalog(),f.contract(),f.known(),original));
        var second=fixture(true);var retained=DriverReadHistoryRowProducer.prepare(second.archive(),second.catalog(),second.contract(),second.known(),1);
        Files.delete(Path.of(retained.rowReference().path()));
        assertThrows(UncheckedIOException.class,()->DriverReadHistoryRowProducer.replay(second.archive(),second.catalog(),second.contract(),second.known(),retained));
    }
    @Test void m5PublicReadPreservesCompleteCoreMirrorsExtensionsAndExactUint64WhileInternalRetreatIsExcluded() throws Exception {
        var f=fixture(true);var publicRead=battle(f,"PUBLIC_QUERY");assertTrue(DriverReadHistoryRowProducer.shouldRecord(publicRead));
        var original=DriverReadHistoryRowProducer.prepare(f.archive(),battleCatalog,battleContract,publicRead,1);
        assertEquals(DriverReadHistoryRowProducer.Kind.BATTLE_CONTROL,original.provenance().kind());
        assertEquals(new BigInteger("18446744073709551615"),original.provenance().querySequence().orElseThrow());
        assertEquals(new IntegerValue(BigInteger.ZERO),original.row().result().get("selected_public_cunit_id"));
        assertEquals(publicRead.value().extensions().get("active_combat_resume_inputs_v1"),original.row().result().get("active_combat_resume_inputs_v1"));
        assertEquals(original.row(),DriverReadHistoryRowProducer.decode(original.row().encode()));
        var internal=battle(f,"INTERNAL_RETREAT");assertFalse(DriverReadHistoryRowProducer.shouldRecord(internal));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.prepare(f.archive(),battleCatalog,battleContract,internal,2));
        var request=internal.receipt().request();var missingRequest=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),json("{}"),request.deadline());
        var r=internal.receipt();var missingReceipt=new PlanningReadReceipt(missingRequest,r.contractId(),r.requestId(),r.before(),r.after(),r.original());
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.shouldRecord(new PlanningReadResult.Known<>(internal.value(),missingReceipt,internal.originalReceipt())));
    }
    private ReadContract<ArmyBattleReadValue> battleContract;
    private RootReadContractCatalog battleCatalog;
    private record BattleValue(ArmyBattleReadValue.Kind kind,Obj normalized,BigInteger sequence,Obj extensions) implements ArmyBattleReadValue { }
    private PlanningReadResult.Known<ArmyBattleReadValue> battle(Fixture f,String capture) {
        var old=f.known().receipt();var source=f.contract().sourceRef();String step="query-battle-control-snapshot-v1-0",cap="game.command.query-battle-control-snapshot-v1-N",id="battle-"+capture;
        var op=new OperationKey(step);var q=old.request();var request=new PlanningReadRequest(q.before(),q.source(),q.sessionId(),op,json("{\"capture_context\":\""+capture+"\",\"public_arguments\":{}}"),q.deadline());
        var b=old.before().binding();var binding=new GuardEvidence(q.before(),q.source(),q.sessionId(),b.connectionGeneration(),op,b.nativeEvidence(),b.capabilityEvidence(),b.authorityId(),b.observedAt(),b.validUntil(),b.supportingEvidence());
        var guard=new PlanningReadGuard(binding,true,true,true,old.before().originalBindingSha256());
        String payload="{\"status\":\"available\",\"selected_public_cunit_id\":0,\"selected_native_carmy_id\":4294967295,\"selected_owner_character_id\":1,\"combat_province_id\":1,\"side_index\":0,\"side_scope\":\"whole_side\",\"affected_public_cunit_ids_in_stored_order\":[0],\"unaffected_same_side_public_cunit_ids_in_stored_order\":[],\"side_flags\":{},\"legality\":{\"legal_now\":false}}";
        String result="{\"step\":\""+step+"\",\"accepted\":true,\"status\":\"available\",\"query_sequence\":18446744073709551615,\"snapshot_revision\":2,\"battle_control_snapshot\":"+payload+",\"active_combat_resume_inputs_v1\":{\"actual_field\":null}}";
        byte[] bytes=("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":true,\"result\":"+result+"}").getBytes(StandardCharsets.UTF_8);
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(result.getBytes(StandardCharsets.UTF_8))),new RawJson(bytes),ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array());
        var receipt=new PlanningReadReceipt(request,id,id,guard,guard,ack);
        java.util.function.Function<PlanningReadReceipt,ArmyBattleReadValue> replay=r->{Obj actual=DriverJson.object(r.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
            return new BattleValue(ArmyBattleReadValue.Kind.CONTROL,OpportunityJson.object(actual.get("battle_control_snapshot"),"actual control"),OpportunityJson.integer(actual.get("query_sequence"),"actual sequence"),
                    new Obj(java.util.Map.of("active_combat_resume_inputs_v1",actual.get("active_combat_resume_inputs_v1"))));};
        battleContract=new ReadContract<>(id,op,Optional.of(cap),cap,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                (r,rid)->new NativeRequest(step,Optional.of(cap),new RawJson("{}".getBytes(StandardCharsets.UTF_8))),replay,replay);
        battleCatalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(battleContract,source)),List.of());
        return new PlanningReadResult.Known<>(replay.apply(receipt),receipt,f.archive().preserveRead(receipt));
    }
    @Test void canonicalReplayReusesExactOriginalReceiptWithoutPreserveOrMutableDecoder() throws Exception {
        var f=fixture(true);var original=DriverReadHistoryRowProducer.prepare(f.archive(),f.catalog(),f.contract(),f.known(),1);
        long files;try(var stream=Files.walk(temporary)){files=stream.filter(Files::isRegularFile).count();}
        String head=f.archive().writer().locked(s->s.head().digest());
        var replayed=DriverReadHistoryRowProducer.replayCanonical(f.archive(),f.catalog(),f.contract(),original.row());
        assertEquals(f.known(),replayed);assertEquals(f.known().originalReceipt(),replayed.originalReceipt());assertEquals(0,f.decodes().get());
        try(var stream=Files.walk(temporary)){assertEquals(files,stream.filter(Files::isRegularFile).count());}
        assertEquals(head,f.archive().writer().locked(s->s.head().digest()));
        var altered=new DriverReadHistoryRowProducer.RawHistoryRow(1,STEP,true,original.row().result().with("synthetic_extra",new Bool(true)),original.provenance());
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.replayCanonical(f.archive(),f.catalog(),f.contract(),altered));
        var different=fixture(true);
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.replayCanonical(f.archive(),f.catalog(),different.contract(),original.row()));
    }
    @Test void reinforcementPublicHistoryPreservesUnavailableNullsAndCompleteOriginalMirrorsWhileInternalObservationIsExcluded() throws Exception {
        var f=fixture(true);var selected=reinforcement(f,"PUBLIC_QUERY");
        assertTrue(DriverReadHistoryRowProducer.shouldRecord(selected.known()));
        var candidate=DriverReadHistoryRowProducer.prepare(f.archive(),selected.catalog(),selected.contract(),selected.known(),1);
        assertEquals(DriverReadHistoryRowProducer.Kind.REINFORCEMENT,candidate.provenance().kind());
        assertEquals(new BigInteger("18446744073709551615"),candidate.provenance().querySequence().orElseThrow());
        assertEquals(selected.known().value().originalFrame(),candidate.row().result().get("battle_reinforcement_assignment"));
        assertSame(Nil.INSTANCE,candidate.row().result().get("contact_projection"));
        assertEquals(new IntegerValue(BigInteger.ZERO),candidate.row().result().get("selected_public_cunit_id"));
        assertEquals(new Text("unsupported_build"),candidate.row().result().get("unavailable_reason"));
        assertEquals(candidate.row(),DriverReadHistoryRowProducer.decode(candidate.row().encode()));
        assertEquals(selected.known(),DriverReadHistoryRowProducer.replayCanonical(f.archive(),selected.catalog(),selected.contract(),candidate.row()));
        var internal=reinforcement(f,"INTERNAL_OBSERVATION");
        assertFalse(DriverReadHistoryRowProducer.shouldRecord(internal.known()));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.prepare(f.archive(),internal.catalog(),internal.contract(),internal.known(),2));
        var wrong=reinforcement(f,"INTERNAL_RETREAT");
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.shouldRecord(wrong.known()));
    }
    private record ReinforcementFixture(ReadContract<BattleResponses.Reinforcement> contract,RootReadContractCatalog catalog,
            PlanningReadResult.Known<BattleResponses.Reinforcement> known) { }
    private ReinforcementFixture reinforcement(Fixture f,String capture) {
        var old=f.known().receipt();var source=f.contract().sourceRef();String step="query-battle-reinforcement-assignment-v1-0";
        String cap="game.command.query-battle-reinforcement-assignment-v1-N",id="reinforcement-"+capture;var q=old.request();var op=new OperationKey(step);
        var request=new PlanningReadRequest(q.before(),q.source(),q.sessionId(),op,json("{\"capture_context\":\""+capture+"\",\"public_arguments\":{}}"),q.deadline());
        var b=old.before().binding();var binding=new GuardEvidence(q.before(),q.source(),q.sessionId(),b.connectionGeneration(),op,b.nativeEvidence(),b.capabilityEvidence(),b.authorityId(),b.observedAt(),b.validUntil(),b.supportingEvidence());
        var guard=new PlanningReadGuard(binding,true,true,true,old.before().originalBindingSha256());
        Obj payload=json("{\"schema_version\":1,\"contract_stage\":\"production_exact_ai_reinforcement_assignment\",\"status\":\"unavailable\",\"unavailable_reason\":\"unsupported_build\",\"battle_reinforcement_assignment_ready\":false,\"snapshot_revision\":2,\"observed_date_raw\":1000,\"selected_public_cunit_id\":0,\"selected_native_carmy_id\":null,\"coordinator_id\":null,\"unit_stack_stored_index\":null,\"subunit_stored_index\":null,\"signal\":null,\"assignment\":null,\"route\":null,\"native_order\":null,\"contact_projection\":null}");
        Obj raw=new Obj(java.util.Map.of("step",new Text(step),"accepted",new Bool(true),"status",new Text("unavailable"),
                "query_sequence",new IntegerValue(new BigInteger("18446744073709551615")),"snapshot_revision",new IntegerValue(BigInteger.TWO),"battle_reinforcement_assignment",payload));
        String result=new String(OpportunityJson.encode(raw),StandardCharsets.UTF_8);
        byte[] bytes=("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":true,\"result\":"+result+"}").getBytes(StandardCharsets.UTF_8);
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(OpportunityJson.encode(raw))),new RawJson(bytes),ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array());
        var receipt=new PlanningReadReceipt(request,id,id,guard,guard,ack);
        java.util.function.Function<PlanningReadReceipt,BattleResponses.Reinforcement> replay=r->{
            Obj actual=DriverJson.object(r.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
            var sourceFrame=r.request().before().frame().identity();
            return new BattleResponses.Reinforcement(new ArmyTypes.Frame(new ArmyTypes.UInt64(sourceFrame.nativeRevision()),sourceFrame.dateRaw().longValueExact(),
                    new ArmyTypes.Present<>(new ArmyTypes.UInt64(OpportunityJson.integer(actual.get("query_sequence"),"fixture original sequence")))),
                    new ArmyTypes.PublicUnitId(0),ArmyTypes.Availability.UNAVAILABLE,false,new ArmyTypes.Present<>("unsupported_build"),
                    new ArmyTypes.NullValue<>(),OpportunityJson.object(actual.get("battle_reinforcement_assignment"),"fixture actual reinforcement"));
        };
        var contract=new ReadContract<>(id,op,Optional.of(cap),cap,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(r,rid)->new NativeRequest(step,Optional.of(cap),new RawJson(new byte[]{'{','}'})),replay,replay);
        var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(contract,source)),List.of());
        return new ReinforcementFixture(contract,catalog,new PlanningReadResult.Known<>(replay.apply(receipt),receipt,f.archive().preserveRead(receipt)));
    }
    @Test void armyWarPublicRowsUseSoleTypedResultsAndPreserveDeclarationsWithoutInventedQueriedMirrors() throws Exception {
        var f=fixture(true);
        for(String family:List.of("DECLARATIONS","OPTIONS","TERMS")) {
            var selected=armyWar(f,family);assertTrue(DriverReadHistoryRowProducer.shouldRecord(selected.known()));
            var candidate=DriverReadHistoryRowProducer.prepare(f.archive(),selected.catalog(),selected.contract(),selected.known(),1);
            assertEquals(selected.known().value().normalizedResult(),candidate.row().result());
            assertEquals(new BigInteger("18446744073709551615"),candidate.provenance().querySequence().orElseThrow());
            assertEquals(candidate.row(),DriverReadHistoryRowProducer.decode(candidate.row().encode()));
            assertEquals(selected.known(),DriverReadHistoryRowProducer.replayCanonical(f.archive(),selected.catalog(),selected.contract(),candidate.row()));
            if(family.equals("DECLARATIONS")) {
                assertEquals(DriverReadHistoryRowProducer.Kind.DECLARABLE_WARS,candidate.provenance().kind());
                assertInstanceOf(Arr.class,candidate.row().result().get("declarable_wars"));assertFalse(candidate.row().result().members().containsKey("queried_snapshot_id"));
                assertEquals(f.known().receipt().request().before(),candidate.provenance().sourceFrame());
            } else {
                assertEquals(new Text("actual-source-frame"),candidate.row().result().get("queried_snapshot_id"));
                assertEquals(new IntegerValue(BigInteger.valueOf(4)),candidate.row().result().get("queried_connection_generation"));
            }
        }
    }
    @Test void armyWarHistoryRejectsWrongPayloadDomainAndMissingOriginalTermsEpisode() throws Exception {
        var f=fixture(true);var declarations=armyWar(f,"DECLARATIONS");
        var row=DriverReadHistoryRowProducer.prepare(f.archive(),declarations.catalog(),declarations.contract(),declarations.known(),1).row();
        Obj altered=row.toJson().with("result",row.result().with("declarable_wars",json("{}")));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(OpportunityJson.encode(altered)));
        var terms=armyWar(f,"TERMS");var termRow=DriverReadHistoryRowProducer.prepare(f.archive(),terms.catalog(),terms.contract(),terms.known(),2).row();
        Obj changed=termRow.toJson().with("result",termRow.result().with("episode_run_id",new Text("foreign-episode")));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(OpportunityJson.encode(changed)));
    }
    private record WarFixture(ReadContract<ArmyWarReadCodec.Observation> contract,RootReadContractCatalog catalog,
            PlanningReadResult.Known<ArmyWarReadCodec.Observation> known) { }
    private WarFixture armyWar(Fixture f,String family) {
        String step=switch(family){case "DECLARATIONS"->"query-declarable-wars";case "OPTIONS"->"query-war-termination-options-1";case "TERMS"->"query-war-termination-terms-v1-1";default->throw new IllegalArgumentException();};
        String cap=switch(family){case "DECLARATIONS"->"game.command.query-declarable-wars";case "OPTIONS"->"game.command.query-war-termination-options-N";case "TERMS"->"game.command.query-war-termination-terms-v1-N";default->throw new IllegalArgumentException();};
        String payload=switch(family){case "DECLARATIONS"->"declarable_wars";case "OPTIONS"->"war_termination_options";case "TERMS"->"war_termination_terms";default->throw new IllegalArgumentException();};
        var old=f.known().receipt();var q=old.request();var source=f.contract().sourceRef();var op=new OperationKey(step);String id="fixture-war-"+family;
        var request=new PlanningReadRequest(q.before(),q.source(),q.sessionId(),op,json("{}"),q.deadline());
        var b=old.before().binding();var binding=new GuardEvidence(q.before(),q.source(),q.sessionId(),b.connectionGeneration(),op,b.nativeEvidence(),b.capabilityEvidence(),b.authorityId(),b.observedAt(),b.validUntil(),b.supportingEvidence());
        var guard=new PlanningReadGuard(binding,true,true,true,old.before().originalBindingSha256());
        Obj raw=new Obj(java.util.Map.of("step",new Text(step),"accepted",new Bool(true),"status",new Text("available"),
                "query_sequence",new IntegerValue(new BigInteger("18446744073709551615")),payload,family.equals("DECLARATIONS")?new Arr(List.of()):json("{\"war_id\":1,\"status\":\"available\"}")));
        String result=new String(OpportunityJson.encode(raw),StandardCharsets.UTF_8);
        byte[] bytes=("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"ok\":true,\"result\":"+result+"}").getBytes(StandardCharsets.UTF_8);
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(OpportunityJson.encode(raw))),new RawJson(bytes),ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array());
        var receipt=new PlanningReadReceipt(request,id,id,guard,guard,ack);
        java.util.function.Function<PlanningReadReceipt,ArmyWarReadCodec.Observation> replay=r->{
            Obj actual=DriverJson.object(r.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
            if(family.equals("DECLARATIONS"))return new ArmyWarReadCodec.Declarations(List.of(),new ArmyTypes.UInt64(OpportunityJson.integer(actual.get("query_sequence"),"fixture original sequence")),actual);
            var frame=r.request().before().frame();
            Obj normalized=actual.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                    .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision())).with("queried_connection_generation",new IntegerValue(r.before().binding().connectionGeneration()))
                    .with(family.equals("OPTIONS")?"queried_episode_run_id":"episode_run_id",new Text(frame.episodeRunId()));
            Obj inner=OpportunityJson.object(actual.get(payload),"actual fixture war payload");
            if(family.equals("TERMS"))return new ArmyWarReadCodec.Terms(inner,normalized);
            var packet=new NativeTerminationOptions.NativePacket(1,WarSide.ATTACKER,true,0,Truth.FALSE,Optional.empty(),StrictJson.object(OpportunityJson.toNode(inner),inner.members().keySet()));
            return new ArmyWarReadCodec.Options(packet,normalized);
        };
        var contract=new ReadContract<>(id,op,Optional.of(cap),cap,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(r,rid)->new NativeRequest(step,Optional.of(cap),new RawJson(new byte[]{'{','}'})),replay,replay);
        var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(contract,source)),List.of());
        return new WarFixture(contract,catalog,new PlanningReadResult.Known<>(replay.apply(receipt),receipt,f.archive().preserveRead(receipt)));
    }
    private Fixture fixture(boolean pure) throws Exception { return DriverReadHistoryTestSupport.create(temporary,pure); }
    private static Obj json(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
}
