package org.xar.ck3.control.military.projectedcontact;

import org.junit.jupiter.api.Test;

/** Default Maven/JUnit entry for the complete same-input regression, after coordinated adoption. */
final class ArmyContactIndexTest {
    @Test void completeIndexDifferentialIdentityOrderAndUnknownRegression() {
        ArmyContactIndexChecks.main(new String[0]);
    }
}
