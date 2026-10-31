package org.xar.ck3.research.m3;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

public final class PostRegistrationMainValidation178 {
    private PostRegistrationMainValidation178() { }

    public static void main(String[] args) {
        List<PostRegistrationMainCasesApi178.Case> cases = PostRegistrationMainBook178.cases();
        int totalMixedChecks = 0;

        for (PostRegistrationMainCasesApi178.Case c : cases) {
            // 1. Initialize Memory with initial Words
            Map<Long, Byte> initialMap = new HashMap<>();
            for (PostRegistrationMainCasesApi178.Word w : c.initial()) {
                validateWord(w);
                long addr = w.address();
                int width = w.width();
                long bits = w.bits();
                for (int i = 0; i < width; i++) {
                    long byteAddr = addr + i;
                    int byteVal = (int) ((bits >>> (8 * i)) & 0xFF);
                    initialMap.put(byteAddr, (byte) byteVal);
                }
            }
            RegistryMemory176 memory = new RegistryMemory176(initialMap);
            PostRegistrationApi178.Memory bridge = new MemoryBridge(memory);

            // 2. Prepare Ports and ScalarObservation (Shared Script)
            Script ports = new Script(bridge, c.calls());
            PostRegistrationApi178.ScalarObservation scalar = ports;

            // 3. Execute apply
            PostRegistrationApi178.CallerOwnedScratch scratch = new PostRegistrationApi178.CallerOwnedScratch(c.sourceRsp());
            PostRegistration178.apply(bridge, ports, scalar, c.moduleBase(), c.incomingVector(), scratch);

            // 4. Validate Queue Exhausted
            ports.validateExhausted();

            // 5. Validate expectedWords via bytes() without event pollution
            Map<Long, Byte> currentBytes = memory.bytes();
            for (PostRegistrationMainCasesApi178.Word w : c.expectedWords()) {
                validateWord(w);
                long addr = w.address();
                int width = w.width();
                long bits = w.bits();
                for (int i = 0; i < width; i++) {
                    long byteAddr = addr + i;
                    int expectedByte = (int) ((bits >>> (8 * i)) & 0xFF);
                    Byte actualByte = currentBytes.get(byteAddr);
                    if (actualByte == null) {
                        throw new IllegalStateException("Missing byte at expected address: " + Long.toHexString(byteAddr));
                    }
                    if ((actualByte & 0xFF) != expectedByte) {
                        throw new IllegalStateException("Byte mismatch at " + Long.toHexString(byteAddr));
                    }
                }
            }

            // 6. Validate Probes and orderedEvents
            List<String> events = memory.events();
            for (PostRegistrationMainCasesApi178.Probe p : c.probes()) {
                int count = 0;
                for (String e : events) {
                    if (e.equals(p.exactEvent())) {
                        count++;
                    }
                }
                if (count != p.count()) {
                    throw new IllegalStateException("Probe count mismatch for " + p.exactEvent());
                }
            }
            validateSubsequence(c.orderedEvents(), events);

            // 7. Validate noWrites if true
            if (c.noWrites()) {
                for (String e : events) {
                    if (e.startsWith("W8:") || e.startsWith("W32:") || e.startsWith("W64:")) {
                        throw new IllegalStateException("Write event found in noWrites case: " + e);
                    }
                }
                // Check all initial bytes unchanged
                for (PostRegistrationMainCasesApi178.Word w : c.initial()) {
                    long addr = w.address();
                    int width = w.width();
                    long bits = w.bits();
                    for (int i = 0; i < width; i++) {
                        long byteAddr = addr + i;
                        int expectedByte = (int) ((bits >>> (8 * i)) & 0xFF);
                        Byte actualByte = currentBytes.get(byteAddr);
                        if (actualByte == null || (actualByte & 0xFF) != expectedByte) {
                            throw new IllegalStateException("Initial byte changed in noWrites case at " + Long.toHexString(byteAddr));
                        }
                    }
                }
            }

            // 8. Print counts
            int sceneChecks = c.calls().size() + c.expectedWords().size() + c.probes().size() + c.orderedEvents().size();
            totalMixedChecks += sceneChecks;
            System.out.println("Scene " + c.id() + ": ports=" + c.calls().size() + " events=" + events.size() + " listedCheckGroups=" + sceneChecks);
        }
        System.out.println("Total listed check groups: " + totalMixedChecks);
    }

    private static void validateWord(PostRegistrationMainCasesApi178.Word w) {
        if (w.width() != 1 && w.width() != 4 && w.width() != 8) {
            throw new IllegalStateException("Invalid word width: " + w.width());
        }
    }

    private static void validateSubsequence(List<String> sub, List<String> seq) {
        int j = 0;
        for (String s : seq) {
            if (j < sub.size() && s.equals(sub.get(j))) {
                j++;
            }
        }
        if (j != sub.size()) {
            throw new IllegalStateException("Ordered events not a subsequence");
        }
    }

    private static final class MemoryBridge implements PostRegistrationApi178.Memory {
        private final RegistryMemory176 delegate;
        MemoryBridge(RegistryMemory176 delegate) { this.delegate = delegate; }
        @Override public int readUnsigned8(long address) { return delegate.readUnsigned8(address); }
        @Override public void write8(long address, int value) { delegate.write8(address, value); }
        @Override public long readPointer(long address) { return delegate.readPointer(address); }
        @Override public int readInt32(long address) { return delegate.readInt32(address); }
        @Override public void writeInt32(long address, int value) { delegate.writeInt32(address, value); }
        @Override public void writeInt64(long address, long value) { delegate.writeInt64(address, value); }
    }

    private static final class Script implements PostRegistrationApi178.Ports, PostRegistrationApi178.ScalarObservation {
        private final PostRegistrationApi178.Memory memory;
        private final List<PostRegistrationMainCasesApi178.Call> calls;
        private int index = 0;

        Script(PostRegistrationApi178.Memory memory, List<PostRegistrationMainCasesApi178.Call> calls) {
            this.memory = memory;
            this.calls = calls;
        }

        private long take(PostRegistrationApi178.Memory m, String role, long[] args) {
            if (m != memory) {
                throw new IllegalStateException("Memory identity mismatch");
            }
            if (index >= calls.size()) {
                throw new IllegalStateException("Unexpected call: " + role);
            }
            PostRegistrationMainCasesApi178.Call c = calls.get(index);
            if (!c.role().equals(role)) {
                throw new IllegalStateException("Role mismatch: expected " + c.role() + " got " + role);
            }
            if (c.arguments().length != args.length) {
                throw new IllegalStateException("Arg count mismatch for " + role);
            }
            for (int i = 0; i < args.length; i++) {
                if (c.arguments()[i] != args[i]) {
                    throw new IllegalStateException("Arg mismatch at index " + i + " for " + role);
                }
            }

            // Validate observes before effects
            MemoryBridge bridge = (MemoryBridge) memory;
            RegistryMemory176 regMem = bridge.delegate;
            Map<Long, Byte> currentBytes = regMem.bytes();

            for (PostRegistrationMainCasesApi178.Word w : c.observes()) {
                validateWord(w);
                long addr = w.address();
                int width = w.width();
                long bits = w.bits();
                for (int i = 0; i < width; i++) {
                    long byteAddr = addr + i;
                    int expectedByte = (int) ((bits >>> (8 * i)) & 0xFF);
                    Byte actualByte = currentBytes.get(byteAddr);
                    if (actualByte == null) {
                        throw new IllegalStateException("Missing observed byte at " + Long.toHexString(byteAddr));
                    }
                    if ((actualByte & 0xFF) != expectedByte) {
                        throw new IllegalStateException("Observed byte mismatch at " + Long.toHexString(byteAddr));
                    }
                }
            }

            // Apply effects
            for (PostRegistrationMainCasesApi178.Word w : c.effects()) {
                validateWord(w);
                long addr = w.address();
                int width = w.width();
                long bits = w.bits();
                for (int i = 0; i < width; i++) {
                    long byteAddr = addr + i;
                    int byteVal = (int) ((bits >>> (8 * i)) & 0xFF);
                    regMem.seed8(byteAddr, byteVal);
                }
            }

            index++;
            return c.returned();
        }

        @Override public int call3f542c0(PostRegistrationApi178.Memory m, long receiver, long descriptor) {
            return (int) take(m, "call3f542c0", new long[]{receiver, descriptor});
        }
        @Override public long callc3e150(PostRegistrationApi178.Memory m) {
            return take(m, "callc3e150", new long[]{});
        }
        @Override public int call86e160(PostRegistrationApi178.Memory m, int requested, int zeroEdx) {
            return (int) take(m, "call86e160", new long[]{Integer.toUnsignedLong(requested), Integer.toUnsignedLong(zeroEdx)});
        }
        @Override public void callc3b700(PostRegistrationApi178.Memory m, long header, int exponent) {
            take(m, "callc3b700", new long[]{header, Integer.toUnsignedLong(exponent)});
        }
        @Override public void call3763f90(PostRegistrationApi178.Memory m, long receiver, long outputVector) {
            take(m, "call3763f90", new long[]{receiver, outputVector});
        }
        @Override public long objectSlot80(PostRegistrationApi178.Memory m, long code, long receiver) {
            return take(m, "objectSlot80", new long[]{code, receiver});
        }
        @Override public int call3f7e220(PostRegistrationApi178.Memory m, long dataRdx, int lengthR8d) {
            return (int) take(m, "call3f7e220", new long[]{dataRdx, Integer.toUnsignedLong(lengthR8d)});
        }
        @Override public void callc39c60(PostRegistrationApi178.Memory m, long header, long output, int hash, long descriptor) {
            take(m, "callc39c60", new long[]{header, output, Integer.toUnsignedLong(hash), descriptor});
        }
        @Override public long calla92eb0(PostRegistrationApi178.Memory m) {
            return take(m, "calla92eb0", new long[]{});
        }
        @Override public long call3793900(PostRegistrationApi178.Memory m, long context, int hash) {
            return take(m, "call3793900", new long[]{context, Integer.toUnsignedLong(hash)});
        }
        @Override public int call3f6d2b0Al(PostRegistrationApi178.Memory m, long descriptor, long data) {
            return (int) take(m, "call3f6d2b0Al", new long[]{descriptor, data});
        }
        @Override public void call857a70(PostRegistrationApi178.Memory m, long output, long format, long operands) {
            take(m, "call857a70", new long[]{output, format, operands});
        }
        @Override public long gs58(PostRegistrationApi178.Memory m) {
            return take(m, "gs58", new long[]{});
        }
        @Override public long call3f5f970(PostRegistrationApi178.Memory m, int flag) {
            return take(m, "call3f5f970", new long[]{Integer.toUnsignedLong(flag)});
        }
        @Override public void call857b60(PostRegistrationApi178.Memory m, long logger, long descriptor, int line, int level, long sourceRsp) {
            take(m, "call857b60", new long[]{logger, descriptor, Integer.toUnsignedLong(line), Integer.toUnsignedLong(level), sourceRsp});
        }
        @Override public int atomicXadd32(PostRegistrationApi178.Memory m, long address, int delta) {
            return (int) take(m, "atomicXadd32", new long[]{address, Integer.toUnsignedLong(delta)});
        }
        @Override public void call4223f44(PostRegistrationApi178.Memory m, long base, long bytes) {
            take(m, "call4223f44", new long[]{base, bytes});
        }
        @Override public void call4232a70(PostRegistrationApi178.Memory m) {
            take(m, "call4232a70", new long[]{});
        }
        @Override public void objectSlot00(PostRegistrationApi178.Memory m, long code, long receiver, int flag) {
            take(m, "objectSlot00", new long[]{code, receiver, Integer.toUnsignedLong(flag)});
        }
        @Override public void allocatorSlot10(PostRegistrationApi178.Memory m, long code, long receiver, long rows, int alignment) {
            take(m, "allocatorSlot10", new long[]{code, receiver, rows, Integer.toUnsignedLong(alignment)});
        }
        @Override public void call4223a84(PostRegistrationApi178.Memory m, long guard) {
            take(m, "call4223a84", new long[]{guard});
        }
        @Override public void call4223a24(PostRegistrationApi178.Memory m, long guard) {
            take(m, "call4223a24", new long[]{guard});
        }
        @Override public void call856050(PostRegistrationApi178.Memory m, long field) {
            take(m, "call856050", new long[]{field});
        }

        @Override public int cvtdq2psMulssAddssCvttss2si(int sourceInteger, int multiplierBits, int addendBits) {
            return (int) take(memory, "scalarObservation", new long[]{Integer.toUnsignedLong(sourceInteger), Integer.toUnsignedLong(multiplierBits), Integer.toUnsignedLong(addendBits)});
        }

        public void validateExhausted() {
            if (index != calls.size()) {
                throw new IllegalStateException("Calls not exhausted");
            }
        }
    }
}