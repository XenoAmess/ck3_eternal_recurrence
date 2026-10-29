package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ExplicitOriginalProtocolId;
import org.xar.ck3.control.application.action.ProtocolRequestIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.lifestyleperks.AuthoredPerkCatalog;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.governance.council.CouncilCodec.*;

/** Actual five native producers. Root must still install exact source qualification and independent observers. */
public final class GovernanceActionPreparation implements ActionPorts.PreparationPort {
    @FunctionalInterface public interface CouncilRefreshPort {
        void verify(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command, String originalRequestId);
    }
    @FunctionalInterface public interface LifestyleRefreshPort {
        void verify(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command);
        default List<org.xar.ck3.control.contracts.ExactRef> preparedEvidence(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command, String originalRequestId) {
            verify(borrowed, command); return List.of();
        }
    }
    public static final String FOCUS = "private-select-player-lifestyle-stock-focus-v1";
    public static final String PERK = "private-select-player-lifestyle-perk-v1";
    public static final String CROWN = "enact-realm-law-crown-v1-private";
    public static final Set<String> OPERATIONS = Set.of(FOCUS, PERK, CouncilActionCodec.PRIVATE_ASSIGN, CouncilActionCodec.ASSIGN, CROWN);
    private final String connectedVersion;
    private final String connectedSha256;
    private final CouncilRefreshPort councilRefresh;
    private final LifestyleRefreshPort lifestyleRefresh;
    private final Optional<ExactRef> publicCallerProducer;
    public GovernanceActionPreparation(String connectedVersion, String connectedSha256, CouncilRefreshPort councilRefresh, LifestyleRefreshPort lifestyleRefresh) {
        this(connectedVersion,connectedSha256,councilRefresh,lifestyleRefresh,Optional.empty());
    }
    public GovernanceActionPreparation(String connectedVersion,String connectedSha256,CouncilRefreshPort councilRefresh,LifestyleRefreshPort lifestyleRefresh,Optional<ExactRef> actualPublicCallerProducer) {
        requireBuild(connectedVersion,connectedSha256);this.connectedVersion=connectedVersion;this.connectedSha256=connectedSha256;
        this.councilRefresh=java.util.Objects.requireNonNull(councilRefresh);this.lifestyleRefresh=java.util.Objects.requireNonNull(lifestyleRefresh);
        this.publicCallerProducer=java.util.Objects.requireNonNull(actualPublicCallerProducer);
        publicCallerProducer.ifPresent(source->StrictJson.require(source.bytes()>0&&java.nio.file.Path.of(source.path()).isAbsolute(),"actual installed public caller producer source required"));
    }
    @Override public void requireProtocolIdentity(ActionCommand command) {
        java.util.Objects.requireNonNull(command);
        ObjectNode args=object(StrictJson.parse(OpportunityJson.encode(command.arguments())));
        var caller=command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)?org.xar.ck3.control.governance.council.CouncilCallerSubmission.requestedId(args):Optional.<String>empty();
        if(command.protocolIdentity() instanceof ProtocolRequestIdentity.BodyDerived) {
            StrictJson.require(caller.isEmpty(),"explicit original Council caller ID cannot use a body-derived protocol header");return;
        }
        StrictJson.require(command.protocolIdentity() instanceof ExplicitOriginalProtocolId,"unsupported protocol identity branch");
        var explicit=(ExplicitOriginalProtocolId)command.protocolIdentity();
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)&&explicit.contract()==ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT
                &&publicCallerProducer.isPresent()&&publicCallerProducer.orElseThrow().equals(explicit.producerSource())
                &&caller.filter(explicit.value()::equals).isPresent(),"explicit Council protocol ID lacks the identical installed source producer, schema or caller arguments");
    }
    @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("governance preparation requires the coordinator's durable original request identity"); }
    @Override public NativeRequest prepare(ActionCommand command, String requestId) {
        requireProtocolIdentity(command);StrictJson.require(!command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN), "private Council preparation requires its original writer Session and fresh held-mailbox final gates");
        return prepared(command, requestId);
    }
    @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command, String requestId) {
        java.util.Objects.requireNonNull(borrowed);requireProtocolIdentity(command);
        // Validate the durable caller material before querying; fresh native gate material is then captured immediately before intent/submit.
        NativeRequest request = prepared(command, requestId);
        if (command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)) councilRefresh.verify(borrowed, command, requestId);
        else if (command.operation().value().equals(FOCUS) || command.operation().value().equals(PERK)) {
            var custody = lifestyleRefresh.preparedEvidence(borrowed, command, requestId);
            StrictJson.require(custody.size() == 1, "successful LIFE preparation must retain one complete original preflight leaf before durable INTENT");
            return new NativeRequest(request.step(), request.requiredCapability(), request.additionalFields(), custody);
        }
        return request;
    }
    private NativeRequest prepared(ActionCommand command, String requestId) {
        StrictJson.text(requestId); String operation = command.operation().value();
        ObjectNode fields = switch (operation) {
            case FOCUS, PERK -> lifestyle(command, operation.equals(FOCUS));
            case CouncilActionCodec.ASSIGN, CouncilActionCodec.PRIVATE_ASSIGN -> CouncilActionCodec.wireFields(councilRequest(command, requestId), operation.equals(CouncilActionCodec.PRIVATE_ASSIGN));
            case CROWN -> crown(command, requestId);
            default -> throw new IllegalArgumentException("not a native governance operation");
        };
        return new NativeRequest(operation, operation.equals(CouncilActionCodec.ASSIGN)
                ? Optional.of("game.action.assign-councillor-v1") : Optional.empty(), new RawJson(StrictJson.canonical(fields)));
    }
    public static CouncilActionCodec.Request councilRequest(ActionCommand command, String requestId) {
        ObjectNode args = object(StrictJson.parse(OpportunityJson.encode(command.arguments())));
        var requestedId=org.xar.ck3.control.governance.council.CouncilCallerSubmission.requestedId(args);
        if(!org.xar.ck3.control.governance.council.CouncilCallerSubmission.isPublic(args))StrictJson.object(args,Set.of("position_key", "candidate_character_id", "original_query", "expected_has_incumbent", "expected_incumbent_character_id"));
        org.xar.ck3.control.governance.council.CouncilCallerSubmission.requirePreparedId(args,requestId);
        CouncilModels.Position role = CouncilModels.Position.exact(text(args, "position_key"));
        var observed = command.before().frame(); var identity = observed.identity();
        boolean privateRoute = command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN);
        StrictJson.require(privateRoute || command.operation().value().equals(CouncilActionCodec.ASSIGN) && role == CouncilModels.Position.STEWARD, "public Council action is Steward-only");
        var frame = new CouncilModels.Frame(privateRoute ? "native:" + identity.nativeRevision() : observed.snapshotId(),
                privateRoute ? identity.nativeRevision() : observed.revision(), identity.nativeRevision(), identity.dateRaw().intValueExact(), identity.player().intValueExact());
        ObjectNode original = object(args.get("original_query")); ObjectNode payload = original;
        int selected = (int) number(args, "candidate_character_id", 1, Integer.MAX_VALUE);
        if (privateRoute) {
            StrictJson.require(text(original, "status").equals("available") && text(original, "step").equals("private-query-council-final-gates-v1"), "private Council assignment requires actual final-gates material");
            StrictJson.trueValue(original.get("private_build")); StrictJson.trueValue(original.get("read_only"));
            StrictJson.require(!bool(original.get("advertised")) && text(original, "queried_snapshot_id").equals(observed.snapshotId())
                    && u64(original.get("queried_revision"), true).equals(observed.revision())
                    && u64(original.get("queried_native_revision"), true).equals(identity.nativeRevision()), "private Council public source frame drift");
            ObjectNode source = StrictJson.object(original.get("source_frame"), Set.of("snapshot_id", "revision", "native_revision", "date_raw", "player_character_id", "paused"));
            StrictJson.require(text(source, "snapshot_id").equals(observed.snapshotId()) && u64(source.get("revision"), true).equals(observed.revision())
                    && u64(source.get("native_revision"), true).equals(identity.nativeRevision()) && number(source, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == frame.dateRaw()
                    && number(source, "player_character_id", 1, Integer.MAX_VALUE) == frame.ownerId() && bool(source.get("paused")), "private Council source binding mismatch");
            payload = object(original.get("council_composition_candidates"));
        }
        CouncilModels.Candidates candidates = CouncilCodec.decode(StrictJson.canonical(payload), frame, role);
        CouncilActionCodec.Request request = CouncilActionCodec.request(candidates, selected, requestId);
        StrictJson.require(bool(args.get("expected_has_incumbent")) == request.incumbentId().isPresent()
                && number(args, "expected_incumbent_character_id", -1, Integer.MAX_VALUE) == request.incumbentId().orElse(-1), "durable Council incumbent differs from original observed seat");
        if (privateRoute) requireFinalGates(original, candidates, selected);
        return request;
    }
    private static void requireFinalGates(ObjectNode original, CouncilModels.Candidates candidates, int selected) {
        ObjectNode gates = StrictJson.object(original.get("council_final_gates"), Set.of("schema", "status", "unavailable_reason", "candidate_count", "rows", "council_composition_candidates"));
        StrictJson.require(text(gates, "schema").equals("xar.ck3.private.council-final-gates/v1") && text(gates, "status").equals("available")
                && text(gates, "unavailable_reason").equals("none") && gates.get("council_composition_candidates").equals(original.get("council_composition_candidates")), "Council gates/payload disagree");
        JsonNode rows = gates.get("rows"); StrictJson.require(rows != null && rows.isArray() && rows.size() == candidates.candidates().size()
                && number(gates, "candidate_count", 0, 0xffff_ffffL) == rows.size(), "Council gate collection incomplete");
        for (int index = 0; index < rows.size(); index++) {
            ObjectNode row = StrictJson.object(rows.get(index), Set.of("character_id", "native_collection_ordinal", "final_gate_available", "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction", "incumbent_fireability_evaluated", "incumbent_can_be_fired"));
            var candidate = candidates.candidates().get(index);
            StrictJson.require(id(row.get("character_id")) == candidate.characterId() && number(row, "native_collection_ordinal", 0, 0xffff_ffffL) == candidate.nativeCollectionOrdinal(), "Council gate candidate identity/order drift");
            for (String key : List.of("final_gate_available", "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction", "incumbent_fireability_evaluated", "incumbent_can_be_fired")) bool(row.get(key));
            if (candidate.characterId() == selected) StrictJson.require(bool(row.get("final_gate_available")) && !bool(row.get("candidate_already_councillor"))
                    && !bool(row.get("candidate_is_guest")) && !bool(row.get("pending_character_interaction"))
                    && (!candidates.seat().incumbentId().isPresent() || bool(row.get("incumbent_fireability_evaluated")) && bool(row.get("incumbent_can_be_fired"))), "selected Council candidate lacks actual native final legality");
        }
    }
    /** Pure replay of the identical original request encoder; it grants no preparation, source or submit authority. */
    public static RawJson lifestyleFields(ActionCommand command) {
        String operation = command.operation().value(); StrictJson.require(operation.equals(FOCUS) || operation.equals(PERK), "exact LIFE operation required");
        return new RawJson(StrictJson.canonical(lifestyle(command, operation.equals(FOCUS))));
    }
    private static ObjectNode lifestyle(ActionCommand command, boolean focus) {
        ObjectNode args = StrictJson.object(StrictJson.parse(OpportunityJson.encode(command.arguments())), Set.of("target_key", "target_lifestyle_key", "original_query", "decision"));
        ObjectNode query = object(args.get("original_query")); String target = text(args, "target_key"), lifestyle = text(args, "target_lifestyle_key");
        StrictJson.require(text(query, "status").equals(focus ? "stock_focus_available" : "available")
                && text(query, "formal_precondition_status").equals(focus ? "stock_focus_ready" : "ready"), "LIFE original source is unavailable");
        var expected = command.before().frame(); var identity = expected.identity(); ObjectNode source = object(query.get("source_frame"));
        ObjectNode snapshot = object(query.get("snapshot"));
        StrictJson.require(text(source, "snapshot_id").equals(expected.snapshotId()) && u64(source.get("revision"), true).equals(expected.revision())
                && u64(source.get("native_revision"), true).equals(identity.nativeRevision()) && number(source, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE) == identity.dateRaw().intValueExact()
                && number(source, "player_character_id", 1, 0xffff_ffffL) == identity.player().longValueExact(), "LIFE outer source changed");
        StrictJson.require(text(snapshot, "snapshot_id").equals(expected.snapshotId()) && text(snapshot, "episode_run_id").equals(expected.episodeRunId())
                && text(query, "episode_run_id").equals(expected.episodeRunId()) && u64(snapshot.get("public_revision"), true).equals(expected.revision())
                && u64(snapshot.get("native_revision"), true).equals(identity.nativeRevision()) && u64(snapshot.get("proof_epoch"), true).equals(identity.nativeRevision())
                && number(snapshot, "date_raw", 0, Integer.MAX_VALUE) == identity.dateRaw().intValueExact()
                && number(snapshot, "player_character_id", 1, 0xffff_ffffL) == identity.player().longValueExact(), "LIFE normalized snapshot changed");
        ObjectNode ready = object(snapshot.get("readiness")); StrictJson.trueValue(ready.get("same_frame_ready"));
        StrictJson.trueValue(ready.get(focus ? "legal_focus_candidates_ready" : "legal_perk_candidates_ready"));
        ObjectNode collection = object(snapshot.get(focus ? "legal_focus_candidates" : "legal_perk_candidates"));
        StrictJson.require(text(collection, "status").equals("available"), "LIFE final legal collection unavailable");
        JsonNode items = collection.get("items"); StrictJson.require(items != null && items.isArray(), "LIFE final legal candidates missing");
        int matches = 0; for (JsonNode raw : items) { ObjectNode row = StrictJson.object(raw, Set.of("key", "lifestyle_key")); if (text(row, "key").equals(target) && text(row, "lifestyle_key").equals(lifestyle)) matches++; }
        StrictJson.require(matches == 1, "LIFE target is not exactly one native-final-legal candidate");
        if (focus) {
            StrictJson.require(target.equals("stewardship_wealth_focus") && lifestyle.equals("stewardship_lifestyle")
                    || target.equals("martial_authority_focus") && lifestyle.equals("martial_lifestyle"), "focus outside original action coverage");
            ObjectNode observedFocus = object(query.get("focus_query")); StrictJson.trueValue(observedFocus.get("native_legal"));
            StrictJson.require(text(observedFocus, "target_key").equals(target), "LIFE target differs from its final focus query");
        } else StrictJson.require(AuthoredPerkCatalog.perks().containsKey(target) && AuthoredPerkCatalog.perks().get(target).wire().equals(lifestyle), "perk outside pinned original catalog/lifestyle");
        return StrictJson.object().put("expected_snapshot_id", "native:" + identity.nativeRevision()).put("expected_episode_run_id", expected.episodeRunId())
                .put("expected_date_raw", identity.dateRaw()).put("expected_player_character_id", identity.player())
                .put("expected_native_revision", identity.nativeRevision()).put("expected_proof_epoch", identity.nativeRevision())
                .put("kind", focus ? "focus" : "perk").put("target_key", target);
    }
    private ObjectNode crown(ActionCommand command, String requestId) {
        ObjectNode args = object(StrictJson.parse(OpportunityJson.encode(command.arguments())));
        boolean caller = org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.isCaller(args);
        if (!caller) StrictJson.object(args, Set.of("readback", "law_key", "choice"));
        var readback = CrownAuthorityCodec.decodeReadback(StrictJson.canonical(args.get("readback"))); var source = readback.sourceFrame(); var before = command.before().frame();
        StrictJson.require(source.queriedSnapshotId() != null && source.queriedSnapshotId().equals(before.snapshotId()) && source.queriedRevision().equals(before.revision())
                && source.queriedNativeRevision().equals(before.identity().nativeRevision()) && source.dateRaw().equals(before.identity().dateRaw())
                && source.playerCharacterId().equals(before.identity().player()) && source.exactCk3Build().equals(connectedVersion)
                && source.exeSha256().equalsIgnoreCase(connectedSha256), "Crown exact source/frame changed");
        List<CrownAuthorityPolicy.CurrencyAmount> limits;
        String submittedRequestId;
        if (caller) {
            org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.select(readback,text(args,"law_key"));
            limits=org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.limits(object(args.get("caller_budgets")));
            submittedRequestId=text(args,"caller_request_id");
        } else {
            var choice = CrownAuthorityPolicy.choose(readback);
            StrictJson.require(choice.status() == CrownAuthorityPolicy.Status.READY && text(args, "law_key").equals(choice.lawKey())
                    && StrictJson.parse(CrownAuthorityCodec.encodeChoice(choice)).equals(args.get("choice")), "Crown durable choice differs from actual native quote");
            limits=choice.budgetsRaw();submittedRequestId=requestId;
        }
        StrictJson.require(!submittedRequestId.isEmpty()&&submittedRequestId.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 63, "Crown original action identity exceeds native capacity");
        ObjectNode fields = StrictJson.object().put("expected_date_raw", before.identity().dateRaw()).put("expected_player_character_id", before.identity().player())
                .put("submitted_request_id", submittedRequestId).put("group_key", readback.groupKey()).put("law_key", text(args,"law_key"))
                .put("expected_native_revision", source.nativeSnapshotRevision()).put("expected_proof_epoch", source.proofEpoch());
        for (var amount : limits) {
            StrictJson.require(amount.amountRaw().signum() >= 0 && amount.amountRaw().compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "Crown budget outside native int64 domain");
            fields.put("budget_" + amount.currency().wire() + "_raw", amount.amountRaw());
        }
        return fields;
    }
}
