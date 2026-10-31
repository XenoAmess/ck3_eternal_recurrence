package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

final class CurrentR4ProfileTest {
    @Test void r4ExtendsOnlyTheNewExplicitInventoryAndTwoSelectedModuleEnvelopes() {
        var prior=ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3;
        var current=ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4;
        assertEquals(4096,prior.maxFiles());assertEquals(5120,current.maxFiles());
        assertEquals(prior.maxBytes(),current.maxBytes());assertEquals(64L<<20,current.maxBytes());
        assertEquals(8L<<20,prior.moduleSourceBytes("application","src"));
        assertEquals(8L<<20,prior.moduleSourceBytes("local-service","src"));
        assertEquals(12L<<20,current.moduleSourceBytes("application","src"));
        assertEquals(12L<<20,current.moduleSourceBytes("local-service","src"));
        for(String unchanged:List.of("contracts","native-transport","build-tools","g2-research",""))assertEquals(8L<<20,current.moduleSourceBytes(unchanged,"src"));
        assertTrue(current.completeG2()&&current.fullParity()&&current.resumedParity()&&current.currentParity());
        assertTrue(prior.currentParity());assertFalse(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2.currentParity());
        assertEquals(8L<<20,current.moduleSourceBytes("application",".mvn"));assertEquals(8L<<20,current.moduleSourceBytes("local-service",".mvn"));assertEquals(35,current.maxReactorProjects());
    }
    @Test void r4KeepsCurrentWholeFixtureAndAllDefaultConsumerRequirements() {
        var profile=ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4;
        assertEquals(ControlCi.httpRequirements(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3),ControlCi.httpRequirements(profile));
        assertThrows(IOException.class,()->ControlCi.requireFullParityFixtureProduction(profile,null));
        Path missing=Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        assertThrows(IllegalArgumentException.class,()->FullParityOracleBindings.fromEnvironment(profile,Map.of(),missing));
        assertThrows(IllegalArgumentException.class,()->FullParityOracleBindings.fromRecordedArguments(profile,List.of()));
    }
    @Test void newSourceProfileDoesNotExpandInputWireOrNativeFinancialAuthority() {
        var profile=CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R4;
        assertEquals(5120,profile.maxFiles());assertEquals(64L<<20,profile.maxLogicalBytes());assertEquals(80L<<20,profile.maxNativeBytes());
        assertEquals(CompleteSourceGraph.modules(CompleteSourceGraph.Profile.G2_FULL_PARITY_20261024_R3),CompleteSourceGraph.modules(profile));
        assertEquals(4<<20,ControlBuild.receiptMaxBytes(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4));
        assertEquals("xar.full-parity-current-oracle-inputs/v11",FullParityCurrentBindings.SCHEMA);
        assertEquals(44,FullParityCurrentBindings.Role.values().length);
        assertEquals(2,java.util.Arrays.stream(FullParityCurrentBindings.Role.values()).filter(r -> r.generation() == 11).count());
        assertEquals(java.util.Set.of("CONSTRUCTION_REFUND_NATIVE_PACKETS", "CONSTRUCTION_REFUND_SIGNED_GOLDEN"),
                java.util.Arrays.stream(FullParityCurrentBindings.Role.values()).filter(r -> r.generation() == 11)
                        .map(FullParityCurrentBindings.Role::name).collect(java.util.stream.Collectors.toSet()));
    }
}
