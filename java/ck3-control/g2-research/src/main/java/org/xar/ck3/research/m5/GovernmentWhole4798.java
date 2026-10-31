package org.xar.ck3.research.m5;

import java.util.Objects;

/**
 * Owned normal composition for held4798B.
 * Delegates exact phase algorithms without duplication.
 */
public final class GovernmentWhole4798 {
    private GovernmentWhole4798() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWhole4798Api.Memory memory, GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets, GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary) {

        // 1. Initial Frame (612B)
        GovernmentInitialFrame162Api.Join initialJoin = GovernmentInitialFrame162.execute(
                entry, memory, calls.initial(), budgets.initial());

        if (initialJoin.nextRva() != 0x30a3162L) {
            throw new UnsupportedOperationException("Initial frame continuation mismatch: " + Long.toHexString(initialJoin.nextRva()));
        }

        // 2. MXCSR Boundary Check (Strict Precondition)
        GovernmentWhole4798Api.MxcsrObservation initialMxcsrObs = Objects.requireNonNull(mxcsrBoundary.afterInitial(initialJoin), "afterInitial MXCSR observation");
        if (!(initialMxcsrObs instanceof GovernmentWhole4798Api.AvailableMxcsr)) {
            String reason = (initialMxcsrObs instanceof GovernmentWhole4798Api.UnavailableMxcsr)
                    ? ((GovernmentWhole4798Api.UnavailableMxcsr) initialMxcsrObs).reason()
                    : "unknown MXCSR observation type";
            throw new GovernmentWhole4798Api.MxcsrUnavailableException(reason);
        }
        GovernmentLookupLoop580Api.Mxcsr32 lookupMxcsr = ((GovernmentWhole4798Api.AvailableMxcsr) initialMxcsrObs).bits();

        // 3. Lookup Loop (580B)
        // Convert Initial Join to Lookup Entry
        GovernmentLookupLoop580Api.Entry lookupEntry = new GovernmentLookupLoop580Api.Entry(
                new GovernmentCompaction160Api.Entry(
                        initialJoin.imageBaseBits(),
                        initialJoin.frameRspBits(),
                        initialJoin.volatileBits(),
                        initialJoin.nonvolatileBits()),
                lookupMxcsr);

        GovernmentLookupLoop580Api.Join lookupJoin = GovernmentLookupLoop580.execute(
                lookupEntry, memory, calls.lookup(), cpu, budgets.lookup());

        // 4. Earlier Rows (489B)
        // Determine EntryPoint based on Lookup Join nextRva
        GovernmentEarlierRows161Api.EntryPoint entryPoint;
        if (lookupJoin.nextRva() == 0x30a33b8L) {
            entryPoint = GovernmentEarlierRows161Api.EntryPoint.AT_30A33B8;
        } else if (lookupJoin.nextRva() == 0x30a33c2L) {
            entryPoint = GovernmentEarlierRows161Api.EntryPoint.AT_30A33C2;
        } else {
            throw new UnsupportedOperationException("Lookup loop continuation mismatch: " + Long.toHexString(lookupJoin.nextRva()));
        }

        // Convert Lookup Join to Earlier Rows Entry
        GovernmentEarlierRows161Api.Entry earlierEntry = new GovernmentEarlierRows161Api.Entry(
                lookupJoin.raw().imageBaseBits(),
                entryPoint,
                lookupJoin.raw().frameRspBits(),
                lookupJoin.raw().volatileBits(),
                lookupJoin.raw().nonvolatileBits());

        GovernmentEarlierRows161Api.Join earlierJoin = GovernmentEarlierRows161.execute(
                earlierEntry, memory, calls.ordinary(), budgets.earlier());

        // 5. Rows (461B)
        // Determine Start based on Earlier Join nextRva
        GovernmentRows461Api.Start start;
        if (earlierJoin.nextRva() == 0x30a35a1L) {
            start = GovernmentRows461Api.Start.AT_35A1;
        } else if (earlierJoin.nextRva() == 0x30a35a4L) {
            start = GovernmentRows461Api.Start.AT_35A4;
        } else {
            throw new UnsupportedOperationException("Earlier rows continuation mismatch: " + Long.toHexString(earlierJoin.nextRva()));
        }

        // Convert Earlier Join to Rows Entry (via Compaction Entry structure expected by Rows)
        GovernmentCompaction160Api.Entry rowsEntry = new GovernmentCompaction160Api.Entry(
                earlierJoin.imageBaseBits(),
                earlierJoin.frameRspBits(),
                earlierJoin.volatileBits(),
                earlierJoin.nonvolatileBits());

        GovernmentRows461Api.Join rowsJoin = GovernmentRows461.execute(
                start, rowsEntry, memory, calls.ordinary(), budgets.rows());

        if (rowsJoin.nextRva() != 0x30a376eL) {
            throw new UnsupportedOperationException("Rows continuation mismatch: " + Long.toHexString(rowsJoin.nextRva()));
        }

        // 6. Middle Composition (2656B)
        // Convert Rows Join to Middle Entry
        GovernmentCompaction160Api.Entry middleEntry = new GovernmentCompaction160Api.Entry(
                rowsJoin.entry().imageBaseBits(),
                rowsJoin.entry().frameRspBits(),
                rowsJoin.entry().volatileBits(),
                rowsJoin.entry().nonvolatileBits());

        GovernmentMiddle166Api.Result middleResult = GovernmentMiddle166.execute(
                middleEntry, memory, calls.ordinary(), budgets.compaction(),
                calls.lookup155(), calls.prefix153(), calls.post153(), budgets.tail());

        // 7. Final MXCSR Observation
        GovernmentWhole4798Api.MxcsrObservation finalMxcsrObs = Objects.requireNonNull(mxcsrBoundary.afterNormalReturn(middleResult), "final MXCSR observation");

        return new GovernmentWhole4798Api.Result(
                initialJoin,
                (GovernmentWhole4798Api.AvailableMxcsr) initialMxcsrObs,
                lookupJoin,
                earlierJoin,
                rowsJoin,
                middleResult,
                finalMxcsrObs);
    }
}
