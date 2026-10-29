package org.xar.ck3.control.military.projectedcontact;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.Decision;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.DefenderConstructorZero;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.Frame;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.IncomingAttackerEntry;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NeedsQuery;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NewEncounter;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.NoContact;
import org.xar.ck3.control.military.projectedcontact.IndexedContactIngress.ResumeExisting;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.CapturedRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRow;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.HistoryIdentity;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Invalidation;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Outcome;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.SourceIdentity;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Unknown;

/** Uses exact original-producer goldens; the added role/context cases are explicitly derived fixtures. */
final class IndexedContactIngressTest {
    private static final ObjectMapper WIRE = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private static final SourceIdentity SOURCE = new SourceIdentity("synthetic-test-machine", "synthetic-1.20.0.4",
            "1".repeat(64), "2".repeat(64), "3".repeat(64));
    private static final HistoryIdentity HISTORY = new HistoryIdentity("synthetic-restored-branch",
            BigInteger.valueOf(4), new BigInteger("9007199254740997"));

    private static JsonNode corpus() throws IOException {
        try (InputStream input = IndexedContactIngressTest.class.getResourceAsStream("/projectedcontact/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("original producer golden missing"); }
            return WIRE.readTree(input);
        }
    }
    private static ObjectNode input(String name) throws IOException {
        for (JsonNode row : corpus().get("cases")) {
            if (row.get("name").asText().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); }
        }
        throw new IOException("missing original case " + name);
    }
    private static byte[] wire(JsonNode value) throws IOException { return WIRE.writeValueAsBytes(value); }
    private static Current context(ProjectedContactCodec.Input input) {
        return new Current(SOURCE, input.snapshot(), HISTORY, Invalidation.NONE);
    }
    private static Current context(byte[] raw) { return context(ProjectedContactCodec.decode(raw)); }
    private static ObjectNode scope(ObjectNode input) {
        return (ObjectNode) input.get("query_rows").get(0).get("result").get("projected_contact_scope");
    }

    @Test void exactOriginalProducerGoldenAndCompleteSelectionOutput() throws IOException, NoSuchAlgorithmException {
        try (InputStream stream = IndexedContactIngressTest.class.getResourceAsStream("/projectedcontact/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("original producer golden missing"); }
            byte[] original = stream.readAllBytes();
            assertEquals(66046, original.length);
            assertEquals("94f03161aec8247ad55ad3bcb4a2db1dec3d741ba77e5dd27b6886f1877e293d",
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        }
        JsonNode cases = corpus().get("cases"); assertEquals(30, cases.size());
        for (JsonNode row : cases) {
            byte[] raw = wire(row.get("input"));
            byte[] indexed = IndexedContactIngressCodec.select(raw, context(raw));
            assertEquals(row.get("expected"), StrictJson.parse(indexed), row.get("name").asText());
            assertArrayEquals(ProjectedContactCodec.select(raw), indexed, row.get("name").asText());
            Decision decision = IndexedContactIngressCodec.decide(raw, context(raw));
            assertEquals(decision, IndexedContactIngressCodec.decodeDecision(IndexedContactIngressCodec.encodeDecision(decision)));
        }
    }

    @Test void defenderUsesNativeConstructorZeroAndRetainsNonzeroIncomingGeometry() throws IOException {
        ObjectNode derived = input("native_order_defender"); scope(derived).put("incoming_adjacency_kind_raw", 3);
        byte[] raw = wire(derived);
        NewEncounter decision = assertInstanceOf(NewEncounter.class, IndexedContactIngressCodec.decide(raw, context(raw)));
        assertInstanceOf(DefenderConstructorZero.class, decision.geometry());
        assertNull(decision.attackerEntryProvinceId()); assertEquals(Integer.valueOf(0), decision.constructorAdjacencyKindRaw());
        assertEquals(30, decision.contactIncomingEntryProvinceId());
        assertEquals(3, decision.selection().projection().incomingAdjacencyKindRaw());
        assertEquals(List.of(22, 21), decision.selection().projection().attackerArmyIds());
        assertEquals(List.of(11), decision.selection().projection().defenderArmyIds());
        JsonNode encoded = StrictJson.parse(IndexedContactIngressCodec.encodeDecision(decision));
        assertTrue(encoded.get("attacker_entry_province_id").isNull());
        assertEquals(0, encoded.get("constructor_adjacency_kind_raw").intValue());
        assertFalse(encoded.has("advantage")); assertFalse(encoded.has("crossing_effect"));
        assertFalse(decision.actualArrivalObserved()); assertFalse(decision.futureContactAuthorized());
        assertFalse(decision.authorizesCommandReplay());
        assertEquals(decision.selection().projection(), ProjectedContactCodec.decodeScope(
                encoded.get("contact_selection").get("projection")));
    }

    @Test void attackerAndExistingCombatRemainSeparateFromDefenderConstructor() throws IOException {
        byte[] raw = wire(input("native_order_attacker"));
        NewEncounter attacker = assertInstanceOf(NewEncounter.class, IndexedContactIngressCodec.decide(raw, context(raw)));
        assertEquals(new IncomingAttackerEntry(30), attacker.geometry());
        assertEquals(Integer.valueOf(30), attacker.attackerEntryProvinceId()); assertNull(attacker.constructorAdjacencyKindRaw());
        byte[] joinRaw = wire(input("join_existing"));
        ResumeExisting join = assertInstanceOf(ResumeExisting.class, IndexedContactIngressCodec.decide(joinRaw, context(joinRaw)));
        assertEquals(join.selection().projection().selectedCurrentCombatId(), Integer.valueOf(join.selectedCombatId()));
        assertEquals(join.selection().projection().selectedCurrentCombatArrayIndex(), Integer.valueOf(join.selectedCombatArrayIndex()));
        JsonNode encoded = StrictJson.parse(IndexedContactIngressCodec.encodeDecision(join));
        assertFalse(encoded.has("attacker_entry_province_id")); assertFalse(encoded.has("constructor_adjacency_kind_raw"));
        assertFalse(join.futureContactAuthorized());
    }

    @Test void completeNoneAndUnknownNeverCollapseIntoTheSameDecision() throws IOException {
        byte[] raw = wire(input("complete_none"));
        assertInstanceOf(NoContact.class, IndexedContactIngressCodec.decide(raw, context(raw)));
        NeedsQuery unknown = assertInstanceOf(NeedsQuery.class,
                IndexedContactIngressCodec.decide(raw, new Unknown("native source provider unavailable")));
        assertEquals(Outcome.UNKNOWN_CONTEXT, unknown.reason());
        assertEquals("query_required", StrictJson.parse(IndexedContactIngressCodec.select(raw,
                new Unknown("source unavailable"))).get("status").asText());
    }

    @Test void allMutationAndUnknownOutcomesInvalidatePreparedIndex() throws IOException {
        byte[] raw = wire(input("native_order_defender")); ProjectedContactCodec.Input input = ProjectedContactCodec.decode(raw);
        Current origin = context(input); Frame frame = IndexedContactIngress.prepare(origin, input.queryRows());
        for (Invalidation invalidation : Invalidation.values()) {
            if (invalidation == Invalidation.NONE) { continue; }
            Current invalid = new Current(origin.source(), origin.snapshot(), origin.history(), invalidation);
            assertEquals(Outcome.INVALIDATED, assertInstanceOf(NeedsQuery.class, frame.select(invalid, input.request())).reason());
            Frame unavailable = IndexedContactIngress.prepare(invalid, input.queryRows());
            assertEquals(0, unavailable.sourceRowsVisited());
            assertInstanceOf(NeedsQuery.class, unavailable.select(origin, input.request()));
        }
        assertEquals(Outcome.UNKNOWN_CONTEXT, assertInstanceOf(NeedsQuery.class,
                frame.select(new Unknown("command result unknown"), input.request())).reason());
    }

    @Test void sameFrameRoleChangeNeedsNewHistoryAndNewIndex() throws IOException {
        ProjectedContactCodec.Input defender = ProjectedContactCodec.decode(wire(input("native_order_defender")));
        ProjectedContactCodec.Input attacker = ProjectedContactCodec.decode(wire(input("native_order_attacker")));
        Current origin = context(defender); Frame old = IndexedContactIngress.prepare(origin, defender.queryRows());
        Current changed = new Current(origin.source(), origin.snapshot(), new HistoryIdentity(
                HISTORY.restoredBranchIdentity(), HISTORY.latestCompletedAdvanceIndex(),
                HISTORY.observedHistoryTailIndex().add(BigInteger.ONE)), Invalidation.NONE);
        assertEquals(Outcome.CONTEXT_CHANGED, assertInstanceOf(NeedsQuery.class, old.select(changed, defender.request())).reason());
        List<QueryRow> effective = new ArrayList<>(defender.queryRows()); effective.addAll(attacker.queryRows());
        Frame fresh = IndexedContactIngress.prepare(changed, effective);
        NewEncounter selected = assertInstanceOf(NewEncounter.class, fresh.select(changed, attacker.request()));
        assertInstanceOf(IncomingAttackerEntry.class, selected.geometry());
        assertEquals(effective.size(), fresh.sourceRowsVisited());
        effective.clear();
        assertEquals(selected, fresh.select(changed, attacker.request()));
    }

    @Test void sourceAndSnapshotMismatchCannotUseValidCurrentHistory() throws IOException {
        byte[] raw = wire(input("native_order_defender")); ProjectedContactCodec.Input input = ProjectedContactCodec.decode(raw);
        Current origin = context(input); Frame frame = IndexedContactIngress.prepare(origin, input.queryRows());
        SourceIdentity changedSource = new SourceIdentity(SOURCE.machineId(), SOURCE.buildVersion(),
                "4".repeat(64), SOURCE.producerSourceSha256(), SOURCE.consumerClosureSha256());
        assertEquals(Outcome.CONTEXT_CHANGED, assertInstanceOf(NeedsQuery.class, frame.select(new Current(changedSource,
                origin.snapshot(), HISTORY, Invalidation.NONE), input.request())).reason());
        ObjectNode changed = input("native_order_defender"); ((ObjectNode) changed.get("snapshot")).put("date_raw", 1001);
        assertEquals(Outcome.UNKNOWN_CONTEXT, assertInstanceOf(NeedsQuery.class,
                IndexedContactIngressCodec.decide(wire(changed), origin)).reason());
        assertNotEquals(origin.snapshot(), ProjectedContactCodec.decode(wire(changed)).snapshot());
    }

    @Test void geometryConstructorAndStrictBoundaryRejectContradictions() throws IOException {
        byte[] defenderRaw = wire(input("native_order_defender"));
        Available defender = (Available) IndexedContactIngressCodec.decide(defenderRaw, context(defenderRaw)).selection();
        assertThrows(IllegalArgumentException.class, () -> new NewEncounter(defender, new IncomingAttackerEntry(30)));
        byte[] attackerRaw = wire(input("native_order_attacker"));
        Available attacker = (Available) IndexedContactIngressCodec.decide(attackerRaw, context(attackerRaw)).selection();
        assertThrows(IllegalArgumentException.class, () -> new NewEncounter(attacker, new DefenderConstructorZero()));
        assertThrows(IllegalArgumentException.class, () -> new NewEncounter(attacker, new IncomingAttackerEntry(29)));
        assertThrows(IllegalArgumentException.class, () -> new ResumeExisting(attacker));
        ObjectNode serialized = (ObjectNode) StrictJson.parse(IndexedContactIngressCodec.encodeDecision(
                IndexedContactIngressCodec.decide(defenderRaw, context(defenderRaw))));
        serialized.put("constructor_adjacency_kind_raw", true);
        byte[] wrongType = StrictJson.canonical(serialized);
        assertThrows(ContractViolationException.class, () -> IndexedContactIngressCodec.decodeDecision(wrongType));
        serialized.put("constructor_adjacency_kind_raw", 0); serialized.remove("attacker_entry_province_id");
        byte[] missingNullable = StrictJson.canonical(serialized);
        assertThrows(ContractViolationException.class, () -> IndexedContactIngressCodec.decodeDecision(missingNullable));
        for (String token : List.of("true", "11.0", "\"11\"", "null")) {
            ObjectNode value = input("native_order_attacker");
            ((ObjectNode) value.get("request")).set("subject_army_id", WIRE.readTree(token));
            byte[] invalid = wire(value);
            assertThrows(ContractViolationException.class, () -> IndexedContactIngressCodec.decide(invalid, context(attackerRaw)));
        }
    }

    @Test void completeKeyRetainsIncomingEntryCurrentOwnerAndPublicZero() throws IOException {
        byte[] raw = wire(input("public_cunit_slot_zero")); ProjectedContactCodec.Input input = ProjectedContactCodec.decode(raw);
        Frame frame = IndexedContactIngress.prepare(context(input), input.queryRows());
        NewEncounter selected = assertInstanceOf(NewEncounter.class, frame.select(context(input), input.request()));
        assertEquals(0, selected.selection().key().subjectArmyId());
        assertTrue(selected.selection().projection().subjectNativeCarmyId() > 0);
        CapturedRow row = assertInstanceOf(CapturedRow.class, input.queryRows().getFirst());
        assertEquals(row.scope().snapshotRevision(), input.snapshot().capture().nativeRevision());
        assertEquals(row.scope(), selected.selection().projection());
    }
}
