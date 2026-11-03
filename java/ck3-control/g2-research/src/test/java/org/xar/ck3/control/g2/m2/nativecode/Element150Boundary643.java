package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner literal held150 fixtures. SOURCE-LITERAL-ORACLE643.json predates this source.
 * Only new API declarations and original150 ASM were read; the new producer body was not read.
 * Two external calls offer explicit complete states, never M6 algorithms or default callee state.
 * Expected access/RAM/register states come from literal source, never a target run. */
public final class Element150Boundary643 {
    private Element150Boundary643() { }
    private static final long I=0x140000000L,P=0x70002008L,PRE=P-0x28,CHILD=P-0x30;
    private static final long DEST=0x8000000000001100L,S=0xf000000000002200L;
    private static final long A16=I+0x54de260,A4=I+0x54de268,VT=I+0x45648a0;
    private static final long RIP=I+0x123456,MARK=0x8880;
    private static final QueueFp604Api.Mxcsr F0=new QueueFp604Api.Mxcsr(1,3);
    private static final QueueFp604Api.Mxcsr F1=new QueueFp604Api.Mxcsr(8,12);
    private static final QueueFp604Api.Mxcsr F2=new QueueFp604Api.Mxcsr(0x40,0xc0);
    private enum Mode { NORMAL,FIRST_STOP,SECOND_STOP,BAD_FIRST_RIP,BAD_SECOND_SP,BAD_SECOND_N,THROW_FIRST,THROW_SECOND,ALIAS }
    private record Event(String kind,long address,long value) { }
    private static void ev(List<Event> z,String k,long p,long v) {z.add(new Event(k,p,v));}
    private static void same(boolean ok,String why) {if(!ok)throw new AssertionError(why);}
    private static Bits128 x(long a) {return new Bits128(a,~a);}
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9) {
        return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));
    }
    private static VolatileBits initialV(long d) {return bank(0x1000,0x111,d,S,0x114,0x115);}
    private static VolatileBits offered(int j) {long b=0x2000+j*0x1000;return bank(b,b+1,b+2,b+3,b+4,b+5);}
    private static VolatileBits overwrite3(VolatileBits b,long ax,long cx,long dx) {
        return new VolatileBits(ax,cx,dx,b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits(),b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());
    }
    private static VolatileBits beforeCall(long d,int j) {
        return j==0?overwrite3(initialV(d),A16,d+0x10,S+0x10):overwrite3(offered(1),A4,d+0x28,S+0x28);
    }
    private static NonvolatileBits initialN() {return new NonvolatileBits(0x201,0x202,0x203,0x204,0x205,0x206,0x207,0x208,x(0x209));}
    private static NonvolatileBits callN(long d) {var n=initialN();return new NonvolatileBits(S,n.rbpBits(),0,d,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static long site(int j) {return j==0?0x37295fb:0x3729620;}
    private static long target(int j) {return j==0?0x21a5050:0xb2eee0;}
    private static GovernmentCrtBoundary185Api.Entry expectedChild(long d,int j) {
        return new GovernmentCrtBoundary185Api.Entry(I,CHILD,beforeCall(d,j),callN(d));
    }
    private static void checkFrame(Element150Fp643Api.CallFrame f,long d,int j) {
        var c=new GovernmentCrtBoundary185Api.Call(site(j),GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target(j),PRE,beforeCall(d,j),callN(d));
        same(f.call().equals(c),"independent complete CALL "+j);
        same(f.childEntry().equals(expectedChild(d,j)),"independent complete child Entry "+j);
        same(f.directionFlagSet()==(j==0)&&f.preMxcsr()==(j==0?F0:F1),"actual DF/current partial MXCSR object "+j);
        same(f.instructionLength()==5&&f.returnRipBits()==I+site(j)+5,"instruction length/return RIP "+j);
    }
    /** Pure mechanical owned byte RAM. No target behavior or expected-state generation. */
    private static final class Ram implements Element150Fp643Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<Event> events=new ArrayList<>();
        void seed(long p,int w,long v) {for(int j=0;j<w;j++)bytes.put(p+j,(byte)(v>>>(8*j)));}
        long peek(long p,int w) {long v=0;for(int j=0;j<w;j++)v|=(bytes.getOrDefault(p+j,(byte)0)&255L)<<(8*j);return v;}
        public int readDword(long p) {int v=(int)peek(p,4);ev(events,"R32",p,v);return v;}
        public long readQword(long p) {long v=peek(p,8);ev(events,"R64",p,v);return v;}
        public int readUnsignedByte(long p) {int v=(int)peek(p,1);ev(events,"R8",p,v);return v;}
        public void writeDword(long p,int v) {ev(events,"W32",p,v);seed(p,4,v);}
        public void writeQword(long p,long v) {ev(events,"W64",p,v);seed(p,8,v);}
        public void writeByte(long p,int v) {ev(events,"W8",p,v&255);seed(p,1,v);}
        public int lockedXaddDword(long p,int v) {throw new AssertionError("unexpected atomic");}
        public Bits128 read128(long p) {throw new AssertionError("unexpected R128");}
        public void write128(long p,Bits128 v) {throw new AssertionError("unexpected W128");}
    }
    private static Ram initial(long d) {
        Ram m=new Ram();for(int j=0;j<0x48;j++)m.seed(d+j,1,0xcc);
        m.seed(S+8,4,0x76543210);m.seed(S+0x40,4,0x55667788);m.seed(S+0x44,1,0x99);
        for(int j=0;j<0x90;j++)m.seed(P-0x40+j,1,0x5a);m.seed(P,8,RIP);m.seed(MARK,1,0xcc);return m;
    }
    private static boolean firstBoundary(Mode m) {return m==Mode.FIRST_STOP||m==Mode.BAD_FIRST_RIP||m==Mode.THROW_FIRST;}
    private static boolean secondBoundary(Mode m) {return m==Mode.SECOND_STOP||m==Mode.BAD_SECOND_SP||m==Mode.BAD_SECOND_N||m==Mode.THROW_SECOND;}
    private static boolean badNormal(Mode m) {return m==Mode.BAD_FIRST_RIP||m==Mode.BAD_SECOND_SP||m==Mode.BAD_SECOND_N;}
    private static boolean throwing(Mode m) {return m==Mode.THROW_FIRST||m==Mode.THROW_SECOND;}
    private static void fixture(Mode mode) {
        long d=mode==Mode.ALIAS?S+4:DEST;Ram m=initial(d),want=initial(d);int[] calls={0};
        QueueFp604Api.Stopped[] stopped={null};RuntimeException sent=new UnsupportedOperationException("owned643 callback throw");
        Element150Fp643Api.Calls cb=f->{
            int j=calls[0]++;same(j<2,"exactly two held calls maximum");checkFrame(f,d,j);
            ev(m.events,"CALL",site(j),target(j));m.writeByte(MARK,j==0?0x11:0x22);
            if(mode==Mode.ALIAS&&j==1){m.writeDword(S+0x40,0x11223344);m.writeByte(S+0x44,0xa6);}
            if((mode==Mode.FIRST_STOP&&j==0)||(mode==Mode.SECOND_STOP&&j==1)) {
                stopped[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(expectedChild(d,j),target(j),j==0,j==0?F0:F1),0,site(j));
                return stopped[0];
            }
            if((mode==Mode.THROW_FIRST&&j==0)||(mode==Mode.THROW_SECOND&&j==1))throw sent;
            long ret=I+site(j)+5,sp=PRE;NonvolatileBits n=callN(d);
            if(mode==Mode.BAD_FIRST_RIP&&j==0)ret++;
            if(mode==Mode.BAD_SECOND_SP&&j==1)sp+=8;
            if(mode==Mode.BAD_SECOND_N&&j==1)n=new NonvolatileBits(n.rbxBits()^1,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(offered(j+1),ret,sp,n),j==1),j==0?F1:F2);
        };
        var input=new Element150Fp643Api.Input(new GovernmentCrtBoundary185Api.Entry(I,P,initialV(d),initialN()),true,F0);
        QueueFp604Api.Outcome out=null;RuntimeException caught=null;
        try {out=Element150FullState643.execute(input,m,cb);}catch(RuntimeException ex){caught=ex;}
        same(calls[0]==(firstBoundary(mode)?1:2),"exact callback count at finite boundary");
        if(badNormal(mode))same(caught instanceof IllegalArgumentException&&out==null,"bad Normal rejected before continuation");
        else if(throwing(mode))same(caught==sent&&out==null,"arbitrary callback exception same identity");
        else {
            same(caught==null,"normal/Stopped path does not throw");
            if(mode==Mode.FIRST_STOP||mode==Mode.SECOND_STOP)same(out==stopped[0]&&out!=null,"Stopped returned with same identity");
            else {
                same(out instanceof QueueFp604Api.Normal,"complete held150 Normal");var nr=(QueueFp604Api.Normal)out;
                var o2=offered(2);var expectedV=overwrite3(o2,d,o2.rcxBits(),o2.rdxBits());
                same(nr.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(expectedV,RIP,P+8,initialN())),"complete final V/N/RIP/SP");
                same(nr.base().postDirectionFlagSet()&&nr.postMxcsr()==F2,"exact post DF and current partial FP same object");
            }
        }
        compare(m,want,expected(mode,d));
        same(m.peek(P+0x18,8)==initialN().rbxBits()&&m.peek(P+0x20,8)==initialN().rsiBits()&&m.peek(P-8,8)==initialN().rdiBits(),"saved NV prefix retained");
        same(m.peek(P+8,8)==d&&m.peek(P+0x10,8)==d+(firstBoundary(mode)?0x10:0x28),"exact overwritten home slots/prefix");
        if(mode==Mode.NORMAL)same(m.peek(d+0x40,4)==0x55667788&&m.peek(d+0x44,1)==0x99,"ordinary final source field loads");
        if(mode==Mode.ALIAS)same(m.peek(S+0x40,4)==0x11223344&&m.peek(d+0x40,4)==0x11223344&&m.peek(S+0x44,1)==0x44&&m.peek(d+0x44,1)==0x44&&m.peek(d+0x38,8)==0x11223344454de268L,"callback and subsequent destination/source alias influence both fresh final loads");
    }
    /** Complete finite source-literal trace; no trace element is copied from actual events. */
    private static List<Event> expected(Mode mode,long d) {
        var z=new ArrayList<Event>();var n=initialN();
        ev(z,"W64",P+0x18,n.rbxBits());ev(z,"W64",P+0x20,n.rsiBits());ev(z,"W64",P+8,d);ev(z,"W64",P-8,n.rdiBits());
        ev(z,"W64",d,VT);ev(z,"R32",S+8,mode==Mode.ALIAS?1:0x76543210);ev(z,"W32",d+8,mode==Mode.ALIAS?1:0x76543210);
        ev(z,"W64",P+0x10,d+0x10);ev(z,"W64",d+0x10,0);ev(z,"W64",d+0x18,0);ev(z,"W64",d+0x20,A16);
        ev(z,"W64",CHILD,I+0x3729600);ev(z,"CALL",0x37295fb,0x21a5050);ev(z,"W8",MARK,0x11);
        if(firstBoundary(mode))return z;
        ev(z,"W64",P+0x10,d+0x28);ev(z,"W64",d+0x28,0);ev(z,"W64",d+0x30,0);ev(z,"W64",d+0x38,A4);
        ev(z,"W64",CHILD,I+0x3729625);ev(z,"CALL",0x3729620,0xb2eee0);ev(z,"W8",MARK,0x22);
        if(mode==Mode.ALIAS){ev(z,"W32",S+0x40,0x11223344);ev(z,"W8",S+0x44,0xa6);}
        if(secondBoundary(mode))return z;
        long tail=mode==Mode.ALIAS?0x11223344:0x55667788,flag=mode==Mode.ALIAS?0x44:0x99;
        ev(z,"R32",S+0x40,tail);ev(z,"W32",d+0x40,tail);ev(z,"R8",S+0x44,flag);ev(z,"W8",d+0x44,flag);
        ev(z,"R64",P+0x18,n.rbxBits());ev(z,"R64",P+0x20,n.rsiBits());ev(z,"R64",P-8,n.rdiBits());ev(z,"R64",P,RIP);return z;
    }
    private static void compare(Ram actual,Ram want,List<Event> literal) {
        for(Event e:literal)switch(e.kind()){
            case "W64"->want.seed(e.address(),8,e.value());case "W32"->want.seed(e.address(),4,e.value());case "W8"->want.seed(e.address(),1,e.value());default->{}
        }
        if(!actual.events.equals(literal)){
            int j=0;while(j<actual.events.size()&&j<literal.size()&&actual.events.get(j).equals(literal.get(j)))j++;
            throw new AssertionError("643 literal cursor "+j+" actual="+(j<actual.events.size()?actual.events.get(j):"END")+" expected="+(j<literal.size()?literal.get(j):"END"));
        }
        same(actual.bytes.equals(want.bytes),"complete RAM/padding/callstack equality, including callback prefix and no rollback");
    }
    public static void normalTwoOffers() {fixture(Mode.NORMAL);}
    public static void firstStopped() {fixture(Mode.FIRST_STOP);}
    public static void secondStopped() {fixture(Mode.SECOND_STOP);}
    public static void invalidNormalPrefixes() {fixture(Mode.BAD_FIRST_RIP);fixture(Mode.BAD_SECOND_SP);fixture(Mode.BAD_SECOND_N);}
    public static void throwPrefixes() {fixture(Mode.THROW_FIRST);fixture(Mode.THROW_SECOND);}
    public static void callbackAliasFreshFinal() {fixture(Mode.ALIAS);}
    public static int verify() {normalTwoOffers();firstStopped();secondStopped();invalidNormalPrefixes();throwPrefixes();callbackAliasFreshFinal();return 6;}
    public static void main(String[] args) {System.out.println(verify());}
}
