package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Op;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Scene;
import org.xar.ck3.control.g2.m2.nativecode.QueueClosedData383.Step;

public final class QueueClosedCases383 {
    private QueueClosedCases383() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("known81-false-known227-growth", 0x1100000000L, 0x3300000000L, 0x7FF000000000L, List.of(
                // 1. Predicate (Classify3727580) - known81-false path
                new Step(Op.R8, List.of(0x110000004EL, 0x0L), 0x0L), // cmp BYTE PTR [rcx+0x4e],0x0
                new Step(Op.R32, List.of(0x110000001CL, 0x0L), 0x0L), // cmp DWORD PTR [rcx+0x1c],0x0
                new Step(Op.R64, List.of(0x1100000030L, 0x5500000000L), 0x0L), // mov rax,QWORD PTR [rcx+0x30]
                new Step(Op.R32, List.of(0x110000003CL, 0x0L), 0x0L), // movsxd rcx,DWORD PTR [rcx+0x3c]
                new Step(Op.R32, List.of(0x1100000048L, 0x0L), 0x0L), // cmp DWORD PTR [rbx+0x48],0xffffffff (in update)

                // 2. Lock Acquisition
                new Step(Op.R32, List.of(0x3305C9FF68L, 0x0L), 0x0L), // mov eax,DWORD PTR [rip+0x257807e] (lock)
                new Step(Op.CAS, List.of(0x3305C9FF68L, 0x0L, 0x1L), 0x0L), // lock cmpxchg DWORD PTR [rip+0x2578072],ecx

                // 3. Physical Stack Write
                new Step(Op.W64, List.of(0x7FF000000000L, 0x1100000000L), 0x0L), // mov QWORD PTR [rsp+0x38],rbx

                // 4. Queue Append (Growth Path)
                // Read count and capacity
                new Step(Op.R32, List.of(0x3305468A74L, 0x2L), 0x0L), // movsxd rax,DWORD PTR [rcx+0xc] (count)
                new Step(Op.R32, List.of(0x3305468A70L, 0x2L), 0x0L), // mov ecx,DWORD PTR [rcx+0x8] (capacity)

                // Allocator and Factor
                new Step(Op.R64, List.of(0x3305468A78L, 0x8800000000L), 0x0L), // mov rcx,QWORD PTR [rbx+0x10] (allocator)
                new Step(Op.R32, List.of(0x33049F64F0L, 0x3FC00000L), 0x0L), // mulss xmm0,DWORD PTR [rip+0x4176163] (factor 1.5)

                // Virtual Table and Allocation
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L), // mov rax,QWORD PTR [rcx] (vptr)
                new Step(Op.R64, List.of(0x9900000008L, 0xAB00000000L), 0x0L), // mov rax,QWORD PTR [rax+0x8] (alloc target)
                new Step(Op.ALLOC, List.of(0xAB00000000L, 0x8800000000L, 0x18L, 0x8L), 0xBB00000000L), // call QWORD PTR [rax+0x8] (alloc size 24, align 8)

                // Write Element to New Buffer
                new Step(Op.R32, List.of(0x3305468A74L, 0x2L), 0x0L), // movsxd rdx,DWORD PTR [rbx+0xc] (post-alloc count)
                new Step(Op.R64, List.of(0x7FF000000000L, 0x1100000000L), 0x0L), // mov rcx,QWORD PTR [r14] (element value)
                new Step(Op.W64, List.of(0xBB00000010L, 0x1100000000L), 0x0L), // mov QWORD PTR [rax+rdx*8],rcx

                // Copy Old Buffer (KnownCOPY count16: 2 R128, 2 W128)
                new Step(Op.R32, List.of(0x3305468A74L, 0x2L), 0x0L), // movsxd rax,DWORD PTR [rbx+0xc] (fresh count)
                new Step(Op.R64, List.of(0x3305468A68L, 0xCC00000000L), 0x0L), // mov rdx,QWORD PTR [rbx] (old buffer)
                new Step(Op.R128, List.of(0xCC00000000L, 0x1122334455667788L, 0x0123456789ABCDEFL), 0x0L), // movdqu xmm1,XMMWORD PTR [rdx]
                new Step(Op.R128, List.of(0xCC00000000L, 0x1122334455667788L, 0x0123456789ABCDEFL), 0x0L), // movdqu xmm2,XMMWORD PTR [rdx+r8*1-0x10] (same address as first)
                new Step(Op.W128, List.of(0xBB00000000L, 0x1122334455667788L, 0x0123456789ABCDEFL), 0x0L), // movdqu XMMWORD PTR [rcx],xmm1
                new Step(Op.W128, List.of(0xBB00000000L, 0x1122334455667788L, 0x0123456789ABCDEFL), 0x0L), // movdqu XMMWORD PTR [rcx+r8*1-0x10],xmm2 (same address as first)

                // Release Old Buffer
                new Step(Op.R64, List.of(0x3305468A78L, 0x8800000000L), 0x0L), // mov rcx,QWORD PTR [rbx+0x10] (fresh allocator)
                new Step(Op.R64, List.of(0x3305468A68L, 0xCC00000000L), 0x0L), // mov rdx,QWORD PTR [rbx] (old buffer)
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L), // mov rax,QWORD PTR [rcx] (vptr)
                new Step(Op.R64, List.of(0x9900000010L, 0xAC00000000L), 0x0L), // mov rax,QWORD PTR [rax+0x10] (free target)
                new Step(Op.FREE, List.of(0xAC00000000L, 0x8800000000L, 0xCC00000000L, 0x8L), 0x0L), // call QWORD PTR [rax+0x10]

                // Publish New State
                new Step(Op.W32, List.of(0x3305468A70L, 0x3L), 0x0L), // mov DWORD PTR [rbx+0x8],ebp (capacity 3)
                new Step(Op.W64, List.of(0x3305468A68L, 0xBB00000000L), 0x0L), // mov QWORD PTR [rbx],rdi (base BB...)
                new Step(Op.W32, List.of(0x3305468A74L, 0x3L), 0x0L), // mov DWORD PTR [rbx+0xc],esi (count 3)

                // Update Flag and Unlock
                new Step(Op.W8, List.of(0x110000004EL, 0x1L), 0x0L), // mov BYTE PTR [rbx+0x4e],0x1
                new Step(Op.W32, List.of(0x3305C9FF68L, 0x0L), 0x0L) // mov DWORD PTR [rip+0x2578047],0x0
            ))
        );
    }
}