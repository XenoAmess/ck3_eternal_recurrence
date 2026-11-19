package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;

/** Source/capability registration DATA only: no RootContext, Native client, owner ticket or Game is created. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.opening56.dll.path",matches=".+")
final class OpeningReadBindingQualificationTest {
    private static ExactRef actualDll() {
        return new ExactRef(Path.of(System.getProperty("xar.opening56.dll.path")).toAbsolutePath().toString(),
                Long.parseLong(System.getProperty("xar.opening56.dll.bytes")),System.getProperty("xar.opening56.dll.sha256"));
    }
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
}
