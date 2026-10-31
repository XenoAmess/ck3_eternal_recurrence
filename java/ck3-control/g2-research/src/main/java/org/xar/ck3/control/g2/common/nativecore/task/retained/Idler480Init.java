package org.xar.ck3.control.g2.common.nativecore.task.retained;
public final class Idler480Init {
public static long init(long object, long inputH, long inputK, InGameIdlerEventDispatch.Memory memory, Idler480Ports.Symbols symbols, Idler480Ports.Calls calls) {
    long O = object;
    long A = inputH;
    long K = inputK;

    long rax = symbols.address(0x44bc418L);
    memory.writeInt64(O + 0L, rax);

    long rsi = 0L;
    memory.writeInt64(O + 8L, rsi);
    memory.writeInt64(O + 0x10L, rsi);

    rax = symbols.address(0x54df888L);
    memory.writeInt64(O + 0x18L, rax);

    memory.writeInt64(O + 0x20L, A);

    memory.writeInt64(O + 0x28L, rsi);
    memory.writeInt64(O + 0x30L, rsi);
    memory.writeInt64(O + 0x38L, rsi);
    memory.writeInt64(O + 0x40L, rsi);

    rax = symbols.address(0x54df890L);
    memory.writeInt64(O + 0x48L, rax);

    long rcx = 8L;
    long p8 = calls.allocate(rcx);

    rcx = symbols.address(0x44bc3f0L);
    memory.writeInt64(p8 + 0L, rcx);

    memory.writeInt64(O + 0x50L, p8);
    memory.writeInt64(O + 0x58L, rsi);
    memory.writeInt64(O + 0x60L, rsi);

    rax = symbols.address(0x54df760L);
    memory.writeInt64(O + 0x68L, rax);

    memory.writeInt64(O + 0x70L, rsi);
    memory.writeInt64(O + 0x78L, rsi);
    memory.writeInt64(O + 0x80L, rax);
    memory.writeInt64(O + 0x88L, rsi);
    memory.writeInt64(O + 0x90L, K);

    rcx = 0xB0L;
    long p1 = calls.allocate(rcx);

    int r8 = 0;
    long rdx = memory.readPointer(O + 0x20L);
    rcx = p1;
    long s1 = calls.constructChild(rcx, rdx, r8);

    memory.writeInt64(O + 0x28L, s1);

    rcx = 0xB0L;
    long p2 = calls.allocate(rcx);

    rcx = memory.readPointer(O + 0x20L);
    memory.writeInt64(p2 + 0L, rcx);
    memory.writeInt64(p2 + 8L, rsi);
    memory.writeInt64(p2 + 0x10L, rsi);

    rcx = symbols.address(0x54e0928L);
    memory.writeInt64(p2 + 0x18L, rcx);
    memory.writeInt64(p2 + 0x20L, rsi);
    memory.writeInt64(p2 + 0x28L, rsi);
    memory.writeInt64(p2 + 0x30L, rcx);
    memory.writeInt64(p2 + 0x38L, rsi);
    memory.writeInt64(p2 + 0x40L, rsi);
    memory.writeInt64(p2 + 0x48L, rcx);
    memory.writeInt64(p2 + 0x50L, rsi);
    memory.writeInt64(p2 + 0x58L, rsi);

    rcx = symbols.address(0x54e0930L);
    memory.writeInt64(p2 + 0x60L, rcx);
    memory.writeInt64(p2 + 0x68L, rsi);
    memory.writeInt64(p2 + 0x70L, rsi);

    rcx = symbols.address(0x54e0938L);
    memory.writeInt64(p2 + 0x78L, rcx);
    memory.writeInt64(p2 + 0x80L, rsi);
    memory.writeInt64(p2 + 0x88L, rsi);

    rcx = symbols.address(0x54e0940L);
    memory.writeInt64(p2 + 0x90L, rcx);
    memory.writeInt64(p2 + 0x98L, rsi);
    memory.writeInt64(p2 + 0xa0L, rsi);

    rcx = symbols.address(0x54e0948L);
    memory.writeInt64(p2 + 0xa8L, rcx);

    memory.writeInt64(O + 0x30L, p2);

    long savedO50 = memory.readPointer(O + 0x50L);

    long registryRcx = symbols.address(0x54e0948L);
    long r1 = calls.getRegistry(registryRcx);

    rcx = symbols.address(0x5434f38L);
    long capacity = memory.readPointer(symbols.address(0x5434f50L));
    long loadedVal = memory.readPointer(symbols.address(0x5434f38L));
    boolean branchTaken = (Long.compareUnsigned(capacity, 16L) >= 0);
    if (branchTaken) {
        rcx = loadedVal;
    }

    long descData = rcx;
    int descLength = memory.readInt32(symbols.address(0x5434f48L));
    byte descFlag = 0;

    Idler480Ports.Descriptor knownDescriptorFields = new Idler480Ports.Descriptor(descData, descLength, descFlag);

    rcx = r1;
    long r2 = calls.findName(rcx, knownDescriptorFields);

    rcx = memory.readPointer(symbols.address(0x5cbf858L));
    if (rcx == 0L) {
        return O;
    }

    calls.virtual30(rcx, r2, savedO50);

    return O;
}
}
