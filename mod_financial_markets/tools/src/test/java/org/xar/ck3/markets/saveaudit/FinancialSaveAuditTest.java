package org.xar.ck3.markets.saveaudit;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Maven bridge for the same already-existing 21 + 31 standalone assertions; no added synthetic qualification. */
final class FinancialSaveAuditTest {
    @TempDir Path directory;
    @Test void originalReadbackAndFinancialInvariants() throws Exception { FinancialSaveAuditSelfTest.main(new String[]{directory.toString()}); }
    @Test void streamingGrowthAndRefusalBoundaries() throws Exception { FinancialStreamingSelfTest.main(new String[]{directory.toString()}); }
}
