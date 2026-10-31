package org.xar.ck3.control.g2.m2.nativecode;

/** Complete held127B normal105D2D0; two actual virtual calls remain explicit ports. */
public final class PendingContextChildInit105D2D0 {
    private PendingContextChildInit105D2D0() { }
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
        // Prologue stack operations (mov rsp+0x8, rsp+0x10, rsp+0x18, push rdi, sub rsp) are ignored per contract.

        // 105d2e4: lea rbx,[rcx+0x18] -> rbx = receiver + 0x18
        long rbx = receiver + 0x18;

        // 105d2e8: xor ebp,ebp -> ebp = 0
        long ebp = 0;

        // 105d2ea: mov QWORD PTR [rcx],rbp -> write64(receiver, 0)
        memory.write64(receiver, ebp);

        // 105d2ed: lea rax,[rip+0x34bd13c] # 0x451a430 -> rax = moduleBase + 0x451a430
        long rax = moduleBase + 0x451a430;

        // 105d2f4: mov DWORD PTR [rcx+0x8],ebp -> write32(receiver+8, 0)
        memory.write32(receiver + 0x8, (int)ebp);

        // 105d2f7: mov rsi,rcx -> rsi = receiver
        long rsi = receiver;

        // 105d2fa: mov QWORD PTR [rcx+0x10],rbx -> write64(receiver+0x10, rbx)
        memory.write64(receiver + 0x10, rbx);

        // 105d2fe: mov QWORD PTR [rbx],rax -> write64(rbx, rax)
        memory.write64(rbx, rax);

        // 105d301: lea r8d,[rbp+0x1] -> r8d = ebp + 1 = 1
        int r8d = (int)(ebp + 1);

        // 105d305: lea rax,[rip+0x4483224] # 0x54e0530 -> rax = moduleBase + 0x54e0530
        rax = moduleBase + 0x54e0530;

        // 105d30c: mov QWORD PTR [rbx+0x10],rax -> write64(rbx+0x10, rax)
        memory.write64(rbx + 0x10, rax);

        // 105d310: mov rdx,QWORD PTR [rsi] -> rdx = read64(rsi)
        long rdx = memory.read64(rsi);

        // 105d313: mov DWORD PTR [rcx+0xc],ebp -> write32(receiver+0xc, 0)
        memory.write32(receiver + 0xc, (int)ebp);

        // 105d316: mov rcx,QWORD PTR [rcx+0x10] -> rcx = read64(receiver+0x10)
        long rcx = memory.read64(receiver + 0x10);

        // 105d31a: mov rax,QWORD PTR [rcx] -> rax = read64(rcx)
        rax = memory.read64(rcx);

        // 105d31d: call QWORD PTR [rax+0x10] -> target = read64(rax+0x10)
        long target1 = memory.read64(rax + 0x10);

        // First virtual call: virtual10(memory, target1, rcx, rdx, r8d)
        // Note: rcx is the value loaded at 105d316, rdx is the value loaded at 105d310
        calls.virtual10(memory, target1, rcx, rdx, r8d);

        // 105d320: mov rax,QWORD PTR [rbx] -> rax = read64(rbx)
        rax = memory.read64(rbx);

        // 105d323: lea r8,[rsi+0x8] -> r8 = rsi + 8 = receiver + 8
        long r8 = rsi + 0x8;

        // 105d327: mov rdx,rsi -> rdx = rsi
        rdx = rsi;

        // 105d32a: mov QWORD PTR [rsi],rbp -> write64(rsi, 0)
        memory.write64(rsi, ebp);

        // 105d32d: mov rcx,rbx -> rcx = rbx
        rcx = rbx;

        // 105d330: mov QWORD PTR [rsi+0x8],rbp -> write64(rsi+8, 0)
        memory.write64(rsi + 0x8, ebp);

        // 105d334: call QWORD PTR [rax+0x20] -> target = read64(rax+0x20)
        long target2 = memory.read64(rax + 0x20);

        // Second virtual call: virtual20(memory, target2, rcx, rdx, r8)
        // Note: rcx is rbx, rdx is rsi, r8 is receiver+8
        calls.virtual20(memory, target2, rcx, rdx, r8);

        // Epilogue stack operations (mov rbx, rax, rsi, rbp, add rsp, pop rdi, ret) are ignored per contract.
        // The function returns the original receiver.
        return receiver;
    }
}