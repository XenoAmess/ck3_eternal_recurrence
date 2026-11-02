package org.xar.ck3.study.m6.provider222;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.ToLongFunction;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;

/** Manual finite logical-RAM checks, not Native ABI, runtime installation or a natural Sway scenario. */
public final class StaticVirtualForwardWithProvider222Test {
    private static final long IMAGE = 0x140000000L;
    private static final long KNOWN = IMAGE + 0x86E140;
    private static int checks;
    private static int scenes;

    private StaticVirtualForwardWithProvider222Test() { }

    private record Event(String kind, Invocation actual) { }

    private static final class Ram implements Memory {
        final Map<Long, Long> words = new HashMap<>();
        final List<Long> reads = new ArrayList<>();
        Long faultAddress;
        RuntimeException fault;

        Ram seed(long address, long value) { words.put(address, value); return this; }
        @Override public long read64(long address) {
            reads.add(address);
            if (faultAddress != null && address == faultAddress.longValue()) { throw fault; }
            Long value = words.get(address);
            if (value == null) { throw new AssertionError("Unexpected read64 " + Long.toHexString(address)); }
            return value.longValue();
        }
        @Override public int read32(long address) { throw new AssertionError("read32"); }
        @Override public int read8(long address) { throw new AssertionError("read8"); }
        @Override public void write64(long address, long value) { throw new AssertionError("write64"); }
        @Override public void write32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void write8(long address, int value) { throw new AssertionError("write8"); }
    }

    private static final class Script implements Calls {
        final List<Event> events = new ArrayList<>();
        ToLongFunction<Invocation> onCall = actual -> { throw new AssertionError("Unexpected opaque CALL"); };
        ToLongFunction<Invocation> onTail = actual -> { throw new AssertionError("Unexpected opaque TAIL"); };
        @Override public long call(Invocation actual) {
            events.add(new Event("call", actual));
            return onCall.applyAsLong(actual);
        }
        @Override public long tailJump(Invocation actual) {
            events.add(new Event("tailJump", actual));
            return onTail.applyAsLong(actual);
        }
    }

    private static void same(Object expected, Object actual) {
        checks++;
        if (!expected.equals(actual)) { throw new AssertionError("Expected " + expected + " but got " + actual); }
    }

    private static void sameLong(long expected, long actual) { same(Long.valueOf(expected), Long.valueOf(actual)); }

    private static void scene(String name, Runnable body) {
        int before = checks;
        body.run();
        scenes++;
        System.out.println("PASS " + name + " checks=" + (checks - before));
    }

    private static void getterWrap() {
        Ram ram = new Ram().seed(0, 0x80000000000000A1L);
        sameLong(0x80000000000000A1L, ObjectProvider86e140.readReturnedObject(0xFFFFFFFFFFFFFBF8L, ram));
        same(List.of(0L), ram.reads);
    }

    private static void getterNextCallFresh() {
        Ram ram = new Ram().seed(0x2408, 0x80000000000000B1L);
        sameLong(0x80000000000000B1L, ObjectProvider86e140.readReturnedObject(0x2000, ram));
        ram.seed(0x2408, 0xF0000000000000B2L);
        sameLong(0xF0000000000000B2L, ObjectProvider86e140.readReturnedObject(0x2000, ram));
        same(List.of(0x2408L, 0x2408L), ram.reads);
    }

    private static void known08(boolean tailTargetsKnown) {
        long target = tailTargetsKnown ? KNOWN : 0x6800;
        Ram ram = new Ram().seed(0x1800, 0x2800).seed(0x2838, KNOWN).seed(0x1C08, 0x4800)
                .seed(0x4800, 0x5800).seed(0x5808, target);
        Script ports = new Script();
        ports.onTail = actual -> 0xFEDCBA9876543208L;
        Input input = new Input(0x1800, 0xF000000000000031L, 0x8000000000000032L, 0x9000000000000033L);
        sameLong(0xFEDCBA9876543208L, StaticVirtualForwardWithProvider222.fromSlot08(input, IMAGE, ram, ports));
        same(List.of(0x1800L, 0x2838L, 0x1C08L, 0x4800L, 0x5808L), ram.reads);
        same(List.of(new Event("tailJump", new Invocation(0x8558A0, target, 0x4800, 0x4800,
                input.rdxRaw64(), input.r8Raw64(), target))), ports.events);
    }

    private static void known10(boolean secondTargetsKnown) {
        long target = secondTargetsKnown ? KNOWN : 0x6900;
        Ram ram = new Ram().seed(0x1900, 0x2900).seed(0x2938, KNOWN).seed(0x1D08, 0x4900)
                .seed(0x4900, 0x5900).seed(0x5910, target);
        Script ports = new Script();
        ports.onCall = actual -> 0x800000000000005AL;
        Input input = new Input(0x1900, 0xF000000000000041L, 0x8000000000000042L, 0x9000000000000043L);
        sameLong(0x800000000000005AL, StaticVirtualForwardWithProvider222.fromSlot10(input, IMAGE, ram, ports));
        same(List.of(0x1900L, 0x2938L, 0x1D08L, 0x4900L, 0x5910L), ram.reads);
        same(List.of(new Event("call", new Invocation(0x85585B, target, 0x4900, 0x4900,
                input.rdxRaw64(), input.r8Raw64(), 0x5900))), ports.events);
    }

    private static void unknownFirstFallback() {
        Ram ram = new Ram().seed(0x1A00, 0x2A00).seed(0x2A38, 0x140007777L)
                .seed(0x4A00, 0x5A00).seed(0x5A08, 0x6A00).seed(0x5B08, 0x6B00);
        Script ports = new Script();
        ports.onCall = actual -> { ram.seed(0x4A00, 0x5B00); return 0x4A00; };
        ports.onTail = actual -> 0x800000000000006AL;
        Input input = new Input(0x1A00, 0xF000000000000051L, 0x8000000000000052L, 0x9000000000000053L);
        sameLong(0x800000000000006AL, StaticVirtualForwardWithProvider222.fromSlot08(input, IMAGE, ram, ports));
        same(List.of(0x1A00L, 0x2A38L, 0x4A00L, 0x5B08L), ram.reads);
        same(List.of(new Event("call", new Invocation(0x855883, 0x140007777L, 0x2A00, 0x1A00,
                        input.rdxRaw64(), input.r8Raw64(), input.r9Raw64())),
                new Event("tailJump", new Invocation(0x8558A0, 0x6B00, 0x4A00, 0x4A00,
                        input.rdxRaw64(), input.r8Raw64(), 0x6B00))), ports.events);
    }

    private static void selfWrap() {
        Ram ram = new Ram();
        // Null opaque port is deliberately unused on the existing exact short circuit.
        sameLong(0, StaticVirtualForwardWithProvider222.fromSlot10(
                new Input(0xFFFFFFFFFFFFFFF8L, 0, 0x55, 0x66), IMAGE, ram, null));
        same(List.of(), ram.reads);
    }

    private static void getterFault() {
        Ram ram = new Ram().seed(0x1B00, 0x2B00).seed(0x2B38, KNOWN);
        RuntimeException sentinel = new IllegalStateException("owner-memory-sentinel");
        ram.faultAddress = Long.valueOf(0x1F08);
        ram.fault = sentinel;
        Script ports = new Script();
        try {
            StaticVirtualForwardWithProvider222.fromSlot08(new Input(0x1B00, 0x61, 0x62, 0x63), IMAGE, ram, ports);
            throw new AssertionError("Expected exact original memory fault");
        } catch (IllegalStateException actual) {
            checks++;
            if (actual != sentinel) { throw new AssertionError("Exception identity changed"); }
        }
        same(List.of(0x1B00L, 0x2B38L, 0x1F08L), ram.reads);
        same(List.of(), ports.events);
    }

    public static void main(String[] args) {
        scene("getter-wrap", StaticVirtualForwardWithProvider222Test::getterWrap);
        scene("getter-next-call-fresh", StaticVirtualForwardWithProvider222Test::getterNextCallFresh);
        scene("known-slot08", () -> known08(false));
        scene("known-slot10", () -> known10(false));
        scene("unknown-first-fallback", StaticVirtualForwardWithProvider222Test::unknownFirstFallback);
        scene("slot10-wrap-self", StaticVirtualForwardWithProvider222Test::selfWrap);
        scene("known-getter-fault", StaticVirtualForwardWithProvider222Test::getterFault);
        scene("same-target-second-CALL-stays-opaque", () -> known10(true));
        scene("same-target-TAIL-stays-opaque", () -> known08(true));
        System.out.println("PASS scenes=" + scenes + " checks=" + checks
                + " logicalObjectRAMOnly=true noFullABI=true actualEntryR9StillRequired=true noNativeOrGame=true");
    }
}
