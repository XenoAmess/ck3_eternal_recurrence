package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionBindings;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;

/** Source/capability registration DATA only: no RootContext, Native client, owner ticket or Game is created. */
final class OpeningReadBindingQualificationTest {
    private static ExactRef actualDll() {
        return new ExactRef(Path.of(System.getProperty("xar.opening56.dll.path")).toAbsolutePath().toString(),
                Long.parseLong(System.getProperty("xar.opening56.dll.bytes")),System.getProperty("xar.opening56.dll.sha256"));
    }
    @EnabledIfSystemProperty(named="xar.opening56.dll.path",matches=".+")
    @Test void independentExactDllProfileDoesNotQualifyLegacyGovernance() {
        var dll=actualDll();
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,dll).isPresent());
        assertTrue(OpeningReadProfile.selectQualified("1.20.0.4",OpeningReadProfile.EXECUTABLE,dll).isEmpty());
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,"0".repeat(64),dll).isEmpty());
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,
                new ExactRef(dll.path(),dll.bytes()+1,dll.sha256())).isEmpty());
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,
                new ExactRef(dll.path(),dll.bytes(),"0".repeat(64))).isEmpty());
        var config=new GovernanceRuntimeInstaller.Config(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,"synthetic-registration-data",Set.of(),1,3);
        assertFalse(config.nativeQualified());assertTrue(config.unavailableReason().isPresent());
        assertThrows(IllegalArgumentException.class,()->new GovernancePlanningReads(new GovernancePlanningReads.Sources(dll,dll),
                OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE));
    }
    @EnabledIfSystemProperty(named="xar.opening56.dll.path",matches=".+")
    @Test void onlyTwoDistinctAdvertisedReadonlyDefinitionsKeepTheirActualSource() {
        var dll=actualDll();var profile=OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,dll).orElseThrow();
        var definitions=new OpeningReadProfile.Bindings(profile,dll);assertEquals(2,definitions.all().size());
        assertSame(definitions.scope(),definitions.all().getFirst());assertSame(definitions.current(),definitions.all().getLast());
        var operations=new HashSet<String>();var contracts=new HashSet<String>();
        for(var contract:definitions.all()) {
            assertTrue(operations.add(contract.operation().value()));assertTrue(contracts.add(contract.contractId()));
            assertEquals(dll,contract.sourceRef());assertEquals(ReadContract.PermissionMode.ADVERTISED_CAPABILITY,contract.permissionMode());
            assertEquals(ReadContract.WireProfile.EXECUTE_STEP,contract.wireProfile());
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,contract.guardMode());assertTrue(contract.hasPureReplay());
        }
        for(var kind:OpeningReadProfile.Kind.values()) {
            var contract=kind==OpeningReadProfile.Kind.SCOPE?definitions.scope():definitions.current();
            assertEquals(kind.step(),contract.operation().value());assertEquals(kind.capability(),contract.requiredCapability().orElseThrow());
            assertEquals(kind.capability(),contract.permissionKey());
        }
        assertFalse(operations.contains("query-campaign-root-context-v1"));assertFalse(operations.contains(GovernancePlanningReads.FORMAL));
    }

    @Test void full111EventBridgesRetainExactOpeningAndMappedSaveSelection() {
        var full = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        var foreground = new ExactRef(Path.of("software-full111-foreground.dll").toAbsolutePath().toString(), 21_523_968L,
                "db2a814aaa702b322a53e76512b8c80d71fc3249c71c9d31a674a436effaee86");
        var diagnostic = new ExactRef(Path.of("software-full111-event-diagnostic.dll").toAbsolutePath().toString(), 21_625_856L,
                "dcc27c14b96491519eb7269f994d5f5534d00741637632879ccc8d317d31343d");
        var directContext = new ExactRef(Path.of("software-full111-direct-context.dll").toAbsolutePath().toString(), 21_633_024L,
                "e2b0a10873102ae51faf2863a2dfe6a739860cfa5ee86fcfd21d847a37996693");
        var preparedLifetime = new ExactRef(Path.of("software-full111-prepared-lifetime.dll").toAbsolutePath().toString(), 21_633_536L,
                "30f82a857597f4a7cfa60024b29979aeaaa2b4b71716add51dc613daff335af8");
        for (var retained : java.util.List.of(foreground, diagnostic, directContext, preparedLifetime)) {
            assertAll(
                    () -> assertTrue(OpeningReadProfile.selectQualified(full.version(), full.executableSha256(), retained).isPresent()),
                    () -> assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(retained)));
            for (var wrong : java.util.List.of(new ExactRef(retained.path(), retained.bytes() + 1, retained.sha256()),
                    new ExactRef(retained.path(), retained.bytes(), "f33eb6d59068ebd21ba78ef43d933222e15427352d2bb206bb60990152963c52"))) {
                assertTrue(OpeningReadProfile.selectQualified(full.version(), full.executableSha256(), wrong).isEmpty());
                assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(wrong));
            }
        }
    }

    @EnabledIfSystemProperty(named="xar.openingFull111.dll.path",matches=".+")
    @Test void full111CombinedDllRegistersOnlyTheTwoOpeningReadsAndRetainsMappedSaveData() throws Exception {
        var full = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        var measured = ControlBuild.FileRef.measure(Path.of(System.getProperty("xar.openingFull111.dll.path")));
        var dll = new ExactRef(measured.path(), measured.bytes(), measured.sha256());
        var source = new GovernanceActionBindings.Sources(dll, dll, dll);
        var decoder = new ExactRef("software-only-java-decoder", 1, "a".repeat(64));
        var sources = new GovernanceRuntimeInstaller.Sources(source, decoder, decoder, decoder, decoder, decoder,
                dll, decoder, java.util.List.of(dll, decoder));
        var config = new GovernanceRuntimeInstaller.Config(full.version(), full.executableSha256(),
                "software-full111-registration", Set.of(), 1, 3);
        var prepared = GovernanceRuntimeInstaller.prepare(Path.of("software-only-unused.lock"), sources, config, Clock.systemUTC());
        assertFalse(prepared.nativeQualified());
        var definitions = prepared.openingReadOnly().orElseThrow().definitions();
        assertEquals(2, definitions.all().size());
        assertEquals("query-current-lifestyle-scope-26785313-v1", definitions.scope().operation().value());
        assertEquals("query-current-lifestyle-state-26785313-v1", definitions.current().operation().value());
        for (var contract : definitions.all()) {
            assertEquals(dll, contract.sourceRef());
            assertEquals(ReadContract.PermissionMode.ADVERTISED_CAPABILITY, contract.permissionMode());
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, contract.guardMode());
            assertTrue(contract.hasPureReplay());
        }
        assertEquals("game.query.current-lifestyle-scope.26785313.v1", definitions.scope().requiredCapability().orElseThrow());
        assertEquals("game.query.current-lifestyle-state.26785313.v1", definitions.current().requiredCapability().orElseThrow());
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION, OpeningReadProfile.EXECUTABLE, dll).isEmpty());
        var wrongSize = new ExactRef(dll.path(), dll.bytes() + 1, dll.sha256());
        var wrongDigest = new ExactRef(dll.path(), dll.bytes(), "0".repeat(64));
        for (var wrong : java.util.List.of(wrongSize, wrongDigest)) {
            assertTrue(OpeningReadProfile.selectQualified(full.version(), full.executableSha256(), wrong).isEmpty());
            assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(wrong));
        }
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(dll));
        var save = FullSnapshotClockControl.requestMappedSave112(dll, "native:10", BigInteger.TEN, Instant.parse("2030-01-02T03:04:05Z"));
        assertEquals("save-checkpoint", save.step());
        assertEquals("game.command.save-checkpoint", save.requiredCapability().orElseThrow());
        assertEquals(full.coreFullAdapterId(), StrictJson.parse(save.additionalFields().bytes())
                .path("full_snapshot_clock_control").path("adapter_id").textValue());
    }
}
