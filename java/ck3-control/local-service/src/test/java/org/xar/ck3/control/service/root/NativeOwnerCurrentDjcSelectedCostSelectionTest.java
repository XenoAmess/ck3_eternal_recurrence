package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUi;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUiResult;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUiSource;
import org.xar.ck3.control.nativebridge.CurrentDjcSelectedCostResult;
import org.xar.ck3.control.nativebridge.CurrentDjcTargetWarQueryResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Explicit local Java DATA tests mode/source matching; no private authority or Native outcome is fabricated. */
class NativeOwnerCurrentDjcSelectedCostSelectionTest {
    static ObjectNode config(){var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v25").put("mode","current_djc_selected_cost")
            .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128).put("target_character_id",888).put("cb_key","duchy_de_jure_greatwar");
        n.putObject("owner_descriptor").put("path","D:/cost-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;}
    static CoreFrame.Prefix prefix(){return new CoreFrame.Prefix(53144328,1,true,0,true,true,777,true);}
    static CurrentDjcDeclarationUiSource uiSource(List<Integer> titles) {
        var cb=CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY;
        var selected=new CurrentDjcDeclarationUiSource.SelectedTuple(cb,Optional.empty(),titles,List.of(-16777215,-16777215),false);
        return new CurrentDjcDeclarationUiSource(new NativeCharacterId(888),cb,true,4,Optional.of(true),Optional.of(true),false,true,true,true,false,
                Optional.of(new NativeCharacterId(777)),Optional.of(new NativeCharacterId(888)),Optional.empty(),Optional.of(selected),List.of(),Optional.of(false),false,false,Optional.empty(),false);
    }
    static CurrentDjcTargetWarQueryResult.OwnerWitness owner(){return new CurrentDjcTargetWarQueryResult.OwnerWitness(BigInteger.valueOf(7),BigInteger.valueOf(13),BigInteger.valueOf(23),42);}
    static CurrentDjcDeclarationUiResult query(){return new CurrentDjcDeclarationUiResult(CurrentDjcDeclarationUi.Action.QUERY_UI,CurrentDjcDeclarationUiResult.Status.AVAILABLE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(prefix()),Optional.of(owner()),Optional.of(uiSource(List.of(123,124))),Optional.empty());}
    static CurrentDjcSelectedCostResult cost(int provider,List<Integer> titles) {
        var ui=uiSource(titles);var s=new CurrentDjcSelectedCostResult.Source(ui.target(),ui.casusBelli(),ui.actor().orElseThrow(),ui.recipient().orElseThrow(),ui.additionalRole(),true,4,Optional.of(true),true,true,true,false,ui.selected().orElseThrow(),true);
        var prices=Arrays.stream(CurrentDjcSelectedCostResult.Currency.values()).map(c->new CurrentDjcSelectedCostResult.Cost(c,"0")).toList();
        return new CurrentDjcSelectedCostResult(CurrentDjcSelectedCostResult.Status.AVAILABLE,true,BigInteger.valueOf(provider),BigInteger.TWO,Optional.of(prefix()),Optional.of(owner()),Optional.of(s),Optional.of(prices),10,Optional.empty());
    }
    @Test void explicitV25OnlySelectsTheReadonlyMode() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_SELECTED_COST,NativeOwnerSnapshotMain268.observationMode(config()));
        for(String mode:List.of("current_djc_declaration_submit","open_ui","send_ui","current_djc_selected_cost ",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",mode)));
    }
    @Test void explicitPreviewRequiresOrderedTupleDataAndNeverBorrowsSendWarningConfiguration() {
        var n=config().put("mode","current_djc_selected_cost_preview");var tuple=n.putObject("tuple_intent");tuple.put("claimant_character_id",-1);tuple.putArray("target_title_ids").add(2314);tuple.putArray("extra_configuration_ids");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_SELECTED_COST_PREVIEW,NativeOwnerSnapshotMain268.observationMode(n));
        var c=NativeOwnerSnapshotMain268.currentDjcSelectedCostConfig(n,true);assertEquals(List.of(2314),c.intent().orElseThrow().targetTitleIds());assertEquals(0,c.maximumWarningPolls());
        var without=n.deepCopy();without.remove("tuple_intent");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(without));
        var withSend=n.deepCopy().put("maximum_warning_polls",1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(withSend));
    }
    @Test void allRequiredFieldsAndNoCallerAuthorityOrPrice() {
        for(String field:List.of("mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","target_character_id","cb_key")) {
            var n=config();n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
        for(String field:List.of("price","currency","costs","raw","scale","formatted_text","tuple_intent","choice_token","provider_generation","query_sequence","expected_core","native_can_send","maximum_warning_polls")) {
            var n=config();n.put(field,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
    }
    @Test void oldSchemasCannotBorrowPriceModeAndFixedCbAndSignedIdsAreValidated() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v21","xar.native-owner-snapshot-config/v23","xar.native-owner-snapshot-config/v24"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema",schema)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("target_character_id",-1)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("cb_key","arbitrary_cb")));
    }
    @Test void disabledWindowRowAndFalseCanSendRemainObservedCostDataWithoutGrantingAnAction()throws Exception {
        assertFalse(query().source().orElseThrow().permitsSend());assertFalse(cost(1,List.of(123,124)).source().orElseThrow().windowEnabled());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDjcSelectedCostFrame(query(),cost(1,List.of(123,124))));
    }
    @Test void changedLeaseOrOrderedSelectedTupleCannotMatchAnOriginalPrivateSource() {
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDjcSelectedCostFrame(query(),cost(2,List.of(123,124))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDjcSelectedCostFrame(query(),cost(1,List.of(124,123))));
    }
}
