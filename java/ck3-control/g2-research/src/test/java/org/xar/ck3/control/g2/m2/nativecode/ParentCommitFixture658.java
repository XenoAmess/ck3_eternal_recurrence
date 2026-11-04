package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/**
 * Neutral658 Test host. One existing final647.Ram supplies all owned bytes and
 * primitive effects; this class supplies only the two nominal Memory interfaces
 * and a shared observation order. It contains no case, bank, outcome, expected
 * trace, target algorithm, production binding or default FP/DF/input state.
 *
 * All effectful accesses must use this adapter's primitive ports. The public
 * delegate is available for literal seeding and exact owned-map inspection.
 * R32/W32/LOCK event values retain the delegate's signed Java-int encoding.
 * Owned storage is software-only, with no Native/OS mapping or fault assertion.
 */
public final class ParentCommitFixture658
        implements ParentKnown647Api.Memory, EmbeddedKnownCommit657.Memory {
    public final ParentFixture647.Ram ram;
    public final List<ParentFixture647.Event> memoryEvents;
    public final List<Object> events = new ArrayList<>();
    private int copiedMemoryEvents;

    /** Stores the SAME supplied actual object; does not synthesize a frame/state. */
    public record Observation(String name, Object actual) {
        public Observation {
            Objects.requireNonNull(name);
            Objects.requireNonNull(actual);
        }
    }

    /** Fresh software storage only; no image, SP, banks, headers or ports seeded. */
    public ParentCommitFixture658() {
        ram = new ParentFixture647.Ram();
        memoryEvents = ram.events;
    }

    public void observe(String name, Object actual) {
        events.add(new Observation(name, actual));
    }

    /** Unrecorded caller-owned literal initialization, using existing seed mechanics. */
    public void seed(long addressBits, int width, long valueBits) {
        ram.seed(addressBits, width, valueBits);
    }

    /** Unrecorded raw bytes; no target instruction or expected-state calculation. */
    public void seedHex(long addressBits, String hex) {
        byte[] literal = HexFormat.of().parseHex(Objects.requireNonNull(hex));
        for (int i = 0; i < literal.length; i++)
            ram.seed(addressBits + i, 1, literal[i] & 255L);
    }

    private void recorded() {
        if (memoryEvents.size() != copiedMemoryEvents + 1)
            throw new IllegalStateException("Memory effects must use the658 adapter ports");
        events.add(memoryEvents.get(copiedMemoryEvents));
        copiedMemoryEvents++;
    }

    @Override public int readDword(long p) {
        int value = ram.readDword(p);
        recorded();
        return value;
    }

    @Override public long readQword(long p) {
        long value = ram.readQword(p);
        recorded();
        return value;
    }

    @Override public int readUnsignedByte(long p) {
        int value = ram.readUnsignedByte(p);
        recorded();
        return value;
    }

    @Override public void writeDword(long p, int v) {
        ram.writeDword(p, v);
        recorded();
    }

    @Override public int lockedXaddDword(long p, int v) {
        int value = ram.lockedXaddDword(p, v);
        recorded();
        return value;
    }

    @Override public void writeQword(long p, long v) {
        ram.writeQword(p, v);
        recorded();
    }

    @Override public void writeByte(long p, int v) {
        ram.writeByte(p, v);
        recorded();
    }

    @Override public Bits128 read128(long p) {
        Bits128 value = ram.read128(p);
        recorded();
        return value;
    }

    @Override public void write128(long p, Bits128 v) {
        ram.write128(p, v);
        recorded();
    }

    @Override public void writeWord(long p, int v) {
        ram.writeWord(p, v);
        recorded();
    }

    @Override public void write128NonTemporal(long p, Bits128 v) {
        ram.write128NonTemporal(p, v);
        recorded();
    }

    @Override public void sfence() {
        ram.sfence();
        recorded();
    }

    @Override public int readUnsignedWord(long p) {
        int value = ram.readUnsignedWord(p);
        recorded();
        return value;
    }

    @Override public FullCopy437Api.Bits256 read256(long p) {
        FullCopy437Api.Bits256 value = ram.read256(p);
        recorded();
        return value;
    }

    @Override public void write256(long p, FullCopy437Api.Bits256 v) {
        ram.write256(p, v);
        recorded();
    }

    @Override public void write256NonTemporal(long p, FullCopy437Api.Bits256 v) {
        ram.write256NonTemporal(p, v);
        recorded();
    }
}
