package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Existing execute_step operations. Scenario aliases retain the original advertised capability. */
public final class FrontendRulesRequests {
    private static final ObjectMapper JSON = new ObjectMapper();
    private FrontendRulesRequests() { }
    public enum Primitive {
        LOADED_FEATURES("query-loaded-feature-manifest-v1", true, false),
        APPLIED_RULES("query-frontend-applied-game-rules-v1", true, true),
        RULES_WINDOW("query-frontend-game-rules-window-v1", true, true),
        SELECT_RULE("select-frontend-game-rule-v1", false, true),
        APPLY_HIDE_RULES("apply-and-hide-frontend-game-rules-v1", false, true),
        HIDE_RULES("hide-frontend-game-rules-v1", false, true),
        RULE_SELECTIONS("query-frontend-game-rule-selections-v1", true, true),
        OPEN_RULES("activate-frontend-game-rules-v1", false, true),
        ROUTE("query-frontend-gui-route-v1", true, true),
        TREE("inspect-frontend-gui-tree-v1", true, true),
        BOOKMARK_MODEL("probe-frontend-bookmark-model-v1", true, true),
        NEW_GAME("activate-frontend-new-game-v1", false, true),
        PICK_ANY("activate-frontend-pick-any-character-v1", false, true),
        START_BOOKMARK("activate-frontend-start-selected-bookmark-v1", false, true),
        SELECT_1066_BOOKMARK("activate-frontend-select-bookmark-1066-v1", false, true),
        SELECT_1066("select-frontend-supported-1066-character-v1", "game.command.activate-frontend-select-supported-1066-character-v1", false),
        SELECT_RANDOM("activate-frontend-select-random-playable-v1", false, true),
        RULER_DESIGNER("activate-frontend-ruler-designer-v1", false, true),
        SCENARIO_PROBE("probe-frontend-bookmark-model-faith-e01-v1", "game.command.probe-frontend-bookmark-model-v1", true),
        SCENARIO_BOOKMARK("activate-frontend-select-bookmark-faith-e01-v1", "game.command.activate-frontend-select-supported-1066-character-v1", false),
        SCENARIO_CHARACTER("select-frontend-bookmark-character-faith-e01-v1", "game.command.activate-frontend-select-supported-1066-character-v1", false),
        SCENARIO_START("activate-frontend-start-selected-bookmark-faith-e01-v1", "game.command.activate-frontend-start-selected-bookmark-v1", false);
        private final OperationKey operation;
        private final String capability;
        private final boolean readOnly;
        private final boolean frontend;
        Primitive(String step, boolean readOnly, boolean frontend) { this.operation = new OperationKey(step); this.capability = "game.command." + step; this.readOnly = readOnly; this.frontend = frontend; }
        Primitive(String step, String capability, boolean readOnly) { this.operation = new OperationKey(step); this.capability = capability; this.readOnly = readOnly; this.frontend = true; }
        public OperationKey operation() { return operation; }
        public String capability() { return capability; }
        public boolean readOnly() { return readOnly; }
        public boolean frontend() { return frontend; }
        public NativeRequest emptyRequest() { require(this != SELECT_RULE, "Select requires all three typed keys"); return new NativeRequest(operation.value(), capability, raw(JSON.createObjectNode())); }
    }
    public record SelectRule(ScriptKey ruleKey, ScriptKey expectedCurrentSettingKey, ScriptKey desiredSettingKey) {
        public SelectRule { Objects.requireNonNull(ruleKey); Objects.requireNonNull(expectedCurrentSettingKey); Objects.requireNonNull(desiredSettingKey); }
        public NativeRequest nativeRequest() {
            ObjectNode fields = JSON.createObjectNode(); fields.put("rule_key", ruleKey.value()); fields.put("expected_current_setting_key", expectedCurrentSettingKey.value()); fields.put("desired_setting_key", desiredSettingKey.value());
            return new NativeRequest(Primitive.SELECT_RULE.operation().value(), Primitive.SELECT_RULE.capability(), raw(fields));
        }
    }
    static RawJson raw(ObjectNode value) { try { return new RawJson(JSON.writeValueAsBytes(value)); } catch (IOException failure) { throw new IllegalArgumentException("native request serialization failed", failure); } }
}
