package org.xar.ck3.research.m3;

import java.util.List;

/** Owner takeover after two source-inconsistent literal-book candidates. */
public final class ReleaseCases167 {
    private ReleaseCases167() { }

    public static List<ReleaseApi167.Scenario> units() {
        return List.of(
            new ReleaseApi167.Scenario("inline-normal", 0x1000L, 0x1008L,
                0x8877665544332211L, 0x1122334455667788L, List.of(), 0L,
                List.of(), 0L, List.of(), List.of(), 0x1008L),
            new ReleaseApi167.Scenario("inline-wrap", 0xfffffffffffffff8L, 0L,
                0xfedcba9876543210L, 0x8000000000000001L, List.of(), 0L,
                List.of(), 0L, List.of(), List.of(), 0L),
            new ReleaseApi167.Scenario("fresh-returned-vptr-and-original-change",
                0x2000L, 0x800000000000a011L, 0xfedcba9876543210L, 0xffff0000aaaabbbbL,
                List.of(w(0x2000L,0x5000L), w(0x5038L,0x6010L),
                    w(0x3000L,0x7000L), w(0x7010L,0x7110L), w(0x8010L,0x8110L)),
                0x3000L, List.of(w(0x3000L,0x8000L),w(0x2000L,0x9000L)),
                0xdeadbeefcafebabeL,
                List.of(c(ReleaseApi167.Stage.SLOT38,0x6010L,0x2000L,
                        0x800000000000a011L,0xfedcba9876543210L,0xffff0000aaaabbbbL),
                    c(ReleaseApi167.Stage.RELEASE10,0x8110L,0x3000L,
                        0x800000000000a011L,0xfedcba9876543210L,0x8000L)),
                List.of(w(0x2000L,0x9000L),w(0x5038L,0x6010L),
                    w(0x3000L,0x8000L),w(0x7010L,0x7110L),w(0x8010L,0x8110L)),
                0xdeadbeefcafebabeL),
            new ReleaseApi167.Scenario("fresh-other-returned-vptr",
                0x4000L,0xfedcba9876543210L,0x8000000000000040L,0xdead00005555aaaaL,
                List.of(w(0x4000L,0xa000L),w(0xa038L,0xb010L),
                    w(0x6000L,0xc000L),w(0xc010L,0xc110L),w(0xd010L,0xd110L)),
                0x6000L,List.of(w(0x6000L,0xd000L)),0x8000000000000001L,
                List.of(c(ReleaseApi167.Stage.SLOT38,0xb010L,0x4000L,
                        0xfedcba9876543210L,0x8000000000000040L,0xdead00005555aaaaL),
                    c(ReleaseApi167.Stage.RELEASE10,0xd110L,0x6000L,
                        0xfedcba9876543210L,0x8000000000000040L,0xd000L)),
                List.of(w(0x4000L,0xa000L),w(0xa038L,0xb010L),
                    w(0x6000L,0xd000L),w(0xc010L,0xc110L),w(0xd010L,0xd110L)),
                0x8000000000000001L)
        );
    }

    public static List<ReleaseApi167.Scenario> consumers() {
        return List.of(
            new ReleaseApi167.Scenario("selector165-normal",
                0x10000L,0x16000L,16L,0xaaaabbbbccccddddL,
                List.of(w(0x10000L,0x11000L),w(0x11038L,0x12010L),
                    w(0x10408L,0x13000L),w(0x13000L,0x14000L),w(0x14010L,0x15010L)),
                0L,List.of(),0xffff000000001234L,
                List.of(c(ReleaseApi167.Stage.RELEASE10,0x15010L,0x13000L,
                    0x16000L,16L,0x14000L)),
                List.of(w(0x10000L,0x11000L),w(0x11038L,0x12010L),
                    w(0x10408L,0x13000L),w(0x13000L,0x14000L),w(0x14010L,0x15010L)),
                0xffff000000001234L),
            // -0x200 + 0x408 is 0x208 under actual long address wrap.
            new ReleaseApi167.Scenario("selector165-address-wrap",
                0xfffffffffffffe00L,0x8000000000000040L,0xf000000000000020L,0x76543210fedcba98L,
                List.of(w(0xfffffffffffffe00L,0x17000L),w(0x17038L,0x18010L),
                    w(0x208L,0x19000L),w(0x19000L,0x1a000L),w(0x1a010L,0x1b010L)),
                0L,List.of(),0xc123456789abcdefL,
                List.of(c(ReleaseApi167.Stage.RELEASE10,0x1b010L,0x19000L,
                    0x8000000000000040L,0xf000000000000020L,0x1a000L)),
                List.of(w(0xfffffffffffffe00L,0x17000L),w(0x17038L,0x18010L),
                    w(0x208L,0x19000L),w(0x19000L,0x1a000L),w(0x1a010L,0x1b010L)),
                0xc123456789abcdefL)
        );
    }

    private static ReleaseApi167.Word w(long address,long value) {
        return new ReleaseApi167.Word(address,value);
    }
    private static ReleaseApi167.Call c(ReleaseApi167.Stage stage,long target,
        long receiver,long rows,long alignment,long r9) {
        return new ReleaseApi167.Call(stage,target,receiver,rows,alignment,r9);
    }
}
