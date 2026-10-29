package org.xar.ck3.control.wave2.events.mandatoryreceipt;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;

/** After-response proposal only. The existing service owns the immutable before/after write. */
public final class MandatoryReceiptModel {
    private MandatoryReceiptModel() { }
    public record Ticket(String incidentId, ExactRef before, ChoiceIdentity windowId,
            ChoiceIdentity instanceId, ChoiceIdentity choiceId) {
        public Ticket {
            StrictJson.text(incidentId); Objects.requireNonNull(before); Objects.requireNonNull(windowId);
            Objects.requireNonNull(instanceId); Objects.requireNonNull(choiceId);
        }
    }
    public record NativePostcondition(boolean verified, Optional<ChoiceIdentity> oldWindowId,
            Optional<ChoiceIdentity> oldInstanceId, Optional<ChoiceIdentity> selectedChoiceId,
            boolean oldWindowNoLongerBlocking) {
        public NativePostcondition {
            Objects.requireNonNull(oldWindowId); Objects.requireNonNull(oldInstanceId); Objects.requireNonNull(selectedChoiceId);
        }
    }
    public record Reply(boolean nativeCommandAcknowledged, Optional<NativePostcondition> postcondition, EvidenceDocument originalResult) {
        public Reply { Objects.requireNonNull(postcondition); Objects.requireNonNull(originalResult); }
    }
    public record ErrorDetails(String type, String message, EvidenceDocument nativeRawReceipt) {
        public ErrorDetails { StrictJson.text(type); Objects.requireNonNull(message); Objects.requireNonNull(nativeRawReceipt); }
    }
    public record Input(Ticket ticket, Reply reply, Optional<ErrorDetails> error, String capturedAtUtc) {
        public Input {
            Objects.requireNonNull(ticket); Objects.requireNonNull(reply); Objects.requireNonNull(error);
            StrictJson.utc(capturedAtUtc);
        }
    }
    public record AfterResponse(Ticket ticket, boolean commandAcknowledged, boolean originalWindowAdvancedVerified,
            EvidenceDocument actionReceipt, Optional<ErrorDetails> error, String capturedAtUtc) {
        public AfterResponse {
            Objects.requireNonNull(ticket); Objects.requireNonNull(actionReceipt); Objects.requireNonNull(error);
            StrictJson.utc(capturedAtUtc);
            if (originalWindowAdvancedVerified && !commandAcknowledged) {
                throw new IllegalArgumentException("window advancement requires original native ACK");
            }
        }
        public boolean replayAllowed() { return false; }
        public boolean materialEffectsVerified() { return false; }
        public boolean offlineFollowupRequired() { return true; }
        public boolean persistenceCommitted() { return false; }
    }
}
