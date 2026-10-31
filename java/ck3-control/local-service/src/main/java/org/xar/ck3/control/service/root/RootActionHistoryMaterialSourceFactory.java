package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.LifeAdvanceEvidence;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.application.routecontact.RouteContactComposite;
import org.xar.ck3.control.application.routecontact.RouteContactEvidenceArchive;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** The actual installed domain material adapters. No handler, query, recorder or writer is constructed here. */
public final class RootActionHistoryMaterialSourceFactory {
    private RootActionHistoryMaterialSourceFactory(){ }
    /** Actual recording metadata only; ordinary execution never derives adjacent source files. */
    public enum RecordingRole {
        NATIVE_DRIVER, OVERVIEW, WAR, BATTLE, MARRIAGE_CONTRACT, OBSERVER_SAMPLING,
        GUI_SERVICE, GUI_CAMERA, PILGRIMAGE, CLOSE, GIFT
    }
    public enum ReaderRole {
        NATIVE_EFFECT_EVIDENCE(org.xar.ck3.control.application.effects.NativeEffectEvidence.class),
        NATIVE_EFFECT_REGISTRY(org.xar.ck3.control.application.effects.NativeEffectRegistry.class),
        NATIVE_RECORDED_EVIDENCE_VERIFIER(org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.class),
        ROOT_GUARD_EVIDENCE(org.xar.ck3.control.application.effects.RootGuardEvidence.class),
        LIFE_ADVANCE_EVIDENCE(LifeAdvanceEvidence.class),
        LIFE_ADVANCE_ROOT_REPLAY(org.xar.ck3.control.application.advance.LifeAdvanceRootReplay.class),
        ROUTE_CONTACT_EVIDENCE_ARCHIVE(org.xar.ck3.control.application.routecontact.RouteContactEvidenceArchive.class),
        ROUTE_CONTACT_STEPS(org.xar.ck3.control.application.routecontact.RouteContactSteps.class),
        FAMILY_SEND_OBSERVATION(org.xar.ck3.control.application.effects.family.FamilySendObservation.class),
        WAR_HISTORY_STEPS(org.xar.ck3.control.application.planning.military.WarHistorySteps.class),
        DRIVER_FRAME_EVIDENCE_LOADER(org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader.class),
        DRIVER_JSON(org.xar.ck3.control.application.driver.DriverJson.class),
        SWAY_RUNTIME_INSTALLER(org.xar.ck3.control.service.sway.SwayRuntimeInstaller.class),
        ROOT_FAMILY_SEND_RECORDING_MATERIAL(RootFamilySendRecordingMaterial.class),
        ROOT_DRIVER_TRANSPORT_RUNTIME_FACTORY(RootDriverTransportRuntimeFactory.class),
        ARMY_OBSERVER_SAMPLING(org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling.class),
        GIFT_ACTION_HISTORY_EVIDENCE(org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.class),
        PHYSICAL_ACTION_CODEC(org.xar.ck3.control.application.action.PhysicalActionCodec.class),
        FINANCE_READ_CONTRACTS(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.class),
        NATIVE_FINANCE_EFFECTS(org.xar.ck3.control.application.effects.NativeFinanceEffects.class),
        ROOT_GUI_PRESENTATION(RootGuiPresentation.class),
        ROOT_RELIGION_PILGRIMAGE(RootReligionPilgrimage.class),
        ROOT_NATURAL_TIMELINE(RootNaturalTimeline.class),
        ROOT_PENDING_UI_RUNTIME(RootPendingUiRuntime.class),
        ROOT_LIFECYCLE_RUNTIME_FACTORY(RootLifecycleRuntimeFactory.class),
        RELIGION_SERVICE(org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService.class),
        RELIGION_PILGRIMAGE(org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.class);
        private final Class<?> implementationType;
        ReaderRole(Class<?> implementationType){this.implementationType=implementationType;}
        public Class<?> implementationType(){return implementationType;}
        String legacyFileName(){return implementationType.getSimpleName()+".java";}
    }
    static <E extends Enum<E>> Map<E,ExactRef> checkedMetadata(Class<E> roleType,Map<E,ExactRef> actual) {
        Objects.requireNonNull(actual);var result=new java.util.EnumMap<E,ExactRef>(roleType);
        actual.forEach((role,reference)->{
            Objects.requireNonNull(role);nonempty(reference);result.put(role,reference);
        });
        return java.util.Collections.unmodifiableMap(result);
    }
    /** The four-argument constructor retains historical compatibility; ordinary maps record supplied refs. */
    public static final class RecordingPolicySources {
        private final Map<RecordingRole,ExactRef> roles;
        private final boolean ordinary;
        public RecordingPolicySources(ExactRef nativeDriver,ExactRef overview,ExactRef war,ExactRef battle) {
            this(Map.of(RecordingRole.NATIVE_DRIVER,nativeDriver,RecordingRole.OVERVIEW,overview,
                    RecordingRole.WAR,war,RecordingRole.BATTLE,battle),false);
            exact(nativeDriver,1658471,"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
            exact(overview,11073,"86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0");
            exact(war,241556,"b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937");
            exact(battle,91388,"2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de");
        }
        private RecordingPolicySources(Map<RecordingRole,ExactRef> actual,boolean ordinary) {
            roles=checkedMetadata(RecordingRole.class,actual);this.ordinary=ordinary;
        }
        public static RecordingPolicySources ordinary(Map<RecordingRole,ExactRef> actual) {
            return new RecordingPolicySources(actual,true);
        }
        public boolean isOrdinary(){return ordinary;}
        public Map<RecordingRole,ExactRef> roleSources(){return roles;}
        public Optional<ExactRef> source(RecordingRole role){return Optional.ofNullable(roles.get(Objects.requireNonNull(role)));}
        private ExactRef legacyAccessor(RecordingRole role) {
            return source(role).orElseThrow(()->new IllegalStateException("recording metadata is absent: "+role));
        }
        public ExactRef nativeDriver(){return legacyAccessor(RecordingRole.NATIVE_DRIVER);}
        public ExactRef overview(){return legacyAccessor(RecordingRole.OVERVIEW);}
        public ExactRef war(){return legacyAccessor(RecordingRole.WAR);}
        public ExactRef battle(){return legacyAccessor(RecordingRole.BATTLE);}
        public List<ExactRef> originals() {
            if(ordinary)return roles.values().stream().distinct().toList();
            return List.of(nativeDriver(),overview(),war(),battle(),RootFamilySendRecordingMaterial.originalContract(nativeDriver()),
                    samplingOriginal(nativeDriver()),guiServiceOriginal(nativeDriver()),guiCameraOriginal(nativeDriver()),
                    pilgrimageOriginal(nativeDriver()),closeOriginal(nativeDriver()),giftOriginal(nativeDriver()));
        }
        @Override public boolean equals(Object other) {
            return other instanceof RecordingPolicySources value&&ordinary==value.ordinary&&roles.equals(value.roles);
        }
        @Override public int hashCode(){return Objects.hash(roles,ordinary);}
        @Override public String toString(){return "RecordingPolicySources[roles="+roles+",ordinary="+ordinary+"]";}
    }
    public record Sources(ExactRef implementation,ExactRef codec,ExactRef publisher,
            RecordingPolicySources recordingPolicy,List<ExactRef> materialReaders,Map<ReaderRole,ExactRef> readerRoles) {
        public Sources {
            for(ExactRef source:List.of(implementation,codec,publisher))nonempty(source);
            Objects.requireNonNull(recordingPolicy);materialReaders=List.copyOf(materialReaders);
            readerRoles=checkedMetadata(ReaderRole.class,readerRoles);
            require(materialReaders.size()<=32&&materialReaders.stream().distinct().count()==materialReaders.size(),
                    "actual finite material reader metadata required");materialReaders.forEach(RootActionHistoryMaterialSourceFactory::nonempty);
            if(recordingPolicy.isOrdinary())
                require(materialReaders.equals(readerRoles.values().stream().distinct().toList()),"ordinary reader roles must retain identical supplied metadata");
            else require(!materialReaders.isEmpty(),"actual historical material reader implementation closure required");
        }
        public Sources(ExactRef implementation,ExactRef codec,ExactRef publisher,RecordingPolicySources policy,List<ExactRef> readers) {
            this(implementation,codec,publisher,policy,readers,Map.of());
        }
        public static Sources ordinary(ExactRef implementation,ExactRef codec,ExactRef publisher,
                Map<RecordingRole,ExactRef> recordings,Map<ReaderRole,ExactRef> readers) {
            var actual=checkedMetadata(ReaderRole.class,readers);
            return new Sources(implementation,codec,publisher,RecordingPolicySources.ordinary(recordings),
                    actual.values().stream().distinct().toList(),actual);
        }
        public boolean isOrdinary(){return recordingPolicy.isOrdinary();}
        public List<ExactRef> originals(){var refs=new LinkedHashSet<>(List.of(implementation,codec,publisher));refs.addAll(recordingPolicy.originals());refs.addAll(materialReaders);return List.copyOf(refs);}
    }
    public record Products(DriverActionHistoryPublisher.MaterialSource materials,List<ExactRef> publisherSources) {
        public Products {Objects.requireNonNull(materials);publisherSources=List.copyOf(publisherSources);require(!publisherSources.isEmpty(),"actual publisher implementation sources required");}
    }
    public static final class Prepared {
        private final Sources sources;private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        public Sources sources(){return sources;}
        public synchronized Products install(RootRuntimeContext context,RootInstalledCatalog catalog)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(catalog);require(catalog.context()==context&&context.bindings()==catalog.bindings(),"material factory requires the identical installed physical catalog");
            catalog.remainingDomains().life().requireContext(context);catalog.remainingDomains().riteCreation().requireContext(context);
            require(catalog.remainingDomains().guardian().context()==context,"actual guardian material owner differs");
            Installed old=installed.get(context);
            if(old!=null){
                require(old.catalog==catalog,"same material context cannot replace its actual catalog");
                old.requireOwner(old.authority,old.journal,old.archive);return old.products;
            }
            require(installed.size()<64,"finite actual material installation history required");
            return context.withSession(same->{
                // The context authenticates either its actual Adopted owner or its explicit private
                // Staged fixture owner under this same writer. No replacement Adopted is constructed.
                var actual=new Installed(context,catalog,sources,context.historyAuthority(same));
                actual.requirePins(same);installed.put(context,actual);return actual.products;
            });
        }
    }
    public enum MissingReason { UNINSTALLED_OPERATION, ORIGINAL_COMPATIBLE_RESULT_ABSENT, ORIGINAL_EXCEPTION_REPORT_ABSENT, INDEPENDENT_DOMAIN_ORIGINAL_ABSENT }
    public static final class Missing extends IOException {
        private static final long serialVersionUID=1L;
        private final MissingReason reason;private final OperationKey operation;
        public Missing(MissingReason reason,OperationKey operation){super(reason.name()+": "+operation.value());this.reason=Objects.requireNonNull(reason);this.operation=Objects.requireNonNull(operation);}
        public MissingReason reason(){return reason;}public OperationKey operation(){return operation;}
    }
    private static final class Installed implements DriverActionHistoryPublisher.MaterialSource {
        private final RootRuntimeContext context;private final RootInstalledCatalog catalog;private final Sources selected;
        private final DriverStateAssembler authority;private final ActionJournal journal;private final ActionPorts.OutcomeArchive archive;
        private final Products products;
        private Installed(RootRuntimeContext context,RootInstalledCatalog catalog,Sources sources,DriverStateAssembler actualAuthority){
            this.context=context;this.catalog=catalog;selected=sources;authority=Objects.requireNonNull(actualAuthority);journal=context.core().journal();archive=context.archive();
            products=new Products(this,List.of(sources.implementation(),sources.codec(),sources.publisher()));
        }
        @Override public void requireOwner(DriverStateAssembler same,ActionJournal sameJournal,ActionPorts.OutcomeArchive sameArchive){
            require(authority==same&&journal==sameJournal&&archive==sameArchive
                    &&catalog.context()==context&&catalog.bindings()==context.bindings(),"action material lost identical physical Driver/journal/archive/catalog custody");
            try {
                context.withSession(borrowed->{
                    require(context.historyAuthority(borrowed)==same,"action material lost its actual adopted or private staged Driver custody");return null;
                });
            }catch(IOException failure){throw new UncheckedIOException("actual action material history owner could not be revalidated",failure);}
        }
        @Override public List<ExactRef> sources(){
            var refs=new LinkedHashSet<>(selected.originals());
            for(var binding:catalog.bindings().actionBindings()){refs.add(binding.effect().producerSource());refs.add(binding.decoderSource());}
            for(var binding:catalog.bindings().compositeBindings()){refs.add(binding.implementationSource());refs.add(binding.decoderSource());}
            for(var binding:catalog.bindings().archivedBindings())refs.add(binding.definitionSource());
            // Future operations can only use these same already installed fixed family sources. Never issue a family here.
            for(var family:catalog.bindings().families()){refs.add(family.implementationSource());refs.add(family.decoderSource());refs.add(family.verifierSource());}
            for(var family:catalog.bindings().compositeFamilies()){refs.add(family.binding().implementationSource());refs.add(family.binding().decoderSource());refs.add(family.verifierSource());}
            refs.addAll(catalog.remainingDomains().sway().historyProducerSources());
            // The fixed operator owner replays cold canonical rejections without issuing a target family.
            refs.addAll(context.core().operatorAuthority().sources());
            for(var binding:catalog.physicalActions().installed())refs.addAll(binding.sources());
            require(refs.size()<=1024,"installed action material source closure exceeds its explicit finite budget");
            return refs.stream().sorted(java.util.Comparator.comparing(ExactRef::path).thenComparingLong(ExactRef::bytes).thenComparing(ExactRef::sha256)).toList();
        }
        @Override public void requireOperatorWithoutRebind(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(originals);context.writer().requireSession(same);requireOwner(authority,journal,archive);
            require(actual.command().expectation() instanceof CommandExpectation.OperatorRebind&&actual.settled()
                    &&actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                    &&actual.command().sessionId().equals(context.game().sessionId()),"operator non-rebind material crossed its actual installed Game/source/session");
            require(DriverOperatorNonRebindOriginals.isRecordedNonRebound(actual),
                    "only an original finite operator rejection or proved-before-write outcome has a non-rebind policy");
            String head=same.head().digest();requirePins(same);
            ExactRef receipt=originals.receiptReferenceOf(actual);
            require(actual.equals(originals.loadReceipt(receipt)),"operator non-rebind lost its actual canonical receipt");
            ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals);
            require(originals.loadRecord(record).receipt().equals(actual),"operator non-rebind is not its actual canonical history member");
            // Core retains this identical installed private owner. Its verifier reopens original guard,
            // complete preparation/outbound, source pins and known-code ACK or BEFORE_WRITE zero proof.
            // Reading canonical history never resolves or issues an action family and creates no membership.
            context.core().operatorAuthority().requireOperatorWithoutRebind(context,same,actual,originals);
            for(ExactRef ref:List.of(receipt,record)){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
            require(head.equals(same.head().digest()),"operator non-rebind verification changed the writer head");
        }
        private void requirePins(Session same)throws IOException {
            context.writer().requireSession(same);requireOwner(authority,journal,archive);
            // The complete installation closure is stable DATA. Pin only this factory's original policy/readers here;
            // the Publisher pins its own sources and this capture's exact producer set before canonical publication.
            if(!selected.isOrdinary())
                for(ExactRef ref:selected.originals()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        }
        @Override public void requireNoGameplayWrite(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(originals);context.writer().requireSession(same);requireOwner(authority,journal,archive);
            require(actual.state() instanceof ActionState.CompositeSettled
                    &&((ActionState.CompositeSettled)actual.state()).settlement() instanceof ActionState.CompositeNoGameplayWrite,
                    "no-gameplay-write consumption requires its exact typed composite terminal");
            require(actual.command().origin() instanceof CommandOrigin.Gameplay
                    &&actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                    &&actual.command().sessionId().equals(context.game().sessionId()),
                    "no-gameplay-write consumption crossed its actual settled Game/source/session");
            var life=catalog.remainingDomains().life();
            var composite=catalog.bindings().compositeBindings().stream().filter(binding->binding.handler().supports(actual.command().operation())).toList();
            require(composite.size()==1&&life.installation().composites().stream().anyMatch(binding->binding==composite.getFirst()),
                    "no-gameplay-write consumption requires its identical installed Life producer");
            var replay=catalog.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow(()->new Missing(MissingReason.UNINSTALLED_OPERATION,actual.command().operation()));
            require(replay.verifier()==life.replay(),"no-gameplay-write consumption lost its identical installed Life replay");
            var settled=(ActionState.CompositeSettled)actual.state();
            require(composite.getFirst().handler() instanceof CompositeActionPort.ZeroGameplayBeforeChildren,
                    "installed Life producer did not opt into its durable-child no-gameplay contract");
            ((CompositeActionPort.ZeroGameplayBeforeChildren)composite.getFirst().handler()).requireNoGameplayWrite(actual.command(),settled.execution());
            life.replay().verify(same.head(),actual,originals);
            // The exact typed receipt is already durable. There is no original Advance result, after-frame or history row to create.
        }
        @Override public void requireLifeControlPrefixInterruption(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals,List<ActionReceipt> canonicalChildren)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(originals);Objects.requireNonNull(canonicalChildren);context.writer().requireSession(same);requireOwner(authority,journal,archive);
            require(actual.state() instanceof ActionState.CompositeSettled
                    &&((ActionState.CompositeSettled)actual.state()).settlement() instanceof ActionState.LifeControlPrefixInterrupted,
                    "Life control prefix interruption consumption requires its exact typed composite terminal");
            require(actual.command().origin() instanceof CommandOrigin.Gameplay
                    &&actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                    &&actual.command().sessionId().equals(context.game().sessionId()),
                    "Life control prefix interruption consumption crossed its actual settled Game/source/session");
            var life=catalog.remainingDomains().life();
            var composite=catalog.bindings().compositeBindings().stream().filter(binding->binding.handler().supports(actual.command().operation())).toList();
            require(composite.size()==1&&life.installation().composites().stream().anyMatch(binding->binding==composite.getFirst()),
                    "Life control prefix interruption consumption requires its identical installed Life producer");
            var replay=catalog.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow(()->new Missing(MissingReason.UNINSTALLED_OPERATION,actual.command().operation()));
            require(replay.verifier()==life.replay(),"Life control prefix interruption consumption lost its identical installed Life replay");
            var settled=(ActionState.CompositeSettled)actual.state();
            var observation=((ActionState.LifeControlPrefixInterrupted)settled.settlement()).observation();
            require(composite.getFirst().handler() instanceof CompositeActionPort.LifeControlPrefixSource,
                    "installed Life producer did not opt into its Life control prefix interruption contract");
            ((CompositeActionPort.LifeControlPrefixSource)composite.getFirst().handler()).requireControlPrefixInterruption(actual.command(),settled.execution(),observation,canonicalChildren);
            life.replay().verify(same.head(),actual,originals);
            // Original ending and children stay archived; no completed Advance report or parent history row is created.
        }
        @Override public OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            return captureActual(same,actual,originals,true,Optional.empty());
        }
        @Override public void requireOriginal(Session same,ActionReceipt actual,OriginalMaterial captured,ActionPorts.OutcomeArchive originals)throws IOException {
            OriginalMaterial replayed=captureActual(same,actual,originals,false,captured instanceof GiftLegacyPair gift?Optional.of(gift.originals()):Optional.empty());
            require(replayed.equals(captured),"actual domain material/result/error/recording path changed during complete archived replay");
        }
        private OriginalMaterial captureActual(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals,boolean preserve,Optional<ExactRef> giftOriginals)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(originals);context.writer().requireSession(same);requireOwner(authority,journal,archive);
            require(actual.settled()&&actual.command().origin() instanceof CommandOrigin.Gameplay
                    &&actual.command().before().game().equals(context.game().generation())&&actual.command().source().equals(context.source())
                    &&actual.command().sessionId().equals(context.game().sessionId()),"material capture needs its actual settled same-Game/source/session Gameplay action");
            var op=actual.command().operation();
            if(actual.state() instanceof PhysicalActionState physical)return physical(same,actual,physical,originals,preserve);
            var replay=catalog.bindings().actualArchivedVerifier(op).orElseThrow(()->new Missing(MissingReason.UNINSTALLED_OPERATION,op));
            var action=catalog.bindings().actualActionBinding(op);
            var composite=catalog.bindings().compositeBindings().stream().filter(binding->binding.handler().supports(op)).toList();
            require(action.isPresent()^(!composite.isEmpty()),"exact installed action or composite identity required");require(composite.size()<=1,"ambiguous actual composite identity");
            // The real domain verifier opens original frames, reads, preparations, child records and publication witnesses.
            // This is archive-only. No observer/prepare/issue or current native query is called.
            var producers=new LinkedHashSet<ExactRef>(selected.originals());producers.add(replay.definitionSource());
            if(action.isPresent()) {
                var installed=catalog.bindings().actionBindings().stream().filter(binding->binding.effect()==action.orElseThrow()).toList();
                require(installed.size()==1,"original action binding identity absent");producers.add(action.orElseThrow().producerSource());producers.add(installed.getFirst().decoderSource());
            }else{producers.add(composite.getFirst().implementationSource());producers.add(composite.getFirst().decoderSource());}
            require(producers.size()<=64,"actual branch producer closure exceeds its explicit source DTO bound");
            if(!selected.isOrdinary())
                for(ExactRef ref:producers){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
            replay.verifier().verify(same.head(),actual,originals);
            var life=catalog.remainingDomains().life();
            if(!composite.isEmpty()&&life.installation().composites().stream().anyMatch(binding->binding==composite.getFirst())) {
                require(replay.verifier()==life.replay(),"Life material must use its identical installed archived replay");
                if (actual.state() instanceof ActionState.CompositeSettled settled
                        && settled.settlement() instanceof ActionState.CompositeRejected) {
                    var canonicalState=same.head().state();
                    var canonicalChildren=settled.execution().children().stream().map(bound->{
                        var child=ContinuityActionJournal.lookup(canonicalState,bound.actionId(),originals).orElseThrow();
                        require(child.bodySha256().equals(bound.bodySha256()),"Life rejected child differs from canonical writer");
                        return child;
                    }).toList();
                    return rejectedLifeInitializationMaterial(actual,canonicalChildren,originals,producers);
                }
                var recorded=life.replay().readRecorded(actual,originals);var evidence=new LinkedHashSet<Evidence>();
                frame(evidence,recorded.starting().nativeFrame(),recorded.starting().driverFacts());frame(evidence,recorded.ending().nativeFrame(),recorded.ending().driverFacts());
                ActionEffects.observation(actual).ifPresent(value->value.supportingEvidence().forEach(ref->evidence.add(new Evidence(EvidenceKind.MATERIAL,ref))));
                if(recorded.originalCompatible().isEmpty())return only(CanonicalReason.RECONCILED_WITHOUT_ORIGINAL_REPORT,evidence,producers);
                var original=recorded.originalCompatible().orElseThrow();evidence.add(new Evidence(EvidenceKind.MATERIAL,original.original()));
                return legacy(op,original.original(),original.body(),evidence,producers);
            }
            var sway=catalog.remainingDomains().sway();var swayBinding=sway.retainedArchived(actual);
            if(swayBinding.isPresent()) {
                require(swayBinding.orElseThrow()==replay,"Sway history replay must be the identical installed issued verifier");
                return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,independent(actual,originals),producers);
            }
            if(action.isPresent()&&(owned(catalog.remainingDomains().guardian().installation(),action.orElseThrow(),replay)
                    ||owned(catalog.riteCreation().installation(),action.orElseThrow(),replay)
                    ||ownedTimeline(life.infrastructure().installation(),catalog.bindings(),action.orElseThrow(),replay)&&AdvancePrimitives.supports(op)))
                return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,independent(actual,originals),producers);
            if(RootFamilySendRecordingMaterial.supports(actual)) {
                var original=selected.isOrdinary()
                        ?RootFamilySendRecordingMaterial.captureOrdinary(context,catalog,same,actual,originals,replay,
                                selected.recordingPolicy().roleSources(),selected.readerRoles(),preserve)
                        :RootFamilySendRecordingMaterial.capture(context,catalog,same,actual,originals,replay,
                                selected.recordingPolicy().nativeDriver(),selected.materialReaders(),preserve);
                producers.addAll(original.producers());var evidence=independent(actual,originals);
                evidence.add(new Evidence(EvidenceKind.READ,original.originalChoiceRead()));
                evidence.add(new Evidence(EvidenceKind.MATERIAL,original.resultRef()));
                evidence.add(new Evidence(EvidenceKind.MATERIAL,original.witnessRef()));
                return legacy(op,original.resultRef(),original.result(),evidence,producers);
            }
            if(op.value().equals("enable-army-observer-research-sampling-v1")||op.value().equals("disable-army-observer-research-sampling-v1")) {
                var transport=catalog.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,RootDriverTransportRuntimeFactory.Runtime.class);
                transport.requireContext(context);
                require(action.isPresent()&&owned(transport.installation(),action.orElseThrow(),replay),"sampling history requires identical installed transport action and archived verifier");
                reader(ReaderRole.ROOT_DRIVER_TRANSPORT_RUNTIME_FACTORY);reader(ReaderRole.ARMY_OBSERVER_SAMPLING);
                RawJson raw=transport.driverResult(actual,originals);ExactRef result=retain(raw,originals,preserve);
                var evidence=independent(actual,originals);evidence.add(new Evidence(EvidenceKind.MATERIAL,result));
                return legacy(op,result,raw,evidence,producers);
            }
            if(op.equals(org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies.GIFT)&&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                require(action.isPresent()&&composite.isEmpty(),"Gift history requires its one actual installed primitive action");
                for(var role:List.of(ReaderRole.GIFT_ACTION_HISTORY_EVIDENCE,ReaderRole.FINANCE_READ_CONTRACTS,ReaderRole.NATIVE_FINANCE_EFFECTS))reader(role);
                var finance=context.finance();require(finance.game().equals(context.game().generation())&&finance.sessionId().equals(context.game().sessionId())
                        &&finance.source().equals(context.source()),"Gift history crossed its actual installed finance owner");
                org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.Captured captured;
                if(preserve)captured=org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.capture(same,actual,originals,context.frameLoader(),finance.definitions());
                else captured=org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.verify(same,actual,
                        giftOriginals.orElseThrow(()->new Missing(MissingReason.ORIGINAL_COMPATIBLE_RESULT_ABSENT,op)),originals,context.frameLoader(),finance.definitions());
                // Owning capture preserves both numeric originals. Replay verifies without writing any material.
                ExactRef submit=originals.materialReferenceOf(captured.submitResult()),receipt=originals.materialReferenceOf(captured.receiptResult());
                var evidence=independent(actual,originals);evidence.add(new Evidence(EvidenceKind.MATERIAL,captured.originals()));
                NativeEffectEvidence.archivedReads(actual,originals).forEach(read->evidence.add(new Evidence(EvidenceKind.READ,originals.readReferenceOf(read))));
                evidence.add(new Evidence(EvidenceKind.MATERIAL,submit));evidence.add(new Evidence(EvidenceKind.MATERIAL,receipt));
                return new GiftLegacyPair(captured.originals(),submit,receipt,
                        org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(captured.submitResult(),captured.submitPublic()),
                        org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers.fromResults(captured.receiptResult(),captured.receiptPublic()),
                        List.copyOf(evidence),List.copyOf(producers));
            }
            if(op.value().equals(org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.SUBMIT_STEP)) {
                var religion=catalog.additionalDomains().religion();
                var runtime=religion.service().component(RootReligionPilgrimage.Runtime.class).orElseThrow(()->new Missing(MissingReason.UNINSTALLED_OPERATION,op));
                runtime.requireContext(context);require(runtime.matchesControl(actual.command())&&action.isPresent()
                        &&action.orElseThrow()==runtime.actionBinding().effect()&&replay==runtime.archivedBinding()
                        &&owned(runtime.installation(),action.orElseThrow(),replay)&&owned(religion.installation(),action.orElseThrow(),replay),
                        "pilgrimage material requires its identical original installed runtime/action/replay");
                for(var role:List.of(ReaderRole.ROOT_RELIGION_PILGRIMAGE,ReaderRole.RELIGION_SERVICE,ReaderRole.RELIGION_PILGRIMAGE))reader(role);
                var evidence=actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Rejected rejected
                        ?pilgrimageRejected(rejected,originals):independent(actual,originals);
                return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,evidence,producers);
            }
            if(op.equals(new OperationKey("save-checkpoint"))
                    &&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    &&actual.state() instanceof ActionState.Settled settled
                    &&settled.settlement() instanceof ActionState.Applied applied) {
                require(action.isPresent() && composite.isEmpty(), "SAVE history requires its one actual installed primitive action");
                var observation = applied.observation();
                require(observation.observerSchema().equals(org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory.OBSERVER_SCHEMA),
                        "SAVE material requires its exact checkpoint observer schema");
                var evidence = new LinkedHashSet<Evidence>();
                // The archived verifier has already validated the physical pair and saved Driver.
                // Retain their original material references and the independent native frame evidence.
                var supporting = observation.supportingEvidence();
                require(supporting.size() == 2, "SAVE requires its typed pair and complete saved Driver archived originals");
                evidence.add(new Evidence(EvidenceKind.MATERIAL, supporting.get(0)));
                evidence.add(new Evidence(EvidenceKind.MATERIAL, supporting.get(1)));
                evidence.add(new Evidence(EvidenceKind.NATIVE_FRAME, observation.originalEvidence()));
                return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER, evidence, producers);
            }
            if(op.value().equals(org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.CLOSE_STEP)) {
                var lifecycle=catalog.remainingDomains().lifecycle();lifecycle.requireContext(context);var timeline=lifecycle.natural().timeline();
                require(action.isPresent()&&action.orElseThrow()==timeline.actionBinding().effect()&&replay==timeline.replayBinding()
                        &&owned(lifecycle.installation(),action.orElseThrow(),replay)
                        &&actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,
                        "Close material requires its identical original installed timeline and independently replayed control");
                for(var role:List.of(ReaderRole.ROOT_NATURAL_TIMELINE,ReaderRole.ROOT_PENDING_UI_RUNTIME,ReaderRole.ROOT_LIFECYCLE_RUNTIME_FACTORY))reader(role);
                return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,independent(actual,originals),producers);
            }
            // Generic ordinary effects carry an explicit durable NativeEffectEvidence compatible original.
            Optional<NativeEffectEvidence.Original> nativeOriginal=NativeEffectEvidence.loadIfPresent(actual,originals,context.frameLoader());
            if(nativeOriginal.isPresent()) {
                var original=nativeOriginal.orElseThrow();var evidence=independent(actual,originals);
                frame(evidence,original.frames().before().originalEvidence(),NativeEffectEvidence.basis(original.frames().before()).driverFacts());
                frame(evidence,original.frames().after().originalEvidence(),NativeEffectEvidence.basis(original.frames().after()).driverFacts());
                for(var read:original.independentReads())evidence.add(new Evidence(EvidenceKind.READ,originals.readReferenceOf(read)));
                original.supportingMaterials().forEach(ref->evidence.add(new Evidence(EvidenceKind.MATERIAL,ref)));
                ExactRef result=originals.materialReferenceOf(original.compatibleResult());evidence.add(new Evidence(EvidenceKind.MATERIAL,result));
                return legacy(op,result,original.compatibleResult(),evidence,producers);
            }
            if(!composite.isEmpty()&&composite.getFirst().handler() instanceof RouteContactComposite) {
                RawJson raw=new RawJson(DriverJson.encode(RouteContactEvidenceArchive.compatibleResult(actual,originals)));
                ExactRef result=retain(raw,originals,preserve);var evidence=independent(actual,originals);evidence.add(new Evidence(EvidenceKind.MATERIAL,result));return legacy(op,result,raw,evidence,producers);
            }
            // Registry retains only a material returned by this actual installed verified observer, never ACK.result.
            if(actual.state() instanceof ActionState.Settled settled) {
                Optional<RawJson> compatible=catalog.bindings().effects().compatibleResult(actual.command().actionId(),settled.attempt().requestId());
                if(compatible.isPresent()) {
                    RawJson raw=compatible.orElseThrow();ExactRef result=retain(raw,originals,preserve);var evidence=independent(actual,originals);
                    evidence.add(new Evidence(EvidenceKind.MATERIAL,result));return legacy(op,result,raw,evidence,producers);
                }
            }
            // Original exceptions must come from their real recorder. A typed rejection reason is not its old Exception text.
            if(actual.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH||actual.outcome()==ActionReceipt.Outcome.REJECTED_CONFIRMED)
                throw new Missing(MissingReason.ORIGINAL_EXCEPTION_REPORT_ABSENT,op);
            throw new Missing(MissingReason.ORIGINAL_COMPATIBLE_RESULT_ABSENT,op);
        }
        private void reader(ReaderRole role){
            if(selected.isOrdinary())return;
            String file=role.legacyFileName();
            require(selected.materialReaders().stream().anyMatch(ref->ref.path().replace((char)92,'/').endsWith("/"+file)),
                    "actual original material reader source is missing: "+file);
        }
        private OriginalMaterial physical(Session same,ActionReceipt actual,PhysicalActionState state,
                ActionPorts.OutcomeArchive originals,boolean preserve)throws IOException {
            var op=actual.command().operation();
            if(!op.equals(RootGuiPresentation.OPERATION))throw new Missing(MissingReason.UNINSTALLED_OPERATION,op);
            var gui=catalog.additionalDomains().gui();
            var binding=catalog.physicalActions().find(op).orElseThrow(()->new Missing(MissingReason.UNINSTALLED_OPERATION,op));
            require(binding==gui.physicalBinding()&&catalog.physicalActions().require(actual.command())==binding
                    &&gui.matchesPhysical(actual.command())
                    &&binding.transportKind()==org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP
                    &&state.request() instanceof PreparedAction.MmapRequest&&state.terminal()
                    &&catalog.bindings().actualActionBinding(op).isEmpty()&&catalog.bindings().actualArchivedVerifier(op).isEmpty(),
                    "only the identical installed source-owned GUI mmap terminal has this direct recording policy");
            require(actual.equals(originals.loadReceipt(originals.receiptReferenceOf(actual))),"physical history lost its original canonical receipt");
            require(state.outcome().orElse(null) instanceof PhysicalOutcome.MmapOutcome,
                    "terminal physical history requires its actual typed original outcome");
            var physicalOutcome=((PhysicalOutcome.MmapOutcome)state.outcome().orElseThrow()).value();
            require(state.phase()==PhysicalActionState.Phase.NOT_POSTED
                            ?physicalOutcome instanceof org.xar.ck3.control.contracts.presentation.OriginalOutcome.NotPosted
                            :state.phase()==PhysicalActionState.Phase.COMPLETED&&physicalOutcome instanceof org.xar.ck3.control.contracts.presentation.OriginalOutcome.Posted,
                    "physical terminal phase crossed its original post or proved-not-posted outcome");
            reader(ReaderRole.ROOT_GUI_PRESENTATION);reader(ReaderRole.PHYSICAL_ACTION_CODEC);
            var producers=new LinkedHashSet<ExactRef>(selected.originals());producers.addAll(binding.sources());
            require(producers.size()<=64,"actual physical source closure exceeds the history DTO bound");
            if(!selected.isOrdinary())
                for(var ref:producers){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
            // Exact producer reopens typed preparation, post bytes and independent observations. Never post or observe again.
            binding.producer().verifyArchived(same.head(),actual,originals);
            RawJson raw=physicalWitness(state,originals);ExactRef witness=retain(raw,originals,preserve);
            var evidence=new LinkedHashSet<Evidence>();evidence.add(new Evidence(EvidenceKind.MATERIAL,witness));
            evidence.add(new Evidence(EvidenceKind.NATIVE_FRAME,state.guard().nativeEvidence()));
            // Codec metadata retains mixed physical roles; they must not all be loaded as MATERIAL.
            return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,evidence,producers);
        }
    }
    /** Full typed archive DATA. Its construction grants neither physical completion nor installed producer qualification. */
    static RawJson physicalWitness(PhysicalActionState state,ActionPorts.OutcomeArchive originals){
        require(state.terminal()&&state.request() instanceof PreparedAction.MmapRequest,"terminal original mmap metadata required");
        var raw=new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(PhysicalActionCodec.encode(state,originals)));
        require(PhysicalActionCodec.decode(org.xar.ck3.control.contracts.StrictJson.parse(raw.bytes()),originals).equals(state),
                "physical typed originals changed across complete metadata roundtrip");return raw;
    }
    private static LinkedHashSet<Evidence> pilgrimageRejected(ActionState.Rejected rejected,ActionPorts.OutcomeArchive originals){
        var proof=org.xar.ck3.control.contracts.StrictJson.object(org.xar.ck3.control.contracts.StrictJson.parse(originals.loadMaterial(rejected.originalEvidence()).bytes()),java.util.Set.of("schema","independent_read"));
        require(org.xar.ck3.control.contracts.StrictJson.text(proof.get("schema")).equals("xar.java.pilgrimage-original-rejection/v1"),"original pilgrimage rejection proof required");
        ExactRef reference=ExactRef.fromJson(proof.get("independent_read"));var read=originals.loadRead(reference);
        require(originals.readReferenceOf(read).equals(reference),"original pilgrimage independent rejection read changed");
        return new LinkedHashSet<>(List.of(new Evidence(EvidenceKind.MATERIAL,rejected.originalEvidence()),new Evidence(EvidenceKind.READ,reference),
                new Evidence(EvidenceKind.NATIVE_FRAME,read.after().binding().nativeEvidence())));
    }
    private static boolean owned(RootDomainInstallation owner,NativeEffectRegistry.Binding effect,NativeRecordedEvidenceVerifier.Binding replay){
        boolean action=owner.actions().stream().anyMatch(binding->binding.effect()==effect);
        boolean verifier=owner.archived().stream().anyMatch(binding->binding==replay);
        require(!action||verifier,"installed domain action lost its original archived verifier identity");return action&&verifier;
    }
    private static boolean ownedTimeline(RootDomainInstallation owner,RootExecutableBindings bindings,NativeEffectRegistry.Binding effect,NativeRecordedEvidenceVerifier.Binding replay){
        if(owned(owner,effect,replay))return true;
        var family=bindings.actualFamily(effect.operation()).orElse(null);
        if(family==null||!owner.actionFamilies().stream().anyMatch(installed->installed==family))return false;
        var binding=bindings.actionBindings().stream().filter(candidate->candidate.effect()==effect).findFirst().orElse(null);
        if(binding==null||!binding.effect().producerSource().equals(family.implementationSource())
                ||!binding.decoderSource().equals(family.decoderSource()))return false;
        var archived=bindings.archivedBindings().stream().filter(candidate->candidate.operation().equals(effect.operation())).findFirst().orElse(null);
        return archived!=null&&archived==replay&&archived.definitionSource().equals(family.verifierSource());
    }
    private static Legacy legacy(OperationKey op,ExactRef result,RawJson body,LinkedHashSet<Evidence> evidence,LinkedHashSet<ExactRef> producers){
        Obj original=DriverJson.object(body.bytes(),DriverJson.MAX_NATIVE_BYTES);
        return new Legacy(recording(op,original),Optional.of(result),Optional.empty(),List.copyOf(evidence),List.copyOf(producers));
    }
    /** The verified zero-dispatch initialization has original refusal material, but no Advance report or after-frame. */
    static CanonicalOnly rejectedLifeInitializationMaterial(ActionReceipt actual,List<ActionReceipt> canonicalChildren,
            ActionPorts.OutcomeArchive originals,LinkedHashSet<ExactRef> producers) {
        require(actual.outcome()==ActionReceipt.Outcome.REJECTED_CONFIRMED && !actual.visibleGameplay() && !actual.eligibleAdvance()
                && actual.state() instanceof ActionState.CompositeSettled,"actual rejected Life terminal required");
        var settled=(ActionState.CompositeSettled)actual.state();
        require(settled.settlement() instanceof ActionState.CompositeRejected rejected && rejected.evidence().isEmpty()
                && rejected.children().equals(settled.execution().children()),"rejected Life retains its complete original child vector");
        org.xar.ck3.control.application.advance.LifeAdvanceComposite.requireRejectedInitialization(actual.command(),settled.execution(),canonicalChildren);
        var evidence=new LinkedHashSet<Evidence>();
        for(var child:canonicalChildren) {
            var rejected=(ActionState.RejectedBeforeDispatch)child.state();
            evidence.add(new Evidence(EvidenceKind.ACTION_RECEIPT,originals.receiptReferenceOf(child)));
            evidence.add(new Evidence(EvidenceKind.MATERIAL,originals.referenceOf(rejected.dispatch())));
            evidence.add(new Evidence(EvidenceKind.NATIVE_FRAME,rejected.attempt().guard().nativeEvidence()));
        }
        return only(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,evidence,producers);
    }

    private static CanonicalOnly only(CanonicalReason reason,LinkedHashSet<Evidence> evidence,LinkedHashSet<ExactRef> producers){
        return new CanonicalOnly(reason,List.copyOf(evidence),List.copyOf(producers));
    }
    private static ExactRef retain(RawJson raw,ActionPorts.OutcomeArchive originals,boolean preserve){
        ExactRef ref=preserve?originals.preserveMaterial(raw):originals.materialReferenceOf(raw);
        require(raw.equals(originals.loadMaterial(ref)),"original domain result archive changed");return ref;
    }
    private static void frame(LinkedHashSet<Evidence> out,ExactRef nativeFrame,ExactRef driverFacts){out.add(new Evidence(EvidenceKind.NATIVE_FRAME,nativeFrame));out.add(new Evidence(EvidenceKind.MATERIAL,driverFacts));}
    /** Only typed settlement originals; mixed publication/writer refs are never mislabelled as material. */
    private static LinkedHashSet<Evidence> independent(ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws Missing {
        var refs=new LinkedHashSet<Evidence>();
        if (IntentAbandonmentProof.isAbandonedResume(actual)) {
            var parent = IntentAbandonmentProof.originalParent(actual, archive);
            var proof = (ActionState.IntentAbandoned) actual.state();
            refs.add(new Evidence(EvidenceKind.ACTION_RECORD, proof.originalIntentRecord()));
            refs.add(new Evidence(EvidenceKind.ACTION_RECORD, proof.originalActionHead()));
            // The original parent guard is BEFORE evidence; no post-state was observed for the abandoned Intent.
            refs.add(new Evidence(EvidenceKind.NATIVE_FRAME,
                    ((ActionState.CompositeUnknown) parent.state()).execution().guard().nativeEvidence()));
            return refs;
        }
        ActionEffects.observation(actual).ifPresent(value->{refs.add(new Evidence(EvidenceKind.NATIVE_FRAME,value.originalEvidence()));value.supportingEvidence().forEach(ref->refs.add(new Evidence(EvidenceKind.MATERIAL,ref)));});
        ActionState.Settlement settlement=actual.state() instanceof ActionState.Settled value?value.settlement():actual.state() instanceof ActionState.CompositeSettled value?value.settlement():null;
        if(settlement instanceof ActionState.ControlApplied control){refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(control.read())));control.supportingReads().forEach(read->refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(read))));}
        if(settlement instanceof ActionState.FamilySendConfirmed send){
            FamilySendObservation original=send.observation();frame(refs,original.beforeFrame().nativeFrame(),original.beforeFrame().driverFacts());frame(refs,original.afterFrame().nativeFrame(),original.afterFrame().driverFacts());
            refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(original.beforeStorage())));refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(original.afterStorage())));
            original.completePreparation().forEach(ref->refs.add(new Evidence(EvidenceKind.MATERIAL,ref)));
        }
        if(settlement instanceof ActionState.SwaySchedulerCompleted scheduler){
            var original=scheduler.proof();refs.add(new Evidence(EvidenceKind.MATERIAL,original.originalRun()));frame(refs,original.finalFrame().nativeFrame(),original.finalFrame().driverFacts());
            original.finalReads().forEach(ref->refs.add(new Evidence(EvidenceKind.READ,ref)));original.childReceiptRefs().forEach(ref->refs.add(new Evidence(EvidenceKind.ACTION_RECEIPT,ref)));
            original.fullPlanOriginals().ifPresent(plan->{refs.add(new Evidence(EvidenceKind.MATERIAL,plan.request()));refs.add(new Evidence(EvidenceKind.MATERIAL,plan.result()));});
        }
        if(settlement instanceof ActionState.NonAppliedTerminal terminal){
            var original=terminal.observation();refs.add(new Evidence(EvidenceKind.NATIVE_FRAME,original.originalEvidence()));
            refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(original.selectedCollection())));refs.add(new Evidence(EvidenceKind.READ,archive.readReferenceOf(original.afterCollection())));
            original.supportingEvidence().forEach(ref->refs.add(new Evidence(EvidenceKind.MATERIAL,ref)));
        }
        if(refs.isEmpty())throw new Missing(MissingReason.INDEPENDENT_DOMAIN_ORIGINAL_ABSENT,actual.command().operation());return refs;
    }
    /** execute_step L9651..9665; only called after an identical real installed operation/material was replayed. */
    static Recording recording(OperationKey op,Obj result){
        String step=op.value();boolean accepted=sampling(step)||step.equals("query-war-declared-overview-v1")||step.equals("close-war-declared-overview-v1")
                ||move(step)&&new Text("observed_after_native_error").equals(result.get("status"))&&new Bool(false).equals(result.get("native_ack_verified"))
                ||route(step)&&new Text("xar.route-contact-readonly-unavailable.v1").equals(result.get("schema"))&&new Text("unavailable").equals(result.get("status"))
                ||numberStep(step,"query-war-termination-options-",false)&&new Text("xar.war-termination-readonly-unavailable/v1").equals(result.get("schema"))&&new Text("unavailable").equals(result.get("status"))
                ||numberStep(step,"query-battle-control-snapshot-v1-",true)&&new Text("xar.battle-control-readonly-unavailable.v1").equals(result.get("schema"))&&new Text("unavailable").equals(result.get("status"));
        if(accepted)require(result.get("accepted") instanceof Bool,"actual accepted-return predicate requires original bool accepted");return accepted?Recording.ACCEPTED_RETURN:Recording.RETURNED;
    }
    static ExactRef samplingOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("army_observer_research_sampling_control.py").toString().replace((char)92,'/'),13969,"927fdbb94ae5c07a14f4039595c865af3b28eac0ecdb0fb629ead9b38016b5ae");}
    static ExactRef guiServiceOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("service.py").toString().replace((char)92,'/'),897392,"a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e");}
    static ExactRef guiCameraOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("realm_overview_camera.py").toString().replace((char)92,'/'),18206,"8ac023d51c8f36ec96d40df0da745f20b2e79aed8c43c365a9260e080fa074ec");}
    static ExactRef giftOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("faction_gift_formal_route_v1.py").toString().replace((char)92,'/'),25674,"90d80bc2602095cfbf81e58e737089df20cde5d4eddb1af3f4d7f2544b7e4310");}
    static ExactRef pilgrimageOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("player_pilgrimage_planner_private_transport.py").toString().replace((char)92,'/'),17095,"d5932bd2a7f6396621f53588bb8ca2791138e48389e4f1a321449d66d9bb3c08");}
    static ExactRef closeOriginal(ExactRef driver){return new ExactRef(java.nio.file.Path.of(driver.path()).resolveSibling("death_succession_modal_private_transport.py").toString().replace((char)92,'/'),22301,"135187b16c0d857c65f53ec24634a45b111219d0e6ac2dd0cf17ab0838726cd2");}
    private static boolean sampling(String step){return step.equals("enable-army-observer-research-sampling-v1")||step.equals("disable-army-observer-research-sampling-v1");}
    private static boolean move(String step){return org.xar.ck3.control.application.planning.military.WarHistorySteps.parseMove(step).isPresent();}
    private static boolean numberStep(String step,String prefix,boolean zero){
        if(!step.startsWith(prefix))return false;String tail=step.substring(prefix.length());if(!tail.matches(zero?"0|[1-9][0-9]*":"[1-9][0-9]*")||tail.length()>10)return false;
        return new java.math.BigInteger(tail).compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE))<=0;
    }
    private static boolean route(String step){try{org.xar.ck3.control.application.routecontact.RouteContactSteps.query(step);return true;}catch(IllegalArgumentException malformed){return false;}}
    private static void exact(ExactRef ref,long bytes,String sha){Objects.requireNonNull(ref);require(ref.bytes()==bytes&&ref.sha256().equals(sha),"actual audited original recording-policy source differs; re-review the translation before selecting a successor");}
    private static void nonempty(ExactRef ref){Objects.requireNonNull(ref);require(ref.bytes()>0,"actual nonempty implementation source required");}
}
