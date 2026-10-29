package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;

/** Root installs this exact Start handler, its replay, and its actual native bookmarks admission once. */
public final class GameplayStartInstaller {
    private final GameplayStartEffects effects;
    private final ExactRef implementation;
    private final ExactRef decoder;
    private final List<RootExecutableBindings.ActionBinding> actions;
    private final List<NativeRecordedEvidenceVerifier.Binding> archived;
    private final List<FrontendRouteAdmission> admissions;
    public GameplayStartInstaller(GameplayStartEffects effects,ExactRef actualImplementation,ExactRef actualDecoder) {
        this.effects=Objects.requireNonNull(effects);implementation=Objects.requireNonNull(actualImplementation);decoder=Objects.requireNonNull(actualDecoder);
        FrontendRulesData.require(implementation.bytes()>0 && decoder.bytes()>0,"actual Start implementation and decoder sources required");
        actions=effects.bindings(implementation).stream().map(binding -> new RootExecutableBindings.ActionBinding(binding,
                ReadContract.GuardMode.FRONTEND_SESSION,Optional.of(FrontendRulesRequests.Primitive.START_BOOKMARK.capability()),decoder)).toList();
        archived=effects.archivedVerifiers(implementation);
        admissions=List.of(new FrontendRouteAdmission(FrontendRulesRequests.Primitive.START_BOOKMARK.operation(),
                Set.of(FrontendRulesData.Route.BOOKMARKS),FrontendRouteAdmission.FrameMode.MENU,implementation));
    }
    public List<RootExecutableBindings.ActionBinding> actions() {
        return actions;
    }
    public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers() { return archived; }
    public List<FrontendRouteAdmission> routeAdmissions() {
        return admissions;
    }
}
