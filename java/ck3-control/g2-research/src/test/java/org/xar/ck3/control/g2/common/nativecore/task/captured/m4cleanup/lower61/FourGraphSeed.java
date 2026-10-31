package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61;

import java.util.List;

/** Literal finite inputs only, without executing or predicting a target algorithm. */
final class FourGraphSeed {
    static final long BASE = 0x100000000L;
    static final long OBJECT = 0x200000000L;
    static final long A = 0x300000000L;
    static final long E0 = 0x400000000L;
    static final long F0 = 0x500000000L;
    static final long E8 = 0x600000000L;
    static final long T54 = 0x700000000L;
    static final long P266 = 0x800000000L;
    static final long P108 = 0x900000000L;
    static final long UNRELATED = 0xA00000000L;
    private record InputSlot(long offset, long imageRva, long bits) { }

    static Lower61Fixture create() {
        var f = new Lower61Fixture();
        f.qwords.put(OBJECT + 0xF8L, A);
        f.qwords.put(OBJECT + 0xE0L, E0);
        f.qwords.put(OBJECT + 0xF0L, F0);
        f.qwords.put(OBJECT + 0xE8L, E8);
        f.qwords.put(OBJECT + 0x100L, 0L);
        f.qwords.put(OBJECT + 0x120L, T54);
        f.dwords.put(E0, 0);
        f.dwords.put(F0, 0);
        f.dwords.put(E8, 0);
        f.dwords.put(T54 + 0x15CL, 0);
        f.dwords.put(UNRELATED, 0x12345678);
        for (InputSlot s : List.of(
                new InputSlot(0x18L, 0x542F238L, 61L),
                new InputSlot(0x20L, 0x542F240L, 62L),
                new InputSlot(0x28L, 0x542F248L, 63L),
                new InputSlot(0x30L, 0x542F250L, 64L),
                new InputSlot(0x38L, 0x542F258L, 65L),
                new InputSlot(0x40L, 0x542F260L, 66L),
                new InputSlot(0x48L, 0x542F268L, 67L),
                new InputSlot(0x68L, 0x542F288L, 68L),
                new InputSlot(0x70L, 0x542F290L, 69L),
                new InputSlot(0x78L, 0x542F298L, 70L),
                new InputSlot(0x80L, 0x542F2A0L, 71L),
                new InputSlot(0x88L, 0x542F2A8L, 72L),
                new InputSlot(0x90L, 0x542F2B0L, 73L),
                new InputSlot(0L, 0x542F220L, 10L),
                new InputSlot(8L, 0x542F228L, 20L),
                new InputSlot(0x10L, 0x542F230L, 30L),
                new InputSlot(0x58L, 0x542F278L, 40L),
                new InputSlot(0x60L, 0x542F280L, 50L))) {
            f.qwords.put(A + s.offset(), s.bits());
            f.qwords.put(BASE + s.imageRva(), s.bits());
        }
        f.qwords.put(A + 0x18L, P266);
        for (long marker : List.of(0x28L, 0x48L, 0x68L, 0x88L, 0xA8L, 0xC8L)) {
            f.qwords.put(OBJECT + marker, BASE + 0x542F498L);
        }
        for (long gate : List.of(0x20L, 0x40L, 0x60L, 0x80L, 0xA0L, 0xC0L)) {
            f.qwords.put(OBJECT + gate, 0L);
        }
        f.qwords.put(BASE + 0x5C5DE30L, 101L);
        f.firstEax = Integer.MIN_VALUE;
        return f;
    }
}
