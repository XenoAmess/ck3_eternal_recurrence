package org.xar.ck3.research.m0.operand363;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;
import org.xar.ck3.research.m1.GovernmentThreadNotify181;
import org.xar.ck3.research.m1.GovernmentThreadWait179;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtNative192Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New literal owned-memory witness, not an imported routine or operating-system test. */
public final class CrtOperandOrder363Manual {
    private static final long I=0x140000000L, CTX=0x700008L, OTHER=0x710008L;
    private static final long ACQUIRE=0x1111222233334444L, TAIL=0x5555666677778888L;
    private static final long CUSTOM=0x9999AAAABBBBCCCCL, BEFORE=0xABCDEF0123456789L;
    private static final VolatileBits V=bits(0x110000001L), FIRST=bits(0x220000002L);
    private static final VolatileBits SECOND=bits(0x330000003L), FINAL=bits(0x440000004L);
    private static final NonvolatileBits N=new NonvolatileBits(0xA00000001L,0xA00000002L,
            0xA00000003L,0xA00000004L,0xFEDCBA9876543210L,0xA00000006L,
            0xA00000007L,0xA00000008L,new Bits128(0xA00000009L,0xA0000000AL));
    private static int checks;
    private CrtOperandOrder363Manual() { }
    private static void check(boolean value,String label) {
        checks++;if(!value)throw new AssertionError(label);
    }
    private static void eq(long a,long b,String label) {check(a==b,label+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(b));}
    private static void same(Object a,Object b,String label) {check(a==b,label);}
    private static void equal(Object a,Object b,String label) {check(a.equals(b),label);}
    private static VolatileBits bits(long n) {
        return new VolatileBits(n,n+1,n+2,n+3,n+4,n+5,n+6,
                new Bits128(n+7,n+8),new Bits128(n+9,n+10),new Bits128(n+11,n+12),
                new Bits128(n+13,n+14),new Bits128(n+15,n+16),new Bits128(n+17,n+18));
    }
    private static VolatileBits args(VolatileBits v,long rax,long rcx,long rdx,long r8) {
        return new VolatileBits(rax,rcx,rdx,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits rbx(long value) {
        return new NonvolatileBits(value,N.rbpBits(),N.rsiBits(),N.rdiBits(),N.r12Bits(),
                N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory,GovernmentSharedManager167Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();
        final List<String> events=new ArrayList<>();
        long failAddress=Long.MIN_VALUE, denyAddress=Long.MIN_VALUE;
        final RuntimeException failure=new IllegalStateException("owned operand unavailable");
        void seed(long a,long v) {for(int n=0;n<8;n++)bytes.put(a+n,(byte)(v>>>(8*n)));}
        long peek(long a) {
            long v=0;for(int n=0;n<8;n++) {
                Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unseeded qword "+Long.toHexString(a+n));
                v|=(b.longValue()&255)<<(8*n);
            }return v;
        }
        @Override public long readQword(long a) {
            events.add("R:"+Long.toHexString(a));
            if(a==failAddress)throw failure;
            if(a==denyAddress)throw new AssertionError("extra read after captured tail result");
            return peek(a);
        }
        @Override public void writeQword(long a,long v) {
            events.add("W:"+Long.toHexString(a)+":"+Long.toHexString(v));seed(a,v);
        }
        @Override public int readDword(long a) {
            int value=0;for(int n=0;n<4;n++)value|=readUnsignedByte(a+n)<<(8*n);return value;
        }
        @Override public int readUnsignedByte(long a) {
            Byte b=bytes.get(a);if(b==null)throw new AssertionError("unseeded byte");return b&255;
        }
        @Override public void writeDword(long a,int v) {for(int n=0;n<4;n++)bytes.put(a+n,(byte)(v>>>(8*n)));}
        @Override public void writeByte(long a,int v) {bytes.put(a,(byte)v);}
        @Override public int lockedXaddDword(long a,int v) {throw new UnsupportedOperationException("not used");}
        @Override public int lockedXaddByte(long a,int v) {throw new UnsupportedOperationException("not used");}
        @Override public Bits128 read128(long a) {throw new UnsupportedOperationException("not used");}
        @Override public void write128(long a,Bits128 v) {throw new UnsupportedOperationException("not used");}
    }
    private abstract static class Port implements Calls {
        @Override public VolatileBits invoke(Call c) {throw new AssertionError("unexpected Call "+c);}
        @Override public NormalReturn tail(Tail t) {throw new AssertionError("unexpected Tail "+t);}
        @Override public long readGsQword58() {return 0x123456789ABCDEFL;}
    }
    private static void frame(Call c,long site,long target,long sp,VolatileBits v,NonvolatileBits n) {
        eq(c.callSiteRva(),site,"site");same(c.kind(),TargetKind.INDIRECT_ABSOLUTE,"indirect Call kind");
        eq(c.targetBits(),target,"fresh target");eq(c.rspBits(),sp,"actual preCALL SP");
        equal(c.volatileBits(),v,"full represented V");equal(c.nonvolatileBits(),n,"full represented N");
    }
    private static void tailFrame(Tail t,long site,long target,long sp,VolatileBits v) {
        eq(t.jumpSiteRva(),site,"tail site");same(t.kind(),TargetKind.INDIRECT_ABSOLUTE,"tail kind");
        eq(t.targetBits(),target,"fresh tail target");eq(t.entry().imageBaseBits(),I,"actual entry image");
        eq(t.entry().rspBits(),sp,"actual tail SP");equal(t.entry().volatileBits(),v,"tail full V");
        equal(t.entry().nonvolatileBits(),N,"tail full N restored");
    }
    private static Call waitCall(long entry) {
        return new Call(0x4223AA9L,TargetKind.DIRECT_RVA,0x4223B30L,entry+8,V,N);
    }
    private static Ram waitRam(long entry) {
        Ram m=new Ram();m.seed(entry,I+0x4223AAEL);m.seed(entry-0x30,BEFORE);
        m.seed(I+0x5C5CB40L,0);m.seed(I+0x5C5CB10L,CTX);
        m.seed(I+0x43DA4F0L,ACQUIRE);m.seed(I+0x43DA500L,TAIL);return m;
    }
    private static void waitAlias(boolean baseline,boolean mutate) {
        long e=I+0x43DA548L,p=e-0x28,slot=e-0x30;
        eq(e&15,8,"aligned callee");eq(p&15,0,"aligned internal CALL");eq((e+8)&15,0,"aligned outer CALL");
        eq(slot,I+0x43DA518L,"alias exactly second IAT operand");
        Ram m=waitRam(e);long expectedTarget=baseline?I+0x4223B80L:mutate?CUSTOM:I+0x4223B6EL;
        int[] count={0};NormalReturn[] actual={null};
        Calls f=new Port() {
            @Override public VolatileBits invoke(Call c) {
                count[0]++;
                if(count[0]==1) {
                    frame(c,0x4223B68L,ACQUIRE,p,args(V,0,I+0x5C5CB18L,V.rdxBits(),V.r8Bits()),rbx(Integer.toUnsignedLong((int)V.rcxBits())));
                    eq(m.peek(slot),I+0x4223B6EL,"first CALL already wrote B6E into later operand slot");
                    if(mutate)m.writeQword(slot,CUSTOM);
                    return FIRST;
                }
                eq(count[0],2,"only second CALL");
                frame(c,0x4223B7AL,expectedTarget,p,args(FIRST,FIRST.raxBits(),CTX,Integer.toUnsignedLong((int)V.rcxBits()),0),rbx(Integer.toUnsignedLong((int)V.rcxBits())));
                eq(m.peek(slot),I+0x4223B80L,"second push occurs before imported callback");
                return SECOND;
            }
            @Override public NormalReturn tail(Tail t) {
                tailFrame(t,0x4223B8CL,TAIL,e,args(SECOND,SECOND.raxBits(),I+0x5C5CB18L,SECOND.rdxBits(),SECOND.r8Bits()));
                actual[0]=new NormalReturn(FINAL,m.readQword(e),e+8,N);m.denyAddress=e;return actual[0];
            }
        };
        VolatileBits returned=GovernmentCrtNative192Calls.bind(I,m,f).invoke(waitCall(e));
        same(returned,FINAL,"actual tail V identity");eq(count[0],2,"two CALLs");
        eq(m.peek(e-8),N.rbxBits(),"saved original RBX");check(actual[0]!=null,"actual tail captured");
        int read=m.events.indexOf("R:"+Long.toHexString(slot));
        int write=m.events.indexOf("W:"+Long.toHexString(slot)+":"+Long.toHexString(I+0x4223B80L));
        check(read>=0&&write>=0,"second operand read and push observed");
        check(baseline?write<read:read<write,"literal memory effect order");
    }
    private static void waitFailure(boolean baseline,boolean second) {
        long e=0x730008L,p=e-0x28,slot=e-0x30;Ram m=waitRam(e);
        m.seed(I+0x43DA518L,CUSTOM);m.failAddress=I+(second?0x43DA518L:0x43DA4F0L);
        int[] calls={0};Calls f=new Port() {
            @Override public VolatileBits invoke(Call c) {
                calls[0]++;frame(c,0x4223B68L,ACQUIRE,p,args(V,0,I+0x5C5CB18L,V.rdxBits(),V.r8Bits()),rbx(Integer.toUnsignedLong((int)V.rcxBits())));
                return FIRST;
            }
        };
        try {GovernmentCrtNative192Calls.bind(I,m,f).invoke(waitCall(e));throw new AssertionError("missing operand failure");}
        catch(RuntimeException failure) {same(failure,m.failure,"failure identity");}
        eq(calls[0],second?1:0,"callback count before operand failure");
        eq(m.peek(slot),baseline?I+(second?0x4223B80L:0x4223B6EL):second?I+0x4223B6EL:BEFORE,"no new push before failing operand read");
        eq(m.peek(e-8),N.rbxBits(),"real earlier prologue write retained");
    }
    private static void notifyRoute(boolean fast) {
        long e=0x740008L,sp=e-0x28,ret=0x1234123412341234L;Ram m=new Ram();
        m.seed(e,ret);m.seed(e-0x30,BEFORE);m.seed(I+0x5C5CB48L,fast?9:0);
        m.seed(I+0x5C5CB10L,CTX);m.seed(I+0x43DA5B0L,ACQUIRE);
        m.seed(I+0x43DA4A8L,TAIL);m.seed(I+0x43DBBA8L,CUSTOM);
        NormalReturn[] result={null};int[] count={0};
        Calls f=new Port() {
            @Override public VolatileBits invoke(Call c) {
                count[0]++;frame(c,0x4223B15L,ACQUIRE,sp,args(V,0,CTX,V.rdxBits(),V.r8Bits()),N);
                eq(m.peek(e-0x30),I+0x4223B1BL,"Notify CALL push");
                m.writeQword(I+0x5C5CB10L,OTHER);return FIRST;
            }
            @Override public NormalReturn tail(Tail t) {
                tailFrame(t,fast?0x4223B07L:0x4223B26L,fast?CUSTOM:TAIL,e,
                        fast?args(V,9,I+0x5C5CB08L,V.rdxBits(),V.r8Bits()):args(FIRST,FIRST.raxBits(),OTHER,FIRST.rdxBits(),FIRST.r8Bits()));
                result[0]=new NormalReturn(FINAL,m.readQword(e),e+8,N);m.denyAddress=e;return result[0];
            }
        };
        Tail outer=new Tail(0x4223A7FL,TargetKind.DIRECT_RVA,0x4223AECL,new Entry(I,e,V,N));
        NormalReturn returned=GovernmentCrtNative192Calls.bind(I,m,f).tail(outer);
        same(returned,result[0],"Notify actual NR identity/no extra RET read");eq(count[0],fast?0:1,"Notify CALL count");
        eq(m.peek(e-0x30),fast?BEFORE:I+0x4223B1BL,"tail owns no push");
        if(!fast) {
            int read=m.events.indexOf("R:"+Long.toHexString(I+0x43DA5B0L));
            int write=m.events.indexOf("W:"+Long.toHexString(e-0x30)+":"+Long.toHexString(I+0x4223B1BL));
            check(read>=0&&read<write,"Notify operand-before-push");
        }
    }
    private static void notifyFailure() {
        long e=0x750008L;Ram m=new Ram();m.seed(e-0x30,BEFORE);
        m.seed(I+0x5C5CB48L,0);m.seed(I+0x5C5CB10L,CTX);m.failAddress=I+0x43DA5B0L;
        try {
            GovernmentCrtNative192Calls.bind(I,m,new Port() { }).tail(new Tail(0x4223A7FL,TargetKind.DIRECT_RVA,0x4223AECL,new Entry(I,e,V,N)));
            throw new AssertionError("missing Notify operand failure");
        }catch(RuntimeException failure) {same(failure,m.failure,"Notify failure identity");}
        eq(m.peek(e-0x30),BEFORE,"Notify read failure before new push");
    }
    private static void legacyAndForwarding() {
        long e=0x760008L;Ram m=waitRam(e);int[] wait={0};
        GovernmentThreadHeader178Api.Ports ports=new GovernmentThreadHeader178Api.Ports() {
            @Override public VolatileBits invokeIat(GovernmentThreadHeader178Api.IatCall c) {
                wait[0]++;
                if(c.callSiteRva()==0x4223B68L)eq(m.peek(e-0x30),I+0x4223B6EL,"legacy Wait first push precedes callback");
                else if(c.callSiteRva()==0x4223B7AL)eq(m.peek(e-0x30),I+0x4223B80L,"legacy Wait second push precedes callback");
                else {check(c.tailJump(),"legacy tail");eq(c.rspBits(),e,"legacy tail actualSP");}
                return FIRST;
            }
            @Override public VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall c) {throw new AssertionError("no direct opaque");}
            @Override public long readGsQword58() {throw new AssertionError("unused GS");}
        };
        GovernmentCallee164Api.NormalReturn wr=GovernmentThreadWait179.execute(new GovernmentCallee164Api.Entry(I,e,V,N),m,ports);
        eq(wait[0],3,"legacy three callbacks");eq(wr.returnRipBits(),I+0x4223AAEL,"legacy actualRET");equal(wr.nonvolatileBits(),N,"legacy N");
        Ram n=new Ram();n.seed(e,BEFORE);n.seed(I+0x5C5CB48L,0);n.seed(I+0x5C5CB10L,CTX);int[] nc={0};
        GovernmentThreadHeader178Api.Ports np=new GovernmentThreadHeader178Api.Ports() {
            @Override public VolatileBits invokeIat(GovernmentThreadHeader178Api.IatCall c) {
                nc[0]++;if(!c.tailJump())eq(n.peek(e-0x30),I+0x4223B1BL,"legacy Notify push precedes callback");return FIRST;
            }
            @Override public VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall c) {throw new AssertionError("unused");}
            @Override public long readGsQword58() {throw new AssertionError("unused");}
        };
        GovernmentCallee164Api.NormalReturn nr=GovernmentThreadNotify181.execute(new GovernmentCallee164Api.Entry(I,e,V,N),n,np);
        eq(nc[0],2,"legacy Notify callbacks");eq(nr.returnRipBits(),BEFORE,"legacy Notify actualRET");
        Ram untouched=new Ram();Call c=new Call(0x4223AA9L,TargetKind.INDIRECT_ABSOLUTE,0x4223B30L,e,V,N);
        Tail t=new Tail(0x4223A7FL,TargetKind.DIRECT_RVA,0x4223AEDL,new Entry(I,e,V,N));
        NormalReturn expected=new NormalReturn(FINAL,BEFORE,e+8,N);
        Calls f=new Port() {
            @Override public VolatileBits invoke(Call actual) {same(actual,c,"unknown Call object forward");return FIRST;}
            @Override public NormalReturn tail(Tail actual) {same(actual,t,"unknown Tail object forward");return expected;}
        };
        Calls bound=GovernmentCrtNative192Calls.bind(I,untouched,f);
        same(bound.invoke(c),FIRST,"unknown Call result identity");same(bound.tail(t),expected,"unknown Tail result identity");
        eq(bound.readGsQword58(),0x123456789ABCDEFL,"GS forward");check(untouched.events.isEmpty(),"unmatched routes never touch memory");
    }
    public static void main(String[] arguments) {
        check(arguments.length==1,"one literal mode");
        if(arguments[0].equals("baseline")) {
            waitAlias(true,false);waitFailure(true,false);
            System.out.println("PASS baseline_counter=2 checks="+checks+" old_B7A_target=B80 architectural_expected=B6E OS_claim=false");
        }else if(arguments[0].equals("selected")) {
            waitAlias(false,false);waitAlias(false,true);
            waitFailure(false,false);waitFailure(false,true);
            notifyRoute(false);notifyRoute(true);notifyFailure();
            legacyAndForwarding();
            System.out.println("PASS cases=4 checks="+checks+" represented185_only=true Game=false");
        }else throw new AssertionError("unknown mode");
    }
}
