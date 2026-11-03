package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.e;

/** Owner Test from the independent 09:43 literal oracle; no producer body was read. */
public final class DefaultAllocateBoundary648 {
    private DefaultAllocateBoundary648() { }

    private static final VolatileBits INPUT_V = new VolatileBits(
            0xfedcba9876543210L, 0x8000000000001111L, 0xf000000000002222L,
            0x8888888888888888L, 0x9999999999999999L,
            0xaaaabbbbccccddddL, 0x123456789abcdef0L,
            new Bits128(0x1000000000000100L, 0xeffffffffffffeffL),
            new Bits128(0x1000000000000101L, 0xeffffffffffffefeL),
            new Bits128(0x1000000000000102L, 0xeffffffffffffefdL),
            new Bits128(0x1000000000000103L, 0xeffffffffffffefcL),
            new Bits128(0x1000000000000104L, 0xeffffffffffffefbL),
            new Bits128(0x1000000000000105L, 0xeffffffffffffefaL));
    private static final VolatileBits CHILD_V = new VolatileBits(
            0xfedcba9876543210L, 0xf000000000002222L, 0xf000000000002222L,
            0x8888888888888888L, 0x9999999999999999L,
            0xaaaabbbbccccddddL, 0x123456789abcdef0L,
            new Bits128(0x1000000000000100L, 0xeffffffffffffeffL),
            new Bits128(0x1000000000000101L, 0xeffffffffffffefeL),
            new Bits128(0x1000000000000102L, 0xeffffffffffffefdL),
            new Bits128(0x1000000000000103L, 0xeffffffffffffefcL),
            new Bits128(0x1000000000000104L, 0xeffffffffffffefbL),
            new Bits128(0x1000000000000105L, 0xeffffffffffffefaL));
    private static final VolatileBits POST_V = new VolatileBits(
            0x800000000000a001L, 0xf00000000000a002L, 0x900000000000a003L,
            0x123400000000a004L, 0x567800000000a005L,
            0x9abc00000000a00aL, 0xdef000000000a00bL,
            new Bits128(0x2000000000000200L, 0xdffffffffffffdffL),
            new Bits128(0x2000000000000201L, 0xdffffffffffffdfeL),
            new Bits128(0x2000000000000202L, 0xdffffffffffffdfdL),
            new Bits128(0x2000000000000203L, 0xdffffffffffffdfcL),
            new Bits128(0x2000000000000204L, 0xdffffffffffffdfbL),
            new Bits128(0x2000000000000205L, 0xdffffffffffffdfaL));
    private static final NonvolatileBits INPUT_N = new NonvolatileBits(
            0x8000000000010101L, 0xf000000000020202L, 0x9000000000030303L,
            0x1234000000040404L, 0xabcdef1200050505L, 0x8000000000060606L,
            0xf000000000070707L, 0x0fedcba900080808L,
            new Bits128(0x1000000000000606L, 0xeffffffffffff9f9L));
    private static final NonvolatileBits BAD_N = new NonvolatileBits(
            0x8000000000010100L, 0xf000000000020202L, 0x9000000000030303L,
            0x1234000000040404L, 0xabcdef1200050505L, 0x8000000000060606L,
            0xf000000000070707L, 0x0fedcba900080808L,
            new Bits128(0x1000000000000606L, 0xeffffffffffff9f9L));

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void seedFill(StaticFixture648.Ram ram, long address, int size, int value) {
        byte[] bytes = new byte[size];
        Arrays.fill(bytes, (byte) value);
        ram.seedBytes(address, bytes);
    }

    private static StaticFixture648.Ram seededRam() {
        StaticFixture648.Ram ram = new StaticFixture648.Ram();
        seedFill(ram, 0x70005fc8L, 128, 0x5a);
        seedFill(ram, 0x9800L, 4, 0xcc);
        seedFill(ram, 0xf000000000002222L, 24, 0xdd);
        seedFill(ram, 0x8000000000001111L, 24, 0xee);
        ram.seed(0x70006008L, 8, 0x140123456L);
        return ram;
    }

    private static void literalFill(Map<Long, Byte> bytes, long address, int count, int value) {
        for (int i = 0; i < count; i++) bytes.put(address + i, (byte) value);
    }

    private static void literalScalar(Map<Long, Byte> bytes, long address, int width, long value) {
        for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
    }

    /** Independent initial bytes plus the three frozen literal writes; no target state read. */
    private static Map<Long, Byte> expectedRam(int marker) {
        Map<Long, Byte> expected = new HashMap<>();
        literalFill(expected, 0x70005fc8L, 128, 0x5a);
        literalFill(expected, 0x9800L, 4, 0xcc);
        literalFill(expected, 0xf000000000002222L, 24, 0xdd);
        literalFill(expected, 0x8000000000001111L, 24, 0xee);
        literalScalar(expected, 0x70006008L, 8, 0x140123456L);
        literalScalar(expected, 0x70005fd8L, 8, 0x1408571dcL);
        literalScalar(expected, 0x9800L, 1, marker);
        literalScalar(expected, 0x70006008L, 8, 0x1122334455667788L);
        require(expected.size() == 180, "Independent RAM extent");
        return Map.copyOf(expected);
    }

    private static List<StaticFixture648.Event> expectedPrefix(int marker) {
        return List.of(
                e("W64", 0x70005fd8L, 0x1408571dcL),
                e("PORT_INVOKE", 0x8571d7L, 0x4223b94L),
                e("W8", 0x9800L, marker),
                e("W64", 0x70006008L, 0x1122334455667788L));
    }

    private static final class Scene {
        final StaticFixture648.Ram ram = seededRam();
        final QueueFp604Api.Mxcsr unknown = new QueueFp604Api.Mxcsr(0, 0);
        final DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(0x140000000L, 0x70006008L, INPUT_V, INPUT_N),
                true, unknown);
        final GovernmentCrtBoundary185Api.Call expectedCall = new GovernmentCrtBoundary185Api.Call(
                0x8571d7L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223b94L,
                0x70005fe0L, CHILD_V, INPUT_N);
        final GovernmentCrtBoundary185Api.Entry expectedChild = new GovernmentCrtBoundary185Api.Entry(
                0x140000000L, 0x70005fd8L, CHILD_V, INPUT_N);
    }

    private static final class Script implements DefaultStaticFp648Api.Calls {
        private final Scene scene;
        private final int marker;
        private final QueueFp604Api.Outcome offered;
        private final RuntimeException failure;
        private int invokeCount;

        Script(Scene scene, int marker, QueueFp604Api.Outcome offered, RuntimeException failure) {
            this.scene = scene;
            this.marker = marker;
            this.offered = offered;
            this.failure = failure;
        }

        @Override
        public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
            require(invokeCount == 0, "Unexpected additional CALL");
            invokeCount++;
            scene.ram.events.add(e("PORT_INVOKE", 0x8571d7L, 0x4223b94L));
            require(frame != null, "Missing CALL frame");
            require(frame.call().equals(scene.expectedCall), "Complete CALL/site/kind/target/preSP/V/N");
            require(frame.childEntry().equals(scene.expectedChild), "Complete child image/SP/V/N");
            require(frame.directionFlagSet(), "Actual incoming DF");
            require(frame.preMxcsr() == scene.unknown, "Same unknown pre-MXCSR object");
            require(frame.instructionLength() == 5, "Actual CALL length");
            require(frame.returnRipBits() == 0x1408571dcL, "Actual child continuation");
            scene.ram.writeByte(0x9800L, marker);
            scene.ram.writeQword(0x70006008L, 0x1122334455667788L);
            if (failure != null) throw failure;
            return offered;
        }

        @Override
        public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
            throw new AssertionError("Unexpected tail from held8571D0");
        }
    }

    private static void checkPrefix(Scene scene, Script script,
            List<StaticFixture648.Event> expectedEvents, Map<Long, Byte> expectedBytes) {
        require(script.invokeCount == 1, "Exactly one child CALL");
        require(scene.ram.events.equals(expectedEvents), "Complete ordered access/CALL prefix");
        require(scene.ram.fullBytes().equals(expectedBytes), "Complete RAM including untouched padding");
    }

    public static void normalChangedStateAndFreshRetAlias() {
        Scene scene = new Scene();
        QueueFp604Api.Mxcsr partial = new QueueFp604Api.Mxcsr(8, 12);
        QueueFp604Api.Normal offered = new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                        POST_V, 0x1408571dcL, 0x70005fe0L, INPUT_N), false), partial);
        Script script = new Script(scene, 0x11, offered, null);
        Map<Long, Byte> bytes = expectedRam(0x11);
        List<StaticFixture648.Event> events = List.of(
                e("W64", 0x70005fd8L, 0x1408571dcL),
                e("PORT_INVOKE", 0x8571d7L, 0x4223b94L),
                e("W8", 0x9800L, 0x11),
                e("W64", 0x70006008L, 0x1122334455667788L),
                e("R64", 0x70006008L, 0x1122334455667788L));
        GovernmentCrtBoundary185Api.NormalReturn expected = new GovernmentCrtBoundary185Api.NormalReturn(
                POST_V, 0x1122334455667788L, 0x70006010L, INPUT_N);
        QueueFp604Api.Outcome actual = DefaultAllocateWithFp648.fromSlot08(scene.input, scene.ram, script);
        if (!(actual instanceof QueueFp604Api.Normal normal)) {
            throw new AssertionError("Expected whole allocator Normal");
        }
        require(normal.base().normalReturn().equals(expected), "Complete final V/N/RIP/SP after fresh RET");
        require(!normal.base().postDirectionFlagSet(), "Accepted changed post-DF");
        require(normal.postMxcsr() == partial, "Same accepted partial post-MXCSR object");
        checkPrefix(scene, script, events, bytes);
    }

    public static void sameStoppedPrefix() {
        Scene scene = new Scene();
        QueueFp604Api.Stopped offered = new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                        0x140000000L, 0x70005fd8L, CHILD_V, INPUT_N),
                        0x4223b94L, true, scene.unknown), 0, 0x8571d7L);
        Script script = new Script(scene, 0x22, offered, null);
        Map<Long, Byte> bytes = expectedRam(0x22);
        List<StaticFixture648.Event> events = expectedPrefix(0x22);
        QueueFp604Api.Outcome actual = DefaultAllocateWithFp648.fromSlot08(scene.input, scene.ram, script);
        require(actual == offered, "Exact pre-created Stopped identity");
        checkPrefix(scene, script, events, bytes);
    }

    public static void sameArbitraryExceptionPrefix() {
        Scene scene = new Scene();
        UnsupportedOperationException sentinel = new UnsupportedOperationException("Owned D0 callback sentinel");
        Script script = new Script(scene, 0x33, null, sentinel);
        Map<Long, Byte> bytes = expectedRam(0x33);
        List<StaticFixture648.Event> events = expectedPrefix(0x33);
        UnsupportedOperationException escaped = null;
        try {
            DefaultAllocateWithFp648.fromSlot08(scene.input, scene.ram, script);
        } catch (UnsupportedOperationException failure) {
            escaped = failure;
        }
        require(escaped == sentinel, "Exact arbitrary exception identity");
        checkPrefix(scene, script, events, bytes);
    }

    private static void rejectedNormal(int marker, long rip, long rsp, NonvolatileBits n, String message) {
        Scene scene = new Scene();
        QueueFp604Api.Mxcsr rejectedFp = new QueueFp604Api.Mxcsr(64, 192);
        QueueFp604Api.Normal offered = new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                        POST_V, rip, rsp, n), false), rejectedFp);
        Script script = new Script(scene, marker, offered, null);
        Map<Long, Byte> bytes = expectedRam(marker);
        List<StaticFixture648.Event> events = expectedPrefix(marker);
        IllegalArgumentException rejected = null;
        try {
            DefaultAllocateWithFp648.fromSlot08(scene.input, scene.ram, script);
        } catch (IllegalArgumentException failure) {
            rejected = failure;
        }
        require(rejected != null, "Bad Normal must be rejected");
        require(rejected.getClass() == IllegalArgumentException.class, "Precise normal-guard exception type");
        require(message.equals(rejected.getMessage()), "Precise normal-guard predicate");
        checkPrefix(scene, script, events, bytes);
    }

    public static void badNormalReturnRejectedThreeWays() {
        rejectedNormal(0x41, 0x1408571ddL, 0x70005fe0L, INPUT_N, "Return RIP mismatch");
        rejectedNormal(0x42, 0x1408571dcL, 0x70005fe8L, INPUT_N, "Caller RSP mismatch");
        rejectedNormal(0x43, 0x1408571dcL, 0x70005fe0L, BAD_N, "Nonvolatile mismatch");
    }

    public static int verify() {
        normalChangedStateAndFreshRetAlias();
        sameStoppedPrefix();
        sameArbitraryExceptionPrefix();
        badNormalReturnRejectedThreeWays();
        return 4;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}
