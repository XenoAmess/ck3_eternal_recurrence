package org.xar.ck3.control.application.action.council;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Pure format/reducer DATA only: no archive membership, private issuer, permission or Native call. */
final class CouncilSeatCheckpointState289Test {
    private static final String HASH = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    private static final String BODY = "1111111111111111111111111111111111111111111111111111111111111111";
    private static final Scope SCOPE = new Scope("parent-a", BODY, "original-submit");
    private static final Instant TIME = Instant.parse("2026-01-01T00:00:00Z");

    private static ExactRef ref(String role) { return new ExactRef("fixture/" + role, 1, HASH); }
    // Independent literal contract spelling; never obtains expected bytes from the codec or JSON tree writer.
    private static String goldenRef(String role) {
        return "{\"bytes\":1,\"path\":\"fixture/" + role + "\",\"sha256\":\"" + HASH + "\"}";
    }
    private static String goldenV1() {
        return "{\"active\":{\"original_attempt_request_id\":\"original-submit\","
                + "\"parent_action_id\":\"parent-a\",\"parent_body_sha256\":\"" + BODY + "\"},"
                + "\"completed_scope_chain\":" + goldenRef("closed") + ",\"machine_id\":\"fixture-machine\","
                + "\"records\":[" + goldenRef("ack-0") + "," + goldenRef("ack-1") + "," + goldenRef("ack-2")
                + "],\"schema\":\"xar.java-council-continuations/v1\"}";
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static List<Retained> acknowledgements() {
        var source = new G2Source("fixture-machine", TIME.toString(), "fixture-build", ref("source"));
        var observed = new ProposalLifecycle.ObservationIdentity("fixture-machine",
                new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                        BigInteger.ONE, BigInteger.valueOf(53175816)), "fixture:1", BigInteger.ONE, "fixture-episode"), 1);
        var rows = new ArrayList<Retained>();
        for (int index = 0; index < 3; index++) {
            var stage = Stage.values()[index];
            var guard = new GuardEvidence(observed, source, "fixture-session", BigInteger.ONE,
                    new OperationKey(stage.step()), ref("native"), ref("hello"), "fixture-authority", TIME, TIME.plusSeconds(60));
            var request = new Request(SCOPE, "continuation-" + index, stage, ref("parent"), ref("prepared-" + index),
                    guard, TIME.plusSeconds(1), TIME.plusSeconds(30), 2L * index + 1, List.of(ref("support")));
            var entry = new Entry(request, Status.ACK, Optional.of(ref("outcome-" + index)),
                    Optional.of(new IssuedCustody(ref("issued-" + index), ref("domain-" + index), ref("event-" + index))),
                    2L * index + 2);
            rows.add(new Retained(ref("ack-" + index), entry));
        }
        return List.copyOf(rows);
    }
    private static State state(List<Retained> rows) {
        return new State("fixture-machine", Optional.of(SCOPE), rows.stream().map(Retained::reference).toList(), Optional.of(ref("closed")));
    }

    @Test void absentCheckpointKeepsLiteralV1BytesAndLegacyConstructor() {
        var old = state(acknowledgements());
        byte[] golden = bytes(goldenV1());
        assertArrayEquals(golden, CouncilContinuationCodec.encodeState(old));
        var reopened = CouncilContinuationCodec.decodeState(golden);
        assertEquals(old, reopened);
        assertTrue(reopened.seatCheckpoint().isEmpty());
        assertArrayEquals(golden, CouncilContinuationCodec.encodeState(new State(old.machineId(), old.active(),
                old.records(), old.completedScopeChain(), Optional.empty())));
    }

    @Test void checkpointPointerRoundTripsAndRejectsForeignScopeOrUnresolvedRows() {
        var rows = acknowledgements();
        var old = state(rows);
        var first = CouncilContinuationReducer.seatCheckpoint(old, rows, SCOPE, ref("seat-a"));
        var next = CouncilContinuationReducer.seatCheckpoint(first, rows, SCOPE, ref("seat-b"));
        String expectedV2 = goldenV1().replace("continuations/v1", "continuations/v2");
        expectedV2 = expectedV2.substring(0, expectedV2.length() - 1) + ",\"seat_checkpoint\":" + goldenRef("seat-b") + "}";
        assertArrayEquals(bytes(expectedV2), CouncilContinuationCodec.encodeState(next));
        var reopened = CouncilContinuationCodec.decodeState(bytes(expectedV2));
        assertEquals(Optional.of(ref("seat-b")), reopened.seatCheckpoint());
        assertEquals(old.machineId(), reopened.machineId());
        assertEquals(old.active(), reopened.active());
        assertEquals(old.records(), reopened.records());
        assertEquals(old.completedScopeChain(), reopened.completedScopeChain());
        assertEquals(Optional.of(ref("seat-a")), first.seatCheckpoint());
        assertTrue(old.seatCheckpoint().isEmpty());
        for (var foreign : List.of(new Scope("parent-b", BODY, SCOPE.originalAttemptRequestId()),
                new Scope(SCOPE.parentActionId(), "2".repeat(64), SCOPE.originalAttemptRequestId()),
                new Scope(SCOPE.parentActionId(), BODY, "another-submit"))) {
            assertThrows(ContractViolationException.class,
                    () -> CouncilContinuationReducer.seatCheckpoint(first, rows, foreign, ref("seat-b")));
        }
        for (var unresolved : List.of(Status.ISSUED, Status.UNKNOWN)) {
            var changedRows = new ArrayList<>(rows);
            var previous = rows.getLast();
            var entry = unresolved == Status.ISSUED
                    ? new Entry(previous.request(), unresolved, Optional.empty(), Optional.empty(), 0)
                    : new Entry(previous.request(), unresolved, previous.entry().outcome(), previous.entry().issued(), previous.entry().resultSequence());
            changedRows.set(2, new Retained(ref("unresolved-" + unresolved.name()), entry));
            var before = state(changedRows);
            assertThrows(ContractViolationException.class,
                    () -> CouncilContinuationReducer.seatCheckpoint(before, changedRows, SCOPE, ref("seat-b")));
        }
        assertThrows(ContractViolationException.class, () -> new State("fixture-machine", Optional.empty(), List.of(), Optional.empty(), Optional.of(ref("seat-a"))));
        assertThrows(ContractViolationException.class, () -> CouncilContinuationCodec.decodeState(bytes(goldenV1().replace("continuations/v1", "continuations/v2"))));
        String v1WithCheckpoint = goldenV1().substring(0, goldenV1().length() - 1) + ",\"seat_checkpoint\":null}";
        String v2NullCheckpoint = expectedV2.replace(goldenRef("seat-b"), "null");
        assertThrows(ContractViolationException.class, () -> CouncilContinuationCodec.decodeState(bytes(v1WithCheckpoint)));
        assertThrows(ContractViolationException.class, () -> CouncilContinuationCodec.decodeState(bytes(v2NullCheckpoint)));
    }
}
