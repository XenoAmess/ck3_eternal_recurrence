package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import static org.junit.jupiter.api.Assertions.*;

/** Pure fresh-review role codec/loader; no actual complete review, writer or Game is constructed. */
final class RootFamilyFreshReviewMaterialTest {
    private static final int MAX=16*1024*1024;
    private static ExactRef ref(RawJson raw) {return new ExactRef("unit-fresh-review.json",raw.bytes().length,ActionCodec.sha256(raw.bytes()));}
    private static ActionPorts.OutcomeArchive archive(RawJson material,boolean wrongRef,AtomicInteger loads) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
            case "loadFullMaterial"->{loads.incrementAndGet();assertEquals(ref(material),args[0]);yield material;}
            case "loadMaterial"->throw new AssertionError("full fresh-review cannot use protocol material loader");
            case "materialReferenceOf"->wrongRef?new ExactRef("wrong-original.json",material.bytes().length,"f".repeat(64)):ref((RawJson)args[0]);
            default->throw new AssertionError("unexpected archive method: "+method.getName());
        });
    }
    private static JsonNode load(RawJson material) {
        return RootFamilyMarriageFreshPreparation.loadReviewMaterial(archive(material,false,new AtomicInteger()),ref(material));
    }
    @Test void smallSortedCanonicalBytesAndOriginalIdentityRemainCompatible() {
        var original=StrictJson.object();original.put("z",true);var inner=original.putObject("a");inner.put("z",7);inner.putNull("absent_value");inner.put("a","鐞夌劙\n");
        var encoded=RootFamilyMarriageFreshPreparation.encodeReviewMaterial(original);
        assertArrayEquals(StrictJson.canonical(original),encoded.bytes());
        var loads=new AtomicInteger();var decoded=RootFamilyMarriageFreshPreparation.loadReviewMaterial(archive(encoded,false,loads),ref(encoded));
        assertEquals(DriverJson.fromNode(original),DriverJson.fromNode(decoded));assertEquals(1,loads.get());
        assertArrayEquals(encoded.bytes(),RootFamilyMarriageFreshPreparation.encodeReviewMaterial(decoded).bytes());
    }
    @Test void manifestLargerThanReceiptBudgetRoundTripsUnderItsOwnFiniteRole() {
        var original=StrictJson.object().put("schema",RootFamilyMarriageFreshPreparation.SCHEMA);
        original.putObject("prepared_plan").put("full_observed_material","x".repeat(1_100_000));
        var encoded=RootFamilyMarriageFreshPreparation.encodeReviewMaterial(original);
        assertTrue(encoded.bytes().length>StrictJson.EXPLICIT_MAX_BYTES);assertTrue(encoded.bytes().length<MAX);
        assertEquals(original,load(encoded));
        assertThrows(IllegalArgumentException.class,()->StrictJson.canonical(original,MAX));
        assertThrows(IllegalArgumentException.class,()->StrictJson.canonical(original,StrictJson.EXPLICIT_MAX_BYTES));
        assertArrayEquals(encoded.bytes(),RootFamilyMarriageFreshPreparation.encodeReviewMaterial(load(encoded)).bytes());
    }
    @Test void opaqueNumberTokensMissingNullAndArraysKeepTheirExactTypedForms() {
        String wide="9".repeat(5000);
        String wire="{\"z\":[null,true,1,\"x\"],\"wide\":"+wide+",\"negative_zero\":-0.0,\"exponent\":1e999999,\"nullable\":null}";
        var original=FullJsonTree.parse(wire.getBytes(StandardCharsets.UTF_8),MAX);
        var encoded=RootFamilyMarriageFreshPreparation.encodeReviewMaterial(original);var decoded=load(encoded);
        assertEquals(new BigInteger(wide),decoded.get("wide").bigIntegerValue());
        assertEquals("-0.0",((DecimalTokenNode)decoded.get("negative_zero")).originalToken());
        assertEquals("1e999999",((DecimalTokenNode)decoded.get("exponent")).originalToken());
        assertFalse(decoded.has("missing"));assertTrue(decoded.get("nullable").isNull());assertEquals(original.get("z"),decoded.get("z"));
        assertArrayEquals(encoded.bytes(),RootFamilyMarriageFreshPreparation.encodeReviewMaterial(decoded).bytes());
        assertThrows(IllegalArgumentException.class,()->new RawJson(encoded.bytes()));
    }
    @Test void roleOverflowDuplicateOrMalformedJsonRemainRejected() {
        var large=StrictJson.object().put("too_large","x".repeat(MAX));
        assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageFreshPreparation.encodeReviewMaterial(large));
        var oversized=RawJson.fullMaterial(("{\"too_large\":\""+"x".repeat(MAX)+"\"}").getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->load(oversized));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8),MAX));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse(new byte[]{'{','"','x','"',':','"',(byte)0xc3,'"','}'},MAX));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse("{}{}".getBytes(StandardCharsets.UTF_8),MAX));
    }
    @Test void originalReferenceAndActualIoFailureAreNotHiddenByTheCodec() {
        var encoded=RootFamilyMarriageFreshPreparation.encodeReviewMaterial(StrictJson.object().put("actual",true));
        assertThrows(IllegalArgumentException.class,()->RootFamilyMarriageFreshPreparation.loadReviewMaterial(archive(encoded,true,new AtomicInteger()),ref(encoded)));
        var failing=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            throw new UncheckedIOException(new IOException("actual complete-material read failed"));
        });
        var error=assertThrows(UncheckedIOException.class,()->RootFamilyMarriageFreshPreparation.loadReviewMaterial(failing,ref(encoded)));
        assertEquals("actual complete-material read failed",error.getCause().getMessage());
    }
}
