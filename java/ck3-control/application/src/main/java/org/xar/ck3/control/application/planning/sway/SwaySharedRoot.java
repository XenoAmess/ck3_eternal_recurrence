package org.xar.ck3.control.application.planning.sway;

import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Typed result view over the identical installed contract. It never constructs a native read registration. */
public final class SwaySharedRoot {
    private interface Access {
        PlanningReadResult<Obj> read(PlanningReadPort reads,PlanningReadRequest request);
        PlanningReadResult<Obj> read(PlanningReadPort reads,Session same,PlanningReadRequest request);
    }
    private final ReadContract<?> actual;
    private final Access access;
    private final Obj arguments;
    private <T> SwaySharedRoot(ReadContract<T> actual,Function<T,Obj> view,Obj arguments,Optional<PlanningReadPort> admittedRootPort) {
        this.actual=Objects.requireNonNull(actual);Objects.requireNonNull(view);
        this.arguments=Objects.requireNonNull(arguments);
        Objects.requireNonNull(admittedRootPort);
        org.xar.ck3.control.contracts.StrictJson.require(actual.operation().equals(OrdinarySwayReadSource.ROOT),"actual shared ROOT operation required");
        access=new Access() {
            private PlanningReadResult<Obj> project(PlanningReadResult<T> result) {
                if(result instanceof PlanningReadResult.Known<T> known){requirePublicCapture(known.receipt());return new PlanningReadResult.Known<>(Objects.requireNonNull(view.apply(known.value())),known.receipt(),known.originalReceipt());}
                if(result instanceof PlanningReadResult.Unavailable<T> missing)return new PlanningReadResult.Unavailable<>(missing.reason(),missing.original());
                throw new IllegalStateException("unhandled typed ROOT result");
            }
            @Override public PlanningReadResult<Obj> read(PlanningReadPort reads,PlanningReadRequest request){return project(admittedRootPort.orElse(Objects.requireNonNull(reads)).read(actual,request));}
            @Override public PlanningReadResult<Obj> read(PlanningReadPort reads,Session same,PlanningReadRequest request){return project(admittedRootPort.orElse(Objects.requireNonNull(reads)).read(same,actual,request));}
        };
    }
    public static SwaySharedRoot finance(ReadContract<FinanceReadContracts.Packet> actual,PlanningReadPort actualCanonicalRootPort){return new SwaySharedRoot(actual,FinanceReadContracts.Packet::originalResult,FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),Optional.of(Objects.requireNonNull(actualCanonicalRootPort)));}
    /** Existing explicit Obj producers retain their exact registration; source compatibility grants no new catalog membership. */
    public static SwaySharedRoot original(ReadContract<Obj> actual){return new SwaySharedRoot(actual,value->value,new Obj(java.util.Map.of()),Optional.empty());}
    public ReadContract<?> actualContract(){return actual;}
    public String contractId(){return actual.contractId();}
    public OperationKey operation(){return actual.operation();}
    public Obj arguments(){return arguments;}
    public static void requirePublicCapture(PlanningReadReceipt original) {
        if(original.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID))org.xar.ck3.control.contracts.StrictJson.require(
                FinanceReadContracts.rootCapture(original.request().arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY,"Sway ROOT consumers require the actual public current capture, never an internal preclock original");
    }
    public PlanningReadResult<Obj> read(PlanningReadPort reads,PlanningReadRequest request){return access.read(reads,request);}
    public PlanningReadResult<Obj> read(PlanningReadPort reads,Session same,PlanningReadRequest request){return access.read(reads,same,request);}
}
