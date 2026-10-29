package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;

/** Real selected-file custody only. No Runtime Inputs, native Bound, plan, storage admission or Prepared positive is fabricated. */
class RootLifecycleSourcesFactoryTest {
    @TempDir Path root;
    private static final String HELPER="local-service/src/main/java/org/xar/ck3/control/service/root/RootLifecycleSourcesFactory.java";
    private static final String PRIVATE="application/src/main/java/org/xar/ck3/control/application/driver/DriverPreclockExpectationProducer.java";
    @Test void actualSelectorFeedsIdenticalDeclaredPublicAndPackagePrivateWinners()throws IOException {
        var helper=row(HELPER,"RootLifecycleSourcesFactory.java","actual selected public helper source");
        var producer=row(PRIVATE,"DriverPreclockExpectationProducer.java","actual selected package-private app producer");
        var index=List.of(helper,producer);var selected=new RootRuntimeSelectedSources(index);
        assertEquals(helper.sourceRef(),RootLifecycleSourcesFactory.selectJava(selected,index,HELPER,Optional.of(RootLifecycleSourcesFactory.class)));
        assertEquals(producer.sourceRef(),RootLifecycleSourcesFactory.selectJava(selected,index,PRIVATE,Optional.empty()));
        assertEquals(2,selected.retainedSources().size());selected.requireCurrent();
    }
    @Test void anotherRuntimeDeclaredBodyOrMissingOrDuplicateDeclarationCannotBorrowTheSelectedWinner()throws IOException {
        var actual=row(PRIVATE,"DriverPreclockExpectationProducer.java","actual selected package-private app producer");
        var other=row(PRIVATE,"OtherProducer.java","different runtime declared app producer");
        var selected=new RootRuntimeSelectedSources(List.of(actual));
        assertThrows(IOException.class,()->RootLifecycleSourcesFactory.selectJava(selected,List.of(other),PRIVATE,Optional.empty()));
        assertThrows(IOException.class,()->RootLifecycleSourcesFactory.selectJava(selected,List.of(),PRIVATE,Optional.empty()));
        assertThrows(IOException.class,()->RootLifecycleSourcesFactory.selectJava(selected,List.of(actual,actual),PRIVATE,Optional.empty()));
        assertThrows(IOException.class,()->RootLifecycleSourcesFactory.selectJava(selected,List.of(actual),PRIVATE,Optional.of(RootLifecycleSourcesFactory.class)));
        assertEquals(actual.sourceRef(),RootLifecycleSourcesFactory.selectJava(selected,List.of(actual),PRIVATE,Optional.empty()));
    }
    private SelectedSource row(String target,String filename,String body)throws IOException {
        Path source=root.resolve(filename);Files.writeString(source,body);FileRef exact=FileRef.measure(source);
        return new SelectedSource(target,new ExactRef(exact.path(),exact.bytes(),exact.sha256()));
    }
}
