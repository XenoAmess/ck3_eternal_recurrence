package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import java.util.Optional;

/** Source-registry lookup consumer port. A matching source key is not an observed-effect qualification. */
@FunctionalInterface
public interface UiRecoveryIdentityPort {
    Optional<UiRecoverySourceModel.Fingerprint> identify(UiRecoverySourceModel.Input input);
}
