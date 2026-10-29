package org.xar.ck3.control.contracts.index;

import org.junit.jupiter.api.Test;

/** Kept in the normal contracts Maven test lifecycle. */
final class OrderedCandidateIndexTest {
    @Test void completeOrderedIdentityAndRevocationRegression() {
        OrderedCandidateIndexTestMain.main(new String[0]);
    }
}
