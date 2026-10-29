package org.xar.ck3.control.service.root;

import java.util.Objects;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Service bridge executes the real shared Main; it supplies no Game, dates, frame, authority or historical inputs. */
public final class RootStartupHostActualInputs implements RootHostBatchAndCloseActualTest.InputsProducer {
    @Override public void withActualInputs(RootHostBatchAndCloseActualTest.InputsWork work)throws Exception {
        Objects.requireNonNull(work);
        var request=RootStartupInputsProducer.fromEnvironment(System.getenv());
        RootStartupInputsProducer.execute(request,new OrdinarySessionHost(),new PublicMcpHost(),actual->{
            var reads=actual.readInputs();
            if(reads.current()!=actual.original()||reads.core()!=actual.core())
                throw new java.io.IOException("actual startup changed its initial current before input delivery");
            work.consume(new RootHostBatchAndCloseActualTest.Inputs(actual.core(),actual.original(),actual.prepared(),
                    actual.host(),actual.nextBatch(),actual.deadline(),request.closeWait(),actual::catalogFor,actual::closeOriginal));
        });
    }
}
