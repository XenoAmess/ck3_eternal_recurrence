package org.xar.ck3.control.application.planning.campaign;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleReducer;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Read-only FIRST CrossRun comparison. It never creates a SAVE, import, cycle, restore or owner permit. */
public final class CrossRunFirstCheckpointReader {
    private CrossRunFirstCheckpointReader() { }

    /** Produced only after the original private material and its canonical historical body were read together. */
    public static final class Saved {
        private final SavedFirstCheckpointMaterialStore.BaselinedMaterial material;
        private final DomainBodies.BodyRef body;
        private final ExactRef strategySource;
        private final CrossRunPlanning.State state;
        private Saved(SavedFirstCheckpointMaterialStore.BaselinedMaterial material,DomainBodies.BodyRef body,
                ExactRef strategySource,CrossRunPlanning.State state) {
            this.material=material;this.body=body;this.strategySource=strategySource;this.state=state;
        }
        public SavedFirstCheckpointMaterialStore.BaselinedMaterial material(){return material;}
        public DomainBodies.BodyRef body(){return body;}
        public ExactRef strategySource(){return strategySource;}
        public CrossRunPlanning.State state(){return state;}
        public CrossRunPlanning.Plan plan(){return state.nextRunPlan();}
    }

    /**
     * Uses the actual private FIRST_BASELINE branch, including original FileWitness, SAVE receipt,
     * saved SEM and BASELINE ancestry. A retained ordinary material or zero-cycle value cannot enter.
     */
    public static Saved read(ContinuityStorePort.Session same,
            SavedFirstCheckpointMaterialStore.BaselinedMaterial material,ActionPorts.OutcomeArchive originalArchive)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(material);Objects.requireNonNull(originalArchive);
        String head=same.head().digest();material.requireRetained(same);
        DomainBodies.BodyRef body=DomainBodies.reference(material.originalHead(),DomainBodies.Slot.CROSS_RUN_PLANNING)
                .orElseThrow(()->new IOException("original FIRST BASELINE has no canonical CrossRun body"));
        require(body.contractSchema().equals(CrossRunPlanningDomain.CONTRACT_SCHEMA),"original FIRST CrossRun schema differs");
        var pin=new WriterContracts.Pin(body.payload(),body.identity());
        byte[] original=same.readPinned(pin,CrossRunPlanning.MAX_BYTES);
        CrossRunPlanning.State expected=CrossRunPlanning.decodeState(original);
        require(Arrays.equals(original,CrossRunPlanning.encodeState(expected)),"FIRST canonical CrossRun bytes differ from typed state");
        exact(body.payload(),original);
        Projection projected=withArchive(originalArchive,same,bound->project(material.sourceSemantic(),body,expected,bound));
        same.verifyPin(pin);material.requireRetained(same);
        require(head.equals(same.head().digest()),"FIRST CrossRun read changed the original canonical head");
        return new Saved(material,body,projected.source(),projected.state());
    }

    /** The actual private restore caller verifies the restored SEM before this additional data comparison. */
    public static Saved compareRestored(ContinuityStorePort.Session same,
            SavedFirstCheckpointMaterialStore.BaselinedMaterial material,SemanticEvidence actualRestored,
            ActionPorts.OutcomeArchive originalArchive)throws IOException {
        Objects.requireNonNull(actualRestored);Saved saved=read(same,material,originalArchive);String head=same.head().digest();
        Projection restored=withArchive(originalArchive,same,bound->project(actualRestored,saved.body,saved.state,bound));
        require(restored.state().equals(saved.state)&&restored.source().equals(saved.strategySource),
                "restored FIRST strategy/source differs from its exact saved originals");
        material.requireRetained(same);
        require(head.equals(same.head().digest()),"FIRST restore comparison changed canonical history");
        return saved;
    }

    /** Actual death reducer -> NEXT serialized result -> FIRST reader. This pure check grants no admission. */
    public static CrossRunPlanning.Plan requireNextPlan(DriverStateSnapshot.Complete predecessor,
            byte[] actualNextResult,CrossRunPlanning.State actualSavedState) {
        Objects.requireNonNull(predecessor);Objects.requireNonNull(actualSavedState);
        LifecycleReducer.requireScoredTerminal(predecessor);
        Obj terminal=null;
        for(int i=predecessor.commandHistory().size()-1;i>=0;i--) {
            Obj row=DriverJson.object(predecessor.commandHistory().get(i).originalRow().json(),LifecycleProofCodec.MAX_RESULT_BYTES);
            if(new Text("death-terminal").equals(row.get("command"))){terminal=object(row.get("result"),"original terminal result");break;}
        }
        require(terminal!=null,"actual scored predecessor is absent");
        var scored=CrossRunStrategySource.decode(object(terminal.get("cross_run_strategy"),"original scored strategy")).state();
        require(scored.equals(actualSavedState),"FIRST saved strategy differs from the actual scored predecessor");
        Obj result=DriverJson.object(actualNextResult,LifecycleProofCodec.MAX_RESULT_BYTES);
        require(new Text(predecessor.session().episodeRunId()).equals(result.get("source_run_id")),
                "NEXT plan result crossed its original scored episode");
        CrossRunPlanning.Plan plan=CrossRunPlanning.parsePlan(object(result.get("cross_run_plan_used"),"actual NEXT plan object"));
        require(plan.equals(actualSavedState.nextRunPlan()),"NEXT used plan differs from its actual FIRST saved strategy");
        return plan;
    }

    private record Projection(ExactRef source,CrossRunPlanning.State state) { }
    private static Projection project(SemanticEvidence semantic,DomainBodies.BodyRef originalBody,
            CrossRunPlanning.State expected,ActionPorts.OutcomeArchive bound)throws IOException {
        Obj full=DriverJson.object(read(bound,semantic.semantic(),ReadinessArchive.Role.SEMANTIC.maximumBytes()),
                ReadinessArchive.Role.SEMANTIC.maximumBytes());
        Obj strategy=object(full.get("one_life_strategy"),"actual full SEM one_life_strategy");
        var source=reference(full.get(DriverPersistentPlanningState.STRATEGY_SOURCE));
        // Narrow read-only projection into the sole source replayer; unrelated cooldown fields are not invented.
        Obj projection=new Obj(Map.of("one_life_strategy",strategy,
                DriverPersistentPlanningState.STRATEGY_SOURCE,full.get(DriverPersistentPlanningState.STRATEGY_SOURCE)));
        DriverPersistentPlanningState.replay(projection,bound);
        Obj proof=DriverJson.object(read(bound,source,DriverJson.MAX_NATIVE_BYTES),DriverJson.MAX_NATIVE_BYTES);
        require(reference(proof.get("body")).equals(originalBody.payload()),
                "FIRST full SEM strategy source is not its canonical BASELINE CrossRun body");
        CrossRunPlanning.State actual=CrossRunStrategySource.decode(strategy).state();
        require(actual.equals(expected),"FIRST full SEM strategy differs from its historical canonical CrossRun state");
        return new Projection(source,actual);
    }
    private static ExactRef reference(Value value){return ExactRef.fromJson(toNode(object(value,"exact original CrossRun source reference")));}
    private static byte[] read(ActionPorts.OutcomeArchive archive,ExactRef ref,int maximum)throws IOException {
        require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded original FIRST CrossRun material required");
        try{byte[] raw=archive.loadMaterial(ref).bytes();exact(ref,raw);return raw;}
        catch(UncheckedIOException failure){throw failure.getCause();}
    }
    private static void exact(ExactRef ref,byte[] bytes){require(bytes!=null&&bytes.length==ref.bytes()&&ref.sha256().equals(DriverJson.sha256(bytes)),"original FIRST CrossRun material bytes differ");}
    @FunctionalInterface private interface Read<T>{T apply(ActionPorts.OutcomeArchive archive)throws IOException;}
    private static <T>T withArchive(ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session same,Read<T> read)throws IOException {
        try{return archive.inSession(same,bound->{try{return read.apply(bound);}catch(IOException failure){throw new UncheckedIOException(failure);}});}
        catch(UncheckedIOException failure){throw failure.getCause();}
    }
}
