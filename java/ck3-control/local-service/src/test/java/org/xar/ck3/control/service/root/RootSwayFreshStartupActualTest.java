package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.sway.SwayFormalCodec;
import org.xar.ck3.control.application.planning.sway.SwayFormalState;
import org.xar.ck3.control.application.planning.sway.SwaySessionInputs;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Actual role10 DATA -> Main -> canonical entry -> first Sway domain. Missing live inputs fail explicitly. */
public final class RootSwayFreshStartupActualTest {
    @Test void actualFreshRole10CreatesOnlyNewAutomationHistoryFromTheOriginalEntryBeforeOrdinaryReads() throws Exception {
        var request=RootStartupInputsProducer.fromEnvironment(System.getenv());
        RootStartupInputsProducer.execute(request,new OrdinarySessionHost(),new PublicMcpHost(),actual->{
            var original=RootSwaySourcesFactory.readExact(actual.privateInputs().data(RootRuntimeDefinitionModel.DataRole.SWAY_CONFIGURATION));
            assertInstanceOf(RootRuntimeDomainAssembly.SwayFresh.class,original.initialization(),"this regression requires actual explicit fresh role10 inputs");
            var inputs=actual.readInputs();var context=inputs.catalog().context();
            assertSame(actual.original(),inputs.current());assertSame(actual.core(),inputs.core());
            context.writer().locked(same->{
                var body=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.SWAY));
                var ledger=SwayFormalCodec.decode(body.canonicalBody());
                var entry=RootInitialEpisodeProof.replayOriginal(context,same,ledger.originalMigrationInput());
                assertEquals(context.game().machineId(),ledger.machineId());assertEquals(entry.episodeId(),ledger.episodeRunId());
                assertTrue(ledger.pending().isEmpty());assertTrue(ledger.resolved().isEmpty());assertTrue(ledger.previous().isEmpty());
                assertTrue(ledger.schedule().isEmpty());assertTrue(ledger.imported().isEmpty());assertTrue(ledger.activeStage().isEmpty());
                assertArrayEquals(body.canonicalBody(),SwayFormalCodec.encode(SwayFormalCodec.decode(body.canonicalBody())));
                assertEquals(ledger.originalMigrationInput(),entry.basis());
                var stateBefore=same.head();var frameBefore=context.transport().latestObservedSnapshot().orElseThrow();
                var projected=SwaySessionInputs.project(ledger,entry.observation());
                assertTrue(projected.ledger().pending().isEmpty());assertTrue(projected.ledger().resolved().isEmpty());
                assertEquals(stateBefore,same.head());
                assertTrue(Arrays.equals(frameBefore.originalPacket(),context.transport().latestObservedSnapshot().orElseThrow().originalPacket()),"retained entry/domain interpretation must not issue a native query");
                assertTrue(Files.notExists(original.legacyLedger(),LinkOption.NOFOLLOW_LINKS));
                assertTrue(Files.notExists(original.legacyLedger().resolveSibling("ordinary-sway-schedule-v1.json"),LinkOption.NOFOLLOW_LINKS));
                var selected=actual.privateInputs().sourceIndex();
                for(String suffix:List.of("/RootInitialEpisodeProof.java","/RootRuntimeDomainAssembly.java","/SwayCanonicalDomain.java","/SwayRuntimeInstaller.java")) {
                    var exact=selected.stream().filter(row->row.targetRelative().endsWith(suffix)).findFirst().orElseThrow().sourceRef();
                    assertTrue(body.reference().producerSources().contains(exact),"actual fresh producer source must be in the same Sway domain closure: "+suffix);
                }
                assertFalse(SwayFormalState.historicalPendingUnresolved(ledger));return null;
            });
        });
    }
}
