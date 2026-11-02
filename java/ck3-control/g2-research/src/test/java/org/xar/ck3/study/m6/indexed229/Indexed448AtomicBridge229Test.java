package org.xar.ck3.study.m6.indexed229;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/** Four business observations prePOST; one direct raw-width counter was added after model END. */
public final class Indexed448AtomicBridge229Test {
    private Indexed448AtomicBridge229Test() { }
    private static int checks;
    private record Seed(long address,long value,int width) { }
    private record Mutation(String operation,long address,long value) { }
    private record Step(String role,long site,Long target,List<Long> arguments,Long returned,List<Mutation> mutations) { }
    private record Scene(String id,IndexedHelper225Api.Input input,List<Seed> seeds,List<Step> steps,
            boolean atomicThrows,List<String> trace,long expected,String error) { }
    public static void main(String[] args){
        List<Scene> scenes=List.of(
        new Scene("empty-list-single-exchange",new IndexedHelper225Api.Input(0x140000000L,3,0x660000L,0x600000L,0x600000L),List.of(new Seed(0x145c5d7a8L,0x123456788765430dL,8),new Seed(0x14542f0b8L,0x123456788765430dL,8)),List.of(),false,List.of("R64:145c5d7a8:123456788765430d","R64:14542f0b8:123456788765430d","X64:145c5d7a8:edcba987789abcf2:123456788765430d"),0x0L,null),
        new Scene("fresh-module-cookie-callbacks",new IndexedHelper225Api.Input(0x140000000L,4,0x660000L,0x600000L,0x600008L),List.of(new Seed(0x145c5d7b0L,0x123456788765430dL,8),new Seed(0x14542f0b8L,0x123456788765430dL,8),new Seed(0x600000L,0x7L,4),new Seed(0x600004L,0x8L,4),new Seed(0x145c5d728L,0x0L,8),new Seed(0x144426a08L,0x770000L,8),new Seed(0x1443da478L,0x7fff00000000a111L,8),new Seed(0x1443da7c0L,0x7fff00000000a222L,8),new Seed(0x1443da680L,0x7fff00000000a333L,8)),List.of(new Step("478",0x424e4ebL,0x7fff00000000a111L,List.of(0x770000L,0x0L,0x800L),0x8000000000000101L,List.of(new Mutation("W64",0x145c5d728L,0xabc0000000000303L),new Mutation("W64",0x14542f0b8L,0xf12345678876542fL))),new Step("7c0",0x424e574L,0x7fff00000000a222L,List.of(0x8000000000000101L),null,List.of(new Mutation("W64",0x14542f0b8L,0x801122334455663fL),new Mutation("W64",0x1443da680L,0x7fff00000000b444L),new Mutation("W32",0x600004L,0x80000008L))),new Step("680",0x424e5a0L,0x7fff00000000b444L,List.of(0x8000000000000101L,0x660000L),0x9000000000000202L,List.of(new Mutation("W64",0x14542f0b8L,0xe102030405060711L)))),false,List.of("R64:145c5d7b0:123456788765430d","R64:14542f0b8:123456788765430d","R32:600000:7","R64:145c5d728:0","R64:144426a08:770000","R64:1443da478:7fff00000000a111","W64:145c5d728:abc0000000000303","W64:14542f0b8:f12345678876542f","X64:145c5d728:8000000000000101:abc0000000000303","R64:1443da7c0:7fff00000000a222","W64:14542f0b8:801122334455663f","W64:1443da680:7fff00000000b444","W32:600004:80000008","R64:14542f0b8:801122334455663f","R64:1443da680:7fff00000000b444","W64:14542f0b8:e102030405060711","R64:14542f0b8:e102030405060711","X64:145c5d7b0:e102030401032711:123456788765430d"),0x9000000000000202L,null),
        new Scene("skip-sentinel-load-fails",new IndexedHelper225Api.Input(0x140000000L,5,0x660000L,0x600000L,0x600008L),List.of(new Seed(0x145c5d7b8L,0x123456788765430dL,8),new Seed(0x14542f0b8L,0x123456788765430dL,8),new Seed(0x600000L,0x7L,4),new Seed(0x600004L,0x8L,4),new Seed(0x145c5d728L,0xffffffffffffffffL,8),new Seed(0x145c5d730L,0x0L,8),new Seed(0x144426a10L,0x880000L,8),new Seed(0x1443da478L,0x7fff00000000c555L,8),new Seed(0x1443da738L,0x7fff00000000c666L,8)),List.of(new Step("478",0x424e4ebL,0x7fff00000000c555L,List.of(0x880000L,0x0L,0x800L),0x0L,List.of(new Mutation("W64",0x14542f0b8L,0xf12345678876542fL))),new Step("738",0x424e4f9L,0x7fff00000000c666L,List.of(),0x80000013L,List.of())),false,List.of("R64:145c5d7b8:123456788765430d","R64:14542f0b8:123456788765430d","R32:600000:7","R64:145c5d728:ffffffffffffffff","R32:600004:8","R64:145c5d730:0","R64:144426a10:880000","R64:1443da478:7fff00000000c555","W64:14542f0b8:f12345678876542f","R64:1443da738:7fff00000000c666","X64:145c5d730:ffffffffffffffff:0","R64:14542f0b8:f12345678876542f","X64:145c5d7b8:edcba987789abd0:123456788765430d"),0x0L,null),
        new Scene("exchange-throws-prefix",new IndexedHelper225Api.Input(0x140000000L,6,0x660000L,0x600000L,0x600000L),List.of(new Seed(0x145c5d7c0L,0x123456788765430dL,8),new Seed(0x14542f0b8L,0x123456788765430dL,8)),List.of(),true,List.of("R64:145c5d7c0:123456788765430d","R64:14542f0b8:123456788765430d","X64_THROW:145c5d7c0:edcba987789abcf2"),0x0L,"sameAtomicMarker"));
        for(Scene scene:scenes)run(scene);
        rawWidthCounter();
        System.out.println("PASS scenes=5 checks="+checks+" uncachedBusiness4=true postPOSTRawWidthCounter1=true singleLogicalExchange=true full185Frame=false hardwareAtomicity=false Native=false Game=false");
    }
    private static void run(Scene scene){
        Ram m=new Ram();m.atomicThrows=scene.atomicThrows();for(Seed s:scene.seeds())m.seed(s.address(),s.value(),s.width());
        int[] cursor={0};IndexedHelper225Api.Memory[] captured={null};
        IndexedHelper225Api.Ports ports=new IndexedHelper225Api.Ports(){
            private long next(IndexedHelper225Api.Memory view,String role,long site,Long target,List<Long> arguments){
                ok(cursor[0]<scene.steps().size(),"no unexpected callback");Step s=scene.steps().get(cursor[0]++);
                eq(role,s.role(),"actual port role");eq(site,s.site(),"actual site");eq(target,s.target(),"actual fresh target");eq(arguments,s.arguments(),"all supplied scalar callback arguments");
                if(captured[0]==null)captured[0]=view;else ok(captured[0]==view,"same captured Memory view across callbacks");
                for(Mutation change:s.mutations()){
                    if(change.operation().equals("W64"))view.writeInt64(change.address(),change.value());
                    else if(change.operation().equals("W32"))view.writeInt32(change.address(),(int)change.value());
                    else throw new AssertionError("unknown controlled callback mutation");
                }
                return s.returned()==null?0L:s.returned().longValue();
            }
            @Override public long call43da478(IndexedHelper225Api.Memory v,long s,long t,long c,int d,int r){return next(v,"478",s,t,List.of(c,Integer.toUnsignedLong(d),Integer.toUnsignedLong(r)));}
            @Override public int call43da738(IndexedHelper225Api.Memory v,long s,long t){return(int)next(v,"738",s,t,List.of());}
            @Override public int call4246a60(IndexedHelper225Api.Memory v,long s,long c,long d,int r){return(int)next(v,"direct6a60",s,null,List.of(c,d,Integer.toUnsignedLong(r)));}
            @Override public void call43da7c0(IndexedHelper225Api.Memory v,long s,long t,long c){next(v,"7c0",s,t,List.of(c));}
            @Override public long call43da680(IndexedHelper225Api.Memory v,long s,long t,long c,long d){return next(v,"680",s,t,List.of(c,d));}
        };
        if(scene.error()==null)eq(Indexed448AtomicBridge229.execute(m,ports,scene.input()),scene.expected(),"whole mature business scalar from new bridge");
        else{
            try{Indexed448AtomicBridge229.execute(m,ports,scene.input());throw new AssertionError("atomic exception swallowed or replayed");}
            catch(UnsupportedOperationException ex){ok(ex==m.marker,"same opaque exchange exception prefix");}
        }
        eq(cursor[0],scene.steps().size(),"exact callback count");eq(m.trace,scene.trace(),"all sameRAM observations/oneeffect exchanges/fresh callback writes");
        eq(m.exchanges,scene.trace().stream().filter(s->s.startsWith("X64")).count(),"each declared exchange is one port operation");
        System.out.println("PASS "+scene.id());
    }
    private static void rawWidthCounter(){
        Ram m=new Ram();long a=0x8000000000000040L,old=0xabc0000000000000L,value=0xfedcba9876543210L;m.seed(a,old,8);
        long observed=Indexed448AtomicBridge229.asIndexed(m).exchangeInt64(a,value);
        eq(observed,old,"full old64 bits including low32zero");eq(m.load(a,8),value,"full new64 bits at full raw address");
        eq(m.trace,List.of(event("X64",a,value)+":"+Long.toUnsignedString(old,16)),"no split read/write exposed");eq(m.exchanges,1,"one direct exchange");
        System.out.println("PASS postPOST-fullWidthOldBits");
    }
    private static void eq(Object a,Object b,String label){checks++;if(!Objects.equals(a,b))throw new AssertionError(label+" actual="+a+" expected="+b);}
    private static void eq(long a,long b,String label){checks++;if(a!=b)throw new AssertionError(label+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(b));}
    private static void ok(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
    private static String event(String op,long a,long value){return op+":"+Long.toUnsignedString(a,16)+":"+Long.toUnsignedString(value,16);}
    private static final class Ram implements AtomicIndexedMemory229{
        private final Map<Long,Byte> data=new HashMap<>();private final List<String> trace=new ArrayList<>();private boolean atomicThrows;private int exchanges;
        private final UnsupportedOperationException marker=new UnsupportedOperationException("controlled exchange unavailable");
        void seed(long a,long value,int width){for(int j=0;j<width;j++)data.put(a+j,(byte)(value>>>(8*j)));}
        long load(long a,int width){long value=0;for(int j=0;j<width;j++){Byte b=data.get(a+j);if(b==null)throw new AssertionError("unowned RAM "+Long.toHexString(a+j));value|=(long)Byte.toUnsignedInt(b)<<(8*j);}return value;}
        @Override public int readDword(long a){long v=load(a,4);trace.add(event("R32",a,v));return(int)v;}
        @Override public long readQword(long a){long v=load(a,8);trace.add(event("R64",a,v));return v;}
        @Override public void writeDword(long a,int v){seed(a,Integer.toUnsignedLong(v),4);trace.add(event("W32",a,Integer.toUnsignedLong(v)));}
        @Override public void writeQword(long a,long v){seed(a,v,8);trace.add(event("W64",a,v));}
        @Override public long exchangeQword(long a,long v){
            exchanges++;if(atomicThrows){trace.add(event("X64_THROW",a,v));throw marker;}
            long old=load(a,8);seed(a,v,8);trace.add(event("X64",a,v)+":"+Long.toUnsignedString(old,16));return old;
        }
        @Override public int readUnsignedByte(long a){throw new AssertionError("unexpected byte read");}
        @Override public void writeByte(long a,int v){throw new AssertionError("unexpected byte write");}
        @Override public int lockedXaddDword(long a,int v){throw new AssertionError("unexpected DWORD XADD");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected memory vector");}
        @Override public void write128(long a,Bits128 v){throw new AssertionError("unexpected memory vector");}
    }
}
