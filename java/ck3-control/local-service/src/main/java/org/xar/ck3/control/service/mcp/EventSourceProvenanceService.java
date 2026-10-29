package org.xar.ck3.control.service.mcp;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.wave2.events.registered.EventSourceProvenance;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual public static-knowledge handler; Root assembles this exact binding and does not recreate the source index. */
public final class EventSourceProvenanceService {
    public static final String TOOL="ck3_query_vanilla_event_source_provenance_v1";
    private final RegisteredEventKnowledge sameKnowledge;
    public EventSourceProvenanceService(RegisteredEventKnowledge sameKnowledge) { this.sameKnowledge=Objects.requireNonNull(sameKnowledge); }
    public EventSourceProvenance.Response query(EventSourceProvenance.Query request) {
        return EventSourceProvenance.query(Objects.requireNonNull(request),sameKnowledge::sourceIndex);
    }
    public McpExecutableDirectory.DirectBinding<EventSourceProvenance.Query,EventSourceProvenance.Response> actualMethod(ExactRef implementationSource) {
        Objects.requireNonNull(implementationSource);
        return new McpExecutableDirectory.DirectBinding<>(TOOL,PublicMcpBindings.Kind.STATIC_KNOWLEDGE,
                EventSourceProvenance.Query.class,EventSourceProvenance.Response.class,this::query,
                call->decode(call.arguments().objectOrEmpty()),response->CallResult.fromBusinessJson(encode(response)),
                new PublicRoutes.Target(getClass().getName(),"query",implementationSource));
    }
    public static EventSourceProvenance.Query decode(RawJson original) {
        ObjectValue arguments=RetainedJson.object(RetainedJson.parse(Objects.requireNonNull(original).bytes()));
        McpJson.require(Set.of("key","build").containsAll(arguments.fields().keySet()),"unknown source provenance argument");
        Value key=arguments.getOrNull("key");McpJson.require(key instanceof StringValue,"source provenance key must be a string");
        Value build=arguments.contains("build")?arguments.get("build"):new StringValue(EventSourceProvenance.CURRENT_BUILD);
        McpJson.require(build instanceof StringValue,"source provenance build must be a string");
        return new EventSourceProvenance.Query(((StringValue)key).value(),((StringValue)build).value());
    }
    public static RawJson encode(EventSourceProvenance.Response response) { return new RawJson(RetainedJson.encode(Objects.requireNonNull(response).json())); }
}
