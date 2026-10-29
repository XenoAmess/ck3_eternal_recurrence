package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryService;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;

/** One concrete Driver group, retaining the twelve independently owned original-business products. */
public final class RootDriverRegistryPublicProducts {
    private RootDriverRegistryPublicProducts() { }
    public enum Kind { GOVERNANCE, FACTION, HEIR, LIFECYCLE, TRANSPORT, FAMILY, GRANT, TITLE_CLAIMS,
        CASH, SAVE_ARTIFACTS, ENGINE_DIAGNOSTICS, PLATFORM }

    /** Exact source custody is checked before this product contributes handlers; it is not Native authority. */
    public record ProductSource(Class<?> implementation, String targetRelative, ExactRef selectedSource) {
        public ProductSource { Objects.requireNonNull(implementation); StrictJson.text(targetRelative); Objects.requireNonNull(selectedSource); }
        public void requireCurrent(RootPublicHandlerProductsFactory.Context context) throws IOException {
            // Compiled implementation references are descriptive metadata.
        }
    }
    /** A real per-Game product must retain its actual installation and guard the identical runtime context. */
    public interface Product {
        RootDomainInstallation installation();
        void requireContext(RootRuntimeContext identical) throws IOException;
    }
    /** Finite source-bound integration protocol; each owner implements its real producer, never a raw dispatcher. */
    public interface PreparedProduct {
        Kind kind();
        ProductSource source();
        List<DomainBodies.Registration> domainRegistrations();
        Collection<NativePrivateActionPermission> privatePermissions();
        void bindCore(RootApplicationAssembly.Core identical) throws IOException;
        Product install(RootRuntimeContext identical) throws IOException;
        RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context, PublicBindings registry) throws IOException;
    }
    /** Closed fields prevent an unbounded service map or missing-family fallback. */
    public record Products(PreparedProduct governance, PreparedProduct faction, PreparedProduct heir,
            PreparedProduct lifecycle, PreparedProduct transport, PreparedProduct family, PreparedProduct grant,
            PreparedProduct titleClaims, PreparedProduct cash, PreparedProduct saveArtifacts,
            PreparedProduct engineDiagnostics, PreparedProduct platform) {
        public Products {
            var all = List.of(governance, faction, heir, lifecycle, transport, family, grant, titleClaims,
                    cash, saveArtifacts, engineDiagnostics, platform);
            var kinds = Kind.values();
            for (int index = 0; index < kinds.length; index++) {
                var product = Objects.requireNonNull(all.get(index));
                StrictJson.require(product.kind() == kinds[index], "Driver prepared product occupies another closed family slot");
                Objects.requireNonNull(product.source());
            }
        }
        public List<PreparedProduct> ordered() { return List.of(governance, faction, heir, lifecycle, transport, family,
                grant, titleClaims, cash, saveArtifacts, engineDiagnostics, platform); }
    }

    public static final class Prepared {
        private final DriverRegistryService.Definitions cached;
        private final Products products;
        private final VanillaEventCatalog eventCatalog;
        private final List<DomainBodies.Registration> registrations;
        private final IdentityHashMap<RootRuntimeContext, Attempt> attempts = new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private boolean bound;
        public Prepared(DriverRegistryService.Definitions cached, Products products, VanillaEventCatalog eventCatalog) {
            this.cached = Objects.requireNonNull(cached); this.products = Objects.requireNonNull(products);
            this.eventCatalog = Objects.requireNonNull(eventCatalog);
            var unique = new LinkedHashMap<DomainBodies.Slot, DomainBodies.Registration>();
            for (var product : products.ordered()) for (var registration : product.domainRegistrations()) {
                var old = unique.putIfAbsent(registration.slot(), registration);
                StrictJson.require(old == null || old == registration, "Driver children claim different registrations for one actual writer slot");
            }
            registrations = List.copyOf(unique.values());
        }
        public Products products() { return products; }
        /** Returns the original pre-Core definition so actual source factories can verify installed contract identity. */
        public DriverRegistryService.Definitions cachedDefinitions() { return cached; }
        public VanillaEventCatalog eventCatalog() { return eventCatalog; }
        public List<DomainBodies.Registration> domainRegistrations() { return registrations; }
        public List<NativePrivateActionPermission> privatePermissions() {
            var result = new ArrayList<NativePrivateActionPermission>();
            for (var product : products.ordered()) for (var permission : product.privatePermissions()) result.add(Objects.requireNonNull(permission));
            return List.copyOf(result);
        }
        public synchronized void bindCore(RootApplicationAssembly.Core identical) throws IOException {
            Objects.requireNonNull(identical);
            if (core != null) { if (core == identical && bound) return; throw new IOException("Driver product Core binding differs or previously failed"); }
            core = identical;
            for (var product : products.ordered()) product.bindCore(identical);
            bound = true;
        }
        /** A validated narrow heterogeneous boundary, with a closed Kind and original same-source object. */
        public <T extends PreparedProduct> T prepared(Kind kind, Class<T> type) {
            Objects.requireNonNull(kind); Objects.requireNonNull(type);
            var actual = products.ordered().get(kind.ordinal());
            StrictJson.require(actual.kind() == kind && type == actual.getClass() && type.isInstance(actual), "Driver prepared product has another exact runtime type/kind"); return type.cast(actual);
        }
        public RootSaveArtifactPublicProducts.Prepared saveArtifacts() { return prepared(Kind.SAVE_ARTIFACTS, RootSaveArtifactPublicProducts.Prepared.class); }
        public RootEngineDiagnosticsPublicProducts.Prepared engineDiagnostics() { return prepared(Kind.ENGINE_DIAGNOSTICS, RootEngineDiagnosticsPublicProducts.Prepared.class); }
        public synchronized Installed install(RootRuntimeContext identical) throws IOException {
            Objects.requireNonNull(identical);
            if (!bound || core != identical.core()) throw new IOException("Driver products require their completely bound identical actual Core");
            var prior = attempts.get(identical);
            if (prior != null) { if (prior.installed != null) { prior.installed.requireContext(identical); return prior.installed; } throw new IOException("partial Driver installation is retained and not replayed", prior.failure); }
            if (attempts.size() >= 64) throw new IOException("Driver per-Game installation bound exhausted");
            var attempt = new Attempt(); attempts.put(identical, attempt);
            var children = new ArrayList<Product>();
            try {
                for (var product : products.ordered()) {
                    var child = Objects.requireNonNull(product.install(identical)); child.requireContext(identical);
                    Objects.requireNonNull(child.installation()); children.add(child);
                }
                var service = new DriverRegistryService(cached, request -> {
                    if (!(identical.actions() instanceof RootApplicationSession actual)) throw new IOException("cached query requires the actual bound Root application session");
                    if (!identical.readCatalog().containsIdentity(cached.cached())) throw new IOException("cached read is not the identical pre-Core Root contract");
                    return actual.readCurrent(cached.cached(), request.expectedRevision(),
                            (OpportunityJson.Obj) OpportunityJson.parse(new byte[]{'{', '}'}), identical.clock().instant().plusSeconds(10));
                });
                var own = new RootDomainInstallation("driver-registry-cached", List.of(),
                        List.of(new RootReadContractCatalog.InstalledRead(cached.cached(), cached.decoderSource())),
                        List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), Set.of(),
                        List.of(), List.of(), List.of(), List.of(), List.of());
                var installations = new ArrayList<RootDomainInstallation>(); installations.add(own);
                children.forEach(child -> installations.add(child.installation()));
                var merged = merge(installations);
                for (var registration : merged.domainRegistrations()) if (registrations.stream().noneMatch(old -> old == registration))
                    throw new IOException("Driver runtime introduced a different unregistered canonical writer domain");
                var installed = new Installed(identical, service, merged, products, children);
                attempt.installed = installed; return installed;
            } catch (IOException failure) { attempt.failure = closeProducts(children, failure); throw attempt.failure; }
            catch (RuntimeException failure) { attempt.failure = closeProducts(children, new IOException("actual Driver component installation failed", failure)); throw attempt.failure; }
        }
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context, PublicBindings registry) throws IOException {
            Objects.requireNonNull(context); Objects.requireNonNull(registry);
            if (context.definitions().additionalDomains().driverRegistry() != this)
                throw new IOException("Driver public products require the identical actual pre-Core Prepared");
            var implementation = context.source(RootDriverRegistryPublicProducts.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DriverRegistryContract.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DriverRegistryCodec.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DriverRegistryService.class);
            var direct = new ArrayList<McpExecutableDirectory.DirectBinding<?, ?>>();
            var diagnostics = new ArrayList<RootRuntimePublicCatalog.Diagnostic>();
            var gaps = new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
            direct.add(cachedBinding(implementation, request -> {
                try { return context.withCurrent(root -> {
                    var installed = context.installed(root).additionalDomains().driverRegistry(); installed.requireContext(context.installed(root).context());
                    return installed.service().queryCachedSuccession(request);
                }); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }));
            for (var child : products.ordered()) {
                child.source().requireCurrent(context);
                var contribution = child.products(context, registry);
                direct.addAll(contribution.direct()); diagnostics.addAll(contribution.diagnostics()); gaps.addAll(contribution.gaps());
            }
            var names = new java.util.HashSet<String>();
            var reserved = Set.of("ck3_query_pending_character_interaction_context_v1", "ck3_query_character_interaction_ordinary_v1", "ck3_initiate_character_interaction_ordinary_v1");
            for (var binding : direct) {
                if (reserved.contains(binding.name())) throw new IOException("Driver child duplicates the separately owned actual Known interaction method: " + binding.name());
                if (!names.add(binding.name())) throw new IOException("Driver child duplicates an exact original public name: " + binding.name());
            }
            return new RootPublicHandlerProductsFactory.Contribution(direct, diagnostics, gaps);
        }
    }
    private static final class Attempt { private Installed installed; private IOException failure; }

    public static final class Installed implements AutoCloseable {
        private final RootRuntimeContext context;
        private final DriverRegistryService service;
        private final RootDomainInstallation installation;
        private final Products prepared;
        private final List<Product> children;
        private boolean closed;
        private Installed(RootRuntimeContext context, DriverRegistryService service, RootDomainInstallation installation,
                Products prepared, List<Product> children) {
            this.context = context; this.service = service; this.installation = installation; this.prepared = prepared; this.children = List.copyOf(children);
        }
        public synchronized void requireContext(RootRuntimeContext identical) throws IOException {
            if (context != identical) throw new IOException("Driver products belong to another actual Game context");
            if (closed) throw new IOException("Driver products have been closed for their actual Game context");
        }
        /** Actual Root retirement calls this while retained writer/session resources can still record disposal.
         * Closing a resource never supplies a normal-exit observation or permission to kill the Game. */
        @Override public synchronized void close() throws IOException {
            if (closed) return;
            closed = true;
            IOException failure = closeProducts(children, null);
            if (failure != null) throw failure;
        }
        public DriverRegistryService service() { return service; }
        public RootDomainInstallation installation() { return installation; }
        public <T extends Product> T product(Kind kind, Class<T> type) throws IOException {
            requireContext(context);
            var actual = children.get(Objects.requireNonNull(kind).ordinal()); actual.requireContext(context);
            StrictJson.require(prepared.ordered().get(kind.ordinal()).kind() == kind && type == actual.getClass() && type.isInstance(actual), "Driver actual product has another exact runtime type/kind"); return type.cast(actual);
        }
        public RootTitleClaimsRuntime titleClaims() throws IOException { return product(Kind.TITLE_CLAIMS, RootTitleClaimsRuntime.class); }
    }
    /** Used for both failed installation and final retirement, retaining the first failure and all later disposal failures. */
    static IOException closeProducts(List<Product> children, IOException failure) {
        for (int index = children.size() - 1; index >= 0; index--) {
            var child = children.get(index);
            if (!(child instanceof AutoCloseable resource)) continue;
            try { resource.close(); }
            catch (Exception cause) {
                if (cause instanceof InterruptedException) Thread.currentThread().interrupt();
                IOException current = cause instanceof IOException io ? io : new IOException("actual Driver child resource disposal failed", cause);
                if (failure == null) failure = current; else if (failure != current) failure.addSuppressed(current);
            }
        }
        return failure;
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context, PublicBindings registry) throws IOException {
        return context.definitions().additionalDomains().driverRegistry().products(context, registry);
    }
    @FunctionalInterface interface CachedCurrent { DriverRegistryContract.CachedResponse read(DriverRegistryContract.CachedRequest request) throws InterruptedException; }
    static McpExecutableDirectory.DirectBinding<DriverRegistryContract.CachedRequest, DriverRegistryContract.CachedResponse> cachedBinding(ExactRef source, CachedCurrent current) {
        return new McpExecutableDirectory.DirectBinding<>(DriverRegistryContract.CACHED_NAME, PublicMcpBindings.Kind.DRIVER_DIRECT,
                DriverRegistryContract.CachedRequest.class, DriverRegistryContract.CachedResponse.class, current::read,
                call -> DriverRegistryCodec.cached(switch (call.arguments().presence()) {
                    case MISSING -> new PublicBindings.Missing();
                    case NULL -> new PublicBindings.Null();
                    case VALUE -> new PublicBindings.Value(call.arguments().original().orElseThrow());
                }), response -> CallResult.fromBusinessJson(DriverRegistryCodec.encode(response)),
                new PublicRoutes.Target(RootDriverRegistryPublicProducts.class.getName(), "queryCachedSuccession", source));
    }
    private static RootDomainInstallation merge(List<RootDomainInstallation> all) {
        return new RootDomainInstallation("driver-registry", all.stream().flatMap(x -> x.domainRegistrations().stream()).distinct().toList(),
                all.stream().flatMap(x -> x.reads().stream()).toList(), all.stream().flatMap(x -> x.readFamilies().stream()).toList(),
                all.stream().flatMap(x -> x.actions().stream()).toList(), all.stream().flatMap(x -> x.composites().stream()).toList(),
                all.stream().flatMap(x -> x.archived().stream()).toList(), all.stream().flatMap(x -> x.actionFamilies().stream()).toList(),
                all.stream().flatMap(x -> x.compositeFamilies().stream()).toList(), all.stream().flatMap(x -> x.frontendAdmissions().stream()).toList(),
                all.stream().flatMap(x -> x.pending().stream()).toList(), all.stream().flatMap(x -> x.requiredPending().stream()).collect(java.util.stream.Collectors.toUnmodifiableSet()),
                all.stream().flatMap(x -> x.policies().stream()).toList(), all.stream().flatMap(x -> x.completions().stream()).toList(),
                all.stream().flatMap(x -> x.fixedDomains().stream()).toList(), all.stream().flatMap(x -> x.familyDomains().stream()).toList(),
                all.stream().flatMap(x -> x.compositeDomains().stream()).toList());
    }
}
