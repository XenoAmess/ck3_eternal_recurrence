package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;

/** Callable assertions over real Root-installed products and canonical actions. Never constructs their authority. */
public final class RootActionHistoryMaterialAssertions {
    private RootActionHistoryMaterialAssertions(){ }
    public static void actualReturnedOriginal(RootActionHistoryMaterialSourceFactory.Products products,
            RootRuntimeContext context,Session same,ActionReceipt actual,ExactRef originalResult,
            DriverActionHistoryCodec.Recording recording)throws java.io.IOException {
        var material=capture(products,context,same,actual);
        var legacy=assertInstanceOf(DriverActionHistoryCodec.Legacy.class,material);
        assertEquals(recording,legacy.recording());assertEquals(java.util.Optional.of(originalResult),legacy.result());assertTrue(legacy.error().isEmpty());
        byte[] original=context.archive().withSession(same).loadMaterial(originalResult).bytes();
        assertEquals(originalResult.bytes(),original.length);assertEquals(originalResult.sha256(),DriverJson.sha256(original));
        assertTrue(legacy.evidence().stream().anyMatch(e->e.kind()==DriverActionHistoryCodec.EvidenceKind.MATERIAL&&e.reference().equals(originalResult)));
    }
    public static void actualDirectWithoutLegacyRecorder(RootActionHistoryMaterialSourceFactory.Products products,
            RootRuntimeContext context,Session same,ActionReceipt actual,List<ExactRef> requiredOriginals)throws java.io.IOException {
        assertFalse(requiredOriginals.isEmpty(),"actual independent expected originals must be supplied by the real domain fixture");
        var material=assertInstanceOf(DriverActionHistoryCodec.CanonicalOnly.class,capture(products,context,same,actual));
        assertEquals(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,material.reason());
        assertTrue(material.evidence().stream().map(DriverActionHistoryCodec.Evidence::reference).toList().containsAll(requiredOriginals));
    }
    private static DriverActionHistoryCodec.OriginalMaterial capture(RootActionHistoryMaterialSourceFactory.Products products,
            RootRuntimeContext context,Session same,ActionReceipt actual)throws java.io.IOException {
        context.writer().requireSession(same);assertTrue(actual.settled());String head=same.head().digest();
        var before=context.adopted().authority().withFrozenFacts(same,lease->lease.state());
        var archive=context.archive().withSession(same);products.materials().requireOwner(context.adopted().authority(),context.core().journal(),context.archive());
        var actualMaterial=products.materials().capture(same,actual,archive);products.materials().requireOriginal(same,actual,actualMaterial,archive);
        assertEquals(head,same.head().digest(),"material capture must not change the canonical writer");
        var after=context.adopted().authority().withFrozenFacts(same,lease->lease.state());assertSame(before,after,"factory cannot publish or replace Driver facts");
        assertTrue(products.materials().sources().containsAll(actualMaterial.producers()));return actualMaterial;
    }
}
