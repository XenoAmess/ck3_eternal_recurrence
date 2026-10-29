package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual canonical writer/archive/FileID boundary. These fixtures mint no private Root Original or native adoption. */
final class RootActivitySavedOriginalGuardTest {
    @TempDir Path root;

    @Test void historicalMemberReadPreservesCurrentPendingAndPublishesNothing() throws Exception {
        try (Fixture fixture = new Fixture(root)) {
        var empty = new FeastDomainRuntime.Ledger(Optional.empty(), Optional.empty());
        var saved = fixture.publish("saved", empty);
        var pending = new FeastDomainRuntime.Pending("original-episode", fixture.sources.getFirst(), "a".repeat(64));
        var later = fixture.publish("later", new FeastDomainRuntime.Ledger(Optional.of(pending), Optional.empty()));
        fixture.writer.locked(same -> {
            var original = RootActivitySavedOriginalGuard.readSavedBody(same, saved.head(), fixture.sources);
            assertEquals(empty, original.ledger());
            original.requireUnchanged(same);
            var current = RootActivitySavedOriginalGuard.readSavedBody(same, later.head(), fixture.sources);
            assertEquals(pending, current.ledger().pending().orElseThrow());
            assertEquals(2, same.head().state().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(3)));
        }
    }

    @Test void identicalBytesAtNewPhysicalIdentityCannotReplaceTheSavedMember() throws Exception {
        try (Fixture fixture = new Fixture(root)) {
        var saved = fixture.publish("saved", new FeastDomainRuntime.Ledger(Optional.empty(), Optional.empty()));
        var member = DomainBodies.reference(saved.head(), DomainBodies.Slot.FEAST).orElseThrow();
        byte[] unchanged = Files.readAllBytes(Path.of(member.payload().path()));
        Path replacement = root.resolve("same-content-new-file.json");
        Files.write(replacement, unchanged);
        Files.move(replacement, Path.of(member.payload().path()), StandardCopyOption.REPLACE_EXISTING);
        fixture.writer.locked(same -> {
            assertThrows(RuntimeException.class, () ->
                    RootActivitySavedOriginalGuard.readSavedBody(same, saved.head(), fixture.sources));
            return null;
        });
        assertArrayEquals(unchanged, Files.readAllBytes(Path.of(member.payload().path())));
        assertFalse(Files.exists(fixture.layout.event(2)));
        }
    }

    @Test void missingMemberAndForgedHeadCannotInitializeWhileProducerMetadataIsOnlyTrace() throws Exception {
        try (Fixture fixture = new Fixture(root)) {
        var saved = fixture.publish("saved", new FeastDomainRuntime.Ledger(Optional.empty(), Optional.empty()));
        Path other = root.resolve("other-producer.txt"); Files.writeString(other, "another original source");
        fixture.writer.locked(same -> {
            assertThrows(IOException.class, () ->
                    RootActivitySavedOriginalGuard.readSavedBody(same, fixture.anchor, fixture.sources));
            var forged = saved.head().toJson(); forged.put("manual_repair_count", 99);
            assertThrows(IOException.class, () ->
                    RootActivitySavedOriginalGuard.readSavedBody(same,
                            ContinuityState.fromJson(forged, Fixture.MACHINE), fixture.sources));
            var preserved = RootActivitySavedOriginalGuard.readSavedBody(same, saved.head(), List.of(Fixture.ref(other)));
            assertEquals(DomainBodies.reference(saved.head(), DomainBodies.Slot.FEAST).orElseThrow(), preserved.reference());
            assertEquals(new FeastDomainRuntime.Ledger(Optional.empty(), Optional.empty()), preserved.ledger());
            preserved.requireUnchanged(same);
            assertEquals(1, same.head().state().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(2)));
        }
    }

    @Test void pendingUnknownRoundTripsWithoutCurrentCodeTraceOrNewPublication() throws Exception {
        try (Fixture fixture = new Fixture(root)) {
            var pending = new FeastDomainRuntime.Pending("original-episode", fixture.sources.getFirst(), "a".repeat(64));
            var ledger = new FeastDomainRuntime.Ledger(Optional.of(pending), Optional.empty());
            byte[] original = FeastDomainRuntime.encode(ledger);
            var saved = fixture.publish("saved-unknown", ledger);
            var member = DomainBodies.reference(saved.head(), DomainBodies.Slot.FEAST).orElseThrow();
            Path different = root.resolve("unused-producer-trace.txt");
            Files.writeString(different, "current code metadata");
            ExactRef differentTrace = Fixture.ref(different);
            ExactRef missingTrace = new ExactRef(root.resolve("missing-producer-trace.java").toAbsolutePath().toString(), 1, "b".repeat(64));
            fixture.writer.locked(same -> {
                var head = same.head();var persisted = same.persistedHead();
                for (var trace : List.<List<ExactRef>>of(List.of(), List.of(differentTrace), List.of(missingTrace))) {
                    var retained = RootActivitySavedOriginalGuard.readSavedBody(same, saved.head(), trace);
                    assertEquals(member, retained.reference());
                    assertEquals(ledger, retained.ledger());
                    assertArrayEquals(original, FeastDomainRuntime.encode(retained.ledger()));
                    assertEquals(RestoredFeastOriginal.Disposition.PENDING, RestoredFeastOriginal.classify(
                            retained.ledger(), org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial.Kind.ORDINARY));
                    retained.requireUnchanged(same);
                    assertEquals(head.digest(), same.head().digest());
                    assertEquals(persisted, same.persistedHead());
                }
                var retained = RootActivitySavedOriginalGuard.readSavedBody(same, saved.head(), List.of(differentTrace));
                Files.writeString(different, "changed code metadata");
                retained.requireUnchanged(same);
                assertEquals(head.digest(), same.head().digest());
                assertEquals(persisted, same.persistedHead());
                return null;
            });
            assertArrayEquals(original, Files.readAllBytes(Path.of(member.payload().path())));
            assertFalse(Files.exists(fixture.layout.event(2)));
        }
    }

    private static final class Fixture implements AutoCloseable {
        static final String MACHINE = "activity-saved-member-store-test-machine";
        final Layout layout;
        final StorageWriteGuardTestSupport storage;
        final ContinuityWriter writer;
        final List<ExactRef> sources;
        final ContinuityState anchor;

        Fixture(Path root) throws IOException {
            assertTrue(System.getProperty("os.name").startsWith("Windows"),
                    "actual Windows ledger/FileID boundary is required; not skipped");
            Files.createDirectories(root);
            var state = StrictJson.object();
            state.put("schema", "root.ck3.continuity-window/v1"); state.put("machine_id", MACHINE);
            state.put("sequence", 0); state.put("window_id", 1); state.put("status", "running");
            state.put("target_days", 10958); state.put("target_years", 30); state.put("calendar_year_days", 365.25);
            state.put("start_date_raw", 1000); state.put("target_date_raw", 1000 + 10958 * 24);
            state.put("last_settled_date_raw", 1000); state.put("last_settled_cycles", 1);
            state.put("manual_repair_count", 1); state.put("automatic_recovery_count", 0);
            state.put("binding_lineage_count", 0);
            var game = state.putObject("game_binding"); game.put("pid", 123);
            game.put("creation_date", "2026-10-23T01:00:00Z");
            state.putNull("latest_binding");
            var pending = state.putObject("pending_cycle"); pending.put("stage", "auto_unsettled");
            pending.put("auto_sequence", 1); state.put("NEXT", 2);
            anchor = ContinuityState.fromJson(state, MACHINE);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial = root.resolve("anchor.json");
            Files.write(snapshot, ContinuityJson.canonical(state)); Files.write(initial, ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source = root.resolve("actual-fixture-producer.txt");
            Files.writeString(source, "actual FEAST canonical member store boundary fixture");
            sources = List.of(ref(source)); layout = new Layout(snapshot, ref(initial), MACHINE);
            Path archive = root.resolve("archive"); Files.createDirectory(archive);
            storage = StorageWriteGuardTestSupport.create(layout);
            try {
                var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive, layout.lock(), 1_048_576), storage);
                var registration = new DomainBodies.Registration(DomainBodies.Slot.FEAST, FeastDomainRuntime.SCHEMA,
                        1_048_576, sources, (head, previous, request, body) -> {
                            FeastDomainRuntime.decode(body);
                            StrictJson.require(request.producerInput().length > 0, "actual fixture producer input required");
                            return ActionCodec.sha256(body);
                        });
                writer = new ContinuityWriter(layout, sources, new TransitionAuthority() {
                    @Override public String revalidate(ContinuityState head, Request input) {
                        throw new AssertionError("domain imports use the actual store verifier");
                    }
                    @Override public ContinuityState reduce(ContinuityState head, Request input) {
                        throw new AssertionError("domain imports use the actual store reducer");
                    }
                }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(store), Optional.empty()), storage);
            } catch (IOException | RuntimeException | Error failure) {
                try { storage.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
                throw failure;
            }
        }

        @Override public void close() throws IOException { storage.close(); }

        Receipt publish(String identity, FeastDomainRuntime.Ledger body) throws IOException {
            Path original = layout.snapshot().getParent().resolve(identity + ".json");
            Files.write(original, FeastDomainRuntime.encode(body));
            var request = new DomainBodies.ImportRequest(DomainBodies.Slot.FEAST, FeastDomainRuntime.SCHEMA,
                    ref(original), StrictJson.canonical(StrictJson.object().put("fixture_actual_producer", identity)),
                    List.of(), identity);
            return writer.commitImport(writer.previewImport(request));
        }
        static ExactRef ref(Path actual) throws IOException {
            byte[] raw = Files.readAllBytes(actual);
            return new ExactRef(actual.toAbsolutePath().toString(), raw.length, ActionCodec.sha256(raw));
        }
    }
}

