package org.xar.ck3.control.service.mcp;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.discovery.EventDiscovery;
import org.xar.ck3.control.wave2.events.discovery.EventDiscovery.Request;
import org.xar.ck3.control.wave2.events.discovery.EventDiscovery.Response;
import org.xar.ck3.control.wave2.events.discovery.EventDiscoveryCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** The actual offline MCP handler. Root must supply a fully loaded sole catalog and the owned evidence reader. */
public final class EventDiscoveryPublicService {
    public static final String NAME = "ck3_list_vanilla_event_knowledge_v1";
    @FunctionalInterface public interface PortableKeys {
        /** The actual PortableEvidenceReader method throws only its BundleException, an IOException subtype. */
        Set<String> load() throws IOException;
    }
    private final EventDiscovery discovery;
    private final VanillaEventCatalog catalog;
    private final PortableKeys portable;
    private final String publicDefaultBuild;
    public EventDiscoveryPublicService(VanillaEventCatalog actualCompleteCatalog, PortableKeys actualPortableReader, String actualPublicDefaultBuild) {
        catalog = Objects.requireNonNull(actualCompleteCatalog);
        discovery = new EventDiscovery(actualCompleteCatalog::catalog, actualCompleteCatalog.textRules());
        portable = Objects.requireNonNull(actualPortableReader);
        StrictJson.require(actualPublicDefaultBuild != null
                && org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge.EXE.containsKey(actualPublicDefaultBuild),
                "source-bound original public default build required");
        publicDefaultBuild = actualPublicDefaultBuild;
    }
    public VanillaEventCatalog catalog() { return catalog; }
    public static EventDiscoveryPublicService fromOriginalDescriptor(VanillaEventCatalog actualCompleteCatalog,
            PortableKeys actualPortableReader, ToolDescriptor original) {
        StrictJson.require(NAME.equals(original.name()), "original event discovery declaration required");
        var schema = McpJson.object(McpJson.parse(original.original().bytes()));
        String declared = McpJson.text(schema.path("inputSchema").path("properties").path("ck3_build").get("default"));
        return new EventDiscoveryPublicService(actualCompleteCatalog, actualPortableReader, declared);
    }
    public Request decode(Arguments arguments) {
        // The original MCP wrapper deliberately treats missing/null arguments as an empty argument object.
        return EventDiscoveryCodec.decodeRequest(arguments.objectOrEmpty().bytes(), discovery.textRules(), publicDefaultBuild);
    }
    public Response list(Request request) {
        Set<String> keys = Set.of();
        // Preserve the original wrapper order, including evidence lookup before discovery validates historical filters.
        if ("1.19.0.6".equals(request.parameters().ck3Build())) {
            try { keys = Set.copyOf(portable.load()); }
            catch (IOException actualBundleFailure) { keys = Set.of(); }
        }
        return discovery.list(request, keys);
    }
    public List<McpExecutableDirectory.DirectBinding<?, ?>> actualMethods(ExactRef actualThisSource) {
        StrictJson.require(actualThisSource != null && actualThisSource.bytes() > 0, "exact installed discovery handler source required");
        return List.of(new McpExecutableDirectory.DirectBinding<>(NAME, PublicMcpBindings.Kind.STATIC_KNOWLEDGE,
                Request.class, Response.class, this::list, call -> decode(call.arguments()),
                response -> CallResult.fromBusinessJson(new RawJson(EventDiscoveryCodec.encode(response))),
                new PublicRoutes.Target(getClass().getName(), "list", actualThisSource)));
    }
}
