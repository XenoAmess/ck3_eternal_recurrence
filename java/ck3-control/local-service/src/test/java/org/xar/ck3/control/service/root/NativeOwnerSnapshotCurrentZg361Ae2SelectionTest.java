package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Result;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Source;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Self-owned Java DATA only; no Native frames, pipe, fixture setup or Game. */
class NativeOwnerSnapshotCurrentZg361Ae2SelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config() {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v49").put("mode","current_zg361_ae2_case_once")
                .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/java-data/zg361/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CoreFrame.Prefix core(int actor,int date) {
        return new CoreFrame.Prefix(date,1,true,0,true,true,actor,true);
    }
    private static CurrentLetterResult.OwnerWitness owner(int connection,int ticket,int pump) {
        return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(pump),42);
    }
    private static CurrentZg361Ae2Source controls(boolean otherCan) {
        var present=new CurrentZg361Ae2Source.ControlRow(CurrentZg361Ae2Source.Control.PRESENT,"zga_ae2_present_decision",true,false,Optional.of(true),true);
        var verify=new CurrentZg361Ae2Source.ControlRow(CurrentZg361Ae2Source.Control.VERIFY,"zga_ae2_verify_decision",otherCan,false,Optional.empty(),false);
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(new CurrentZg361Ae2Source.Controls(true,true,true,true,true,false,false,Optional.of(CurrentZg361Ae2Source.Control.PRESENT),List.of(present,verify))),Optional.empty());
    }
    private static CurrentZg361Ae2Source events(int actor,boolean phase,boolean canPay) {
        String text="actual Java DATA";
        var a=new CurrentZg361Ae2Source.Option(17,"zg361comp.1.ae2.r3",true,text,"","third actual tooltip");
        var b=new CurrentZg361Ae2Source.Option(15,"zg361comp.1.ae2.r1",canPay,text,"","\u0000\u0015actual25\n");
        var c=new CurrentZg361Ae2Source.Option(16,"zg361comp.1.ae2.r2",true,text,"","second actual tooltip");
        var actual=new CurrentZg361Ae2Source.Ae2(7,Integer.toUnsignedLong(actor),"zg361comp.1",42,phase,true,true,true,true,List.of(a,b,c),phase&&canPay);
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.EVENTS,Optional.empty(),Optional.of(new CurrentZg361Ae2Source.Events(true,List.of(new CurrentZg361Ae2Source.EventIdentity(7,Integer.toUnsignedLong(actor),"zg361comp.1")),Optional.of(actual))));
    }
    private static CurrentZg361Ae2Result query(CurrentZg361Ae2.Action action,CurrentZg361Ae2Source source,CoreFrame.Prefix core) {
        return new CurrentZg361Ae2Result(action,CurrentZg361Ae2Result.Status.AVAILABLE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(core),Optional.of(owner(1,3,4)),Optional.of(source),Optional.empty());
    }
    private static CurrentZg361Ae2Result dispatch(CurrentZg361Ae2Source source,CoreFrame.Prefix core,BigInteger query,int connection) {
        return new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.CONFIRM_PRESENT,CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED,true,true,true,BigInteger.ONE,query,BigInteger.ONE,Optional.of(core),Optional.of(owner(connection,8,9)),Optional.of(source),Optional.empty());
    }
    @Test void strictV49SelectsOnlyTheFixedComposite() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_ZG361_AE2,NativeOwnerSnapshotMain268.observationMode(config()));
        assertEquals(24,NativeOwnerSnapshotMain268.currentZg361Ae2Config(config()).submissions());
    }
    @Test void oldSchemaAndForeignModeCannotBorrowTheNewComposite() {
        var old=config().put("schema","xar.native-owner-snapshot-config/v48");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old));
        var foreign=config().put("mode","current_living_original_case_once");
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2Config(foreign));
    }
    @Test void callerSelectorsWalletFlagsDaysAndLeaseFieldsAreRejected() {
        for(String name:List.of("actor","history_id","subject","instance_id","index","option_key","key","case_id","phase_bound","native_can","days","provider_generation","query_sequence","checkpoint_archive_path")) {
            var c=config();c.put(name,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2Config(c),name);
        }
        var missing=config();missing.remove("owner_descriptor");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2Config(missing));
    }
    @Test void finiteSubmissionsCountOnlyActualConditionalListBranches() {
        assertEquals(18,NativeOwnerSnapshotMain268.currentZg361Ae2SubmissionBound(false,false));
        assertEquals(21,NativeOwnerSnapshotMain268.currentZg361Ae2SubmissionBound(true,false));
        assertEquals(21,NativeOwnerSnapshotMain268.currentZg361Ae2SubmissionBound(false,true));
        assertEquals(24,NativeOwnerSnapshotMain268.currentZg361Ae2SubmissionBound(true,true));
        var bad=config().put("overall_timeout_seconds",601);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2Config(bad));
    }
    @Test void fullSignedCoreIdentityIsPreservedWithoutHistoryIdSubstitution()throws IOException {
        var high=core(-2,Integer.MIN_VALUE);NativeOwnerSnapshotMain268.requireCurrentZg361Ae2SameCore(high,core(-2,Integer.MIN_VALUE));
        NativeOwnerSnapshotMain268.requireCurrentZg361Ae2SameCore(core(0,0),core(0,0));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2SameCore(high,core(1128,Integer.MIN_VALUE)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2SameCore(high,core(-2,Integer.MIN_VALUE+24)));
    }
    @Test void queryNeedsActualCompleteCoreConnectionAndCorrectQueryAction()throws IOException {
        var c=core(0,0);var f=query(CurrentZg361Ae2.Action.QUERY_CONTROLS,controls(true),c);
        assertSame(f.source().orElseThrow(),NativeOwnerSnapshotMain268.requireCurrentZg361Ae2QueryFrame(f,CurrentZg361Ae2.Action.QUERY_CONTROLS,c,BigInteger.ONE));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2QueryFrame(f,CurrentZg361Ae2.Action.QUERY_AE2,c,BigInteger.ONE));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2QueryFrame(f,CurrentZg361Ae2.Action.QUERY_CONTROLS,c,BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2QueryFrame(f,CurrentZg361Ae2.Action.QUERY_CONTROLS,core(0,24),BigInteger.ONE));
    }
    @Test void dispatchRetainsWholeBeforeSourceAndLeaseButAllowsNewTicketPump()throws IOException {
        var c=core(0,0);var before=query(CurrentZg361Ae2.Action.QUERY_CONTROLS,controls(true),c);
        NativeOwnerSnapshotMain268.requireCurrentZg361Ae2DispatchFrame(dispatch(controls(true),c,BigInteger.TWO,1),before,CurrentZg361Ae2.Action.CONFIRM_PRESENT,BigInteger.ONE);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2DispatchFrame(dispatch(controls(false),c,BigInteger.TWO,1),before,CurrentZg361Ae2.Action.CONFIRM_PRESENT,BigInteger.ONE));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2DispatchFrame(dispatch(controls(true),c,BigInteger.TEN,1),before,CurrentZg361Ae2.Action.CONFIRM_PRESENT,BigInteger.ONE));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2DispatchFrame(dispatch(controls(true),c,BigInteger.TWO,2),before,CurrentZg361Ae2.Action.CONFIRM_PRESENT,BigInteger.ONE));
    }
    @Test void authoredFifteenAndCompleteTooltipBytesDoNotUseDisplayOrdinalZero()throws IOException {
        var s=events(-2,true,true);var actual=NativeOwnerSnapshotMain268.requireCurrentZg361Ae2ActualTooltips(s,core(-2,0));
        assertEquals(17,actual.options().get(0).authoredOptionIndex());assertEquals(15,actual.payNowOption().authoredOptionIndex());
        assertEquals("\u0000\u0015actual25\n",actual.payNowOption().tooltip());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2ActualTooltips(s,core(0,0)));
    }
    @Test void falseCanAndFalsePhaseRemainQueryDataWithoutPayAuthority()throws IOException {
        var c=core(0,0);var source=events(0,false,false);var f=query(CurrentZg361Ae2.Action.QUERY_AE2,source,c);
        assertSame(source,NativeOwnerSnapshotMain268.requireCurrentZg361Ae2QueryFrame(f,CurrentZg361Ae2.Action.QUERY_AE2,c,BigInteger.ONE));
        assertFalse(source.actionAdmissible(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361Ae2ActualTooltips(source,c));
    }
    @Test void dispatchKindsAndSummaryNeverClaimActualPaymentVerifierOrSave()throws IOException {
        assertEquals(CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,NativeOwnerSnapshotMain268.currentZg361Ae2DispatchStatus(CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST));
        assertEquals(CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED,NativeOwnerSnapshotMain268.currentZg361Ae2DispatchStatus(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW));
        assertEquals(CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED,NativeOwnerSnapshotMain268.currentZg361Ae2DispatchStatus(CurrentZg361Ae2.Action.CONFIRM_VERIFY));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentZg361Ae2DispatchStatus(CurrentZg361Ae2.Action.QUERY_AE2));
        var r=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentZg361Ae2Result(r,"java-data");
        for(String flag:List.of("payment_confirmed","fixture_verifier_pass","actual_wallet_deltas_observed","business_contract_pass","wholeproduct_pass","new_date_observed","physical_save_confirmed"))assertFalse(r.path(flag).booleanValue(),flag);
        assertEquals(0,r.path("date_calls").intValue());assertEquals(0,r.path("save_calls").intValue());
    }
}
