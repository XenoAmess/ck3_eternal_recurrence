package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real registered writer/reducer/store regression. This lower-bound test does not mint a Root source capture or Ready. */
final class RootOrdinaryClaimReducerIntegrationTest {
    @TempDir Path temporary;
    private static final String MACHINE = "fixture-claim-machine";
    private record Fixture(ContinuityWriter writer, OrdinaryClaimDomain domain, ImmutableArtifactStore store,
            Map<ExactRef, WriterContracts.Pin> published, RootOrdinaryClaimOriginals.Captured actual,
            AtomicInteger seedReplays, Path snapshot, ExactRef manifest) { }
    private ExactRef ref(Path path, byte[] raw) { return new ExactRef(path.toString(), raw.length, ActionCodec.sha256(raw)); }
    private Fixture fixture(String name, boolean legacy) throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(), "real original-lock regression requires Windows");
        Path root = Files.createDirectory(temporary.resolve(name)); Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        byte[] initial = ContinuityJson.canonical(initial()); Files.write(snapshot, initial); Files.write(anchor, initial);
        Path lock = root.resolve("ROOT-CONTINUITY-WINDOW.lock"); Files.write(lock, new byte[0]); Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path source = root.resolve("reviewed-producer.txt"); byte[] sourceRaw = "controlled actual ordinary reducer fixture source".getBytes(java.nio.charset.StandardCharsets.UTF_8); Files.write(source, sourceRaw);
        var layout = new WriterContracts.Layout(snapshot, ref(anchor, initial), MACHINE);
        var storage = StorageWriteGuardTestSupport.create(layout); var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(Files.createDirectory(root.resolve("archive")), lock, 16L << 20), storage);
        Map<ExactRef, WriterContracts.Pin> published = new HashMap<>();
        OrdinaryClaimDomain.Artifacts artifacts = new OrdinaryClaimDomain.Artifacts() {
            @Override public ExactRef publish(ContinuityStorePort.Session same, byte[] original) {
                try { same.requireWriter(lock); var pin = store.publish(original, OrdinaryOnceClaims.MAX_BYTES); published.put(pin.reference(), pin); return pin.reference(); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public byte[] read(ExactRef original) {
                try { var pin = published.get(original); if (pin == null) throw new IOException("controlled original was not actually published"); return store.read(pin, OrdinaryOnceClaims.MAX_BYTES); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
        };
        Path originalDirectory = Files.createDirectory(root.resolve("ordinary-interaction-actions"));
        if (legacy) Files.write(originalDirectory.resolve("original.claim.json"), RootOrdinaryClaimOriginalsTest.legacy("legacy-original", "2147483647"));
        var actual = RootOrdinaryClaimOriginals.capture(originalDirectory);
        var domain = new OrdinaryClaimDomain(lock, artifacts, new RootOrdinaryClaimRuntime.SourceConsumptionAuthority());
        AtomicInteger calls = new AtomicInteger(); var retained = new java.util.ArrayList<ExactRef>();
        var manifestRef = new java.util.concurrent.atomic.AtomicReference<ExactRef>();
        var registration = domain.registration(List.of(ref(source, sourceRaw)), (original, head) -> {
            try {
                calls.incrementAndGet(); assertEquals(manifestRef.get(), original); assertEquals(MACHINE, head.machineId());
                actual.requireUnchanged(); return actual.state(head.machineId(), retained);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        });
        var writer = new ContinuityWriter(layout, List.of(ref(source, sourceRaw)), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, WriterContracts.Request request) { return ContinuityJson.digest(request.detailsObject()); }
            @Override public ContinuityState reduce(ContinuityState head, WriterContracts.Request request) { return OriginalWindowReducer.reduce(head, request); }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(store), Optional.empty()), storage);
        writer.locked(same -> {
            for (var original : actual.originals()) retained.add(artifacts.publish(same, original.bytes()));
            byte[] census = StrictJson.canonical(StrictJson.object().put("schema", "controlled-real-directory-census/v1").put("actual_claim_count", actual.originals().size()));
            manifestRef.set(artifacts.publish(same, census)); return null;
        });
        return new Fixture(writer, domain, store, published, actual, calls, snapshot, manifestRef.get());
    }
    private static ObjectNode initial() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE).put("sequence", 0)
                .put("window_id", 1).put("status", "running").put("target_days", 10958).put("target_years", 30).put("calendar_year_days", 365.25)
                .put("start_date_raw", 1000).put("target_date_raw", 1000 + 10958 * 24).put("last_settled_date_raw", 1000)
                .put("last_settled_cycles", 1).put("manual_repair_count", 1).put("automatic_recovery_count", 0).put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 121).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static OrdinaryOnceClaims.Request next(String request) {
        return new OrdinaryOnceClaims.Request(new OrdinaryOnceClaims.Identity(MACHINE, 121, "134999999999999999", 2_147_483_647L,
                "educate_child_interaction", 4_000_000_002L), new OrdinaryOnceClaims.Binding("native:11", "12", "11", "1000", "1", "episode"), request);
    }
    @Test void realRegisteredReducerRejectsAnEmptyStateInPlaceOfTheCompleteLegacyProducer() throws Exception {
        var fixture = fixture("real-seed-reducer", true); byte[] before = Files.readAllBytes(fixture.snapshot());
        fixture.writer().locked(same -> {
            assertThrows(IllegalArgumentException.class, () -> fixture.domain().importOriginal(same, fixture.manifest(), new OrdinaryOnceClaims.State(MACHINE, List.of(), List.of(), List.of())));
            assertTrue(same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM) instanceof DomainBodies.Unavailable);
            List<ExactRef> retained = fixture.actual().originals().stream().map(original -> fixture.published().keySet().stream()
                    .filter(ref -> ref.sha256().equals(original.source().sha256()) && ref.bytes() == original.source().bytes()).findFirst().orElseThrow()).toList();
            var actual = fixture.actual().state(MACHINE, retained);
            fixture.domain().importOriginal(same, fixture.manifest(), actual);
            var stored = assertInstanceOf(DomainBodies.Available.class, same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM));
            assertEquals(actual, OrdinaryOnceClaims.decode(stored.canonicalBody()));
            assertThrows(IllegalArgumentException.class, () -> fixture.domain().claim(same, next("cannot-bypass-legacy")));
            return null;
        });
        assertTrue(fixture.seedReplays().get() >= 3, "preview and commit must re-enter the actual source reducer");
        assertFalse(java.util.Arrays.equals(before, Files.readAllBytes(fixture.snapshot())));
        assertEquals(1L, fixture.writer().locked(same -> same.head().state().sequence()).longValue());
    }
    @Test void realZeroCensusAllowsOneClaimAndRefusesRepeatedUnknownPairWithoutAnyPermitWrite() throws Exception {
        var fixture = fixture("real-once-domain", false);
        fixture.writer().locked(same -> { fixture.domain().importOriginal(same, fixture.manifest(), fixture.actual().state(MACHINE, List.of())); return null; });
        fixture.writer().locked(same -> {
            var retained = fixture.domain().claim(same, next("original-unknown"));
            assertEquals(0, retained.claim().ordinal()); assertEquals(retained, fixture.domain().requireClaim(same, "original-unknown"));
            return null;
        });
        byte[] before = Files.readAllBytes(fixture.snapshot()); long sequence = fixture.writer().locked(same -> same.head().state().sequence());
        fixture.writer().locked(same -> {
            assertThrows(RootOrdinaryClaimRuntime.PermitUnavailable.class, () -> fixture.domain().claim(same, next("new-id-after-unknown")));
            var known = assertInstanceOf(DomainBodies.Available.class, same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM));
            var state = OrdinaryOnceClaims.decode(known.canonicalBody()); assertEquals(1, state.claims().size()); assertTrue(state.consumptions().isEmpty()); return null;
        });
        assertEquals(sequence, fixture.writer().locked(same -> same.head().state().sequence()).longValue()); assertArrayEquals(before, Files.readAllBytes(fixture.snapshot()));
    }
}
