package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;

/** Bounded canonical journal arguments retain original archived reads rather than copying full GUI/native payloads. */
final class FrontendRulesArguments {
    private static final ObjectMapper JSON = new ObjectMapper();
    private FrontendRulesArguments() { }
    record Select(FrontendRulesRequests.SelectRule request, ExactRef selections, ExactRef window) {
        Select { Objects.requireNonNull(request); Objects.requireNonNull(selections); Objects.requireNonNull(window); }
    }
    record Closure(RulesAction action, ExactRef selections, ExactRef window) {
        Closure { Objects.requireNonNull(action); require(action != RulesAction.SELECT, "closure action required"); Objects.requireNonNull(selections); Objects.requireNonNull(window); }
    }
    record RouteInput(ExactRef before, java.util.Optional<ExactRef> tree) {
        RouteInput { Objects.requireNonNull(before); Objects.requireNonNull(tree); }
    }
    record ModelInput(String characterKey, ExactRef model, boolean scenario) {
        ModelInput { new ScriptKey(characterKey); Objects.requireNonNull(model); }
    }
    static OpportunityJson.Obj empty() { return domain(JSON.createObjectNode()); }
    static OpportunityJson.Obj selection(Select value) {
        ObjectNode node = JSON.createObjectNode(); node.put("rule_key", value.request().ruleKey().value()); node.put("expected_current_setting_key", value.request().expectedCurrentSettingKey().value()); node.put("desired_setting_key", value.request().desiredSettingKey().value());
        node.set("selections", ref(value.selections())); node.set("window", ref(value.window())); return domain(node);
    }
    static Select selection(OpportunityJson.Obj arguments) {
        ObjectNode node = node(arguments); exact(node, Set.of("rule_key", "expected_current_setting_key", "desired_setting_key", "selections", "window"));
        return new Select(new FrontendRulesRequests.SelectRule(new ScriptKey(text(node, "rule_key")), new ScriptKey(text(node, "expected_current_setting_key")), new ScriptKey(text(node, "desired_setting_key"))), ref(obj(node, "selections")), ref(obj(node, "window")));
    }
    static OpportunityJson.Obj closure(Closure value) {
        ObjectNode node = JSON.createObjectNode(); node.put("action", value.action().wire()); node.set("selections", ref(value.selections())); node.set("window", ref(value.window())); return domain(node);
    }
    static Closure closure(OpportunityJson.Obj arguments) {
        ObjectNode node = node(arguments); exact(node, Set.of("action", "selections", "window")); String action = text(node, "action");
        require(action.equals("hide") || action.equals("apply_and_hide"), "closed rule action required"); return new Closure(action.equals("hide") ? RulesAction.HIDE : RulesAction.APPLY_AND_HIDE, ref(obj(node, "selections")), ref(obj(node, "window")));
    }
    static OpportunityJson.Obj route(RouteInput value) {
        ObjectNode node = JSON.createObjectNode(); node.set("before", ref(value.before()));
        if (value.tree().isPresent()) node.set("tree", ref(value.tree().get())); else node.putNull("tree"); return domain(node);
    }
    static RouteInput route(OpportunityJson.Obj arguments) {
        ObjectNode node = node(arguments); exact(node, Set.of("before", "tree")); JsonNode tree = field(node, "tree");
        return new RouteInput(ref(obj(node, "before")), tree.isNull() ? java.util.Optional.empty() : java.util.Optional.of(ref(tree)));
    }
    static OpportunityJson.Obj model(ModelInput value) {
        ObjectNode node = JSON.createObjectNode(); node.put("character_key", value.characterKey()); node.set("model", ref(value.model())); node.put("scenario", value.scenario()); return domain(node);
    }
    static ModelInput model(OpportunityJson.Obj arguments) {
        ObjectNode node = node(arguments); exact(node, Set.of("character_key", "model", "scenario")); return new ModelInput(text(node, "character_key"), ref(obj(node, "model")), bool(node, "scenario"));
    }
    static OpportunityJson.Obj key(String key) { ObjectNode value = JSON.createObjectNode(); value.put("character_key", new ScriptKey(key).value()); return domain(value); }
    static String key(OpportunityJson.Obj arguments) { ObjectNode value = node(arguments); exact(value, Set.of("character_key")); return new ScriptKey(text(value, "character_key")).value(); }
    static ObjectNode node(OpportunityJson.Obj arguments) { return object(new RawJson(OpportunityJson.encode(arguments))); }
    static OpportunityJson.Obj domain(ObjectNode node) {
        OpportunityJson.Value value = OpportunityJson.parse(FrontendRulesRequests.raw(node).bytes()); require(value instanceof OpportunityJson.Obj, "journal argument object required"); return (OpportunityJson.Obj) value;
    }
    static ObjectNode ref(ExactRef value) { ObjectNode node = JSON.createObjectNode(); node.put("path", value.path()); node.put("sha256", value.sha256()); node.put("bytes", value.bytes()); return node; }
    static ExactRef ref(JsonNode value) {
        exact(value, Set.of("path", "sha256", "bytes")); long bytes = integer(value, "bytes", java.math.BigInteger.ONE, java.math.BigInteger.valueOf(9007199254740991L)).longValueExact();
        return new ExactRef(text(value, "path"), bytes, text(value, "sha256"));
    }
}
