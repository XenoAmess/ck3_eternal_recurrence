package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class RootSoftwareFixtureHandoffTest {
    @TempDir Path root;
    private ControlBuild.FileRef missing(String name) {
        return new ControlBuild.FileRef(root.resolve(name).toAbsolutePath().toString(), 2, "0".repeat(64));
    }
    @Test void originalProbeMustBelongToBothDeclaredClosures() {
        var request = missing("original.json"); var payload = missing("payload.json");
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareFixtureHandoff.Request(
                List.of(payload), List.of(request), request, payload));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareFixtureHandoff.Request(
                List.of(request), List.of(request), payload, payload));
        assertThrows(IllegalArgumentException.class, () -> new RootSoftwareFixtureHandoff.Request(
                List.of(request), List.of(request, request), request, payload));
    }
    @Test void aDescriptorCannotSelectAnArbitraryPublicationPath() {
        assertThrows(IllegalArgumentException.class, () -> RootSoftwareFixtureHandoff.publication(null, "../other.json"));
    }
    @Test void anotherNativeOwnerBirthFailsBeforeAnyDeclaredSourceIsOpened() throws IOException {
        var actual = WindowsJobProcess.exactProcess(ProcessHandle.current().pid());
        var wrongBirth = new java.math.BigInteger(actual.creationFiletimeDecimal()).subtract(java.math.BigInteger.ONE).toString();
        var original = missing("original.json"); var payload = missing("payload.json");
        var request = new RootSoftwareFixtureHandoff.Request(List.of(original), List.of(original), original, payload);
        var sources = List.of(missing("G2SoftwareFixtureSourceProvider.java"), missing("RootSoftwareFixtureLifecycle.java"),
                missing("DeferredRootSoftwareFixtureProvider.java"), missing("G2CallContextHost.java"), missing("G2CallContextWire.java"));
        var pending = new RootSoftwareFixtureHandoff.Pending("xar.root-software-fixture-pending/v1", RootSoftwareFixtureHandoff.SCOPE,
                WindowsJobProcess.currentMachineId(), Instant.now().plusSeconds(60).toString(),
                new MapAdmissionServiceOwner.ProcessWire(actual.pid(), wrongBirth, actual.executable()),
                missing("accepted-build.json"), missing("java.exe"), sources, request, root.toAbsolutePath().normalize().toString());
        IOException refusal = assertThrows(IOException.class, () -> RootSoftwareFixtureHandoff.verifyInputs(pending));
        assertEquals("original Root owner/machine/finite software lifetime unavailable", refusal.getMessage());
    }
}
