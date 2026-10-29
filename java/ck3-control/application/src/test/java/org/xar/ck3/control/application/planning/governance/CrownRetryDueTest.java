package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** Complete synthetic query producers feed the real codecs/reducer/verifier. No native/writer/Game qualification. */
public final class CrownRetryDueTest {
    private static final String MACHINE = "m7-crown-software-fixture";
    private static final String CONTRACT = "fixture.original-crown-body/v1";
    private static final String BUILD = "1.20.0.4/build25734779-fixture";
    private static final long RAW = 53_169_072;
    private static final java.time.Instant DEADLINE = java.time.Instant.parse("2026-10-23T17:40:30Z");
    private static final BigInteger ACTOR = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final Path LOCK = Path.of("fixture-only-crown.lock").toAbsolutePath().normalize();
    private static final ExactRef RUNTIME = ref("fixture-exe-not-a-real-runtime", bytes("fixture-runtime"));
    private static final ExactRef PRODUCER = ref("fixture-producer-not-a-real-source", bytes("fixture-producer"));
    private static final G2Source SOURCE = new G2Source(MACHINE, "2026-10-23T17:40:00Z", BUILD,
            ref("fixture-native-current", bytes("fixture-current-native")));

    /** Test-only shared producer fixture. No private proof constructor, native process or real writer is substituted. */
    public record CapturedDue(CrownRetryDue producer, CrownRetryDue.VerifiedDue due,
            ContinuityStorePort.Session borrowed, ObservationIdentity observed, G2Source source,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic,
            CrownRetryPublication publication, CrownRetryPublication.ImportProof proof, Path writerLock) {
        /** Synthetic store uses the real cadence serializer/domain reducer, then recaptures private due at that actual head. */
        public CapturedDue withCadence(org.xar.ck3.control.planning.optionalcadence.CadenceModels.State state) throws IOException {
            if (!(borrowed instanceof Session actual)) throw new IllegalArgumentException("original synthetic store required");
            actual.installCadence(state);
            var current = producer.capture(borrowed, proof, observed, source, semantic, DEADLINE);
            producer.requireCurrent(borrowed, current, DEADLINE);
            return new CapturedDue(producer, current, borrowed, observed, source, semantic, publication, proof, writerLock);
        }
    }
    public static CapturedDue publishedDueFixture() throws IOException { return publishedDueFixtureAtDays(1); }
    public static CapturedDue publishedDueFixtureAtDays(long days) throws IOException {
        StrictJson.require(days >= 0 && days <= 365, "bounded synthetic elapsed days required");
        Fixture f = new Fixture(); var proof = f.service.publish(f.session, f.input, DEADLINE);
        var current = identity("134371375868945259", RAW + days * 24, 9, 14);
        var service = dueService(f); var snapshot = semantic(current);
        var due = service.capture(f.session, proof, current, SOURCE, snapshot, DEADLINE);
        return new CapturedDue(service, due, f.session, current, SOURCE, snapshot, f.service, proof, LOCK);
    }

    @Test void fullPublisherFeedsPrivateDueAndKeepsSelectedFortyFiveDayHorizonBoundedByTenDays() throws Exception {
        Fixture f = new Fixture(); var proof = f.service.publish(f.session, f.input, DEADLINE);
        var current = identity("134371375868945259", RAW + 24, 9, 14);
        var service = dueService(f);
        var due = service.capture(f.session, proof, current, SOURCE, semantic(current), DEADLINE);
        service.requireCurrent(f.session, due, DEADLINE);
        assertEquals(BigInteger.TEN, due.horizonDays(current, BigInteger.valueOf(45), true, true));
        assertEquals(BigInteger.valueOf(3), due.horizonDays(current, BigInteger.valueOf(3), true, true));
        assertEquals(BigInteger.valueOf(45), due.horizonDays(current, BigInteger.valueOf(45), false, true));
        assertEquals(BigInteger.valueOf(45), due.horizonDays(current, BigInteger.valueOf(45), true, false));
        assertEquals(1, f.session.commits); assertFalse(due.authorizesAction()); assertEquals(0, due.savedDayCredit());
        assertEquals(0, CrownRetryDue.VerifiedDue.class.getConstructors().length);
        assertEquals(proof.body(), due.publicationBody());
    }
    @Test void deadlineExpiryOnlyStopsClippingAndRequiresTheExistingFreshFinalTermsPath() throws Exception {
        Fixture f = new Fixture(); var proof = f.service.publish(f.session, f.input, DEADLINE); var service = dueService(f);
        for (long date : List.of(RAW + 11 * 24, RAW + 12 * 24)) {
            var current = identity("134371375868945259", date, 9, 14);
            var due = service.capture(f.session, proof, current, SOURCE, semantic(current), DEADLINE);
            assertEquals(BigInteger.valueOf(45), due.horizonDays(current, BigInteger.valueOf(45), true, true));
            assertFalse(due.authorizesAction());
        }
        assertEquals(1, f.session.commits);
    }
    @Test void actualPublisherDueStatusChangesOnlyWhenItsVerifiedCalendarDeadlineArrives() throws Exception {
        var before = publishedDueFixtureAtDays(1); before.producer().requireCurrent(before.borrowed(), before.due(), DEADLINE);
        assertFalse(before.due().currentlyDue(before.observed()));
        var due = publishedDueFixtureAtDays(11); due.producer().requireCurrent(due.borrowed(), due.due(), DEADLINE);
        assertTrue(due.due().currentlyDue(due.observed()));
        assertFalse(due.due().authorizesAction());
        assertThrows(IllegalArgumentException.class, () -> due.due().currentlyDue(before.observed()));
    }
    @Test void oldSamePidHintAndDifferentRequestFrameCannotBecomeActualDueData() throws Exception {
        Fixture f = new Fixture(); var proof = f.service.publish(f.session, f.input, DEADLINE); var service = dueService(f);
        var current = identity("134371375868945259", RAW + 24, 9, 14);
        var due = service.capture(f.session, proof, current, SOURCE, semantic(current), DEADLINE);
        var oneTick = identity("134371375868945260", RAW + 24, 9, 14);
        assertThrows(IllegalArgumentException.class, () -> service.capture(f.session, proof, oneTick, SOURCE, semantic(oneTick), DEADLINE));
        assertThrows(IllegalArgumentException.class, () -> due.horizonDays(oneTick, BigInteger.valueOf(45), true, true));
        var newFrame = identity("134371375868945259", RAW + 48, 10, 15);
        assertThrows(IllegalArgumentException.class, () -> due.horizonDays(newFrame, BigInteger.valueOf(45), true, true));
        assertThrows(IllegalArgumentException.class, () -> service.capture(f.session, proof, current, SOURCE, semantic(newFrame), DEADLINE));
        f.session.replaceBody(bytes("{\"pending\":null,\"resolved\":null,\"retry\":null}"));
        assertThrows(IllegalArgumentException.class, () -> service.requireCurrent(f.session, due, DEADLINE));
    }
    @Test void wrongWriterAndUnavailableCurrentRuntimeDoNotFallBackToUnprovedState() throws Exception {
        Fixture f = new Fixture(); var proof = f.service.publish(f.session, f.input, DEADLINE); var service = dueService(f);
        var current = identity("134371375868945259", RAW + 24, 9, 14);
        f.session.rejectWriter = true;
        assertThrows(IOException.class, () -> service.capture(f.session, proof, current, SOURCE, semantic(current), DEADLINE));
        f.session.rejectWriter = false; f.failRead = true;
        assertThrows(IOException.class, () -> service.capture(f.session, proof, current, SOURCE, semantic(current), DEADLINE));
        assertEquals(1, f.session.commits);
    }
    private static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic(ObservationIdentity current) {
        ObjectNode snapshot = snapshot(current.frame().snapshotId(), current.frame().revision().intValueExact(),
                current.frame().identity().nativeRevision().intValueExact());
        snapshot.put("date_raw", current.frame().identity().dateRaw());
        return org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(snapshot)), "complete fixture SEM");
    }
    private static CrownRetryDue dueService(Fixture f) {
        return new CrownRetryDue(store(f), borrowed -> { assertSame(f.session, borrowed); borrowed.requireWriter(LOCK); }, f.service);
    }
    private static ContinuityStorePort store(Fixture f) {
        return new ContinuityStorePort() {
            public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { return f.session.preview(request); }
            public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { return f.session.commit(prepared); }
            public ExactRef persistedHead() { return f.session.persistedHead(); }
            public <T> T locked(ContinuityStorePort.SessionWork<T> work) throws IOException { return work.run(f.session); }
        };
    }

    private static ObservationIdentity identity(String birth, long raw, int nativeRevision, int publicRevision) {
        return new ObservationIdentity(MACHINE, new GameGeneration(321, new PythonOnlyUInt64(new BigInteger(birth))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(ACTOR, BigInteger.valueOf(nativeRevision), BigInteger.valueOf(raw)),
                        "actual-native-" + nativeRevision, BigInteger.valueOf(publicRevision), "original-campaign-episode"), 1);
    }
    private static ObjectNode snapshot(String snapshot, int revision, int nativeRevision) {
        ObjectNode row = StrictJson.object(); row.put("snapshot_id", snapshot); row.put("revision", revision); row.put("native_revision", nativeRevision);
        row.put("episode_run_id", "original-campaign-episode"); row.put("date_raw", RAW); row.put("paused", true); row.put("map_ready", true);
        row.putObject("played_character").put("character_id", ACTOR).put("alive", true);
        row.putObject("diagnostics").putObject("hello").put("expected_ck3_version", CrownFinalTerms.Build.CK3_12004.version())
                .put("expected_ck3_sha256", CrownFinalTerms.Build.CK3_12004.sha256()); return row;
    }
    private static byte[] nativeConsume() {
        ObjectNode row = StrictJson.object(); row.put("schema", CrownFinalTermsCodec.CONSUME_SCHEMA); row.put("expected_revision", 12); row.put("request_id", "actual-fixture-query");
        row.set("before_snapshot", snapshot("before-native-7", 12, 7)); row.set("after_snapshot", snapshot("actual-native-8", 13, 8));
        ObjectNode command = row.putObject("command_result"); command.put("type", "command_result"); command.put("protocol_version", 1); command.put("request_id", "actual-fixture-query"); command.put("ok", true);
        ObjectNode result = command.putObject("result"); result.put("step", CrownFinalTerms.STEP); result.put("accepted", true); result.put("status", "available");
        result.put("private_build", true); result.put("read_only", true); result.put("advertised", false); result.put("backend_id", "native-headless"); result.put("snapshot_revision", 7);
        ObjectNode payload = result.putObject("realm_law_final_terms"); payload.put("schema", CrownFinalTerms.SCHEMA); payload.put("snapshot_revision", 7);
        payload.put("date_raw", RAW); payload.put("actor_character_id", ACTOR); payload.put("cost_scale", 100000);
        var slots = payload.putArray("cost_slots"); CrownFinalTerms.SLOTS.forEach(slots::add); var groups = payload.putArray("groups");
        ObjectNode crown = groups.addObject(); crown.put("group_key", "crown_authority"); crown.put("active_law_key", "crown_authority_0");
        var candidates = crown.putArray("candidates"); law(candidates.addObject(), "crown_authority_0", true, false); law(candidates.addObject(), "crown_authority_1", false, false);
        ObjectNode succession = groups.addObject(); succession.put("group_key", "succession_order_laws"); succession.put("active_law_key", "partition");
        law(succession.putArray("candidates").addObject(), "partition", true, true);
        var raw = new CrownCooldown.RawObservation(true, true, true, 28, 7, 21, BigInteger.valueOf(RAW + 11 * 24), CrownCooldown.EXPIRY_TYPE, CrownCooldown.PROJECTED_UNIT);
        var tick = new CrownCooldown.TurnTick(true, BigInteger.TWO, true, true, true, null, CrownCooldown.TICK_SOURCE);
        payload.set("crown_authority_cooldown", StrictJson.parse(CrownCooldownCodec.encode(raw)));
        payload.set("crown_authority_cooldown_turn_tick", StrictJson.parse(CrownCooldownCodec.encode(tick))); return StrictJson.canonical(row);
    }
    private static void law(ObjectNode row, String key, boolean active, boolean profile) {
        row.put("law_key", key); row.put("active", active); row.put("final_status", active ? "already_active" : "engine_blocked");
        row.put("final_can_enact", false); row.put("native_reason", active ? "" : "observed current cooldown"); var costs = row.putArray("cost_raw");
        for (int index = 0; index < 10; index++) costs.add(0);
        if (profile) { row.put("succession_profile_status", "absent"); row.putNull("succession_profile"); }
    }
    private static byte[] crown() {
        var source = new CrownAuthorityPolicy.SourceFrame(BigInteger.valueOf(5), BigInteger.valueOf(5), BigInteger.ONE,
                BigInteger.valueOf(RAW), ACTOR, "1.20.0.4", CrownFinalTerms.Build.CK3_12004.sha256(), "native-5", BigInteger.TEN, BigInteger.valueOf(5));
        var candidates = List.of(new CrownAuthorityPolicy.Candidate("crown_authority_0", true, false, false, "active", List.of()),
                new CrownAuthorityPolicy.Candidate("crown_authority_1", false, true, false, "native final blocked", List.of()));
        var balances = Arrays.stream(CrownAuthorityPolicy.Currency.values()).map(currency -> new CrownAuthorityPolicy.Balance(currency, BigInteger.valueOf(100_000))).toList();
        var titles = new CrownAuthorityPolicy.TitleSuccessors(BigInteger.ONE, List.of(new CrownAuthorityPolicy.HeldTitle(BigInteger.ONE, true, List.of(ACTOR))));
        return CrownAuthorityCodec.encodeReadback(new CrownAuthorityPolicy.Readback(CrownAuthorityPolicy.READ_SCHEMA, true, true, "crown_authority", "crown_authority_0", candidates, balances, titles, source, true, false));
    }
    private static final class Fixture {
        private final byte[] original = bytes("{\"pending\":null,\"resolved\":{\"action_id\":\"retained-original\",\"ack\":{\"ok\":true},\"native_receipt\":null},\"retry\":null}");
        private final byte[] crown = crown();
        private final byte[] nativeConsume = nativeConsume();
        private final CrownRetryPublication.Input input = new CrownRetryPublication.Input(identity("134371375868945259", RAW, 8, 13), identity("134371375868945259", RAW, 8, 13), SOURCE,
                ref("fixture-original-body", original), ref("fixture-crown-readback", crown), ref("synthetic-crown-receipt", bytes("fixture-crown-receipt")), ref("fixture-final-consume", nativeConsume), ref("synthetic-terms-receipt", bytes("fixture-terms-receipt")), List.of(RUNTIME));
        private final CrownRetryPublication service;
        private final Session session;
        private int captures;
        private boolean failRead;
        private boolean badOutput;
        private byte[] output;
        private Fixture() {
            service = new CrownRetryPublication(LOCK, CONTRACT, List.of(RUNTIME), List.of(PRODUCER), new CrownRetryPublication.MaterialPort() {
                @Override public CrownRetryPublication.Material capture(WriterContracts.Head head, CrownRetryPublication.Input selected, java.time.Instant callerDeadline) throws IOException {
                    captures++; if (failRead) throw new IOException("actual native archive unavailable");
                    return new CrownRetryPublication.Material(input.currentObserved(), SOURCE, original, crown, nativeConsume);
                }
                @Override public void requireCurrent(WriterContracts.Head head, CrownRetryPublication.Input selected, ObservationIdentity current, G2Source source, java.time.Instant callerDeadline) throws IOException {
                    if (failRead) throw new IOException("held runtime source unavailable");
                    assertEquals(List.of(RUNTIME), selected.runtimeSources()); assertEquals(MACHINE, current.machineId());
                }
            }, (id, body) -> { output = body.clone(); return ref("fixture-output-" + id, badOutput ? bytes("wrong-source") : body); });
            session = new Session(this);
        }
    }
    /** Fake storage exercises order and the real verifier; it never claims physical-file/writer qualification. */
    private static final class Session implements ContinuityStorePort.Session {
        private final Fixture fixture;
        private ContinuityState state;
        private DomainBodies.BodyRef bodyRef;
        private byte[] body;
        private int commits;
        private boolean noChange;
        private boolean rejectWriter;
        private byte[] cadenceBytes;
        private DomainBodies.BodyRef cadenceRef;
        private Session(Fixture fixture) {
            this.fixture = fixture; body = fixture.original.clone(); bodyRef = bodyRef(fixture.input.previousBody());
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("start_date_raw", RAW); row.put("target_date_raw", RAW + 100 * 24);
            row.put("target_days", 100); row.put("status", "running"); row.put("last_settled_cycles", 0); row.put("last_settled_date_raw", RAW);
            state = DomainBodies.reduceImport(ContinuityState.fromJson(row, MACHINE), bodyRef);
        }
        private void installCadence(org.xar.ck3.control.planning.optionalcadence.CadenceModels.State cadence) {
            cadenceBytes = org.xar.ck3.control.planning.optionalcadence.CadenceJson.writeState(cadence);
            ExactRef ref = ref("fixture-original-cadence-body", cadenceBytes);
            cadenceRef = new DomainBodies.BodyRef(DomainBodies.Slot.OPTIONAL_CADENCE,
                    org.xar.ck3.control.planning.optionalcadence.CadenceModels.SCHEMA, ref, nativeId(ref), List.of(PRODUCER));
            state = DomainBodies.reduceImport(state, cadenceRef);
        }
        private static DomainBodies.BodyRef bodyRef(ExactRef ref) { return new DomainBodies.BodyRef(DomainBodies.Slot.CROWN, CONTRACT, ref, nativeId(ref), List.of(PRODUCER)); }
        private void replaceBody(byte[] replacement) { body = replacement.clone(); bodyRef = bodyRef(ref("another-original-body", body)); state = DomainBodies.reduceImport(state, bodyRef); }
        @Override public void requireWriter(Path expected) throws IOException { if (rejectWriter || !LOCK.equals(expected)) throw new IOException("another writer/escaped session"); }
        @Override public WriterContracts.Pin capturePin(ExactRef reference, int maximumBytes) { return new WriterContracts.Pin(reference, nativeId(reference)); }
        @Override public void verifyPin(WriterContracts.Pin pin) { }
        @Override public WriterContracts.Head head() { return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false); }
        @Override public ExactRef persistedHead() { return ref("fixture-head", state.canonicalBytes()); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { throw new IOException("no action writer permitted"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { throw new IOException("no action writer permitted"); }
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) {
            if (slot == DomainBodies.Slot.OPTIONAL_CADENCE && cadenceRef != null)
                return new DomainBodies.Available(cadenceRef, cadenceBytes, persistedHead(), List.of());
            assertEquals(DomainBodies.Slot.CROWN, slot);
            return new DomainBodies.Available(bodyRef, ContinuityJson.canonical(object(body)), persistedHead(), List.of());
        }
        @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request) throws IOException {
            String checked = fixture.service.verify(head(), Optional.of(bodyRef), request, fixture.output);
            return new DomainBodies.PreparedImport(head(), request, new WriterContracts.Pin(request.originalBody(), nativeId(request.originalBody())), List.of(), List.of(), checked);
        }
        @Override public WriterContracts.Receipt commitImport(DomainBodies.PreparedImport prepared) throws IOException {
            String checked = fixture.service.verify(head(), Optional.of(bodyRef), prepared.request(), fixture.output);
            assertEquals(prepared.preconditionDigest(), checked); commits++;
            if (noChange) return new WriterContracts.Receipt(WriterContracts.Disposition.NO_CHANGE, state, "b".repeat(64), 0, false);
            body = fixture.output.clone(); bodyRef = bodyRef(prepared.request().originalBody()); state = DomainBodies.reduceImport(state, bodyRef);
            return new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED, state, "b".repeat(64), 1, false);
        }
    }
    private static WriterContracts.FileIdentity nativeId(ExactRef ref) { return new WriterContracts.FileIdentity("1", "9007199254740993", "134371375868945259", "2026-10-23T17:40:00Z", ref.bytes()); }
    private static Set<String> fields(ObjectNode row) { return row.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toUnmodifiableSet()); }
    private static ObjectNode object(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, CrownRetryPublication.MAX_BODY_BYTES); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String path, byte[] raw) {
        try { return new ExactRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
