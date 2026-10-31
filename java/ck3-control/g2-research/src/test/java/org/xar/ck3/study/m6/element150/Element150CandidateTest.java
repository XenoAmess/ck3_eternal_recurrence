package org.xar.ck3.study.m6.element150;

import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.element190.RawMemory190.Access;
import java.util.ArrayList;
import java.util.List;

public final class Element150CandidateTest {
    public static final long D=0x8000000012341000L,S=0xf0000000abcd2000L,I=0x7fffffffff000000L;
    public record Scenario(String id,boolean sameObject,int kind,int tail,int flag,boolean mutateTail,int tailAfter4,int flagAfter4) { }
    public record Call(String kind,List<Long> arguments) { }
    public static final class Fixture extends RawMemory190 implements Element150Inputs.Calls {
        public final Scenario item;public final long source;
        public final List<Object> events=new ArrayList<>();public final List<Call> calls=new ArrayList<>();
        public Runnable firstHook=()->{},secondHook=()->{};
        public long firstSourceWord,secondSourceWord,secondDestinationWord;
        public Fixture(Scenario item) {
            this.item=item;source=item.sameObject()?D:S;fill(D,0x80,0xcc);if(source!=D)fill(source,0x80,0xcc);
            put32(source+0x08,item.kind());put32(source+0x40,item.tail());put8(source+0x44,item.flag());
            for(int n=0;n<4;++n)put8(D+0x45+n,0xc5+n);
        }
        @Override protected void observed(Access access) { events.add(access); }
        @Override public void copy16_21a5050(long destinationHeader,long sourceHeader) {
            Call c=new Call("copy16",List.of(destinationHeader,sourceHeader));calls.add(c);events.add(c);
            firstSourceWord=peek64(sourceHeader);firstHook.run();
        }
        @Override public void copy4_b2eee0(long destinationHeader,long sourceHeader) {
            Call c=new Call("copy4",List.of(destinationHeader,sourceHeader));calls.add(c);events.add(c);
            secondSourceWord=peek64(sourceHeader);secondDestinationWord=peek64(destinationHeader);
            if(item.mutateTail()) { put32(source+0x40,item.tailAfter4());put8(source+0x44,item.flagAfter4()); }
            secondHook.run();
        }
        public long run() { return Element150Candidate.copy(new Element150Inputs.Input(D,source,I),this,this); }
    }
    private static int checks,cases;
    private static void equal(Object expected,Object actual) { ++checks;if(!expected.equals(actual))throw new IllegalStateException("expected "+expected+" actual "+actual); }
    private static Scenario item(String id,boolean same) { return new Scenario(id,same,0x87654321,0x12345678,0xe9,false,0,0); }
    private static void headers(Fixture f,int tail,int flag) {
        equal(I+0x45648a0L,f.peek64(D));equal(f.item.kind(),f.peek32(D+8));
        equal(0L,f.peek64(D+0x10));equal(0L,f.peek64(D+0x18));equal(I+0x54de260L,f.peek64(D+0x20));
        equal(0L,f.peek64(D+0x28));equal(0L,f.peek64(D+0x30));equal(I+0x54de268L,f.peek64(D+0x38));
        equal(tail,f.peek32(D+0x40));equal(flag,f.peek8(D+0x44));
        equal(List.of(0xc5,0xc6,0xc7,0xc8),List.of(f.peek8(D+0x45),f.peek8(D+0x46),f.peek8(D+0x47),f.peek8(D+0x48)));
    }
    private static void calls(Fixture f) {
        equal(List.of(new Call("copy16",List.of(D+0x10,f.source+0x10)),new Call("copy4",List.of(D+0x28,f.source+0x28))),f.calls);
    }
    public static void main(String[] arguments) {
        Fixture normal=new Fixture(item("normal",false));equal(D,normal.run());calls(normal);headers(normal,0x12345678,0xe9);
        equal(0xccccccccccccccccL,normal.firstSourceWord);equal(0xccccccccccccccccL,normal.secondSourceWord);
        equal(List.of(new Access("w64",D,8,I+0x45648a0L),new Access("r32",S+8,4,0x87654321L),new Access("w32",D+8,4,0x87654321L),
                new Access("w64",D+0x10,8,0L),new Access("w64",D+0x18,8,0L),new Access("w64",D+0x20,8,I+0x54de260L),normal.calls.get(0),
                new Access("w64",D+0x28,8,0L),new Access("w64",D+0x30,8,0L),new Access("w64",D+0x38,8,I+0x54de268L),normal.calls.get(1),
                new Access("r32",S+0x40,4,0x12345678L),new Access("w32",D+0x40,4,0x12345678L),new Access("r8",S+0x44,1,0xe9),new Access("w8",D+0x44,1,0xe9)),normal.events);++cases;

        Fixture self=new Fixture(item("self",true));equal(D,self.run());calls(self);headers(self,0x12345678,0xe9);
        equal(0L,self.firstSourceWord);equal(0L,self.secondSourceWord);++cases;

        Fixture first=new Fixture(item("first_mutation",false));
        first.firstHook=()->{ first.put32(S+0x40,0xaabbccdd);first.put8(S+0x44,0x81);first.put64(S+0x28,0xf000123456789abcL);first.put32(S+8,7); };
        equal(D,first.run());calls(first);headers(first,0xaabbccdd,0x81);equal(0xf000123456789abcL,first.secondSourceWord);++cases;

        Fixture second=new Fixture(new Scenario("second_mutation",false,0x87654321,1,2,true,Integer.MIN_VALUE,0xff));
        equal(D,second.run());calls(second);headers(second,Integer.MIN_VALUE,0xff);++cases;

        Fixture overwritten=new Fixture(item("second_header_overwritten",false));
        overwritten.firstHook=()->{ overwritten.put64(D+0x28,0x1111L);overwritten.put64(D+0x30,0x2222L);overwritten.put64(D+0x38,0x3333L); };
        equal(D,overwritten.run());calls(overwritten);headers(overwritten,0x12345678,0xe9);equal(0L,overwritten.secondDestinationWord);++cases;

        Fixture zero=new Fixture(new Scenario("zero",false,0,0,0,false,0,0));equal(D,zero.run());calls(zero);headers(zero,0,0);++cases;

        Fixture stop1=new Fixture(item("stop1",false));RuntimeException one=new RuntimeException("one");stop1.firstHook=()->{throw one;};
        try { stop1.run();throw new IllegalStateException("missing sentinel"); } catch(RuntimeException failure) { equal(one,failure); }
        equal(1,stop1.calls.size());equal(0xccccccccccccccccL,stop1.peek64(D+0x28));equal(0xcccccccc,stop1.peek32(D+0x40));++cases;

        Fixture stop2=new Fixture(item("stop2",false));RuntimeException two=new RuntimeException("two");stop2.secondHook=()->{throw two;};
        try { stop2.run();throw new IllegalStateException("missing sentinel"); } catch(RuntimeException failure) { equal(two,failure); }
        equal(2,stop2.calls.size());equal(I+0x54de268L,stop2.peek64(D+0x38));equal(0xcccccccc,stop2.peek32(D+0x40));++cases;
        System.out.println("ELEMENT150_DATA_CASES="+cases+" CHECKS="+checks);
    }
}
