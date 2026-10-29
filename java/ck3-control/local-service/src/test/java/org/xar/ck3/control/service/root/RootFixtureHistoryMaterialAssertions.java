package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.InitialDriverBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Called by the genuine fixture entry suite under its original borrowed writer. No Staged,
 * Known, Adopted, source authority, baseline or product is fabricated by these assertions. */
public final class RootFixtureHistoryMaterialAssertions {
    private RootFixtureHistoryMaterialAssertions(){ }

    public static RootInstalledCatalog.FixtureProducts assertActualStaged(
            RootActionHistoryMaterialSourceFactory.Prepared prepared,RootInstalledCatalog catalog,
            InitialDriverBootstrap.Staged stage,Session same)throws IOException {
        var context=catalog.context();context.writer().requireSession(same);
        stage.requireFixtureOwner(same,context.game(),context.source());
        stage.requireFixtureBootstrap(same,context.frontend().initialDriver());
        assertThrows(RuntimeException.class,context::adopted);
        assertFalse(same.head().state().toJson().has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD));
        var authority=stage.fixtureAuthority(same);var before=stage.fixtureDriver(same);String head=same.head().digest();
        var products=catalog.stageFixture(stage);catalog.requireFixtureProducts(stage,products);
        assertSame(authority,context.historyAuthority(same));
        assertSame(products,catalog.stageFixture(stage));
        var material=prepared.install(context,catalog);assertSame(material,prepared.install(context,catalog));
        material.materials().requireOwner(authority,context.core().journal(),context.archive());
        products.actionHistory().requireOwner(authority,context.core().journal(),context.archive());
        products.readHistory().requireOwner(authority,context.archive(),catalog.bindings().readCatalog());
        products.capabilities().requireOwner(authority,context.archive(),catalog.bindings());
        assertSame(products.readHistory(),context.readHistoryPublisher());
        assertSame(products.readHistory(),products.capabilities().readHistoryPublisher());
        assertFalse(products.actionHistory().hasPending(same));assertFalse(products.readHistory().hasPending(same));
        assertSame(before,stage.fixtureDriver(same));
        authority.withFrozenFacts(same,frozen->{assertSame(before,frozen.state());return null;});
        assertThrows(RuntimeException.class,context::adopted);
        assertFalse(same.head().state().toJson().has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD));
        assertEquals(head,same.head().digest());return products;
    }

    /** The caller must perform the real entry commit/adoption between the two assertion methods.
     * Adoption must reuse every actual staged object, without rebuilding an equal replacement. */
    public static void assertActualAdoptedReuses(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootInstalledCatalog catalog,InitialDriverBootstrap.Staged original,
            RootInstalledCatalog.FixtureProducts products,Session same)throws IOException {
        var context=catalog.context();context.writer().requireSession(same);
        assertTrue(original.fixtureRetired());var adopted=context.adopted();
        assertSame(adopted.authority(),context.historyAuthority(same));
        String head=same.head().digest();
        var before=adopted.authority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
        catalog.requireFixtureProducts(original,products);assertSame(products,catalog.stageFixture(original));
        assertSame(products.readHistory(),context.readHistoryPublisher());
        assertSame(products.readHistory(),catalog.readHistory());
        assertSame(products.readHistory(),products.capabilities().readHistoryPublisher());
        var material=prepared.install(context,catalog);assertSame(material,prepared.install(context,catalog));
        material.materials().requireOwner(adopted.authority(),context.core().journal(),context.archive());
        products.actionHistory().requireOwner(adopted.authority(),context.core().journal(),context.archive());
        products.capabilities().requireOwner(adopted.authority(),context.archive(),catalog.bindings());
        adopted.authority().withFrozenFacts(same,frozen->{assertSame(before,frozen.state());return null;});
        assertEquals(head,same.head().digest());
    }
}
