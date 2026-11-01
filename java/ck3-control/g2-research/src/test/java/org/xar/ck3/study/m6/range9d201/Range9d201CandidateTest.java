package org.xar.ck3.study.m6.range9d201;

import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;

/** Bounded software checks; callbacks remain opaque and do not model their memory effects. */
public final class Range9d201CandidateTest {
    private static int cases;
    private static int checks;
    private Range9d201CandidateTest() { }

    private static void check(boolean condition, String reason) {
        ++checks;
        if (!condition) throw new IllegalStateException(reason);
    }
    private static String hex(long value) { return Long.toHexString(value); }
    private static final class Calls implements Range9d201Inputs.Calls {
        private final StringBuilder events;
        Calls(StringBuilder events) { this.events=events; }
        @Override public void first4220aa4(long a,long b,long c,long d) {
            events.append("first4(").append(hex(a)).append(',').append(hex(b)).append(',')
                    .append(hex(c)).append(',').append(hex(d)).append(')');
        }
        @Override public void later4220aa4(long a,long b) {
            events.append("later2(").append(hex(a)).append(',').append(hex(b)).append(')');
        }
    }
    private static void core(String id,long begin,long middle,long end,long entryR9,
                             long expected,String expectedEvents,boolean nullCalls) {
        ++cases;
        StringBuilder events=new StringBuilder();
        long result=Range9d201Candidate.apply(new Range9d201Inputs.Input(begin,middle,end,entryR9),
                nullCalls ? null : new Calls(events));
        check(result==expected,id+" raw64 return");
        check(events.toString().equals(expectedEvents),id+" qualified callback order/arity");
        System.out.println("{\"id\":\""+id+"\",\"rax\":\""+hex(result)
                +"\",\"events\":\""+events+"\"}");
    }
    private static void consumer(int index,String expectedEvents) {
        ++cases;
        RawMemory190 memory=new RawMemory190();
        memory.put64(0x1000,0x2000);
        memory.put32(0x1008,8);
        memory.put32(0x100c,3);
        memory.put64(0x1010,0x4000);
        StringBuilder events=new StringBuilder();
        Copy4Add200Inputs.Calls passthrough=new Copy4Add200Inputs.Calls() {
            @Override public long virtual8(long target,long rcx,long bytes,long align,long r9) {
                throw new IllegalStateException("unexpected within-capacity allocation");
            }
            @Override public void virtual16(long target,long rcx,long base,long align) {
                throw new IllegalStateException("unexpected within-capacity release");
            }
            @Override public void copy4226860(long destination,long source,long bytes) {
                events.append("copy(").append(hex(destination)).append(',').append(hex(source))
                        .append(',').append(hex(bytes)).append(')');
            }
            @Override public void range9d0950(long begin,long middle,long end,long r9) {
                throw new IllegalStateException("known 9D edge incorrectly forwarded");
            }
        };
        Copy4AddWithKnownRange9d201.apply(new Copy4Add200Inputs.Input(0x1000,index,0x3000,0x3008),
                memory,passthrough,new Calls(events));
        check(memory.peek64(0x1000)==0x2000,"consumer base unchanged");
        check(memory.peek32(0x1008)==8,"consumer capacity unchanged");
        check(memory.peek32(0x100c)==5,"consumer actual updated size");
        check(memory.peek64(0x1010)==0x4000,"consumer allocator unchanged");
        check(events.toString().equals(expectedEvents),"consumer literal actual call chain index="+index);
    }
    public static void main(String[] args) {
        core("equal_begin_middle",0x1000,0x1000,0x1020,0x9000,0x1020,"",true);
        core("equal_middle_end",0x1000,0x1020,0x1020,0x9000,0x1000,"",true);
        core("aligned",0x1000,0x1010,0x1020,0x9000,0x1010,
                "first4(1000,1010,1020,9000)later2(1010,1020)later2(1000,1020)",false);
        core("software_misaligned",0x1001,0x1012,0x1039,0x9000,0x1025,
                "first4(1001,1012,1039,9000)later2(1012,1039)later2(1001,1039)",false);
        core("software_negative",0x8000,0x1013,0x1000,0x9000,0x7fec,
                "first4(8000,1013,1000,9000)later2(1013,1000)later2(8000,1000)",false);
        core("software_wrap",0xfffffffffffffff8L,0x7ffffffffffffffcL,0x8000000000000004L,0x9000,0,
                "first4(fffffffffffffff8,7ffffffffffffffc,8000000000000004,9000)"
                        +"later2(7ffffffffffffffc,8000000000000004)later2(fffffffffffffff8,8000000000000004)",false);
        consumer(1,"copy(200c,3000,8)first4(2004,200c,2014,2000)later2(200c,2014)later2(2004,2014)");
        consumer(3,"copy(200c,3000,8)");
        System.out.println("{\"cases\":"+cases+",\"checks\":"+checks+",\"failures\":0}");
    }
}
