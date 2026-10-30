package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.RequestIds;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneCodec;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumerCodec;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistoryCodec;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopePolicy;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual Java collection sequence over the sole guarded read transport. It does not implement another native client. */
public final class GovernanceCollector implements GovernanceObservationSupplier {
    public interface LifestyleReadPort {
        Read<Obj> formal(PlanningRequest request);
        Read<Obj> stockFocus(PlanningRequest request, String target);
    }
    @FunctionalInterface public interface RootReadPort { Read<Obj> read(PlanningRequest request); }
    @FunctionalInterface public interface CrownCooldownReadPort { Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> read(PlanningRequest request); }
    @FunctionalInterface public interface StateSupplier {
        Read<Durable> read(PlanningRequest request);
        default Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) {
            return new Unavailable<>("the actual Crown retry body decoder is not installed");
        }
        default Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {
            return new Unavailable<>("actual same-publication private Crown due proof is not installed");
        }
    }
    /** The composition root installs each exact migrated query definition. An absent definition is unavailable. */
    public record Reads(Optional<ReadContract<Obj>> root, Optional<ReadContract<Obj>> lifeFormal,
            Optional<ReadContract<Obj>> stockFocus, Optional<ReadContract<Obj>> councilFinalGates,
            Optional<ReadContract<Obj>> crownReadback, Optional<ReadContract<Obj>> coreCouncilComposition,
            Optional<ReadContract<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest>> crownCooldown) {
        public Reads {
            Objects.requireNonNull(root); Objects.requireNonNull(lifeFormal); Objects.requireNonNull(stockFocus);
            Objects.requireNonNull(councilFinalGates); Objects.requireNonNull(crownReadback);
            Objects.requireNonNull(coreCouncilComposition);
            Objects.requireNonNull(crownCooldown);
        }
    }
    private final PlanningReadPort port;
    private final OutcomeArchive archive;
    private final StateSupplier states;
    private final Reads reads;
    private final Optional<GovernanceBorrowedSession> borrowed;
    private final Optional<LifestyleReadPort> lifestyleReads;
    private final Optional<RootReadPort> rootReads;
    private final Optional<CrownCooldownReadPort> crownClocks;
    public GovernanceCollector(PlanningReadPort port, OutcomeArchive archive, StateSupplier states, Reads reads) {
        this.port = Objects.requireNonNull(port); this.archive = Objects.requireNonNull(archive);
        this.states = Objects.requireNonNull(states); this.reads = Objects.requireNonNull(reads);
        this.borrowed = Optional.empty();
        this.lifestyleReads = Optional.empty();
        this.rootReads = Optional.empty();
        this.crownClocks = Optional.empty();
    }
    /** The Root runtime uses this constructor while its sole writer Session is already live. */
    public GovernanceCollector(PlanningReadPort port, OutcomeArchive archive, StateSupplier states, Reads reads,
            GovernanceBorrowedSession borrowed) {
        this.port = Objects.requireNonNull(port); this.archive = Objects.requireNonNull(archive);
        this.states = Objects.requireNonNull(states); this.reads = Objects.requireNonNull(reads);
        this.borrowed = Optional.of(Objects.requireNonNull(borrowed));
        this.lifestyleReads = Optional.empty();
        this.rootReads = Optional.empty();
        this.crownClocks = Optional.empty();
    }
    public GovernanceCollector(PlanningReadPort port, OutcomeArchive archive, StateSupplier states, Reads reads,
            GovernanceBorrowedSession borrowed, LifestyleReadPort lifestyleReads) {
        this.port = Objects.requireNonNull(port); this.archive = Objects.requireNonNull(archive);
        this.states = Objects.requireNonNull(states); this.reads = Objects.requireNonNull(reads);
        this.borrowed = Optional.of(Objects.requireNonNull(borrowed));
        this.lifestyleReads = Optional.of(Objects.requireNonNull(lifestyleReads));
        this.rootReads = Optional.empty();
        this.crownClocks = Optional.empty();
    }
    /** Reuse the one actual campaign-root contract through its typed owner rather than minting another operation. */
    public GovernanceCollector(PlanningReadPort port, OutcomeArchive archive, StateSupplier states, Reads reads,
            GovernanceBorrowedSession borrowed, LifestyleReadPort lifestyleReads, RootReadPort rootReads) {
        this.port = Objects.requireNonNull(port); this.archive = Objects.requireNonNull(archive);
        this.states = Objects.requireNonNull(states); this.reads = Objects.requireNonNull(reads);
        this.borrowed = Optional.of(Objects.requireNonNull(borrowed)); this.lifestyleReads = Optional.of(Objects.requireNonNull(lifestyleReads));
        this.rootReads = Optional.of(Objects.requireNonNull(rootReads));
        this.crownClocks = Optional.empty();
    }
    public GovernanceCollector(PlanningReadPort port,OutcomeArchive archive,StateSupplier states,Reads reads,
            GovernanceBorrowedSession borrowed,LifestyleReadPort lifestyleReads,RootReadPort rootReads,CrownCooldownReadPort crownClocks) {
        this.port=Objects.requireNonNull(port);this.archive=Objects.requireNonNull(archive);this.states=Objects.requireNonNull(states);this.reads=Objects.requireNonNull(reads);
        this.borrowed=Optional.of(Objects.requireNonNull(borrowed));this.lifestyleReads=Optional.of(Objects.requireNonNull(lifestyleReads));this.rootReads=Optional.of(Objects.requireNonNull(rootReads));this.crownClocks=Optional.of(Objects.requireNonNull(crownClocks));
    }
    private Read<Obj> root(PlanningRequest request) { return rootReads.isPresent() ? rootReads.orElseThrow().read(request) : query(request, reads.root(), new Obj(Map.of())); }
    private Read<Obj> formal(PlanningRequest request) {
        return lifestyleReads.isPresent() ? lifestyleReads.orElseThrow().formal(request) : query(request, reads.lifeFormal(), new Obj(Map.of()));
    }
    private Read<Obj> stockFocus(PlanningRequest request, String target) {
        return lifestyleReads.isPresent() ? lifestyleReads.orElseThrow().stockFocus(request, target)
                : new Unavailable<>("actual same-Session LIFE state plus final-focus query producer is not installed");
    }
    @Override public Read<Durable> durable(PlanningRequest request) {
        Read<Durable> read = Objects.requireNonNull(states.read(request));
        if (read instanceof Known<Durable> known) known.value().bind(request);
        return read;
    }

    @Override public Read<Life> lifestyle(PlanningRequest request, String preferredFocus, boolean opening) {
        Read<Obj> root = root(request);
        if (root instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> rootKnown = (Known<Obj>) root;
        Obj historyRow = new Obj(Map.of()).with("command", new Text("query-campaign-root-context-v1")).with("ok", new Bool(true)).with("result", rootKnown.value());
        List<Value> sceneRows = new ArrayList<>(request.observations().history()); sceneRows.add(historyRow);
        Obj scene = new Obj(Map.of()).with("schema", new Text(ConstructionSceneCodec.SCENE_SCHEMA))
                .with("snapshot", request.observations().snapshot()).with("history", new Arr(sceneRows));
        var source = ConstructionSceneCodec.decodeScene(DriverJson.toNode(scene));
        var assessment = opening || !request.observations().bridgeCapabilities().contains(LifestyleScopePolicy.ALL_LIFESTYLE_CAPABILITY)
                ? LifestyleScopePolicy.sameFrameFeudalLifestyleScope(source) : LifestyleScopePolicy.sameFramePlayerLifestylePerkScope(source);
        Obj scope = object(parse(ConstructionSceneCodec.encodeRootScope(assessment.root())), "lifestyle root scope");
        if (assessment.root().status() != org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.RootScopeStatus.ADMITTED) {
            Obj notRequested = new Obj(Map.of()).with("status", new Text("not_requested_outside_current_admitted_scope"));
            Obj wrapper = new Obj(Map.of()).with("schema", new Text(LifestyleConsumerCodec.SCHEMA))
                    .with("baseline_plan", new Obj(Map.of()).with("selected_step", new Text("life-advance"))).with("scope", scope).with("query", Nil.INSTANCE)
                    .with("preferred_focus_target_key", new Text(preferredFocus)).with("allow_wartime_initial_focus", new Bool(opening));
            return new Known<>(new Life(LifestyleConsumerCodec.decode(encode(wrapper)), lifecycleHistory(request), notRequested), rootKnown.originals());
        }
        Read<Obj> raw = formal(request);
        if (raw instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> formal = (Known<Obj>) raw; Known<Obj> selected = formal;
        Value snapshot = formal.value().get("snapshot");
        boolean absent = snapshot instanceof Obj life && life.get("current_focus") instanceof Obj focus
                && new Text("absent").equals(focus.get("presence"));
        // The chosen target is queried last; comparing another target cannot authorize this one.
        if (opening || absent || !new Text("available").equals(formal.value().get("status"))) {
            Read<Obj> stock = stockFocus(request, preferredFocus);
            if (stock instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
            selected = (Known<Obj>) stock;
        }
        bindLife(request, selected.value());
        Obj wrapper = new Obj(Map.of()).with("schema", new Text(LifestyleConsumerCodec.SCHEMA))
                .with("baseline_plan", new Obj(Map.of()).with("selected_step", new Text("life-advance"))).with("scope", scope)
                .with("query", selected.value()).with("preferred_focus_target_key", new Text(preferredFocus))
                .with("allow_wartime_initial_focus", new Bool(opening));
        LifestyleConsumer.Request input = LifestyleConsumerCodec.decode(encode(wrapper));
        var history = lifecycleHistory(request);
        List<ExactRef> refs = new ArrayList<>(rootKnown.originals()); refs.addAll(formal.originals()); refs.addAll(selected.originals());
        return new Known<>(new Life(input, history, selected.value()), refs);
    }

    @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) {
        Read<Obj> wealthRead = stockFocus(request, LifestyleMinPolicy.WEALTH_FOCUS);
        if (wealthRead instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Read<Obj> martialRead = stockFocus(request, LifestyleMinPolicy.MARTIAL_FOCUS);
        if (martialRead instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> wealth = (Known<Obj>) wealthRead, martial = (Known<Obj>) martialRead;
        bindLife(request, wealth.value()); bindLife(request, martial.value());
        Obj snapshot = object(wealth.value().get("snapshot"), "opening snapshot");
        Value traits = snapshot.get("actor_traits");
        Obj evidence = new Obj(Map.of()).with("schema", new Text(LifestyleMinCodec.FIRST_FOCUS_SCHEMA))
                .with("wealth", focusObservation(wealth.value())).with("martial", focusObservation(martial.value()))
                .with("actor_traits", traits instanceof Obj found ? project(found, List.of("status", "observed_keys")) : Nil.INSTANCE)
                .with("at_peace", new Bool(!request.observations().warInProgress()));
        List<ExactRef> refs = new ArrayList<>(wealth.originals()); refs.addAll(martial.originals());
        return new Known<>(new OpeningComparison(LifestyleMinCodec.decodeFirstFocus(encode(evidence)), evidence), refs);
    }
    @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) {
        Read<Obj> raw = query(request, reads.councilFinalGates(), new Obj(Map.of()).with("position_key", new Text(position.key())));
        if (raw instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> known = (Known<Obj>) raw;
        return new Known<>(CouncilSelection.decode(request, position, known.value()), known.originals());
    }
    @Override public Read<Crown> crown(PlanningRequest request) {
        Read<Obj> raw = query(request, reads.crownReadback(), new Obj(Map.of()));
        if (raw instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> known = (Known<Obj>) raw;
        var readback = CrownAuthorityCodec.decodeReadback(encode(known.value())); var frame = readback.sourceFrame();
        var expected = request.before().frame();
        StrictJson.require(frame.queriedSnapshotId() != null && frame.queriedSnapshotId().equals(expected.snapshotId())
                && frame.queriedRevision().equals(expected.revision()) && frame.queriedNativeRevision().equals(expected.identity().nativeRevision())
                && frame.dateRaw().equals(expected.identity().dateRaw()) && frame.playerCharacterId().equals(expected.identity().player()),
                "Crown native quote crossed the complete planning frame");
        return new Known<>(new Crown(readback, known.value()), known.originals());
    }
    @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) {
        Read<Obj> raw = query(request, reads.coreCouncilComposition(), new Obj(Map.of()));
        if (raw instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> known = (Known<Obj>) raw;
        return new Known<>(CouncilSelection.decodeComposition(request, known.value()), known.originals());
    }
    @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) {
        Read<Obj> raw = root(request);
        if (raw instanceof Unavailable<Obj> unavailable) return new Unavailable<>(unavailable.reason());
        Known<Obj> known = (Known<Obj>) raw;
        Obj root = object(known.value().get("campaign_root_context"), "actual campaign root"); var frame = request.before().frame();
        StrictJson.require(new Text("available").equals(root.get("status"))
                && integer(root.get("snapshot_revision"), "root native revision").equals(frame.identity().nativeRevision())
                && integer(root.get("date_raw"), "root date").equals(frame.identity().dateRaw())
                && integer(root.get("player_character_id"), "root actor").equals(frame.identity().player()), "council root source drift");
        if (!(root.get("council") instanceof Obj council) || !(council.get("positions") instanceof Arr rows))
            return new Unavailable<>("current root did not publish council positions; absence is not an empty council");
        if (new Text("unavailable").equals(council.get("status")))
            return new Unavailable<>(text(council.get("unavailable_reason"), "root council unavailable reason"));
        StrictJson.require(new Text("available").equals(council.get("status")), "explicit root council status required");
        List<Seat> positions = new ArrayList<>();
        for (Value item : rows.items()) {
            Obj seat = object(item, "root council position"); String key = text(seat.get("position_key"), "position_key");
            for (CouncilSelection.Position position : CouncilSelection.Position.values()) if (position.key().equals(key)) {
                StrictJson.require(positions.stream().noneMatch(knownSeat -> knownSeat.position() == position), "duplicate root council position");
                Value value = seat.get("incumbent_character_id");
                StrictJson.require(value != null, "root incumbent field is missing, not an observed vacancy");
                positions.add(new Seat(position, value == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(value, "root incumbent"))));
            }
        }
        return new Known<>(new CouncilRoot(positions, known.value()), known.originals());
    }
    @Override public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) {
        var read = states.crownRetry(request, lawKey);
        if (read instanceof Known<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> known) {
            var frame = known.value().frame(); var current = request.before().frame();
            StrictJson.require(frame.context() != null && current.episodeRunId().equals(frame.context().episodeRunId())
                    && frame.playedCharacterObject() && current.identity().player().equals(frame.actorCharacterId())
                    && current.identity().dateRaw().equals(frame.dateRaw()) && lawKey.equals(known.value().lawKey()), "Crown retry state crossed the current actor/episode/date/target");
        }
        return read;
    }
    @Override public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) {
        var read = crownClocks.isPresent()?crownClocks.orElseThrow().read(request):query(request, reads.crownCooldown(), new Obj(Map.of()));
        if (read instanceof Known<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> known)
            StrictJson.require(known.value().dateRaw().equals(request.before().frame().identity().dateRaw()), "Crown cooldown source date drift");
        return read;
    }
    @Override public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {
        var read=states.crownRetryDue(request);
        if(read instanceof Known<CrownRetryDue.VerifiedDue> known)StrictJson.require(known.value().observed().equals(request.before())&&!known.value().authorizesAction(),"private Crown due crossed the actual planning frame or claims action authority");
        return read;
    }
    private <T> Read<T> query(PlanningRequest request, Optional<ReadContract<T>> installed, Obj arguments) {
        if (installed.isEmpty()) return new Unavailable<>("the exact Java governance query producer is not installed");
        ReadContract<T> contract = installed.orElseThrow();
        var input = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), contract.operation(), arguments, request.deadline());
        PlanningReadResult<T> read;
        try {
            read = borrowed.isPresent() ? borrowed.orElseThrow().use(request, session -> port.read(session, contract, input))
                    : port.read(contract, input);
        } catch (java.io.IOException unavailable) {
            return new Unavailable<>("same-writer governance read unavailable: " + unavailable.getMessage());
        }
        if (read instanceof PlanningReadResult.Unavailable<T> unavailable) return new Unavailable<>(unavailable.reason());
        PlanningReadResult.Known<T> known = (PlanningReadResult.Known<T>) read;
        bindReceipt(request, contract, known.receipt());
        try {
            ExactRef retained = borrowed.isPresent()
                    ? borrowed.orElseThrow().use(request, session -> archive.inSession(session, bound -> bound.preserve(known.receipt().original())))
                    : archive.preserve(known.receipt().original());
            return new Known<>(known.value(), List.of(retained));
        } catch (java.io.IOException unavailable) {
            return new Unavailable<>("same-writer governance archive unavailable: " + unavailable.getMessage());
        }
    }
    private static void bindReceipt(PlanningRequest request, ReadContract<?> contract, PlanningReadReceipt receipt) {
        StrictJson.require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(),
                "native query ACK has no accepted original result token");
        StrictJson.require(receipt.request().before().equals(request.before()) && receipt.request().source().equals(request.source())
                && receipt.request().sessionId().equals(request.sessionId()) && receipt.contractId().equals(contract.contractId()), "query receipt identity differs");
        for (var guard : List.of(receipt.before(), receipt.after())) {
            StrictJson.require(guard.binding().observed().equals(request.before()) && guard.binding().source().equals(request.source())
                    && guard.binding().sessionId().equals(request.sessionId()) && guard.paused() && guard.mapReady() && guard.playerAlive(),
                    "governance read lost the same paused semantic frame");
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()), "full semantic read binding drift");
    }
    static void bindLife(PlanningRequest request, Obj query) {
        if (!List.of(new Text("available"), new Text("stock_focus_available")).contains(query.get("status"))) return;
        Obj source = object(query.get("source_frame"), "LIFE source frame"), snapshot = object(query.get("snapshot"), "LIFE snapshot");
        var frame = request.before().frame();
        StrictJson.require(new Text(frame.snapshotId()).equals(source.get("snapshot_id"))
                && integer(source.get("revision"), "source revision").equals(frame.revision())
                && integer(source.get("native_revision"), "source native revision").equals(frame.identity().nativeRevision())
                && integer(source.get("date_raw"), "source date").equals(frame.identity().dateRaw()), "LIFE source frame drift");
        StrictJson.require(new Text(frame.snapshotId()).equals(snapshot.get("snapshot_id"))
                && new Text(frame.episodeRunId()).equals(snapshot.get("episode_run_id"))
                && integer(snapshot.get("public_revision"), "LIFE public revision").equals(frame.revision())
                && integer(snapshot.get("native_revision"), "LIFE native revision").equals(frame.identity().nativeRevision())
                && integer(snapshot.get("date_raw"), "LIFE date").equals(frame.identity().dateRaw())
                && integer(snapshot.get("player_character_id"), "LIFE actor").equals(frame.identity().player()), "LIFE payload frame drift");
        verifyLifestyleSourceFacts(request.before(),query);
    }
    /** Persisted fact siblings are projections of retained raw native inputs, never a second input dialect. */
    public static void verifyLifestyleSourceFacts(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity observed,Obj query) {
        var id=observed.frame().identity();
        var binding=org.xar.ck3.control.governance.lifestylesource.LifestyleSourceFacts.Binding.exact("native:"+id.nativeRevision(),id.nativeRevision(),id.dateRaw().intValueExact(),id.player(),Optional.empty());
        var raw=StrictJson.parse(encode(query));
        String predicate=org.xar.ck3.control.governance.lifestylesource.LifestylePredicateSourceCodec.WIRE_KEY;
        String predicateFacts=org.xar.ck3.control.governance.lifestylesource.LifestylePredicateSourceCodec.FACTS_KEY;
        String frontier=org.xar.ck3.control.governance.lifestylesource.LifestyleTriggerFrontierCodec.WIRE_KEY;
        String frontierFacts=org.xar.ck3.control.governance.lifestylesource.LifestyleTriggerFrontierCodec.FACTS_KEY;
        if(raw.hasNonNull(predicate))org.xar.ck3.control.governance.lifestylesource.LifestylePredicateSourceCodec.verifyFacts(raw.get(predicateFacts),raw.get(predicate),binding);
        else StrictJson.require(!raw.has(predicateFacts),"missing/null predicate input cannot acquire a facts sibling");
        if(raw.hasNonNull(frontier))org.xar.ck3.control.governance.lifestylesource.LifestyleTriggerFrontierCodec.verifyFacts(raw.get(frontierFacts),raw.get(frontier),binding);
        else StrictJson.require(!raw.has(frontierFacts),"missing/null frontier input cannot acquire a facts sibling");
    }
    private static Obj history(PlanningRequest request) {
        List<Value> rows = new ArrayList<>();
        for (Obj row : request.observations().history()) {
            Value command = row.get("command"), result = row.get("result");
            if (new Text("auto-turn").equals(command) && result instanceof Obj root && root.get("auto_turn") instanceof Obj turn) {
                command = turn.get("selected_step"); if (turn.get("result") instanceof Obj nested) result = nested;
            }
            // Canonical Java source bridge: if a SUBMIT row has a valid DriverActionHistorySource, project it as RECEIPT
            if ((new Text("private-select-player-lifestyle-stock-focus-v1").equals(command) || new Text("private-select-player-lifestyle-perk-v1").equals(command))
                    && row.get("ok") instanceof Bool ok && ok.value() && result instanceof Obj res
                    && (new Text("private-select-player-lifestyle-stock-focus-v1").equals(command) && new Text("focus").equals(res.get("kind"))
                        || new Text("private-select-player-lifestyle-perk-v1").equals(command) && new Text("perk").equals(res.get("kind")))) {
                Value sourceVal = row.get("java_action_history_source");
                if (sourceVal instanceof Obj sourceObj) {
                    try {
                        var raw = RawJson.fullMaterial(DriverJson.encode(sourceObj));
                        var source = DriverActionHistoryCodec.decode(raw);
                        if (source.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                                && source.material() instanceof DriverActionHistoryCodec.Legacy legacy
                                && legacy.recording() == DriverActionHistoryCodec.Recording.RETURNED
                                && legacy.result().isPresent() && legacy.error().isEmpty()) {
                            String expectedId = RequestIds.forActionBody(source.bodySha256());
                            if (res.get("action_request_id") instanceof Text id && id.value().equals(expectedId)
                                    && res.get("status") instanceof Text status && status.value().equals("applied")
                                    && res.get("step") instanceof Text step && step.value().equals("private-query-player-lifestyle-receipt-v1")
                                    && res.get("postcondition_verified") instanceof Bool pc && pc.value()
                                    && res.get("episode_run_id") instanceof Text ep && ep.value().equals(request.before().frame().episodeRunId())) {
                                command = new Text("private-query-player-lifestyle-receipt-v1");
                            }
                        }
                    } catch (IllegalArgumentException ignored) { /* conservative decline */ }
                }
            }
            boolean relevant = List.of(new Text("private-select-player-lifestyle-perk-v1"), new Text("private-select-player-lifestyle-stock-focus-v1"),
                    new Text("private-query-player-lifestyle-receipt-v1")).contains(command);
            rows.add(new Obj(Map.of()).with("command", command == null ? Nil.INSTANCE : command).with("ok", row.get("ok") == null ? Nil.INSTANCE : row.get("ok"))
                    .with("result_json", relevant && result != null ? new Text(new String(encode(result), StandardCharsets.UTF_8)) : Nil.INSTANCE));
        }
        return new Obj(Map.of()).with("schema", new Text(LifestyleHistoryCodec.SCHEMA)).with("episode_run_id", new Text(request.before().frame().episodeRunId())).with("history", new Arr(rows));
    }
    static org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory.Input lifecycleHistory(PlanningRequest request) {
        return LifestyleHistoryCodec.decode(encode(history(request)));
    }
    private static Obj focusObservation(Obj query) {
        Value value = query.get("focus_query"); if (!(value instanceof Obj)) value = query.get("focus");
        Obj focus = object(value, "observed stock focus");
        Obj result = project(focus, List.of("status", "native_legal", "target_key", "target_lifestyle_key", "target_lifestyle_progress"));
        if (result.get("target_lifestyle_progress") instanceof Obj progress)
            result = result.with("target_lifestyle_progress", project(progress, List.of("presence", "xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points")));
        return result;
    }
    private static Obj project(Obj source, List<String> fields) {
        Obj result = new Obj(Map.of()); for (String field : fields) if (source.get(field) != null) result = result.with(field, source.get(field)); return result;
    }
}
