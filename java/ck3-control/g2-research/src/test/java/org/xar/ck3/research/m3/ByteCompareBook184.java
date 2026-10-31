package org.xar.ck3.research.m3;
import java.util.List;
import java.util.ArrayList;

public final class ByteCompareBook184 {
    private ByteCompareBook184() { }

    public enum Kind { READ_BYTE, READ_QWORD }

    public record Step(Kind kind, long address, long returned) { }

    public record Scenario(String id, long left, long right, long lengthBits,
            List<Step> expectedSteps, int expectedReturned) { }

    public static List<Scenario> cases() {
        List<Scenario> list = new ArrayList<>();


        list.add(new Scenario("zero_no_reads", 0x1000L, 0x2000L, 0L, List.of(), 0));



        list.add(new Scenario("shortbyte_mismatch", 0x1000L, 0x2000L, 1L,
            List.of(
                new Step(Kind.READ_BYTE, 0x1000L, 0x01L),
                new Step(Kind.READ_BYTE, 0x2000L, 0x02L)
            ), -1));






        list.add(new Scenario("unaligned_prefix_mismatch", 0x1001L, 0x2000L, 8L,
            List.of(
                new Step(Kind.READ_BYTE, 0x1001L, 0xAAL),
                new Step(Kind.READ_BYTE, 0x2000L, 0xBBL)
            ), -1));






        list.add(new Scenario("aligned8_byte_tail_equal", 0x1000L, 0x2000L, 9L,
            List.of(
                new Step(Kind.READ_QWORD, 0x1000L, 0x1122334455667788L),
                new Step(Kind.READ_QWORD, 0x2000L, 0x1122334455667788L),
                new Step(Kind.READ_BYTE, 0x1008L, 0x99L),
                new Step(Kind.READ_BYTE, 0x2008L, 0x99L)
            ), 0));









        list.add(new Scenario("batch32_fourth_qword_mismatch", 0x1000L, 0x2000L, 32L,
            List.of(
                new Step(Kind.READ_QWORD, 0x1000L, 0x11L),
                new Step(Kind.READ_QWORD, 0x2000L, 0x11L),
                new Step(Kind.READ_QWORD, 0x1008L, 0x22L),
                new Step(Kind.READ_QWORD, 0x2008L, 0x22L),
                new Step(Kind.READ_QWORD, 0x1010L, 0x33L),
                new Step(Kind.READ_QWORD, 0x2010L, 0x33L),
                new Step(Kind.READ_QWORD, 0x1018L, 0x01L),
                new Step(Kind.READ_QWORD, 0x2018L, 0x02L),
                new Step(Kind.READ_QWORD, 0x2018L, 0x02L)
            ), -1));





        list.add(new Scenario("equal32_then_equal8", 0x1000L, 0x2000L, 40L,
            List.of(
                new Step(Kind.READ_QWORD, 0x1000L, 0x11L),
                new Step(Kind.READ_QWORD, 0x2000L, 0x11L),
                new Step(Kind.READ_QWORD, 0x1008L, 0x22L),
                new Step(Kind.READ_QWORD, 0x2008L, 0x22L),
                new Step(Kind.READ_QWORD, 0x1010L, 0x33L),
                new Step(Kind.READ_QWORD, 0x2010L, 0x33L),
                new Step(Kind.READ_QWORD, 0x1018L, 0x44L),
                new Step(Kind.READ_QWORD, 0x2018L, 0x44L),
                new Step(Kind.READ_QWORD, 0x1020L, 0x55L),
                new Step(Kind.READ_QWORD, 0x2020L, 0x55L)
            ), 0));

















        list.add(new Scenario("qword_mismatch_fresh_right_equal", 0x1000L, 0x2000L, 8L,
            List.of(
                new Step(Kind.READ_QWORD, 0x1000L, 0xAAL),
                new Step(Kind.READ_QWORD, 0x2000L, 0xBBAL),
                new Step(Kind.READ_QWORD, 0x2000L, 0xAAL)
            ), 1));










        list.add(new Scenario("negative_length_immediate_qword_mismatch", 0x1000L, 0x2000L, -1L,
            List.of(
                new Step(Kind.READ_QWORD, 0x1000L, 0x01L),
                new Step(Kind.READ_QWORD, 0x2000L, 0x02L),
                new Step(Kind.READ_QWORD, 0x2000L, 0x02L)
            ), -1));

        return list;
    }
}
