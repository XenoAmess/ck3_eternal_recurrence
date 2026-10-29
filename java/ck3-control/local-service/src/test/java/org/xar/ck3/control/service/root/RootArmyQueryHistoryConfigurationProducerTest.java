package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;

/** The existing actual full-configuration fixture supplies every private input. Missing inputs fail.
 * These tests neither invent a NativePlan nor create an allow-all storage authority. */
class RootArmyQueryHistoryConfigurationProducerTest {
    @TempDir Path temporary;

    @Test void actualTotalProducerPassesOneQualifiedHistoryObjectToEveryPreparedConsumer()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var same=input.queryHistory();same.requireSame(input.plan(),input.clock());
        assertEquals(input.settings().configuration().queryHistorySettings(),same.original());
        assertSame(same,actual.definitions().catalogFactory().sources().remainingDomains().strengths().queryHistorySettings());
        assertSame(input.operatorAuthority(),actual.factory().retainedInput().operatorAuthority());
        var retained=List.copyOf(input.selected().retainedSources());
        var producer=expected(input,"local-service",RootArmyQueryHistoryConfigurationProducer.class);
        var decoder=expected(input,"native-transport",OriginalDriverQueryHistorySettings.class);
        assertTrue(retained.contains(producer));assertTrue(retained.contains(decoder));
        input.plan().sources().requireLoadedClass(RootArmyQueryHistoryConfigurationProducer.class);
        input.plan().sources().requireLoadedClass(OriginalDriverQueryHistorySettings.class);
        actual.factory().requireDefinitions(actual.definitions().catalogFactory().sources());
    }

    @Test void actualIndependentRequestReproducesTheSameDocumentAndFiniteClosedOutputQuote()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var original=input.queryHistory();var refs=original.document().sourceRefs();
        var prepared=RootArmyQueryHistoryConfigurationProducer.prepare(refs.configurationOriginal(),refs.producerOriginal(),input.plan(),input.clock());
        assertEquals(original.document(),prepared.document());
        assertArrayEquals(OriginalDriverQueryHistorySettings.encode(original.document()),prepared.bytes());
        byte[] copy=prepared.bytes();copy[0]^=1;
        assertArrayEquals(OriginalDriverQueryHistorySettings.encode(original.document()),prepared.bytes());
        var quote=prepared.quote(temporary.resolve("army-query-history-settings.json"));
        assertEquals(RootBootstrapOutputContract.Kind.ARMY_QUERY_HISTORY_CONFIGURATION,quote.kind());
        assertEquals(prepared.bytes().length,quote.bytes());
        assertTrue(quote.bytes()<=OriginalDriverQueryHistorySettings.MAX_BYTES);
        prepared.requireCurrent();
        // No files, binding, issuer card or store is manufactured from the quote.
        assertFalse(java.nio.file.Files.exists(temporary.resolve("army-query-history-settings.json")));
    }

    @Test void commandRejectsMissingOrAmbiguousModesBeforeReadingOrWritingAnyOriginal() {
        assertThrows(IllegalArgumentException.class,()->RootArmyQueryHistoryConfigurationProducer.main(new String[0]));
        String[] args=new String[11];java.util.Arrays.fill(args,"invalid");args[0]="CREATE_NEW";
        assertThrows(IllegalArgumentException.class,()->RootArmyQueryHistoryConfigurationProducer.main(args));
        args[0]="QUOTE";
        assertThrows(IllegalArgumentException.class,()->RootArmyQueryHistoryConfigurationProducer.main(args));
    }

    private static ExactRef expected(RootDriverProductSourcesFactory.Input input,String module,Class<?> type)throws IOException {
        String target=module+"/src/main/java/"+type.getName().replace('.','/')+".java";
        var found=input.inputs().sourceIndex().stream().filter(row->row.targetRelative().equals(target)).toList();
        if(found.size()!=1)throw new IOException("required actual producer/reader is missing from the original source index: "+target);
        return found.getFirst().sourceRef();
    }
}
