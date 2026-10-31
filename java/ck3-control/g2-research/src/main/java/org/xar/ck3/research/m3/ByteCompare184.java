package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.ByteCompareApi184.Memory;

public final class ByteCompare184 {
    private ByteCompare184() { }

    public static int compare(Memory memory, long left, long right, long lengthBits) {
        long rdx = right - left;
        long r8 = lengthBits;
        long rcx = left;


        if (Long.compareUnsigned(r8, 8L) < 0) {

            if (r8 == 0L) {

                return 0;
            }

            while (r8 != 0L) {
                int al = memory.readUnsigned8(rcx);
                int bl = memory.readUnsigned8(rcx + rdx);
                if (al != bl) {




                    return al < bl ? -1 : 1;
                }
                rcx = rcx + 1L;
                r8 = r8 - 1L;
            }

            return 0;
        }


        if ((rcx & 7L) != 0L) {

            while ((rcx & 7L) != 0L) {
                int al = memory.readUnsigned8(rcx);
                int bl = memory.readUnsigned8(rcx + rdx);
                if (al != bl) {
                    return al < bl ? -1 : 1;
                }
                rcx = rcx + 1L;
                r8 = r8 - 1L;
            }
        }


        long r9 = r8 >>> 3;
        if (r9 != 0L) {

            long r9_32 = r9 >>> 2;
            if (r9_32 != 0L) {

                while (r9_32 != 0L) {
                    long q0l = memory.readPointer(rcx);
                    long q0r = memory.readPointer(rcx + rdx);
                    if (q0l != q0r) {

                        long freshRight = memory.readPointer(rcx + rdx);
                        long swappedLeft = Long.reverseBytes(q0l);
                        long swappedRight = Long.reverseBytes(freshRight);
                        if (Long.compareUnsigned(swappedLeft, swappedRight) < 0) return -1;
                        if (Long.compareUnsigned(swappedLeft, swappedRight) > 0) return 1;
                        return 1;

                    }

                    long q1l = memory.readPointer(rcx + 8L);
                    long q1r = memory.readPointer(rcx + rdx + 8L);
                    if (q1l != q1r) {
                        long freshRight = memory.readPointer(rcx + rdx + 8L);
                        long swappedLeft = Long.reverseBytes(q1l);
                        long swappedRight = Long.reverseBytes(freshRight);
                        if (Long.compareUnsigned(swappedLeft, swappedRight) < 0) return -1;
                        if (Long.compareUnsigned(swappedLeft, swappedRight) > 0) return 1;
                        return 1;
                    }

                    long q2l = memory.readPointer(rcx + 16L);
                    long q2r = memory.readPointer(rcx + rdx + 16L);
                    if (q2l != q2r) {
                        long freshRight = memory.readPointer(rcx + rdx + 16L);
                        long swappedLeft = Long.reverseBytes(q2l);
                        long swappedRight = Long.reverseBytes(freshRight);
                        if (Long.compareUnsigned(swappedLeft, swappedRight) < 0) return -1;
                        if (Long.compareUnsigned(swappedLeft, swappedRight) > 0) return 1;
                        return 1;
                    }

                    long q3l = memory.readPointer(rcx + 24L);
                    long q3r = memory.readPointer(rcx + rdx + 24L);
                    if (q3l != q3r) {
                        long freshRight = memory.readPointer(rcx + rdx + 24L);
                        long swappedLeft = Long.reverseBytes(q3l);
                        long swappedRight = Long.reverseBytes(freshRight);
                        if (Long.compareUnsigned(swappedLeft, swappedRight) < 0) return -1;
                        if (Long.compareUnsigned(swappedLeft, swappedRight) > 0) return 1;
                        return 1;
                    }

                    rcx = rcx + 32L;
                    r9_32 = r9_32 - 1L;
                }
            }


            r8 = r8 & 31L;

            r9 = r8 >>> 3;
            if (r9 != 0L) {

                while (r9 != 0L) {
                    long q0l = memory.readPointer(rcx);
                    long q0r = memory.readPointer(rcx + rdx);
                    if (q0l != q0r) {
                        long freshRight = memory.readPointer(rcx + rdx);
                        long swappedLeft = Long.reverseBytes(q0l);
                        long swappedRight = Long.reverseBytes(freshRight);
                        if (Long.compareUnsigned(swappedLeft, swappedRight) < 0) return -1;
                        if (Long.compareUnsigned(swappedLeft, swappedRight) > 0) return 1;
                        return 1;
                    }
                    rcx = rcx + 8L;
                    r9 = r9 - 1L;
                }
            }


            r8 = r8 & 7L;

            if (r8 != 0L) {
                while (r8 != 0L) {
                    int al = memory.readUnsigned8(rcx);
                    int bl = memory.readUnsigned8(rcx + rdx);
                    if (al != bl) {
                        return al < bl ? -1 : 1;
                    }
                    rcx = rcx + 1L;
                    r8 = r8 - 1L;
                }
            }
            return 0;
        }


        if (r8 != 0L) {
            while (r8 != 0L) {
                int al = memory.readUnsigned8(rcx);
                int bl = memory.readUnsigned8(rcx + rdx);
                if (al != bl) {
                    return al < bl ? -1 : 1;
                }
                rcx = rcx + 1L;
                r8 = r8 - 1L;
            }
        }
        return 0;
    }
}
