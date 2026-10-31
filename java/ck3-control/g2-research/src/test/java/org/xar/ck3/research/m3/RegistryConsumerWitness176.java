package org.xar.ck3.research.m3;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/** Independent, finite source-derived data for held 3763730; no native execution. */
public final class RegistryConsumerWitness176 {
    private static final long MODULE = 0L;
    private static final long STACK = 0x100000L;
    private static final long MANAGER = 0x1000L;
    private static final long VECTOR = 0x1100L;
    private static final long VECTOR_ROWS = 0x1200L;
    private static final long TABLE = 0x2000L;
    private static final long OBJECT = 0x3000L;
    private static final long VTABLE = 0x3100L;
    private static final long CALLER20 = 0x1122334455667788L;
    private static final long CALLER28 = 0x8877665544332211L;
    private static final long HIGH1 = 0x0102030405060708L;
    private static final long HIGH2 = 0x8899aabbccddeeffL;
    private static final long COUNTER = 0x5c6a9dcL;
    private static int checks;

    private RegistryConsumerWitness176() { }

    private record Step(String role, long[] arguments, long result,
                        Consumer<Fixture> effect) { }

    /** A queue of literal opaque-call observations, not an implementation of the core. */
    private static final class Script implements RegistryConsumerApi176.Ports {
        private final Fixture fixture;
        private final Deque<Step> steps = new ArrayDeque<>();
        private final List<String> called = new ArrayList<>();

        Script(Fixture fixture) { this.fixture = fixture; }

        void add(String role, long result, Consumer<Fixture> effect, long... arguments) {
            steps.addLast(new Step(role, arguments.clone(), result, effect));
        }

        long take(RegistryConsumerApi176.Memory memory, String role, long... arguments) {
            require(memory == fixture.memory, fixture.id + ": memory identity");
            Step next = steps.pollFirst();
            require(next != null, fixture.id + ": unexpected port " + role);
            require(next.role().equals(role), fixture.id + ": expected "
                    + next.role() + " but observed " + role);
            require(Arrays.equals(next.arguments(), arguments), fixture.id + ": " + role
                    + " expected " + Arrays.toString(next.arguments())
                    + " observed " + Arrays.toString(arguments));
            called.add(role);
            if (next.effect() != null) { next.effect().accept(fixture); }
            return next.result();
        }

        void finished() {
            require(steps.isEmpty(), fixture.id + ": unconsumed ports " + steps.size());
        }

        @Override public void call9ce3f0(RegistryConsumerApi176.Memory m, long h) {
            take(m, "9ce3f0", h);
        }
        @Override public void callca6190(RegistryConsumerApi176.Memory m, long h, int n) {
            take(m, "ca6190", h, n);
        }
        @Override public int handlerAl(RegistryConsumerApi176.Memory m, long c, long k) {
            return (int) take(m, "handlerAl", c, k);
        }
        @Override public void call3f7aa40(RegistryConsumerApi176.Memory m, long d, long s) {
            take(m, "3f7aa40", d, s);
        }
        @Override public void allocatorSlot10(RegistryConsumerApi176.Memory m,
                long c, long a, long b, int align) {
            take(m, "allocatorSlot10", c, a, b, align);
        }
        @Override public long objectSlot08(RegistryConsumerApi176.Memory m, long c, long r) {
            return take(m, "objectSlot08", c, r);
        }
        @Override public int objectSlotA8Al(RegistryConsumerApi176.Memory m, long c, long r) {
            return (int) take(m, "objectSlotA8Al", c, r);
        }
        @Override public void objectSlot00(RegistryConsumerApi176.Memory m,
                long c, long r, int flag) {
            take(m, "objectSlot00", c, r, flag);
        }
        @Override public long objectSlot30(RegistryConsumerApi176.Memory m,
                long c, long r, long out) {
            return take(m, "objectSlot30", c, r, out);
        }
        @Override public int incomingSlot48Al(RegistryConsumerApi176.Memory m, long c, long r) {
            return (int) take(m, "incomingSlot48Al", c, r);
        }
        @Override public long call3768260(RegistryConsumerApi176.Memory m) {
            return take(m, "3768260");
        }
        @Override public long call3f8a6d0(RegistryConsumerApi176.Memory m, long c, int k) {
            return take(m, "3f8a6d0", c, k);
        }
        @Override public long call3f4f8e0(RegistryConsumerApi176.Memory m, int k) {
            return take(m, "3f4f8e0", k);
        }
        @Override public void call3795e30(RegistryConsumerApi176.Memory m,
                long pair, int mode, long d) {
            take(m, "3795e30", pair, mode, d);
        }
        @Override public long call3f95fd0(RegistryConsumerApi176.Memory m, long f, long out) {
            return take(m, "3f95fd0", f, out);
        }
        @Override public long call864a20(RegistryConsumerApi176.Memory m) {
            return take(m, "864a20");
        }
        @Override public void call857a70(RegistryConsumerApi176.Memory m,
                long out, long format, long operands) {
            take(m, "857a70", out, format, operands);
        }
        @Override public long gs58(RegistryConsumerApi176.Memory m) {
            return take(m, "gs58");
        }
        @Override public long call3f5f970(RegistryConsumerApi176.Memory m, int flag) {
            return take(m, "3f5f970", flag);
        }
        @Override public void call857b60(RegistryConsumerApi176.Memory m,
                long logger, long d, int line, int level, long s) {
            take(m, "857b60", logger, d, line, level, s);
        }
        @Override public int atomicXadd32(RegistryConsumerApi176.Memory m, long a, int d) {
            return (int) take(m, "atomicXadd32", a, d);
        }
        @Override public void call4223f44(RegistryConsumerApi176.Memory m, long b, long n) {
            take(m, "4223f44", b, n);
        }
        @Override public void call4232a70(RegistryConsumerApi176.Memory m) {
            take(m, "4232a70");
        }
    }

    private static final class Fixture {
        final String id;
        final RegistryMemory176 memory = new RegistryMemory176(Map.of());
        final Script ports = new Script(this);

        Fixture(String id, boolean firstOccupied, boolean incomingOccupied) {
            this.id = id;
            // All scratch bytes are explicit supplied bytes, including retained high halves.
            region(STACK, 0x200, 0x5a);
            region(MANAGER, 0x60, 0);
            region(TABLE, 0x30, 0);
            region(VECTOR, 0x10, 0);
            region(VECTOR_ROWS, 8, 0);
            memory.seed64(STACK + 0x20L, CALLER20);
            memory.seed64(STACK + 0x28L, CALLER28);
            memory.seed64(STACK + 0xc8L, HIGH1);
            memory.seed64(STACK + 0xd8L, HIGH2);
            memory.seed64(MANAGER + 0x30L, TABLE);
            memory.seed32(MANAGER + 0x3cL, 0);
            memory.seed8(MANAGER + 0x40L, 0);
            memory.seed8(TABLE + 4L, firstOccupied ? 1 : 0);
            memory.seed8(TABLE + 0x1cL, 1); // Occupied end sentinel at table+18h.
            memory.seed64(VECTOR, VECTOR_ROWS);
            memory.seed32(VECTOR + 0xcL, incomingOccupied ? 1 : 0);
            memory.seed64(VECTOR_ROWS, OBJECT);
        }

        void region(long address, int count, int value) {
            for (int i = 0; i < count; ++i) { memory.seed8(address + i, value); }
        }

        long peek(long address, int width) {
            Map<Long, Byte> bytes = memory.bytes();
            long bits = 0L;
            for (int i = 0; i < width; ++i) {
                Byte b = bytes.get(address + i);
                require(b != null, id + ": missing observed byte " + Long.toHexString(address + i));
                bits |= (b.longValue() & 0xffL) << (8 * i);
            }
            return bits;
        }

        void word(long address, int width, long expected) {
            long actual = peek(address, width);
            require(actual == expected, id + ": word " + Long.toHexString(address)
                    + " expected " + Long.toHexString(expected)
                    + " observed " + Long.toHexString(actual));
        }

        void eventCount(String event, long expected) {
            long actual = memory.events().stream().filter(event::equals).count();
            require(actual == expected, id + ": event " + event + " count " + actual);
        }

        void eventSubsequence(String... expected) {
            List<String> actual = memory.events();
            int cursor = 0;
            for (String event : expected) {
                while (cursor < actual.size() && !actual.get(cursor).equals(event)) { ++cursor; }
                require(cursor < actual.size(), id + ": missing ordered event " + event);
                ++cursor;
            }
        }

        void run() {
            memory.clearEvents();
            RegistryConsumerApi176.Completion actual = RegistryConsumer176.consume(memory,
                    ports, MODULE, MANAGER, VECTOR, new RegistryConsumerApi176.Scratch(STACK));
            require(actual == RegistryConsumerApi176.Completion.RETURNED, id + ": completion " + actual);
            ports.finished();
        }

        void finish(int expectedPorts, long expectedFlags, long expectedHome, long expected28) {
            require(ports.called.size() == expectedPorts, id + ": number of ports");
            word(STACK + 0x190L, 4, expectedFlags);
            word(STACK + 0x198L, 8, expectedHome);
            word(STACK + 0x20L, 8, CALLER20);
            word(STACK + 0x28L, 8, expected28);
            word(STACK + 0xc8L, 8, HIGH1);
            word(STACK + 0xd8L, 8, HIGH2);
            System.out.println(id + " ports=" + ports.called.size() + " memoryEvents="
                    + memory.events().size());
        }
    }

    private static void require(boolean condition, String message) {
        ++checks;
        if (!condition) { throw new AssertionError(message); }
    }

    // 376376B..3793: empty sentinel equals captured end. No first-phase home reload.
    private static void emptySentinel() {
        Fixture f = new Fixture("empty-sentinel", false, false);
        f.run();
        f.eventCount("R64:100198", 0);
        f.eventSubsequence("R64:1030", "R8:2004", "R8:201c", "R8:1040", "R32:103c",
                "R64:1100", "R32:110c");
        f.finish(0, 0L, VECTOR, CALLER28);
    }

    // 380B and 386B test AL only. 3903 reloads the actual mutable homeslot.
    private static void firstPhaseAlAndFreshHome() {
        Fixture f = new Fixture("firstphase-al-fresh-home", true, false);
        f.memory.seed32(TABLE + 8L, 0x1a2b);
        f.memory.seed64(TABLE + 0x10L, OBJECT);
        f.region(OBJECT, 0x10, 0);
        f.memory.seed64(OBJECT, VTABLE);
        f.memory.seed64(VTABLE + 8L, 0x3110L);
        f.memory.seed64(0x5c6a4b8L, 0x4000L);
        f.memory.seed64(0x4000L, 0x4010L);
        f.memory.seed8(0x5000L, 0xa5);
        f.memory.seed64(0x6000L, 0x6100L);
        f.memory.seed64(0x6110L, 0x6120L);
        f.region(0x7100L, 0x10, 0);
        f.memory.seed64(0x7100L, 0x7200L);
        f.memory.seed64(0x8000L, 0x8100L);
        f.memory.seed64(0x81a8L, 0x81b0L);
        f.memory.seed64(0x8100L, 0x8110L);
        f.memory.seed64(0x8200L, 0x8210L);
        f.ports.add("9ce3f0", 0L, x -> {
            x.word(STACK + 0x40L, 4, 0L);
            x.word(STACK + 0x44L, 1, 0L);
            x.memory.seed64(STACK + 0x48L, 0x5000L);
            x.memory.seed32(STACK + 0x54L, 1);
            x.memory.seed64(STACK + 0x58L, 0x6000L);
        }, STACK + 0x48L);
        f.ports.add("handlerAl", 0x100L, x -> {
            x.word(STACK + 0x40L, 4, 0x1a2bL);
            x.word(STACK + 0x54L, 4, 1L);
            x.word(0x5000L, 1, 0L);
        }, 0x4010L, STACK + 0x40L);
        f.ports.add("allocatorSlot10", 0L, x -> {
            x.word(STACK + 0x54L, 4, 0L);
            x.memory.seed64(STACK + 0x198L, 0x7100L);
        }, 0x6120L, 0x6000L, 0x5000L, 1L);
        f.ports.add("objectSlot08", 0x8000L, null, 0x3110L, OBJECT);
        f.ports.add("objectSlotA8Al", 0x101L,
                x -> x.memory.seed64(0x8000L, 0x8200L), 0x81b0L, 0x8000L);
        f.ports.add("objectSlot00", 0L, null, 0x8210L, 0x8000L, 1L);
        f.run();
        f.word(STACK + 0x1a0L, 8, 0x8000L);
        f.eventCount("R64:100198", 1);
        f.eventCount("R64:1100", 0);
        f.eventSubsequence("R64:100198", "R64:7100", "R32:710c");
        // Clearing R14's cleanup bit does not rewrite the source frame flag at 3827.
        f.finish(6, 1L, 0x7100L, CALLER28);
    }

    private static Fixture incoming(String id, boolean contextual, boolean tlsGuard) {
        Fixture f = new Fixture(id, false, true);
        f.region(OBJECT, 0x20, 0);
        f.memory.seed64(OBJECT, VTABLE);
        f.memory.seed32(OBJECT + 8L, 0x1234);
        f.memory.seed8(OBJECT + 0xcL, contextual ? 1 : 0);
        f.memory.seed64(VTABLE + 0x48L, 0x400048L);
        f.region(0x5000L, 0x10, 0);
        f.memory.seed8(0x500cL, contextual ? 1 : 0);
        f.memory.seed64(0x5000L, 0x7000L);
        f.region(0x7000L, 0x20, 0);
        f.region(0x8000L, 0x20, 0);
        f.memory.seed64(0xa000L, 0xb000L);
        f.memory.seed8(0xb158L, tlsGuard ? 1 : 0);
        f.ports.add("incomingSlot48Al", 0x100L, null, 0x400048L, OBJECT);
        // Returned 5000 differs from output P+140; source must consume actual RAX.
        f.ports.add("3f95fd0", 0x5000L, x -> {
            x.memory.seed64(STACK + 0x140L, 0xdeadbeef00000000L);
            x.memory.seed64(STACK + 0x148L, 0x1122334455667788L);
        }, OBJECT + 0x10L, STACK + 0x140L);
        f.ports.add("3768260", 0x6000L, null);
        return f;
    }

    private static void observeFormat(Fixture f, long primary, long auxiliary) {
        f.word(STACK + 0x110L, 8, primary);
        f.word(STACK + 0x118L, 8, HIGH1);
        f.word(STACK + 0x120L, 8, auxiliary);
        f.word(STACK + 0x128L, 8, HIGH2);
        f.word(STACK + 0xa0L, 8, 0x492ec88L);
        f.word(STACK + 0xa8L, 8, 0x30L);
        f.word(STACK + 0xe0L, 8, 0xccL);
        f.word(STACK + 0xe8L, 8, STACK + 0x110L);
    }

    private static void retainedCopyEvents(Fixture f, long primary, long auxiliary) {
        f.eventSubsequence("R64:1000c0", "R64:1000c8",
                "W64:100110:" + Long.toHexString(primary), "W64:100118:102030405060708",
                "R64:1000d0", "R64:1000d8",
                "W64:100120:" + Long.toHexString(auxiliary), "W64:100128:8899aabbccddeeff");
    }

    // 393C low-byte zero continues; 39A3..39AF copy both retained high halves.
    private static void incomingCopiesTlsGuard() {
        Fixture f = incoming("incoming-copies-tls1", false, true);
        f.ports.add("3f4f8e0", 0x8000L, null, 0x1234L);
        f.ports.add("857a70", 0L, x -> {
            observeFormat(x, 0x8000L, 0x7000L);
            x.memory.seed64(STACK + 0xf0L, 0x9000L);
            x.memory.seed64(STACK + 0x108L, 0L);
        }, STACK + 0xf0L, STACK + 0xa0L, STACK + 0xe0L);
        f.ports.add("gs58", 0xa000L, null);
        f.run();
        retainedCopyEvents(f, 0x8000L, 0x7000L);
        f.eventCount("R64:100198", 0);
        f.eventCount("R32:5c6a9dc", 0);
        f.eventCount("R32:100190", 0); // TLS1 jumps over 3A56's flags reload.
        f.eventSubsequence("R64:a000", "R8:b158", "R64:100108");
        f.finish(6, 2L, VECTOR, CALLER28);
    }

    // Signed counter -1 permits logging; gap 1F is accepted and free bytes are 1027.
    private static void incomingLoggerAtomicLargeFree() {
        Fixture f = incoming("incoming-logger-atomic-largefree", true, false);
        f.memory.seed64(0x8018L, 0x10L);
        f.memory.seed64(0x8000L, 0x8100L);
        f.memory.seed64(0x7018L, 0x10L);
        f.memory.seed64(0x7000L, 0x7100L);
        f.memory.seed32(COUNTER, -1);
        f.memory.seed64(0x20001fL, 0x200000L);
        f.ports.add("3f8a6d0", 0x8000L, null, 0x6000L, 0x1234L);
        f.ports.add("864a20", 0x7000L, null);
        f.ports.add("857a70", 0L, x -> {
            observeFormat(x, 0x8100L, 0x7100L);
            x.memory.seed64(STACK + 0xf0L, 0x200027L);
            x.memory.seed64(STACK + 0x108L, 0xfffL);
        }, STACK + 0xf0L, STACK + 0xa0L, STACK + 0xe0L);
        f.ports.add("gs58", 0xa000L, null);
        f.ports.add("3f5f970", 0xc000L, null, 1L);
        f.ports.add("857b60", 0L, x -> {
            x.word(STACK + 0x20L, 8, CALLER20);
            x.word(STACK + 0x28L, 8, STACK + 0xf0L);
        }, 0xc000L, 0x492ece0L, 0x8bL, 4L, STACK);
        f.ports.add("atomicXadd32", 0xffffffffL, x -> {
            x.word(COUNTER, 4, 0xffffffffL);
            x.memory.seed32(COUNTER, 0);
        }, COUNTER, 1L);
        f.ports.add("4223f44", 0L, null, 0x200000L, 0x1027L);
        f.run();
        retainedCopyEvents(f, 0x8100L, 0x7100L);
        f.word(COUNTER, 4, 0L);
        f.eventCount("R64:100198", 0);
        f.eventCount("R32:100190", 1);
        f.eventSubsequence("R64:a000", "R8:b158", "R32:5c6a9dc",
                "W64:100028:1000f0", "R32:100190", "R64:100108", "R64:1000f0",
                "R64:20001f");
        f.finish(11, 2L, VECTOR, STACK + 0xf0L);
    }

    public static void main(String[] args) {
        emptySentinel();
        firstPhaseAlAndFreshHome();
        incomingCopiesTlsGuard();
        incomingLoggerAtomicLargeFree();
        System.out.println("cases=4 checks=" + checks + " native=0 game=0");
    }
}
