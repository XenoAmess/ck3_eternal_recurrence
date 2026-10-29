package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.StrictJson;

/** Requires actual reviewed prelaunch inputs. Missing inputs fail; no synthetic Core/plan is substituted. */
public final class RootDriverProductSourcesFactoryTest {
    private static final String PROPERTY="xar.root.runtime.definitions";
    private static Actual retained;
    private static IOException failure;
    private static boolean entered;

    public record Actual(RootRuntimeDefinitions definitions, RootDriverProductSourcesFactory factory,
            RootDriverRegistryPublicProducts.Prepared prepared, RootDriverProductSourcesFactory.Sources sources) {
        public Actual {
            Objects.requireNonNull(definitions);Objects.requireNonNull(factory);
            Objects.requireNonNull(prepared);Objects.requireNonNull(sources);
        }
    }
    /** The two independently owned role matrices consume this same real producer and exact inputs. */
    public static synchronized Actual actual() throws IOException {
        if(retained!=null){retained.factory().requireCurrent();return retained;}
        if(entered)throw new IOException("actual Driver source fixture previously failed",failure);
        entered=true;
        try {
            String path=required(PROPERTY+".path"),bytes=required(PROPERTY+".bytes"),sha=required(PROPERTY+".sha256");
            if(!Path.of(path).isAbsolute()||!bytes.matches("[1-9][0-9]{0,8}")||!sha.matches("[0-9a-f]{64}"))
                throw new IOException("actual finite Driver full-configuration exact ref required");
            long length=Long.parseLong(bytes);
            if(length>RootRuntimeDefinitions.MAXIMUM_BYTES)throw new IOException("Driver full configuration exceeds its real SDK lane");
            var ref=new ControlBuild.FileRef(path,length,sha);
            var definitions=RootRuntimeDefinitions.readExact(ref,Clock.systemUTC());
            var factory=definitions.driverProductSources();
            var prepared=factory.prepare();
            factory.requireDefinitions(definitions.catalogFactory().sources());
            retained=new Actual(definitions,factory,prepared,factory.sources());return retained;
        }catch(IOException invalid){failure=invalid;throw invalid;}
        catch(RuntimeException invalid){failure=new IOException("invalid actual Driver fixture",invalid);throw failure;}
    }

    @Test void originalFullConfigurationProducesAllTwelveIdenticalPreparedProducts() throws IOException {
        var actual=actual();var definitions=actual.definitions().catalogFactory().sources();
        assertSame(actual.prepared(),definitions.additionalDomains().driverRegistry());
        assertSame(actual.prepared(),actual.factory().prepare());
        assertSame(actual.sources(),actual.factory().sources());
        var products=actual.prepared().products().ordered();
        assertEquals(List.of(RootDriverRegistryPublicProducts.Kind.values()),products.stream().map(
                RootDriverRegistryPublicProducts.PreparedProduct::kind).toList());
        var input=actual.factory().retainedInput();
        assertSame(input.finance(),definitions.finance());assertSame(input.construction(),definitions.construction());
        assertSame(input.nativeGovernance(),definitions.nativeGovernance());assertSame(input.frontend(),definitions.frontend());
        assertSame(input.governance(),definitions.governance());assertSame(input.retry(),definitions.retryRuntime());
        var faction=actual.prepared().prepared(RootDriverRegistryPublicProducts.Kind.FACTION,
                RootDriverFactionPublicSupplier.Prepared.class);
        assertSame(input.finance(),faction.sources().finance());
        assertTrue(faction.domainRegistrations().isEmpty(),"the original Finance owns the Gift domain registrations");
        assertTrue(faction.privatePermissions().isEmpty(),"the direct wrapper adds no Native permission");
        assertEquals(actual.sources().cachedNative(),actual.prepared().cachedDefinitions().cached().sourceRef());
        for(var product:products) {
            var source=product.source();
            assertEquals(source.selectedSource(),input.selected().javaSourceAt(source.targetRelative(),source.implementation()));
        }
        actual.factory().requireDefinitions(definitions);
    }

    @Test void actualSourceDataRoundTripsThroughTheStrictSingleFieldContract() throws IOException {
        var sources=actual().sources();
        byte[] wire=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(sources),1<<20);
        var restored=ControlBuild.strictMapper().readValue(wire,RootDriverProductSourcesFactory.Sources.class);
        assertEquals(sources,restored);
        var unknown=StrictJson.parse(wire,1<<20).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)unknown).put("fallback_sources",true);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(
                StrictJson.canonical(unknown,1<<20),RootDriverProductSourcesFactory.Sources.class));
        var wrong=StrictJson.parse(wire,1<<20).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)wrong.path("java_products").path("faction")).put("bytes",true);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(
                StrictJson.canonical(wrong,1<<20),RootDriverProductSourcesFactory.Sources.class));
    }

    /** The existing whole Root fixture invokes this only after its genuine catalog installation. */
    public static void assertActualInstalled(RootRuntimeDefinitions definitions,RootInstalledCatalog catalog) throws IOException {
        Objects.requireNonNull(definitions);Objects.requireNonNull(catalog);
        var registry=definitions.catalogFactory().sources().additionalDomains().driverRegistry();
        var context=catalog.context();var installed=catalog.additionalDomains().driverRegistry();
        installed.requireContext(context);assertSame(installed,registry.install(context));
        assertTrue(context.readCatalog().containsIdentity(registry.cachedDefinitions().cached()));
        var faction=installed.product(RootDriverRegistryPublicProducts.Kind.FACTION,
                RootDriverFactionPublicSupplier.Installed.class);
        faction.requireContext(context);
        assertSame(context.finance(),faction.finance());
        assertSame(context.finance().publicGifts(),faction.publicGifts());
        for(var prepared:registry.products().ordered()) {
            var child=prepared.install(context);child.requireContext(context);
            assertSame(child,prepared.install(context));
            var own=child.installation();var merged=installed.installation();
            for(var read:own.reads())assertTrue(merged.reads().stream().anyMatch(actual->actual==read));
            for(var family:own.readFamilies())assertTrue(merged.readFamilies().stream().anyMatch(actual->actual==family));
            for(var action:own.actions())assertTrue(merged.actions().stream().anyMatch(actual->actual==action));
            for(var replay:own.archived())assertTrue(merged.archived().stream().anyMatch(actual->actual==replay));
        }
    }

    /** Requires two independently genuine Core owners supplied by the whole Root fixture. */
    public static void assertForeignCoreRejected(RootRuntimeDefinitions definitions,RootInstalledCatalog original,
            RootInstalledCatalog foreign) throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(foreign);
        assertNotSame(original.context().core(),foreign.context().core());
        var registry=definitions.catalogFactory().sources().additionalDomains().driverRegistry();
        assertSame(original.additionalDomains().driverRegistry(),registry.install(original.context()));
        assertThrows(IOException.class,()->registry.bindCore(foreign.context().core()));
        assertThrows(IOException.class,()->registry.install(foreign.context()));
    }

    private static String required(String property) throws IOException {
        String value=System.getProperty(property);
        if(value==null||value.isBlank())throw new IOException("required real Driver source fixture property missing: "+property);
        return value;
    }
}
