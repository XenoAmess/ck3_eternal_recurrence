package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

/** Concrete additional business producers installed into the original Root read/action registries. */
public final class RootAdditionalDomains {
    private RootAdditionalDomains() { }

    /** Execution metadata supplied by the ordinary application; resolving it grants no native permission. */
    @FunctionalInterface public interface ImplementationMetadata {
        ExactRef implementation(Class<?> actualClass);
    }

    /** Ordinary business configuration; the application constructs every group below from its real inputs. */
    public record Config(RootGuiPublicProducts.Config gui,RootReligionPublicProducts.Config religion,
            RootArtifactsPublicProducts.Config artifacts,RootDriverProductSourcesFactory.PlainConfig driver) {
        public Config {
            Objects.requireNonNull(gui);Objects.requireNonNull(religion);
            Objects.requireNonNull(artifacts);Objects.requireNonNull(driver);
        }
    }

    public static Prepared ordinary(Config config,RootDriverProductSourcesFactory.SharedServices shared,
            RootCoreBoundPorts ports,ImplementationMetadata metadata,Clock clock)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(shared);Objects.requireNonNull(ports);
        Objects.requireNonNull(metadata);Objects.requireNonNull(clock);
        var rules=new RootFrontendRulesPublicProducts.Prepared();
        var coa=new RootFrontendCoaPublicProducts.Prepared();
        var gui=RootGuiPublicProducts.ordinary(config.gui(),metadata);
        var religion=RootReligionPublicProducts.ordinary(config.religion(),metadata);
        var artifacts=RootArtifactsPublicProducts.ordinary(config.artifacts(),gui,religion.sharedKernel(),ports,metadata);
        var cases=RootChinaCasesPublicProducts.ordinary(metadata);
        var career=RootChinaCareerPublicProducts.ordinary(metadata);
        var driver=RootDriverProductSourcesFactory.prepareOrdinary(config.driver(),shared,ports,metadata,clock);
        return new Prepared(rules,coa,gui,religion,artifacts,cases,career,driver);
    }

    public static final class Prepared {
        private final RootFrontendRulesPublicProducts.Prepared frontendRules;
        private final RootFrontendCoaPublicProducts.Prepared frontendCoa;
        private final RootGuiPublicProducts.Prepared gui;
        private final RootReligionPublicProducts.Prepared religion;
        private final RootArtifactsPublicProducts.Prepared artifacts;
        private final RootChinaCasesPublicProducts.Prepared chinaCases;
        private final RootChinaCareerPublicProducts.Prepared chinaCareer;
        private final RootDriverRegistryPublicProducts.Prepared driverRegistry;
        private final List<DomainBodies.Registration> registrations;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private boolean bindingComplete;

        public Prepared(RootFrontendRulesPublicProducts.Prepared frontendRules,
                RootFrontendCoaPublicProducts.Prepared frontendCoa,RootGuiPublicProducts.Prepared gui,
                RootReligionPublicProducts.Prepared religion,RootArtifactsPublicProducts.Prepared artifacts,
                RootChinaCasesPublicProducts.Prepared chinaCases,RootChinaCareerPublicProducts.Prepared chinaCareer,
                RootDriverRegistryPublicProducts.Prepared driverRegistry) {
            this.frontendRules=Objects.requireNonNull(frontendRules);this.frontendCoa=Objects.requireNonNull(frontendCoa);
            this.gui=Objects.requireNonNull(gui);this.religion=Objects.requireNonNull(religion);
            this.artifacts=Objects.requireNonNull(artifacts);this.chinaCases=Objects.requireNonNull(chinaCases);
            this.chinaCareer=Objects.requireNonNull(chinaCareer);this.driverRegistry=Objects.requireNonNull(driverRegistry);
            // Freeze the finite extension and its original permission before Core/Managed construction.
            for(var definition:this.artifacts.navigationDefinitions())this.gui.addNavigationDefinition(definition);
            for(var definition:this.religion.navigationDefinitions())this.gui.addNavigationDefinition(definition);
            this.gui.addInventoryDefinition(this.artifacts.inventoryDefinition());
            var all=new ArrayList<DomainBodies.Registration>();
            all.addAll(frontendRules.domainRegistrations());all.addAll(frontendCoa.domainRegistrations());
            all.addAll(gui.domainRegistrations());all.addAll(religion.domainRegistrations());
            all.addAll(artifacts.domainRegistrations());all.addAll(chinaCases.domainRegistrations());
            all.addAll(chinaCareer.domainRegistrations());all.addAll(driverRegistry.domainRegistrations());
            var unique=new LinkedHashMap<DomainBodies.Slot,DomainBodies.Registration>();
            for(var registration:all) {
                Objects.requireNonNull(registration);
                var prior=unique.putIfAbsent(registration.slot(),registration);
                if(prior!=null&&prior!=registration)
                    throw new IllegalArgumentException("additional producers claim distinct registrations for one canonical domain slot");
            }
            registrations=List.copyOf(unique.values());
        }

        /** These identical cached registrations must reach Core before the original writer opens. */
        public List<DomainBodies.Registration> domainRegistrations() { return registrations; }
        public RootFrontendRulesPublicProducts.Prepared frontendRules() { return frontendRules; }
        public RootFrontendCoaPublicProducts.Prepared frontendCoa() { return frontendCoa; }
        public RootGuiPublicProducts.Prepared gui() { return gui; }
        public RootReligionPublicProducts.Prepared religion() { return religion; }
        public RootArtifactsPublicProducts.Prepared artifacts() { return artifacts; }
        public RootChinaCasesPublicProducts.Prepared chinaCases() { return chinaCases; }
        public RootChinaCareerPublicProducts.Prepared chinaCareer() { return chinaCareer; }
        public RootDriverRegistryPublicProducts.Prepared driverRegistry() { return driverRegistry; }

        /** Retain every original source qualifier and add the sole actual managed lifecycle qualification. */
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
            Objects.requireNonNull(actual);var all=new ArrayList<NativePrivateActionPermission>();
            all.addAll(frontendRules.privatePermissions());all.addAll(frontendCoa.privatePermissions());
            all.addAll(gui.privatePermissions());
            all.addAll(artifacts.privatePermissions());all.addAll(chinaCases.privatePermissions());
            all.addAll(chinaCareer.privatePermissions());all.addAll(driverRegistry.privatePermissions());
            var qualified=new ArrayList<NativePrivateActionPermission>();
            for(var permission:all)qualified.add(Objects.requireNonNull(permission).withAdditionalQualification(actual));
            // Religion leaf permissions already retain its once-bound deferred actual verifier.
            qualified.addAll(religion.privatePermissions(actual));
            return List.copyOf(qualified);
        }

        /** A partial binding cannot be retried against another Core or silently replayed. */
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);
            if(core!=null) {
                if(core==same&&bindingComplete)return;
                throw new IOException("additional business producers already entered another or incomplete Core binding");
            }
            core=same;
            frontendRules.bindCore(same);frontendCoa.bindCore(same);gui.bindCore(same);religion.bindCore(same);
            artifacts.bindCore(same);chinaCases.bindCore(same);chinaCareer.bindCore(same);driverRegistry.bindCore(same);
            bindingComplete=true;
        }

        public synchronized Installed install(RootRuntimeContext same)throws IOException {
            Objects.requireNonNull(same);
            if(!bindingComplete||core!=same.core())throw new IOException("additional installation requires its identical completely bound Core");
            var previous=attempts.get(same);
            if(previous!=null) {
                if(previous.installed!=null){previous.installed.requireContext(same);return previous.installed;}
                throw new IOException("additional business installation already entered; partial effects are not replayed",previous.failure);
            }
            if(attempts.size()>=64)throw new IOException("additional actual Game installation attempt bound exhausted");
            var attempt=new Attempt();attempts.put(same,attempt);
            RootDriverRegistryPublicProducts.Installed actualDriver=null;
            RootGuiPublicProducts.Installed actualGui=null;
            try {
                var actualArtifacts=artifacts.install(same);
                var actualRules=frontendRules.install(same);var actualCoa=frontendCoa.install(same);
                actualGui=gui.install(same);var actualReligion=religion.install(same);
                var actualCases=chinaCases.install(same);var actualCareer=chinaCareer.install(same);
                actualDriver=driverRegistry.install(same);
                var installed=new Installed(same,actualRules,actualCoa,actualGui,actualReligion,actualArtifacts,
                        actualCases,actualCareer,actualDriver);
                for(var installation:installed.installations())for(var registration:installation.domainRegistrations())
                    if(registrations.stream().noneMatch(original->original==registration))
                        throw new IOException("additional per-Game product introduced an unregistered or different canonical domain producer");
                attempt.installed=installed;return installed;
            } catch(IOException failure) {attempt.failure=closeFailed(actualDriver,actualGui,failure);throw attempt.failure;}
            catch(RuntimeException failure) {attempt.failure=closeFailed(actualDriver,actualGui,new IOException("actual additional business installation failed",failure));throw attempt.failure;}
        }

        private static IOException closeFailed(RootDriverRegistryPublicProducts.Installed actual,
                RootGuiPublicProducts.Installed actualGui,IOException failure) {
            if(actual!=null)try{actual.close();}catch(IOException|RuntimeException disposal){if(disposal!=failure)failure.addSuppressed(disposal);}
            if(actualGui!=null)try{actualGui.close();}catch(IOException|RuntimeException disposal){if(disposal!=failure)failure.addSuppressed(disposal);}
            return failure;
        }
    }

    private static final class Attempt {
        private Installed installed;
        private IOException failure;
    }

    /** Only the actual aggregate installation can construct this retained collection of typed products. */
    public static final class Installed implements AutoCloseable {
        private final RootRuntimeContext context;
        private final RootFrontendRulesPublicProducts.Installed frontendRules;
        private final RootFrontendCoaPublicProducts.Installed frontendCoa;
        private final RootGuiPublicProducts.Installed gui;
        private final RootReligionPublicProducts.Installed religion;
        private final RootArtifactsPublicProducts.Installed artifacts;
        private final RootChinaCasesPublicProducts.Installed chinaCases;
        private final RootChinaCareerPublicProducts.Installed chinaCareer;
        private final RootDriverRegistryPublicProducts.Installed driverRegistry;
        private final List<RootDomainInstallation> installations;
        private boolean closed;

        private Installed(RootRuntimeContext context,RootFrontendRulesPublicProducts.Installed frontendRules,
                RootFrontendCoaPublicProducts.Installed frontendCoa,RootGuiPublicProducts.Installed gui,
                RootReligionPublicProducts.Installed religion,RootArtifactsPublicProducts.Installed artifacts,
                RootChinaCasesPublicProducts.Installed chinaCases,RootChinaCareerPublicProducts.Installed chinaCareer,
                RootDriverRegistryPublicProducts.Installed driverRegistry) {
            this.context=Objects.requireNonNull(context);
            this.frontendRules=Objects.requireNonNull(frontendRules);this.frontendCoa=Objects.requireNonNull(frontendCoa);
            this.gui=Objects.requireNonNull(gui);this.religion=Objects.requireNonNull(religion);
            this.artifacts=Objects.requireNonNull(artifacts);this.chinaCases=Objects.requireNonNull(chinaCases);
            this.chinaCareer=Objects.requireNonNull(chinaCareer);this.driverRegistry=Objects.requireNonNull(driverRegistry);
            installations=List.of(frontendRules.installation(),frontendCoa.installation(),gui.installation(),religion.installation(),
                    artifacts.installation(),chinaCases.installation(),chinaCareer.installation(),driverRegistry.installation());
            if(installations.stream().distinct().count()!=installations.size())
                throw new IllegalArgumentException("additional business groups must retain their own actual installation products");
        }
        public synchronized void requireContext(RootRuntimeContext identical)throws IOException {
            if(closed)throw new IOException("additional resources have already entered original cleanup");
            if(context!=Objects.requireNonNull(identical))throw new IOException("additional products belong to another actual Root runtime context");
            driverRegistry.requireContext(identical);
        }
        @Override public synchronized void close()throws IOException {
            if(closed)return;closed=true;IOException failure=null;
            try{driverRegistry.close();}catch(IOException disposal){failure=disposal;}
            catch(RuntimeException disposal){failure=new IOException("original Driver resources failed to close",disposal);}
            try{gui.close();}catch(IOException|RuntimeException disposal) {
                if(failure==null)failure=disposal instanceof IOException io?io:new IOException("original GUI resources failed to close",disposal);
                else if(disposal!=failure)failure.addSuppressed(disposal);
            }
            if(failure!=null)throw failure;
        }
        public List<RootDomainInstallation> installations() { return installations; }
        public RootFrontendRulesPublicProducts.Installed frontendRules() { return frontendRules; }
        public RootFrontendCoaPublicProducts.Installed frontendCoa() { return frontendCoa; }
        public RootGuiPublicProducts.Installed gui() { return gui; }
        public RootReligionPublicProducts.Installed religion() { return religion; }
        public RootArtifactsPublicProducts.Installed artifacts() { return artifacts; }
        public RootChinaCasesPublicProducts.Installed chinaCases() { return chinaCases; }
        public RootChinaCareerPublicProducts.Installed chinaCareer() { return chinaCareer; }
        public RootDriverRegistryPublicProducts.Installed driverRegistry() { return driverRegistry; }
    }
}
