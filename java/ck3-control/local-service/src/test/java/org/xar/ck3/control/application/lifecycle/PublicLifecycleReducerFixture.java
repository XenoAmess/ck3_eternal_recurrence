package org.xar.ck3.control.application.lifecycle;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.CommandExpectation;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact campaign source06 DATA fixture, renamed for this consumer module and with its original ready helper inlined.
 * This creates no Root, private Lease, managed creator, canonical strategy qualification or Host. */
final class PublicLifecycleReducerFixture {
    static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    final NativeCheckpointFiles files=new NativeCheckpointFiles();
    final LifecycleObservationPort.Snapshot snapshot;
    final ActionCommand parent;
    PublicLifecycleReducerFixture(Path root) throws IOException {
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var lifecycle=LifecycleJson.row();lifecycle.put("schema","xar.ck3.succession-lifecycle-binding/v1");lifecycle.put("lifecycle","rogue_one_life");
        lifecycle.put("xar_enabled","xar_on");lifecycle.put("pact_contract","test-pact");lifecycle.put("source","test-bound-source");lifecycle.put("environment_sha256","a".repeat(64));
        var document=LifecycleJson.row();document.put("format_version",2);document.put("pipe_name","test-pipe");document.put("bridge_pid",123);
        document.put("episode_character_id",73);document.put("episode_run_id","episode-1");var history=document.putArray("command_history");
        var original=history.addObject();original.put("index",1);original.put("command","query-large-original");original.put("ok",false);
        original.putObject("result").put("status","unknown").put("retained_original","x".repeat(150000));
        document.putNull("last_checkpoint");document.putNull("rollback_war_failure");document.putNull("managed_restore_transaction");document.putNull("succession_expectation");
        document.set("succession_lifecycle",lifecycle);document.putNull("campaign_goal");document.putArray("rollback_war_failures");
        var driver=DriverStateSnapshot.decodeComplete(LifecycleJson.bytes(document));
        var basis=files.createNew(root.resolve("original-driver.json"),driver.encode()).reference();
        var state=LifecycleJson.row();state.put("paused",true);state.put("map_ready",true);state.put("speed",3);state.put("date_raw",240);
        state.putObject("played_character").put("character_id",73).put("alive",false);state.put("one_life_terminal_reason","played_character_dead");
        state.set("one_life_settlement",ready());state.putNull("succession_reconciliation");
        state.put("snapshot_id","native:1");state.put("revision",1);state.put("native_revision",1);state.put("episode_run_id","episode-1");
        state.putObject("diagnostics").put("bridge_pid",123).put("connection_generation",1);state.putArray("active_wars");state.putArray("player_armies");
        var envelope=LifecycleJson.row();envelope.put("type","state_snapshot");envelope.put("protocol_version",1);envelope.put("snapshot_id","native:1");envelope.put("revision",1);envelope.set("state",state);
        byte[] json=LifecycleJson.bytes(envelope),packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var evidence=files.createNew(root.resolve("terminal-native.bin"),packet).reference();var sourceRef=files.createNew(root.resolve("source.txt"),"test source".getBytes(StandardCharsets.UTF_8)).reference();
        var source=new G2Source("test-machine",AT.toString(),"test-build",sourceRef);
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",game,BigInteger.ONE,"test-session"),"native:1",BigInteger.ONE,new RawJson(LifecycleJson.bytes(state)),packet,AT);
        var auxiliary=LifecycleJson.row();auxiliary.putArray("native_capabilities").add("game.state.xar-one-life-settlement");
        auxiliary.set("one_life_strategy",LifecycleJson.parse(CrossRunPlanning.encodeState(CrossRunPlanning.empty()),CrossRunPlanning.MAX_BYTES));
        auxiliary.putNull("family_marriage_ledger");
        var known=new DriverSnapshotFacts.Known(driver,new DriverSnapshotFacts.Stamp(0,0,game,"episode-1",LifecycleJson.sha(driver.encode())),basis,List.of(),
                OpportunityJson.object(LifecycleJson.immutable(auxiliary),"actual auxiliary"),Optional.empty(),Optional.empty());
        snapshot=new LifecycleObservationPort.Snapshot(actual,source,OpportunityJson.object(LifecycleJson.immutable(state),"actual terminal semantic"),known,evidence);
        var hello=files.createNew(root.resolve("original-hello.json"),"test original hello".getBytes(StandardCharsets.UTF_8)).reference();
        var manifest=files.createNew(root.resolve("original-semantic-manifest.json"),"test original semantic manifest".getBytes(StandardCharsets.UTF_8)).reference();
        var identity=new LifecycleIdentity("test-machine",game,"test-session",BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.valueOf(73),"episode-1",0,0),
                new LifecycleIdentity.Frame("native:1",BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(240),true,true),
                new LifecycleIdentity.Character(BigInteger.valueOf(73),false),LifecycleIdentity.TerminalReason.DEAD,
                new LifecycleIdentity.Evidence(evidence,hello,manifest,basis,sourceRef),AT);
        var expected=new LifecycleExpectedPostcondition(identity,source,"lifecycle-test-result/v1",LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),false),
                        new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.advance_verified"),false),
                        new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"),false)));
        parent=new ActionCommand("death-test-1",new CommandOrigin.LifecycleTerminal(identity),source,"test-session",new OperationKey("death-terminal"),
                new OpportunityJson.Obj(Map.of("expected_revision",new OpportunityJson.IntegerValue(BigInteger.ONE))),new CommandExpectation.LifecycleTerminal(expected),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(30));
    }
    LifecycleReducer.Reduction reduction() {
        var settled=DeathSettlement.normalize(OpportunityJson.toNode(snapshot.semantic().get("one_life_settlement"))).orElseThrow();
        return LifecycleReducer.death(snapshot,settled,new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of()),AT);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode ready() {
        var row=LifecycleJson.row();row.put("ready",true);row.put("commit_serial",1);row.put("source_character_id",73);
        row.putObject("final_score").put("raw",1234500).put("scale",100000);row.put("score_before_reject",15.5);
        row.put("record_candidate",10);row.put("old_record",10);row.put("record_delta",0);
        row.put("blessing_count",2);row.put("refusal_count",1);row.put("contract_progress",6);row.put("record_written",false);return row;
    }
}
