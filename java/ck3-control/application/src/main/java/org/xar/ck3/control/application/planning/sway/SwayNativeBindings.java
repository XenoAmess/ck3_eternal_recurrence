package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual exact read registrations and primitive preparation; no endpoint, writer or dispatch authority. */
public final class SwayNativeBindings {
    public static final String START_ARGUMENTS = "xar.java.sway-start-command/v1";
    public static final String PUBLIC_START_ARGUMENTS = "xar.java.sway-start-public-command/v1";
    public static final String STOP_ARGUMENTS = "xar.java.sway-stop-command/v1";
    private SwayNativeBindings() { }

    public static ReadContract<SwayNativeWire.TargetRead> target(ExactRef definitionSource, long target) {
        SwayNativeWire.actionCharacter(target); OperationKey key = new OperationKey(SwayNativeWire.TARGET + target);
        return new ReadContract<>("sway-target-actual4:" + target, key, Optional.empty(), "allow_private_active_scheme_sway_query",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, definitionSource,
                (request, requestId) -> {
                    JsonNode args = args(request.arguments(), Set.of("target_character_id"));
                    require(SwayNativeWire.actionCharacter(args, "target_character_id") == target, "installed Sway target differs");
                    return new NativeRequest(key.value(), Optional.empty(), new RawJson(StrictJson.canonical(StrictJson.object())));
                }, original -> SwayNativeWire.target(original.original().originalFrame().bytes(), original.requestId(), bind(original, key), target));
    }
    /** Receipt is read-only even though its original historical wire lacks read_only. It never sends Start. */
    public static ReadContract<SwayNativeWire.AppliedReceipt> receipt(ExactRef definitionSource, long target, String actionId, BigInteger preCaptureEpoch) {
        SwayNativeWire.actionCharacter(target); SwayNativeWire.action(actionId, false); SwayNativeWire.u64(preCaptureEpoch, 1);
        OperationKey key = new OperationKey(SwayNativeWire.RECEIPT + target);
        return new ReadContract<>("sway-receipt-actual4:" + target + ":" + actionId, key, Optional.empty(), "allow_private_active_scheme_sway_action",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, definitionSource,
                (request, requestId) -> {
                    JsonNode args = args(request.arguments(), Set.of("action_id")); SwayNativeWire.equals(args, "action_id", actionId);
                    ObjectNode extra = StrictJson.object(); extra.put("action_id", actionId); return primitive(key.value(), extra);
                }, original -> SwayNativeWire.receipt(original.original().originalFrame().bytes(), original.requestId(), bind(original, key), actionId, target, preCaptureEpoch));
    }

    /** Every preparation re-decodes the archived original guarded read, instead of trusting proposal copies. */
    public static ActionPorts.PreparationPort startPreparation(ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(archive);
        return command -> {
            JsonNode row = args(command.arguments(), Set.of("schema", "target_character_id", "original_target_read"));
            var admission=startAdmission(row); SwayNativeWire.action(command.actionId(), false);
            long target = SwayNativeWire.actionCharacter(row, "target_character_id");
            require(command.operation().value().equals(SwayNativeWire.START + target), "Sway Start exact operation differs");
            PlanningReadReceipt original = archive.loadRead(ExactRef.fromJson(row.get("original_target_read")));
            require(original.request().before().equals(command.before()) && original.request().source().equals(command.source())
                    && original.request().sessionId().equals(command.sessionId()), "Sway Start original read crossed origin");
            SwayNativeWire.TargetRead read = SwayNativeWire.target(original.original().originalFrame().bytes(), original.requestId(), bind(original, new OperationKey(SwayNativeWire.TARGET + target)), target);
            require(SwayFormalState.startEligible(read,true,admission), "Sway Start requires its explicit ordinary opportunity or public native final input");
            ObjectNode extra = StrictJson.object(); extra.put("action_id", command.actionId()); extra.put("expected_capture_epoch", read.captureEpoch());
            extra.put("expected_container_generation", read.containerGeneration()); extra.put("expected_target_opinion_of_actor", Integer.toString(read.targetOpinion()));
            return primitive(command.operation().value(), extra);
        };
    }
    public static SwayFormalState.StartAdmission startAdmission(JsonNode arguments) {
        StrictJson.object(arguments,Set.of("schema","target_character_id","original_target_read"));String schema=SwayNativeWire.string(arguments,"schema");
        if(START_ARGUMENTS.equals(schema))return SwayFormalState.StartAdmission.ORDINARY_OPPORTUNITY;
        require(PUBLIC_START_ARGUMENTS.equals(schema),"registered exact Sway Start command schema required");return SwayFormalState.StartAdmission.PUBLIC_NATIVE_FINAL;
    }
    /** Eligibility and durable pending Stop are additionally revalidated by the SWAY Intent hook. */
    public static ActionPorts.PreparationPort stopPreparation() {
        return command -> {
            JsonNode row = args(command.arguments(), Set.of("schema", "original_action_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation", "original_target_read", "completion_read", "opinion_read"));
            SwayNativeWire.equals(row, "schema", STOP_ARGUMENTS); SwayNativeWire.action(command.actionId(), true); SwayNativeWire.action(SwayNativeWire.string(row, "original_action_id"), false);
            require(command.operation().value().equals(SwayNativeWire.STOP), "Sway Stop exact operation differs");
            long actor = command.before().frame().identity().player().longValueExact(), target = SwayNativeWire.integer(row, "target_character_id", 1, Integer.MAX_VALUE);
            long id = SwayNativeWire.integer(row, "scheme_instance_id", 0, 0xffff_fffeL); int generation = Math.toIntExact(SwayNativeWire.integer(row, "scheme_instance_generation", 0, 255));
            SwayNativeWire.currentCharacter(actor); SwayNativeWire.instance(id, generation); require(actor != target, "Sway Stop actor/target differs");
            for (String field : List.of("original_target_read", "completion_read", "opinion_read")) require(ExactRef.fromJson(row.get(field)).bytes() > 0, "original Stop evidence required");
            ObjectNode extra = StrictJson.object(); extra.put("action_id", command.actionId()); extra.put("actor_character_id", actor); extra.put("target_character_id", target);
            extra.put("scheme_instance_id", id); extra.put("scheme_instance_generation", generation); return primitive(SwayNativeWire.STOP, extra);
        };
    }

    public static SwayNativeWire.Binding bind(PlanningReadReceipt receipt, OperationKey operation) {
        require(receipt.request().operation().equals(operation) && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "Sway original read operation/ACK missing");
        var request = receipt.request(); var before = receipt.before(); var after = receipt.after();
        for (PlanningReadGuard guard : List.of(before, after)) {
            GuardEvidence binding = guard.binding(); require(binding.observed().equals(request.before()) && binding.source().equals(request.source())
                    && binding.sessionId().equals(request.sessionId()) && binding.operation().equals(operation)
                    && guard.paused() && guard.mapReady() && guard.playerAlive(), "Sway read lost full paused living guard");
        }
        require(before.originalBindingSha256().equals(after.originalBindingSha256()) && before.binding().connectionGeneration().equals(after.binding().connectionGeneration())
                && before.binding().authorityId().equals(after.binding().authorityId()), "Sway native custody changed");
        require(SwayNativeWire.BUILD.equals(request.source().exactBuild()), "Sway read source exact build differs");
        JsonNode packet = StrictJson.parse(receipt.original().originalFrame().bytes(), SwayNativeWire.MAX);
        JsonNode token = StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes(), SwayNativeWire.MAX);
        require(packet.isObject() && packet.get("result") != null && packet.get("result").equals(token), "Sway original complete frame and separate result token differ");
        return new SwayNativeWire.Binding(request.before(), request.sessionId(), before.binding().connectionGeneration(), before.binding().authorityId(), SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    static NativeRequest primitive(String step, ObjectNode extra) { return new NativeRequest(step, Optional.empty(), new RawJson(StrictJson.canonical(extra))); }
    static JsonNode args(OpportunityJson.Obj value, Set<String> fields) { return StrictJson.object(StrictJson.parse(OpportunityJson.encode(value)), fields); }
}
