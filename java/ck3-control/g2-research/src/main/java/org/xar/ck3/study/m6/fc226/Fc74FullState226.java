package org.xar.ck3.study.m6.fc226;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class Fc74FullState226 {
    private Fc74FullState226() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls lower) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(lower);

        long image = entry.imageBaseBits();
        long S = entry.rspBits();
        long pre = S - 0x28L;

        // Owned frame initialization per contract
        memory.writeQword(S + 0x8L, entry.nonvolatileBits().rbxBits());
        memory.writeQword(S + 0x10L, entry.nonvolatileBits().rsiBits());
        memory.writeQword(S - 0x8L, entry.nonvolatileBits().rdiBits());

        // Registers initialization
        GovernmentCallee164Api.Entry calleeEntry = new GovernmentCallee164Api.Entry(
                image, pre, entry.volatileBits(), entry.nonvolatileBits());
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(calleeEntry);

        // MemoryView adapter
        NativeTaskMemory memView = new NativeTaskMemory() {
            @Override public long readPointer(long address) {
                return memory.readQword(address);
            }
            @Override public int readInt32(long address) {
                int val = memory.readDword(address);
                if (address == image + 0x542F328L) {
                    r.rcx = Integer.toUnsignedLong(val);
                }
                return val;
            }
            @Override public void writeInt32(long address, int value) {
                memory.writeDword(address, value);
            }
            @Override public void writeInt64(long address, long value) {
                memory.writeQword(address, value);
            }
        };

        // Ports adapter
        Fc74Api238.Ports ports = new Fc74Api238.Ports() {
        // Helper to perform owned CALL: push return address, invoke, apply volatile bits
        private void performCall(long siteRva, GovernmentCrtBoundary185Api.TargetKind kind, long targetBits) {
            // Contract says: "DirecttargetBits areRVA... IATsites0x424FC83 length6... OtherdirectCALL sites... all length5."
            // So for IAT (INDIRECT_ABSOLUTE), length is 6. For DIRECT_RVA, length is 5.
            long instructionLength = (kind == GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE) ? 6L : 5L;
            long retAddr = image + siteRva + instructionLength;

            memory.writeQword(pre - 0x8L, retAddr);

            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                    siteRva, kind, targetBits, pre, r.volatileBits(), r.nonvolatileBits());

            GovernmentPrimaryTail155Api.VolatileBits v = lower.invoke(call);
            r.apply(v);
        }

            @Override public int callIat43da738(NativeTaskMemory m, long siteRva, long actualTarget, int entryEcxBits) {
                // actualTarget is already read by caller logic in Fc74Target424FC74 via memory.readPointer
                // We must NOT re-read it here. We use the provided actualTarget.
                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget);

                // Post-call effects for first IAT:
                // "firstIAT afterapply r.rbx=uint32((int)r.rax)"
                r.rbx = Integer.toUnsignedLong((int) r.rax);

                return (int) r.rax;
            }
            @Override public long call424e900(NativeTaskMemory m, long siteRva, int ecxBits) {
                // Set RCX to uint32(index) before call?
                // Contract: "CallE900 setsRCX=uint32(index);applyallV;sourceRDI=actualreturnedRAX."
                // The index is passed as ecxBits. We set r.rcx before invoking.
                r.rcx = Integer.toUnsignedLong(ecxBits);

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E900L);

                // Post-call effects for E900:
                // "sourceRDI=actualreturnedRAX. If nonzero and not-1, sourcefinalRSI=RDI beforefinalIAT. If-1 sourcezerosRDI/RSI; ifzero RDI0/RSIincoming until laterpath."
                // "E900afterapply r.rdi=r.rax; ifrax==-1 setrdi=rsi=0; else ifrax!=0 r.rsi=r.rdi; zero leavesRSIincoming."
                r.rdi = r.rax;
                if (r.rax == -1L) {
                    r.rdi = 0L;
                    r.rsi = 0L;
                } else if (r.rax != 0L) {
                    r.rsi = r.rdi;
                }

                return r.rax;
            }
            @Override public int call424e948(NativeTaskMemory m, long siteRva, int ecxBits, long rdxBits) {
                // Contract: "CallE948 setsRCX=uint32(index),RDX=providedfullraw(-1,0,block),applyallV;only FCB9 EAX0 branch zerosRDI/RSI beforefinish."
                r.rcx = Integer.toUnsignedLong(ecxBits);
                r.rdx = rdxBits;

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E948L);

                // Post-call effects for E948:
                // "E948afterapply: ONLY atsiteFCB9 iflow32RAX==0 zeroRDI/RSI;other sites keep."
                if (siteRva == 0x424FCB9L) {
                    if ((int) r.rax == 0) {
                        r.rdi = 0L;
                        r.rsi = 0L;
                    }
                }

                return (int) r.rax;
            }
            @Override public long call424e2ec(NativeTaskMemory m, long siteRva, long rcxBits, long rdxBits) {
                // Contract: "CallE2EC setsRCX=1,RDX=0x3C8 with32bitzeroextension;applyallV;RDI=allocatedRAX."
                // The arguments rcxBits and rdxBits are provided by the business logic (1 and 0x3C8).
                // We set them as full raw 64-bit values (zero-extended from 32-bit inputs if necessary, but here they are longs).
                r.rcx = Integer.toUnsignedLong((int) rcxBits);
                r.rdx = Integer.toUnsignedLong((int) rdxBits);

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E2ECL);

                // Post-call effects for E2EC:
                // "E2EC afterapply r.rdi=r.rax."
                r.rdi = r.rax;

                return r.rax;
            }
            @Override public void call424e364(NativeTaskMemory m, long siteRva, long rcxBits) {
                // Contract: "CallFree(FCE8 orFD17) setsRCX=rawargument,applyallV;afterFCE8 cleanup sourcezerosRDI/RSI;afterFD17 success sourceRSI=RDI."
                // "RCX for Free/F8A8 pointers must be fullraw64, neveruint32cast"
                r.rcx = rcxBits;

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E364L);

                // Post-call effects for Free:
                if (siteRva == 0x424FCE8L) {
                    r.rdi = 0L;
                    r.rsi = 0L;
                } else if (siteRva == 0x424FD17L) {
                    r.rsi = r.rdi;
                }
            }
            @Override public void call424f8a8(NativeTaskMemory m, long siteRva, long rcxBits) {
                // Contract: "CallF8A8 setsRCX=block,actualFD10CALL withcurrentRSIstillincoming."
                // "RCX for Free/F8A8 pointers must be fullraw64, neveruint32cast"
                r.rcx = rcxBits;

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424F8A8L);

                // Post-call effects for F8A8:
                // "F8A8 afterapply keepRDI/RSI."
                // No changes to RDI/RSI.
            }
            @Override public void callIat43da420(NativeTaskMemory m, long siteRva, long actualTarget, int ecxBits) {
                // Contract: "Before finalIAT setRCX=uint32(savedError), RBXsavedError and sourcechosenRDI/RSI must stillbeoffered, RAX NOT prematurely set tobusinessselected value."
                // "lastIAT beforecall RCX=uint32(savedError) butRAX staysactualpriorcallRAX untilafterlastIAT."
                // savedError is stored in RBX by the first IAT handler.
                r.rcx = Integer.toUnsignedLong((int) r.rbx);

                performCall(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget);

                // Post-call effects for last IAT:
                // "After actualbusinessbody including finalIAT returns selected: sourceNEG RDI->SBB RAX,RAX->AND RAX,RSI yields selected under known sourcechosenRDI/RSI and normalpreservation ofnonvolatile portstate; overwrite ONLY RAX withactualscalarbusinessresult afterfinalIAT, retain all OTHER actualfinalV/XMM."
                // The business logic returns 'selected' which is the result of the final calculation.
                // However, the contract says "overwrite ONLY RAX withactualscalarbusinessresult afterfinalIAT".
                // The 'selected' value is returned by Fc74Target424FC74.execute.
                // We need to ensure RAX is set to 'selected' AFTER the last IAT call returns.
                // But wait, the last IAT call is part of the business logic flow.
                // The contract says: "Reuse current Fc74Target424FC74.execute... THREEARG businessbody."
                // The business body calls callIat43da420.
                // After callIat43da420 returns, the business body returns 'selected'.
                // The wrapper then sets r.rax = selected.
                // So inside callIat43da420, we just perform the call. The RAX update happens in the wrapper after execute returns.
            }
        };

        // Business execution
        Fc74Api238.Input input = new Fc74Api238.Input(image, (int) entry.volatileBits().rcxBits());
        long selected = Fc74Target424FC74.execute(memView, ports, input);

        // Epilogue
        // "overwrite ONLY RAX withactualscalarbusinessresult afterfinalIAT, retain all OTHER actualfinalV/XMM"
        r.rax = selected;

        // "Epilogue exactRAM order freshR64[S+0x8]restoreRBX, freshR64[S+0x10]restoreRSI, SPpre+0x20 thenPOP RDI freshR64[S-0x8], actualRET freshR64[S],callerSP=S+0x8."

        // Restore RBX from S+0x8
        r.rbx = memory.readQword(S + 0x8L);
        // Restore RSI from S+0x10
        r.rsi = memory.readQword(S + 0x10L);
        // Adjust SP
        r.rsp = pre + 0x20L;
        // POP RDI from S-0x8 (which is pre+0x20)
        r.rdi = memory.readQword(S - 0x8L);
        // RET reads from S (which is pre+0x28? No, S is the original SP. pre = S - 0x28.
        // The return address is at S.
        // "actualRET freshR64[S]"
        long actualRip = memory.readQword(S);

        // Caller SP is S + 0x8
        long callerRsp = S + 0x8L;

        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), actualRip, callerRsp, r.nonvolatileBits());
    }
}