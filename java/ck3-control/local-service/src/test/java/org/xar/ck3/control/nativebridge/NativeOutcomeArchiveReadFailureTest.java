package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual failed READ producer and cold original reader. No constructed failure or Known. */
final class NativeOutcomeArchiveReadFailureTest {
    @TempDir Path root;
    private static final OperationKey QUERY = new OperationKey("query-fixture-archive-failed-read-v1");
    private static final String CAPABILITY = "game.query.fixture-archive-failed-read";
    private record Captured(PlanningReadFailure failure, ExactRef original, int readWrites) { }
    private enum Damage { AFTER_ORIGINAL, EXTERNAL_SOURCE }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<ReadContract<RawJson>> installed) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "archive-failed-read", source -> {
            var contract = new ReadContract<RawJson>("archive-failed-read/v1", QUERY, Optional.of(CAPABILITY),
                    "archive-failed-read", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                    ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                    (request, id) -> new NativeRequest(QUERY.value(), CAPABILITY, raw("{}")),
                    receipt -> receipt.original().originalResultToken().orElseThrow(),
                    receipt -> receipt.original().originalResultToken().orElseThrow());
            installed.set(contract); return List.of(contract);
        }, request -> raw("{\"actual_read\":true}"));
    }
    private static Captured capture(ActionWriterIntegrationFixture actual, ReadContract<RawJson> contract, boolean lost) throws Exception {
        if (lost) actual.loseReadAckOnce(); else actual.rejectNextScenarioRead();
        var basis = actual.command("archive-failed-read-source");
        var request = new PlanningReadRequest(basis.origin(), basis.source(), basis.sessionId(), contract.operation(),
                new OpportunityJson.Obj(Map.of()), Instant.now().plusSeconds(15));
        var observed = new AtomicReference<PlanningReadFailure>();
        var baseline = new AtomicInteger(-1);
        var result = actual.writer.locked(locked -> actual.collector.current(locked, request.before(), request.deadline(), lease -> {
            assertEquals(request.before(), lease.frame().identity());
            baseline.set(actual.nativeReadWrites());
            return actual.reads.readWithFailureEvidence(locked, contract, request,
                (same, installed, requested, unavailable, attempted, originals) -> {
                    attempted.orElseThrow().requireOriginal(same, installed, requested, unavailable, originals);
                    PlanningReadFailure failed = unavailable.observedFailure().orElseThrow();
                    assertNotSame(failed.before(), failed.after());
                    observed.set(failed);
                });
        }));
        assertInstanceOf(PlanningReadResult.Unavailable.class, result);
        assertNotNull(observed.get(), () -> "the real producer must retain its failed after; actual READ: " + result
                + "; baseline=" + baseline.get() + "; writes=" + actual.nativeReadWrites()
                + "; scenario_writes=" + actual.scenarioReadWrites());
        assertEquals(baseline.get() + 1, actual.nativeReadWrites(), "archive verification cannot issue a nested READ");
        assertEquals(1, actual.scenarioReadWrites()); assertEquals(0, actual.nativeActionWrites());
        // DATA interpretation retains its original writer/archive but does not extend the live source lease.
        var failed = observed.get();
        ExactRef original = actual.writer.locked(same -> actual.archive.inSession(same, originals -> {
            originals.verifyReadFailureOriginals(failed);
            ExactRef ref = PlanningReadFailureCodec.preserve(failed, originals);
            assertEquals(failed, PlanningReadFailureCodec.load(ref, originals));
            originals.withSession(same).verifyReadFailureOriginals(failed);
            originals.inSession(same, bound -> {
                assertEquals(failed, PlanningReadFailureCodec.load(ref, bound)); return null;
            });
            return ref;
        }));
        assertEquals(baseline.get() + 1, actual.nativeReadWrites());
        assertEquals(1, actual.scenarioReadWrites()); assertEquals(0, actual.nativeActionWrites());
        return new Captured(failed, original, actual.nativeReadWrites());
    }
    private static ExactRef reference(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        return new ExactRef(path.toAbsolutePath().normalize().toString(), bytes.length, ActionCodec.sha256(bytes));
    }
    private static NativeOutcomeArchive reopen(ActionWriterIntegrationFixture actual, Captured captured) throws Exception {
        String machine = actual.writer.locked(same -> same.head().state().machineId());
        var layout = new WriterContracts.Layout(actual.root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                reference(actual.root.resolve("anchor.json")), machine);
        var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(actual.root.resolve("artifacts"),
                layout.lock(), 16 * 1024 * 1024), actual.writer.storageGuard());
        var cold = new ContinuityWriter(layout, List.of(captured.failure().request().source().sourceRef()),
                new WriterContracts.TransitionAuthority() {
                    @Override public String revalidate(ContinuityState previous, WriterContracts.Request request) {
                        throw new AssertionError("cold failed READ cannot preview a transition");
                    }
                    @Override public ContinuityState reduce(ContinuityState previous, WriterContracts.Request request) {
                        throw new AssertionError("cold failed READ cannot reduce or submit a transition");
                    }
                }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()),
                actual.writer.storageGuard());
        return new NativeOutcomeArchive(store, cold);
    }
    private void coldRoundTrip(boolean lost) throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve(lost ? "lost" : "negative"), false, scenario(installed))) {
            Captured captured = capture(actual, installed.get(), lost);
            if (lost) assertInstanceOf(NativeActionPort.Unknown.class, captured.failure().original());
            else assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class, captured.failure().original()).nativeOk());
            byte[] ledger = actual.ledgerBytes(); long files = fileCount(actual.root);
            NativeOutcomeArchive cold = reopen(actual, captured);
            var expired = new AtomicReference<ActionPorts.OutcomeArchive>();
            cold.writer().locked(same -> cold.inSession(same, bound -> {
                expired.set(bound.withSession(same));
                assertEquals(captured.failure(), PlanningReadFailureCodec.load(captured.original(), bound));
                bound.withSession(same).verifyReadFailureOriginals(captured.failure());
                assertThrows(RuntimeException.class, () -> actual.archive.withSession(same));
                return null;
            }));
            assertEquals(captured.failure(), PlanningReadFailureCodec.load(captured.original(), cold));
            assertThrows(RuntimeException.class, () -> expired.get().verifyReadFailureOriginals(captured.failure()),
                    "a closed borrowed session cannot be revived for cold verification");
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(files, fileCount(actual.root));
            assertEquals(captured.readWrites(), actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void actualNegativeReadColdReopensOriginalGuardsAndSessionViewsWithoutWrites() throws Exception { coldRoundTrip(false); }
    @Test void actualResponseWaitUnknownColdReopensWithoutResubmittingRead() throws Exception { coldRoundTrip(true); }

    @Test void actualAncestorHeadReplaysWhileForeignDigestAndFutureHeadRefuse() throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("history"), false, scenario(installed))) {
            Captured captured = capture(actual, installed.get(), false);
            actual.coordinator.execute(actual.command("actual-next-action-for-ancestor"));
            assertTrue(actual.sequence() > captured.failure().headSequence());
            int actions = actual.nativeActionWrites(), reads = actual.nativeReadWrites(); byte[] ledger = actual.ledgerBytes();
            NativeOutcomeArchive cold = reopen(actual, captured);
            assertEquals(captured.failure(), PlanningReadFailureCodec.load(captured.original(), cold));
            for (boolean future : List.of(false, true)) {
                ObjectNode changed = (ObjectNode) StrictJson.parse(cold.loadMaterial(captured.original()).bytes());
                if (future) changed.put("head_sequence", Long.toString(actual.sequence() + 1));
                else changed.put("head_digest", captured.failure().headDigest().equals("f".repeat(64)) ? "e".repeat(64) : "f".repeat(64));
                ExactRef invalid = cold.preserveMaterial(new RawJson(StrictJson.canonical(changed)));
                assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.load(invalid, cold));
            }
            for (String field : List.of("original_ref", "prepared_ref")) {
                ExactRef canonical = field.equals("original_ref") ? captured.failure().originalRef() : captured.failure().preparedRef();
                Path alias = actual.root.resolve(field + "-same-bytes.json");
                Files.write(alias, Files.readAllBytes(Path.of(canonical.path())));
                ObjectNode changed = (ObjectNode) StrictJson.parse(cold.loadMaterial(captured.original()).bytes());
                changed.set(field, reference(alias).toJson());
                ExactRef invalid = cold.preserveMaterial(new RawJson(StrictJson.canonical(changed)));
                assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.load(invalid, cold),
                        "same bytes outside the immutable store cannot alias the canonical " + field);
            }
            assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(reads, actual.nativeReadWrites()); assertEquals(actions, actual.nativeActionWrites());
        }
    }
    private void damagedOriginal(Damage damage) throws Exception {
        var installed = new AtomicReference<ReadContract<RawJson>>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve(damage.name()), false, scenario(installed))) {
            Captured captured = capture(actual, installed.get(), false);
            NativeOutcomeArchive cold = reopen(actual, captured);
            ExactRef ref = damage == Damage.EXTERNAL_SOURCE ? captured.failure().request().source().sourceRef()
                    : captured.failure().after().binding().supportingEvidence().getFirst();
            Path original = Path.of(ref.path());
            assertTrue(original.toRealPath().startsWith(actual.root.toRealPath()));
            if (damage == Damage.EXTERNAL_SOURCE)
                assertFalse(original.toRealPath().startsWith(actual.root.resolve("artifacts").toRealPath()));
            byte[] ledger = actual.ledgerBytes();
            Files.writeString(original, "{\"actual_original_changed\":true}", StandardCharsets.UTF_8);
            byte[] changed = Files.readAllBytes(original); long files = fileCount(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.verifyReadFailureOriginals(captured.failure()));
            assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.load(captured.original(), actual.archive));
            assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.preserve(captured.failure(), actual.archive));
            assertThrows(RuntimeException.class, () -> cold.verifyReadFailureOriginals(captured.failure()));
            assertThrows(RuntimeException.class, () -> PlanningReadFailureCodec.load(captured.original(), cold));
            assertThrows(RuntimeException.class, () -> cold.writer().locked(same -> cold.inSession(same, bound -> {
                bound.verifyReadFailureOriginals(captured.failure()); return null;
            })));
            assertArrayEquals(changed, Files.readAllBytes(original)); assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(files, fileCount(actual.root)); assertEquals(captured.readWrites(), actual.nativeReadWrites());
            assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void changedAfterOriginalFailsHookCodecAndPreserveWithoutRepair() throws Exception { damagedOriginal(Damage.AFTER_ORIGINAL); }
    @Test void changedConfiguredExternalSourceFailsWriterPinWithoutMaterialAlias() throws Exception { damagedOriginal(Damage.EXTERNAL_SOURCE); }
    private static long fileCount(Path directory) throws IOException {
        try (var files = Files.walk(directory)) { return files.filter(Files::isRegularFile).count(); }
    }
}
