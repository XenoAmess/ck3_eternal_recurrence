package org.xar.ck3.research.m3;
import java.util.List;
import java.util.ArrayList;

public final class MoveSlotBook193 {
    private MoveSlotBook193() { }

    public enum Kind { WRITE_INT32, WRITE_BYTE, READ_RAW128, WRITE_RAW128, WRITE_INT64, CLEANUP }

    public record Cell(long address, int width, long value) { }

    public record Event(Kind kind, long address, long low, long high, List<Cell> writesAfter) { }

    public record Scenario(String id, long bucket, int probe, int hash, long descriptor,
                           List<Cell> initial, List<Event> expected) { }

    public static List<Scenario> cases() {
        List<Scenario> list = new ArrayList<>();

        list.add(new Scenario(
            "self",
            0x100L, 0, 0, 0x108L,
            List.of(
                new Cell(0x100L, 4, 0L),
                new Cell(0x104L, 1, 0L)
            ),
            List.of(
                new Event(Kind.WRITE_INT32, 0x100L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_BYTE, 0x104L, 0L, 0L, List.of())
            )
        ));

        list.add(new Scenario(
            "disjoint",
            0x200L, 0, 0, 0x300L,
            List.of(
                new Cell(0x200L, 4, 0L),
                new Cell(0x204L, 1, 0L),
                new Cell(0x300L, 8, 0x1122334455667788L),
                new Cell(0x308L, 8, 0x99AABBCCDDEEFF00L),
                new Cell(0x310L, 8, 0x2233445566778899L),
                new Cell(0x318L, 8, 0xAABBCCDDEEFF0011L)
            ),
            List.of(
                new Event(Kind.WRITE_INT32, 0x200L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_BYTE, 0x204L, 0L, 0L, List.of()),
                new Event(Kind.CLEANUP, 0x208L, 0L, 0L, List.of(
                    new Cell(0x300L, 8, 0x0000000000000000L),
                    new Cell(0x308L, 8, 0x0000000000000000L),
                    new Cell(0x310L, 8, 0x0000000000000000L),
                    new Cell(0x318L, 8, 0x0000000000000000L)
                )),
                new Event(Kind.READ_RAW128, 0x300L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_RAW128, 0x208L, 0L, 0L, List.of()),
                new Event(Kind.READ_RAW128, 0x310L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_RAW128, 0x218L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_INT64, 0x310L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_INT64, 0x318L, 0x0F, 0L, List.of()),
                new Event(Kind.WRITE_BYTE, 0x300L, 0L, 0L, List.of())
            )
        ));

        list.add(new Scenario(
            "overlap",
            0x400L, 0, 0, 0x400L,
            List.of(
                new Cell(0x400L, 8, 0L),
                new Cell(0x404L, 1, 0L),
                new Cell(0x408L, 8, 0x1111111111111111L),
                new Cell(0x410L, 8, 0x2222222222222222L),
                new Cell(0x418L, 8, 0x3333333333333333L),
                new Cell(0x420L, 8, 0x4444444444444444L)
            ),
            List.of(
                new Event(Kind.WRITE_INT32, 0x400L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_BYTE, 0x404L, 0L, 0L, List.of()),
                new Event(Kind.CLEANUP, 0x408L, 0L, 0L, List.of()),
                new Event(Kind.READ_RAW128, 0x400L, 0L, 0x1111111111111111L, List.of()),
                new Event(Kind.WRITE_RAW128, 0x408L, 0L, 0x1111111111111111L, List.of()),
                new Event(Kind.READ_RAW128, 0x410L, 0x1111111111111111L, 0x3333333333333333L, List.of()),
                new Event(Kind.WRITE_RAW128, 0x418L, 0x1111111111111111L, 0x3333333333333333L, List.of()),
                new Event(Kind.WRITE_INT64, 0x410L, 0L, 0L, List.of()),
                new Event(Kind.WRITE_INT64, 0x418L, 0x0F, 0L, List.of()),
                new Event(Kind.WRITE_BYTE, 0x400L, 0L, 0L, List.of())
            )
        ));

        return list;
    }
}
