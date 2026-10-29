package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Collection;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.*;

/** The Driver FAMILY product borrows the sole already-installed Family and owns the new treatment read. */
public final class RootDriverFamilyPublicProduct {
    private RootDriverFamilyPublicProduct() {}
    public static final class Prepared implements PreparedProduct {
        private final RootFamilyRuntimeFactory.Prepared family;
        private final ProductSource source;
        private RootApplicationAssembly.Core core;
        public Prepared(RootFamilyRuntimeFactory.Prepared sameActualFamily,ProductSource actualSource) {
            family=Objects.requireNonNull(sameActualFamily);source=Objects.requireNonNull(actualSource);
            // Source audit gate removed
        }
        @Override public Kind kind(){return Kind.FAMILY;}
        @Override public ProductSource source(){return source;}
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public Collection<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core identical)throws IOException {
            Objects.requireNonNull(identical);if(core!=null&&core!=identical)throw new IOException("Family Driver product crossed Core");
            core=identical;
        }
        @Override public synchronized Installed install(RootRuntimeContext identical)throws IOException {
            if(core==null||core!=identical.core())throw new IOException("Family Driver product lacks its identical actual Core");
            var actual=family.requireInstalled(identical);actual.nativeReads().requireContext(identical);actual.treatment().requireContext(identical);
            return new Installed(identical,actual);
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            // Source audit gate removed
            return RootFamilySupplementReadPublicProducts.install(context,registry);
        }
    }
    public static final class Installed implements Product {
        private final RootRuntimeContext context;
        private final RootFamilyRuntimeFactory.Installed family;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext context,RootFamilyRuntimeFactory.Installed family) {
            this.context=context;this.family=family;
            installation=new RootDomainInstallation("driver-family-supplement",List.of(),family.treatment().installedReads(),
                    List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public void requireContext(RootRuntimeContext identical)throws IOException {
            if(context!=identical)throw new IOException("Family Driver view belongs to another actual Root");
            family.nativeReads().requireContext(identical);family.treatment().requireContext(identical);
        }
        public RootFamilyRuntimeFactory.Installed family(){return family;}
    }
}

