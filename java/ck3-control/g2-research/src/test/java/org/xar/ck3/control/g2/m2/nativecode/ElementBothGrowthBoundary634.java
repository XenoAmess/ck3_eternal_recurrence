package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;

/** New same-instance scalar software composition; foreign COPY/allocator effects remain controlled. */
public final class ElementBothGrowthBoundary634 {
    private ElementBothGrowthBoundary634() { }
    private static final long IMAGE=0x140000000L;
    private static final long D=0x8000000000001100L,S=0xf000000000002200L;
    private static final long B16=0xc000000000003300L,N16=0x9000000000004400L;
    private static final long B4=0xb000000000006600L,ALT4=0xb000000000007700L,N4=0xa000000000005500L;
    private static final long A16=IMAGE+0x54de260L,A4=IMAGE+0x54de268L,ALT_ALLOC16=0x9800000000008800L;
    private static final long V16=0x7100L,V4=0x7200L,ALT_V16=0x7300L;
    private static final long T16A=0x8111L,T16F=0x8122L,T16ALT=0x8133L,T4A=0x8211L,T4F=0x8222L;
    private static final long W0L=0x0123456789abcdefL,W0H=0xfedcba9876543210L;
    private static final long W1L=0x8000000000000001L,W1H=0x7ffffffffffffffeL;
    private static final int P0=0x11223344,P1=0x89abcdef,P2=0x76543210;
    private static final int KIND=0x88776655,TAIL=0x10203040,CHANGED_TAIL=0x55667788;
    private static final int FLAG=0x5a,CHANGED_FLAG=0xa5;
    private record E(String kind,long a,long b,long c,long d,long e) { }
    private static E e(String k,long a,long b,long c,long d,long f) { return new E(k,a,b,c,d,f); }
    private static void add(List<E> x,String k,long a,long b) { x.add(e(k,a,b,0,0,0)); }
    private static void word(List<E> x,String k,long a,long l,long h) { x.add(e(k,a,l,h,0,0)); }
    private static final class Marker extends RuntimeException {
        private static final long serialVersionUID=1L;
    }
    private static final class Ram implements Range8c194Inputs.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<E> events=new ArrayList<>();
        private void seed(long a,int width,long value) {
            for(int i=0;i<width;i++)bytes.put(a+i,(byte)(value>>>(i*8)));
        }
        private long peek(long a,int width) {
            long v=0;for(int i=0;i<width;i++)v|=(bytes.getOrDefault(a+i,(byte)0)&255L)<<(i*8);return v;
        }
        @Override public int read32(long a) { int v=(int)peek(a,4);add(events,"R32",a,v);return v; }
        @Override public long read64(long a) { long v=peek(a,8);add(events,"R64",a,v);return v; }
        @Override public int read8(long a) { int v=(int)peek(a,1);add(events,"R8",a,v);return v; }
        @Override public void write32(long a,int v) { add(events,"W32",a,v);seed(a,4,v); }
        @Override public void write64(long a,long v) { add(events,"W64",a,v);seed(a,8,v); }
        @Override public void write8(long a,int v) { add(events,"W8",a,v&255);seed(a,1,v); }
        @Override public Range8c194Inputs.Word16 read16(long a) {
            long l=peek(a,8),h=peek(a+8,8);word(events,"R16",a,l,h);return new Range8c194Inputs.Word16(l,h);
        }
        @Override public void write16(long a,Range8c194Inputs.Word16 v) {
            word(events,"W16",a,v.lowRaw64(),v.highRaw64());seed(a,8,v.lowRaw64());seed(a+8,8,v.highRaw64());
        }
    }
    private static Ram initial() {
        Ram r=new Ram();
        for(int i=0;i<0x50;i++)r.seed(D+i,1,0xcc);
        r.seed(S+8,4,KIND);r.seed(S+0x10,8,B16);r.seed(S+0x18,8,0x0000000200000007L);
        r.seed(S+0x28,8,B4);r.seed(S+0x30,8,0x0000000300000009L);
        r.seed(S+0x40,4,TAIL);r.seed(S+0x44,1,FLAG);
        r.seed(B16,8,W0L);r.seed(B16+8,8,W0H);r.seed(B16+16,8,W1L);r.seed(B16+24,8,W1H);
        r.seed(B4,4,P0);r.seed(B4+4,4,P1);r.seed(B4+8,4,P2);
        r.seed(ALT4,4,P0);r.seed(ALT4+4,4,P1);
        r.seed(A16,8,V16);r.seed(A4,8,V4);r.seed(ALT_ALLOC16,8,ALT_V16);
        r.seed(V16+8,8,T16A);r.seed(V16+16,8,T16F);r.seed(ALT_V16+16,8,T16ALT);
        r.seed(V4+8,8,T4A);r.seed(V4+16,8,T4F);
        return r;
    }
    private static final class Ports16 implements Range8c194Inputs.Calls {
        private final Ram ram;private final boolean alias;
        private Ports16(Ram ram,boolean alias) { this.ram=ram;this.alias=alias; }
        @Override public long virtual8(long t,long a,long bytes,long align,long end) {
            ram.events.add(e("A16",t,a,bytes,align,end));
            if(alias)ram.write64(D+0x20,ALT_ALLOC16);
            return N16;
        }
        @Override public void virtual16(long t,long a,long old,long align,long r9) {
            ram.events.add(e("F16",t,a,old,align,r9));
            if(alias) {
                ram.write64(S+0x28,ALT4);ram.write32(S+0x34,2);
                ram.write32(S+0x40,CHANGED_TAIL);ram.write8(S+0x44,CHANGED_FLAG);
            }
        }
        @Override public void direct8f8550(long a,long b,long c,long d) { throw new AssertionError("unexpected non-growth16"); }
    }
    private static final class Ports4 implements Copy4Add200Inputs.Calls {
        private final Ram ram;private final boolean alias,fail;private final Marker marker;
        private int copyCalls;
        private Ports4(Ram ram,boolean alias,boolean fail,Marker marker) { this.ram=ram;this.alias=alias;this.fail=fail;this.marker=marker; }
        @Override public long virtual8(long t,long a,long bytes,long align,long end) {
            ram.events.add(e("A4",t,a,bytes,align,end));return N4;
        }
        @Override public void copy4226860(long d,long s,long bytes) {
            ram.events.add(e("C4",d,s,bytes,0,0));
            int n=alias?8:12;long begin=alias?ALT4:B4;
            if(copyCalls==0) {
                if(d!=N4||s!=0||bytes!=0)throw new AssertionError("first controlled COPY arguments");
            } else if(copyCalls==1) {
                if(d!=N4||s!=begin||bytes!=n)throw new AssertionError("positive controlled COPY arguments");
                // Finite foreign result, NOT a copy implementation or reads of the source to derive outputs.
                ram.write32(N4,P0);
                if(fail)throw marker;
                ram.write32(N4+4,P1);if(!alias)ram.write32(N4+8,P2);
            } else if(copyCalls==2) {
                if(d!=N4+n||s!=0||bytes!=0)throw new AssertionError("tail controlled COPY arguments");
            } else throw new AssertionError("extra COPY");
            copyCalls++;
        }
        @Override public void virtual16(long t,long a,long old,long align) { ram.events.add(e("F4",t,a,old,align,0)); }
        @Override public void range9d0950(long a,long b,long c,long d) { throw new AssertionError("unexpected non-growth4"); }
    }
    /** Literal finite expectation, frozen from source; no target call or general lower algorithm constructs it. */
    private static List<E> expected(boolean alias,boolean fail) {
        List<E> x=new ArrayList<>();
        add(x,"W64",D,IMAGE+0x45648a0L);add(x,"R32",S+8,KIND);add(x,"W32",D+8,KIND);
        add(x,"W64",D+0x18,0);add(x,"W64",D+0x20,0);add(x,"W64",D+0x10,0);
        add(x,"W64",D+0x18,0);add(x,"W64",D+0x20,A16);add(x,"R32",S+0x1c,2);add(x,"R64",S+0x10,B16);
        add(x,"R32",D+0x1c,0);add(x,"R32",D+0x18,0);add(x,"R64",D+0x20,A16);
        add(x,"R64",A16,V16);add(x,"R64",V16+8,T16A);x.add(e("A16",T16A,A16,32,8,B16+32));
        if(alias)add(x,"W64",D+0x20,ALT_ALLOC16);
        add(x,"R64",D+0x10,0);
        word(x,"R16",B16,W0L,W0H);word(x,"W16",N16,W0L,W0H);
        word(x,"R16",B16+16,W1L,W1H);word(x,"W16",N16+16,W1L,W1H);
        add(x,"R64",D+0x10,0);add(x,"R32",D+0x1c,0);
        long a=alias?ALT_ALLOC16:A16,v=alias?ALT_V16:V16,t=alias?T16ALT:T16F;
        add(x,"R64",D+0x20,a);add(x,"R64",a,v);add(x,"R64",v+16,t);x.add(e("F16",t,a,0,8,0));
        if(alias) {
            add(x,"W64",S+0x28,ALT4);add(x,"W32",S+0x34,2);
            add(x,"W32",S+0x40,CHANGED_TAIL);add(x,"W8",S+0x44,CHANGED_FLAG);
        }
        add(x,"W64",D+0x10,N16);add(x,"W32",D+0x18,2);add(x,"W32",D+0x1c,2);
        add(x,"W64",D+0x30,0);add(x,"W64",D+0x38,0);add(x,"W64",D+0x28,0);
        add(x,"W64",D+0x30,0);add(x,"W64",D+0x38,A4);
        long begin=alias?ALT4:B4;int n=alias?2:3;
        add(x,"R64",S+0x28,begin);add(x,"R32",S+0x34,n);
        add(x,"R32",D+0x34,0);add(x,"R32",D+0x30,0);add(x,"R64",D+0x38,A4);
        add(x,"R64",A4,V4);add(x,"R64",V4+8,T4A);x.add(e("A4",T4A,A4,n*4,4,begin+n*4));
        add(x,"R64",D+0x28,0);x.add(e("C4",N4,0,0,0,0));x.add(e("C4",N4,begin,n*4,0,0));
        add(x,"W32",N4,P0);
        if(fail)return x;
        add(x,"W32",N4+4,P1);if(!alias)add(x,"W32",N4+8,P2);
        add(x,"R64",D+0x28,0);add(x,"R32",D+0x34,0);x.add(e("C4",N4+n*4,0,0,0,0));
        add(x,"R64",D+0x38,A4);add(x,"R64",D+0x28,0);add(x,"R64",A4,V4);add(x,"R64",V4+16,T4F);
        x.add(e("F4",T4F,A4,0,4,0));add(x,"W64",D+0x28,N4);add(x,"W32",D+0x30,n);add(x,"W32",D+0x34,n);
        int tail=alias?CHANGED_TAIL:TAIL,flag=alias?CHANGED_FLAG:FLAG;
        add(x,"R32",S+0x40,tail);add(x,"W32",D+0x40,tail);add(x,"R8",S+0x44,flag);add(x,"W8",D+0x44,flag);
        return x;
    }
    private static void one(boolean alias,boolean fail) {
        Ram r=initial(),wanted=initial();List<E> expect=expected(alias,fail);
        for(E row:expect) {
            switch(row.kind()) {
                case "W8" -> wanted.seed(row.a(),1,row.b());
                case "W32" -> wanted.seed(row.a(),4,row.b());
                case "W64" -> wanted.seed(row.a(),8,row.b());
                case "W16" -> { wanted.seed(row.a(),8,row.b());wanted.seed(row.a()+8,8,row.c()); }
                default -> { }
            }
        }
        Marker marker=new Marker();boolean caught=false;
        try {
            long result=Element172BothGrowth634.assign(new Element172Inputs.Input(D,S,IMAGE),r,new Ports16(r,alias),new Ports4(r,alias,fail,marker));
            if(fail)throw new AssertionError("missing throw");
            if(result!=D)throw new AssertionError("full raw return");
        } catch(Marker ex) { if(!fail||ex!=marker)throw new AssertionError("foreign exception identity");caught=true; }
        if(caught!=fail)throw new AssertionError("throw outcome");
        if(!r.events.equals(expect)) {
            int i=0;while(i<r.events.size()&&i<expect.size()&&r.events.get(i).equals(expect.get(i)))i++;
            throw new AssertionError("634 event "+i+" actual="+(i<r.events.size()?r.events.get(i):"END")+" expected="+(i<expect.size()?expect.get(i):"END")+" lengths="+r.events.size()+"/"+expect.size());
        }
        if(!r.bytes.equals(wanted.bytes))throw new AssertionError("complete shared byte RAM including untouched padding");
    }
    public static int verify() { one(false,false);one(true,false);one(false,true);return 3; }
    public static void main(String[] args) { System.out.println(verify()); }
}
