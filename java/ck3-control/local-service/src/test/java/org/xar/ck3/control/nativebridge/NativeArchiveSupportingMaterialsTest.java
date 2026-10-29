package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Controlled source-shaped packets run real producers, physical archive and ordinary domain replay.
 * This grants no live Game, retreat legality, battle outcome or current .4 qualification.
 */
final class NativeArchiveSupportingMaterialsTest {
    @TempDir Path temp;
    private static final String STATE = """
            {"paused":true,"map_ready":true,"speed":3,"date_raw":%d,
             "played_character":{"character_id":73,"alive":true},"active_event":null,
             "pending_character_interaction":null,"one_life_terminal_reason":null,"active_wars":[],
             "player_armies":[{"army_id":1,"owner_character_id":73,"controllable":true,"in_combat":false,
              "retreating":false,"army_state":"regular","army_state_code":1,"current_province_id":2,
              "move_target_province_id":null,"route_province_ids":[]}]}
            """;
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    static NativeObservationPort.ObservedFrame frame(PlanningRequest base, int revision, boolean moving, Instant observed) throws IOException {
        String originalState = STATE.formatted(base.before().frame().identity().dateRaw());
        String state = moving ? originalState.replace("\"move_target_province_id\":null", "\"move_target_province_id\":3").replace("\"route_province_ids\":[]", "\"route_province_ids\":[2,3]") : originalState;
        byte[] packet = NativeWire.packet(bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"archive-frame-" + revision + "\",\"revision\":" + revision + ",\"state\":" + state + "}"));
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(base.before().machineId(), base.before().game(), BigInteger.valueOf(5), base.sessionId()),
                "archive-frame-" + revision, BigInteger.valueOf(revision), new RawJson(bytes(state)), packet, observed.plusMillis(revision));
    }
    static DriverObservationFacts actualFacts(NativeObservationPort.ObservedFrame original, G2Source source,
            ExactRef fullRef, RawJson fullDriver, ActionPorts.OutcomeArchive archive) {
        var known = DriverFactsRepository.imported(fullRef, fullDriver.bytes(), 3, 7, original.session().game(), new OpportunityJson.Obj(Map.of()));
        RawJson manifest = DriverObservationEvidenceReader.encode(known, original, original.nativeRevision(), 1, source, new OpportunityJson.Obj(Map.of()), fullRef);
        ExactRef manifestRef = archive.preserveMaterial(manifest);
        return DriverObservationEvidenceReader.decode(manifestRef, manifest, fullDriver, original);
    }
    private record Case(ActionReceipt receipt, ActionReceipt ordinary, NativeEffectEvidence.FrameLoader frames, RawJson completeDomain, ExactRef domainRef) { }
    private static Case produced(ActionWriterIntegrationFixture fixture) throws IOException, InterruptedException {
        var ready = fixture.ready(); PlanningRequest base = ready.request(); var sem = ready.semanticEvidence().orElseThrow();
        RawJson fullDriver = fixture.archive.loadMaterial(sem.originalDriver()); ExactRef fullRef = sem.originalDriver();
        Instant now = Instant.now().minusSeconds(1), deadline = Instant.now().plusSeconds(20); var count = new AtomicInteger();
        var held = new HeldDriverObservationPort(until -> {
            int position = count.getAndIncrement();
            try { return frame(base, position == 0 ? 9 : 10, position != 0, now); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }, original -> new DriverObservationFacts.Known(actualFacts(original, base.source(), fullRef, fullDriver, fixture.archive)),
                fixture.archive::preserveNativeFrame, new DriverObservationAssembler(), 8);
        var before = held.observe(deadline); OperationKey operation = new OperationKey("move-army-1-to-3");
        var command = new ActionCommand("archive-material-move", before.identity(), before.source(), before.sessionId(), operation, new OpportunityJson.Obj(Map.of()),
                NativeArmyMoveEffects.expected(before.identity(), before.source(), operation),
                new JointBudgetSelector.Claims(Set.of(BigInteger.ONE), Set.of(), Set.of(), Set.of()), deadline);
        var guard = new GuardEvidence(before.identity(), before.source(), before.sessionId(), before.connectionGeneration(), operation,
                before.originalEvidence(), before.originalEvidence(), "source-shaped-domain-fixture", before.observedAt(), deadline);
        var attempt = new ActionState.Attempt("material-move-request", before.observedAt(), guard, new NativeRequest(operation.value(), Optional.empty(), new RawJson(bytes("{}"))));
        var dispatch = new NativeActionPort.Unknown(attempt.requestId(), "controlled missing original ACK; no replay", new byte[0], Optional.empty());
        var projected = new NativeArmyMoveEffects(new NativeEffectSnapshots(held, fixture.archive)).observe(command, attempt, dispatch);
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, projected.result()).observation();
        var basic = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(observed)));
        var loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        var original = NativeEffectEvidence.load(basic, fixture.archive, loader);
        // A complete typed ACTIVE_RETREAT domain, including old exclusions and nullable fields.
        // It is archived data only; no domain initialization or retreat qualification is claimed.
        var post = new OpportunityJson.Obj(Map.of("source_marker", new OpportunityJson.Text("complete original state"),
                "optional", OpportunityJson.Nil.INSTANCE, "empty", new OpportunityJson.Arr(List.of()),
                "original_scale", new OpportunityJson.DecimalValue("1.0"), "filetime", new OpportunityJson.Text("9007199254740993")));
        var claim = new ActiveRetreatState.Claim(new ActiveRetreatState.ClaimKey(before.identity().frame().episodeRunId(), 0, Integer.MIN_VALUE), ActiveRetreatState.ClaimStatus.NATIVE_REJECTED);
        var domain = new ActiveRetreatState.State(Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(post), List.of(claim));
        RawJson completeDomain = new RawJson(DriverJson.encode(ActiveRetreatState.encode(domain)));
        ExactRef domainRef = fixture.archive.preserveMaterial(completeDomain);
        ExactRef basis = NativeEffectEvidence.preserve(command, attempt, original.frames(), original.independentReads(), original.compatibleResult(), List.of(domainRef), fixture.archive);
        var effect = new ActionState.EffectObservation(observed.after(), observed.source(), observed.sessionId(), observed.observerSchema(), observed.actual(),
                observed.provenance(), observed.observedAt(), observed.originalEvidence(), List.of(basis, domainRef));
        return new Case(new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.Applied(effect))), basic, loader, completeDomain, domainRef);
    }
    @Test void sourceProducerPhysicalArchiveAndSoleV2LoaderKeepCompleteMaterialWithoutGrantingRetreatToOrdinaryMove() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("complete"), false)) {
            Case original = produced(fixture); byte[] ledger = fixture.ledgerBytes();
            ExactRef kept = fixture.writer.locked(session -> fixture.archive.inSession(session, archive -> archive.preserveReceipt(original.receipt())));
            ActionReceipt decoded = fixture.archive.loadReceipt(kept); var rebuilt = NativeEffectEvidence.load(decoded, fixture.archive, original.frames());
            assertEquals(List.of(original.domainRef()), rebuilt.supportingMaterials());
            assertArrayEquals(original.completeDomain().bytes(), fixture.archive.loadMaterial(original.domainRef()).bytes());
            var state = ActiveRetreatState.decode(DriverJson.object(fixture.archive.loadMaterial(original.domainRef()).bytes(), DriverJson.MAX_NATIVE_BYTES));
            assertEquals(0, state.claims().getFirst().key().selectedPublicCunitId()); assertEquals(Integer.MIN_VALUE, state.claims().getFirst().key().expectedCombatId());
            var ordinary = fixture.archive.loadReceipt(fixture.archive.preserveReceipt(original.ordinary()));
            assertDoesNotThrow(() -> NativeArmyMoveEffects.archivedVerifier(ordinary.command().operation(), ordinary.command().source().sourceRef(), original.frames()).verifier().verify(null, ordinary, fixture.archive));
            // Generic v2 custody can retain the complete domain body. The ordinary Move domain
            // correctly refuses to borrow retreat material or declare that preview legally valid.
            assertThrows(IllegalArgumentException.class, () -> NativeArmyMoveEffects.archivedVerifier(decoded.command().operation(), decoded.command().source().sourceRef(), original.frames()).verifier().verify(null, decoded, fixture.archive));
            assertArrayEquals(ledger, fixture.ledgerBytes());
            Files.writeString(Path.of(original.domainRef().path()), "{\"changed\":true}");
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadReceipt(kept));
            assertThrows(UncheckedIOException.class, () -> NativeEffectEvidence.load(decoded, fixture.archive, original.frames()));
            assertEquals("{\"changed\":true}", Files.readString(Path.of(original.domainRef().path())));
        }
    }
    @Test void bodyStillPresentDoesNotPermitReceiptToDropTheDeclaredSupportingClosure() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("dropped"), false)) {
            Case original = produced(fixture); var settled = (ActionState.Settled) original.receipt().state();
            var effect = ((ActionState.Applied) settled.settlement()).observation();
            var dropped = new ActionState.EffectObservation(effect.after(), effect.source(), effect.sessionId(), effect.observerSchema(), effect.actual(),
                    effect.provenance(), effect.observedAt(), effect.originalEvidence(), List.of(effect.supportingEvidence().getFirst()));
            var data = new ActionReceipt(1, 1, original.receipt().command(), original.receipt().bodySha256(), new ActionState.Settled(settled.attempt(), settled.dispatch(), new ActionState.Applied(dropped)));
            ActionReceipt loaded = fixture.archive.loadReceipt(fixture.archive.preserveReceipt(data));
            // Generic archival retention grants no domain permission. Its sole v2 domain consumer rejects this exact omission.
            assertThrows(IllegalArgumentException.class, () -> NativeEffectEvidence.load(loaded, fixture.archive, original.frames()));
            assertThrows(IllegalArgumentException.class, () -> NativeArmyMoveEffects.archivedVerifier(data.command().operation(), data.command().source().sourceRef(), original.frames()).verifier().verify(null, loaded, fixture.archive));
        }
    }
    @Test void foreignMissingPathAndOversizeDeclaredBoundRejectBeforeGenericWriterPinRead() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("root"), false)) {
            ExactRef kept = fixture.archive.preserveMaterial(new RawJson(bytes("{\"actual\":true}")));
            Path missing = temp.resolve("foreign-never-created.bin"); ExactRef foreign = new ExactRef(missing.toString(), 1, "0".repeat(64));
            fixture.writer.locked(session -> {
                IOException failure = assertThrows(IOException.class, () -> fixture.archive.readArtifact(session, foreign, 1024));
                assertTrue(failure.getMessage().contains("content-addressed root"));
                assertThrows(IllegalArgumentException.class, () -> fixture.archive.readArtifact(session, kept, WriterContracts.MAX_PIN_BYTES + 1));
                assertThrows(IOException.class, () -> fixture.archive.readArtifact(session, kept, Math.toIntExact(kept.bytes() - 1)));
                return null;
            });
            assertFalse(Files.exists(missing));
        }
    }
    @Test void actualPreparedRequestRetainsSeparateOriginalsWithStrictV2AndHistoricalV1Bytes() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("preparation"), false)) {
            var ready = fixture.ready(); byte[] packet = frame(ready.request(), 12, false, Instant.now()).originalPacket();
            ExactRef originalPacket = fixture.writer.locked(session -> fixture.archive.preserveArtifact(session, packet, 65536));
            RawJson intent = new RawJson(bytes("{\"target\":3}"));
            ExactRef basis = fixture.archive.preserveMaterial(new RawJson(bytes("{\"controlled_preparation_basis\":true}")));
            var historical = new NativeRequest("move-army-1-to-3", Optional.empty(), intent);
            var prepared = new NativeRequest(historical.step(), historical.requiredCapability(), intent, List.of(basis, originalPacket));
            ExactRef oldRef = fixture.archive.preserveRequest(historical), currentRef = fixture.archive.preserveRequest(prepared);
            assertEquals(historical, fixture.archive.loadRequest(oldRef)); assertEquals(prepared, fixture.archive.loadRequest(currentRef));
            var oldRow = org.xar.ck3.control.contracts.StrictJson.parse(fixture.archive.loadMaterial(oldRef).bytes());
            var currentRow = org.xar.ck3.control.contracts.StrictJson.parse(fixture.archive.loadMaterial(currentRef).bytes());
            assertEquals("xar.native-request-archive/v1", oldRow.path("schema").textValue()); assertFalse(oldRow.has("preparation_evidence"));
            assertEquals("xar.native-request-archive/v2", currentRow.path("schema").textValue()); assertEquals(2, currentRow.path("preparation_evidence").size());
            assertEquals(oldRef, fixture.archive.requestReferenceOf(new NativeRequest(historical.step(), Optional.empty(), intent, List.of())));
            // Only the existing additions enter the native wire; preparation originals remain custody metadata.
            assertArrayEquals(NativeWire.execute("actual-request", historical.step(), BigInteger.valueOf(12), historical.additionalFields().bytes()),
                    NativeWire.execute("actual-request", prepared.step(), BigInteger.valueOf(12), prepared.additionalFields().bytes()));
            Files.writeString(Path.of(basis.path()), "{\"corrupt\":true}");
            assertThrows(UncheckedIOException.class, () -> fixture.archive.loadRequest(currentRef));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.requestReferenceOf(prepared));
            assertEquals("{\"corrupt\":true}", Files.readString(Path.of(basis.path())));
        }
    }
}
