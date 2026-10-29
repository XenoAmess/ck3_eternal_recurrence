package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Public battle read consumers of the actual finite M5 collectors and both original outer person codecs. */
public final class ArmyBattleReadService {
    @FunctionalInterface public interface Current { ArmyRetreatFrames.Current current(); }
    public record Reply(ArmyBattleReads.Selection selection, ArmyRetreatFrames.Current captured, PlanningReadResult.Known<ArmyBattleReads.Observation> original) {
        public Reply { Objects.requireNonNull(selection); Objects.requireNonNull(captured); Objects.requireNonNull(original); require(captured.context().equals(selection.context()), "public battle captured another frame"); require(same(ArmyBattleReads.decode(selection, original.receipt()), original.value()), "battle reply differs from its full original Native read"); }
    }
    private final ContinuityStorePort writer; private final ArmyBattleReads battles; private final java.util.function.Supplier<RootReadContractCatalog> catalog; private final Current current;
    public ArmyBattleReadService(ContinuityStorePort originalWriter, ArmyBattleReads actualBattles, RootReadContractCatalog exactCatalog, Current actualCurrent) {
        this(originalWriter, actualBattles, () -> Objects.requireNonNull(exactCatalog), actualCurrent);
    }
    public ArmyBattleReadService(ContinuityStorePort originalWriter, ArmyBattleReads actualBattles, java.util.function.Supplier<RootReadContractCatalog> actualCatalog, Current actualCurrent) {
        writer = Objects.requireNonNull(originalWriter); battles = Objects.requireNonNull(actualBattles); catalog = Objects.requireNonNull(actualCatalog); current = Objects.requireNonNull(actualCurrent);
    }
    public Reply query_battle_control_snapshot_v1(ArmyCalls.Unit input) { require(input.method() == PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, "control route method differs"); return query(input); }
    public Reply query_battle_transition_v1(ArmyCalls.CombatId input) { require(input.method() == PublicMethod.QUERY_BATTLE_TRANSITION_V1, "transition route method differs"); return query(input); }
    public Reply query_battle_terminal_transition_v1(ArmyCalls.Terminal input) { return query(input); }
    private Reply query(ArmyCalls.Call input) {
        try { return writer.locked(session -> { var captured = current.current(); var selection = new ArmyBattleReads.Selection(input, captured.context(), ArmyBattleReads.Capture.PUBLIC_QUERY); var original = battles.read(session, Objects.requireNonNull(catalog.get()), selection); ArmyRetreatFrames.same(captured, current.current()); return new Reply(selection, captured, original); }); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings, ExactRef actualSource) {
        return List.of(register(bindings, PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1, ArmyCalls.Unit.class, this::query_battle_control_snapshot_v1, actualSource),
                register(bindings, PublicMethod.QUERY_BATTLE_TRANSITION_V1, ArmyCalls.CombatId.class, this::query_battle_transition_v1, actualSource),
                register(bindings, PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, ArmyCalls.Terminal.class, this::query_battle_terminal_transition_v1, actualSource));
    }
    private static <Q extends ArmyCalls.Call> PublicBindings.TypedBinding<Q,Reply> register(PublicBindings bindings, PublicMethod method, Class<Q> type, PublicRoutes.Handler<Q,Reply> handler, ExactRef source) {
        return bindings.register(method, type, Reply.class, handler, args -> { if (!(args instanceof PublicBindings.Value value)) throw new IllegalArgumentException("battle read requires exact named arguments"); return type.cast(ArmyCallCodec.decode(method, value.original())); }, ArmyBattleReadService::encode,
                new PublicRoutes.Target(ArmyBattleReadService.class.getName(), method.pythonName(), source), PublicRoutes.Status.IMPLEMENTED, "original receipt, source/mirrors/current diagnostics and declared integer fields; Root installation and runtime verification required");
    }
    public static RawJson encode(Reply reply) {
        var n = ArmyNativeReadEvidence.result(reply.selection().context(), reply.original().receipt());
        Obj value = org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(n), org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        return ArmyBattlePublicPresenter.encode(reply.original().value(), value, new ArmyPublicSnapshot(reply.selection().context(), reply.captured().actual().semantic()));
    }
    private static boolean same(ArmyBattleReads.Observation expected, ArmyBattleReads.Observation actual) {
        if (expected.method() != actual.method() || !expected.querySequence().equals(actual.querySequence()) || !expected.normalized().equals(actual.normalized())) return false;
        if (expected instanceof ArmyBattleReads.Control left && actual instanceof ArmyBattleReads.Control right) return left.resume().equals(right.resume());
        if (expected instanceof ArmyBattleReads.Terminal left && actual instanceof ArmyBattleReads.Terminal right)
            return left.sixStage().map(BattlePersonSixStageCaptureCodec.NormalizedQuery::toJson).equals(right.sixStage().map(BattlePersonSixStageCaptureCodec.NormalizedQuery::toJson))
                    && left.installedTransfers().map(BattlePersonInstalledTransfersCodec.Query::toJson).equals(right.installedTransfers().map(BattlePersonInstalledTransfersCodec.Query::toJson));
        return expected instanceof ArmyBattleReads.Transition && actual instanceof ArmyBattleReads.Transition;
    }
}
