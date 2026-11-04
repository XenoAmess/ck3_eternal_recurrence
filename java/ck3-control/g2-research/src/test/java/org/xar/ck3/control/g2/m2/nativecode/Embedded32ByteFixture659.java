package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/**
 * Test-owned mechanical bytes and event order for the two bounded659 scenes.
 * No root constants, register banks, FP/DF state, case, oracle or target algorithm.
 *
 * Only the already existing637.Memory interface is implemented here. A future
 * Test-local nominal adapter may extend this class only after the real659
 * Memory declaration is held. No future659 declaration is invented by this file.
 *
 * Every accessed byte must be explicitly seeded. This is software storage;
 * native mapping, alignment, faults, concurrency and atomicity are not asserted.
 */
public class Embedded32ByteFixture659 implements EmbeddedElementsFp637.Memory {
    public record Event(String kind, long address, long a, long b, long c, long d) {
        public Event { Objects.requireNonNull(kind); }
    }

    /** Keeps the same actual frame/offer/argument object, never a replacement. */
    public record Observation(String name, Object actual) {
        public Observation {
            Objects.requireNonNull(name);
            Objects.requireNonNull(actual);
        }
    }

    public final Map<Long,Byte> bytes = new LinkedHashMap<>();
    public final List<Event> memoryEvents = new ArrayList<>();
    public final List<Object> events = new ArrayList<>();

    /** Empty software ownership only; no image, SP, bank, header or port defaults. */
    public Embedded32ByteFixture659() { }

    /** Literal initialization only, with no target event or implicit zero fill. */
    public final void seedHex(long baseBits, String literalHex) {
        if (!events.isEmpty()) throw new IllegalStateException("Seed before target observations only");
        byte[] literal = HexFormat.of().parseHex(Objects.requireNonNull(literalHex));
        for (int i=0; i<literal.length; i++) {
            long p=baseBits+i;
            if (bytes.putIfAbsent(p,literal[i]) != null)
                throw new IllegalArgumentException("Overlapping seed byte " + Long.toUnsignedString(p,16));
        }
    }

    public final void observe(String name, Object actual) {
        events.add(new Observation(name,actual));
    }

    private void owned(long p, int width) {
        for (int i=0; i<width; i++)
            if (!bytes.containsKey(p+i))
                throw new IllegalStateException("Unowned software byte " + Long.toUnsignedString(p+i,16));
    }

    private long raw(long p, int width) {
        long value=0;
        for (int i=0; i<width; i++) value |= (bytes.get(p+i) & 255L) << (8*i);
        return value;
    }

    private void store(long p, int width, long value) {
        for (int i=0; i<width; i++) bytes.put(p+i,(byte)(value >>> (8*i)));
    }

    private void record(String kind, long p, long a, long b, long c, long d) {
        Event event=new Event(kind,p,a,b,c,d);
        memoryEvents.add(event);
        events.add(event);
    }

    private Bits128 raw128(long p) {
        return new Bits128(raw(p,8),raw(p+8,8));
    }

    private void store128(long p, Bits128 value) {
        store(p,8,value.lowBits());
        store(p+8,8,value.highBits());
    }

    private FullCopy437Api.Bits256 raw256(long p) {
        return new FullCopy437Api.Bits256(raw128(p),raw128(p+16));
    }

    private void store256(long p, FullCopy437Api.Bits256 value) {
        store128(p,value.low());
        store128(p+16,value.high());
    }

    @Override public final int readDword(long p) {
        owned(p,4);
        int value=(int)raw(p,4);
        record("R32",p,value,0,0,0);
        return value;
    }

    @Override public final long readQword(long p) {
        owned(p,8);
        long value=raw(p,8);
        record("R64",p,value,0,0,0);
        return value;
    }

    @Override public final int readUnsignedByte(long p) {
        owned(p,1);
        int value=(int)raw(p,1);
        record("R8",p,value,0,0,0);
        return value;
    }

    @Override public final void writeDword(long p, int value) {
        owned(p,4);
        record("W32",p,value,0,0,0);
        store(p,4,value);
    }

    @Override public final int lockedXaddDword(long p, int addend) {
        owned(p,4);
        int old=(int)raw(p,4), sum=old+addend;
        record("LOCK_XADD32",p,addend,old,sum,0);
        store(p,4,sum);
        return old;
    }

    @Override public final void writeQword(long p, long value) {
        owned(p,8);
        record("W64",p,value,0,0,0);
        store(p,8,value);
    }

    @Override public final void writeByte(long p, int value) {
        owned(p,1);
        record("W8",p,value & 255,0,0,0);
        store(p,1,value);
    }

    @Override public final Bits128 read128(long p) {
        owned(p,16);
        Bits128 value=raw128(p);
        record("R128",p,value.lowBits(),value.highBits(),0,0);
        return value;
    }

    @Override public final void write128(long p, Bits128 value) {
        Objects.requireNonNull(value);
        owned(p,16);
        record("W128",p,value.lowBits(),value.highBits(),0,0);
        store128(p,value);
    }

    @Override public final void writeWord(long p, int value) {
        owned(p,2);
        record("W16",p,value & 65535,0,0,0);
        store(p,2,value);
    }

    @Override public final void write128NonTemporal(long p, Bits128 value) {
        Objects.requireNonNull(value);
        owned(p,16);
        record("W128NT",p,value.lowBits(),value.highBits(),0,0);
        store128(p,value);
    }

    @Override public final void sfence() {
        record("SFENCE",0,0,0,0,0);
    }

    @Override public final int readUnsignedWord(long p) {
        owned(p,2);
        int value=(int)raw(p,2);
        record("R16",p,value,0,0,0);
        return value;
    }

    @Override public final FullCopy437Api.Bits256 read256(long p) {
        owned(p,32);
        FullCopy437Api.Bits256 value=raw256(p);
        record("R256",p,value.low().lowBits(),value.low().highBits(),
                value.high().lowBits(),value.high().highBits());
        return value;
    }

    @Override public final void write256(long p, FullCopy437Api.Bits256 value) {
        Objects.requireNonNull(value);
        owned(p,32);
        record("W256",p,value.low().lowBits(),value.low().highBits(),
                value.high().lowBits(),value.high().highBits());
        store256(p,value);
    }

    @Override public final void write256NonTemporal(long p, FullCopy437Api.Bits256 value) {
        Objects.requireNonNull(value);
        owned(p,32);
        record("W256NT",p,value.low().lowBits(),value.low().highBits(),
                value.high().lowBits(),value.high().highBits());
        store256(p,value);
    }
}
