package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Framed Native + original Driver producer, shared export, public serializer and restoring consumer. */
final class PublicSnapshotCodecTest {
    private static final BigInteger MAX64=new BigInteger("18446744073709551615");
    private static DriverObservationAssembler.Complete actual(String extension) {
        var full=full(extension,"original");return assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(full.actual(),full.facts(),full.originalEvidence()));
    }
    private static DriverObservationAssembler.FullSnapshot full(String extension,String playerToken) {
        String state=DriverObservationAssemblerTest.STATE.replace("\"original\":\"retained\"",
                "\"original\":\"retained\",\"connection_generation\":"+MAX64+",\"hello\":{\"connection_generation\":"+MAX64+"},\"last_heartbeat\":{\"sequence\":"+MAX64+",\"monotonic_ms\":"+MAX64+",\"command_entry_trace_v1\":{\"timeline\":{\"monotonic_ms\":"+MAX64+",\"submit_result\":-1}}}")
                .replace("\"active_wars\":[]","\"active_wars\":[],\"open_extension\":"+extension);
        if("missing".equals(playerToken))state=state.replace("\"played_character\":{\"character_id\":73,\"alive\":true},","");
        else if(!"original".equals(playerToken))state=state.replace("{\"character_id\":73,\"alive\":true}",playerToken);
        byte[] stateBytes=DriverStateAssemblerTest.bytes(state);
        byte[] envelope=DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"full64-source\",\"revision\":"+MAX64+",\"state\":"+state+"}");
        byte[] packet=ByteBuffer.allocate(envelope.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
        var session=new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),MAX64,"held-session");
        var frame=new NativeObservationPort.ObservedFrame(session,"full64-source",MAX64,new RawJson(stateBytes),packet,java.time.Instant.parse("2026-10-23T16:00:00Z"));
        var facts=new DriverObservationFacts(DriverStateAssemblerTest.known().driver(),3,7,session,frame.snapshotId(),MAX64,DriverJson.sha256(stateBytes),MAX64,2,
                DriverStateAssemblerTest.source(),new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("original facts")));
        return new DriverObservationAssembler().projectFull(frame,facts,DriverStateAssemblerTest.ref(packet));
    }
    @Test void actualProducerToPublicParserPreservesFull64AndEveryOpenSafeField() {
        var complete=actual("{\"revision\":73,\"float\":1.25,\"missing_stays_missing\":[],\"explicit_null\":null,\"numeric_text\":\"9007199254740993\"}");
        var exported=PublicSnapshotCodec.export(complete,true);RawJson encoded=PublicSnapshotCodec.encode(exported);
        var publicTree=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(MAX64.toString(),OpportunityJson.text(publicTree.get("revision"),"revision"));
        assertEquals(MAX64.toString(),OpportunityJson.text(publicTree.get("native_revision"),"native_revision"));
        var diagnostics=OpportunityJson.object(publicTree.get("diagnostics"),"diagnostics");
        assertEquals(MAX64.toString(),OpportunityJson.text(OpportunityJson.object(diagnostics.get("last_heartbeat"),"heartbeat").get("sequence"),"sequence"));
        assertInstanceOf(OpportunityJson.IntegerValue.class,OpportunityJson.object(publicTree.get("open_extension"),"extension").get("revision"));
        assertEquals(complete.semantic(),PublicSnapshotCodec.decode(encoded));
        assertEquals(2,exported.includedCount());assertArrayEquals(complete.originalEvidence().sha256().getBytes(),exported.actual().originalEvidence().sha256().getBytes());
    }
    @Test void sharedOmittedHistoryProducerLeavesActualFullEvidenceUnchanged() {
        var complete=actual("null");var omitted=PublicSnapshotCodec.export(complete,false);
        assertEquals(2,omitted.totalCount());assertEquals(0,omitted.includedCount());
        assertTrue(OpportunityJson.array(omitted.semantic().get("native_command_history"),"export history").isEmpty());
        assertEquals(2,OpportunityJson.array(complete.semantic().get("native_command_history"),"original history").size());
        assertEquals(omitted.semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(omitted)));
    }
    @Test void publicParserRejectsMissingWrongTypedAndRoundedIdentityRoles() {
        String valid=new String(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(actual("null"),false)).bytes(),java.nio.charset.StandardCharsets.UTF_8);
        for(String invalid:List.of(valid.replace("\"revision\":\""+MAX64+"\",",""),
                valid.replace("\"revision\":\""+MAX64+"\"","\"revision\":true"),
                valid.replace("\"revision\":\""+MAX64+"\"","\"revision\":18446744073709551615"),
                valid.replace("\"revision\":\""+MAX64+"\"","\"revision\":18446744073709552000.0"),
                valid.replace("\"revision\":\""+MAX64+"\"","\"revision\":\"018446744073709551615\""),
                valid.replace("\"paused\":true","\"paused\":1"),valid.replace("\"active_event\":null,","")))
            assertThrows(IllegalArgumentException.class,() -> PublicSnapshotCodec.decode(new RawJson(DriverStateAssemblerTest.bytes(invalid))));
    }
    @Test void unknownUnsafeNativeExtensionIsExplicitGapRatherThanIntegerGuessing() {
        var complete=actual("{\"revision\":9007199254740993}");
        var failure=assertThrows(IllegalArgumentException.class,() -> PublicSnapshotCodec.encode(PublicSnapshotCodec.export(complete,false)));
        assertTrue(failure.getMessage().contains("/open_extension/revision"));
        assertEquals(new BigInteger("9007199254740993"),OpportunityJson.integer(OpportunityJson.object(complete.semantic().get("open_extension"),"extension").get("revision"),"revision"));
    }
    @Test void actualTerminalFullProducerPreservesMissingNullDeadAndChangedPlayerWithoutOrdinaryIdentity() {
        for(String player:List.of("missing","null","{\"character_id\":73,\"alive\":false}","{\"character_id\":74,\"alive\":true}")) {
            var full=full("{\"opaque\":null}",player);var originalDriver=DriverStateAssemblerTest.ref(full.facts().driver().encode());
            var projected=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.project(full,
                    DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual original hello")),originalDriver,
                    DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual source qualification"))));
            var encoded=PublicSnapshotCodec.encodeTerminal(full,projected.identity(),true);var restored=PublicSnapshotCodec.decode(encoded);
            assertEquals(full.semantic(),restored);assertEquals(2,full.facts().observationVersion());
            assertEquals(player.equals("missing"),!restored.members().containsKey("played_character"));
            if(player.equals("null"))assertSame(OpportunityJson.Nil.INSTANCE,restored.get("played_character"));
            assertEquals(MAX64.toString(),OpportunityJson.text(DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES).get("revision"),"revision"));
            var omitted=PublicSnapshotCodec.decode(PublicSnapshotCodec.encodeTerminal(full,projected.identity(),false));
            assertEquals(2,OpportunityJson.array(full.semantic().get("native_command_history"),"original history").size());
            assertTrue(OpportunityJson.array(omitted.get("native_command_history"),"omitted history").isEmpty());
            var before=projected.identity();var wrong=new LifecycleIdentity(before.machineId(),before.game(),"another-session",before.connectionGeneration(),before.subject(),before.frame(),before.currentPlayer(),before.terminalReason(),before.evidence(),before.observedAt());
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeTerminal(full,wrong,false));
        }
    }
    private static DriverObservationAssembler.Complete withReadHistory(boolean unsafeArguments) {
        var base=full("null","original");var facts=base.facts();var frame=base.actual();
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(frame.session().machineId(),frame.session().game(),
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(
                        facts.driver().session().actorId(),frame.nativeRevision(),OpportunityJson.integer(base.semantic().get("date_raw"),"date_raw")),frame.snapshotId(),facts.publicRevision(),facts.driver().session().episodeRunId()),facts.observationVersion());
        String step="query-route-contact-horizon-v1-1";var result=new OpportunityJson.Obj(Map.ofEntries(
                Map.entry("step",new OpportunityJson.Text(step)),Map.entry("accepted",new OpportunityJson.Bool(true)),Map.entry("status",new OpportunityJson.Text("available")),
                Map.entry("route_contact_horizon",new OpportunityJson.Obj(Map.of("original",new OpportunityJson.Text("retained")))),
                Map.entry("queried_snapshot_id",new OpportunityJson.Text(frame.snapshotId())),Map.entry("queried_revision",new OpportunityJson.IntegerValue(facts.publicRevision())),
                Map.entry("queried_native_revision",new OpportunityJson.IntegerValue(frame.nativeRevision())),Map.entry("query_sequence",new OpportunityJson.IntegerValue(MAX64)),
                Map.entry("queried_connection_generation",new OpportunityJson.IntegerValue(MAX64)),Map.entry("queried_episode_run_id",new OpportunityJson.Text(identity.frame().episodeRunId()))));
        var arguments=new OpportunityJson.Obj(unsafeArguments?Map.of("unqualified_revision",new OpportunityJson.IntegerValue(MAX64)):Map.of());
        var source=new org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.ReadProvenance(
                org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.Kind.CONTACT_HORIZON,"actual-installed-contract","actual-read-request",
                DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual receipt")),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual definition")),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("actual decoder")),
                identity,facts.source(),frame.session().sessionId(),MAX64,java.util.Optional.of(MAX64),arguments,List.of());
        var row=new org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.RawHistoryRow(1,step,true,result,source);
        assertEquals(row,org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(row.encode()));
        var old=facts.driver();var driver=new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete(old.session(),List.of(row.historyEntry()),old.lastCheckpoint(),old.rollbackWarFailure(),old.managedRestoreTransaction(),old.successionExpectation(),old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
        var next=new DriverObservationFacts(driver,facts.driverVersion(),facts.episodeEpoch(),facts.transport(),facts.snapshotId(),facts.nativeRevision(),facts.nativeStateSha256(),facts.publicRevision(),facts.observationVersion(),facts.source(),facts.originalSemanticFields(),facts.semanticFactsEvidence());
        return assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(frame,next,base.originalEvidence()));
    }
    @Test void sourceOwnedReadHistoryPublicRolesRoundtripWithoutConvertingUnknownArgumentNamesOrClaimingWorldCredit() {
        var actual=withReadHistory(false);var encoded=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(actual,true));
        var tree=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);var row=OpportunityJson.object(OpportunityJson.array(tree.get("native_command_history"),"history").getFirst(),"row");
        var source=OpportunityJson.object(row.get("read_history_source"),"read source");assertEquals(MAX64.toString(),OpportunityJson.text(source.get("connection_generation"),"connection_generation"));
        assertEquals(MAX64.toString(),OpportunityJson.text(source.get("query_sequence"),"query_sequence"));
        assertEquals(MAX64.toString(),OpportunityJson.text(OpportunityJson.object(row.get("result"),"result").get("queried_revision"),"queried_revision"));
        assertEquals(actual.semantic(),PublicSnapshotCodec.decode(encoded));
        String publicText=new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8);
        for(String invalid:List.of(publicText.replace("\"query_sequence\":\""+MAX64+"\"","\"query_sequence\":true"),
                publicText.replace("\"query_sequence\":\""+MAX64+"\"","\"query_sequence\":\"01\"")))
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(DriverStateAssemblerTest.bytes(invalid))));
        var unsafe=withReadHistory(true);var failed=assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encode(PublicSnapshotCodec.export(unsafe,true)));
        assertTrue(failed.getMessage().contains("/native_command_history/0/read_history_source/arguments/unqualified_revision"));
        assertEquals(1,OpportunityJson.array(unsafe.semantic().get("native_command_history"),"original history").size());
        assertTrue(OpportunityJson.array(PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(unsafe,false))).get("native_command_history"),"omitted").isEmpty());
    }
}
