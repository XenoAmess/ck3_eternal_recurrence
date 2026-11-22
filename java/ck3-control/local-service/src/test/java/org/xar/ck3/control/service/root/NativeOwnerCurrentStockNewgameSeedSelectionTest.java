package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.FrontendMenuFrameV1;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Pure DATA selection boundaries, not a Native frame producer or a no-mod world/SAVE qualification. */
final class NativeOwnerCurrentStockNewgameSeedSelectionTest {
    private static ObjectNode config(){
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v39").put("mode","current_stock_newgame_robert_seed")
                .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",1024)
                .put("checkpoint_archive_path","D:/stock-seed-DATA/immutable.ck3").put("maximum_checkpoint_bytes",256L<<20)
                .put("checkpoint_observation_attempts",64).put("checkpoint_poll_interval_ms",500).put("maximum_core_polls",256).put("core_poll_interval_ms",2000);
        c.putObject("owner_descriptor").put("path","D:/stock-seed-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CoreFrame.Partial core(CoreFrame.Prefix p){return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,p);}
    private static CoreFrame.Prefix prefix(){return new CoreFrame.Prefix(53144328,2,true,0,true,true,Integer.MIN_VALUE,true);}
    private static FrontendMenuFrameV1.Source main(){return new FrontendMenuFrameV1.Source(FrontendMenuFrameV1.Route.MAIN_MENU,Optional.empty(),Optional.empty(),false,false);}
    private static FrontendMenuFrameV1.Source bookmarks(){return new FrontendMenuFrameV1.Source(FrontendMenuFrameV1.Route.BOOKMARKS,Optional.empty(),Optional.empty(),false,false);}
    private static FrontendMenuFrameV1.OwnerWitness owner(long connection,long ticket){return new FrontendMenuFrameV1.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static FrontendMenuFrameV1 query(){return new FrontendMenuFrameV1(FrontendMenuFrameV1.Action.QUERY_MENU,FrontendMenuFrameV1.Status.AVAILABLE,false,false,false,
            BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(main()),Optional.of(owner(9,11)),Optional.empty());}
    private static FrontendMenuFrameV1 open(long provider,long connection){return new FrontendMenuFrameV1(FrontendMenuFrameV1.Action.OPEN_BOOKMARKS,FrontendMenuFrameV1.Status.BOOKMARKS_OPENED,true,true,false,
            BigInteger.valueOf(provider),BigInteger.TWO,BigInteger.ONE,Optional.of(bookmarks()),Optional.of(owner(connection,29)),Optional.empty());}

    @Test void explicitV39SelectsOnlyOneFixedWorkflowWithFiniteSubmissionHeadroom() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_STOCK_NEWGAME_SEED,NativeOwnerSnapshotMain268.observationMode(config()));
        var parsed=NativeOwnerSnapshotMain268.currentStockSeedConfig(config());assertEquals(267,parsed.submissions());assertEquals(256,parsed.maximumCorePolls());
        for(String mode:List.of("current_frontend_menu","current_core_checkpoint_save","current_stock_newgame","current_date_advance",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",mode)));
    }
    @Test void callerCannotSupplyActorDateCoreLeaseActionsPermissionsOrPreviousMaterial() {
        for(String field:List.of("actor","actor_id","date_raw","expected_core","load","product","fixture","production_root","enabled_mods","no_mods","native_can",
                "action","event_role","query_sequence","provider_generation","deadline_unix_ms","instance_id","previous_checkpoint_source","previous_checkpoint_archive","unknown"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(field,"forged")),field);
    }
    @Test void requiredFieldsAndRealOwnerFilePinCannotBeOmittedOrBooleanSized() {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","checkpoint_archive_path",
                "maximum_checkpoint_bytes","checkpoint_observation_attempts","checkpoint_poll_interval_ms","maximum_core_polls","core_poll_interval_ms")) {
            var c=config();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c),field);
        }
        var c=config();((ObjectNode)c.get("owner_descriptor")).put("bytes",true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c));
    }
    @Test void boundedNewPollingFieldsCannotLeakIntoOldModesOrExceedTheirRanges() {
        for(String key:List.of("maximum_core_polls","core_poll_interval_ms","checkpoint_observation_attempts","checkpoint_poll_interval_ms","maximum_checkpoint_bytes"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(key,0)),key);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("maximum_core_polls",257)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("core_poll_interval_ms",5001)));
        var old=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v14").put("mode","current_core_checkpoint_save")
                .put("checkpoint_archive_path","D:/old-DATA/first.ck3").put("maximum_checkpoint_bytes",1024).put("checkpoint_observation_attempts",1).put("checkpoint_poll_interval_ms",100);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CORE_CHECKPOINT_SAVE,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("maximum_core_polls",1)));
    }
    @Test void actualNewGameTypedNoModsAllowsOnlyExplicitSettingsSeedAndRejectsSavedOrEnvironment() throws IOException {
        var vanilla=NativeLaunchPlan.PreparedProfile.vanilla();
        NativeOwnerSnapshotMain268.requireCurrentStockSeedDeclaration(new NativeLaunchPlan.NewGame(),vanilla);
        var ref=new ControlBuild.FileRef("D:/stock-seed-DATA/settings.txt",1,"0".repeat(64));
        NativeOwnerSnapshotMain268.requireCurrentStockSeedDeclaration(new NativeLaunchPlan.NewGame(),NativeLaunchPlan.PreparedProfile.vanilla(ref));
        var savedRef=new ControlBuild.FileRef("D:/stock-seed-DATA/source.ck3",1,"0".repeat(64));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockSeedDeclaration(new NativeLaunchPlan.SavedGame("source",savedRef),vanilla));
        var explicit=NativeLaunchPlan.PreparedProfile.explicit(ref,ProfileKind.SAVED_VANILLA,List.of(),List.of());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockSeedDeclaration(new NativeLaunchPlan.NewGame(),explicit));
    }
    @Test void onlyAnActualEmptyEnabledModsArrayPassesWithoutDisablingDlc() throws IOException {
        var actual=StrictJson.object();actual.putArray("enabled_mods");actual.putArray("disabled_dlcs").add("a_legitimate_disabled_dlc");
        NativeOwnerSnapshotMain268.requireStockSeedEnabledMods(actual);
        for(var wrong:List.of(StrictJson.object(),StrictJson.object().putNull("enabled_mods"),StrictJson.object().put("enabled_mods",false),StrictJson.object().put("enabled_mods","[]")))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedEnabledMods(wrong));
        actual.withArray("enabled_mods").add("mod/fixture.mod");assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedEnabledMods(actual));
    }
    @Test void typedCurrentUnavailableOrIncompleteCoreIsNotReadyAndOldBuildIsRejected() throws IOException {
        assertFalse(NativeOwnerSnapshotMain268.stockSeedCoreReady(new CoreFrame.Unavailable(ExactCk3Build.CK3_121003_STEAM_26785313,true,"loading-DATA")));
        assertFalse(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144328,2,true,-1,false,false,-1,false))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.stockSeedCoreReady(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix())));
    }
    @Test void readyCoreUsesActualSignedActorAndRequiresZeroDatePausedLivingMapAndLocalPlayer() throws IOException {
        assertTrue(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(prefix())));
        assertTrue(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144328,5,true,0,true,true,0,true))));
        assertFalse(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144328,2,false,0,true,true,7,true))));
        assertFalse(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144328,2,true,-1,true,true,7,true))));
        assertFalse(NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144328,2,true,0,true,true,7,false))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.stockSeedCoreReady(core(new CoreFrame.Prefix(53144352,2,true,0,true,true,7,true))));
    }
    @Test void independentAfterSaveMustRetainTheWholeActualPrefix() throws IOException {
        NativeOwnerSnapshotMain268.requireStockSeedSameCore(prefix(),core(prefix()));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedSameCore(prefix(),core(new CoreFrame.Prefix(53144328,3,true,0,true,true,Integer.MIN_VALUE,true))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedSameCore(prefix(),core(new CoreFrame.Prefix(53144328,2,true,0,true,true,17,true))));
    }
    @Test void genuineAfterMenuSourceAndNewTicketAreAllowedButOriginalLeaseConnectionAndStatusStayRequired() throws IOException {
        NativeOwnerSnapshotMain268.requireStockSeedFrontendEffect(query(),open(1,9),FrontendMenuFrameV1.Action.OPEN_BOOKMARKS);
        assertNotEquals(query().source(),open(1,9).source());assertNotEquals(query().ownerWitness(),open(1,9).ownerWitness());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedFrontendEffect(query(),open(2,9),FrontendMenuFrameV1.Action.OPEN_BOOKMARKS));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedFrontendEffect(query(),open(1,10),FrontendMenuFrameV1.Action.OPEN_BOOKMARKS));
        var refusal=new FrontendMenuFrameV1(FrontendMenuFrameV1.Action.OPEN_BOOKMARKS,FrontendMenuFrameV1.Status.SOURCE_CHANGED,false,false,false,
                BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(main()),Optional.of(owner(9,30)),Optional.of("actual-refusal-DATA"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedFrontendEffect(query(),refusal,FrontendMenuFrameV1.Action.OPEN_BOOKMARKS));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireStockSeedFrontendEffect(query(),open(1,9),FrontendMenuFrameV1.Action.QUIT_MENU));
    }
}
