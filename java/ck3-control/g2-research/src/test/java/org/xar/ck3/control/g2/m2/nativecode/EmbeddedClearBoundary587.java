package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Fixed owner source oracle for the new composition, not a target-derived simulator. */
public final class EmbeddedClearBoundary587 {
    private EmbeddedClearBoundary587() { }
    private static final long I=0x140000000L,E=0x8000L,D=0x10000L,S=0x20000L;
    private static final Bits128 X0=new Bits128(0x101,0x102),X1=new Bits128(0x201,0x202),
        X2=new Bits128(0x301,0x302),X3=new Bits128(0x401,0x402),X4=new Bits128(0x501,0x502),
        X5=new Bits128(0x601,0x602),X6=new Bits128(0x701,0x702),SRC=new Bits128(0x12345678,0x87654321);
    private static final NonvolatileBits N=new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,X6);
    private static final long RET=0x7172737475767778L;
    private static VolatileBits v(long a,long c,long d,long r8,Bits128 x0) {
        return new VolatileBits(a,c,d,r8,0x55,0x66,0x77,x0,X1,X2,X3,X4,X5);
    }
    private static final VolatileBits V=v(0x11,D,S,0x44,X0);
    private static NonvolatileBits n(long b,long p,long s,long d,long r14) {
        return new NonvolatileBits(b,p,s,d,0xB5,0xB6,r14,0xB8,X6);
    }
    private static void need(boolean value,String text) { if(!value) throw new AssertionError(text); }
    private static GovernmentCrtBoundary185Api.Entry entry(VolatileBits bits) {
        return new GovernmentCrtBoundary185Api.Entry(I,E,bits,N);
    }
    private static FullCopy437Api.CallResult returned(VolatileBits bits,NonvolatileBits saved,long rip,long sp,boolean df) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(bits,rip,sp,saved),df);
    }
    private static void checkFrame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean df,int len,long ret,long site,long target,GovernmentCrtBoundary185Api.TargetKind kind,
            long sp,VolatileBits expectedV,NonvolatileBits expectedN,boolean expectedDF,int expectedLen) {
        need(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,sp,expectedV,expectedN)),"complete call");
        need(child.equals(new GovernmentCrtBoundary185Api.Entry(I,sp-8,expectedV,expectedN)),"complete child entry");
        need(df==expectedDF && len==expectedLen && ret==I+site+expectedLen,"DF/length/continuation");
    }
    private static final class Ram implements FullCopy437Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();
        int touches;
        void seed(int w,long a,long value) { put(bytes,w,a,value); }
        static void put(Map<Long,Byte> map,int w,long a,long value) {
            for(int j=0;j<w;j++) map.put(a+j,(byte)(value>>>(8*j)));
        }
        long raw(int w,long a) {
            long value=0;
            for(int j=0;j<w;j++) {
                Byte b=bytes.get(a+j);if(b==null) throw new AssertionError("unseeded "+Long.toHexString(a+j));
                value|=Byte.toUnsignedLong(b)<<(j*8);
            }
            return value;
        }
        void store(int w,long a,long value) {
            touches++;
            if(!((a>=E-0x100 && a+w<=E+0x30)||(a>=D && a+w<=D+0x200))) throw new AssertionError("write bounds");
            seed(w,a,value);
        }
        public int readDword(long a) { touches++;return (int)raw(4,a); }
        public long readQword(long a) { touches++;return raw(8,a); }
        public Bits128 read128(long a) { touches++;return new Bits128(raw(8,a),raw(8,a+8)); }
        public void writeDword(long a,int x) { store(4,a,Integer.toUnsignedLong(x)); }
        public void writeQword(long a,long x) { store(8,a,x); }
        public void writeWord(long a,int x) { store(2,a,x&0xFFFFL); }
        public void writeByte(long a,int x) { store(1,a,x&0xFFL); }
        public void write128(long a,Bits128 x) { store(8,a,x.lowBits());store(8,a+8,x.highBits()); }
        public int readUnsignedByte(long a) { throw new UnsupportedOperationException(); }
        public int readUnsignedWord(long a) { throw new UnsupportedOperationException(); }
        public int lockedXaddDword(long a,int x) { throw new UnsupportedOperationException(); }
        public void write128NonTemporal(long a,Bits128 x) { throw new UnsupportedOperationException(); }
        public FullCopy437Api.Bits256 read256(long a) { throw new UnsupportedOperationException(); }
        public void write256(long a,FullCopy437Api.Bits256 x) { throw new UnsupportedOperationException(); }
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x) { throw new UnsupportedOperationException(); }
        public void sfence() { throw new UnsupportedOperationException(); }
    }
    private static VolatileBits post() {
        return new VolatileBits(0x9001,0x9002,0x9003,0x9004,0x9005,0x9006,0x9007,
            new Bits128(0x9101,0x9102),new Bits128(0x9201,0x9202),new Bits128(0x9301,0x9302),
            new Bits128(0x9401,0x9402),new Bits128(0x9501,0x9502),new Bits128(0x9601,0x9602));
    }
    private static void nonpositive(int kind) {
        Ram ram=new Ram();
        long receiver=kind==1?E+4:kind==2?E-0xC:D;
        long saved=kind==1?0x11223344FFFFFFFEL:N.rsiBits();
        NonvolatileBits savedN=new NonvolatileBits(N.rbxBits(),N.rbpBits(),saved,N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
        VolatileBits bits=v(0x11,receiver,S,0x44,X0);
        long beforeRIP=kind==2?0xAABBCCDD80000001L:RET;
        long afterRIP=kind==2?0xAABBCCDD00000000L:RET;
        ram.seed(8,E,beforeRIP);
        if(kind==0) ram.seed(4,D+0xC,0);
        Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        Ram.put(expected,8,E+0x10,saved);Ram.put(expected,8,E-8,N.rdiBits());
        Ram.put(expected,4,receiver+0xC,0);
        boolean df=kind!=2;
        var input=new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,E,bits,savedN),df,
            (h,g)->{throw new AssertionError("nonpositive no loop");});
        var actual=EmbeddedClearFullState889780.execute(input,ram,f->{throw new AssertionError("nonpositive no call");});
        need(actual.equals(returned(bits,savedN,afterRIP,E+8,df)),"full nonpositive NR: snapshot RSI / freshRET");
        need(ram.bytes.equals(expected),"complete nonpositive ownedRAM");
        if(kind==1) need(actual.normalReturn().nonvolatileBits().rsiBits()==0x11223344FFFFFFFEL && ram.raw(8,E+0x10)==0x1122334400000000L,"restoreRSI precedesaliasclear");
    }
    private static void positive() {
        Ram ram=new Ram();ram.seed(8,E,RET);ram.seed(4,D+0xC,1);ram.seed(8,D,0x30000);
        ram.seed(8,0x30000,0x40000);ram.seed(8,0x40000,0xABCDEF);
        Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        long[][] cells={{8,E+0x10,0xB3},{8,E-8,0xB4},{8,E+8,0xB1},{8,E-0x30,I+0x8897AA},{4,D+0xC,0}};
        for(long[] c:cells) Ram.put(expected,(int)c[0],c[1],c[2]);
        int[] calls={0},steps={0};
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            need(h==0x8897A0 && g==0x30000 && calls[0]==0,"original source header/guard");steps[0]++;
        };
        var input=new FullCopy437Api.Input(entry(V),true,budget);
        var actual=EmbeddedClearFullState889780.execute(input,ram,f->{
            need(calls[0]++==0 && steps[0]==1,"one actual call afterbudget");
            NonvolatileBits offeredN=new NonvolatileBits(0x30000,0xB2,D,1,0xB5,0xB6,0xB7,0xB8,X6);
            checkFrame(f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits(),
                0x8897A8,0xABCDEF,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,E-0x28,
                v(0x40000,0x30000,0,0x44,X0),offeredN,true,2);
            need(ram.raw(8,E-0x30)==f.returnRipBits(),"actual two-byte CALL push");
            return returned(post(),offeredN,f.returnRipBits(),f.call().rspBits(),false);
        });
        need(actual.equals(returned(post(),N,RET,E+8,false)),"full positive callbackpost V/XMM/DF andfreshN");
        need(calls[0]==1 && steps[0]==1 && ram.bytes.equals(expected),"complete positive ownedRAM");
    }
    private static void beforeMemoryBudget() {
        Ram ram=new Ram();ram.seed(8,E,RET);ram.seed(4,D+0xC,1);ram.seed(8,D,0x30000);
        var marker=new UnsupportedOperationException("sourcebudget587");int[] steps={0};
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            need(h==0x8897A0 && g==0x30000,"budget before first unseeded Q[RBX]");steps[0]++;throw marker;
        };
        try { EmbeddedClearFullState889780.execute(new FullCopy437Api.Input(entry(V),true,budget),ram,f->{throw new AssertionError("no call");});throw new AssertionError("missing budget"); }
        catch(UnsupportedOperationException actual) { need(actual==marker && steps[0]==1,"same original marker"); }
    }
    public static int verify() { nonpositive(0);nonpositive(1);nonpositive(2);positive();beforeMemoryBudget();return 5; }
    public static void main(String[] args) { System.out.println(verify()); }
}
