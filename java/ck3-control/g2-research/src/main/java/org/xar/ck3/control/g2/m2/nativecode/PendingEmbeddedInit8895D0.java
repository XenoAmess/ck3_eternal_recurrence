package org.xar.ck3.control.g2.m2.nativecode;

/** Actual130-byte normal constructor at8895D0, called by full233B373ACF0. */
public final class PendingEmbeddedInit8895D0 {
    private PendingEmbeddedInit8895D0() { }
    public interface Memory {
        long read64(long address);
        void write32(long address, int value);
        void write64(long address, long value);
    }
    public interface Calls {
        void virtual10(Memory memory, long target, long rcx, long rdx, int r8d);
        void virtual20(Memory memory, long target, long rcx, long rdx, long r8);
    }
    public static long initialize(Memory memory, Calls calls, long receiver, long moduleBase) {
        // LEA rbx,[rcx+0x18] -> rbx = receiver + 0x18
        long rbx = receiver + 0x18;
        // XOR ebp,ebp -> ebp = 0
        long ebp = 0;
        // MOV QWORD PTR [rcx],rbp -> write64(receiver, 0)
        memory.write64(receiver, ebp);
        // LEA rax,[rip+0x3c03cac] -> rax = moduleBase + 0x448D2A0L (vptr448D2A0)
        long rax = moduleBase + 0x448D2A0L;
        // MOV DWORD PTR [rcx+0x8],ebp -> write32(receiver+8, 0)
        memory.write32(receiver + 8, (int)ebp);
        // MOV rsi,rcx -> rsi = receiver
        long rsi = receiver;
        // MOV QWORD PTR [rcx+0x10],rbx -> write64(receiver+0x10, rbx)
        memory.write64(receiver + 0x10, rbx);
        // MOV QWORD PTR [rbx],rax -> write64(rbx, rax)
        memory.write64(rbx, rax);
        // LEA r8d,[rbp+0x8] -> r8d = 8 (since ebp=0)
        int r8d = 8;
        // LEA rax,[rip+0x4c54cd4] -> rax = moduleBase + 0x54DE2E0L (token54DE2E0)
        rax = moduleBase + 0x54DE2E0L;
        // MOV QWORD PTR [rbx+0xc8],rax -> write64(rbx+0xc8, rax)
        memory.write64(rbx + 0xc8, rax);
        // MOV rdx,QWORD PTR [rsi] -> rdx = read64(rsi)
        long rdx = memory.read64(rsi);
        // MOV DWORD PTR [rcx+0xc],ebp -> write32(receiver+0xc, 0)
        memory.write32(receiver + 0xc, (int)ebp);
        // MOV rcx,QWORD PTR [rcx+0x10] -> rcx = read64(receiver+0x10)
        long rcx = memory.read64(receiver + 0x10);
        // MOV rax,QWORD PTR [rcx] -> rax = read64(rcx)
        rax = memory.read64(rcx);
        // CALL QWORD PTR [rax+0x10] -> virtual10
        // First virtual target is read64(read64(pointer)+10)
        long target10 = memory.read64(rax + 0x10);
        calls.virtual10(memory, target10, rcx, rdx, r8d);
        // MOV rax,QWORD PTR [rbx] -> rax = read64(rbx)
        rax = memory.read64(rbx);
        // LEA r8,[rsi+0x8] -> r8 = rsi + 8
        long r8 = rsi + 8;
        // MOV rdx,rsi -> rdx = rsi
        rdx = rsi;
        // MOV QWORD PTR [rsi],rbp -> write64(rsi, 0)
        memory.write64(rsi, ebp);
        // MOV rcx,rbx -> rcx = rbx
        rcx = rbx;
        // MOV QWORD PTR [rsi+0x8],rbp -> write64(rsi+8, 0)
        memory.write64(rsi + 8, ebp);
        // CALL QWORD PTR [rax+0x20] -> virtual20
        // Second target is read64(freshVtable+20)
        long target20 = memory.read64(rax + 0x20);
        calls.virtual20(memory, target20, rcx, rdx, r8);
        // Return receiver (full64 result)
        return receiver;
    }
}