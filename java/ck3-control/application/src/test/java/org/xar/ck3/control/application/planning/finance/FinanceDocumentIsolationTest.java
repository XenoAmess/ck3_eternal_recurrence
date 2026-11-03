package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Public synthetic DATA boundaries, without storage, session or allocation-rate authority. */
final class FinanceDocumentIsolationTest {
    private static final ExactRef DEFINITION = new ExactRef("D:/fixture/finance-reader.java", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186",
            "2026-11-03T05:00:00Z", "1.20.0.4", DEFINITION);

    private static PlanningRequest request() {
        var identity = new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                        BigInteger.ONE, BigInteger.valueOf(100)), "native:1", BigInteger.ONE,
                        "episode-finance-isolation"), 1);
        Obj snapshot = object(parse(("{\"paused\":true,\"map_ready\":true,\"snapshot_id\":\"native:1\","
                + "\"revision\":1,\"native_revision\":1,\"date_raw\":100,"
                + "\"episode_run_id\":\"episode-finance-isolation\","
                + "\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],"
                + "\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null}")
                .getBytes(StandardCharsets.UTF_8)), "fixture");
        var observed = new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(),
                List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(identity, SOURCE, "finance-isolation-session",
                Instant.parse("2026-11-03T06:00:00Z"), observed);
    }

    private static FinanceStatePort.Document document(FinanceStatePort.Domain domain, byte[] raw) {
        return new FinanceStatePort.Document(domain,
                new ExactRef("D:/fixture/" + domain + ".json", raw.length, ActionCodec.sha256(raw)), raw);
    }

    private static FinanceStatePort port(PlanningRequest request, List<FinanceStatePort.Document> documents,
            List<FinanceStatePort.ReaderBinding> readers) {
        return new FinanceStatePort(ignored -> new FinanceStatePort.Head(request.before(), DEFINITION,
                documents, List.of(), Optional.empty()), readers);
    }

    @Test void callerAccessorAndDecoderArraysCannotAlterRetainedLedgerOrLaterRead() {
        var request = request();
        for (String bom : List.of("", "\ufeff")) {
            byte[] input = (bom + "{\"pending\":null,\"extension\":{\"unknown\":[1.2300,-0.0,\"独立原件\"]}}")
                    .getBytes(StandardCharsets.UTF_8);
            byte[] expected = input.clone();
            var document = document(FinanceStatePort.Domain.MERCENARY, input);
            Arrays.fill(input, (byte) '!');
            Arrays.fill(document.bytes(), (byte) '?');
            var calls = new AtomicInteger();
            var reader = new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY, DEFINITION, body -> {
                assertSame(document, body);
                assertArrayEquals(expected, body.bytes());
                byte[] callbackCopy = body.bytes();
                Arrays.fill(callbackCopy, (byte) '#');
                calls.incrementAndGet();
                return FinanceStatePort.Pending.CLEAR;
            });
            var port = port(request, List.of(document), List.of(reader));
            byte[] json = bom.isEmpty() ? expected : Arrays.copyOfRange(expected, 3, expected.length);
            Obj expectedRow = DriverJson.object(json, 4 * 1024 * 1024);
            var first = assertInstanceOf(FinanceStatePort.Known.class, port.read(request)).snapshot();
            var ledger = first.ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow();
            assertEquals(FinanceStatePort.Pending.CLEAR, ledger.pending());
            assertEquals(expectedRow, ledger.original());
            assertArrayEquals(expected, ledger.document().bytes());
            Arrays.fill(ledger.document().bytes(), (byte) '$');
            var later = assertInstanceOf(FinanceStatePort.Known.class, port.read(request)).snapshot();
            assertEquals(expectedRow, later.ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow().original());
            assertArrayEquals(expected, document.bytes());
            assertEquals(2, calls.get());
        }
    }

    @Test void pendingValidationAndDecoderFailureKeepPerDomainOrderAndSurvivingEvidence() {
        var request = request();
        var invalid = document(FinanceStatePort.Domain.MERCENARY,
                "{\"pending\":[]}".getBytes(StandardCharsets.UTF_8));
        var rejected = document(FinanceStatePort.Domain.CROWN,
                "{\"pending\":null}".getBytes(StandardCharsets.UTF_8));
        var kept = document(FinanceStatePort.Domain.CONSTRUCTION,
                "{\"pending\":{\"request_id\":\"unchanged-opaque\"},\"extra\":17}".getBytes(StandardCharsets.UTF_8));
        var calls = new ArrayList<String>();
        var readers = List.of(
                new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY, DEFINITION, body -> {
                    fail("malformed pending must be rejected before the callback");
                    return FinanceStatePort.Pending.CLEAR;
                }),
                new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CROWN, DEFINITION, body -> {
                    calls.add("crown");
                    Arrays.fill(body.bytes(), (byte) '!');
                    throw new IllegalArgumentException("controlled owning-decoder rejection");
                }),
                new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION, DEFINITION, body -> {
                    calls.add("construction");
                    return FinanceStatePort.Pending.PENDING;
                }));
        var snapshot = assertInstanceOf(FinanceStatePort.Known.class,
                port(request, List.of(invalid, rejected, kept), readers).read(request)).snapshot();
        assertEquals(List.of("crown", "construction"), calls);
        assertTrue(snapshot.ledger(FinanceStatePort.Domain.MERCENARY).isEmpty());
        assertTrue(snapshot.unavailableReason(FinanceStatePort.Domain.MERCENARY).orElseThrow()
                .contains("explicit original pending field required"));
        assertTrue(snapshot.unavailableReason(FinanceStatePort.Domain.CROWN).orElseThrow()
                .contains("controlled owning-decoder rejection"));
        var ledger = snapshot.ledger(FinanceStatePort.Domain.CONSTRUCTION).orElseThrow();
        assertSame(kept, ledger.document());
        assertEquals(FinanceStatePort.Pending.PENDING, ledger.pending());
        assertEquals(new IntegerValue(BigInteger.valueOf(17)), ledger.original().get("extra"));
        assertEquals(new Text("unchanged-opaque"), ledger.pendingObject().orElseThrow().get("request_id"));
        assertArrayEquals("{\"pending\":null}".getBytes(StandardCharsets.UTF_8), rejected.bytes());
    }
}
