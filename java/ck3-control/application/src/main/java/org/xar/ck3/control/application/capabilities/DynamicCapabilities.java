package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedArtifact;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.planning.warexit.WarExitCapabilities;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.routecontact.RouteContactCapabilities;
import org.xar.ck3.control.application.routecontact.RouteContactCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Production gameplay capability calculation. A received hello is descriptive
 * metadata; every advertised operation must also resolve to the identical
 * frozen Root callable that will prepare/execute it.
 */
public final class DynamicCapabilities {
    private static final Set<String> LIFE_PRIMITIVES = Set.of("set-speed-1","set-speed-3","set-speed-5","resume-map","pause-map");
    private static final Set<String> EXACT_DAY = Set.of("set-speed-1","resume-map","pause-map");
    private static final Set<String> SENTINEL = Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N","game.command.research-query-tactical-daily-sentinel-v1");
    private static final Set<String> RETREAT = Set.of(NativeActionSteps.PREVIEW,NativeActionSteps.MOVE,"game.command.query-battle-control-snapshot-v1-N");
    private DynamicCapabilities() { }

    public record Configuration(Optional<Path> stateDir,Optional<Path> saveDir,int routeContactTimelineSpeed,
            int routeContactEffectiveTimelineSpeed,boolean allowRouteContactHighSpeedAb,boolean stationaryObjectiveHoldCanaryRequested) {
        public Configuration {
            Objects.requireNonNull(stateDir); Objects.requireNonNull(saveDir);
            stateDir.ifPresent(p -> require(p.isAbsolute(),"actual absolute state directory required"));
            saveDir.ifPresent(p -> require(p.isAbsolute(),"actual absolute save directory required"));
            require(routeContactTimelineSpeed >= 1 && routeContactTimelineSpeed <= 5
                    && routeContactEffectiveTimelineSpeed >= 1 && routeContactEffectiveTimelineSpeed <= 5,"timeline speeds must be integer 1..5");
        }
    }

    /** Pure configured-original decoder. No frame, Driver or capability authority is required or produced. */
    public static Configuration decodeConfiguration(Obj actual) {
        Objects.requireNonNull(actual);require(actual.members().keySet().equals(Set.of("state_dir","save_dir","route_contact_timeline_speed","route_contact_effective_timeline_speed",
                "allow_route_contact_high_speed_ab","stationary_objective_hold_canary_requested")),"complete configuration contract required");
        return new Configuration(configurationPath(actual,"state_dir"),configurationPath(actual,"save_dir"),
                integer(actual.get("route_contact_timeline_speed"),"route_contact_timeline_speed").intValueExact(),
                integer(actual.get("route_contact_effective_timeline_speed"),"route_contact_effective_timeline_speed").intValueExact(),
                bool(actual.get("allow_route_contact_high_speed_ab"),"allow_route_contact_high_speed_ab"),
                bool(actual.get("stationary_objective_hold_canary_requested"),"stationary_objective_hold_canary_requested"));
    }
    public static Obj encodeConfiguration(Configuration actual) {
        Objects.requireNonNull(actual);return new Obj(Map.of("state_dir",actual.stateDir().<Value>map(value->new Text(value.toString())).orElse(Nil.INSTANCE),
                "save_dir",actual.saveDir().<Value>map(value->new Text(value.toString())).orElse(Nil.INSTANCE),
                "route_contact_timeline_speed",new IntegerValue(BigInteger.valueOf(actual.routeContactTimelineSpeed())),
                "route_contact_effective_timeline_speed",new IntegerValue(BigInteger.valueOf(actual.routeContactEffectiveTimelineSpeed())),
                "allow_route_contact_high_speed_ab",new Bool(actual.allowRouteContactHighSpeedAb()),
                "stationary_objective_hold_canary_requested",new Bool(actual.stationaryObjectiveHoldCanaryRequested())));
    }
    private static Optional<Path> configurationPath(Obj row,String field) {
        Value value=row.get(field);return value==Nil.INSTANCE?Optional.empty():Optional.of(Path.of(text(value,field)).normalize());
    }
    /** Immutable actual runtime-owner capture, decoded from its archived original bytes under its owning lock. */
    public static final class DriverInputs {
        public static final String SCHEMA = "xar.native-driver-capability-inputs/v3";
        private static final Set<String> KEYS = Set.of("schema","driver_stamp","state_version","arrange_marriage_choices","campaign_root_context_query",
                "active_combat_retreat_v1_token","episode_seed","episode_transition","succession_reconciliation","configuration","independent_battle_speed_readiness","native_session_control");
        private final Stamp stamp;
        private final ExactRef originalFacts;
        private final Obj original;
        private final BigInteger stateVersion;
        private final List<Obj> marriages;
        private final Optional<Obj> rootQuery,retreatToken,seed,transition,reconciliation,independentBattle;
        private final Configuration config;
        private final CapabilitySessionPresentation session;
        private DriverInputs(Complete frame,Known driver,ExactRef source,byte[] raw) {
            require(source.bytes() == raw.length && source.sha256().equals(DriverJson.sha256(raw)),"actual archived runtime capability facts differ");
            Obj row = DriverJson.object(raw,DriverJson.MAX_NATIVE_BYTES);
            require(row.members().keySet().equals(KEYS) && named(row,"schema",SCHEMA),"complete versioned runtime-owner capability fields required");
            require(object(row.get("driver_stamp"),"driver_stamp").equals(DriverRuntimeCapabilities.capabilityStamp(frame,driver)),"runtime state crossed the actual frozen Driver/native frame");
            stamp = driver.stamp(); originalFacts = source; original = row;
            stateVersion = integer(row.get("state_version"),"state_version"); require(stateVersion.signum() >= 0,"nonnegative exact runtime-owner state version required");
            marriages = requiredRows(row,"arrange_marriage_choices");
            for (Obj choice : marriages) require(text(choice.get("choice_id"),"choice_id").matches("[0-9]+-[0-9]+"),"canonical actual marriage choice required");
            rootQuery = optionalObject(row,"campaign_root_context_query"); retreatToken = optionalObject(row,"active_combat_retreat_v1_token");
            seed = optionalObject(row,"episode_seed"); transition = optionalObject(row,"episode_transition"); reconciliation = optionalObject(row,"succession_reconciliation");
            independentBattle = optionalObject(row,"independent_battle_speed_readiness");
            session = CapabilitySessionPresentation.decode(object(present(row,"native_session_control"),"native_session_control"));
            config = decodeConfiguration(object(row.get("configuration"),"configuration"));
            session.validateConfiguration(config);
        }
        public static DriverInputs decode(Complete frame,Known driver,ExactRef source,byte[] actualOriginal) {
            Objects.requireNonNull(frame); Objects.requireNonNull(driver); Objects.requireNonNull(source); Objects.requireNonNull(actualOriginal);
            return new DriverInputs(frame,driver,source,actualOriginal.clone());
        }
        public Stamp stamp() { return stamp; }
        public ExactRef originalFacts() { return originalFacts; }
        public Obj original() { return original; }
        public BigInteger stateVersion() { return stateVersion; }
        public Configuration configuration() { return config; }
        public List<Obj> marriageChoices() { return marriages; }
        public Optional<Obj> campaignRootQuery() { return rootQuery; }
        public Optional<Obj> activeRetreatToken() { return retreatToken; }
        public Optional<Obj> episodeSeed() { return seed; }
        public Optional<Obj> episodeTransition() { return transition; }
        public Optional<Obj> successionReconciliation() { return reconciliation; }
        public Optional<Obj> independentBattleSpeedReadiness() { return independentBattle; }
        public CapabilitySessionPresentation nativeSessionControl() { return session; }
        private static Optional<Obj> optionalObject(Obj row,String field) {
            Value value = present(row,field); return value == Nil.INSTANCE ? Optional.empty() : Optional.of(object(value,field));
        }
    }
    public sealed interface InputState permits AvailableInputs, UnavailableInputs { }
    public record AvailableInputs(DriverInputs inputs) implements InputState { public AvailableInputs { Objects.requireNonNull(inputs); } }
    public record UnavailableInputs(List<String> reasons) implements InputState {
        public UnavailableInputs { reasons = List.copyOf(reasons); require(!reasons.isEmpty(),"explicit missing actual runtime-owner inputs required"); }
    }
    /** The Root installs the actual owner. A bootstrap without real cache/runtime facts must return UnavailableInputs. */
    public interface ActualDriverInputsSource {
        InputState capture(Complete frame,Known driver) throws IOException;
        boolean stillCurrent(DriverInputs captured,Complete frame,Known driver) throws IOException;
    }
    public sealed interface Result permits Projected, Incomplete { }
    public record Incomplete(List<String> reasons) implements Result {
        public Incomplete { reasons = List.copyOf(reasons); require(!reasons.isEmpty(),"actual capability inputs unavailable"); }
    }
    public record Projected(CapabilitySnapshot snapshot,List<String> gaps) implements Result {
        public Projected { Objects.requireNonNull(snapshot); gaps = List.copyOf(gaps); }
    }
    /** Both public MCP surfaces use this single encoder, including explicit unavailable results. */
    public static Obj toJson(Result result) {
        Objects.requireNonNull(result);
        if (result instanceof Projected available) return available.snapshot().toJson();
        Incomplete missing = (Incomplete)result;
        return new Obj(Map.of("format_version",new IntegerValue(BigInteger.ONE),"status",new Text("unavailable"),
                "snapshot",new Bool(false),"wait_for_change",new Bool(false),"action_steps",new Arr(List.of()),
                "composite_action_steps",new Arr(List.of()),"capability_gaps",strings(missing.reasons())));
    }
    public record CapabilitySnapshot(Set<OperationKey> actionSteps,Set<String> bridgeCapabilities,Set<OperationKey> compositeActionSteps,
            Optional<Obj> battleSpeedReadiness,boolean independentBattleSpeedReady,boolean snapshot,boolean waitForChange,
            Obj canonical,ExactRef runtimeFacts,Stamp driverStamp,String frameBindingSha256) {
        public CapabilitySnapshot {
            actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities); compositeActionSteps = Set.copyOf(compositeActionSteps);
            Objects.requireNonNull(battleSpeedReadiness); Objects.requireNonNull(canonical); Objects.requireNonNull(runtimeFacts); Objects.requireNonNull(driverStamp);
            require(actionSteps.containsAll(compositeActionSteps),"composites must remain in exact installed action set");
        }
        public Obj toJson() { return canonical; }
    }

    /** Pure selectors plus one shared strong file capture. No native command, planning query, ledger mutation or replay is performed. */
    public static Result project(Complete frame,Known driver,Obj receivedCapabilities,ExecutableStepBindings installed,
            ActualDriverInputsSource actualInputs,CapabilityFileProbe fileProbe) throws IOException {
        return project(frame,driver,receivedCapabilities,installed,actualInputs,fileProbe,ProjectionPurpose.ORDINARY);
    }
    private enum ProjectionPurpose { ORDINARY, PUBLIC_PLANNING_READ_ONLY }
    /** Public planning needs current capability DATA before its terminal/window/ordinary branch.
     * Only the actual private raw-scope producer can supply this input; no ordinary guard is widened. */
    public static Result projectPublicPlanning(Complete frame,Known driver,Obj receivedCapabilities,ExecutableStepBindings installed,
            org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.PublicPlanningInputs actualInputs,
            CapabilityFileProbe fileProbe)throws IOException {
        Objects.requireNonNull(actualInputs).requireScope(frame,driver);
        return project(frame,driver,receivedCapabilities,installed,actualInputs,fileProbe,ProjectionPurpose.PUBLIC_PLANNING_READ_ONLY);
    }
    /** A finite inventory for the original pure terminal planner. These are DATA roles, never an ordinary action origin. */
    public record PublicTerminalInventory(Set<OperationKey> steps,Set<String> nativeCapabilities,ExactRef originalInputs){
        public PublicTerminalInventory {steps=Set.copyOf(steps);nativeCapabilities=Set.copyOf(nativeCapabilities);Objects.requireNonNull(originalInputs);}
    }
    public static PublicTerminalInventory projectPublicTerminal(
            org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot full,Known driver,Obj received,
            ExecutableStepBindings installed,org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.PublicTerminalInputs inputs,
            org.xar.ck3.control.application.driver.DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
            CapabilityFileProbe files)throws IOException {
        Objects.requireNonNull(full);Objects.requireNonNull(driver);Objects.requireNonNull(received);Objects.requireNonNull(installed);
        inputs.requireScope(full,driver);scope.requireInputs(full,driver);require(installed.frozen(),"actual frozen executable metadata required");
        Obj semantic=full.semantic(),diagnostics=object(received.get("diagnostics"),"actual terminal diagnostics");
        for(String key:List.of("connected","semantic_state_available","transport_fatal_error","hello"))present(diagnostics,key);
        Obj hello=object(diagnostics.get("hello"),"actual terminal HELLO");
        require(hello.equals(object(object(semantic.get("diagnostics"),"full terminal diagnostics").get("hello"),"full terminal HELLO"))
                &&integer(hello.get("pid"),"pid").equals(BigInteger.valueOf(full.actual().session().game().pid()))
                &&integer(hello.get("connection_generation"),"connection_generation").equals(full.actual().session().connectionGeneration())
                &&yes(diagnostics,"connected")&&yes(diagnostics,"semantic_state_available")&&nil(diagnostics,"transport_fatal_error")
                &&named(received,"mode","native-headless")&&named(received,"backend_id","native-headless")&&no(received,"visual_fallback"),
                "terminal inventory lost its actual current raw Native protocol source");
        Set<String> caps=new LinkedHashSet<>();for(Value raw:array(hello.get("capabilities"),"capabilities"))caps.add(text(raw,"capability"));
        require(caps.contains("game.state.snapshot")&&bool(present(received,"snapshot"),"snapshot"),"actual terminal Native snapshot capability unavailable");
        bool(present(received,"wait_for_change"),"wait_for_change");
        List<Obj> history=DriverSurvivingHistory.rows(driver.driver());
        require(new Arr(history.stream().map(row->(Value)row).toList()).equals(semantic.get("native_command_history")),
                "terminal inventory requires the actual full expanded Driver history");
        var normalized=inputs.capabilityLifecycle();
        Value originalReason=inputs.nativeCampaignConstructor()?semantic.get("one_life_terminal_reason"):present(semantic,"one_life_terminal_reason");
        require(inputs.nativeCampaignConstructor()||originalReason==Nil.INSTANCE||originalReason instanceof Text,"terminal reason must preserve its explicit null/string role");
        String terminal=textOrNull(semantic,"one_life_terminal_reason");
        Optional<Obj> completed=FreshCapabilityHistory.completedTerminal(history,driver.stamp().episodeRunId());
        Set<String> candidates=new TreeSet<>();
        if(terminal!=null&&normalized.lifecycle().equals("rogue_one_life"))candidates.add("death-terminal");
        if(successorReady(semantic,terminal,normalized.lifecycle(),completed,inputs.successionReconciliation()))candidates.add("continue-as-reconciled-successor");
        boolean needSeed=terminal!=null&&!terminal.equals("played_character_changed")&&completed.isPresent()
                &&inputs.configuration().stateDir().isPresent()&&inputs.episodeTransition().isEmpty();
        if(needSeed){
            require(files!=null,"actual immutable seed file producer unavailable");
            var capture=files.capturePublicTerminal(full,driver,scope,inputs.configuration(),true);
            require(capture.seed().isPresent(),"configured terminal seed source was not observed");
            var seed=capture.seed().orElseThrow();
            if(seed instanceof SeedAdoption.Unknown)throw new IOException("actual terminal immutable seed read unavailable");
            if(seed instanceof SeedAdoption.Available available&&seedMatches(inputs.episodeSeed(),available))candidates.add("start-next-episode");
        }
        Set<String> admitted=describe(candidates,caps,installed,inputs::verifySource);inputs.requireScope(full,driver);scope.requireCurrent();
        return new PublicTerminalInventory(operations(admitted),caps,inputs.original());
    }
    private static Result project(Complete frame,Known driver,Obj receivedCapabilities,ExecutableStepBindings installed,
            ActualDriverInputsSource actualInputs,CapabilityFileProbe fileProbe,ProjectionPurpose purpose)throws IOException {
        Objects.requireNonNull(frame); Objects.requireNonNull(driver); Objects.requireNonNull(receivedCapabilities);
        if(purpose==ProjectionPurpose.ORDINARY&&driver.auxiliary().members().containsKey(SuccessorUiObligation.AUXILIARY_KEY)) {
            var pending=SuccessorUiObligationCodec.decode(DriverJson.encode(driver.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            if(pending.blocksOrdinaryActionsAndSave())return new Incomplete(List.of("actual_successor_ui_pending_requires_its_private_root_ui_scope"));
        }
        if (installed == null || !installed.frozen()) return new Incomplete(List.of("actual_frozen_root_executable_bindings_unavailable"));
        if (actualInputs == null) return new Incomplete(List.of("actual_driver_ephemeral_input_owner_unavailable"));
        InputState inputState = actualInputs.capture(frame,driver);
        if (inputState instanceof UnavailableInputs missing) return new Incomplete(missing.reasons());
        DriverInputs inputs = ((AvailableInputs)inputState).inputs();
        require(inputs.stamp().equals(driver.stamp()),"actual runtime-owner inputs crossed frozen Driver version");
        require(driver.stamp().game().equals(frame.identity().game()) && driver.stamp().episodeRunId().equals(frame.identity().frame().episodeRunId())
                && driver.observation().isPresent(),"actual Driver/native binding unavailable");
        Obj semantic = frame.semantic(), diagnostics = object(receivedCapabilities.get("diagnostics"),"diagnostics");
        for (String key : List.of("connected","semantic_state_available","transport_fatal_error","hello")) present(diagnostics,key);
        Obj hello = object(diagnostics.get("hello"),"original hello");
        require(yes(diagnostics,"connected") && yes(diagnostics,"semantic_state_available") && nil(diagnostics,"transport_fatal_error")
                && named(receivedCapabilities,"mode","native-headless") && named(receivedCapabilities,"backend_id","native-headless")
                && no(receivedCapabilities,"visual_fallback"),"current received native protocol state unavailable");
        require(integer(hello.get("pid"),"pid").equals(BigInteger.valueOf(frame.identity().game().pid()))
                && integer(hello.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"hello crossed current process/generation");
        Set<String> caps = new LinkedHashSet<>();
        for (Value raw : array(hello.get("capabilities"),"capabilities")) caps.add(text(raw,"capability"));
        boolean snapshotSupported = caps.contains("game.state.snapshot") && bool(present(receivedCapabilities,"snapshot"),"snapshot");
        if (!snapshotSupported) return new Incomplete(List.of("actual_complete_native_snapshot_capability_unavailable"));
        boolean waitSupported = bool(present(receivedCapabilities,"wait_for_change"),"wait_for_change");
        List<Obj> history = DriverSurvivingHistory.rows(driver.driver());
        require(new Arr(history.stream().map(row -> (Value)row).toList()).equals(semantic.get("native_command_history")),"actual owned full history differs from current semantic assembler");
        List<String> gaps = new ArrayList<>();
        List<Obj> tail = FreshCapabilityHistory.last128(history);
        FreshCapabilityHistory.Occupation occupation = caps.contains(NativeActionSteps.OCCUPATION)
                ? FreshCapabilityHistory.occupation(semantic,tail) : new FreshCapabilityHistory.Occupation(Set.of(),List.of());
        Set<String> candidates = new TreeSet<>(NativeActionSteps.candidates(new NativeActionSteps.Input(caps,semantic,inputs.marriageChoices(),occupation.opposingOccupiedTargets())));
        if (yes(semantic, "paused")) {
            for (ExecutableStepBindings.InstalledStep step : installed.installed()) {
                if (step.kind() == ExecutableStepBindings.Kind.ACTION
                        && step.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        && step.requiredCapability().isEmpty()) {
                    candidates.add(step.operation().value());
                }
            }
        }
        candidates.remove("research-arm-tactical-daily-sentinel-v1-N");
        if (caps.contains(NativeActionSteps.ASSAULT_STATE) && caps.contains(NativeActionSteps.OCCUPATION))
            NativeActionSteps.addAssaults(candidates,occupation.holdingSiegeStates(),caps.contains("game.command.start-assault-N") && caps.contains("game.command.stop-assault-N"),caps.contains("game.command.stop-assault-N"));
        candidates.addAll(FreshCapabilityHistory.firstHopSteps(semantic,tail,candidates,caps));
        inputs.campaignRootQuery().ifPresent(root -> {
            CapitalContactScopes.capitalRegroupScope(semantic,root).ifPresent(scope -> addCapital(candidates,caps,scope,true));
            CapitalContactScopes.alliedCapitalHoldScope(semantic,root).ifPresent(scope -> addCapital(candidates,caps,scope,false));
            DefenderRefugeScopes.sameFrameDirectVassalRefugeScope(semantic,root).ifPresent(scope -> {
                int army = integerAt(scope,"army_id").intValueExact(); List<Integer> hostiles = requiredIds(scope.get("hostile_army_ids"),true);
                for (int target : requiredIds(scope.get("candidate_province_ids"),false)) {
                    if (caps.contains(NativeActionSteps.PREVIEW)) candidates.add(NativeActionSteps.preview(army,target));
                    if (caps.contains(NativeActionSteps.MOVE)) candidates.add(NativeActionSteps.move(army,target));
                    if (caps.contains(NativeActionSteps.HORIZON)) candidates.add(NativeActionSteps.horizon(army,target,hostiles));
                }
            });
        });
        Set<String> composites = new TreeSet<>();
        // Primitive availability is the real frozen installation intersection, before a composite is considered.
        Set<String> installedPrimitives = admitted(candidates,caps,installed,frame,purpose,actualInputs);
        if (waitSupported && installedPrimitives.containsAll(LIFE_PRIMITIVES) && !caps.contains("game.command.life-advance")) { composites.add("life-advance"); composites.add("life-advance-one-day"); }
        Configuration config = inputs.configuration();
        if (waitSupported && caps.containsAll(SENTINEL) && yes(semantic,"paused") && yes(semantic,"map_ready") && nil(semantic,"active_event") && nil(semantic,"pending_character_interaction")
                && FreshCapabilityHistory.sentinelWatch(semantic).isPresent() && installedPrimitives.containsAll(Set.of("resume-map","pause-map"))) {
            if (installedPrimitives.contains("set-speed-3")) composites.add("battle-decision-epoch-advance");
            if (installedPrimitives.contains("set-speed-" + config.routeContactTimelineSpeed()) && (config.allowRouteContactHighSpeedAb() || config.routeContactTimelineSpeed() <= 3)) {
                composites.add("committed-route-sentinel-advance"); composites.add("war-objective-hold-sentinel-advance");
            }
            if (installedPrimitives.contains("set-speed-5")) composites.add("battle-terminal-cruise");
        }
        if (caps.containsAll(RETREAT) && yes(semantic,"paused")) {
            composites.addAll(FreshCapabilityHistory.retreatPreviewSteps(semantic,candidates));
            inputs.activeRetreatToken().flatMap(token -> FreshCapabilityHistory.retreatOrder(semantic,token)).ifPresent(composites::add);
        }
        if (waitSupported && caps.contains(NativeActionSteps.HORIZON) && installedPrimitives.containsAll(EXACT_DAY)) {
            try {
                var routeFrame = RouteContactCodec.frame(frame.identity(),frame.source(),frame.sessionId(),semantic);
                var rows = DriverSurvivingHistory.entries(driver.driver());
                for (OperationKey step : RouteContactCapabilities.steps(routeFrame,
                        RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(rows),routeFrame),RouteContactHistoryAdapter.timeline(rows))) {
                    boolean window = step.value().startsWith("advance-route-contact-window-v1-");
                    if (!window || caps.containsAll(SENTINEL) && installedPrimitives.contains("set-speed-" + config.routeContactEffectiveTimelineSpeed())) composites.add(step.value());
                }
            } catch (IllegalArgumentException | ArithmeticException missingRouteInput) { gaps.add("current_complete_route_capability_inputs: " + missingRouteInput.getMessage()); }
        }
        for (OperationKey step : WarExitCapabilities.steps(semantic,history,caps)) candidates.add(step.value());
        if (caps.contains("game.command.query-war-entry-assessments-v1-N") && yes(semantic,"paused")) {
            Set<Integer> targets = new LinkedHashSet<>();
            for (Obj row : rows(semantic.get("declarable_wars"))) if (int32Id(row.get("target_character_id"))) targets.add(idAt(row,"target_character_id"));
            for (Obj war : rows(semantic.get("active_wars"))) if (int32Id(war.get("primary_opponent_character_id"))) targets.add(idAt(war,"primary_opponent_character_id"));
            for (int target : targets) candidates.add("query-war-entry-assessments-v1-1-" + target);
        }
        String terminal = textOrNull(semantic,"one_life_terminal_reason"), lifecycle = textOrNull(obj(semantic.get("succession_lifecycle")).orElse(null),"lifecycle");
        if(purpose==ProjectionPurpose.PUBLIC_PLANNING_READ_ONLY
                &&actualInputs instanceof org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.PublicPlanningInputs rawInputs
                &&rawInputs.privateCapabilityLifecycle().isPresent())lifecycle=rawInputs.privateCapabilityLifecycle().orElseThrow().lifecycle();
        Optional<Obj> completed = FreshCapabilityHistory.completedTerminal(history,frame.identity().frame().episodeRunId());
        if (terminal != null && "rogue_one_life".equals(lifecycle)) composites.add("death-terminal");
        if (successorReady(semantic,terminal,lifecycle,completed,inputs.successionReconciliation())) composites.add("continue-as-reconciled-successor");
        boolean needSeed = terminal != null && !"played_character_changed".equals(terminal) && completed.isPresent() && config.stateDir().isPresent() && inputs.episodeTransition().isEmpty();
        if (fileProbe == null) gaps.add("actual_checkpoint_and_seed_file_probe_unavailable");
        else {
            CapabilityFileProbe.Capture files = fileProbe.capture(frame,driver.stamp(),config,needSeed);
            require(files.stamp().equals(driver.stamp()) && files.frameBindingSha256().equals(frame.fullBindingSha256()),"actual file projection crossed frozen observation");
            if (files.checkpoint() instanceof CapabilityFileProbe.Present && config.stateDir().isPresent()) composites.add("restore-checkpoint");
            if (files.checkpoint() instanceof CapabilityFileProbe.Unavailable unavailable) gaps.add("checkpoint_file: " + unavailable.reason());
            if (needSeed && files.seed().filter(s -> s instanceof SeedAdoption.Available).isPresent() && seedMatches(inputs.episodeSeed(),(SeedAdoption.Available)files.seed().orElseThrow())) composites.add("start-next-episode");
            if (needSeed && files.seed().filter(s -> s instanceof SeedAdoption.Unknown).isPresent()) gaps.add("immutable_seed_current_read_unavailable");
        }
        candidates.addAll(composites);
        if (LegacyResearchHold.active(semantic)) { candidates.removeIf(s -> LegacyResearchHold.dateControl(s) || LegacyResearchHold.armyMoveControl(s)); composites.retainAll(candidates); }
        Set<String> admitted = admitted(candidates,caps,installed,frame,purpose,actualInputs); composites.retainAll(admitted);
        require(actualInputs.stillCurrent(inputs,frame,driver),"runtime-owner capability state changed during projection");
        Optional<Obj> independent = inputs.independentBattleSpeedReadiness();
        boolean independentReady = independent.filter(row -> independentMatches(semantic,row)).isPresent();
        if (independent.isPresent() && !independentReady) gaps.add("independent_battle_speed_payload_not_current_ready");
        Obj battle = battleReadiness(config,independent.filter(row -> independentMatches(semantic,row)),admitted);
        Map<String,Value> output = new LinkedHashMap<>(receivedCapabilities.members());
        output.put("format_version",new IntegerValue(BigInteger.ONE)); output.put("source",new Text("injected-dll-named-pipe")); output.put("latency",new Text("realtime"));
        for (String key : List.of("headless","minimized_operation","snapshot")) output.put(key,new Bool(true));
        output.put("wait_for_change",new Bool(waitSupported)); output.put("status",new Text("available"));
        output.put("fallback_enabled",new Bool(false)); output.put("action_steps",strings(admitted)); output.put("composite_action_steps",strings(composites));
        output.put("bridge_capabilities",strings(caps)); output.put("battle_speed_readiness",battle);
        output.put("independent_battle_speed_ready",new Bool(independentReady)); output.put("capability_gaps",strings(gaps));
        output.put("episode_seed",inputs.episodeSeed().<Value>map(v -> v).orElse(Nil.INSTANCE)); output.put("episode_character_id",new IntegerValue(driver.driver().session().actorId()));
        output.put("episode_run_id",new Text(driver.driver().session().episodeRunId())); output.put("one_life_terminal",new Bool(terminal != null));
        output.put("one_life_terminal_reason",terminal == null ? Nil.INSTANCE : new Text(terminal));
        output.put("native_session_control",inputs.nativeSessionControl().toJson(config,inputs.episodeTransition(),admitted.contains("restore-checkpoint")));
        output.put("episode_identity_pending",new Bool(inputs.nativeSessionControl().bindingState() == CapabilitySessionPresentation.BindingState.PENDING_COLD_CANDIDATE));
        output.putAll(CapabilityFlags.project(caps,installed,snapshotSupported).members());
        output.put("active_combat_retreat_v1_composition_supported",new Bool(caps.containsAll(RETREAT)
                && installed.supportsCapability(NativeActionSteps.PREVIEW) && installed.supportsCapability(NativeActionSteps.MOVE)
                && installed.supportsCapability("game.command.query-battle-control-snapshot-v1-N")));
        output.put("active_combat_retreat_v1_token_ready",new Bool(inputs.activeRetreatToken().flatMap(token -> FreshCapabilityHistory.retreatOrder(semantic,token)).filter(admitted::contains).isPresent()));
        output.put("one_life_settlement_status",semantic.members().containsKey("one_life_settlement_status") ? semantic.get("one_life_settlement_status") : Nil.INSTANCE);
        output.put("continue_as_heir_after_death",new Bool(false)); output.put("transport_ready",new Bool(true));
        output.put("checkpoint_materialization",new Obj(Map.of("configured",new Bool(config.saveDir().isPresent()),"save_dir",config.saveDir().<Value>map(p -> new Text(p.toString())).orElse(Nil.INSTANCE),"filename",new Text("xar_checkpoint.ck3"))));
        output.put("runtime_capability_facts",new Obj(Map.of("path",new Text(inputs.originalFacts().path()),"bytes",new IntegerValue(BigInteger.valueOf(inputs.originalFacts().bytes())),"sha256",new Text(inputs.originalFacts().sha256()))));
        output.put("runtime_state_version",new Text(inputs.stateVersion().toString()));
        return new Projected(new CapabilitySnapshot(operations(admitted),caps,operations(composites),Optional.of(battle),independentReady,true,waitSupported,new Obj(output),inputs.originalFacts(),driver.stamp(),frame.fullBindingSha256()),gaps);
    }
    private static Set<String> exact(Set<String> candidates,Set<String> caps,ExecutableStepBindings installed,CommandOrigin.Gameplay actualOrigin) {
        Set<String> result = new TreeSet<>();
        for (String step : candidates) {
            if (step.matches(".*(?:^|-)(N|IDS|ID)(?:-|$).*")) continue;
            OperationKey operation = new OperationKey(step);
            installed.resolve(operation,actualOrigin).filter(binding -> binding.requiredCapability().map(caps::contains).orElse(true)).ifPresent(binding -> result.add(step));
        }
        return result;
    }
    @FunctionalInterface private interface SourcePins{void require(ExactRef actual)throws IOException;}
    private static Set<String> admitted(Set<String> candidates,Set<String> caps,ExecutableStepBindings installed,Complete frame,
            ProjectionPurpose purpose,ActualDriverInputsSource actualInputs)throws IOException {
        if(purpose==ProjectionPurpose.ORDINARY)return exact(candidates,caps,installed,new CommandOrigin.Gameplay(frame.identity()));
        if(!(actualInputs instanceof org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.PublicPlanningInputs inputs))
            throw new IllegalArgumentException("actual private raw planning inputs required for metadata-only projection");
        return describe(candidates,caps,installed,inputs::verifySource);
    }
    private static Set<String> describe(Set<String> candidates,Set<String> caps,ExecutableStepBindings installed,SourcePins pins)throws IOException {
        Set<String> result=new TreeSet<>();
        for(String step:candidates){
            if(step.matches(".*(?:^|-)(N|IDS|ID)(?:-|$).*"))continue;
            var described=installed.describeForPublicPlanning(new OperationKey(step));if(described.isEmpty())continue;
            var actual=described.orElseThrow();var descriptor=actual.descriptor();
            require(descriptor.operation().value().equals(step),"public planning metadata described another operation");
            if(descriptor.requiredCapability().filter(required->!caps.contains(required)).isPresent())continue;
            pins.require(descriptor.implementationSource());pins.require(descriptor.decoderSource());
            if(actual.archivedVerifierSource().isPresent())pins.require(actual.archivedVerifierSource().orElseThrow());
            result.add(step);
        }
        return result;
    }
    private static void addCapital(Set<String> steps,Set<String> caps,CapitalContactScopes.Scope scope,boolean move) {
        if (move && caps.contains(NativeActionSteps.PREVIEW)) steps.add(NativeActionSteps.preview(scope.armyId(),scope.capitalProvinceId()));
        if (move && caps.contains(NativeActionSteps.MOVE)) steps.add(NativeActionSteps.move(scope.armyId(),scope.capitalProvinceId()));
        if (caps.contains(NativeActionSteps.HORIZON)) steps.add(NativeActionSteps.horizon(scope.armyId(),scope.capitalProvinceId(),scope.hostileArmyIds()));
    }
    private static boolean successorReady(Obj snapshot,String terminal,String lifecycle,Optional<Obj> completed,Optional<Obj> maybeReconciliation) {
        if (!"played_character_changed".equals(terminal) || !("ordinary_campaign_succession".equals(lifecycle) || "rogue_one_life".equals(lifecycle) && completed.isPresent()) || maybeReconciliation.isEmpty()) return false;
        Obj row = maybeReconciliation.orElseThrow(), binding = obj(row.get("successor_binding")).orElse(null);
        if (!named(row,"status","available") || !named(row,"verdict","matched") || !yes(row,"successor_match") || !yes(row,"title_distribution_match") || binding == null) return false;
        for (String field : List.of("snapshot_id","revision","native_revision","date_raw")) if (!equalField(binding,field,snapshot,field)) return false;
        return true;
    }
    private static boolean seedMatches(Optional<Obj> metadata,SeedAdoption.Available actual) {
        if (metadata.isEmpty()) return false; Obj row = metadata.orElseThrow(); SeedArtifact seed = actual.artifact();
        return named(row,"name",SeedArtifact.NAME) && eq(row,"size",new IntegerValue(BigInteger.valueOf(seed.save().reference().bytes())))
                && named(row,"sha256",seed.save().reference().sha256()) && eq(row,"date_raw",new IntegerValue(seed.dateRaw())) && eq(row,"character_id",new IntegerValue(seed.characterId()));
    }
    private static boolean independentMatches(Obj snapshot,Obj payload) {
        Obj binding = obj(payload.get("source_binding")).orElse(null), diagnostics = obj(snapshot.get("diagnostics")).orElse(null);
        if (!yes(payload,"ready") || binding == null || diagnostics == null) return false;
        for (String key : List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id")) if (!equalField(binding,key,snapshot,key)) return false;
        return equalField(binding,"connection_generation",diagnostics,"connection_generation");
    }
    static Obj battleReadiness(Configuration config,Optional<Obj> independent,Set<String> admitted) {
        Map<String,Value> result = new LinkedHashMap<>();
        Map<String,String> bound = Map.of("decision_sentinel_live_ready","battle-decision-epoch-advance",
                "committed_route_sentinel_live_ready","committed-route-sentinel-advance","stationary_objective_hold_sentinel_live_ready","war-objective-hold-sentinel-advance",
                "stationary_objective_hold_sentinel_canary_ready","war-objective-hold-sentinel-advance","terminal_sentinel_live_ready","battle-terminal-cruise",
                "committed_route_sentinel_speed_4_live_ready","committed-route-sentinel-advance","committed_route_sentinel_speed_5_live_ready","committed-route-sentinel-advance",
                "stationary_objective_hold_sentinel_speed_4_live_ready","war-objective-hold-sentinel-advance","stationary_objective_hold_sentinel_speed_5_live_ready","war-objective-hold-sentinel-advance",
                "overwhelming_matrix_live_ready","battle-terminal-cruise");
        bound.forEach((flag,operation) -> result.put(flag,new Bool(admitted.contains(operation) && independent.filter(row -> yes(row,flag)).isPresent())));
        result.put("stationary_objective_hold_legacy_canary_flag_requested",new Bool(config.stationaryObjectiveHoldCanaryRequested()));
        result.put("noncombat_sentinel_timeline_speed",new IntegerValue(BigInteger.valueOf(config.routeContactTimelineSpeed())));
        result.put("route_contact_effective_timeline_speed",new IntegerValue(BigInteger.valueOf(config.routeContactEffectiveTimelineSpeed())));
        result.put("noncombat_sentinel_high_speed_ab",new Bool(config.allowRouteContactHighSpeedAb()));
        independent.ifPresent(value -> result.put("independent_battle_speed_readiness",value)); return new Obj(result);
    }
    private static Set<OperationKey> operations(Set<String> values) { return values.stream().map(OperationKey::new).collect(java.util.stream.Collectors.toUnmodifiableSet()); }
    private static Arr strings(Iterable<String> values) { List<Value> rows = new ArrayList<>(); for (String value : values) rows.add(new Text(value)); return new Arr(rows); }
}
