package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Pure software profile/wire checks; never reads Steam or creates QualifiedOffline. */
final class SteamOffline1123ProfileTest {
    private static final String SHA="2dfb0a5d50dd90667549cc7d413c7bfb0794c9af4ebaf08bf1cf7d938a11ea93";
    private static int integer(byte[] bytes,int offset){return ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt(offset);}
    private static SteamOfflineObservation.NativeEvidence evidence(SteamOfflineProfiles.Profile profile,int offset){
        var steam=new SteamOfflineObservation.SteamProcess(12001,"134000000000000001",Path.of("steam.exe").toAbsolutePath().normalize().toString(),profile.version());
        var source=new SteamOfflineObservation.Source(Path.of("steamui.dll").toAbsolutePath().normalize().toString(),profile.bytes(),profile.sha256(),"9007199254740993","1794535550000000000");
        long base=0x180000000L;var anchor=profile.anchors().get(0);
        return new SteamOfflineObservation.NativeEvidence("software-fixture-machine","2026-11-18T17:00:00Z","software-fixture-nonce",
                Long.toString(base),profile.imageSize(),Integer.toString(profile.valueRva()),Long.toString(base+profile.valueRva()),
                Integer.toString(anchor.rva()),anchor.hex(),SteamOfflineObservation.hash(anchor.bytes()),List.of(1,1),steam,steam,source,source,
                Integer.toString(profile.managerRva()),Long.toString(0x200000000L),Integer.toString(offset),List.of(4,4));
    }
    @Test void exact1123SelectorDoesNotInheritAnotherSourceOrLayout(){
        var current=SteamOfflineProfiles.select("11.23.65.88",19675800,SHA);
        assertEquals(19959808,current.imageSize());assertEquals(0x11ca0d7,current.valueRva());
        assertEquals(0x11c8328,current.managerRva());assertEquals(0x160,current.trayOffset());
        for(var other:SteamOfflineProfiles.ALL)if(other!=current){
            assertEquals(0x154,other.trayOffset());
            assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(current.version(),other.bytes(),other.sha256()));
            assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(other.version(),current.bytes(),current.sha256()));
        }
        assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(current.version(),current.bytes()+1,SHA));
        assertThrows(IllegalArgumentException.class,()->SteamOfflineProfiles.select(current.version(),current.bytes(),"0".repeat(64)));
    }
    @Test void allProfileInstructionDisplacementsAgreeWithDeclaredByteAndTrayLayout(){
        for(var profile:SteamOfflineProfiles.ALL){
            var anchors=profile.anchors();var producer=anchors.get(0);var getter=anchors.get(1);var caller=anchors.get(2);var tray=anchors.get(3);
            int backing=producer.rva()+8+integer(producer.bytes(),4);
            int object=caller.rva()+7+integer(caller.bytes(),3);
            assertEquals(profile.valueRva(),backing);
            assertEquals(backing,object+integer(getter.bytes(),28));
            assertEquals(getter.rva(),caller.rva()+12+integer(caller.bytes(),8));
            assertEquals(backing,tray.rva()+7+integer(tray.bytes(),2));
            assertEquals(profile.managerRva(),tray.rva()+16+integer(tray.bytes(),12));
            byte[] compare=anchors.get(4).bytes(),store=anchors.get(5).bytes();
            assertEquals(profile.trayOffset(),integer(compare,compare.length-4));
            assertEquals(profile.trayOffset(),integer(store,store.length-4));
        }
    }
    @Test void positiveNativeWireRoundTripsOnlyTheOffsetOfItsExactProfile()throws Exception{
        for(var profile:SteamOfflineProfiles.ALL){
            var value=evidence(profile,profile.trayOffset());
            var common=new SteamOfflineObservation.Common(value.machineId(),value.observedAtUtc(),value.nonce(),
                    Optional.of(value.steamBefore()),Optional.of(value.sourceBefore()),Optional.empty(),List.of());
            var data=new SteamOfflineObservation.Offline(common,SteamOfflineObservation.Method.NATIVE_CURRENT_USER_BYTE,Optional.of(value));
            assertEquals(data,SteamOfflineObservationCodec.decode(SteamOfflineObservationCodec.encode(data)));
            int other=profile.trayOffset()==0x154?0x160:0x154;
            assertThrows(IllegalArgumentException.class,()->evidence(profile,other));
        }
    }
    @Test void originalPackageProfileConstructorKeepsItsLegacyTrayOffset(){
        var original=SteamOfflineProfiles.ALL.get(0);
        var copy=new SteamOfflineProfiles.Profile(original.version(),original.bytes(),original.sha256(),original.imageSize(),
                original.valueRva(),original.managerRva(),original.anchors());
        assertEquals(0x154,copy.trayOffset());
    }
}
