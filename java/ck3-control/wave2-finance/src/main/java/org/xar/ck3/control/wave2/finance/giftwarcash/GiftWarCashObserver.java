package org.xar.ck3.control.wave2.finance.giftwarcash;

import java.util.Objects;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Candidate;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Decision;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.FrameRead;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Market;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Presence;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reason;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Request;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Root;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Snapshot;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Spending;

/** Application seam for the original wrapper's existing observations, with no new native query. */
public final class GiftWarCashObserver {
    private GiftWarCashObserver() { }
    public sealed interface ExistingInputs permits NoStateDirectory, StoredInputs { }
    public record NoStateDirectory() implements ExistingInputs { }
    public record StoredInputs(Read<Spending> spending, Read<Market> market,
            Read<FrameRead> marketSourceFrame, Read<Presence> mercenaryPending) implements ExistingInputs {
        public StoredInputs {
            Objects.requireNonNull(spending); Objects.requireNonNull(market);
            Objects.requireNonNull(marketSourceFrame); Objects.requireNonNull(mercenaryPending);
        }
    }
    @FunctionalInterface
    public interface CurrentInputsPort {
        /** Read the original bounded ledgers and already captured same-frame history. Never query CK3. */
        ExistingInputs readExisting(Snapshot snapshot, Read<Root> sameFrameRoot);
    }

    public static Decision observe(Snapshot snapshot, Read<Candidate> candidate, Read<Root> root,
            CurrentInputsPort port) {
        Objects.requireNonNull(port);
        Decision early = GiftWarCashPolicy.assess(new Request(snapshot, candidate, root,
                Read.nil(), Read.nil(), Read.nil(), Read.nil()));
        if (early.reason() != Reason.SPENDING) { return early; }
        ExistingInputs existing = Objects.requireNonNull(port.readExisting(snapshot, root));
        if (existing instanceof NoStateDirectory) { return early; }
        if (existing instanceof StoredInputs inputs) {
            return GiftWarCashPolicy.assess(new Request(snapshot, candidate, root, inputs.spending(),
                    inputs.market(), inputs.marketSourceFrame(), inputs.mercenaryPending()));
        }
        throw new IllegalArgumentException("unsupported current input branch");
    }
}
