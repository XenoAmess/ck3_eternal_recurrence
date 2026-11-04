package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Public Publisher preflight failures under a real writer Session; no historical proof is minted. */
public final class PublisherHistoricalPreflightP0Test {
    private static final String MACHINE = "upper109-public-preflight-test";
    private static final int INPUT_LIMIT = 65_536;
    @TempDir Path temporary;

    @Test
    void legacyEntryBindsTheRealSessionBeforeNullActionFailure() throws IOException {
        assertNullActionAfterRealBinding("legacy-null", DriverReadHistoryPublisher::new);
    }

    @Test
    void explicitScopeEntryRejectsNullActionBeforeCallingTheScope() throws IOException {
        AtomicInteger scopeCalls = new AtomicInteger();
        assertNullActionAfterRealBinding("explicit-null", explicitScopeMustNotRun(scopeCalls));
        assertEquals(0, scopeCalls.get(), "invalid action must fail before explicit scope entry");
    }

    @Test
    void legacyBindingFailureStopsBeforeActionValidation() throws IOException {
        assertBindingFailureStopsTheEntry("legacy-bind-failure", DriverReadHistoryPublisher::new);
    }

    @Test
    void explicitScopeBindingFailureStopsBeforeActionValidationOrScope() throws IOException {
        AtomicInteger scopeCalls = new AtomicInteger();
        assertBindingFailureStopsTheEntry("explicit-bind-failure", explicitScopeMustNotRun(scopeCalls));
        assertEquals(0, scopeCalls.get(), "failed original binding must not enter the explicit scope");
    }

    private void assertNullActionAfterRealBinding(String directory, PublisherFactory create) throws IOException {
        try (Fixture fixture = new Fixture(temporary.resolve(directory))) {
            fixture.writer.locked(same -> {
                fixture.writer.requireSession(same);
                assertSame(same, fixture.writer.borrowedSession());
                Head before = same.head();
                List<String> calls = new ArrayList<>();
                OutcomeArchive observed = archiveBinding(fixture.archive, same, calls, null);
                DriverReadHistoryPublisher publisher = create.create(
                        unusedAssembler(), observed, RootReadContractCatalog.staticOnly(List.of()),
                        List.of(fixture.source));

                // The finite physical refs are not interpreted: the original null action is rejected first.
                assertThrows(NullPointerException.class, () -> publisher.requireHistoricalUnresolvedHistoryExtension(
                        same, null, fixture.source, fixture.source, before));

                assertEquals(List.of("withSession-enter", "withSession-bound"), calls);
                fixture.writer.requireSession(same);
                assertSame(same, fixture.writer.borrowedSession());
                assertEquals(before.digest(), same.head().digest());
                return null;
            });
        }
    }

    private void assertBindingFailureStopsTheEntry(String directory, PublisherFactory create) throws IOException {
        try (Fixture fixture = new Fixture(temporary.resolve(directory))) {
            fixture.writer.locked(same -> {
                fixture.writer.requireSession(same);
                Head before = same.head();
                List<String> calls = new ArrayList<>();
                IllegalStateException original = new IllegalStateException("owned withSession failure");
                OutcomeArchive observed = archiveBinding(fixture.archive, same, calls, original);
                DriverReadHistoryPublisher publisher = create.create(
                        unusedAssembler(), observed, RootReadContractCatalog.staticOnly(List.of()),
                        List.of(fixture.source));

                IllegalStateException actual = assertThrows(IllegalStateException.class,
                        () -> publisher.requireHistoricalUnresolvedHistoryExtension(
                                same, null, fixture.source, fixture.source, before));

                assertSame(original, actual, "the original binding failure must survive unchanged");
                assertEquals(List.of("withSession-enter"), calls);
                fixture.writer.requireSession(same);
                assertSame(same, fixture.writer.borrowedSession());
                assertEquals(before.digest(), same.head().digest());
                return null;
            });
        }
    }

    private static PublisherFactory explicitScopeMustNotRun(AtomicInteger calls) {
        return (authority, archive, catalog, sources) -> new DriverReadHistoryPublisher(
                authority, archive, catalog, sources, (same, operation) -> {
                    calls.incrementAndGet();
                    throw new AssertionError("preflight failure must not invoke explicit historical scope");
                });
    }

    /** A public adapter observes the real archive binding; it does not fabricate a Session or issuer. */
    private static OutcomeArchive archiveBinding(NativeOutcomeArchive actual, ContinuityStorePort.Session expected,
            List<String> calls, IllegalStateException bindingFailure) {
        return (OutcomeArchive) Proxy.newProxyInstance(
                OutcomeArchive.class.getClassLoader(), new Class<?>[] {OutcomeArchive.class},
                (proxy, method, arguments) -> {
                    if (!method.getName().equals("withSession") || method.getParameterCount() != 1) {
                        throw new AssertionError("unexpected archive call before action validation: " + method.getName());
                    }
                    calls.add("withSession-enter");
                    assertSame(expected, arguments[0]);
                    if (bindingFailure != null) throw bindingFailure;
                    OutcomeArchive bound = actual.withSession(expected);
                    calls.add("withSession-bound");
                    return bound;
                });
    }

    private static DriverStateAssembler unusedAssembler() {
        ActionJournal noJournalUse = new ActionJournal() {
            @Override public <T> T locked(Function<LockedJournal, T> operation) {
                throw new AssertionError("historical preflight must not read the action journal");
            }
            @Override public <T> T locked(ContinuityStorePort.Session same, Function<LockedJournal, T> operation) {
                throw new AssertionError("historical preflight must not borrow the action journal");
            }
        };
        DriverFactsRepository unavailable = new DriverFactsRepository(
                new DriverSnapshotFacts.Unavailable(List.of("construct-only preflight fixture; no Known facts")));
        DriverObservationFacts.Reader noObservation = actual -> {
            throw new AssertionError("historical preflight must not observe Native or Driver facts");
        };
        return new DriverStateAssembler(new ActionSnapshotReader(noJournalUse), unavailable, noObservation);
    }

    @FunctionalInterface
    private interface PublisherFactory {
        DriverReadHistoryPublisher create(DriverStateAssembler authority, OutcomeArchive archive,
                RootReadContractCatalog catalog, List<ExactRef> sources);
    }

    private static final class Fixture implements AutoCloseable {
        final ExactRef source;
        final StorageWriteGuardTestSupport storage;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;

        Fixture(Path root) throws IOException {
            Files.createDirectory(root);
            byte[] initial = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path artifacts = Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "owned public Publisher preflight fixture",
                    StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), INPUT_LIMIT).pin().reference();
            Layout layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), INPUT_LIMIT).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            try {
                ImmutableArtifactStore store = new ImmutableArtifactStore(
                        new ImmutableArtifactStore.Config(artifacts, layout.lock(), 8 * 1024 * 1024), storage);
                writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                    @Override public String revalidate(ContinuityState before, Request request) {
                        throw new AssertionError("preflight fixture must not preview a transition");
                    }
                    @Override public ContinuityState reduce(ContinuityState before, Request request) {
                        throw new AssertionError("preflight fixture must not commit a transition");
                    }
                }, Clock.fixed(Instant.parse("2026-11-03T00:00:00Z"), ZoneOffset.UTC),
                        new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
                archive = new NativeOutcomeArchive(store, writer);
            } catch (IOException | RuntimeException | Error failure) {
                try { storage.close(); }
                catch (IOException closing) { if (closing != failure) failure.addSuppressed(closing); }
                throw failure;
            }
        }

        @Override public void close() throws IOException { storage.close(); }
    }

    /** Existing finite software continuity shape; no live Game observation or Root admission is claimed. */
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object();
        row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running");
        row.put("target_days", 10958); row.put("target_years", 30); row.put("calendar_year_days", 365.25);
        row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
        row.put("NEXT", 11559);
        return row;
    }
}
