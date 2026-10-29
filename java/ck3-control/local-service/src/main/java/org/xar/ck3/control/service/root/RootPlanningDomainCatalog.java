package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Exact callable identity determines a fact's declared domain; no operation-name inference or fallback. */
public final class RootPlanningDomainCatalog implements RootPlanningInputsFactory.DomainCatalog {
    private final RootRuntimeContext context;
    private final RootExecutableBindings bindings;
    private final RootSaveRuntime save;
    private final Map<OperationKey,RootDomainInstallation.FixedDomain> fixed=new HashMap<>();
    private final Map<RootExecutableBindings.Family<?>,Domain> families=new IdentityHashMap<>();
    private final Map<RootExecutableBindings.CompositeBinding,Domain> composites=new IdentityHashMap<>();
    private final Optional<RootAubRuntimeFactory.Runtime> aub;
    private final Optional<RootRiteCreationRuntimeFactory.Runtime> rite;
    private final Optional<RootDriverTransportRuntimeFactory.Runtime> sampling;
    private final Optional<RootGuiPublicProducts.Installed> gui;
    private final Optional<RootReligionPilgrimage.Runtime> pilgrimage;
    private final Optional<RootMilitaryControlStepRuntime.Installed> militaryControls;
    private final RootPublicPauseArchiveClassifier publicPause;
    /** Every actual catalog retains its complete per-Game callable authorities, including public pause. */
    public RootPlanningDomainCatalog(RootRuntimeContext context,RootExecutableBindings actual,List<RootDomainInstallation> installed,
            RootSaveRuntime sameSave,RootAubRuntimeFactory.Runtime sameAub,RootRiteCreationRuntimeFactory.Runtime sameRite,
            RootDriverTransportRuntimeFactory.Runtime sameSampling,RootGuiPublicProducts.Installed sameGui,
            RootReligionPublicProducts.Installed sameReligionRuntime,RootMilitaryControlStepRuntime.Installed sameMilitaryControls,
            RootPublicPauseArchiveClassifier samePublicPause)throws IOException {
        this.context=Objects.requireNonNull(context);bindings=Objects.requireNonNull(actual);save=Objects.requireNonNull(sameSave);
        aub=Optional.of(Objects.requireNonNull(sameAub));rite=Optional.of(Objects.requireNonNull(sameRite));
        sampling=Optional.of(Objects.requireNonNull(sameSampling));gui=Optional.of(Objects.requireNonNull(sameGui));
        Optional<RootReligionPublicProducts.Installed> sameReligion=Optional.of(Objects.requireNonNull(sameReligionRuntime));
        militaryControls=Optional.of(Objects.requireNonNull(sameMilitaryControls));
        publicPause=Objects.requireNonNull(samePublicPause);publicPause.requireContext(context);
        StrictJson.require(context.bindings()==bindings,
                "planning classification requires this context's identical bound inventory");
        Optional<RootReligionPilgrimage.Runtime> actualPilgrimage=Optional.empty();
        if(sameReligion.isPresent()) {
            try { actualPilgrimage=sameReligion.orElseThrow().service().component(RootReligionPilgrimage.Runtime.class); }
            catch(IOException failure) { throw new IllegalArgumentException("actual religion component lookup failed",failure); }
        }
        pilgrimage=actualPilgrimage;
        List<RootDomainInstallation> actualInstalled=List.copyOf(installed);
        StrictJson.require(actualInstalled.stream().filter(domain->domain==publicPause.publicPause().installation()).count()==1,
                "public pause classification requires its sole identical installed domain");
        aub.ifPresent(runtime->{
            runtime.requireContext(context);
            StrictJson.require(actualInstalled.stream().anyMatch(domain->domain==runtime.installation()),
                    "AUB control classification requires this exact installed runtime definition");
            classifyAubControl(bindings,runtime.selectAction(),runtime.confirmAction(),new OperationKey(AubOperations.SELECT)).orElseThrow();
            classifyAubControl(bindings,runtime.selectAction(),runtime.confirmAction(),new OperationKey(AubOperations.CONFIRM)).orElseThrow();
        });
        rite.ifPresent(runtime->{
            runtime.requireContext(context);
            StrictJson.require(actualInstalled.stream().anyMatch(domain->domain==runtime.installation()),
                    "Rite control classification requires this exact installed runtime definition");
            List<RootExecutableBindings.ActionBinding> actions=runtime.installation().actions();
            StrictJson.require(runtime.enabled()==!actions.isEmpty(),"Rite enabled state differs from its actual installed actions");
            for(var action:actions) classifyRiteControl(bindings,actions,runtime.installation().archived(),action.effect().operation()).orElseThrow();
            if(actions.isEmpty())StrictJson.require(runtime.installation().archived().isEmpty(),"disabled Rite runtime must not retain action replay authorities");
        });
        sampling.ifPresent(runtime->{
            StrictJson.require(runtime.context()==context,
                    "observer sampling classification requires its identical per-Game runtime");
            requireInstalledSamplingContents(actualInstalled,runtime.installation());
            List<RootExecutableBindings.ActionBinding> actions=List.of(runtime.enableAction(),runtime.disableAction());
            StrictJson.require(runtime.installation().actions().size()==2
                    &&runtime.installation().actions().get(0)==actions.get(0)
                    &&runtime.installation().actions().get(1)==actions.get(1),
                    "observer sampling requires its complete exact two-action installation");
            for(var action:actions)classifySamplingControl(bindings,actions,runtime.installation().archived(),
                    action.effect().operation()).orElseThrow();
        });
        gui.ifPresent(installedGui->{
            try { installedGui.requireContext(context); }
            catch(IOException failure) { throw new IllegalArgumentException("GUI classification crossed its actual context",failure); }
            StrictJson.require(actualInstalled.stream().filter(domain->domain==installedGui.installation()).count()==1,
                    "GUI classification requires its sole exact installed domain");
            for(var navigation:installedGui.navigationBindings())
                requireNavigationIdentity(bindings,navigation.actionBinding(),navigation.archivedBinding());
            try { requireGuiPhysicalIdentity(context.core().physicalActions(),bindings,installedGui.physicalBinding()); }
            catch(IOException failure) { throw new IllegalArgumentException("GUI physical registry is not actually bound",failure); }
        });
        sameReligion.ifPresent(religion->{
            StrictJson.require(actualInstalled.stream().filter(domain->domain==religion.installation()).count()==1,
                    "religion control classification requires its sole actual installed parent");
            pilgrimage.ifPresent(runtime->{
                try { runtime.requireContext(context); }
                catch(IOException failure) { throw new IllegalArgumentException("pilgrimage classification crossed its actual context",failure); }
                requireInstalledPilgrimageContents(religion.installation(),runtime.installation());
                requireNavigationIdentity(bindings,runtime.actionBinding(),runtime.archivedBinding());
            });
        });
        militaryControls.ifPresent(runtime->{
            try { runtime.requireContext(context); }
            catch(IOException failure) { throw new IllegalArgumentException("military control classification crossed its actual context",failure); }
            StrictJson.require(actualInstalled.stream().filter(domain->domain==runtime.installation()).count()==1,
                    "military classification requires its sole exact installed domain");
            requireMilitaryCallableIdentity(bindings,runtime);
        });
        StrictJson.require(bindings.actionBindings().stream().anyMatch(value->value==save.action()),"system control must be the identical installed canonical SAVE action");
        for(RootDomainInstallation domain:actualInstalled) {
            for(var claim:domain.fixedDomains()) {
                StrictJson.require(bindings.actionBindings().stream().anyMatch(value->value==claim.binding()),"fact domain cites an uninstalled action object");
                StrictJson.require(fixed.putIfAbsent(claim.binding().effect().operation(),claim)==null,"duplicate fixed action domain");
            }
            for(var claim:domain.familyDomains()) {
                StrictJson.require(bindings.families().stream().anyMatch(value->value==claim.family()),"fact domain cites an uninstalled action family");
                StrictJson.require(families.put(claim.family(),claim.domain())==null,"duplicate action family domain");
            }
            for(var claim:domain.compositeDomains()) {
                StrictJson.require(bindings.compositeBindings().stream().anyMatch(value->value==claim.binding()),"fact domain cites an uninstalled composite object");
                StrictJson.require(composites.put(claim.binding(),claim.domain())==null,"duplicate composite domain");
            }
        }
    }
    @Override public RootPlanningInputsFactory.Classification classify(ActionReceipt receipt,Session same,OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(receipt);Objects.requireNonNull(same);Objects.requireNonNull(archive);
        ActionCommand command=receipt.command();
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay && command.source().equals(context.source())
                && command.origin().game().equals(context.game().generation()) && command.sessionId().equals(context.game().sessionId()),
                "fact domain requires this runtime's actual gameplay command");
        context.writer().requireSession(same);publicPause.requireContext(context);
        var pause=publicPause.classify(command);
        if(pause.isPresent()) {
            publicPause.verifyArchivedReceipt(same,receipt,archive);
            return pause.orElseThrow();
        }
        var control=classifyControl(bindings,save.action(),command.operation());
        if(control.isPresent())return control.orElseThrow();
        if(aub.isPresent()) {
            var runtime=aub.orElseThrow();
            var actualControl=classifyAubControl(bindings,runtime.selectAction(),runtime.confirmAction(),command.operation());
            if(actualControl.isPresent()) {
                StrictJson.require(command.expected().observerSchema().equals(AubOperations.OBSERVER),
                        "AUB control fact must retain its actual independent result contract");
                return actualControl.orElseThrow();
            }
        }
        if(rite.isPresent()) {
            var runtime=rite.orElseThrow();
            var actualControl=classifyRiteControl(bindings,runtime.installation().actions(),runtime.installation().archived(),command.operation());
            if(actualControl.isPresent()) {
                StrictJson.require(command.expected().observerSchema().equals(RootRiteCreationRuntimeFactory.OBSERVER),
                        "Rite control fact must retain its actual independent result contract");
                return actualControl.orElseThrow();
            }
        }
        if(sampling.isPresent()) {
            var runtime=sampling.orElseThrow();
            var actualControl=classifySamplingControl(bindings,List.of(runtime.enableAction(),runtime.disableAction()),
                    runtime.installation().archived(),command.operation());
            if(actualControl.isPresent()) {
                StrictJson.require(command.expected().observerSchema().equals(ArmyObserverSampling.OBSERVER),
                        "observer sampling fact must retain its independent actual result contract");
                return actualControl.orElseThrow();
            }
        }
        if(gui.isPresent()) {
            var installedGui=gui.orElseThrow();installedGui.requireContext(context);
            RootPlanningInputsFactory.Classification matched=null;
            for(var navigation:installedGui.navigationBindings()) {
                var found=classifyGuiNavigation(bindings,navigation,command);
                if(found.isPresent()) {
                    StrictJson.require(matched==null,"multiple actual GUI producers claimed the same selector");
                    matched=found.orElseThrow();
                }
            }
            if(matched!=null)return matched;
            var physical=installedGui.physicalBinding();
            if(command.operation().equals(physical.operation())) {
                var physicalRegistry=context.core().physicalActions();
                requireGuiPhysicalIdentity(physicalRegistry,bindings,physical);
                StrictJson.require(physicalRegistry.require(command)==physical&&installedGui.matchesPhysical(command),
                        "physical GUI control differs from its actual body-derived source/selector");
                return new RootPlanningInputsFactory.SystemControl(
                        RootPlanningInputsFactory.ControlKind.GUI_PHYSICAL_PRESENTATION);
            }
        }
        if(pilgrimage.isPresent()) {
            var runtime=pilgrimage.orElseThrow();runtime.requireContext(context);
            requireNavigationIdentity(bindings,runtime.actionBinding(),runtime.archivedBinding());
            if(runtime.matchesControl(command))return new RootPlanningInputsFactory.SystemControl(
                    RootPlanningInputsFactory.ControlKind.PILGRIMAGE_CONTROL);
        }
        if(militaryControls.isPresent()) {
            var runtime=militaryControls.orElseThrow();runtime.requireContext(context);
            requireMilitaryCallableIdentity(bindings,runtime);
            if(runtime.actionBindings().stream().anyMatch(action->action.effect().operation().equals(command.operation()))) {
                StrictJson.require(runtime.matchesControl(command),
                        "military control command differs from its actual source-owned finite producer");
                return new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.MILITARY_UI_CONTROL);
            }
        }
        var direct=fixed.get(command.operation());
        if(direct!=null) {
            StrictJson.require(bindings.actualActionBinding(command.operation()).orElseThrow()==direct.binding().effect(),"fact domain action identity changed");
            return new RootPlanningInputsFactory.BusinessDomain(direct.domain());
        }
        var family=bindings.actualFamily(command.operation());
        if(family.isPresent()) {
            Domain value=families.get(family.orElseThrow());
            if(value==null)throw new IOException("actual issued action family has no explicit planning domain");return new RootPlanningInputsFactory.BusinessDomain(value);
        }
        RootExecutableBindings.CompositeBinding matched=null;
        for(var binding:bindings.compositeBindings())if(binding.handler().supports(command.operation())) {
            StrictJson.require(matched==null,"ambiguous actual composite planning domain");matched=binding;
        }
        if(matched!=null) {
            StrictJson.require(bindings.resolve(command.operation(),command.origin()).filter(value->value.kind()==ExecutableStepBindings.Kind.COMPOSITE).isPresent()
                    && bindings.actualArchivedVerifier(command.operation()).isPresent(),"composite fact lacks actual issued handler/replay");
            Domain value=composites.get(matched);if(value==null)throw new IOException("actual installed composite has no explicit planning domain");return new RootPlanningInputsFactory.BusinessDomain(value);
        }
        throw new IOException("actual command has no installed source-bound planning domain");
    }
    /** Pure metadata classification; the caller still authenticates the actual command and canonical receipt. */
    static java.util.Optional<RootPlanningInputsFactory.Classification> classifyControl(RootExecutableBindings actual,
            RootExecutableBindings.ActionBinding sameSave,OperationKey operation) {
        Objects.requireNonNull(actual);Objects.requireNonNull(sameSave);Objects.requireNonNull(operation);
        StrictJson.require(sameSave.effect().operation().equals(RootSaveRuntime.OPERATION),"system control definition must be the actual SAVE operation");
        if(!operation.equals(sameSave.effect().operation()))return java.util.Optional.empty();
        StrictJson.require(actual.actionBindings().stream().anyMatch(binding->binding==sameSave)
                &&actual.actualActionBinding(operation).orElseThrow()==sameSave.effect(),
                "system control classification requires the identical installed SAVE handler");
        return java.util.Optional.of(new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE));
    }

    /** Identity metadata only; the caller still authenticates the original command and archived receipt. */
    static Optional<RootPlanningInputsFactory.Classification> classifyAubControl(RootExecutableBindings actual,
            RootExecutableBindings.ActionBinding sameSelect,RootExecutableBindings.ActionBinding sameConfirm,OperationKey operation) {
        Objects.requireNonNull(actual);Objects.requireNonNull(sameSelect);Objects.requireNonNull(sameConfirm);Objects.requireNonNull(operation);
        StrictJson.require(sameSelect.effect().operation().equals(new OperationKey(AubOperations.SELECT))
                &&sameConfirm.effect().operation().equals(new OperationKey(AubOperations.CONFIRM)),
                "AUB control definitions must retain both exact original operations");
        boolean select=operation.equals(sameSelect.effect().operation());
        if(!select&&!operation.equals(sameConfirm.effect().operation()))return Optional.empty();
        StrictJson.require(actual.actionBindings().stream().anyMatch(value->value==sameSelect)
                &&actual.actionBindings().stream().anyMatch(value->value==sameConfirm)
                &&actual.actualActionBinding(sameSelect.effect().operation()).orElseThrow()==sameSelect.effect()
                &&actual.actualActionBinding(sameConfirm.effect().operation()).orElseThrow()==sameConfirm.effect()
                &&actual.actualArchivedVerifier(sameSelect.effect().operation()).isPresent()
                &&actual.actualArchivedVerifier(sameConfirm.effect().operation()).isPresent(),
                "AUB control classification requires identical installed action handlers and archived verifiers");
        return Optional.of(new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.AUB_POLICY_CONTROL));
    }

    /** The complete installed roster supplies authority; selector names alone do not classify controls. */
    static Optional<RootPlanningInputsFactory.Classification> classifyRiteControl(RootExecutableBindings actual,
            List<RootExecutableBindings.ActionBinding> sameActions,List<NativeRecordedEvidenceVerifier.Binding> sameReplay,OperationKey operation) {
        Objects.requireNonNull(actual);Objects.requireNonNull(operation);
        List<RootExecutableBindings.ActionBinding> controls=List.copyOf(sameActions);
        List<NativeRecordedEvidenceVerifier.Binding> replays=List.copyOf(sameReplay);
        if(controls.isEmpty()) { StrictJson.require(replays.isEmpty(),"Rite replay roster cannot outlive its installed controls");return Optional.empty(); }
        Set<OperationKey> expected=new HashSet<>();
        for(RiteCreation selector:RiteCreation.values())if(selector!=RiteCreation.PREVIEW)expected.add(selector.operationKey());
        Set<OperationKey> seen=new HashSet<>();
        for(var binding:controls) {
            OperationKey selected=binding.effect().operation();
            StrictJson.require(expected.contains(selected)&&seen.add(selected),
                    "Rite control roster must contain each exact finite action selector once");
            StrictJson.require(actual.actionBindings().stream().anyMatch(value->value==binding)
                    &&actual.actualActionBinding(selected).orElseThrow()==binding.effect()
                    &&actual.actualArchivedVerifier(selected).isPresent(),
                    "Rite control requires the identical installed handler, effect and archived verifier");
        }
        StrictJson.require(seen.equals(expected),"Rite control classification requires the complete installed seven-action roster");
        Set<OperationKey> replayed=new HashSet<>();
        for(var replay:replays)StrictJson.require(expected.contains(replay.operation())&&replayed.add(replay.operation())
                &&actual.actualArchivedVerifier(replay.operation()).orElseThrow()==replay,
                "Rite control requires each identical installed archived verifier once");
        StrictJson.require(replayed.equals(expected),"Rite archived verifier roster differs from its complete action roster");
        if(!seen.contains(operation))return Optional.empty();
        return Optional.of(new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.RITE_CREATION_CONTROL));
    }
    /** Only the same installed sampling handlers and replay objects classify these research controls. */
    static Optional<RootPlanningInputsFactory.Classification> classifySamplingControl(RootExecutableBindings actual,
            List<RootExecutableBindings.ActionBinding> sameActions,List<NativeRecordedEvidenceVerifier.Binding> sameReplay,
            OperationKey operation) {
        Objects.requireNonNull(actual);Objects.requireNonNull(operation);
        var controls=List.copyOf(sameActions);var replays=List.copyOf(sameReplay);
        Set<OperationKey> expected=Set.of(new OperationKey(ArmyObserverSampling.ENABLE),
                new OperationKey(ArmyObserverSampling.DISABLE));
        Set<OperationKey> seen=new HashSet<>(),replayed=new HashSet<>();
        for(var binding:controls) {
            var selected=binding.effect().operation();
            StrictJson.require(expected.contains(selected)&&seen.add(selected)
                    &&actual.actionBindings().stream().anyMatch(value->value==binding)
                    &&actual.actualActionBinding(selected).orElseThrow()==binding.effect(),
                    "observer sampling requires each identical installed action/effect once");
        }
        StrictJson.require(seen.equals(expected),"complete observer sampling two-action roster required");
        for(var replay:replays)StrictJson.require(expected.contains(replay.operation())&&replayed.add(replay.operation())
                &&actual.actualArchivedVerifier(replay.operation()).orElseThrow()==replay,
                "observer sampling requires each identical installed archived verifier once");
        StrictJson.require(replayed.equals(expected),"complete observer sampling replay roster required");
        if(!seen.contains(operation))return Optional.empty();
        return Optional.of(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.OBSERVER_SAMPLING_CONTROL));
    }

    /** DriverRegistry merges child installations. Ownership is the complete identical callable content,
     * never a requirement to register the child container twice beside its merged parent. */
    static void requireInstalledSamplingContents(List<RootDomainInstallation> actualInstalled,
            RootDomainInstallation child) {
        Objects.requireNonNull(child);
        StrictJson.require(child.actions().size()==2&&child.archived().size()==2&&child.readFamilies().size()==1,
                "complete sampling action/replay/query family content required");
        boolean found=List.copyOf(actualInstalled).stream().anyMatch(parent->
                child.actions().stream().allMatch(binding->parent.actions().stream().filter(value->value==binding).count()==1)
                &&child.archived().stream().allMatch(replay->parent.archived().stream().filter(value->value==replay).count()==1)
                &&child.readFamilies().stream().allMatch(family->parent.readFamilies().stream().filter(value->value==family).count()==1));
        StrictJson.require(found,"actual merged installation must retain each identical sampling action, replay and read family");
    }

    /** The private-issued GUI wrapper supplies its actual per-context producer and finite partition. */
    static Optional<RootPlanningInputsFactory.Classification> classifyGuiNavigation(RootExecutableBindings actual,
            RootGuiPublicProducts.InstalledNavigation navigation,ActionCommand command) {
        Objects.requireNonNull(navigation);Objects.requireNonNull(command);
        requireNavigationIdentity(actual,navigation.actionBinding(),navigation.archivedBinding());
        boolean control=navigation.matchesControl(command),pending=navigation.matchesPending(command);
        StrictJson.require(!(control&&pending),"GUI control and final-pending selectors overlap");
        if(control)return Optional.of(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.GUI_NAVIGATION_CONTROL));
        if(pending)return Optional.of(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.GUI_NAVIGATION_FINAL_PENDING));
        return Optional.empty();
    }
    /** Same actual fixed-control installation; an observer name never substitutes for these objects. */
    static void requireMilitaryCallableIdentity(RootExecutableBindings actual,RootMilitaryControlStepRuntime.Installed runtime) {
        Objects.requireNonNull(actual);Objects.requireNonNull(runtime);
        var actions=runtime.actionBindings();var archived=runtime.archivedBindings();
        StrictJson.require(actions.size()==3&&archived.size()==3,
                "complete actual military control action/replay roster required");
        var seen=new java.util.HashSet<OperationKey>();
        for(var action:actions) {
            var operation=action.effect().operation();
            StrictJson.require(seen.add(operation),"duplicate actual military control operation");
            var matching=archived.stream().filter(replay->replay.operation().equals(operation)).toList();
            StrictJson.require(matching.size()==1,"one actual military archived verifier per action required");
            requireNavigationIdentity(actual,action,matching.getFirst());
        }
    }

    /** Pure callable identity check; equal names, source refs or copied verifier bodies confer no identity. */
    static void requireNavigationIdentity(RootExecutableBindings actual,RootExecutableBindings.ActionBinding action,
            NativeRecordedEvidenceVerifier.Binding replay) {
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(replay);
        var operation=action.effect().operation();
        StrictJson.require(actual.actionBindings().stream().filter(value->value==action).count()==1
                &&actual.actualActionBinding(operation).orElseThrow()==action.effect()
                &&replay.operation().equals(operation)
                &&actual.archivedBindings().stream().filter(value->value==replay).count()==1
                &&actual.actualArchivedVerifier(operation).orElseThrow()==replay,
                "control classification requires identical installed action, effect and archived verifier objects");
    }

    /** Religion merges its extensions once; the child must retain every identical callable object. */
    static void requireInstalledPilgrimageContents(RootDomainInstallation parent,RootDomainInstallation child) {
        Objects.requireNonNull(parent);Objects.requireNonNull(child);
        StrictJson.require(child.actions().size()==1&&child.archived().size()==1&&child.readFamilies().size()==2,
                "complete pilgrimage action/replay/two-read-family metadata required");
        StrictJson.require(child.actions().stream().allMatch(binding->parent.actions().stream().filter(value->value==binding).count()==1)
                &&child.archived().stream().allMatch(replay->parent.archived().stream().filter(value->value==replay).count()==1)
                &&child.readFamilies().stream().allMatch(family->parent.readFamilies().stream().filter(value->value==family).count()==1),
                "actual merged religion installation lost an identical pilgrimage callable");
    }

    /** Physical presentation owns its separate canonical plane; it is never a Native action alias. */
    static void requireGuiPhysicalIdentity(PhysicalActionRegistry actual,RootExecutableBindings nativeBindings,
            PhysicalActionRegistry.Binding same) {
        Objects.requireNonNull(actual);Objects.requireNonNull(nativeBindings);Objects.requireNonNull(same);
        StrictJson.require(same.transportKind()==org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP
                &&actual.find(same.operation()).orElseThrow()==same
                &&nativeBindings.actualActionBinding(same.operation()).isEmpty(),
                "GUI physical control requires its identical Core physical binding and no Native action alias");
    }

}

