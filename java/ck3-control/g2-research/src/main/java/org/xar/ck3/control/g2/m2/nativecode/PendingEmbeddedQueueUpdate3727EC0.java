package org.xar.ck3.control.g2.m2.nativecode;

/** Actual103 normal3727EC0 calledby394, controlledatomic/queueports, not Game. */
public final class PendingEmbeddedQueueUpdate3727EC0 {
    private PendingEmbeddedQueueUpdate3727EC0() { }
    public interface Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
        void write8(long address,int value);
        void write32(long address,int value);
        void write64(long address,long value);
        int compareExchange32(long address,int expected,int desired);
    }
    public interface Calls {
        int classify3727580(Memory memory,long rcx);
        void pause(Memory memory);
        void enqueue880340(Memory memory,long rcx,long rdx);
    }
    public static void update(Memory memory,Calls calls,long receiver,long moduleBase,long stackSlotAddress) {
        // 3727ec6: cmp BYTE PTR [rcx+0x4e],0x0
        if ((memory.read8(receiver + 0x4e) & 0xff) != 0) {
            return;
        }
        // 3727ecf: call 0x3727580
        int rawAL = calls.classify3727580(memory, receiver);
        // 3727ed4: cmp DWORD PTR [rbx+0x48],0xffffffff
        int id = memory.read32(receiver + 0x48);
        // 3727ed8: setne dl (DL = 1 if id != 0xffffffff else 0)
        int dl = (id == 0xffffffff) ? 0 : 1;
        // 3727edb: cmp dl,al (exact byte equality of DL and AL low 8 bits)
        if (dl == (rawAL & 0xff)) {
            return;
        }
        // Spin loop for lock acquisition
        long lockAddress = moduleBase + 0x5c9ff68L;
        while (true) {
            // 3727ee4: mov eax,DWORD PTR [rip+0x257807e] (read lock)
            int lockVal = memory.read32(lockAddress);
            if (lockVal != 0) {
                // 3727ef8: pause
                calls.pause(memory);
                continue;
            }
            // 3727eee: lock cmpxchg DWORD PTR [rip+0x2578072],ecx (CAS lock, expected 0, desired 1)
            int old = memory.compareExchange32(lockAddress, 0, 1);
            // 3727ef5: je (ZF if old == 0)
            if (old != 0) {
                // 3727ef8: pause
                calls.pause(memory);
                continue;
            }
            break;
        }
        // 3727efc: lea rdx,[rsp+0x38] (stackSlotAddress is the physical stack slot)
        // 3727f01: mov QWORD PTR [rsp+0x38],rbx (write receiver to stack slot)
        memory.write64(stackSlotAddress, receiver);
        // 3727f06: lea rcx,[rip+0x1d40b5b] (queue global address)
        long queueAddress = moduleBase + 0x5468a68L;
        // 3727f0d: call 0x880340 (enqueue)
        calls.enqueue880340(memory, queueAddress, stackSlotAddress);
        // 3727f12: mov BYTE PTR [rbx+0x4e],0x1
        memory.write8(receiver + 0x4e, 1);
        // 3727f17: mov DWORD PTR [rip+0x2578047],0x0 (release lock)
        memory.write32(lockAddress, 0);
    }
}