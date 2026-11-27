package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.family.FamilyDomainSource;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.planning.family.FamilyOrdinaryRestoreMigration;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Real Writer pins and domain receipts. The software source has no Native or restore authority. */
final class RootFamilyCommittedRestoreWriterTest {
    private static final String MACHINE = "committed-family-receipt-fixture";
    private static final List<Slot> SLOTS = List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE);
    private static final Episode EPISODE = new Episode("retained-family-episode", BigInteger.valueOf(202));
    private static final SessionIdentity SAVED = owner(101, "saved"), DEPARTED = owner(102, "departed"),
            SUCCESSOR = owner(103, "same-successor-after-reconnect");

    @TempDir Path root;

    @Test void actualIndependentSavedBodiesAndDepartedUnknownSurviveStableReceiptReadback() throws IOException {
        var old = fixture(root.resolve("saved"));
        var target = fixture(root.resolve("target"));
        var oldWriter = old.writer();
        var targetWriter = target.writer();
        for (Slot slot : SLOTS) {
            importOriginal(old, oldWriter, slot, body(slot, "saved-older-" + slot), "saved-" + slot);
            importOriginal(target, targetWriter, slot, body(slot, "departed-unknown-" + slot), "departed-" + slot);
        }
        var oldSaved = oldWriter.locked(same -> same.head());
        var originalAttachment = targetWriter.locked(same -> same.head());
        var prior = new EnumMap<Slot, DomainBodies.BodyRef>(Slot.class);
        var issued = new EnumMap<Slot, DomainBodies.ImportRequest>(Slot.class);
        var outputs = new EnumMap<Slot, DomainBodies.BodyRef>(Slot.class);
        var material = write(root.resolve("saved-material.json"), StrictJson.canonical(StrictJson.object().put("fixture", "independent")));
        var basis = write(root.resolve("stable-attachment.json"), originalAttachment.state().canonicalBytes());

        try (var guard = StorageWriteGuard.noWrites()) {
            var retainedOld = old.reader(guard);
            targetWriter.locked(same -> {
                var saved = retainedOld.readOnlyFrom(same, independent -> {
                    var head = independent.requireHistoricalState(oldSaved.state().sequence(), oldSaved.digest());
                    var result = new EnumMap<Slot, DomainBodies.Available>(Slot.class);
                    for (Slot slot : SLOTS) {
                        var found = assertInstanceOf(DomainBodies.Available.class, independent.readDomain(slot));
                        assertEquals(DomainBodies.reference(head, slot).orElseThrow(), found.reference());
                        result.put(slot, found);
                    }
                    return result;
                });
                for (Slot slot : SLOTS) {
                    var previous = assertInstanceOf(DomainBodies.Available.class, same.readDomain(slot));
                    assertEquals(DomainBodies.reference(originalAttachment.state(), slot).orElseThrow(), previous.reference());
                    var transition = new FamilyOrdinaryRestoreMigration.Transition(SAVED, DEPARTED, SUCCESSOR, EPISODE, material,
                            basis, saved.get(slot).reference().payload(), previous.reference().payload());
                    byte[] output = FamilyOrdinaryRestoreMigration.derive(slot, saved.get(slot).canonicalBody(), previous.canonicalBody(), transition);
                    var decoded = StrictJson.parse(output);
                    assertEquals("departed-unknown-" + slot, decoded.path("pending").path("java_action_id").textValue());
                    var entry = decoded.path(FamilyOrdinaryRestoreMigration.HISTORY).get(0);
                    assertFalse(entry.path("ck3_command_submitted").booleanValue());
                    assertFalse(entry.path("relation_completion_credit").booleanValue());

                    var ref = target.archive().publish(output, ContinuityJson.DOMAIN_MAX_BYTES).reference();
                    var request = RootFamilyOrdinaryRestoreDomains.request(slot, saved.get(slot).reference(),
                            previous.reference(), transition, List.of(material, basis), ref);
                    assertEquals("family-ordinary-restore-" + slot + "-" + basis.sha256() + "-" + transition.previousBody().sha256(),
                            request.evidenceId());
                    same.commitImport(same.previewImport(request));
                    prior.put(slot, previous.reference());
                    issued.put(slot, request);
                    outputs.put(slot, assertInstanceOf(DomainBodies.Available.class, same.readDomain(slot)).reference());
                }
                return null;
            });
        }
        assertEquals(oldSaved.digest(), oldWriter.locked(same -> same.head()).digest());
        var restarted = target.writer();
        restarted.locked(same -> {
            var before = same.head();
            same.requireDomainImportContinuation(originalAttachment.state().sequence(), originalAttachment.digest());
            for (Slot slot : SLOTS) {
                var request = issued.get(slot);
                RootFamilyOrdinaryRestoreDomains.requireRecordedImport(same, target.layout(), originalAttachment.state().sequence(),
                        request, prior.get(slot), outputs.get(slot));
                var wrongIdentity = new DomainBodies.ImportRequest(slot, request.contractSchema(), request.originalBody(),
                        request.producerInput(), request.evidence(), "foreign-connection-specific-id");
                assertThrows(IOException.class, () -> RootFamilyOrdinaryRestoreDomains.requireRecordedImport(same, target.layout(),
                        originalAttachment.state().sequence(), wrongIdentity, prior.get(slot), outputs.get(slot)));
                var missingOriginals = new DomainBodies.ImportRequest(slot, request.contractSchema(), request.originalBody(),
                        request.producerInput(), List.of(basis), request.evidenceId());
                assertThrows(IllegalArgumentException.class, () -> RootFamilyOrdinaryRestoreDomains.requireRecordedImport(same, target.layout(),
                        originalAttachment.state().sequence(), missingOriginals, prior.get(slot), outputs.get(slot)));
            }
            assertEquals(before.digest(), same.head().digest());
            assertEquals(originalAttachment.state().settledCycles(), before.state().settledCycles());
            assertEquals(originalAttachment.state().settledDateRaw(), before.state().settledDateRaw());
            return null;
        });
    }

    private record Fixture(WriterContracts.Layout layout, ExactRef source, ImmutableArtifactStore.Config config,
            StorageWriteGuard guard, ImmutableArtifactStore archive, List<DomainBodies.Registration> registrations) {
        ContinuityWriter writer() throws IOException {
            return new ContinuityWriter(layout, List.of(source), NEVER, Clock.systemUTC(),
                    new ContinuityWriter.Extensions(registrations, Optional.of(archive), Optional.empty()), guard);
        }
        ContinuityWriter reader(StorageWriteGuard noWrites) throws IOException {
            var readOnly = ImmutableArtifactStore.readOnlyExisting(config, noWrites);
            return ContinuityWriter.readOnlyExisting(layout, List.of(source), NEVER, Clock.systemUTC(),
                    new ContinuityWriter.Extensions(registrations, Optional.of(readOnly), Optional.empty()), noWrites);
        }
    }

    private static Fixture fixture(Path directory) throws IOException {
        Files.createDirectory(directory);
        Path lock = Files.createFile(directory.resolve("continuity.lock"));
        Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path artifacts = Files.createDirectory(directory.resolve("artifacts"));
        var state = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE).put("sequence", 0)
                .put("window_id", 1).put("status", "running").put("target_days", 365).put("start_date_raw", 1008)
                .put("target_date_raw", 9768).put("last_settled_date_raw", 1008).put("last_settled_cycles", 1);
        byte[] original = ContinuityJson.canonical(state);
        var snapshot = Files.write(directory.resolve("continuity.json"), original);
        var anchor = write(directory.resolve("anchor.json"), original);
        var trustedSource = write(directory.resolve("source.json"), new byte[] {1});
        var layout = new WriterContracts.Layout(snapshot, anchor, MACHINE);
        var guard = StorageWriteGuardTestSupport.create(layout);
        var config = new ImmutableArtifactStore.Config(artifacts, lock, 1_048_576);
        var store = new ImmutableArtifactStore(config, guard);
        var domains = SLOTS.stream().map(slot -> new DomainBodies.Registration(slot, FamilyDomainSource.schema(slot),
                ContinuityJson.DOMAIN_MAX_BYTES, List.of(trustedSource), (before, previous, request, body) -> {
                    FamilyDomainSource.validate(slot, body);
                    return ActionCodec.sha256(request.producerInput());
                })).toList();
        return new Fixture(layout, trustedSource, config, guard, store, domains);
    }

    private static void importOriginal(Fixture fixture, ContinuityWriter writer, Slot slot, byte[] original, String identity) throws IOException {
        writer.locked(same -> {
            ExactRef body = fixture.archive().publish(original, ContinuityJson.DOMAIN_MAX_BYTES).reference();
            var request = new DomainBodies.ImportRequest(slot, FamilyDomainSource.schema(slot), body,
                    ContinuityJson.canonical(StrictJson.object().put("fixture", identity)), List.of(fixture.source()), identity);
            same.commitImport(same.previewImport(request));
            return null;
        });
    }

    private static byte[] body(Slot slot, String actionId) {
        var result = StrictJson.object().put("schema", FamilyDomainSource.schema(slot));
        result.putObject("pending").put("episode_run_id", EPISODE.runId()).put("played_character_id", EPISODE.player())
                .put("heir_character_id", 11).put("candidate_character_id", 12).put("source_bridge_pid", 101)
                .put("source_bridge_creation_date", "saved-bridge").put("pre_native_revision", 5)
                .put("status", "receipt_pending").put("java_action_id", actionId);
        result.putNull("resolved");
        return ContinuityJson.canonical(result);
    }

    private static ExactRef write(Path path, byte[] bytes) throws IOException {
        Files.write(path, bytes);
        return new ExactRef(path.toString(), bytes.length, ActionCodec.sha256(bytes));
    }

    private static SessionIdentity owner(long pid, String session) {
        return new SessionIdentity(MACHINE, new GameGeneration(pid, new PythonOnlyUInt64(BigInteger.valueOf(pid))), session);
    }

    private static final WriterContracts.TransitionAuthority NEVER = new WriterContracts.TransitionAuthority() {
        @Override public String revalidate(ContinuityState before, WriterContracts.Request request) { throw new AssertionError("unexpected ordinary event"); }
        @Override public ContinuityState reduce(ContinuityState before, WriterContracts.Request request) { throw new AssertionError("unexpected ordinary event"); }
    };
}
