package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Concrete public route -> same installed read coordinator -> held Native transport -> strict original receipt. */
public final class ArmyClosedReadService {
    @FunctionalInterface public interface Current { ArmyRetreatFrames.Current current(); }
    public record Reply(ArmyCalls.Call input, ArmyRetreatFrames.Current captured, PlanningReadResult.Known<ArmyClosedReads.Observation> original) {
        public Reply {
            Objects.requireNonNull(input); Objects.requireNonNull(captured); Objects.requireNonNull(original);
            ArmyTypes.require(input.method() == original.value().method(), "Army public result belongs to another method");
            ArmyTypes.require(original.value().equals(ArmyClosedReadCodec.decode(input, captured.context(), original.receipt())), "Army reply is not the actual validated Native read");
        }
        public Context context() { return captured.context(); }
    }
    private final Current current;
    private final PlanningReadPort reads;
    private final java.util.function.Supplier<RootReadContractCatalog> catalog;
    private final ArmyClosedReadContracts contracts;
    public ArmyClosedReadService(Current current, PlanningReadPort reads, RootReadContractCatalog catalog, ArmyClosedReadContracts contracts) {
        this(current, reads, () -> Objects.requireNonNull(catalog), contracts);
    }
    public ArmyClosedReadService(Current current, PlanningReadPort reads, java.util.function.Supplier<RootReadContractCatalog> actualCatalog, ArmyClosedReadContracts contracts) {
        this.current = Objects.requireNonNull(current); this.reads = Objects.requireNonNull(reads);
        this.catalog = Objects.requireNonNull(actualCatalog); this.contracts = Objects.requireNonNull(contracts);
    }
    public Reply query_player_default_raise_v1(ArmyCalls.Frame input) { requireMethod(input, PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1); return read(input); }
    public Reply query_player_truce_expiry_v1(ArmyCalls.Truce input) { return read(input); }
    public Reply query_army_gathering_research_sampling_v1(ArmyCalls.Frame input) { requireMethod(input, PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1); return read(input); }
    private Reply read(ArmyCalls.Call input) {
        var captured = Objects.requireNonNull(current.current()); Context context = captured.context(); input.revision().requireCurrent(context.before().frame().revision());
        var selection = new ArmyClosedReadContracts.Selection(input, context);
        var result = reads.read(contracts.issue(Objects.requireNonNull(catalog.get()), selection), contracts.request(selection));
        if (result instanceof PlanningReadResult.Known<ArmyClosedReads.Observation> known) {
            ArmyRetreatFrames.same(captured, Objects.requireNonNull(current.current()));
            return new Reply(input, captured, known);
        }
        throw new IllegalStateException(((PlanningReadResult.Unavailable<ArmyClosedReads.Observation>) result).reason());
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings, ExactRef actualServiceSource) {
        Objects.requireNonNull(bindings); Objects.requireNonNull(actualServiceSource);
        return List.of(
                register(bindings, PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1, ArmyCalls.Frame.class, this::query_player_default_raise_v1, actualServiceSource),
                register(bindings, PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, ArmyCalls.Truce.class, this::query_player_truce_expiry_v1, actualServiceSource),
                register(bindings, PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1, ArmyCalls.Frame.class, this::query_army_gathering_research_sampling_v1, actualServiceSource));
    }
    private static <Q extends ArmyCalls.Call> PublicBindings.TypedBinding<Q,Reply> register(PublicBindings bindings, PublicMethod method, Class<Q> type,
            PublicRoutes.Handler<Q,Reply> handler, ExactRef source) {
        return bindings.register(method, type, Reply.class, handler, arguments -> {
            if (!(arguments instanceof PublicBindings.Value value)) throw new IllegalArgumentException("Army method requires its named argument object");
            return type.cast(ArmyCallCodec.decode(method, value.original()));
        }, ArmyClosedReadService::encode, new PublicRoutes.Target(ArmyClosedReadService.class.getName(), method.pythonName(), source),
                PublicRoutes.Status.IMPLEMENTED, "three closed native read producers; Root installation and runtime acceptance still required");
    }
    public static RawJson encode(Reply reply) { return ArmyClosedReadCodec.encode(reply.original().value(), reply.context(), reply.captured().actual().semantic()); }
    private static void requireMethod(ArmyCalls.Call input, PublicMethod expected) { ArmyTypes.require(input.method() == expected, "Army typed route method mismatch"); }
}
