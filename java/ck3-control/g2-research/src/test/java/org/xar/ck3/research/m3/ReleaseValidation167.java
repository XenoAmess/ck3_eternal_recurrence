package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;

/** Owner takeover after two complete but source/API-invalid candidates. */
public final class ReleaseValidation167 {
    private static int checks;
    private ReleaseValidation167() { }

    public static void main(String[] args) throws Exception {
        Path out = Path.of(args[0]);
        Files.createDirectories(out);
        List<String> inputs = new ArrayList<>();
        List<String> observed = new ArrayList<>();
        check(ReleaseCases167.units().size() == 4, "unit count");
        check(ReleaseCases167.consumers().size() == 2, "consumer count");
        for (ReleaseApi167.Scenario scenario : ReleaseCases167.units()) {
            inputs.add(inputLine(scenario));
            observed.add(run(scenario, false));
        }
        Files.write(out.resolve("RELEASE-CASES167.txt"), inputs, StandardCharsets.US_ASCII);
        Files.write(out.resolve("RELEASE-JAVA167.txt"), observed, StandardCharsets.US_ASCII);
        for (ReleaseApi167.Scenario scenario : ReleaseCases167.consumers()) run(scenario, true);
        for (int mode = 0; mode < 3; mode++) forwarding(mode);
        System.out.println("4unit/2consumer/3forwarding; checks=" + checks);
    }

    private static String run(ReleaseApi167.Scenario scenario, boolean bound) {
        ByteMemory memory = new ByteMemory(scenario.initialWords());
        List<ReleaseApi167.Call> calls = new ArrayList<>();
        ReleaseApi167.Ports outer = new ReleaseApi167.Ports() {
            public long slot38(NativeTaskMemory observedMemory, long target,
                long receiver, long rows, long alignment, long r9) {
                check(!bound, "selected slot38 reached outer");
                check(observedMemory == memory, "slot38 memory identity");
                check(calls.size() < 2, "slot38 callback bound");
                calls.add(new ReleaseApi167.Call(ReleaseApi167.Stage.SLOT38,
                    target,receiver,rows,alignment,r9));
                for (ReleaseApi167.Word effect : scenario.firstEffects()) {
                    memory.writeInt64(effect.address(), effect.value());
                }
                return scenario.firstReturn();
            }
            public long release10(NativeTaskMemory observedMemory, long target,
                long receiver, long rows, long alignment, long r9) {
                check(observedMemory == memory, "release10 memory identity");
                check(calls.size() < 2, "release10 callback bound");
                calls.add(new ReleaseApi167.Call(ReleaseApi167.Stage.RELEASE10,
                    target,receiver,rows,alignment,r9));
                return scenario.releaseReturn();
            }
        };
        ReleaseApi167.Ports ports = outer;
        if (bound) {
            long selected = memory.readPointer(memory.readPointer(scenario.receiver()) + 0x38L);
            ports = new BoundReleaseSelector167(outer, selected);
        }
        long result = ReleaseWrapper167.apply(memory, ports, scenario.receiver(),
            scenario.rows(), scenario.alignment(), scenario.incomingR9());
        check(calls.equals(scenario.expectedCalls()), scenario.id() + " call transcript");
        check(result == scenario.expectedResult(), scenario.id() + " result");
        check(memory.snapshot().equals(new ByteMemory(scenario.expectedFinalWords()).snapshot()),
            scenario.id() + " full memory");
        StringJoiner observedWords = new StringJoiner(",");
        for (ReleaseApi167.Word word : scenario.initialWords()) {
            observedWords.add(h(word.address()) + ":" + h(memory.readPointer(word.address())));
        }
        System.out.println(scenario.id() + " pass");
        return scenario.id() + "|" + h(result) + "|" + calls(calls) + "|"
            + (scenario.initialWords().isEmpty() ? "-" : observedWords.toString());
    }

    private static void forwarding(int mode) {
        ByteMemory memory = new ByteMemory(List.of(new ReleaseApi167.Word(0x9000L,0xaaaaL)));
        long selected = 0xabc0L;
        long target = mode == 2 ? selected : 0xdef0L;
        long expectedReturn = mode == 0 ? 0x8000000000000001L
            : mode == 1 ? 0xfedcba9876543210L : 0x1122334455667788L;
        long expectedEffect = mode == 0 ? 0xb001L : mode == 1 ? 0xb002L : 0xb003L;
        List<ReleaseApi167.Call> actual = new ArrayList<>();
        ReleaseApi167.Ports outer = new ReleaseApi167.Ports() {
            public long slot38(NativeTaskMemory observedMemory, long observedTarget,
                long receiver, long rows, long alignment, long r9) {
                check(mode == 0, "wrong forwarding slot");
                return accept(ReleaseApi167.Stage.SLOT38,observedMemory,observedTarget,
                    receiver,rows,alignment,r9);
            }
            public long release10(NativeTaskMemory observedMemory, long observedTarget,
                long receiver, long rows, long alignment, long r9) {
                check(mode != 0, "wrong forwarding release");
                return accept(ReleaseApi167.Stage.RELEASE10,observedMemory,observedTarget,
                    receiver,rows,alignment,r9);
            }
            private long accept(ReleaseApi167.Stage stage,NativeTaskMemory observedMemory,
                long observedTarget,long receiver,long rows,long alignment,long r9) {
                check(observedMemory == memory, "forwarding memory identity");
                check(actual.isEmpty(), "forwarding callback bound");
                actual.add(new ReleaseApi167.Call(stage,observedTarget,receiver,rows,alignment,r9));
                observedMemory.writeInt64(0x9000L,expectedEffect);
                return expectedReturn;
            }
        };
        BoundReleaseSelector167 binding = new BoundReleaseSelector167(outer,selected);
        long result = mode == 0
            ? binding.slot38(memory,target,0x1234L,0xffff0000aabbccddL,0x8000000000000010L,0x55667788L)
            : binding.release10(memory,target,0x1234L,0xffff0000aabbccddL,0x8000000000000010L,0x55667788L);
        ReleaseApi167.Stage stage = mode == 0 ? ReleaseApi167.Stage.SLOT38 : ReleaseApi167.Stage.RELEASE10;
        check(actual.equals(List.of(new ReleaseApi167.Call(stage,target,0x1234L,
            0xffff0000aabbccddL,0x8000000000000010L,0x55667788L))), "forwarded arguments");
        check(result == expectedReturn, "forwarded return");
        check(memory.snapshot().equals(new ByteMemory(List.of(
            new ReleaseApi167.Word(0x9000L,expectedEffect))).snapshot()), "forwarded effects");
        System.out.println("forwarding-" + mode + " pass");
    }

    private static void check(boolean condition,String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private static String h(long value) { return Long.toUnsignedString(value,16); }
    private static String words(List<ReleaseApi167.Word> words) {
        if (words.isEmpty()) return "-";
        StringJoiner result = new StringJoiner(",");
        for (ReleaseApi167.Word word : words) result.add(h(word.address()) + ":" + h(word.value()));
        return result.toString();
    }
    private static String calls(List<ReleaseApi167.Call> calls) {
        if (calls.isEmpty()) return "-";
        StringJoiner result = new StringJoiner("/");
        for (ReleaseApi167.Call call : calls) result.add(call.stage() + ":" + h(call.target())
            + ":" + h(call.receiver()) + ":" + h(call.rows()) + ":" + h(call.alignment()) + ":" + h(call.r9()));
        return result.toString();
    }
    private static String inputLine(ReleaseApi167.Scenario scenario) {
        return scenario.id() + "|" + h(scenario.receiver()) + "|" + h(scenario.rows())
            + "|" + h(scenario.alignment()) + "|" + h(scenario.incomingR9())
            + "|" + words(scenario.initialWords()) + "|" + h(scenario.firstReturn())
            + "|" + words(scenario.firstEffects()) + "|" + h(scenario.releaseReturn());
    }

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
