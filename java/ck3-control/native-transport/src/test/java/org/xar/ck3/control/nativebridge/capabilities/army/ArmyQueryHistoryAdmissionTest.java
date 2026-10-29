package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore.*;

/** Same Store admission -> captured DATA publication boundary, using explicit software guards only. */
final class ArmyQueryHistoryAdmissionTest {
    @TempDir Path temporary;
    private static ArtifactIO forbiddenIO(){return new ArtifactIO(){
        @Override public long existingFlatBytes(Path folder){throw new AssertionError("admission/disabled/compact must not inspect sidecars");}
        @Override public StoredFile writeExclusive(Path file,long maximum,WriteBody body){throw new AssertionError("admission/disabled/compact must not create sidecars");}
    };}
    private static CompactInput compact(){
        var source=ArmyJson.empty().put("step",STEP).put("accepted",true).put("query_sequence",1)
                .put("queried_snapshot_id","native:11").put("queried_revision",7).put("queried_native_revision",11);
        source.putArray("army_strengths");
        return new CompactInput(ArmyQueryHistoryStore.buildSummary(new RawJson(ArmyJson.bytes(source)),
                Optional.empty(),Optional.of("software_source_disabled"),Optional.empty()));
    }
    private static ArmyStrengthsDriverResult.NumericResult deliberatelyLazyOriginal()throws Exception {
        var nativeResult=ArmyJson.empty().put("step",STEP).put("accepted",true).put("status","available")
                .put("backend_id","controlled").put("query_sequence",1);
        nativeResult.putArray("army_strengths");
        var seed=ArmyStrengthsSourceTest.input(nativeResult,ArmyStrengthsSourceTest.projectedHello());
        var old=seed.original();
        // The finite typed source is usable, while a complete encoding must reject the changed sequence.
        var source=new Read(old.profile(),old.status(),BigInteger.TWO,old.backendId(),List.of(),
                old.timing(),old.publishedScopeStatus(),old.original());
        var query=new Query(Profile.ORDINARY_CORE_V1,Mode.AUTO_CORE,new Missing<>(),
                EntryMode.OBSERVED_PREPARED,EntryMode.OBSERVED_PREPARED);
        var selection=new ArmyStrengthsContracts.Selection(seed.snapshot(),query,seed.originalHello().orElseThrow(),new Missing<>());
        return ArmyStrengthsDriverResult.numeric(ArmyStrengthsDriverResult.project(selection,source,new ArmyStrengthsPipeline()));
    }

    @Test void directAndCompactRecordRevalidateTheSameGuardAndRefusalCannotUseCapturedData()throws Exception {
        AtomicInteger checks=new AtomicInteger();AtomicBoolean refuse=new AtomicBoolean();
        var store=new ArmyQueryHistoryStore(new Settings(temporary.resolve("no-files"),0),()->{
            checks.incrementAndGet();if(refuse.get())throw new IOException("actual original source expired");
        },forbiddenIO());
        store.requireCurrentAdmission();assertEquals(1,checks.get());
        var captured=assertInstanceOf(AlreadyCompact.class,store.record(compact()));assertEquals(2,checks.get());
        assertTrue(captured.issuedBy(store));
        refuse.set(true);
        assertEquals("actual original source expired",assertThrows(IOException.class,store::requireCurrentAdmission).getMessage());
        assertEquals(3,checks.get());
        var rejected=assertInstanceOf(AdmissionRejected.class,store.record(compact()));assertEquals(4,checks.get());
        var summary=ArmyJson.parse(rejected.summary().bytes());
        assertEquals("sidecar_admission_rejected",summary.get("unavailable_reason").textValue());
        assertEquals("actual original source expired",summary.at("/history_storage_diagnostic/reason").textValue());
        assertEquals(summary,ArmyJson.parse(new RawJson(rejected.summary().bytes()).bytes()));
        assertFalse(Files.exists(store.settings().evidenceDirectory()));
    }

    @Test void zeroBudgetStillUsesTheSameGuardBeforeTheOriginalLazyProducerAndNeverTouchesIO()throws Exception {
        var numeric=deliberatelyLazyOriginal();assertThrows(IllegalArgumentException.class,numeric::original);
        AtomicInteger checks=new AtomicInteger();AtomicBoolean refuse=new AtomicBoolean();
        var store=new ArmyQueryHistoryStore(new Settings(temporary.resolve("zero-budget"),0),()->{
            checks.incrementAndGet();if(refuse.get())throw new IllegalArgumentException("actual source binding changed");
        },forbiddenIO());
        var captured=assertInstanceOf(Disabled.class,store.record(numeric));captured.requireInput(numeric);
        assertTrue(captured.issuedBy(store));assertEquals(1,checks.get());
        store.requireCurrentAdmission();assertEquals(2,checks.get());
        refuse.set(true);
        assertThrows(IllegalArgumentException.class,store::requireCurrentAdmission);assertEquals(3,checks.get());
        var rejected=assertInstanceOf(AdmissionRejected.class,store.record(numeric));rejected.requireInput(numeric);
        assertEquals(4,checks.get());assertFalse(Files.exists(store.settings().evidenceDirectory()));
        assertEquals("actual source binding changed",ArmyJson.parse(rejected.summary().bytes())
                .at("/history_storage_diagnostic/reason").textValue());
    }

    @Test void originalOptionalNoneRemainsUnguardedDataWithoutAnInventedAdmissionAuthority()throws Exception {
        var store=new ArmyQueryHistoryStore(new Settings(temporary.resolve("unguarded-data"),0),Optional.empty(),forbiddenIO());
        store.requireCurrentAdmission();
        var result=assertInstanceOf(AlreadyCompact.class,store.record(compact()));
        assertTrue(result.issuedBy(store));assertTrue(result.input().isEmpty());
        assertEquals(result.settings(),store.settings());assertFalse(Files.exists(store.settings().evidenceDirectory()));
    }
}
