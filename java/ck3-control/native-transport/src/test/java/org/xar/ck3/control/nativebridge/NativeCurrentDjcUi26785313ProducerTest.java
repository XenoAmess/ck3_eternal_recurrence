package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

class NativeCurrentDjcUi26785313ProducerTest {
    static ObjectNode envelope(String name)throws IOException {
        try(var in=NativeCurrentDjcUi26785313ProducerTest.class.getResourceAsStream("/current-djc-ui26785313-cpp-v1/"+name+".json")) {
            if(in==null)throw new IOException("Actual C++ producer resource absent: "+name);return NativeWire.object(NativeWire.parse(in.readAllBytes()));
        }
    }
    static ObjectNode token(String name)throws IOException{return NativeWire.object(envelope(name).get("result"));}
    static CurrentDjcDeclarationUiResult decode(ObjectNode n)throws IOException{return CurrentDjcDeclarationUiResult.decode(new RawJson(StrictJson.canonical(n)));}
    @Test void allTwelveActualCppResultShapesRetainExactOkRoles()throws Exception {
        for(String name:List.of("open-ready-SYNTHETIC-DATA","resident-ready-SYNTHETIC-DATA","confirmation-false-negative-SYNTHETIC-DATA","open_ui-dispatched-SYNTHETIC-DATA","select_choice-dispatched-SYNTHETIC-DATA","send_ui-dispatched-SYNTHETIC-DATA","warning-pending-SYNTHETIC-DATA","warning-ready-SYNTHETIC-DATA","accept_warning-dispatched-SYNTHETIC-DATA","indeterminate-SYNTHETIC-DATA","incoherent-SYNTHETIC-DATA","unavailable-NoGame")) {
            var e=envelope(name);var result=decode(NativeWire.object(e.get("result")));assertEquals(e.get("ok").booleanValue(),result.nativeOk(),name);
        }
    }
    @Test void availableFalseConfirmationIsARealObservationAndCannotOpen()throws Exception {
        var r=decode(token("confirmation-false-negative-SYNTHETIC-DATA"));assertTrue(r.nativeOk());assertEquals(CurrentDjcDeclarationUiResult.Status.AVAILABLE,r.status());
        var s=r.source().orElseThrow();assertFalse(s.nativeConfirmation().orElseThrow());assertFalse(s.openAdmissible());assertFalse(s.permitsOpen());
    }
    @Test void orderedSignedExtraIdsAndClaimantAbsenceAreNotReinterpreted()throws Exception {
        var r=decode(token("resident-ready-SYNTHETIC-DATA"));var s=r.source().orElseThrow();var chosen=s.choices().getFirst();
        assertEquals(List.of(-16777215,-16777215),chosen.tuple().extraConfigurationIds());assertEquals(List.of(123,124),chosen.tuple().targetTitleIds());assertTrue(chosen.tuple().claimant().isEmpty());
        assertTrue(chosen.nativeToken().signum()>0);assertTrue(s.permitsSelection(chosen));
        var reconstructed=new CurrentDjcDeclarationUiSource.Choice(chosen.nativeToken(),chosen.tuple());assertFalse(s.permitsSelection(reconstructed));
    }
    @Test void selectedAndChoiceEnabledWireKeysAreDifferentExactContracts()throws Exception {
        var n=token("resident-ready-SYNTHETIC-DATA");var selected=(ObjectNode)n.get("source").get("selected");selected.set("native_enabled",selected.remove("source_row_enabled"));assertThrows(IOException.class,()->decode(n));
        var m=token("resident-ready-SYNTHETIC-DATA");var choice=(ObjectNode)m.get("source").get("choices").get(0);choice.set("source_row_enabled",choice.remove("native_enabled"));assertThrows(IOException.class,()->decode(m));
    }
    @Test void voidUiDispatchCannotBecomeHandledWarPaymentOrSave()throws Exception {
        for(String field:List.of("native_handled","submitted","war_created","payment_confirmed","physical_save_confirmed")) {
            var n=token("accept_warning-dispatched-SYNTHETIC-DATA");n.put(field,true);assertThrows(IOException.class,()->decode(n),field);
        }
        var n=token("send_ui-dispatched-SYNTHETIC-DATA");n.put("total_debit",0);assertThrows(IOException.class,()->decode(n));
    }
    @Test void pendingIsReadonlyFalseOkWithPositivePrivateLeaseNotAcceptPermission()throws Exception {
        var r=decode(token("warning-pending-SYNTHETIC-DATA"));assertFalse(r.nativeOk());assertEquals(CurrentDjcDeclarationUiResult.Status.WARNING_PENDING,r.status());assertFalse(r.effectAttempted());assertFalse(r.nativeReturned());assertEquals(BigInteger.ZERO,r.claimSequence());
        assertTrue(r.providerGeneration().signum()>0&&r.querySequence().signum()>0);assertFalse(r.source().orElseThrow().permitsAccept());
        var n=token("warning-pending-SYNTHETIC-DATA");n.put("action","send_ui").put("step",CurrentDjcDeclarationUi.Action.SEND_UI.step());assertThrows(IOException.class,()->decode(n));
    }
    @Test void uint64MaxLeaseIsExactAndOverflowOrNumericOrLeadingZerosReject()throws Exception {
        assertEquals(NativeWire.UINT64_MAX,decode(token("open-ready-SYNTHETIC-DATA")).providerGeneration());
        for(String bad:List.of("18446744073709551616","01","-1")){var n=token("open-ready-SYNTHETIC-DATA");n.put("provider_generation",bad);assertThrows(IOException.class,()->decode(n));}
        var n=token("open-ready-SYNTHETIC-DATA");n.put("provider_generation",1);assertThrows(IOException.class,()->decode(n));
    }
    @Test void unavailableNullsDoNotMintSourceOrLeaseAndPositiveStatusCannotBuyMissingSource()throws Exception {
        var r=decode(token("unavailable-NoGame"));assertFalse(r.nativeOk());assertTrue(r.source().isEmpty()&&r.factsBefore().isEmpty()&&r.ownerWitness().isEmpty());
        var n=token("unavailable-NoGame");n.put("status","available");n.putNull("unavailable_reason");assertThrows(IOException.class,()->decode(n));
        var m=token("open-ready-SYNTHETIC-DATA");m.put("source_available",false);assertThrows(IOException.class,()->decode(m));
    }
    @Test void exactActionStepAndNativeBeforeSourceCoherenceCannotBeRenamed()throws Exception {
        var n=token("open_ui-dispatched-SYNTHETIC-DATA");n.put("step",CurrentDjcDeclarationUi.Action.SEND_UI.step());assertThrows(IOException.class,()->decode(n));
        var m=token("open_ui-dispatched-SYNTHETIC-DATA");((ObjectNode)m.get("source")).put("native_confirmation",false);assertThrows(IOException.class,()->decode(m));
        var x=token("open-ready-SYNTHETIC-DATA");x.put("arbitrary_widget","accept_button");assertThrows(IOException.class,()->decode(x));
    }
}
