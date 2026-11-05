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
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.nativebridge.NativeWire;
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

    /** A bounded new read-only query may follow only an archived, completed exact availability rejection. */
    static NativeFreshSnapshotPort.Result readAvailableFreshSnapshot(NativeFreshSnapshotPort port,
            Instant deadline, java.time.Clock clock, int maximumAttempts,
            java.util.function.Consumer<NativeFreshSnapshotPort.Unavailable> preserveUnavailable)
            throws IOException, InterruptedException {
        Objects.requireNonNull(port); Objects.requireNonNull(deadline); Objects.requireNonNull(clock);
        Objects.requireNonNull(preserveUnavailable);
        require(maximumAttempts >= 1 && maximumAttempts <= 65536, "finite actual fresh READ attempt bound required");
        NativeFreshSnapshotPort.Result last = null;
        for (int attempt = 0; attempt < maximumAttempts; attempt++) {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException("actual fresh READ interrupted");
            if (!clock.instant().isBefore(deadline)) {
                if (last != null) return last;
                throw new IOException("actual fresh READ original deadline expired before dispatch");
            }
            NativeFreshSnapshotPort.Result fresh = port.readFreshFullState(deadline);
            if (fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                preserveUnavailable.accept(unavailable);
                if (unavailable.dispatch() instanceof NativeActionPort.Unknown) {
                    if (!clock.instant().isBefore(deadline)) return unavailable;
                    if (Thread.currentThread().isInterrupted()) throw new InterruptedException("actual fresh READ collection interrupted");
                    fresh = port.collectFreshFullState(unavailable.dispatch().requestId(), deadline);
                    if (fresh instanceof NativeFreshSnapshotPort.Unavailable collected) preserveUnavailable.accept(collected);
                }
            }
            last = fresh;
            if (!(fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable)) return fresh;
            if (!(unavailable.dispatch() instanceof NativeActionPort.AckReceived ack) || ack.nativeOk()) return unavailable;
            var decoded = NativeWire.decode(ack.originalPacket());
            require(decoded instanceof NativeWire.CommandResult, "actual fresh READ ACK packet type changed");
            var original = (NativeWire.CommandResult) decoded;
            require(!original.nativeOk() && original.requestId().equals(ack.requestId())
                    && java.util.Arrays.equals(original.payload().value(), ack.originalFrame().bytes()),
                    "actual fresh READ ACK binding changed");
            require(ack.outbound().isPresent(), "actual fresh READ negative ACK requires its retained outbound packet");
            var outbound = NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
            require(outbound.requestId().equals(ack.requestId()) && outbound.step().equals(NativeFreshSnapshotPort.STEP),
                    "actual fresh READ negative ACK crossed its original read-only request");
            if (attempt == 0) {
                // Diagnostics only, after both original-preservation callbacks have returned successfully.
                try {
                    var notice = StrictJson.object();
                    notice.put("schema", "xar.root-read-owner-triage/v1");
                    notice.put("status", "OWNER_UI_TRIAGE_REQUIRED");
                    notice.put("read_request_id", ack.requestId());
                    notice.put("observed_at_utc", clock.instant().toString());
                    notice.put("observation_deadline_utc", deadline.toString());
                    notice.put("maximum_attempts", maximumAttempts);
                    notice.put("read_attempt", attempt + 1);
                    var scopedAction = ActionScope.currentActionId();
                    if (scopedAction.isPresent() && scopedAction.orElseThrow().length() <= 256)
                        notice.put("action_scope_id", scopedAction.orElseThrow());
                    else notice.putNull("action_scope_id");
                    notice.put("command_deadline_status", "NOT_HELD_IN_THIS_READER");
                    notice.put("artifact_refs_status", "PRESERVED_BY_CALLBACK_NOT_EXPOSED_TO_READER");
                    notice.put("archive_callbacks_completed", true);
                    notice.put("original_frame_present", unavailable.originalFrame().isPresent());
                    notice.put("native_ok", false);
                    notice.put("native_error_presence", original.error().presence().name());
                    if (original.error().token().isPresent()) {
                        byte[] errorToken = original.error().token().orElseThrow().value();
                        notice.put("native_error_token_bytes", errorToken.length);
                        if (errorToken.length <= 1024) notice.set("native_error", NativeWire.parse(errorToken));
                        else notice.put("native_error_omitted_over_bound", true);
                    }
                    notice.put("ui_block_confirmed", false);
                    notice.put("native_cause_confirmed", false);
                    notice.put("diagnostic_only", true);
                    byte[] line = StrictJson.canonical(notice);
                    if (line.length <= 8192) System.out.println(new String(line, java.nio.charset.StandardCharsets.UTF_8));
                } catch (IOException | RuntimeException diagnosticOnly) {
                    // A failed diagnostic attempt cannot change the original observation/archive outcome.
                }
            }
            if (original.error().presence() != NativeWire.Presence.VALUE) return unavailable;
            var error = NativeWire.parse(original.error().token().orElseThrow().value());
            if (!error.isTextual() || !error.textValue().equals("fresh_full_state_native_read_unavailable")) return unavailable;
            Instant now = clock.instant();
            if (attempt + 1 >= maximumAttempts || !now.isBefore(deadline)) return unavailable;
            Duration remaining = Duration.between(now, deadline);
            Duration pause = remaining.compareTo(Duration.ofMillis(100)) < 0 ? remaining : Duration.ofMillis(100);
            Thread.sleep(pause);
        }
        return Objects.requireNonNull(last);
    }

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
            statuses=new ClockStatusRead(context.reads(),exactInstalledStatus,exactUnknownStatus,context.archive(),this::observeRetainedParentStatus);
            unknownStatus=Objects.requireNonNull(exactUnknownStatus);terminalStatus=Objects.requireNonNull(exactTerminalStatus);physicalStatus=Objects.requireNonNull(exactPhysicalStatus);
            RootUnknownSentinelReadProfile.requireInstalled(unknownStatus,statuses);
            RootUnknownSentinelReadProfile.requireInstalled(terminalStatus,statuses);
            RootUnknownSentinelReadProfile.requireInstalled(physicalStatus,statuses);
            timeline=new AdvanceClock(observations,statuses,readiness,context.clock(),timings.maximumFrames(),timings.commandTimeout(),timings.advanceTimeout());
            primitives=new AdvancePrimitives(observations,statuses,context.clock(),timings.maximumFrames(),pendingDate,timings.advanceTimeout());
            replay=new AdvancePrimitiveArchivedReplay(freshFrameLoader(context.frameLoader()));
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
        /** One canonical retained Life parent may borrow the actual physical-only Status source; no Ready or action permission. */
        private ClockStatusRead.Observation observeRetainedParentStatus(ActionCommand parent,
                AdvanceObservationPort.Frame current,Instant deadline) {
            try {
                return context.withSession(same->{
                    context.requireCurrent(deadline);context.writer().requireSession(same);
                    context.adopted().authority().requireOutsideObservationScope(same);
                    require(ActionScope.currentActionId().filter(parent.actionId()::equals).isPresent()
                            && ActionCommandScope.current().filter(value->java.util.Arrays.equals(
                                ActionCodec.encodeCommand(value),ActionCodec.encodeCommand(parent))).isPresent(),
                            "physical Life Status escaped its original coordinator parent");
                    var archive=context.archive().withSession(same);var head=same.head();
                    var actions=context.core().journal().locked(same,locked->List.copyOf(locked.snapshot().actions()));
                    var original=org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyLifeRecoveryRoot(actions)
                            .orElseThrow(()->new IOException("physical Life Status has no unique canonical read-only parent"));
                    require(original.bodySha256().equals(ActionCodec.bodySha256(parent))
                            && java.util.Arrays.equals(ActionCodec.encodeCommand(original.command()),ActionCodec.encodeCommand(parent)),
                            "physical Life Status changed its actual original parent command");
                    var execution=((ActionState.CompositeUnknown)original.state()).execution();
                    var children=execution.children().stream().map(binding->{
                        var matches=actions.stream().filter(value->value.command().actionId().equals(binding.actionId())).toList();
                        require(matches.size()==1&&matches.getFirst().bodySha256().equals(binding.bodySha256())
                                &&matches.getFirst().settled(),"physical Life Status cannot cross an unresolved or replaced child");
                        return matches.getFirst();
                    }).toList();
                    require(!children.isEmpty(),"physical Life Status requires its complete original child prefix");
                    AdvanceClockArchivedReplay.verifyChildBindings(parent,children);requireWatchRole(original,children.getLast());
                    var plan=AdvancePlan.decode(parent);
                    var arm=children.stream().filter(value->value.command().operation().value().equals(plan.armStep()))
                            .findFirst().orElseThrow(()->new IOException("physical Life Status lost its original ARM"));
                    AdvanceClock.validateArm(AdvancePrimitives.acknowledgedSentinel(
                            arm.ack().filter(NativeActionPort.AckReceived::nativeOk).orElseThrow(),plan.armStep()),plan);
                    var manifest=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                            current.semantic().get("java_driver_facts_evidence"),"actual parent Status Driver basis");
                    ExactRef facts=ExactRef.fromJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(manifest));
                    var complete=context.frameLoader().load(new NativeEffectEvidence.FrameBasis(current.originalEvidence(),facts),archive);
                    require(complete.identity().equals(current.identity())&&complete.source().equals(current.source())
                            &&complete.sessionId().equals(current.sessionId())&&complete.semantic().equals(current.semantic())
                            &&complete.observedAt().equals(current.observedAt())&&complete.originalEvidence().equals(current.originalEvidence()),
                            "physical Life Status changed its complete original current observation");
                    requireFrameBinding(parent,complete);
                    require(current.provenance() instanceof ObservationProvenance.FreshSnapshotQuery,
                            "physical Life Status requires its actual independent current READ");
                    verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery)current.provenance(),complete,archive);
                    var pins=List.of(same.capturePin(current.originalEvidence(),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES),
                            same.capturePin(facts,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES));
                    var observation=context.physicalStatusReads().withObserved(same,deadline,lease->{
                        var identity=lease.identity();var frame=lease.frame();
                        require(identity.source().equals(parent.source())&&identity.game().equals(parent.before().game())
                                &&identity.machineId().equals(parent.before().machineId())&&identity.sessionId().equals(parent.sessionId())
                                &&frame.nativeRevision().compareTo(current.identity().frame().identity().nativeRevision())>=0
                                &&!frame.observedAt().isBefore(current.observedAt()),
                                "physical Life Status crossed the original source/Game/session or regressed Native time");
                        var state=org.xar.ck3.control.application.driver.DriverJson.object(frame.state().bytes(),
                                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
                        var player=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(state.get("played_character"),"physical Life Status player");
                        require(org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(state.get("paused"),"paused")
                                &&org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(state.get("map_ready"),"map_ready")
                                &&org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(player.get("alive"),"alive")
                                &&org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(player.get("character_id"),"character_id")
                                    .equals(parent.before().frame().identity().player())
                                &&org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(state.get("date_raw"),"date_raw")
                                    .compareTo(current.identity().frame().identity().dateRaw())>=0,
                                "physical Life Status requires the actual paused living original actor and nonregressing date");
                        RootUnknownSentinelReadProfile.requirePhysicalProfile(physicalStatus);
                        var request=PlanningReadRequest.newStatusOnly(identity,physicalStatus.operation(),
                                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),deadline);
                        var result=context.reads().read(same,physicalStatus,request);
                        if(!(result instanceof PlanningReadResult.Known<Status>))
                            throw new IOException("actual physical Life Status query unavailable: "+((PlanningReadResult.Unavailable<Status>)result).reason());
                        var known=(PlanningReadResult.Known<Status>)result;
                        require(known.receipt().request().equals(request)&&known.receipt().contractId().equals(physicalStatus.contractId())
                                &&known.value().equals(ClockStatusRead.decode(known.receipt().original())),
                                "physical Life Status returned another original query or decoded value");
                        return new ClockStatusRead.Observation(known.value(),known.receipt(),archive.preserve(known.receipt().original()));
                    });
                    for(var pin:pins)same.verifyPin(pin);
                    context.requireCurrent(deadline);context.writer().requireSession(same);
                    require(head.digest().equals(same.head().digest()),"physical Life Status changed canonical history");
                    return observation;
                });
            } catch(IOException failure) {throw new UncheckedIOException("actual retained Life physical Status unavailable",failure);}
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
    /** Replays actual fresh READ originals; the delegate remains the sole full Driver decoder. */
    static NativeEffectEvidence.FrameLoader freshFrameLoader(NativeEffectEvidence.FrameLoader actual) {
        Objects.requireNonNull(actual);
        return new NativeEffectEvidence.FrameLoader() {
            @Override public DriverObservationAssembler.Complete load(NativeEffectEvidence.FrameBasis basis,
                    ActionPorts.OutcomeArchive archive) { return actual.load(basis, archive); }
            @Override public void verifyFreshSnapshotQuery(ObservationProvenance.FreshSnapshotQuery proof,
                    DriverObservationAssembler.Complete complete, ActionPorts.OutcomeArchive archive) {
                RootAdvanceInfrastructureFactory.verifyFreshSnapshotQuery(proof, complete, archive);
            }
        };
    }

    /** Original DATA validation only: this cannot issue a source session, Received, or writer permission. */
    static void verifyFreshSnapshotQuery(ObservationProvenance.FreshSnapshotQuery proof,
            DriverObservationAssembler.Complete complete, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(proof);Objects.requireNonNull(complete);Objects.requireNonNull(archive);
        try {
            var read=successfulAck(archive.load(proof.readAcknowledgement()));
            require(read.requestId().equals(proof.requestId()), "fresh query request differs from its original READ ACK");
            var custody=read.custody().orElseThrow();
            byte[] packet=archive.loadNativeFrame(complete.originalEvidence());
            require(packet.length==complete.originalEvidence().bytes()
                    && ActionCodec.sha256(packet).equals(complete.originalEvidence().sha256()), "fresh native original bytes differ");
            var decoded=NativeWire.decode(packet);
            require(decoded instanceof NativeWire.Snapshot, "fresh native original is not a full snapshot");
            var snapshot=(NativeWire.Snapshot)decoded;
            var actual=new NativeObservationPort.ObservedFrame(custody.session(),snapshot.snapshotId(),snapshot.revision(),
                    new RawJson(snapshot.state().value()),packet,complete.observedAt());
            var identity=complete.identity();
            require(custody.session().machineId().equals(identity.machineId()) && custody.session().game().equals(identity.game())
                    && custody.session().sessionId().equals(complete.sessionId())
                    && custody.session().connectionGeneration().equals(complete.connectionGeneration())
                    && complete.source().machineId().equals(identity.machineId())
                    && snapshot.snapshotId().equals(identity.frame().snapshotId())
                    && snapshot.revision().equals(identity.frame().identity().nativeRevision()),
                    "fresh READ crossed actual Native/Driver identity/source/connection");
            if(!(proof.basis() instanceof ObservationProvenance.LiveAfterSetter)) {
                NativeFreshSnapshotPort.verifyOriginal(read,actual,proof.snapshotReceived());
            }
            if(proof.basis() instanceof ObservationProvenance.LiveAfterSetter live) {
                NativeFreshSnapshotPort.verifyAfterOriginal(successfulAck(archive.load(live.setterAcknowledgement())),
                        read,actual,proof.snapshotReceived());
            } else if(proof.basis() instanceof ObservationProvenance.ColdAfterAcknowledgement cold) {
                var originalReceipt=archive.loadReceipt(cold.originalReceipt());
                require(archive.receiptReferenceOf(originalReceipt).equals(cold.originalReceipt()),"cold original receipt reference differs");
                require(originalReceipt.state() instanceof ActionState.AckReceived || originalReceipt.state() instanceof ActionState.Unknown,
                        "cold resume-map requires its actual unresolved acknowledged original");
                var command=originalReceipt.command();
                require(originalReceipt.bodySha256().equals(ActionCodec.bodySha256(command)), "cold original command body differs");
                var knownPending = org.xar.ck3.control.application.session.ContinuityBatchJournal.isReadOnlyKnownPendingRecovery(originalReceipt);
                var councilPending=org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyPositiveAckCouncilRecoveryRoot(List.of(originalReceipt))
                        .filter(originalReceipt::equals).isPresent();
                var eventPending=org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyEventRecoveryRoot(List.of(originalReceipt))
                        .filter(originalReceipt::equals).isPresent();
                require((command.origin() instanceof CommandOrigin.Gameplay && command.operation().value().equals("resume-map")
                        && command.arguments().members().isEmpty()) || knownPending || councilPending || eventPending,
                        "cold original requires exact resume-map, known-pending or original positive-ACK Council/EVENT recovery primitive");
                requireFrameBinding(command,complete);
                var attempt=ActionTransitions.attempt(originalReceipt.state()).orElseThrow();
                var dispatch=ActionTransitions.dispatch(originalReceipt.state()).orElseThrow();
                var ack=successfulAck(dispatch);
                var guard=attempt.guard();
                require(guard.origin() instanceof CommandOrigin.Gameplay && command.origin().acceptsGuard(guard.origin())
                        && guard.observed().equals(command.before()) && guard.source().equals(command.source())
                        && guard.sessionId().equals(command.sessionId()) && guard.operation().equals(command.operation()),
                        "cold resume-map original Attempt crossed its complete command/guard binding");
                var prepared=attempt.preparedRequest();
                var base=councilPending?new NativeRequest(command.operation().value(),Optional.empty(),
                        new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(org.xar.ck3.control.governance.council.CouncilActionCodec.wireFields(
                                org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation.councilRequest(command,attempt.requestId()),true))))
                        :eventPending?EventActionPreparation.prepare(command)
                        :knownPending?org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionEffects.preparation().prepare(command):AdvancePrimitives.prepareRequest(command);
                if(councilPending)org.xar.ck3.control.nativebridge.capabilities.governance.CouncilContinuationPolicy.requireOriginalPending(command,attempt,ack);
                require(prepared.step().equals(base.step()) && prepared.requiredCapability().equals(base.requiredCapability())
                        && java.util.Arrays.equals(prepared.additionalFields().bytes(),base.additionalFields().bytes()),
                        "cold resume-map preparation differs from the actual primitive producer");
                require(ack.requestId().equals(attempt.requestId()),"cold ACK differs from Attempt");
                var requestRef=archive.requestReferenceOf(attempt.preparedRequest());
                var dispatchRef=archive.referenceOf(ack);
                require(archive.loadRequest(requestRef).equals(attempt.preparedRequest()) && archive.load(dispatchRef).equals(ack),"cold originals differ");
                var outbound=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
                require(outbound.requestId().equals(attempt.requestId()) && outbound.step().equals(command.operation().value())
                        && outbound.expectedRevision().or(()->outbound.expectedSnapshotRevision()).filter(command.before().frame().identity().nativeRevision()::equals).isPresent()
                        && java.util.Arrays.equals(outbound.normalizedAdditionalFields().value(),attempt.preparedRequest().additionalFields().bytes()),"cold outbound differs");
                var originalDecoded=NativeWire.decode(ack.originalPacket());
                require(originalDecoded instanceof NativeWire.CommandResult result && result.nativeOk() && result.requestId().equals(ack.requestId())
                        && java.util.Arrays.equals(result.payload().value(),ack.originalFrame().bytes())
                        && result.result().token().isPresent()==ack.originalResultToken().isPresent()
                        && (result.result().token().isEmpty()||java.util.Arrays.equals(result.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes())),"cold ACK packet differs");
                var prior=ack.custody().orElseThrow();prior.verify(ack,guard);
                require(!prior.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                        "cold resume-map actual write predates its canonical Attempt");
                require(prior.session().machineId().equals(custody.session().machineId()) && prior.session().game().equals(custody.session().game())
                        && prior.session().sessionId().equals(custody.session().sessionId()) && !read.requestId().equals(ack.requestId()),"cold session/request mismatch");
                if(prior.session().equals(custody.session()) && prior.custodyEpoch().equals(custody.custodyEpoch())) {
                    NativeFreshSnapshotPort.verifyAfterOriginal(ack,read,actual,proof.snapshotReceived());
                } else {
                    require(custody.session().connectionGeneration().compareTo(prior.session().connectionGeneration())>=0
                            && custody.writeEntered().observedAt().isAfter(prior.responseReceived().observedAt()),"cold read crossed connection or predates ACK");
                }
            } else {
                var watch=(ObservationProvenance.SameGameWatch)proof.basis();
                var parent=archive.loadReceipt(watch.originalParentReceipt());
                var resume=archive.loadReceipt(watch.originalResumeReceipt());
                requireWatchRole(parent,resume);
                requireFrameBinding(parent.command(),complete);
                var setter=resume.ack().orElseThrow();var prior=setter.custody().orElseThrow();prior.verify(setter);
                require(prior.session().machineId().equals(custody.session().machineId())
                        && prior.session().game().equals(custody.session().game())
                        && prior.session().sessionId().equals(custody.session().sessionId())
                        && !read.requestId().equals(setter.requestId())
                        && !custody.writeEntered().observedAt().isBefore(prior.responseReceived().observedAt()),
                        "same-Game watch READ predates or crosses its original resumed Game/session");
            }
        } catch(IOException failure) {throw new UncheckedIOException("actual fresh READ originals differ",failure);}
    }

    private static NativeActionPort.AckReceived successfulAck(NativeActionPort.DispatchOutcome value) {
        require(value instanceof NativeActionPort.AckReceived ack && ack.nativeOk(), "successful original native ACK required");
        return (NativeActionPort.AckReceived)value;
    }
    private static void requireFrameBinding(ActionCommand parent,DriverObservationAssembler.Complete complete) {
        require(parent.source().equals(complete.source()) && parent.sessionId().equals(complete.sessionId())
                && parent.before().machineId().equals(complete.identity().machineId())
                && parent.before().game().equals(complete.identity().game())
                && parent.before().frame().episodeRunId().equals(complete.identity().frame().episodeRunId())
                && parent.before().frame().identity().player().equals(complete.identity().frame().identity().player()),
                "fresh observation crossed original parent source/session/Game/episode/actor");
    }
    private static void requireWatchRole(ActionReceipt parent,ActionReceipt resume) {
        require(parent.state() instanceof ActionState.CompositeUnknown && LifeAdvanceComposite.accepts(parent.command().operation().value()),
                "same-Game watch requires its original UNKNOWN Life parent");
        var execution=((ActionState.CompositeUnknown)parent.state()).execution();
        require(execution.handlerId().equals(LifeAdvanceComposite.HANDLER) && !execution.children().isEmpty()
                && parent.command().origin().acceptsGuard(execution.guard().origin())
                && execution.guard().source().equals(parent.command().source())
                && execution.guard().sessionId().equals(parent.command().sessionId())
                && execution.guard().observed().equals(parent.command().before())
                && execution.guard().operation().equals(parent.command().operation()), "watch lost its original Life execution/guard");
        var bound=execution.children().getLast();var child=resume.command();
        require(bound.actionId().equals(child.actionId()) && bound.bodySha256().equals(resume.bodySha256())
                && child.actionId().equals(ActionIds.child(parent.command().actionId(),execution.children().size(),child.operation()))
                && child.operation().value().equals("resume-map") && resume.state() instanceof ActionState.Settled settled
                && settled.settlement() instanceof ActionState.Applied && resume.ack().filter(NativeActionPort.AckReceived::nativeOk).isPresent()
                && child.source().equals(parent.command().source())
                && child.sessionId().equals(parent.command().sessionId())
                && child.before().machineId().equals(parent.command().before().machineId())
                && child.before().game().equals(parent.command().before().game())
                && child.before().frame().episodeRunId().equals(parent.command().before().frame().episodeRunId())
                && child.before().frame().identity().player().equals(parent.command().before().frame().identity().player()),
                "watch resume is not the exact settled successful final child of its original parent");
    }

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
                    return freshParentObservation(same, parent, deadline);
                });
            }catch(IOException failure){throw new UncheckedIOException(clockObservationFailure(failure),failure);}
        }
        /** Diagnostic only; the original IOException remains the thrown cause and no observation is accepted here. */
        private static String clockObservationFailure(IOException original) {
            final int limit=1536;
            var message=new StringBuilder("actual held clock observation unavailable");
            var seen=new IdentityHashMap<Throwable,Boolean>();
            Throwable current=original;
            for(int depth=0;current!=null && depth<8 && message.length()<limit;depth++) {
                if(seen.put(current,Boolean.TRUE)!=null) {
                    appendDiagnostic(message," <- [cause cycle]",limit);current=null;break;
                }
                appendDiagnostic(message,depth==0?": ":" <- ",limit);
                appendDiagnostic(message,current.getClass().getName(),limit);
                String detail=current.getMessage();
                if(detail!=null && !detail.isEmpty()) {
                    appendDiagnostic(message,": ",limit);appendDiagnostic(message,detail,limit);
                }
                current=current.getCause();
            }
            if(current!=null)appendDiagnostic(message," <- [cause limit]",limit);
            return message.toString();
        }
        private static void appendDiagnostic(StringBuilder output,String value,int limit) {
            for(int index=0;index<value.length() && output.length()<limit;) {
                char next=value.charAt(index++);
                if(Character.isHighSurrogate(next)) {
                    if(index<value.length() && Character.isLowSurrogate(value.charAt(index))) {
                        if(output.length()+2>limit)break;
                        output.append(next).append(value.charAt(index++));
                    } else output.append('\uFFFD');
                } else output.append(Character.isLowSurrogate(next)?'\uFFFD':next);
            }
        }
        @Override public Frame next(ActionCommand parent,ObservationIdentity after,Instant deadline){
            actual(parent,deadline);
            try {return context.withSession(same->{
                context.adopted().authority().requireOutsideObservationScope(same);
                for(int count=0;count<timings.maximumFrames() && context.clock().instant().isBefore(deadline);count++) {
                    Frame frame=freshParentObservation(same,parent,deadline);
                    if(frame.identity().frame().identity().nativeRevision().compareTo(after.frame().identity().nativeRevision())>0)return frame;
                }
                throw new IOException("actual fresh next frame did not advance its native revision within the original finite budget");
            });}catch(IOException failure){throw new UncheckedIOException("actual fresh next observation unavailable",failure);}
        }
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
            var receipt=context.core().journal().locked(same,locked->locked.find(child.actionId()).orElseThrow());
            require(receipt.command().equals(child),"reserved child receipt differs from its actual command");
            var ack=receipt.ack().filter(NativeActionPort.AckReceived::nativeOk).orElseThrow();
            var archive=context.archive().withSession(same);
            var proofBasis=new ObservationProvenance.LiveAfterSetter(archive.preserve(ack));
            return freshObservation(same,child,deadline,proofBasis);
        }

        private Frame freshParentObservation(ContinuityStorePort.Session same,ActionCommand parent,Instant deadline)throws IOException {
            var canonical=context.core().journal().locked(same,locked->locked.find(parent.actionId()).orElseThrow());
            require(canonical.command().equals(parent),"fresh parent differs from its current canonical command");
            var execution=canonical.state() instanceof ActionState.CompositeUnknown unknown?unknown.execution():
                    canonical.state() instanceof ActionState.CompositeRunning running?running.execution():null;
            require(execution!=null && !execution.children().isEmpty(),"post-action observation requires actual canonical child history");
            var children=context.core().journal().locked(same,locked->execution.children().stream().map(bound->{
                var child=locked.find(bound.actionId()).orElseThrow();
                require(bound.bodySha256().equals(child.bodySha256()) && child.settled(),"fresh observation has an unresolved or changed canonical child");
                return child;
            }).toList());
            AdvanceClockArchivedReplay.verifyChildBindings(parent,children);
            var last=children.getLast();var ack=last.ack().filter(NativeActionPort.AckReceived::nativeOk).orElseThrow();
            var archive=context.archive().withSession(same);
            ObservationProvenance.FreshSnapshotBasis basis;
            if(canonical.state() instanceof ActionState.CompositeUnknown
                    && !ack.custody().orElseThrow().session().equals(context.adopted().session())) {
                requireWatchRole(canonical,last);
                require(org.xar.ck3.control.application.session.ContinuityBatchJournal.readOnlyLifeRecoveryRoot(
                        ContinuityActionJournal.receipts(same.head().state(),archive)).filter(canonical::equals).isPresent(),
                        "same-Game watch is not the admitted complete canonical Life prefix");
                basis=new ObservationProvenance.SameGameWatch(archive.receiptReferenceOf(canonical),archive.receiptReferenceOf(last));
            } else basis=new ObservationProvenance.LiveAfterSetter(archive.preserve(ack));
            return freshObservation(same,parent,deadline,basis);
        }

        private Frame freshObservation(ContinuityStorePort.Session same,ActionCommand parent,Instant deadline,
                ObservationProvenance.FreshSnapshotBasis basis)throws IOException {
            var archive=context.archive().withSession(same);
            NativeFreshSnapshotPort.Result fresh;
            try {
                fresh=readAvailableFreshSnapshot(context.transport(),deadline,context.clock(),timings.maximumFrames(),unavailable->{
                    archive.preserve(unavailable.dispatch());
                    unavailable.originalFrame().ifPresent(archive::preserveNativeFrame);
                });
            } catch(InterruptedException interrupted) {
                Thread.currentThread().interrupt();var failure=new InterruptedIOException("actual fresh read interrupted; original action is not replayed");
                failure.initCause(interrupted);throw failure;
            }
            if(fresh instanceof NativeFreshSnapshotPort.Unavailable unavailable) {
                var dispatch=unavailable.dispatch();var original=archive.preserve(dispatch);
                var frame=unavailable.originalFrame().map(archive::preserveNativeFrame);
                String kind=dispatch instanceof NativeActionPort.AckReceived ack?"ACK/native_ok="+ack.nativeOk():
                        dispatch instanceof NativeActionPort.RejectedBeforeDispatch?"REJECTED_BEFORE_DISPATCH":"UNKNOWN";
                String reason=unavailable.reason();
                throw new IOException("actual fresh read unavailable: kind="+kind+"; request_id="+dispatch.requestId()
                        +"; dispatch_ref="+original+"; frame_ref="+frame.map(Object::toString).orElse("absent")
                        +"; reason="+reason.substring(0,Math.min(512,reason.length())));
            }
            var received=(NativeFreshSnapshotPort.Received)fresh;
            require(context.clock().instant().isBefore(deadline) && !received.originalFrame().observedAt().isAfter(deadline),
                    "actual received-frame projection deadline expired");
            var proof=new ObservationProvenance.FreshSnapshotQuery(received.acknowledgement().requestId(),
                    archive.preserve(received.acknowledgement()),received.snapshotReceived(),basis);
            var complete=context.adopted().authority().withFrozenRawObservation(received.originalFrame(),same,frozen->{
                var original=archive.preserveNativeFrame(received.originalFrame());
                var projected=context.core().observationAssembler().assemble(received.originalFrame(),frozen.facts(),original);
                if(projected instanceof DriverObservationAssembler.Incomplete missing)
                    throw new IllegalStateException("incomplete actual semantic observation: "+String.join(",",missing.reasons()));
                return (DriverObservationAssembler.Complete)projected;
            });
            requireFrameBinding(parent,complete);
            verifyFreshSnapshotQuery(proof,complete,archive);
            require(context.clock().instant().isBefore(deadline),"actual fresh projection exceeded its original deadline");
            return new Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),proof,
                    complete.observedAt(),complete.originalEvidence());
        }

    }
}
