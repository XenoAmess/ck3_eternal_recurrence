package org.xar.ck3.control.wave3.governance.lifestylescope;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneCodec;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.SceneInput;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopePolicy.*;

/** Strict LIFE wrapper; shared scene/history JSON is parsed only by ConstructionSceneCodec. */
public final class LifestyleScopeCodec {
    public static final String SCHEMA = "xar.java.lifestyle-scope.v1";
    public static final int MAX_BYTES = 65_536;
    private static final ObjectMapper PROJECTION_TRANSPORT = new ObjectMapper();
    private LifestyleScopeCodec() { }

    public sealed interface Input permits WrapperInput, ServiceRequest { SceneInput scene(); }
    public record WrapperInput(Mode mode, SceneInput scene) implements Input {
        public WrapperInput { Objects.requireNonNull(mode); Objects.requireNonNull(scene); }
    }
    public record ServiceRequest(ServiceInput input) implements Input {
        public ServiceRequest { Objects.requireNonNull(input); }
        @Override public SceneInput scene() { return input.scene(); }
    }
    public static Input decode(byte[] raw) {
        JsonNode node = StrictJson.object(StrictJson.parse(raw, MAX_BYTES), Set.of("schema", "operation", "scene", "service"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "lifestyle scope schema required");
        SceneInput scene = ConstructionSceneCodec.decodeScene(sceneBytes(node.get("scene")));
        String operation = StrictJson.text(node.get("operation"));
        if (operation.equals("service")) { return new ServiceRequest(service(node.get("service"), scene)); }
        StrictJson.require(node.get("service").isNull(), "wrapper operation requires an explicit null service field");
        Mode mode = switch (operation) {
            case "feudal_peace" -> Mode.FEUDAL_PEACE;
            case "feudal_lifestyle" -> Mode.FEUDAL_LIFESTYLE;
            case "player_perk" -> Mode.PLAYER_PERK;
            default -> throw new IllegalArgumentException("unknown lifestyle scope operation");
        };
        return new WrapperInput(mode, scene);
    }
    private static byte[] sceneBytes(JsonNode node) {
        // Preserve valid JSON numeric types in unconsumed SDK extensions; shared decodeScene validates consumed fields.
        try { byte[] raw = PROJECTION_TRANSPORT.writeValueAsBytes(node);
            StrictJson.require(raw.length <= ConstructionSceneCodec.MAX_BYTES, "shared scene byte budget"); return raw;
        } catch (IOException error) { throw new ContractViolationException("unable to transport shared scene projection", error); }
    }
    private static ServiceInput service(JsonNode value, SceneInput scene) {
        JsonNode node = StrictJson.object(value, Set.of("initial_focus_required", "cached_v3", "capability_read"));
        Cache cache = switch (StrictJson.text(node.get("cached_v3"))) {
            case "unset" -> Cache.UNSET; case "enabled" -> Cache.ENABLED; case "disabled" -> Cache.DISABLED;
            default -> throw new IllegalArgumentException("unknown capability cache state");
        };
        JsonNode read = StrictJson.object(node.get("capability_read"), Set.of("status", "bridge_capabilities"));
        CapabilityStatus status = switch (StrictJson.text(read.get("status"))) {
            case "not_queried" -> CapabilityStatus.NOT_QUERIED; case "unavailable" -> CapabilityStatus.UNAVAILABLE;
            case "available" -> CapabilityStatus.AVAILABLE;
            default -> throw new IllegalArgumentException("unknown capability read status");
        };
        StrictJson.require(read.get("bridge_capabilities").isArray(), "capability list required");
        List<String> capabilities = new ArrayList<>();
        for (JsonNode capability : read.get("bridge_capabilities")) { capabilities.add(StrictJson.text(capability)); }
        return new ServiceInput(scene, bool(node.get("initial_focus_required")), cache, new CapabilityRead(status, capabilities));
    }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean required"); return node.booleanValue();
    }
    public sealed interface Output permits WrapperOutput, ServiceOutput { }
    public record WrapperOutput(org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.RootScope scope) implements Output { }
    public record ServiceOutput(ServiceSelection selection) implements Output { }
    public static Output project(Input input) {
        return switch (input) {
            case WrapperInput wrapper -> new WrapperOutput(LifestyleScopePolicy.assess(wrapper.scene(), wrapper.mode()).root());
            case ServiceRequest request -> new ServiceOutput(LifestyleScopePolicy.forService(request.input()));
        };
    }
    public static byte[] encodeResult(Output output) {
        return switch (output) {
            case WrapperOutput wrapper -> ConstructionSceneCodec.encodeRootScope(wrapper.scope());
            case ServiceOutput service -> encodeSelection(service.selection());
        };
    }
    public static byte[] evaluate(byte[] raw) { return encodeResult(project(decode(raw))); }
    public static byte[] encodeSelection(ServiceSelection selection) {
        ObjectNode node = StrictJson.object();
        node.set("scope", StrictJson.parse(ConstructionSceneCodec.encodeRootScope(selection.assessment().root()), 4_096));
        node.put("capability_cache_present", selection.nextCache() != Cache.UNSET);
        if (selection.nextCache() == Cache.UNSET) { node.putNull("all_lifestyle_v3_capability"); }
        else { node.put("all_lifestyle_v3_capability", selection.nextCache() == Cache.ENABLED); }
        node.put("capability_read_used", selection.capabilityReadUsed());
        return StrictJson.canonical(node, 8_192);
    }
    public static byte[] encode(Input input) {
        ObjectNode node = StrictJson.object(); node.put("schema", SCHEMA);
        node.set("scene", StrictJson.parse(ConstructionSceneCodec.encodeScene(input.scene()), ConstructionSceneCodec.MAX_BYTES));
        if (input instanceof WrapperInput wrapper) {
            node.put("operation", switch (wrapper.mode()) {
                case FEUDAL_PEACE -> "feudal_peace"; case FEUDAL_LIFESTYLE -> "feudal_lifestyle"; case PLAYER_PERK -> "player_perk";
            }); node.putNull("service");
        } else if (input instanceof ServiceRequest request) {
            node.put("operation", "service"); ServiceInput service = request.input(); ObjectNode context = StrictJson.object();
            context.put("initial_focus_required", service.initialFocusRequired());
            context.put("cached_v3", service.cachedV3().name().toLowerCase(java.util.Locale.ROOT));
            ObjectNode read = StrictJson.object(); read.put("status", service.capabilityRead().status().name().toLowerCase(java.util.Locale.ROOT));
            ArrayNode capabilities = read.putArray("bridge_capabilities"); service.capabilityRead().bridgeCapabilities().forEach(capabilities::add);
            context.set("capability_read", read); node.set("service", context);
        }
        return StrictJson.canonical(node, MAX_BYTES);
    }
}
