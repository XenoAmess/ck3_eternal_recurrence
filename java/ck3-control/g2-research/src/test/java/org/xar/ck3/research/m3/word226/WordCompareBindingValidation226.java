package org.xar.ck3.research.m3.word226;
import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
/** Owner mechanical fixture only; no newbindingtest/expected beforefirstHTTP. */
public final class WordCompareBindingValidation226 {
    static int checks,groups,eventCount,memoryEvents,portEvents;
    static String h(long v){return Long.toUnsignedString(v,16);}
    static void check(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    static void equal(long a,long b,String why){check(a==b,why+" actual="+h(a)+" expected="+h(b));}
    static void same(Object a,Object b){check(a==b,"identity");}
    static void iae(Runnable r){checks++;try{r.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expectedIAE");}
    static void events(List<String> actual,String... expected){check(actual.equals(List.of(expected)),"trace actual="+actual+" expected="+List.of(expected));for(String e:actual){eventCount++;if(e.startsWith("R")||e.startsWith("W")||e.startsWith("X"))memoryEvents++;else portEvents++;}}
    static void done(String s){groups++;System.out.println("PASS "+s);}
    static final class Mem implements WordCompareBinding226Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> log;Mem(List<String> l){log=l;}
        void seed(long a,int n,long v){for(int i=0;i<n;i++)bytes.put(a+i,(byte)(v >>> (i*8)));}
        void seed8(long a,int v){seed(a,1,v);}void seed16(long a,int v){seed(a,2,v);}void seed32(long a,int v){seed(a,4,v);}void seed64(long a,long v){seed(a,8,v);}
        long peek(long a,int n){long v=0;for(int i=0;i<n;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n){long v=peek(a,n);log.add("R"+(8*n)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v){seed(a,n,v);log.add("W"+(8*n)+"@"+h(a)+"="+h(n==8?v:v&0xffffffffL));}
        @Override public long readPointer(long a){return get(a,8);}@Override public int readInt32(long a){return (int)get(a,4);}
        @Override public void writeInt32(long a,int v){put(a,4,v);}@Override public void writeInt64(long a,long v){put(a,8,v);}
        @Override public long exchangeInt64(long a,long v){long old=peek(a,8);seed(a,8,v);log.add("X64@"+h(a)+"="+h(old)+"->"+h(v));return old;}
        @Override public int readWord16(long a){return (int)get(a,2);}
    }
    static class Fallback implements IndexedHelper225Api.Ports {
        @Override public long call43da478(IndexedHelper225Api.Memory m,long site,long target,long rcx,int edx,int r8d){throw new AssertionError("unexpected478");}
        @Override public int call43da738(IndexedHelper225Api.Memory m,long site,long target){throw new AssertionError("unexpected738");}
        @Override public int call4246a60(IndexedHelper225Api.Memory m,long site,long rcx,long rdx,int r8d){throw new AssertionError("activefallback replay");}
        @Override public void call43da7c0(IndexedHelper225Api.Memory m,long site,long target,long rcx){throw new AssertionError("unexpected7C0");}
        @Override public long call43da680(IndexedHelper225Api.Memory m,long site,long target,long rcx,long rdx){throw new AssertionError("unexpected680");}
    }
    public static void main(String[] args){delegatesAndGuards();activeAndReal();System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);}
static void delegatesAndGuards() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    RuntimeException marker=new RuntimeException("controlled passive callback failure");
    Fallback fallback=new Fallback() {
        @Override public long call43da478(IndexedHelper225Api.Memory q,long site,long target,long rcx,int edx,int r8d) {
            same(q,foreign);equal(site,0x1111L,"478 site");equal(target,0xf100000000000001L,"478 target");equal(rcx,0xf200000000000002L,"478 RCX");equal(edx,Integer.MIN_VALUE,"478 EDX");equal(r8d,-1,"478 R8D");
            a.add("P478:"+h(site)+":"+h(target)+":"+h(rcx)+":"+h(Integer.toUnsignedLong(edx))+":"+h(Integer.toUnsignedLong(r8d)));return 0xf300000000000003L;
        }
        @Override public int call43da738(IndexedHelper225Api.Memory q,long site,long target) {
            same(q,foreign);equal(site,0x2222L,"738 site");equal(target,0xf400000000000004L,"738 target");
            a.add("P738:"+h(site)+":"+h(target));return 0x87654321;
        }
        @Override public void call43da7c0(IndexedHelper225Api.Memory q,long site,long target,long rcx) {
            same(q,foreign);equal(site,0x3333L,"7C0 site");equal(target,0xf500000000000005L,"7C0 target");equal(rcx,0xf600000000000006L,"7C0 RCX");
            a.add("P7c0:"+h(site)+":"+h(target)+":"+h(rcx));throw marker;
        }
        @Override public long call43da680(IndexedHelper225Api.Memory q,long site,long target,long rcx,long rdx) {
            same(q,foreign);equal(site,0x4444L,"680 site");equal(target,0xf700000000000007L,"680 target");equal(rcx,0xf800000000000008L,"680 RCX");equal(rdx,0xf900000000000009L,"680 RDX");
            a.add("P680:"+h(site)+":"+h(target)+":"+h(rcx)+":"+h(rdx));return 0x80000000abcdef12L;
        }
    };
    WordCompare226Api reject=(q,left,right,count)->{throw new AssertionError("rejected active callback reached algorithm");};
    IndexedHelper225Api.Ports bound=WordCompareFromIndexedBinding226.bind(m,reject,fallback);
    iae(()->bound.call4246a60(foreign,0x424e514L,1,2,7));events(a);
    iae(()->bound.call4246a60(m,0x424e515L,1,2,7));events(a);
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"active guards beforeall effects");
    equal(bound.call43da478(foreign,0x1111L,0xf100000000000001L,0xf200000000000002L,Integer.MIN_VALUE,-1),0xf300000000000003L,"478 exactfullreturn");
    equal(bound.call43da738(foreign,0x2222L,0xf400000000000004L),0x87654321,"738 exactintreturn");
    try {bound.call43da7c0(foreign,0x3333L,0xf500000000000005L,0xf600000000000006L);throw new AssertionError("passive exception swallowed");}
    catch(RuntimeException actual){same(actual,marker);}
    equal(bound.call43da680(foreign,0x4444L,0xf700000000000007L,0xf800000000000008L,0xf900000000000009L),0x80000000abcdef12L,"680 exactfullreturn");
    events(a,"P478:1111:f100000000000001:f200000000000002:80000000:ffffffff","P738:2222:f400000000000004",
        "P7c0:3333:f500000000000005:f600000000000006","P680:4444:f700000000000007:f800000000000008:f900000000000009");
    check(m.bytes.isEmpty()&&foreign.bytes.isEmpty(),"passivedelegates noextraMemoryeffect");
    done("delegatesAndGuards");
}

static void activeAndReal() {
    List<String> log = new ArrayList<>();
    Mem m = new Mem(log);
    int[] callCounter = new int[1];
    WordCompare226Api algorithm = new WordCompare226Api() {
        @Override public WordCompare226Api.Result execute(WordCompare226Api.Memory memory, long left, long right, long count) {
            same(memory, m);
            int idx = callCounter[0]++;
            check(idx<2,"script exactlytwoinvocations");
            log.add("Pscript:"+h(left)+":"+h(right)+":"+h(count));
            if (idx == 0) {
                equal(left, 0xf000000000001000L, "left0");
                equal(right, 0xe000000000002000L, "right0");
                equal(count, 0x80000000L, "count0");
                return new WordCompare226Api.Result(-123456789, 0xFEDCBA9876543210L, 0x1111222233334444L, 65535, true);
            } else {
                equal(left, 0x3333444455556666L, "left1");
                equal(right, 0x777788889999AAAAL, "right1");
                equal(count, 0xFFFFFFFFL, "count1");
                return new WordCompare226Api.Result(0x81234567, 1L, 0x5555L, 7, true);
            }
        }
    };
    IndexedHelper225Api.Ports bound = WordCompareFromIndexedBinding226.bind(m, algorithm, new Fallback());
    int r1 = bound.call4246a60(m, 0x424E514L, 0xf000000000001000L, 0xe000000000002000L, 0x80000000);
    int r2 = bound.call4246a60(m, 0x424E52AL, 0x3333444455556666L, 0x777788889999AAAAL, 0xFFFFFFFF);
    check(r1 == -123456789, "r1");
    check(r2 == 0x81234567, "r2");
    check(callCounter[0] == 2, "calls");
    check(m.bytes.isEmpty(), "noMemoryEvents");
    events(log,"Pscript:f000000000001000:e000000000002000:80000000",
        "Pscript:3333444455556666:777788889999aaaa:ffffffff");
    log.clear();
    WordCompare4246A60 realAlgo = new WordCompare4246A60();
    IndexedHelper225Api.Ports boundReal = WordCompareFromIndexedBinding226.bind(m, realAlgo, new Fallback());
    m.seed16(0x1000L, 0x8000);
    m.seed16(0x2000L, 0x7FFF);
    m.seed(0x0FFFL, 1, 0xAA);
    m.seed(0x1002L, 1, 0xBB);
    m.seed(0x1FFFL, 1, 0xCC);
    m.seed(0x2002L, 1, 0xDD);
    int r3 = boundReal.call4246a60(m, 0x424E514L, 0x1000L, 0x2000L, 1);
    check(r3 == 1, "r3");
    events(log, "R16@1000=8000", "R16@2000=7fff");
    check(m.peek(0x0FFFL, 1) == 0xAA, "canaryL-1");
    check(m.peek(0x1002L, 1) == 0xBB, "canaryL+2");
    check(m.peek(0x1FFFL, 1) == 0xCC, "canaryR-1");
    check(m.peek(0x2002L, 1) == 0xDD, "canaryR+2");
    equal(m.peek(0x1000L,2),0x8000,"realleftWORD unchanged");
    equal(m.peek(0x2000L,2),0x7fff,"realrightWORD unchanged");
    done("activeAndReal");
}
}
