package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Original offline public query, explicitly sharing the complete catalog used by discovery. */
public final class VanillaEventKnowledgeMethods {
    public static final String NAME = "ck3_query_vanilla_event_knowledge_v1";
    public record Request(String eventDefinitionKey, String ck3Build) {
        public Request { Objects.requireNonNull(eventDefinitionKey); Objects.requireNonNull(ck3Build); }
    }
    public record Response(RawJson original) { public Response { Objects.requireNonNull(original); } }
    private final VanillaEventCatalog fullCatalog;
    private final String originalPublicDefaultBuild;
    public VanillaEventKnowledgeMethods(VanillaEventCatalog sameFullCatalog, ToolDescriptor actualOriginalDescriptor) {
        fullCatalog = Objects.requireNonNull(sameFullCatalog); Objects.requireNonNull(actualOriginalDescriptor);
        McpJson.require(NAME.equals(actualOriginalDescriptor.name()), "actual original full event query descriptor required");
        ObjectNode descriptor = McpJson.object(McpJson.parse(actualOriginalDescriptor.original().bytes()));
        var defaultBuild = descriptor.path("inputSchema").path("properties").path("ck3_build").get("default");
        McpJson.require(defaultBuild != null && defaultBuild.isTextual(), "source-owned MCP default build required");
        // MCP passes CURRENT_CK3_BUILD; the registry function itself has a different EXACT default.
        originalPublicDefaultBuild = defaultBuild.textValue();
    }
    public Response query(Request request) {
        Objects.requireNonNull(request);
        var original = fullCatalog.fullQuery(request.ck3Build(), request.eventDefinitionKey());
        RawJson encoded = new RawJson(RetainedJson.pythonCanonical(original,
                new RetainedJson.CanonicalBudget(RawJson.MAXIMUM_BYTES, RawJson.MAXIMUM_BYTES, 1000)).bytes());
        McpJson.publicNumbers(McpJson.parse(encoded.bytes()));
        return new Response(encoded);
    }
    public List<McpExecutableDirectory.DirectBinding<?, ?>> actualMethods(ExactRef actualCompiledImplementation) {
        return List.of(new McpExecutableDirectory.DirectBinding<>(NAME, PublicMcpBindings.Kind.STATIC_KNOWLEDGE,
                Request.class, Response.class, this::query, call -> decode(call.arguments()),
                response -> CallResult.fromBusinessJson(response.original()),
                new PublicRoutes.Target(getClass().getName(), "query", actualCompiledImplementation)));
    }
    public Request decode(Arguments arguments) {
        ObjectNode input = McpJson.object(McpJson.parse(arguments.objectOrEmpty().bytes()));
        McpJson.fields(input, Set.of("event_definition_key", "ck3_build"), Set.of("event_definition_key"));
        McpJson.require(input.get("event_definition_key").isTextual(), "original event key argument must be a string");
        String build = originalPublicDefaultBuild;
        if (input.has("ck3_build")) {
            McpJson.require(input.get("ck3_build").isTextual(), "original build argument must be a string");
            build = input.get("ck3_build").textValue();
        }
        // Blank/invalid keys and unsupported builds use the complete provider's original response branches.
        return new Request(input.get("event_definition_key").textValue(), build);
    }
    public VanillaEventCatalog catalog() { return fullCatalog; }
}
