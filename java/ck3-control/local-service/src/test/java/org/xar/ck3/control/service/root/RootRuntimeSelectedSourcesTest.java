package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.RootMcpPlanning;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.OriginalKind;

/** Historical source references reach their real typed consumers as DATA after file changes. */
class RootRuntimeSelectedSourcesTest {
    @TempDir Path root;
    private static final String TARGET="local-service/src/main/java/org/xar/ck3/control/service/root/ActualProducer.java";
    @Test void actualSelectedProducerAndOriginalProvenanceAreRetainedWithoutSelectingUnconsumedFiles()throws IOException {
        Path body=root.resolve("ActualProducer.java"),unused=root.resolve("Unused.java"),nativeFile=root.resolve("actual_native.cpp");
        Files.writeString(body,"actual selected source");Files.writeString(unused,"unused");Files.writeString(nativeFile,"actual native source");
        var selected=new RootRuntimeSelectedSources(List.of(row(TARGET,body),row(TARGET.replace("ActualProducer","Unused"),unused)));
        assertEquals(exact(body),selected.javaTarget(TARGET));assertEquals(exact(nativeFile),selected.original(FileRef.measure(nativeFile),OriginalKind.NATIVE_CPP));
        assertEquals(2,selected.retainedSources().size());
        var historicalNative=FileRef.measure(nativeFile);Files.delete(nativeFile);
        Files.writeString(unused,"an unconsumed winner is not a runtime body");selected.requireCurrent();
        assertEquals(new ExactRef(historicalNative.path(),historicalNative.bytes(),historicalNative.sha256()),
                selected.original(historicalNative,OriginalKind.NATIVE_CPP));
    }
    @Test void duplicateOrMissingWinnerAndWrongProducerKindAreRefused()throws IOException {
        Path body=root.resolve("ActualProducer.java");Files.writeString(body,"actual selected source");var actual=row(TARGET,body);
        assertThrows(IOException.class,()->new RootRuntimeSelectedSources(List.of(actual,actual)));
        var selected=new RootRuntimeSelectedSources(List.of(actual));
        assertThrows(IOException.class,()->selected.javaTarget(TARGET.replace("ActualProducer","Missing")));
        assertThrows(IOException.class,()->selected.original(FileRef.measure(body),OriginalKind.NATIVE_CPP));
    }
    @Test void selectedSameBytesReplacementDoesNotCreateARecurringIdentityGate()throws IOException {
        Path body=root.resolve("ActualProducer.java"),replacement=root.resolve("replacement.java");Files.writeString(body,"actual selected source");
        var selected=new RootRuntimeSelectedSources(List.of(row(TARGET,body)));selected.javaTarget(TARGET);
        Files.copy(body,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(body));Files.move(replacement,body,StandardCopyOption.REPLACE_EXISTING);
        selected.requireCurrent();assertEquals(exact(body),selected.javaTarget(TARGET));
    }
    @Test void changedHistoricalProducerBytesDoNotInvalidateStoredProvenance()throws IOException {
        Path body=root.resolve("ActualProducer.java");Files.writeString(body,"actual selected source");var selected=new RootRuntimeSelectedSources(List.of(row(TARGET,body)));
        ExactRef original=selected.javaTarget(TARGET);
        Files.writeString(body,"different selected source");assertEquals(original,selected.javaTarget(TARGET));selected.requireCurrent();
        Files.delete(body);assertEquals(original,selected.javaTarget(TARGET));selected.requireCurrent();
    }
    @Test void historicalPublicPlannerReferenceReachesTheRealTypedBindingAfterItsSourceFileDisappears()throws Exception {
        String target="local-service/src/main/java/org/xar/ck3/control/service/mcp/RootMcpPlanning.java";
        Path historicalFile=root.resolve("RootMcpPlanning.java");Files.writeString(historicalFile,"historical planner source DATA");
        var historical=row(target,historicalFile);var selected=new RootRuntimeSelectedSources(List.of(historical));
        Files.delete(historicalFile);
        assertEquals(historical.sourceRef(),selected.javaSourceAt(target,RootMcpPlanning.class));
        assertEquals(historical.sourceRef(),selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMcpPlanning.class));
        selected.requireCurrent();assertEquals(List.of(historical.sourceRef()),selected.retainedSources());
        assertThrows(IOException.class,()->selected.javaSourceAt(target.replace("RootMcpPlanning","Other"),RootMcpPlanning.class));
        assertThrows(IOException.class,()->selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,String.class));
        RawJson response=new RawJson("{\"historical_data\":true}".getBytes(StandardCharsets.UTF_8));
        var calls=new AtomicInteger();var registry=new PublicBindings();
        var planner=new RootMcpPlanning(new RootMcpPlanning.Backend() {
            @Override public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(true,false,List.of());}
            @Override public RawJson plan(PublicPlanningCodec.PlanRequest request){calls.incrementAndGet();return response;}
            @Override public RawJson execute(PublicPlanningCodec.ExecuteRequest request){throw new AssertionError("no execution authority in a source-DATA test");}
        });
        assertEquals(1,planner.register(registry,historical.sourceRef()).size());registry.freeze(Set.of(PublicMethod.PLAN_TURN));
        var bound=registry.lookup(PublicMethod.PLAN_TURN).orElseThrow();
        assertEquals(historical.sourceRef(),bound.info().target().orElseThrow().implementationSource());
        assertEquals(response,bound.invoke(new PublicBindings.Missing()));assertEquals(1,calls.get());
    }
    private static SelectedSource row(String target,Path source)throws IOException{return new SelectedSource(target,exact(source));}
    private static ExactRef exact(Path source)throws IOException{FileRef actual=FileRef.measure(source);return new ExactRef(actual.path(),actual.bytes(),actual.sha256());}
}
