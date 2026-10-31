package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.driver.HeldDriverObservationPort;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** One actual clock/primitive graph per physical Root; no transport, writer or synthetic observation is created. */
public final class RootAdvanceInfrastructureFactory {
    public static final String TIMINGS_SCHEMA="xar.java-root-advance-timings/v1";
    public static final int TIMINGS_MAX_BYTES=4096;
    private RootAdvanceInfrastructureFactory() { }

    public record Sources(ExactRef primitiveProducer,ExactRef primitiveDecoder,ExactRef primitiveVerifier,
            ExactRef statusDefinition,ExactRef statusDecoder,ExactRef unknownStatusDecoder) {
        public Sources {
            for(ExactRef ref:List.of(primitiveProducer,primitiveDecoder,primitiveVerifier,statusDefinition,statusDecoder,unknownStatusDecoder))
                require(ref.bytes()>0,"actual native clock producer/decoder/verifier/Status definition sources required");
        }
    }
    /** Real source-bound settings are parsed before installation; integer configuration never accepts booleans/floats. */
    public record Timings(ExactRef original,int maximumFrames,Duration commandTimeout,Duration advanceTimeout,boolean ordinary) {
        private static final int MAXIMUM_FRAMES=65536;
        private static final long MAXIMUM_COMMAND_MILLIS=300000;
        private static final long MAXIMUM_ADVANCE_MILLIS=3600000;
        private static final Set<String> FIELDS=Set.of("schema","maximum_frames","command_timeout_millis","advance_timeout_millis");
        public Timings {
            Objects.requireNonNull(original);
            require(original.bytes()>0 && (ordinary||original.bytes()<=TIMINGS_MAX_BYTES),"actual clock timing configuration metadata required");
            requireValues(maximumFrames,commandTimeout,advanceTimeout);
        }
        public Timings(ExactRef original,int maximumFrames,Duration commandTimeout,Duration advanceTimeout) {
            this(original,maximumFrames,commandTimeout,advanceTimeout,false);
        }
        public static Timings ordinary(ExactRef wholeConfigMetadata,int maximumFrames,
                Duration commandTimeout,Duration advanceTimeout) {
            return new Timings(wholeConfigMetadata,maximumFrames,commandTimeout,advanceTimeout,true);
        }
        private static void requireValues(int maximumFrames,Duration commandTimeout,Duration advanceTimeout) {
            Objects.requireNonNull(commandTimeout);Objects.requireNonNull(advanceTimeout);
            require(maximumFrames>=1 && maximumFrames<=MAXIMUM_FRAMES
                    && !commandTimeout.isNegative() && !commandTimeout.isZero()
                    && commandTimeout.compareTo(Duration.ofMillis(MAXIMUM_COMMAND_MILLIS))<=0
                    && !advanceTimeout.isNegative() && !advanceTimeout.isZero()
                    && advanceTimeout.compareTo(Duration.ofMillis(MAXIMUM_ADVANCE_MILLIS))<=0,
                    "finite real clock wait/command/advance limits required");
            require(commandTimeout.getNano()%1000000==0 && advanceTimeout.getNano()%1000000==0,
                    "clock timing durations must contain exact whole milliseconds");
        }
        /** Pure production configuration. The caller retains these actual bytes before binding their ExactRef. */
        public static RawJson encode(int maximumFrames,Duration commandTimeout,Duration advanceTimeout) {
            requireValues(maximumFrames,commandTimeout,advanceTimeout);
            ObjectNode row=StrictJson.object().put("schema",TIMINGS_SCHEMA).put("maximum_frames",maximumFrames)
                    .put("command_timeout_millis",commandTimeout.toMillis()).put("advance_timeout_millis",advanceTimeout.toMillis());
            StrictJson.object(row,FIELDS);
            byte[] bytes=StrictJson.canonical(row);
            require(bytes.length<=TIMINGS_MAX_BYTES,"clock timing configuration exceeds its byte limit");
            return new RawJson(bytes);
        }
        public static Timings decode(ExactRef original,RawJson actual) {
            Objects.requireNonNull(original);Objects.requireNonNull(actual);
            require(actual.bytes().length<=TIMINGS_MAX_BYTES && original.bytes()==actual.bytes().length && original.sha256().equals(ActionCodec.sha256(actual.bytes())),
                    "clock timing original bytes/SHA differ");
            ObjectNode row=StrictJson.object(StrictJson.parse(actual.bytes()),FIELDS);
            require(TIMINGS_SCHEMA.equals(StrictJson.text(row.get("schema"))),"clock timing schema differs");
            int frames=StrictJson.integer(row.get("maximum_frames"),BigInteger.ONE,BigInteger.valueOf(MAXIMUM_FRAMES)).intValueExact();
            long command=StrictJson.integer(row.get("command_timeout_millis"),BigInteger.ONE,BigInteger.valueOf(MAXIMUM_COMMAND_MILLIS)).longValueExact();
            long advance=StrictJson.integer(row.get("advance_timeout_millis"),BigInteger.ONE,BigInteger.valueOf(MAXIMUM_ADVANCE_MILLIS)).longValueExact();
            return new Timings(original,frames,Duration.ofMillis(command),Duration.ofMillis(advance));
        }
        public void requireOriginal(ActionPorts.OutcomeArchive archive) {
            if(ordinary)return;
            require(equals(decode(original,Objects.requireNonNull(archive).loadMaterial(original))),
                    "actual installed clock timings differ from their exact retained configuration");
        }
    }
    /** These are exact installed-family arguments, not another arm/cancel command formatter. */
    public record Arm(OperationKey operation) {
        public Arm {Objects.requireNonNull(operation);AdvancePrimitives.armSpec(operation.value());}
    }
    public record Cancel(OperationKey operation) {
        public Cancel {Objects.requireNonNull(operation);AdvancePrimitives.cancelGeneration(operation.value());}
    }

    public static final class Prepared {
        private final Sources sources;
        private final Timings timings;
        private final ReadContract<Status> status,unknownStatus,terminalStatus,physicalStatus;
        private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        public Prepared(Sources actualSources,Timings actualTimings) {
            sources=Objects.requireNonNull(actualSources);timings=Objects.requireNonNull(actualTimings);
            status=ClockStatusRead.registeredContract(sources.statusDefinition());
            unknownStatus=RootUnknownSentinelReadProfile.registeredContract(status);
            terminalStatus=RootUnknownSentinelReadProfile.registeredTerminalContract(status);
            physicalStatus=RootUnknownSentinelReadProfile.registeredPhysicalContract(status);
        }
        public ReadContract<Status> statusContract(){return status;}
        public ReadContract<Status> unknownStatusContract(){return unknownStatus;}
        public ReadContract<Status> terminalStatusContract(){return terminalStatus;}
        public ReadContract<Status> physicalStatusContract(){return physicalStatus;}
        public Sources sources(){return sources;}
        public Timings timings(){return timings;}
        public List<ExactRef> requiredSources() {
            return java.util.stream.Stream.of(sources.primitiveProducer(),sources.primitiveDecoder(),sources.primitiveVerifier(),
                    sources.statusDefinition(),sources.statusDecoder(),sources.unknownStatusDecoder(),timings.original()).distinct().toList();
        }
        /** Pure construction occurs before the physical Driver is adopted. Reusing a context retains every actual instance. */
        public synchronized Installed install(RootRuntimeContext context,AdvanceReadiness.Port sameReadiness,
                PendingUiLifeAdvance.Scope samePendingDate)throws IOException {
            Objects.requireNonNull(context);
            Objects.requireNonNull(sameReadiness);Objects.requireNonNull(samePendingDate);
            Installed prior=installed.get(context);
            if(prior!=null) {
                require(prior.readiness==sameReadiness && prior.pendingDate==samePendingDate,
                        "same physical clock context cannot replace its actual readiness or pending date source scope");return prior;
            }
            require(installed.size()<64,"finite physical clock installations exceeded");
            var actual=new Installed(context,sameReadiness,samePendingDate,sources,timings,status,unknownStatus,terminalStatus,physicalStatus);installed.put(context,actual);return actual;
        }
    }

    public static final class Installed {
        private final RootRuntimeContext context;
        private final Sources sources;
        private final Timings timings;
        private final AdvanceReadiness.Port readiness;
        private final PendingUiLifeAdvance.Scope pendingDate;
        private final AdvanceObservationPort observations;
        private final ClockStatusRead statuses;
        private final ReadContract<Status> unknownStatus,terminalStatus,physicalStatus;
        private final AdvanceClock timeline;
        private final AdvancePrimitives primitives;
        private final AdvancePrimitiveArchivedReplay replay;
        private final RootExecutableBindings.Family<Arm> arms;
        private final RootExecutableBindings.Family<Cancel> cancels;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext actualContext,AdvanceReadiness.Port sameReadiness,
                PendingUiLifeAdvance.Scope samePendingDate,Sources sources,
                Timings timings,ReadContract<Status> exactInstalledStatus,ReadContract<Status> exactUnknownStatus,
                ReadContract<Status> exactTerminalStatus,ReadContract<Status> exactPhysicalStatus) {
            context=actualContext;this.sources=sources;this.timings=timings;readiness=sameReadiness;pendingDate=samePendingDate;
            observations=pendingDate.observations(new ActualObservations(context,timings));
            statuses=new ClockStatusRead(context.reads(),exactInstalledStatus,exactUnknownStatus,context.archive());
            unknownStatus=Objects.requireNonNull(exactUnknownStatus);terminalStatus=Objects.requireNonNull(exactTerminalStatus);physicalStatus=Objects.requireNonNull(exactPhysicalStatus);
            RootUnknownSentinelReadProfile.requireInstalled(unknownStatus,statuses);
            RootUnknownSentinelReadProfile.requireInstalled(terminalStatus,statuses);
            RootUnknownSentinelReadProfile.requireInstalled(physicalStatus,statuses);
            timeline=new AdvanceClock(observations,statuses,readiness,context.clock(),timings.maximumFrames(),timings.commandTimeout(),timings.advanceTimeout());
            primitives=new AdvancePrimitives(observations,statuses,context.clock(),timings.maximumFrames(),pendingDate,timings.advanceTimeout());
            replay=new AdvancePrimitiveArchivedReplay(context.frameLoader());
            List<RootExecutableBindings.ActionBinding> fixed=new ArrayList<>();
            List<NativeRecordedEvidenceVerifier.Binding> archived=new ArrayList<>();
            for(String step:List.of("pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5")) {
                var issued=issue(new OperationKey(step),"game.command."+step,sources);fixed.add(issued.action());archived.add(issued.archived());
            }
            arms=new RootExecutableBindings.Family<>("shared-actual-clock-arm",Arm.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(ClockStatusRead.ARM_CAP),sources.primitiveProducer(),sources.primitiveDecoder(),sources.primitiveVerifier(),
                    value->encode(value.operation()),Arm::operation,value->issue(value.operation(),ClockStatusRead.ARM_CAP,sources),
                    operation->operation.value().startsWith(ClockStatusRead.ARM_PREFIX)?Optional.of(new Arm(operation)):Optional.empty());
            cancels=new RootExecutableBindings.Family<>("shared-actual-clock-cancel",Cancel.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(ClockStatusRead.CANCEL_CAP),sources.primitiveProducer(),sources.primitiveDecoder(),sources.primitiveVerifier(),
                    value->encode(value.operation()),Cancel::operation,value->issue(value.operation(),ClockStatusRead.CANCEL_CAP,sources),
                    operation->operation.value().startsWith(ClockStatusRead.CANCEL_PREFIX)?Optional.of(new Cancel(operation)):Optional.empty());
            installation=new RootDomainInstallation("shared-actual-advance-infrastructure",List.of(),
                    List.of(new RootReadContractCatalog.InstalledRead(exactInstalledStatus,sources.statusDecoder()),
                            new RootReadContractCatalog.InstalledRead(unknownStatus,sources.unknownStatusDecoder()),
                            new RootReadContractCatalog.InstalledRead(terminalStatus,sources.unknownStatusDecoder()),
                            new RootReadContractCatalog.InstalledRead(physicalStatus,sources.unknownStatusDecoder())),List.of(),fixed,List.of(),archived,
                    List.of(arms,cancels),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private RootExecutableBindings.IssuedAction issue(OperationKey operation,String capability,Sources sources) {
            var effect=NativeEffectRegistry.Binding.existing(operation,sources.primitiveProducer(),primitives,primitives);
            var binding=new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(capability),sources.primitiveDecoder());
            return new RootExecutableBindings.IssuedAction(binding,replay.binding(operation,sources.primitiveVerifier()));
        }
        public AdvanceObservationPort observations(){return observations;}
        public ClockStatusRead statuses(){return statuses;}
        public ReadContract<Status> unknownStatuses(){return unknownStatus;}
        public ReadContract<Status> terminalStatuses(){return terminalStatus;}
        public ReadContract<Status> physicalStatuses(){return physicalStatus;}
        public AdvanceClock timeline(){return timeline;}
        public AdvancePrimitives primitives(){return primitives;}
        public AdvancePrimitiveArchivedReplay replay(){return replay;}
        public RootDomainInstallation installation(){return installation;}
        public Sources sources(){return sources;}
        public Timings timings(){return timings;}
        /** Ownership of installed callable objects only; the caller still proves actual canonical parent/child and lease permission. */
        public void requireOwner(RootRuntimeContext same,RootExecutableBindings bindings) {
            require(context==Objects.requireNonNull(same) && context.bindings()==Objects.requireNonNull(bindings),
                    "derived clock admission crossed its original physical Root/catalog");
            require(bindings.readCatalog().containsIdentity(statuses.contract())
                    && statuses.contract().sourceRef().equals(sources.statusDefinition()),
                    "derived clock admission lost its exact installed Status object/source");
            for(ReadContract<Status> profile:List.of(unknownStatus,terminalStatus,physicalStatus)) {
                require(bindings.readCatalog().containsIdentity(profile), "actual source-bound sentinel profile is not installed by identity");
                RootUnknownSentinelReadProfile.requireInstalled(profile,statuses);
            }
            for(String step:List.of("pause-map","resume-map","set-speed-1","set-speed-2","set-speed-3","set-speed-4","set-speed-5")) {
                OperationKey operation=new OperationKey(step);
                var actual=bindings.actualActionBinding(operation).orElseThrow(() -> new IllegalArgumentException("actual fixed clock producer is absent"));
                require(actual.preparation()==primitives && actual.producerSource().equals(sources.primitiveProducer())
                        && bindings.archivedBindings().stream().anyMatch(value->value.operation().equals(operation)
                            && value.definitionSource().equals(sources.primitiveVerifier())),
                        "derived clock admission crossed the actual shared primitive producer/replay sources");
            }
        }
    }
    private static RawJson encode(OperationKey operation) {
        var row=StrictJson.object().put("operation",operation.value());return new RawJson(StrictJson.canonical(row));
    }
    /** The same final held producer is resolved at invocation, after actual adoption. Absence never becomes an empty frame. */
    private static final class ActualObservations implements AdvanceObservationPort {
        private final RootRuntimeContext context;
        private final Timings timings;
        private HeldDriverObservationPort actual;
        private ActualObservations(RootRuntimeContext context,Timings timings){this.context=context;this.timings=timings;}
        private synchronized HeldDriverObservationPort actual(ActionCommand parent,Instant deadline) {
            try {
                context.requireCurrent(deadline);
                timings.requireOriginal(context.archive());
                require(!deadline.isAfter(ActionObservationWindow.deadline(parent)) && parent.source().equals(context.source())
                        && parent.sessionId().equals(context.game().sessionId()) && parent.before().game().equals(context.game().generation()),
                        "actual clock observation crossed the original current Root Game/source/session/deadline");
                var adopted=context.adopted();adopted.producer().requireSameTransport(context.transport(),context.source());
                var held=adopted.observations();
                require(actual==null || actual==held,"same physical clock cannot replace its actual held observation producer");actual=held;return held;
            } catch(IOException failure){throw new UncheckedIOException("actual adopted clock observation unavailable",failure);}
        }
        @Override public Frame current(ActionCommand parent,Instant deadline){
            HeldDriverObservationPort sameHeld=actual(parent,deadline);
            try {
                return context.withSession(same->{
                    if (ActionChildPlanningScope.isReservedChild(same, same.head(), parent)) {
                        context.adopted().authority().requireOutsideObservationScope(same);
                        return freshReservedChildObservation(same, parent, deadline, sameHeld);
                    }
                    var borrowed=context.collector().withActiveCurrent(same,parent.before(),deadline,lease->{
                        var original=lease.frame();
                        require(original.identity().equals(parent.before()) && original.source().equals(parent.source())
                                && original.sessionId().equals(parent.sessionId()), "active clock observation crossed its exact held parent frame");
                        var push=new ObservationProvenance.Push(original.identity().frame().snapshotId(),
                                original.identity().frame().identity().nativeRevision(),original.originalEvidence());
                        return new Frame(original.identity(),original.source(),original.sessionId(),original.semantic(),push,
                                original.observedAt(),original.originalEvidence());
                    });
                    if(borrowed.isPresent())return borrowed.orElseThrow();
                    // A running parent can reuse its exact guarded entry before any child; later observations stay fresh.
                    // An incompatible ordinary scope throws above and cannot trigger fallback sampling.
                    context.adopted().authority().requireOutsideObservationScope(same);
                    var validation = ActionCommandScope.validationGuard(parent, same);
                    if (validation.isPresent()) {
                        var guard = validation.orElseThrow();
                        try { return sameHeld.retainedEntry(parent, guard, deadline); }
                        catch (IllegalStateException missing) {
                            var replayed = RootGuardEvidence.loadFrame(guard, context.archive().withSession(same), context.core().frameLoader());
                            return sameHeld.retainedEntryReplay(parent, guard, deadline, replayed);
                        }
                    }
                    var entry = ActionChildPlanningScope.entryGuard(same, same.head(), parent);
                    if (entry.isPresent()) {
                        var guard = entry.orElseThrow();
                        try { return sameHeld.retainedEntry(parent, guard, deadline); }
                        catch (IllegalStateException missing) {
                            var replayed = RootGuardEvidence.loadFrame(guard, context.archive().withSession(same), context.core().frameLoader());
                            return sameHeld.retainedEntryReplay(parent, guard, deadline, replayed);
                        }
                    }
                    return sameHeld.current(parent,deadline);
                });
            }catch(IOException failure){throw new UncheckedIOException("actual held clock observation unavailable",failure);}
        }
        @Override public Frame next(ActionCommand parent,ObservationIdentity after,Instant deadline){return actual(parent,deadline).next(parent,after,deadline);}
        /** The actual held packet is only a read/control basis; STATUS still supplies its independent original. */
        @Override public <T> T withClockControlBasis(ActionCommand parent, Instant deadline,
                java.util.function.Function<Frame,T> work) {
            Objects.requireNonNull(work);
            actual(parent,deadline);
            try {
                return context.withSession(same -> {
                    if (RootPlanningReadGuard.lifeCancellationStatusSource(same, same.head(), parent,
                            context.archive().withSession(same)).isPresent()) {
                        return context.collector().currentDerivedCleanup(same, parent.before(), deadline,
                                lease -> clockControlBasis(parent, lease.frame(), work));
                    }
                    return context.collector().current(same, parent.before(), deadline,
                            lease -> clockControlBasis(parent, lease.frame(), work));
                });
            } catch(IOException failure) {
                throw new UncheckedIOException("actual held clock control basis unavailable",failure);
            }
        }
        private static <T> T clockControlBasis(ActionCommand parent,
                org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete original,
                java.util.function.Function<Frame,T> work) {
            require(original.source().equals(parent.source()) && original.sessionId().equals(parent.sessionId())
                    && original.identity().machineId().equals(parent.before().machineId())
                    && original.identity().game().equals(parent.before().game())
                    && original.identity().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                    && original.identity().frame().identity().player().equals(parent.before().frame().identity().player()),
                    "clock control basis crossed its actual original source/session/Game/episode/actor");
            var basis = new Frame(original.identity(), original.source(), original.sessionId(), original.semantic(),
                    new ObservationProvenance.Push(original.identity().frame().snapshotId(),
                            original.identity().frame().identity().nativeRevision(), original.originalEvidence()),
                    original.observedAt(), original.originalEvidence());
            return work.apply(basis);
        }

        private Frame freshReservedChildObservation(ContinuityStorePort.Session same, ActionCommand child,
                Instant deadline, HeldDriverObservationPort sameHeld) throws IOException {
            var receipt = context.core().journal().locked(same, locked -> locked.find(child.actionId()).orElseThrow());
            require(receipt.command().equals(child) && receipt.bodySha256().equals(ActionCodec.bodySha256(child)),
                    "reserved child receipt crossed its actual command/body");
            var ack = receipt.ack().filter(NativeActionPort.AckReceived::nativeOk)
                    .orElseThrow(() -> new IOException("actual reserved child has no successful original ACK"));
            NativeFreshSnapshotPort.Result fresh;
            try { fresh = context.transport().readFreshFullState(deadline); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                var failure = new InterruptedIOException("actual reserved child fresh read interrupted; no replay");
                failure.initCause(interrupted);throw failure;
            }
            if (fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                String reason = unavailable.reason();
                throw new IOException("actual reserved child fresh read unavailable: " + reason.substring(0, Math.min(512, reason.length())));
            }
            var received = (NativeFreshSnapshotPort.Received)fresh;
            NativeFreshSnapshotPort.verifyAfter(ack, received);
            require(context.clock().instant().isBefore(deadline)
                    && !received.originalFrame().observedAt().isAfter(deadline), "actual received-frame projection deadline expired");
            var complete = context.adopted().authority().withFrozenRawObservation(received.originalFrame(), same, frozen -> {
                var nativeOriginal = context.archive().withSession(same).preserveNativeFrame(received.originalFrame());
                var projected = context.core().observationAssembler().assemble(received.originalFrame(), frozen.facts(), nativeOriginal);
                if (projected instanceof org.xar.ck3.control.application.driver.DriverObservationAssembler.Incomplete missing)
                    throw new IllegalStateException("incomplete actual semantic observation: " + String.join(",", missing.reasons()));
                return (org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete) projected;
            });
            require(context.clock().instant().isBefore(deadline), "actual waited snapshot projection exceeded its original capture deadline");
            require(child.before().machineId().equals(complete.identity().machineId())
                    && child.before().game().equals(complete.identity().game())
                    && child.before().frame().episodeRunId().equals(complete.identity().frame().episodeRunId())
                    && child.sessionId().equals(complete.sessionId()) && child.source().equals(complete.source()),
                    "observation crossed held parent Game/source/session/episode");
            return new Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                    new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                            complete.identity().frame().identity().nativeRevision(), complete.originalEvidence()),
                    complete.observedAt(), complete.originalEvidence());
        }
    }
}
