package org.xar.ck3.research.m3;

import java.util.List;

public final class MapRehashBook190 {
    private MapRehashBook190() { }

    public enum Action { GROW, REHASH }
    public enum Kind {
        READ_POINTER, READ_INT32, READ8, WRITE_INT64, WRITE_INT32, WRITE8,
        GS58, INIT_HEADER, INIT_FOOTER, ALLOCATE08, FREE10,
        INSERT, CLEANUP, ERROR_BUILD, ERROR_THROW
    }
    public record Cell(long address, int width, long value) { }
    public record Event(Kind kind, long a, long b, long c, long d, long e,
                        long returned, List<Cell> writesAfter) { }
    public record Scenario(String id, Action action, long moduleBase, long map,
                           int exponent, long entryRsp, List<Cell> initial,
                           List<Event> expected, MapRehashApi190.Completion completion) { }

    private static Cell c(long a, int w, long v) { return new Cell(a, w, v); }
    private static Event x(Kind k, long a, long b, long c, long d, long e, long r, Cell... after) {
        return new Event(k, a, b, c, d, e, r, List.of(after));
    }
    private static Event rp(long a, long r) { return x(Kind.READ_POINTER, a, 0, 0, 0, 0, r); }
    private static Event ri(long a, long r) { return x(Kind.READ_INT32, a, 0, 0, 0, 0, r); }
    private static Event r8(long a, long r) { return x(Kind.READ8, a, 0, 0, 0, 0, r); }
    private static Event w64(long a, long v) { return x(Kind.WRITE_INT64, a, v, 0, 0, 0, 0); }
    private static Event w32(long a, long v) { return x(Kind.WRITE_INT32, a, v, 0, 0, 0, 0); }
    private static Event w8(long a, long v) { return x(Kind.WRITE8, a, v, 0, 0, 0, 0); }
    private static Event gs(long r, Cell... after) { return x(Kind.GS58, 0, 0, 0, 0, 0, r, after); }

    public static List<Scenario> cases() {
        return List.of(
            new Scenario("grow_ordinary_fresh_limit", Action.GROW, 0, 0x1000, 0, 0x9000,
                List.of(c(0x1014, 4, 0), c(0x1008, 8, 0x5D1F5E0), c(0x1010, 4, 0),
                    c(0x1020, 8, 0x2000), c(0x2000, 8, 0x3000), c(0x3008, 8, 0x4000),
                    c(0x6000, 8, 0x6100), c(0x6110, 4, 5), c(0x5D1F630, 4, 0)),
                List.of(
                    ri(0x1014, 0), rp(0x1008, 0x5D1F5E0), w8(0x1018, 5),
                    rp(0x1020, 0x2000), ri(0x1010, 0), w32(0x1010, 0), w32(0x1014, 7),
                    rp(0x2000, 0x3000), rp(0x3008, 0x4000),
                    x(Kind.ALLOCATE08, 0x4000, 0x2000, 560, 8, 0, 0x5000, c(0x1018, 1, 0)),
                    r8(0x1018, 0), w64(0x1008, 0x5000),
                    w8(0x5004, 0), w8(0x502C, 0), w8(0x5054, 0), w8(0x507C, 0),
                    w8(0x50A4, 0), w8(0x50CC, 0), w8(0x50F4, 0), w8(0x511C, 0), w8(0x5144, 255),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0)),
                MapRehashApi190.Completion.RETURNED),

            new Scenario("grow_error_preserves_supplied_high_half", Action.GROW, 0, 0x1000, 0, 0x9000,
                List.of(c(0x1014, 4, 0x3FFFFFFF), c(0x9008, 8, 0xAABBCCDDEEFF0011L),
                    c(0x9010, 8, 0x2233445566778899L)),
                List.of(ri(0x1014, 0x3FFFFFFF),
                    x(Kind.ERROR_BUILD, 0x9008, 0x1000, 0, 0, 0, 0,
                        c(0x9008, 8, 0x1122334455667788L)),
                    x(Kind.ERROR_THROW, 0, 0, 0, 0, 0, 0)),
                MapRehashApi190.Completion.UNSUPPORTED_INT3_AFTER_ERROR_CALLS_RETURNED),

            new Scenario("rehash_invalid_zero", Action.REHASH, 0, 0x1000, 0, 0x9000,
                List.of(), List.of(), MapRehashApi190.Completion.RETURNED),

            new Scenario("rehash_invalid_thirty_one", Action.REHASH, 0, 0x1000, 31, 0x9000,
                List.of(), List.of(), MapRehashApi190.Completion.RETURNED),

            new Scenario("rehash_static_old_base_skips_positive_count", Action.REHASH, 0, 0x1000, 1, 0x9000,
                List.of(c(0x1008, 8, 0x5D1F5E0), c(0x1010, 4, 7), c(0x1020, 8, 0x2000),
                    c(0x2000, 8, 0x3000), c(0x3008, 8, 0x4000),
                    c(0x6000, 8, 0x6100), c(0x6110, 4, 5), c(0x5D1F630, 4, 0)),
                List.of(
                    rp(0x1008, 0x5D1F5E0), w8(0x1018, 3), rp(0x1020, 0x2000), ri(0x1010, 7),
                    w32(0x1010, 0), w32(0x1014, 1), rp(0x2000, 0x3000), rp(0x3008, 0x4000),
                    x(Kind.ALLOCATE08, 0x4000, 0x2000, 240, 8, 0, 0x5000),
                    r8(0x1018, 3), w64(0x1008, 0x5000),
                    w8(0x5004, 0), w8(0x502C, 0), w8(0x5054, 0), w8(0x507C, 0), w8(0x50A4, 0),
                    w8(0x50CC, 255),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0)),
                MapRehashApi190.Completion.RETURNED),

            new Scenario("rehash_captured_negative_count_fresh_allocator", Action.REHASH, 0, 0x1000, 1, 0x9000,
                List.of(c(0x1008, 8, 0x7000), c(0x1010, 4, -1), c(0x1020, 8, 0x2000),
                    c(0x2000, 8, 0x3000), c(0x3008, 8, 0x4000),
                    c(0x2200, 8, 0x3200), c(0x3210, 8, 0x4210),
                    c(0x6000, 8, 0x6100), c(0x6110, 4, 5), c(0x5D1F630, 4, 0)),
                List.of(
                    rp(0x1008, 0x7000), w8(0x1018, 3), rp(0x1020, 0x2000), ri(0x1010, -1),
                    w32(0x1010, 0), w32(0x1014, 1), rp(0x2000, 0x3000), rp(0x3008, 0x4000),
                    x(Kind.ALLOCATE08, 0x4000, 0x2000, 240, 8, 0, 0x5000,
                        c(0x1020, 8, 0x2200), c(0x1010, 4, 123)),
                    r8(0x1018, 3), w64(0x1008, 0x5000),
                    w8(0x5004, 0), w8(0x502C, 0), w8(0x5054, 0), w8(0x507C, 0), w8(0x50A4, 0),
                    w8(0x50CC, 255),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    rp(0x1020, 0x2200), rp(0x2200, 0x3200), rp(0x3210, 0x4210),
                    x(Kind.FREE10, 0x4210, 0x2200, 0x7000, 8, 0, 0)),
                MapRehashApi190.Completion.RETURNED),

            new Scenario("rehash_empty_then_two_occupied_captured_count", Action.REHASH, 0, 0x1000, 1, 0x9000,
                List.of(c(0x1008, 8, 0x7000), c(0x1010, 4, 2), c(0x1020, 8, 0x2000),
                    c(0x2000, 8, 0x3000), c(0x3008, 8, 0x4000), c(0x2200, 8, 0x3200), c(0x3210, 8, 0x4210),
                    c(0x6000, 8, 0x6100), c(0x6110, 4, 5), c(0x5D1F630, 4, 0),
                    c(0x7004, 1, 0), c(0x702C, 1, 1), c(0x7028, 4, 0x12345678),
                    c(0x7054, 1, 0), c(0x7050, 4, 0x7777),
                    c(0x8FD8, 8, 0x7F7F7F7F7F7F7F7FL), c(0x8FE8, 8, 0x1122334455667788L),
                    c(0x8FF0, 8, 0x99AABBCCDDEEFF00L), c(0x9010, 1, 127)),
                List.of(
                    rp(0x1008, 0x7000), w8(0x1018, 3), rp(0x1020, 0x2000), ri(0x1010, 2),
                    w32(0x1010, 0), w32(0x1014, 1), rp(0x2000, 0x3000), rp(0x3008, 0x4000),
                    x(Kind.ALLOCATE08, 0x4000, 0x2000, 240, 8, 0, 0x5000, c(0x1018, 1, 0)),
                    r8(0x1018, 0), w64(0x1008, 0x5000),
                    w8(0x5004, 0), w8(0x502C, 0), w8(0x5054, 255),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    r8(0x7004, 0), r8(0x702C, 1), ri(0x7028, 0x12345678),
                    w64(0x8FD8, 0x9010), w8(0x9010, 0),
                    x(Kind.INSERT, 0x1000, 0x8FE8, 0x12345678, 0x7030, 0x9010, 0,
                        c(0x1010, 4, -7), c(0x1020, 8, 0x2200), c(0x7054, 1, 2),
                        c(0x7050, 4, -11), c(0x8FE8, 8, 0xABCDEF), c(0x9010, 1, 1)),
                    x(Kind.CLEANUP, 0x7030, 0, 0, 0, 0, 0),
                    r8(0x7054, 2), ri(0x7050, -11), w64(0x8FD8, 0x9010), w8(0x9010, 0),
                    x(Kind.INSERT, 0x1000, 0x8FE8, -11, 0x7058, 0x9010, 0,
                        c(0x8FE8, 8, 0xFEDCBA), c(0x9010, 1, 2)),
                    x(Kind.CLEANUP, 0x7058, 0, 0, 0, 0, 0),
                    gs(0x6000), rp(0x6000, 0x6100), ri(0x6110, 5), ri(0x5D1F630, 0),
                    rp(0x1020, 0x2200), rp(0x2200, 0x3200), rp(0x3210, 0x4210),
                    x(Kind.FREE10, 0x4210, 0x2200, 0x7000, 8, 0, 0)),
                MapRehashApi190.Completion.RETURNED)
        );
    }
}
