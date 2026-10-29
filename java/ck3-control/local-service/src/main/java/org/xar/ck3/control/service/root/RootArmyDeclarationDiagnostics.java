package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationDiagnostics;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReads;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnostics;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.RootMcpBridgeDiagnostics;

/** Actual one-field supplement producer. RootMcpBridgeDiagnostics owns the physical source guard around this callback. */
public final class RootArmyDeclarationDiagnostics {
    public record Sources(ExactRef implementation,ExactRef formatter,ExactRef custody) {
        public Sources {for(var ref:List.of(implementation,formatter,custody))StrictJson.require(ref.bytes()>0,"actual selected pending-declaration producer source required");}
    }
    private final RootRuntimeContext owner;
    private final ArmyWarReads warReads;
    private final Sources sources;
    private RootArmyDeclarationDiagnostics(RootRuntimeContext actual,ArmyWarReads reads,Sources sources) {
        owner=Objects.requireNonNull(actual);warReads=Objects.requireNonNull(reads);this.sources=Objects.requireNonNull(sources);
        requireInstalledFamily();warReads.pendingDeclaration(owner.reads());
    }
    /** Invoked only with the actual installed military object; new/empty parallel families fail identity checks. */
    public static RootArmyDeclarationDiagnostics install(RootRuntimeDefinitions.Inputs selected,RootRuntimeContext actual,OrdinaryMilitaryInstaller military)throws IOException {
        Objects.requireNonNull(selected);Objects.requireNonNull(actual);Objects.requireNonNull(military);
        Sources sources=new Sources(source(selected,"local-service","service/root/RootArmyDeclarationDiagnostics"),
                source(selected,"native-transport","nativebridge/capabilities/army/ArmyDeclarationDiagnostics"),
                source(selected,"native-transport","nativebridge/capabilities/army/ArmyWarReads"));
        return install(sources,actual,military);
    }
    /** Catalog consumes the actual PreparedSources product after binding its original inventory once. */
    public static RootArmyDeclarationDiagnostics install(Sources sources,RootRuntimeContext actual,OrdinaryMilitaryInstaller military)throws IOException {
        Objects.requireNonNull(sources);Objects.requireNonNull(actual);Objects.requireNonNull(military);
        return new RootArmyDeclarationDiagnostics(actual,military.warReads(),sources);
    }
    public ExactRef implementationSource(){return sources.implementation();}
    public Sources sources(){return sources;}
    /** Read same original custody under the caller's existing writer and source-qualified diagnostic scope. */
    public Optional<Obj> capture(RootRuntimeContext current,ContinuityStorePort.Session same,
            DriverSnapshotFacts.Known actualDriver,BridgeDiagnostics.Received actualReceived)throws IOException {
        StrictJson.require(current==owner,"pending declaration diagnostics crossed Root context");Objects.requireNonNull(actualDriver);Objects.requireNonNull(actualReceived);
        owner.writer().requireSession(same);requireInstalledFamily();
        return owner.adopted().authority().withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==actualDriver&&actualDriver.stamp().game().equals(owner.game().generation()),"pending diagnostics requires the identical held Driver facts");
            var transport=owner.transport();owner.adopted().producer().requireSameTransport(transport,owner.source());
            var before=transport.diagnostics();RootMcpBridgeDiagnostics.requireSameReceived(actualReceived.original(),before);
            var session=actualReceived.session().orElseThrow(()->new IOException("actual pending diagnostics received session absent"));
            StrictJson.require(session.game().equals(owner.game().generation())&&session.sessionId().equals(owner.game().sessionId())
                    &&session.machineId().equals(owner.source().machineId()),"pending diagnostics crossed actual transport Game/session");
            var captured=ArmyDeclarationDiagnostics.capture(warReads,owner.reads());
            captured.originalCustody().ifPresent(pending->{
                var original=pending.selection().context();
                StrictJson.require(original.source().equals(owner.source())&&original.before().game().equals(session.game())
                        &&original.before().machineId().equals(session.machineId())&&original.sessionId().equals(session.sessionId())
                        &&owner.readCatalog().containsIdentity(pending.contract()),"pending original custody belongs to another installed Root/source/Game");
            });
            captured.requireCurrent(warReads,owner.reads());owner.writer().requireSession(same);requireInstalledFamily();
            RootMcpBridgeDiagnostics.requireSameReceived(before,transport.diagnostics());
            return captured.field();
        });
    }
    private void requireInstalledFamily(){for(var family:warReads.families())StrictJson.require(owner.readCatalog().families().stream().anyMatch(actual->actual==family),"pending diagnostics cannot replace actual installed Army family with an empty store");}
    private static ExactRef source(RootRuntimeDefinitions.Inputs input,String module,String path)throws IOException {
        String target=module+"/src/main/java/org/xar/ck3/control/"+path+".java";var selected=input.sourceIndex().stream().filter(row->row.targetRelative().equals(target)).toList();
        if(selected.size()!=1)throw new IOException("actual unique pending diagnostics source absent: "+target);
        ExactRef ref=selected.getFirst().sourceRef();RootRuntimeDefinitions.read(RootApplicationConfiguration.file(ref),64<<20);return ref;
    }
}
