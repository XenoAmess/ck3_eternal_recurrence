package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.*;

/** Unchanged original producer fixture -> actual shared codec -> read domain codec -> public decimal64.
 * The outer eight-field envelope follows the pinned original C++ producer and is a test assembly, not a capture.
 * These pure tests do not replace the Root coordinator/writer-session/original transport acceptance.
 */
final class FactionAlertReadServiceTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    private static final String FIXTURE_SHA = "41b30820281d4d58163826fb1c6aa7c5f487323737b37e8f4e60e9647e057837";
    private static final ExactRef REF = new ExactRef("fixture-source", 1, "a".repeat(64));
    private record Vector(ObjectNode nativeResult, RawJson wars, Selection selection) {
        RawJson raw() { return new RawJson(StrictJson.canonical(nativeResult)); }
    }
    private static JsonNode parse(RawJson raw) { return StrictJson.parse(raw.bytes(), 1_000_000); }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static Vector vector(BigInteger revision) throws Exception {
        byte[] bytes;
        try (var input = FactionAlertReadServiceTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(input, "NOT EXECUTED: selected wave2-finance original test resource must be routed by the native-transport POM");
            bytes = input.readAllBytes();
        }
        assertEquals(FIXTURE_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode root = StrictJson.parse(bytes, 1_000_000); JsonNode selected = null;
        for (JsonNode c : root.get("cases")) if (c.get("name").textValue().equals("exact-build-1.20.0.4")) selected = c;
        assertNotNull(selected);
        ObjectNode frame = (ObjectNode) root.get("bases").get(selected.get("base").textValue()).deepCopy();
        for (JsonNode operation : selected.get("operations")) {
            String path = operation.get("path").textValue(); int slash = path.lastIndexOf('/');
            ObjectNode parent = slash == 0 ? frame : (ObjectNode) frame.at(path.substring(0, slash));
            if (operation.path("remove").asBoolean(false)) parent.remove(path.substring(slash + 1));
            else parent.set(path.substring(slash + 1), operation.get("value").deepCopy());
        }
        frame.put("snapshot_revision", revision);
        ObjectNode nativeResult = StrictJson.object().put("step", STEP).put("accepted", true).put("status", frame.get("status").textValue())
                .put("query_sequence", MAX).put("snapshot_revision", revision).put("player_faction_alerts_ready", frame.at("/readiness/alert_ready").booleanValue())
                .put("backend_id", "native-headless"); nativeResult.set("player_faction_alerts", frame);
        RawJson wars = new RawJson(StrictJson.canonical(selected.get("active_wars")));
        Instant now = Instant.parse("2026-10-24T00:00:00Z");
        var source = new G2Source("fixture-machine", now.toString(), "1.20.0.4", REF);
        var identity = new JointBudgetSelector.Frame(frame.get("player_character_id").bigIntegerValue(), revision, frame.get("date_raw").bigIntegerValue());
        var binding = new JointBudgetSelector.ProposalFrame(identity, "native:fixture", BigInteger.valueOf(9), "fixture-episode");
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), binding, 1);
        var context = new Context(before, source, "fixture-session", now.plusSeconds(60), new SameFrameWars(before, wars), "native-headless");
        return new Vector(nativeResult, wars, new Selection(new Query(BigInteger.valueOf(9)), context));
    }
    @Test void originalSharedProducerPreservesCurrentNativePowerAndUnknownClock() throws Exception {
        Vector v = vector(BigInteger.valueOf(41)); RawJson original = v.raw();
        Observation observation = decodeToken(v.selection(), original);
        var shared = FactionAlertsBoundary.normalizeCurrentNativeResult(original.bytes(),
                new FactionAlertModel.ExpectedFrame(v.selection().context().dateRaw(), BigInteger.valueOf(41), java.util.Optional.of(FactionAlertModel.Build.CK3_12004)), v.wars().bytes());
        var expected = shared.projection();
        assertEquals(shared.querySequence(), observation.querySequence());
        assertEquals(expected.frame(), observation.frame()); assertArrayEquals(expected.normalizedAlertJson(), observation.normalizedAlert().bytes());
        assertArrayEquals(original.bytes(), observation.originalResult().bytes());
        assertFalse(observation.exactDemandClockObserved()); assertFalse(observation.componentStrengthCachesObserved());
        var available = assertInstanceOf(FactionAlertModel.Available.class, observation.frame());
        assertTrue(available.targetingFactions().stream().anyMatch(f -> f.power().raw() == 9_100_000));
        ((ObjectNode) v.nativeResult().at("/player_faction_alerts/targeting_factions/1")).put("months_until_max_discontent", 0);
        assertFalse(decodeToken(v.selection(), v.raw()).exactDemandClockObserved());
    }
    @Test void fullOriginalEnvelopeAndActorFrameMirrorsRemainStrict() throws Exception {
        Vector v = vector(BigInteger.valueOf(41));
        var names = new java.util.ArrayList<String>(); v.nativeResult().fieldNames().forEachRemaining(names::add);
        for (String field : names) {
            ObjectNode changed = v.nativeResult().deepCopy(); changed.remove(field);
            assertThrows(IllegalArgumentException.class, () -> decodeToken(v.selection(), new RawJson(StrictJson.canonical(changed))), field);
        }
        for (String field : List.of("query_sequence", "snapshot_revision")) for (String token : List.of("true", "41.0", "\"41\"", "null", "-1", "18446744073709551616")) {
            ObjectNode changed = v.nativeResult().deepCopy(); changed.set(field, parse(raw("{\"v\":" + token + "}")).get("v"));
            assertThrows(IllegalArgumentException.class, () -> decodeToken(v.selection(), new RawJson(StrictJson.canonical(changed))), field + token);
        }
        ObjectNode wrong = v.nativeResult().deepCopy().put("player_faction_alerts_ready", false);
        assertThrows(IllegalArgumentException.class, () -> decodeToken(v.selection(), new RawJson(StrictJson.canonical(wrong))));
        ObjectNode actor = v.nativeResult().deepCopy(); ((ObjectNode) actor.get("player_faction_alerts")).put("player_character_id", 1);
        assertThrows(IllegalArgumentException.class, () -> decodeToken(v.selection(), new RawJson(StrictJson.canonical(actor))));
        ObjectNode extra = v.nativeResult().deepCopy().put("exact_deadline", 90);
        assertThrows(IllegalArgumentException.class, () -> decodeToken(v.selection(), new RawJson(StrictJson.canonical(extra))));
        Context c = v.selection().context();
        var missingWars = new Context(c.before(), c.source(), c.sessionId(), c.deadline(), new SameFrameWars(c.before(), raw("[]")), c.snapshotBackendId());
        assertThrows(IllegalArgumentException.class, () -> decodeToken(new Selection(v.selection().query(), missingWars), v.raw()));
    }
    @Test void fullOriginalFrameMustOwnTheSameExactResultTokenAndRequest() throws Exception {
        Vector v = vector(BigInteger.valueOf(41));
        ObjectNode envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "faction-read").put("ok", true);
        envelope.set("result", v.nativeResult().deepCopy()); RawJson full = new RawJson(StrictJson.canonical(envelope));
        assertEquals(decodeToken(v.selection(), v.raw()), decodeOriginal(v.selection(), "faction-read", full, v.raw()));
        assertThrows(IllegalArgumentException.class, () -> decodeOriginal(v.selection(), "another-read", full, v.raw()));
        ObjectNode token = v.nativeResult().deepCopy().put("query_sequence", BigInteger.ONE);
        assertThrows(IllegalArgumentException.class, () -> decodeOriginal(v.selection(), "faction-read", full, new RawJson(StrictJson.canonical(token))));
        ObjectNode falseAck = envelope.deepCopy().put("ok", false);
        assertThrows(IllegalArgumentException.class, () -> decodeOriginal(v.selection(), "faction-read", new RawJson(StrictJson.canonical(falseAck)), v.raw()));
        ObjectNode extra = envelope.deepCopy().put("unknown", 1);
        assertThrows(IllegalArgumentException.class, () -> decodeOriginal(v.selection(), "faction-read", new RawJson(StrictJson.canonical(extra)), v.raw()));
    }
    @Test void decimal64PublicRoundtripDoesNotMutateOriginalNumericPacket() throws Exception {
        Vector v = vector(MAX); Observation original = decodeToken(v.selection(), v.raw());
        RawJson encoded = encodePublic(v.selection(), original); JsonNode n = parse(encoded);
        assertEquals(MAX.toString(), n.get("query_sequence").textValue()); assertEquals(MAX.toString(), n.get("snapshot_revision").textValue());
        assertEquals(MAX.toString(), n.at("/player_faction_alerts/snapshot_revision").textValue());
        PublicProjection restored = decodePublic(v.selection(), encoded);
        assertEquals(original.frame(), restored.frame()); assertEquals(original.normalizedAlert(), restored.normalizedAlert());
        assertEquals(original.originalResultSha256(), restored.originalResultSha256());
        assertTrue(parse(original.originalResult()).get("query_sequence").isIntegralNumber()); assertArrayEquals(v.raw().bytes(), original.originalResult().bytes());
        for (String wrong : List.of("00", "+41", "18446744073709551616")) {
            ObjectNode changed = ((ObjectNode) n).deepCopy().put("snapshot_revision", wrong);
            assertThrows(IllegalArgumentException.class, () -> decodePublic(v.selection(), new RawJson(StrictJson.canonical(changed))));
        }
        ObjectNode floating = ((ObjectNode) n).deepCopy().put("query_sequence", MAX.doubleValue());
        assertThrows(IllegalArgumentException.class, () -> decodePublic(v.selection(), new RawJson(StrictJson.canonical(floating))));
    }
    @Test void publicInputRequiresOneNamedRevisionAndNeverRoundsNumbers() {
        assertEquals(new Query(MAX), decodeQuery(raw("{\"expected_revision\":\"18446744073709551615\"}")));
        assertEquals(new Query(BigInteger.valueOf(9)), decodeQuery(raw("{\"expected_revision\":9}")));
        assertEquals(new Query(MAX), decodeQuery(encodeQuery(new Query(MAX))));
        for (String input : List.of("{}", "{\"expected_revision\":null}", "{\"expected_revision\":true}", "{\"expected_revision\":9.0}",
                "{\"expected_revision\":9007199254740992}", "{\"expected_revision\":\"09\"}", "{\"expected_revision\":9,\"other\":0}"))
            assertThrows(IllegalArgumentException.class, () -> decodeQuery(raw(input)));
    }
    @Test void publicProjectionRejectsDetachedFrameNormalizedAlertAndSequence() throws Exception {
        Vector v = vector(BigInteger.valueOf(41)); Observation original = decodeToken(v.selection(), v.raw());
        ObjectNode changedToken = v.nativeResult().deepCopy().put("query_sequence", BigInteger.ONE);
        Observation another = decodeToken(v.selection(), new RawJson(StrictJson.canonical(changedToken)));
        var detachedSequence = new Observation(another.querySequence(), original.frame(), original.normalizedAlert(),
                original.originalResult(), original.originalResultSha256());
        assertThrows(IllegalArgumentException.class, () -> encodePublic(v.selection(), detachedSequence));
        ObjectNode changedAlert = ((ObjectNode) parse(original.normalizedAlert())).deepCopy();
        ((ObjectNode) changedAlert.at("/targeting_factions/1")).put("months_until_max_discontent", 0);
        var detachedAlert = new Observation(original.querySequence(), original.frame(), new RawJson(StrictJson.canonical(changedAlert)),
                original.originalResult(), original.originalResultSha256());
        assertThrows(IllegalArgumentException.class, () -> encodePublic(v.selection(), detachedAlert));
        ObjectNode otherNative = v.nativeResult().deepCopy();
        ((ObjectNode) otherNative.at("/player_faction_alerts/targeting_factions/1")).put("months_until_max_discontent", 0);
        Observation otherFrame = decodeToken(v.selection(), new RawJson(StrictJson.canonical(otherNative)));
        var detachedFrame = new Observation(original.querySequence(), otherFrame.frame(), original.normalizedAlert(),
                original.originalResult(), original.originalResultSha256());
        assertThrows(IllegalArgumentException.class, () -> encodePublic(v.selection(), detachedFrame));
        Context c = v.selection().context();
        var wrongDateIdentity = new JointBudgetSelector.Frame(BigInteger.valueOf(c.player()), c.nativeRevision(),
                BigInteger.valueOf(c.dateRaw()).add(BigInteger.ONE));
        var wrongFrame = new JointBudgetSelector.ProposalFrame(wrongDateIdentity, c.before().frame().snapshotId(),
                c.before().frame().revision(), c.before().frame().episodeRunId());
        var wrongBefore = new ProposalLifecycle.ObservationIdentity(c.before().machineId(), c.before().game(), wrongFrame, c.before().observationVersion());
        var wrongContext = new Context(wrongBefore, c.source(), c.sessionId(), c.deadline(), new SameFrameWars(wrongBefore, c.wars().activeWars()), c.snapshotBackendId());
        assertThrows(IllegalArgumentException.class, () -> encodePublic(new Selection(v.selection().query(), wrongContext), original));
        assertEquals(original.frame(), decodePublic(v.selection(), encodePublic(v.selection(), original)).frame());
        assertFalse(otherFrame.exactDemandClockObserved());
    }
    @Test void offlineOriginalReceiptUsesExactArchivedSelectionWithoutCurrentProvider() throws Exception {
        Vector v = vector(BigInteger.valueOf(41)); Context c = v.selection().context();
        var binding = new GuardEvidence(c.before(), c.source(), c.sessionId(), BigInteger.ONE, new OperationKey(STEP),
                REF, REF, "fixture-authority", c.deadline().minusSeconds(30), c.deadline());
        var guard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
        ObjectNode envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "archived-faction-read").put("ok", true);
        envelope.set("result", v.nativeResult().deepCopy()); RawJson full = new RawJson(StrictJson.canonical(envelope));
        byte[] packet = ByteBuffer.allocate(4 + full.bytes().length).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(full.bytes().length).put(full.bytes()).array();
        var ack = new NativeActionPort.AckReceived("archived-faction-read", true, java.util.Optional.of(v.raw()), full, packet);
        var receipt = new PlanningReadReceipt(request(v.selection()), contractId(v.selection()), ack.requestId(), guard, guard, ack);
        Observation expected = decodeToken(v.selection(), v.raw());
        assertEquals(expected, decodeArchivedOriginal(receipt, c.wars(), c.snapshotBackendId()));
        // Resolve the real installed Family and its explicit archival callback without any Current/read port.
        Contracts owner = new Contracts(REF, REF);
        var catalog = new RootReadContractCatalog(List.of(), owner.families());
        var installed = owner.issue(catalog, v.selection());
        assertTrue(installed.hasPureReplay());
        assertEquals(expected, installed.replay(receipt));
        assertEquals(installed.decode(receipt), installed.replay(receipt));
        var wrongContract = new PlanningReadReceipt(receipt.request(), receipt.contractId() + "-suffix", receipt.requestId(), guard, guard, ack);
        assertThrows(IllegalArgumentException.class, () -> decodeArchivedOriginal(wrongContract, c.wars(), c.snapshotBackendId()));
        assertThrows(IllegalArgumentException.class, () -> installed.replay(wrongContract));
        assertThrows(IllegalArgumentException.class, () -> decodeArchivedOriginal(receipt, c.wars(), "other-backend"));
        assertThrows(IllegalArgumentException.class, () -> decodeArchivedOriginal(receipt, new SameFrameWars(c.before(), raw("[]")), c.snapshotBackendId()));
        for (int offset : List.of(0, packet.length - 1)) {
            byte[] tampered = packet.clone(); tampered[offset] ^= 1;
            var detachedAck = new NativeActionPort.AckReceived(ack.requestId(), true, java.util.Optional.of(v.raw()), full, tampered);
            var detachedPacket = new PlanningReadReceipt(receipt.request(), receipt.contractId(), receipt.requestId(), guard, guard, detachedAck);
            assertThrows(IllegalArgumentException.class, () -> decodeArchivedOriginal(detachedPacket, c.wars(), c.snapshotBackendId()));
            assertThrows(IllegalArgumentException.class, () -> installed.replay(detachedPacket));
        }
        var drifted = new Selection(v.selection().query(), new Context(c.before(), c.source(), c.sessionId(),
                c.deadline().plusSeconds(1), c.wars(), c.snapshotBackendId()));
        assertThrows(IllegalArgumentException.class, () -> owner.issue(catalog, drifted).replay(receipt));
        assertArrayEquals(packet, receipt.original().originalPacket());
    }
    @Test void identicalInstalledFamilyIsRequiredAndCompleteContextOwnsContract() throws Exception {
        Vector v = vector(BigInteger.valueOf(41)); Contracts owner = new Contracts(REF, REF);
        var empty = new RootReadContractCatalog(List.of(), List.of());
        assertThrows(IllegalArgumentException.class, () -> owner.issue(empty, v.selection()));
        var installed = new RootReadContractCatalog(List.of(), owner.families());
        var contract = owner.issue(installed, v.selection()); assertSame(contract, owner.issue(installed, v.selection()));
        assertEquals(contractId(v.selection()), contract.contractId());
        assertEquals(STEP, contract.prepare(request(v.selection()), "faction-request").step());
        assertEquals("{}", new String(contract.prepare(request(v.selection()), "faction-request").additionalFields().bytes(), StandardCharsets.UTF_8));
        Context c = v.selection().context(); var later = new Context(c.before(), c.source(), c.sessionId(), c.deadline().plusSeconds(1), c.wars(), c.snapshotBackendId());
        var next = new Selection(v.selection().query(), later);
        assertNotEquals(contractId(v.selection()), contractId(next));
        assertNotSame(contract, owner.issue(installed, next));
        assertThrows(IllegalArgumentException.class, () -> contract.prepare(request(next), "faction-request"));
        assertThrows(IllegalArgumentException.class, () -> new Selection(new Query(BigInteger.valueOf(8)), c));
    }

    @Test void originalProducerToExecutionRetainsTheCompleteDriverEnvelope()throws Exception {
        Vector v=vector(MAX);Observation observed=decodeToken(v.selection(),v.raw());
        JsonNode result=parse(encodeExecution(v.selection(),observed));
        var expected=new java.util.HashSet<>(FactionAlertsBoundary.CURRENT_NATIVE_RESULT_FIELDS);
        expected.addAll(java.util.Set.of("queried_snapshot_id","queried_revision","queried_native_revision"));
        var actual=new java.util.HashSet<String>();result.fieldNames().forEachRemaining(actual::add);
        assertEquals(expected,actual);
        assertEquals(MAX.toString(),result.get("query_sequence").textValue());
        assertEquals(MAX.toString(),result.get("snapshot_revision").textValue());
        assertEquals(v.selection().context().before().frame().snapshotId(),result.get("queried_snapshot_id").textValue());
        assertEquals(v.selection().context().before().frame().revision().toString(),result.get("queried_revision").textValue());
        assertEquals(MAX.toString(),result.at("/player_faction_alerts/snapshot_revision").textValue());
        assertTrue(v.nativeResult().get("query_sequence").isIntegralNumber());
        assertEquals(v.raw(),observed.originalResult());
        assertEquals(result.get("status"),result.at("/player_faction_alerts/status"));
        assertEquals(result.get("player_faction_alerts_ready"),result.at("/player_faction_alerts/readiness/alert_ready"));
        assertFalse(result.has("public_wire_schema"));assertFalse(result.has("source"));assertFalse(result.has("binding"));
    }
    @Test void executionProjectionRejectsAnObservationChangedAfterOriginalDecode()throws Exception {
        Vector v=vector(MAX);Observation original=decodeToken(v.selection(),v.raw());
        ObjectNode changed=(ObjectNode)parse(original.normalizedAlert()).deepCopy();changed.put("date_raw",1);
        Observation tampered=new Observation(original.querySequence(),original.frame(),new RawJson(StrictJson.canonical(changed)),
                original.originalResult(),original.originalResultSha256());
        assertThrows(IllegalArgumentException.class,()->encodeExecution(v.selection(),tampered));
    }
}
