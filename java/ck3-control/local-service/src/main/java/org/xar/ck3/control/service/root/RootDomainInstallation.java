package org.xar.ck3.control.service.root;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Actual callable objects from one concrete domain installer. Empty unrelated lists never claim missing capability. */
public record RootDomainInstallation(
        String id,
        List<DomainBodies.Registration> domainRegistrations,
        List<RootReadContractCatalog.InstalledRead> reads,
        List<RootReadContractCatalog.Family<?,?>> readFamilies,
        List<RootExecutableBindings.ActionBinding> actions,
        List<RootExecutableBindings.CompositeBinding> composites,
        List<NativeRecordedEvidenceVerifier.Binding> archived,
        List<RootExecutableBindings.Family<?>> actionFamilies,
        List<RootExecutableBindings.CompositeFamily<?>> compositeFamilies,
        List<FrontendRouteAdmission> frontendAdmissions,
        List<RootDomainIntentPreparation.Binding> pending,
        Set<OperationKey> requiredPending,
        List<OrdinaryPolicy> policies,
        List<OrdinaryPlanCompletion> completions,
        List<FixedDomain> fixedDomains,
        List<FamilyDomain> familyDomains,
        List<CompositeDomain> compositeDomains) {
    public RootDomainInstallation {
        StrictJson.text(id);domainRegistrations=List.copyOf(domainRegistrations);reads=List.copyOf(reads);
        readFamilies=List.copyOf(readFamilies);actions=List.copyOf(actions);composites=List.copyOf(composites);
        archived=List.copyOf(archived);actionFamilies=List.copyOf(actionFamilies);compositeFamilies=List.copyOf(compositeFamilies);frontendAdmissions=List.copyOf(frontendAdmissions);
        pending=List.copyOf(pending);requiredPending=Set.copyOf(requiredPending);policies=List.copyOf(policies);
        completions=List.copyOf(completions);fixedDomains=List.copyOf(fixedDomains);
        familyDomains=List.copyOf(familyDomains);compositeDomains=List.copyOf(compositeDomains);
        StrictJson.require(reads.size()<=4096 && actions.size()<=4096 && archived.size()<=4096
                && readFamilies.size()<=256 && actionFamilies.size()<=256 && compositeFamilies.size()<=256 && composites.size()<=128
                && policies.size()<=34 && pending.size()<=128,"bounded concrete domain installation required");
        for(FixedDomain binding:fixedDomains)StrictJson.require(actions.stream().anyMatch(actual->actual==binding.binding()),"domain claim is not the identical installed action");
        for(FamilyDomain binding:familyDomains)StrictJson.require(actionFamilies.stream().anyMatch(actual->actual==binding.family()),"domain claim is not the identical installed family");
        for(CompositeDomain binding:compositeDomains)StrictJson.require(composites.stream().anyMatch(actual->actual==binding.binding()),"domain claim is not the identical installed composite");
    }
    public record FixedDomain(RootExecutableBindings.ActionBinding binding,Domain domain) {
        public FixedDomain { Objects.requireNonNull(binding);Objects.requireNonNull(domain); }
    }
    public record FamilyDomain(RootExecutableBindings.Family<?> family,Domain domain) {
        public FamilyDomain { Objects.requireNonNull(family);Objects.requireNonNull(domain); }
    }
    public record CompositeDomain(RootExecutableBindings.CompositeBinding binding,Domain domain) {
        public CompositeDomain { Objects.requireNonNull(binding);Objects.requireNonNull(domain); }
    }
}
