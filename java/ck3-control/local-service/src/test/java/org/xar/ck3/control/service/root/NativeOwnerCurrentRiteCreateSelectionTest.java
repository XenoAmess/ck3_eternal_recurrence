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
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentRiteCreate;
import org.xar.ck3.control.nativebridge.CurrentRiteCreateResult;
import org.xar.ck3.control.nativebridge.CurrentRiteCreateSource;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure DATA selection tests. No Native packet, Game, created Rite or binding proof. */
final class NativeOwnerCurrentRiteCreateSelectionTest {
    private static ObjectNode config(String mode) {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v41").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/rite-create-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(mode.equals("current_rite_create_navigation"))c.put("navigation_action","OPEN_RITE_CREATOR");
        else c.put("expected_source_rite_id",47);
        if(mode.equals("current_rite_create_and_accept_confirmation"))
            c.put("maximum_confirmation_polls",4).put("confirmation_poll_interval_ms",500);
        return c;
    }
    private static ObjectNode query() {return config("current_rite_create_query");}
    private static ObjectNode composite() {return config("current_rite_create_and_accept_confirmation");}
    private static CoreFrame.Prefix prefix(int actor) {return new CoreFrame.Prefix(53144328,2,true,0,true,true,actor,true);}
    private static CoreFrame.Partial core(CoreFrame.Prefix p) {return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,p);}
    private static CurrentRiteCreateSource source(boolean confirmation,int actor,boolean nativeCan) {
        return confirmation?new CurrentRiteCreateSource(CurrentRiteCreateSource.Phase.CONFIRMATION,47,actor,Optional.empty(),
                Optional.of(new CurrentRiteCreateSource.Confirmation(true,nativeCan,true,true,true,nativeCan))):
                new CurrentRiteCreateSource(CurrentRiteCreateSource.Phase.DRAFT,47,actor,
                Optional.of(new CurrentRiteCreateSource.Draft(true,nativeCan,Long.MAX_VALUE,Long.MIN_VALUE,true,true,true,true,true,false,nativeCan)),Optional.empty());
    }
    private static CurrentRiteCreateResult queryFrame(boolean confirmation,int actor,boolean nativeCan,long connection,long ticket) {
        return new CurrentRiteCreateResult(confirmation?CurrentRiteCreate.Action.QUERY_CONFIRMATION:CurrentRiteCreate.Action.QUERY,
                CurrentRiteCreateResult.Status.AVAILABLE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,
                Optional.of(prefix(actor)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7)),
                Optional.of(source(confirmation,actor,nativeCan)),Optional.empty());
    }
    private static CurrentRiteCreateResult dispatched(CurrentRiteCreateResult before,long connection,long ticket,Optional<CurrentRiteCreateSource> source) {
        boolean create=before.action()==CurrentRiteCreate.Action.QUERY;
        return new CurrentRiteCreateResult(create?CurrentRiteCreate.Action.CREATE:CurrentRiteCreate.Action.ACCEPT_CONFIRMATION,
                create?CurrentRiteCreateResult.Status.CREATE_DISPATCHED:CurrentRiteCreateResult.Status.CONFIRMATION_DISPATCHED,
                true,true,true,before.providerGeneration(),before.querySequence(),BigInteger.valueOf(3),before.factsBefore(),
                Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7)),source,Optional.empty());
    }

    @Test void threeExplicitModesHaveExactFieldsAndSubmissions() {
        var q=NativeOwnerSnapshotMain268.currentRiteCreateConfig(query());
        assertEquals(NativeOwnerSnapshotMain268.RiteCreateMode.QUERY,q.mode());assertEquals(3,q.submissions());assertEquals(7,query().size());
        var full=NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite());
        assertEquals(NativeOwnerSnapshotMain268.RiteCreateMode.CREATE_AND_ACCEPT_CONFIRMATION,full.mode());
        assertEquals(11,full.submissions());assertEquals(9,composite().size());
        var nav=NativeOwnerSnapshotMain268.currentRiteCreateConfig(config("current_rite_create_navigation"));
        assertEquals(NativeOwnerSnapshotMain268.RiteCreateMode.NAVIGATION,nav.mode());assertEquals(3,nav.submissions());
        assertEquals(-1,nav.expectedSourceRiteId());
        for(String mode:List.of("current_rite_create","current_rite_create_query ","current_rite_final_confirmation","current_rite_doctrine",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("mode",mode)));
    }
    @Test void allCommonFieldsAndActualOwnerFilePinAreRequired() {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id")) {
            var c=query();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(c),field);
        }
        var boolBytes=query();((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(boolBytes));
        var extra=query();((ObjectNode)extra.get("owner_descriptor")).put("permission",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(extra));
        for(String field:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put(field,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put(field,true)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put(field,"1")));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("overall_timeout_seconds",601)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("read_timeout_seconds",61)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("maximum_frames_per_operation",65537)));
    }
    @Test void observedRiteIdIsMandatoryUint32DataWithoutDefaultZero() {
        for(long value:new long[]{0,47,0xffff_fffeL})
            assertEquals(value,NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("expected_source_rite_id",value)).expectedSourceRiteId());
        for(long value:new long[]{-1,0xffff_ffffL,0x1_0000_0000L})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("expected_source_rite_id",value)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("expected_source_rite_id",true)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("expected_source_rite_id","47")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("expected_source_rite_id",47.0)));
    }
    @Test void onlyCompositeMayPollAndOriginalFiniteBoundsRemainExplicit() {
        assertEquals(8,NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put("maximum_confirmation_polls",1)).submissions());
        assertEquals(71,NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put("maximum_confirmation_polls",64)).submissions());
        for(long value:new long[]{0,65})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put("maximum_confirmation_polls",value)));
        for(long value:new long[]{99,5001})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put("confirmation_poll_interval_ms",value)));
        for(String field:List.of("maximum_confirmation_polls","confirmation_poll_interval_ms")) {
            var missing=composite();missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(missing));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put(field,true)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put(field,1)));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(composite().put("status_poll_interval_ms",500)));
    }
    @Test void navigationHasOnlyItsTwoFixedActionsAndNeverBorrowsOldEdit() {
        for(String action:List.of("OPEN_RITE_CREATOR","OPEN_PUPPET_RITE_CREATOR"))
            assertEquals(action,NativeOwnerSnapshotMain268.currentRiteCreateConfig(config("current_rite_create_navigation").put("navigation_action",action)).navigationAction());
        for(String action:List.of("CONFIRM_EDIT","create_rite","OPEN_RITE_EDITOR","OPEN_RITE_CREATOR ",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(config("current_rite_create_navigation").put("navigation_action",action)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(config("current_rite_create_navigation").put("expected_source_rite_id",47)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put("navigation_action","OPEN_RITE_CREATOR")));
        for(String field:List.of("action","actor","native_can_create","known_dynastic","selected_dynastic","piety_cost_raw","permission","expected_core","source","provider_generation","query_sequence","lease","instance_id","key","ordinal","checkpoint_archive_path","previous_checkpoint_source","rite_action","maximum_status_polls","unknown"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreateConfig(query().put(field,"forged")),field);
    }
    @Test void schemasDoNotBorrowNewCreateModesAndOldV18StaysSeparate() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v18","xar.native-owner-snapshot-config/v16","xar.native-owner-snapshot-config/v40"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("schema",schema)));
        var old=composite().put("schema","xar.native-owner-snapshot-config/v18").put("mode","current_rite_final_confirmation");
        old.remove("confirmation_poll_interval_ms");old.put("status_poll_interval_ms",500);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_FINAL_CONFIRMATION,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("confirmation_poll_interval_ms",500)));
    }
    @Test void actualCoreRetainsSignedActorButRejectsEveryNotReadyBoundary() throws IOException {
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE})
            assertEquals(prefix(actor),NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(core(prefix(actor))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix(36423))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(new CoreFrame.Unavailable(ExactCk3Build.CK3_121003_STEAM_26785313,true,"loading-DATA")));
        // Prefix itself validates speed and absent-actor sentinels before a helper can run.
        assertThrows(IllegalArgumentException.class,()->new CoreFrame.Prefix(53144328,0,true,0,true,true,36423,true));
        assertThrows(IllegalArgumentException.class,()->new CoreFrame.Prefix(53144328,6,true,0,true,true,36423,true));
        assertThrows(IllegalArgumentException.class,()->prefix(-1));
        for(var p:List.of(new CoreFrame.Prefix(53144328,2,false,0,true,true,36423,true),
                new CoreFrame.Prefix(53144328,2,true,-1,true,true,36423,true),
                new CoreFrame.Prefix(53144328,2,true,0,false,true,36423,true),
                new CoreFrame.Prefix(53144328,2,true,0,true,false,-1,false),
                new CoreFrame.Prefix(53144328,2,true,0,true,true,36423,false)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(core(p)));
    }
    @Test void summaryNeverClaimsCreationBindingDateOrSaveFromDispatch() {
        for(String mode:List.of("current_rite_create_query","current_rite_create_and_accept_confirmation","current_rite_create_navigation")) {
            var result=StrictJson.object();var cfg=NativeOwnerSnapshotMain268.currentRiteCreateConfig(config(mode));
            NativeOwnerSnapshotMain268.initializeCurrentRiteCreateResult(result,cfg,"DATA-machine");
            for(String field:List.of("rite_created","initial_binding_confirmed","new_date_observed","physical_save_confirmed","native_returned","native_handled","query_available","create_callback_dispatched","accept_callback_dispatched"))
                assertFalse(result.get(field).booleanValue(),field);
            for(String field:List.of("read_calls","draft_calls","query_calls","create_calls","confirmation_query_calls","accept_calls","navigation_calls","date_calls","save_calls"))
                assertEquals(0,result.get(field).intValue(),field);
            if(cfg.mode()==NativeOwnerSnapshotMain268.RiteCreateMode.NAVIGATION)assertFalse(result.has("expected_source_rite_id"));
            else assertEquals(47,result.get("expected_source_rite_id").longValue());
        }
    }
    @Test void completeFalseCanQueriesRetainFullRawDataButWrongCoreRiteOrConnectionIsRejected() throws IOException {
        for(boolean confirmation:new boolean[]{false,true})for(boolean can:new boolean[]{false,true}) {
            var q=queryFrame(confirmation,36423,can,9,20);
            var action=confirmation?CurrentRiteCreate.Action.QUERY_CONFIRMATION:CurrentRiteCreate.Action.QUERY;
            var actual=NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(q,action,prefix(36423),47,BigInteger.valueOf(9));
            assertEquals(q.source().orElseThrow(),actual);
            if(confirmation)assertEquals(can,actual.confirmation().orElseThrow().nativeCanAccept());
            else {
                assertEquals(can,actual.draft().orElseThrow().nativeCanCreate());
                assertEquals(Long.MAX_VALUE,actual.draft().orElseThrow().pietyCostRaw());
                assertEquals(Long.MIN_VALUE,actual.draft().orElseThrow().pietyMissingRaw());
            }
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(q,action,prefix(36423),48,BigInteger.valueOf(9)));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(q,action,new CoreFrame.Prefix(53144352,2,true,0,true,true,36423,true),47,BigInteger.valueOf(9)));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(q,action,prefix(36423),47,BigInteger.valueOf(10)));
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(queryFrame(confirmation,36423,can,9,900),action,prefix(36423),47,BigInteger.valueOf(9)));
        }
        for(int actor:new int[]{0,-2})assertEquals(actor,NativeOwnerSnapshotMain268.requireCurrentRiteCreateQueryFrame(
                queryFrame(false,actor,false,9,20),CurrentRiteCreate.Action.QUERY,prefix(actor),47,BigInteger.valueOf(9)).actorId());
    }
    @Test void voidDispatchAndFinitePendingUseOriginalWholeSourceLeaseAndIndependentCustody() throws IOException {
        for(boolean confirmation:new boolean[]{false,true}) {
            var q=queryFrame(confirmation,36423,true,9,20);
            var done=dispatched(q,9,900,q.source());
            var action=confirmation?CurrentRiteCreate.Action.ACCEPT_CONFIRMATION:CurrentRiteCreate.Action.CREATE;
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateDispatchFrame(done,q,action));
            assertFalse(done.nativeHandled());assertFalse(done.riteCreated());assertFalse(done.initialBindingConfirmed());
            assertFalse(done.newDateObserved());assertFalse(done.physicalSaveConfirmed());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateDispatchFrame(dispatched(q,10,900,q.source()),q,action));
            if(!confirmation) {
                var changed=new CurrentRiteCreateSource(CurrentRiteCreateSource.Phase.DRAFT,47,36423,
                        Optional.of(new CurrentRiteCreateSource.Draft(true,true,123,0,true,true,true,true,true,false,true)),Optional.empty());
                assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateDispatchFrame(dispatched(q,9,900,Optional.of(changed)),q,action));
            }
        }
        var original=queryFrame(false,36423,true,9,20);
        for(boolean facts:new boolean[]{false,true}) {
            var waiting=new CurrentRiteCreateResult(CurrentRiteCreate.Action.QUERY_CONFIRMATION,CurrentRiteCreateResult.Status.CONFIRMATION_PENDING,
                    false,false,true,original.providerGeneration(),original.querySequence(),BigInteger.ZERO,
                    facts?Optional.of(prefix(36423)):Optional.empty(),facts?Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(9),BigInteger.valueOf(901),BigInteger.valueOf(902),7)):Optional.empty(),Optional.empty(),Optional.of("actual-DATA-pending"));
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateWaitingFrame(waiting,original,prefix(36423),BigInteger.valueOf(9)));
        }
        var unknown=new CurrentRiteCreateResult(CurrentRiteCreate.Action.QUERY_CONFIRMATION,CurrentRiteCreateResult.Status.INDETERMINATE,
                false,false,false,original.providerGeneration(),original.querySequence(),BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual-DATA-unknown"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateWaitingFrame(unknown,original,prefix(36423),BigInteger.valueOf(9)));
    }
}
