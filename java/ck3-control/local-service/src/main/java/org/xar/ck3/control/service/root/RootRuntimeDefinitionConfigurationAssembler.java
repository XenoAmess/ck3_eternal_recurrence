package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Assembles the first Configuration from independent typed originals and declared domains.
 * This class neither accepts a definitions template nor writes DATA or grants runtime readiness. */
public final class RootRuntimeDefinitionConfigurationAssembler {
    private RootRuntimeDefinitionConfigurationAssembler() { }

    public record PhysicalOriginals(FileRef applicationRef,FileRef storageLeaseRef,
            FileRef nativeLaunchPlanRef,FileRef runtimePackageRequestRef,SourceIndex sourceIndex,
            List<SourcePin> sources,List<ProducerClosure> closures,List<DataPin> originalData) {
        public PhysicalOriginals {
            Objects.requireNonNull(applicationRef);Objects.requireNonNull(storageLeaseRef);
            Objects.requireNonNull(nativeLaunchPlanRef);Objects.requireNonNull(runtimePackageRequestRef);
            Objects.requireNonNull(sourceIndex);
            sources=List.copyOf(sources);closures=List.copyOf(closures);originalData=List.copyOf(originalData);
        }
    }

    /** These are the existing twelve domain/startup records, with no parallel policy schema or defaults. */
    public record DeclaredDomainInputs(GovInputs governance,FinanceInputs finance,ArmyInputs army,
            PrisonerInputs prisoners,FamilyInputs family,FrontendInputs frontend,InteractionInputs interactions,
            ActivityInputs activity,CrossRunInputs crossRun,IncidentInputs incidents,PublicInputs publicCatalog,
            StartupInputs startup) {
        public DeclaredDomainInputs {
            Objects.requireNonNull(governance);Objects.requireNonNull(finance);Objects.requireNonNull(army);
            Objects.requireNonNull(prisoners);Objects.requireNonNull(family);Objects.requireNonNull(frontend);
            Objects.requireNonNull(interactions);Objects.requireNonNull(activity);Objects.requireNonNull(crossRun);
            Objects.requireNonNull(incidents);Objects.requireNonNull(publicCatalog);Objects.requireNonNull(startup);
        }
    }

    /** Pure model composition only. All field validation and schema ownership remain in the one Configuration constructor. */
    public static Configuration configuration(PhysicalOriginals physical,DeclaredDomainInputs domains,
            String machineId,Instant observedAt,Instant reviewAt) {
        Objects.requireNonNull(physical);Objects.requireNonNull(domains);
        Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);
        return new Configuration(RootRuntimeDefinitionModel.SCHEMA,machineId,observedAt.toString(),reviewAt.toString(),
                physical.applicationRef(),physical.storageLeaseRef(),physical.nativeLaunchPlanRef(),physical.runtimePackageRequestRef(),
                physical.sourceIndex(),physical.sources(),physical.closures(),physical.originalData(),
                domains.governance(),domains.finance(),domains.army(),domains.prisoners(),domains.family(),domains.frontend(),
                domains.interactions(),domains.activity(),domains.crossRun(),domains.incidents(),domains.publicCatalog(),domains.startup());
    }

    /** Compose the existing typed DATA contract without historical source qualification. */
    public static Configuration productionConfiguration(PhysicalOriginals physical,DeclaredDomainInputs domains,
            String machineId,Instant observedAt,Instant reviewAt,Clock clock)throws IOException {
        Objects.requireNonNull(clock);return configuration(physical,domains,machineId,observedAt,reviewAt);
    }

    /** The existing Publisher alone issues Prepared. This aggregate adds no output witness, admission or Ready authority. */
    public static final class Assembled {
        private final RootRuntimeDefinitionsPublisher.Prepared prepared;
        private final RootRuntimeDefinitionsPublisher.Request request;
        private final byte[] requestBytes;
        private Assembled(RootRuntimeDefinitionsPublisher.Prepared prepared,
                RootRuntimeDefinitionsPublisher.Request request,byte[] requestBytes) {
            this.prepared=prepared;this.request=request;this.requestBytes=requestBytes.clone();
        }
        public RootRuntimeDefinitionsPublisher.Prepared prepared(){return prepared;}
        public RootRuntimeDefinitionsPublisher.Request request(){return request;}
        public byte[] requestBytes(){return requestBytes.clone();}
        public void requireCurrent(Clock clock)throws IOException {prepared.requireCurrent(Objects.requireNonNull(clock));}
    }

    /** Preserve the caller's observed time and actual machine metadata; publication is separate CREATE_NEW DATA. */
    public static Assembled assemble(PhysicalOriginals physical,DeclaredDomainInputs domains,Instant observedAt,Instant reviewAt,
            FileRef actualOutputBinding,Path target,Clock clock)throws IOException {
        Objects.requireNonNull(physical);Objects.requireNonNull(domains);Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);
        Objects.requireNonNull(actualOutputBinding);Objects.requireNonNull(target);Objects.requireNonNull(clock);
        Configuration config=productionConfiguration(physical,domains,WindowsJobProcess.currentMachineId(),observedAt,reviewAt,clock);
        var prepared=RootRuntimeDefinitionsPublisher.prepare(config,clock);
        var request=new RootRuntimeDefinitionsPublisher.Request(RootRuntimeDefinitionsPublisher.SCHEMA,config,actualOutputBinding,target.toString());
        byte[] encoded=RootRuntimeDefinitionsPublisher.encodeRequest(request);
        if(!request.equals(RootRuntimeDefinitionsPublisher.decodeRequest(encoded)))
            throw new IOException("sole publication request codec changed the independent assembled inputs");
        return new Assembled(prepared,request,encoded);
    }
    /** Compatibility plan/capture parameters are passive; they do not qualify DATA composition. */
    public static Assembled assemble(PhysicalOriginals physical,DeclaredDomainInputs domains,Instant observedAt,Instant reviewAt,
            FileRef actualOutputBinding,Path target,NativeLaunchPlan sameActualPlan,
            RootOriginalMcpCapture.Retained sameCapturedOriginals,Clock clock)throws IOException {
        return assemble(physical,domains,observedAt,reviewAt,actualOutputBinding,target,clock);
    }

}
