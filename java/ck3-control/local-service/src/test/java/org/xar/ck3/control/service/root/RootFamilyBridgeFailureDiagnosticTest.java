package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Original producer failure becomes a precise existing MissingDocuments result, without a fabricated Bridge. */
final class RootFamilyBridgeFailureDiagnosticTest {
    @Test void actualExplicitBudgetFailureIsReportedInsteadOfMissingProcessIdentity() {
        var original = assertThrows(IllegalArgumentException.class,
                () -> StrictJson.canonical(StrictJson.object(), DriverJson.MAX_NATIVE_BYTES));
        assertTrue(original.getMessage().contains("explicit JSON output byte budget"));
        assertDiagnostic(original);
    }

    @Test void originalArchiveIoFailureRetainsItsCauseAndDoesNotReadDomainBodies() {
        assertDiagnostic(new IOException("retained original semantic artifact is unavailable"));
    }

    private static void assertDiagnostic(Exception original) {
        var translated = RootFamilyBridge.observationUnavailable(original);
        assertSame(original, translated.getCause());
        var domainReads = new AtomicInteger();
        var bridge = new FamilyDomainSource.CurrentBridge() {
            @Override public Optional<FamilyDomainSource.BridgeObservation> observe(PlanningRequest request) { throw translated; }
            @Override public boolean verifyRetained(PlanningReadReceipt read, FamilyDomainSource.BridgeObservation observed) {
                throw new AssertionError("failed observation grants no retained identity");
            }
        };
        var source = new FamilyDomainSource(() -> { domainReads.incrementAndGet(); throw new AssertionError("unavailable observation cannot read family bodies"); }, bridge);
        var missing = assertInstanceOf(FamilyPorts.MissingDocuments.class, source.readCurrent(request()));
        assertTrue(missing.reason().contains("actual family Bridge observation unavailable"));
        assertTrue(missing.reason().contains(original.getClass().getSimpleName()));
        assertTrue(missing.reason().contains(original.getMessage()));
        assertFalse(missing.reason().contains("Game PID cannot substitute"));
        assertEquals(0, domainReads.get());
    }

    private static PlanningRequest request() {
        var now = Instant.parse("2026-10-30T15:47:00Z");
        var source = new G2Source("software-family-diagnostic", now.toString(), "fixture-build", new ExactRef("fixture/source", 1, "a".repeat(64)));
        var identity = new ObservationIdentity(source.machineId(), new GameGeneration(4242,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(53144328)), "native:1", BigInteger.ONE, "software-episode"), 1);
        var snapshot = DriverJson.object(("{\"paused\":true,\"map_ready\":true,\"revision\":1,\"native_revision\":1,\"date_raw\":53144328,"
                +"\"snapshot_id\":\"native:1\",\"episode_run_id\":\"software-episode\",\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES);
        return new PlanningRequest(identity, source, "software-session", now.plusSeconds(30),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
}
