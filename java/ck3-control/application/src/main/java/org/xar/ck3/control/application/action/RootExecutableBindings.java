package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The sole live inventory contains the actual preparer, observer and original-evidence verifier. */
public final class RootExecutableBindings implements ExecutableStepBindings, ActionPorts.PreparationPort {
    private record PhysicalStatusAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority actual) { }
    private final Map<org.xar.ck3.control.contracts.GameGeneration,PhysicalStatusAuthority> physicalStatusAuthorities=new HashMap<>();
    /** Bind the actual per-Game raw read issuer once into the same installed catalog. */
    public synchronized void bindPhysicalStatusAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority actual) {
        Objects.requireNonNull(game);StrictJson.text(sessionId);Objects.requireNonNull(source);Objects.requireNonNull(actual);
        PhysicalStatusAuthority prior=physicalStatusAuthorities.get(game);
        if(prior!=null){StrictJson.require(prior.actual()==actual&&prior.sessionId().equals(sessionId)&&prior.source().equals(source),
                "actual physical Status authority cannot be replaced");return;}
        StrictJson.require(physicalStatusAuthorities.size()<64,"bounded actual per-Game physical Status authorities required");
        physicalStatusAuthorities.put(game,new PhysicalStatusAuthority(game,sessionId,source,actual));
    }
    public synchronized org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority requirePhysicalStatusAuthority(PhysicalStatusIdentity identity) {
        Objects.requireNonNull(identity);var actual=physicalStatusAuthorities.get(identity.game());
        StrictJson.require(actual!=null&&actual.sessionId().equals(identity.sessionId())&&actual.source().equals(identity.source()),
                "actual physical Status issuer is not installed for this Game/source/session");
        return actual.actual();
    }
    @FunctionalInterface public interface CaptureReadOnlyWork<T> { T consume()throws Exception; }
    private record CaptureReadOnlyScope(Thread owner,CaptureReadOnlyScope parent) { }
    private final Map<org.xar.ck3.control.contracts.GameGeneration,CaptureReadOnlyScope> captureReadOnlyScopes=new HashMap<>();
    /** A synchronous denial only. The callback receives no handle which can close or replace another scope. */
    public <T>T withCaptureReadOnly(org.xar.ck3.control.contracts.GameGeneration game,CaptureReadOnlyWork<T> work)throws Exception {
        Objects.requireNonNull(game);Objects.requireNonNull(work);
        final CaptureReadOnlyScope scope;
        synchronized(this) {
            var prior=captureReadOnlyScopes.get(game);
            if(prior!=null&&prior.owner()!=Thread.currentThread())
                throw new java.io.IOException("capture read-only scope belongs to another thread");
            StrictJson.require(prior!=null||captureReadOnlyScopes.size()<64,"bounded per-Game capture read-only scopes required");
            scope=new CaptureReadOnlyScope(Thread.currentThread(),prior);captureReadOnlyScopes.put(game,scope);
        }
        try{return work.consume();}
        finally {
            synchronized(this) {
                if(captureReadOnlyScopes.get(game)!=scope||scope.owner()!=Thread.currentThread())
                    throw new IllegalStateException("capture read-only scope lost its original owner");
                if(scope.parent()==null)captureReadOnlyScopes.remove(game);else captureReadOnlyScopes.put(game,scope.parent());
            }
        }
    }
    /** Pure denial, independent of the original physical observation scope. */
    public synchronized void requireOutsideCaptureReadOnly(org.xar.ck3.control.contracts.GameGeneration game)throws java.io.IOException {
        if(captureReadOnlyScopes.containsKey(Objects.requireNonNull(game)))
            throw new java.io.IOException("capture read-only validation forbids an action");
    }
    /** Automatic collection has no single command; no collection may write while this catalog has a capture callback. */
    public synchronized void requireOutsideCaptureReadOnly()throws java.io.IOException {
        if(!captureReadOnlyScopes.isEmpty())throw new java.io.IOException("capture read-only validation forbids automatic collection");
    }
    /** Central action prelude calls this before any canonical mutation on every physical/pipe/composite plane. */
    public void requireOutsidePhysicalStatusRead(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            org.xar.ck3.control.contracts.GameGeneration game) throws java.io.IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(game);same.head();
        final PhysicalStatusAuthority actual;synchronized(this){actual=physicalStatusAuthorities.get(game);}
        if(actual!=null)actual.actual().requireOutside(same);
    }
    @Override public void requireOutsideReadOnlyScope(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionCommand command) {
        Objects.requireNonNull(command);
        try{requireOutsideCaptureReadOnly(command.origin().game());requireOutsidePhysicalStatusRead(same,command.origin().game());}
        catch(java.io.IOException unavailable){throw new java.io.UncheckedIOException("actual read-only physical Status scope forbids an action",unavailable);}
    }
    private record DirectWindowAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,DirectFixedWindowQueryAuthority actual){}
    private final Map<org.xar.ck3.control.contracts.GameGeneration,DirectWindowAuthority> directWindowAuthorities=new HashMap<>();
    public synchronized void bindDirectWindowQueryAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,DirectFixedWindowQueryAuthority actual) throws java.io.IOException {
        Objects.requireNonNull(game);StrictJson.text(sessionId);Objects.requireNonNull(source);Objects.requireNonNull(actual);
        actual.requireOwner(game,sessionId,source);
        DirectWindowAuthority prior=directWindowAuthorities.get(game);
        if(prior!=null){StrictJson.require(prior.actual()==actual&&prior.sessionId().equals(sessionId)&&prior.source().equals(source),
                "actual direct-window query authority cannot be replaced");return;}
        StrictJson.require(directWindowAuthorities.size()<64,"bounded actual per-Game direct-window query authorities required");
        directWindowAuthorities.put(game,new DirectWindowAuthority(game,sessionId,source,actual));
    }
    @Override public ActionPorts.PostconditionResult observeOriginalDirectWindowQuery(
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionReceipt actualPending,
            DirectFixedWindowQueryContinuation token,ActionPorts.DirectWindowQueryWork work)
            throws java.io.IOException,InterruptedException {
        Objects.requireNonNull(same);Objects.requireNonNull(actualPending);Objects.requireNonNull(token);Objects.requireNonNull(work);same.head();
        ActionCommand command=actualPending.command();
        String close=command.operation().value();
        StrictJson.require(Set.of("close-war-declared-overview-v1","close-war-results-window-v1").contains(close)
                &&command.origin() instanceof CommandOrigin.Gameplay&&token.actionId().equals(command.actionId()),
                "only the exact original direct fixed-window close may consume its source-owned query");
        var arguments=org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.decode(command.arguments());
        StrictJson.require(arguments.executionProfile()==org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW,
                "SDK or another action profile cannot borrow direct-window query continuation");
        final DirectWindowAuthority authority;synchronized(this){authority=directWindowAuthorities.get(command.origin().game());}
        if(authority==null||!authority.sessionId().equals(command.sessionId())||!authority.source().equals(command.source()))
            throw new java.io.IOException("actual source-owned direct-window query authority is unavailable");
        authority.actual().requireOwner(command.origin().game(),command.sessionId(),command.source());
        ActionPorts.PostconditionResult result=authority.actual().observeOriginalQuery(same,actualPending,token,work);
        authority.actual().requireOwner(command.origin().game(),command.sessionId(),command.source());
        StrictJson.require(result instanceof ActionPorts.DirectFixedWindowObserved||result instanceof ActionPorts.Pending,
                "direct-window query source returned another action settlement");
        return Objects.requireNonNull(result);
    }
    /** Actual private public-pause issuer. Parsed parent/caller/locator facts never implement its authority. */
    public interface PublicPauseAuthority {
        ExactRef definitionSource();
        CompositeActionPort handler();
        void requireOwner(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
                org.xar.ck3.control.g2.common.G2Source source)throws java.io.IOException;
        GuardEvidence verifyParent(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionCommand parent);
        ExactRef verifyReservedPause(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionCommand child,
                org.xar.ck3.control.application.readiness.ReadinessAuthority.PhysicalReadLease actual,
                InstalledStep definition,ActionPorts.OutcomeArchive archive)throws java.io.IOException;
        void verifyArchivedParent(ActionCommand parent,GuardEvidence guard,ActionPorts.OutcomeArchive archive,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.application.effects.OriginalEvidencePort originals)throws java.io.IOException;
        void verifyArchivedChild(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionReceipt child,
                GuardEvidence guard,ActionPorts.OutcomeArchive archive,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.application.effects.OriginalEvidencePort originals)throws java.io.IOException;
    }
    private Optional<PublicPauseAuthority> publicPauseAuthority=Optional.empty();
    public synchronized void bindPublicPauseAuthority(PublicPauseAuthority actual)throws java.io.IOException {
        Objects.requireNonNull(actual);requireSource(actual.definitionSource());
        var handler=Objects.requireNonNull(actual.handler());
        var matches=compositeBindings.stream().filter(binding->binding.handler()==handler
                &&binding.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&binding.implementationSource().equals(actual.definitionSource())).toList();
        StrictJson.require(matches.size()==1&&composites.find(org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.OPERATION).orElseThrow()==handler,
                "public pause issuer must be the identical actually registered closed composite/source");
        if(publicPauseAuthority.isPresent()){StrictJson.require(publicPauseAuthority.orElseThrow()==actual,"actual public pause issuer cannot be replaced");return;}
        publicPauseAuthority=Optional.of(actual);
    }
    /** Pure finite routing only; permission always requires the same installed private source below. */
    public static boolean isPublicPauseParent(ActionCommand parent){
        Objects.requireNonNull(parent);
        if(!parent.operation().equals(org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.OPERATION))return false;
        org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.validateParent(parent);return true;
    }
    public PublicPauseAuthority requirePublicPauseAuthority(ActionCommand parent)throws java.io.IOException {
        StrictJson.require(isPublicPauseParent(parent),"only the exact typed public pause parent uses its private issuer");
        final PublicPauseAuthority actual;synchronized(this){actual=publicPauseAuthority.orElseThrow(
                ()->new java.io.IOException("actual source-owned public pause authority is unavailable"));}
        actual.requireOwner(parent.origin().game(),parent.sessionId(),parent.source());
        StrictJson.require(composites.find(parent.operation()).orElseThrow()==actual.handler()
                &&compositeBindings.stream().filter(binding->binding.handler()==actual.handler()
                    &&binding.implementationSource().equals(actual.definitionSource())).count()==1,
                "public pause private issuer escaped its actual registered handler/source");
        return actual;
    }
    private record OperatorAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,ActionPorts.GuardPort guard) { }
    private final Map<org.xar.ck3.control.contracts.GameGeneration,OperatorAuthority> operatorAuthorities=new HashMap<>();
    /** Root installs its actual private per-Game issuer into this identical installed catalog. */
    public synchronized void bindOperatorAuthority(org.xar.ck3.control.contracts.GameGeneration game,String sessionId,
            org.xar.ck3.control.g2.common.G2Source source,ActionPorts.GuardPort actual) {
        Objects.requireNonNull(game);StrictJson.text(sessionId);Objects.requireNonNull(source);Objects.requireNonNull(actual);
        OperatorAuthority prior=operatorAuthorities.get(game);
        if(prior!=null){StrictJson.require(prior.guard()==actual&&prior.sessionId().equals(sessionId)&&prior.source().equals(source),"operator authority cannot be replaced");return;}
        StrictJson.require(operatorAuthorities.size()<64,"bounded actual per-Game operator authorities required");
        operatorAuthorities.put(game,new OperatorAuthority(game,sessionId,source,actual));
    }
    public GuardEvidence verifyOperatorAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,ActionCommand command) {
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,"only an exact typed operator request may use its private authority");
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay||command.origin() instanceof CommandOrigin.LifecycleTerminal,"operator does not create another origin");
        final OperatorAuthority actual;synchronized(this){actual=operatorAuthorities.get(command.origin().game());}
        StrictJson.require(actual!=null&&actual.sessionId().equals(command.sessionId())&&actual.source().equals(command.source()),"actual source-bound operator authority is not installed for this Game/session");
        return actual.guard().verify(Objects.requireNonNull(head),command);
    }
    /** Implemented by the same real CLOSE preparation producer; no detached proof DTO grants a route. */
    public interface SuccessionUiOriginProof extends ActionPorts.PreparationPort {
        ExactRef successionUiDefinitionSource();
        void requireSuccessionOrigin(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session original,
                ActionCommand exactCommand) throws java.io.IOException;
    }
    /** Only the identical actual source/material producer can qualify the two original CoA source actions. */
    public interface CoaSourceOriginProof extends ActionPorts.PreparationPort {
        ExactRef coaSourceDefinitionSource();
        void requireCoaSourceOrigin(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session original,
                ActionCommand exactCommand) throws java.io.IOException;
    }
    /** Same actual operator preparation source; its private Root scope must qualify the exact typed request. */
    public interface OperatorSourceOriginProof extends ActionPorts.PreparationPort {
        ExactRef operatorDefinitionSource();
        void requireOperatorOrigin(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session original,
                ActionCommand exactCommand) throws java.io.IOException;
    }
    public record ActionBinding(NativeEffectRegistry.Binding effect, ReadContract.GuardMode guardMode,
            Optional<String> requiredCapability, ExactRef decoderSource, Optional<SuccessionUiOriginProof> successionUiProof,
            Optional<CoaSourceOriginProof> coaSourceProof,Optional<OperatorSourceOriginProof> operatorSourceProof) {
        public ActionBinding {
            Objects.requireNonNull(effect); Objects.requireNonNull(guardMode);
            StrictJson.require(guardMode!=ReadContract.GuardMode.STATUS_ONLY,"physical Status mode cannot register an action"); Objects.requireNonNull(requiredCapability);
            requiredCapability.ifPresent(StrictJson::text); requireSource(decoderSource);
            NativeStepDiscriminator.requireRegistration(effect.operation(), Kind.ACTION, requiredCapability);
            successionUiProof = Objects.requireNonNull(successionUiProof);
            coaSourceProof = Objects.requireNonNull(coaSourceProof);
            operatorSourceProof=Objects.requireNonNull(operatorSourceProof);
            StrictJson.require((successionUiProof.isPresent()?1:0)+(coaSourceProof.isPresent()?1:0)+(operatorSourceProof.isPresent()?1:0)<=1,
                    "two source-owned origin profiles cannot share a binding");
            if (successionUiProof.isPresent()) {
                var actual = successionUiProof.orElseThrow();
                StrictJson.require(effect.operation().value().equals("continue-death-succession-modal-v1")
                        && guardMode == ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION && requiredCapability.isEmpty()
                        && effect.preparation() == actual && effect.producerSource().equals(actual.successionUiDefinitionSource()),
                        "only the same source-owned CLOSE producer may install the finite terminal/succession-UI origin pair");
                requireSource(actual.successionUiDefinitionSource());
            }
            if (coaSourceProof.isPresent()) {
                var actual=coaSourceProof.orElseThrow();
                StrictJson.require(Set.of("probe-coat-of-arms-source-v1","export-coat-of-arms-source-v1").contains(effect.operation().value())
                        && guardMode==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        && requiredCapability.equals(Optional.of("game.command."+effect.operation().value()))
                        && effect.preparation()==actual && effect.producerSource().equals(actual.coaSourceDefinitionSource()),
                        "only the same original CoA source producer may install its finite Menu/gameplay origin pair");
                requireSource(actual.coaSourceDefinitionSource());
            }
            if(operatorSourceProof.isPresent()) {
                var actual=operatorSourceProof.orElseThrow();requireOperatorStep(effect.operation());
                StrictJson.require(guardMode==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        &&requiredCapability.equals(Optional.of(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.CAPABILITY))
                        &&effect.preparation()==actual&&effect.producerSource().equals(actual.operatorDefinitionSource()),
                        "only the same actual operator preparation source can qualify its finite gameplay/terminal pair");
                requireSource(actual.operatorDefinitionSource());
            }
        }
        public ActionBinding(NativeEffectRegistry.Binding effect,ReadContract.GuardMode mode,Optional<String> capability,
                ExactRef decoderSource,Optional<SuccessionUiOriginProof> successionUiProof,Optional<CoaSourceOriginProof> coaSourceProof) {
            this(effect,mode,capability,decoderSource,successionUiProof,coaSourceProof,Optional.empty());
        }
        public ActionBinding(NativeEffectRegistry.Binding effect, ReadContract.GuardMode mode,
                Optional<String> capability, ExactRef decoderSource) { this(effect, mode, capability, decoderSource, Optional.empty(),Optional.empty()); }
        public ActionBinding(NativeEffectRegistry.Binding effect,ReadContract.GuardMode mode,Optional<String> capability,
                ExactRef decoderSource,Optional<SuccessionUiOriginProof> successionUiProof) {
            this(effect,mode,capability,decoderSource,successionUiProof,Optional.empty());
        }
        public static ActionBinding coaSource(NativeEffectRegistry.Binding effect,ExactRef decoderSource,CoaSourceOriginProof sameProducer) {
            return new ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of("game.command."+effect.operation().value()),decoderSource,Optional.empty(),Optional.of(sameProducer));
        }
        public static ActionBinding operatorSource(NativeEffectRegistry.Binding effect,ExactRef decoderSource,OperatorSourceOriginProof sameProducer) {
            return new ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.CAPABILITY),decoderSource,Optional.empty(),Optional.empty(),Optional.of(sameProducer));
        }
        public Set<ReadContract.GuardMode> originModes() {
            if(operatorSourceProof.isPresent())return Set.of(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION);
            if(coaSourceProof.isPresent())return Set.of(ReadContract.GuardMode.FRONTEND_SESSION,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
            return successionUiProof.isPresent() ? Set.of(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP) : Set.of(guardMode);
        }
    }
    public record CompositeBinding(CompositeActionPort handler, ReadContract.GuardMode guardMode,
            Optional<String> requiredCapability, ExactRef implementationSource, ExactRef decoderSource) {
        public CompositeBinding {
            Objects.requireNonNull(handler); StrictJson.text(handler.handlerId()); Objects.requireNonNull(guardMode);
            StrictJson.require(guardMode!=ReadContract.GuardMode.STATUS_ONLY,"physical Status mode cannot register a composite");
            Objects.requireNonNull(requiredCapability); requiredCapability.ifPresent(StrictJson::text);
            requireSource(implementationSource); requireSource(decoderSource);
        }
    }
    public record IssuedAction(ActionBinding action, NativeRecordedEvidenceVerifier.Binding archived) {
        public IssuedAction {
            Objects.requireNonNull(action); Objects.requireNonNull(archived);
            StrictJson.require(action.effect().operation().equals(archived.operation()), "action and archive replay operation differ");
        }
    }
    @FunctionalInterface public interface OperationDecoder<A> {
        /** Pure strict operation grammar only. Decoding grants neither a current frame nor dispatch permission. */
        Optional<A> decode(OperationKey operation);
    }
    private interface FamilyChoice {
        Family<?> owner();
        IssuedAction issue();
    }
    /** Only this installed family can issue its fixed source, origin and archive replay pair. */
    public static final class Family<A> {
        private final String id;
        private final Class<A> argumentType;
        private final ReadContract.GuardMode mode;
        private final Optional<String> capability;
        private final ExactRef preparationSource;
        private final ExactRef decoderSource;
        private final ExactRef verifierSource;
        private final Function<A, RawJson> encode;
        private final Function<A, OperationKey> operation;
        private final Function<A, IssuedAction> factory;
        private final Optional<OperationDecoder<A>> operationDecoder;
        private final Map<RawJson, IssuedAction> issued = new HashMap<>();
        public Family(String id, Class<A> argumentType, ReadContract.GuardMode mode, Optional<String> capability,
                ExactRef preparationSource, ExactRef decoderSource, ExactRef verifierSource,
                Function<A, RawJson> encode, Function<A, OperationKey> operation, Function<A, IssuedAction> factory) {
            this(id, argumentType, mode, capability, preparationSource, decoderSource, verifierSource, encode, operation, factory, Optional.empty());
        }
        public Family(String id, Class<A> argumentType, ReadContract.GuardMode mode, Optional<String> capability,
                ExactRef preparationSource, ExactRef decoderSource, ExactRef verifierSource,
                Function<A, RawJson> encode, Function<A, OperationKey> operation, Function<A, IssuedAction> factory,
                OperationDecoder<A> actualOperationDecoder) {
            this(id, argumentType, mode, capability, preparationSource, decoderSource, verifierSource, encode, operation, factory,
                    Optional.of(Objects.requireNonNull(actualOperationDecoder)));
        }
        private Family(String id, Class<A> argumentType, ReadContract.GuardMode mode, Optional<String> capability,
                ExactRef preparationSource, ExactRef decoderSource, ExactRef verifierSource,
                Function<A, RawJson> encode, Function<A, OperationKey> operation, Function<A, IssuedAction> factory,
                Optional<OperationDecoder<A>> operationDecoder) {
            this.id = StrictJson.text(id); this.argumentType = Objects.requireNonNull(argumentType);
            this.mode = Objects.requireNonNull(mode);
            StrictJson.require(mode!=ReadContract.GuardMode.STATUS_ONLY,"physical Status mode cannot register an action family");
            this.capability = Objects.requireNonNull(capability);
            capability.ifPresent(StrictJson::text); requireSource(preparationSource); requireSource(decoderSource); requireSource(verifierSource);
            this.preparationSource = preparationSource; this.decoderSource = decoderSource; this.verifierSource = verifierSource;
            this.encode = Objects.requireNonNull(encode); this.operation = Objects.requireNonNull(operation); this.factory = Objects.requireNonNull(factory);
            this.operationDecoder = Objects.requireNonNull(operationDecoder);
        }
        public String id() { return id; }
        public ExactRef implementationSource() { return preparationSource; }
        public ExactRef decoderSource() { return decoderSource; }
        public ExactRef verifierSource() { return verifierSource; }
        public Optional<String> requiredCapability() { return capability; }
        public ReadContract.GuardMode guardMode() { return mode; }
        private Optional<FamilyChoice> decode(OperationKey expected) {
            if (operationDecoder.isEmpty()) return Optional.empty();
            Optional<A> decoded = Objects.requireNonNull(operationDecoder.orElseThrow().decode(expected));
            if (decoded.isEmpty()) return Optional.empty();
            A argument = decoded.orElseThrow();
            StrictJson.require(argumentType.isInstance(argument) && expected.equals(operation.apply(argument)),
                    "installed operation decoder changed the exact typed family operation");
            return Optional.of(new FamilyChoice() {
                @Override public Family<?> owner() { return Family.this; }
                @Override public IssuedAction issue() { return Family.this.issue(argument); }
            });
        }
        private synchronized IssuedAction issue(A arguments) {
            StrictJson.require(argumentType.isInstance(arguments), "dynamic action argument runtime type differs");
            A exact = argumentType.cast(arguments); RawJson key = Objects.requireNonNull(encode.apply(exact));
            StrictJson.require(key.bytes().length <= 65536, "bounded dynamic action arguments required");
            OperationKey expected = Objects.requireNonNull(operation.apply(exact));
            IssuedAction retained = issued.get(key);
            if (retained != null) {
                StrictJson.require(retained.action().effect().operation().equals(expected), "same dynamic arguments changed operation");
                return retained;
            }
            StrictJson.require(issued.size() < 4096, "dynamic action family limit reached");
            IssuedAction actual = Objects.requireNonNull(factory.apply(exact)); ActionBinding binding = actual.action();
            StrictJson.require(binding.successionUiProof().isEmpty() && binding.coaSourceProof().isEmpty() && binding.effect().operation().equals(expected) && binding.effect().producerSource().equals(preparationSource)
                    && binding.decoderSource().equals(decoderSource) && binding.guardMode() == mode
                    && binding.requiredCapability().equals(capability) && actual.archived().definitionSource().equals(verifierSource),
                    "dynamic action factory changed its fixed operation/source/origin/capability/replay");
            issued.put(key, actual); return actual;
        }
    }
    private interface CompositeChoice {
        CompositeFamily<?> owner();
        CompositeBinding issue();
    }
    /** A dynamic composite retains its actual installed handler and only issues the exact archived replay binding. */
    public static final class CompositeFamily<A> {
        private record Issued(OperationKey operation, NativeRecordedEvidenceVerifier.Binding archived) { }
        private final String id;
        private final Class<A> argumentType;
        private final CompositeBinding binding;
        private final ExactRef verifierSource;
        private final Function<A, RawJson> encode;
        private final Function<A, OperationKey> operation;
        private final Function<A, NativeRecordedEvidenceVerifier.Binding> factory;
        private final Optional<OperationDecoder<A>> operationDecoder;
        private final Map<RawJson, Issued> issued = new HashMap<>();
        public CompositeFamily(String id, Class<A> argumentType, CompositeBinding exactInstalledHandler, ExactRef verifierSource,
                Function<A, RawJson> encode, Function<A, OperationKey> operation,
                Function<A, NativeRecordedEvidenceVerifier.Binding> archivedFactory) {
            this(id,argumentType,exactInstalledHandler,verifierSource,encode,operation,archivedFactory,Optional.empty());
        }
        public CompositeFamily(String id,Class<A> argumentType,CompositeBinding exactInstalledHandler,ExactRef verifierSource,
                Function<A,RawJson> encode,Function<A,OperationKey> operation,
                Function<A,NativeRecordedEvidenceVerifier.Binding> archivedFactory,OperationDecoder<A> actualOperationDecoder) {
            this(id,argumentType,exactInstalledHandler,verifierSource,encode,operation,archivedFactory,
                    Optional.of(Objects.requireNonNull(actualOperationDecoder)));
        }
        private CompositeFamily(String id,Class<A> argumentType,CompositeBinding exactInstalledHandler,ExactRef verifierSource,
                Function<A,RawJson> encode,Function<A,OperationKey> operation,
                Function<A,NativeRecordedEvidenceVerifier.Binding> archivedFactory,Optional<OperationDecoder<A>> operationDecoder) {
            this.id = StrictJson.text(id); this.argumentType = Objects.requireNonNull(argumentType);
            binding = Objects.requireNonNull(exactInstalledHandler); requireSource(verifierSource); this.verifierSource = verifierSource;
            this.encode = Objects.requireNonNull(encode); this.operation = Objects.requireNonNull(operation); factory = Objects.requireNonNull(archivedFactory);
            this.operationDecoder=Objects.requireNonNull(operationDecoder);
        }
        public String id() { return id; }
        public CompositeBinding binding() { return binding; }
        public ExactRef verifierSource() { return verifierSource; }
        private Optional<CompositeChoice> decode(OperationKey expected,RootExecutableBindings sameInstalled) {
            if(operationDecoder.isEmpty())return Optional.empty();
            Optional<A> decoded=Objects.requireNonNull(operationDecoder.orElseThrow().decode(expected));
            if(decoded.isEmpty())return Optional.empty();
            A argument=decoded.orElseThrow();
            StrictJson.require(argumentType.isInstance(argument)&&expected.equals(operation.apply(argument))
                    &&binding.handler().supports(expected),"installed composite operation decoder changed its typed operation/handler");
            return Optional.of(new CompositeChoice(){
                @Override public CompositeFamily<?> owner(){return CompositeFamily.this;}
                @Override public CompositeBinding issue(){return sameInstalled.issueComposite(CompositeFamily.this,argument);}
            });
        }
        private synchronized Issued issue(A arguments) {
            StrictJson.require(argumentType.isInstance(arguments), "dynamic composite argument runtime type differs");
            A actual = argumentType.cast(arguments); RawJson key = Objects.requireNonNull(encode.apply(actual));
            StrictJson.require(key.bytes().length <= 65536, "bounded dynamic composite arguments required");
            OperationKey expected = Objects.requireNonNull(operation.apply(actual));
            StrictJson.require(binding.handler().supports(expected), "dynamic composite operation is unsupported by its exact installed handler");
            Issued retained = issued.get(key);
            if (retained != null) { StrictJson.require(retained.operation().equals(expected), "same composite arguments changed operation"); return retained; }
            StrictJson.require(issued.size() < 4096, "dynamic composite family limit reached");
            NativeRecordedEvidenceVerifier.Binding replay = Objects.requireNonNull(factory.apply(actual));
            StrictJson.require(replay.operation().equals(expected) && replay.definitionSource().equals(verifierSource),
                    "dynamic composite archive factory changed operation or verifier source");
            Issued result = new Issued(expected, replay); issued.put(key, result); return result;
        }
    }

    private final Map<OperationKey, ActionBinding> actions = new HashMap<>();
    private final Map<OperationKey, NativeRecordedEvidenceVerifier.Binding> archived = new HashMap<>();
    private final List<Family<?>> families;
    private final List<CompositeFamily<?>> compositeFamilies;
    private final RootReadContractCatalog reads;
    private final NativeEffectRegistry effects;
    private final List<CompositeBinding> compositeBindings;
    private final CompositeRegistry composites;

    private RootExecutableBindings(List<ActionBinding> actions, RootReadContractCatalog reads,
            List<CompositeBinding> composites, List<NativeRecordedEvidenceVerifier.Binding> archived,
            List<Family<?>> families, List<CompositeFamily<?>> compositeFamilies, int retainedEffects) {
        this.reads = Objects.requireNonNull(reads); this.compositeBindings = List.copyOf(composites); this.families = List.copyOf(families);
        this.compositeFamilies = List.copyOf(compositeFamilies);
        StrictJson.require(actions.size() <= 4096 && composites.size() <= 128 && archived.size() <= 4096 && families.size() <= 256 && compositeFamilies.size() <= 128,
                "bounded actual Root inventory required");
        this.composites = new CompositeRegistry(this.compositeBindings.stream().map(CompositeBinding::handler).toList());
        Set<String> ids = new HashSet<>();
        for (Family<?> family : this.families) StrictJson.require(ids.add(family.id()), "duplicate installed action family");
        for (CompositeFamily<?> family : this.compositeFamilies) {
            StrictJson.require(ids.add(family.id()) && this.compositeBindings.stream().anyMatch(binding -> binding == family.binding()),
                    "duplicate composite family id or uninstalled actual handler binding");
        }
        for (ActionBinding binding : List.copyOf(actions)) retain(binding);
        for (NativeRecordedEvidenceVerifier.Binding verifier : List.copyOf(archived)) retainArchived(verifier);
        // A live catalog is mandatory. Copying the initial list would strand all subsequently issued families.
        effects = new NativeEffectRegistry(this, retainedEffects);
    }
    public static RootExecutableBindings freeze(List<ActionBinding> actions, RootReadContractCatalog reads,
            List<CompositeBinding> composites, int retainedEffects) {
        return new RootExecutableBindings(actions, reads, composites, List.of(), List.of(), List.of(), retainedEffects);
    }
    public static RootExecutableBindings freeze(List<ActionBinding> actions, RootReadContractCatalog reads,
            List<CompositeBinding> composites, List<NativeRecordedEvidenceVerifier.Binding> archived,
            List<Family<?>> families, int retainedEffects) {
        return new RootExecutableBindings(actions, reads, composites, archived, families, List.of(), retainedEffects);
    }
    public static RootExecutableBindings freeze(List<ActionBinding> actions, RootReadContractCatalog reads,
            List<CompositeBinding> composites, List<NativeRecordedEvidenceVerifier.Binding> archived,
            List<Family<?>> families, List<CompositeFamily<?>> compositeFamilies, int retainedEffects) {
        return new RootExecutableBindings(actions, reads, composites, archived, families, compositeFamilies, retainedEffects);
    }
    public synchronized <A> ActionBinding issue(Family<A> family, A arguments) {
        StrictJson.require(families.stream().anyMatch(installed -> installed == family), "uninstalled dynamic action family object");
        return retainIssued(family.issue(arguments));
    }
    private ActionBinding retainIssued(IssuedAction actual) {
        ActionBinding old = actions.get(actual.action().effect().operation());
        if (old != null) {
            StrictJson.require(old == actual.action() && archived.get(actual.archived().operation()) == actual.archived(),
                    "distinct action factories claim one exact operation"); return old;
        }
        StrictJson.require(actions.size() < 4096, "Root action inventory is full");
        StrictJson.require(archived.size() < 4096 && !archived.containsKey(actual.archived().operation()), "Root replay inventory conflicts or is full");
        retain(actual.action()); retainArchived(actual.archived()); return actual.action();
    }
    public synchronized Optional<NativeEffectRegistry.Binding> actualActionBinding(OperationKey operation) {
        issueFromOperation(Objects.requireNonNull(operation));
        return Optional.ofNullable(actions.get(Objects.requireNonNull(operation))).map(ActionBinding::effect);
    }
    private void issueFromOperation(OperationKey operation) {
        if (actions.containsKey(operation)) return;
        List<FamilyChoice> choices = families.stream().flatMap(family -> family.decode(operation).stream()).toList();
        List<CompositeChoice> compositeChoices=compositeFamilies.stream().flatMap(family->family.decode(operation,this).stream()).toList();
        StrictJson.require(choices.size()+compositeChoices.size()<=1,"multiple actual typed action/composite families decode the same operation");
        if(!compositeChoices.isEmpty()){
            CompositeChoice choice=compositeChoices.getFirst();
            StrictJson.require(compositeFamilies.stream().anyMatch(family->family==choice.owner()),
                    "composite decoder escaped its actual installed family");
            choice.issue();return;
        }
        if (choices.isEmpty()) return;
        FamilyChoice choice = choices.getFirst();
        StrictJson.require(families.stream().anyMatch(family -> family == choice.owner()), "operation decoder escaped its actual installed family");
        IssuedAction actual = choice.issue();
        StrictJson.require(actual.action().effect().operation().equals(operation), "operation-decoded family issued another action");
        retainIssued(actual);
    }
    public synchronized <A> CompositeBinding issueComposite(CompositeFamily<A> family, A arguments) {
        StrictJson.require(compositeFamilies.stream().anyMatch(installed -> installed == family), "uninstalled dynamic composite family object");
        CompositeFamily.Issued actual = family.issue(arguments);
        StrictJson.require(!actions.containsKey(actual.operation()) && reads.contracts().stream().noneMatch(read -> read.operation().equals(actual.operation()))
                && composites.find(actual.operation()).orElseThrow() == family.binding().handler(), "dynamic composite conflicts with another actual route");
        NativeRecordedEvidenceVerifier.Binding old = archived.get(actual.operation());
        if (old != null) StrictJson.require(old == actual.archived(), "distinct replay factories claim one exact composite operation");
        else retainArchived(actual.archived());
        return family.binding();
    }
    /** Only a family which actually issued this identical retained binding can describe its origin. */
    public synchronized Optional<Family<?>> actualFamily(OperationKey operation) {
        ActionBinding selected = actions.get(Objects.requireNonNull(operation));
        if (selected == null) return Optional.empty();
        Family<?> result = null;
        for (Family<?> family : families) {
            synchronized (family) {
                if (family.issued.values().stream().noneMatch(issued -> issued.action() == selected)) continue;
                StrictJson.require(result == null || result == family, "actual action has conflicting installed issuing families");
                result = family;
            }
        }
        return Optional.ofNullable(result);
    }
    public synchronized Optional<NativeRecordedEvidenceVerifier.Binding> actualArchivedVerifier(OperationKey operation) {
        return Optional.ofNullable(archived.get(Objects.requireNonNull(operation)));
    }
    public List<Family<?>> families() { return families; }
    public List<CompositeFamily<?>> compositeFamilies() { return compositeFamilies; }
    public synchronized Optional<CompositeFamily<?>> actualCompositeFamily(OperationKey operation) {
        NativeRecordedEvidenceVerifier.Binding replay = archived.get(Objects.requireNonNull(operation));
        if (replay == null) return Optional.empty();
        CompositeFamily<?> selected = null;
        for (CompositeFamily<?> family : compositeFamilies) synchronized (family) {
            if (family.issued.values().stream().noneMatch(issued -> issued.operation().equals(operation) && issued.archived() == replay)) continue;
            StrictJson.require(selected == null || selected == family, "actual composite has conflicting issuing families"); selected = family;
        }
        return Optional.ofNullable(selected);
    }
    public synchronized List<ActionBinding> actionBindings() {
        return actions.values().stream().sorted(java.util.Comparator.comparing(binding -> binding.effect().operation().value())).toList();
    }
    public synchronized List<NativeRecordedEvidenceVerifier.Binding> archivedBindings() {
        return archived.values().stream().sorted(java.util.Comparator.comparing(binding -> binding.operation().value())).toList();
    }
    private void retain(ActionBinding binding) {
        OperationKey operation = binding.effect().operation();
        requireNoReadOrComposite(operation);
        ActionBinding previous = actions.putIfAbsent(operation, binding);
        if (previous != null) {
            String message = "duplicate actual action binding; operation=" + operation.value() + ", firstPreparation=" + previous.effect().preparation().getClass().getName() + ", firstObserver=" + previous.effect().observer().getClass().getName() + ", newPreparation=" + binding.effect().preparation().getClass().getName() + ", newObserver=" + binding.effect().observer().getClass().getName();
            StrictJson.require(false, message);
        }
    }
    private void retainArchived(NativeRecordedEvidenceVerifier.Binding verifier) {
        StrictJson.require(archived.size() < 4096, "Root archived verifier inventory is full");
        StrictJson.require(actions.containsKey(verifier.operation()) || composites.find(verifier.operation()).isPresent(),
                "archive verifier has no actual executable binding");
        StrictJson.require(archived.putIfAbsent(verifier.operation(), verifier) == null, "duplicate archive verifier binding");
    }
    private void requireNoReadOrComposite(OperationKey operation) {
        StrictJson.require(reads.contracts().stream().noneMatch(read -> read.operation().equals(operation))
                && composites.find(operation).isEmpty(), "native operation is claimed by action/read/composite twice");
    }
    @Override public boolean frozen() { return true; }
    @Override public synchronized List<InstalledStep> installed() {
        List<InstalledStep> all = new ArrayList<>();
        for (ActionBinding binding : actionBindings()) for (ReadContract.GuardMode mode : binding.originModes())
            all.add(new InstalledStep(binding.effect().operation(), Kind.ACTION,
                    mode, binding.requiredCapability(), binding.effect().producerSource(), binding.decoderSource()));
        
        record ReadRoute(OperationKey operation, ReadContract.GuardMode mode) { }
        java.util.LinkedHashMap<ReadRoute, List<RootReadContractCatalog.InstalledRead>> readGroups = new java.util.LinkedHashMap<>();
        for (RootReadContractCatalog.InstalledRead binding : reads.installed()) {
            ReadContract<?> read = binding.contract();
            StrictJson.require(!actions.containsKey(read.operation()) && compositeBindings.stream().noneMatch(composite -> composite.guardMode() == read.guardMode() && composite.handler().supports(read.operation())), "dynamic read conflicts with actual action/composite");
            
            ReadRoute route = new ReadRoute(read.operation(), read.guardMode());
            readGroups.computeIfAbsent(route, k -> new ArrayList<>()).add(binding);
        }
        
        List<String> conflictDiagnostics = new ArrayList<>();
        for (var entry : readGroups.entrySet()) {
            var route = entry.getKey();
            var bindings = entry.getValue();
            if (bindings.size() > 1) {
                var firstCap = bindings.getFirst().contract().requiredCapability();
                boolean hasConflict = bindings.stream().anyMatch(b -> !b.contract().requiredCapability().equals(firstCap));
                if (hasConflict) {
                    StringBuilder sb = new StringBuilder("READ conflict for operation=").append(route.operation().value()).append(", guardMode=").append(route.mode().name()).append(", contracts=[");
                    for (var b : bindings) {
                        var r = b.contract();
                        sb.append("{id=").append(r.contractId()).append(",cap=").append(r.requiredCapability()).append(",wire=").append(r.wireProfile()).append(",permMode=").append(r.permissionMode()).append(",permKey=").append(r.permissionKey()).append("},");
                    }
                    sb.append("]");
                    conflictDiagnostics.add(sb.toString());
                } else {
                    // Coalesce: same semantic route (op, mode, cap), keep first representative
                    var read = bindings.getFirst().contract();
                    all.add(new InstalledStep(read.operation(), Kind.READ, read.guardMode(), read.requiredCapability(), read.sourceRef(), bindings.getFirst().decoderSource()));
                }
            } else {
                var read = bindings.getFirst().contract();
                all.add(new InstalledStep(read.operation(), Kind.READ, read.guardMode(), read.requiredCapability(), read.sourceRef(), bindings.getFirst().decoderSource()));
            }
        }
        
        StrictJson.require(conflictDiagnostics.isEmpty(), String.join("; ", conflictDiagnostics));
        
        return all.stream().sorted(java.util.Comparator.comparing((InstalledStep step) -> step.operation().value())
                .thenComparing(step -> step.kind().name()).thenComparing(step -> step.guardMode().name())).toList();
    }
    public List<ReadContract<?>> readContracts() { return reads.contracts(); }
    public RootReadContractCatalog readCatalog() { return reads; }
    public NativeEffectRegistry effects() { return effects; }
    public CompositeRegistry composites() { return composites; }
    public List<CompositeBinding> compositeBindings() { return compositeBindings; }
    @Override public synchronized Optional<PublicPlanningStep> describeForPublicPlanning(OperationKey operation) {
        Objects.requireNonNull(operation);
        // Decoders are the installed strict pure grammars. Their factories and issue callbacks are never invoked here.
        var actionChoices = families.stream().flatMap(family -> family.decode(operation).stream()).toList();
        var compositeChoices = compositeFamilies.stream().flatMap(family -> family.decode(operation, this).stream()).toList();
        StrictJson.require(actionChoices.size() + compositeChoices.size() <= 1,
                "multiple installed families describe one public planning operation");
        var directReads = installed().stream().filter(s -> s.kind() == Kind.READ && s.operation().equals(operation)).toList();
        var directComposites = compositeBindings.stream().filter(binding -> binding.handler().supports(operation)).toList();
        ActionBinding directAction = actions.get(operation);
        StrictJson.require(directReads.size() <= 1 && directComposites.size() <= 1
                && (directAction == null || directReads.isEmpty() && directComposites.isEmpty())
                && (directReads.isEmpty() || directComposites.isEmpty()),
                "ambiguous installed public planning operation or origin metadata");
        if (directAction != null) {
            StrictJson.require(compositeChoices.isEmpty() && (actionChoices.isEmpty()
                    || actualFamily(operation).filter(owner -> owner == actionChoices.getFirst().owner()).isPresent()),
                    "public planning decoder conflicts with the actual retained action producer");
            var verifier = archived.get(operation);
            if (verifier == null) return Optional.empty();
            if (!actionChoices.isEmpty()) StrictJson.require(verifier.definitionSource().equals(actionChoices.getFirst().owner().verifierSource()),
                    "retained action verifier differs from its installed family metadata");
            return Optional.of(new PublicPlanningStep(new InstalledStep(operation, Kind.ACTION, directAction.guardMode(),
                    directAction.requiredCapability(), directAction.effect().producerSource(), directAction.decoderSource()),
                    Optional.of(verifier.definitionSource())));
        }
        if (!directReads.isEmpty()) {
            StrictJson.require(actionChoices.isEmpty() && compositeChoices.isEmpty(),
                    "public planning read conflicts with an installed action/composite grammar");
            return Optional.of(new PublicPlanningStep(directReads.getFirst(), Optional.empty()));
        }
        if (!directComposites.isEmpty()) {
            StrictJson.require(actionChoices.isEmpty(), "public planning composite conflicts with an installed action grammar");
            var binding = directComposites.getFirst();
            StrictJson.require(composites.find(operation).orElseThrow() == binding.handler(),
                    "public planning composite is not the identical installed handler");
            var retained = archived.get(operation);
            Optional<ExactRef> verifier = retained == null ? Optional.empty() : Optional.of(retained.definitionSource());
            if (!compositeChoices.isEmpty()) {
                var family = compositeChoices.getFirst().owner();
                StrictJson.require(family.binding() == binding, "public planning composite decoder escaped its installed handler");
                if (verifier.isPresent()) StrictJson.require(verifier.orElseThrow().equals(family.verifierSource()),
                        "retained composite verifier differs from its installed family metadata");
                verifier = Optional.of(family.verifierSource());
            }
            if (verifier.isEmpty()) return Optional.empty();
            return Optional.of(new PublicPlanningStep(new InstalledStep(operation, Kind.COMPOSITE, binding.guardMode(),
                    binding.requiredCapability(), binding.implementationSource(), binding.decoderSource()), verifier));
        }
        StrictJson.require(compositeChoices.isEmpty(), "public planning composite grammar has no actual installed handler");
        if (actionChoices.isEmpty()) return Optional.empty();
        var family = actionChoices.getFirst().owner();
        return Optional.of(new PublicPlanningStep(new InstalledStep(operation, Kind.ACTION, family.guardMode(),
                family.requiredCapability(), family.implementationSource(), family.decoderSource()), Optional.of(family.verifierSource())));
    }
    @Override public synchronized Optional<InstalledStep> resolve(OperationKey operation) {
        Objects.requireNonNull(operation);
        issueFromOperation(operation);
        var directMatches = installed().stream().filter(step -> step.operation().equals(operation)).distinct().toList();
        StrictJson.require(directMatches.size() <= 1, "operation-only lookup is ambiguous; actual origin is required");
        Optional<InstalledStep> direct = directMatches.stream().findFirst();
        List<CompositeBinding> matches = compositeBindings.stream().filter(binding -> binding.handler().supports(operation)).toList();
        StrictJson.require(matches.size() <= 1 && (matches.isEmpty() || direct.isEmpty()), "ambiguous actual Root operation");
        if (direct.isPresent() || matches.isEmpty()) return direct;
        if (!archived.containsKey(operation)) return Optional.empty();
        CompositeBinding binding = matches.getFirst();
        StrictJson.require(composites.find(operation).orElseThrow() == binding.handler(), "actual composite handler identity differs");
        return Optional.of(new InstalledStep(operation, Kind.COMPOSITE, binding.guardMode(), binding.requiredCapability(), binding.implementationSource(), binding.decoderSource()));
    }
    @Override public synchronized Optional<InstalledStep> resolve(OperationKey operation, CommandOrigin actual) {
        return resolve(operation, ExecutableStepBindings.originMode(Objects.requireNonNull(actual)));
    }
    @Override public synchronized Optional<InstalledStep> resolve(OperationKey operation, ReadContract.GuardMode actualMode) {
        Objects.requireNonNull(operation); Objects.requireNonNull(actualMode); issueFromOperation(operation);
        var direct = installed().stream().filter(step -> step.operation().equals(operation) && step.guardMode() == actualMode).distinct().toList();
        var compositesForOperation = compositeBindings.stream().filter(binding -> binding.handler().supports(operation) && binding.guardMode() == actualMode).toList();
        StrictJson.require(direct.size() <= 1 && compositesForOperation.size() <= 1
                && (compositesForOperation.isEmpty() || direct.isEmpty()), "ambiguous actual Root operation/origin: operation=" + operation.value() + ", actualMode=" + actualMode.name() + ", direct=" + direct.stream().map(s -> s.operation().value() + "/" + s.kind().name() + "/" + s.guardMode().name()).collect(java.util.stream.Collectors.joining(",")) + " composite=" + compositesForOperation.stream().map(c -> c.handler().handlerId() + "/" + c.guardMode().name()).collect(java.util.stream.Collectors.joining(",")));
        if (!direct.isEmpty()) return Optional.of(direct.getFirst());
        if (compositesForOperation.isEmpty() || !archived.containsKey(operation)) return Optional.empty();
        var binding = compositesForOperation.getFirst();
        StrictJson.require(composites.find(operation).orElseThrow() == binding.handler(), "actual composite handler identity differs");
        return Optional.of(new InstalledStep(operation, Kind.COMPOSITE, binding.guardMode(), binding.requiredCapability(), binding.implementationSource(), binding.decoderSource()));
    }
    @Override public boolean supportsCapability(String capability) {
        StrictJson.text(capability);
        return ExecutableStepBindings.super.supportsCapability(capability)
                || compositeBindings.stream().anyMatch(binding -> binding.requiredCapability().filter(capability::equals).isPresent())
                || families.stream().anyMatch(family -> family.requiredCapability().filter(capability::equals).isPresent());
    }
    public synchronized void requireCompleteArchiveCoverage() {
        for (OperationKey operation : actions.keySet()) StrictJson.require(archived.containsKey(operation), "actual action lacks original-evidence verifier: " + operation.value());
    }
    @Override public NativeRequest prepare(ActionCommand command) { return prepareActual(command, Optional.empty()); }
    /** Delegation only: the same actual producer must qualify any explicit original protocol ID. */
    @Override public void requireProtocolIdentity(ActionCommand command) {
        Objects.requireNonNull(command);
        var descriptor = resolve(command.operation(), command.origin()).orElseThrow(() -> new IllegalArgumentException("protocol identity has no actual origin-bound action"));
        if (descriptor.kind() == Kind.COMPOSITE) {
            ActionPorts.PreparationPort.super.requireProtocolIdentity(command);
            return;
        }
        StrictJson.require(descriptor.kind() == Kind.ACTION, "protocol identity qualification requires the actual primitive producer");
        ActionBinding binding;
        synchronized (this) { binding = actions.get(command.operation()); }
        if (binding == null) throw new IllegalStateException("actual action producer unavailable");
        binding.effect().preparation().requireProtocolIdentity(command);
    }
    /** Read-only continuation delegates to the identical source, without replaying the old before preflight. */
    @Override public ActionPorts.PostconditionResult observeOperatorReconciliation(
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ActionReceipt actualCanonicalPending, java.time.Instant freshDeadline, ActionPorts.OperatorReconciliationWork observer)
            throws java.io.IOException, InterruptedException {
        Objects.requireNonNull(same); Objects.requireNonNull(actualCanonicalPending);
        Objects.requireNonNull(freshDeadline); Objects.requireNonNull(observer);
        ActionCommand command=actualCanonicalPending.command();
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,
                "only the original typed operator may use its source reconciliation");
        StrictJson.require(command.operation().value().equals(command.expectation().requireOperatorRebind().request().step()),
                "operator reconciliation changed its original native target");
        var descriptor=resolve(command.operation(),command.origin()).orElseThrow(
                ()->new IllegalArgumentException("operator reconciliation has no actual origin-bound action"));
        StrictJson.require(descriptor.kind()==Kind.ACTION,"operator reconciliation requires the actual primitive producer");
        final ActionBinding binding; synchronized(this){binding=actions.get(command.operation());}
        if(binding==null||binding.operatorSourceProof().isEmpty())
            throw new java.io.IOException("actual source-owned operator reconciliation is unavailable");
        var actual=binding.operatorSourceProof().orElseThrow(); var source=binding.effect().producerSource();
        StrictJson.require(binding.effect().preparation()==actual&&source.equals(actual.operatorDefinitionSource()),
                "operator reconciliation source/preparation changed");
        ActionPorts.PostconditionResult result=actual.observeOperatorReconciliation(same,actualCanonicalPending,freshDeadline,observer);
        StrictJson.require(source.equals(actual.operatorDefinitionSource()),"operator reconciliation source changed after observation");
        return Objects.requireNonNull(result,"actual operator reconciliation returned no result");
    }
    @Override public NativeRequest prepare(ActionCommand command, String requestId) { StrictJson.text(requestId); return prepareActual(command, Optional.of(requestId)); }
    @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            ActionCommand command, String requestId) {
        Objects.requireNonNull(borrowed); StrictJson.text(requestId); ActionBinding binding;
        synchronized (this) { binding = actions.get(command.operation()); }
        if (binding == null) throw new UnsupportedOperationException("No installed actual primitive: " + command.operation().value());
        requirePreparationOrigin(binding, command, Optional.of(borrowed));
        NativeRequest prepared = effects.prepare(borrowed, command, requestId);
        NativeStepDiscriminator.requireRequest(command.operation(), Kind.ACTION, prepared);
        StrictJson.require(prepared.requiredCapability().equals(binding.requiredCapability()),
                "same-session preparation changed installed operation/capability"); return prepared;
    }
    private NativeRequest prepareActual(ActionCommand command, Optional<String> requestId) {
        Objects.requireNonNull(command); ActionBinding binding;
        synchronized (this) { binding = actions.get(command.operation()); }
        if (binding == null) throw new UnsupportedOperationException("No installed actual primitive: " + command.operation().value());
        requirePreparationOrigin(binding, command, Optional.empty());
        NativeRequest request = requestId.isPresent() ? effects.prepare(command, requestId.orElseThrow()) : effects.prepare(command);
        NativeStepDiscriminator.requireRequest(command.operation(), Kind.ACTION, request);
        StrictJson.require(request.requiredCapability().equals(binding.requiredCapability()),
                "actual preparation changed its installed operation/capability"); return request;
    }
    private static boolean originMatches(CommandOrigin origin, ReadContract.GuardMode mode) {
        return switch (mode) {
            case GAMEPLAY_PAUSED_MAP -> origin instanceof CommandOrigin.Gameplay;
            case FRONTEND_SESSION -> origin instanceof CommandOrigin.Frontend;
            case LIFECYCLE_TERMINAL_SESSION -> origin instanceof CommandOrigin.LifecycleTerminal;
            default -> false; // Newly introduced read-only origins never acquire primitive preparation authority.
        };
    }
    private static void requirePreparationOrigin(ActionBinding binding, ActionCommand command,
            Optional<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> borrowed) {
        StrictJson.require(!(command.origin() instanceof CommandOrigin.Reconciliation) && !(command.origin() instanceof CommandOrigin.PhysicalStatusOnly)
                && binding.originModes().contains(ExecutableStepBindings.originMode(command.origin())),
                "primitive origin differs from installed finite origin profile");
        if(binding.operatorSourceProof().isPresent()) {
            var same=borrowed.orElseThrow(()->new IllegalStateException("operator action requires its actual borrowed writer"));
            var actual=binding.operatorSourceProof().orElseThrow();var source=binding.effect().producerSource();
            StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,"operator preparation requires the exact typed operator expectation");
            var request=command.expectation().requireOperatorRebind().request();
            StrictJson.require(command.operation().value().equals(request.step()),"operator expectation changed its native target");
            try {
                StrictJson.require(source.equals(actual.operatorDefinitionSource()),"operator source changed before qualification");
                actual.requireOperatorOrigin(same,command);
                StrictJson.require(source.equals(actual.operatorDefinitionSource()),"operator source changed after qualification");
            } catch(java.io.IOException unavailable) {throw new java.io.UncheckedIOException("actual operator origin qualification unavailable",unavailable);}
            return;
        }
        if(binding.coaSourceProof().isPresent()) {
            var same=borrowed.orElseThrow(()->new IllegalStateException("source-owned CoA action requires its actual borrowed writer"));
            var actual=binding.coaSourceProof().orElseThrow();var source=binding.effect().producerSource();
            try {
                StrictJson.require(source.equals(actual.coaSourceDefinitionSource()),"CoA origin proof source changed");
                actual.requireCoaSourceOrigin(same,command);
                StrictJson.require(source.equals(actual.coaSourceDefinitionSource()),"CoA origin proof source changed after qualification");
            } catch(java.io.IOException unavailable) {throw new java.io.UncheckedIOException("actual original CoA source origin proof unavailable",unavailable);}
            return;
        }
        if (binding.successionUiProof().isEmpty()) return;
        var same = borrowed.orElseThrow(() -> new IllegalStateException("source-owned succession CLOSE requires its actual borrowed writer"));
        var actual = binding.successionUiProof().orElseThrow();
        try {
            var source = binding.effect().producerSource();
            StrictJson.require(source.equals(actual.successionUiDefinitionSource()), "succession origin proof source changed");
            actual.requireSuccessionOrigin(same, command);
            StrictJson.require(source.equals(actual.successionUiDefinitionSource()), "succession origin proof source changed after qualification");
        } catch (java.io.IOException unavailable) { throw new java.io.UncheckedIOException("actual succession origin proof unavailable", unavailable); }
    }
    private static void requireOperatorStep(OperationKey operation) {
        String prefix="set-played-character-v1-",value=operation.value();
        StrictJson.require(value.startsWith(prefix),"only original operator native steps use this finite profile");
        String suffix=value.substring(prefix.length());StrictJson.require(suffix.matches("[1-9][0-9]{0,9}"),"canonical positive int32 operator native target required");
        long target=Long.parseLong(suffix);StrictJson.require(target<=Integer.MAX_VALUE&&value.equals(prefix+target),"operator native target exceeds signed int32");
    }
    private static void requireSource(ExactRef source) { Objects.requireNonNull(source); StrictJson.require(source.bytes() > 0, "exact nonempty installed source required"); }
}

