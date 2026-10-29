package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Relocation;
import org.xar.ck3.control.build.CompleteSourceGraph.SelectedFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Real Source08 producers retire a renamed test only under both original and current owner authorities. */
final class Source08TestRenamePipelineTest {
    @TempDir Path temporary;
    private static final String NEW="local-service/src/test/java/org/example/ExplicitConsumerRegression.java";
    private record Renamed(Source08Assembly.Input input,FileRef originalAuthority,FileRef finalAuthority,
            FileRef finalBody,List<FileRef> baseline) { }

    private Renamed fixture()throws IOException {
        var fixture=SourceRelocationTestSupport.fixture(temporary);var original=fixture.input();
        var previous=original.relocations().get(1);
        var originalMoves=original.relocations().stream().map(move->new SourceRelocationTestSupport.Move(
                move.oldTargetRelative(),move==previous?NEW:move.newTargetRelative(),move.sourceRef())).toList();
        var originalFiles=fixture.currentFiles().stream().map(row->new SelectedFile(
                row.targetRelative().equals(previous.newTargetRelative())?NEW:row.targetRelative(),row.sourceRef())).toList();
        FileRef originalAuthority=SourceRelocationTestSupport.json(temporary.resolve("original-rename-authority.json"),
                new SourceRelocationTestSupport.Owner("xar.source08.test-rename-authority/v1",original.machineId(),
                        "/root/planner_owner",originalFiles,originalMoves));
        FileRef finalBody=SourceRelocationTestSupport.write(temporary.resolve("ExplicitConsumerRegression.java"),
                "package org.example; public final class ExplicitConsumerRegression { public static final int ORIGINAL_CASES=2; }\n");
        FileRef finalAuthority=SourceRelocationTestSupport.json(temporary.resolve("current-test-owner.json"),
                new SourceRelocationTestSupport.Owner("xar.java.effective-source-selection/v1",original.machineId(),
                        "/root/parity_ci",List.of(new SelectedFile(NEW,finalBody)),List.of()));
        var moves=new ArrayList<Relocation>();
        for(var move:originalMoves) moves.add(move.oldTargetRelative().equals(previous.oldTargetRelative())
                ?new Relocation(move.oldTargetRelative(),NEW,move.sourceRef(),originalAuthority,finalBody,finalAuthority,NEW)
                :new Relocation(move.oldTargetRelative(),move.newTargetRelative(),move.sourceRef(),originalAuthority));
        var owners=List.of(new Source08Assembly.OwnerInput("rename-original","/root/planner_owner",
                CompleteSourceGraph.Component.COMMON,Source08Assembly.TargetScope.REACTOR_ONLY,originalAuthority),
                new Source08Assembly.OwnerInput("rename-final","/root/parity_ci",CompleteSourceGraph.Component.COMMON,
                        Source08Assembly.TargetScope.REACTOR_ONLY,finalAuthority));
        var input=new Source08Assembly.Input(Source08Assembly.RELOCATION_INPUT_SCHEMA,original.machineId(),original.observedAtUtc(),
                original.plan16RequestRef(),original.source07RequestRef(),original.profile(),original.modules(),owners,
                List.of(new SourceGraphPlanProducer.Winner(NEW,"rename-final")),moves);
        return new Renamed(input,originalAuthority,finalAuthority,finalBody,fixture.originals());
    }

    @Test void actualAssemblyPlanResolveMaterializerAndAuditKeepOnlyExactRenamedTestBody()throws Exception {
        var fixture=fixture();var input=SourceRelocationTestSupport.json(temporary.resolve("input.json"),fixture.input());
        Path request=temporary.resolve("request.json"),audit=temporary.resolve("assembly-audit.json"),output=temporary.resolve("plan.json");
        Source08Assembly.main(new String[]{input.path(),request.toString(),audit.toString()});
        SourceGraphPlanProducer.main(new String[]{request.toString(),output.toString()});
        var plan=CompleteSourceGraph.readPlan(FileRef.measure(output));var proof=CompleteSourceGraph.resolve(plan);
        assertEquals(fixture.baseline(),CompleteSourceGraph.baselineFiles(plan));
        assertFalse(proof.files().stream().anyMatch(row->row.targetRelative().equals(SourceRelocationTestSupport.CURRENT_OLD)));
        assertEquals(fixture.finalBody(),proof.files().stream().filter(row->row.targetRelative().equals(NEW)).findFirst().orElseThrow().sourceRef());
        Path materialized=temporary.resolve("materialized");var pins=SourceRelocationTestSupport.copyFinal(plan,materialized);
        CompleteSourceGraphMaterializer.verifyCanonical(plan,materialized,pins);
        assertEquals(pins,CompleteSourceGraph.verifyMaterialized(plan,materialized).sourcePins());
        assertFalse(Files.exists(materialized.resolve(SourceRelocationTestSupport.CURRENT_OLD)));
        assertEquals(Files.readString(Path.of(fixture.finalBody().path())),Files.readString(materialized.resolve(NEW)));
        var recorded=ControlBuild.strictMapper().readValue(Files.readAllBytes(audit),Source08Assembly.Audit.class);
        assertFalse(recorded.compiled());assertFalse(recorded.sourceBodiesCopied());
        assertEquals(plan,ControlBuild.strictMapper().readValue(CompleteSourceGraph.encodePlan(plan),CompleteSourceGraph.Plan.class));
        input.verify();fixture.originalAuthority().verify();fixture.finalAuthority().verify();
    }

    @Test void mainRenameRoleChangeWrongOriginalAndWrongCurrentOwnerCannotRetireSource()throws Exception {
        var fixture=fixture();var request=Source08Assembly.prepare(fixture.input());
        var plan=SourceGraphPlanProducer.produce(SourceRelocationTestSupport.json(temporary.resolve("request.json"),request));
        var first=plan.relocations().getFirst();var renamed=plan.relocations().get(1);
        assertThrows(IllegalArgumentException.class,()->new Relocation(first.oldTargetRelative(),
                "local-service/src/main/java/org/example/Renamed.java",first.sourceRef(),first.selectionRef()));
        assertThrows(IllegalArgumentException.class,()->new Relocation(renamed.oldTargetRelative(),
                "local-service/src/main/java/org/example/ExplicitConsumerRegression.java",renamed.sourceRef(),renamed.selectionRef()));
        assertThrows(IllegalArgumentException.class,()->new Relocation(renamed.oldTargetRelative(),
                renamed.oldTargetRelative(),renamed.sourceRef(),renamed.selectionRef()));
        FileRef wrong=SourceRelocationTestSupport.write(temporary.resolve("different.java"),"different exact original bytes");
        var wrongSource=new ArrayList<>(plan.relocations());wrongSource.set(1,new Relocation(renamed.oldTargetRelative(),NEW,
                wrong,renamed.selectionRef(),renamed.finalSourceRef(),renamed.finalSelectionRef(),NEW));
        assertThrows(IOException.class,()->CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan,wrongSource)));
        var wrongOwner=new ArrayList<>(plan.relocations());wrongOwner.set(1,new Relocation(renamed.oldTargetRelative(),NEW,
                renamed.sourceRef(),renamed.selectionRef(),renamed.finalSourceRef(),renamed.selectionRef(),NEW));
        assertThrows(IOException.class,()->CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan,wrongOwner)));
        var wrongFinal=new ArrayList<>(plan.relocations());wrongFinal.set(1,new Relocation(renamed.oldTargetRelative(),NEW,
                renamed.sourceRef(),renamed.selectionRef(),wrong,renamed.finalSelectionRef(),NEW));
        assertThrows(IOException.class,()->CompleteSourceGraph.resolve(SourceRelocationTestSupport.withMoves(plan,wrongFinal)));
    }
}
