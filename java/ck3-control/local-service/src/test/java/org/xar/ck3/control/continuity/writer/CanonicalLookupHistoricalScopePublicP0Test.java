package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import static org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.CheckedArchiveRead;
import org.xar.ck3.control.application.action.ActionPorts.HistoricalReadLimits;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Public DATA lookup over physically retained records and a real writer Head.
 * A software anchor is installed before the final writer is opened. It grants
 * no Root admission, current observation, native permit or action authority.
 * No production optimization implementation or private oracle was read.
 */
final class CanonicalLookupHistoricalScopePublicP0Test {
    @TempDir Path temporary;
    private static final String MACHINE = "canonical-lookup-scope-public";
    private static final Instant AT = Instant.parse("2026-11-04T00:00:00Z");
    private static final HistoricalReadLimits OWN = new HistoricalReadLimits(16, 65_536, 36);
    private static final HistoricalReadLimits OUTER = new HistoricalReadLimits(1, 1, 4);
    private enum Scene { COMPLETE, BAD_SUFFIX, IO_BEFORE_BAD_SUFFIX, NULL_HEAD_BEFORE_IO, MISSING_HEAD }
    private enum Mode { PLAIN, OWNED, BORROWED }
    private record Outcome(List<Optional<ActionReceipt>> values, Throwable failure) { }
    @FunctionalInterface private interface Attempt { List<Optional<ActionReceipt>> run() throws IOException; }

    @Test void sameCanonicalLookupPreservesResultsHeadAndFirstSuffixFailureAcrossRealScopes() throws Exception {
        for (Scene scene : Scene.values()) {
            try (Fixture fixture = new Fixture(temporary.resolve(scene.name()), scene)) {
                fixture.writer.locked(same -> {
                    var original = same.head();
                    byte[] stateBytes = original.state().canonicalBytes();
                    Outcome plain = null;
                    for (Mode mode : Mode.values()) {
                        Outcome ioBasis = null;
                        if (scene == Scene.IO_BEFORE_BAD_SUFFIX) {
                            ioBasis = capture(() -> invoke(mode, fixture.archive, same, actual -> {
                                actual.loadRecord(fixture.middle);
                                return List.of();
                            }));
                            assertInstanceOf(UncheckedIOException.class, ioBasis.failure());
                        }
                        Outcome observed = capture(() -> invoke(mode, fixture.archive, same,
                                actual -> queries(same.head().state(), actual)));
                        if (mode == Mode.PLAIN) plain = observed;
                        switch (scene) {
                            case COMPLETE -> {
                                assertNull(observed.failure());
                                assertEquals(List.of(Optional.of(fixture.newest), Optional.of(fixture.other),
                                        Optional.empty(), Optional.empty()), observed.values());
                                assertArrayEquals(ActionCodec.encodeCommand(fixture.newest.command()),
                                        ActionCodec.encodeCommand(observed.values().getFirst().orElseThrow().command()));
                            }
                            case MISSING_HEAD -> {
                                assertNull(observed.failure());
                                assertEquals(List.of(Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty()),
                                        observed.values(), "missing head must not inspect unrelated missing originals");
                            }
                            case BAD_SUFFIX -> {
                                assertInstanceOf(RuntimeException.class, observed.failure());
                                assertEquals("action record chain sequence/machine drift", observed.failure().getMessage());
                            }
                            case NULL_HEAD_BEFORE_IO -> {
                                assertInstanceOf(RuntimeException.class, observed.failure());
                                assertEquals("action record head cannot silently change from missing to null",
                                        observed.failure().getMessage());
                            }
                            case IO_BEFORE_BAD_SUFFIX -> {
                                assertInstanceOf(UncheckedIOException.class, observed.failure());
                                assertEquals(failureChain(ioBasis.failure()), failureChain(observed.failure()),
                                        "lookup must retain this real archive's missing-middle I/O before its later bad suffix");
                            }
                        }
                        if (scene != Scene.IO_BEFORE_BAD_SUFFIX && mode != Mode.PLAIN) {
                            assertEquals(plain.values(), observed.values());
                            assertEquals(failureChain(plain.failure()), failureChain(observed.failure()));
                        }
                        assertArrayEquals(stateBytes, same.head().state().canonicalBytes());
                        assertEquals(original.digest(), same.head().digest());
                        assertEquals(original.state().sequence(), same.head().state().sequence());
                    }
                    return null;
                });
            }
        }
    }

    private static List<Optional<ActionReceipt>> queries(ContinuityState state, OutcomeArchive archive) {
        return List.of(ContinuityActionJournal.lookup(state, "selected", archive),
                ContinuityActionJournal.lookup(state, "other", archive),
                ContinuityActionJournal.lookup(state, "absent", archive),
                ContinuityActionJournal.lookup(state, null, archive));
    }

    private static <T> T invoke(Mode mode, NativeOutcomeArchive owner, ContinuityStorePort.Session same,
            CheckedArchiveRead<T> operation) throws IOException {
        return switch (mode) {
            case PLAIN -> operation.read(owner.withSession(same));
            case OWNED -> owner.inHistoricalReadScopeOrBorrow(same, OWN, operation);
            case BORROWED -> owner.inHistoricalReadScope(same, OUTER, outer -> {
                T result = owner.inHistoricalReadScopeOrBorrow(same, OWN, operation);
                assertEquals(result, operation.read(outer), "borrowed execution must leave the original outer scope usable");
                return result;
            });
        };
    }

    private static Outcome capture(Attempt operation) {
        try { return new Outcome(operation.run(), null); }
        catch (IOException | RuntimeException failure) { return new Outcome(null, failure); }
    }

    private static List<String> failureChain(Throwable failure) {
        var result = new ArrayList<String>();
        for (Throwable current = failure; current != null; current = current.getCause()) {
            assertTrue(result.size() < 16, "finite original exception chain required");
            result.add(current.getClass().getName() + ":" + current.getMessage());
        }
        return List.copyOf(result);
    }

    private static final class Fixture implements AutoCloseable {
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        final StorageWriteGuardTestSupport storage;
        final ActionReceipt newest;
        final ActionReceipt other;
        final ExactRef middle;

        Fixture(Path root, Scene scene) throws IOException {
            Files.createDirectory(root);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json");
            Path setupAnchor = root.resolve("setup-anchor.json");
            byte[] seed = ContinuityJson.canonical(state());
            Files.write(snapshot, seed, StandardOpenOption.CREATE_NEW);
            Files.write(setupAnchor, seed, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path artifacts = Files.createDirectory(root.resolve("artifacts"));
            Path sourcePath = root.resolve("source.txt");
            Files.writeString(sourcePath, "finite public canonical lookup DATA fixture", StandardOpenOption.CREATE_NEW);
            ExactRef source = LedgerFiles.read(sourcePath, 65_536).pin().reference();
            Layout setupLayout = new Layout(snapshot, LedgerFiles.read(setupAnchor, 65_536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(setupLayout);
            try {
                ImmutableArtifactStore store = new ImmutableArtifactStore(
                        new ImmutableArtifactStore.Config(artifacts, setupLayout.lock(), 8 * 1024 * 1024), storage);
                ContinuityWriter setupWriter = writer(setupLayout, source, store, storage);
                NativeOutcomeArchive setupArchive = new NativeOutcomeArchive(store, setupWriter);
                newest = receipt(6, "selected", source);
                other = receipt(4, "other", source);
                boolean badSuffix = scene != Scene.COMPLETE;
                ActionReceipt oldest = receipt(badSuffix ? 7 : 2, "selected", source);
                List<ExactRef> chain = setupWriter.locked(same -> setupArchive.inSession(same, actual -> {
                    ExactRef tail = actual.preserveRecord(new ActionRecord(oldest, Optional.empty()));
                    ExactRef middleRecord = actual.preserveRecord(new ActionRecord(other, Optional.of(tail)));
                    ExactRef head = actual.preserveRecord(new ActionRecord(newest, Optional.of(middleRecord)));
                    return List.of(head, middleRecord);
                }));
                middle = chain.getLast();
                // Controlled loss happens during setup, with no active writer or historical callback.
                if (scene == Scene.IO_BEFORE_BAD_SUFFIX || scene == Scene.NULL_HEAD_BEFORE_IO || scene == Scene.MISSING_HEAD)
                    Files.delete(Path.of(middle.path()));
                ObjectNode canonical = state();
                if (scene == Scene.NULL_HEAD_BEFORE_IO) canonical.putNull(ContinuityActionJournal.STATE_FIELD);
                else if (scene != Scene.MISSING_HEAD) canonical.set(ContinuityActionJournal.STATE_FIELD, chain.getFirst().toJson());
                byte[] finalized = ContinuityJson.canonical(canonical);
                Path anchor = root.resolve("anchor.json");
                StorageWriteGuardTestSupport.atomic(anchor, finalized, false);
                StorageWriteGuardTestSupport.atomic(snapshot, finalized, true);
                Layout layout = new Layout(snapshot, LedgerFiles.read(anchor, 65_536).pin().reference(), MACHINE);
                // A fresh actual reader opens the finalized software anchor. No setup Session escapes.
                writer = writer(layout, source, store, storage);
                archive = new NativeOutcomeArchive(store, writer);
            } catch (IOException | RuntimeException | Error failure) {
                try { storage.close(); }
                catch (IOException closing) { if (closing != failure) failure.addSuppressed(closing); }
                throw failure;
            }
        }

        @Override public void close() throws IOException { storage.close(); }
    }

    private static ContinuityWriter writer(Layout layout, ExactRef source, ImmutableArtifactStore store,
            StorageWriteGuard storage) throws IOException {
        return new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before, Request request) {
                throw new AssertionError("lookup fixture must not preview any canonical transition");
            }
            @Override public ContinuityState reduce(ContinuityState before, Request request) {
                throw new AssertionError("lookup fixture must not commit any canonical transition");
            }
        }, Clock.fixed(AT, ZoneOffset.UTC),
                new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
    }

    private static ActionReceipt receipt(long sequence, String id, ExactRef actualSource) {
        ObjectNode gameData = StrictJson.object().put("pid", 314).put("creation_filetime", "42");
        GameGeneration game = GameGeneration.fromJson(gameData);
        Frame frame = new Frame(BigInteger.valueOf(7), BigInteger.valueOf(11), BigInteger.valueOf(1000));
        ProposalFrame proposed = new ProposalFrame(frame, "lookup-software-snapshot", BigInteger.ONE, "lookup-software-episode");
        ObservationIdentity before = new ObservationIdentity(MACHINE, game, proposed, 1);
        G2Source source = new G2Source(MACHINE, AT.toString(), "canonical-lookup-public", actualSource);
        ExpectedPostcondition expected = new ExpectedPostcondition(1, before, source, "canonical.lookup.fixture/v1",
                List.of(new ExpectedBoolean(new FieldKey("fixture_seen"), true)));
        ActionCommand command = new ActionCommand(id, before, source, "canonical-lookup-session",
                new OperationKey("fixture.lookup"), new OpportunityJson.Obj(Map.of()), expected,
                new Claims(Set.of(), Set.of(), Set.of(), Set.of()), Instant.parse("2026-12-01T00:00:00Z"));
        return new ActionReceipt(1, sequence, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
    }

    private static ObjectNode state() {
        ObjectNode row = StrictJson.object();
        row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 6); row.put("window_id", 1); row.put("status", "running");
        row.put("target_days", 10958); row.put("target_years", 30); row.put("calendar_year_days", 365.25);
        row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 314).put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
        row.put("NEXT", 11559);
        return row;
    }
}
