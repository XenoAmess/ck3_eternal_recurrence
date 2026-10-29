package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

/** Parser/source contracts only: these cases never observe the real Steam client or mint admission. */
final class SteamOfflineContractTest {
    @TempDir Path temporary;
    @Test void offlineRequiresBothOriginalPositiveNativeSamples()throws Exception{
        SteamOfflineProbe.requirePositive(1,4);
        for(int[] invalid:new int[][]{{0,4},{1,0},{1,3},{2,4},{1,7}})assertThrows(IOException.class,()->SteamOfflineProbe.requirePositive(invalid[0],invalid[1]));
    }
    @Test void allThreeOriginalProfilesBindVersionSizeAndShaTogether(){
        assertEquals(3,SteamOfflineProfiles.ALL.size());
        for(var profile:SteamOfflineProfiles.ALL){
            assertSame(profile,SteamOfflineProfiles.select(profile.version(),profile.bytes(),profile.sha256()));
            assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select("0.0.0.0",profile.bytes(),profile.sha256()));
            assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(profile.version(),profile.bytes()+1,profile.sha256()));
            assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(profile.version(),profile.bytes(),"0".repeat(64)));
            assertEquals(6,profile.anchors().size());assertTrue(profile.anchors().stream().allMatch(a->a.bytes().length>0&&a.rva()>0));
        }
    }
    @Test void malformedPhysicalPeCannotBecomeQualifiedSteamSource()throws Exception{
        Path source=temporary.resolve("software-not-steam.dll");Files.write(source,new byte[128]);
        assertThrows(IOException.class,()->SteamOfflineProbe.fileAnchors(source,SteamOfflineProfiles.ALL.get(0)));
        Files.write(source,new byte[]{0x4d,0x5a});
        assertThrows(IOException.class,()->SteamOfflineProbe.fileAnchors(source,SteamOfflineProfiles.ALL.get(0)));
    }
    @Test void actualProducerFailureWritesUnavailableWithoutAnOfflineBooleanOrFalseOnlineClaim()throws Exception{
        Path steam=temporary.resolve("steam.exe");Files.writeString(steam,"software input, not Steam");
        Path receipt=temporary.resolve("unavailable.json");
        var plan=new SteamOfflineProbe.Plan("software-only-different-machine",ControlBuild.FileRef.measure(steam),Instant.now().plusSeconds(5));
        var failure=assertThrows(SteamOfflineProbe.UnavailableException.class,()->SteamOfflineProbe.observe(plan,receipt));
        assertEquals("unavailable",failure.status());new ControlBuild.FileRef(failure.evidence().path(),failure.evidence().bytes(),failure.evidence().sha256()).verify();
        var actual=ControlBuild.strictMapper().readTree(Files.readAllBytes(receipt));
        assertEquals("unavailable",actual.path("status").textValue());assertFalse(actual.has("offline_mode"));
        assertEquals("software-only-different-machine",actual.path("machine_id").textValue());
        assertEquals("native_query_failed",actual.path("reason").textValue());
        assertTrue(actual.path("diagnostics").toString().contains("machine differs"));
        assertEquals(SteamOfflineObservation.Status.UNAVAILABLE,SteamOfflineObservationCodec.decode(Files.readAllBytes(receipt)).status());
    }
}
