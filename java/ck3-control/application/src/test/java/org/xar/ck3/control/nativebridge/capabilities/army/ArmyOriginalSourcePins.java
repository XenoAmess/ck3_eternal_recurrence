package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;

/** Test-only exact original source pins. Missing environment is a failure, never a synthetic pass. */
final class ArmyOriginalSourcePins {
    private ArmyOriginalSourcePins() { }
    static void verify(String relative,String expectedSha) throws Exception {
        String configured=System.getProperty("xar.repository.root");if(configured==null||configured.isBlank())throw new IllegalStateException("required source root missing: xar.repository.root");
        var root=java.nio.file.Path.of(configured).toRealPath();var path=root.resolve(relative).toRealPath();assertTrue(path.startsWith(root));assertEquals(expectedSha,java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(java.nio.file.Files.readAllBytes(path))),"original producer source drift: "+relative);
    }
}
