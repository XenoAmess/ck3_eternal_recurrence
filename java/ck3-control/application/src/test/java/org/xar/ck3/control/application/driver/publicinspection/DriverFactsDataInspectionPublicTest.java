package org.xar.ck3.control.application.driver.publicinspection;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic public DATA only; no Root issuer, current Game or marker permission. */
public final class DriverFactsDataInspectionPublicTest {
    private static DriverStateAssembler assemblerWithRejectingPorts(DriverSnapshotFacts.State state) {
        ActionJournal journal = new ActionJournal() {
            @Override public <T> T locked(Function<LockedJournal, T> operation) {
                throw new AssertionError("facts DATA inspection must not enter the action journal");
            }
        };
        return new DriverStateAssembler(new ActionSnapshotReader(journal), new DriverFactsRepository(state),
                ignored -> { throw new AssertionError("facts DATA inspection must not request an observation"); });
    }

    private static DriverSnapshotFacts.Known syntheticKnown(OpportunityJson.Obj auxiliary) {
        var nil = new DriverStateSnapshot.NullValue();
        var driver = new DriverStateSnapshot.Complete(
                new DriverStateSnapshot.Session("synthetic-data-pipe", 42, BigInteger.valueOf(73), "synthetic-data-episode"),
                List.of(), nil, nil, nil, nil, nil, nil, nil);
        byte[] encoded = driver.encode();
        String sha256 = DriverJson.sha256(encoded);
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, game, driver.session().episodeRunId(), sha256);
        var syntheticBasis = new ExactRef("memory/synthetic-data-driver.json", encoded.length, sha256);
        return new DriverSnapshotFacts.Known(driver, stamp, syntheticBasis, List.of(), auxiliary,
                Optional.empty(), Optional.empty());
    }

    @Test public void unavailableFactsReachExactlyOneDataCallbackWithoutJournalOrObservation() {
        var unavailable = new DriverSnapshotFacts.Unavailable(List.of("synthetic facts are unavailable"));
        var assembler = assemblerWithRejectingPorts(unavailable);
        var invocations = new AtomicInteger();

        String result = assembler.inspectFactsData(state -> {
            invocations.incrementAndGet();
            assertSame(unavailable, state);
            return ((DriverSnapshotFacts.Unavailable) state).reasons().get(0);
        });

        assertEquals("synthetic facts are unavailable", result);
        assertEquals(1, invocations.get());
    }

    @Test public void knownFactsExposeTheSameUninterpretedAuxiliaryDataWithoutActionProjection() {
        var probe = new OpportunityJson.Text("synthetic uninterpreted DATA only");
        var auxiliary = new OpportunityJson.Obj(Map.of("synthetic_data_probe", probe));
        var known = syntheticKnown(auxiliary);
        var assembler = assemblerWithRejectingPorts(known);
        var invocations = new AtomicInteger();

        OpportunityJson.Obj result = assembler.inspectFactsData(state -> {
            invocations.incrementAndGet();
            assertSame(known, state);
            var data = (DriverSnapshotFacts.Known) state;
            assertSame(known.stamp(), data.stamp());
            assertSame(known.stamp().game(), data.stamp().game());
            assertEquals(known.driver().session().episodeRunId(), data.stamp().episodeRunId());
            return data.auxiliary();
        });

        assertSame(auxiliary, result);
        assertSame(probe, result.members().get("synthetic_data_probe"));
        assertEquals(1, invocations.get());
    }

    @Test public void callbackFailureIsNotRelabeledAsAbsenceAndDoesNotRetryTheInspection() {
        var unavailable = new DriverSnapshotFacts.Unavailable(List.of("synthetic unavailable DATA"));
        var assembler = assemblerWithRejectingPorts(unavailable);
        var deliberate = new IllegalStateException("synthetic callback failure");
        var invocations = new AtomicInteger();

        var thrown = assertThrows(IllegalStateException.class, () -> assembler.inspectFactsData(state -> {
            invocations.incrementAndGet();
            assertSame(unavailable, state);
            throw deliberate;
        }));

        assertSame(deliberate, thrown);
        assertEquals(1, invocations.get());
        DriverSnapshotFacts.State next = assembler.inspectFactsData(state -> {
            invocations.incrementAndGet();
            return state;
        });
        assertSame(unavailable, next);
        assertEquals(2, invocations.get());
    }
}
