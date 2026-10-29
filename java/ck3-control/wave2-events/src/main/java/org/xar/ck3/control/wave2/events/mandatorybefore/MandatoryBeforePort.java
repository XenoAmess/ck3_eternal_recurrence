package org.xar.ck3.control.wave2.events.mandatorybefore;

/** Original service before-writer consumer seam; no path, write or submission method is exposed. */
@FunctionalInterface
public interface MandatoryBeforePort {
    MandatoryBeforeModel.BeforeBody produce(MandatoryBeforeModel.Input input);
}
