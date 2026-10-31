package org.xar.ck3.control.g2.common.nativecore.task.captured;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Objects;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79ePorts;

public final class Idler79eRegressionHost {
    public enum Op { READ8, READ32, READ64, WRITE8, WRITE32, WRITE64, DEC32 }
    public record Access(Op op, long address, int bytes, long value) {}
    @FunctionalInterface public interface Observer { void after(Memory memory, Access access); }

    public static final class Memory implements Idler79ePorts.Memory {
        private static final long BASE = 0x100000L;
        private static final int MAX_REGION = 65536;
        private long nextAlloc = BASE;
        private List<long[]> regions = new ArrayList<>(); // [start, endExclusive]
        private List<byte[]> data = new ArrayList<>();
        private List<Access> traceList = new ArrayList<>();
        private Observer observer = null;

        public Memory() {}

        public long allocate(int bytes) {
            if (bytes <= 0 || bytes > MAX_REGION) throw new IllegalArgumentException("Invalid allocation size");
            long start = nextAlloc;
            for (int i = 0; i < regions.size(); i++) {
                long existing = regions.get(i)[0];
                int length = data.get(i).length;
                if (Long.compareUnsigned(start - existing, length) < 0
                        || Long.compareUnsigned(existing - start, bytes) < 0) {
                    throw new IllegalArgumentException("Allocation overlaps an existing region");
                }
            }
            map(start, bytes);
            nextAlloc = start + ((bytes + 7L) & ~7L) + 0x100L;
            return start;
        }

        public void map(long address, int bytes) {
            if (bytes <= 0 || bytes > MAX_REGION) throw new IllegalArgumentException("Invalid map size");
            long end = address + bytes;
            // Check for exact idempotent match
            for (int i = 0; i < regions.size(); i++) {
                if (regions.get(i)[0] == address && regions.get(i)[1] == end) {
                    return; // idempotent
                }
            }
            // Check for overlaps using unsigned difference
            for (int i = 0; i < regions.size(); i++) {
                long s = regions.get(i)[0];
                int length = data.get(i).length;
                if (Long.compareUnsigned(address - s, length) < 0
                        || Long.compareUnsigned(s - address, bytes) < 0) {
                    throw new IllegalArgumentException("Overlapping region");
                }
            }
            regions.add(new long[]{address, end});
            data.add(new byte[bytes]);
        }

        private int findRegion(long address, int bytes) {
            if (bytes <= 0) throw new IllegalArgumentException("Invalid access width");
            for (int i = 0; i < regions.size(); i++) {
                long offset = address - regions.get(i)[0];
                int length = data.get(i).length;
                if (bytes <= length && Long.compareUnsigned(offset, length - bytes) <= 0) {
                    return i;
                }
            }
            throw new IllegalArgumentException("Out of bounds or crossing regions");
        }

        public void onAccess(Observer observer) {
            this.observer = observer;
        }

        public List<Access> trace() {
            return Collections.unmodifiableList(new ArrayList<>(traceList));
        }

        public void clearTrace() {
            traceList.clear();
        }

        public void seedByte(long address, int unsignedValue) {
            if (unsignedValue < 0 || unsignedValue > 255) throw new IllegalArgumentException("Byte out of range");
            int idx = findRegion(address, 1);
            long start = regions.get(idx)[0];
            data.get(idx)[(int)(address - start)] = (byte) unsignedValue;
        }

        public void seedInt32(long address, int value) {
            int idx = findRegion(address, 4);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            d[off] = (byte) value;
            d[off+1] = (byte)(value >>> 8);
            d[off+2] = (byte)(value >>> 16);
            d[off+3] = (byte)(value >>> 24);
        }

        public void seedInt64(long address, long value) {
            int idx = findRegion(address, 8);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            for (int i = 0; i < 8; i++) {
                d[off+i] = (byte)(value >>> (i * 8));
            }
        }

        public int peekUnsignedByte(long address) {
            int idx = findRegion(address, 1);
            long start = regions.get(idx)[0];
            return data.get(idx)[(int)(address - start)] & 0xFF;
        }

        public int peekInt32(long address) {
            int idx = findRegion(address, 4);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            return (d[off] & 0xFF) | ((d[off+1] & 0xFF) << 8) | ((d[off+2] & 0xFF) << 16) | ((d[off+3] & 0xFF) << 24);
        }

        public long peekInt64(long address) {
            int idx = findRegion(address, 8);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            long v = 0;
            for (int i = 0; i < 8; i++) {
                v |= ((long)(d[off+i] & 0xFF)) << (i * 8);
            }
            return v;
        }

        public int readUnsignedByte(long address) {
            int idx = findRegion(address, 1);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            int val = data.get(idx)[off] & 0xFF;
            Access acc = new Access(Op.READ8, address, 1, val);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
            return val;
        }

        public long readPointer(long address) {
            int idx = findRegion(address, 8);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            long val = 0;
            for (int i = 0; i < 8; i++) {
                val |= ((long)(d[off+i] & 0xFF)) << (i * 8);
            }
            Access acc = new Access(Op.READ64, address, 8, val);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
            return val;
        }

        public int readInt32(long address) {
            int idx = findRegion(address, 4);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            int val = (d[off] & 0xFF) | ((d[off+1] & 0xFF) << 8) | ((d[off+2] & 0xFF) << 16) | ((d[off+3] & 0xFF) << 24);
            Access acc = new Access(Op.READ32, address, 4, (long)val);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
            return val;
        }

        public void writeByte(long address, byte value) {
            int idx = findRegion(address, 1);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            data.get(idx)[off] = value;
            Access acc = new Access(Op.WRITE8, address, 1, value & 0xFF);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
        }

        public void writeInt32(long address, int value) {
            int idx = findRegion(address, 4);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            d[off] = (byte) value;
            d[off+1] = (byte)(value >>> 8);
            d[off+2] = (byte)(value >>> 16);
            d[off+3] = (byte)(value >>> 24);
            Access acc = new Access(Op.WRITE32, address, 4, (long)value);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
        }

        public void writeInt64(long address, long value) {
            int idx = findRegion(address, 8);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            for (int i = 0; i < 8; i++) {
                d[off+i] = (byte)(value >>> (i * 8));
            }
            Access acc = new Access(Op.WRITE64, address, 8, value);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
        }

        public void decrementInt32(long address) {
            int idx = findRegion(address, 4);
            long start = regions.get(idx)[0];
            int off = (int)(address - start);
            byte[] d = data.get(idx);
            int val = (d[off] & 0xFF) | ((d[off+1] & 0xFF) << 8) | ((d[off+2] & 0xFF) << 16) | ((d[off+3] & 0xFF) << 24);
            int newVal = val - 1;
            d[off] = (byte) newVal;
            d[off+1] = (byte)(newVal >>> 8);
            d[off+2] = (byte)(newVal >>> 16);
            d[off+3] = (byte)(newVal >>> 24);
            Access acc = new Access(Op.DEC32, address, 4, (long)newVal);
            traceList.add(acc);
            if (observer != null) observer.after(this, acc);
        }
    }

    public record Call28(long rcx, int edx, int r8d) {}
    public static final class Probe implements Idler79ePorts.Ports {
        private List<Idler79ePorts.Known383e320> list383 = new ArrayList<>();
        private List<Call28> list28 = new ArrayList<>();
        private Consumer<Idler79ePorts.Known383e320> cb383 = null;
        private Consumer<Call28> cb28 = null;

        public Probe() {}

        public void on383e320(Consumer<Idler79ePorts.Known383e320> callback) {
            cb383 = callback;
        }

        public void on28eed20(Consumer<Call28> callback) {
            cb28 = callback;
        }

        public List<Idler79ePorts.Known383e320> calls383e320() {
            return Collections.unmodifiableList(new ArrayList<>(list383));
        }

        public List<Call28> calls28eed20() {
            return Collections.unmodifiableList(new ArrayList<>(list28));
        }

        public void call383e320(Idler79ePorts.Known383e320 known) {
            list383.add(known);
            if (cb383 != null) cb383.accept(known);
        }

        public void call28eed20(long rcx, int edx, int r8d) {
            Call28 c = new Call28(rcx, edx, r8d);
            list28.add(c);
            if (cb28 != null) cb28.accept(c);
        }
    }

    private static int assertionCount = 0;
    private static int testCount = 0;
    private static List<String> completedTests = new ArrayList<>();
    private static boolean inTest = false;
    private static final List<Integer> completedChecks = new ArrayList<>();

    public static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
        assertionCount++;
    }

    public static void equal(long expected, long actual, String message) {
        if (expected != actual) throw new AssertionError(message + " expected=" + expected + " actual=" + actual);
        assertionCount++;
    }

    public static void same(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(message + " expected=" + expected + " actual=" + actual);
        assertionCount++;
    }

    public static <T extends Throwable> T expectThrows(Class<T> type, Runnable action) {
        Objects.requireNonNull(type, "type");
        Objects.requireNonNull(action, "action");
        try {
            action.run();
        } catch (Throwable failure) {
            if (type.isInstance(failure)) {
                assertionCount++;
                return type.cast(failure);
            }
            throw new AssertionError("Expected " + type.getName() + " but got "
                    + failure.getClass().getName(), failure);
        }
        throw new AssertionError("Expected exception " + type.getName() + " but none thrown");
    }

    public static synchronized void test(String name, Runnable witness) {
        if (inTest) throw new IllegalStateException("Nested test");
        inTest = true;
        int startAssertions = assertionCount;
        try {
            witness.run();
            if (assertionCount == startAssertions) {
                throw new AssertionError("Test " + name + " had no assertions");
            }
            testCount++;
            completedTests.add(name);
            completedChecks.add(assertionCount - startAssertions);
        } finally {
            inTest = false;
        }
    }

    public static int getAssertionCount() { return assertionCount; }
    public static int getTestCount() { return testCount; }
    public static List<String> getCompletedTests() { return Collections.unmodifiableList(new ArrayList<>(completedTests)); }

    private static String jsonString(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char character = value.charAt(i);
            switch (character) {
                case '\\' -> result.append("\\\\");
                case '"' -> result.append("\\\"");
                case '\n' -> result.append("\\n");
                case '\r' -> result.append("\\r");
                case '\t' -> result.append("\\t");
                default -> {
                    if (character < 0x20) result.append("\\u%04x".formatted((int) character));
                    else result.append(character);
                }
            }
        }
        return result.append('"').toString();
    }

    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("No arguments required");
        int startAssertions = assertionCount;
        int startTests = testCount;
        int startNames = completedTests.size();
        Idler79eScanClearWitnesses.run();
        Idler79eCompositionWitnesses.run();
        int deltaAssertions = assertionCount - startAssertions;
        int deltaTests = testCount - startTests;
        if (deltaTests != 10 || deltaAssertions < deltaTests) {
            throw new AssertionError("Expected ten nonempty successful source witnesses; got " + deltaTests);
        }
        StringBuilder json = new StringBuilder("{\"pass\":true,\"nativeExecuted\":false,\"gameActions\":0,\"assertions\":")
                .append(deltaAssertions).append(",\"tests\":").append(deltaTests).append(",\"witnesses\":[");
        for (int i = startNames; i < completedTests.size(); i++) {
            if (i > startNames) json.append(',');
            json.append("{\"name\":").append(jsonString(completedTests.get(i)))
                    .append(",\"checks\":").append(completedChecks.get(i)).append('}');
        }
        json.append("]}");
        System.out.println(json);
    }
}
