package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Complete26769E0 normal-path projection over supplied storage, no live U or fullNativeABI. */
public final class Request26769e0 {
    private Request26769e0() { }
    /** Explicit supplied storage for source private temporaries, not physical stack bindings. */
    public record Scratch(long initializerHolder,long lookupHolder,long view70,long view50,long viewC,long initializerScratch) { }
    public record Known3852500(long rcx,long rdx,long r8,long r9,long stack20) { }
    /** Only source-established registers/stack field, no unknown volatile arguments. */
    public interface Ports {
        void call3852500(Known3852500 known);
        void call855db0(long rcx,long rdx,long r8);
        void callVirtual0(long target,long rcx,int edx);
        void call856050(long rcx);
    }
    public static long create(long moduleBase, long outputHolder, long descriptor, long sourceString, Scratch scratch, RequestE92780.Memory memory, RequestE92780.Ports initializerPorts, Ports ports) {
        long initializerHolder = scratch.initializerHolder();
        long initializerScratch = scratch.initializerScratch();
        RequestE92780.initialize(moduleBase, initializerHolder, descriptor, initializerScratch, memory, initializerPorts);

        long localU = memory.readPointer(initializerHolder);
        memory.writeByte(localU + 0xA9, (byte)1);

        long sourceStringLength = memory.readPointer(sourceString + 0x10);
        if (sourceStringLength == 0) {
            memory.writeInt64(outputHolder, localU);
            long bFlag = memory.readUnsignedByte(descriptor + 0x28);
            if (bFlag != 0) {
                ports.call856050(descriptor);
            }
            return outputHolder;
        }

        long globalSlot = moduleBase + 0x5CB87F8L;
        long receiver = memory.readPointer(globalSlot);
        long rcx = memory.readPointer(receiver + 0x1C0);

        long capC = memory.readPointer(sourceString + 0x18);
        long viewC = sourceString;
        if (Long.compareUnsigned(capC, 16L) >= 0) {
            viewC = memory.readPointer(sourceString);
        }
        long viewCAddr = scratch.viewC();
        memory.writeInt64(viewCAddr, viewC);
        memory.writeInt32(viewCAddr + 0x8, (int)sourceStringLength);
        memory.writeByte(viewCAddr + 0xC, (byte)0);

        long rax70 = rcx + 0x70;
        int edx70 = memory.readInt32(rax70 + 0x10);
        long cap70 = memory.readPointer(rax70 + 0x18);
        if (Long.compareUnsigned(cap70, 16L) >= 0) {
            rax70 = memory.readPointer(rax70);
        }
        long view70Addr = scratch.view70();
        memory.writeInt64(view70Addr, rax70);
        memory.writeInt32(view70Addr + 0x8, edx70);
        memory.writeByte(view70Addr + 0xC, (byte)0);

        long rax50 = rcx + 0x50;
        int edx50 = memory.readInt32(rax50 + 0x10);
        long cap50 = memory.readPointer(rax50 + 0x18);
        if (Long.compareUnsigned(cap50, 16L) >= 0) {
            rax50 = memory.readPointer(rax50);
        }
        long view50Addr = scratch.view50();
        memory.writeInt64(view50Addr, rax50);
        memory.writeInt32(view50Addr + 0x8, edx50);
        memory.writeByte(view50Addr + 0xC, (byte)0);

        long lookupHolderAddr = scratch.lookupHolder();
        long stack20 = view70Addr;
        ports.call3852500(new Known3852500(rcx, lookupHolderAddr, viewCAddr, view50Addr, stack20));

        long resultP = memory.readPointer(lookupHolderAddr);
        long p140 = resultP + 0x140;
        long u70 = localU + 0x70;
        if (u70 != p140) {
            long r8 = memory.readPointer(p140 + 0x10);
            long capP140 = memory.readPointer(p140 + 0x18);
            if (Long.compareUnsigned(capP140, 16L) >= 0) {
                p140 = memory.readPointer(p140);
            }
            ports.call855db0(u70, p140, r8);
            resultP = memory.readPointer(lookupHolderAddr);
        }

        long p170Flag = memory.readUnsignedByte(resultP + 0x170);
        int ecx = (p170Flag != 0) ? 1 : 0;
        memory.writeInt32(localU + 0x90, ecx);

        memory.writeInt64(outputHolder, localU);

        long rcx2 = memory.readPointer(lookupHolderAddr);
        if (rcx2 != 0) {
            long target = memory.readPointer(memory.readPointer(rcx2));
            ports.callVirtual0(target, rcx2, 1);
        }

        long bFlag = memory.readUnsignedByte(descriptor + 0x28);
        if (bFlag != 0) {
            ports.call856050(descriptor);
        }

        return outputHolder;
    }
}
