package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.Collection;
import java.util.Set;
import java.util.IdentityHashMap;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.platform.NativeLaunchPlan;

import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;

/** Exact original pathless public method. Preparing profile custody grants no Game, SAVE or restore authority. */
public final class RootSaveArtifactPublicProducts {
    public static final String NAME = "ck3_inspect_save_artifacts_v1";
    private RootSaveArtifactPublicProducts() { }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final NativeLaunchPlan plan;
        private final Clock clock;
        private final RootSaveArtifactInspector inspector;
        private final RootDriverRegistryPublicProducts.ProductSource source;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext, Installed> installed = new IdentityHashMap<>();
        private Prepared(NativeLaunchPlan plan, Clock clock, TextRules originalTextRules, ExactRef actualImplementation) throws IOException {
            this.plan = Objects.requireNonNull(plan); this.clock = Objects.requireNonNull(clock);
            inspector = new RootSaveArtifactInspector(plan.profileDirectory(), originalTextRules);
            source = new RootDriverRegistryPublicProducts.ProductSource(RootSaveArtifactPublicProducts.class,
                    "local-service/src/main/java/org/xar/ck3/control/service/root/RootSaveArtifactPublicProducts.java", Objects.requireNonNull(actualImplementation));
            requireCurrent();
        }
        @Override public RootDriverRegistryPublicProducts.Kind kind() { return RootDriverRegistryPublicProducts.Kind.SAVE_ARTIFACTS; }
        @Override public RootDriverRegistryPublicProducts.ProductSource source() { return source; }
        @Override public List<DomainBodies.Registration> domainRegistrations() { return List.of(); }
        @Override public Collection<NativePrivateActionPermission> privatePermissions() { return List.of(); }
        @Override public synchronized void bindCore(RootApplicationAssembly.Core identical) throws IOException {
            Objects.requireNonNull(identical); requireCurrent();
            if (core != null && core != identical) throw new IOException("SAVE inspection already belongs to another actual Core");
            core = identical;
        }
        @Override public synchronized Installed install(RootRuntimeContext identical) throws IOException {
            requireCurrent(); Objects.requireNonNull(identical);
            if (core == null || identical.core() != core) throw new IOException("SAVE inspection requires its identical bound actual Core");
            var previous = installed.get(identical);
            if (previous != null) { previous.requireContext(identical); return previous; }
            if (installed.size() >= 64) throw new IOException("SAVE inspection per-Game installation bound exhausted");
            Installed result = new Installed(this, identical); result.requireContext(identical); installed.put(identical, result); return result;
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,
                PublicBindings registry) throws IOException {
            source.requireCurrent(context); return RootSaveArtifactPublicProducts.install(context, registry, this);
        }
        public void requireCurrent() throws IOException {
            inspector.requireCurrent();
        }
        public void requireSamePlan(NativeLaunchPlan identical) throws IOException {
            Objects.requireNonNull(identical);
            if (!plan.profileDirectory().equals(identical.profileDirectory())) {
                throw new IOException("SAVE inspection requires the actual configured profile directory");
            }
            requireCurrent();
        }
        RootSaveArtifactInspector.Response inspect(RootSaveArtifactCodec.Request request) {
            Objects.requireNonNull(request);
            try { requireCurrent(); var response = inspector.inspect(); requireCurrent(); return response; }
            catch (IOException unavailable) { throw new UncheckedIOException("configured original SAVE profile inspection unavailable", unavailable); }
        }
    }
    public static Prepared prepare(NativeLaunchPlan sameActualPlan, Clock clock, TextRules originalTextRules,
            ExactRef actualImplementation) throws IOException {
        return new Prepared(sameActualPlan, clock, Objects.requireNonNull(originalTextRules), actualImplementation);
    }
    public static final class Installed implements RootDriverRegistryPublicProducts.Product {
        private final Prepared prepared;
        private final RootRuntimeContext context;
        private final RootDomainInstallation installation;
        private Installed(Prepared prepared, RootRuntimeContext context) {
            this.prepared = prepared; this.context = context;
            // Filesystem inspection owns no native operation, reducer, action or clock policy.
            installation = new RootDomainInstallation("save-artifacts-read-only", List.of(), List.of(), List.of(), List.of(),
                    List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), Set.of(), List.of(), List.of(), List.of(), List.of(), List.of());
        }
        @Override public RootDomainInstallation installation() { return installation; }
        @Override public void requireContext(RootRuntimeContext identical) throws IOException {
            if (context != identical) throw new IOException("SAVE inspection product belongs to another actual runtime context");
            identical.game().verify();
            prepared.requireSamePlan(identical.game().launchPlan());
        }
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry) throws IOException {
        return context.definitions().additionalDomains().driverRegistry().saveArtifacts().products(context, registry);
    }
    /** The total supplier must pass its one actual pre-Core Prepared; no callback or caller-selected path is accepted. */
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry, Prepared actualPrepared) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(registry); Objects.requireNonNull(actualPrepared);
        if (context.definitions().additionalDomains().driverRegistry().saveArtifacts() != actualPrepared)
            throw new IOException("SAVE inspection requires the identical actual pre-Core product");
        actualPrepared.requireCurrent(); ExactRef source = context.source(RootSaveArtifactPublicProducts.class);
        context.source(RootSaveArtifactInspector.class); context.source(RootSaveArtifactCodec.class);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(binding(source, actualPrepared::inspect)), List.of(), List.of());
    }
    /** Actual business leaf is shared by the production Prepared and the isolated filesystem protocol regressions. */
    static McpExecutableDirectory.DirectBinding<RootSaveArtifactCodec.Request, RootSaveArtifactInspector.Response> binding(
            ExactRef actualSource, PublicRoutes.Handler<RootSaveArtifactCodec.Request, RootSaveArtifactInspector.Response> actual) {
        Objects.requireNonNull(actualSource); Objects.requireNonNull(actual);
        return new McpExecutableDirectory.DirectBinding<>(NAME, PublicMcpBindings.Kind.DRIVER_DIRECT,
                RootSaveArtifactCodec.Request.class, RootSaveArtifactInspector.Response.class, actual,
                call -> RootSaveArtifactCodec.decodeRequest(call.arguments()),
                response -> CallResult.fromBusinessJson(RootSaveArtifactCodec.encode(response)),
                new PublicRoutes.Target(RootSaveArtifactPublicProducts.class.getName(), "inspect_save_artifacts_v1", actualSource));
    }
}
