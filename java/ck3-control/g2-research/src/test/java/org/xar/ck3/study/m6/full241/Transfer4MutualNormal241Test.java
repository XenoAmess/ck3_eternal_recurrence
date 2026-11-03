package org.xar.ck3.study.m6.full241;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Floating;
import org.xar.ck3.study.m6.full239.Swap4Full239;

/**
 * One new normal three-known-CALL scenario, not the seven original 239 scenarios.
 * All literal table values, data COPY effects, allocation and FP are explicit owned ports.
 * This manual owner witness establishes no Native/hardware result.
 */
public final class Transfer4MutualNormal241Test {
    private static final long I=0x140000000L,S=0x9008L,F=S-0x458L,E=F-8L,C=E-0x48L;
    private static final long H=F+0x20L,Q=F+0x40L,K=I+0x44BBB10L,L=I+0x54DE268L;
    private static final long D=0x2000L,T=0x3000L,A=0x4000L,B=0x5000L;
    private static final long DB=0x6000L,TB=0x7000L,NEW=0x8000L;
    private static final long ALLOC_TARGET=0xBAD24101L,FREE_TARGET=0xBAD24102L;
    private static final long RET=0xABCD76543210L;
    private static final Bits128 ZERO=new Bits128(0L,0L);
    private static int checks;

    private Transfer4MutualNormal241Test() { }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("one new scenario only");
        threeKnownMovesThenActualCleanup();
        System.out.println("PASS scenes=1 checks="+checks
                +" threeActualKnownMoveCallsReturned=true cleanupBoundaryObserved=true"
                +" old239ScenariosExecuted=0 controlledCopyAllocatorFloatingOnly=true"
                +" represented185Only=true Native=false Game=false hardwareABI=false");
    }

    /** Complete new input and expected output were frozen in ORACLE241-FROZEN.md first. */
    public static void threeKnownMovesThenActualCleanup() {
        Ram m=new Ram();
        m.poke(S,RET);
        m.poke(D,DB);m.poke32(D+8L,3);m.poke32(D+0xCL,1);m.poke(D+0x10L,A);
        m.poke(T,TB);m.poke32(T+8L,3);m.poke32(T+0xCL,2);m.poke(T+0x10L,B);
        m.poke32(DB,0x11223344);
        m.poke32(TB,0x55667788);m.poke32(TB+4L,0x99AABBCC);

        // Artificial RAM at the exact raw source literal. These values are not Native captures.
        m.poke(K+8L,ALLOC_TARGET);m.poke(K+0x10L,FREE_TARGET);
        m.poke32(I+0x49F64F0L,0x3FC00000);

        VolatileBits initial=change(v(0x100L),0xE001L,D,T,
                0x8000000000000038L,0xF000000000000009L,0xE011L);
        NonvolatileBits originalN=n();
        Entry entry=new Entry(I,S,initial,originalN);
        VolatileBits[] result={rax(v(0x1100L),NEW),v(0x2200L),v(0x3300L),v(0x4400L),
                v(0x5500L),v(0x6600L),v(0x7700L),v(0x8800L)};
        int[] fpSteps={0},callSteps={0},budgetSteps={0};
        List<Long> sites=new ArrayList<>();

        Floating fp=new Floating() {
            @Override public Bits128 convertSignedDwords(Bits128 input) {
                equal(fpSteps[0]++,0);equal(input,ZERO);return ZERO;
            }
            @Override public Bits128 multiplyLowSingle(Bits128 input,int multiplierRaw32) {
                equal(fpSteps[0]++,1);equal(input,ZERO);equal(multiplierRaw32,0x3FC00000);return ZERO;
            }
            @Override public int truncateLowSingle(Bits128 input) {
                equal(fpSteps[0]++,2);equal(input,ZERO);return 0;
            }
        };

        Budget budget=(site,cursor,end)->{
            int index=budgetSteps[0]++;
            long[] expectedSites={0xB2EDF0L,0xB2EE82L,0xB2EEE0L,
                    0xB2EE8EL,0xB2EEE0L,0xB2EE9BL,0xB2EEE0L};
            long[] expectedSp={S,F,E,F,E,F,E};
            check(index<expectedSites.length);
            equal(site,expectedSites[index]);equal(cursor,expectedSp[index]);equal(end,0L);
            if(index==1) {
                equal(m.peek(Q),K);equal(m.peek(F+0x448L),L);
                header(m,H,0L,0,0,Q);header(m,D,DB,3,1,A);header(m,T,TB,3,2,B);
            } else if(index==3) {
                equal(callSteps[0],5);equal(fpSteps[0],3);
                equal(m.peek(F-8L),I+0xB2EE87L);
                header(m,H,NEW,1,1,Q);header(m,D,DB,3,0,A);header(m,T,TB,3,2,B);
                equal(m.dword(NEW),0x11223344);
            } else if(index==5) {
                equal(callSteps[0],6);equal(m.peek(F-8L),I+0xB2EE93L);
                header(m,H,NEW,1,1,Q);header(m,D,DB,3,2,A);header(m,T,TB,3,0,B);
                equal(m.dword(DB),0x55667788);equal(m.dword(DB+4L),0x99AABBCC);
            }
        };

        Calls ports=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                int index=callSteps[0]++;check(index<8);sites.add(call.callSiteRva());
                long[] expectedSites={0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,
                        0xB2EFE5L,0xB2EFFEL,0xB2EFFEL,0xB2EEBBL};
                long site=expectedSites[index];
                boolean indirect=index==0||index==4||index==7;
                equal(call.callSiteRva(),site);
                equal(call.kind(),indirect?TargetKind.INDIRECT_ABSOLUTE:TargetKind.DIRECT_RVA);
                equal(call.targetBits(),index==0?ALLOC_TARGET:indirect?FREE_TARGET:0x4226860L);
                equal(call.rspBits(),index==7?F:C);
                equal(m.peek(call.rspBits()-8L),I+site+(indirect?3L:5L));

                VolatileBits expectedV;
                NonvolatileBits expectedN;
                if(index==0) {
                    expectedV=x0(change(initial,K,Q,4L,4L,initial.r9Bits(),initial.r11Bits()),ZERO);
                    expectedN=localN(DB,0L,1L,T,4L,1L,H,D,originalN);
                    equal(fpSteps[0],3);header(m,H,0L,0,0,Q);
                } else if(index==1) {
                    expectedV=change(result[0],NEW,NEW,0L,0L,result[0].r9Bits(),result[0].r11Bits());
                    expectedN=localN(DB,0L,1L,NEW,4L,1L,H,D,originalN);
                    header(m,H,0L,0,0,Q);check(!m.has(NEW));
                } else if(index==2) {
                    expectedV=change(result[1],result[1].raxBits(),NEW,DB,4L,
                            result[1].r9Bits(),result[1].r11Bits());
                    expectedN=localN(DB,0L,1L,NEW,4L,1L,H,D,originalN);
                    // One explicitly selected four-byte effect, not an imported COPY algorithm.
                    equal(m.dword(DB),0x11223344);m.writeDword(NEW,0x11223344);
                } else if(index==3) {
                    expectedV=change(result[2],1L,NEW+4L,0L,0L,result[2].r9Bits(),result[2].r11Bits());
                    expectedN=localN(DB,0L,1L,NEW,4L,1L,H,D,originalN);
                    header(m,H,0L,0,0,Q);check(!m.has(NEW+4L));
                } else if(index==4) {
                    expectedV=change(result[3],K,Q,0L,4L,result[3].r9Bits(),result[3].r11Bits());
                    expectedN=localN(DB,0L,1L,NEW,4L,1L,H,D,originalN);
                    header(m,H,0L,0,0,Q);
                } else if(index==5) {
                    expectedV=change(result[4],3L,DB,TB,8L,result[4].r9Bits(),result[4].r11Bits());
                    expectedN=localN(TB,0L,0L,T,8L,2L,D,T,originalN);
                    header(m,D,DB,3,0,A);header(m,T,TB,3,2,B);
                    equal(m.dword(TB),0x55667788);equal(m.dword(TB+4L),0x99AABBCC);
                    m.writeDword(DB,0x55667788);m.writeDword(DB+4L,0x99AABBCC);
                } else if(index==6) {
                    expectedV=change(result[5],3L,TB,NEW,4L,result[5].r9Bits(),result[5].r11Bits());
                    expectedN=localN(NEW,0L,0L,T,4L,1L,T,H,originalN);
                    header(m,T,TB,3,0,B);header(m,H,NEW,1,1,Q);
                    equal(m.dword(NEW),0x11223344);m.writeDword(TB,0x11223344);
                } else {
                    expectedV=change(result[6],K,Q,NEW,4L,result[6].r9Bits(),result[6].r11Bits());
                    expectedN=localN(D,originalN.rbpBits(),0L,T,originalN.r12Bits(),
                            originalN.r13Bits(),originalN.r14Bits(),originalN.r15Bits(),originalN);
                    header(m,H,NEW,1,0,Q);header(m,D,DB,3,2,A);header(m,T,TB,3,1,B);
                    equal(m.retReads,List.of(I+0xB2EE87L,I+0xB2EE93L,I+0xB2EEA0L));
                }
                equal(call.volatileBits(),expectedV);equal(call.nonvolatileBits(),expectedN);
                return result[index];
            }
            @Override public NormalReturn tail(Tail tail) {throw new AssertionError("unexpected tail");}
            @Override public long readGsQword58() {throw new AssertionError("unexpected GS");}
        };

        NormalReturn out=Swap4Full239.execute(entry,m,ports,fp,budget);
        equal(callSteps[0],8);equal(fpSteps[0],3);equal(budgetSteps[0],7);
        equal(sites,List.of(0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,
                0xB2EFE5L,0xB2EFFEL,0xB2EFFEL,0xB2EEBBL));
        equal(out.volatileBits(),change(result[7],result[7].raxBits(),result[7].rcxBits(),
                result[7].rdxBits(),result[7].r8Bits(),result[7].r9Bits(),S-8L));
        equal(out.nonvolatileBits(),originalN);equal(out.returnRipBits(),RET);equal(out.callerRspBits(),S+8L);
        equal(m.retReads,List.of(I+0xB2EE87L,I+0xB2EE93L,I+0xB2EEA0L));
        header(m,D,DB,3,2,A);header(m,T,TB,3,1,B);header(m,H,NEW,1,0,Q);
        equal(m.dword(DB),0x55667788);equal(m.dword(DB+4L),0x99AABBCC);
        equal(m.dword(TB),0x11223344);equal(m.dword(TB+4L),0x99AABBCC);
        equal(m.dword(NEW),0x11223344);check(!m.has(NEW+4L));
        equal(m.peek(Q),K);equal(m.peek(F+0x448L),L);
        equal(m.peek(K+8L),ALLOC_TARGET);equal(m.peek(K+0x10L),FREE_TARGET);
        equal(m.peek(S),RET);equal(m.peek(S-8L),originalN.rdiBits());
        equal(m.peek(S+8L),originalN.rbxBits());equal(m.peek(S+0x10L),originalN.rsiBits());
        check(!m.readBytes.contains(L));check(!m.readBytes.contains(K));

        // Exact union of byte addresses written by this new source/port trace, including stack.
        Set<Long> expectedWrites=new HashSet<>();
        for(long qword:new long[]{S+8L,S+0x10L,S-8L,F+0x40L,F+0x448L,F+0x20L,
                F+0x28L,F+0x30L,F-8L,E-8L,E-0x10L,E-0x18L,
                C+0x50L,C+0x28L,C+0x58L,C+0x60L,C+0x20L,C-8L})
            bytes(expectedWrites,qword,8);
        bytes(expectedWrites,D+0xCL,4);bytes(expectedWrites,T+0xCL,4);
        bytes(expectedWrites,NEW,4);bytes(expectedWrites,DB,8);bytes(expectedWrites,TB,4);
        equal(m.writtenBytes,expectedWrites);
    }

    private static void header(Ram m,long object,long buffer,int capacity,int count,long allocator) {
        equal(m.peek(object),buffer);equal(m.dword(object+8L),capacity);
        equal(m.dword(object+0xCL),count);equal(m.peek(object+0x10L),allocator);
    }
    private static NonvolatileBits localN(long b,long p,long s,long d,long r12,long r13,
            long r14,long r15,NonvolatileBits original) {
        return new NonvolatileBits(b,p,s,d,r12,r13,r14,r15,original.xmm6());
    }
    private static Bits128 x(long t) {
        return new Bits128(0x8000000000000000L|t,0xF000000000000000L|t);
    }
    private static VolatileBits v(long t) {
        return new VolatileBits(t+1L,t+2L,t+3L,0x8000000000000000L|t+8L,
                0xF000000000000000L|t+9L,t+10L,t+11L,
                x(t+16L),x(t+32L),x(t+48L),x(t+64L),x(t+80L),x(t+96L));
    }
    private static NonvolatileBits n() {
        return new NonvolatileBits(0xB1L,0xB2L,0xB3L,0xB4L,
                0xF000000100000005L,0xB6L,0xB7L,0xB8L,x(0xB9L));
    }
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8,long r9,long r11) {
        return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),r11,
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits x0(VolatileBits v,Bits128 x0) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),
                v.r10Bits(),v.r11Bits(),x0,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits rax(VolatileBits v,long a) {
        return change(v,a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r11Bits());
    }
    private static void bytes(Set<Long> set,long a,int count) {
        for(int j=0;j<count;j++)set.add(a+j);
    }
    private static void equal(Object actual,Object expected) {
        checks++;
        if(!java.util.Objects.equals(actual,expected))
            throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);
    }
    private static void check(boolean condition) {
        checks++;if(!condition)throw new AssertionError("check="+checks);
    }

    /** Pure sparse little-endian RAM. Reads cannot mutate bytes or select source branches. */
    private static final class Ram implements Memory {
        final Map<Long,Integer> data=new HashMap<>();
        final Set<Long> readBytes=new HashSet<>(),writtenBytes=new HashSet<>();
        final List<Long> retReads=new ArrayList<>();
        boolean has(long a) {return data.containsKey(a);}
        void poke(long a,long bits) {
            for(int j=0;j<8;j++)data.put(a+j,(int)(bits>>>(j*8))&255);
        }
        void poke32(long a,int bits) {
            for(int j=0;j<4;j++)data.put(a+j,(bits>>>(j*8))&255);
        }
        long peek(long a) {
            long bits=0L;
            for(int j=0;j<8;j++) {
                Integer b=data.get(a+j);
                if(b==null)throw new UnsupportedOperationException("unheld241RAM "+Long.toHexString(a+j));
                bits|=(long)b<<(j*8);
            }
            return bits;
        }
        int dword(long a) {
            int bits=0;
            for(int j=0;j<4;j++) {
                Integer b=data.get(a+j);
                if(b==null)throw new UnsupportedOperationException("unheld241Dword "+Long.toHexString(a+j));
                bits|=b<<(j*8);
            }
            return bits;
        }
        @Override public long readQword(long a) {
            long value=peek(a);bytes(readBytes,a,8);
            if(a==F-8L)retReads.add(value);
            return value;
        }
        @Override public int readDword(long a) {bytes(readBytes,a,4);return dword(a);}
        @Override public int readUnsignedByte(long a) {
            Integer b=data.get(a);
            if(b==null)throw new UnsupportedOperationException("unheld241Byte "+Long.toHexString(a));
            readBytes.add(a);return b;
        }
        @Override public void writeQword(long a,long value) {bytes(writtenBytes,a,8);poke(a,value);}
        @Override public void writeDword(long a,int value) {bytes(writtenBytes,a,4);poke32(a,value);}
        @Override public void writeByte(long a,int value) {writtenBytes.add(a);data.put(a,value&255);}
        @Override public Bits128 read128(long a) {return new Bits128(readQword(a),readQword(a+8L));}
        @Override public void write128(long a,Bits128 value) {
            writeQword(a,value.lowBits());writeQword(a+8L,value.highBits());
        }
        @Override public int lockedXaddDword(long a,int addend) {
            throw new UnsupportedOperationException("no atomic port in this241scenario");
        }
    }
}
