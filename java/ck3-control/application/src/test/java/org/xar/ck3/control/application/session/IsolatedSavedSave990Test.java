package org.xar.ck3.control.application.session;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.SettledSameGameData;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ObservedGameplayEntry;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Pure-DATA witness for ContinuityBatchJournal.UnresolvedSameGameData constructor's no-capture branch
 * using historical typed DTOs. Ref labels/file witnesses are DATA, not physical or canonical proof.
 * No writer session, current authority, native IO, file IO, or private artifact access.
 * This does not test full history validation, stable-file SAVE confirmation, or a private SavedRole.
 */
final class IsolatedSavedSave990Test {

    private static final String MACHINE = "witness-machine";
    private static final String SESSION = "witness-session";
    private static final String BATCH = "witness-batch";
    private static final String ACTION_ID = "witness-save-action";
    private static final String SHA256 = "0000000000000000000000000000000000000000000000000000000000000000";
    private static final Instant OLD_DEADLINE = Instant.parse("2020-01-01T00:00:00Z");
    private static final Instant OLD_OBSERVED = Instant.parse("2019-12-31T23:59:59Z");

    private static ExactRef ref(String path) {
        return new ExactRef(java.nio.file.Path.of("data-only-fixture").toAbsolutePath().resolve(path).toString(), 1, SHA256);
    }

    private static GameGeneration game() {
        return new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE));
    }

    private static G2Source source() {
        return new G2Source(MACHINE, "2020-01-01T00:00:00Z", "test-build", ref("source-ref"));
    }

    private static ProposalLifecycle.ObservationIdentity identity() {
        var frame = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.valueOf(9), BigInteger.valueOf(53144328)),
                "snapshot-9", BigInteger.valueOf(2), "episode-real-1");
        return new ProposalLifecycle.ObservationIdentity(MACHINE, game(), frame, 1);
    }

    private static ActionCommand command() { return command(ACTION_ID); }

    private static ActionCommand command(String actionId) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, identity(), source(),
                CheckpointRequestFactory.OBSERVER_SCHEMA,
                List.of(
                        new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("date_raw"), BigInteger.valueOf(53144328)),
                        new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("played_character_id"), BigInteger.valueOf(73)),
                        new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("checkpoint_pair_verified"), true)));
        return new ActionCommand(actionId, identity(), source(), SESSION, new OperationKey("save-checkpoint"),
                new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                OLD_DEADLINE);
    }

    private static ActionReceipt receipt() { return receipt(command(), "req-1", 10, true); }

    private static ActionReceipt receipt(ActionCommand cmd, String requestId, long sequence, boolean nativeOk) {
        var sha = ActionCodec.bodySha256(cmd);
        var attempt = new ActionState.Attempt(requestId, OLD_OBSERVED,
                new GuardEvidence(cmd.origin(), source(), SESSION, BigInteger.ONE, cmd.operation(),
                        ref("native-ev"), ref("cap-ev"), "auth", OLD_OBSERVED, OLD_DEADLINE),
                new NativeRequest("save-checkpoint", Optional.empty(), new RawJson(new byte[]{'{', '}'})));
        // Historical packet DATA only: no outbound/current custody or freshness is invented.
        var ackBody = "{\"type\":\"ack\",\"protocol_version\":1,\"request_id\":\"" + requestId
                + "\",\"ok\":" + nativeOk + ",\"result\":null}";
        var ackBytes = ackBody.getBytes(StandardCharsets.UTF_8);
        var framedAck = new byte[4 + ackBytes.length];
        java.nio.ByteBuffer.wrap(framedAck).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(ackBytes.length);
        System.arraycopy(ackBytes, 0, framedAck, 4, ackBytes.length);
        var ack = new NativeActionPort.AckReceived(requestId, nativeOk, Optional.empty(),
                new RawJson(ackBytes), framedAck);
        var unknown = new ActionState.Unknown(Optional.of(attempt), Optional.of(ack), "unresolved", List.of(ref("ev")));
        return new ActionReceipt(1, sequence, cmd, sha, unknown);
    }

    private static CheckpointPair pair() {
        var save = new CheckpointPair.FileWitness(ref("save-ref"), new FileStatIdentity(BigInteger.ONE, "1", "1"));
        var driver = new CheckpointPair.FileWitness(ref("driver-ref"), new FileStatIdentity(BigInteger.ONE, "1", "1"));
        return new CheckpointPair(save, driver, identity(), "lineage", 1, ACTION_ID, ref("ack-ref"), OLD_OBSERVED);
    }

    private static SemanticEvidence semantic() {
        return new SemanticEvidence(identity(), ref("sem"), ref("native"), ref("stamp"), ref("driver"), OLD_OBSERVED);
    }

    private static DriverSnapshotFacts.Known known() {
        var wire = "{\"format_version\":2,\"pipe_name\":\"p\",\"bridge_pid\":42,\"episode_character_id\":73,\"episode_run_id\":\"episode-real-1\",\"last_checkpoint\":null,\"command_history\":[],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":null}";
        var bytes = wire.getBytes(StandardCharsets.UTF_8);
        var ref = new ExactRef("driver-ref", bytes.length, DriverJson.sha256(bytes));
        return DriverFactsRepository.imported(ref, bytes, 1, 1, game(), new OpportunityJson.Obj(Map.of()));
    }

    private static ControllerRestartState controller() {
        return new ControllerRestartState(new SessionIdentity(MACHINE, game(), SESSION), BATCH, 1, Set.of(BATCH), Set.of(),
                Optional.of(pair()), Optional.of(ref("head")), 0, false, false, false, 0, Set.of(), false);
    }

    private static ObservedGameplayEntry.Details entry() {
        return new ObservedGameplayEntry.Details(MACHINE, SESSION, "ep", "snap", game(), 1, 0, 73,
                BigInteger.ONE, BigInteger.ONE, new ObservedGameplayEntry.Origin.CurrentMap(),
                ref("read"), ref("frame"), ref("driver"), ref("facts"));
    }

    @Test void actualNoCaptureBranchAcceptsIsolatedSaveDataAndRejectsFiniteMutations() {
        // Positive fixture: history.canonicalSequence=11 > receipt.sequence=10.
        var original = receipt();
        var history = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(original), 11, SHA256, List.of(ref("h")));
        var data = new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(original), Optional.of(history));
        assertTrue(data.retainedHistory().isPresent());
        assertSame(original, data.unresolvedActions().getFirst());
        assertInstanceOf(ActionState.Unknown.class, original.state());
        var historicalAck = original.ack().orElseThrow();
        assertTrue(historicalAck.outbound().isEmpty());
        assertTrue(historicalAck.custody().isEmpty());
        assertEquals(historicalAck.originalFrame().bytes().length,
                java.nio.ByteBuffer.wrap(historicalAck.originalPacket()).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt());
        assertArrayEquals(historicalAck.originalFrame().bytes(),
                java.util.Arrays.copyOfRange(historicalAck.originalPacket(), 4, historicalAck.originalPacket().length));
        assertThrows(IllegalStateException.class, () -> data.capturedManifest());
        assertFalse(data.unresolvedActions().getFirst().settled());
        assertEquals(OLD_DEADLINE, data.unresolvedActions().getFirst().command().deadline());

        // Negative 1: Missing saved pair (cycleSEM still present)
        var noPairController = new ControllerRestartState(new SessionIdentity(MACHINE, game(), SESSION), BATCH, 1, Set.of(BATCH), Set.of(),
                Optional.empty(), Optional.of(ref("head")), 0, false, false, false, 0, Set.of(), false);
        var h1 = new SettledSameGameData(entry(), noPairController, known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(receipt()), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), noPairController, known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h1)));

        // Negative 2: Missing cycle semantic (savedpair still present)
        var h2 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.empty(), identity(), List.of(receipt()), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h2)));

        // Negative 3: Wrong StartAfter origin
        var startAck = new ObservedGameplayEntry.Details(MACHINE, SESSION, "ep", "snap", game(), 1, 0, 73,
                BigInteger.ONE, BigInteger.ONE, new ObservedGameplayEntry.Origin.StartAfter(ref("start")),
                ref("read"), ref("frame"), ref("driver"), ref("facts"));
        var h3 = new SettledSameGameData(startAck, controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(receipt()), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h3)));

        // Negative 4: Two distinct unresolved originals, each valid historical DATA.
        var second = receipt(command("second-save-action"), "req-2", 11, true);
        assertNotEquals(original.command().actionId(), second.command().actionId());
        var h4 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(original, second), 12, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                12, SHA256, List.of(BATCH), 1, List.of(original, second), Optional.of(h4)));

        // Negative 5: Original SAVE not contained by retained canonical history
        var h5 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h5)));

        // Negative 6: Canonical sequence not later (equal to receipt sequence)
        var h6 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(receipt()), 10, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                10, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h6)));

        // Negative 7: Changed retained source
        var otherSource = new G2Source("other", "2020-01-01T00:00:00Z", "test-build", ref("source-ref"));
        var h7 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                otherSource, Optional.of(semantic()), identity(), List.of(receipt()), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h7)));

        // Negative 8: No original positive ACK (Unknown without dispatch)
        var noAck = new ActionState.Unknown(Optional.empty(), Optional.empty(), "unresolved", List.of(ref("ev")));
        var r8 = new ActionReceipt(1, 10, command(), ActionCodec.bodySha256(command()), noAck);
        var h8 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(r8), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(r8), Optional.of(h8)));

        // Negative 9: Different capturedController from retained history
        var otherController = new ControllerRestartState(new SessionIdentity(MACHINE, game(), SESSION), BATCH, 2, Set.of(BATCH), Set.of(),
                Optional.of(pair()), Optional.of(ref("head")), 0, false, false, false, 0, Set.of(), false);
        var h9 = new SettledSameGameData(entry(), otherController, known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(receipt()), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(receipt()), Optional.of(h9)));


        // Negative 10: A retained negative ACK must not acquire positive-ACK SAVE admission.
        var negativeAck = receipt(command(), "negative-ack", 10, false);
        var h10 = new SettledSameGameData(entry(), controller(), known(), ref("full-driver"),
                new NativeObservationPort.TransportSession(MACHINE, game(), BigInteger.ONE, SESSION),
                source(), Optional.of(semantic()), identity(), List.of(negativeAck), 11, SHA256, List.of(ref("h")));
        assertThrows(IllegalArgumentException.class, () -> new ContinuityBatchJournal.UnresolvedSameGameData(Optional.empty(), controller(), known(), ref("full-driver"),
                11, SHA256, List.of(BATCH), 1, List.of(negativeAck), Optional.of(h10)));
    }
}