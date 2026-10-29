package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual typed bootstrap publication -> original-file import -> ledger and Family consumer.
 * The fixture uses native file identities and the existing finite test storage guard; it grants no Game/InitialEpisodeProof.
 * Host must use its already admitted test temporary root. */
final class RootFamilyInitialDataImportTest {
    @TempDir Path temporary;
    private static final List<Slot> SLOTS = List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE);
    private record Fixture(Path root, String machine, ContinuityWriter writer, NativeOutcomeArchive archive,
            RootFamilyOriginalDomains domains, Map<Slot, ExactRef> originals, Map<Slot, ExactRef> freshOriginals, ExactRef producer,
            StorageWriteGuardTestSupport storage) implements AutoCloseable {
        @Override public void close() throws IOException { storage.close(); }
    }
    private static ExactRef reference(Path path) throws IOException {
        var actual = SharedSourceFiles.observe(path).source();
        return new ExactRef(actual.path(), actual.bytes(), actual.sha256());
    }
    private static byte[] initialState(String machine) {
        var value = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", machine)
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("target_days", 10958).put("target_years", 30)
                .put("calendar_year_days", 365.25).put("start_date_raw", 1000).put("target_date_raw", 263992)
                .put("last_settled_date_raw", 1000).put("last_settled_cycles", 1).put("manual_repair_count", 1)
                .put("automatic_recovery_count", 0).put("binding_lineage_count", 0);
        value.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-25T20:00:00Z");
        value.putNull("latest_binding");
        value.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
        value.put("NEXT", 11559);
        return ContinuityJson.canonical(value);
    }
    private Fixture fixture(FamilyInitialData.Documents initial, boolean retainedPending) throws IOException {
        Path root = Files.createDirectory(temporary.resolve("writer"));
        String machine = WindowsJobProcess.currentMachineId();
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json"),
                lock = root.resolve("ROOT-CONTINUITY-WINDOW.lock");
        byte[] state = initialState(machine);
        Files.write(snapshot, state); Files.write(anchor, state); Files.createFile(lock);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source = root.resolve("family-data-software-producer.txt");
        Files.writeString(source, "software fixture source for the actual original-domain importer");
        ExactRef producer = reference(source);
        var immutableFiles = new NativeCheckpointFiles();
        var originals = new EnumMap<Slot, ExactRef>(Slot.class);
        var freshOriginals = new EnumMap<Slot, ExactRef>(Slot.class);
        // Actual first publication: typed request serde -> existing bootstrap Guard -> sole publisher.
        // These exact refs are also consumed by Definitions.readData before the same writer imports them.
        RootFamilyInitialDataProducer.Published published = publishInitials(root, initial);
        freshOriginals.putAll(published.originalDocuments().selected());
        for (var pin : published.definitionInputs()) {
            Slot slot = switch (pin.role()) {
                case FAMILY_DOMAIN -> Slot.FAMILY;
                case CHILD_MATRILINEAL_DOMAIN -> Slot.CHILD_MATRILINEAL;
                case DEFAULT_MARRIAGE_DOMAIN -> Slot.DEFAULT_MARRIAGE;
                default -> throw new IllegalArgumentException("unexpected initial family DATA role");
            };
            assertEquals(initial.body(slot), FamilyInitialData.decode(slot, RootRuntimeDefinitions.readData(pin)));
        }
        for (var body : initial.bodies()) {
            ExactRef original = freshOriginals.get(body.slot());
            if (retainedPending && body.slot() == Slot.CHILD_MATRILINEAL) {
                byte[] bytes = FamilyInitialData.encode(body);
                var prior = StrictJson.parse(bytes, ContinuityJson.DOMAIN_MAX_BYTES);
                if (!(prior instanceof com.fasterxml.jackson.databind.node.ObjectNode object))
                    throw new IllegalArgumentException("initial family fixture is not an object");
                object.putObject("pending").put("episode_run_id", "retained-software-episode").put("heir_character_id", 2)
                        .put("candidate_character_id", 3).put("source_bridge_pid", 321)
                        .put("source_bridge_creation_date", "2026-10-24T01:00:00Z").put("pre_native_revision", 1);
                bytes = StrictJson.canonical(object);
                FamilyDomainSource.validate(body.slot(), bytes);
                var retained = immutableFiles.createNew(root.resolve(body.slot().name() + "-retained-original.json"), bytes);
                immutableFiles.verify(retained);
                assertArrayEquals(bytes, immutableFiles.read(retained, ContinuityJson.DOMAIN_MAX_BYTES));
                original = retained.reference();
            }
            originals.put(body.slot(), original);
        }
        var domains = new RootFamilyOriginalDomains(lock, originals, List.of(producer));
        var layout = new Layout(snapshot, reference(anchor), machine);
        var storage = StorageWriteGuardTestSupport.create(root, lock, 16L << 20);
        try {
            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), lock, 8L << 20), storage);
            var writer = new ContinuityWriter(layout, List.of(producer), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { return OriginalWindowReducer.reduce(predecessor, request); }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(domains.registrations(), Optional.of(artifacts), Optional.empty()), storage);
            var archive = new NativeOutcomeArchive(artifacts, writer);
            domains.bindWriter(writer, archive);
            return new Fixture(root, machine, writer, archive, domains, Map.copyOf(originals), Map.copyOf(freshOriginals), producer, storage);
        } catch (IOException | RuntimeException failure) {
            try { storage.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
            throw failure;
        }
    }
    private static RootFamilyInitialDataProducer.Published publishInitials(Path root,
            FamilyInitialData.Documents documents) throws IOException {
        Path asset = Files.createDirectory(root.resolve("published-initial-data"));
        Clock clock = Clock.systemUTC(); Instant now = clock.instant();
        var quote = new RootJavaBootstrapInputs.FamilyRequest(RootJavaBootstrapInputs.FAMILY_SCHEMA,
                WindowsJobProcess.currentMachineId(), now.plusSeconds(3600).toString(), RootJavaBootstrapInputs.Mode.QUOTE, null,
                asset.resolve("family.json").toString(), asset.resolve("matrilineal.json").toString(),
                asset.resolve("default-marriage.json").toString(), documents);
        var planned = RootJavaBootstrapInputs.prepareFamily(quote, clock).quote();
        assertEquals(3, planned.size());
        FileRef binding = authority(root, asset, planned, clock, now);
        var request = new RootJavaBootstrapInputs.FamilyRequest(quote.schema(), quote.machineId(), quote.reviewAtUtc(),
                RootJavaBootstrapInputs.Mode.CREATE_NEW, binding, quote.familyTarget(), quote.childMatrilinealTarget(),
                quote.defaultMarriageTarget(), documents);
        byte[] wire = RootJavaBootstrapInputs.encodeFamilyRequest(request);
        var decoded = RootJavaBootstrapInputs.decodeFamilyRequest(wire);
        assertEquals(request, decoded);
        return RootJavaBootstrapInputs.prepareFamily(decoded, clock).createNew(clock);
    }
    /** Software issuer uses the same finite Guard records as RootFamilyBootstrapInputsTest.
     * No production issuer, Game identity, initial episode proof or runtime admission is created. */
    private static FileRef authority(Path root, Path asset, List<RootBootstrapOutputContract.Output> outputs,
            Clock clock, Instant now) throws IOException {
        Path control = Files.createDirectory(root.resolve("initial-publication-control"));
        String machine = WindowsJobProcess.currentMachineId(), review = now.plusSeconds(3600).toString();
        var declaration = new RootBootstrapOutputContract.Declaration(RootBootstrapOutputContract.DECLARATION,
                RootBootstrapOutputContract.PURPOSE, machine, "/root", "family-import-fixture", now.minusSeconds(1).toString(), review,
                asset.toString(), SharedSourceFiles.nativeDirectory(asset), control.toString(), SharedSourceFiles.nativeDirectory(control),
                1536L * 1024, 512L * 1024, 1 << 20, 64, outputs, List.of(), List.of());
        FileRef declarationRef = writeFixture(control.resolve("declaration.json"), RootBootstrapOutputContract.encode(declaration));
        FileRef census = writeFixture(control.resolve("census.json"),
                RootBootstrapOutputContract.encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef, clock)));
        var policy = StrictJson.object().put("policy_version", "1.0.0"); var rules = policy.putObject("capacity");
        rules.put("safety_floor_bytes", 2L << 30); rules.put("safety_ceiling_bytes", 20L << 30);
        rules.put("default_project_quota_ceiling_bytes", 100L << 30);
        rules.put("safety_volume_fraction", new java.math.BigDecimal("0.05"));
        rules.put("default_project_quota_volume_fraction", new java.math.BigDecimal("0.10"));
        FileRef policyRef = writeFixture(control.resolve("policy.json"), ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume = asset.getRoot(); long total = Files.getFileStore(volume).getTotalSpace(), free = Files.getFileStore(volume).getUsableSpace();
        var financial = StrictJson.object().put("scope", "software-fixture-actual-volume-observation").put("machine_id", machine)
                .put("total_bytes", total).put("usable_bytes", free).put("old_workpackage_actual_is_unknown", true);
        FileRef head = writeFixture(control.resolve("financial.json"), StrictJson.canonical(financial));
        var usage = new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null, Math.subtractExact(total, free), head);
        var release = new RootBootstrapOutputContract.CapacityRelease(RootBootstrapOutputContract.CAPACITY,
                RootBootstrapOutputContract.PURPOSE, machine, "/root", RootBootstrapOutputContract.ISSUER, "family-import-fixture",
                now.toString(), review, policyRef, declarationRef, census, head, 2L << 20,
                List.of(new RootBootstrapOutputContract.Volume(volume.toString(), 2L << 20, 0, 0, total, review, usage, List.of(), 0)), List.of());
        FileRef capacity = writeFixture(control.resolve("capacity.json"), RootBootstrapOutputContract.encode(release));
        return writeFixture(control.resolve("binding.json"), RootBootstrapOutputContract.encode(new RootBootstrapOutputContract.Binding(
                RootBootstrapOutputContract.BINDING, RootBootstrapOutputContract.PURPOSE, machine, "/root", RootBootstrapOutputContract.ISSUER,
                "family-import-fixture", now.toString(), review, declarationRef, census, capacity)));
    }
    private static FileRef writeFixture(Path target, byte[] bytes) throws IOException {
        Files.write(target, bytes); return FileRef.measure(target);
    }
    private static PlanningRequest softwareRequest(Fixture fixture) {
        var source = new G2Source(fixture.machine(), "2026-10-25T20:00:00Z", "software-original-domain-import", fixture.producer());
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.valueOf(1000)),
                "software-native-1", BigInteger.ONE, "software-episode");
        var before = new ObservationIdentity(fixture.machine(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        var snapshot = StrictJson.object().put("snapshot_id", "software-native-1").put("revision", 1).put("native_revision", 1).put("date_raw", 1000)
                .put("episode_run_id", "software-episode").put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", 1).put("alive", true);
        snapshot.putArray("active_wars"); snapshot.putArray("player_armies");
        snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction");
        Obj semantic = org.xar.ck3.control.application.driver.DriverJson.object(StrictJson.canonical(snapshot),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        return new PlanningRequest(before, source, "software-family-import-session", Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(semantic, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    @Test void typedThreeSlotOriginalsImportThroughTheActualWriterAndReachItsOrdinaryDomainConsumer() throws Exception {
        var fresh = FamilyInitialData.fresh();
        var initial = new FamilyInitialData.Documents(new FamilyInitialData.Body(Slot.FAMILY, FamilyInitialData.History.EMPTY),
                fresh.childMatrilineal(), new FamilyInitialData.Body(Slot.DEFAULT_MARRIAGE, FamilyInitialData.History.EMPTY));
        try (var fixture = fixture(initial, false)) {
            fixture.writer().locked(same -> {
                for (Slot slot : SLOTS) {
                    assertInstanceOf(DomainBodies.Unavailable.class, same.readDomain(slot));
                    fixture.domains().importOriginal(same, slot);
                    var actual = assertInstanceOf(DomainBodies.Available.class, same.readDomain(slot));
                    assertArrayEquals(FamilyInitialData.encode(initial.body(slot)), actual.canonicalBody());
                    assertEquals(initial.body(slot), FamilyInitialData.decode(slot, actual.canonicalBody()));
                    assertEquals(FamilyDomainSource.schema(slot), actual.reference().contractSchema());
                }
                String committed = same.head().digest(); long sequence = same.head().state().sequence();
                for (Slot slot : SLOTS) fixture.domains().importOriginal(same, slot);
                assertEquals(committed, same.head().digest()); assertEquals(sequence, same.head().state().sequence());
                var request = softwareRequest(fixture);
                var bridge = new FamilyDomainSource.CurrentBridge() {
                    @Override public Optional<FamilyDomainSource.BridgeObservation> observe(PlanningRequest actual) {
                        assertSame(request, actual);
                        return Optional.of(new FamilyDomainSource.BridgeObservation(new FamilyPorts.BridgeIdentity(77, "software-bridge-birth"), fixture.producer()));
                    }
                    @Override public boolean verifyRetained(org.xar.ck3.control.application.action.PlanningReadReceipt original,
                            FamilyDomainSource.BridgeObservation observed) { throw new AssertionError("fixture never qualifies a native receipt"); }
                };
                var consumed = assertInstanceOf(FamilyPorts.KnownDocuments.class,
                        new FamilyDomainSource(fixture.writer()::borrowedSession, bridge).readCurrent(request)).documents();
                assertEquals(same.persistedHead(), consumed.canonicalHead());
                assertEquals(3, consumed.importedDocuments().size());
                for (Obj body : List.of(consumed.family(), consumed.matrilineal(), consumed.childDefault())) {
                    assertEquals(OpportunityJson.Nil.INSTANCE, body.get("pending"));
                    assertEquals(OpportunityJson.Nil.INSTANCE, body.get("resolved"));
                }
                assertTrue(consumed.family().get("episode_history") instanceof OpportunityJson.Arr);
                assertFalse(consumed.matrilineal().members().containsKey("episode_history"));
                assertTrue(consumed.childDefault().get("episode_history") instanceof OpportunityJson.Arr);
                return null;
            });
        }
    }
    @Test void selectingFreshInitialDataNeverOverwritesAnExistingUnresolvedDomain() throws Exception {
        try (var fixture = fixture(FamilyInitialData.fresh(), true)) {
            fixture.writer().locked(same -> {
                fixture.domains().importOriginal(same, Slot.CHILD_MATRILINEAL);
                var old = assertInstanceOf(DomainBodies.Available.class, same.readDomain(Slot.CHILD_MATRILINEAL));
                assertTrue(FamilyDomainSource.validate(Slot.CHILD_MATRILINEAL, old.canonicalBody()).get("pending") instanceof Obj);
                var selected = new RootFamilyOriginalDomains(fixture.writer().originalLockPath(), fixture.freshOriginals(), List.of(fixture.producer()));
                selected.bindWriter(fixture.writer(), fixture.archive());
                String before = same.head().digest();
                assertEquals(old.reference().payload(), selected.importOriginal(same, Slot.CHILD_MATRILINEAL));
                assertEquals(before, same.head().digest());
                assertArrayEquals(old.canonicalBody(), assertInstanceOf(DomainBodies.Available.class, same.readDomain(Slot.CHILD_MATRILINEAL)).canonicalBody());
                return null;
            });
        }
    }
    @Test void changedSelectedInitialOriginalCannotPublishAnyDomainOrResetItsHead() throws Exception {
        try (var fixture = fixture(FamilyInitialData.fresh(), false)) {
            Path selected = Path.of(fixture.originals().get(Slot.FAMILY).path());
            Files.writeString(selected, "{\"schema\":\"different-original\",\"pending\":null,\"resolved\":null}");
            String before = fixture.writer().locked(same -> same.head().digest());
            assertThrows(IOException.class, () -> fixture.writer().locked(same -> { fixture.domains().importOriginal(same, Slot.FAMILY); return null; }));
            fixture.writer().locked(same -> {
                assertEquals(before, same.head().digest());
                assertInstanceOf(DomainBodies.Unavailable.class, same.readDomain(Slot.FAMILY));
                return null;
            });
        }
    }
}
