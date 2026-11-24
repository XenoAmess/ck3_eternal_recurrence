package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundaries only; no Cpp original, inventory probe, action or authority is synthesized. */
final class NativeCurrentLivingInventorySlotBoundsTest {
    private static List<CurrentLivingInventoryQuerySource.Numeric> numeric() {
        return List.of(Long.MIN_VALUE, -1L, 0L, Long.MAX_VALUE).stream()
                .map(raw -> new CurrentLivingInventoryQuerySource.Numeric(
                        CurrentLivingInventoryQuerySource.NumericState.NUMERIC, 1, Optional.of(raw))).toList();
    }

    private static List<CurrentLivingInventoryQuerySource.Reference> references() {
        var result = new ArrayList<CurrentLivingInventoryQuerySource.Reference>();
        for (var role : CurrentLivingInventoryQuerySource.ReferenceRole.values()) {
            boolean selected = role == CurrentLivingInventoryQuerySource.ReferenceRole.SELECTED_ARTIFACT;
            result.add(new CurrentLivingInventoryQuerySource.Reference(role,
                    selected ? CurrentLivingInventoryQuerySource.ReferenceState.ABSENT
                            : CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,
                    selected ? 0 : 36, selected ? Optional.empty()
                            : Optional.of(role == CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_TARGET ? 0L : 7L)));
        }
        return result;
    }

    private static List<CurrentLivingInventoryQuerySource.Slot> slots(int count) {
        var slots = new ArrayList<CurrentLivingInventoryQuerySource.Slot>();
        for (int i = 0; i < count; i++) {
            boolean weapon = i == count - 1;
            slots.add(new CurrentLivingInventoryQuerySource.Slot(weapon ? "weapon" : "slot_" + i,
                    weapon ? Optional.of(0L) : Optional.empty()));
        }
        return slots;
    }

    private static CurrentLivingInventoryQuerySource source(long actor, int count) {
        var target = new CurrentLivingInventoryQuerySource.Artifact(0L, actor, "sword", 0, true, numeric());
        var unrelated = new CurrentLivingInventoryQuerySource.Artifact(0xffff_fffeL, actor, "a\u0000b\n", -2, false, numeric());
        return new CurrentLivingInventoryQuerySource(actor, List.of(target, unrelated), slots(count),
                Optional.of(count - 1), references(), true, true);
    }

    private static CurrentLivingInventoryQueryResult available(CurrentLivingInventoryQuerySource source) {
        var core = new CoreFrame.Prefix(0, 3, true, 1, true, true, (int) source.actorFullId(), true);
        var owner = new CurrentLetterResult.OwnerWitness(BigInteger.ONE, BigInteger.TWO, BigInteger.TEN, 7);
        return new CurrentLivingInventoryQueryResult(CurrentLivingInventoryQueryResult.Status.AVAILABLE, true,
                BigInteger.ONE, BigInteger.TWO, Optional.of(core), Optional.of(owner), Optional.of(source), Optional.empty());
    }

    @Test void complete32_36_64SlotsAndFinalWeaponIndexRoundTripWithoutTruncation() throws IOException {
        for (long actor : List.of(0L, 0xffff_fffeL)) {
            for (int count : List.of(32, 36, 64)) {
                var original = source(actor, count);
                var decoded = CurrentLivingInventoryQuerySource.decode(original.encode());
                assertEquals(original, decoded);
                assertEquals(count, decoded.slots().size());
                assertEquals(Optional.of(count - 1), decoded.weaponSlot());
                assertEquals("slot_0", decoded.slots().getFirst().key());
                assertEquals("weapon", decoded.slots().getLast().key());
                assertEquals(Optional.of(0L), decoded.slots().getLast().artifactFullId());
                assertEquals(Optional.of(7L), decoded.fixedReferences().get(1).artifactFullId());
                var frame = available(original);
                assertEquals(frame, CurrentLivingInventoryQueryResult.decode(frame.encode()));
                assertFalse(frame.effectAttempted());
                assertEquals(BigInteger.ZERO, frame.claimSequence());
                assertTrue(frame.encode().bytes().length < NativeWire.MAXIMUM_FRAME_BYTES);
                System.out.println("LIVING_SLOT64_JAVA_DATA count=" + count + " actor=" + actor
                        + " result_utf8_bytes=" + frame.encode().bytes().length);
            }
        }
    }

    @Test void sixtyFiveSlotsAndWrongOrOutOfRangeWeaponIndexFailInsteadOfDroppingRows() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> source(0, 65));
        var original = source(0, 64);
        var tooMany = original.encode();
        ((ArrayNode) tooMany.get("slots")).addObject().put("key", "extra_65").putNull("artifact_full_id");
        assertEquals(65, tooMany.path("slots").size());
        assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(tooMany));
        for (int badIndex : List.of(-1, 31, 64)) {
            var wrong = original.encode().put("weapon_slot", badIndex);
            assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(wrong));
        }
        assertEquals(Optional.of(63), CurrentLivingInventoryQuerySource.decode(original.encode()).weaponSlot());
    }

    @Test void largerCensusStillRequiresUniqueOwnedSlotsAndCompleteDoubleSample() throws IOException {
        var original = source(0, 36);
        var duplicate = original.encode();
        ((ObjectNode) duplicate.path("slots").get(1)).put("key", "slot_0");
        assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(duplicate));
        for (long badId : List.of(77L, 0xffff_ffffL)) {
            var missingOwned = original.encode();
            ((ObjectNode) missingOwned.path("slots").get(35)).put("artifact_full_id", badId);
            assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(missingOwned));
        }
        for (String flag : List.of("complete_inventory", "sampled_twice")) {
            var incomplete = original.encode().put(flag, false);
            assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(incomplete));
        }
        var foreignOwner = original.encode();
        ((ObjectNode) foreignOwner.path("artifacts").get(0)).put("owner_full_id", 1L);
        assertThrows(IOException.class, () -> CurrentLivingInventoryQuerySource.decode(foreignOwner));
    }
}
