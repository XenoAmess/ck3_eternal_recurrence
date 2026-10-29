package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.planning.military.OriginalMilitaryReadPort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Ordinary-only reuse of an actual archived current-frame read. Public explicit queries retain the original fresh port. */
public final class MilitaryCanonicalReads implements OriginalMilitaryReadPort {
    private final RootRuntimeContext current;
    private final Supplier<DriverReadHistoryPublisher> publisher;
    public MilitaryCanonicalReads(RootRuntimeContext current,Supplier<DriverReadHistoryPublisher> samePublisher) {
        this.current=Objects.requireNonNull(current);publisher=Objects.requireNonNull(samePublisher);
    }
    public <T> Optional<DriverReadHistoryPublisher.CanonicalRead<T>> find(ContinuityStorePort.Session borrowed,ReadContract<T> contract,PlanningReadRequest request)throws IOException {
        current.requireCurrent(request.deadline());current.writer().requireSession(borrowed);
        DriverReadHistoryPublisher actual=Objects.requireNonNull(publisher.get(),"ordinary reads require the actual once-bound Driver read publisher");
        if(actual.catalog()!=current.readCatalog())throw new IOException("ordinary cache belongs to another installed Root catalog");
        return actual.canonicalReadWitness(borrowed,contract,request);
    }
    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
        try{return current.withSession(same->read(same,contract,request));}
        catch(IOException|IllegalArgumentException|IllegalStateException failure){return unavailable(failure);}
    }
    @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session borrowed,ReadContract<T> contract,PlanningReadRequest request) {
        try {
            var retained=find(borrowed,contract,request);
            if(retained.isPresent()) {
                var witness=retained.orElseThrow();var original=witness.requireCurrent(borrowed,contract,request);
                T value=witness.originalContract().replay(original.receipt());
                if(!value.equals(original.value()))throw new IOException("canonical original contract replay differs from its actual value");
                return original;
            }
            return current.reads().read(borrowed,contract,request);
        }catch(IOException|IllegalArgumentException|IllegalStateException failure){return unavailable(failure);}
    }
    @Override public <T>T replayOriginal(ReadContract<T> contract,PlanningReadRequest request,PlanningReadResult.Known<T> returned) {
        try{return current.withSession(same->{
            var retained=find(same,contract,request);T value;
            if(retained.isPresent()) {
                var witness=retained.orElseThrow();var original=witness.requireCurrent(same,contract,request);
                if(!original.equals(returned))throw new IOException("returned military read differs from its actual canonical original");
                value=witness.originalContract().replay(original.receipt());
            }else {
                if(!returned.receipt().request().equals(request)||!returned.receipt().contractId().equals(contract.contractId()))
                    throw new IOException("no current canonical witness exists for this old military receipt");
                value=contract.replay(returned.receipt());
            }
            if(!value.equals(returned.value()))throw new IOException("military original model differs from pure replay");return value;
        });}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private static <T>PlanningReadResult.Unavailable<T> unavailable(Exception failure) {
        return new PlanningReadResult.Unavailable<>("actual ordinary archived-read reuse unavailable: "+failure.getMessage(),Optional.empty());
    }
}
