package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueCodec;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValuePolicy;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;
import org.xar.ck3.control.wave3.governance.heirdiagnostic.HeirCandidateDiagnosticConsumerPort;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineageConsumerPort;
import org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingConsumerPort;
import org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingReadPolicy;
import org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingModel;
import org.xar.ck3.control.governance.heirpreference.HeirPreferenceCodec;

/** Actual ordinary family orchestration. Reads use Root's exact catalog; commands have one authority. */
public final class FamilyOrdinaryPolicy implements OrdinaryPolicy {
    private final ExactRef implementation;
    private final PlanningReadPort reader;
    private final Reads reads;
    private final LedgerSource ledgers;
    private final Commands commands;
    private final MaterialResults materials;
    private final Settings settings;
    private final FamilyGuardianCadence guardianCadence = new FamilyGuardianCadence();
    private Optional<WartimeReviewScope> lastWartimeReview = Optional.empty();
    /** Process-local scheduling only: never a candidate, native receipt or action authority.
     * The original episode/actor/date gate is narrowed to the complete unchanged source,
     * frame, observation, baseline and original documents. Any changed input rereads.
     * This is deliberately not persisted or serialized across a runtime restart. */
    private record WartimeReviewScope(ObservationIdentity frame, G2Source source, String sessionId,
            PlanningObservation observation, Documents documents, Draft baseline) {
        private WartimeReviewScope {
            Objects.requireNonNull(frame); Objects.requireNonNull(source); Objects.requireNonNull(sessionId);
            Objects.requireNonNull(observation); Objects.requireNonNull(documents); Objects.requireNonNull(baseline);
        }
    }
    FamilyGuardianCadence guardianCadence() { return guardianCadence; }
    public FamilyOrdinaryPolicy(ExactRef implementation, PlanningReadPort reader, Reads reads,
            LedgerSource ledgers, Commands commands, MaterialResults materials, Settings settings) {
        this.implementation = Objects.requireNonNull(implementation); this.reader = Objects.requireNonNull(reader);
        this.reads = Objects.requireNonNull(reads); this.ledgers = Objects.requireNonNull(ledgers);
        this.commands = Objects.requireNonNull(commands); this.materials = Objects.requireNonNull(materials);
        this.settings = Objects.requireNonNull(settings);
    }
    @Override public PlanningStage stage() { return PlanningStage.FAMILY_AND_EDUCATION; }
    @Override public ExactRef implementationSource() { return implementation; }
    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        return evaluate(request,previous,Optional.empty());
    }
    /** M5's actual selected alternative uses this same complete Native read/pending/command path. */
    public Decision evaluateForCandidate(PlanningRequest request,Draft previous,BigInteger actualCandidate) {
        if(actualCandidate==null||actualCandidate.signum()<=0||actualCandidate.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))>0)
            throw new IllegalArgumentException("bounded positive actual family candidate required");
        return evaluate(request,previous,Optional.of(actualCandidate));
    }
    private Decision evaluate(PlanningRequest request,Draft previous,Optional<BigInteger> actualCandidate) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        if (!settings.familyEnabled() && settings.matrilinealPair().isEmpty() && !settings.childDefaultEnabled()) {
            clearWartimeReview(); return new Keep("family private capabilities are not enabled");
        }
        if (!request.observations().paused() || !request.observations().mapReady() || request.observations().foregroundPresent()) {
            clearWartimeReview(); return new Keep("family reads require the ordinary paused frame");
        }
        try {
            LedgerRead loaded = ledgers.readCurrent(request);
            if (!(loaded instanceof KnownDocuments known)) {
                clearWartimeReview(); return incomplete(((MissingDocuments) loaded).reason());
            }
            Documents docs = known.documents();
            Optional<WartimeReviewScope> review = wartimeReviewScope(request, previous, docs, actualCandidate);
            if (alreadyReviewed(review)) return new Keep("unchanged wartime family review already completed");
            Decision result;
            try {
                result = evaluateDocuments(request, previous, docs, actualCandidate);
            } catch (MissingInput missing) {
                clearWartimeReview(); return optionalMissing(request, previous, docs, missing.getMessage());
            }
            rememberWartimeReview(review, previous, result);
            return result;
        } catch (IllegalArgumentException invalid) {
            clearWartimeReview(); return incomplete("family source/contract rejected: " + invalid.getMessage());
        }
    }
    private Decision evaluateDocuments(PlanningRequest request, Draft previous, Documents docs, Optional<BigInteger> actualCandidate) {
        Decision family = settings.familyEnabled() ? family(request, previous, docs,actualCandidate) : new Keep("family proposal disabled");
        Draft current = family instanceof Replace replace ? replace.draft() : previous;
        if (!(family instanceof Keep) && !(family instanceof Replace)) return family;
        if (settings.matrilinealPair().isPresent()) {
            Decision child = FamilyChildPolicy.matrilineal(this, request, current, docs, settings.matrilinealPair().get());
            if (!(child instanceof Keep)) return child;
        }
        if (settings.childDefaultEnabled()) {
            Decision child = FamilyChildPolicy.childDefault(this, request, current, docs);
            if (!(child instanceof Keep)) return child;
        }
        return family;
    }
    private Optional<WartimeReviewScope> wartimeReviewScope(PlanningRequest request, Draft previous,
            Documents docs, Optional<BigInteger> actualCandidate) {
        String step = selected(previous);
        if (!settings.familyEnabled() || actualCandidate.isPresent() || !request.observations().warInProgress()
                || step == null || !(step.equals("life-advance") || step.startsWith("query-"))) return Optional.empty();
        // Pending, UNKNOWN and retained results always reach the original reducers. No outcome
        // class is inferred from a receipt, a status string or an absent relationship.
        for (Obj domain : List.of(docs.family(), docs.matrilineal(), docs.childDefault()))
            if (domain.get("pending") != Nil.INSTANCE || domain.get("resolved") != Nil.INSTANCE) return Optional.empty();
        for (String field : List.of("family_marriage_pending", "current_betrothal_pending"))
            if (previous.detail().get(field) != null && previous.detail().get(field) != Nil.INSTANCE) return Optional.empty();
        return Optional.of(new WartimeReviewScope(request.before(), request.source(), request.sessionId(),
                request.observations(), docs, previous));
    }
    private synchronized boolean alreadyReviewed(Optional<WartimeReviewScope> review) {
        if (review.isPresent() && review.equals(lastWartimeReview)) return true;
        lastWartimeReview = Optional.empty(); return false;
    }
    private synchronized void rememberWartimeReview(Optional<WartimeReviewScope> review, Draft previous, Decision result) {
        // Only a completed observation that retains the exact independently selected action
        // can suppress another identical review. Refresh/failure/new command cannot.
        lastWartimeReview = result instanceof Replace replaced
                && replaced.draft().command().equals(previous.command())
                && replaced.draft().kind() == previous.kind() && replaced.draft().purpose() == previous.purpose()
                && replaced.draft().domain().equals(previous.domain())
                && Objects.equals(selected(replaced.draft()), selected(previous)) ? review : Optional.empty();
    }
    private synchronized void clearWartimeReview() { lastWartimeReview = Optional.empty(); }
    /** Called by OrdinaryCorePolicy at the original ruler-marriage position, before later family work. */
    public Decision evaluateRulerMarriage(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        Obj snapshot = request.observations().snapshot(); Obj played = object(snapshot.get("played_character"));
        List<Obj> history = request.observations().history();
        boolean relationKnown = played.members().keySet().containsAll(Set.of("betrothed_id", "primary_spouse_id", "spouse_ids"));
        boolean partnered = relationKnown && (played.get("betrothed_id") != Nil.INSTANCE || played.get("primary_spouse_id") != Nil.INSTANCE
                || !array(played.get("spouse_ids")).isEmpty());
        if (partnered) return new Keep("current native ruler relationship already exists");
        Optional<Obj> attempt = FamilyHistory.rulerAttempt(history, snapshot);
        boolean warAttempted = history.stream().anyMatch(row -> {
            String step = FamilyHistory.command(row);
            return "query-declarable-wars".equals(step) && yes(row.get("ok")) || step != null && (step.startsWith("declare-war-") || step.startsWith("enforce-demands-"));
        });
        boolean warFocus = OrdinaryCorePolicy.focus(request).filter("war"::equals).isPresent();
        if (attempt.isEmpty() && warFocus && !warAttempted) return new Keep("original cross-run war focus precedes first ruler marriage discovery");
        Obj detail = previous.detail().with("marriage_intent", attempt.<Value>map(value -> value).orElse(Nil.INSTANCE));
        if (attempt.isPresent() && "pending".equals(string(attempt.get().get("status"))))
            return select(request, previous, "life-advance", obj(), detail, "native_arrange_marriage_response_wait",
                    "advance one bounded interval while waiting for the exact spouse or betrothal relationship", Purpose.DATE_ADVANCE);
        Value retry = attempt.filter(value -> "retry".equals(string(value.get("status")))).map(value -> value.get("candidate_character_id")).orElse(Nil.INSTANCE);
        List<Obj> choices = new ArrayList<>(); Set<String> identities = new HashSet<>();
        if (snapshot.get("arrange_marriage_choices") instanceof Arr rows) {
            for (Value raw : rows.items()) {
                Obj choice = object(raw); String id = text(choice.get("choice_id"));
                BigInteger actor = integer(choice.get("played_character_id")), candidate = integer(choice.get("candidate_character_id"));
                if (actor.signum() <= 0 || candidate.signum() <= 0 || actor.equals(candidate) || !id.equals(actor + "-" + candidate)
                        || !eq(choice.get("played_character_id"), played.get("character_id")) || !identities.add(id))
                    throw new IllegalArgumentException("ruler native choice identity changed");
                choices.add(choice);
            }
        } else if (snapshot.get("arrange_marriage_choices") != null && snapshot.get("arrange_marriage_choices") != Nil.INSTANCE)
            throw new IllegalArgumentException("native marriage choices require array");
        choices.sort(Comparator.comparing((Obj choice) -> eq(choice.get("candidate_character_id"), retry))
                .thenComparing(choice -> integer(choice.get("candidate_character_id"))).thenComparing(choice -> text(choice.get("choice_id"))));
        if (!choices.isEmpty()) {
            Obj choice = choices.get(0); String step = "arrange-marriage-" + text(choice.get("choice_id"));
            return select(request, previous, step, obj("choice_id", choice.get("choice_id")), detail.with("marriage_choice", choice),
                    "native_arrange_marriage", retry == Nil.INSTANCE ? "submit the first currently valid native ruler marriage choice"
                            : "submit a fresh valid candidate after the previous proposal was explicitly refused or invalidated", Purpose.WORLD_ACTION);
        }
        BigInteger anchor = attempt.filter(value -> "retry".equals(string(value.get("status")))).map(value -> integer(value.get("retry_index"))).orElse(BigInteger.ZERO);
        String query = Query.RULER_CHOICES.operation().value();
        BigInteger last = FamilyHistory.latest(history, query, false), success = FamilyHistory.latest(history, query, true), advance = FamilyHistory.latestAdvance(history);
        long count = 0; Optional<Obj> latestResult = Optional.empty();
        for (int i = 0; i < history.size(); i++) if (query.equals(FamilyHistory.command(history.get(i)))) {
            if (FamilyHistory.index(history.get(i), i).compareTo(anchor) > 0) count++;
            latestResult = FamilyHistory.result(history.get(i));
        }
        boolean lostCache = success.compareTo(anchor) > 0 && success.equals(last) && latestResult.isPresent()
                && latestResult.get().get("arrange_marriage_choices") instanceof Arr cached && !cached.items().isEmpty();
        if (count < 3 && (last.compareTo(anchor) <= 0 || !success.equals(last) || advance.compareTo(last) > 0 || lostCache)) {
            try {
                read(request, Query.RULER_CHOICES, obj("expected_revision", snapshot.get("revision")));
                return new Refresh("actual native ruler choices read; refresh current observation before selecting a command");
            } catch (MissingInput missing) { return incomplete(missing.getMessage()); }
        }
        if (count < 3 && last.compareTo(advance) > 0)
            return select(request, previous, "life-advance", obj(), detail, "native_arrange_marriage_refresh",
                    "the latest native marriage query was empty; advance once before refreshing it", Purpose.DATE_ADVANCE);
        return new Keep("bounded native ruler marriage discovery exhausted or not due");
    }
    private Decision family(PlanningRequest request, Draft previous, Documents docs,Optional<BigInteger> actualCandidate) {
        Obj snapshot = request.observations().snapshot(); boolean wartime = request.observations().warInProgress();
        if (!eligible(previous, wartime)) return new Keep("current ordinary action precedes optional fresh family selection");
        boolean fulfillmentPending = docs.family().get("pending") instanceof Obj originalPending && yes(originalPending.get("fulfill_existing_betrothal"));
        Decision pending = pending(request, previous, docs.family(), docs, Query.FAMILY_RESULT, "family_marriage", fulfillmentPending);
        if (pending != null) return pending;
        ObservedRead relationRead = readObserved(request, Query.CURRENT_RELATION, obj("expected_native_revision", snapshot.get("native_revision")));
        Obj relation = relationRead.value();
        if (!"available".equals(string(relation.get("status")))) throw new MissingInput("current first-heir native relationship unavailable");
        requireSameNative(relation, snapshot);
        Obj detail = previous.detail().with("family_marriage_current_relationship", relation);
        Obj resolved = docs.family().get("resolved") instanceof Obj value && sameEpisode(value, snapshot) ? value : null;
        Set<BigInteger> rejected = new HashSet<>();
        if (resolved != null) {
            boolean warm = docs.bridge().matches(resolved, "post_");
            if (oneOf(resolved.get("status"), "refused", "invalidated") && unpartnered(relation) && warm
                    && eq(resolved.get("heir_character_id"), relation.get("heir_character_id"))) {
                rejected.addAll(candidateHistory(object(resolved.get("source_pending")), "prior_rejected_candidate_ids"));
                rejected.add(positive(resolved.get("candidate_character_id")));
            } else if (material(resolved) && eq(resolved.get("heir_character_id"), relation.get("heir_character_id"))
                    && relationContains(relation, resolved.get("candidate_character_id"))) {
                boolean warmMarriage = warm && "betrothal".equals(string(resolved.get("status")))
                        && (eq(relation.get("primary_spouse_character_id"), resolved.get("candidate_character_id"))
                        || array(relation.get("spouse_character_ids")).contains(resolved.get("candidate_character_id")));
                if (warmMarriage) {
                    if (!materials.consume(request, Query.CURRENT_RELATION, relationRead.receipt().request().arguments(), relationRead))
                        return incomplete("actual warm marriage relation could not update the original family ledger");
                    return new Refresh("actual warm betrothal-to-marriage relation consumed; refresh canonical head before alliance read");
                }
                Decision resolution = resolution(request, previous, resolved, docs, Query.FAMILY_RESULT, Query.FAMILY_ALLIANCE, "family_marriage");
                if (resolution != null) return resolution;
                detail = detail.with("family_marriage_result_consumed", resolved);
                boolean originalBetrothal = "betrothal".equals(string(resolved.get("status")))
                        && eq(relation.get("betrothed_character_id"), resolved.get("candidate_character_id"))
                        && !yes(object(resolved.get("source_pending")).get("fulfill_existing_betrothal"));
                if (!settings.fulfillCurrentBetrothal() || !originalBetrothal)
                    return education(request, previous, relation, detail);
            } else if (!warm && !material(resolved)) throw new MissingInput("cold prior refusal is not established in current Bridge process");
        }
        if (settings.fulfillCurrentBetrothal() && relation.get("betrothed_character_id") != Nil.INSTANCE) {
            if(actualCandidate.isPresent())throw new MissingInput("M5 alternative source changed to an existing betrothal; the old proposal cannot be prepared");
            Obj input = obj("schema", t(BetrothalValueCodec.SCHEMA), "snapshot", snapshot, "relationship", relation);
            Obj choice = decode(BetrothalValueCodec.encodeChoice(BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(bytes(input)))));
            detail = detail.with("current_betrothal_choice", choice).with("current_betrothal_relationship", relation).with("current_betrothal_status", choice.get("status"));
            if ("selected".equals(string(choice.get("status")))) return select(request, previous,
                    "submit-current-first-heir-betrothal-fulfillment-v1-private", obj("relationship", relation, "choice", choice), detail,
                    "current_first_heir_betrothal_fulfillment", "fulfill the existing native-current bilateral betrothal", Purpose.WORLD_ACTION);
            return education(request, previous, relation, detail);
        }
        if (!unpartnered(relation)) return education(request, previous, relation, detail);
        ObservedRead legalityRead = readObserved(request, Query.HEIR_LEGALITY, obj("expected_native_revision", snapshot.get("native_revision")));
        Obj legality = legalityRead.value();
        if (!"available".equals(string(legality.get("status")))) throw new MissingInput("first-heir legality unavailable");
        requireSameNative(legality, snapshot);
        if (!eq(legality.get("observed_first_heir_character_id"), relation.get("heir_character_id"))) throw new IllegalArgumentException("first-heir legality crossed current relation");
        Arr exclusions = new Arr(rejected.stream().sorted().<Value>map(IntegerValue::new).toList());
        var intake = HeirCandidateIntakeConsumerPort.evaluate(bytes(obj("legal_rows", legality.get("native_legal_candidates"), "rejected_candidate_ids", exclusions)));
        Obj intakeResult = decode(intake.result());
        detail = detail.with("family_marriage_intake", intakeResult).with("family_marriage_legality", legality);
        if (intake.nextRichCandidateIds().isEmpty()) return education(request, previous, relation, detail);
        List<BigInteger> ids = intake.nextRichCandidateIds().get();
        Obj projection = read(request, Query.HEIR_PROJECTION, obj("legality", legality, "legality_read", originalRef(legalityRead.originalReceipt()),
                "candidate_character_ids", new Arr(ids.stream().<Value>map(IntegerValue::new).toList())));
        if (!"available".equals(string(projection.get("status")))) throw new MissingInput("exact five rich native candidate rows unavailable");
        requireSameNative(projection, snapshot);
        for (Value raw : array(projection.get("rows"))) {
            Obj row = object(raw);
            if (!eq(row.get("heir_character_id"), relation.get("heir_character_id")) || !ids.contains(positive(row.get("candidate_character_id")))
                    || !eq(row.get("heir_betrothed_character_id"), relation.get("betrothed_character_id"))
                    || !eq(row.get("heir_primary_spouse_character_id"), relation.get("primary_spouse_character_id"))
                    || !eq(row.get("heir_spouse_character_ids"), relation.get("spouse_character_ids")))
                throw new IllegalArgumentException("projection crossed current heir or exact shortlist");
        }
        var ranking = HeirCandidateRankingConsumerPort.evaluate(HeirCandidateRankingConsumerPort.decode(bytes(obj("legality", legality,
                "projection", projection, "rejected_candidate_ids", exclusions))));
        Value choices = org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(ranking.choices());
        detail = detail.with("family_marriage_choices", choices).with("family_marriage_diagnostics", org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(ranking.rejectionReasons()));
        Obj choice = array(choices).isEmpty() ? null : object(array(choices).get(0));
        boolean dynasty = request.observations().campaignGoal().isPresent();
        if (dynasty && choice != null) {
            Value ordered = org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(HeirPreferenceCodec.prioritize(bytes(obj("choices", choices, "rows", projection.get("rows")))));
            List<Value> previews = new ArrayList<>();
            for (Value raw : array(ordered)) {
                Obj candidate = object(raw); Obj projected = array(projection.get("rows")).stream().map(FamilyJson::object)
                        .filter(row -> eq(row.get("candidate_character_id"), candidate.get("candidate_character_id"))).findFirst().orElseThrow();
                Obj previewObservation = read(request, Query.CHILD_HOUSE_PREVIEW, obj("expected_revision", snapshot.get("revision"),
                        "subject_character_id", legality.get("observed_first_heir_character_id"), "candidate_character_id", candidate.get("candidate_character_id"),
                        "request_matrilineal_option", projected.get("matrilineal_option_selected")));
                previews.add(previewObservation);
                Obj preview = object(previewObservation.get("native_child_house_preview"));
                if ("available".equals(string(preview.get("status"))) && yes(preview.get("complete_can_send"))
                        && eq(preview.get("dynasty_id"), projected.get("played_dynasty_id"))) break;
            }
            Obj lineage = decode(HeirLineageConsumerPort.evaluate(bytes(obj("snapshot", snapshot, "legality", legality, "projection", projection,
                    "choices", choices, "previews", rows(previews)))).result());
            choice = lineage.get("choice") instanceof Obj selected ? selected : null; detail = detail.with("family_marriage_lineage", lineage);
            // The original producer admits only the actual Native lineage result for this goal.
            // Its other ranked candidates do not acquire dynasty-continuity qualification.
            choices = new Arr(choice == null ? List.of() : List.of(choice));
        }
        if(actualCandidate.isPresent()) {
            BigInteger selected=actualCandidate.orElseThrow();
            if(dynasty) {
                if(choice==null||!eq(choice.get("candidate_character_id"),new IntegerValue(selected)))
                    throw new MissingInput("M5 alternative is absent from the actual Native lineage-selected source");
            } else {
                List<Obj> observed=array(choices).stream().map(FamilyJson::object).filter(row->eq(row.get("candidate_character_id"),new IntegerValue(selected))).toList();
                if(observed.size()!=1)throw new MissingInput("M5 selected alternative is absent or duplicated in the actual fresh ranked source");
                choice=observed.getFirst();
            }
        }
        Obj diagnostic = decode(HeirCandidateDiagnosticConsumerPort.project(bytes(obj("legality", legality, "projection", projection, "snapshot", snapshot,
                "choice", nil(choice), "ranking", intakeResult.get("ranking"), "rejected_candidate_ids", exclusions))));
        detail = detail.with("family_marriage_private_diagnostic", diagnostic).with("family_marriage_valued_choices", choices);
        if (choice == null) return education(request, previous, relation, detail.with("family_marriage_status", t("no_positive_observed_marriage_opportunity")));
        Obj args = obj("choice", choice, "legality", legality, "projection", projection, "relationship", relation);
        return select(request, previous, "submit-observed-first-heir-marriage-v1-private", args,
                detail.with("family_marriage_choice", choice).with("family_marriage_legality", legality).with("family_marriage_projection", projection)
                        .with("family_marriage_rejected_candidate_ids", exclusions).with("family_marriage_war_context", warContext(snapshot, choice)),
                "first_heir_marriage_typed_submit", "submit one exact native-final unpartnered first-heir proposal", Purpose.WORLD_ACTION);
    }
    private Decision education(PlanningRequest request, Draft previous, Obj relation, Obj detail) {
        return FamilyEducationPolicy.evaluate(this, request, previous, relation, detail, settings.childFocusEnabled());
    }
    static boolean eligible(Draft previous, boolean wartime) {
        String selected = selected(previous);
        return "life-advance".equals(selected) || wartime && selected != null && selected.startsWith("query-")
                || !wartime && selected != null && selected.startsWith("declare-war-");
    }
    static String selected(Draft previous) {
        return previous.command().map(command -> command.operation().value()).orElseGet(() -> string(previous.detail().get("selected_step")));
    }
    Obj read(PlanningRequest request, Query query, Obj arguments) {
        return readObserved(request, query, arguments).value();
    }
    ObservedRead readObserved(PlanningRequest request, Query query, Obj arguments) {
        Obj submittedArguments = arguments; PlanningReadResult<Obj> result;
        if (reads.projected(query).isPresent()) {
            var observed = reads.projected(query).orElseThrow().read(request, arguments);
            submittedArguments = observed.canonicalArguments(); result = observed.result();
        } else {
            var contract = reads.find(query).orElseThrow(() -> new MissingInput("actual Root read contract absent: " + query.operation().value()));
            result = reader.read(contract, new PlanningReadRequest(request.before(), request.source(), request.sessionId(), query.operation(), arguments, request.deadline()));
        }
        if (result instanceof PlanningReadResult.Known<Obj> known) {
            var observed = known.receipt().request();
            if (!observed.before().equals(request.before()) || !observed.source().equals(request.source()) || !observed.sessionId().equals(request.sessionId())
                    || !observed.operation().equals(query.operation()) || !observed.arguments().equals(submittedArguments)) throw new IllegalArgumentException("family read receipt crossed actual request");
            return new ObservedRead(known.value(), known.receipt(), known.originalReceipt());
        }
        throw new MissingInput("native family read unavailable: " + query.operation().value());
    }
    static Obj originalRef(ExactRef ref) { return obj("path", t(ref.path()), "bytes", n(ref.bytes()), "sha256", t(ref.sha256())); }
    Decision select(PlanningRequest request, Draft previous, String step, Obj args, Obj detail, String phase, String reason, Purpose purpose) {
        OperationKey operation = new OperationKey(step);
        if (!request.observations().actionSteps().contains(operation)) return incomplete("selected family operation is not executable: " + step);
        Obj plan = detail.with("policy", t("one-life-turn-v1")).with("phase", t(phase)).with("reason", t(reason)).with("selected_step", t(step));
        Optional<ActionCommand> prepared = commands.prepare(request, operation, args, plan);
        if (prepared.isEmpty()) return incomplete("actual family preparation/postcondition binding absent: " + step);
        ActionCommand command = prepared.get();
        if (!command.operation().equals(operation) || !command.before().equals(request.before()) || !command.source().equals(request.source())
                || !command.sessionId().equals(request.sessionId())) throw new IllegalArgumentException("family command factory crossed action/frame/source");
        return new Replace(new Draft("one-life-turn-v1", phase, reason, Kind.ORDINARY, prepared, purpose, previous.domain(), plan), reason);
    }
    Decision annotate(Draft previous, Obj detail) {
        return new Replace(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(), previous.purpose(), previous.domain(), detail), "preserve complete family observations");
    }
    Decision pending(PlanningRequest request, Draft previous, Obj ledger, Documents docs, Query query, String prefix, boolean checkpointAware) {
        if (!(ledger.get("pending") instanceof Obj pending)) return null;
        Obj snapshot = request.observations().snapshot();
        if (!sameEpisode(pending, snapshot)) return incomplete("unresolved family proposal belongs to a different episode");
        if (yes(pending.get("fulfill_existing_betrothal")) && !eq(pending.get("played_character_id"), object(snapshot.get("played_character")).get("character_id")))
            return incomplete("pending fulfillment actor differs from current ruler");
        if (query == Query.FAMILY_RESULT && !checkpointAware) {
            Obj encoded = obj("schema", t(MarriagePendingConsumerPort.SCHEMA), "planned", obj("plan", previous.detail()), "snapshot", snapshot,
                    "ledger", ledger, "bridge_identity", obj("pid", n(docs.bridge().pid()), "creation_date", t(docs.bridge().creationDate())));
            var decision = MarriagePendingReadPolicy.decide(MarriagePendingConsumerPort.decode(bytes(encoded)));
            if (decision instanceof MarriagePendingModel.ReadResult result)
                return materialRead(request, query, obj("pending", pending, "cold", new Bool(result.coldRecovery()), "expected_revision", snapshot.get("revision")), "read exact family proposal resolution before another send");
            if (decision instanceof MarriagePendingModel.OtherEpisode) return incomplete("unresolved family proposal belongs to another episode");
            return annotate(previous, previous.detail().with(prefix + "_pending", pending).with(prefix + "_status", t(yes(pending.get("cold_absent_relation_unresolved")) ? "cold_absent_relation_unresolved" : "await_later_paused_frame")));
        }
        boolean cold = !docs.bridge().matches(pending, "source_"), checked = docs.bridge().matches(pending, "last_checked_");
        Value last = pending.get("last_checked_native_revision"); if (last == null) last = pending.get("pre_native_revision");
        BigInteger revision = integer(last);
        if (checkpointAware && checked && pending.get("last_consumed_checkpoint_native_revision") instanceof IntegerValue consumed) revision = revision.max(consumed.value());
        Value dateValue = pending.get("last_consumed_checkpoint_date_raw");
        if (dateValue == null && yes(pending.get("fulfill_existing_betrothal"))) {
            dateValue = pending.get("last_checked_date_raw"); if (dateValue == null) dateValue = pending.get("source_date_raw");
        }
        boolean laterDate = checkpointAware && checked && dateValue instanceof IntegerValue date && integer(snapshot.get("date_raw")).compareTo(date.value()) > 0;
        if (cold && !checked || integer(snapshot.get("native_revision")).compareTo(revision) > 0 || laterDate)
            return materialRead(request, query, obj("pending", pending, "cold", new Bool(cold), "expected_revision", snapshot.get("revision")), cold ? "cold bilateral result recheck" : "later paused bilateral result read");
        return annotate(previous, previous.detail().with(prefix + "_pending", pending).with(prefix + "_status", t("await_later_paused_frame")));
    }
    Decision resolution(PlanningRequest request, Draft previous, Obj resolved, Documents docs, Query resultQuery, Query allianceQuery, String prefix) {
        if (!material(resolved)) return null;
        if (!docs.bridge().matches(resolved, "post_")) return materialRead(request, resultQuery,
                obj("pending", object(resolved.get("source_pending")), "cold", new Bool(true), "material_recheck", new Bool(true), "expected_revision", request.observations().snapshot().get("revision")), "re-read actual material pair in current Bridge process");
        Obj source = object(resolved.get("source_pending")); Value recipient = source.get("recipient_character_id");
        Value actor = object(request.observations().snapshot().get("played_character")).get("character_id");
        if (eq(recipient, actor) && eq(source.get("played_character_id"), actor)) return null;
        boolean family = prefix.equals("family_marriage");
        Value alliance = resolved.get(family ? "alliance_result" : "actual_alliance_result");
        boolean currentAlliance = alliance instanceof Obj observed
                && docs.bridge().matches(family ? observed : resolved, family ? "" : "alliance_");
        if (recipient instanceof IntegerValue && !currentAlliance)
            return materialRead(request, allianceQuery, obj("resolved", resolved, "expected_revision", request.observations().snapshot().get("revision")), "read actual bilateral alliance after material relation");
        return null;
    }
    Decision materialRead(PlanningRequest request, Query query, Obj arguments, String reason) {
        ObservedRead observed = readObserved(request, query, arguments);
        if (!materials.consume(request, query, arguments, observed)) return incomplete("actual family read exists but sole-writer imported-document reducer is unavailable");
        return new Refresh(reason + "; refresh canonical head and current observation");
    }
    static Set<BigInteger> candidateHistory(Obj source, String field) {
        Value raw = source.get(field); if (raw == null) return Set.of();
        Set<BigInteger> ids = new HashSet<>(); for (Value item : array(raw)) if (!ids.add(positive(item))) throw new IllegalArgumentException("duplicate family candidate history");
        return Set.copyOf(ids);
    }
    static void requireSameNative(Obj result, Obj snapshot) {
        if (!eq(result.get("native_revision"), snapshot.get("native_revision"))) throw new IllegalArgumentException("family native observation crossed paused frame");
    }
    static boolean relationContains(Obj relation, Value partner) {
        return eq(relation.get("betrothed_character_id"), partner) || eq(relation.get("primary_spouse_character_id"), partner)
                || relation.get("spouse_character_ids") instanceof Arr spouses && spouses.items().contains(partner);
    }
    static Obj warContext(Obj snapshot, Obj choice) {
        return obj("active_wars", snapshot.get("active_wars"), "treasury_observed", nil(snapshot.get("played_character_gold")),
                "future_war_cash_reserve_raw", Nil.INSTANCE, "prospective_ally_war_obligation", t("unknown"), "proposal", choice);
    }
    static Decision incomplete(String reason) { return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, reason); }
    private static Decision optionalMissing(PlanningRequest request, Draft previous, Documents docs, String reason) {
        return previous.command().isPresent()
                && (request.observations().warInProgress() || !retainedFamilyWork(docs, previous))
                ? new Defer(reason, previous.detail().with("family_unavailable", t(reason))) : new Wait(reason);
    }
    private static boolean retainedFamilyWork(Documents docs, Draft previous) {
        for (Obj domain : List.of(docs.family(), docs.matrilineal(), docs.childDefault()))
            if (domain.get("pending") != Nil.INSTANCE || domain.get("resolved") != Nil.INSTANCE) return true;
        for (String field : List.of("family_marriage_pending", "current_betrothal_pending")) {
            Value value = previous.detail().get(field);
            if (value != null && value != Nil.INSTANCE) return true;
        }
        return false;
    }
    static final class MissingInput extends RuntimeException {
        private static final long serialVersionUID = 1L;
        MissingInput(String message) { super(message); }
    }
}

