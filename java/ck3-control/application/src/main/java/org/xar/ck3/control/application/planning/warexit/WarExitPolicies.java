package org.xar.ck3.control.application.planning.warexit;

import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.object;
import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.textIs;
import static org.xar.ck3.control.application.planning.warexit.WarExitEvidence.trueValue;
import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.advance.AdvanceRewrite;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult.StopReason;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence.War;
import org.xar.ck3.control.application.planning.warexit.WarExitReads.Key;
import org.xar.ck3.control.application.planning.warexit.WarExitReads.Query;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeInteractionRoles;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.Configuration;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.g2.m0.RaiktorRecommendationInputCodec;
import org.xar.ck3.control.g2.m0.RaiktorUtilityComparisonTrace;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.military.prewaradmission.OrdinaryPrewarAdmission;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionCodec;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;

/** Original collector -> shared Java M0 producer/evaluator -> sole ActionCommand proposal. */
public final class WarExitPolicies implements OrdinaryPolicy {
    private final PlanningStage stage;
    private final ExactRef implementationSource;
    private final WarExitReads reads;
    private final Optional<Configuration> configuration;
    private final Optional<WarExitReads.DeclarationLeaseSource> declarationLeases;
    private final boolean ordinaryContinuationOnly;
    private final Map<CollectionKey, Collection> collections = new HashMap<>();
    private final Map<PrewarKey, PlanningReadResult<Query>> prewarAttempts = new HashMap<>();
    private ObservationIdentity cacheFrame;
    private String cacheSession;

    /** Configuration must come from the actual exact-file loader; no path, default model or Python fallback here. */
    public WarExitPolicies(PlanningStage stage, ExactRef implementationSource, WarExitReads reads, Configuration configuration,
                          WarExitReads.DeclarationLeaseSource declarationLeases) {
        require(stage == PlanningStage.THREE_WAY_WAR_EXIT || stage == PlanningStage.PREWAR_FORCE_COALITION,
                "war adapter owns only its two original stages");
        this.stage = stage; this.implementationSource = Objects.requireNonNull(implementationSource);
        require(implementationSource.bytes() > 0, "actual implementation source reference required");
        this.reads = Objects.requireNonNull(reads); this.configuration = Optional.of(Objects.requireNonNull(configuration));
        this.declarationLeases = Optional.of(Objects.requireNonNull(declarationLeases));
        this.ordinaryContinuationOnly = false;
    }
    /** Original strategy9860..10154 uses no full Raiktor configuration or declaration lease. */
    public static WarExitPolicies ordinaryBeforeTactics(ExactRef implementationSource, WarExitReads actualReads) {
        return new WarExitPolicies(implementationSource, actualReads);
    }
    private WarExitPolicies(ExactRef implementationSource, WarExitReads actualReads) {
        this.stage = PlanningStage.THREE_WAY_WAR_EXIT;
        this.implementationSource = Objects.requireNonNull(implementationSource);
        require(implementationSource.bytes() > 0, "actual ordinary continuation implementation source required");
        this.reads = Objects.requireNonNull(actualReads);
        this.configuration = Optional.empty(); this.declarationLeases = Optional.empty();
        this.ordinaryContinuationOnly = true;
    }
    @Override public PlanningStage stage() { return stage; }
    @Override public ExactRef implementationSource() { return implementationSource; }

    @Override public synchronized Decision evaluate(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous); resetFrame(request);
        if (ordinaryContinuationOnly) return new Stop(StopReason.INCOMPLETE_PRODUCTION_CHAIN,
                "ordinary-before-tactics adapter does not install the full Raiktor/prewar input producers");
        try {
            return stage == PlanningStage.THREE_WAY_WAR_EXIT ? formal(request, previous) : prewar(request, previous);
        } catch (IllegalArgumentException malformed) {
            return new Stop(StopReason.INVALID_FRAME, "war policy input rejected: " + malformed.getMessage());
        }
    }

    private void resetFrame(PlanningRequest request) {
        if (!request.before().equals(cacheFrame) || !request.sessionId().equals(cacheSession)) {
            collections.clear(); prewarAttempts.clear(); cacheFrame = request.before(); cacheSession = request.sessionId();
        }
    }

    private Decision formal(PlanningRequest request, Draft previous) {
        if (!request.observations().paused() || request.observations().foregroundPresent())
            return new NotApplicable("the original Raiktor formal collector applies only on a clear paused frame");
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        JsonNode optionsRows = snapshot.get("war_termination_options");
        if (optionsRows == null || optionsRows.isNull()) return new NotApplicable("no published Raiktor termination row; preserve ordinary core collection");
        require(optionsRows.isArray(), "published termination rows must be an array");
        List<ObjectNode> raiktorRows = new ArrayList<>();
        for (JsonNode value : optionsRows) {
            ObjectNode row = object(value, "termination cache row"); JsonNode cb = row.get("active_casus_belli_identity");
            if (cb instanceof ObjectNode && textIs(cb.get("canonical_key"), "raiktor_claim_cb")) raiktorRows.add(row);
        }
        if (raiktorRows.isEmpty()) return new NotApplicable("the current original formal Raiktor branch does not apply");
        if (raiktorRows.size() != 1) return new Wait("multiple_current_raiktor_wars");
        int id = WarExitEvidence.positive(raiktorRows.getFirst().get("war_id"));
        List<War> matches = WarExitEvidence.wars(snapshot).stream().filter(war -> war.warId() == id).toList();
        if (matches.size() != 1) return new Wait("current_raiktor_war_identity_unavailable");
        War war = matches.getFirst();
        if (war.playerSide() != WarExitEvidence.Side.ATTACKER || !war.primaryLeader() || war.opponent().orElse(0) <= 0)
            return new Wait("raiktor_primary_attacker_binding_unavailable");
        if (war.score().orElse(Integer.MIN_VALUE) >= 100) return new NotApplicable("preserve original enforce-demands priority at 100 score");
        List<ObjectNode> history = WarExitEvidence.historySinceRestore(request);
        if (WarExitEvidence.priorTerminalSubmission(history, id)) return new Wait("previous_terminal_submission_requires_fresh_status");
        CollectionKey key = new CollectionKey(request.before(), request.sessionId(), id, war.opponent().orElseThrow());
        Collection state = collections.computeIfAbsent(key, ignored -> new Collection());
        if (state.options == null) {
            state.options = WarExitEvidence.currentQuery(history, snapshot, "query-war-termination-options-" + id,
                    "queried_episode_run_id").orElse(null);
            if (state.options == null) return queryOptions(request, state, id);
        }

        // Reuse the original published double-read trace only when it contains the two actual query/capture tuples.
        if (state.first == null) importPublishedPowerTrace(snapshot, state, war.opponent().orElseThrow());
        if (state.first == null) {
            state.before = snapshot.deepCopy(); state.beforeRequest = request;
            PlanningReadResult<Query> result = readOnce(request, state, "power-first", new Key(WarExitReads.Kind.POWER, war.opponent().orElseThrow()), empty());
            if (result instanceof PlanningReadResult.Known<Query> known) {
                state.first = known.value().envelope(); return new Refresh("first actual power read completed; capture the real between snapshot without advancing Game");
            }
            return unavailableRead("first_power_query_unavailable", result);
        }
        if (state.second == null) {
            if (request == state.beforeRequest) return new Refresh("a new actual semantic capture is required between the two independent power reads");
            state.between = snapshot.deepCopy(); state.betweenRequest = request;
            PlanningReadResult<Query> result = readOnce(request, state, "power-second", new Key(WarExitReads.Kind.POWER, war.opponent().orElseThrow()), empty());
            if (result instanceof PlanningReadResult.Known<Query> known) {
                state.second = known.value().envelope(); return new Refresh("second actual power read completed; capture the real after snapshot without advancing Game");
            }
            return unavailableRead("second_power_query_unavailable", result);
        }
        if (state.after == null) {
            if (request == state.betweenRequest) return new Refresh("a new actual semantic capture is required after the second power read");
            state.after = snapshot.deepCopy();
        }
        if (state.terms == null) {
            state.terms = WarExitEvidence.currentQuery(history, snapshot, "query-war-termination-terms-v1-" + id,
                    "episode_run_id").orElse(null);
            if (state.terms == null) {
                PlanningReadResult<Query> result = readOnce(request, state, "terms", new Key(WarExitReads.Kind.TERMS, id), empty());
                if (result instanceof PlanningReadResult.Known<Query> known) {
                    state.terms = known.value().envelope(); return new Refresh("actual terms read completed; consume a freshly published semantic observation before comparing exits");
                }
                return unavailableRead("terms_query_unavailable", result);
            }
        }
        var input = new RaiktorActualRecommendationFactory.Inputs(snapshot, state.options, state.terms,
                state.before, state.first, state.between, state.second, state.after, id, war.opponent().orElseThrow(), true);
        var produced = RaiktorActualRecommendationFactory.produce(input, configuration.orElseThrow());
        if (produced instanceof RaiktorActualRecommendationFactory.Unavailable unavailable) {
            ObjectNode missing = StrictJson.object(); missing.put("policy", "raiktor-formal-three-way-exit-v1");
            var blockers = missing.putArray("blockers"); unavailable.blockers().forEach(blocker -> blockers.add(blocker.name()));
            var diagnostics = missing.putArray("diagnostics"); unavailable.diagnostics().forEach(diagnostics::add);
            return new Defer("actual advanced exit inputs unavailable; preserve legal ordinary war handling", immutable(missing));
        }
        var available = (RaiktorActualRecommendationFactory.Available) produced;
        ObjectNode recommendation = object(available.recommendation(), "actual Java recommendation");
        ObjectNode certificate = gate(request, snapshot, war, recommendation);
        String outcome = StrictJson.text(certificate.get("recommended_outcome"));
        // The factory already issued the typed comparison trace from this same certificate. Keep its source receipt too.
        OpportunityJson.Obj detail = previous.detail().with("war_exit_recommendation", immutable(recommendation))
                .with("war_exit_comparison_trace", immutable(RaiktorUtilityComparisonTrace.toJson(available.trace())));
        if (outcome.equals("continue")) {
            return new Replace(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(),
                    previous.command(), previous.purpose(), previous.domain(), detail),
                    "the formal continue choice returns to the bounded tactical planner; no direct resume-map command");
        }
        String step = (outcome.equals("white_peace") ? "offer-white-peace-" : "surrender-war-") + id;
        ActionCommand command = LegacyWarExitPolicy.terminalCommand(request, war, outcome,
                Optional.of(immutable(object(certificate.get("postcondition_plan"), "frozen postcondition plan"))));
        return new Replace(new Draft("raiktor-formal-three-way-exit-v1", "native_war_raiktor_threeway_terminal",
                "one same-frame legal terminal wins the existing Java three-way comparison", OrdinaryPolicy.Kind.WAR_EXIT,
                Optional.of(command), Purpose.WORLD_ACTION, Optional.of(Domain.war),
                detail.with("selected_step", new OpportunityJson.Text(step))), "one source-bound M0 terminal proposal selected");
    }

    private Decision queryOptions(PlanningRequest request, Collection state, int id) {
        PlanningReadResult<Query> result = readOnce(request, state, "options", new Key(WarExitReads.Kind.OPTIONS, id), empty());
        if (result instanceof PlanningReadResult.Known<Query> known) {
            state.options = known.value().envelope(); return new Refresh("actual native options read completed; recapture the original semantic publication");
        }
        return unavailableRead("options_query_unavailable", result);
    }

    /** Original strategy.py9860-10154; the core calls this after assault and pending-interaction priority. */
    public synchronized Decision evaluateBeforeTactics(PlanningRequest request, Draft previous) {
        resetFrame(request);
        try {
            ObjectNode snapshot = WarExitEvidence.snapshot(request);
            List<ObjectNode> history = WarExitEvidence.effectiveHistorySinceRestore(request);
            for (War war : WarExitEvidence.wars(snapshot)) {
                Optional<WarExitEvidence.SurrenderState> surrender = WarExitEvidence.surrenderState(history, snapshot, war.warId());
                if (surrender.isPresent()) {
                    if (surrender.orElseThrow().sameDayPending()) return responseAdvance(request, previous, war,
                            "native_war_surrender_response_advance", "surrender", surrender.orElseThrow().source());
                    return new Stop(StopReason.UNKNOWN_ACTION_UNRESOLVED,
                            "prior surrender has not produced independent old-WarID disappearance; never submit it again");
                }
                Optional<WarExitEvidence.Cooldown> cooldown = WarExitEvidence.whitePeaceCooldown(history, snapshot, war.warId());
                if (cooldown.isPresent() && cooldown.orElseThrow().status().equals("cooldown")) {
                    var material = cooldown.orElseThrow();
                    if (material.actionStatus().equals("submitted_pending") && material.elapsedRaw().orElse(-1L) == 0)
                        return responseAdvance(request, previous, war, "native_war_white_peace_response_advance", "white_peace", material.source());
                    continue; // Original pending window continues ordinary military OODA without daily context rebuilds.
                }
                Optional<WarExitEvidence.Options> observed = WarExitEvidence.currentOptions(snapshot, war.warId());
                Collection state = collections.computeIfAbsent(new CollectionKey(request.before(), request.sessionId(), war.warId(),
                        war.opponent().orElse(0)), ignored -> new Collection());
                if (observed.isEmpty()) {
                    Optional<OpportunityJson.Obj> defer = WarExitQueryCadence.defer(request, war, history);
                    if (defer.isPresent()) continue;
                    Key key = new Key(WarExitReads.Kind.OPTIONS, war.warId());
                    if (!request.observations().actionSteps().contains(new OperationKey(WarExitReads.step(key)))) continue;
                    PlanningReadResult<Query> read = readOnce(request, state, "tactics-options", key, empty());
                    if (read instanceof PlanningReadResult.Known<Query>) return new Refresh("original war termination collector completed; use actual new publication before tactics");
                    return unavailableRead("optional_native_war_termination_query_unavailable", read);
                }
                WarExitEvidence.Options options = observed.orElseThrow();
                if (!claimWhitePeaceCandidate(request.observations().snapshot(), war.warId())) continue;
                ObjectNode terms = currentTerms(snapshot, war.warId());
                if (terms == null) {
                    Key key = new Key(WarExitReads.Kind.TERMS, war.warId());
                    if (!request.observations().actionSteps().contains(new OperationKey(WarExitReads.step(key)))) continue;
                    PlanningReadResult<Query> read = readOnce(request, state, "tactics-terms", key, empty());
                    if (read instanceof PlanningReadResult.Known<Query>) return new Refresh("original claim-disposition read completed; require actual same-frame publication");
                    return unavailableRead("claim_cb_terms_query_unavailable", read);
                }
                if (!claimTermsReady(request.observations().snapshot(), war.warId())) continue;
                if (cooldown.isEmpty()) {
                    String step = "offer-white-peace-" + war.warId();
                    if (!request.observations().actionSteps().contains(new OperationKey(step)))
                        return new Stop(StopReason.UNSUPPORTED_ACTION, "same-frame minimal white peace is ready but the original literal is unreachable");
                    ActionCommand command = LegacyWarExitPolicy.terminalCommand(request, war, "white_peace", Optional.empty());
                    ObjectNode decision = StrictJson.object().put("policy", "claim-cb-minimal-white-peace-v1")
                            .put("outcome", "white_peace").put("all_declared_target_claims_present", true)
                            .put("weak_claims_allowed", true).put("native_ai_equivalent", false).put("semantic_optimal", false)
                            .put("campaign_forecast_used", false);
                    decision.set("recipient_response", options.original().get("options").get("white_peace").get("recipient_response"));
                    NativeInteractionRoles.putOption(decision, options.whitePeace().recipientContext());
                    decision.set("claimant_character_id", terms.get("claimant_character_id")); decision.set("target_title_ids", terms.get("target_title_ids"));
                    return new Replace(new Draft("one-life-turn-v1", "native_war_claim_cb_minimal_white_peace",
                            "the original primary-attacker claim rule has current recipient acceptance and retained declared claims",
                            OrdinaryPolicy.Kind.WAR_EXIT, Optional.of(command), Purpose.WORLD_ACTION, Optional.of(Domain.war),
                            previous.detail().with("selected_step", new OpportunityJson.Text(step)).with("decision", immutable(decision))),
                            "select the existing minimal claim white-peace rule without claiming full campaign optimality");
                }
            }
            return new Keep("original early war collectors and minimal exits selected no action; continue tactics");
        } catch (IllegalArgumentException malformed) {
            return new Stop(StopReason.INVALID_FRAME, "early war collector input rejected: " + malformed.getMessage());
        }
    }

    /** Actual same-frame options determine whether the original terms read is needed. */
    public static boolean claimWhitePeaceCandidate(OpportunityJson.Obj actualFrame, int warId) {
        return OrdinaryWhitePeacePolicy.needsClaimTerms(actualFrame, warId);
    }

    static ObjectNode currentTerms(ObjectNode snapshot, int id) {
        JsonNode rows = snapshot.get("war_termination_terms"); if (rows == null || rows.isNull()) return null;
        require(rows.isArray(), "termination terms cache must be an array"); ObjectNode selected = null;
        for (JsonNode row : rows) if (row instanceof ObjectNode value && WarExitEvidence.integerIs(value.get("war_id"), id)) {
            require(selected == null, "duplicate cached terms WarID"); selected = value;
        }
        if (selected == null || !WarExitEvidence.sameFrame(snapshot, selected, "episode_run_id")) return null;
        ObjectNode nativeTerms = selected.deepCopy();
        for (String field : List.of("query_sequence", "queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_connection_generation", "episode_run_id")) nativeTerms.remove(field);
        return NativeTerminationTerms.normalize(nativeTerms, id);
    }

    /** All action eligibility is the single full original four-variant policy. */
    public static boolean claimTermsReady(OpportunityJson.Obj actualFrame, int warId) {
        return OrdinaryWhitePeacePolicy.evaluate(actualFrame, warId) instanceof OrdinaryWhitePeacePolicy.Ready ready
                && ready.variant() == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB;
    }

    static Decision responseAdvance(PlanningRequest request, Draft previous, War war, String phase,
                                             String outcome, ObjectNode submission) {
        if (!request.observations().actionSteps().contains(new OperationKey("life-advance")))
            return new Stop(StopReason.UNSUPPORTED_ACTION, "the queued terminal needs one same-day bounded advance, without repeating submission");
        String identity = request.before().frame().snapshotId() + ":" + request.before().frame().revision() + ":" + war.warId();
        String actionId = "war-reply-day:" + hash(StrictJson.object().put("identity", identity)).toLowerCase(Locale.ROOT);
        OpportunityJson.Obj args = new OpportunityJson.Obj(Map.of("war_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(war.warId())),
                "requested_outcome", new OpportunityJson.Text(outcome), "submission_source", immutable(submission)));
        var baseExpected = new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, request.before(), request.source(),
                "xar.ck3.java-life-advance-observation/v1", List.of(new ExpectedBoolean(new FieldKey("advance.completion_verified"), true)));
        ActionCommand original = new ActionCommand(actionId, request.before(), request.source(), request.sessionId(),
                new OperationKey("life-advance"), args, baseExpected,
                new Claims(Set.of(), Set.of(), Set.of(request.before().frame().identity().player()), Set.of("war:" + war.warId())), request.deadline());
        ActionCommand exactDay = AdvanceRewrite.exactDay(request, original);
        return new Replace(new Draft("one-life-turn-v1", phase,
                "observe one native settlement day through the original exact-day composite without repeating the terminal",
                OrdinaryPolicy.Kind.WAR_EXIT, Optional.of(exactDay), Purpose.DATE_ADVANCE, Optional.of(Domain.war),
                previous.detail().with("submission", immutable(submission)).with("selected_step", new OpportunityJson.Text("life-advance-one-day"))),
                "the original same-day terminal response branch advances exactly one native day");
    }

    private PlanningReadResult<Query> readOnce(PlanningRequest request, Collection state, String phase, Key key, OpportunityJson.Obj arguments) {
        PlanningReadResult<Query> previous = state.attempts.get(phase);
        if (previous != null) return previous;
        if (!request.observations().bridgeCapabilities().contains(WarExitReads.capability(key.kind()))) {
            var unavailable = new PlanningReadResult.Unavailable<Query>("native query capability is not advertised", Optional.empty());
            state.attempts.put(phase, unavailable); return unavailable;
        }
        state.attempts.put(phase, new PlanningReadResult.Unavailable<>("readonly attempt started; not automatically repeated", Optional.empty()));
        PlanningReadResult<Query> result = reads.read(request, key, arguments); state.attempts.put(phase, result); return result;
    }

    private Decision prewar(PlanningRequest request, Draft previous) {
        ObjectNode detail = object(OpportunityJson.toNode(previous.detail()), "original selected prewar plan");
        JsonNode requiredValue = detail.get("required_prewar_force_coalition_query");
        if (requiredValue == null || requiredValue.isNull()) return new NotApplicable("the actual selected plan has no required formal prewar read");
        ObjectNode required = StrictJson.object(requiredValue, Set.of("declaration_id", "expected_revision", "profile"));
        require(textIs(required.get("profile"), "v2") && required.get("expected_revision").isIntegralNumber()
                && required.get("expected_revision").bigIntegerValue().equals(request.before().frame().revision()),
                "ordinary prewar query intent is malformed or stale");
        String declarationId = StrictJson.text(required.get("declaration_id"));
        ObjectNode selected = object(detail.get("selected_declaration"), "actual selected declaration source");
        require(textIs(selected.get("declaration_id"), declarationId), "required query differs from the selected declaration");
        WarExitReads.DeclarationLeaseResult leaseResult = declarationLeases.orElseThrow().forRequest(request);
        if (leaseResult instanceof WarExitReads.UnavailableDeclarationLease unavailable)
            return new Stop(StopReason.INCOMPLETE_PRODUCTION_CHAIN, "actual native declaration cache lease is unavailable: " + unavailable.reason());
        var lease = ((WarExitReads.AvailableDeclarationLease) leaseResult).lease();
        require(lease.matches(request), "actual selected declaration cache lease crossed the current frame");
        ObjectNode actualSelected = org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.encodeChoice(lease.selected(declarationId));
        for (String key : List.of("declaration_id", "target_character_id", "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids"))
            require(selected.has(key) && selected.get(key).equals(actualSelected.get(key)), "selected native declaration source changed: " + key);
        BigInteger sequence = lease.querySequence();
        ObjectNode snapshot = WarExitEvidence.snapshot(request);
        snapshot.set("declarable_wars", org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.encode(lease.declarations()));
        var admission = OrdinaryPrewarAdmission.assess(PrewarAdmissionCodec.decodeLegacyContainer(snapshot, selected));
        if (admission.declareAdmitted()) return new Keep("the actual independently bound complete coalition and final native legality admit the original selected declaration");
        if (admission.requiredQuery() == null) return new Wait("prewar declaration remains unadmitted: " + admission.reason().wire());
        if (!request.observations().bridgeCapabilities().contains(WarExitReads.capability(WarExitReads.Kind.PREWAR_COALITION)))
            return new Wait("native_does_not_advertise_formal_prewar_v2_read_support");
        ObjectNode selectedPayload = selected.deepCopy(); selectedPayload.remove("declaration_id");
        StrictJson.object(selectedPayload, Set.of("target_character_id", "casus_belli_index", "casus_belli_key", "configuration_index", "claimant_character_id", "target_title_ids"));
        ObjectNode args = StrictJson.object().put("declaration_id", declarationId).put("declaration_query_sequence", sequence);
        args.set("selected_declaration", selectedPayload);
        PrewarKey key = new PrewarKey(request.before(), request.sessionId(), sequence, declarationId, immutable(selectedPayload));
        PlanningReadResult<Query> prior = prewarAttempts.get(key);
        if (prior != null) return new Wait("the exact same-frame prewar query was already attempted; require actual new publication, never repeat or declare from a partial result");
        prewarAttempts.put(key, new PlanningReadResult.Unavailable<>("prewar readonly attempt started; not automatically repeated", Optional.empty()));
        PlanningReadResult<Query> result = reads.read(request, new Key(WarExitReads.Kind.PREWAR_COALITION, 0), immutable(args));
        prewarAttempts.put(key, result);
        if (result instanceof PlanningReadResult.Known<Query>)
            return new Refresh("one actual formal prewar query completed; recapture current declaration source and replan with query disabled for this exact attempt");
        var unavailable = (PlanningReadResult.Unavailable<Query>) result;
        return new Wait("prewar_force_query_unavailable_request_not_retried: " + unavailable.reason());
    }

    private static ObjectNode gate(PlanningRequest request, ObjectNode snapshot, War war, ObjectNode recommendation) {
        require(textIs(recommendation.get("schema"), "xar.ck3.raiktor_three_way_exit_recommendation.v6")
                && textIs(recommendation.get("provider"), "raiktor-three-way-exit-recommendation-provider-v6"), "recommendation provider drifted");
        ObjectNode certificate = object(recommendation.get("recommendation_certificate"), "recommendation certificate");
        require(WarExitEvidence.integerIs(certificate.get("schema_version"), 1)
                && textIs(certificate.get("contract"), "raiktor-three-way-exit-recommendation-v7"), "recommendation certificate drifted");
        ObjectNode unhashed = certificate.deepCopy(); unhashed.remove("certificate_sha256");
        require(textIs(certificate.get("certificate_sha256"), hash(unhashed)), "recommendation certificate hash drifted");
        require(trueValue(recommendation.get("production_recommendation_ready")) && trueValue(recommendation.get("action_ready"))
                && recommendation.get("blockers").isArray() && recommendation.get("blockers").isEmpty(), "recommendation is not production ready");
        String outcome = StrictJson.text(certificate.get("recommended_outcome"));
        require(Set.of("continue", "white_peace", "surrender").contains(outcome), "recommendation outcome drifted");
        ObjectNode action = object(certificate.get("action_plan"), "recommendation action plan");
        String expected = outcome.equals("continue") ? "resume-map"
                : (outcome.equals("white_peace") ? "offer-white-peace-" : "surrender-war-") + war.warId();
        require(trueValue(action.get("ready")) && trueValue(action.get("single_action_only"))
                && textIs(action.get("semantic_action"), outcome) && textIs(action.get("literal"), expected)
                && textIs(recommendation.get("recommended_outcome"), outcome) && textIs(recommendation.get("action_literal"), expected),
                "recommendation action plan drifted");
        var frame = RaiktorActualRecommendationFactory.decodeFrame(certificate.get("frame"));
        ObjectNode diagnostics = object(snapshot.get("diagnostics"), "native diagnostics");
        require(frame.snapshotId().equals(request.before().frame().snapshotId())
                && frame.snapshotRevision().equals(request.before().frame().revision())
                && frame.nativeRevision().equals(request.before().frame().identity().nativeRevision())
                && BigInteger.valueOf(frame.dateRaw()).equals(request.before().frame().identity().dateRaw())
                && frame.episodeId().equals(request.before().frame().episodeRunId()) && frame.warId() == war.warId()
                && frame.primaryAttackerCharacterId() == request.before().frame().identity().player().intValueExact()
                && frame.primaryDefenderCharacterId() == war.opponent().orElseThrow()
                && frame.connectionId().equals("connection-generation:" + diagnostics.get("connection_generation").bigIntegerValue())
                && frame.ck3Pid() == WarExitEvidence.positive(diagnostics.get("bridge_pid")) && request.observations().paused()
                && !request.observations().foregroundPresent(), "recommendation crossed the complete actual paused action frame");
        // Preserve the original continue gate's registered literal, while the formal planner itself keeps tactical control.
        require(request.observations().actionSteps().contains(new OperationKey(expected)), "recommended action step is not advertised");
        if (!outcome.equals("continue")) {
            require(war.primaryLeader(), "terminal recommendation requires primary war leadership");
            require(request.observations().bridgeCapabilities().contains(outcome.equals("white_peace")
                    ? "game.command.offer-white-peace-N" : "game.command.surrender-war-N"), "recommended action capability is not advertised");
        }
        return certificate;
    }

    private static void importPublishedPowerTrace(ObjectNode snapshot, Collection state, int opponent) {
        JsonNode raw = snapshot.get("war_entry_assessments_two_read_trace_v1"); if (raw == null || raw.isNull()) return;
        require(raw.isArray(), "published power trace must be array"); List<ObjectNode> rows = new ArrayList<>();
        for (JsonNode row : raw) if (row instanceof ObjectNode object && WarExitEvidence.integerIs(object.get("target_character_id"), opponent)) rows.add(object);
        if (rows.isEmpty() || rows.size() == 1) return;
        require(rows.size() == 2, "power double-read trace drifted");
        state.before = object(rows.get(0).get("before_snapshot"), "actual before power snapshot").deepCopy();
        state.first = object(rows.get(0).get("query"), "actual first power query").deepCopy();
        state.between = object(rows.get(0).get("after_snapshot"), "actual between power snapshot").deepCopy();
        state.second = object(rows.get(1).get("query"), "actual second power query").deepCopy();
        state.after = object(rows.get(1).get("after_snapshot"), "actual after power snapshot").deepCopy();
    }

    private static Decision unavailableRead(String reason, PlanningReadResult<Query> result) {
        if (result instanceof PlanningReadResult.Unavailable<Query> unavailable) {
            ObjectNode evidence = StrictJson.object().put("reason", reason).put("diagnostic", unavailable.reason()).put("request_retried", false);
            return new Defer(reason, immutable(evidence));
        }
        throw new IllegalArgumentException("unexpected collector result branch");
    }
    static OpportunityJson.Obj immutable(JsonNode value) { return DriverJson.object(RaiktorExitObservationCodec.encodeWire(value), DriverJson.MAX_NATIVE_BYTES); }
    private static String hash(JsonNode value) { return RetainedJson.pythonCanonical(RetainedJson.parse(RaiktorExitObservationCodec.encodeWire(value)),
            new RetainedJson.CanonicalBudget(StrictJson.EXPLICIT_MAX_BYTES, 100_000, 128)).sha256().toUpperCase(Locale.ROOT); }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private record CollectionKey(ObservationIdentity frame, String sessionId, int warId, int opponent) { }
    private record PrewarKey(ObservationIdentity frame, String sessionId, BigInteger sequence, String declarationId, OpportunityJson.Obj selected) { }
    private static final class Collection {
        final Map<String, PlanningReadResult<Query>> attempts = new HashMap<>();
        ObjectNode options; ObjectNode terms; ObjectNode before; ObjectNode first; ObjectNode between; ObjectNode second; ObjectNode after;
        PlanningRequest beforeRequest; PlanningRequest betweenRequest;
    }
}

