package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Snapshot;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.QuoteRow;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Presence;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.War;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Root;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Spending;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.BudgetFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Market;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.FrameRead;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.SourceFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashPolicy;
import org.xar.ck3.control.wave3.planning.warpriorityfocus.WarCashFocusProjection;
import org.xar.ck3.control.wave3.planning.warpriorityfocus.WarCashFocusProjection.FocusedWar;

import static org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.*;

/** Full existing optional construction cash gate; it neither queries nor changes a procurement epoch. */
public final class WartimeConstructionCash {
    public static final BigInteger FIXED_BUFFER = BigInteger.valueOf(40_000_000);
    public static final BigInteger SCALE = BigInteger.valueOf(100_000);
    public static final int MAXIMUM_MAINTENANCE_MONTHS = 24;
    private WartimeConstructionCash() { }

    public static Decision observe(Input input) {
        Kind kind = Kind.of(input.kindWire());
        if (kind == Kind.UNKNOWN) return defer(input, Reason.KIND, Optional.empty(), Optional.empty());
        if (kind == Kind.NEW_HOLDING) return defer(input, Reason.HOLDING, Optional.empty(), Optional.empty());
        Snapshot snapshot = input.context().snapshot();
        if (!snapshot.wars().known()) return defer(input, Reason.WARS, Optional.empty(), Optional.empty());
        if (snapshot.wars().value().isEmpty()) return decision(input, Status.PEACE, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
        if (snapshot.wars().value().stream().anyMatch(war -> !war.warId().known()))
            return defer(input, Reason.WARS, Optional.empty(), Optional.empty());
        if (!nonnegative(input.cost())) return defer(input, Reason.COST, Optional.empty(), Optional.empty());
        if (!snapshot.walletRaw().known() || !equal(snapshot.walletScale(), SCALE))
            return defer(input, Reason.TREASURY, Optional.empty(), Optional.empty());
        Optional<BigInteger> maintenance = maximumMaintenance(snapshot, input.context().root());
        if (maintenance.isEmpty()) return defer(input, Reason.MAINTENANCE, Optional.empty(), Optional.empty());
        Optional<BigInteger> commitments = commitments(snapshot, input.context().spending());
        if (commitments.isEmpty()) return defer(input, Reason.SPENDING, Optional.empty(), Optional.empty());
        if (!input.context().mercenaryPending().known() || input.context().mercenaryPending().value() != Presence.NULL)
            return defer(input, Reason.MERCENARY, Optional.empty(), Optional.empty());
        if (!marketBound(snapshot, input.context().market(), input.context().marketSourceFrame()))
            return defer(input, Reason.MARKET, Optional.empty(), Optional.empty());
        boolean empty = input.marketShape() == MarketShape.EMPTY;
        if (empty) return defer(input, Reason.EMPTY_MARKET, Optional.of(true), Optional.empty());
        Set<BigInteger> hostile = new HashSet<>();
        for (War war : snapshot.wars().value()) for (Read<BigInteger> province : war.enemyProvinces())
            if (province.known()) hostile.add(province.value());
        List<Comparison> comparisons = new ArrayList<>();
        for (QuoteEvidence evidence : input.quotes()) comparisons.add(compare(evidence, hostile));
        List<Comparison> options = comparisons.stream().filter(Comparison::usable).toList();
        Optional<List<Comparison>> compared = Optional.of(comparisons);
        if (options.isEmpty()) return defer(input, Reason.NO_USABLE, Optional.of(false), compared);
        // This producer computes the real cash-protection reasons/order from the original snapshot.
        // No focus, deficit or priority GREEN is accepted from the construction input JSON.
        Optional<FocusedWar> focus = WarCashFocusProjection.observe(input.focusRequest().decodeRequired());
        Optional<BigInteger> deficit = focus.filter(war -> war.observedPlayerRaisedSoldiers().isPresent()
                && war.observedEnemyRaisedSoldiers().isPresent()).map(war -> war.observedEnemyRaisedSoldiers().orElseThrow()
                .subtract(war.observedPlayerRaisedSoldiers().orElseThrow()).max(BigInteger.ZERO));
        Optional<Comparison> approved = approved(input.procurement(), snapshot, focus, deficit, options);
        List<Comparison> adequate = options.stream().filter(row -> deficit.filter(value -> value.signum() > 0).isPresent()
                && row.soldiers().value().compareTo(deficit.orElseThrow()) >= 0).toList();
        Comparator<Comparison> quoteOrder = Comparator.comparing((Comparison row) -> row.contractGold().orElseThrow())
                .thenComparing(row -> row.companyId().value());
        Comparison chosen;
        SelectionBasis basis;
        if (approved.isPresent()) { chosen = approved.orElseThrow(); basis = SelectionBasis.ASSESSED; }
        else if (!adequate.isEmpty()) { chosen = adequate.stream().min(quoteOrder).orElseThrow(); basis = SelectionBasis.CHEAPEST_ADEQUATE; }
        else { chosen = options.stream().max(quoteOrder).orElseThrow(); basis = SelectionBasis.CONSERVATIVE_MAXIMUM; }
        BigInteger military = FIXED_BUFFER.max(maintenance.orElseThrow().multiply(BigInteger.valueOf(MAXIMUM_MAINTENANCE_MONTHS)));
        BigInteger required = military.add(commitments.orElseThrow()).add(chosen.contractGold().orElseThrow());
        BigInteger after = snapshot.walletRaw().value().subtract(input.cost().value());
        Reserve reserve = new Reserve(snapshot.walletRaw().value(), after, required, maintenance.orElseThrow(), military,
                commitments.orElseThrow(), chosen, basis, focus.map(FocusedWar::warId), deficit);
        boolean ample = after.compareTo(required) >= 0;
        return decision(input, ample ? Status.AMPLE : Status.DEFER, Optional.of(ample ? Reason.RETAIN : Reason.NOT_AMPLE),
                Optional.of(false), compared, Optional.of(reserve));
    }

    private static Comparison compare(QuoteEvidence evidence, Set<BigInteger> hostile) {
        QuoteRow quote = evidence.quote();
        if (evidence.groups() == GroupShape.INCOMPLETE) return new Comparison(quote.companyId(), false, false,
                Optional.empty(), quote.currentSoldiers(), QuoteReason.INCOMPLETE);
        boolean completeCost = quote.costs().known() && quote.costs().value().size() == 10
                && quote.costs().value().stream().allMatch(amount -> amount.signum() >= 0)
                && equal(quote.resourceScale(), SCALE) && yes(quote.available());
        boolean usable = GiftWarCashPolicy.usableEmergencyQuote(quote, hostile);
        return new Comparison(quote.companyId(), true, usable,
                completeCost ? Optional.of(quote.costs().value().getFirst()) : Optional.empty(), quote.currentSoldiers(),
                usable ? QuoteReason.USABLE : QuoteReason.NOT_READY);
    }

    private static Optional<Comparison> approved(Read<ProcurementCandidate> read, Snapshot snapshot,
            Optional<FocusedWar> focus, Optional<BigInteger> deficit, List<Comparison> options) {
        if (!read.known() || !read.value().emptyRejections() || !read.value().financeFrame().known()
                || focus.isEmpty() || deficit.isEmpty()) return Optional.empty();
        ProcurementCandidate chosen = read.value(); FinanceFrame frame = chosen.financeFrame().value();
        if (!frame.exactKeys() || !same(frame.actor(), snapshot.actor())
                || !equal(frame.revision(), snapshot.frame().nativeRevision()) || !equal(frame.date(), snapshot.frame().dateRaw())
                || !chosen.purposeWars().known() || !chosen.purposeWars().value().contains(focus.orElseThrow().warId())) return Optional.empty();
        return options.stream().filter(row -> same(row.companyId(), chosen.companyId())
                && chosen.goldCost().known() && row.contractGold().orElseThrow().equals(chosen.goldCost().value())
                && row.soldiers().value().compareTo(deficit.orElseThrow()) >= 0).findFirst();
    }

    private static Optional<BigInteger> maximumMaintenance(Snapshot snapshot, Read<Root> read) {
        if (!read.known()) return Optional.empty();
        Root root = read.value();
        return equal(root.status(), "available") && same(root.playerCharacterId(), snapshot.actor())
                && equal(root.snapshotRevision(), snapshot.frame().nativeRevision()) && equal(root.dateRaw(), snapshot.frame().dateRaw())
                && equal(root.maximumStatus(), "available") && nonnegative(root.maintenanceRaw()) && equal(root.maintenanceScale(), SCALE)
                ? Optional.of(root.maintenanceRaw().value()) : Optional.empty();
    }
    private static Optional<BigInteger> commitments(Snapshot snapshot, Read<Spending> read) {
        if (!read.known() || !equal(read.value().status(), "observed") || !read.value().frame().known()) return Optional.empty();
        Spending spending = read.value(); BudgetFrame frame = spending.frame().value();
        return frame.exactFields() && same(frame.actorCharacterId(), snapshot.actor())
                && equal(frame.nativeRevision(), snapshot.frame().nativeRevision()) && equal(frame.dateRaw(), snapshot.frame().dateRaw())
                && equal(frame.snapshotId(), snapshot.frame().snapshotId()) && nonnegative(spending.reservedGoldRaw())
                && equal(spending.activeWarCount(), BigInteger.valueOf(snapshot.wars().value().size()))
                ? Optional.of(spending.reservedGoldRaw().value()) : Optional.empty();
    }
    private static boolean marketBound(Snapshot snapshot, Read<Market> read, Read<FrameRead> sourceRead) {
        if (!read.known() || !sourceRead.known()) return false;
        Market market = read.value(); FrameRead frame = sourceRead.value(); SourceFrame source = snapshot.frame();
        return yes(market.available()) && same(market.actorCharacterId(), snapshot.actor())
                && equal(market.dateRaw(), source.dateRaw()) && market.rows().known() && frame.exactFields()
                && equal(frame.playedCharacterId(), source.playedCharacterId()) && equal(frame.nativeRevision(), source.nativeRevision())
                && equal(frame.dateRaw(), source.dateRaw()) && equal(frame.snapshotId(), source.snapshotId())
                && equal(frame.revision(), source.revision()) && equal(frame.episodeRunId(), source.episodeRunId());
    }
    private static Decision defer(Input input, Reason reason, Optional<Boolean> empty, Optional<List<Comparison>> comparisons) {
        return decision(input, Status.DEFER, Optional.of(reason), empty, comparisons, Optional.empty());
    }
    private static Decision decision(Input input, Status status, Optional<Reason> reason, Optional<Boolean> empty,
            Optional<List<Comparison>> comparisons, Optional<Reserve> reserve) {
        return new Decision(input.context().snapshot().frame(), input.kindWire(), input.cost(), status, reason, empty, comparisons, reserve);
    }
    private static boolean nonnegative(Read<BigInteger> read) { return read.known() && read.value().signum() >= 0; }
    private static boolean yes(Read<Boolean> read) { return read.known() && read.value(); }
    private static <T> boolean equal(Read<T> read, T value) { return read.known() && read.value().equals(value); }
    private static <T> boolean same(Read<T> left, Read<T> right) { return left.known() && right.known() && left.value().equals(right.value()); }
}
