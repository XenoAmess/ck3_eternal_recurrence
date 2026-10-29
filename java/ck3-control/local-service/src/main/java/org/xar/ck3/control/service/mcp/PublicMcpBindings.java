package org.xar.ck3.control.service.mcp;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeFailure;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;
import org.xar.ck3.control.service.root.PrisonerPublicFailure12004;
import org.xar.ck3.control.service.root.RootAubRuntimeFactory;
import org.xar.ck3.control.service.root.StatusCapabilityFailure;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiActionFailure;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiReadFailure;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes.TypedRoute;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Original admission, descriptor, concrete route and result schema are one checked installation. */
public final class PublicMcpBindings {
    @FunctionalInterface public interface Decoder<Q> { Q decode(ToolCall call) throws ToolFailure, RpcFailure; }
    @FunctionalInterface public interface Encoder<R> { CallResult encode(R response) throws ToolFailure; }
    @FunctionalInterface public interface CallEncoder<R> { CallResult encode(ToolCall originalCall, R response) throws ToolFailure; }
    @FunctionalInterface public interface ResourceHandler<R> { R read(ResourceCall call) throws InterruptedException, ToolFailure, RpcFailure; }
    @FunctionalInterface public interface ResourceEncoder<R> { ResourceResult encode(R response) throws ToolFailure; }
    public enum Kind { PUBLIC_SERVICE, DRIVER_DIRECT, STATIC_KNOWLEDGE, APPLICATION_COMPOSITE }
    public record BindingInfo(String name, Kind kind, PublicRoutes.Target actualTarget, Optional<String> publicMethod) {
        public BindingInfo {
            McpJson.toolName(name); Objects.requireNonNull(kind); Objects.requireNonNull(actualTarget); Objects.requireNonNull(publicMethod);
            McpJson.require((kind == Kind.PUBLIC_SERVICE) == publicMethod.isPresent(), "service binding metadata must retain the exact public method");
        }
    }
    private interface Bound {
        ToolDescriptor descriptor();
        CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure;
        BindingInfo info();
    }
    private record Typed<Q,R>(ToolDescriptor descriptor, Class<Q> requestType, Class<R> responseType,
            PublicRoutes.Handler<Q,R> handler, Decoder<Q> decoder, CallEncoder<R> encoder, BindingInfo info) implements Bound {
        @Override public CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure {
            final Q request;
            try {
                descriptor.validateArguments(call.arguments());
                // The original MCP SDK invokes tools with params.arguments or {}; field presence remains unchanged.
                ToolCall decoded = call.arguments().presence() == Presence.VALUE ? call
                        : new ToolCall(call.name(), new Arguments(Presence.VALUE, Optional.of(call.arguments().objectOrEmpty())),
                                call.meta(), call.cancellation());
                request = requestType.cast(Objects.requireNonNull(decoder.decode(decoded), "typed request required"));
            } catch (PublicServiceFailure originalService) {
                // A decoded semantic business error retains its original type, message and evidence.
                // Invalid JSON shape still uses the invalid-arguments branch below.
                throw new ToolFailure(originalService.getMessage(),originalService);
            } catch (IllegalArgumentException invalid) {
                throw new ToolFailure("invalid tool arguments; no application invocation occurred", invalid);
            }
            if (call.cancellation().requested())
                throw new ToolFailure("request cancelled before application dispatch; no application invocation occurred");
            try {
                R response = responseType.cast(Objects.requireNonNull(handler.invoke(request), "typed application result required"));
                CallResult result = Objects.requireNonNull(encoder.encode(call, response), "complete MCP result required");
                descriptor.validateResult(result);
                return result;
            } catch (McpAutoFailure actualDiagnostic) {
                if (!descriptor.name().equals("ck3_auto_turn")) throw actualDiagnostic;
                CallResult result = actualDiagnostic.result(); descriptor.validateResult(result); return result;
            } catch (PublicServiceFailure originalService) {
                // Its original typed service stages prove this error; preserve the standard MCP message.
                // The typed cause retains the Python error kind and exact candidate evidence for internal consumers.
                throw new ToolFailure(originalService.getMessage(),originalService);
            } catch (StatusCapabilityFailure originalStatus) {
                // Only the installed Status source classifies its actual received HELLO as missing support.
                // Preserve its original evidence and exact exception; no packet, read or action is retried.
                var originalService = new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                        originalStatus.getMessage(), Optional.of(originalStatus.originalHello()),
                        new PublicServiceFailure.Details(originalStatus, Optional.empty(), Optional.empty()));
                throw new ToolFailure(originalService.getMessage(), originalService);
            } catch (RootAubRuntimeFactory.PreSubmissionRevisionMismatch originalAub) {
                var originalService = new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                        originalAub.getMessage(), Optional.empty(), new PublicServiceFailure.Details(originalAub,
                        Optional.empty(), Optional.of(PublicServiceFailure.PreSubmissionDefaults.ORIGINAL)));
                throw new ToolFailure(originalService.getMessage(), originalService);
            } catch (ContactScopeFailure originalContact) {
                // Only the source's explicit proof-bearing kind assigns an original public class.
                throw switch (originalContact.kind()) {
                    case UNCLASSIFIED_NATIVE -> new ToolFailure(originalContact.getMessage(), originalContact);
                    case BRIDGE_UNAVAILABLE -> contactFailure(originalContact, PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE, Optional.empty());
                    case NATIVE_COMMAND_REJECTED -> contactFailure(originalContact, PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED, Optional.empty());
                    case PRE_SUBMISSION_REVISION_MISMATCH -> contactFailure(originalContact,
                            PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                            Optional.of(PublicServiceFailure.PreSubmissionDefaults.ORIGINAL));
                };
            } catch (FactionAlertReadService.QueryFailure originalFaction) {
                PublicServiceFailure.Kind kind = switch (originalFaction.kind()) {
                    case BRIDGE_UNAVAILABLE -> PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE;
                    case NATIVE_COMMAND_REJECTED -> PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED;
                };
                var originalService = new PublicServiceFailure(kind, originalFaction.getMessage(),
                        originalFaction.originalCandidate(), new PublicServiceFailure.Details(originalFaction,
                        Optional.empty(), Optional.empty()));
                throw new ToolFailure(originalService.getMessage(), originalService);
            } catch (PrisonerPublicFailure12004 originalPrisoner) {
                Optional<PublicServiceFailure.NativeAttributes> attributes = Optional.empty();
                if (originalPrisoner.publishesNativeAttributes()) {
                    NativeWire.Field field = originalPrisoner.nativeError();
                    RawJson nativeError = field.presence() == NativeWire.Presence.VALUE
                            ? new RawJson(field.token().orElseThrow().value())
                            : new RawJson("null".getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    attributes = Optional.of(new PublicServiceFailure.NativeAttributes(nativeError,
                            originalPrisoner.requestId().orElseThrow()));
                }
                // All original prisoner branches explicitly carry BridgeUnavailableError.
                // The exact original outcome/read/receipt/references remain on the same carrier.
                var originalService = new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                        originalPrisoner.getMessage(), Optional.empty(), new PublicServiceFailure.Details(
                        originalPrisoner, attributes, Optional.empty()));
                throw new ToolFailure(originalService.getMessage(), originalService);
            } catch (GuiReadFailure originalRead) {
                // The producer retains its actual Unavailable and DispatchOutcome. UNKNOWN has no
                // inferred timeout/refusal category, and the public boundary never retries the read.
                throw new ToolFailure(originalRead.getMessage(),originalRead);
            } catch (GuiActionFailure originalAction) {
                // The actual action producer supplies its canonical receipt and rejected native ACK.
                throw new ToolFailure(originalAction.getMessage(),originalAction);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new ToolFailure("application invocation interrupted; world outcome is unconfirmed; do not resend", interrupted);
            } catch (ToolFailure encodingFailure) {
                throw new ToolFailure("application was dispatched; result unavailable; world outcome unconfirmed; do not resend", encodingFailure);
            }
        }
    }
    private static ToolFailure contactFailure(ContactScopeFailure original, PublicServiceFailure.Kind kind,
            Optional<PublicServiceFailure.PreSubmissionDefaults> defaults) {
        var service = new PublicServiceFailure(kind, original.getMessage(), Optional.empty(),
                new PublicServiceFailure.Details(original, Optional.empty(), defaults));
        return new ToolFailure(service.getMessage(), service);
    }
    private interface BoundResource {
        ResourceDescriptor descriptor();
        ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure;
    }
    private record TypedResource<R>(ResourceDescriptor descriptor, Class<R> resultType, ResourceHandler<R> handler,
            ResourceEncoder<R> encoder, PublicRoutes.Target actualTarget) implements BoundResource {
        @Override public ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure {
            if (call.cancellation().requested()) throw new ToolFailure("resource request cancelled before application read");
            try {
                ResourceResult result = Objects.requireNonNull(encoder.encode(resultType.cast(Objects.requireNonNull(handler.read(call)))));
                for (var item : McpJson.parse(result.bytes()).get("contents"))
                    McpJson.require(descriptor.uri().equals(McpJson.text(item.get("uri"))), "resource result URI differs from bound route");
                return result;
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new ToolFailure("resource read interrupted", interrupted);
            }
        }
    }
    private final McpCoverage.Catalog catalog;
    private final LinkedHashMap<String,McpCoverage.Decision> decisions = new LinkedHashMap<>();
    private final LinkedHashMap<String,Bound> bindings = new LinkedHashMap<>();
    private final LinkedHashMap<String,BoundResource> resources = new LinkedHashMap<>();
    private boolean frozen;

    public PublicMcpBindings(McpCoverage.Catalog originalCatalog, List<McpCoverage.Decision> actualDecisions) {
        catalog = Objects.requireNonNull(originalCatalog);
        for (McpCoverage.Decision decision : List.copyOf(actualDecisions))
            McpJson.require(decisions.putIfAbsent(decision.name(), decision) == null, "duplicate original admission decision");
        McpJson.require(decisions.keySet().equals(catalog.declarations().stream().map(McpCoverage.Declaration::name)
                .collect(java.util.stream.Collectors.toSet())), "every original declaration requires one actual admission decision");
    }
    public synchronized <Q,R> void register(ToolDescriptor descriptor, TypedRoute<Q,R> route, Class<R> resultType,
            Decoder<Q> decoder, Encoder<R> encoder) {
        Objects.requireNonNull(encoder);
        registerWithCall(descriptor, route, resultType, decoder, (call, response) -> encoder.encode(response));
    }
    /** Presenters receive the original validated invocation; no mutable/thread-local request correlation. */
    public synchronized <Q,R> void registerWithCall(ToolDescriptor descriptor, TypedRoute<Q,R> route, Class<R> resultType,
            Decoder<Q> decoder, CallEncoder<R> encoder) {
        Objects.requireNonNull(route);
        McpJson.require(PublicMcpNativeAdapter.expectedServiceMethod(descriptor.name()) == route.method(),
                "original MCP descriptor and actual service method differ");
        var info = route.info();
        McpJson.require(info.status() == PublicRoutes.Status.IMPLEMENTED || info.status() == PublicRoutes.Status.DELEGATED,
                "only a concrete public method route can be admitted");
        add(descriptor, Kind.PUBLIC_SERVICE, route.requestType(), resultType, route::invoke, decoder, encoder,
                info.target().orElseThrow(), Optional.of(route.method().pythonName()));
    }
    /** Original driver and offline helpers outside the service enum still require concrete source-bound methods. */
    public synchronized <Q,R> void registerDirect(ToolDescriptor descriptor, Kind kind, Class<Q> requestType, Class<R> resultType,
            PublicRoutes.Handler<Q,R> actualMethod, Decoder<Q> decoder, Encoder<R> encoder, PublicRoutes.Target target) {
        McpJson.require(kind != Kind.PUBLIC_SERVICE, "service registration requires its actual TypedRoute");
        Objects.requireNonNull(encoder);
        add(descriptor, kind, requestType, resultType, actualMethod, decoder, (call, response) -> encoder.encode(response), target, Optional.empty());
    }
    private <Q,R> void add(ToolDescriptor descriptor, Kind kind, Class<Q> requestType, Class<R> resultType,
            PublicRoutes.Handler<Q,R> actualMethod, Decoder<Q> decoder, CallEncoder<R> encoder,
            PublicRoutes.Target target, Optional<String> publicMethod) {
        Objects.requireNonNull(descriptor); Objects.requireNonNull(kind); Objects.requireNonNull(requestType);
        Objects.requireNonNull(resultType); Objects.requireNonNull(actualMethod); Objects.requireNonNull(decoder);
        Objects.requireNonNull(encoder); Objects.requireNonNull(target);
        McpJson.require(!requestType.isPrimitive() && !resultType.isPrimitive(), "typed MCP request/result must be reference types");
        McpJson.require(!frozen, "MCP binding directory is frozen");
        McpCoverage.Decision decision = decisions.get(descriptor.name());
        McpJson.require(decision != null && decision.admission() == McpCoverage.Admission.ADMITTED,
                "tool is not source-admitted by this Root");
        var bound = new Typed<>(descriptor, requestType, resultType, actualMethod, decoder, encoder,
                new BindingInfo(descriptor.name(), kind, target, publicMethod));
        McpJson.require(bindings.putIfAbsent(descriptor.name(), bound) == null, "duplicate MCP tool binding");
    }
    public synchronized <R> void registerResource(ResourceDescriptor descriptor, Class<R> resultType,
            ResourceHandler<R> actualMethod, ResourceEncoder<R> encoder, PublicRoutes.Target actualTarget) {
        McpJson.require(!frozen, "MCP binding directory is frozen");
        var bound = new TypedResource<>(Objects.requireNonNull(descriptor), Objects.requireNonNull(resultType),
                Objects.requireNonNull(actualMethod), Objects.requireNonNull(encoder), Objects.requireNonNull(actualTarget));
        McpJson.require(resources.putIfAbsent(descriptor.uri(), bound) == null, "duplicate resource binding");
    }
    public synchronized McpCoverage.Report coverage() {
        boolean complete = decisions.values().stream().noneMatch(row -> row.admission() == McpCoverage.Admission.UNMIGRATED)
                && decisions.values().stream().filter(row -> row.admission() == McpCoverage.Admission.ADMITTED)
                    .allMatch(row -> bindings.containsKey(row.name()))
                && resources.keySet().equals(java.util.Set.of("ck3://capabilities", "ck3://state/current"));
        return new McpCoverage.Report(List.copyOf(decisions.values()), bindings.size(), resources.size(), complete);
    }
    public synchronized List<BindingInfo> actualBindings() {
        return bindings.values().stream().map(Bound::info).toList();
    }
    /** Production refuses migration gaps. Explicit software scope is not ordinary-runtime qualification. */
    public synchronized PublicMcpDirectory freeze() { return freeze(true); }
    public synchronized PublicMcpDirectory freezeSoftwareScope() { return freeze(false); }
    private PublicMcpDirectory freeze(boolean requireFullMigration) {
        McpJson.require(!frozen, "MCP directory already frozen");
        for (McpCoverage.Decision row : decisions.values()) if (row.admission() == McpCoverage.Admission.ADMITTED)
            McpJson.require(bindings.containsKey(row.name()), "admitted original tool has no actual Java binding: " + row.name());
        McpJson.require(!requireFullMigration || coverage().completeMigration(), "whole MCP migration and both resources required");
        frozen = true;
        List<ToolDescriptor> descriptors = bindings.values().stream().map(Bound::descriptor).toList();
        List<ResourceDescriptor> resourceDescriptors = resources.values().stream().map(BoundResource::descriptor).toList();
        Map<String,Bound> snapshot = Map.copyOf(bindings);
        Map<String,BoundResource> resourceSnapshot = Map.copyOf(resources);
        return new PublicMcpDirectory() {
            @Override public Scope scope() { return requireFullMigration ? Scope.COMPLETE_MIGRATION : Scope.SOFTWARE_ONLY; }
            @Override public List<ToolDescriptor> tools() { return descriptors; }
            @Override public List<ResourceDescriptor> resources() { return resourceDescriptors; }
            @Override public CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure {
                Bound bound = snapshot.get(call.name());
                if (bound == null) throw new ToolFailure("Unknown tool: " + call.name());
                return bound.invoke(call);
            }
            @Override public ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure {
                BoundResource bound = resourceSnapshot.get(call.uri());
                if (bound == null) throw new RpcFailure(-32602, "Unknown resource: " + call.uri(), Optional.empty());
                return bound.read(call);
            }
        };
    }
}
