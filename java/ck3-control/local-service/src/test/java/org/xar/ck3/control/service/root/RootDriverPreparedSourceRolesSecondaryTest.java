package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.Kind;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.PreparedProduct;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;

/**
 * The secondary six roles consume the one full-configuration fixture and actual pre-Core factory.
 * Missing reviewed fixture inputs fail in that producer; this test has no synthetic Inputs, Core,
 * Native plan, Finance, Family, skipped-positive or callback replacement. Mutated selectors below
 * are deliberately unqualified negative inputs derived from the actual retained twenty objects.
 */
final class RootDriverPreparedSourceRolesSecondaryTest {
    private enum Role {
        GRANT(Kind.GRANT, RootGrantTitlePublicProducts.class, RootGrantTitlePublicProducts.Prepared.class,
                RootDriverProductSourcesFactory.JavaProducts::grant),
        TITLE_CLAIMS(Kind.TITLE_CLAIMS, RootTitleClaimsRuntime.class, RootTitleClaimsRuntime.Prepared.class,
                RootDriverProductSourcesFactory.JavaProducts::titleClaims),
        CASH(Kind.CASH, RootCashObservationPublicProducts.class, RootCashObservationPublicProducts.Prepared.class,
                RootDriverProductSourcesFactory.JavaProducts::cash),
        SAVE_ARTIFACTS(Kind.SAVE_ARTIFACTS, RootSaveArtifactPublicProducts.class, RootSaveArtifactPublicProducts.Prepared.class,
                RootDriverProductSourcesFactory.JavaProducts::saveArtifacts),
        ENGINE_DIAGNOSTICS(Kind.ENGINE_DIAGNOSTICS, RootEngineDiagnosticsPublicProducts.class,
                RootEngineDiagnosticsPublicProducts.Prepared.class, RootDriverProductSourcesFactory.JavaProducts::engineDiagnostics),
        PLATFORM(Kind.PLATFORM, RootNormalExitRuntime.class, RootNormalExitRuntime.Prepared.class,
                RootDriverProductSourcesFactory.JavaProducts::platform);

        private final Kind kind;
        private final Class<?> implementation;
        private final Class<? extends PreparedProduct> preparedType;
        private final Function<RootDriverProductSourcesFactory.JavaProducts, ExactRef> selected;
        Role(Kind kind, Class<?> implementation, Class<? extends PreparedProduct> preparedType,
                Function<RootDriverProductSourcesFactory.JavaProducts, ExactRef> selected) {
            this.kind = kind; this.implementation = implementation; this.preparedType = preparedType; this.selected = selected;
        }
        String target() { return "local-service/src/main/java/" + implementation.getName().replace('.', '/') + ".java"; }
        ExactRef source(RootDriverProductSourcesFactory.Sources actual) { return selected.apply(actual.javaProducts()); }
    }

    @Test void actualFullConfigurationRetainsAllSixSecondarySourceRolesAndProductIdentities() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        var input = actual.factory().retainedInput();
        assertSame(actual.definitions().inputs(), input.inputs());
        assertSame(actual.factory(), actual.definitions().driverProductSources());
        assertSame(actual.prepared(), actual.factory().prepare());
        assertSame(actual.sources(), actual.factory().sources());
        assertEquals(6, Role.values().length);
        for (Role role : Role.values()) {
            PreparedProduct product = actual.prepared().products().ordered().get(role.kind.ordinal());
            assertEquals(role.kind, product.kind(), role.name());
            assertSame(role.preparedType, product.getClass(), role.name());
            assertSame(product, actual.prepared().prepared(role.kind, role.preparedType), role.name());
            assertEquals(role.implementation, product.source().implementation(), role.name());
            assertEquals(role.target(), product.source().targetRelative(), role.name());
            assertEquals(role.source(actual.sources()), product.source().selectedSource(), role.name());
            assertEquals(role.source(actual.sources()), input.selected().javaSourceAt(role.target(), role.implementation), role.name());
            var originals = input.inputs().sourceIndex().stream().filter(row -> row.targetRelative().equals(role.target())).toList();
            assertEquals(1, originals.size(), role.name());
            assertEquals(originals.getFirst().sourceRef(), product.source().selectedSource(), role.name());
        }
        assertEquals(actual.sources().javaProducts().titleClaims(), actual.sources().titleClaims().runtime());
        actual.factory().requireDefinitions(actual.definitions().catalogFactory().sources());
        actual.factory().requireCurrent();
    }

    @Test void eachMissingSecondaryRoleFailsTheActualFactoryBeforeAnySecondPreparation() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        for (Role role : Role.values()) {
            var rows = new ArrayList<>(actual.factory().retainedInput().inputs().sourceIndex());
            assertEquals(1, rows.stream().filter(row -> row.targetRelative().equals(role.target())).count());
            assertTrue(rows.removeIf(row -> row.targetRelative().equals(role.target())));
            rejectDerivedSelector(actual, rows, role.name() + ": missing exact target");
        }
    }

    @Test void eachForeignSecondaryImplementationCannotBorrowAnExistingQualifiedRole() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        for (Role role : Role.values()) {
            Role foreign = role == Role.GRANT ? Role.CASH : Role.GRANT;
            ExactRef wrong = foreign.source(actual.sources());
            assertNotEquals(role.source(actual.sources()), wrong);
            rejectDerivedSelector(actual, replace(actual, role, wrong), role.name() + ": foreign real implementation");
        }
    }

    @Test void eachChangedSecondarySourceDigestIsRejectedWithoutMutatingAnyOriginalFile() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        for (Role role : Role.values()) {
            ExactRef original = role.source(actual.sources());
            char first = original.sha256().charAt(0);
            String changed = (first == '0' ? "1" : "0") + original.sha256().substring(1);
            ExactRef drift = new ExactRef(original.path(), original.bytes(), changed);
            rejectDerivedSelector(actual, replace(actual, role, drift), role.name() + ": changed exact SHA claim");
        }
        // This is configuration/source-ref drift. Physical FileID replacement has its separate
        // main/primary owned full-configuration regression; no shared frozen Java file is edited here.
    }

    @Test void anEqualLookingUnqualifiedSelectorCannotAcquireTheActualInputsIdentity() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        rejectDerivedSelector(actual, actual.factory().retainedInput().inputs().sourceIndex(),
                "identical source values do not replace the actual immutable Inputs custody");
    }

    @Test void secondarySlotsRejectRealProductsFromAnotherKindAndKeepTheSamePrepared() throws IOException {
        var actual = RootDriverProductSourcesFactoryTest.actual();
        var products = actual.prepared().products();
        for (Role role : Role.values()) {
            assertThrows(IllegalArgumentException.class,
                    () -> actual.prepared().prepared(role.kind, RootDriverFactionPublicSupplier.Prepared.class), role.name());
            // All twelve objects are genuine retained products. Only the rejected data arrangement changes.
            var changed = new ArrayList<>(products.ordered());
            changed.set(role.kind.ordinal(), products.faction());
            assertThrows(IllegalArgumentException.class, () -> closedProducts(changed), role.name());
            assertSame(actual.prepared(), actual.factory().prepare());
            assertSame(products, actual.factory().prepare().products());
        }
        actual.factory().requireDefinitions(actual.definitions().catalogFactory().sources());
    }

    private static List<SelectedSource> replace(RootDriverProductSourcesFactoryTest.Actual actual,
            Role role, ExactRef rejected) {
        List<SelectedSource> rows = actual.factory().retainedInput().inputs().sourceIndex();
        assertEquals(1, rows.stream().filter(row -> row.targetRelative().equals(role.target())).count());
        return rows.stream().map(row -> row.targetRelative().equals(role.target())
                ? new SelectedSource(row.targetRelative(), rejected) : row).toList();
    }

    private static void rejectDerivedSelector(RootDriverProductSourcesFactoryTest.Actual actual,
            List<SelectedSource> altered, String reason) throws IOException {
        var original = actual.factory().retainedInput();
        var selected = new RootRuntimeSelectedSources(altered);
        // The production affinity guard refuses this source-only selector even in the equal-values
        // control. No fabricated RuntimeDefinitions.Inputs or permission enters this constructor.
        var candidate = new RootDriverProductSourcesFactory.Input(original.inputs(), selected,
                original.originals(), original.settings(), original.registration(), original.plan(),
                original.storage(), original.frontend(), original.finance(), original.construction(),
                original.family(), original.governance(), original.retry(), original.lifecycle(),
                original.ports(), original.nativeGovernance(), original.grantStore(), original.clock(),
                original.queryHistory(), original.operatorAuthority());
        assertSame(original.inputs(), candidate.inputs()); assertNotSame(original.selected(), candidate.selected());
        assertSame(original.originals(), candidate.originals()); assertSame(original.settings(), candidate.settings());
        assertSame(original.registration(), candidate.registration()); assertSame(original.plan(), candidate.plan());
        assertSame(original.storage(), candidate.storage()); assertSame(original.frontend(), candidate.frontend());
        assertSame(original.finance(), candidate.finance()); assertSame(original.construction(), candidate.construction());
        assertSame(original.family(), candidate.family()); assertSame(original.governance(), candidate.governance());
        assertSame(original.retry(), candidate.retry()); assertSame(original.lifecycle(), candidate.lifecycle());
        assertSame(original.ports(), candidate.ports()); assertSame(original.nativeGovernance(), candidate.nativeGovernance());
        assertSame(original.grantStore(), candidate.grantStore()); assertSame(original.clock(), candidate.clock());
        assertSame(original.queryHistory(), candidate.queryHistory());
        assertSame(original.operatorAuthority(), candidate.operatorAuthority());
        var rejected = new RootDriverProductSourcesFactory(candidate);
        assertThrows(IOException.class, rejected::prepare, reason);
        assertThrows(IOException.class, rejected::prepare, reason + ": failed attempt remains latched");
        assertThrows(IOException.class, rejected::sources, reason + ": failed attempt exposes no source product");
        assertSame(actual.prepared(), actual.factory().prepare(), reason + ": actual producer was not replaced");
        assertSame(actual.sources(), actual.factory().sources(), reason);
        actual.factory().requireCurrent();
    }

    private static RootDriverRegistryPublicProducts.Products closedProducts(List<PreparedProduct> actual) {
        assertEquals(12, actual.size());
        return new RootDriverRegistryPublicProducts.Products(actual.get(0), actual.get(1), actual.get(2),
                actual.get(3), actual.get(4), actual.get(5), actual.get(6), actual.get(7), actual.get(8),
                actual.get(9), actual.get(10), actual.get(11));
    }
}
