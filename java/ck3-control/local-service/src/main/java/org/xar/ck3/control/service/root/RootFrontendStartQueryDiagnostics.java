package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendStartRootQueries;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.GameplayStartEffects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.RootMcpBridgeDiagnostics;

/** Source-bound projection from the actual per-Game Start effect's sole query journal, never another cached ROOT read. */
public final class RootFrontendStartQueryDiagnostics {
    public record Sources(ExactRef implementation,ExactRef formatter,ExactRef custody) {
        public Sources {for(ExactRef ref:List.of(implementation,formatter,custody))
            if(ref.bytes()<=0)throw new IllegalArgumentException("actual selected Start query diagnostic sources required");}
    }
    private record InstalledPair(GameplayStartEffects effects,RootFrontendStartQueryDiagnostics diagnostics){ }
    public static final class Prepared {
        private final Sources sources;private final RootRuntimeStorageGuard storage;
        private final Map<RootRuntimeContext,InstalledPair> installed=new IdentityHashMap<>();
        public Prepared(Sources sources,RootRuntimeStorageGuard sameActualStorage){this.sources=Objects.requireNonNull(sources);storage=Objects.requireNonNull(sameActualStorage);}
        /** Same prepared source definition installs one actual journal for each genuine new physical Root context. */
        public synchronized RootFrontendStartQueryDiagnostics install(RootRuntimeContext context,GameplayStartEffects effects)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(effects);InstalledPair previous=installed.get(context);
            if(previous!=null){if(previous.effects()!=effects)throw new IOException("same Root context cannot replace its actual Start effect/journal");return previous.diagnostics();}
            if(installed.size()>=64)throw new IOException("bounded actual Start diagnostic installations require original reconciliation");
            var root=context.finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);
            var journal=new FrontendStartRootQueries(context,root,storage);effects.bindRootQueries(journal);
            var actual=new RootFrontendStartQueryDiagnostics(context,effects,journal,sources);installed.put(context,new InstalledPair(effects,actual));return actual;
        }
    }
    private final RootRuntimeContext owner;private final GameplayStartEffects effects;
    private final FrontendStartRootQueries journal;private final Sources sources;
    private RootFrontendStartQueryDiagnostics(RootRuntimeContext owner,GameplayStartEffects effects,FrontendStartRootQueries journal,Sources sources){
        this.owner=owner;this.effects=effects;this.journal=journal;this.sources=sources;
    }
    public Sources sources(){return sources;}
    public ExactRef implementationSource(){return sources.implementation();}
    /** RootMcpBridgeDiagnostics already owns the physical diagnostic/source guard around this exact callback. */
    public Optional<Obj> capture(RootRuntimeContext current,ContinuityStorePort.Session same,DriverSnapshotFacts.Known actualDriver,
            BridgeDiagnostics.Received actualReceived)throws IOException {
        if(current!=owner||effects.rootQueries()!=journal)throw new IOException("frontend diagnostic crossed its sole installed Root/effect/query journal");
        Objects.requireNonNull(actualDriver);Objects.requireNonNull(actualReceived);owner.writer().requireSession(same);
        return owner.adopted().authority().withFrozenFacts(same,frozen->{
            if(frozen.state()!=actualDriver||!actualDriver.stamp().game().equals(owner.game().generation()))
                throw new IOException("frontend diagnostic lost the exact actually held Driver");
            var transport=owner.transport();owner.adopted().producer().requireSameTransport(transport,owner.source());
            var before=transport.diagnostics();RootMcpBridgeDiagnostics.requireSameReceived(actualReceived.original(),before);
            var session=actualReceived.session().orElseThrow(()->new IOException("actual frontend diagnostic received transport session absent"));
            if(!session.game().equals(owner.game().generation())||!session.sessionId().equals(owner.game().sessionId())
                    ||!session.machineId().equals(owner.source().machineId())||!actualReceived.pipeName().equals(transport.pipeName()))
                throw new IOException("frontend diagnostic crossed its actual physical transport/source/session");
            var captured=journal.capture(same);Optional<Obj> field=captured.field();journal.requireCurrent(same,captured);
            if(effects.rootQueries()!=journal)throw new IOException("actual frontend diagnostic producer changed during capture");
            owner.writer().requireSession(same);RootMcpBridgeDiagnostics.requireSameReceived(before,transport.diagnostics());return field;
        });
    }
}
