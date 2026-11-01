package org.xar.ck3.research.m3.manualfc74binding238;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74FromHandlerBinding238;
import org.xar.ck3.research.m3.terminal214.Terminal4247004Api214;
import org.xar.ck3.research.m3.terminal214.TerminalHandler4247004;

/** Independent finite supplied-storage witness; no native execution. */
public final class Fc74BindingValidation238 {
    private Fc74BindingValidation238() { }
    private static int checks;
    private static int scenes;
    private static int orderedEvents;

    private static void check(boolean condition,String message) {
        checks++;
        if(!condition) throw new AssertionError(message);
    }
    private static long u(int value) { return Integer.toUnsignedLong(value); }
    private record Step(String op,long[] args,long value,Runnable after) { }
    private static Step row(String op,long value,long... args) {
        return new Step(op,args.clone(),value,null);
    }
    private static Step rowAfter(String op,long value,Runnable after,long... args) {
        return new Step(op,args.clone(),value,after);
    }
    private static final class Ram implements Terminal4247004Api214.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final Deque<Step> expected=new ArrayDeque<>();
        private int consumed;
        void expect(Step... rows) { expected.addAll(Arrays.asList(rows)); }
        Step take(String op,long... args) {
            Step next=expected.pollFirst();
            check(next!=null,"unexpected "+op+Arrays.toString(args));
            check(next.op().equals(op)&&Arrays.equals(next.args(),args),
                    "expected "+next.op()+Arrays.toString(next.args())+" received "+op+Arrays.toString(args));
            consumed++;
            return next;
        }
        private void rawWrite(long address,long value,int width) {
            for(int i=0;i<width;i++) bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        private long rawRead(long address,int width) {
            long value=0;
            for(int i=0;i<width;i++) {
                Byte actual=bytes.get(address+i);
                if(actual==null) throw new AssertionError("unseeded byte "+Long.toUnsignedString(address+i,16));
                value|=(long)(actual&255)<<(8*i);
            }
            return value;
        }
        void seed8(long address,int value) { rawWrite(address,value,1); }
        void seed32(long address,int value) { rawWrite(address,u(value),4); }
        void seed64(long address,long value) { rawWrite(address,value,8); }
        int peek8(long address) { return (int)rawRead(address,1); }
        int peek32(long address) { return (int)rawRead(address,4); }
        long peek64(long address) { return rawRead(address,8); }
        Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
        private void effect(String op,long address,long value,int width) {
            Step next=take(op,address);
            check(next.value()==value,"opaque effect value "+op);
            rawWrite(address,value,width);
        }
        void effect32(long address,int value) { effect("E32",address,u(value),4); }
        void effect64(long address,long value) { effect("E64",address,value,8); }
        @Override public int readUnsigned8(long address) {
            Step next=take("R8",address);int value=(int)rawRead(address,1);
            check(next.value()==value,"R8 value");return value;
        }
        @Override public void write8(long address,int value) {
            Step next=take("W8",address);check(next.value()==(value&255),"W8 value");rawWrite(address,value,1);
        }
        @Override public long readPointer(long address) {
            Step next=take("R64",address);long value=rawRead(address,8);
            check(next.value()==value,"R64 value");return value;
        }
        @Override public int readInt32(long address) {
            Step next=take("R32",address);int value=(int)rawRead(address,4);
            check(next.value()==u(value),"R32 unsigned encoded tuple");return value;
        }
        @Override public void writeInt32(long address,int value) {
            Step next=take("W32",address);check(next.value()==u(value),"W32 value");rawWrite(address,u(value),4);
        }
        @Override public void writeInt64(long address,long value) {
            Step next=take("W64",address);check(next.value()==value,"W64 value");rawWrite(address,value,8);
        }
        void finish(String label) {
            check(expected.isEmpty(),label+" unused events="+expected.size());
            scenes++;orderedEvents+=consumed;
        }
    }
    private static final class ScriptPorts implements Fc74Api238.Ports {
        private final Ram ram;
        ScriptPorts(Ram ram) { this.ram=ram; }
        private long call(NativeTaskMemory memory,String op,long... args) {
            check(memory==ram,"identical Memory for "+op);
            Step next=ram.take(op,args);
            if(next.after()!=null) next.after().run();
            return next.value();
        }
        @Override public int callIat43da738(NativeTaskMemory memory,long site,long target,int ecx) {
            return (int)call(memory,"P738",site,target,u(ecx));
        }
        @Override public long call424e900(NativeTaskMemory memory,long site,int ecx) {
            return call(memory,"PE900",site,u(ecx));
        }
        @Override public int call424e948(NativeTaskMemory memory,long site,int ecx,long rdx) {
            return (int)call(memory,"PE948",site,u(ecx),rdx);
        }
        @Override public long call424e2ec(NativeTaskMemory memory,long site,long rcx,long rdx) {
            return call(memory,"PE2EC",site,rcx,rdx);
        }
        @Override public void call424e364(NativeTaskMemory memory,long site,long rcx) {
            call(memory,"PE364",site,rcx);
        }
        @Override public void call424f8a8(NativeTaskMemory memory,long site,long rcx) {
            call(memory,"PF8A8",site,rcx);
        }
        @Override public void callIat43da420(NativeTaskMemory memory,long site,long target,int ecx) {
            call(memory,"P420",site,target,u(ecx));
        }
    }
    private static final class Fallback implements Terminal4247004Api214.Ports {
        private final Ram trace;
        private final Terminal4247004Api214.Memory expectedMemory;
        private final Terminal4247004Api214.DispatchR8 expectedR8;
        private final Terminal4247004Api214.DispatchRdx expectedRdx;
        Fallback(Ram trace,Terminal4247004Api214.Memory expectedMemory,
                Terminal4247004Api214.DispatchR8 expectedR8,Terminal4247004Api214.DispatchRdx expectedRdx) {
            this.trace=trace;this.expectedMemory=expectedMemory;this.expectedR8=expectedR8;this.expectedRdx=expectedRdx;
        }
        private long call(Terminal4247004Api214.Memory memory,String op,long... args) {
            check(memory==expectedMemory,"fallback original Memory for "+op);
            Step next=trace.take(op,args);
            if(next.after()!=null) next.after().run();
            return next.value();
        }
        @Override public long call424fc74(Terminal4247004Api214.Memory memory,long site,int ecx) {
            throw new AssertionError("active FC74 delegated to fallback");
        }
        @Override public long call423b18c(Terminal4247004Api214.Memory memory,long site) { return call(memory,"FERR",site); }
        @Override public void call4232a50(Terminal4247004Api214.Memory memory,long site) { call(memory,"FABORT",site); }
        @Override public void call4247ffc(Terminal4247004Api214.Memory memory,long site,int ecx) { call(memory,"FLOCK",site,u(ecx)); }
        @Override public long call424faf8(Terminal4247004Api214.Memory memory,long site) { return call(memory,"FFAF8",site); }
        @Override public void call4248050(Terminal4247004Api214.Memory memory,long site,int ecx) { call(memory,"FUNLOCK",site,u(ecx)); }
        @Override public void call4242354(Terminal4247004Api214.Memory memory,long site,int ecx) { call(memory,"FTAIL",site,u(ecx)); }
        @Override public void callIndirectR8(Terminal4247004Api214.Memory memory,Terminal4247004Api214.DispatchR8 call) {
            check(call==expectedR8,"same DispatchR8 object");
            call(memory,"FR8",call.siteRva(),call.targetSlotAddress(),call.targetBits(),call.handlerBits(),u(call.ecxBits()),u(call.edxBits()));
        }
        @Override public void callIndirectRdx(Terminal4247004Api214.Memory memory,Terminal4247004Api214.DispatchRdx call) {
            check(call==expectedRdx,"same DispatchRdx object");
            call(memory,"FRDX",call.siteRva(),call.targetSlotAddress(),call.targetBits(),call.handlerBits(),u(call.ecxBits()));
        }
    }
    private static void rejected(Runnable work,String label) {
        try { work.run(); }
        catch(IllegalArgumentException expected) { checks++;return; }
        throw new AssertionError(label+" not rejected");
    }
    private static void sameException(Runnable work,RuntimeException expected,String label) {
        try { work.run(); }
        catch(RuntimeException actual) { check(actual==expected,label+" exception identity");return; }
        throw new AssertionError(label+" no exception");
    }

    private static void actualHandler238() {
        Ram ram=new Ram();
        long base=0x0000000010000000L,H=0x0000000000008000L,B=H-0x68L;
        long header=0x8123456789ABC000L,table=0x0000000000004100L;
        ram.seed64(B+0x70,0xA0A1A2A3A4A5A6A7L);
        ram.seed64(B+0x78,0x1234567889ABCDEFL);
        ram.seed64(B+0x80,0xDEADBEEFCAFEBABEL);
        ram.seed8(H+7,0xA5);ram.seed8(H+0x20,0x5A);
        ram.seed64(0x00000000143DA738L,0xA111222233334444L);
        ram.seed64(0x00000000143DA420L,0xB111222233334444L);
        ram.seed64(0x000000001542F328L,0xBEEFCAFE00000007L);
        ram.seed64(header,0x0000000000003100L);
        ram.seed8(header-1,0x69);ram.seed8(header+8,0x96);
        ram.seed64(0x00000000144268B0L,1L);
        ram.seed32(table+4,4);ram.seed64(table+8,1L);
        ram.seed8(table+3,0x9A);ram.seed8(table+16,0xA9);
        ScriptPorts child=new ScriptPorts(ram);
        Fallback fallback=new Fallback(ram,ram,null,null);
        Terminal4247004Api214.Ports bound=Fc74FromHandlerBinding238.bind(base,ram,child,fallback);
        ram.expect(
            row("R32",0x0000000089ABCDEFL,0x0000000000008010L),
            row("W32",0x0000000000000000L,0x0000000000008010L),
            row("W8",0x0000000000000001L,0x0000000000008008L),
            row("R64",0xA111222233334444L,0x00000000143DA738L),
            row("P738",0x00000000FEDCBA98L,0x000000000424FC83L,0xA111222233334444L,0x0000000000000004L),
            row("R32",0x0000000000000007L,0x000000001542F328L),
            row("PE900",0x8123456789ABC000L,0x000000000424FC96L,0x0000000000000007L),
            row("R64",0xB111222233334444L,0x00000000143DA420L),
            rowAfter("P420",0L,()->{ram.effect64(header,table);},0x000000000424FD21L,0xB111222233334444L,0x00000000FEDCBA98L),
            row("E64",0x0000000000004100L,0x8123456789ABC000L),
            row("R64",0x0000000000004100L,0x8123456789ABC000L),
            row("R64",0x0000000000000001L,0x00000000144268B0L),
            row("R32",0x0000000000000004L,0x0000000000004104L),
            row("W8",0x0000000000000000L,0x0000000000008008L),
            row("R64",0xDEADBEEFCAFEBABEL,0x0000000000008018L),
            row("W64",0x0000000000000000L,0x0000000000008018L),
            row("R64",0x0000000000000001L,0x0000000000004108L)
        );
        Terminal4247004Api214.Outcome returned=TerminalHandler4247004.execute(ram,bound,
                new Terminal4247004Api214.Input(base,4,new Terminal4247004Api214.Scratch(H)));
        check(returned instanceof Terminal4247004Api214.NormalReturn,"actual214 normalreturn");
        check(((Terminal4247004Api214.NormalReturn)returned).raxBits()==0L,"actual214 handler1 result0");
        check(ram.peek64(B+0x70)==0xA0A1A2A3A4A5A600L,"BYTE writes preserve upperseven bytes");
        check(ram.peek64(B+0x78)==0x1234567800000000L,"DWORD RMW preserves upperfour bytes");
        check(ram.peek64(B+0x80)==0L,"QWORD RMW zero");
        check(ram.peek8(H+7)==0xA5&&ram.peek8(H+0x20)==0x5A,"supplied business scratch outsidecanaries");
        check(ram.peek64(header)==table,"actualshared child mutation reaches outerheaderload");
        check(ram.peek8(header-1)==0x69&&ram.peek8(header+8)==0x96,"header exact8byte change");
        check(ram.peek32(table+4)==4&&ram.peek64(table+8)==1L,"foundrow unchanged");
        check(ram.peek8(table+3)==0x9A&&ram.peek8(table+16)==0xA9,"rowboundaries unchanged");
        check(ram.peek64(0x000000001542F328L)==0xBEEFCAFE00000007L,"index source32read leaves fullcellunchanged");
        check(ram.peek64(0x00000000143DA738L)==0xA111222233334444L&&ram.peek64(0x00000000143DA420L)==0xB111222233334444L,"bothIATcellsunchanged");
        check(ram.peek64(0x00000000144268B0L)==1L,"outercountunchanged");
        ram.finish("actual214bindFC74newedge");
    }
    private static void bindingProtocol238() {
        long moduleBase = 0x40000000L;
        Ram capturedMemory = new Ram();
        Ram traceRam = capturedMemory;

        Ram foreignMemory = new Ram();
        foreignMemory.seed64(0x5500L,0xA1B2C3D4E5F60718L);
        Map<Long,Byte> foreignBefore=foreignMemory.snapshot();

        Terminal4247004Api214.DispatchR8 r8 = new Terminal4247004Api214.DispatchR8(0x4247218L,0xFFFFFFFF01020304L,0x8123456789ABCDEFL,0x7766554433221100L,0x80000005,0xFEDCBA98);
        Terminal4247004Api214.DispatchRdx rdx = new Terminal4247004Api214.DispatchRdx(0x4247229L,0x9999AAAABBBBCCCCL,0x0123456789ABCDEFL,0xEEDDCCBBAA998877L,0xFFFFFFFF);

        Fallback fallback = new Fallback(traceRam, foreignMemory, r8, rdx);
        ScriptPorts child = new ScriptPorts(capturedMemory);

        Terminal4247004Api214.Ports boundPorts = Fc74FromHandlerBinding238.bind(moduleBase, capturedMemory, child, fallback);

        rejected(() -> boundPorts.call424fc74(foreignMemory, 0x424707DL, 0), "Wrong memory rejected");
        check(capturedMemory.snapshot().isEmpty(), "Captured memory unchanged by wrong memory guard");
        check(traceRam.snapshot().isEmpty(), "Trace memory unchanged by wrong memory guard");

        rejected(() -> boundPorts.call424fc74(capturedMemory, 0x4247000L, 0), "Wrong site rejected");
        check(capturedMemory.snapshot().isEmpty(), "Captured memory unchanged by wrong site guard");
        check(traceRam.snapshot().isEmpty(), "Trace memory unchanged by wrong site guard");

        check(capturedMemory.consumed==0&&traceRam.consumed==0&&foreignMemory.consumed==0,"guards before any event");
        check(foreignMemory.snapshot().equals(foreignBefore)&&foreignMemory.expected.isEmpty(),"foreign guard bytes/queue unchanged");
        long iatTarget = 0xC111222233334444L;
        capturedMemory.seed64(moduleBase + 0x43DA738L, iatTarget);
        Map<Long,Byte> beforeActive=capturedMemory.snapshot();

        RuntimeException childEx = new RuntimeException("Child Exception");
        capturedMemory.expect(row("R64",iatTarget,moduleBase+0x43DA738L), rowAfter("P738", 0L, () -> { throw childEx; }, 0x424FC83L, iatTarget, u(0xFEEDC0DE)));

        sameException(() -> boundPorts.call424fc74(capturedMemory, 0x424707DL, 0xFEEDC0DE), childEx, "Active FC74 child exception propagation");

        check(capturedMemory.consumed==2 && capturedMemory.expected.isEmpty(), "exact R64 plus childthrow prefix only");
        check(capturedMemory.snapshot().equals(beforeActive), "Active child throw prefix changes no bytes");

        traceRam.expect(row("FERR", 0x8123456789ABCDEFL, 0x1111222233334444L));
        long res1 = boundPorts.call423b18c(foreignMemory, 0x1111222233334444L);
        check(res1 == 0x8123456789ABCDEFL, "call423b18c return");

        traceRam.expect(row("FABORT", 0L, 0x1111222233334445L));
        boundPorts.call4232a50(foreignMemory, 0x1111222233334445L);

        traceRam.expect(row("FLOCK", 0L, 0x1111222233334446L, u(0x89ABCDEF)));
        boundPorts.call4247ffc(foreignMemory, 0x1111222233334446L, 0x89ABCDEF);

        traceRam.expect(row("FFAF8", 0xFEDCBA9876543210L, 0x1111222233334447L));
        long res2 = boundPorts.call424faf8(foreignMemory, 0x1111222233334447L);
        check(res2 == 0xFEDCBA9876543210L, "call424faf8 return");

        traceRam.expect(row("FUNLOCK", 0L, 0x1111222233334448L, u(0xFEDCBA98)));
        boundPorts.call4248050(foreignMemory, 0x1111222233334448L, 0xFEDCBA98);

        traceRam.expect(row("FTAIL", 0L, 0x1111222233334449L, u(0x80000001)));
        boundPorts.call4242354(foreignMemory, 0x1111222233334449L, 0x80000001);

        traceRam.expect(row("FR8", 0L, 0x4247218L,0xFFFFFFFF01020304L,0x8123456789ABCDEFL,0x7766554433221100L,u(0x80000005),u(0xFEDCBA98)));
        boundPorts.callIndirectR8(foreignMemory, r8);

        traceRam.expect(row("FRDX", 0L, 0x4247229L,0x9999AAAABBBBCCCCL,0x0123456789ABCDEFL,0xEEDDCCBBAA998877L,u(0xFFFFFFFF)));
        boundPorts.callIndirectRdx(foreignMemory, rdx);

        RuntimeException fallbackEx = new RuntimeException("Fallback Exception");

        traceRam.expect(rowAfter("FERR", 0L, () -> { throw fallbackEx; }, 0x1111222233334444L));
        sameException(() -> boundPorts.call423b18c(foreignMemory, 0x1111222233334444L), fallbackEx, "call423b18c exception");

        traceRam.expect(rowAfter("FABORT", 0L, () -> { throw fallbackEx; }, 0x1111222233334445L));
        sameException(() -> boundPorts.call4232a50(foreignMemory, 0x1111222233334445L), fallbackEx, "call4232a50 exception");

        traceRam.expect(rowAfter("FLOCK", 0L, () -> { throw fallbackEx; }, 0x1111222233334446L, u(0x89ABCDEF)));
        sameException(() -> boundPorts.call4247ffc(foreignMemory, 0x1111222233334446L, 0x89ABCDEF), fallbackEx, "call4247ffc exception");

        traceRam.expect(rowAfter("FFAF8", 0L, () -> { throw fallbackEx; }, 0x1111222233334447L));
        sameException(() -> boundPorts.call424faf8(foreignMemory, 0x1111222233334447L), fallbackEx, "call424faf8 exception");

        traceRam.expect(rowAfter("FUNLOCK", 0L, () -> { throw fallbackEx; }, 0x1111222233334448L, u(0xFEDCBA98)));
        sameException(() -> boundPorts.call4248050(foreignMemory, 0x1111222233334448L, 0xFEDCBA98), fallbackEx, "call4248050 exception");

        traceRam.expect(rowAfter("FTAIL", 0L, () -> { throw fallbackEx; }, 0x1111222233334449L, u(0x80000001)));
        sameException(() -> boundPorts.call4242354(foreignMemory, 0x1111222233334449L, 0x80000001), fallbackEx, "call4242354 exception");

        traceRam.expect(rowAfter("FR8", 0L, () -> { throw fallbackEx; }, 0x4247218L,0xFFFFFFFF01020304L,0x8123456789ABCDEFL,0x7766554433221100L,u(0x80000005),u(0xFEDCBA98)));
        sameException(() -> boundPorts.callIndirectR8(foreignMemory, r8), fallbackEx, "callIndirectR8 exception");

        traceRam.expect(rowAfter("FRDX", 0L, () -> { throw fallbackEx; }, 0x4247229L,0x9999AAAABBBBCCCCL,0x0123456789ABCDEFL,0xEEDDCCBBAA998877L,u(0xFFFFFFFF)));
        sameException(() -> boundPorts.callIndirectRdx(foreignMemory, rdx), fallbackEx, "callIndirectRdx exception");

        check(capturedMemory.snapshot().equals(beforeActive),"all passive methods leave capturedbytes unchanged");
        check(foreignMemory.snapshot().equals(foreignBefore)&&foreignMemory.consumed==0&&foreignMemory.expected.isEmpty(),"passive originalforeignMemory has no extra touch");
        capturedMemory.finish("Binding Protocol");
    }

    public static void main(String[] args) {
        actualHandler238();bindingProtocol238();
        System.out.println("FC74_BINDING238_PASS scenes="+scenes+" orderedEvents="+orderedEvents+" mixedChecks="+checks+" Native=0 Game=0");
    }
}
