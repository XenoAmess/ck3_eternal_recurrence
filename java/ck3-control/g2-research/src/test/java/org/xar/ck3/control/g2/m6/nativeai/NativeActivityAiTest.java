package org.xar.ck3.control.g2.m6.nativeai;

import java.math.BigInteger;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.nativeai.NativeActivityAi.*;

final class NativeActivityAiTest {
    private static final int BASE = 0x29C55C0;
    private static Definition definition(int pointer, long id, int rankOne) {
        return new Definition(new TypePointer(BigInteger.valueOf(pointer)), id,
                List.of(999, rankOne, 0, -1, 0, 0, 0));
    }

    @Test void rankRebuildKeepsRegistryOrderAndDuplicatesButNeverRankZero() {
        Definition a = definition(16, 2, 12), disabled = definition(32, 3, 0);
        RankIndex index = rebuildIndex(List.of(a, disabled, a));
        assertEquals(List.of(), index.at(0));
        assertEquals(List.of(a, a), index.at(1));
        assertEquals(List.of(), index.at(3));
        assertThrows(IllegalArgumentException.class, () -> index.at(7));
    }

    @Test void nativeMonthTableAndSignedArithmeticAreExplicit() {
        assertEquals(0, monthOrdinal(BASE));
        assertEquals(0, monthOrdinal(BASE + 30 * 24));
        assertEquals(1, monthOrdinal(BASE + 31 * 24));
        assertEquals(2, monthOrdinal(BASE + 59 * 24));
        assertEquals(11, monthOrdinal(BASE + 364 * 24));
        assertEquals(12, monthOrdinal(BASE + 365 * 24));
    }

    @Test void pendingInvalidationIsConsumedOnceEvenWhenIntervalNotDue() {
        Definition a = definition(16, 1, 12);
        Invalidations original = new Invalidations(Set.of(a.pointer()));
        RecomputePlan plan = plan(rebuildIndex(List.of(a, a)), 1, original, 0, BASE, Mode.HOST);
        assertEquals(1, plan.required().size());
        assertEquals(RecomputeReason.CONSUMED_INVALIDATION, plan.required().get(0).reason());
        assertTrue(plan.invalidationsAfterConsumption().pending().isEmpty());
        assertEquals(1, original.pending().size());
    }

    @Test void hostFiltersInclusivelyAtThresholdAndRejectsIncompleteEvaluationSet() {
        Definition a = definition(16, 0, 1), b = definition(32, 1, 1);
        RecomputePlan plan = plan(rebuildIndex(List.of(a, b)), 1, new Invalidations(Set.of()),
                0, BASE, Mode.HOST);
        assertEquals(2, plan.required().size());
        List<Evaluation> evaluations = List.of(new Scored(plan.required().get(0), 100),
                new GateRejected(plan.required().get(1)));
        assertEquals(1, filter(plan, evaluations, 100).size());
        assertThrows(IllegalArgumentException.class, () -> filter(plan, List.of(), 100));
        assertThrows(IllegalArgumentException.class, () -> filter(plan,
                List.of(evaluations.get(1), evaluations.get(0)), 100));
    }

    @Test void inspectionForcesRecomputeAndPreservesNegativeRejectedScore() {
        Definition a = definition(16, 1, 12);
        RecomputePlan plan = plan(rebuildIndex(List.of(a)), 1, new Invalidations(Set.of()),
                0, BASE, Mode.INSPECTION);
        assertEquals(RecomputeReason.INSPECTION_FORCED, plan.required().get(0).reason());
        assertEquals(-1000, filter(plan, List.of(new GateRejected(plan.required().get(0))),
                9999).get(0).score());
    }

    @Test void actualScore100DoesNotPassNativeRoll100And101Does() {
        Definition a = definition(16, 0, 1);
        RequiredEvaluation requirement = plan(rebuildIndex(List.of(a)), 1,
                new Invalidations(Set.of()), 0, BASE, Mode.HOST).required().get(0);
        Selection hundred = select(List.of(new Candidate(requirement, 100)), 186);
        assertEquals(100, hundred.roll().orElseThrow());
        assertEquals(1547708543, hundred.randomCounterAfter());
        assertFalse(hundred.passesScoreRoll());
        assertTrue(select(List.of(new Candidate(requirement, 101)), 186).passesScoreRoll());
        assertFalse(select(List.of(), 186).passesScoreRoll());
    }

    @Test void shuffleTieIsDeterministicAndMaximumUsesSignedScore() {
        Definition a = definition(16, 0, 1), b = definition(32, 1, 1);
        RecomputePlan plan = plan(rebuildIndex(List.of(a, b)), 1, new Invalidations(Set.of()),
                0, BASE, Mode.HOST);
        Candidate ca = new Candidate(plan.required().get(0), 101);
        Candidate cb = new Candidate(plan.required().get(1), 101);
        Selection tie = select(List.of(ca, cb), 0);
        assertEquals(tie.shuffled().get(0), tie.maximum().orElseThrow());
        assertEquals(tie, select(List.of(ca, cb), 0));
        assertEquals(cb, select(List.of(new Candidate(ca.requirement(), Integer.MIN_VALUE), cb),
                0).maximum().orElseThrow());
    }

    @Test void pointerHashIncludesAllEightBytesWithoutDecimalRounding() {
        TypePointer pointer = new TypePointer(new BigInteger("1311768467463790320"));
        assertEquals("1311768467463790320", pointer.decimal());
        assertEquals(-1144508555, typeKeyHash(pointer));
        assertThrows(IllegalArgumentException.class, () -> new TypePointer(BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,
                () -> new TypePointer(BigInteger.ONE.shiftLeft(64)));
    }

    @Test void normalRecomputeConsumesOnlyPendingSetAndKeepsCooldownProjectionIndependent() {
        Definition a = definition(16, 1, 12);
        RawCooldowns cooldowns = new RawCooldowns(Map.of(a.pointer(), BASE + 240));
        ActivityMemory before = new ActivityMemory(cooldowns, new Invalidations(Set.of(a.pointer())));
        RecomputePlan plan = plan(rebuildIndex(List.of(a)), 1, before.invalidations(), 0, BASE, Mode.HOST);
        assertTrue(plan.invalidationsAfterConsumption().pending().isEmpty());
        assertTrue(cooldownBlocked(before.cooldowns(), a.pointer(), BASE));
        assertFalse(cooldownBlocked(before.cooldowns(), a.pointer(), BASE + 240));
        assertEquals(BASE + 240, before.cooldowns().rawDates().get(a.pointer()));
        assertEquals(1, before.invalidations().pending().size());
    }

    @Test void actualForceEffectClearsCooldownAndMarksTypeThroughDistinctContainers() {
        Definition a = definition(16, 1, 12);
        ActivityMemory before = new ActivityMemory(new RawCooldowns(Map.of(a.pointer(), BASE + 240)),
                new Invalidations(Set.of()));
        ActivityMemory forced = projectForcedReevaluation(before, a.pointer());
        assertFalse(cooldownBlocked(forced.cooldowns(), a.pointer(), BASE));
        assertEquals(Set.of(a.pointer()), forced.invalidations().pending());
        assertTrue(cooldownBlocked(before.cooldowns(), a.pointer(), BASE));
        assertTrue(before.invalidations().pending().isEmpty());
        RawCooldowns written = projectCooldownWrite(forced.cooldowns(), a.pointer(), BASE, 7);
        assertEquals(BASE + 168, written.rawDates().get(a.pointer()));
        assertEquals(Set.of(a.pointer()), forced.invalidations().pending());
    }

    @Test void propertyContractMatchesActualPinnedParserInstructionBytes() throws IOException {
        try (var input = getClass().getResourceAsStream("/m6native/source05.json")) {
            assertNotNull(input, "Root selected graph must include the actual source fixture");
            var source = StrictJson.parse(input.readAllBytes(), 200000);
            assertEquals(EXE_SHA256, source.path("exe").path("sha256").textValue());
            var rows = source.get("property_binding_instructions");
            assertNotNull(rows);
            assertTrue(rows.isArray());
            Set<Property> seen = new HashSet<>();
            for (var row : rows) {
                Property property = Property.valueOf(row.get("property").textValue());
                assertTrue(seen.add(property));
                byte[] field = HexFormat.of().parseHex(row.get("field").get("bytes_hex").textValue());
                assertEquals(7, field.length);
                assertEquals(0x48, Byte.toUnsignedInt(field[0]));
                int opcode = Byte.toUnsignedInt(field[1]);
                assertTrue(opcode == 0x8D || opcode == 0x81);
                int displacement = ByteBuffer.wrap(field, 3, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
                assertEquals(property.objectOffset(), 0x3F18 + displacement);
                byte[] token = HexFormat.of().parseHex(row.get("token").get("bytes_hex").textValue());
                int tokenOffset;
                if (token.length == 5) {
                    assertEquals(0xB9, Byte.toUnsignedInt(token[0]));
                    tokenOffset = 1;
                } else {
                    assertEquals(7, token.length);
                    assertEquals(0x41, Byte.toUnsignedInt(token[0]));
                    assertEquals(0x81, Byte.toUnsignedInt(token[1]));
                    tokenOffset = 3;
                }
                assertEquals(property.runtimeToken(), ByteBuffer.wrap(token, tokenOffset, 4)
                        .order(ByteOrder.LITTLE_ENDIAN).getInt());
            }
            assertEquals(Set.of(Property.values()), seen);
        }
    }
}
