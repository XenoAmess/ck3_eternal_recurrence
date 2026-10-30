package org.xar.ck3.control.application.planning.governance;

import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Synthetic codec and exact source tests; these do not mint a fresh-entry or restoration proof. */
final class GovernanceOpeningDocumentTest {
    private GovernanceOpeningDocument.Document initial() {
        return new GovernanceOpeningDocument.Document(request().before(),SOURCE,request().sessionId(),OpeningStage.AWAIT_SUBMIT,
                Optional.empty(),Optional.empty(),List.of(REF));
    }
    @Test void initialProducerDocumentRoundTripsItsExactFiletimeAndNeverDecodesAsComplete() {
        var original=initial();byte[] wire=GovernanceOpeningDocument.encode(original);
        var restored=GovernanceOpeningDocument.decode(wire);
        assertEquals(original,restored);assertEquals(OpeningStage.AWAIT_SUBMIT,restored.stage());
        assertEquals("133700000000000001",restored.observed().game().creationFiletime().value().toString());
        assertArrayEquals(wire,GovernanceOpeningDocument.encode(restored));
    }
    @Test void missingFieldsWrongTypesAndLegacySingleGateCannotDefaultToComplete() {
        var raw=StrictJson.object(StrictJson.parse(GovernanceOpeningDocument.encode(initial())),java.util.Set.of("schema","session_id","stage","observation","source","action_receipt","checkpoint","originals","prepared_command","existing_observed"));
        var missing=raw.deepCopy();missing.remove("stage");
        assertThrows(RuntimeException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(missing)));
        var wrong=raw.deepCopy();wrong.put("stage",true);
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(wrong)));
        var legacy=StrictJson.object().put("stage","complete").put("checkpoint_saved",true);
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(legacy)));
    }
    @Test void pendingContinuationRequiresItsActualReceiptAndFreshGateCannotContainOne() {
        var original=initial();
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),
                OpeningStage.AWAIT_RECEIPT,Optional.empty(),Optional.empty(),List.of(REF)));
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),
                OpeningStage.AWAIT_SUBMIT,Optional.of(REF),Optional.empty(),List.of(REF)));
    }
    @Test void sourceBindingIsCheckedForActualCurrentEpisodeBeforeAnyFlagIsDerived() {
        var original=initial();GovernanceOpeningDocument.requireSameEpisode(original,request().before(),SOURCE);
        var changed=new G2Source(SOURCE.machineId(),NOW.toString(),"1.20.0.3",REF);
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.requireSameEpisode(original,request().before(),changed));
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),
                OpeningStage.COMPLETE,Optional.empty(),Optional.empty(),List.of()));
    }
    @Test void preparedOriginalIsNeverDecodedAsAnActionReceiptOrCompletion() {
        var original=initial();var pending=new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.AWAIT_RECEIPT,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.of(REF),Optional.empty());
        var decoded=GovernanceOpeningDocument.decode(GovernanceOpeningDocument.encode(pending));
        assertEquals(Optional.of(REF),decoded.preparedCommand());assertTrue(decoded.actionReceipt().isEmpty());assertEquals(OpeningStage.AWAIT_RECEIPT,decoded.stage());
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.empty(),Optional.empty()));
    }
    @Test void preparedCommandCannotEnterConsumptionWithoutTheActualFocusReceipt() {
        var original=initial();
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.AWAIT_CONSUMPTION,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.of(REF),Optional.empty()));
        var pending=new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.AWAIT_RECEIPT,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.of(REF),Optional.empty());
        var raw=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(GovernanceOpeningDocument.encode(pending));raw.put("stage",OpeningStage.AWAIT_CONSUMPTION.name());
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(raw)));
    }
    @Test void existingFocusAndSubmittedFocusRemainSeparatePersistedBranches() {
        var original=initial();var observed=identity(10);
        var existing=new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.empty(),Optional.of(observed));
        assertEquals(existing,GovernanceOpeningDocument.decode(GovernanceOpeningDocument.encode(existing)));
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.of(REF),Optional.empty(),List.of(REF),Optional.of(REF),Optional.of(observed)));
        var raw=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(GovernanceOpeningDocument.encode(existing));raw.set("prepared_command",REF.toJson());
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(StrictJson.canonical(raw)));
    }
    @Test void foreignExistingFocusCannotTurnAnOpeningBodyIntoComplete() {
        var original=initial();var value=identity(10);var frame=value.frame();var nativeIdentity=frame.identity();
        var foreign=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity("foreign-machine",value.game(),frame,value.observationVersion());
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.empty(),Optional.of(foreign)));
        var foreignFrame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(nativeIdentity,frame.snapshotId(),frame.revision(),"foreign-episode");
        var foreignEpisode=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(value.machineId(),value.game(),foreignFrame,value.observationVersion());
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.empty(),Optional.empty(),List.of(REF),Optional.empty(),Optional.of(foreignEpisode)));
    }

    @Test void consumedSameGameFocusDocumentRetainsOriginalActionAndCommandWithoutManufacturingSave() {
        var original=initial();
        var complete=new GovernanceOpeningDocument.Document(original.observed(),SOURCE,original.sessionId(),OpeningStage.COMPLETE,
                Optional.of(REF),Optional.empty(),List.of(REF),Optional.of(REF),Optional.empty());
        var decoded=GovernanceOpeningDocument.decode(GovernanceOpeningDocument.encode(complete));
        assertEquals(complete,decoded);
        assertTrue(decoded.checkpoint().isEmpty());
        assertEquals(Optional.of(REF),decoded.actionReceipt());
        assertEquals(Optional.of(REF),decoded.preparedCommand());
        assertThrows(IllegalArgumentException.class,()->new GovernanceOpeningDocument.Document(original.observed(),SOURCE,
                original.sessionId(),OpeningStage.COMPLETE,Optional.empty(),Optional.empty(),List.of(REF),
                Optional.of(REF),Optional.empty()));
    }

}
