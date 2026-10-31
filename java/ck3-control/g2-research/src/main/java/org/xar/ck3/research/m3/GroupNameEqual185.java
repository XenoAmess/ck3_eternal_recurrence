package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.GroupNameEqualApi185.Memory;
import org.xar.ck3.research.m3.GroupNameEqualApi185.Scratch;
import org.xar.ck3.research.m3.GroupNameEqualApi185.Vector128;

/** Low-byte normal result and exact observations of held212B plus14B helper. */
public final class GroupNameEqual185 {
    private GroupNameEqual185() { }

    public static int equalAl(Memory memory, long moduleBase, long left, long right, Scratch scratch) {
        int mask = memory.readUnsigned16(moduleBase + 0x5CAFCBCL);
        long rightWord = scratch.sourceEntryRsp() + 8L;
        long leftWord = scratch.sourceEntryRsp() + 0x10L;
        memory.write16(rightWord, mask & (int) right);
        memory.write16(leftWord, mask & (int) left);

        int observedRightWord = memory.readUnsigned16(rightWord);
        int observedLeftWord = memory.readUnsigned16(leftWord);
        long selectedWord = observedLeftWord < observedRightWord ? rightWord : leftWord;
        int limit = memory.readUnsigned16(moduleBase + 0x5CB0A58L);
        int counter = memory.readUnsigned16(selectedWord);

        if (counter <= limit) {
            while (true) {
                Vector128 leftVector = memory.read128(left);
                Vector128 rightVector = memory.read128(right);
                int mismatchMask = 0;
                int zeroMask = 0;
                for (int i = 0; i < 16; i++) {
                    int leftByte = byteAt(leftVector, i);
                    int rightByte = byteAt(rightVector, i);
                    if (leftByte != rightByte) {
                        mismatchMask |= 1 << i;
                    }
                    if (leftByte == 0) {
                        zeroMask |= 1 << i;
                    }
                }
                if (zeroMask != 0) {
                    int prefixBits = Integer.numberOfTrailingZeros(zeroMask) + 1;
                    int prefixMask = (1 << prefixBits) - 1;
                    return (mismatchMask & prefixMask) == 0 ? 1 : 0;
                }
                if (mismatchMask != 0) {
                    return 0;
                }
                left += 0x10L;
                right += 0x10L;
                counter = (counter + 0x10) & 0xFFFF;
                if (counter > limit) {
                    break;
                }
            }
        }

        long rightOffset = right - left;
        while (true) {
            int leftByte = memory.readUnsigned8(left);
            int rightByte = memory.readUnsigned8(left + rightOffset);
            if (leftByte != rightByte) {
                return 0;
            }
            left++;
            if (rightByte == 0) {
                return 1;
            }
        }
    }

    private static int byteAt(Vector128 vector, int index) {
        long bits = index < 8 ? vector.low() : vector.high();
        return (int) ((bits >>> ((index & 7) * 8)) & 0xFFL);
    }
}
