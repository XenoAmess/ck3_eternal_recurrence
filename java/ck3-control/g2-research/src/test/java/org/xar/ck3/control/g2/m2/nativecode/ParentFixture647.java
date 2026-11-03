package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
/** Mechanical owned RAM, event recording and raw input banks only; no target algorithm or oracle. */
public final class ParentFixture647 {
    private ParentFixture647() { }
    public static final long IMAGE=0x140000000L,SP=0x70001008L,RIP=IMAGE+0x123456;
    public record Event(String kind,long address,long a,long b,long c,long d) { }
    public static Event e(String k,long p,long v) {return new Event(k,p,v,0,0,0);}
    public static Event e128(String k,long p,Bits128 v) {return new Event(k,p,v.lowBits(),v.highBits(),0,0);}
    public static Event e256(String k,long p,FullCopy437Api.Bits256 v) {return new Event(k,p,v.low().lowBits(),v.low().highBits(),v.high().lowBits(),v.high().highBits());}
    public static Bits128 x(long a) {return new Bits128(a,~a);}
    public static VolatileBits initialV(long begin,long end) {return new VolatileBits(0x101,begin,end,0x104,0x105,0x106,0x107,x(0x108),x(0x109),x(0x10a),x(0x10b),x(0x10c),x(0x10d));}
    public static NonvolatileBits initialN() {return new NonvolatileBits(0x201,0x202,0x203,0x204,0x205,0x206,0x207,0x208,x(0x209));}
    public static QueueFp604Api.Input input(long begin,long end,boolean df,QueueFp604Api.Mxcsr fp,GovernmentCrtBoundary185Api.LoopBudget budget) {return new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,initialV(begin,end),initialN()),df,budget),fp);}
    public static void check(boolean ok,String why) {if(!ok)throw new AssertionError(why);}
    public static final class Ram implements ParentKnown647Api.Memory {
        public final Map<Long,Byte> bytes=new HashMap<>();public final List<Event> events=new ArrayList<>();
        public long throwBudgetPc=-1;
        public RuntimeException budgetFailure=new UnsupportedOperationException("fixture budget stop");
        public void seed(long p,int w,long value) {for(int j=0;j<w;j++)bytes.put(p+j,(byte)(value>>>(8*j)));}
        public long peek(long p,int w) {long v=0;for(int j=0;j<w;j++)v|=(bytes.getOrDefault(p+j,(byte)0)&255L)<<(8*j);return v;}
        public void seed128(long p,Bits128 v) {seed(p,8,v.lowBits());seed(p+8,8,v.highBits());}
        public void seed256(long p,FullCopy437Api.Bits256 v) {seed128(p,v.low());seed128(p+16,v.high());}
        public void step(long pc,long cursor) {events.add(e("BUDGET",pc,cursor));if(pc==throwBudgetPc)throw budgetFailure;}
        @Override public int readDword(long p) {int v=(int)peek(p,4);events.add(e("R32",p,v));return v;}
        @Override public long readQword(long p) {long v=peek(p,8);events.add(e("R64",p,v));return v;}
        @Override public Bits128 read128(long p) {Bits128 v=new Bits128(peek(p,8),peek(p+8,8));events.add(e128("R128",p,v));return v;}
        @Override public FullCopy437Api.Bits256 read256(long p) {var v=new FullCopy437Api.Bits256(new Bits128(peek(p,8),peek(p+8,8)),new Bits128(peek(p+16,8),peek(p+24,8)));events.add(e256("R256",p,v));return v;}
        @Override public void writeDword(long p,int v) {events.add(e("W32",p,v));seed(p,4,v);}
        @Override public void writeQword(long p,long v) {events.add(e("W64",p,v));seed(p,8,v);}
        @Override public void write128(long p,Bits128 v) {events.add(e128("W128",p,v));seed(p,8,v.lowBits());seed(p+8,8,v.highBits());}
        @Override public void write256(long p,FullCopy437Api.Bits256 v) {events.add(e256("W256",p,v));seed(p,8,v.low().lowBits());seed(p+8,8,v.low().highBits());seed(p+16,8,v.high().lowBits());seed(p+24,8,v.high().highBits());}
        @Override public int readUnsignedByte(long p) {int v=(int)peek(p,1);events.add(e("R8",p,v));return v;}
        @Override public int readUnsignedWord(long p) {int v=(int)peek(p,2);events.add(e("R16",p,v));return v;}
        @Override public void writeByte(long p,int v) {events.add(e("W8",p,v&255));seed(p,1,v);}
        @Override public void writeWord(long p,int v) {events.add(e("W16",p,v&65535));seed(p,2,v);}
        @Override public int lockedXaddDword(long p,int v) {int old=(int)peek(p,4),sum=old+v;events.add(new Event("LOCK_XADD32",p,v,old,sum,0));seed(p,4,sum);return old;}
        @Override public void write128NonTemporal(long p,Bits128 v) {events.add(e128("W128NT",p,v));seed128(p,v);}
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 v) {events.add(e256("W256NT",p,v));seed256(p,v);}
        @Override public void sfence() {events.add(e("SFENCE",0,0));}
    }
}
