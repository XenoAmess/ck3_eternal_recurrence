package org.xar.ck3.study.m6.element172;

import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.element190.RawMemory190.Access;
import java.util.ArrayList;
import java.util.List;

public final class Element172CandidateTest {
    public static final long D=0x8000000012341000L,S=0xf0000000abcd2000L,I=0x7fffffffff000000L;
    public record Scenario(String id,boolean sameObject,int kind,int count16,int count4,long begin16,long begin4,
                           int tail,int flag,boolean mutateSecond,int countAfter16,long beginAfter16,
                           boolean mutateTail,int tailAfter4,int flagAfter4) { }
    public record Call(String kind,List<Long> arguments) { }
    public static final class Fixture extends RawMemory190 implements Element172Inputs.Calls {
        public final Scenario item;public final long source;
        public final List<Object> events=new ArrayList<>();public final List<Call> calls=new ArrayList<>();
        public Runnable firstHook=()->{},secondHook=()->{};
        public Fixture(Scenario item) {
            this.item=item;source=item.sameObject()?D:S;fill(D,0x80,0xcc);if(source!=D)fill(source,0x80,0xcc);
            put32(source+0x08,item.kind());put64(source+0x10,item.begin16());put32(source+0x1c,item.count16());
            put64(source+0x28,item.begin4());put32(source+0x34,item.count4());put32(source+0x40,item.tail());put8(source+0x44,item.flag());
            for(int n=0;n<4;++n)put8(D+0x45+n,0xc5+n);
        }
        @Override protected void observed(Access access) { events.add(access); }
        @Override public void copy16_8c70b0(long header,long zero,long begin,long end) {
            Call c=new Call("copy16",List.of(header,zero,begin,end));calls.add(c);events.add(c);
            if(item.mutateSecond()) { put64(source+0x28,item.beginAfter16());put32(source+0x34,item.countAfter16()); }
            firstHook.run();
        }
        @Override public void copy4_add0d0(long header,long zero,long begin,long end) {
            Call c=new Call("copy4",List.of(header,zero,begin,end));calls.add(c);events.add(c);
            if(item.mutateTail()) { put32(source+0x40,item.tailAfter4());put8(source+0x44,item.flagAfter4()); }
            secondHook.run();
        }
        public long run() { return Element172Candidate.assign(new Element172Inputs.Input(D,source,I),this,this); }
    }
    private static int cases,checks;
    private static void equal(Object expected,Object actual) { ++checks;if(!expected.equals(actual))throw new IllegalStateException("expected "+expected+" actual "+actual); }
    private static Call c(String kind,long header,long begin,long end) { return new Call(kind,List.of(header,0L,begin,end)); }
    private static Scenario item(String id,boolean same,int n16,int n4,long b16,long b4) {
        return new Scenario(id,same,0x87654321,n16,n4,b16,b4,0x12345678,0xe9,false,0,0L,false,0,0);
    }
    private static void headers(Fixture f,int tail,int flag) {
        equal(I+0x45648a0L,f.peek64(D));equal(f.item.kind(),f.peek32(D+8));
        equal(0L,f.peek64(D+0x10));equal(0L,f.peek64(D+0x18));equal(I+0x54de260L,f.peek64(D+0x20));
        equal(0L,f.peek64(D+0x28));equal(0L,f.peek64(D+0x30));equal(I+0x54de268L,f.peek64(D+0x38));
        equal(tail,f.peek32(D+0x40));equal(flag,f.peek8(D+0x44));
        equal(List.of(0xc5,0xc6,0xc7,0xc8),List.of(f.peek8(D+0x45),f.peek8(D+0x46),f.peek8(D+0x47),f.peek8(D+0x48)));
    }
    public static void main(String[] arguments) {
        Fixture signed=new Fixture(item("signed",false,-2,-1,0x8000000000000010L,0xfffffffffffffff0L));
        equal(D,signed.run());equal(List.of(c("copy16",D+0x10,0x8000000000000010L,0x7ffffffffffffff0L),c("copy4",D+0x28,0xfffffffffffffff0L,0xffffffffffffffecL)),signed.calls);
        equal(List.of(new Access("w64",D,8,I+0x45648a0L),new Access("r32",S+8,4,0x87654321L),new Access("w32",D+8,4,0x87654321L),
                new Access("w64",D+0x18,8,0),new Access("w64",D+0x20,8,0),new Access("w64",D+0x10,8,0),new Access("w64",D+0x18,8,0),new Access("w64",D+0x20,8,I+0x54de260L),
                new Access("r32",S+0x1c,4,0xfffffffeL),new Access("r64",S+0x10,8,0x8000000000000010L),signed.calls.get(0)),signed.events.subList(0,11));
        equal(23,signed.events.size());headers(signed,0x12345678,0xe9);++cases;

        Scenario mutation=new Scenario("mutate",false,7,1,9,0xfffffffffffffff0L,0x10L,1,2,true,-2,0x8000000000000004L,true,Integer.MIN_VALUE,0xe1);
        Fixture changed=new Fixture(mutation);equal(D,changed.run());equal(List.of(c("copy16",D+0x10,0xfffffffffffffff0L,0L),c("copy4",D+0x28,0x8000000000000004L,0x7ffffffffffffffcL)),changed.calls);headers(changed,Integer.MIN_VALUE,0xe1);++cases;

        Fixture self=new Fixture(item("self",true,-2,7,0x1122334455667788L,0x8877665544332211L));equal(D,self.run());
        equal(List.of(c("copy16",D+0x10,0L,0L),c("copy4",D+0x28,0L,0L)),self.calls);headers(self,0x12345678,0xe9);++cases;

        Fixture selfChanged=new Fixture(new Scenario("self_mutate",true,3,1,1,0x11L,0x22L,4,5,true,3,0x3333L,true,-7,0xff));
        equal(D,selfChanged.run());equal(List.of(c("copy16",D+0x10,0L,0L),c("copy4",D+0x28,0L,0L)),selfChanged.calls);headers(selfChanged,-7,0xff);++cases;

        Fixture extremes=new Fixture(item("extremes",false,Integer.MIN_VALUE,Integer.MAX_VALUE,0x10L,0xfffffffffffffff0L));equal(D,extremes.run());
        equal(List.of(c("copy16",D+0x10,0x10L,0xfffffff800000010L),c("copy4",D+0x28,0xfffffffffffffff0L,0x00000001ffffffecL)),extremes.calls);headers(extremes,0x12345678,0xe9);++cases;

        Fixture zero=new Fixture(item("zero",false,0,0,0x8000000000000001L,0xfffffffffffffff3L));equal(D,zero.run());
        equal(List.of(c("copy16",D+0x10,0x8000000000000001L,0x8000000000000001L),c("copy4",D+0x28,0xfffffffffffffff3L,0xfffffffffffffff3L)),zero.calls);headers(zero,0x12345678,0xe9);++cases;

        Fixture stop1=new Fixture(item("stop1",false,1,1,0x10L,0x20L));RuntimeException one=new RuntimeException("one");stop1.firstHook=()->{throw one;};
        try { stop1.run();throw new IllegalStateException("missing sentinel"); } catch(RuntimeException failure) { equal(one,failure); }
        equal(1,stop1.calls.size());equal(0xccccccccccccccccL,stop1.peek64(D+0x28));equal(0xcccccccc,stop1.peek32(D+0x40));++cases;

        Fixture stop2=new Fixture(item("stop2",false,1,1,0x10L,0x20L));RuntimeException two=new RuntimeException("two");stop2.secondHook=()->{throw two;};
        try { stop2.run();throw new IllegalStateException("missing sentinel"); } catch(RuntimeException failure) { equal(two,failure); }
        equal(2,stop2.calls.size());equal(I+0x54de268L,stop2.peek64(D+0x38));equal(0xcccccccc,stop2.peek32(D+0x40));++cases;
        System.out.println("ELEMENT172_DATA_CASES="+cases+" CHECKS="+checks);
    }
}
