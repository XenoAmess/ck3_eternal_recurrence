package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentDesInitGuardResult;
import org.xar.ck3.control.nativebridge.CurrentDesInitGuardSource;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure Java DATA selection boundaries; no Native frames, Game or world-state proof. */
final class NativeOwnerCurrentDesInitGuardSelectionTest {
    private static ObjectNode config() {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v40").put("mode","current_des_saved_game_init_guard")
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/des-guard-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CoreFrame.Prefix prefix(int actor) {return new CoreFrame.Prefix(53144328,2,true,0,true,true,actor,true);}
    private static CoreFrame.Partial core(CoreFrame.Prefix p) {return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,p);}
    private static CurrentDesInitGuardResult frame(int actor,boolean shown,long connection,long ticket) {
        return new CurrentDesInitGuardResult(CurrentDesInitGuardResult.Status.AVAILABLE,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,
                Optional.of(prefix(actor)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7)),
                Optional.of(new CurrentDesInitGuardSource(actor,true,true,true,shown,true,true)),Optional.empty());
    }

    @Test void explicitV40HasExactlyOneReadonlyModeAndCommonSixFields() {
        assertEquals(6,config().size());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DES_SAVED_GAME_INIT_GUARD,NativeOwnerSnapshotMain268.observationMode(config()));
        for(String mode:List.of("current_des_saved_game_init_execute","current_des_saved_game_init_guard ","current_stock_newgame_robert_seed","current_core_checkpoint_save",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",mode)));
    }
    @Test void unknownSelectorsPermissionsActionsAndSaveFieldsAreNeverBorrowed() {
        for(String field:List.of("key","guard_key","character_id","actor","is_player","native_shown","initialized","permission","action","expected_core","lease",
                "query_sequence","provider_generation","control_step","checkpoint_archive_path","previous_checkpoint_source","previous_checkpoint_archive",
                "maximum_core_polls","core_poll_interval_ms","phase","product","instance_id","unknown"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(field,"forged")),field);
    }
    @Test void everyCommonFieldAndExactOwnerFilePinIsRequired() {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var c=config();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(c),field);
        }
        var boolSize=config();((ObjectNode)boolSize.get("owner_descriptor")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(boolSize));
        var extra=config();((ObjectNode)extra.get("owner_descriptor")).put("approved",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(extra));
    }
    @Test void commonTimeoutAndFrameValuesHaveActualIntegerBounds() {
        for(String field:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(field,0)),field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(field,true)),field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put(field,"1")),field);
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("overall_timeout_seconds",601)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("read_timeout_seconds",61)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("maximum_frames_per_operation",65537)));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(config().put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536)));
    }
    @Test void oldSchemaDoesNotBorrowV40AndOldLetterQueryStillSelectsItsOriginalMode() {
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema","xar.native-owner-snapshot-config/v39")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema","xar.native-owner-snapshot-config/v24")));
        var old=config().put("schema","xar.native-owner-snapshot-config/v24").put("mode","current_letter_query");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
    }
    @Test void freshCoreAllowsFullSignedPackedActorAndRejectsOldBuildOrNotReady() throws IOException {
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE})
            assertEquals(prefix(actor),NativeOwnerSnapshotMain268.requireCurrentDesInitGuardCore(core(prefix(actor))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardCore(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix(36423))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardCore(new CoreFrame.Unavailable(ExactCk3Build.CK3_121003_STEAM_26785313,true,"loading-DATA")));
        assertThrows(IllegalArgumentException.class,()->prefix(-1));
    }
    @Test void freshCoreRequiresEveryPausedLivingMapAndLocalPlayerPredicate() {
        // Invalid speed is rejected by the existing typed prefix before any Main helper.
        for(int speed:new int[]{0,6})
            assertThrows(IllegalArgumentException.class,()->new CoreFrame.Prefix(53144328,speed,true,0,true,true,36423,true));
        for(var p:List.of(
                new CoreFrame.Prefix(53144328,2,false,0,true,true,36423,true),new CoreFrame.Prefix(53144328,2,true,-1,true,true,36423,true),
                new CoreFrame.Prefix(53144328,2,true,0,false,true,36423,true),new CoreFrame.Prefix(53144328,2,true,0,true,false,-1,false),
                new CoreFrame.Prefix(53144328,2,true,0,true,true,36423,false)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardCore(core(p)));
    }
    @Test void falseShownAndTrueShownAreBothAvailableObservationData() throws IOException {
        for(boolean shown:new boolean[]{false,true}) {
            var f=frame(36423,shown,9,20);
            var s=NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(f,prefix(36423),BigInteger.valueOf(9));
            assertEquals(shown,s.nativeShown());assertTrue(f.successful());
            assertFalse(f.initializationExecuted());assertFalse(f.migrationExecuted());assertFalse(f.nativeReturned());
        }
        for(int actor:new int[]{0,-2})
            assertEquals(actor,NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(frame(actor,false,9,20),prefix(actor),BigInteger.valueOf(9)).characterId());
    }
    @Test void changedCoreOrConnectionAndTypedRefusalNeverQualifyButNewTicketIsAllowed() throws IOException {
        var f=frame(36423,false,9,20);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(f,new CoreFrame.Prefix(53144352,2,true,0,true,true,36423,true),BigInteger.valueOf(9)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(f,prefix(36423),BigInteger.valueOf(10)));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(frame(36423,false,9,900),prefix(36423),BigInteger.valueOf(9)));
        for(var status:List.of(CurrentDesInitGuardResult.Status.UNAVAILABLE,CurrentDesInitGuardResult.Status.EXPIRED,CurrentDesInitGuardResult.Status.STALE_SOURCE,CurrentDesInitGuardResult.Status.INDETERMINATE)) {
            var refused=new CurrentDesInitGuardResult(status,status!=CurrentDesInitGuardResult.Status.INDETERMINATE,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,
                    Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual-DATA-refusal"));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDesInitGuardQueryFrame(refused,prefix(36423),BigInteger.valueOf(9)));
        }
    }
    @Test void summaryNeverTurnsAnObservationIntoInitializationExecuteDateOrSaveCredit() {
        var result=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentDesInitGuardResult(result,"DATA-machine");
        for(String field:List.of("query_available","effect_attempted","native_returned","native_handled","initialization_executed","migration_executed","initialization_proven","migration_proven","new_date_observed","physical_save_confirmed"))
            assertFalse(result.get(field).booleanValue(),field);
        for(String field:List.of("read_calls","query_calls","execute_calls","date_calls","save_calls"))assertEquals(0,result.get(field).intValue(),field);
        assertTrue(result.get("native_shown").isNull());assertTrue(result.get("character_id").isNull());
        assertFalse(result.has("initialized"));assertFalse(result.has("des_initialized"));
    }
}
