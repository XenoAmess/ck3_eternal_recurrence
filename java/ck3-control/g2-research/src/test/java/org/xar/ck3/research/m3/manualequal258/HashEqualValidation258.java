package org.xar.ck3.research.m3.manualequal258;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.hash188.HashInsertC39C60;
import org.xar.ck3.research.m3.hashequal258.HashEqualBinding258;

/** New supplied-storage boundary cases; no Native, CPU, FP or old suite execution. */
public final class HashEqualValidation258 {
    private static final long MASK=0x5CAFCBCL, LIMIT=0x5CB0A58L, SITE=0xC39CCAL;
    private static int checks, events;
    private record E(String op,long address,long first,long second) { }
    private record P(String op,HashInsert188Api.Memory memory,long site,long a,long b,long c,long d) { }
    private static E e(String op,long a,long b) { return new E(op,a,b,0); }
    private static E v(long a,long low,long high) { return new E("R128",a,low,high); }
    private static void check(boolean good) { checks++;if(!good)throw new AssertionError("check "+checks); }
    private static void trace(M m,List<E> expected) {
        check(m.log.equals(expected));events+=m.log.size();m.log.clear();
    }
    private static void vector(List<E> out,long entry,long left,long right,long ll,long lh,long rl,long rh) {
        out.add(e("R16",MASK,0));out.add(e("W16",entry+8,0));out.add(e("W16",entry+16,0));
        out.add(e("R16",entry+8,0));out.add(e("R16",entry+16,0));out.add(e("R16",LIMIT,0));
        out.add(e("R16",entry+16,0));out.add(v(left,ll,lh));out.add(v(right,rl,rh));
    }

    private static void directViewsAndUnqualifiedCallsPreserveBoundaries() {
        M m=new M();Capture p=new Capture();HashInsert188Api.Ports bound=HashEqualBinding258.bind(0,m,p);
        m.seed(MASK,0,2);m.seed(LIMIT,0,2);
        long left=0x3000,right=0x4000,entry=0x7000;
        long low=0x6161616161616161L, high=0x0061616161616161L;
        m.seed128(left,low,high);m.seed128(right,low,high);
        check(bound.equal3f6d2b0(m,SITE,left,right,entry)==1);
        List<E> expected=new ArrayList<>();vector(expected,entry,left,right,low,high,low,high);trace(m,expected);
        m.seed128(right,low,0x0062616161616161L);
        check(bound.equal3f6d2b0(m,SITE,left,right,entry)==0);
        expected=new ArrayList<>();vector(expected,entry,left,right,low,high,low,0x0062616161616161L);trace(m,expected);

        m.seed(MASK,0xFFFF,2);m.seed(left,'q',1);m.seed(right,'r',1);
        check(bound.equal3f6d2b0(m,SITE,left,right,entry)==0);
        trace(m,List.of(e("R16",MASK,0xFFFF),e("W16",entry+8,0x4000),e("W16",entry+16,0x3000),
                e("R16",entry+8,0x4000),e("R16",entry+16,0x3000),e("R16",LIMIT,0),
                e("R16",entry+8,0x4000),e("R8",left,'q'),e("R8",right,'r')));

        M foreign=new M();long a=Long.MIN_VALUE+3,b=-17,rsp=Long.MAX_VALUE-7;
        check(bound.equal3f6d2b0(m,SITE,a,b)==0x81234567);
        check(p.calls.remove(0).equals(new P("equal4",m,SITE,a,b,0,0)));
        check(bound.equal3f6d2b0(foreign,SITE,a,b,rsp)==0x76543210);
        check(p.calls.remove(0).equals(new P("equal5",foreign,SITE,a,b,rsp,0)));
        check(bound.equal3f6d2b0(m,SITE+1,a,b,rsp)==0x76543210);
        check(p.calls.remove(0).equals(new P("equal5",m,SITE+1,a,b,rsp,0)));
        check(bound.equal3f6d2b0(null,SITE,a,b,rsp)==0x76543210);
        check(p.calls.remove(0).equals(new P("equal5",null,SITE,a,b,rsp,0)));
        check(m.log.isEmpty()&&foreign.log.isEmpty());
        bound.copy855f00(m,1,a,b);bound.assign855db0(m,2,a,b,rsp);
        bound.rehashC3a400(m,3,a);bound.insertC3b960(m,4,a,b,0xFEDCBA98,rsp);
        bound.destroy856050(m,5,a);check(bound.capacity86e160(m,6,0x80000001,0xFEDCBA98)==0xCAFEBABE);
        bound.reserveC3b700(m,7,a,0xFEDCBA98);bound.overflow86f210(m,8,a,b);bound.terminal4232cf4(m,9);
        check(p.calls.equals(List.of(new P("copy",m,1,a,b,0,0),new P("assign",m,2,a,b,rsp,0),
                new P("rehash",m,3,a,0,0,0),new P("insert",m,4,a,b,0xFEDCBA98,rsp),
                new P("destroy",m,5,a,0,0,0),new P("capacity",m,6,0x80000001,0xFEDCBA98,0,0),
                new P("reserve",m,7,a,0xFEDCBA98,0,0),new P("overflow",m,8,a,b,0,0),new P("terminal2",m,9,0,0,0,0))));
        p.calls.clear();RuntimeException terminal=new RuntimeException("terminal marker");p.terminal=terminal;
        try {bound.terminal4232cf4(m,10,rsp);throw new AssertionError("no terminal throw");}
        catch(RuntimeException actual) {check(actual==terminal);}
        check(p.calls.equals(List.of(new P("terminal3",m,10,rsp,0,0,0))));check(m.log.isEmpty());

        m.seed(MASK,0,2);RuntimeException read=new RuntimeException("read marker");m.failure=read;m.failAddress=MASK;
        try {bound.equal3f6d2b0(m,SITE,left,right,entry);throw new AssertionError("no read throw");}
        catch(RuntimeException actual) {check(actual==read);}
        trace(m,List.of(e("R16",MASK,0)));m.failure=null;
        try {HashEqualBinding258.bind(0,null,p);throw new AssertionError("null memory");}
        catch(NullPointerException expectedNull) {check(m.log.isEmpty());}
        try {HashEqualBinding258.bind(0,m,null);throw new AssertionError("null fallback");}
        catch(NullPointerException expectedNull) {check(m.log.isEmpty());}
    }

    private static void actualCallerUsesEachCurrentFrameAndOldDefault() {
        long map=0x1000,data=0x2000,next=0x3000,desc=0x4000,out=0x9000,body=0x8800;
        M m=fixture(map,data,desc);m.seed128(data+8,0x0079656BL,0);m.seed(map+0x18,3,1);
        Capture fallback=new Capture();HashInsert188Api.Ports ports=HashEqualBinding258.bind(0,m,fallback);
        HashInsert188Api.Input input=new HashInsert188Api.Input(0,map,out,0,desc,new HashInsert188Api.Scratch(body));
        check(HashInsertC39C60.execute(input,m,ports)==out);
        List<E> expected=prefix(map,data,desc);vector(expected,body-8,desc,data+8,0x0079656B,0,0x0079656B,0);
        expected.add(e("W64",out,data));expected.add(e("W8",out+8,0));trace(m,expected);
        check(fallback.calls.isEmpty()&&m.peek(out,8)==data&&m.peek(out+8,1)==0);

        m=fixture(map,data,desc);m.seed128(data+8,0x6F6E,0);m.seed(data+0x2C,0,1);m.seed(map+0x18,0,1);
        m.seed(next+4,1,1);m.seed(next+0x20,15,8);m.seed128(next+8,0x0079656B,0);
        Growth growth=new Growth(m,map,next);ports=HashEqualBinding258.bind(0,m,growth);
        check(HashInsertC39C60.execute(input,m,ports)==out);
        expected=prefix(map,data,desc);vector(expected,body-8,desc,data+8,0x0079656B,0,0x6F6E,0);
        expected.add(e("R8",data+0x2C,0));expected.add(e("R32",map+0x14,1));expected.add(e("R8",map+0x18,0));
        expected.add(new E("CAPACITY",0xC39F2F,2,1));expected.add(new E("RESERVE",0xC39F3E,map,1));
        expected.add(e("OPAQUE_W64",map+8,next));expected.add(e("W8",body+0xC0,0));expected.add(e("W64",body+0x20,body+0xC0));
        expected.addAll(prefix(map,next,desc));vector(expected,body-0xB0-8,desc,next+8,0x0079656B,0,0x0079656B,0);
        expected.add(e("W64",out,next));expected.add(e("W8",out+8,0));trace(m,expected);
        check(growth.calls.isEmpty());check(m.peek(body,2)==0&&m.peek(body+8,2)==0);
        check(m.peek(body-0xB0,2)==0&&m.peek(body-0xB0+8,2)==0);
        check(m.peek(out,8)==next&&m.peek(out+8,1)==0);

        m=fixture(map,data,desc);OldOnly old=new OldOnly();
        check(HashInsertC39C60.execute(input,m,old)==out);
        expected=prefix(map,data,desc);expected.add(e("W64",out,data));expected.add(e("W8",out+8,0));trace(m,expected);
        check(old.calls.equals(List.of(new P("equal4",m,SITE,desc,data+8,0,0))));
    }
    private static M fixture(long map,long data,long desc) {
        M m=new M();m.seed(MASK,0,2);m.seed(LIMIT,0,2);m.seed(map+0x14,1,4);m.seed(map+8,data,8);
        m.seed(data+4,1,1);m.seed(data+0x20,15,8);m.seed(desc+0x18,15,8);m.seed128(desc,0x0079656B,0);
        return m;
    }
    private static List<E> prefix(long map,long data,long desc) {
        return new ArrayList<>(List.of(e("R32",map+0x14,1),e("R64",map+8,data),e("R8",data+4,1),
                e("R64",desc+0x18,15),e("R64",data+0x20,15)));
    }
    private static final class M implements HashEqualBinding258.Memory {
        final Map<Long,Integer> bytes=new HashMap<>();final List<E> log=new ArrayList<>();
        RuntimeException failure;long failAddress;
        void seed(long a,long bits,int size) {for(int i=0;i<size;i++)bytes.put(a+i,(int)(bits>>>(i*8))&255);}
        void seed128(long a,long low,long high) {seed(a,low,8);seed(a+8,high,8);}
        long peek(long a,int size) {long result=0;for(int i=0;i<size;i++){Integer b=bytes.get(a+i);if(b==null)throw new AssertionError("unseeded "+Long.toHexString(a+i));result|=(long)b<<(i*8);}return result;}
        long read(String op,long a,int size) {long x=peek(a,size);log.add(e(op,a,x));if(failure!=null&&a==failAddress)throw failure;return x;}
        void write(String op,long a,long value,int size) {long x=size==8?value:value&((1L<<(size*8))-1);log.add(e(op,a,x));seed(a,value,size);}
        @Override public long readPointer(long a){return read("R64",a,8);}
        @Override public int readInt32(long a){return (int)read("R32",a,4);}
        @Override public void writeInt32(long a,int x){write("W32",a,x,4);}
        @Override public void writeInt64(long a,long x){write("W64",a,x,8);}
        @Override public int readUnsigned8(long a){return (int)read("R8",a,1);}
        @Override public void write8(long a,int x){write("W8",a,x,1);}
        @Override public int readUnsigned16(long a){return (int)read("R16",a,2);}
        @Override public void write16(long a,int x){write("W16",a,x,2);}
        @Override public HashInsert188Api.Bytes16 read128(long a){long l=peek(a,8),h=peek(a+8,8);log.add(v(a,l,h));return new HashInsert188Api.Bytes16(l,h);}
        @Override public void write128(long a,HashInsert188Api.Bytes16 x){log.add(new E("W128",a,x.low(),x.high()));seed128(a,x.low(),x.high());}
    }
    private static class OldOnly implements HashInsert188Api.Ports {
        final List<P> calls=new ArrayList<>();RuntimeException terminal;
        @Override public int equal3f6d2b0(HashInsert188Api.Memory m,long s,long a,long b){calls.add(new P("equal4",m,s,a,b,0,0));return 0x81234567;}
        @Override public void copy855f00(HashInsert188Api.Memory m,long s,long a,long b){calls.add(new P("copy",m,s,a,b,0,0));}
        @Override public void assign855db0(HashInsert188Api.Memory m,long s,long a,long b,long c){calls.add(new P("assign",m,s,a,b,c,0));}
        @Override public void rehashC3a400(HashInsert188Api.Memory m,long s,long a){calls.add(new P("rehash",m,s,a,0,0,0));}
        @Override public void insertC3b960(HashInsert188Api.Memory m,long s,long a,long b,int c,long d){calls.add(new P("insert",m,s,a,b,c,d));}
        @Override public void destroy856050(HashInsert188Api.Memory m,long s,long a){calls.add(new P("destroy",m,s,a,0,0,0));}
        @Override public int capacity86e160(HashInsert188Api.Memory m,long s,int a,int b){calls.add(new P("capacity",m,s,a,b,0,0));return 0xCAFEBABE;}
        @Override public void reserveC3b700(HashInsert188Api.Memory m,long s,long a,int b){calls.add(new P("reserve",m,s,a,b,0,0));}
        @Override public void overflow86f210(HashInsert188Api.Memory m,long s,long a,long b){calls.add(new P("overflow",m,s,a,b,0,0));}
        @Override public void terminal4232cf4(HashInsert188Api.Memory m,long s){calls.add(new P("terminal2",m,s,0,0,0,0));}
    }
    private static final class Capture extends OldOnly {
        @Override public int equal3f6d2b0(HashInsert188Api.Memory m,long s,long a,long b,long rsp){calls.add(new P("equal5",m,s,a,b,rsp,0));return 0x76543210;}
        @Override public void terminal4232cf4(HashInsert188Api.Memory m,long s,long rsp){calls.add(new P("terminal3",m,s,rsp,0,0,0));throw terminal;}
    }
    private static final class Growth extends OldOnly {
        final M memory;final long map,next;
        Growth(M memory,long map,long next){this.memory=memory;this.map=map;this.next=next;}
        @Override public int capacity86e160(HashInsert188Api.Memory m,long s,int a,int b){check(m==memory);memory.log.add(new E("CAPACITY",s,a,b));return 1;}
        @Override public void reserveC3b700(HashInsert188Api.Memory m,long s,long a,int b){check(m==memory);memory.log.add(new E("RESERVE",s,a,b));memory.log.add(e("OPAQUE_W64",map+8,next));memory.seed(map+8,next,8);}
    }
    public static void main(String[] args) {
        directViewsAndUnqualifiedCallsPreserveBoundaries();actualCallerUsesEachCurrentFrameAndOldDefault();
        check(events==89);System.out.println("PASS groups=2 ordered_events="+events+" checks="+checks);
    }
}
