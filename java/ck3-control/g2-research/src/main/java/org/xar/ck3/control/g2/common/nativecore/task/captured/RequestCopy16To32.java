package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Only the source 4226986..422699C path reached for unsigned length16..32. */
public final class RequestCopy16To32 {
    private RequestCopy16To32() { }

    @FunctionalInterface
    public interface Remainder {
        void call4226860(long destination, long source, long lengthBits);
    }

    public static boolean tryCopy(long destination, long source, long lengthBits,
            RequestE92780.Memory memory) {

        if (lengthBits < 0) {
            return false;
        }
        if (lengthBits < 16 || lengthBits > 32) {
            return false;
        }

        RequestE92780.Raw128 firstRead = memory.readRaw128(source);

        long secondSourceAddress = source + lengthBits - 16L;
        RequestE92780.Raw128 secondRead = memory.readRaw128(secondSourceAddress);

        memory.writeRaw128(destination, firstRead);

        long secondDestinationAddress = destination + lengthBits - 16L;
        memory.writeRaw128(secondDestinationAddress, secondRead);

        return true;
    }

    public static void copyOrDelegate(long destination, long source, long lengthBits,
            RequestE92780.Memory memory, Remainder remainder) {
        if (tryCopy(destination, source, lengthBits, memory)) {
            return;
        }
        remainder.call4226860(destination, source, lengthBits);
    }
}
