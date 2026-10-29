package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.RootSoftwareChildBootstrap;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;

/** Exercises the actual child bootstrap/installation transport only. Synthetic modules grant no SDK or Native authority. */
final class ColdSourceInstallationTransportTest {
    @TempDir Path temporary;
    @Test void actualOriginalChildUsesSharedPrefixBeforeServing() throws Exception {
        var settings = settings(false);
        var child=WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
        try {
            child.closeOwnedInput();
            assertEquals(0,child.awaitActualExit().exitCode());
            assertEquals("ORIGINAL_SOURCE32_CANONICAL_OWNER_PRESENT",Files.readString(child.stdoutPath()).trim());
            assertEquals(0,child.actualCommandResult().orElseThrow().accounting().activeProcesses());
        } finally {
            child.closeOwnedInput();
            child.awaitActualExit();
        }
    }
    @Test void malformedDerivedEmissionFailsBeforeCreatingChildFiles() throws Exception {
        var settings=settings(true);
        assertThrows(java.io.IOException.class,()->WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION));
        assertFalse(Files.exists(settings.outputRoot()),"Java verification must reject before process/output creation");
    }
    @Test void leaseCopyRetainsExplicitLineageAndWriterDoesNotInstallIt() throws Exception {
        var settings=settings(false);
        var narrowed=ClosedAdoptionMain.withinLease(settings,settings.leaseDeadline().minusSeconds(1));
        assertEquals(settings.sdkLineageBinding(),narrowed.sdkLineageBinding());
        assertFalse(WindowsFileWriterSession.bootstrapProgram(narrowed,WindowsFileWriterSession.Mode.WRITER).contains("_xar_root_install_sdk("));
        assertTrue(WindowsFileWriterSession.bootstrapProgram(narrowed,WindowsFileWriterSession.Mode.ROOT_OPERATION).contains("_xar_root_install_sdk("));
    }
    private WindowsFileWriterSession.Settings settings(boolean derived) throws Exception {
        Path repo=temporary.resolve("repo");Path modules=repo.resolve("tools/g2_saved_campaign");Files.createDirectories(modules);
        Files.writeString(repo.resolve("tools/__init__.py"),"");Files.writeString(modules.resolve("__init__.py"),"");
        Path transport=modules.resolve("current_saved_continuity_v1.py");
        Files.writeString(transport,"import sys\ndef serve_java_closed_partial_file_session_v1(**kwargs):\n"
                +"    assert 'tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1' in sys.modules\n"
                +"    print('ORIGINAL_SOURCE32_CANONICAL_OWNER_PRESENT')\n    return 0\n");
        Path owner=modules.resolve("root_current_saved_campaign_cold_owner_v1.py");
        Files.writeString(owner,"def install_java_verified_sdk_source_v1(**kwargs):\n    raise AssertionError('original route must not install Derived')\n");
        Files.setLastModifiedTime(owner,java.nio.file.attribute.FileTime.fromMillis(1_700_000_000_000L));
        assertEquals(1_700_000_000_000L,Files.getLastModifiedTime(owner).toMillis());
        Path freeze=temporary.resolve("source-only-freeze.json");Files.writeString(freeze,"{\"schema\":\"synthetic-source-only\"}");
        var binding=new RootSoftwareChildBootstrap.SdkLineageBinding(derived
                ? RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32:RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32,
                ControlBuild.FileRef.measure(freeze),derived?ControlBuild.FileRef.measure(freeze):null);
        String pythonValue=System.getProperty("xar.python");assertNotNull(pythonValue,"explicit qualified Python required");
        var environment=new HashMap<>(System.getenv());environment.put("PYTHONPATH",repo.toString());
        environment.put("PYTHONDONTWRITEBYTECODE","1");environment.put("PYTHONUTF8","1");
        environment.put("TMP",temporary.toString());environment.put("TEMP",temporary.toString());
        return new WindowsFileWriterSession.Settings(Path.of(pythonValue),repo,temporary.resolve("child-output"),
                96L*1024*1024,Duration.ofSeconds(20),Instant.now().plusSeconds(25),environment,
                pin(transport),pin(owner),()->{},Optional.of(binding));
    }
    private static ExactRef pin(Path path) throws Exception {
        byte[] raw=Files.readAllBytes(path);
        return new ExactRef(path.toString(),raw.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
}
