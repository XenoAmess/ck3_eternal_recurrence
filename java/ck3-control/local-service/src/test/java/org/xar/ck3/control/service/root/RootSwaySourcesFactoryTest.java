package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.sway.SwaySelectedObservation;
import org.xar.ck3.control.application.planning.sway.SwayFollowingConsumption;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Sole producer -> strict reader -> actual runtime configuration projection; no Core or native qualification. */
public final class RootSwaySourcesFactoryTest {
    @TempDir Path output;
    @Test void exactConfigurationRoundtripPreservesExplicitSchedulerBranchAndIdenticalRootRegistration() {
        for(boolean scheduler:new boolean[]{false,true}) {
            var source=configuration(scheduler);var encoded=RootSwaySourcesFactory.encode(source);var actual=RootSwaySourcesFactory.decode(encoded);assertEquals(source,actual);assertArrayEquals(encoded,RootSwaySourcesFactory.encode(actual));
            assertEquals(scheduler,assertInstanceOf(RootRuntimeDomainAssembly.SwayOriginals.class,actual.initialization()).scheduler().isPresent());assertEquals(scheduler,actual.invalidationReasonQuery());
            var originalRoot=new FinanceReadContracts.Registration(ref("actual-root-definition"),new FinanceReadContracts.Permission(Optional.empty(),"software-root",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP));
            var runtime=RootSwaySourcesFactory.runtimeConfiguration(actual,actual.originalWriterLock(),originalRoot);
            assertSame(originalRoot,runtime.sharedRoot().registration());assertEquals(FinanceReadContracts.ROOT_CONTRACT_ID,runtime.sharedRoot().contractId());assertEquals(actual.capabilities(),runtime.capabilities());assertEquals(actual.legacyLedger(),runtime.originalLegacyLedger());assertEquals(actual.invalidationReasonQuery(),runtime.invalidationReasonQuery());
        }
    }
    @Test void originalRequiredFieldsAndWrongScalarTypesNeverBecomeDefaultsOrEmptyOriginals() {
        for(String defect:new String[]{"missing-permission","null-permission","numeric-permission","missing-scheduler","null-formal","missing-origin","bool-bytes","float-bytes","null-capability","numeric-capability","unknown-field","old-schema","unknown-machine","wrong-legacy"}) {
            var row=(ObjectNode)StrictJson.parse(RootSwaySourcesFactory.encode(configuration(true)));
            switch(defect){case "missing-permission"->row.remove("invalidation_reason_query");case "null-permission"->row.putNull("invalidation_reason_query");case "numeric-permission"->row.put("invalidation_reason_query",1);case "missing-scheduler"->((ObjectNode)row.get("initialization")).remove("scheduler");case "null-formal"->((ObjectNode)row.get("initialization")).putNull("formal");case "missing-origin"->((ObjectNode)row.get("initialization")).remove("guarded_origin_read");case "bool-bytes"->((ObjectNode)row.at("/initialization/formal")).put("bytes",true);case "float-bytes"->((ObjectNode)row.at("/initialization/formal")).put("bytes",1.0);case "null-capability"->((ObjectNode)row.get("capabilities")).putNull("formal_query");case "numeric-capability"->((ObjectNode)row.get("capabilities")).put("formal_action",1);case "unknown-field"->row.put("ready",true);case "old-schema"->row.put("schema","xar.java.sway-source-configuration/v2");case "unknown-machine"->row.put("machine_id","unknown");case "wrong-legacy"->row.put("legacy_ledger",path("other-ledger").toString());default->throw new AssertionError(defect);}
            assertThrows(IllegalArgumentException.class,()->RootSwaySourcesFactory.decode(StrictJson.canonical(row)),defect);
        }
    }
    @Test void explicitFreshRoundtripNeedsNoFutureGameReadAndNeverAcceptsImportFields() throws Exception {
        var source=new RootSwaySourcesFactory.SourceConfiguration("test-machine",Instant.parse("2026-10-24T00:00:00Z"),Instant.parse("2026-10-24T04:30:00Z"),output.resolve("writer.lock"),output.resolve("not-created-legacy-ledger"),new OrdinarySwayService.Capabilities(true,true,true),new RootRuntimeDomainAssembly.SwayFresh(),false);
        assertFalse(Files.exists(source.legacyLedger()));
        assertEquals(source,RootSwaySourcesFactory.decode(RootSwaySourcesFactory.encode(source)));
        for(String defect:new String[]{"missing","null","kind-bool","kind-unknown","origin","formal","scheduler"}) {
            var row=(ObjectNode)StrictJson.parse(RootSwaySourcesFactory.encode(source));var branch=(ObjectNode)row.get("initialization");
            switch(defect) {
                case "missing"->row.remove("initialization");case "null"->row.putNull("initialization");case "kind-bool"->branch.put("kind",true);case "kind-unknown"->branch.put("kind","fresh_default");
                case "origin"->branch.set("guarded_origin_read",ref("fabricated-read").toJson());case "formal"->branch.set("formal",ref("old-ledger").toJson());case "scheduler"->branch.putNull("scheduler");default->throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class,()->RootSwaySourcesFactory.decode(StrictJson.canonical(row)),defect);
        }
    }
    @Test void originalWriterScopeAndReviewIntervalAreStrictDataContracts() {
        var original=configuration(false);var registration=new FinanceReadContracts.Registration(ref("actual-root"),new FinanceReadContracts.Permission(Optional.empty(),"software-root",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP));
        assertThrows(IllegalArgumentException.class,()->RootSwaySourcesFactory.runtimeConfiguration(original,path("other-lock"),registration));
        var row=(ObjectNode)StrictJson.parse(RootSwaySourcesFactory.encode(original));row.put("review_at_utc",original.observedAt().toString());assertThrows(IllegalArgumentException.class,()->RootSwaySourcesFactory.decode(StrictJson.canonical(row)));
    }
    /** Actual complete SDK/source-input fixture must supply its real objects; this helper does not construct Inputs or issue Core. */
    public static RootSwaySourcesFactory.Products prepareActualAndAssert(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeDomainSettings.Bound settings,FinanceReadContracts.Registration sameRoot)throws Exception {
        var actual=RootSwaySourcesFactory.prepare(inputs,selected,settings,sameRoot);var original=RootSwaySourcesFactory.readExact(inputs.data(RootRuntimeDefinitionModel.DataRole.SWAY_CONFIGURATION));assertEquals(original.initialization(),actual.initialization());
        assertTrue(actual.prepared().registration().producerSources().contains(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,SwaySelectedObservation.class)));
        assertTrue(actual.prepared().registration().producerSources().contains(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootInitialEpisodeProof.class)));
        assertTrue(actual.prepared().registration().producerSources().contains(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootRuntimeDomainAssembly.class)));
        assertTrue(actual.prepared().registration().producerSources().contains(selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,SwayFollowingConsumption.class)));return actual;
    }
    private static RootSwaySourcesFactory.SourceConfiguration configuration(boolean scheduler){return new RootSwaySourcesFactory.SourceConfiguration("test-machine",Instant.parse("2026-10-24T00:00:00Z"),Instant.parse("2026-10-24T04:30:00Z"),path("writer.lock"),path("original-ledger"),new OrdinarySwayService.Capabilities(true,true,false),new RootRuntimeDomainAssembly.SwayOriginals(ref("original-ledger"),scheduler?Optional.of(ref("original-scheduler")):Optional.empty(),ref("guarded-origin-read")),scheduler);}
    private static Path path(String name){return Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize().resolve("software-sway-source-config").resolve(name);}
    private static ExactRef ref(String name){return new ExactRef(path(name).toString(),1,"a".repeat(64));}
}
