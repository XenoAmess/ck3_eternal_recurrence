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

final class LifecycleBusinessFixture {
    static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    final NativeCheckpointFiles files=new NativeCheckpointFiles();
    final LifecycleObservationPort.Snapshot snapshot;
    final ActionCommand parent;
    LifecycleBusinessFixture(Path root) throws IOException {
        this(root,DeathSettlementTest.ready(false,10,10));
    }
    LifecycleBusinessFixture(Path root,com.fasterxml.jackson.databind.node.ObjectNode nativeSettlement) throws IOException {
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var lifecycle=LifecycleJson.row();lifecycle.put("schema","xar.ck3.succession-lifecycle-binding/v1");lifecycle.put("lifecycle","rogue_one_life");
        lifecycle.put("xar_enabled","xar_on");lifecycle.put("pact_contract","test-pact");lifecycle.put("source","test-bound-source");lifecycle.put("environment_sha256","a".repeat(64));
        var document=LifecycleJson.row();document.put("format_version",2);document.put("pipe_name","test-pipe");document.put("bridge_pid",123);
        document.put("episode_character_id",73);document.put("episode_run_id","episode-1");var history=document.putArray("command_history");
        var original=history.addObject();original.put("index",1);original.put("command","query-large-original");original.put("ok",false);
        original.putObject("result").put("status","unknown").put("retained_original","x".repeat(150000)).put("opaque_decimal",-0.0);
        document.putNull("last_checkpoint");document.putNull("rollback_war_failure");document.putNull("managed_restore_transaction");document.putNull("succession_expectation");
        document.set("succession_lifecycle",lifecycle);document.putNull("campaign_goal");document.putArray("rollback_war_failures");
        var driver=DriverStateSnapshot.decodeComplete(LifecycleJson.bytes(document));
        var basis=files.createNew(root.resolve("original-driver.json"),driver.encode()).reference();
        var state=LifecycleJson.row();state.put("paused",true);state.put("map_ready",true);state.put("speed",3);state.put("date_raw",240);
        state.putObject("played_character").put("character_id",73).put("alive",false);state.put("one_life_terminal_reason","played_character_dead");
        state.set("one_life_settlement",nativeSettlement.deepCopy());state.putNull("succession_reconciliation");
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
        var semantic=OpportunityJson.object(LifecycleJson.immutable(state),"actual v1 raw terminal semantic");
        var originalManifest=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.encode(
                known,actual,BigInteger.ONE,1L,source,semantic,basis);
        var manifest=files.createNew(root.resolve("original-semantic-manifest.json"),originalManifest.bytes()).reference();
        var observations=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.decode(
                manifest,originalManifest,new RawJson(driver.encode()),actual);
        var observedKnown=new DriverSnapshotFacts.Known(driver,known.stamp(),basis,known.actionRows(),known.auxiliary(),
                known.loop(),Optional.of(observations));
        snapshot=new LifecycleObservationPort.Snapshot(actual,source,semantic,observedKnown,evidence);
        var hello=files.createNew(root.resolve("original-hello.json"),"test original hello".getBytes(StandardCharsets.UTF_8)).reference();
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
        return LifecycleReducer.death(snapshot,settlement(),new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of()),AT);
    }
    DeathSettlement.Ready settlement() {
        var raw=org.xar.ck3.control.application.driver.DriverJson.object(snapshot.actual().state().bytes(),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        return DeathSettlement.normalize(OpportunityJson.toNode(raw.get("one_life_settlement"))).orElseThrow();
    }
}
