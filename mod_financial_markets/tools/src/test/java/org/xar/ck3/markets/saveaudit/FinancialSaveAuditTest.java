package org.xar.ck3.markets.saveaudit;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Maven bridge for the same already-existing 21 + 31 standalone assertions; no added synthetic qualification. */
final class FinancialSaveAuditTest {
    @TempDir Path directory;
    @Test void originalReadbackAndFinancialInvariants() throws Exception { FinancialSaveAuditSelfTest.main(new String[]{directory.toString()}); }
    @Test void streamingGrowthAndRefusalBoundaries() throws Exception { FinancialStreamingSelfTest.main(new String[]{directory.toString()}); }
    @Test void explicitRetiredObserverReadbackReportsEveryUntypedIdentityWithoutRelaxingFinancialRecords() throws Exception {
        var layout = new FinancialProjector.LayoutHypothesis("synthetic", "999", java.math.BigInteger.valueOf(100000), "story", "char");
        String old = "51={owner=31254 seed=2278055527 variables={data={{flag=xfma_complete data={type=value identity=100000}}}}}";
        String scene = FinancialSaveAuditSelfTest.scene();
        java.util.function.Function<String,String> append = body -> scene.substring(0, scene.length()-2) + body + "}}";
        Path save = directory.resolve("retired.txt"); java.nio.file.Files.writeString(save, append.apply(old));
        org.junit.jupiter.api.Assertions.assertThrows(java.io.IOException.class, () -> FinancialSaveReader.read(save, "synthetic-retired-machine", layout));
        var read = FinancialSaveReader.readWithRetiredXfma(save, "synthetic-retired-machine", layout);
        org.junit.jupiter.api.Assertions.assertEquals(2, read.financial().coverage().passes());
        org.junit.jupiter.api.Assertions.assertEquals(6, read.financial().coverage().tableRecords());
        org.junit.jupiter.api.Assertions.assertEquals(5, read.financial().coverage().selectedFinancialRecords());
        org.junit.jupiter.api.Assertions.assertEquals("51", read.untypedRecords().getFirst().nativeId());
        org.junit.jupiter.api.Assertions.assertEquals("RETIRED_XFMA_VALUE_ONLY_V1", read.untypedRecords().getFirst().classification());
        org.junit.jupiter.api.Assertions.assertEquals("xfma_complete", read.untypedRecords().getFirst().variables().getFirst().flag());
        org.junit.jupiter.api.Assertions.assertEquals(FinancialAudit.Assessment.CANDIDATE_INVARIANTS_HOLD, FinancialAudit.audit(FinancialProjector.project(read.financial(), layout)).assessment());
        for (String invalid : java.util.List.of(old.replace("xfma_complete", "xfm_free_cents"), old.replace("owner=31254", "owner=31254 extra=yes"),
                old.replace("type=value", "type=story"), old.replace("identity=100000", "identity={bad=yes}"), old.replace("flag=xfma_complete", "flag=xfma_complete flag=xfma_other"),
                "52={owner=31254 seed=1}", "53={owner=31254 seed=1 variables={data={}}}")) {
            java.nio.file.Files.writeString(save, append.apply(invalid));
            org.junit.jupiter.api.Assertions.assertThrows(java.io.IOException.class, () -> FinancialSaveReader.readWithRetiredXfma(save, "synthetic-retired-machine", layout));
        }
        java.nio.file.Files.writeString(save, append.apply(old) + "malformed={");
        org.junit.jupiter.api.Assertions.assertThrows(java.io.IOException.class, () -> FinancialSaveReader.readWithRetiredXfma(save, "synthetic-retired-machine", layout));
    }
    @Test void retiredObserverInspectKeepsTypedColdFinancialComparisonAndExplicitEvidence() throws Exception {
        var layout = new FinancialProjector.LayoutHypothesis("synthetic", "999", java.math.BigInteger.valueOf(100000), "story", "char");
        String scene = FinancialSaveAuditSelfTest.scene();
        String observer = "51={owner=31254 seed=1 variables={data={{flag=xfma_complete data={type=value identity=100000}}}}}";
        Path first=directory.resolve("first.txt"), second=directory.resolve("second.txt");
        java.nio.file.Files.writeString(first, scene.substring(0,scene.length()-2)+observer+"}}"); java.nio.file.Files.copy(first, second);
        var inputs=new FinancialSaveAuditMain.Inputs("synthetic-retired-machine", org.xar.ck3.save.FilePins.pin(first), java.util.List.of(org.xar.ck3.save.FilePins.pin(second)), layout, java.util.List.of());
        var result=FinancialSaveAuditMain.inspectRetiredXfma(inputs);
        org.junit.jupiter.api.Assertions.assertTrue(result.financial().coldComparison().getFirst().exactSelectedFinancialState());
        org.junit.jupiter.api.Assertions.assertEquals(result.firstUntypedRecords(),result.secondUntypedRecords().getFirst());
        org.junit.jupiter.api.Assertions.assertEquals(result, org.xar.ck3.save.SaveJson.read(org.xar.ck3.save.SaveJson.write(result), FinancialSaveAuditMain.RetiredObserverOutput.class));
        org.junit.jupiter.api.Assertions.assertFalse(result.financial().financialCertified());
    }

    @Test void namedRetiredObserverCommandUsesSourceBoundReportWhileOldVerbStillRejects() throws Exception {
        var layout = new FinancialProjector.LayoutHypothesis("synthetic", "999", java.math.BigInteger.valueOf(100000), "story", "char");
        String scene = FinancialSaveAuditSelfTest.scene();
        Path save=directory.resolve("named-retired.txt");
        java.nio.file.Files.writeString(save,scene.substring(0,scene.length()-2)+"51={owner=31254 seed=1 variables={data={{flag=xfma_complete data={type=value identity=100000}}}}}}}");
        Path repository=Path.of("").toAbsolutePath();
        while(repository!=null&&!java.nio.file.Files.isRegularFile(repository.resolve("java/ck3-save-core/pom.xml")))repository=repository.getParent();
        org.junit.jupiter.api.Assertions.assertNotNull(repository);
        var inputs=new FinancialSaveAuditMain.Inputs("synthetic-retired-machine",org.xar.ck3.save.FilePins.pin(save),java.util.List.of(),layout,java.util.List.of());
        Path request=directory.resolve("named-inputs.json"), output=directory.resolve("named-report.json"), strictOutput=directory.resolve("strict-report.json");
        java.nio.file.Files.write(request,org.xar.ck3.save.SaveJson.write(new SaveAuditCommand.Request(1,repository.toString(),inputs)));
        var command=new SaveAuditCommand();
        org.junit.jupiter.api.Assertions.assertEquals(1,command.run("audit","--inputs",request.toString(),"--output",strictOutput.toString()));
        org.junit.jupiter.api.Assertions.assertFalse(java.nio.file.Files.exists(strictOutput));
        org.junit.jupiter.api.Assertions.assertEquals(0,command.run("audit-retired-xfma","--inputs",request.toString(),"--output",output.toString()));
        var report=org.xar.ck3.save.SaveJson.read(java.nio.file.Files.readAllBytes(output),SaveAuditCommand.RetiredObserverReport.class);
        org.junit.jupiter.api.Assertions.assertEquals("51",report.audit().firstUntypedRecords().getFirst().nativeId());
        org.junit.jupiter.api.Assertions.assertEquals(2,report.audit().financial().first().streamingCoverage().passes());
        org.junit.jupiter.api.Assertions.assertFalse(report.financialCertified());
        org.junit.jupiter.api.Assertions.assertEquals(1,command.run("audit-retired-xfma","--inputs",request.toString(),"--output",output.toString()));
    }

}
