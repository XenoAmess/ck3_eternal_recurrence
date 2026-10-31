package org.xar.ck3.control.g2.m2.nativecode;

/** Finite normal-path semantics of the held actual4 leaf at RVA2756120.
 * Caller supplies writable memory and its actual image basis; no Game query/allocation.
 */
public final class PendingComponentInit2756120 {
    private PendingComponentInit2756120() { }
    public interface Memory {
        void write8(long address, int value);
        void write32(long address, int value);
        void write64(long address, long value);
    }
    public static long initialize(Memory memory, long componentAddress, long moduleBase) {
        long r8 = 0L;
        long rax = 0L;
        long rdx = 0L;
        long rcx = componentAddress;

        // 2756120: xor r8d,r8d -> r8 = 0
        r8 = 0L;

        // 2756123: mov QWORD PTR [rcx+0x18],0xf
        memory.write64(rcx + 0x18L, 0xFL);

        // 275612b: lea rax,[rcx+0x78]
        rax = rcx + 0x78L;

        // 275612f: mov QWORD PTR [rcx],r8
        memory.write64(rcx, r8);

        // 2756132: lea rdx,[rip+0x2d9019f] # 0x54e62d8
        // moduleBase is derived as literalToken - 0x54E62D8L, so rip-relative target is moduleBase + 0x54E62D8L
        rdx = moduleBase + 0x54E62D8L;

        // 2756139: mov QWORD PTR [rax],r8
        memory.write64(rax, r8);

        // 275613c: mov QWORD PTR [rax+0x10],r8
        memory.write64(rax + 0x10L, r8);

        // 2756140: mov QWORD PTR [rax+0x18],0xf
        memory.write64(rax + 0x18L, 0xFL);

        // 2756148: mov QWORD PTR [rax+0x20],r8
        memory.write64(rax + 0x20L, r8);

        // 275614c: mov QWORD PTR [rax+0x30],r8
        memory.write64(rax + 0x30L, r8);

        // 2756150: mov QWORD PTR [rax+0x38],0xf
        memory.write64(rax + 0x38L, 0xFL);

        // 2756158: mov QWORD PTR [rax+0x40],r8
        memory.write64(rax + 0x40L, r8);

        // 275615c: mov QWORD PTR [rax+0x50],r8
        memory.write64(rax + 0x50L, r8);

        // 2756160: mov QWORD PTR [rax+0x58],0xf
        memory.write64(rax + 0x58L, 0xFL);

        // 2756168: mov QWORD PTR [rax+0x60],r8
        memory.write64(rax + 0x60L, r8);

        // 275616c: mov QWORD PTR [rax+0x68],r8
        memory.write64(rax + 0x68L, r8);

        // 2756170: mov QWORD PTR [rax+0x70],rdx
        memory.write64(rax + 0x70L, rdx);

        // 2756174: mov QWORD PTR [rcx+0x1e8],rax
        memory.write64(rcx + 0x1E8L, rax);

        // 275617b: mov rax,rcx
        rax = rcx;

        // 275617e: mov QWORD PTR [rcx+0x10],r8
        memory.write64(rcx + 0x10L, r8);

        // 2756182: mov QWORD PTR [rcx+0x20],r8
        memory.write64(rcx + 0x20L, r8);

        // 2756186: mov QWORD PTR [rcx+0x30],r8
        memory.write64(rcx + 0x30L, r8);

        // 275618a: mov QWORD PTR [rcx+0x38],0xf
        memory.write64(rcx + 0x38L, 0xFL);

        // 2756192: mov QWORD PTR [rcx+0x40],r8
        memory.write64(rcx + 0x40L, r8);

        // 2756196: mov QWORD PTR [rcx+0x50],r8
        memory.write64(rcx + 0x50L, r8);

        // 275619a: mov QWORD PTR [rcx+0x58],0xf
        memory.write64(rcx + 0x58L, 0xFL);

        // 27561a2: mov QWORD PTR [rcx+0x60],r8
        memory.write64(rcx + 0x60L, r8);

        // 27561a6: mov QWORD PTR [rcx+0x68],r8
        memory.write64(rcx + 0x68L, r8);

        // 27561aa: mov QWORD PTR [rcx+0x70],rdx
        memory.write64(rcx + 0x70L, rdx);

        // 27561ae: mov QWORD PTR [rcx+0xf0],r8
        memory.write64(rcx + 0xF0L, r8);

        // 27561b5: mov QWORD PTR [rcx+0x100],r8
        memory.write64(rcx + 0x100L, r8);

        // 27561bc: mov QWORD PTR [rcx+0x108],0xf
        memory.write64(rcx + 0x108L, 0xFL);

        // 27561c7: mov QWORD PTR [rcx+0x110],r8
        memory.write64(rcx + 0x110L, r8);

        // 27561ce: mov QWORD PTR [rcx+0x120],r8
        memory.write64(rcx + 0x120L, r8);

        // 27561d5: mov QWORD PTR [rcx+0x128],0xf
        memory.write64(rcx + 0x128L, 0xFL);

        // 27561e0: mov QWORD PTR [rcx+0x130],r8
        memory.write64(rcx + 0x130L, r8);

        // 27561e7: mov QWORD PTR [rcx+0x140],r8
        memory.write64(rcx + 0x140L, r8);

        // 27561ee: mov QWORD PTR [rcx+0x148],0xf
        memory.write64(rcx + 0x148L, 0xFL);

        // 27561f9: mov QWORD PTR [rcx+0x150],r8
        memory.write64(rcx + 0x150L, r8);

        // 2756200: mov QWORD PTR [rcx+0x158],r8
        memory.write64(rcx + 0x158L, r8);

        // 2756207: mov QWORD PTR [rcx+0x160],rdx
        memory.write64(rcx + 0x160L, rdx);

        // 275620e: mov QWORD PTR [rcx+0x168],r8
        memory.write64(rcx + 0x168L, r8);

        // 2756215: mov QWORD PTR [rcx+0x178],r8
        memory.write64(rcx + 0x178L, r8);

        // 275621c: mov QWORD PTR [rcx+0x180],0xf
        memory.write64(rcx + 0x180L, 0xFL);

        // 2756227: mov QWORD PTR [rcx+0x188],r8
        memory.write64(rcx + 0x188L, r8);

        // 275622e: mov QWORD PTR [rcx+0x198],r8
        memory.write64(rcx + 0x198L, r8);

        // 2756235: mov QWORD PTR [rcx+0x1a0],0xf
        memory.write64(rcx + 0x1A0L, 0xFL);

        // 2756240: mov QWORD PTR [rcx+0x1a8],r8
        memory.write64(rcx + 0x1A8L, r8);

        // 2756247: mov QWORD PTR [rcx+0x1b8],r8
        memory.write64(rcx + 0x1B8L, r8);

        // 275624e: mov QWORD PTR [rcx+0x1c0],0xf
        memory.write64(rcx + 0x1C0L, 0xFL);

        // 2756259: mov QWORD PTR [rcx+0x1c8],r8
        memory.write64(rcx + 0x1C8L, r8);

        // 2756260: mov QWORD PTR [rcx+0x1d0],r8
        memory.write64(rcx + 0x1D0L, r8);

        // 2756267: mov QWORD PTR [rcx+0x1d8],rdx
        memory.write64(rcx + 0x1D8L, rdx);

        // 275626e: mov QWORD PTR [rcx+0x1e0],rcx
        memory.write64(rcx + 0x1E0L, rcx);

        // 2756275: mov QWORD PTR [rcx+0x1f0],r8
        memory.write64(rcx + 0x1F0L, r8);

        // 275627c: mov QWORD PTR [rcx+0x200],r8
        memory.write64(rcx + 0x200L, r8);

        // 2756283: mov QWORD PTR [rcx+0x208],0xf
        memory.write64(rcx + 0x208L, 0xFL);

        // 275628e: mov QWORD PTR [rcx+0x210],r8
        memory.write64(rcx + 0x210L, r8);

        // 2756295: mov QWORD PTR [rcx+0x220],r8
        memory.write64(rcx + 0x220L, r8);

        // 275629c: mov QWORD PTR [rcx+0x228],0xf
        memory.write64(rcx + 0x228L, 0xFL);

        // 27562a7: mov QWORD PTR [rcx+0x230],r8
        memory.write64(rcx + 0x230L, r8);

        // 27562ae: mov QWORD PTR [rcx+0x240],r8
        memory.write64(rcx + 0x240L, r8);

        // 27562b5: mov QWORD PTR [rcx+0x248],0xf
        memory.write64(rcx + 0x248L, 0xFL);

        // 27562c0: mov QWORD PTR [rcx+0x250],0xffffffffffffffff
        memory.write64(rcx + 0x250L, -1L);

        // 27562cb: mov DWORD PTR [rcx+0x258],0xffffffff
        memory.write32(rcx + 0x258L, -1);

        // 27562d5: mov BYTE PTR [rcx+0x25c],r8b
        memory.write8(rcx + 0x25CL, (int) r8);

        // 27562dc: mov DWORD PTR [rcx+0x260],r8d
        memory.write32(rcx + 0x260L, (int) r8);

        // 27562e3: mov BYTE PTR [rcx+0x264],0x1
        memory.write8(rcx + 0x264L, 1);

        // 27562ea: ret
        return rax;
    }
}
