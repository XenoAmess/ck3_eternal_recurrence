package org.xar.ck3.research.m3;
import java.util.List;
import org.xar.ck3.research.m3.C3e150Api180.Memory;
import org.xar.ck3.research.m3.C3e150Api180.Ports;

public final class StaticTableBaseBook180 {
    private StaticTableBaseBook180() { }

    public enum Kind { GS58, READ_POINTER, READ_DWORD, HEADER, WRITE_BYTE, FOOTER }

    public record Event(Kind kind, long address, long value) { }

    public record Scenario(String id, long moduleBase, long gs58, long tlsModule,
            int tlsEpoch, int guardBefore, int guardAfterHeader, List<Event> expectedEvents,
            long expectedReturned) { }

    public static List<Scenario> cases() {
        List<Scenario> list = new java.util.ArrayList<>();
        long mb = 0x10000000L;
        long gs = 0x20000000L;
        long tls = 0x30000000L;
        int ep = 100;
        int gb = 200;
        int ga = 300;
        int gaNeg = -1;
        int gaZero = 0;
        int gaMax = Integer.MAX_VALUE;
        int gaMin = Integer.MIN_VALUE;
        int epMax = Integer.MAX_VALUE;
        int epMin = Integer.MIN_VALUE;
        int gbMax = Integer.MAX_VALUE;
        int gbMin = Integer.MIN_VALUE;

        // 1. Equality: guardBefore == tlsEpoch -> no header
        list.add(new Scenario("eq", mb, gs, tls, ep, ep, ga, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, ep & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, ep & 0xFFFFFFFFL)
        ), mb + 0x5D1F5E0));

        // 2. Less: guardBefore < tlsEpoch -> no header
        list.add(new Scenario("lt", mb, gs, tls, ep, ep - 1, ga, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, ep & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, (ep - 1) & 0xFFFFFFFFL)
        ), mb + 0x5D1F5E0));

        // 3. Greater, after != -1 -> header, fresh read, return
        list.add(new Scenario("gt_ne", mb, gs, tls, ep, ep + 1, ga, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, ep & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, (ep + 1) & 0xFFFFFFFFL),
            new Event(Kind.HEADER, mb + 0x5D1F630, 0),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, ga & 0xFFFFFFFFL)
        ), mb + 0x5D1F5E0));

        // 4. Greater, after == -1 -> header, fresh read, writes, footer, LEA return
        list.add(new Scenario("gt_eq_neg1", mb, gs, tls, ep, ep + 1, gaNeg, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, ep & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, (ep + 1) & 0xFFFFFFFFL),
            new Event(Kind.HEADER, mb + 0x5D1F630, 0),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, gaNeg & 0xFFFFFFFFL),
            new Event(Kind.WRITE_BYTE, mb + 0x5D1F5E4, 0),
            new Event(Kind.WRITE_BYTE, mb + 0x5D1F60C, 255),
            new Event(Kind.FOOTER, mb + 0x5D1F630, 0)
        ), mb + 0x5D1F5E0));

        // 5. Signed MAX guard / MIN tls: guardBefore > tlsEpoch -> header path
        list.add(new Scenario("max_min", mb, gs, tls, epMin, gbMax, ga, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, epMin & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, gbMax & 0xFFFFFFFFL),
            new Event(Kind.HEADER, mb + 0x5D1F630, 0),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, ga & 0xFFFFFFFFL)
        ), mb + 0x5D1F5E0));

        // 6. Signed MIN guard / MAX tls: guardBefore < tlsEpoch -> no header
        list.add(new Scenario("min_max", mb, gs, tls, epMax, gbMin, ga, List.of(
            new Event(Kind.GS58, 0, gs),
            new Event(Kind.READ_POINTER, gs, tls),
            new Event(Kind.READ_DWORD, tls + 0x10, epMax & 0xFFFFFFFFL),
            new Event(Kind.READ_DWORD, mb + 0x5D1F630, gbMin & 0xFFFFFFFFL)
        ), mb + 0x5D1F5E0));

        return list;
    }
}
