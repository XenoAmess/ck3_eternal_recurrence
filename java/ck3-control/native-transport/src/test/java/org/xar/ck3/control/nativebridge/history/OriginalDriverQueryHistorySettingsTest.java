package org.xar.ck3.control.nativebridge.history;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.*;

/** Pure request producer/sole codec/effective-consumer regression; no private Bound or Game permit is minted. */
final class OriginalDriverQueryHistorySettingsTest {
    private static final Instant OBSERVED=Instant.parse("2026-10-24T08:00:00Z");
    private static final Instant REVIEW=Instant.parse("2026-10-24T10:30:00Z");
    private static final Set<String> REQUEST_FIELDS=Set.of("schema","machine_id","observed_at","review_at","configuration");
    private static Request input(Configuration value){return new Request("xenoamess-full-tower-eb9d2c1186",OBSERVED,REVIEW,value);}
    private static Path directory(){return Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize().resolve("explicit-army-history-state");}
    private static ExactRef ref(String name,long bytes,String hash){return new ExactRef(directory().resolve(name).toString(),bytes,hash);}
    private static ExactRef driver(){return ref("native_driver.py",LEGACY_DRIVER_BYTES,LEGACY_DRIVER_SHA256);}
    private static LegacyCaptured legacy(DirectoryFact directory,LimitFact limit,GuardFact guard){return new LegacyCaptured(driver(),directory,limit,guard);}
    private static ObjectNode requestNode(Request value){return StrictJson.object(StrictJson.parse(encodeRequest(value),MAX_BYTES),REQUEST_FIELDS);}
    private static ObjectNode configuration(ObjectNode root){return StrictJson.object(root.get("configuration"),Set.of("kind","state_directory","limit_bytes","admission"));}
    private static void rejected(ObjectNode value){assertThrows(RuntimeException.class,()->decodeRequest(StrictJson.canonical(value,MAX_BYTES)));}

    @Test void explicitJavaInputFlowsThroughDocumentAndSoleEffectiveConsumer()throws Exception{
        var request=input(new JavaConfigured(new Directory(directory()),Long.MAX_VALUE,Admission.ROOT_STORAGE));
        byte[] raw=encodeRequest(request);assertEquals(request,decodeRequest(raw));
        var doc=new Document(new SourceRefs(ref("request.json",raw.length,"1".repeat(64)),
                ref(PRODUCER_FILE,1234,"2".repeat(64))),request);
        byte[] encoded=encode(doc);var consumed=decode(encoded);
        assertEquals(doc,consumed);assertArrayEquals(encoded,encode(consumed));
        assertEquals(new WithStateDirectory(directory(),Long.MAX_VALUE),effective(consumed.request().configuration()));
        assertTrue(new String(encoded,java.nio.charset.StandardCharsets.UTF_8).contains("\"limit_bytes\":\"9223372036854775807\""));
    }
    @Test void javaDisabledIsExplicitAndCannotBeInferredFromMissingLegacyFacts()throws Exception{
        var modern=input(new JavaConfigured(new Disabled(),0,Admission.ROOT_STORAGE));
        assertEquals(new NoStateDirectory(),effective(decodeRequest(encodeRequest(modern)).configuration()));
        var missing=legacy(new MissingDirectory(),new MissingLimit(),new MissingGuard());
        var observed=decodeRequest(encodeRequest(input(missing)));
        assertEquals(Origin.LEGACY_CAPTURED,observed.configuration().origin());
        assertEquals(missing,observed.configuration());
        assertEquals(Problem.LEGACY_FACTS_MISSING,assertThrows(UnusableSettings.class,()->effective(observed.configuration())).problem());
    }
    @Test void legacyMissingNullAndEmptyRemainDistinctAcrossSerialization()throws Exception{
        for(var fact:List.<DirectoryFact>of(new MissingDirectory(),new NullDirectory(),new DirectoryValue(""))){
            var request=input(legacy(fact,new LimitValue(BigInteger.ZERO),new NullGuard()));
            assertEquals(request,decodeRequest(encodeRequest(request)));
        }
        assertEquals(new NoStateDirectory(),effective(legacy(new NullDirectory(),new LimitValue(BigInteger.ZERO),new NullGuard())));
        assertEquals(Problem.LEGACY_RELATIVE_DIRECTORY,assertThrows(UnusableSettings.class,
                ()->effective(legacy(new DirectoryValue(""),new LimitValue(BigInteger.ZERO),new NullGuard()))).problem());
        var nullLimit=legacy(new NullDirectory(),new NullLimit(),new NullGuard());
        assertEquals(nullLimit,decodeRequest(encodeRequest(input(nullLimit))).configuration());
        assertEquals(Problem.LEGACY_NULL_LIMIT,assertThrows(UnusableSettings.class,()->effective(nullLimit)).problem());
    }
    @Test void fullLegacyIntegerIsPreservedBeforeActualStoreRangeQualification()throws Exception{
        BigInteger huge=BigInteger.ONE.shiftLeft(80);var old=legacy(new DirectoryValue(directory().toString()),new LimitValue(huge),new NullGuard());
        assertEquals(old,decodeRequest(encodeRequest(input(old))).configuration());
        assertEquals(Problem.LEGACY_LIMIT_RANGE,assertThrows(UnusableSettings.class,()->effective(old)).problem());
        var inline=legacy(new NullDirectory(),new LimitValue(huge),new NullGuard());
        assertEquals(inline,decodeRequest(encodeRequest(input(inline))).configuration());
        assertEquals(new NoStateDirectory(),effective(inline));
        assertThrows(IllegalArgumentException.class,()->new LimitValue(BigInteger.valueOf(-1)));
    }
    @Test void capturedCallableReferenceDoesNotBecomeRootStorageAdmission(){
        var old=legacy(new DirectoryValue(directory().toString()),new LimitValue(BigInteger.TEN),new GuardValue(ref("original-guard.py",41,"3".repeat(64))));
        assertEquals(old,decodeRequest(encodeRequest(input(old))).configuration());
        assertEquals(Problem.LEGACY_GUARD_UNBOUND,assertThrows(UnusableSettings.class,()->effective(old)).problem());
    }
    @Test void declaredLegacyValuesCannotMintObservedRuntimeArgumentCustody()throws Exception{
        var declared=legacy(new NullDirectory(),new LimitValue(BigInteger.ZERO),new NullGuard());
        assertEquals(new NoStateDirectory(),effective(declared));
        assertEquals(Problem.LEGACY_CAPTURE_UNAVAILABLE,assertThrows(UnusableSettings.class,
                ()->OriginalDriverQueryHistorySettings.requireCapturedRuntimeFacts(declared)).problem());
        var modern=new JavaConfigured(new Disabled(),0,Admission.ROOT_STORAGE);
        assertDoesNotThrow(()->OriginalDriverQueryHistorySettings.requireCapturedRuntimeFacts(modern));
    }
    @Test void numericBooleanNullUnknownAndMissingFieldsDoNotCoerceIntoConfiguration(){
        var request=input(new JavaConfigured(new Disabled(),0,Admission.ROOT_STORAGE));
        for(var wrong:List.of(StrictJson.object().put("v",true).get("v"),StrictJson.object().put("v",0).get("v"),
                StrictJson.object().put("v",0.0).get("v"),StrictJson.object().putNull("v").get("v"))){
            var root=requestNode(request);configuration(root).set("limit_bytes",wrong);rejected(root);
        }
        for(String spelling:List.of("-1","+0","00","0.0","9223372036854775808")){
            var root=requestNode(request);configuration(root).put("limit_bytes",spelling);rejected(root);
        }
        var missing=requestNode(request);configuration(missing).remove("limit_bytes");rejected(missing);
        var unknown=requestNode(request);unknown.put("unknown",true);rejected(unknown);
        var admission=requestNode(request);configuration(admission).put("admission","NOOP");rejected(admission);
        var missingSelection=requestNode(request);configuration(missingSelection).remove("state_directory");rejected(missingSelection);
    }
    @Test void originalSourceVersionAndRequestPeriodAreValidatedBeforeInternalUse(){
        assertThrows(IllegalArgumentException.class,()->new LegacyCaptured(ref("native_driver.py",LEGACY_DRIVER_BYTES,"4".repeat(64)),
                new NullDirectory(),new LimitValue(BigInteger.ZERO),new NullGuard()));
        assertThrows(IllegalArgumentException.class,()->new Request("unknown",OBSERVED,REVIEW,new JavaConfigured(new Disabled(),0,Admission.ROOT_STORAGE)));
        assertThrows(IllegalArgumentException.class,()->new Request("actual-machine",OBSERVED,OBSERVED,new JavaConfigured(new Disabled(),0,Admission.ROOT_STORAGE)));
        assertThrows(IllegalArgumentException.class,()->new Directory(Path.of("relative-state")));
        assertThrows(IllegalArgumentException.class,()->new JavaConfigured(new Disabled(),-1,Admission.ROOT_STORAGE));
    }
}
