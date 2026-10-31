package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Source E92780 supplied-storage projection. Scratch is caller-owned storage for
 * source local string32B, scalar DWORD+20, flag BYTE+28. No real stack binding,
 * current U identity, Native helper ABI or allocation availability is claimed. */
public final class RequestE92780 {
    private RequestE92780() { }
    public record Raw128(long low, long high) { }
    public interface Memory extends NativeTaskMemory {
        int readUnsignedByte(long address);
        void writeByte(long address, byte value);
        void writeInt16(long address, short value);
        Raw128 readRaw128(long address);
        void writeRaw128(long address, Raw128 value);
    }
    /** Only source-established argument fields, not complete Native signatures. */
    public interface Ports {
        long call4223b94(int ecx);
        void call855f00(long rcx, long rdx);
        void call856050(long rcx);
    }
    public static void writeDefaults(long moduleBase, long allocatedU, Memory memory) {
        long rbx = allocatedU;
        // E927E8: mov WORD PTR [rbx+0x8],0x0
        memory.writeInt16(rbx + 0x8, (short)0);
        // E927EE: mov BYTE PTR [rbx+0xa],0x0
        memory.writeByte(rbx + 0xa, (byte)0);
        // E927F2: mov DWORD PTR [rbx+0xc],ecx (ecx is 0 after E927A9 xor)
        memory.writeInt32(rbx + 0xc, 0);
        // E927F5: mov QWORD PTR [rbx+0x10],rcx (rcx is 0 after E927A9 xor)
        memory.writeInt64(rbx + 0x10, 0L);
        // E927F9: xor eax,eax -> eax=0
        // E927FB: mov QWORD PTR [rbx+0x18],rax
        memory.writeInt64(rbx + 0x18, 0L);
        // E927FF: mov BYTE PTR [rbx+0x20],al (al=0)
        memory.writeByte(rbx + 0x20, (byte)0);
        // E92802: mov QWORD PTR [rbx+0x28],rcx (rcx=0)
        memory.writeInt64(rbx + 0x28, 0L);
        // E92806: mov QWORD PTR [rbx+0x38],rcx (rcx=0)
        memory.writeInt64(rbx + 0x38, 0L);
        // E9280A: mov QWORD PTR [rbx+0x40],0xf
        memory.writeInt64(rbx + 0x40, 0xF);
        // E92812: mov QWORD PTR [rbx+0x48],rcx (rcx=0)
        memory.writeInt64(rbx + 0x48, 0L);
        // E92816: mov QWORD PTR [rbx+0x58],rcx (rcx=0)
        memory.writeInt64(rbx + 0x58, 0L);
        // E9281A: mov QWORD PTR [rbx+0x60],0xf
        memory.writeInt64(rbx + 0x60, 0xF);
        // E92822: mov WORD PTR [rbx+0x68],ax (ax=0)
        memory.writeInt16(rbx + 0x68, (short)0);
        // E92826: mov BYTE PTR [rbx+0x6a],al (al=0)
        memory.writeByte(rbx + 0x6a, (byte)0);
        // E92829: lea rax,[rip+0x3669a78] # 0x44fc2a8
        // E92830: mov QWORD PTR [rbx],rax
        memory.writeInt64(rbx, moduleBase + 0x44FC2A8L);
        // E92833: mov QWORD PTR [rbx+0x70],rcx (rcx=0)
        memory.writeInt64(rbx + 0x70, 0L);
        // E92837: mov QWORD PTR [rbx+0x80],rcx (rcx=0)
        memory.writeInt64(rbx + 0x80, 0L);
        // E9283E: mov QWORD PTR [rbx+0x88],0xf
        memory.writeInt64(rbx + 0x88, 0xF);
        // E92849: mov BYTE PTR [rbx+0x70],0x0
        memory.writeByte(rbx + 0x70, (byte)0);
        // E9284D: mov DWORD PTR [rbx+0x90],ecx (ecx=0)
        memory.writeInt32(rbx + 0x90, 0);
        // E92853: mov DWORD PTR [rbx+0x94],0x29c77f8
        memory.writeInt32(rbx + 0x94, 0x29C77F8);
        // E9285D: mov QWORD PTR [rbx+0x98],0xffffffffffffffff
        memory.writeInt64(rbx + 0x98, -1L);
        // E92868: mov eax,0xffffffff
        // E9286D: mov BYTE PTR [rbx+0xa0],0x3
        memory.writeByte(rbx + 0xa0, (byte)3);
        // E92874: mov DWORD PTR [rbx+0xa4],eax (eax=0xffffffff)
        memory.writeInt32(rbx + 0xa4, -1);
        // E9287A: mov WORD PTR [rbx+0xa8],0x100
        memory.writeInt16(rbx + 0xa8, (short)0x100);
        memory.writeByte(allocatedU + 0xD8L, (byte) 0);
    }
    public static long initialize(long moduleBase, long outputHolder, long descriptor, long scratch, Memory memory, Ports ports) {
        final long allocatedU = ports.call4223b94(0xE0);
        memory.writeByte(scratch + 0x28L, (byte) 0);
        if (memory.readUnsignedByte(descriptor + 0x28L) != 0) {
            memory.writeRaw128(scratch, memory.readRaw128(descriptor));
            memory.writeRaw128(scratch + 0x10L, memory.readRaw128(descriptor + 0x10L));
            memory.writeInt64(descriptor + 0x10L, 0L);
            memory.writeInt64(descriptor + 0x18L, 15L);
            memory.writeByte(descriptor, (byte) 0);
            memory.writeInt32(scratch + 0x20L, memory.readInt32(descriptor + 0x20L));
            memory.writeByte(scratch + 0x28L, (byte) 1);
        }
        writeDefaults(moduleBase, allocatedU, memory);
        int localFlag = memory.readUnsignedByte(scratch + 0x28L);
        if (localFlag != 0) {
            ports.call855f00(allocatedU + 0xB0L, scratch);
            memory.writeInt32(allocatedU + 0xD0L, memory.readInt32(scratch + 0x20L));
            memory.writeByte(allocatedU + 0xD8L, (byte) 1);
            localFlag = memory.readUnsignedByte(scratch + 0x28L);
        }
        if (localFlag != 0) {
            ports.call856050(scratch);
        }
        memory.writeInt64(outputHolder, allocatedU);
        return outputHolder;
    }
}
