package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.SlotProducerGrowthWithFp618;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageFp619;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageSetFp620;
import org.xar.ck3.control.g2.m2.nativecode.SlotReserveWithFp615;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.KnownSetFp617;


/**
 * Thin assembly class connecting SlotProducerGrowthWithFp618 to KnownPageFp619 and KnownPageSetFp620.
 * No algorithm duplication, no state repair, no direct memory/register operations.
 */
public final class SlotProducerKnownPageSetFp621 {
    private SlotProducerKnownPageSetFp621() { }

    public static QueueFp604Api.Outcome execute(
            SlotProducerGrowthWithFp618.Input input,
            KnownPageFp619.Memory memory,
            SlotProducerGrowthWithFp618.Calls otherProducerCalls,
            KnownPageFp619.Calls otherPageCalls,
            SlotReserveWithFp615.Calls reserveOtherCalls,
            FullCopyWithFp613.TailCalls unknownCopyTails,
            KnownSetFp617.TailCalls unknownReserveSetTails,
            KnownPageSetFp620.TailCalls unknownPageSetTails) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherProducerCalls);
        Objects.requireNonNull(otherPageCalls);
        Objects.requireNonNull(reserveOtherCalls);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(unknownReserveSetTails);
        Objects.requireNonNull(unknownPageSetTails);

        // Bind the page SET handler (620) first, using the exact same memory and budget.
        // This handler routes the three Page SET edges (2A3227C, 2A322EE, 2A32325) to M1 206/207.
        KnownPageFp619.Calls pageHandler = KnownPageSetFp620.bind(
                memory,
                input.base().budget(),
                unknownPageSetTails,
                otherPageCalls);

        // Bind the upper Page handler (619) next, using the exact same memory and budget.
        // This handler routes the 2A327E7 -> Page 381 edge to the known Page implementation.
        SlotProducerGrowthWithFp618.Calls producerHandler = KnownPageFp619.bind(
                memory,
                input.base().budget(),
                pageHandler,
                otherProducerCalls);

        // Execute the complete 470B producer growth path once with the assembled handlers.
        // The 618 implementation internally handles the reserve edge (2A327CE -> 1ACDFB0)
        // using the provided reserveOtherCalls and unknownReserveSetTails.
        return SlotProducerGrowthWithFp618.execute(
                input,
                memory,
                producerHandler,
                reserveOtherCalls,
                unknownCopyTails,
                unknownReserveSetTails);
    }
}