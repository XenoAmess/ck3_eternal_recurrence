package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import java.util.List;
import java.util.ArrayList;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.HashMap;
import java.util.Objects;

public final class GlobalReleaseValidation168 {
    private static int checks;
    private static final List<String> nativeInputs = new ArrayList<>();
    private static final List<String> nativeObserved = new ArrayList<>();
    private GlobalReleaseValidation168() { }
    public static void main(String[] args) throws Exception {
        validateUnits();
        Path output = Path.of(args[0]);
        Files.createDirectories(output);
        Files.write(output.resolve("GLOBAL-RELEASE-CASES168.txt"),nativeInputs,StandardCharsets.US_ASCII);
        Files.write(output.resolve("GLOBAL-RELEASE-JAVA168.txt"),nativeObserved,StandardCharsets.US_ASCII);
        validatePipelines();
        forwarding(0);
        forwarding(1);
        System.out.println("4unit/2pipeline/2forwarding; checks=" + checks);
    }
    private static void validateUnits() {
        List<GlobalReleaseApi168.Scenario> scenarios = GlobalReleaseCases168.units();
        check(scenarios.size() == 4, "units size");
        for (GlobalReleaseApi168.Scenario s : scenarios) {
            Probe probe = new Probe(s.tailResult());
            long result = GlobalReleaseWrapper168.apply(probe, s.incoming().rcx(), s.incoming().rdx(), s.incoming().r8(), s.incoming().r9(), s.incoming().rax());
            check(probe.count == s.expectedCalls(), "unit calls " + s.id());
            check(Objects.equals(probe.observed, s.expectedTail()), "unit tail " + s.id());
            check(result == s.expectedResult(), "unit result " + s.id());
            recordUnit(s,result,probe);
            System.out.println(s.id() + " pass");
        }
    }
    private static void validatePipelines() {
        List<GlobalReleaseCases168.Pipeline> pipelines = GlobalReleaseCases168.pipelines();
        check(pipelines.size() == 2, "pipelines size");
        for (GlobalReleaseCases168.Pipeline p : pipelines) {
            ByteMemory memory = new ByteMemory(p.initialWords());
            Map<Long, Byte> before = memory.snapshot();
            Probe probe = new Probe(p.tailResult());
            BoundGlobalRelease168 binding = new BoundGlobalRelease168(rejectOuter(), p.wrapperTarget(), probe);
            BoundReleaseSelector167 selector = new BoundReleaseSelector167(binding, p.selectorTarget());
            long result = ReleaseWrapper167.apply(memory, selector, p.receiver(), p.rows(), p.alignment(), p.incomingR9());
            check(probe.count == p.expectedTailCalls(), "pipeline tail calls " + p.id());
            check(Objects.equals(probe.observed, p.expectedTail()), "pipeline tail " + p.id());
            check(result == p.expectedResult(), "pipeline result " + p.id());
            check(before.equals(memory.snapshot()), "pipeline memory unchanged " + p.id());
            System.out.println(p.id() + " pass");
        }
    }
    private static void recordUnit(GlobalReleaseApi168.Scenario s,long result,Probe probe) {
        GlobalReleaseApi168.Registers in=s.incoming();
        nativeInputs.add(s.id()+"|"+h(in.rcx())+"|"+h(in.rdx())+"|"+h(in.r8())+"|"+h(in.r9())
            +"|"+h(in.rax())+"|"+h(s.tailResult()));
        String suffix=probe.observed==null ? "-|-|-|-|-"
            : h(probe.observed.rcx())+"|"+h(probe.observed.rdx())+"|"+h(probe.observed.r8())
                +"|"+h(probe.observed.r9())+"|"+h(probe.observed.rax());
        nativeObserved.add(s.id()+"|"+h(result)+"|"+probe.count+"|"+suffix);
    }
    private static final class Probe implements GlobalReleaseApi168.Ports {
        private final long result;
        private int count;
        private GlobalReleaseApi168.Registers observed;
        private Probe(long result) { this.result=result; }
        public long tail40ec530(long rcx,long rdx,long r8,long r9,long rax) {
            check(++count == 1,"tail callback bound");
            observed=new GlobalReleaseApi168.Registers(rcx,rdx,r8,r9,rax);
            return result;
        }
    }
    private static ReleaseApi167.Ports rejectOuter() {
        return new ReleaseApi167.Ports() {
            public long slot38(NativeTaskMemory m,long t,long r,long rows,long a,long r9) {
                throw new AssertionError("unexpected outer slot38");
            }
            public long release10(NativeTaskMemory m,long t,long r,long rows,long a,long r9) {
                throw new AssertionError("unexpected outer release10");
            }
        };
    }
    private static void forwarding(int mode) {
        ByteMemory memory=new ByteMemory(List.of(new ReleaseApi167.Word(0x9000L,0x1234L)));
        long selected=0xaa00L;
        long target=mode==0 ? selected : 0xbb00L;
        long expectedReturn=mode==0 ? 0x8000000000000001L : 0xfedcba9876543210L;
        long effect=mode==0 ? 0xcc01L : 0xcc02L;
        java.util.ArrayList<ReleaseApi167.Call> calls=new java.util.ArrayList<>();
        ReleaseApi167.Ports outer=new ReleaseApi167.Ports() {
            public long slot38(NativeTaskMemory m,long t,long r,long rows,long a,long r9) {
                check(mode==0,"forwarding method");
                return accept(ReleaseApi167.Stage.SLOT38,m,t,r,rows,a,r9);
            }
            public long release10(NativeTaskMemory m,long t,long r,long rows,long a,long r9) {
                check(mode==1,"forwarding method");
                return accept(ReleaseApi167.Stage.RELEASE10,m,t,r,rows,a,r9);
            }
            private long accept(ReleaseApi167.Stage stage,NativeTaskMemory m,long t,long r,
                long rows,long a,long r9) {
                check(m==memory,"forwarding memory");
                check(calls.isEmpty(),"forwarding callback bound");
                calls.add(new ReleaseApi167.Call(stage,t,r,rows,a,r9));
                m.writeInt64(0x9000L,effect);
                return expectedReturn;
            }
        };
        GlobalReleaseApi168.Ports noTail=(c,d,e,f,g)->{throw new AssertionError("forward reached tail");};
        BoundGlobalRelease168 binding=new BoundGlobalRelease168(outer,selected,noTail);
        long result=mode==0
            ? binding.slot38(memory,target,0x1111L,0x8000000000000030L,0xffff000000000008L,0x2222L)
            : binding.release10(memory,target,0x1111L,0x8000000000000030L,0xffff000000000008L,0x2222L);
        ReleaseApi167.Stage stage=mode==0 ? ReleaseApi167.Stage.SLOT38 : ReleaseApi167.Stage.RELEASE10;
        check(calls.equals(List.of(new ReleaseApi167.Call(stage,target,0x1111L,
            0x8000000000000030L,0xffff000000000008L,0x2222L))),"forwarded args");
        check(result==expectedReturn,"forwarded return");
        check(memory.snapshot().equals(new ByteMemory(List.of(
            new ReleaseApi167.Word(0x9000L,effect))).snapshot()),"forwarded effects");
        System.out.println("forwarding-"+mode+" pass");
    }
    private static void check(boolean condition,String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static final class ByteMemory implements NativeTaskMemory {
        private final Map<Long,Byte> bytes = new HashMap<>();
        private ByteMemory(List<ReleaseApi167.Word> words) {
            for (ReleaseApi167.Word word : words) {
                for (int i=0;i<8;i++) {
                    if (bytes.putIfAbsent(word.address()+i,(byte)(word.value() >>> (8*i))) != null) {
                        throw new AssertionError("overlapping fixture word");
                    }
                }
            }
        }
        private long read(long address,int width) {
            long value=0L;
            for (int i=0;i<width;i++) {
                Byte one=bytes.get(address+i);
                if (one==null) throw new AssertionError("unmapped read " + h(address+i));
                value |= (one & 255L) << (8*i);
            }
            return value;
        }
        private void write(long address,long value,int width) {
            for (int i=0;i<width;i++) {
                if (!bytes.containsKey(address+i)) throw new AssertionError("unmapped write " + h(address+i));
            }
            for (int i=0;i<width;i++) bytes.put(address+i,(byte)(value >>> (8*i)));
        }
        public long readPointer(long address) { return read(address,8); }
        public int readInt32(long address) { return (int)read(address,4); }
        public int readUnsigned8(long address) { return (int)read(address,1); }
        public void writeInt64(long address,long value) { write(address,value,8); }
        public void writeInt32(long address,int value) { write(address,value,4); }
        public void write8(long address,int value) { write(address,value,1); }
        private Map<Long,Byte> snapshot() { return Map.copyOf(bytes); }
    }
}
