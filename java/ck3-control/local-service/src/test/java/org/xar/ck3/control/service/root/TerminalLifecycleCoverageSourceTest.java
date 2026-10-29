package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;

/** Mixed coverage DATA exercises the actual terminal join's typed selector; no receipt, terminal proof or Root permission is minted. */
final class TerminalLifecycleCoverageSourceTest {
    @TempDir Path root;
    private ExactRef original(String name)throws Exception {
        byte[] raw=("actual retained "+name+" DATA").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Path target=root.resolve(name);Files.write(target,raw);
        return new ExactRef(target.toString(),raw.length,ActionCodec.sha256(raw));
    }
    private DriverSnapshotFacts.ActionRow legacy(String id,long ordinal,ExactRef source) {
        return new DriverSnapshotFacts.ActionRow(id,"b".repeat(64),ordinal,ordinal,source);
    }
    private DriverSnapshotFacts.ActionRow canonical(String id,long sequence,ExactRef source) {
        return new DriverSnapshotFacts.ActionRow(id,"c".repeat(64),sequence,new DriverSnapshotFacts.CanonicalOnly(source));
    }
    @Test void mixedCanonicalOnlyAndLegacyCoverageSelectsTheActualOriginalWithoutCallingAbsentOrdinals()throws Exception {
        var first=canonical("canonical-before",1,original("canonical-before.bin"));
        var actual=legacy("original-death-history",2,original("original-death-row.bin"));
        var last=canonical("canonical-after",3,original("canonical-after.bin"));
        assertThrows(IllegalStateException.class,first::historyIndex);
        assertThrows(IllegalStateException.class,last::originalResult);
        var joined=TerminalLifecycleDecisionProducer.legacyRowsAt(List.of(first,actual,last),2);
        assertEquals(1,joined.size());assertSame(actual,joined.getFirst().action());
        assertEquals(actual.originalResult(),joined.getFirst().source().originalRow());
        assertEquals(2,joined.getFirst().source().historyIndex());
        assertThrows(UnsupportedOperationException.class,joined::clear);
    }
    @Test void canonicalSourceCannotBecomeACompatibleDeathRowOrInventOrdinalZero()throws Exception {
        var actual=canonical("actual-no-compatible-history",1,original("actual-canonical-source.bin"));
        assertTrue(TerminalLifecycleDecisionProducer.legacyRowsAt(List.of(actual),1).isEmpty());
        assertThrows(IllegalArgumentException.class,()->TerminalLifecycleDecisionProducer.legacyRowsAt(List.of(actual),0));
        assertThrows(IllegalStateException.class,actual::historyIndex);
        assertThrows(IllegalStateException.class,actual::originalResult);
    }
    @Test void twoRealLegacyBindingsStayAmbiguousForTheExistingUniqueCanonicalJoinGuard()throws Exception {
        var first=legacy("first-real-binding",2,original("first-original.bin"));
        var second=legacy("second-real-binding",2,original("second-original.bin"));
        var values=TerminalLifecycleDecisionProducer.legacyRowsAt(List.of(first,second),2);
        assertEquals(2,values.size());assertEquals(List.of(first,second),values.stream().map(TerminalLifecycleDecisionProducer.LegacyActionCoverage::action).toList());
    }
}
