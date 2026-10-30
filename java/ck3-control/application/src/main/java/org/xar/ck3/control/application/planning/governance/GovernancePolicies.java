package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real ordinary producers. Query collection, pure decisions, proposals and actual receipts remain separate stages. */
public final class GovernancePolicies {
    public static final String EFFECT_SCHEMA = "xar.java.governance-independent-effect/v1";
    public static final OperationKey FOCUS = new OperationKey("private-select-player-lifestyle-stock-focus-v1");
    public static final OperationKey PERK = new OperationKey("private-select-player-lifestyle-perk-v1");
    public static final OperationKey COUNCIL = new OperationKey("private-assign-councillor-v1");
    public static final OperationKey CORE_COUNCIL = new OperationKey("assign-councillor-v1");
    public static final OperationKey CROWN = new OperationKey("enact-realm-law-crown-v1-private");
    private GovernancePolicies() { }

    private abstract static class Policy implements OrdinaryPolicy {
        final GovernanceObservationSupplier supplier;
        private final ExactRef source;
        private final PlanningStage stage;
        Policy(GovernanceObservationSupplier supplier, ExactRef source, PlanningStage stage) {
            this.supplier = Objects.requireNonNull(supplier); this.source = Objects.requireNonNull(source); this.stage = stage;
            StrictJson.require(source.bytes() > 0, "actual Java governance producer source required");
        }
        @Override public PlanningStage stage() { return stage; }
        @Override public ExactRef implementationSource() { return source; }
        static Decision missing(String reason) { return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, reason); }
        static boolean advance(Draft previous) { return previous.command().filter(command -> command.operation().value().equals("life-advance")).isPresent(); }
        static CadenceModels.Frame frame(PlanningRequest request) {
            var frame = request.before().frame(); return new CadenceModels.Frame(frame.episodeRunId(), frame.identity().dateRaw(), frame.identity().nativeRevision());
        }
        static Obj annotation(Draft previous, String name, Value evidence) { return previous.detail().with(name, evidence); }
        static Decision annotated(Draft previous, Obj detail, String reason) {
            return new Replace(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(), previous.purpose(), previous.domain(), detail), reason);
        }
        static Obj cadenceIntent(CadenceModels.State before, CadenceModels.Domain domain, PlanningRequest request, Obj detail) {
            return GovernanceCadencePublication.append(detail, domain, request, before);
        }
        static boolean deferred(Durable state, CadenceModels.Domain domain, PlanningRequest request) {
            return OptionalCheckCadence.deferred(state.cadence().orElseThrow(), domain, frame(request)).isPresent();
        }
        static Decision pending(DomainState state) {
            return new Wait(state.status() == DomainStatus.UNKNOWN ? "governance state is UNKNOWN; only original reconciliation is permitted"
                    : "retain original governance intent for independent material receipt; never submit it again");
        }
    }

    public static final class Lifestyle extends Policy {
        public Lifestyle(GovernanceObservationSupplier supplier, ExactRef source) { super(supplier, source, PlanningStage.LIFESTYLE); }
        @Override public Decision evaluate(PlanningRequest request, Draft previous) {
            boolean deferrable = previous.purpose() == Purpose.READ_ONLY && previous.command().filter(command ->
                    command.operation().value().equals("query-campaign-root-context-v1")
                    || request.observations().warInProgress() && command.operation().value().startsWith("query-")).isPresent();
            boolean blockedWar = previous.command().isEmpty() && previous.phase().startsWith("native_war");
            if (!(advance(previous) || deferrable || blockedWar)) return new NotApplicable("existing earlier action retains ordinary precedence");
            Read<Durable> durableRead = supplier.durable(request);
            if (durableRead instanceof Unavailable<Durable> unavailable) return missing(unavailable.reason());
            Durable state = ((Known<Durable>) durableRead).value(); state.bind(request);
            if (state.cadence().isEmpty()) return missing("actual optional cadence body is unimported");
            var originalHistory = GovernanceCollector.lifecycleHistory(request);
            if (LifestyleHistory.select(originalHistory).status() != LifestyleHistory.Status.CLEAR)
                return new Wait("the original pending LIFE action bypasses optional cooldown and must be reconciled without another query or submission");
            if (deferred(state, CadenceModels.Domain.LIFESTYLE, request)) return new Keep("existing optional lifestyle cooldown remains due later");
            Read<Life> read = supplier.lifestyle(request, LifestyleMinPolicy.WEALTH_FOCUS, false);
            if (read instanceof Unavailable<Life> unavailable) return missing(unavailable.reason());
            Life life = ((Known<Life>) read).value(); var history = LifestyleHistory.select(life.history());
            if (history.status() != LifestyleHistory.Status.CLEAR) return new Wait("the sole lifestyle history reducer retains an original pending or uncertain receipt");
            LifestyleConsumer.Outcome outcome = LifestyleConsumer.consumeWithHistory(life.input(), originalHistory);
            Obj detail = annotation(previous, "lifestyle_original_query", life.originalQuery());
            if (outcome.recommendation() != null) detail = detail.with("lifestyle_decision", parse(LifestyleMinCodec.encode(outcome.recommendation())));
            return switch (outcome.route()) {
                case PERK_SUBMIT, FOCUS_SUBMIT -> selectedLife(request, previous, life, outcome, detail, false);
                case KEEP_BASELINE, EDUCATION_CONTINUE -> annotated(previous, detail, "existing typed LIFE scope/education consumer continued the original route");
                case NO_LEGAL_MINIMUM -> annotated(previous, cadenceIntent(state.cadence().orElseThrow(), CadenceModels.Domain.LIFESTYLE, request, detail),
                        "complete native LIFE no-action read; cadence publication is an intent for the sole writer");
                case QUERY_ROOT -> new Wait("LIFE scope still needs its original same-frame root query");
                default -> deferrable || blockedWar ? annotated(previous, detail, "preserve the original read/war result with unavailable LIFE evidence")
                        : new Wait("LIFE action lacks complete source-bound final legality");
            };
        }
    }

    public static final class Opening extends Policy {
        public Opening(GovernanceObservationSupplier supplier, ExactRef source) { super(supplier, source, PlanningStage.OPENING_LIFESTYLE_FOCUS); }
        @Override public Decision evaluate(PlanningRequest request, Draft previous) {
            if (!request.observations().initialLifestyleFocusRequired()) return new NotApplicable("opening focus is not required by this episode");
            Read<Durable> durableRead = supplier.durable(request);
            if (durableRead instanceof Unavailable<Durable> unavailable) return missing(unavailable.reason());
            Durable state = ((Known<Durable>) durableRead).value(); state.bind(request); if (state.opening().isEmpty()) return missing("actual persistent opening gate producer is not installed"); OpeningGate gate = state.opening().orElseThrow();
            if (!gate.episodeRunId().equals(request.before().frame().episodeRunId())
                    || !gate.dateRaw().equals(request.before().frame().identity().dateRaw())) return new Wait("opening episode/date changed before the source-bound gate was consumed");
            if (gate.stage() == OpeningStage.COMPLETE) return new Wait("opening gate completion must be installed by the sole writer before ordinary planning resumes");
            if (LifestyleHistory.select(GovernanceCollector.lifecycleHistory(request)).status() != LifestyleHistory.Status.CLEAR && gate.action().isEmpty())
                return new Wait("an original opening LIFE action remains unresolved before any current-focus query");
            if (gate.action().isPresent()) {
                var original = gate.action().orElseThrow();
                var consumed = original.command().before().game().equals(request.before().game())
                        ? GovernanceReceipts.consumeOpeningSameGame(original, request, gate.checkpoint())
                        : GovernanceReceipts.consume(original, request, gate.checkpoint(), true);
                if (consumed.status() != GovernanceReceipts.Status.CONSUMED) return new Wait(consumed.reason());
                Obj intent = new Obj(Map.of()).with("opening_required_gate_intent", new Text(gate.checkpoint().isPresent()
                        ? "complete_after_receipt_consumption_and_checkpoint" : "complete_after_receipt_consumption"))
                        .with("action_id", new Text(consumed.original().command().actionId()));
                if (gate.checkpoint().isPresent()) intent = intent.with("checkpoint_receipt_path",
                        new Text(gate.checkpoint().orElseThrow().actualReceipt().path()));
                return new Replace(new Draft("java-opening-focus-v1", "initial_lifestyle_focus_consumption", consumed.reason(), Kind.OPENING_FOCUS,
                        Optional.empty(), Purpose.READ_ONLY, Optional.of(Domain.lifestyle), intent), consumed.reason());
            }
            Read<Life> firstRead = supplier.lifestyle(request, LifestyleMinPolicy.WEALTH_FOCUS, true);
            if (firstRead instanceof Unavailable<Life> unavailable) return missing(unavailable.reason());
            Life first = ((Known<Life>) firstRead).value();
            if (LifestyleHistory.select(first.history()).status() != LifestyleHistory.Status.CLEAR)
                return new Wait("submitted opening focus takes precedence over observing its now-present focus");
            if (existingFocus(first.originalQuery())) {
                Obj evidence = annotation(previous, "initial_lifestyle_focus_existing", first.originalQuery())
                        .with("opening_required_gate_intent", new Text("consume_verified_existing_focus_on_following_turn"));
                return new Replace(new Draft("java-opening-focus-v1", "initial_lifestyle_focus_already_present", "existing focus and exact XP/points observed",
                        Kind.OPENING_FOCUS, Optional.empty(), Purpose.READ_ONLY, Optional.of(Domain.lifestyle), evidence), "existing focus does not authorize another focus submission");
            }
            Read<OpeningComparison> comparisonRead = supplier.openingComparison(request);
            if (comparisonRead instanceof Unavailable<OpeningComparison> unavailable) return missing(unavailable.reason());
            OpeningComparison comparison = ((Known<OpeningComparison>) comparisonRead).value();
            var choice = LifestyleMinPolicy.chooseFirstFocus(comparison.input());
            if (!choice.selected()) return new Wait("opening comparison has no observed native-legal wealth or martial target");
            Read<Life> selectedRead = supplier.lifestyle(request, choice.targetKey(), true);
            if (selectedRead instanceof Unavailable<Life> unavailable) return missing(unavailable.reason());
            Life selected = ((Known<Life>) selectedRead).value();
            var outcome = LifestyleConsumer.consumeWithHistory(selected.input(), selected.history());
            if (outcome.route() != LifestyleConsumer.Route.FOCUS_SUBMIT) return new Wait("the exact selected opening target lacks the last fresh final-legal query");
            Obj detail = annotation(previous, "opening_first_focus_comparison", parse(LifestyleMinCodec.encode(choice)));
            return selectedLife(request, previous, selected, outcome, detail, true);
        }
    }

    public static final class Council extends Policy {
        public Council(GovernanceObservationSupplier supplier, ExactRef source) { super(supplier, source, PlanningStage.COUNCIL); }
        /** Called by OrdinaryCorePolicy at the original Council19 point, before cross-focus/marriage. */
        public Decision evaluateCoreCouncil(PlanningRequest request, Draft previous) {
            Read<Durable> durableRead = supplier.durable(request);
            if (durableRead instanceof Unavailable<Durable> unavailable) return missing(unavailable.reason());
            Durable state = ((Known<Durable>) durableRead).value(); state.bind(request);
            if (state.council().isEmpty()) return missing("actual council domain body is unimported");
            if (state.council().orElseThrow().status() != DomainStatus.KNOWN_CLEAR) return pending(state.council().orElseThrow());
            if (!request.observations().bridgeCapabilities().containsAll(Set.of("game.query.council-composition-candidates-v1", "game.action.assign-councillor-v1")))
                return new NotApplicable("the original Council19 capability pair is absent");
            if (!request.observations().paused()) return new Wait("pause-map is required before the original Council19 read");
            Read<CouncilSelection.Query> read = supplier.coreCouncil(request);
            if (read instanceof Unavailable<CouncilSelection.Query> unavailable) return missing(unavailable.reason());
            var decision = CouncilSelection.choose(((Known<CouncilSelection.Query>) read).value());
            if (decision.outcome() == CouncilSelection.Outcome.ASSIGN_REQUIRED || decision.outcome() == CouncilSelection.Outcome.REPLACE_REQUIRED)
                return selectedCouncil(request, previous, decision, true);
            return annotated(previous, previous.detail().with("council_observation_consumed", new Bool(true)),
                    "original steward decision consumed; ordinary core continues without repeating Council19");
        }
        @Override public Decision evaluate(PlanningRequest request, Draft previous) {
            if (!advance(previous)) return new NotApplicable("normal council runs only before an otherwise selected life advance");
            Read<Durable> durableRead = supplier.durable(request);
            if (durableRead instanceof Unavailable<Durable> unavailable) return missing(unavailable.reason());
            Durable state = ((Known<Durable>) durableRead).value(); state.bind(request);
            if (state.cadence().isEmpty()) return missing("actual optional cadence body is unimported");
            if (state.council().isEmpty()) return missing("actual council domain body is unimported");
            if (state.council().orElseThrow().status() != DomainStatus.KNOWN_CLEAR) return pending(state.council().orElseThrow());
            if (!request.observations().paused() || !request.observations().mapReady() || request.observations().foregroundPresent())
                return new Keep("the original council ordinary scene is unavailable");
            if (deferred(state, CadenceModels.Domain.COUNCIL, request)) return new Keep("council optional review is deferred by the existing cadence");
            Obj detail = previous.detail().with("council_original_state", state.council().orElseThrow().originalBody()); boolean complete = true;
            // The actual legacy producer retains validated FOLLOW JSON; it does not manufacture an ActionReceipt.
            Value retainedApplied = state.council().orElseThrow().originalBody().get("applied");
            if (retainedApplied instanceof Obj applied && new Text("applied").equals(applied.get("status"))
                    && applied.get("next_turn_consumed") instanceof Bool
                    && new Text(request.before().frame().episodeRunId()).equals(applied.get("episode_run_id"))
                    && new Text(request.before().frame().snapshotId()).equals(applied.get("next_turn_snapshot_id"))
                    && new IntegerValue(request.before().frame().identity().nativeRevision()).equals(applied.get("next_turn_native_revision"))
                    && new IntegerValue(request.before().frame().identity().dateRaw()).equals(applied.get("next_turn_date_raw")))
                detail = detail.with("council_receipt_consumed", applied);
            List<CouncilSelection.Position> presentRoles = null;
            if (state.council().orElseThrow().latest().isPresent() && state.council().orElseThrow().latest().orElseThrow().outcome() == org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                var receipt = state.council().orElseThrow().latest().orElseThrow();
                var consumption = GovernanceReceipts.consume(receipt, request, Optional.empty(), false);
                if (consumption.status() != GovernanceReceipts.Status.CONSUMED)
                    return annotated(previous, detail.with("council_receipt_consumption", new Text(consumption.status().name())), consumption.reason());
                String key = text(receipt.command().arguments().get("position_key"), "applied council position");
                var role = java.util.Arrays.stream(CouncilSelection.Position.values()).filter(value -> value.key().equals(key)).findFirst().orElseThrow();
                var rootRead = supplier.councilRoot(request); var queryRead = supplier.council(request, role);
                if (rootRead instanceof Unavailable<CouncilRoot> unavailable) return missing(unavailable.reason());
                if (queryRead instanceof Unavailable<CouncilSelection.Query> unavailable) return technicalRead(request, previous, state, detail, unavailable, role);
                CouncilRoot root = ((Known<CouncilRoot>) rootRead).value(); var query = ((Known<CouncilSelection.Query>) queryRead).value();
                Optional<BigInteger> holder = root.seats().stream().filter(seat -> seat.position() == role).findFirst().flatMap(Seat::incumbent);
                if (!query.available() || !holder.equals(query.incumbent())) return new Wait("independent current root and council position do not agree on the applied seat");
                boolean persists = holder.filter(id -> id.equals(integer(receipt.command().arguments().get("candidate_character_id"), "applied candidate"))).isPresent();
                detail = detail.with("council_receipt_consumed", new Obj(Map.of()).with("action_id", new Text(receipt.command().actionId())).with("next_turn_consumed", new Bool(persists))
                        .with("current_root", root.original()).with("current_query", query.original()));
                presentRoles = root.seats().stream().map(Seat::position).toList();
                detail = projectJobProgress(request, detail, root);
            }
            for (CouncilSelection.Position role : CouncilSelection.Position.values()) {
                if (role != CouncilSelection.Position.STEWARD) {
                    if (presentRoles == null) {
                        var positions = supplier.councilRoot(request);
                        if (positions instanceof Unavailable<CouncilRoot> unavailable)
                            return annotated(previous, detail.with("council_root_unavailable", new Text(unavailable.reason())), "preserve steward evidence without inventing other seats");
                        presentRoles = ((Known<CouncilRoot>) positions).value().seats().stream().map(Seat::position).toList();
                        detail = projectJobProgress(request, detail, ((Known<CouncilRoot>) positions).value());
                    }
                    if (!presentRoles.contains(role)) continue;
                }
                Read<CouncilSelection.Query> read = supplier.council(request, role);
                if (read instanceof Unavailable<CouncilSelection.Query> unavailable) return technicalRead(request, previous, state, detail, unavailable, role);
                var query = ((Known<CouncilSelection.Query>) read).value(); var decision = CouncilSelection.choose(query);
                complete &= query.available(); detail = detail.with("council_" + role.name().toLowerCase(java.util.Locale.ROOT) + "_query", query.original());
                if (decision.outcome() == CouncilSelection.Outcome.ASSIGN_REQUIRED || decision.outcome() == CouncilSelection.Outcome.REPLACE_REQUIRED)
                    return selectedCouncil(request, new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(), previous.purpose(), previous.domain(), detail), decision, false);
            }
            if (complete) detail = cadenceIntent(state.cadence().orElseThrow(), CadenceModels.Domain.COUNCIL, request, detail);
            return annotated(previous, detail, "retained all steward/chancellor/chaplain observations; no legal strict skill improvement");
        }
    }

    private static Obj projectJobProgress(PlanningRequest request, Obj detail, CouncilRoot root) {
        Obj context = object(root.original().get("campaign_root_context"), "actual current Council root for job observations");
        var nativeRoot = GovernanceDomainDocument.object(org.xar.ck3.control.application.driver.DriverJson.toNode(context));
        List<Value> observations = new ArrayList<>();
        for (CouncilSelection.Position position : CouncilSelection.Position.values()) {
            var progress = GovernanceDomainDocument.jobProgress(nativeRoot, request.before().frame().episodeRunId(), position.key(), Optional.empty());
            observations.add(parse(StrictJson.canonical(progress)));
        }
        return detail.with("council_job_progress_observations", new Arr(observations));
    }

    private static Decision technicalRead(PlanningRequest request, Draft previous, Durable state, Obj detail,
            Unavailable<CouncilSelection.Query> unavailable, CouncilSelection.Position role) {
        if (unavailable.councilTechnicalReadFailure().isEmpty()) return Policy.missing(unavailable.reason());
        var failure = unavailable.councilTechnicalReadFailure().orElseThrow();
        if (!Policy.advance(previous) || state.council().isEmpty() || state.council().orElseThrow().status() != DomainStatus.KNOWN_CLEAR)
            return Policy.missing(unavailable.reason());
        try { failure.requireCurrent(request, role); }
        catch (IllegalArgumentException invalid) { return Policy.missing(unavailable.reason() + "; actual technical read proof unavailable: " + invalid.getMessage()); }
        Obj intent = GovernanceCadencePublication.appendCouncilTechnical(detail, request, state.cadence().orElseThrow(), failure.diagnostic());
        var plan = GovernanceCadencePublication.fromDetail(intent).orElseThrow();
        var due = GovernanceCadencePublication.reduce(plan).row(CadenceModels.Domain.COUNCIL).nextDueDateRaw().orElseThrow();
        Obj deferred = new Obj(Map.of()).with("status", new Text("readonly_unavailable_deferred")).with("read_only", new Bool(true))
                .with("business_submission", new Bool(false)).with("action_credit", new Bool(false)).with("no_action_counter_incremented", new Bool(false))
                .with("evidence_path", new Text(failure.diagnostic().path())).with("next_due_date_raw", new IntegerValue(due));
        return Policy.annotated(previous, intent.with("council_observation_consumed", new Bool(false))
                .with("council_observation_status", new Text("technical_unavailable")).with("council_technical_defer", deferred),
                "retain the original life advance after the actual same-frame read-only Council failure; no action or no-action credit");
    }

    public static final class Crown extends Policy {
        public Crown(GovernanceObservationSupplier supplier, ExactRef source) { super(supplier, source, PlanningStage.CROWN_AUTHORITY); }
        @Override public Decision evaluate(PlanningRequest request, Draft previous) {
            if (!advance(previous)) return new NotApplicable("Crown fallback runs only after earlier ordinary choices retain advance");
            Read<Durable> durableRead = supplier.durable(request);
            if (durableRead instanceof Unavailable<Durable> unavailable) return missing(unavailable.reason());
            Durable state = ((Known<Durable>) durableRead).value(); state.bind(request);
            if (state.cadence().isEmpty()) return missing("actual optional cadence body is unimported");
            if (state.crown().isEmpty()) return missing("actual crown domain body is unimported");
            if (state.crown().orElseThrow().status() != DomainStatus.KNOWN_CLEAR) return pending(state.crown().orElseThrow());
            Read<CrownRetryDue.VerifiedDue> due = supplier.crownRetryDue(request);
            boolean cadenceDeferred = deferred(state, CadenceModels.Domain.CROWN, request);
            boolean atDueOverride = cadenceDeferred && due instanceof Known<CrownRetryDue.VerifiedDue> known
                    && known.value().currentlyDue(request.before());
            if (cadenceDeferred && !atDueOverride)
                return new Keep("the existing Crown optional cadence retains its future date without a verified due native retry");
            // Only query timing changes. Actual native quotes and enactment final terms retain every legality gate.
            Read<GovernanceObservationSupplier.Crown> read = supplier.crown(request);
            if (read instanceof Unavailable<GovernanceObservationSupplier.Crown> unavailable) return missing(unavailable.reason());
            GovernanceObservationSupplier.Crown crown = ((Known<GovernanceObservationSupplier.Crown>) read).value();
            var choice = CrownAuthorityPolicy.choose(crown.readback());
            Obj detail = previous.detail().with("crown_original_state", state.crown().orElseThrow().originalBody()).with("crown_readback", crown.originalReadback()).with("crown_decision", parse(CrownAuthorityCodec.encodeChoice(choice)));
            if (state.crown().orElseThrow().latest().isPresent() && state.crown().orElseThrow().latest().orElseThrow().outcome() == org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                var receipt = state.crown().orElseThrow().latest().orElseThrow();
                var consumption = GovernanceReceipts.consume(receipt, request, Optional.empty(), false);
                if (consumption.status() != GovernanceReceipts.Status.CONSUMED)
                    return annotated(previous, detail.with("crown_receipt_consumption", new Text(consumption.status().name())), consumption.reason());
                String law = text(receipt.command().arguments().get("law_key"), "resolved Crown law");
                detail = detail.with("crown_result_consumed", new Obj(Map.of()).with("action_id", new Text(receipt.command().actionId()))
                        .with("next_turn_consumed", new Bool(law.equals(crown.readback().activeLawKey())))
                        .with("next_turn_effective_law_key", new Text(crown.readback().activeLawKey())).with("material_receipt_retained", new Bool(true)));
            }
            if (choice.status() == CrownAuthorityPolicy.Status.NATIVE_BLOCKED && choice.lawKey() != null)
                detail = retry(request, choice.lawKey(), detail);
            if (choice.status() != CrownAuthorityPolicy.Status.READY)
                return annotated(previous, crown.readback().available() && !atDueOverride ? cadenceIntent(state.cadence().orElseThrow(), CadenceModels.Domain.CROWN, request, detail) : detail,
                        "original Crown quote did not select a native-final-legal stock upgrade");
            Obj arguments = new Obj(Map.of()).with("readback", crown.originalReadback()).with("law_key", new Text(choice.lawKey()))
                    .with("choice", parse(CrownAuthorityCodec.encodeChoice(choice)));
            List<ExpectedValue> expected = new ArrayList<>(); expected.add(new ExpectedText(new FieldKey("crown.effective_law_key"), choice.lawKey()));
            for (var amount : choice.quotedPostBalancesRaw()) expected.add(new ExpectedText(new FieldKey("crown.balance_" + amount.currency().wire() + "_raw"), amount.amountRaw().toString()));
            return selected(request, CROWN, arguments, expected, Set.of(request.before().frame().identity().player()), Set.of("realm-law:crown_authority"),
                    Optional.empty(), Kind.ORDINARY, "crown_ordinary_typed_enact", "enact the selected source-backed Crown upgrade using its exact native quote", detail);
        }
        private Obj retry(PlanningRequest request, String lawKey, Obj detail) {
            var retained = supplier.crownRetry(request, lawKey);
            if (retained instanceof Unavailable<CrownRetryCodec.MatchRequest> unavailable) {
                // No current-Game proof disables only cache reuse. It cannot prevent the first fresh query.
                detail = detail.with("crown_retry_cache_unavailable_reason", new Text(unavailable.reason()));
            } else {
                var state = ((Known<CrownRetryCodec.MatchRequest>) retained).value();
                var cached = CrownRetryPolicy.matchingFutureRetry(state.frame(), state.state(), lawKey);
                if (cached.isPresent()) return detail.with("crown_calendar_retry", parse(CrownRetryCodec.encodeMatch(cached)))
                        .with("crown_calendar_retry_source", new Text("reused_hint"));
            }
            var observed = supplier.crownCooldown(request);
            if (observed instanceof Unavailable<CrownCooldownCodec.ClockRequest> unavailable)
                return detail.with("crown_cooldown_unavailable_reason", new Text(unavailable.reason()));
            var raw = ((Known<CrownCooldownCodec.ClockRequest>) observed).value();
            var clock = CrownCooldown.interpret(raw.observation(), raw.dateRaw(), raw.turnTick());
            detail = detail.with("crown_cooldown_clock", parse(CrownCooldownCodec.encode(clock)));
            var current = request.before(); var frame = current.frame(); var identity = frame.identity();
            StrictJson.require(raw.dateRaw().equals(identity.dateRaw()), "fresh Crown cooldown must bind this actual current date");
            if (!clock.calendarDeadlineReady() || clock.queryRetryDateRaw() == null
                    || clock.queryRetryDateRaw().compareTo(identity.dateRaw()) <= 0)
                return detail.with("crown_calendar_retry", Nil.INSTANCE);
            Obj hint = new Obj(Map.of()).with("source_context", new Obj(Map.of()).with("bridge_pid", new IntegerValue(BigInteger.valueOf(current.game().pid())))
                            .with("episode_run_id", new Text(frame.episodeRunId()))).with("actor_character_id", new IntegerValue(identity.player()))
                    .with("law_key", new Text(lawKey)).with("observed_date_raw", new IntegerValue(raw.dateRaw()))
                    .with("retry_date_raw", new IntegerValue(clock.queryRetryDateRaw()));
            return detail.with("crown_calendar_retry", hint).with("crown_calendar_retry_source", new Text("current_query"))
                    .with("crown_required_retry_intent", new Obj(Map.of()).with("after", hint).with("publication_authority", new Text("sole_continuity_writer")));
        }
    }

    private static Decision selectedLife(PlanningRequest request, Draft previous, Life life, LifestyleConsumer.Outcome outcome, Obj detail, boolean opening) {
        String target; String lifestyle; boolean perk;
        if (outcome.recommendation() instanceof LifestyleMinPolicy.MinimumDecision minimum) {
            var action = minimum.decision().selectedAction(); target = action.targetKey(); lifestyle = action.targetLifestyleKey(); perk = action.kind() == LifestyleMinPolicy.Kind.PERK;
        } else {
            var all = (LifestyleMinPolicy.AllLifestyleDecision) outcome.recommendation();
            var action = ((LifestylePerksModel.Recommendation) all.decision()).action(); target = action.targetKey(); lifestyle = action.targetLifestyle().wire(); perk = true;
        }
        GovernanceCollector.bindLife(request, life.originalQuery());
        Obj arguments = new Obj(Map.of()).with("target_key", new Text(target)).with("target_lifestyle_key", new Text(lifestyle))
                .with("original_query", life.originalQuery()).with("decision", parse(LifestyleMinCodec.encode(outcome.recommendation())));
        List<ExpectedValue> expected = new ArrayList<>(); expected.add(new ExpectedText(new FieldKey("lifestyle.target_key"), target));
        expected.add(new ExpectedBoolean(new FieldKey(perk ? "lifestyle.target_perk_owned" : "lifestyle.has_current_focus"), true));
        if (!perk) expected.add(new ExpectedText(new FieldKey("lifestyle.current_focus_key"), target));
        return selected(request, perk ? PERK : FOCUS, arguments, expected, Set.of(request.before().frame().identity().player()),
                Set.of(perk ? "lifestyle-perk:" + target : "lifestyle-focus"), Optional.of(Domain.lifestyle), opening ? Kind.OPENING_FOCUS : Kind.ORDINARY,
                perk ? "lifestyle_min_perk_action" : "lifestyle_min_focus_action", "one native-final-legal lifestyle choice", detail.with("lifestyle_original_query", life.originalQuery()));
    }
    private static Decision selectedCouncil(PlanningRequest request, Draft previous, CouncilSelection.Decision decision, boolean core) {
        CouncilSelection.Query query = decision.original(); CouncilSelection.Candidate candidate = decision.selected().orElseThrow();
        if (candidate.characterId().signum() <= 0 || query.incumbent().filter(id -> id.signum() <= 0).isPresent())
            return new Stop(PlanningResult.StopReason.POLICY_BLOCKED, "native candidate retained but original assignment request requires positive int32 IDs");
        Obj arguments = new Obj(Map.of()).with("position_key", new Text(query.position().key())).with("candidate_character_id", new IntegerValue(candidate.characterId()))
                .with("original_query", query.original()).with("expected_has_incumbent", new Bool(query.incumbent().isPresent()))
                .with("expected_incumbent_character_id", new IntegerValue(query.incumbent().orElse(BigInteger.valueOf(-1))));
        return selected(request, core ? CORE_COUNCIL : COUNCIL, arguments,
                List.of(new ExpectedText(new FieldKey("council.position_key"), query.position().key()),
                        new ExpectedInteger(new FieldKey("council.incumbent_character_id"), candidate.characterId())),
                Set.of(candidate.characterId()), Set.of("council-seat:" + query.position().key()), Optional.of(Domain.council), Kind.ORDINARY,
                core ? "council_composition_action" : "council_private_typed_submit", "assign the original deterministic native-legal council skill improvement", previous.detail());
    }
    private static Decision selected(PlanningRequest request, OperationKey operation, Obj arguments, List<ExpectedValue> expected,
            Set<BigInteger> characters, Set<String> keys, Optional<Domain> domain, Kind kind, String phase, String reason, Obj detail) {
        if (!request.observations().actionSteps().contains(operation)) return new Stop(PlanningResult.StopReason.UNSUPPORTED_ACTION, "the exact selected governance action has no registered Java preparation/transport route");
        List<ExpectedValue> values = new ArrayList<>(expected); values.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        var post = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, request.before(), request.source(), EFFECT_SCHEMA, values);
        var claims = new Claims(Set.of(), Set.of(), characters, keys);
        String identity = request.before().frame().episodeRunId() + "|" + request.before().frame().snapshotId() + "|" + operation.value() + "|" + HexFormat.of().formatHex(encode(arguments));
        String id;
        try { id = "governance-" + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(identity.getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("required SHA-256 provider missing", impossible); }
        var command = new ActionCommand(id, request.before(), request.source(), request.sessionId(), operation, arguments, post, claims, request.deadline());
        return new Replace(new Draft("java-ordinary-governance-v1", phase, reason, kind, Optional.of(command), Purpose.WORLD_ACTION, domain, detail), reason);
    }
    public static boolean existingFocus(Obj query) {
        if (!(query.get("snapshot") instanceof Obj snapshot) || !(snapshot.get("current_focus") instanceof Obj focus)
                || !new Text("present").equals(focus.get("presence"))) return false;
        Obj readiness = object(snapshot.get("readiness"), "opening readiness"), progress = object(snapshot.get("current_lifestyle_progress"), "opening XP/points");
        StrictJson.require(bool(readiness.get("current_focus_ready"), "focus ready") && bool(readiness.get("lifestyle_progress_ready"), "progress ready")
                && text(focus.get("lifestyle_key"), "lifestyle").equals(text(progress.get("lifestyle_key"), "progress lifestyle"))
                && new Text("present").equals(progress.get("presence")), "existing opening focus lacks exact current progress");
        text(focus.get("key"), "existing focus key");
        for (String key : List.of("xp_total_raw", "xp_within_level_raw", "xp_per_level", "unspent_perk_points", "used_perk_points"))
            StrictJson.require(integer(progress.get(key), key).signum() >= (key.equals("xp_per_level") ? 1 : 0), "invalid existing opening progress");
        return true;
    }
}
