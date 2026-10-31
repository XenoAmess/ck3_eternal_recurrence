package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;

/** Controlled opaque outcomes and shared memory, without any caller/callee algorithm. */
class Lower61Fixture implements Lower61Inputs.Memory, Lower61Inputs.Calls,
        Lower61Inputs.EdgeObserver, B374Inputs.Calls {
    record Read64(long address, long bits) { }
    record Read32(long address, int bits) { }
    record First(Lower61Inputs.FirstCall known) { }
    enum Opaque { POINTER, ERROR }
    record MapEax(long rcxRaw) { }
    record Write32(long address, int bits) { }
    record Write64(long address, long bits) { }
    record Edge(boolean tail, long rcxRaw) { }
    record Remaining(String target, long rcxRaw) { }

    final Map<Long, Long> qwords = new LinkedHashMap<>();
    final Map<Long, Integer> dwords = new LinkedHashMap<>();
    final List<Object> events = new ArrayList<>();
    final List<Lower61Inputs.FirstCall> firstCalls = new ArrayList<>();
    final List<Edge> edges = new ArrayList<>();
    final List<Remaining> remainingCalls = new ArrayList<>();
    final List<Write32> writes32 = new ArrayList<>();
    int firstEax = 1;
    long destination = 0x100000001L;
    int errorEax = -1;
    int mappedEax = 0x87654321;
    Consumer<Lower61Inputs.FirstCall> firstEffect = known -> { };

    @Override
    public long readPointer(long address) {
        Long bits = qwords.get(address);
        if (bits == null) { throw new IllegalArgumentException("Missing QWORD " + address); }
        events.add(new Read64(address, bits));
        return bits;
    }

    @Override
    public int readInt32(long address) {
        Integer bits = dwords.get(address);
        if (bits == null) { throw new IllegalArgumentException("Missing DWORD " + address); }
        events.add(new Read32(address, bits));
        return bits;
    }

    @Override
    public void writeInt64(long address, long bits) {
        qwords.put(address, bits);
        events.add(new Write64(address, bits));
    }

    @Override
    public void writeInt32(long address, int bits) {
        if (!dwords.containsKey(address)) {
            throw new IllegalArgumentException("Missing DWORD write target " + address);
        }
        dwords.put(address, bits);
        var event = new Write32(address, bits);
        writes32.add(event);
        events.add(event);
    }

    @Override
    public int callSlot43DA748(Lower61Inputs.FirstCall known) {
        firstCalls.add(known);
        events.add(new First(known));
        firstEffect.accept(known);
        return firstEax;
    }

    @Override
    public long call423B18C() { events.add(Opaque.POINTER); return destination; }

    @Override
    public int callSlot43DA738() { events.add(Opaque.ERROR); return errorEax; }

    @Override
    public int call423B0D4(long knownRcxRaw) {
        events.add(new MapEax(knownRcxRaw));
        return mappedEax;
    }

    @Override
    public void normal(long knownRcxRaw) {
        var event = new Edge(false, knownRcxRaw);
        edges.add(event); events.add(event);
    }

    @Override
    public void tail(long knownRcxRaw) {
        var event = new Edge(true, knownRcxRaw);
        edges.add(event); events.add(event);
    }

    @Override
    public void call424E364(long knownRcxRaw) {
        throw new AssertionError("Adapter must not delegate the implemented normal lower edge");
    }

    @Override
    public void tail424E364(long knownRcxRaw) {
        throw new AssertionError("Adapter must not delegate the implemented tail lower edge");
    }

    @Override
    public void call42552D0(long knownRcxRaw) { remaining("42552D0", knownRcxRaw); }

    @Override
    public void call4255910(long knownRcxRaw) { remaining("4255910", knownRcxRaw); }

    @Override
    public void call425689C(long knownRcxRaw) { remaining("425689C", knownRcxRaw); }

    private void remaining(String target, long knownRcxRaw) {
        var event = new Remaining(target, knownRcxRaw);
        remainingCalls.add(event); events.add(event);
    }
}
