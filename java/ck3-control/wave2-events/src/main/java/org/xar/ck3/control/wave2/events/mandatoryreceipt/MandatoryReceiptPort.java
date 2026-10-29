package org.xar.ck3.control.wave2.events.mandatoryreceipt;

/** Consumer seam for the existing service's after-response body; provides no write or replay method. */
@FunctionalInterface
public interface MandatoryReceiptPort {
    MandatoryReceiptModel.AfterResponse produce(MandatoryReceiptModel.Input input);
}
