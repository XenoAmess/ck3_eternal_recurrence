package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;

/** Source-selection regression only; this helper cannot issue a native qualification or Root read permit.
 * The persistent actual RootHostBatchAndCloseActualTest enters the same catalog install and original frame callback. */
public final class RootCrownNativeReadInstallationTest {
    @TempDir Path directory;
    private FileRef original()throws Exception {
        Path path=directory.resolve("ck3_12004_realm_law_action_mailbox.cpp");
        byte[] bytes="source-selection-only, not a native fixture\n".getBytes(StandardCharsets.UTF_8);
        Files.write(path,bytes);
        return new FileRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    @Test public void actualSelectedOriginalIsRetainedWithoutPathRebinding()throws Exception {
        var actual=original();
        assertEquals(new ExactRef(actual.path(),actual.bytes(),actual.sha256()),
                RootRuntimeCatalogFactory.crownDefinition(List.of(actual)));
    }
    @Test public void missingAmbiguousAndHistoricalDataNeverSupplyTheNativeDefinition()throws Exception {
        var actual=original();
        assertThrows(java.io.IOException.class,()->RootRuntimeCatalogFactory.crownDefinition(List.of()));
        assertThrows(java.io.IOException.class,()->RootRuntimeCatalogFactory.crownDefinition(List.of(actual,actual)));
        var data=new FileRef(directory.resolve("law-wire.json").toString(),actual.bytes(),actual.sha256());
        assertThrows(java.io.IOException.class,()->RootRuntimeCatalogFactory.crownDefinition(List.of(data)));
    }
    @Test public void ChangedOriginalDoesNotInheritTheQualifiedSourcePin()throws Exception {
        var actual=original();Files.writeString(Path.of(actual.path()),"changed source",StandardCharsets.UTF_8);
        assertThrows(java.io.IOException.class,()->RootRuntimeCatalogFactory.crownDefinition(List.of(actual)));
    }
    @Test public void bothActualCrownContractsRetainIndependentDispatchAndShareOnlyAvailability()throws Exception {
        var source=original();
        var definition=new ExactRef(source.path(),source.bytes(),source.sha256());
        var planning=new org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads(
                new org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.Sources(definition,definition),
                "1.20.0.4","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        var archive=org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class.cast(
                java.lang.reflect.Proxy.newProxyInstance(getClass().getClassLoader(),
                        new Class<?>[]{org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class},
                        (proxy,method,args)->{throw new AssertionError("availability cannot read or write an archive");}));
        var nativeRead=CrownAuthorityNativeRead.contract(definition,true,archive,
                (basis,originals)->{throw new AssertionError("availability cannot load a frame");});
        var contracts=new java.util.ArrayList<org.xar.ck3.control.application.action.ReadContract<?>>(planning.all());
        contracts.add(nativeRead);
        var reads=org.xar.ck3.control.application.action.RootReadContractCatalog.staticOnly(contracts);
        var root=org.xar.ck3.control.application.action.RootExecutableBindings.freeze(List.of(),reads,List.of(),32);
        assertTrue(reads.containsIdentity(planning.crown()));assertTrue(reads.containsIdentity(nativeRead));
        assertEquals(6,reads.contracts().size());
        assertEquals(1,root.installed().stream().filter(view->view.operation().equals(nativeRead.operation())).count());
        assertEquals(org.xar.ck3.control.application.action.ExecutableStepBindings.Kind.READ,
                root.describeForPublicPlanning(nativeRead.operation()).orElseThrow().descriptor().kind());
        assertEquals(org.xar.ck3.control.application.action.ReadContract.WireProfile.EXECUTE_STEP,planning.crown().wireProfile());
        assertEquals(org.xar.ck3.control.application.action.ReadContract.WireProfile.G2_PRIVATE_QUERY,nativeRead.wireProfile());
        assertEquals(org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.CROWN,planning.crown().permissionKey());
        assertEquals(CrownAuthorityNativeRead.PERMISSION_KEY,nativeRead.permissionKey());
        assertEquals(java.util.Optional.empty(),planning.crown().requiredCapability());
        assertEquals(java.util.Optional.empty(),nativeRead.requiredCapability());
    }

}
