package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Finite Driver LIFECYCLE child. Reuses the identical actual lifecycle/Native permission/writer. */
public final class RootDriverLifecycleRuntimeInstaller {
    private RootDriverLifecycleRuntimeInstaller(){ }
    public record Sources(ExactRef runtime,ExactRef publicSupplier,ExactRef publicCodec,
            ExactRef uiState,ExactRef uiCodec,ExactRef uiReducer,ExactRef pendingSource,
            ExactRef pendingProjection,ExactRef pendingPublisher,ExactRef pendingQualifier,
            ExactRef queryDefinition,ExactRef closeDefinition) {
        public Sources {for(ExactRef value:List.of(runtime,publicSupplier,publicCodec,uiState,uiCodec,uiReducer,
                pendingSource,pendingProjection,pendingPublisher,pendingQualifier,queryDefinition,closeDefinition))
            Objects.requireNonNull(value);}
        public List<ExactRef> all(){return List.of(runtime,publicSupplier,publicCodec,uiState,uiCodec,uiReducer,
                pendingSource,pendingProjection,pendingPublisher,pendingQualifier,queryDefinition,closeDefinition);}
    }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final RootDriverRegistryPublicProducts.ProductSource productSource;
        private final Sources sources;private final RootLifecycleRuntimeFactory.Prepared lifecycle;private final Clock clock;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private static final class Attempt {RootPendingUiRuntime installed;IOException failure;}
        public Prepared(RootDriverRegistryPublicProducts.ProductSource actualSource,Sources actualSources,
                RootLifecycleRuntimeFactory.Prepared sameLifecycle,Clock sameClock) {
            productSource=Objects.requireNonNull(actualSource);sources=Objects.requireNonNull(actualSources);
            lifecycle=Objects.requireNonNull(sameLifecycle);clock=Objects.requireNonNull(sameClock);
            // Source audit gates removed
        }
        @Override public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.LIFECYCLE;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source(){return productSource;}
        public Sources sources(){return sources;}
        public Clock clock(){return clock;}
        public RootLifecycleRuntimeFactory.Prepared lifecycle(){return lifecycle;}
        public List<ExactRef> requiredSources(){var values=new java.util.LinkedHashSet<ExactRef>();values.add(productSource.selectedSource());values.addAll(sources.all());return List.copyOf(values);}
        /** The existing sole natural registration and Close permission are contributed by the actual lifecycle factory. */
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public Collection<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core identical)throws IOException {
            Objects.requireNonNull(identical);lifecycle.requireBoundCore(identical);
            if(core!=null){if(core==identical)return;throw new IOException("UI Driver product crossed its original Core");}core=identical;
        }
        @Override public synchronized RootPendingUiRuntime install(RootRuntimeContext identical)throws IOException {
            Objects.requireNonNull(identical);if(core==null||identical.core()!=core||identical.clock()!=clock)throw new IOException("UI Driver product lost its same Core/clock");
            var previous=attempts.get(identical);if(previous!=null){if(previous.installed!=null)return previous.installed;throw new IOException("partial UI installation is retained without replay",previous.failure);}
            StrictJson.require(attempts.size()<64,"finite per-Game UI product bound exceeded");var attempt=new Attempt();attempts.put(identical,attempt);
            try{var actual=lifecycle.installedFor(identical);actual.requireContext(identical);var result=RootPendingUiRuntime.create(this,identical,actual);
                result.requireContext(identical);attempt.installed=result;return result;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual PendingUI installation failed",failure);throw attempt.failure;}
        }
        public synchronized RootPendingUiRuntime installedFor(RootRuntimeContext identical)throws IOException {
            var actual=attempts.get(identical);if(actual==null||actual.installed==null)throw new IOException("actual PendingUI product is not installed");
            actual.installed.requireContext(identical);return actual.installed;
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            source().requireCurrent(context);return RootDriverLifecyclePublicSupplier.install(context,registry);
        }
    }
}
