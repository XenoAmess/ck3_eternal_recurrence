package org.xar.ck3.control.service.mcp;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Installs actual typed methods only. Original declarations and missing methods never become stub handlers. */
public final class McpExecutableDirectory {
    public enum MissingReason { ORIGINAL_UNMIGRATED, NO_ORIGINAL_DESCRIPTOR, NO_ACTUAL_METHOD, NO_ACTUAL_RESOURCE_PROVIDER }
    public record Missing(String identity, MissingReason reason) {
        public Missing { Objects.requireNonNull(identity); Objects.requireNonNull(reason); }
    }
    public sealed interface Result permits Complete, Partial { McpCoverage.Report coverage(); }
    public record Complete(PublicMcpDirectory directory, McpCoverage.Report coverage) implements Result {
        public Complete { McpJson.require(directory.scope()==Scope.COMPLETE_MIGRATION && coverage.completeMigration(), "complete executable directory required"); }
    }
    public record Partial(PublicMcpDirectory softwareDirectory, McpCoverage.Report coverage, List<Missing> missing) implements Result {
        public Partial { missing=List.copyOf(missing); McpJson.require(softwareDirectory.scope()==Scope.SOFTWARE_ONLY && !missing.isEmpty(), "partial directory requires precise missing methods"); }
    }
    public record DirectBinding<Q,R>(String name, PublicMcpBindings.Kind kind, Class<Q> requestType, Class<R> resultType,
            PublicRoutes.Handler<Q,R> actual, PublicMcpBindings.Decoder<Q> decoder, PublicMcpBindings.Encoder<R> encoder,
            PublicRoutes.Target target) {
        public DirectBinding { McpJson.toolName(name); Objects.requireNonNull(kind); McpJson.require(kind!=PublicMcpBindings.Kind.PUBLIC_SERVICE,"actual service requires registry typed binding");
            Objects.requireNonNull(requestType);Objects.requireNonNull(resultType);Objects.requireNonNull(actual);Objects.requireNonNull(decoder);Objects.requireNonNull(encoder);Objects.requireNonNull(target); }
        private void register(PublicMcpBindings destination,ToolDescriptor descriptor) {
            destination.registerDirect(descriptor,kind,requestType,resultType,actual,decoder,encoder,target);
        }
    }
    private McpExecutableDirectory() { }

    public static Result assemble(McpCoverage.Catalog original,List<McpCoverage.Decision> actualAdmission,
            List<ToolDescriptor> actualOriginalDescriptors,List<ResourceDescriptor> originalResources,
            PublicBindings actualFrozenServiceRegistry,List<DirectBinding<?,?>> actualDirectMethods) {
        Objects.requireNonNull(actualFrozenServiceRegistry); McpJson.require(actualFrozenServiceRegistry.frozen(),"actual service registry must freeze before MCP composition");
        Map<String,ToolDescriptor> descriptors=new LinkedHashMap<>();
        for(ToolDescriptor descriptor:List.copyOf(actualOriginalDescriptors)) McpJson.require(descriptors.putIfAbsent(descriptor.name(),descriptor)==null,"duplicate original tool descriptor");
        Map<String,DirectBinding<?,?>> direct=new LinkedHashMap<>();
        for(DirectBinding<?,?> binding:List.copyOf(actualDirectMethods)) McpJson.require(direct.putIfAbsent(binding.name(),binding)==null,"duplicate actual direct method");
        var names=original.declarations().stream().map(McpCoverage.Declaration::name).collect(java.util.stream.Collectors.toSet());
        McpJson.require(names.containsAll(descriptors.keySet()) && names.containsAll(direct.keySet()),"descriptor/direct method outside exact original MCP identity catalog");
        List<McpCoverage.Decision> decisions=new ArrayList<>(); List<Missing> missing=new ArrayList<>();
        Map<String,PublicBindings.TypedBinding<?,?>> services=new LinkedHashMap<>();
        for(McpCoverage.Decision decision:List.copyOf(actualAdmission)) {
            MissingReason reason=null;
            if(decision.admission()==McpCoverage.Admission.UNMIGRATED) reason=MissingReason.ORIGINAL_UNMIGRATED;
            if(decision.admission()==McpCoverage.Admission.ADMITTED) {
                if(!descriptors.containsKey(decision.name())) reason=MissingReason.NO_ORIGINAL_DESCRIPTOR;
                else {
                    PublicBindings.TypedBinding<?,?> service=findService(actualFrozenServiceRegistry,decision.name());
                    McpJson.require(service==null || !direct.containsKey(decision.name()),"same original identity claims service and direct methods");
                    if(service!=null) services.put(decision.name(),service);
                    else if(!direct.containsKey(decision.name())) reason=MissingReason.NO_ACTUAL_METHOD;
                }
            }
            if(reason!=null) { missing.add(new Missing(decision.name(),reason)); decisions.add(new McpCoverage.Decision(decision.name(),McpCoverage.Admission.UNMIGRATED,decision.actualAdmissionProducer(),decision.conditionAndScope())); }
            else decisions.add(decision);
        }
        PublicMcpBindings destination=new PublicMcpBindings(original,decisions);
        for(McpCoverage.Decision decision:decisions) if(decision.admission()==McpCoverage.Admission.ADMITTED) {
            var service=services.get(decision.name());
            if(service!=null) registerService(destination,descriptors.get(decision.name()),service);
            else direct.get(decision.name()).register(destination,descriptors.get(decision.name()));
        }
        Map<String,ResourceDescriptor> resources=new LinkedHashMap<>();
        for(ResourceDescriptor descriptor:List.copyOf(originalResources)) McpJson.require(resources.putIfAbsent(descriptor.uri(),descriptor)==null,"duplicate original resource descriptor");
        resource(destination,actualFrozenServiceRegistry,resources,"ck3://capabilities",PublicMethod.CAPABILITIES,missing);
        resource(destination,actualFrozenServiceRegistry,resources,"ck3://state/current",PublicMethod.SNAPSHOT,missing);
        McpCoverage.Report report=destination.coverage();
        if(missing.isEmpty()) return new Complete(destination.freeze(),report);
        return new Partial(destination.freezeSoftwareScope(),report,missing);
    }
    private static PublicBindings.TypedBinding<?,?> findService(PublicBindings actual,String name) {
        final PublicMethod expected;
        try { expected=PublicMcpNativeAdapter.expectedServiceMethod(name); }
        catch(IllegalArgumentException notService) { return null; }
        return actual.lookup(expected).map(value -> (PublicBindings.TypedBinding<?,?>)value).orElse(null);
    }
    private static <Q,R> void registerService(PublicMcpBindings destination,ToolDescriptor descriptor,PublicBindings.TypedBinding<Q,R> actual) {
        PublicMcpNativeAdapter.register(destination,descriptor,actual);
    }
    private static void resource(PublicMcpBindings destination,PublicBindings actual,Map<String,ResourceDescriptor> descriptors,
            String uri,PublicMethod method,List<Missing> missing) {
        var binding=actual.lookup(method);
        if(!descriptors.containsKey(uri) || binding.isEmpty()) { missing.add(new Missing(uri,MissingReason.NO_ACTUAL_RESOURCE_PROVIDER)); return; }
        bindResource(destination,descriptors.get(uri),(PublicBindings.TypedBinding<?,?>)binding.orElseThrow());
    }
    private static <Q,R> void bindResource(PublicMcpBindings destination,ResourceDescriptor descriptor,PublicBindings.TypedBinding<Q,R> exactToolProvider) {
        // This exact same frozen object is also used by the tool adapter. It mints no Session or Native request of its own.
        destination.registerResource(descriptor,RawJson.class,call -> exactToolProvider.encode(exactToolProvider.invokeTyped(exactToolProvider.decode(new PublicBindings.Missing()))),
                value -> ResourceResult.fromBusinessJson(descriptor.uri(),value),exactToolProvider.info().target().orElseThrow());
    }
}
