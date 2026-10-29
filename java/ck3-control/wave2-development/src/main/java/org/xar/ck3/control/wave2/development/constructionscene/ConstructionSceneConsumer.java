package org.xar.ck3.control.wave2.development.constructionscene;

import java.util.Objects;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.*;

/** Extracted construction_formal_consumer.py scope/cash call sites. No driver, ledger or dispatch. */
public final class ConstructionSceneConsumer {
    private ConstructionSceneConsumer() { }
    public sealed interface ScopeDirective permits PreserveBaseline, QueryRoot, OptionalSpendDeferred,
            PrewarUnchanged, ReadCurrentCash { }
    public record PreserveBaseline() implements ScopeDirective { }
    public record QueryRoot(String selectedStep, String phase) implements ScopeDirective {
        public QueryRoot {
            if (!ConstructionScenePolicy.ROOT_QUERY_STEP.equals(selectedStep) || !"construction_feudal_scope_query".equals(phase)) {
                throw new IllegalArgumentException("scope query directive must use original public query");
            }
        }
    }
    public record OptionalSpendDeferred(String reason) implements ScopeDirective {
        public OptionalSpendDeferred { Objects.requireNonNull(reason); }
    }
    public record PrewarUnchanged(String reason) implements ScopeDirective {
        public PrewarUnchanged { Objects.requireNonNull(reason); }
    }
    public record ReadCurrentCash(Admitted scene) implements ScopeDirective {
        public ReadCurrentCash { Objects.requireNonNull(scene); }
    }
    public sealed interface CashDirective permits ReadNativeQuote, ClanObservationDeferred { }
    /** The next native quote read still has to prove final legality and actual spend constraints. */
    public record ReadNativeQuote() implements CashDirective { }
    public record ClanObservationDeferred(CashReason reason, String phase) implements CashDirective {
        public ClanObservationDeferred {
            Objects.requireNonNull(reason);
            if (!"construction_clan_observation_deferred".equals(phase)) { throw new IllegalArgumentException("original Clan defer phase required"); }
        }
    }

    public static ScopeDirective afterScope(Scope scope, boolean prewar, boolean rootQueryAvailable, String actualGameVersion) {
        Objects.requireNonNull(scope);
        if (scope instanceof RootQueryNeeded) {
            if (rootQueryAvailable) { return new QueryRoot(ConstructionScenePolicy.ROOT_QUERY_STEP, "construction_feudal_scope_query"); }
            return prewar ? new PrewarUnchanged("feudal_root_query_unavailable")
                    : new OptionalSpendDeferred("construction trial needs same-frame public feudal root query");
        }
        if (!(scope instanceof Admitted admitted)) {
            if (!prewar) { return new PreserveBaseline(); }
            return new PrewarUnchanged(scope instanceof Unavailable ? "scope_scope_unavailable" : "scope_outside_scene");
        }
        if (admitted.government() == Government.CLAN && !"1.20.0.4".equals(actualGameVersion)) { return new PreserveBaseline(); }
        return new ReadCurrentCash(admitted);
    }

    public static CashDirective afterCash(Admitted scope, CashFrameResult observedCash) {
        Objects.requireNonNull(scope); Objects.requireNonNull(observedCash);
        if (scope.government() == Government.CLAN && observedCash instanceof CashFrameDeferred deferred) {
            return new ClanObservationDeferred(deferred.reason(), "construction_clan_observation_deferred");
        }
        return new ReadNativeQuote();
    }
}
