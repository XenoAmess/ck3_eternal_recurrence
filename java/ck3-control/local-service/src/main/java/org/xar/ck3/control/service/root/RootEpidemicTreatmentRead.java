package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.capabilities.family.EpidemicTreatmentPresenceQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Prepared source definitions are retained before Core; each physical Game installs one actual read. */
public final class RootEpidemicTreatmentRead {
    public record Sources(ExactRef nativeDefinition,ExactRef decoder,List<ExactRef> completeProducers) {
        public Sources {
            Objects.requireNonNull(nativeDefinition);Objects.requireNonNull(decoder);completeProducers=List.copyOf(completeProducers);
            StrictJson.require(nativeDefinition.bytes()>0&&decoder.bytes()>0&&completeProducers.size()<=64
                    &&completeProducers.stream().distinct().count()==completeProducers.size()
                    &&completeProducers.contains(nativeDefinition)&&completeProducers.contains(decoder),
                    "actual complete treatment native and decoder source closure required");
        }
    }
    public static final class Prepared {
        private final Sources sources;
        private final Map<RootRuntimeContext,RootEpidemicTreatmentRead> installed=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(Sources sources) {this.sources=Objects.requireNonNull(sources);}
        public Sources sources(){return sources;}
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"treatment prepared definitions bind Core once");core=Objects.requireNonNull(actual);
        }
        public synchronized RootEpidemicTreatmentRead install(RootRuntimeContext context) {
            Objects.requireNonNull(context);StrictJson.require(core!=null&&context.core()==core,"treatment definitions lost the exact bound Core");
            var prior=installed.get(context);if(prior!=null)return prior;
            StrictJson.require(installed.size()<64,"bounded physical treatment installations exhausted");
            var actual=new RootEpidemicTreatmentRead(context,sources);installed.put(context,actual);return actual;
        }
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final ReadContract<Obj> contract;
    private RootEpidemicTreatmentRead(RootRuntimeContext context,Sources sources) {
        this.context=Objects.requireNonNull(context);this.sources=Objects.requireNonNull(sources);
        contract=EpidemicTreatmentPresenceQueries.contract(sources.nativeDefinition(),request->{
            try {
                context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
                StrictJson.require(context.readCatalog().containsIdentity(contract())&&request.source().equals(context.source())
                        &&request.sessionId().equals(context.game().sessionId())&&request.before().game().equals(context.game().generation()),
                        "treatment read is not the same installed physical Root contract");
            }catch(IOException unavailable){throw new java.io.UncheckedIOException(unavailable);}
        });
    }
    public Sources sources(){return sources;}
    public ReadContract<Obj> contract(){return contract;}
    public List<RootReadContractCatalog.InstalledRead> installedReads(){return List.of(new RootReadContractCatalog.InstalledRead(contract,sources.decoder()));}
    public void requireContext(RootRuntimeContext actual){StrictJson.require(context==actual,"treatment observation crossed Root context");}
    public PlanningReadResult.Known<Obj> read(Session same,Complete actual,java.math.BigInteger expectedRevision,Instant deadline)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(deadline);
        StrictJson.require(actual.source().equals(context.source())&&actual.sessionId().equals(context.game().sessionId())
                &&actual.identity().game().equals(context.game().generation())&&context.readCatalog().containsIdentity(contract),
                "treatment query requires the actual held current Root frame and installed read");
        var request=new PlanningReadRequest(actual.identity(),actual.source(),actual.sessionId(),contract.operation(),
                EpidemicTreatmentPresenceQueries.arguments(expectedRevision),deadline);
        var result=context.reads().read(same,contract,request);context.writer().requireSession(same);
        if(result instanceof PlanningReadResult.Known<Obj> known)return known;
        throw new IOException("actual native treatment presence read unavailable");
    }
}

