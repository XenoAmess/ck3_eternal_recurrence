package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** New owner whole93/FP fixtures from original587 ASM and old complete source.
 * SOURCE-LITERAL-ORACLE645.json was frozen before this Test. The new645 wrapper body was not read.
 * All virtual destructor outcomes are complete owned offers; no callee/OS/FP-preservation defaults.
 * Expected events, full bytes and register banks are literal-source expectations, never target output. */
public final class EmbeddedClearBoundary645 {
    private EmbeddedClearBoundary645() { }
    private static final long I=0x140000000L,P=0x70003008L,PRE=P-0x28,CHILD=P-0x30;
    private static final long R=0x8000000000011000L,E=0xf000000000002200L,E1=E+0x48;
    private static final long T0=0x9000000000004000L,T1OLD=0xf000000000006000L,T1NEW=0x8000000000007000L;
    private static final long A0=0x800000000000aaaaL,A1=0xf00000000000bbbbL,OLD=0x900000000000ccccL,POISON=0x800000000000ddddL;
    private static final long OTHER=0x8000000000009900L,MARK=0x9990,RIP=I+0x123456;
    private static final QueueFp604Api.Mxcsr F0=new QueueFp604Api.Mxcsr(1,3),F1=new QueueFp604Api.Mxcsr(8,12),F2=new QueueFp604Api.Mxcsr(0x40,0xc0);
    private enum Mode { EMPTY_ZERO,EMPTY_NEGATIVE,POSITIVE,FIRST_STOP,SECOND_STOP,BAD_FIRST_RIP,BAD_SECOND_SP,BAD_SECOND_N,THROW_FIRST,THROW_SECOND,THROW_BUDGET_SECOND,RET_ALIAS,RSI_ALIAS }
    private record Event(String kind,long address,long value) { }
    private static void ev(List<Event> z,String k,long p,long v) {z.add(new Event(k,p,v));}
    private static void same(boolean ok,String why) {if(!ok)throw new AssertionError(why);}
    private static Bits128 x(long n) {return new Bits128(n,~n);}
    private static boolean positive(Mode m) {return m!=Mode.EMPTY_ZERO&&m!=Mode.EMPTY_NEGATIVE&&m!=Mode.RET_ALIAS&&m!=Mode.RSI_ALIAS;}
    private static long receiver(Mode m) {return m==Mode.RET_ALIAS?P-0xc:m==Mode.RSI_ALIAS?P+4:R;}
    private static int count(Mode m) {return positive(m)?2:m==Mode.EMPTY_ZERO?0:-1;}
    private static long initialRip(Mode m) {return m==Mode.RET_ALIAS?0xfedcba98ffffffffL:RIP;}
    private static long finalRip(Mode m) {return m==Mode.RET_ALIAS?0xfedcba9800000000L:RIP;}
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9) {
        return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));
    }
    private static VolatileBits initialV(Mode m) {return bank(0x1000,0x111,receiver(m),0x113,0x114,0x115);}
    private static VolatileBits offered(int j) {long b=0x2000+j*0x1000;return bank(b,b+1,b+2,b+3,b+4,b+5);}
    private static NonvolatileBits initialN(Mode m) {return new NonvolatileBits(0x201,0x202,m==Mode.RSI_ALIAS?0xaabbccddffffffffL:0x203,0x204,0x205,0x206,0x207,0x208,x(0x209));}
    private static VolatileBits callV(Mode m,int j) {
        var b=j==0?initialV(m):offered(1);return new VolatileBits(j==0?T0:T1NEW,j==0?E:E1,0,b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits(),b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());
    }
    private static NonvolatileBits callN(Mode m,int j) {var n=initialN(m);return new NonvolatileBits(j==0?E:E1,n.rbpBits(),receiver(m),2-j,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static GovernmentCrtBoundary185Api.Entry expectedChild(Mode m,int j) {return new GovernmentCrtBoundary185Api.Entry(I,CHILD,callV(m,j),callN(m,j));}
    private static void checkFrame(EmbeddedClearFp645Api.CallFrame f,Mode m,int j) {
        var o=f.original();var c=new GovernmentCrtBoundary185Api.Call(0x8897a8,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,j==0?A0:A1,PRE,callV(m,j),callN(m,j));
        same(o.call().equals(c),"independent complete virtual CALL "+j);
        same(o.childEntry().equals(expectedChild(m,j)),"independent complete virtual child "+j);
        same(o.directionFlagSet()==(j==0)&&f.preMxcsr()==(j==0?F0:F1),"actual loop DF/current partial FP same object "+j);
        same(o.instructionLength()==2&&o.returnRipBits()==I+0x8897aa,"actual2-byte CALL return metadata");
    }
    /** Owned byte RAM and recording only. Unexpected wide/atomic operations fail. */
    private static final class Ram implements FullCopy437Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events=new ArrayList<>();
        void seed(long p,int w,long v) {for(int j=0;j<w;j++)bytes.put(p+j,(byte)(v>>>(8*j)));}
        long peek(long p,int w) {long v=0;for(int j=0;j<w;j++)v|=(bytes.getOrDefault(p+j,(byte)0)&255L)<<(8*j);return v;}
        public int readDword(long p) {int v=(int)peek(p,4);ev(events,"R32",p,v);return v;}
        public long readQword(long p) {long v=peek(p,8);ev(events,"R64",p,v);return v;}
        public int readUnsignedByte(long p) {throw new AssertionError("unexpected R8");}
        public void writeDword(long p,int v) {ev(events,"W32",p,v);seed(p,4,v);}
        public void writeQword(long p,long v) {ev(events,"W64",p,v);seed(p,8,v);}
        public void writeByte(long p,int v) {ev(events,"W8",p,v&255);seed(p,1,v);}
        public int lockedXaddDword(long p,int v) {throw new AssertionError("unexpected atomic");}
        public void writeWord(long p,int v) {throw new AssertionError("unexpected W16");}
        public int readUnsignedWord(long p) {throw new AssertionError("unexpected R16");}
        public Bits128 read128(long p) {throw new AssertionError("unexpected R128");}
        public void write128(long p,Bits128 v) {throw new AssertionError("unexpected W128");}
        public void write128NonTemporal(long p,Bits128 v) {throw new AssertionError("unexpected NT128");}
        public FullCopy437Api.Bits256 read256(long p) {throw new AssertionError("unexpected R256");}
        public void write256(long p,FullCopy437Api.Bits256 v) {throw new AssertionError("unexpected W256");}
        public void write256NonTemporal(long p,FullCopy437Api.Bits256 v) {throw new AssertionError("unexpected NT256");}
        public void sfence() {throw new AssertionError("unexpected SFENCE");}
    }
    private static Ram initial(Mode mode) {
        Ram m=new Ram();for(int j=0;j<0x90;j++)m.seed(P-0x40+j,1,0x5a);
        long r=receiver(mode);m.seed(r,8,E);m.seed(r+12,4,count(mode));
        m.seed(E,8,T0);m.seed(T0,8,A0);m.seed(E1,8,T1OLD);m.seed(T1OLD,8,OLD);m.seed(T1NEW,8,POISON);
        m.seed(MARK,1,0xcc);m.seed(P,8,initialRip(mode));return m;
    }
    private static boolean firstBoundary(Mode m) {return m==Mode.FIRST_STOP||m==Mode.BAD_FIRST_RIP||m==Mode.THROW_FIRST;}
    private static boolean secondBoundary(Mode m) {return m==Mode.SECOND_STOP||m==Mode.BAD_SECOND_SP||m==Mode.BAD_SECOND_N||m==Mode.THROW_SECOND;}
    private static boolean invalid(Mode m) {return m==Mode.BAD_FIRST_RIP||m==Mode.BAD_SECOND_SP||m==Mode.BAD_SECOND_N;}
    private static boolean throwing(Mode m) {return m==Mode.THROW_FIRST||m==Mode.THROW_SECOND||m==Mode.THROW_BUDGET_SECOND;}
    private static void fixture(Mode mode) {
        Ram m=initial(mode),want=initial(mode);int[] calls={0},steps={0};QueueFp604Api.Stopped[] stopped={null};
        RuntimeException sentinel=new UnsupportedOperationException("owned645 finite callback/budget throw");
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,cursor)->{
            int j=steps[0]++;same(j<2&&pc==0x8897a0&&cursor==(j==0?E:E1),"actual source loop budget/captured cursor");
            ev(m.events,"BUDGET",pc,cursor);if(mode==Mode.THROW_BUDGET_SECOND&&j==1)throw sentinel;
        };
        EmbeddedClearFp645Api.Calls cb=f->{
            int j=calls[0]++;same(j<2,"two actual virtual invocations maximum");checkFrame(f,mode,j);
            ev(m.events,"CALL",0x8897a8,j==0?A0:A1);m.writeByte(MARK,j==0?0x11:0x22);
            if(j==0){m.writeQword(E1,T1NEW);m.writeQword(T1NEW,A1);m.writeQword(receiver(mode),OTHER);m.writeDword(receiver(mode)+12,9);}
            if((mode==Mode.FIRST_STOP&&j==0)||(mode==Mode.SECOND_STOP&&j==1)) {
                stopped[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(expectedChild(mode,j),0x8897a8,j==0,j==0?F0:F1),0,0x8897a8);return stopped[0];
            }
            if((mode==Mode.THROW_FIRST&&j==0)||(mode==Mode.THROW_SECOND&&j==1))throw sentinel;
            long ret=I+0x8897aa,sp=PRE;NonvolatileBits n=callN(mode,j);
            if(mode==Mode.BAD_FIRST_RIP&&j==0)ret++;
            if(mode==Mode.BAD_SECOND_SP&&j==1)sp+=8;
            if(mode==Mode.BAD_SECOND_N&&j==1)n=new NonvolatileBits(n.rbxBits()^1,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offered(j+1),ret,sp,n),j==1),j==0?F1:F2);
        };
        var input=new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,P,initialV(mode),initialN(mode)),true,budget),F0);
        QueueFp604Api.Outcome out=null;RuntimeException caught=null;
        try {out=EmbeddedClearWithFp645.execute(input,m,cb);}catch(RuntimeException ex){caught=ex;}
        int expectedCalls=!positive(mode)?0:firstBoundary(mode)||mode==Mode.THROW_BUDGET_SECOND?1:2;
        int expectedSteps=!positive(mode)?0:firstBoundary(mode)?1:2;
        same(calls[0]==expectedCalls&&steps[0]==expectedSteps,"finite callback/budget counts without base/count recapture");
        if(invalid(mode))same(caught instanceof IllegalArgumentException&&out==null,"bad Normal rejected before next source effects");
        else if(throwing(mode))same(caught==sentinel&&out==null,"arbitrary callback/budget exception same identity");
        else {
            same(caught==null,"normal/Stopped does not throw");
            if(mode==Mode.FIRST_STOP||mode==Mode.SECOND_STOP)same(out==stopped[0]&&out!=null,"first/second deep Stopped same identity");
            else {
                same(out instanceof QueueFp604Api.Normal,"whole93 normal completion");var nr=(QueueFp604Api.Normal)out;
                var vv=positive(mode)?offered(2):initialV(mode);
                same(nr.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(vv,finalRip(mode),P+8,initialN(mode))),"complete final V/N/RIP/SP including actual fresh RET");
                same(nr.base().postDirectionFlagSet()&&nr.postMxcsr()==(positive(mode)?F2:F0),"same current partial MXCSR and actual DF");
                same(m.peek(receiver(mode)+12,4)==0,"final source count is zero");
            }
        }
        compare(m,want,expected(mode));
        if(positive(mode))same(m.peek(receiver(mode),8)==OTHER,"first callback container-base write retained");
        if(positive(mode)&&mode!=Mode.POSITIVE)same(m.peek(receiver(mode)+12,4)==9,"Stopped/rejected/throw prefix keeps callback count without final zero");
        if(mode==Mode.RET_ALIAS)same(m.peek(P,8)==0xfedcba9800000000L,"count-zero write precedes fresh actual RET");
        if(mode==Mode.RSI_ALIAS)same(m.peek(P+0x10,8)==0xaabbccdd00000000L,"RSI home cleared after actual original RSI restore");
    }
    private static void callback1Writes(List<Event> z,Mode m) {
        ev(z,"W8",MARK,0x11);ev(z,"W64",E1,T1NEW);ev(z,"W64",T1NEW,A1);ev(z,"W64",receiver(m),OTHER);ev(z,"W32",receiver(m)+12,9);
    }
    /** Literal expected accesses, with early-boundary prefixes independent of actual events. */
    private static List<Event> expected(Mode mode) {
        var z=new ArrayList<Event>();var n=initialN(mode);long r=receiver(mode);
        ev(z,"W64",P+0x10,n.rsiBits());ev(z,"W64",P-8,n.rdiBits());ev(z,"R32",r+12,count(mode));
        if(!positive(mode)) {
            ev(z,"R64",P+0x10,n.rsiBits());ev(z,"W32",r+12,0);ev(z,"R64",P-8,n.rdiBits());ev(z,"R64",P,finalRip(mode));return z;
        }
        ev(z,"W64",P+8,n.rbxBits());ev(z,"R64",r,E);
        ev(z,"BUDGET",0x8897a0,E);ev(z,"R64",E,T0);ev(z,"R64",T0,A0);ev(z,"W64",CHILD,I+0x8897aa);ev(z,"CALL",0x8897a8,A0);callback1Writes(z,mode);
        if(firstBoundary(mode))return z;
        ev(z,"BUDGET",0x8897a0,E1);if(mode==Mode.THROW_BUDGET_SECOND)return z;
        ev(z,"R64",E1,T1NEW);ev(z,"R64",T1NEW,A1);ev(z,"W64",CHILD,I+0x8897aa);ev(z,"CALL",0x8897a8,A1);ev(z,"W8",MARK,0x22);
        if(secondBoundary(mode))return z;
        ev(z,"R64",P+8,n.rbxBits());ev(z,"W32",r+12,0);ev(z,"R64",P+0x10,n.rsiBits());ev(z,"R64",P-8,n.rdiBits());ev(z,"R64",P,finalRip(mode));return z;
    }
    private static void compare(Ram actual,Ram want,List<Event> literal) {
        for(Event e:literal)switch(e.kind()){
            case "W64"->want.seed(e.address(),8,e.value());case "W32"->want.seed(e.address(),4,e.value());case "W8"->want.seed(e.address(),1,e.value());default->{}
        }
        if(!actual.events.equals(literal)) {
            int j=0;while(j<actual.events.size()&&j<literal.size()&&actual.events.get(j).equals(literal.get(j)))j++;
            throw new AssertionError("645 literal cursor "+j+" actual="+(j<actual.events.size()?actual.events.get(j):"END")+" expected="+(j<literal.size()?literal.get(j):"END"));
        }
        same(actual.bytes.equals(want.bytes),"complete RAM/padding/stack/prefix equality; no target-derived oracle or rollback");
    }
    public static void nonPositiveNoCalls() {fixture(Mode.EMPTY_ZERO);fixture(Mode.EMPTY_NEGATIVE);}
    public static void positiveTwoOffers() {fixture(Mode.POSITIVE);}
    public static void stoppedPrefixes() {fixture(Mode.FIRST_STOP);fixture(Mode.SECOND_STOP);}
    public static void invalidNormalPrefixes() {fixture(Mode.BAD_FIRST_RIP);fixture(Mode.BAD_SECOND_SP);fixture(Mode.BAD_SECOND_N);}
    public static void throwPrefixes() {fixture(Mode.THROW_FIRST);fixture(Mode.THROW_SECOND);fixture(Mode.THROW_BUDGET_SECOND);}
    public static void retAndRestoreAlias() {fixture(Mode.RET_ALIAS);fixture(Mode.RSI_ALIAS);}
    public static int verify() {nonPositiveNoCalls();positiveTwoOffers();stoppedPrefixes();invalidNormalPrefixes();throwPrefixes();retAndRestoreAlias();return 6;}
    public static void main(String[] args) {System.out.println(verify());}
}
