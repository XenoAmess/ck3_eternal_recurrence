package org.xar.ck3.research.m3;

public final class CapacityIndex179 {
    private CapacityIndex179() { }

    public static int select(int count, int bias) {

        if (count > 1) {
            return selectLarge(count, bias);
        }

        return Math.max(3, bias);
    }

    private static int selectLarge(int count, int bias) {

        int bsr = Integer.numberOfLeadingZeros(count - 1) ^ 31;

        int msbIndex = 31 - Integer.numberOfLeadingZeros(count - 1);

        int r8 = 1 << msbIndex;

        int edx = 31 - msbIndex;

        int r8_final = 1 + msbIndex;

        int ecx = r8_final + bias;

        return Math.max(3, ecx);
    }
}