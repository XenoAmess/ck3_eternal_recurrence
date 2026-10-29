package org.xar.ck3.control.wave2.finance.giftwarcash;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.BudgetFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Candidate;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Choice;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Decision;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.EmergencyQuote;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.FrameRead;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.GiftObservation;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Market;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Presence;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.QuoteRow;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reason;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Request;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reserve;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Root;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Snapshot;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.SourceFrame;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Spending;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Status;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Treasury;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.War;

/** Pure optional-spend guard. It neither queries CK3 nor requalifies existing submitted gifts. */
public final class GiftWarCashPolicy {
    public static final BigInteger MILITARY_FLOOR_RAW = BigInteger.valueOf(20_000_000);
    public static final BigInteger RESOURCE_SCALE = BigInteger.valueOf(100_000);
    public static final int MAINTENANCE_MONTHS = 18;
    private GiftWarCashPolicy() { }

    public static Decision assess(Request request) {
        Objects.requireNonNull(request); Snapshot snapshot = request.snapshot(); SourceFrame frame = snapshot.frame();
        if (!snapshot.wars().known() || snapshot.wars().value().stream()
                .anyMatch(war -> !positive(war.warId()))) { return defer(frame, Reason.WAR_SCOPE, null); }
        List<War> wars = snapshot.wars().value();
        if (wars.isEmpty()) { return new Decision(frame, Status.OUTSIDE_WARTIME, null, null, null); }
        Treasury treasury = quote(snapshot, request.candidate());
        if (treasury == null) { return defer(frame, Reason.GIFT_QUOTE, null); }
        // A proven failed lower bound is conclusive before unknown maintenance/commitments/market.
        if (treasury.afterGiftRaw().compareTo(MILITARY_FLOOR_RAW) < 0) {
            return defer(frame, Reason.MILITARY_FLOOR, treasury);
        }
        BigInteger rate = rate(snapshot, request.root());
        if (rate == null) { return defer(frame, Reason.MAINTENANCE, treasury); }
        BigInteger commitments = commitments(snapshot, request.spending());
        if (commitments == null) { return defer(frame, Reason.SPENDING, treasury); }
        if (!request.mercenaryPending().known() || request.mercenaryPending().value() != Presence.NULL) {
            return defer(frame, Reason.MERCENARY, treasury);
        }
        if (!marketBound(snapshot, request.market(), request.marketSourceFrame())) {
            return defer(frame, Reason.MARKET, treasury);
        }
        Set<BigInteger> hostile = new HashSet<>();
        for (War war : wars) {
            for (Read<BigInteger> province : war.enemyProvinces()) { if (province.known()) { hostile.add(province.value()); } }
        }
        List<EmergencyQuote> quotes = new ArrayList<>();
        for (QuoteRow row : request.market().value().rows().value()) {
            if (usableEmergencyQuote(row, hostile)) { quotes.add(new EmergencyQuote(row.companyId().value(), row.costs().value().getFirst())); }
        }
        if (quotes.isEmpty()) { return defer(frame, Reason.NO_USABLE_QUOTE, treasury); }
        EmergencyQuote selected = quotes.stream().max(Comparator.comparing(EmergencyQuote::completeContractGoldRaw)
                .thenComparing(EmergencyQuote::companyId)).orElseThrow();
        BigInteger military = MILITARY_FLOOR_RAW.max(rate.multiply(BigInteger.valueOf(MAINTENANCE_MONTHS)));
        Reserve reserve = new Reserve(military, commitments, selected, quotes.size());
        Status status = treasury.afterGiftRaw().compareTo(reserve.requiredRaw()) >= 0
                ? Status.WAR_CASH_RETAINED : Status.DEFER_NEW_GIFT;
        return new Decision(frame, status, Reason.RETAIN_RESERVE, treasury, reserve);
    }

    private static Decision defer(SourceFrame frame, Reason reason, Treasury treasury) {
        return new Decision(frame, Status.DEFER_NEW_GIFT, reason, treasury, null);
    }
    private static Treasury quote(Snapshot snapshot, Read<Candidate> read) {
        if (!read.known() || !read.value().choice().known() || !read.value().observation().known()) { return null; }
        Choice choice = read.value().choice().value(); GiftObservation observed = read.value().observation().value();
        SourceFrame frame = snapshot.frame();
        if (!same(choice.playerCharacterId(), snapshot.actor()) || !equal(choice.nativeRevision(), frame.nativeRevision())
                || !equal(choice.dateRaw(), frame.dateRaw()) || !equal(observed.nativeRevision(), frame.nativeRevision())
                || !equal(observed.observedDateRaw(), frame.dateRaw()) || !same(observed.playerCharacterId(), snapshot.actor())
                || !equal(snapshot.walletScale(), RESOURCE_SCALE) || !snapshot.walletRaw().known()
                || !equal(observed.playerGoldScale(), RESOURCE_SCALE) || !same(observed.playerGoldRaw(), snapshot.walletRaw())
                || !nonnegative(choice.giftCostRaw()) || !same(observed.previewGoldCostRaw(), choice.giftCostRaw())) { return null; }
        BigInteger wallet = snapshot.walletRaw().value(); BigInteger cost = choice.giftCostRaw().value();
        return new Treasury(wallet, cost, wallet.subtract(cost));
    }
    private static BigInteger rate(Snapshot snapshot, Read<Root> read) {
        if (!read.known()) { return null; } Root root = read.value(); SourceFrame frame = snapshot.frame();
        return equal(root.status(), "available") && same(root.playerCharacterId(), snapshot.actor())
                && equal(root.snapshotRevision(), frame.nativeRevision()) && equal(root.dateRaw(), frame.dateRaw())
                && equal(root.maximumStatus(), "available") && equal(root.maintenanceScale(), RESOURCE_SCALE)
                && nonnegative(root.maintenanceRaw()) ? root.maintenanceRaw().value() : null;
    }
    private static BigInteger commitments(Snapshot snapshot, Read<Spending> read) {
        if (!read.known()) { return null; } Spending spending = read.value();
        if (!equal(spending.status(), "observed") || !spending.frame().known()) { return null; }
        BudgetFrame frame = spending.frame().value();
        return frame.exactFields() && same(frame.actorCharacterId(), snapshot.actor())
                && equal(frame.nativeRevision(), snapshot.frame().nativeRevision())
                && equal(frame.dateRaw(), snapshot.frame().dateRaw()) && equal(frame.snapshotId(), snapshot.frame().snapshotId())
                && nonnegative(spending.reservedGoldRaw())
                && equal(spending.activeWarCount(), BigInteger.valueOf(snapshot.wars().value().size()))
                ? spending.reservedGoldRaw().value() : null;
    }
    private static boolean marketBound(Snapshot snapshot, Read<Market> read, Read<FrameRead> frameRead) {
        if (!read.known() || !frameRead.known()) { return false; }
        Market market = read.value(); FrameRead frame = frameRead.value(); SourceFrame source = snapshot.frame();
        return yes(market.available()) && same(market.actorCharacterId(), snapshot.actor())
                && equal(market.dateRaw(), source.dateRaw()) && market.rows().known() && frame.exactFields()
                && equal(frame.playedCharacterId(), source.playedCharacterId()) && equal(frame.nativeRevision(), source.nativeRevision())
                && equal(frame.dateRaw(), source.dateRaw()) && equal(frame.snapshotId(), source.snapshotId())
                && equal(frame.revision(), source.revision()) && equal(frame.episodeRunId(), source.episodeRunId());
    }
    /** Native quote predicate only; each consuming policy owns its financial and strategic approval. */
    public static boolean usableEmergencyQuote(QuoteRow row, Set<BigInteger> hostile) {
        Objects.requireNonNull(row); Objects.requireNonNull(hostile);
        return row.costs().known() && row.costs().value().size() == 10
                && row.costs().value().stream().allMatch(value -> value.signum() >= 0)
                && equal(row.resourceScale(), RESOURCE_SCALE) && yes(row.available()) && yes(row.canHire())
                && yes(row.canAfford()) && yes(row.hireReady()) && row.employer() != Presence.VALUE
                && nonnegative(row.companyId()) && yes(row.troopsAvailable()) && positive(row.currentSoldiers())
                && positive(row.spawnProvince()) && yes(row.positionReady()) && yes(row.attemptedInActiveWar())
                && !hostile.contains(row.spawnProvince().value());
    }
    private static boolean positive(Read<BigInteger> read) { return read.known() && read.value().signum() > 0; }
    private static boolean nonnegative(Read<BigInteger> read) { return read.known() && read.value().signum() >= 0; }
    private static boolean yes(Read<Boolean> read) { return read.known() && read.value().booleanValue(); }
    private static <T> boolean equal(Read<T> read, T value) { return read.known() && read.value().equals(value); }
    private static <T> boolean same(Read<T> left, Read<T> right) {
        return left.known() && right.known() && left.value().equals(right.value());
    }
}
