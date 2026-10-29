package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import static org.xar.ck3.control.governance.council.CouncilCodec.*;

/** Root installs concrete producers/effect consumers and actual private source verifiers together. */
public final class GovernanceActionBindings {
    private GovernanceActionBindings() { }
    public record Sources(ExactRef lifestyle, ExactRef council, ExactRef crown) {
        public Sources { for (ExactRef value : List.of(lifestyle, council, crown)) StrictJson.require(value != null && value.bytes() > 0, "exact original governance producer required"); }
        public ExactRef forOperation(String operation) {
            return switch (operation) {
                case GovernanceActionPreparation.FOCUS, GovernanceActionPreparation.PERK -> lifestyle;
                case CouncilActionCodec.ASSIGN, CouncilActionCodec.PRIVATE_ASSIGN -> council;
                case GovernanceActionPreparation.CROWN -> crown;
                default -> throw new IllegalArgumentException("unsupported governance operation");
            };
        }
    }
    public static List<NativeEffectRegistry.Binding> bindings(Sources sources, GovernanceActionPreparation producer,
            NativeEffectRegistry.Observer actualObserver, Set<OperationKey> rootAdmittedOperations) {
        Objects.requireNonNull(sources); Objects.requireNonNull(producer); Objects.requireNonNull(actualObserver);
        List<NativeEffectRegistry.Binding> result = new ArrayList<>();
        for (OperationKey operation : Set.copyOf(rootAdmittedOperations).stream().sorted(java.util.Comparator.comparing(OperationKey::value)).toList()) {
            StrictJson.require(GovernanceActionPreparation.OPERATIONS.contains(operation.value()), "Root governance set contains an unrelated operation");
            result.add(new NativeEffectRegistry.Binding(operation, sources.forOperation(operation.value()), producer, actualObserver));
        }
        return List.copyOf(result);
    }
    public static List<NativePrivateActionPermission> privatePermissions(Sources sources, Set<OperationKey> rootAdmittedOperations,
            NativePrivateActionPermission.QualificationVerifier actualQualification) {
        Objects.requireNonNull(actualQualification); List<NativePrivateActionPermission> result = new ArrayList<>();
        for (OperationKey operation : Set.copyOf(rootAdmittedOperations)) {
            StrictJson.require(GovernanceActionPreparation.OPERATIONS.contains(operation.value()), "unrelated private governance operation");
            if (operation.value().equals(CouncilActionCodec.ASSIGN)) continue;
            result.add(new NativePrivateActionPermission(operation, "governance-native-" + operation.value(), sources.forOperation(operation.value()), request -> {
                try { validateWire(request); } catch (RuntimeException malformed) { throw new IOException("typed governance native request invalid", malformed); }
            }, actualQualification));
        }
        return List.copyOf(result);
    }
    public static void validateWire(NativeRequest request) {
        String operation = request.step(); ObjectNode fields = object(StrictJson.parse(request.additionalFields().bytes()));
        switch (operation) {
            case CouncilActionCodec.PRIVATE_ASSIGN -> {
                StrictJson.object(fields, Set.of("candidate_character_id")); number(fields, "candidate_character_id", 1, Integer.MAX_VALUE);
            }
            case GovernanceActionPreparation.FOCUS, GovernanceActionPreparation.PERK -> {
                StrictJson.object(fields, Set.of("expected_snapshot_id", "expected_episode_run_id", "expected_date_raw", "expected_player_character_id", "expected_native_revision", "expected_proof_epoch", "kind", "target_key"));
                var nativeRevision = u64(fields.get("expected_native_revision"), true);
                StrictJson.require(text(fields, "expected_snapshot_id").equals("native:" + nativeRevision)
                        && u64(fields.get("expected_proof_epoch"), true).equals(nativeRevision), "LIFE native snapshot/proof mismatch");
                text(fields, "expected_episode_run_id"); number(fields, "expected_date_raw", 0, Integer.MAX_VALUE); number(fields, "expected_player_character_id", 1, 0xffff_ffffL);
                StrictJson.require(text(fields, "kind").equals(operation.equals(GovernanceActionPreparation.FOCUS) ? "focus" : "perk"), "LIFE operation/kind mismatch"); text(fields, "target_key");
            }
            case GovernanceActionPreparation.CROWN -> {
                Set<String> required = Set.of("expected_date_raw", "expected_player_character_id", "submitted_request_id", "group_key", "law_key", "expected_native_revision", "expected_proof_epoch");
                Set<String> actual = new HashSet<>(); fields.fieldNames().forEachRemaining(actual::add);
                StrictJson.require(actual.containsAll(required), "Crown native fields missing"); actual.removeAll(required);
                Set<String> budgets = Set.of("budget_gold_raw", "budget_prestige_raw", "budget_piety_raw", "budget_influence_raw", "budget_merit_raw");
                StrictJson.require(budgets.containsAll(actual), "unknown Crown native field"); actual.forEach(key -> number(fields, key, 0, Long.MAX_VALUE));
                number(fields, "expected_date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE); number(fields, "expected_player_character_id", 1, 0xffff_ffffL);
                u64(fields.get("expected_native_revision"), true); u64(fields.get("expected_proof_epoch"), true);
                StrictJson.require(text(fields, "group_key").equals("crown_authority") && text(fields, "law_key").startsWith("crown_authority_")
                        && text(fields, "submitted_request_id").getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 63, "Crown native identity outside original contract");
            }
            default -> throw new IllegalArgumentException("private governance wire operation not installed");
        }
        StrictJson.require(request.requiredCapability().isEmpty(), "private governance wire must not invent an advertised capability");
    }
}
