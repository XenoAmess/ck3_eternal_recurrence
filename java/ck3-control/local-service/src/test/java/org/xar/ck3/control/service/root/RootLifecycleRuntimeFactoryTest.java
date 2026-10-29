package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;

/** Public preparation data cannot replace original producer closure or exact configured roots.
 * These tests create no managed Game, private Lease, SeedStore, Root or storage admission. */
final class RootLifecycleRuntimeFactoryTest {
    @TempDir Path temporary;
    private ExactRef ref(String name) {return new ExactRef(temporary.resolve(name).toString(),1,"a".repeat(64));}
    private RootLifecycleRuntimeFactory.Sources sources(List<ExactRef> producers) {
        return new RootLifecycleRuntimeFactory.Sources(producers,ref("timeline.cpp"),ref("close.cpp"),ref("prisoner.cpp"),
                ref("originals.java"),ref("timeline.java"),ref("prisoner.java"),ref("composite.java"),ref("replay.java"));
    }
    @Test void originalPreparationRejectsAnEmptyOrAmbiguousProducerClosureBeforeAnyRootIsConstructed() {
        ExactRef source=ref("producer.java");var caller=new ArrayList<>(List.of(source));var value=sources(caller);caller.clear();
        assertEquals(List.of(source),value.naturalProducers());
        assertThrows(IllegalArgumentException.class,()->sources(List.of()));
        assertThrows(IllegalArgumentException.class,()->sources(List.of(source,source)));
        assertThrows(UnsupportedOperationException.class,()->value.naturalProducers().clear());
    }
    @Test void configuredLifecyclePathsAndClockBudgetRemainExplicitAndFinite() {
        Set<String> handler=Set.of("actual-life-advance-handler");
        assertDoesNotThrow(()->new RootLifecycleRuntimeFactory.Configuration(temporary,temporary,temporary,temporary,handler,Duration.ofSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->new RootLifecycleRuntimeFactory.Configuration(temporary.resolve("child/.."),temporary,temporary,temporary,handler,Duration.ofSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->new RootLifecycleRuntimeFactory.Configuration(temporary,temporary,temporary,temporary,Set.of(),Duration.ofSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->new RootLifecycleRuntimeFactory.Configuration(temporary,temporary,temporary,temporary,Set.of(" "),Duration.ofSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->new RootLifecycleRuntimeFactory.Configuration(temporary,temporary,temporary,temporary,handler,Duration.ZERO));
        assertThrows(IllegalArgumentException.class,()->new RootLifecycleRuntimeFactory.Configuration(temporary,temporary,temporary,temporary,handler,Duration.ofMinutes(6)));
    }
}
