package org.xar.ck3.study.m6.copy4add200;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;

/** Bounded source-derived DATA using explicitly opaque callees, never a game runner. */
public final class Copy4Add200CandidateTest {
    private static final long H=0x1000,O=0x2000,N=0x3000,S=0x4000,A=0x5000;
    private static final long AA=0x6000,VA=0x6100,TA=0x6200,FA=0x6300;
    private static final long AB=0x7000,VB=0x7100,TB=0x7200,FB=0x7300;
    private static int checks;
    private static final List<String> RAW_ROWS=new ArrayList<>();
    private Copy4Add200CandidateTest() { }
    private record Event(String kind,long target,List<Long> args) { }
    private record Header(long base,int capacity,int size,long allocator) { }
    private static Event e(String kind,long target,long... args) {
        List<Long> values=new ArrayList<>();for(long value:args)values.add(value);
        return new Event(kind,target,List.copyOf(values));
    }
    private static void check(boolean value,String reason) {
        ++checks;if(!value)throw new AssertionError(reason);
    }
    private static final class Memory extends RawMemory190 implements Range8c194Inputs.Memory {
        final List<String> accesses=new ArrayList<>();
        @Override protected void observed(Access access) {
            accesses.add(access.operation()+":"+Long.toHexString(access.address()));
        }
        @Override public Range8c194Inputs.Word16 read16(long address) {
            return new Range8c194Inputs.Word16(peek64(address),peek64(address+8));
        }
        @Override public void write16(long address,Range8c194Inputs.Word16 word) {
            put64(address,word.lowRaw64());put64(address+8,word.highRaw64());
        }
    }
    private static void allocators(Memory memory) {
        memory.put64(AA,VA);memory.put64(VA+8,TA);memory.put64(VA+16,FA);
        memory.put64(AB,VB);memory.put64(VB+8,TB);memory.put64(VB+16,FB);
    }
    private static void header(Memory memory,long address,long base,int cap,int size,long allocator) {
        memory.put64(address,base);memory.put32(address+8,cap);memory.put32(address+12,size);memory.put64(address+16,allocator);
    }
    private static Header header(Memory memory,long address) {
        return new Header(memory.peek64(address),memory.peek32(address+8),memory.peek32(address+12),memory.peek64(address+16));
    }
    private static String pointerRole(long value) {
        if(value==0)return "NULL";
        if(value==AA)return "AA";if(value==AB)return "AB";
        long[] bases={O,N,S,A};String[] names={"O","N","S","ALT"};
        for(int i=0;i<bases.length;++i)if(value>=bases[i] && value-bases[i]<128)return names[i]+"+"+(value-bases[i]);
        throw new AssertionError("unqualified pointer role "+Long.toHexString(value));
    }
    private static String targetRole(long value) {
        if(value==0)return "";if(value==TA)return "TA";if(value==FA)return "FA";if(value==TB)return "TB";if(value==FB)return "FB";
        throw new AssertionError("unqualified target");
    }
    private static String rawRow(String id,Header header,List<Event> events) {
        List<String> calls=new ArrayList<>();
        for(Event event:events) {
            List<String> args=new ArrayList<>();
            for(int i=0;i<event.args().size();++i) {
                boolean pointer=switch(event.kind()) { case "a" -> i==0 || i==3;case "f" -> i<2;case "c" -> i<2;case "r" -> true;default -> throw new AssertionError("unknown kind"); };
                long value=event.args().get(i);
                args.add("\""+(pointer?pointerRole(value):String.format("0x%016x",value))+"\"");
            }
            calls.add("{\"kind\":\""+event.kind()+"\",\"target\":\""+targetRole(event.target())+"\",\"args\":["+String.join(",",args)+"]}");
        }
        String state=header==null?"null":"{\"base\":\""+pointerRole(header.base())+"\",\"capacity\":"+header.capacity()+",\"size\":"+header.size()+",\"allocator\":\""+pointerRole(header.allocator())+"\"}";
        return "{\"id\":\""+id+"\",\"header\":"+state+",\"calls\":["+String.join(",",calls)+"]}";
    }
    private static final class Calls implements Copy4Add200Inputs.Calls {
        final Memory memory;final long header;final int mutation;
        final List<Event> events=new ArrayList<>();
        int copies;Header beforeRelease;Integer sizeAtRange;
        Calls(Memory memory,long header,int mutation) { this.memory=memory;this.header=header;this.mutation=mutation; }
        @Override public long virtual8(long target,long rcx,long bytes,long alignment,long r9) {
            events.add(e("a",target,rcx,bytes,alignment,r9));return N;
        }
        @Override public void virtual16(long target,long rcx,long oldBase,long alignment) {
            events.add(e("f",target,rcx,oldBase,alignment));beforeRelease=header(memory,header);
        }
        @Override public void copy4226860(long destination,long source,long bytes) {
            events.add(e("c",0,destination,source,bytes));++copies;
            if(mutation==1 && copies==1) { memory.put64(header,A);memory.put32(header+12,4); }
            if(mutation==2 && copies==2) {
                memory.put64(header,A);memory.put32(header+12,5);memory.put64(header+16,AB);
            }
        }
        @Override public void range9d0950(long begin,long middle,long end,long base) {
            events.add(e("r",0,begin,middle,end,base));sizeAtRange=memory.peek32(header+12);
        }
    }
    private static void core(String id,int cap,int size,long old,int mutation,int count,long index,
                             Header expected,List<Event> expectedEvents) {
        Memory memory=new Memory();allocators(memory);header(memory,H,old,cap,size,AA);
        Calls calls=new Calls(memory,H,mutation);
        Copy4Add200Candidate.apply(new Copy4Add200Inputs.Input(H,index,S,S+4L*count),memory,calls);
        check(calls.events.equals(expectedEvents),id+" exact qualified callbacks "+calls.events);
        check(header(memory,H).equals(expected),id+" final header");
        if(!id.endsWith("software_only"))RAW_ROWS.add(rawRow(id,header(memory,H),calls.events));
        if(mutation==1) {
            check(Integer.valueOf(6).equals(calls.sizeAtRange),"size committed before range callback");
            check(memory.accesses.equals(List.of("r32:100c","r32:1008","r64:1000","r32:100c","r64:1000","w32:100c")),"no-growth exact fresh read/store order");
        } else {
            Header before=mutation==2 ? new Header(A,cap,5,AB) : new Header(old,cap,size,AA);
            check(before.equals(calls.beforeRelease),id+" release precedes saved-header writes");
        }
    }
    private static final Range8c194Inputs.Calls NO_RANGE16=new Range8c194Inputs.Calls() {
        @Override public long virtual8(long target,long rcx,long rdx,long r8,long r9) { throw new AssertionError("unexpected range16 allocation"); }
        @Override public void virtual16(long target,long rcx,long rdx,long r8,long r9) { throw new AssertionError("unexpected range16 release"); }
        @Override public void direct8f8550(long rcx,long rdx,long r8,long r9) { throw new AssertionError("unreachable198 must not be forced"); }
    };
    private static void upper(boolean alias) {
        long d=0x9000,s=alias?d:0xA000,image=0x10000000,allocator=image+0x54de268L;
        Memory memory=new Memory();allocators(memory);
        memory.put32(s+8,0x81234567);memory.put64(s+0x10,0xB000);memory.put32(s+0x1c,0);
        memory.put64(s+0x28,S);memory.put32(s+0x34,2);memory.put32(s+0x40,0x76543210);memory.put8(s+0x44,0xA5);
        memory.put64(allocator,VA);
        Calls calls=new Calls(memory,d+0x28,0);
        long returned=Element172WithKnownCopy4Add200.assign(new Element172Inputs.Input(d,s,image),memory,NO_RANGE16,calls);
        check(returned==d,"upper preserves raw64 RAX");
        check(memory.peek64(d)==image+0x45648a0L,"upper original vtable");
        check(memory.peek32(d+8)==0x81234567,"upper field08 bits");
        check(memory.peek32(d+0x40)==0x76543210 && memory.peek8(d+0x44)==0xA5,"upper fresh tail bits");
        check(header(memory,d+0x10).equals(new Header(0,0,0,image+0x54de260L)),"upper actual range16 remains initialized empty");
        if(alias) {
            check(calls.events.isEmpty(),"selfalias sourcecount4 cleared before read");
            check(header(memory,d+0x28).equals(new Header(0,0,0,allocator)),"selfalias actual copy4 empty");
        } else {
            check(calls.events.equals(List.of(e("a",TA,allocator,8,4,S+8),e("c",0,N,0,0),e("c",0,N,S,8),e("c",0,N+8,0,0),e("f",FA,allocator,0,4))),"real172 through ADDgrowth callback sequence");
            check(header(memory,d+0x28).equals(new Header(N,2,2,allocator)),"upper newcopy4 header");
            check(new Header(0,0,0,allocator).equals(calls.beforeRelease),"upper release before final header install");
        }
    }
    public static void main(String[] args) {
        Memory empty=new Memory();Calls none=new Calls(empty,0,0);
        Copy4Add200Candidate.apply(new Copy4Add200Inputs.Input(0,0,0,0),empty,none);
        check(empty.accesses.isEmpty() && none.events.isEmpty(),"empty NULL no memory or callback");
        RAW_ROWS.add(rawRow("empty_null",null,none.events));
        core("within_fresh",8,2,O,1,2,1,new Header(A,8,6,AA),List.of(e("c",0,O+8,S,8),e("r",0,A+4,A+16,A+24,A)));
        core("growth_null",0,0,0,0,2,0,new Header(N,2,2,AA),List.of(e("a",TA,AA,8,4,S+8),e("c",0,N,0,0),e("c",0,N,S,8),e("c",0,N+8,0,0),e("f",FA,AA,0,4)));
        core("growth_tail",2,2,O,0,2,1,new Header(N,4,4,AA),List.of(e("a",TA,AA,16,4,S+8),e("c",0,N,O,4),e("c",0,N+4,S,8),e("c",0,N+12,O+4,4),e("f",FA,AA,O,4)));
        core("growth_fresh",2,2,O,2,2,1,new Header(N,4,4,AB),List.of(e("a",TA,AA,16,4,S+8),e("c",0,N,O,4),e("c",0,N+4,S,8),e("c",0,N+12,A+4,16),e("f",FB,AB,A,4)));
        core("growth_float_invalid_software_only",1431655808,1431655809,O,0,1,0,new Header(N,1431655810,1431655810,AA),List.of(e("a",TA,AA,5726623240L,4,S+4),e("c",0,N,O,0),e("c",0,N,S,4),e("c",0,N+4,O,5726623236L),e("f",FA,AA,O,4)));
        upper(false);upper(true);
        System.out.println("{\"rows\":["+String.join(",",RAW_ROWS)+"]}");
        System.err.println("Copy4Add200CandidateTest cases=8 checks="+checks+" failures=0; opaque-callee DATA only");
    }
}
