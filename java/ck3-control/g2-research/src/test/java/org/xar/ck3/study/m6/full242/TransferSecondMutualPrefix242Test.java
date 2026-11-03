package org.xar.ck3.study.m6.full242;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Floating;
import org.xar.ck3.study.m6.full239.Swap4Full239;

/** One NEW controlled software prefix. No old239 test, actual child algorithm or hardware claim. */
public final class TransferSecondMutualPrefix242Test {
    private static final long I=0x140000000L,S=0x9008L,F=S-0x458L,C=F-8L,H=C-0x48L,TEMP=F+0x20L;
    private static final long D=0x2000L,T=0x3000L,DB=0x4000L,TB=0x5000L,A=0xA000L,B=0xA100L;
    private static final long ND=0x6000L,NT=0x7000L,NDB=0x8000L,NTB=0x8100L,ALLOC=0x8200L;
    private static final long A2=0xB000L,TAB2=0xB100L,FREE2=0xBAD002L;
    // These are explicitly synthetic owned-RAM fixture slots, not actual static contents.
    private static final long L=I+0x44BBB10L,ALLOC_TARGET=0xBAD010L,FREE_TARGET=0xBAD011L;
    private static final long RET=0x123456789ABCDEF0L;
    private static int checks;
    private TransferSecondMutualPrefix242Test() { }

    public static void main(String[] args) {
        secondMoveFreeThrowsAfterFreshSavedState();
        System.out.println("PASS newScenes=1 checks="+checks
                +" successfulFirstMutualReturn=true secondMutualExceptionalPrefix=true freshSavedN=true"
                +" positiveSmallCounts=true syntheticLiteralSlots=true controlledOpaqueChildrenOnly=true"
                +" intermediateFullReturnDirectlyObserved=false fullHardwareABI=false Native=false Game=false");
    }

    private static void secondMoveFreeThrowsAfterFreshSavedState() {
        Ram m=ram();
        VolatileBits initial=state(v(0x100L),0xE001L,D,T,0x8000000000000038L);
        NonvolatileBits original=n0(),fresh=n1();
        Entry entry=new Entry(I,S,initial,original);
        VolatileBits[] returned={state(v(0x1000L),ALLOC,0x1002L,0x1003L,0x1008L),
                v(0x2000L),v(0x3000L),v(0x4000L),v(0x5000L)};
        int[] invoked={0},fpCalls={0},moveEntries={0};
        List<BudgetEvent> events=new ArrayList<>();
        RuntimeException boundary=new IllegalStateException("second-mutual-free242-original-object");

        Floating floating=new Floating() {
            @Override public Bits128 convertSignedDwords(Bits128 input) {
                eq(fpCalls[0]++,0);eq(invoked[0],0);eq(input,new Bits128(0,0));return input;
            }
            @Override public Bits128 multiplyLowSingle(Bits128 input,int multiplier) {
                eq(fpCalls[0]++,1);eq(invoked[0],0);eq(input,new Bits128(0,0));eq(multiplier,0x3FC00000);return input;
            }
            @Override public int truncateLowSingle(Bits128 input) {
                eq(fpCalls[0]++,2);eq(invoked[0],0);eq(input,new Bits128(0,0));return 0;
            }
        };

        Budget budget=(site,cursor,end)->{
            events.add(new BudgetEvent(site,cursor,end));eq(end,0L);
            if(site==0xB2EEE0L) {
                int index=moveEntries[0]++;
                eq(cursor,C);eq(m.peek(C),I+(index==0?0xB2EE87L:0xB2EE93L));
                check(index<2);
            }
            if(site==0xB2EE8EL) {
                eq(invoked[0],5);eq(fpCalls[0],3);eq(cursor,F);
                eq(m.peek(C),I+0xB2EE87L);
                eq(m.peek(TEMP),ALLOC);eq(m.peek32(TEMP+8),1);eq(m.peek32(TEMP+0xCL),1);
                eq(m.peek32(D+0xCL),0);
                eq(m.qReads.subList(m.qReads.size()-9,m.qReads.size()),
                        List.of(F+0x10L,F+8L,F-0x30L,F-0x28L,F,F-0x20L,F-0x18L,F-0x10L,C));
                eq(m.qReads.stream().filter(a->a==C).count(),1L);
                check(!m.qReads.contains(S));
            }
        };

        Calls calls=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                int index=invoked[0]++;
                check(index<6);eq(fpCalls[0],3);eq(call.rspBits(),H);
                long[] sites={0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,0xB2EFE5L,0xB2EF06L};
                long site=sites[index];
                boolean indirect=index==0||index==4||index==5;
                eq(call.callSiteRva(),site);
                eq(call.kind(),indirect?TargetKind.INDIRECT_ABSOLUTE:TargetKind.DIRECT_RVA);
                eq(call.targetBits(),index==0?ALLOC_TARGET:index==4?FREE_TARGET:index==5?FREE2:0x4226860L);
                eq(m.peek(H-8L),I+site+(indirect?3L:5L));
                if(index<5) {
                    NonvolatileBits expected=new NonvolatileBits(DB,0L,1L,index==0?T:ALLOC,4L,1L,TEMP,D,original.xmm6());
                    eq(call.nonvolatileBits(),expected);
                }
                if(index==0) {
                    eq(call.volatileBits(),zeroX0(state(initial,L,F+0x40L,4L,4L)));
                } else if(index==1) {
                    eq(call.volatileBits(),state(returned[0],ALLOC,ALLOC,0L,0L));
                } else if(index==2) {
                    eq(call.volatileBits(),state(returned[1],returned[1].raxBits(),ALLOC,DB,4L));
                } else if(index==3) {
                    eq(call.volatileBits(),state(returned[2],1L,ALLOC+4L,0L,0L));
                } else if(index==4) {
                    eq(call.volatileBits(),state(returned[3],L,F+0x40L,0L,4L));
                    // These aliases are the first Move's genuine conditional and pushed save slots.
                    // No actual COPY/free semantics are assigned to the controlled port.
                    m.writeQword(F,fresh.rbxBits());
                    m.writeQword(F-0x10L,fresh.rbpBits());
                    m.writeQword(F+8L,fresh.rsiBits());
                    m.writeQword(F+0x10L,fresh.rdiBits());
                    m.writeQword(F-0x28L,fresh.r12Bits());
                    m.writeQword(F-0x30L,fresh.r13Bits());
                    m.writeQword(F-0x18L,fresh.r14Bits());
                    m.writeQword(F-0x20L,fresh.r15Bits());
                } else {
                    eq(call.volatileBits(),state(returned[4],TAB2,A2,NDB,4L));
                    eq(call.nonvolatileBits(),new NonvolatileBits(ND,fresh.rbpBits(),fresh.rsiBits(),NT,
                            fresh.r12Bits(),fresh.r13Bits(),ND,NT,original.xmm6()));
                    eq(m.peek(C),I+0xB2EE93L);
                    eq(m.peek(C-8L),fresh.rbpBits());
                    eq(m.peek(C-0x10L),fresh.r14Bits());
                    eq(m.peek(C-0x18L),fresh.r15Bits());
                    throw boundary;
                }
                return returned[index];
            }
            @Override public NormalReturn tail(Tail transfer) { throw new AssertionError("unexpected242TAIL"); }
            @Override public long readGsQword58() { throw new AssertionError("unexpected242GS"); }
        };

        boolean received=false;
        try {
            Swap4Full239.execute(entry,m,calls,floating,budget);
            throw new AssertionError("unexpected normal top-level242 return");
        } catch(RuntimeException failure) {
            check(failure==boundary);received=true;
        }
        check(received);eq(invoked[0],6);eq(fpCalls[0],3);eq(moveEntries[0],2);
        eq(events,List.of(new BudgetEvent(0xB2EDF0L,S,0L),new BudgetEvent(0xB2EE82L,F,0L),
                new BudgetEvent(0xB2EEE0L,C,0L),new BudgetEvent(0xB2EE8EL,F,0L),new BudgetEvent(0xB2EEE0L,C,0L)));
        eq(m.writes,expectedWrites(original,fresh));eq(m.writes.size(),40);
        eq(m.peek(C),I+0xB2EE93L);eq(m.peek(H-8L),I+0xB2EF09L);
        eq(m.qReads.stream().filter(a->a==C).count(),1L);
        check(!m.qReads.contains(S));check(!m.qReads.contains(S+8L));
        check(!m.qReads.contains(S+0x10L));check(!m.qReads.contains(S-8L));
        eq(m.peek(S),RET);eq(m.peek(S+8L),original.rbxBits());
        eq(m.peek(S+0x10L),original.rsiBits());eq(m.peek(S-8L),original.rdiBits());
        eq(m.peek(TEMP),ALLOC);eq(m.peek32(TEMP+8),1);eq(m.peek32(TEMP+0xCL),1);
        eq(m.peek32(D+0xCL),0);eq(m.peek32(T+0xCL),2);
        eq(m.peek(ND),NDB);eq(m.peek32(ND+8),17);eq(m.peek32(ND+0xCL),5);eq(m.peek(ND+0x10L),A2);
        eq(m.peek(NT),NTB);eq(m.peek32(NT+8),19);eq(m.peek32(NT+0xCL),6);eq(m.peek(NT+0x10L),A2);
        eq(m.peek(F+0x40L),L);eq(m.peek(F+0x448L),I+0x54DE268L);
        eq(m.qReads.stream().filter(a->a>=L&&a<L+0x18L).toList(),List.of(L+8L,L+0x10L));
        check(!m.qReads.contains(I+0x54DE268L));
        eq(m.dReads.stream().filter(a->a==I+0x49F64F0L).count(),1L);
    }

    private static List<Write> expectedWrites(NonvolatileBits original,NonvolatileBits fresh) {
        List<Write> w=new ArrayList<>();
        q(w,S+8L,original.rbxBits());q(w,S+0x10L,original.rsiBits());q(w,S-8L,original.rdiBits());
        q(w,F+0x40L,L);q(w,F+0x448L,I+0x54DE268L);q(w,F+0x20L,0);q(w,F+0x28L,0);q(w,F+0x30L,F+0x40L);
        q(w,C,I+0xB2EE87L);
        q(w,C-8L,original.rbpBits());q(w,C-0x10L,original.r14Bits());q(w,C-0x18L,original.r15Bits());
        q(w,H+0x50L,D);d(w,TEMP+0xCL,0);q(w,H+0x28L,original.r12Bits());
        q(w,H+0x58L,0);q(w,H+0x60L,T);q(w,H+0x20L,original.r13Bits());
        q(w,H-8L,I+0xB2EFA1L);q(w,H-8L,I+0xB2EFB2L);q(w,H-8L,I+0xB2EFC0L);
        q(w,H-8L,I+0xB2EFD7L);q(w,H-8L,I+0xB2EFE8L);
        q(w,F,fresh.rbxBits());q(w,F-0x10L,fresh.rbpBits());q(w,F+8L,fresh.rsiBits());q(w,F+0x10L,fresh.rdiBits());
        q(w,F-0x28L,fresh.r12Bits());q(w,F-0x30L,fresh.r13Bits());q(w,F-0x18L,fresh.r14Bits());q(w,F-0x20L,fresh.r15Bits());
        q(w,TEMP,ALLOC);d(w,TEMP+0xCL,1);d(w,TEMP+8L,1);d(w,D+0xCL,0);
        q(w,C,I+0xB2EE93L);q(w,C-8L,fresh.rbpBits());q(w,C-0x10L,fresh.r14Bits());q(w,C-0x18L,fresh.r15Bits());
        q(w,H-8L,I+0xB2EF09L);return w;
    }
    private static void q(List<Write> w,long address,long value) { w.add(new Write(address,8,value)); }
    private static void d(List<Write> w,long address,int value) { w.add(new Write(address,4,Integer.toUnsignedLong(value))); }

    private static Ram ram() {
        Ram m=new Ram();m.poke(S,RET);
        header(m,D,DB,7,1,A);header(m,T,TB,9,2,B);
        header(m,ND,NDB,17,5,A2);header(m,NT,NTB,19,6,A2);
        m.poke(A2,TAB2);m.poke(TAB2+0x10L,FREE2);
        m.poke(L+8L,ALLOC_TARGET);m.poke(L+0x10L,FREE_TARGET);
        m.poke32(I+0x49F64F0L,0x3FC00000);return m;
    }
    private static void header(Ram m,long address,long pointer,int capacity,int count,long allocator) {
        m.poke(address,pointer);m.poke32(address+8L,capacity);m.poke32(address+0xCL,count);m.poke(address+0x10L,allocator);
    }
    private static Bits128 x(long tag) { return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag); }
    private static VolatileBits v(long tag) {
        return new VolatileBits(0xA000000000000000L|tag|1L,0xB000000000000000L|tag|2L,0xC000000000000000L|tag|3L,
                0xD000000000000000L|tag|8L,0xE000000000000000L|tag|9L,0xF000000000000000L|tag|10L,
                0x9000000000000000L|tag|11L,x(tag+0x10L),x(tag+0x20L),x(tag+0x30L),x(tag+0x40L),x(tag+0x50L),x(tag+0x60L));
    }
    private static VolatileBits state(VolatileBits v,long rax,long rcx,long rdx,long r8) {
        return new VolatileBits(rax,rcx,rdx,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits zeroX0(VolatileBits v) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                new Bits128(0,0),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits n0() {
        return new NonvolatileBits(0xB100000000000001L,0xB200000000000002L,0xB300000000000003L,0xB400000000000004L,
                0xD000000100000005L,0xB600000000000006L,0xB700000000000007L,0xB800000000000008L,x(0xB9L));
    }
    private static NonvolatileBits n1() {
        return new NonvolatileBits(ND,0xE200000000000002L,0xE300000000000003L,NT,0xF000000100000005L,
                0xE600000000000006L,0xE700000000000007L,0xE800000000000008L,n0().xmm6());
    }
    private record BudgetEvent(long site,long cursor,long end) { }
    private record Write(long address,int width,long value) { }

    /** Plain byte RAM. Reads have no mutation or control-flow effects except missing-byte rejection. */
    private static final class Ram implements Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Long> qReads=new ArrayList<>(),dReads=new ArrayList<>();
        private final List<Write> writes=new ArrayList<>();
        void poke(long address,long value) { for(int j=0;j<8;j++)bytes.put(address+j,(int)(value>>>(j*8))&255); }
        void poke32(long address,int value) { for(int j=0;j<4;j++)bytes.put(address+j,(value>>>(j*8))&255); }
        private int byteAt(long address) {
            Integer value=bytes.get(address);
            if(value==null)throw new UnsupportedOperationException("unheld242RAM "+Long.toHexString(address));
            return value;
        }
        long peek(long address) { long value=0;for(int j=0;j<8;j++)value|=(long)byteAt(address+j)<<(j*8);return value; }
        int peek32(long address) { int value=0;for(int j=0;j<4;j++)value|=byteAt(address+j)<<(j*8);return value; }
        @Override public long readQword(long address) { qReads.add(address);return peek(address); }
        @Override public int readDword(long address) { dReads.add(address);return peek32(address); }
        @Override public int readUnsignedByte(long address) { return byteAt(address); }
        @Override public void writeQword(long address,long value) { writes.add(new Write(address,8,value));poke(address,value); }
        @Override public void writeDword(long address,int value) { writes.add(new Write(address,4,Integer.toUnsignedLong(value)));poke32(address,value); }
        @Override public void writeByte(long address,int value) { writes.add(new Write(address,1,value&255));bytes.put(address,value&255); }
        @Override public Bits128 read128(long address) { return new Bits128(readQword(address),readQword(address+8L)); }
        @Override public void write128(long address,Bits128 value) { writeQword(address,value.lowBits());writeQword(address+8L,value.highBits()); }
        @Override public int lockedXaddDword(long address,int value) { throw new AssertionError("unexpected242atomic"); }
    }
    private static void eq(long actual,long expected) {
        checks++;if(actual!=expected)throw new AssertionError("check="+checks+" actual="+Long.toHexString(actual)+" expected="+Long.toHexString(expected));
    }
    private static void eq(Object actual,Object expected) {
        checks++;if(!Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);
    }
    private static void check(boolean condition) { checks++;if(!condition)throw new AssertionError("check="+checks); }
}
