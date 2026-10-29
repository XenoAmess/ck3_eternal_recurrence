package org.xar.ck3.control.wave2.events.mandatorybefore;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;

/** Validated before-body proposal; never a persisted ticket, authorization or token claim. */
public final class MandatoryBeforeModel {
    private MandatoryBeforeModel() { }
    public record Input(String incidentId, String capturedAtUtc, FrameBinding frame, NativeWindow window,
            NativeChoice selectedChoice, EvidenceDocument originalCapture) {
        public Input {
            StrictJson.text(incidentId); StrictJson.utc(capturedAtUtc); Objects.requireNonNull(frame);
            Objects.requireNonNull(window); Objects.requireNonNull(selectedChoice); Objects.requireNonNull(originalCapture);
        }
    }
    public record BeforeBody(Input source) {
        public BeforeBody { Objects.requireNonNull(source); }
        public boolean dispatchAttempted() { return false; }
        public boolean replayAllowed() { return false; }
        public boolean offlineFollowupRequired() { return true; }
        public boolean persistenceCommitted() { return false; }
        public boolean actionAuthorized() { return false; }
    }
}
