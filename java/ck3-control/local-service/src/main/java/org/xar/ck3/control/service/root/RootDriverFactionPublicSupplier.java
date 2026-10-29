package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicPort;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;

/** Original Gift5 public names over the same installed Finance product; no second writer or Family. */
public final class RootDriverFactionPublicSupplier {
    private RootDriverFactionPublicSupplier() { }
    /** The existing Finance installation owns every Gift domain, contract and service. */
    public record Sources(FinanceRuntimeInstaller.Prepared finance,
            RootDriverRegistryPublicProducts.ProductSource implementation) {
        public Sources {
            Objects.requireNonNull(finance); Objects.requireNonNull(implementation);
            // Source audit gate removed
        }
    }
    /** Direct public integration retains the same pre-Core Finance; it never installs Finance again. */
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final Sources sources;
        private RootApplicationAssembly.Core core;
        private final java.util.IdentityHashMap<RootRuntimeContext,Installed> installed=new java.util.IdentityHashMap<>();
        public Prepared(Sources sources) { this.sources=Objects.requireNonNull(sources); }
        Sources sources() { return sources; }
        @Override public RootDriverRegistryPublicProducts.Kind kind() { return RootDriverRegistryPublicProducts.Kind.FACTION; }
        @Override public RootDriverRegistryPublicProducts.ProductSource source() { return sources.implementation(); }
        @Override public List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> domainRegistrations() { return List.of(); }
        @Override public java.util.Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions() { return List.of(); }
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual) throws IOException {
            Objects.requireNonNull(actual);
            if(core!=null&&core!=actual)throw new IOException("Faction Gift direct product changed its actual Core");
            core=actual;
        }
        @Override public synchronized Installed install(RootRuntimeContext actual) throws IOException {
            Objects.requireNonNull(actual);
            if(core==null||actual.core()!=core)throw new IOException("Faction Gift direct product lacks its identical bound Core");
            var prior=installed.get(actual);
            if(prior!=null) { prior.requireContext(actual); return prior; }
            if(installed.size()>=64)throw new IOException("Faction Gift physical product bound exhausted");
            var product=new Installed(actual);
            product.requireContext(actual); installed.put(actual,product); return product;
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(
                RootPublicHandlerProductsFactory.Context context,PublicBindings registry) throws IOException {
            sources.implementation().requireCurrent(context);
            if(context.definitions().finance()!=sources.finance()
                    ||context.definitions().additionalDomains().driverRegistry().prepared(kind(),Prepared.class)!=this)
                throw new IOException("Faction Gift handlers lost the identical prepared Finance/Driver product");
            return RootDriverFactionPublicSupplier.install(context,registry);
        }
    }
    public static final class Installed implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;
        private final org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices finance;
        private final FactionGiftPublicPort publicGifts;
        private final RootDomainInstallation installation=new RootDomainInstallation("driver-faction-public-existing-finance",
                List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                java.util.Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        private Installed(RootRuntimeContext actual) {
            context=actual; finance=actual.finance(); publicGifts=finance.publicGifts();
        }
        org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices finance() { return finance; }
        FactionGiftPublicPort publicGifts() { return publicGifts; }
        @Override public RootDomainInstallation installation() { return installation; }
        @Override public void requireContext(RootRuntimeContext actual) throws IOException {
            if(context!=actual||actual.finance()!=finance||actual.finance().publicGifts()!=publicGifts)
                throw new IOException("Faction Gift direct product crossed its installed Finance/public service/context");
        }
    }
    public static RootPublicHandlerProductsFactory.Contribution install(
            RootPublicHandlerProductsFactory.Context context, PublicBindings registry) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(registry);
        StrictJson.require(!registry.frozen(), "public registry already frozen");
        ExactRef actualSource = context.source(RootDriverFactionPublicSupplier.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION, FactionGiftPublicContract.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION, FactionGiftPublicCodec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION, FactionGiftPublicPort.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION, FactionGiftPublicNumbers.class);
        return new RootPublicHandlerProductsFactory.Contribution(
                bindings(actualSource, request -> invoke(context, request)), List.of(), List.of());
    }
    public static RawJson invoke(RootPublicHandlerProductsFactory.Context context, Request request)
            throws InterruptedException {
        Objects.requireNonNull(context); Objects.requireNonNull(request);
        Instant deadline = context.clock().instant().plus(request instanceof Send
                ? context.actionTimeout() : context.observationTimeout());
        try {
            return context.withCurrent(root -> context.installed(root).context().finance().publicGifts().invoke(request, deadline));
        } catch (IOException unavailable) {
            throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    unavailable.getMessage(), Optional.empty());
        }
    }
    static List<McpExecutableDirectory.DirectBinding<?, ?>> bindings(ExactRef source,
            PublicRoutes.Handler<Request, RawJson> actualSameFinanceProducer) {
        Objects.requireNonNull(source); Objects.requireNonNull(actualSameFinanceProducer);
        return List.of(
                binding(Method.CANDIDATE, CandidateQuery.class, source, actualSameFinanceProducer),
                binding(Method.SEND, Send.class, source, actualSameFinanceProducer),
                binding(Method.RECEIPT, ReceiptQuery.class, source, actualSameFinanceProducer),
                binding(Method.COLD_RECOVERY, ColdRecoveryQuery.class, source, actualSameFinanceProducer),
                binding(Method.RESOLVED, ResolvedQuery.class, source, actualSameFinanceProducer));
    }
    private static <Q extends Request> McpExecutableDirectory.DirectBinding<Q, RawJson> binding(
            Method method, Class<Q> type, ExactRef source, PublicRoutes.Handler<Request, RawJson> actual) {
        return new McpExecutableDirectory.DirectBinding<>(method.originalName(), PublicMcpBindings.Kind.DRIVER_DIRECT,
                type, RawJson.class, actual::invoke,
                call -> type.cast(decode(method, call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,
                new PublicRoutes.Target(RootDriverFactionPublicSupplier.class.getName(), "invoke", source));
    }
    public static Request decode(Method method, PublicMcpDirectory.Arguments arguments) {
        Objects.requireNonNull(arguments);
        StrictJson.require(arguments.presence() == PublicMcpDirectory.Presence.VALUE,
                "original Gift public call requires named arguments");
        return FactionGiftPublicCodec.decode(method, arguments.original().orElseThrow());
    }
}
