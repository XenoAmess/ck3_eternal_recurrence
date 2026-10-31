package org.xar.ck3.research.m3.manager177;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Cell;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Outcome;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Scene;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Step;

/** Independent finite literals from the six held normal fragments; calls stay opaque. */
public final class ManagerInitializerWitnessBook177 {
    private static final long BASE = 0x140000000L;
    private static final long GLOBAL = BASE + 0x5c6a4d0L;

    private ManagerInitializerWitnessBook177() { }

    private static Cell cell(long address, int width, long value) {
        return new Cell(address, width, value);
    }

    private static Step access(String kind, long address, long value) {
        return new Step(kind, new long[] { address, value }, 0L, List.of());
    }

    private static Step call(String kind, long returned, List<Cell> effects, long... arguments) {
        return new Step(kind, arguments, returned, effects);
    }

    /* A fixed literal sequence, shared only to avoid duplicating the identical constructor stores. */
    private static ArrayList<Step> prefix(long context, long object, long provider,
                                          List<Cell> lastMapEffects, long observedCapacity32) {
        return new ArrayList<>(List.of(
                access("R64", GLOBAL, 0L),
                call("CONTEXT", context, List.of(), 0x37635b6L),
                call("OBJECT", object, List.of(), 0x37635c3L, 0x210L),
                access("W64", object, 0L),
                access("W64", object + 8L, 0L),
                access("W64", object + 0x10L, 0L),
                access("W64", object + 0x18L, BASE + 0x54f2a78L),
                access("W8", object + 0x20L, 0L),
                call("PROVIDER", provider, List.of(), 0x37635edL),
                access("W64", object + 0x30L, provider),
                access("W64", object + 0x38L, 0L),
                access("W64", object + 0x48L, BASE + 0x54f2a80L),
                access("W8", object + 0x40L, 0L),
                access("W32", object + 0x44L, 0x3f666666L),
                access("W32", object + 0x50L, 0L),
                access("W64", object + 0x68L, BASE + 0x54de268L),
                access("W64", object + 0x58L, 0L),
                access("W64", object + 0x60L, 0L),
                access("W32", object + 0x70L, 0L),
                call("MAP", 0L, List.of(), 0x376362fL, object + 0x78L),
                call("MAP", 0L, List.of(), 0x376363bL, object + 0xd8L),
                call("MAP", 0L, List.of(), 0x3763647L, object + 0x138L),
                call("MAP", 0L, lastMapEffects, 0x3763653L, object + 0x198L),
                access("W64", object + 0x1f8L, 0L),
                access("W64", object + 0x208L, BASE + 0x54f2a88L),
                access("W64", object + 0x200L, 0L),
                access("R32", object + 0x10L, observedCapacity32)));
    }

    private static ArrayList<Cell> finalObject(long object, long provider, long data,
                                              long count32, long allocator) {
        return new ArrayList<>(List.of(
                cell(object, 8, 0L),
                cell(object + 8L, 8, data),
                cell(object + 0x10L, 4, 0x4e20L),
                cell(object + 0x14L, 4, count32),
                cell(object + 0x18L, 8, allocator),
                cell(object + 0x20L, 1, 0L),
                cell(object + 0x30L, 8, provider),
                cell(object + 0x38L, 8, 0L),
                cell(object + 0x40L, 1, 0L),
                cell(object + 0x44L, 4, 0x3f666666L),
                cell(object + 0x48L, 8, BASE + 0x54f2a80L),
                cell(object + 0x50L, 4, 0L),
                cell(object + 0x58L, 8, 0L),
                cell(object + 0x60L, 8, 0L),
                cell(object + 0x68L, 8, BASE + 0x54de268L),
                cell(object + 0x70L, 4, 0L),
                cell(object + 0x1f8L, 8, 0L),
                cell(object + 0x200L, 8, 0L),
                cell(object + 0x208L, 8, BASE + 0x54f2a88L)));
    }

    private static Scene guarded() {
        long observed = 0xff00112233445566L;
        return new Scene("guard-nonzero-no-other-access", BASE,
                List.of(cell(GLOBAL, 8, observed)),
                List.of(access("R64", GLOBAL, observed)),
                new Outcome(false, observed), List.of(cell(GLOBAL, 8, observed)));
    }

    private static Scene oldNullSkipReserve() {
        long context = 0x0000032200002000L;
        long object = 0x0000021100001000L;
        long provider = 0x0000043300003000L;
        // The final opaque MAP effect supplies the branch input after source's zero stores.
        ArrayList<Step> steps = prefix(context, object, provider,
                List.of(cell(object + 0x10L, 4, 0x4e20L)), 0x4e20L);
        steps.addAll(List.of(
                access("R64", context, 0L),
                access("W64", context, object),
                access("R64", context, object),
                access("W64", GLOBAL, object)));
        ArrayList<Cell> finals = finalObject(object, provider, 0L, 0L, BASE + 0x54f2a78L);
        finals.add(cell(context, 8, object));
        finals.add(cell(GLOBAL, 8, object));
        return new Scene("old-null-map-capacity-skips-reserve", BASE,
                List.of(cell(GLOBAL, 8, 0L), cell(context, 8, 0L)), List.copyOf(steps),
                new Outcome(true, object), List.copyOf(finals));
    }

    private static Scene oldNonNullCopyFreshFieldsAndPublish() {
        long context = 0x0000132200002000L;
        long object = 0x0000121100001000L;
        long provider = 0x0000143300003000L;
        long old = 0x8000044400004000L;
        long allocatorA = 0x0000055500005000L;
        long vtableA = 0x0000066600006000L;
        long allocateTarget = 0x0000077700007008L;
        long reserved = 0x0000088800008000L;
        long beforeCopyData = 0x0000099900009000L;
        long allocatorB = 0x80000aaa0000a000L;
        long vtableB = 0x80000bbb0000b000L;
        long releaseTarget = 0x80000ccc0000c010L;
        long afterCopyData = 0x80000ddd0000d000L;
        long published = 0xfedcba9876543210L;
        ArrayList<Step> steps = prefix(context, object, provider, List.of(
                cell(object + 0x10L, 4, 0xffffffffL),
                cell(object + 0x14L, 4, 3L),
                cell(object + 8L, 8, beforeCopyData),
                cell(object + 0x18L, 8, allocatorA)), 0xffffffffL);
        steps.addAll(List.of(
                access("R64", object + 0x18L, allocatorA),
                access("R64", allocatorA, vtableA),
                access("R64", vtableA + 8L, allocateTarget),
                call("ALLOC", reserved, List.of(cell(object + 0x14L, 4, 5L)),
                        0x3763692L, allocateTarget, allocatorA, 0x27100L, 8L),
                access("R32", object + 0x14L, 5L),
                access("R64", object + 8L, beforeCopyData),
                call("COPY", 0L, List.of(
                        cell(object + 0x14L, 4, 0x80000002L),
                        cell(object + 0x18L, 8, allocatorB),
                        cell(object + 8L, 8, afterCopyData)),
                        0x37636aeL, reserved, beforeCopyData, 0x28L),
                access("R32", object + 0x14L, 0x80000002L),
                access("R64", object + 0x18L, allocatorB),
                access("R64", object + 8L, afterCopyData),
                access("R64", allocatorB, vtableB),
                access("R64", vtableB + 0x10L, releaseTarget),
                call("RELEASE", 0L, List.of(
                        cell(object + 0x14L, 4, 0x12345678L),
                        cell(object + 8L, 8, 0x1111222233334444L)),
                        0x37636c7L, releaseTarget, allocatorB, afterCopyData, 8L),
                access("W64", object + 8L, reserved),
                access("W32", object + 0x14L, 0x80000002L),
                access("W32", object + 0x10L, 0x4e20L),
                access("R64", context, old),
                access("W64", context, object),
                call("DESTROY", 0L, List.of(cell(context, 8, 0x0123456789abcdefL)),
                        0x37636f0L, old),
                call("FREE", 0L, List.of(cell(context, 8, published)),
                        0x37636fdL, old, 0x210L),
                access("W64", GLOBAL, 0L),
                access("R64", context, published),
                access("W64", GLOBAL, published)));
        ArrayList<Cell> finals = finalObject(object, provider, reserved, 0x80000002L, allocatorB);
        finals.add(cell(context, 8, published));
        finals.add(cell(GLOBAL, 8, published));
        return new Scene("old-nonnull-copy-fresh-fields-and-final-publish", BASE,
                List.of(cell(GLOBAL, 8, 0L), cell(context, 8, old),
                        cell(allocatorA, 8, vtableA), cell(vtableA + 8L, 8, allocateTarget),
                        cell(allocatorB, 8, vtableB), cell(vtableB + 0x10L, 8, releaseTarget)),
                List.copyOf(steps), new Outcome(true, published), List.copyOf(finals));
    }

    public static List<Scene> scenes() {
        return List.of(guarded(), oldNullSkipReserve(), oldNonNullCopyFreshFieldsAndPublish());
    }
}
