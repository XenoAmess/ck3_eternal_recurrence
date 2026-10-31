package org.xar.ck3.research.m3;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan;

public final class CleanupContextBook197 {
    private CleanupContextBook197() { }

    public enum Entry { CORE, MOVE_SLOT, FOREIGN_CALLBACK }
    public enum Expected { RETURNED, UNSUPPORTED_RESULT, THREW_UNSUPPORTED, THREW_FOREIGN }
    public enum Kind { READ_POINTER, READ_INT32, WRITE_INT32, WRITE_INT64, READ_BYTE, WRITE_BYTE,
        WRITE_INT16, READ_RAW128, WRITE_RAW128, FIRST_CALL, FAILURE_CELL, LAST_ERROR, MAP_CODE }

    public record Cell(long address, int byteWidth, long low, long high) { }
    public record LowerReturns(int firstCallBits, long failureCellAddress, int lastErrorBits, int mappedBits) { }
    public record Event(Kind kind, long address, long arg0, long arg1, long result) { }

    public record Scenario(String id, Entry entry, long moduleBase, long storage, long bucket,
        int probe, int hash, long sourceDescriptor, List<Cell> initialCells, LowerReturns lowerReturns,
        List<Event> expectedEvents, Expected expectedOutcome,
        Optional<InlineStorageCleanupPlan.Path> expectedPlanPath, List<Cell> finalCells) { }

    public static List<Scenario> cases() {
        return List.of(
            // 1. INLINE: capacity < 16, no heap read, no lower call, direct reset.
            new Scenario(
                "inline_small_capacity",
                Entry.CORE,
                0x1000L, 0x2000L, 0L, 0, 0, 0L,
                List.of(
                    new Cell(0x2018L, 8, 5L, 0L) // capacity = 5 (< 16)
                ),
                new LowerReturns(0, 0L, 0, 0),
                List.of(
                    new Event(Kind.READ_POINTER, 0x2018L, 0L, 0L, 5L),
                    new Event(Kind.WRITE_INT64, 0x2010L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2018L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2000L, 0L, 0L, 0L)
                ),
                Expected.RETURNED,
                Optional.of(InlineStorageCleanupPlan.Path.INLINE),
                List.of(
                    new Cell(0x2010L, 8, 0L, 0L),
                    new Cell(0x2018L, 8, 15L, 0L),
                    new Cell(0x2000L, 1, 0L, 0L)
                )
            ),

            // 2. DIRECT_CALL: capacity >= 16, S < 4096, RCX == 0. Lower skips heap/calls, then reset.
            new Scenario(
                "direct_call_null_pointer_skip",
                Entry.CORE,
                0x1000L, 0x2000L, 0L, 0, 0, 0L,
                List.of(
                    new Cell(0x2018L, 8, 16L, 0L), // capacity = 16
                    new Cell(0x2000L, 8, 0L, 0L)    // P = 0
                ),
                new LowerReturns(0, 0L, 0, 0),
                List.of(
                    new Event(Kind.READ_POINTER, 0x2018L, 0L, 0L, 16L),
                    new Event(Kind.READ_POINTER, 0x2000L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2010L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2018L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2000L, 0L, 0L, 0L)
                ),
                Expected.RETURNED,
                Optional.of(InlineStorageCleanupPlan.Path.DIRECT_CALL),
                List.of(
                    new Cell(0x2010L, 8, 0L, 0L),
                    new Cell(0x2018L, 8, 15L, 0L),
                    new Cell(0x2000L, 1, 0L, 0L)
                )
            ),

            // 3. DIRECT_CALL: capacity = -1 (unsigned max), S = 0 (< 4096), P != 0. Lower fails.
            new Scenario(
                "direct_call_wrap_failure",
                Entry.CORE,
                0x1000L, 0x2000L, 0L, 0, 0, 0L,
                List.of(
                    new Cell(0x2018L, 8, -1L, 0L), // capacity = -1 (unsigned max)
                    new Cell(0x2000L, 8, 0x3000L, 0L), // P = 0x3000
                    new Cell(0x1000L + 0x5C5DE30L, 8, 0x9999L, 0L) // heap handle
                ),
                new LowerReturns(0, 0x4000L, -1, 0x1234), // firstCallBits = 0 (failure)
                List.of(
                    new Event(Kind.READ_POINTER, 0x2018L, 0L, 0L, -1L),
                    new Event(Kind.READ_POINTER, 0x2000L, 0L, 0L, 0x3000L),
                    new Event(Kind.READ_POINTER, 0x1000L + 0x5C5DE30L, 0L, 0L, 0x9999L),
                    new Event(Kind.FIRST_CALL, 0x9999L, 0L, 0x3000L, 0L),
                    new Event(Kind.FAILURE_CELL, 0L, 0L, 0L, 0x4000L),
                    new Event(Kind.LAST_ERROR, 0L, 0L, 0L, 0xFFFFFFFFL),
                    new Event(Kind.MAP_CODE, 0xFFFFFFFFL, 0L, 0L, 0x1234L),
                    new Event(Kind.WRITE_INT32, 0x4000L, 0x1234, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2010L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2018L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2000L, 0L, 0L, 0L)
                ),
                Expected.RETURNED,
                Optional.of(InlineStorageCleanupPlan.Path.DIRECT_CALL),
                List.of(
                    new Cell(0x4000L, 4, 0x1234L, 0L),
                    new Cell(0x2010L, 8, 0L, 0L),
                    new Cell(0x2018L, 8, 15L, 0L),
                    new Cell(0x2000L, 1, 0L, 0L)
                )
            ),

            // 4. ADJUSTED_CALL: capacity >= 16, S >= 4096, delta <= 31. RCX != 0. Lower succeeds (high bit).
            new Scenario(
                "adjusted_call_success_high_bit",
                Entry.CORE,
                0x1000L, 0x2000L, 0L, 0, 0, 0L,
                List.of(
                    new Cell(0x2018L, 8, 5000L, 0L), // capacity = 5000
                    new Cell(0x2000L, 8, 0x3000L, 0L), // P = 0x3000
                    new Cell(0x3000L - 8L, 8, 0x2FF0L, 0L), // H = 0x2FF0 (delta = 8 <= 31)
                    new Cell(0x1000L + 0x5C5DE30L, 8, 0x9999L, 0L) // heap handle
                ),
                new LowerReturns(0x80000000, 0L, 0, 0), // firstCallBits = 0x80000000 (nonzero)
                List.of(
                    new Event(Kind.READ_POINTER, 0x2018L, 0L, 0L, 5000L),
                    new Event(Kind.READ_POINTER, 0x2000L, 0L, 0L, 0x3000L),
                    new Event(Kind.READ_POINTER, 0x2FF8L, 0L, 0L, 0x2FF0L),
                    new Event(Kind.READ_POINTER, 0x1000L + 0x5C5DE30L, 0L, 0L, 0x9999L),
                    new Event(Kind.FIRST_CALL, 0x9999L, 0L, 0x2FF0L, 0x80000000L),
                    new Event(Kind.WRITE_INT64, 0x2010L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2018L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2000L, 0L, 0L, 0L)
                ),
                Expected.RETURNED,
                Optional.of(InlineStorageCleanupPlan.Path.ADJUSTED_CALL),
                List.of(
                    new Cell(0x2010L, 8, 0L, 0L),
                    new Cell(0x2018L, 8, 15L, 0L),
                    new Cell(0x2000L, 1, 0L, 0L)
                )
            ),

            // 5. REJECTED_HEADER: capacity >= 16, S >= 4096, delta > 31. No lower/heap/reset.
            new Scenario(
                "rejected_header_no_effects",
                Entry.CORE,
                0x1000L, 0x2000L, 0L, 0, 0, 0L,
                List.of(
                    new Cell(0x2018L, 8, 5000L, 0L), // capacity = 5000
                    new Cell(0x2000L, 8, 0x3000L, 0L), // P = 0x3000
                    new Cell(0x3000L - 8L, 8, 0x1000L, 0L) // H = 0x1000 (delta = 0x1FF8 > 31)
                ),
                new LowerReturns(0, 0L, 0, 0),
                List.of(
                    new Event(Kind.READ_POINTER, 0x2018L, 0L, 0L, 5000L),
                    new Event(Kind.READ_POINTER, 0x2000L, 0L, 0L, 0x3000L),
                    new Event(Kind.READ_POINTER, 0x2FF8L, 0L, 0L, 0x1000L)
                ),
                Expected.UNSUPPORTED_RESULT,
                Optional.of(InlineStorageCleanupPlan.Path.REJECTED_HEADER),
                List.of(
                    new Cell(0x2018L, 8, 5000L, 0L),
                    new Cell(0x2000L, 8, 0x3000L, 0L),
                    new Cell(0x2FF8L, 8, 0x1000L, 0L)
                )
            ),

            // 6. MOVE_SLOT: Normal cleanup before copy. Storage = bucket + 8.
            new Scenario(
                "move_slot_normal_cleanup",
                Entry.MOVE_SLOT,
                0x1000L, 0x2008L, 0x2000L, 1, -1, 0x3000L,
                List.of(
                    new Cell(0x2020L, 8, 100L, 0L), // capacity at dest+18
                    new Cell(0x2008L, 8, 0x4000L, 0L), // P at dest
                    new Cell(0x1000L + 0x5C5DE30L, 8, 0x9999L, 0L), // heap handle
                    new Cell(0x3000L, 16, 0x1111111111111111L, 0x2222222222222222L), // source raw128
                    new Cell(0x3010L, 16, 0x3333333333333333L, 0x4444444444444444L) // source raw128+16
                ),
                new LowerReturns(1, 0L, 0, 0),
                List.of(
                    new Event(Kind.WRITE_INT32, 0x2000L, -1, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2004L, 1L, 0L, 0L),
                    new Event(Kind.READ_POINTER, 0x2020L, 0L, 0L, 100L),
                    new Event(Kind.READ_POINTER, 0x2008L, 0L, 0L, 0x4000L),
                    new Event(Kind.READ_POINTER, 0x1000L + 0x5C5DE30L, 0L, 0L, 0x9999L),
                    new Event(Kind.FIRST_CALL, 0x9999L, 0L, 0x4000L, 1L),
                    new Event(Kind.WRITE_INT64, 0x2018L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x2020L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2008L, 0L, 0L, 0L),
                    new Event(Kind.READ_RAW128, 0x3000L, 0x1111111111111111L, 0x2222222222222222L, 0L),
                    new Event(Kind.WRITE_RAW128, 0x2008L, 0x1111111111111111L, 0x2222222222222222L, 0L),
                    new Event(Kind.READ_RAW128, 0x3010L, 0x3333333333333333L, 0x4444444444444444L, 0L),
                    new Event(Kind.WRITE_RAW128, 0x2018L, 0x3333333333333333L, 0x4444444444444444L, 0L),
                    new Event(Kind.WRITE_INT64, 0x3010L, 0L, 0L, 0L),
                    new Event(Kind.WRITE_INT64, 0x3018L, 15L, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x3000L, 0L, 0L, 0L)
                ),
                Expected.RETURNED,
                Optional.empty(),
                List.of(
                    new Cell(0x2000L, 4, -1L, 0L),
                    new Cell(0x2004L, 1, 1L, 0L),
                    new Cell(0x2008L, 16, 0x1111111111111111L, 0x2222222222222222L),
                    new Cell(0x2018L, 16, 0x3333333333333333L, 0x4444444444444444L),
                    new Cell(0x3010L, 8, 0L, 0L),
                    new Cell(0x3018L, 8, 15L, 0L),
                    new Cell(0x3000L, 1, 0L, 0L)
                )
            ),

            // 7. MOVE_SLOT: Unsupported cleanup stops before copy. Storage = bucket + 8.
            new Scenario(
                "move_slot_unsupported_stop",
                Entry.MOVE_SLOT,
                0x1000L, 0x2008L, 0x2000L, 1, -1, 0x3000L,
                List.of(
                    new Cell(0x2020L, 8, 5000L, 0L), // capacity at dest+18
                    new Cell(0x2008L, 8, 0x3000L, 0L), // P at dest
                    new Cell(0x3000L - 8L, 8, 0x1000L, 0L) // H at P-8 (delta > 31)
                ),
                new LowerReturns(0, 0L, 0, 0),
                List.of(
                    new Event(Kind.WRITE_INT32, 0x2000L, -1, 0L, 0L),
                    new Event(Kind.WRITE_BYTE, 0x2004L, 1L, 0L, 0L),
                    new Event(Kind.READ_POINTER, 0x2020L, 0L, 0L, 5000L),
                    new Event(Kind.READ_POINTER, 0x2008L, 0L, 0L, 0x3000L),
                    new Event(Kind.READ_POINTER, 0x2FF8L, 0L, 0L, 0x1000L)
                ),
                Expected.THREW_UNSUPPORTED,
                Optional.empty(),
                List.of(
                    new Cell(0x2000L, 4, -1L, 0L),
                    new Cell(0x2004L, 1, 1L, 0L),
                    new Cell(0x2020L, 8, 5000L, 0L),
                    new Cell(0x2008L, 8, 0x3000L, 0L),
                    new Cell(0x2FF8L, 8, 0x1000L, 0L)
                )
            ),

            // 8. FOREIGN_CALLBACK: Identity check fails, throws IAE before any core/memory touch.
            new Scenario(
                "foreign_callback_identity_fail",
                Entry.FOREIGN_CALLBACK,
                0x1000L, 0L, 0L, 0, 0, 0L,
                List.of(),
                new LowerReturns(0, 0L, 0, 0),
                List.of(),
                Expected.THREW_FOREIGN,
                Optional.empty(),
                List.of()
            )
        );
    }
}