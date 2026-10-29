package org.xar.ck3.control.wave2.development.constructionscene;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.*;

/** Pure same-frame scene and current Clan NET binding, retaining the original reverse-history order. */
public final class ConstructionScenePolicy {
    public static final String ROOT_QUERY_STEP = "query-campaign-root-context-v1";
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private ConstructionScenePolicy() { }

    public static Scope scope(SceneInput input) {
        RootScope original = sameFrameRootScope(input, false, true);
        return switch (original.status()) {
            case SCOPE_UNAVAILABLE -> new Unavailable();
            case ROOT_QUERY_NEEDED -> new RootQueryNeeded(original.atPeace());
            case ADMITTED -> new Admitted(original.atPeace(), Government.FEUDAL, original.revision(), original.actorId(), original.collectTaxesActive());
            case OUTSIDE_SCENE -> {
                GovernmentObservation government = original.government();
                if (government != null && government.key().is("clan_government") && government.flags().known()
                        && government.flags().value().contains("government_is_clan")) {
                    yield new Admitted(original.atPeace(), Government.CLAN, original.revision(), original.actorId(), Field.missing());
                }
                yield new OutsideScene(original.atPeace());
            }
        };
    }

    /** Complete shared original helper for construction and existing peace/lifestyle/player-perk wrappers. */
    public static RootScope sameFrameRootScope(SceneInput input, boolean requirePeace, boolean requireFeudal) {
        Snapshot snapshot = input.snapshot();
        if (!snapshot.paused().is(true) || !snapshot.activeWarCount().known()) { return rootUnavailable(); }
        boolean atPeace = snapshot.activeWarCount().value() == 0;
        if (requirePeace && !atPeace) { return new RootScope(RootScopeStatus.OUTSIDE_SCENE, false, null, null, null, Field.missing(), null); }
        if (!valid(snapshot.nativeRevision(), ConstructionScenePolicy::validRevision)
                || !positive(snapshot.publicRevision()) || !snapshot.snapshotId().is("native:" + snapshot.nativeRevision().value())
                || !valid(snapshot.actorId(), ConstructionScenePolicy::validActor)
                || !valid(snapshot.dateRaw(), value -> value.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0
                    && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0)) { return rootUnavailable(); }
        for (int index = input.history().size() - 1; index >= 0; index--) {
            HistoryRow row = input.history().get(index);
            if (!row.command().is(ROOT_QUERY_STEP) || !row.ok().is(true) || !row.root().known()) { continue; }
            Root root = row.root().value();
            if (!root.status().is("available") || !same(root.revision(), snapshot.nativeRevision())
                    || !same(root.dateRaw(), snapshot.dateRaw()) || !same(root.actorId(), snapshot.actorId())) { continue; }
            if (!root.government().known() || !root.government().value().flags().known()) { return rootUnavailable(); }
            GovernmentObservation government = root.government().value();
            boolean feudal = government.key().is("feudal_government") && government.flags().value().contains("government_is_feudal");
            if (feudal || (!requireFeudal && government.key().known() && !government.key().value().isEmpty())) {
                return new RootScope(RootScopeStatus.ADMITTED, atPeace, government.key().value(), snapshot.nativeRevision().value(), snapshot.actorId().value(), taxes(root), government);
            }
            return new RootScope(RootScopeStatus.OUTSIDE_SCENE, atPeace, null, snapshot.nativeRevision().value(), snapshot.actorId().value(), Field.missing(), government);
        }
        return new RootScope(RootScopeStatus.ROOT_QUERY_NEEDED, atPeace, null, null, null, Field.missing(), null);
    }
    private static RootScope rootUnavailable() { return new RootScope(RootScopeStatus.SCOPE_UNAVAILABLE, false, null, null, null, Field.missing(), null); }

    public static CashFrameResult clanCashFrame(CashInput input) {
        if (!input.packet().known()) { return new CashFrameDeferred(CashReason.UNAVAILABLE); }
        CashPacket packet = input.packet().value(); Snapshot snapshot = input.snapshot();
        if (!valid(snapshot.actorId(), ConstructionScenePolicy::validActor)
                || !valid(snapshot.nativeRevision(), ConstructionScenePolicy::validRevision)
                || !snapshot.dateRaw().known() || !same(packet.actorId(), snapshot.actorId())
                || !same(packet.revision(), snapshot.nativeRevision()) || !same(packet.dateRaw(), snapshot.dateRaw())
                || !packet.gameVersion().is("1.20.0.4") || !packet.readOnly().is(true)) {
            return new CashFrameDeferred(CashReason.FRAME_MISMATCH);
        }
        if (!packet.readiness().known() || !packet.monthlyIncomeSemanticsObject().is(true)) {
            return new CashFrameDeferred(CashReason.NET_UNOBSERVED);
        }
        CashReadiness ready = packet.readiness().value();
        if (!ready.sameFrame().is(true) || !ready.treasury().is(true) || !ready.gross().is(true)
                || !ready.totalExpenses().is(true) || !ready.net().is(true)) { return new CashFrameDeferred(CashReason.NET_UNOBSERVED); }
        return new CashFrameObserved();
    }

    static boolean validRevision(BigInteger value) { return value.signum() > 0 && value.compareTo(UINT64_MAX) <= 0; }
    static boolean validActor(BigInteger value) { return value.signum() > 0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0; }
    private static boolean positive(Field<BigInteger> value) { return value.known() && value.value().signum() > 0; }
    private static boolean valid(Field<BigInteger> value, java.util.function.Predicate<BigInteger> predicate) {
        return value.known() && predicate.test(value.value());
    }
    private static <T> boolean same(Field<T> left, Field<T> right) { return left.known() && right.known() && left.value().equals(right.value()); }
    private static Field<Boolean> taxes(Root root) {
        if (!root.council().known()) { return Field.nil(); }
        Council council = root.council().value();
        if (!council.status().is("available") || !council.positions().known()) { return Field.nil(); }
        List<Position> stewards = council.positions().value().stream().filter(position -> position.key().is("councillor_steward")).toList();
        if (stewards.size() != 1) { return Field.nil(); }
        Position steward = stewards.getFirst();
        return Field.of(positive(steward.incumbentId()) && steward.taskKey().is("task_collect_taxes") && steward.frozen().is(false));
    }
}
