package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.InvocationData;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.OriginalError;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.RawHistoryRow;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.Source;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Source-list DATA boundaries only. No Context, source issuer, private candidate or Root exists. */
final class RootPublicStepSourceClosureTest {
    private static ExactRef ref(String name){return new ExactRef("D:/test-only-source-list/"+name+".json",1,"a".repeat(64));}
    private static List<ExactRef> sources(int count){
        var result=new ArrayList<ExactRef>();for(int i=0;i<count;i++)result.add(ref("producer-"+i));return List.copyOf(result);
    }
    private static Source source(List<ExactRef> producers){
        return new Source("hire-mercenary-v1",new OriginalError("UnsupportedStepError","original error DATA"),
                Optional.empty(),Optional.empty(),ref("driver"),ref("known"),ref("native"),ref("facts"),ref("invocation"),
                ref("caller"),ref("epoch"),Optional.empty(),Optional.empty(),0,"b".repeat(64),producers);
    }
    private static RootPublicStepExecution.Read product(List<ExactRef> sources){
        return new RootPublicStepExecution.Read("source-list-data-only",operation->false,
                context->{throw new AssertionError("DATA construction cannot qualify a Root owner");},
                (request,frame,known,same,caller,archive)->{throw new AssertionError("DATA construction cannot perform a read");},sources);
    }
    @Test void completeWarSizedAndMaximumJavaClosuresSurviveProductAndFailureWireWithoutDroppingSources(){
        for(int count:List.of(71,96,DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES)){
            var producers=sources(count);assertEquals(producers,product(producers).sources());
            var source=source(producers);var row=new RawHistoryRow(1,source,Optional.empty());
            var decoded=DriverPublicExecuteFailureRowProducer.decode(row.encode());
            assertEquals(row,decoded);assertEquals(producers,decoded.source().producerSources());
            var data=new InvocationData(new OperationKey(source.command()),source.error(),Optional.empty(),Optional.empty(),
                    source.beforeDriver(),source.originalKnown(),source.nativeFrame(),source.driverFacts(),source.caller(),source.epochManifest(),
                    source.unsupportedCapabilities(),source.unresolvedAction(),source.headSequence(),source.headDigest(),producers);
            var invocation=DriverPublicExecuteFailureRowProducer.invocationJson(data);
            assertEquals(count,assertInstanceOf(OpportunityJson.Arr.class,invocation.get("producer_sources")).items().size());
            assertTrue(decoded.source().evidence().containsAll(producers));
        }
    }
    @Test void finiteClosureLimitAndDistinctSourceRequirementApplyToProductConstructorAndDurableDecoder(){
        var overflow=sources(DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES+1);
        assertThrows(IllegalArgumentException.class,()->product(overflow));
        assertThrows(IllegalArgumentException.class,()->source(overflow));
        var duplicates=new ArrayList<>(sources(71));duplicates.add(duplicates.getFirst());
        assertThrows(IllegalArgumentException.class,()->product(duplicates));
        assertThrows(IllegalArgumentException.class,()->source(duplicates));
        var valid=source(sources(71));
        var refs=new OpportunityJson.Arr(overflow.stream().map(org.xar.ck3.control.application.driver.DriverObservationEvidenceReader::reference)
                .map(OpportunityJson.Value.class::cast).toList());
        var invalid=DriverPublicExecuteFailureRowProducer.sourceJson(valid).with("producer_sources",refs);
        var row=new RawHistoryRow(1,valid,Optional.empty()).toJson().with(DriverPublicExecuteFailureRowProducer.SOURCE_FIELD,invalid);
        assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.decode(
                org.xar.ck3.control.application.driver.DriverJson.encode(row)));
    }
}
