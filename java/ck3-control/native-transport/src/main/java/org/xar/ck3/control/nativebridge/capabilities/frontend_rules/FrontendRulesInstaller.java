package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.*;

/** Supplies the identical definition/effect objects to the sole Root inventories and coordinators. */
public final class FrontendRulesInstaller {
    private final FrontendRulesDefinitions definitions;
    private final FrontendRulesEffects effects;
    private final ExactRef implementation;
    private final ExactRef decoder;
    private final List<RootExecutableBindings.ActionBinding> actions;
    private final List<NativeRecordedEvidenceVerifier.Binding> archived;
    public FrontendRulesInstaller(FrontendRulesDefinitions definitions, PlanningReadPort soleReads, ActionPorts.OutcomeArchive archive,
            ExactRef actualEffectsSource, ExactRef actualDecoderSource) {
        this.definitions = java.util.Objects.requireNonNull(definitions); this.implementation = java.util.Objects.requireNonNull(actualEffectsSource);
        this.decoder = java.util.Objects.requireNonNull(actualDecoderSource); effects = new FrontendRulesEffects(definitions, soleReads, archive);
        require(implementation.bytes() > 0 && decoder.bytes() > 0, "actual installer/effect/decoder sources required");
        actions = effects.bindings(implementation).stream().map(binding -> new RootExecutableBindings.ActionBinding(binding,
                ReadContract.GuardMode.FRONTEND_SESSION, Optional.of(FrontendRulesEffects.primitive(binding.operation()).capability()), decoder)).toList();
        archived = effects.archivedVerifiers(implementation);
    }
    public FrontendRulesDefinitions definitions() { return definitions; }
    public FrontendRulesEffects effects() { return effects; }
    public List<ReadContract<?>> reads() { return definitions.contracts(); }
    public List<RootExecutableBindings.ActionBinding> actions() {
        return actions;
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers() { return archived; }
    public List<FrontendRouteAdmission> routeAdmissions() {
        var result = new ArrayList<FrontendRouteAdmission>();
        Set<Route> menuRoutes = Set.of(Route.MAIN_MENU, Route.BOOKMARKS, Route.LOBBY, Route.RULER_DESIGNER, Route.COAT_OF_ARMS_DESIGNER);
        for (var contract : definitions.contracts()) {
            if (contract.guardMode() != ReadContract.GuardMode.FRONTEND_SESSION) continue;
            Set<Route> routes = contract == definitions.bookmark() || contract == definitions.scenarioBookmark() ? Set.of(Route.BOOKMARKS) : menuRoutes;
            result.add(new FrontendRouteAdmission(contract.operation(), routes, FrontendRouteAdmission.FrameMode.MENU, implementation));
        }
        for (var action : actions()) {
            var primitive = FrontendRulesEffects.primitive(action.effect().operation());
            Set<Route> routes = switch (primitive) {
                case NEW_GAME -> Set.of(Route.MAIN_MENU);
                case PICK_ANY, OPEN_RULES, SELECT_1066_BOOKMARK, SELECT_1066, SELECT_RULE, APPLY_HIDE_RULES, HIDE_RULES -> Set.of(Route.BOOKMARKS);
                case RULER_DESIGNER, SELECT_RANDOM -> Set.of(Route.LOBBY);
                default -> throw new IllegalArgumentException("unimplemented frontend route admission");
            };
            result.add(new FrontendRouteAdmission(action.effect().operation(), routes, FrontendRouteAdmission.FrameMode.MENU, implementation));
        }
        return List.copyOf(result);
    }
}
