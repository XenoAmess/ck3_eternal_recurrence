package org.xar.ck3.control.wave2.military.holyreinf;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.military.projection.HolyInputValidation.require;
import org.xar.ck3.control.wave2.military.projection.HolyInputValidation;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement.*;

/** Central strict boundary. SDK snapshots/contexts are declared projections with additive fields allowed. */
public final class HolyReinforcementCodec {
    public static final String CHOOSE_SCHEMA = "xar.ck3.holy-reinforcement-choose-input.v1";
    public static final String PLAN_SCHEMA = "xar.ck3.holy-reinforcement-plan-input.v1";
    public static final String POST_SCHEMA = "xar.ck3.holy-reinforcement-post-input.v1";
    public static final int BYTE_BUDGET = 131_072;
    private static final long U32 = 0xffff_ffffL;
    private static final String SHA3 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String SHA4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private HolyReinforcementCodec() { }

    public static byte[] choose(byte[] input) { return StrictJson.canonical(chooseNode(input), BYTE_BUDGET); }
    public static ObjectNode chooseNode(byte[] input) {
        ObjectNode root = envelope(input, CHOOSE_SCHEMA, Set.of("schema", "snapshot", "plan", "holy_context"));
        Snapshot snapshot = snapshot(root.get("snapshot")); Plan plan = plan(root.get("plan"));
        Context context = siegeNeed(snapshot, plan) == null ? null : context(root.get("holy_context"), snapshot);
        return proposal(HolyReinforcement.choose(snapshot, plan, context));
    }

    /** Reuses the actual selected proposal in the ordinary planner's two branches and preserves its other fields. */
    public static byte[] plan(byte[] input) { return StrictJson.canonical(planNode(input), BYTE_BUDGET); }
    public static ObjectNode planNode(byte[] input) {
        ObjectNode root = envelope(input, PLAN_SCHEMA, Set.of("schema", "snapshot", "planned", "bridge_capabilities",
                "query_available", "holy_context", "query_error"));
        Snapshot snapshot = snapshot(root.get("snapshot")); ObjectNode planned = obj(root.get("planned"));
        JsonNode oldPlan = planned.get("plan"); ObjectNode out = planned.deepCopy();
        boolean queryAvailable = bool(root.get("query_available")); String queryError = nullableMessage(root.get("query_error"));
        List<String> capabilities = strings(root.get("bridge_capabilities"));
        if (!(oldPlan instanceof ObjectNode) || siegeNeed(snapshot, plan(oldPlan)) == null
                || !capabilities.contains(CAPABILITY) || !queryAvailable) { return out; }
        ObjectNode changed = ((ObjectNode) oldPlan).deepCopy(); out.set("plan", changed);
        if (queryError != null) {
            ObjectNode unavailable = StrictJson.object().put("status", "input_unavailable").put("reason", queryError);
            changed.set("holy_order_reinforcement_observation", unavailable);
        } else {
            try {
                Proposal result = HolyReinforcement.choose(snapshot, plan(oldPlan), context(root.get("holy_context"), snapshot));
                if (result.status() != Status.ACTIONABLE) { changed.set("holy_order_reinforcement_observation", proposal(result)); }
                else {
                    changed.put("phase", "native_war_holy_order_siege_reinforcement").put("selected_step", STEP)
                            .put("reason", "current native legal order troops cover the observed blocked-siege deficit");
                    changed.set("holy_order_hire_proposal", proposal(result)); changed.set("deferred_siege_plan", oldPlan.deepCopy());
                }
            } catch (ProjectionDomainRejection error) {
                changed.set("holy_order_reinforcement_observation", StrictJson.object().put("status", "input_unavailable").put("reason", error.getMessage()));
            }
        }
        return out;
    }

    /** Existing writer/driver supplies independent query results. This adapter never executes or retries an action. */
    public static byte[] postcondition(byte[] input) { return StrictJson.canonical(postconditionNode(input), BYTE_BUDGET); }
    public static ObjectNode postconditionNode(byte[] input) {
        ObjectNode root = envelope(input, POST_SCHEMA, Set.of("schema", "before_snapshot", "plan", "before_context", "ack",
                "after_snapshot", "after_context", "army_strengths", "actor_expenses", "expense_query_error", "post_query_error"));
        Snapshot before = snapshot(root.get("before_snapshot")); Plan plan = plan(root.get("plan"));
        Proposal valued = HolyReinforcement.choose(before, plan, context(root.get("before_context"), before));
        return finishPost(valued, root, false);
    }

    private static ObjectNode finishPost(Proposal valued, ObjectNode root, boolean actualSelectedProposal) {
        ObjectNode ack = obj(root.get("ack")); boolean accepted = Boolean.TRUE.equals(optionalBool(ack.get("accepted")));
        Snapshot after = null; Context afterContext = null; List<ArmyStrength> strengths = List.of();
        if (accepted && !nullish(root.get("after_snapshot")) && !nullish(root.get("after_context"))) {
            after = snapshot(root.get("after_snapshot")); afterContext = context(root.get("after_context"), after);
            strengths = armyStrengths(root.get("army_strengths"));
        }
        Postcondition result = comparePost(valued, accepted, after, afterContext, strengths);
        ObjectNode receipt = post(result); JsonNode expense = root.get("actor_expenses");
        if (result.employerObserved()) {
            // The domain uses a typed projection; this validated SDK observer remains byte-domain complete at its output boundary.
            for (JsonNode row : root.path("after_context").path("rows")) {
                if (reference(row.get("holy_order_id")) == result.holyOrderId()) {
                    JsonNode association = row.path("military_terms").get("troop_association");
                    receipt.set("troop_association", association == null ? receipt.nullNode() : association.deepCopy());
                }
            }
        }
        receipt.set("actor_expenses", expense.deepCopy());
        receipt.set("expense_query_error", root.get("expense_query_error").deepCopy());
        nullableMessage(root.get("expense_query_error"));
        String queryError = nullableMessage(root.get("post_query_error"));
        if (queryError != null && accepted) {
            if (!actualSelectedProposal) { require(result.nextFormal() == null, "post-query error cannot carry a completed usable-army query"); }
            receipt.putNull("next_formal");
            receipt.put("status", "verification_pending").put("post_query_error", queryError);
        }
        ObjectNode output = ack.deepCopy(); output.set("holy_order_reinforcement_postcondition", receipt);
        return output;
    }


    /** Decodes an actual earlier selected proposal; it never reconstructs a before snapshot/context. */
    public static Proposal selectedProposal(JsonNode value) {
        ObjectNode p = HolyInputValidation.object(value, Set.of("schema", "status", "source_frame", "military_need",
                "selected_step", "candidate_rows", "before_resource_stocks_raw", "holy_order_id", "source_ordinal",
                "prior_employer_id", "native_quote_raw", "current_soldiers", "ranking_policy", "original_ai_ranking_observed"));
        require(SCHEMA.equals(text(p.get("schema"))) && "actionable".equals(text(p.get("status")))
                && STEP.equals(text(p.get("selected_step"))) && "lowest_native_piety_then_gold_prestige_full_id".equals(text(p.get("ranking_policy")))
                && !bool(p.get("original_ai_ranking_observed")), "valued current proposal required");
        ObjectNode f = HolyInputValidation.object(p.get("source_frame"), Set.of("snapshot_id", "revision", "native_revision", "date_raw", "played_character_id"));
        Frame frame = new Frame(nullableText(f.get("snapshot_id")), integerOrNull(f.get("revision")),
                integerOrNull(f.get("native_revision")), integerOrNull(f.get("date_raw")), referenceOrNull(f.get("played_character_id")));
        ObjectNode n = HolyInputValidation.object(p.get("military_need"), Set.of("war_id", "target_province_id", "garrison_size", "besieging_strength", "additional_soldiers_required"));
        Need need = new Need(integer(n.get("war_id")), integer(n.get("target_province_id")), integer(n.get("garrison_size")),
                integer(n.get("besieging_strength")), integer(n.get("additional_soldiers_required")));
        ObjectNode s = HolyInputValidation.object(p.get("before_resource_stocks_raw"), Set.of("gold", "prestige", "piety"));
        Stocks stocks = new Stocks(integerOrNull(s.get("gold")), integerOrNull(s.get("prestige")), integerOrNull(s.get("piety")));
        List<CandidateEvaluation> candidates = new ArrayList<>();
        for (JsonNode item : array(p.get("candidate_rows"))) {
            ObjectNode c = HolyInputValidation.object(item, Set.of("holy_order_id", "source_ordinal", "can_hire", "can_afford",
                    "can_hire_reason_literal", "can_afford_reason_literal", "status", "reason"));
            String reason = nullableText(c.get("reason"));
            require((reason == null ? "eligible" : "not_selected").equals(text(c.get("status"))), "candidate status differs");
            candidates.add(new CandidateEvaluation(reference(c.get("holy_order_id")), (int) HolyInputValidation.integer(c.get("source_ordinal"), 0, Integer.MAX_VALUE),
                    optionalBool(c.get("can_hire")), optionalBool(c.get("can_afford")), nullableText(c.get("can_hire_reason_literal")),
                    nullableText(c.get("can_afford_reason_literal")), reason));
        }
        List<BigInteger> quote = integers(p.get("native_quote_raw")); require(quote.size() == 10, "ten native resources required");
        Selection selected = new Selection(reference(p.get("holy_order_id")), (int) HolyInputValidation.integer(p.get("source_ordinal"), 0, Integer.MAX_VALUE),
                referenceOrNull(p.get("prior_employer_id")), quote, (int) HolyInputValidation.integer(p.get("current_soldiers"), Integer.MIN_VALUE, Integer.MAX_VALUE));
        return new Proposal(Status.ACTIONABLE, frame, need, stocks, null, candidates, selected);
    }

    public static final String SELECTED_POST_SCHEMA = "xar.ck3.holy-reinforcement-selected-post-input.v1";
    public static ObjectNode selectedPostNode(byte[] input) {
        ObjectNode root = selectedPostEnvelope(input);
        return finishPost(selectedProposal(root.get("proposal")), root, true);
    }

    /** Only a transport read directive; the original driver retains every send/permission guard. */
    public static ObjectNode selectedPostReadDirective(byte[] input) {
        ObjectNode root = selectedPostEnvelope(input); Proposal valued = selectedProposal(root.get("proposal"));
        boolean accepted = Boolean.TRUE.equals(optionalBool(obj(root.get("ack")).get("accepted")));
        Snapshot after = null; Context context = null;
        if (accepted && !nullish(root.get("after_snapshot")) && !nullish(root.get("after_context"))) {
            after = snapshot(root.get("after_snapshot")); context = context(root.get("after_context"), after);
        }
        Postcondition comparison = comparePost(valued, accepted, after, context, List.of());
        boolean references = comparison.troopAssociation() != null && comparison.troopAssociation().rows().stream()
                .anyMatch(row -> row.available() && row.nativeCarmyResolved() && row.nativeCarmyId() != null);
        ObjectNode out = StrictJson.object(); boolean query = references && after != null && !after.playerArmies().isEmpty();
        out.put("query_army_strengths", query); ArrayNode ids = out.putArray("army_ids");
        if (query) { after.playerArmies().stream().map(PublicArmy::armyId).distinct().forEach(ids::add); }
        put(out, "expected_revision", after == null ? null : after.frame().revision()); return out;
    }

    private static ObjectNode selectedPostEnvelope(byte[] input) {
        return envelope(input, SELECTED_POST_SCHEMA, Set.of("schema", "proposal", "ack", "after_snapshot", "after_context",
                "army_strengths", "actor_expenses", "expense_query_error", "post_query_error"));
    }

    public static Snapshot snapshot(JsonNode value) {
        ObjectNode node = obj(value); JsonNode actor = node.get("played_character");
        ObjectNode played = actor instanceof ObjectNode ? (ObjectNode) actor : null;
        Frame frame = new Frame(nullableText(node.get("snapshot_id")), integerOrNull(node.get("revision")),
                integerOrNull(node.get("native_revision")), integerOrNull(node.get("date_raw")),
                played == null ? null : referenceOrNull(played.get("character_id")));
        List<BigInteger> wars = null;
        if (!nullish(node.get("active_wars"))) {
            wars = new ArrayList<>(); for (JsonNode row : array(node.get("active_wars"))) {
                if (row instanceof ObjectNode && !nullish(row.get("war_id"))) { wars.add(integer(row.get("war_id"))); }
            }
        }
        List<PublicArmy> armies = new ArrayList<>();
        if (!nullish(node.get("player_armies"))) {
            for (JsonNode row : array(node.get("player_armies"))) {
                if (row instanceof ObjectNode) { armies.add(new PublicArmy(reference(row.get("army_id")),
                        referenceOrNull(row.get("owner_character_id")), optionalBool(row.get("controllable")),
                        referenceOrNull(row.get("current_province_id")))); }
            }
        }
        String version = null, sha = null; JsonNode diagnostics = node.path("diagnostics").path("hello");
        if (diagnostics instanceof ObjectNode) {
            version = nullableText(diagnostics.has("expected_ck3_version") ? diagnostics.get("expected_ck3_version") : diagnostics.get("game_version"));
            sha = nullableText(diagnostics.has("expected_ck3_sha256") ? diagnostics.get("expected_ck3_sha256") : diagnostics.get("executable_sha256"));
            if (sha != null) { sha = sha.toUpperCase(Locale.ROOT); }
        }
        return new Snapshot(frame, optionalBool(node.get("paused")), optionalBool(node.get("map_ready")),
                played == null ? null : optionalBool(played.get("alive")), wars,
                new Stocks(stock(node.get("played_character_gold")), stock(node.get("played_character_prestige")),
                        stock(node.get("played_character_piety"))), armies, version, sha);
    }

    public static Plan plan(JsonNode value) {
        ObjectNode node = obj(value); Siege siege = null;
        if (node.get("siege_state") instanceof ObjectNode row) {
            siege = new Siege(nullableText(row.get("status")), optionalBool(row.get("player_army_besieging")),
                    integerOrNull(row.get("province_id")), integerOrNull(row.get("garrison_size")), integerOrNull(row.get("besieging_strength")));
        }
        JsonNode pursuit = node.get("pursuit");
        return new Plan(nullableText(node.get("phase")), nullableText(node.get("selected_step")), siege,
                pursuit instanceof ObjectNode ? integerOrNull(pursuit.get("war_id")) : null);
    }

    /** Full original domain-normalizer closure, including optional independent observer families. */
    public static Context context(JsonNode value, Snapshot snapshot) {
        ObjectNode node = obj(value); String version = text(node.get("game_version")), sha = text(node.get("executable_sha256")).toUpperCase(Locale.ROOT);
        require((version.equals("1.20.0.3") && sha.equals(SHA3)) || (version.equals("1.20.0.4") && sha.equals(SHA4)), "native source does not match frozen exact build");
        require(version.equals(snapshot.version()) && sha.equals(snapshot.sha()), "native holy-order context belongs to another build");
        require(text(node.get("schema")).equals(version.equals("1.20.0.3") ? "ck3_12003_player_holy_order_context_v1" : "ck3_12004_player_holy_order_context_v1"), "native holy-order schema malformed");
        long actor = reference(node.get("played_character_id"));
        require(Objects.equals(actor, snapshot.frame().playedCharacterId()) && Objects.equals(integer(node.get("date_raw")), snapshot.frame().dateRaw()), "native holy-order context differs from queried frame");
        scale(node.get("raw_scale")); require(bool(node.get("read_only")), "holy-order query must be read only");
        require(integer(node.get("capture_epoch")).signum() > 0, "positive capture epoch required");
        boolean available = availability(node); List<Order> orders = new ArrayList<>();
        for (JsonNode item : array(node.get("rows"))) {
            ObjectNode row = obj(item); long id = reference(row.get("holy_order_id")); reference(row.get("rite_id")); boolean military = bool(row.get("is_military"));
            for (String field : List.of("founder_id", "patron_id", "employer_id")) { referenceOrNull(row.get(field)); }
            for (JsonNode lease : array(row.get("leased_title_ids"))) { reference(lease); }
            Long employer = referenceOrNull(row.get("employer_id")); Terms terms = null;
            if (!military) { require(nullish(row.get("military_terms")), "nonmilitary order has military terms"); }
            else {
                ObjectNode t = obj(row.get("military_terms")); boolean termsAvailable = availability(t); scale(t.get("resource_scale"));
                Boolean hire = optionalBool(t.get("can_hire")), afford = optionalBool(t.get("can_afford"));
                if (termsAvailable) { require(hire != null && afford != null, "available final native predicates required"); }
                List<BigInteger> costs = null;
                if (!nullish(t.get("resource_costs_raw"))) { costs = integers(t.get("resource_costs_raw")); require(costs.size() == 10, "ten native resource costs required"); }
                require(!termsAvailable || costs != null, "available native costs absent");
                for (String prefix : List.of("can_hire", "can_afford")) { reasonLiteral(t, prefix + "_reasons_available", prefix + "_reason_literal"); }
                Strength strength = null;
                if (t.has("troop_strength")) {
                    ObjectNode s = obj(t.get("troop_strength")); boolean ok = availability(s); Integer soldiers = null;
                    if (ok) { soldiers = (int) HolyInputValidation.integer(s.get("current_soldiers"), 0, Integer.MAX_VALUE); }
                    else { require(nullish(s.get("current_soldiers")), "unavailable strength contains soldiers"); }
                    strength = new Strength(ok, nullableText(s.get("unavailable_reason")), soldiers);
                }
                if (t.has("hire_cost_context")) { validateCost(t.get("hire_cost_context")); }
                if (t.has("current_reinforcement_v1")) { validateReinforcement(t.get("current_reinforcement_v1"), employer, actor); }
                if (t.has("current_war_eligibility")) {
                    ObjectNode w = obj(t.get("current_war_eligibility")); boolean ok = availability(w); Boolean qualifies = optionalBool(w.get("qualifies"));
                    require(!ok || qualifies != null, "available war subgate incomplete"); reasonLiteral(w, "reasons_available", "reason_literal");
                    require(!ok || bool(w.get("reasons_available")), "available war subgate reason absent");
                }
                if (t.has("service_lifecycle")) {
                    ObjectNode service = obj(t.get("service_lifecycle")); boolean ok = availability(service), applies = bool(service.get("applies_to_player"));
                    require(applies == Objects.equals(employer, actor), "service lifecycle scope differs");
                    for (String field : List.of("release_eligible", "associated_regiment_in_combat", "release_check_queued")) {
                        Boolean predicate = optionalBool(service.get(field)); require(!ok || !applies || predicate != null, "service lifecycle incomplete");
                        require(applies || predicate == null, "inapplicable service lifecycle contains predicates");
                    }
                }
                Association association = t.has("troop_association") ? association(t.get("troop_association"), employer, actor) : null;
                terms = new Terms(termsAvailable, nullableText(t.get("unavailable_reason")), hire, afford,
                        nullableText(t.get("can_hire_reason_literal")), nullableText(t.get("can_afford_reason_literal")), costs, strength, association);
            }
            orders.add(new Order(id, military, employer, terms));
        }
        return new Context(available, nullableText(node.get("unavailable_reason")), actor,
                integerOrNull(node.get("queried_revision")), integerOrNull(node.get("queried_native_revision")), orders);
    }

    private static Association association(JsonNode value, Long employer, long actor) {
        ObjectNode a = obj(value); boolean available = availability(a), applies = bool(a.get("applies_to_player"));
        require(applies == Objects.equals(employer, actor), "troop association scope differs"); List<AssociationMember> members = new ArrayList<>();
        for (JsonNode item : array(a.get("rows"))) {
            ObjectNode m = obj(item); boolean ok = availability(m);
            require(ok || !available, "available association contains unavailable member");
            members.add(new AssociationMember(reference(m.get("regiment_id")), ok, nullableText(m.get("unavailable_reason")),
                    bool(m.get("regiment_resolved")), referenceOrNull(m.get("native_carmy_id")), bool(m.get("native_carmy_resolved")),
                    referenceOrNull(m.get("combat_id")), bool(m.get("combat_resolved"))));
        }
        require(applies || members.isEmpty(), "inapplicable troop association has rows");
        return new Association(available, nullableText(a.get("unavailable_reason")), applies, members);
    }

    private static void validateCost(JsonNode value) {
        ObjectNode c = obj(value); boolean available = availability(c); bool(c.get("order_title_resolved")); scale(c.get("resource_scale"));
        Long title = referenceOrNull(c.get("order_title_id")); referenceOrNull(c.get("order_title_holder_id"));
        Boolean holder = optionalBool(c.get("title_holder_is_player")), patron = optionalBool(c.get("patron_is_player")), other = optionalBool(c.get("employed_by_other"));
        Long factor = signedOrNull(c.get("selected_patron_multiplier_raw"), Long.MIN_VALUE, Long.MAX_VALUE);
        String branch = nullableText(c.get("cost_branch")); Set<String> branches = Set.of("title_holder_zero", "ordinary", "patron_hire", "patron_recall");
        require(branch == null || branches.contains(branch), "holy-order cost branch malformed"); if (!available) { return; }
        require(title != null && holder != null && branch != null, "available cost context incomplete");
        if (branch.equals("title_holder_zero")) { require(holder && patron == null && other == null && factor == null, "holder exemption sampled later branch"); }
        else {
            require(!holder, "later quote branch conflicts with holder exemption");
            if (branch.equals("ordinary")) { require(Boolean.FALSE.equals(patron) && other == null && factor == null, "ordinary branch contains patron inputs"); }
            else { require(Boolean.TRUE.equals(patron) && other != null && other == branch.equals("patron_recall") && factor != null, "patron cost branch incomplete"); }
        }
    }

    private static void validateReinforcement(JsonNode value, Long employer, long actor) {
        ObjectNode family = obj(value); scale(family.get("fraction_scale")); boolean available = availability(family);
        Long count = signedOrNull(family.get("source_count"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        ArrayNode rows = array(family.get("rows")); require(!available || (count != null && count == rows.size()), "persistent roster count differs");
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = obj(rows.get(index)); ordinal(row.get("source_index"), index); reference(row.get("persistent_regiment_id"));
            boolean resolved = bool(row.get("resolved")), ok = availability(row);
            Long owner = referenceOrNull(row.get("owner_character_id"));
            Long fraction = signedOrNull(row.get("monthly_replenishment_fraction_raw"), Long.MIN_VALUE, Long.MAX_VALUE);
            Long months = signedOrNull(row.get("native_months_to_full"), Integer.MIN_VALUE, Integer.MAX_VALUE);
            require(!ok || !resolved || (owner != null && fraction != null && months != null), "available persistent inputs incomplete");
            ArrayNode chunks = array(row.get("chunks")); require(!resolved || !ok || chunks.size() == 7, "persistent chunk count differs");
            require(resolved || (chunks.isEmpty() && owner == null && fraction == null && months == null), "unresolved persistent reference has actual inputs");
            for (int chunkIndex = 0; chunkIndex < chunks.size(); chunkIndex++) {
                ObjectNode chunk = obj(chunks.get(chunkIndex)); ordinal(chunk.get("chunk_index"), chunkIndex); boolean chunkOk = availability(chunk);
                for (String field : List.of("maximum_soldiers", "current_soldiers", "native_chunk_index", "state_raw")) {
                    require(!chunkOk || !nullish(chunk.get(field)), "available chunk input absent"); signedOrNull(chunk.get(field), Integer.MIN_VALUE, Integer.MAX_VALUE);
                }
                for (String field : List.of("persistent_regiment_id", "army_regiment_id")) {
                    require(!chunkOk || !nullish(chunk.get(field)), "available chunk reference absent"); referenceOrNull(chunk.get(field));
                }
                Long pending = signedOrNull(chunk.get("pending_raw"), 0, 255); require(!chunkOk || pending != null, "available pending raw absent");
                for (String field : List.of("native_can_replenish", "native_chunk_can_replenish")) {
                    Boolean predicate = optionalBool(chunk.get(field)); require(!chunkOk || predicate != null, "independent chunk predicate absent");
                }
            }
        }
        ObjectNode roles = obj(family.get("army_roles")); availability(roles); boolean applies = bool(roles.get("applies_to_player"));
        require(applies == Objects.equals(employer, actor), "Army-role scope differs"); ArrayNode roleRows = array(roles.get("rows"));
        require(applies || roleRows.isEmpty(), "inapplicable Army-role rows present");
        for (int index = 0; index < roleRows.size(); index++) {
            ObjectNode role = obj(roleRows.get(index)); ordinal(role.get("association_index"), index); reference(role.get("army_regiment_id"));
            boolean armyResolved = bool(role.get("army_resolved")), unitResolved = bool(role.get("unit_resolved")), ok = availability(role);
            for (String field : List.of("native_carmy_id", "commander_character_id", "public_army_id", "unit_carmy_backlink", "owner_character_id")) { referenceOrNull(role.get(field)); }
            require(!ok || !armyResolved || (!nullish(role.get("native_carmy_id")) && !nullish(role.get("commander_character_id")) && !nullish(role.get("public_army_id"))), "Army-role fields incomplete");
            require(!unitResolved || (armyResolved && !nullish(role.get("owner_character_id"))), "actual Unit owner incomplete");
        }
    }

    private static List<ArmyStrength> armyStrengths(JsonNode value) {
        if (nullish(value)) { return List.of(); } List<ArmyStrength> result = new ArrayList<>();
        ObjectNode query = obj(value);
        for (JsonNode row : array(query.get("army_strengths"))) { result.add(new ArmyStrength(reference(row.get("army_id")),
                nullableText(row.get("status")), referenceOrNull(row.get("native_carmy_id")), integerOrNull(row.get("current_soldiers")))); }
        return List.copyOf(result);
    }

    public static ObjectNode proposal(Proposal value) {
        ObjectNode out = StrictJson.object().put("schema", SCHEMA).put("status", snake(value.status()));
        out.set("source_frame", frame(value.sourceFrame())); out.set("military_need", need(value.militaryNeed()));
        out.putNull("selected_step"); ArrayNode candidates = out.putArray("candidate_rows");
        for (CandidateEvaluation row : value.candidates()) {
            ObjectNode item = candidates.addObject().put("holy_order_id", row.holyOrderId()).put("source_ordinal", row.sourceOrdinal());
            put(item, "can_hire", row.canHire()); put(item, "can_afford", row.canAfford()); put(item, "can_hire_reason_literal", row.canHireReason());
            put(item, "can_afford_reason_literal", row.canAffordReason()); item.put("status", row.reason() == null ? "eligible" : "not_selected"); put(item, "reason", row.reason());
        }
        if (value.beforeStocks() != null) { out.set("before_resource_stocks_raw", stocks(value.beforeStocks())); }
        if (value.status() == Status.INPUT_UNAVAILABLE) { put(out, "unavailable_reason", value.unavailableReason()); }
        Selection selection = value.selection();
        if (selection != null) {
            out.put("holy_order_id", selection.holyOrderId()).put("source_ordinal", selection.sourceOrdinal()); put(out, "prior_employer_id", selection.priorEmployerId());
            out.set("native_quote_raw", numbers(selection.nativeQuoteRaw())); out.put("current_soldiers", selection.currentSoldiers()).put("selected_step", STEP)
                    .put("ranking_policy", "lowest_native_piety_then_gold_prestige_full_id").put("original_ai_ranking_observed", false);
        }
        return out;
    }
    private static JsonNode need(Need value) {
        if (value == null) { return StrictJson.object().nullNode(); }
        ObjectNode out = StrictJson.object(); put(out, "war_id", value.warId()); put(out, "target_province_id", value.targetProvinceId());
        put(out, "garrison_size", value.garrisonSize()); put(out, "besieging_strength", value.besiegingStrength());
        put(out, "additional_soldiers_required", value.additionalSoldiersRequired()); return out;
    }
    private static ObjectNode frame(Frame value) {
        ObjectNode out = StrictJson.object(); put(out, "snapshot_id", value.snapshotId()); put(out, "revision", value.revision());
        put(out, "native_revision", value.nativeRevision()); put(out, "date_raw", value.dateRaw()); put(out, "played_character_id", value.playedCharacterId()); return out;
    }
    private static ObjectNode stocks(Stocks value) {
        ObjectNode out = StrictJson.object(); put(out, "gold", value.gold()); put(out, "prestige", value.prestige()); put(out, "piety", value.piety()); return out;
    }
    private static ObjectNode post(Postcondition value) {
        ObjectNode out = StrictJson.object().put("schema", "xar.ck3.holy-order-siege-reinforcement-postcondition.v1")
                .put("status", snake(value.status())).put("holy_order_id", value.holyOrderId()).put("employer_observed", value.employerObserved())
                .put("usable_army_observed", value.usableArmyObserved()).put("source", "independent_current_queries").put("full_hire_loop_complete", false);
        out.set("quote_raw", numbers(value.quote())); out.set("before_resource_stocks_raw", stocks(value.beforeStocks()));
        out.set("after_resource_stocks_raw", value.afterStocks() == null ? out.nullNode() : stocks(value.afterStocks()));
        out.set("observed_stock_delta_raw", value.observedDelta() == null ? out.nullNode() : stocks(value.observedDelta()));
        put(out, "unchanged_date_quote_delta_match", value.unchangedDateQuoteDeltaMatch()); out.putNull("next_formal");
        ArrayNode material = out.putArray("material_armies");
        for (MaterialArmy row : value.materialArmies()) {
            ObjectNode item = material.addObject().put("army_id", row.armyId()).put("native_carmy_id", row.nativeCarmyId()).put("current_soldiers", row.currentSoldiers()).put("controllable", true);
            put(item, "owner_character_id", row.ownerCharacterId()); put(item, "current_province_id", row.currentProvinceId());
        }
        if (value.afterSourceFrame() != null) { out.set("after_source_frame", frame(value.afterSourceFrame())); put(out, "actual_employer_id", value.actualEmployerId()); }
        if (value.employerObserved()) { out.set("troop_association", associationJson(value.troopAssociation())); }
        if (value.nextFormal() != null) {
            NextFormal next = value.nextFormal(); ObjectNode item = StrictJson.object().put("selected_step", next.selectedStep()).put("army_id", next.armyId())
                    .put("target_province_id", next.targetProvinceId()).put("expected_revision", next.expectedRevision()).put("source", "observed_order_army_and_original_siege_target");
            out.set("next_formal", item);
        }
        return out;
    }
    private static JsonNode associationJson(Association value) {
        if (value == null) { return StrictJson.object().nullNode(); }
        ObjectNode out = StrictJson.object().put("available", value.available()).put("applies_to_player", value.appliesToPlayer()); put(out, "unavailable_reason", value.unavailableReason());
        ArrayNode rows = out.putArray("rows"); for (AssociationMember row : value.rows()) {
            ObjectNode item = rows.addObject().put("regiment_id", row.regimentId()).put("available", row.available()).put("regiment_resolved", row.regimentResolved())
                    .put("native_carmy_resolved", row.nativeCarmyResolved()).put("combat_resolved", row.combatResolved());
            put(item, "unavailable_reason", row.unavailableReason()); put(item, "native_carmy_id", row.nativeCarmyId()); put(item, "combat_id", row.combatId());
        } return out;
    }
    private static ObjectNode envelope(byte[] input, String schema, Set<String> fields) {
        ObjectNode root = HolyInputValidation.parseObject(input, BYTE_BUDGET, fields); require(schema.equals(text(root.get("schema"))), "wrong holy reinforcement request schema"); return root;
    }
    private static ObjectNode obj(JsonNode value) { require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value; }
    private static ArrayNode array(JsonNode value) { require(value instanceof ArrayNode, "JSON array required"); return (ArrayNode) value; }
    private static boolean nullish(JsonNode value) { return value == null || value.isNull(); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue(); }
    private static Boolean optionalBool(JsonNode value) { return nullish(value) ? null : bool(value); }
    private static String text(JsonNode value) { require(value != null && value.isTextual(), "actual JSON text required"); return value.textValue(); }
    private static String nullableMessage(JsonNode value) {
        if (nullish(value)) { return null; }
        require(value.isTextual(), "exception text requires a JSON string"); return value.textValue();
    }
    private static String nullableText(JsonNode value) { return nullish(value) ? null : text(value); }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "exact JSON integer required; bool/float rejected"); return value.bigIntegerValue(); }
    private static BigInteger integerOrNull(JsonNode value) { return nullish(value) ? null : integer(value); }
    private static long reference(JsonNode value) { return HolyInputValidation.integer(value, 0, U32); }
    private static Long referenceOrNull(JsonNode value) { return nullish(value) ? null : reference(value); }
    private static Long signedOrNull(JsonNode value, long low, long high) { return nullish(value) ? null : HolyInputValidation.integer(value, low, high); }
    private static void scale(JsonNode value) { require(integer(value).equals(BigInteger.valueOf(100000)), "exact native scale 100000 required"); }
    private static void ordinal(JsonNode value, int index) { require(integer(value).equals(BigInteger.valueOf(index)), "source occurrence ordinal differs"); }
    private static boolean availability(ObjectNode value) {
        boolean available = bool(value.get("available")); String reason = nullableText(value.get("unavailable_reason"));
        require(available ? reason == null : reason != null && !reason.isEmpty(), "availability and reason disagree"); return available;
    }
    private static void reasonLiteral(ObjectNode value, String sampledField, String literalField) {
        boolean sampled = bool(value.get(sampledField)); String literal = nullableText(value.get(literalField));
        require(sampled ? literal != null : literal == null, "source reason availability differs");
    }
    private static BigInteger stock(JsonNode value) {
        if (!(value instanceof ObjectNode) || nullish(value.get("raw"))) { return null; }
        BigInteger raw = integer(value.get("raw")); JsonNode scale = value.get("scale");
        return scale != null && !scale.isNull() && integer(scale).equals(BigInteger.valueOf(100000)) ? raw : null;
    }
    private static List<BigInteger> integers(JsonNode value) { List<BigInteger> out = new ArrayList<>(); for (JsonNode item : array(value)) { out.add(integer(item)); } return List.copyOf(out); }
    private static List<String> strings(JsonNode value) { List<String> out = new ArrayList<>(); for (JsonNode item : array(value)) { out.add(text(item)); } return List.copyOf(out); }
    private static ArrayNode numbers(List<BigInteger> values) { ArrayNode out = StrictJson.object().arrayNode(); values.forEach(out::add); return out; }
    private static String snake(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static void put(ObjectNode node, String field, String value) { if (value == null) { node.putNull(field); } else { node.put(field, value); } }
    private static void put(ObjectNode node, String field, BigInteger value) { if (value == null) { node.putNull(field); } else { node.put(field, value); } }
    private static void put(ObjectNode node, String field, Long value) { if (value == null) { node.putNull(field); } else { node.put(field, value); } }
    private static void put(ObjectNode node, String field, Boolean value) { if (value == null) { node.putNull(field); } else { node.put(field, value); } }
}
