package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/**
 * Exact public war result projection after the sole full native receipt decoder. This is pure:
 * no query, publication, permit, current-frame acquisition, cache activation or submission.
 */
public final class ArmyWarPublicResultCodec {
    private ArmyWarPublicResultCodec() { }

    public static RawJson encode(ArmyWarReadCodec.Scope scope, PlanningReadReceipt original,
            ArmyWarReadCodec.Observation observed, Optional<UInt64> declarationSequence) {
        Objects.requireNonNull(scope); Objects.requireNonNull(original); Objects.requireNonNull(observed);
        Objects.requireNonNull(declarationSequence);
        require(scope.call().method() == observed.method(), "public method differs from actual typed observation");
        var selectedArgs = DriverJson.object(ArmyCallCodec.encode(scope.call()).bytes(), DriverJson.MAX_NATIVE_BYTES);
        require(original.request().arguments().equals(selectedArgs), "public war reply changed the original typed request");
        require(ArmyWarReadCodec.decode(scope, original).equals(observed), "public war reply differs from the full original native receipt");
        ObjectNode result = object(OpportunityJson.toNode(observed.normalizedResult())).deepCopy();
        switch (observed.method()) {
            case QUERY_DECLARABLE_WARS -> {
                // Python publishes the original normalized result plus the Driver backend only.
                absent(result, "queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_date_raw");
                backend(result);
            }
            case QUERY_WAR_OCCUPATION_TARGETS_V1, QUERY_WAR_TERMINATION_OPTIONS, QUERY_WAR_TERMINATION_TERMS, QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS -> {
                // One original Driver projection owns its full metadata and recipient guards.
                // Service adds only its own selected war ID before the shared public number projection.
                result=object(OpportunityJson.toNode(DriverJson.object(ArmyWarOriginalResultCodec.encode(scope,original,observed).bytes(),DriverJson.MAX_NATIVE_BYTES)));
                war(result,scope);
            }
            case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1 -> {
                // The private producer has its own exact build backend and public domain shape.
                triplet(result, scope);
            }
            case QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1 -> { backend(result); triplet(result, scope); }
            case QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2 -> {
                backend(result); triplet(result, scope);
                ObjectNode snapshot = object(OpportunityJson.toNode(scope.currentSnapshot()));
                bind(result, "queried_date_raw", get(snapshot, "date_raw"));
                bind(result, "queried_actor_character_id", get(object(get(snapshot, "played_character")), "character_id"));
                bind(result, "queried_connection_generation", get(object(get(snapshot, "diagnostics")), "connection_generation"));
                bind(result, "queried_episode_run_id", get(snapshot, "episode_run_id"));
                var selected = scope.declaration().orElseThrow(() -> new IllegalArgumentException("actual selected declaration is absent"));
                ObjectNode source = DeclarationContract.encodeChoice(selected);
                // current_prewar_declaration_source emits exactly this seven-field selection.
                ObjectNode exact = empty();
                for (String name : List.of("declaration_id", "target_character_id", "casus_belli_index", "casus_belli_key",
                        "configuration_index", "claimant_character_id", "target_title_ids")) exact.set(name, get(source, name));
                bind(result, "selected_declaration_source", exact);
                UInt64 sequence = declarationSequence.orElseThrow(() -> new IllegalArgumentException("actual declaration lease query sequence is absent"));
                require(sequence.value().signum() > 0, "actual declaration query sequence must be positive");
                bind(result, "declaration_query_sequence", empty().numberNode(sequence.value()));
            }
            default -> throw new IllegalArgumentException("public war projection is not supported; loaded-effect exit preview remains disabled");
        }
        requireSourceMetadata(result, scope, original);
        return ArmyPublicWire.encodeExactSourceBound(DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES), scope.context());
    }

    private static void war(ObjectNode result, ArmyWarReadCodec.Scope scope) {
        require(scope.call() instanceof ArmyCalls.War, "selected public war call is absent");
        bind(result, "war_id", empty().numberNode(((ArmyCalls.War) scope.call()).warId()));
    }
    private static void backend(ObjectNode result) { bind(result, "backend_id", empty().textNode("native-headless")); }
    private static void triplet(ObjectNode result, ArmyWarReadCodec.Scope scope) {
        var context = scope.context();
        bind(result, "queried_snapshot_id", empty().textNode(context.before().frame().snapshotId()));
        bind(result, "queried_revision", empty().numberNode(context.before().frame().revision()));
        bind(result, "queried_native_revision", empty().numberNode(context.nativeRevision()));
    }
    private static void requireSourceMetadata(ObjectNode result, ArmyWarReadCodec.Scope scope, PlanningReadReceipt original) {
        ObjectNode snapshot = object(OpportunityJson.toNode(scope.currentSnapshot()));
        for (String field : List.of("queried_date_raw", "query_date_raw")) if (result.has(field))
            equal(get(result, field), scope.context().dateRaw());
        if (result.has("queried_actor_character_id")) equal(get(result, "queried_actor_character_id"), scope.context().playerId());
        if (result.has("queried_connection_generation")) {
            var value=result.get("queried_connection_generation");
            if(value.isNull()) {
                var diagnostics=snapshot.get("diagnostics");var actual=diagnostics!=null&&diagnostics.isObject()?diagnostics.get("connection_generation"):null;
                require(actual==null||actual.isNull(),"public war null connection contradicts the original semantic source");
            } else equal(value,original.before().binding().connectionGeneration());
        }
        for (String field : List.of("queried_episode_run_id", "episode_run_id")) if (result.has(field)) {
            var actual=snapshot.get("episode_run_id");var value=result.get(field);
            require(value.isNull()?(actual==null||actual.isNull()):value.equals(actual),"public war episode metadata changed");
        }
    }
    private static void bind(ObjectNode object, String field, com.fasterxml.jackson.databind.JsonNode exact) {
        if (object.has(field)) require(get(object, field).equals(exact), "original public field conflicts with actual source: " + field);
        else object.set(field, exact.deepCopy());
    }
    private static void absent(ObjectNode object, String... fields) {
        for (String field : fields) require(!object.has(field), "original declaration result contains unexpected public metadata: " + field);
    }
}


