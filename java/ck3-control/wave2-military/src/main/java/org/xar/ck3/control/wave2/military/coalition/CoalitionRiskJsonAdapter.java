package org.xar.ck3.control.wave2.military.coalition;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.FinalCbRoles;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.MissingDomain;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Mobilization;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Observation;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.ObservationStatus;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.OwnerForce;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Participant;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.ParticipantSource;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Policy;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.PotentialEnemyParticipants;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.RiskResult;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.SelectedDeclaration;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.TwoRoundObservation;

/** Strict domain boundary; connection/episode and before/after leases belong to the calling admission gate. */
public final class CoalitionRiskJsonAdapter {
    public static final String GAME_VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Pattern DECLARATION_ID = Pattern.compile("([1-9][0-9]*)-(0|[1-9][0-9]*)-(-1|0|[1-9][0-9]*)");
    private static final Set<String> FIELDS = Set.of("schema_version", "status", "read_only", "game_version",
            "executable_sha256", "capture_epoch", "native_revision", "public_revision", "date_raw", "actor_character_id",
            "declaration_id", "selected_declaration", "effective_target_character_id", "ticket", "query_sequence",
            "two_round_observation", "final_cb_roles", "potential_enemy_participants", "owner_forces",
            "actor_lower_soldiers", "enemy_upper_soldiers", "enemy_force_coverage_complete",
            "complete_initial_participants_ready", "missing_required_domains", "native_mobilization_qualification");
    private static final Set<String> SELECTED_FIELDS = Set.of("target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids");
    private static final Set<String> REQUEST_FIELDS = Set.of("request_id", "ticket", "query_sequence", "capture_epoch");
    private static final Set<String> ROUND_FIELDS = Set.of("round_count", "complete_dto_equal", "frame_binding_equal", "unavailable_reason");
    private static final Set<String> ROLE_FIELDS = Set.of("available", "unavailable_reason", "primary_attacker_character_id",
            "primary_defender_character_id", "source", "native_fallback", "final_can_send");
    private static final Set<String> PARTICIPANTS_FIELDS = Set.of("available", "unavailable_reason", "collection_complete",
            "participants", "current_allies_complete", "holy_joiners_complete", "additional_supporters_complete", "selected_cb_initial_complete");
    private static final Set<String> PARTICIPANT_FIELDS = Set.of("character_id", "sources");
    private static final Set<String> OWNER_FIELDS = Set.of("owner_character_id", "actor_lower_soldiers", "actor_lower_ready",
            "inventory_upper_soldiers", "inventory_upper_ready", "inventory_scope", "unavailable_reasons");
    private static final Set<String> MOBILIZATION_FIELDS = Set.of("available", "unavailable_reason", "source", "native_raise_legal",
            "default_raise_province_id", "unraised_lower_soldiers", "unraised_lower_ready", "raised_commandable_lower_soldiers",
            "raised_lower_ready", "executable_lower_soldiers", "executable_lower_ready", "physical_inventory_lower_soldiers",
            "native_unraised_stock_soldiers", "native_unraised_stock_ready", "component_combination");
    private static final Set<String> POLICY_FIELDS = Set.of("policy_id", "scope", "minimum_actor_to_enemy_ratio_numerator",
            "minimum_actor_to_enemy_ratio_denominator", "assumption");

    private CoalitionRiskJsonAdapter() { }

    public record Assessment(RiskResult risk, Boolean finalCanSend) {
        public Assessment { Objects.requireNonNull(risk); }
        public ObjectNode riskJson() { return encodeRisk(risk); }
    }

    public static Assessment assess(JsonNode domain, JsonNode projectedSnapshot, JsonNode expectedDeclaration,
                                    JsonNode independentReceipt, String expectedRequestId) {
        return assess(domain, projectedSnapshot, expectedDeclaration, independentReceipt, expectedRequestId, null, null);
    }

    public static Assessment assess(JsonNode domain, JsonNode projectedSnapshot, JsonNode expectedDeclaration,
                                    JsonNode independentReceipt, String expectedRequestId,
                                    BigInteger expectedCaptureEpoch, JsonNode policy) {
        Observation observation = normalize(domain, projectedSnapshot, expectedDeclaration,
                independentReceipt, expectedRequestId, expectedCaptureEpoch);
        return new Assessment(PrewarCoalition.assessValidated(observation, policy(policy)), observation.finalCbRoles().finalCanSend());
    }

    /** Does not infer an independent TOP receipt from domain fields or authenticate the outer query lease. */
    public static Observation normalize(JsonNode domain, JsonNode snapshot, JsonNode expectedDeclaration,
                                         JsonNode independentReceipt, String expectedRequestId,
                                         BigInteger expectedCaptureEpoch) {
        ObjectNode root = object(domain, FIELDS);
        require(integer(root.get("schema_version"), 2, 2) == 2, "schema_version");
        String status = text(root.get("status"));
        require(status.equals("partial") || status.equals("available"), "read-only status");
        truth(root.get("read_only"));
        Metadata metadata = metadata(root, snapshot, expectedDeclaration, independentReceipt, expectedRequestId, expectedCaptureEpoch);
        TwoRoundObservation rounds = rounds(root.get("two_round_observation"));
        FinalCbRoles roles = roles(root.get("final_cb_roles"));
        PotentialEnemyParticipants participants = participants(root.get("potential_enemy_participants"), roles);
        List<OwnerForce> owners = owners(root.get("owner_forces"), metadata.actor(), roles, participants.participants());
        Mobilization mobilization = mobilization(root.get("native_mobilization_qualification"));
        Map<Integer, OwnerForce> byOwner = new HashMap<>();
        for (OwnerForce owner : owners) byOwner.put(owner.ownerCharacterId(), owner);
        List<MissingDomain> missing = new ArrayList<>();
        if (!rounds.ready()) missing.add(MissingDomain.TWO_ROUND);
        if (!roles.available()) missing.add(MissingDomain.FINAL_ROLES);
        boolean participantReady = participants.available() && roles.available();
        if (!participantReady) missing.add(MissingDomain.PARTICIPANTS);
        if (!participants.currentAlliesComplete()) missing.add(MissingDomain.CURRENT_ALLIES);
        if (!participants.holyJoinersComplete()) missing.add(MissingDomain.HOLY_JOINERS);
        if (!participants.additionalSupportersComplete()) missing.add(MissingDomain.ADDITIONAL_SUPPORTERS);
        if (!participants.selectedCbInitialComplete()) missing.add(MissingDomain.SELECTED_CB_INITIAL);
        OwnerForce actorForce = byOwner.get(metadata.actor());
        require(actorForce.actorLowerReady() == mobilization.executableLowerReady()
                && Objects.equals(actorForce.actorLowerSoldiers(), mobilization.executableLowerSoldiers()),
                "actor owner lower must equal the actual mobilization executable lower");
        if (!mobilization.available()) missing.add(MissingDomain.MOBILIZATION);
        if (!actorForce.actorLowerReady()) missing.add(MissingDomain.ACTOR_LOWER);
        boolean upperReady = participants.participants().stream().allMatch(participant -> byOwner.get(participant.characterId()).inventoryUpperReady());
        if (!upperReady) missing.add(MissingDomain.ENEMY_UPPER);
        Long upperSum = null;
        if (upperReady) {
            BigInteger sum = BigInteger.ZERO;
            for (Participant participant : participants.participants()) {
                sum = sum.add(BigInteger.valueOf(byOwner.get(participant.characterId()).inventoryUpperSoldiers()));
            }
            if (sum.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) > 0) missing.add(MissingDomain.ENEMY_OVERFLOW);
            else upperSum = sum.longValueExact();
        }
        boolean initialReady = rounds.ready() && participantReady;
        boolean enemyComplete = initialReady && upperReady && upperSum != null;
        Long lower = count(root.get("actor_lower_soldiers"));
        Long upper = count(root.get("enemy_upper_soldiers"));
        Long expectedLower = rounds.ready() && actorForce.actorLowerReady() ? actorForce.actorLowerSoldiers() : null;
        Long expectedUpper = enemyComplete ? upperSum : null;
        require(Objects.equals(lower, expectedLower) && Objects.equals(upper, expectedUpper), "force aggregate scope mismatch");
        boolean coverage = bool(root.get("enemy_force_coverage_complete"));
        boolean initial = bool(root.get("complete_initial_participants_ready"));
        require(coverage == enemyComplete && initial == initialReady, "overclaimed or suppressed force/participant coverage");
        List<MissingDomain> declaredMissing = texts(root.get("missing_required_domains")).stream().map(MissingDomain::fromWire).toList();
        require(new HashSet<>(declaredMissing).equals(new HashSet<>(missing)), "declared missing domains differ from source coverage");
        require(status.equals(missing.isEmpty() ? "available" : "partial"), "status differs from actual domain coverage");
        return new Observation(missing.isEmpty() ? ObservationStatus.AVAILABLE : ObservationStatus.PARTIAL,
                GAME_VERSION, EXECUTABLE_SHA256, uint64(root.get("capture_epoch")), uint64(root.get("native_revision")),
                uint64(root.get("public_revision")), (int) integer(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                metadata.actor(), metadata.declarationId(), metadata.selected(), optionalCharacter(root.get("effective_target_character_id"), false),
                uint64(root.get("ticket")), uint64(root.get("query_sequence")), rounds, roles, participants,
                owners, lower, upper, coverage, initial, declaredMissing, mobilization);
    }

    /** Shape/binding check only. It grants neither a full lease nor gameplay permission. */
    public static boolean isCurrent(JsonNode domain, JsonNode snapshot, JsonNode expectedDeclaration,
                                     JsonNode independentReceipt, String expectedRequestId, BigInteger expectedCaptureEpoch) {
        try {
            normalize(domain, snapshot, expectedDeclaration, independentReceipt, expectedRequestId, expectedCaptureEpoch);
            return true;
        } catch (IllegalArgumentException exception) { return false; }
    }

    private record Metadata(int actor, String declarationId, SelectedDeclaration selected) { }

    private static Metadata metadata(ObjectNode root, JsonNode snapshotNode, JsonNode expectedDeclarationNode,
                                      JsonNode receiptNode, String requestId, BigInteger expectedCaptureEpoch) {
        ObjectNode snapshot = extensible(snapshotNode);
        truth(snapshot.get("paused")); truth(snapshot.get("map_ready"));
        exactBuild(root.get("game_version"), root.get("executable_sha256"));
        ObjectNode hello = extensible(extensible(snapshot.get("diagnostics")).get("hello"));
        exactBuild(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"));
        ObjectNode receipt = object(receiptNode, REQUEST_FIELDS);
        require(nonblank(requestId).equals(nonblank(receipt.get("request_id"))), "independent TOP receipt request ID mismatch");
        for (String field : List.of("ticket", "query_sequence", "capture_epoch")) {
            require(uint64(root.get(field)).equals(uint64(receipt.get(field))), "independent TOP receipt " + field + " mismatch");
        }
        BigInteger epoch = uint64(root.get("capture_epoch"));
        if (expectedCaptureEpoch != null) {
            require(expectedCaptureEpoch.signum() > 0 && expectedCaptureEpoch.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "expected capture epoch outside uint64");
            require(epoch.equals(expectedCaptureEpoch), "expected capture epoch mismatch");
        }
        if (snapshot.has("capture_epoch")) require(epoch.equals(uint64(snapshot.get("capture_epoch"))), "snapshot capture epoch mismatch");
        require(uint64(root.get("native_revision")).equals(uint64(snapshot.get("native_revision"))), "native revision mismatch");
        require(uint64(root.get("public_revision")).equals(uint64(snapshot.get("revision"))), "public revision mismatch");
        require(integer(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)
                == integer(snapshot.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE), "date mismatch");
        ObjectNode played = extensible(snapshot.get("played_character"));
        truth(played.get("alive"));
        int actor = character(root.get("actor_character_id"));
        require(actor == character(played.get("character_id")), "living actor mismatch");
        ObjectNode expected = extensible(expectedDeclarationNode);
        String declarationId = declarationId(expected);
        SelectedDeclaration selected = declarationSelected(expected);
        require(text(root.get("declaration_id")).equals(declarationId)
                && selected(root.get("selected_declaration")).equals(selected), "selected declaration mismatch");
        JsonNode catalogue = array(snapshot.get("declarable_wars"));
        ObjectNode match = null;
        for (JsonNode candidate : catalogue) {
            if (candidate.isObject() && candidate.has("declaration_id") && candidate.get("declaration_id").isTextual()
                    && candidate.get("declaration_id").textValue().equals(declarationId)) {
                require(match == null, "declaration catalogue is ambiguous");
                match = extensible(candidate);
            }
        }
        require(match != null && declarationSelected(match).equals(selected), "declaration catalogue absent or stale");
        declarationId(match);
        optionalCharacter(root.get("effective_target_character_id"), false);
        return new Metadata(actor, declarationId, selected);
    }

    private static void exactBuild(JsonNode version, JsonNode sha) {
        require(text(version).equals(GAME_VERSION) && text(sha).toUpperCase(Locale.ROOT).equals(EXECUTABLE_SHA256),
                "prewar source differs from exact frozen 1.20.0.4 build");
    }

    private static String declarationId(ObjectNode node) {
        String identity = text(node.get("declaration_id"));
        require(DECLARATION_ID.matcher(identity).matches(), "noncanonical declaration ID");
        SelectedDeclaration selected = declarationSelected(node);
        require(identity.equals(selected.targetCharacterId() + "-" + selected.casusBelliIndex() + "-" + selected.configurationIndex()),
                "declaration ID and ordered tuple disagree");
        return identity;
    }

    private static SelectedDeclaration declarationSelected(ObjectNode declaration) {
        ObjectNode projection = StrictJson.object();
        for (String field : SELECTED_FIELDS) {
            require(declaration.has(field), "declaration lost selected tuple field " + field);
            projection.set(field, declaration.get(field));
        }
        return selected(projection);
    }

    private static SelectedDeclaration selected(JsonNode node) {
        ObjectNode row = object(node, SELECTED_FIELDS);
        List<Integer> titles = new ArrayList<>();
        for (JsonNode title : array(row.get("target_title_ids"))) titles.add((int) integer(title, 0, Integer.MAX_VALUE));
        return new SelectedDeclaration(character(row.get("target_character_id")),
                (int) integer(row.get("casus_belli_index"), 0, Integer.MAX_VALUE), nonblank(row.get("casus_belli_key")),
                (int) integer(row.get("configuration_index"), -1, Integer.MAX_VALUE),
                (int) integer(row.get("claimant_character_id"), -1, Integer.MAX_VALUE), titles);
    }

    private static TwoRoundObservation rounds(JsonNode node) {
        ObjectNode row = object(node, ROUND_FIELDS);
        integer(row.get("round_count"), 2, 2);
        boolean equal = bool(row.get("complete_dto_equal"));
        boolean frame = bool(row.get("frame_binding_equal"));
        return new TwoRoundObservation(equal, frame, reason(row.get("unavailable_reason"), equal && frame));
    }

    private static FinalCbRoles roles(JsonNode node) {
        ObjectNode row = object(node, ROLE_FIELDS);
        boolean available = bool(row.get("available"));
        String reason = reason(row.get("unavailable_reason"), available);
        require(text(row.get("source")).equals(PrewarCoalition.FINAL_ROLES_SOURCE), "roles must come from finalized CB context");
        Integer attacker = optionalCharacter(row.get("primary_attacker_character_id"), true);
        Integer defender = optionalCharacter(row.get("primary_defender_character_id"), true);
        require(!available || attacker != null && defender != null, "ready final roles lost an actual receiver");
        require(attacker == null || !attacker.equals(defender), "final primary sides collapse");
        return new FinalCbRoles(available, reason, attacker, defender,
                nullableBool(row.get("native_fallback")), nullableBool(row.get("final_can_send")));
    }

    private static PotentialEnemyParticipants participants(JsonNode node, FinalCbRoles roles) {
        ObjectNode row = object(node, PARTICIPANTS_FIELDS);
        boolean available = bool(row.get("available"));
        boolean complete = bool(row.get("collection_complete"));
        String reason = reason(row.get("unavailable_reason"), available);
        require(available == complete, "participant availability must describe complete potential collection");
        boolean allies = bool(row.get("current_allies_complete"));
        boolean holy = bool(row.get("holy_joiners_complete"));
        boolean additional = bool(row.get("additional_supporters_complete"));
        boolean selectedInitial = bool(row.get("selected_cb_initial_complete"));
        List<Participant> result = new ArrayList<>();
        Set<Integer> seen = new HashSet<>();
        int primaries = 0;
        for (JsonNode item : array(row.get("participants"))) {
            ObjectNode participant = object(item, PARTICIPANT_FIELDS);
            int character = nativeCharacter(participant.get("character_id"));
            List<ParticipantSource> sources = texts(participant.get("sources")).stream().map(ParticipantSource::fromWire).toList();
            require(seen.add(character) && !sources.isEmpty(), "participants repeat an owner or lose provenance");
            if (sources.contains(ParticipantSource.PRIMARY_DEFENDER)) {
                primaries++;
                require(roles.primaryDefenderCharacterId() == null || character == roles.primaryDefenderCharacterId(),
                        "primary defender provenance differs from finalized roles");
            }
            result.add(new Participant(character, sources));
        }
        require(primaries <= 1, "duplicate primary-defender provenance");
        require(!available || roles.available() && primaries == 1 && allies && holy && additional && selectedInitial,
                "complete participants lack finalized roles or required supporter domain");
        return new PotentialEnemyParticipants(available, reason, complete, result, allies, holy, additional, selectedInitial);
    }

    private static List<OwnerForce> owners(JsonNode node, int actor, FinalCbRoles roles, List<Participant> participants) {
        Set<Integer> enemyOwners = new HashSet<>();
        for (Participant participant : participants) enemyOwners.add(participant.characterId());
        Set<Integer> expected = new HashSet<>(enemyOwners);
        expected.add(actor);
        if (roles.primaryAttackerCharacterId() != null) expected.add(roles.primaryAttackerCharacterId());
        if (roles.primaryDefenderCharacterId() != null) expected.add(roles.primaryDefenderCharacterId());
        Set<Integer> seen = new HashSet<>();
        List<OwnerForce> result = new ArrayList<>();
        for (JsonNode item : array(node)) {
            ObjectNode row = object(item, OWNER_FIELDS);
            int owner = nativeCharacter(row.get("owner_character_id"));
            require(seen.add(owner) && expected.contains(owner), "owner forces duplicate or invent a scope member");
            boolean lowerReady = bool(row.get("actor_lower_ready"));
            Long lower = count(row.get("actor_lower_soldiers"));
            boolean upperReady = bool(row.get("inventory_upper_ready"));
            Long upper = count(row.get("inventory_upper_soldiers"));
            List<String> reasons = texts(row.get("unavailable_reasons"));
            require(text(row.get("inventory_scope")).equals(PrewarCoalition.INVENTORY_SCOPE), "owner inventory scope mismatch");
            require(lowerReady == (lower != null) && upperReady == (upper != null), "owner count readiness mismatch");
            require(owner == actor || !lowerReady && lower == null, "nonactor cannot claim actor floor");
            require(owner != actor || lowerReady || !reasons.isEmpty(), "unknown actor floor requires reason");
            require(!enemyOwners.contains(owner) || upperReady || !reasons.isEmpty(), "unknown enemy inventory requires reason");
            require(owner != actor || !lowerReady || !upperReady || lower <= upper, "actor floor exceeds physical ceiling");
            result.add(new OwnerForce(owner, lower, lowerReady, upper, upperReady, reasons));
        }
        require(seen.equals(expected), "owner forces omitted a role or observed participant");
        return List.copyOf(result);
    }

    private static Mobilization mobilization(JsonNode node) {
        ObjectNode row = object(node, MOBILIZATION_FIELDS);
        boolean available = bool(row.get("available"));
        String reason = reason(row.get("unavailable_reason"), available);
        require(text(row.get("source")).equals(PrewarCoalition.MOBILIZATION_SOURCE), "mobilization source is not actual command validation and owned rosters");
        require(text(row.get("component_combination")).equals(PrewarCoalition.COMPONENT_COMBINATION), "mobilization cannot sum unproven physical components");
        Long physical = count(row.get("physical_inventory_lower_soldiers"));
        Integer stock = nullableInt(row.get("native_unraised_stock_soldiers"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        boolean stockReady = bool(row.get("native_unraised_stock_ready"));
        require(!stockReady || stock != null && stock >= 0, "ready native stock requires nonnegative int32 count");
        Boolean legal = nullableBool(row.get("native_raise_legal"));
        Integer province = nullableInt(row.get("default_raise_province_id"), 1, Integer.MAX_VALUE);
        require(legal == null || province != null, "native raise verdict requires actual default province");
        boolean unraisedReady = bool(row.get("unraised_lower_ready"));
        Long unraised = count(row.get("unraised_lower_soldiers"));
        boolean raisedReady = bool(row.get("raised_lower_ready"));
        Long raised = count(row.get("raised_commandable_lower_soldiers"));
        boolean executableReady = bool(row.get("executable_lower_ready"));
        Long executable = count(row.get("executable_lower_soldiers"));
        require(unraisedReady == (unraised != null) && raisedReady == (raised != null)
                && executableReady == (executable != null) && available == executableReady,
                "mobilization readiness contradicts nullable certified bound");
        boolean expectedUnraisedReady = physical != null && stockReady;
        Long expectedUnraised = expectedUnraisedReady ? Math.min(physical, stock.longValue()) : null;
        require(unraisedReady == expectedUnraisedReady && Objects.equals(unraised, expectedUnraised),
                "unraised lower is not bounded by actual stock and physical inventory");
        if (executableReady) {
            Long proven = raisedReady ? raised : null;
            if (Boolean.TRUE.equals(legal) && unraisedReady) proven = proven == null ? unraised : Math.max(proven, unraised);
            require(proven != null && proven.equals(executable), "executable lower must be maximum actually proven component");
        }
        return new Mobilization(available, reason, legal, province, unraised, unraisedReady, raised, raisedReady,
                executable, executableReady, physical, stock, stockReady);
    }

    private static Policy policy(JsonNode value) {
        if (value == null || value.isNull()) return PrewarCoalition.DEFAULT_POLICY;
        ObjectNode row = object(value, POLICY_FIELDS);
        require(text(row.get("scope")).equals(PrewarCoalition.INVENTORY_SCOPE)
                && text(row.get("assumption")).equals(PrewarCoalition.ASSUMPTION), "policy changes scope or claims calibration");
        return new Policy(nonblank(row.get("policy_id")), integer(row.get("minimum_actor_to_enemy_ratio_numerator"), 1, Long.MAX_VALUE),
                integer(row.get("minimum_actor_to_enemy_ratio_denominator"), 1, Long.MAX_VALUE));
    }

    public static ObjectNode encodeRisk(RiskResult risk) {
        ObjectNode result = StrictJson.object();
        result.put("status", risk.status().wire()).put("force_risk_qualified", risk.forceRiskQualified()).put("reason", risk.reason().wire());
        Policy policy = risk.policy();
        ObjectNode config = result.putObject("policy");
        config.put("policy_id", policy.policyId()).put("scope", PrewarCoalition.INVENTORY_SCOPE)
                .put("minimum_actor_to_enemy_ratio_numerator", policy.minimumActorToEnemyRatioNumerator())
                .put("minimum_actor_to_enemy_ratio_denominator", policy.minimumActorToEnemyRatioDenominator())
                .put("assumption", PrewarCoalition.ASSUMPTION);
        put(result, "actor_lower_soldiers", risk.actorLowerSoldiers()); put(result, "enemy_upper_soldiers", risk.enemyUpperSoldiers());
        ArrayNode missing = result.putArray("missing_required_domains");
        risk.missingRequiredDomains().forEach(domain -> missing.add(domain.wire()));
        return result;
    }

    public static ObjectNode encodeObservation(Observation observation) {
        ObjectNode result = StrictJson.object();
        result.put("schema_version", 2).put("status", observation.status().wire()).put("read_only", true)
                .put("game_version", observation.gameVersion()).put("executable_sha256", observation.executableSha256())
                .put("capture_epoch", observation.captureEpoch()).put("native_revision", observation.nativeRevision())
                .put("public_revision", observation.publicRevision()).put("date_raw", observation.dateRaw())
                .put("actor_character_id", observation.actorCharacterId()).put("declaration_id", observation.declarationId())
                .put("ticket", observation.ticket()).put("query_sequence", observation.querySequence())
                .put("enemy_force_coverage_complete", observation.enemyForceCoverageComplete())
                .put("complete_initial_participants_ready", observation.completeInitialParticipantsReady());
        put(result, "effective_target_character_id", observation.effectiveTargetCharacterId());
        put(result, "actor_lower_soldiers", observation.actorLowerSoldiers()); put(result, "enemy_upper_soldiers", observation.enemyUpperSoldiers());
        SelectedDeclaration selected = observation.selectedDeclaration();
        ObjectNode selectedNode = result.putObject("selected_declaration");
        selectedNode.put("target_character_id", selected.targetCharacterId()).put("casus_belli_index", selected.casusBelliIndex())
                .put("casus_belli_key", selected.casusBelliKey()).put("configuration_index", selected.configurationIndex())
                .put("claimant_character_id", selected.claimantCharacterId());
        ArrayNode titles = selectedNode.putArray("target_title_ids");
        selected.targetTitleIds().forEach(titles::add);
        TwoRoundObservation rounds = observation.twoRoundObservation();
        result.putObject("two_round_observation").put("round_count", 2).put("complete_dto_equal", rounds.completeDtoEqual())
                .put("frame_binding_equal", rounds.frameBindingEqual()).put("unavailable_reason", rounds.unavailableReason());
        FinalCbRoles roles = observation.finalCbRoles();
        ObjectNode roleNode = result.putObject("final_cb_roles");
        roleNode.put("available", roles.available()).put("unavailable_reason", roles.unavailableReason())
                .put("source", PrewarCoalition.FINAL_ROLES_SOURCE);
        put(roleNode, "primary_attacker_character_id", roles.primaryAttackerCharacterId());
        put(roleNode, "primary_defender_character_id", roles.primaryDefenderCharacterId());
        roleNode.put("native_fallback", roles.nativeFallback()).put("final_can_send", roles.finalCanSend());
        PotentialEnemyParticipants participants = observation.potentialEnemyParticipants();
        ObjectNode participantNode = result.putObject("potential_enemy_participants");
        participantNode.put("available", participants.available()).put("unavailable_reason", participants.unavailableReason())
                .put("collection_complete", participants.collectionComplete()).put("current_allies_complete", participants.currentAlliesComplete())
                .put("holy_joiners_complete", participants.holyJoinersComplete()).put("additional_supporters_complete", participants.additionalSupportersComplete())
                .put("selected_cb_initial_complete", participants.selectedCbInitialComplete());
        ArrayNode participantRows = participantNode.putArray("participants");
        for (Participant participant : participants.participants()) {
            ObjectNode row = participantRows.addObject().put("character_id", participant.characterId());
            ArrayNode sources = row.putArray("sources"); participant.sources().forEach(source -> sources.add(source.wire()));
        }
        ArrayNode ownerRows = result.putArray("owner_forces");
        for (OwnerForce owner : observation.ownerForces()) {
            ObjectNode row = ownerRows.addObject().put("owner_character_id", owner.ownerCharacterId())
                    .put("actor_lower_ready", owner.actorLowerReady()).put("inventory_upper_ready", owner.inventoryUpperReady())
                    .put("inventory_scope", PrewarCoalition.INVENTORY_SCOPE);
            put(row, "actor_lower_soldiers", owner.actorLowerSoldiers()); put(row, "inventory_upper_soldiers", owner.inventoryUpperSoldiers());
            ArrayNode reasons = row.putArray("unavailable_reasons"); owner.unavailableReasons().forEach(reasons::add);
        }
        Mobilization mobilization = observation.nativeMobilizationQualification();
        ObjectNode mobilizationNode = result.putObject("native_mobilization_qualification");
        mobilizationNode.put("available", mobilization.available()).put("unavailable_reason", mobilization.unavailableReason())
                .put("source", PrewarCoalition.MOBILIZATION_SOURCE).put("native_raise_legal", mobilization.nativeRaiseLegal())
                .put("unraised_lower_ready", mobilization.unraisedLowerReady()).put("raised_lower_ready", mobilization.raisedLowerReady())
                .put("executable_lower_ready", mobilization.executableLowerReady()).put("native_unraised_stock_ready", mobilization.nativeUnraisedStockReady())
                .put("component_combination", PrewarCoalition.COMPONENT_COMBINATION);
        put(mobilizationNode, "default_raise_province_id", mobilization.defaultRaiseProvinceId());
        put(mobilizationNode, "unraised_lower_soldiers", mobilization.unraisedLowerSoldiers());
        put(mobilizationNode, "raised_commandable_lower_soldiers", mobilization.raisedCommandableLowerSoldiers());
        put(mobilizationNode, "executable_lower_soldiers", mobilization.executableLowerSoldiers());
        put(mobilizationNode, "physical_inventory_lower_soldiers", mobilization.physicalInventoryLowerSoldiers());
        put(mobilizationNode, "native_unraised_stock_soldiers", mobilization.nativeUnraisedStockSoldiers());
        ArrayNode missing = result.putArray("missing_required_domains"); observation.missingRequiredDomains().forEach(domain -> missing.add(domain.wire()));
        return result;
    }

    private static ObjectNode object(JsonNode node, Set<String> fields) { return inputObject(node, fields); }
    private static ObjectNode extensible(JsonNode node) {
        require(node instanceof ObjectNode, "existing SDK object required");
        return (ObjectNode) node;
    }
    private static JsonNode array(JsonNode node) {
        require(node != null && node.isArray(), "actual JSON array required");
        return node;
    }
    private static long integer(JsonNode node, long minimum, long maximum) { return inputInteger(node, minimum, maximum); }
    private static BigInteger uint64(JsonNode node) { return inputInteger(node, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static int character(JsonNode node) { return (int) integer(node, 1, Integer.MAX_VALUE); }
    private static int nativeCharacter(JsonNode node) {
        int value = (int) integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE);
        require(value != -1, "absent native CharacterID is forbidden");
        return value;
    }
    private static Integer optionalCharacter(JsonNode node, boolean nativeHandle) {
        require(node != null, "required nullable CharacterID field missing");
        return node.isNull() ? null : nativeHandle ? nativeCharacter(node) : character(node);
    }
    private static Long count(JsonNode node) {
        require(node != null, "required nullable count missing");
        return node.isNull() ? null : integer(node, 0, Long.MAX_VALUE);
    }
    private static Integer nullableInt(JsonNode node, int minimum, int maximum) {
        require(node != null, "required nullable int32 missing");
        return node.isNull() ? null : (int) integer(node, minimum, maximum);
    }
    private static boolean bool(JsonNode node) {
        require(node != null && node.isBoolean(), "actual JSON boolean required");
        return node.booleanValue();
    }
    private static Boolean nullableBool(JsonNode node) {
        require(node != null, "required nullable boolean missing");
        return node.isNull() ? null : bool(node);
    }
    private static void truth(JsonNode node) { require(bool(node), "actual true required"); }
    private static String text(JsonNode node) {
        require(node != null && node.isTextual(), "actual JSON string required");
        return node.textValue();
    }
    private static String nonblank(JsonNode node) { return nonblank(text(node)); }
    private static String nonblank(String value) {
        require(value != null && !value.isEmpty() && value.equals(PrewarCoalition.stripPython(value)), "nonempty text without surrounding whitespace required");
        return value;
    }
    private static String reason(JsonNode node, boolean available) {
        require(node != null, "required unavailable reason missing");
        if (available) { require(node.isNull(), "available stage reason must be null"); return null; }
        String value = text(node);
        require(!PrewarCoalition.stripPython(value).isEmpty(), "unavailable stage must describe reason");
        return value;
    }
    private static List<String> texts(JsonNode node) {
        List<String> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (JsonNode entry : array(node)) {
            String value = nonblank(entry);
            require(seen.add(value), "text array repeats entry"); result.add(value);
        }
        return List.copyOf(result);
    }
    private static void put(ObjectNode node, String field, Long value) {
        if (value == null) node.putNull(field); else node.put(field, value);
    }
    private static void put(ObjectNode node, String field, Integer value) {
        if (value == null) node.putNull(field); else node.put(field, value);
    }
    private static void require(boolean condition, String message) { if (!condition) throw new ProjectionDomainRejection("prewar v2 " + message); }

    // These wrappers contain only the shared input primitive; no algorithm, result construction or encoder is caught.
    private static ObjectNode inputObject(JsonNode value, Set<String> fields) {
        try { return StrictJson.object(value, fields); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static long inputInteger(JsonNode value, long minimum, long maximum) {
        try { return StrictJson.integer(value, minimum, maximum); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static BigInteger inputInteger(JsonNode value, BigInteger minimum, BigInteger maximum) {
        try { return StrictJson.integer(value, minimum, maximum); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static void inputTrue(JsonNode value) {
        try { StrictJson.trueValue(value); }
        catch (ContractViolationException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
}
