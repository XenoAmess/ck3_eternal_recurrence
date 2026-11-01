package org.xar.ck3.research.m3.dispatch219;

import java.util.*;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper218Api;
import org.xar.ck3.research.m3.dispatch218.DispatchHelper42420C0;

/** Owner mechanical byte fixture; only appended test methods supply semantic literals. */
public final class DispatchMiddleValidation219 {
    static int checks, groups, eventCount, memoryEvents, portEvents;
    static String h(long value) { return Long.toUnsignedString(value,16); }
    static void check(boolean value,String why) { checks++; if(!value)throw new AssertionError(why); }
    static void equal(long actual,long expected,String why) { check(actual==expected,why+" actual="+h(actual)+" expected="+h(expected)); }
    static void same(Object actual,Object expected) { check(actual==expected,"memory identity"); }
    static void iae(Runnable action) { checks++;try { action.run(); } catch(IllegalArgumentException expected) {return;}throw new AssertionError("expected IAE"); }
    static void events(List<String> actual,String... expected) {
        check(actual.equals(List.of(expected)),"complete ordered events actual="+actual+" expected="+List.of(expected));
        for(String value:actual) {eventCount++;if(value.startsWith("R")||value.startsWith("W")||value.startsWith("X"))memoryEvents++;else portEvents++;}
    }
    static void done(String name) {groups++;System.out.println("PASS "+name);}
    static final class Mem implements DispatchMiddle219Api.Memory {
        final Map<Long,Byte> data=new HashMap<>();
        final List<String> log;
        Mem(List<String> log) {this.log=log;}
        void seed(long a,int n,long v) {for(int i=0;i<n;i++)data.put(a+i,(byte)(v >>> (8*i)));}
        void seed8(long a,int v) {seed(a,1,v);}
        void seed16(long a,int v) {seed(a,2,v);}
        void seed32(long a,int v) {seed(a,4,v);}
        void seed64(long a,long v) {seed(a,8,v);}
        long peek(long a,int n) {long v=0;for(int i=0;i<n;i++){Byte b=data.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(long)(b&255) << (i*8);}return v;}
        long get(long a,int n) {long v=peek(a,n);log.add("R"+(n*8)+"@"+h(a)+"="+h(v));return v;}
        void put(long a,int n,long v) {seed(a,n,v);log.add("W"+(n*8)+"@"+h(a)+"="+h(n==8?v:v&((1L << (8*n))-1)));}
        @Override public long readPointer(long a) {return get(a,8);}
        @Override public int readInt32(long a) {return (int)get(a,4);}
        @Override public int readUnsigned8(long a) {return (int)get(a,1);}
        @Override public int readUnsigned16(long a) {return (int)get(a,2);}
        @Override public void writeInt32(long a,int v) {put(a,4,v);}
        @Override public void writeInt64(long a,long v) {put(a,8,v);}
        @Override public void write8(long a,int v) {put(a,1,v);}
        @Override public void exchangeInt32(long a,int v) {long old=peek(a,4);seed(a,4,v);log.add("X32@"+h(a)+"="+h(old)+"->"+h(Integer.toUnsignedLong(v)));}
    }
    static class Calls implements DispatchMiddle219Api.Ports {
        @Override public void call43dbba8(DispatchMiddle219Api.Memory m,long site,long target,long rax,int ecx,int edx,int r8d) {throw new AssertionError("unexpected indirect");}
        @Override public void call424de88(DispatchMiddle219Api.Memory m,long site,long rcx) {throw new AssertionError("unexpected de88");}
        @Override public void call424e1ac(DispatchMiddle219Api.Memory m,long site,long rcx,long rdx) {throw new AssertionError("unexpected e1ac");}
    }
    static class Outer implements DispatchHelper218Api.Ports {
        @Override public void enter(NativeTaskMemory m,long site,int ecx) {throw new AssertionError("unexpected enter");}
        @Override public void call42420f8(NativeTaskMemory m,long site,long rcx) {throw new AssertionError("unexpected outer middle");}
        @Override public long leave(NativeTaskMemory m,long site,int ecx,long rbx) {throw new AssertionError("unexpected leave");}
    }
    public static void main(String[] args) {
        earlyAndSelection();
        cookieEqual();
        cookieFreshAlias();
        actualMiddleBinding();
        System.out.println("GROUPS="+groups+" EVENTS="+eventCount+" MEMORY="+memoryEvents+" PORTS="+portEvents+" MIXED_CHECKS="+checks);
    }
static void earlyAndSelection() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed8(0x15c5d2e8L,0x80);m.seed8(0x15c5d2e7L,0xa5);m.seed8(0x15c5d2e9L,0x5a);
    DispatchMiddle42420F8.execute(m,new Calls(),new DispatchMiddle219Api.Input(0x10000000L,0xffff000000001000L));
    events(a,"R8@15c5d2e8=80");equal(m.peek(0x15c5d2e8L,1),0x80,"early flag");
    equal(m.peek(0x15c5d2e7L,1),0xa5,"early before");equal(m.peek(0x15c5d2e9L,1),0x5a,"early after");
    a.clear();Mem n=new Mem(a);
    n.seed8(0x15c5d2e8L,0);n.seed32(0x15c5d2dcL,0xdeadbeef);
    n.seed64(0x1000L,0x2000L);n.seed32(0x2000L,1);n.seed32(0x4000L,2);
    n.seed64(0x1008L,0x3000L);n.seed32(0x3000L,7);
    Calls one=new Calls() {
        @Override public void call424de88(DispatchMiddle219Api.Memory q,long site,long rcx) {
            same(q,n);equal(site,0x4242162L,"one de88site");equal(rcx,0x15c5d6b0L,"one selected LEA");
            a.add("Pde88:"+h(site)+":"+h(rcx));q.writeInt64(0x1000L,0x4000L);
        }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory q,long site,long rcx,long rdx) {
            same(q,n);equal(site,0x4242191L,"one unconditional secondsite");equal(rcx,0x1441ed78L,"one secondRCX");equal(rdx,0x1441ed80L,"one secondRDX");
            a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));
        }
    };
    DispatchMiddle42420F8.execute(n,one,new DispatchMiddle219Api.Input(0x10000000L,0x1000L));
    events(a,"R8@15c5d2e8=0","X32@15c5d2dc=deadbeef->1","R64@1000=2000","R32@2000=1",
        "Pde88:4242162:15c5d6b0","W64@1000=4000","R64@1000=4000","R32@4000=2",
        "Pe1ac:4242191:1441ed78:1441ed80","R64@1008=3000","R32@3000=7");
    equal(n.peek(0x15c5d2dcL,4),1,"one wholeexchange");equal(n.peek(0x15c5d2e8L,1),0,"one no flagstore");equal(n.peek(0x1000L,8),0x4000L,"one freshpointer");
    check(!n.data.containsKey(0x1010L),"one third pointer unmapped");
    a.clear();Mem o=new Mem(a);
    o.seed8(0x15c5d2e8L,0);o.seed32(0x15c5d2dcL,0x01234567);
    o.seed64(0x5000L,0x6000L);o.seed32(0x6000L,-1);o.seed32(0x7000L,0);
    o.seed64(0x5010L,0x8000L);o.seed8(0x8000L,0x80);o.seed8(0x7fffL,0xc3);o.seed8(0x8001L,0x3c);
    Calls other=new Calls() {
        @Override public void call424e1ac(DispatchMiddle219Api.Memory q,long site,long rcx,long rdx) {
            same(q,o);equal(site,0x4242191L,"other unconditional secondsite");equal(rcx,0x1441ed78L,"otherRCX");equal(rdx,0x1441ed80L,"otherRDX");
            a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));q.writeInt64(0x5008L,0x7000L);
        }
    };
    DispatchMiddle42420F8.execute(o,other,new DispatchMiddle219Api.Input(0x10000000L,0x5000L));
    events(a,"R8@15c5d2e8=0","X32@15c5d2dc=1234567->1","R64@5000=6000","R32@6000=ffffffff",
        "R64@5000=6000","R32@6000=ffffffff","Pe1ac:4242191:1441ed78:1441ed80","W64@5008=7000",
        "R64@5008=7000","R32@7000=0","W8@15c5d2e8=1","R64@5010=8000","W8@8000=1");
    equal(o.peek(0x15c5d2dcL,4),1,"otherexchange");equal(o.peek(0x15c5d2e8L,1),1,"otherflag");equal(o.peek(0x8000L,1),1,"otherfinalbyte");
    equal(o.peek(0x7fffL,1),0xc3,"other byte before");equal(o.peek(0x8001L,1),0x3c,"other byte after");
    done("earlyAndSelection");
}

static void cookieEqual() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed8(0x25c5d2e8L,0);m.seed8(0x25c5d2e9L,0x81);m.seed32(0x25c5d2dcL,0x80000000);
    m.seed64(0x9000L,0xa000L);m.seed32(0xa000L,0);m.seed32(0xb000L,0);m.seed32(0xc000L,1);
    m.seed64(0x2542f0b8L,0xfedcba9876543200L);m.seed64(0x25c5d2e0L,0xfedcba9876543200L);
    Calls calls=new Calls() {
        @Override public void call424de88(DispatchMiddle219Api.Memory q,long site,long rcx) {
            same(q,m);equal(site,0x4242162L,"equal de88site");equal(rcx,0x25c5d698L,"equal selectedLEA");
            a.add("Pde88:"+h(site)+":"+h(rcx));q.writeInt64(0x9000L,0xb000L);
        }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory q,long site,long rcx,long rdx) {
            same(q,m);
            if(site==0x424217eL) {
                equal(rcx,0x2441ed48L,"equal firstRCX");equal(rdx,0x2441ed70L,"equal firstRDX");
                a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));q.writeInt64(0x9008L,0xc000L);
            } else {
                equal(site,0x4242191L,"equal secondsite");equal(rcx,0x2441ed78L,"equal secondRCX");equal(rdx,0x2441ed80L,"equal secondRDX");
                a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));
            }
        }
    };
    DispatchMiddle42420F8.execute(m,calls,new DispatchMiddle219Api.Input(0x20000000L,0x9000L));
    events(a,"R8@25c5d2e8=0","X32@25c5d2dc=80000000->1","R64@9000=a000","R32@a000=0",
        "R64@2542f0b8=fedcba9876543200","R64@25c5d2e0=fedcba9876543200",
        "Pde88:4242162:25c5d698","W64@9000=b000","R64@9000=b000","R32@b000=0",
        "Pe1ac:424217e:2441ed48:2441ed70","W64@9008=c000","Pe1ac:4242191:2441ed78:2441ed80",
        "R64@9008=c000","R32@c000=1");
    equal(m.peek(0x25c5d2e8L,1),0,"equal no finalflag");equal(m.peek(0x25c5d2e9L,1),0x81,"equal adjacentbyte");
    equal(m.peek(0x25c5d2dcL,4),1,"equal exchange");equal(m.peek(0x9000L,8),0xb000L,"equal freshfirstptr");equal(m.peek(0x9008L,8),0xc000L,"equal freshsecondptr");
    check(!m.data.containsKey(0x9010L),"equal thirdslot unmapped");check(!m.data.containsKey(0x243dbba8L),"equal IATslot unmapped");
    done("cookieEqual");
}

static void actualMiddleBinding() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a),foreign=new Mem(a);
    Outer delegates=new Outer() {
        @Override public void enter(NativeTaskMemory q,long site,int ecx) {
            same(q,foreign);a.add("PdelegateEnter:"+h(site)+":"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public long leave(NativeTaskMemory q,long site,int ecx,long rbx) {
            same(q,foreign);a.add("PdelegateLeave:"+h(site)+":"+h(Integer.toUnsignedLong(ecx))+":"+h(rbx));return 0xaabbccdd01234567L;
        }
    };
    DispatchHelper218Api.Ports guarded=DispatchMiddleBinding219.bind(m,0x30000000L,new Calls(),delegates);
    iae(()->guarded.call42420f8(foreign,0x42420e0L,0x10100L));events(a);
    iae(()->guarded.call42420f8(m,0x42420e1L,0x10100L));events(a);
    check(m.data.isEmpty()&&foreign.data.isEmpty(),"newmiddle guards zero effects");
    guarded.enter(foreign,0x11L,-1);
    equal(guarded.leave(foreign,0x22L,Integer.MIN_VALUE,0xf000000000001234L),0xaabbccdd01234567L,"leave exact delegate raw64");
    events(a,"PdelegateEnter:11:ffffffff","PdelegateLeave:22:80000000:f000000000001234");a.clear();
    m.seed32(0x10000L,-1);m.seed32(0x10200L,2);
    m.seed8(0x35c5d2e8L,0);m.seed32(0x35c5d2dcL,-123);
    m.seed64(0x10100L,0x11000L);m.seed32(0x11000L,2);m.seed64(0x10108L,0x12000L);m.seed32(0x12000L,1);
    m.seed8(0x10110L,0xd2);m.seed8(0x10117L,0xd3);m.seed8(0x10204L,0xd4);
    Calls child=new Calls() {
        @Override public void call424e1ac(DispatchMiddle219Api.Memory q,long site,long rcx,long rdx) {
            same(q,m);equal(site,0x4242191L,"chain mandatorysite");equal(rcx,0x3441ed78L,"chain RCX");equal(rdx,0x3441ed80L,"chain RDX");
            a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));q.writeInt32(0x10200L,0x80000001);
        }
    };
    Outer tails=new Outer() {
        @Override public void enter(NativeTaskMemory q,long site,int ecx) {
            same(q,m);equal(site,0x42420d7L,"chain enter site");equal(ecx,-1,"chain enter signedECX");a.add("Penter:"+h(Integer.toUnsignedLong(ecx)));
        }
        @Override public long leave(NativeTaskMemory q,long site,int ecx,long rbx) {
            same(q,m);equal(site,0x42420e8L,"chain leave site");equal(ecx,0x80000001,"chain postmiddle freshECX");equal(rbx,0x10200L,"chain originalR9");
            a.add("Pleave:"+h(Integer.toUnsignedLong(ecx))+":"+h(rbx));return 0xfedcba9876543210L;
        }
    };
    DispatchHelper218Api.Ports bound=DispatchMiddleBinding219.bind(m,0x30000000L,child,tails);
    equal(DispatchHelper42420C0.execute(m,bound,new DispatchHelper218Api.Input(0x10000L,0x10100L,0x10200L)),0xfedcba9876543210L,"actual218 still returns lastleave");
    events(a,"R32@10000=ffffffff","Penter:ffffffff","R8@35c5d2e8=0","X32@35c5d2dc=ffffff85->1",
        "R64@10100=11000","R32@11000=2","R64@10100=11000","R32@11000=2",
        "Pe1ac:4242191:3441ed78:3441ed80","W32@10200=80000001","R64@10108=12000","R32@12000=1",
        "R32@10200=80000001","Pleave:80000001:10200");
    equal(m.peek(0x35c5d2dcL,4),1,"chain exchange");equal(m.peek(0x35c5d2e8L,1),0,"chain no flagstore");equal(m.peek(0x10200L,4),0x80000001L,"chain callbackeffect");
    equal(m.peek(0x10108L,8),0x12000L,"chain secondpointer unchanged");equal(m.peek(0x10110L,1),0xd2,"chain unusedthirdslot first");equal(m.peek(0x10117L,1),0xd3,"chain unusedthirdslot end");equal(m.peek(0x10204L,1),0xd4,"chain postdata nextbyte");
    done("actualMiddleBinding");
}

static void cookieFreshAlias() {
    List<String> a=new ArrayList<>();Mem m=new Mem(a);
    m.seed64(0x5c5d2d8L,0x100002000L);m.seed32(0x100002000L,0);
    m.seed64(0x542f0b8L,0x800000000000003fL);m.seed64(0x5c5d2e0L,0x0123456789abcd00L);
    m.seed64(0x43dbba8L,0xf123456789abcdefL);m.seed64(0x5c5d2e8L,0xa000L);
    m.seed32(0x4000L,1);m.seed32(0x5000L,0);m.seed32(0xb000L,0);
    m.seed8(0xc000L,0xa5);m.seed8(0xc001L,0x5a);m.seed8(0xc002L,0x3c);
    Calls calls=new Calls() {
        @Override public void call43dbba8(DispatchMiddle219Api.Memory q,long site,long target,long rax,int ecx,int edx,int r8d) {
            same(q,m);equal(site,0x4242147L,"IAT source site");equal(target,0xf123456789abcdefL,"actual IAT target");
            equal(rax,0x02468acf13579a7fL,"full decoded ROR63");equal(ecx,0,"IAT ECX");equal(edx,0,"IAT EDX");equal(r8d,0,"IAT R8D");
            a.add("Piat:"+h(site)+":"+h(target)+":"+h(rax)+":"+ecx+":"+edx+":"+r8d);
            q.writeInt64(0x5c5d2d8L,0x4000L);
        }
        @Override public void call424de88(DispatchMiddle219Api.Memory q,long site,long rcx) {
            same(q,m);equal(site,0x4242162L,"unequal de88site");equal(rcx,0x5c5d698L,"unequal selectedLEA");
            a.add("Pde88:"+h(site)+":"+h(rcx));q.writeInt64(0x5c5d2d8L,0x5000L);
        }
        @Override public void call424e1ac(DispatchMiddle219Api.Memory q,long site,long rcx,long rdx) {
            same(q,m);
            if(site==0x424217eL) {
                equal(rcx,0x441ed48L,"unequal firstRCX");equal(rdx,0x441ed70L,"unequal firstRDX");
                a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));q.writeInt64(0x5c5d2e0L,0xb000L);
            } else {
                equal(site,0x4242191L,"unequal mandatorysecond");equal(rcx,0x441ed78L,"unequal secondRCX");equal(rdx,0x441ed80L,"unequal secondRDX");
                a.add("Pe1ac:"+h(site)+":"+h(rcx)+":"+h(rdx));q.writeInt64(0x5c5d2e8L,0xc000L);
            }
        }
    };
    DispatchMiddle42420F8.execute(m,calls,new DispatchMiddle219Api.Input(0,0x5c5d2d8L));
    events(a,"R8@5c5d2e8=0","X32@5c5d2dc=1->1","R64@5c5d2d8=100002000","R32@100002000=0",
        "R64@542f0b8=800000000000003f","R64@5c5d2e0=123456789abcd00","R64@43dbba8=f123456789abcdef",
        "Piat:4242147:f123456789abcdef:2468acf13579a7f:0:0:0","W64@5c5d2d8=4000","Pde88:4242162:5c5d698",
        "W64@5c5d2d8=5000","R64@5c5d2d8=5000","R32@5000=0","Pe1ac:424217e:441ed48:441ed70",
        "W64@5c5d2e0=b000","Pe1ac:4242191:441ed78:441ed80","W64@5c5d2e8=c000","R64@5c5d2e0=b000",
        "R32@b000=0","W8@5c5d2e8=1","R64@5c5d2e8=c001","W8@c001=1");
    equal(m.peek(0x5c5d2d8L,8),0x5000L,"aliased finalfirstptr");equal(m.peek(0x5c5d2dcL,4),0,"X32 cell later changed by P callbackwrite");
    equal(m.peek(0x5c5d2e0L,8),0xb000L,"cookieB alias now secondptr");equal(m.peek(0x5c5d2e8L,8),0xc001L,"globalW8 precedes freshthirdptr");
    equal(m.peek(0x5c5d2e8L,1),1,"aliased flagbyte");equal(m.peek(0xc001L,1),1,"actual fresh thirdbyte");
    equal(m.peek(0xc000L,1),0xa5,"stale thirdaddress byte untouched");equal(m.peek(0xc002L,1),0x3c,"after thirdbyte");
    equal(m.peek(0x542f0b8L,8),0x800000000000003fL,"originalcookie unchanged");equal(m.peek(0x43dbba8L,8),0xf123456789abcdefL,"actual IAT slot unchanged");
    equal(m.peek(0x4000L,4),1,"intermediateobject unchanged");equal(m.peek(0x5000L,4),0,"fresh firstobject");
    done("cookieFreshAlias");
}

}
