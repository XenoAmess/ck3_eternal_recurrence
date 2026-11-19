package org.xar.ck3.markets.saveaudit;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveJson;
import static org.junit.jupiter.api.Assertions.*;

final class FinancialTombstoneTest {
    @TempDir Path directory;
    @Test void twoPassFinancialReaderKeepsAllRealMoneyAndSeparateTombstoneCoverage() throws Exception {
        String base=FinancialSaveAuditSelfTest.scene();
        Path save=directory.resolve("tombstone.txt");Files.writeString(save,base.substring(0,base.length()-2)+"1288=none}}");
        var layout=new FinancialProjector.LayoutHypothesis("synthetic","999",BigInteger.valueOf(100000),"story","char");
        var old=directory.resolve("original.txt");Files.writeString(old,base);
        var before=FinancialSaveReader.read(old,"synthetic-tombstone-machine",layout);
        var after=FinancialSaveReader.read(save,"synthetic-tombstone-machine",layout);
        assertEquals(before.financialStories(),after.financialStories());assertEquals(5,after.coverage().tableRecords());
        assertEquals(6,after.coverage().tableSlots());assertEquals(5,after.coverage().selectedFinancialRecords());
        assertEquals("1288",after.coverage().tombstones().getFirst().id().value());
        assertEquals(before.coverage().streamedFinancialTokenBytes(),after.coverage().streamedFinancialTokenBytes());
        assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD,FinancialAudit.audit(FinancialProjector.project(after,layout)).assessment());
        var inputs=new FinancialSaveAuditMain.Inputs("synthetic-tombstone-machine",FilePins.pin(save),List.of(FilePins.pin(save)),layout,List.of());
        var result=FinancialSaveAuditMain.inspectRetiredXfma(inputs);
        assertTrue(result.financial().coldComparison().getFirst().exactSelectedFinancialState());
        assertEquals(result,SaveJson.read(SaveJson.write(result),FinancialSaveAuditMain.RetiredObserverOutput.class));
        assertFalse(result.financial().financialCertified());
    }
    @Test void financialMissingTypeMalformedVariableAndQuotedNoneRemainErrors() throws Exception {
        String base=FinancialSaveAuditSelfTest.scene();var layout=new FinancialProjector.LayoutHypothesis("synthetic","999",BigInteger.valueOf(100000),"story","char");
        for(String bad:List.of("1288=\"none\"","1288=0","1288={owner=31254 seed=1 variables={data={{flag=xfm_free_cents data={type=value identity=1}}}}}")) {
            Path save=directory.resolve("bad-"+Math.abs(bad.hashCode())+".txt");Files.writeString(save,base.substring(0,base.length()-2)+bad+"}}");
            assertThrows(java.io.IOException.class,()->FinancialSaveReader.readWithRetiredXfma(save,"synthetic-tombstone-machine",layout));
        }
    }
}
