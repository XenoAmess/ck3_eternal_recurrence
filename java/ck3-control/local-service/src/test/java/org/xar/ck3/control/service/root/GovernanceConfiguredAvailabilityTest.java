package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionBindings;

/** Configuration availability only; these references do not mint Native, Root, writer or action authority. */
final class GovernanceConfiguredAvailabilityTest {
    @TempDir Path temporary;
    private GovernanceRuntimeInstaller.Sources sources() {
        var nativeSource=new ExactRef(temporary.resolve("software-source.cpp").toString(),1,"a".repeat(64));
        var javaSource=new ExactRef(temporary.resolve("software-source.java").toString(),1,"b".repeat(64));
        return new GovernanceRuntimeInstaller.Sources(new GovernanceActionBindings.Sources(nativeSource,nativeSource,nativeSource),
                javaSource,javaSource,javaSource,javaSource,javaSource,nativeSource,javaSource,List.of(javaSource),Optional.empty());
    }
    private GovernanceRuntimeInstaller.Config config(String version,String sha) {
        return new GovernanceRuntimeInstaller.Config(version,sha,"software-availability",Set.of(new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN)),1,3);
    }
    @Test void recognizedFlorinCanPrepareCanonicalDefinitionsButCannotIssueOrInstallNativeGovernance()throws Exception {
        var config=config(ExactCk3Build.CK3_1210.version(),ExactCk3Build.CK3_1210.executableSha256());
        assertFalse(config.nativeQualified());assertTrue(config.unavailableReason().isPresent());
        var prepared=GovernanceRuntimeInstaller.prepare(temporary.resolve("original.lock"),sources(),config,Clock.systemUTC());
        assertFalse(prepared.nativeQualified());assertEquals(config.unavailableReason(),prepared.unavailableReason());
        assertFalse(prepared.domainRegistrations().isEmpty(),"canonical original-history definitions remain available");
        var qualifications=new AtomicInteger();
        assertTrue(prepared.privatePermissions((actual,hello,frame,request)->{qualifications.incrementAndGet();throw new AssertionError("no Native qualification permitted");}).isEmpty());
        assertEquals(0,qualifications.get());
        assertThrows(IOException.class,()->prepared.install(null),"must reject before any actual Core/context side effect");
        assertThrows(IllegalArgumentException.class,()->GovernanceRuntimeInstaller.buildPreparation(sources(),config,
                (same,value,id)->{throw new AssertionError("no native query");},(same,value)->{throw new AssertionError("no native query");}));
        assertThrows(IllegalArgumentException.class,()->CouncilCodec.requireBuild(config.gameVersion(),config.executableSha256()));
    }
    @Test void theFourLegacyExactConfigurationsKeepTheirOriginalQualifiedPath() {
        String[][] builds={{"1.19.0.6","2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"},
                {"1.20.0.2","AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"},
                {"1.20.0.3","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"},
                {"1.20.0.4","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"}};
        for(var build:builds) {
            var config=config(build[0],build[1]);assertTrue(config.nativeQualified());assertTrue(config.unavailableReason().isEmpty());
        }
        var latest=config(builds[3][0],builds[3][1]);
        var prepared=GovernanceRuntimeInstaller.prepare(temporary.resolve("legacy.lock"),sources(),latest,Clock.systemUTC());
        assertTrue(prepared.nativeQualified());assertTrue(prepared.unavailableReason().isEmpty());
    }
    @Test void mixedUnknownAndAliasedIdentitiesRemainRejectedAtConfiguration() {
        var sha=ExactCk3Build.CK3_1210.executableSha256();
        assertThrows(IllegalArgumentException.class,()->config("1.21.0","0".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->config("1.20.0.4",sha));
        assertThrows(IllegalArgumentException.class,()->config("1.21.0.0",sha));
        assertThrows(IllegalArgumentException.class,()->config("1.22.0",sha));
    }
}
