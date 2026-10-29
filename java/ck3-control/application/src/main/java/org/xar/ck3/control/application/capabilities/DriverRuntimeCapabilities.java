package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Reads the actual Driver owner's archived input reference while borrowing its original writer Session. */
public final class DriverRuntimeCapabilities implements DynamicCapabilities.ActualDriverInputsSource {
    public static final String AUXILIARY_KEY="capability_inputs";
    private final DriverStateAssembler authority;
    private final ActionPorts.OutcomeArchive archive;
    private final ContinuityStorePort.Session borrowed;
    public DriverRuntimeCapabilities(DriverStateAssembler actualAuthority,ActionPorts.OutcomeArchive actualArchive,
            ContinuityStorePort.Session originalWriterSession) {
        authority=Objects.requireNonNull(actualAuthority);borrowed=Objects.requireNonNull(originalWriterSession);
        archive=Objects.requireNonNull(actualArchive).withSession(borrowed);
    }
    @Override public DynamicCapabilities.InputState capture(Complete frame,Known driver) throws IOException {
        Objects.requireNonNull(frame);Objects.requireNonNull(driver);
        return authority.withFrozenFacts(borrowed,frozen -> {
            if(!(frozen.state() instanceof Known current)) return new DynamicCapabilities.UnavailableInputs(List.of("actual_complete_driver_owner_unavailable"));
            requireSame(current,driver);
            if(!current.auxiliary().members().containsKey(AUXILIARY_KEY))
                return new DynamicCapabilities.UnavailableInputs(List.of("actual_runtime_capability_input_reference_missing"));
            if(current.auxiliary().get(AUXILIARY_KEY)==Nil.INSTANCE)
                return new DynamicCapabilities.UnavailableInputs(List.of("actual_runtime_capability_input_reference_null"));
            ExactRef reference=reference(current);
            RawJson original=archive.loadMaterial(reference);
            return new DynamicCapabilities.AvailableInputs(DynamicCapabilities.DriverInputs.decode(frame,current,reference,original.bytes()));
        });
    }
    @Override public boolean stillCurrent(DynamicCapabilities.DriverInputs captured,Complete frame,Known driver) throws IOException {
        Objects.requireNonNull(captured);Objects.requireNonNull(frame);Objects.requireNonNull(driver);
        return authority.withFrozenFacts(borrowed,frozen -> {
            if(!(frozen.state() instanceof Known current)) return false;
            requireSame(current,driver);
            if(!current.auxiliary().members().containsKey(AUXILIARY_KEY) || current.auxiliary().get(AUXILIARY_KEY)==Nil.INSTANCE) return false;
            return captured.stamp().equals(current.stamp()) && reference(current).equals(captured.originalFacts())
                    && object(captured.original().get("driver_stamp"),"driver_stamp")
                    .equals(capabilityStamp(frame,current));
        });
    }
    /** Root invokes this in the same held Driver/native callback used to obtain frame and current. */
    public DynamicCapabilities.Result read(Complete frame,Known current,Obj actualProtocolCapabilities,
            ExecutableStepBindings actualBindings,CapabilityFileProbe actualFiles) {
        try { return DynamicCapabilities.project(frame,current,actualProtocolCapabilities,actualBindings,this,actualFiles); }
        catch(IOException | IllegalArgumentException | IllegalStateException | ArithmeticException failure) {
            return new DynamicCapabilities.Incomplete(List.of("actual_runtime_capability_projection_unavailable: "+failure.getClass().getSimpleName()+": "+Objects.toString(failure.getMessage(),"unknown")));
        }
    }
    /** Typed producer input. Every optional is an explicitly known absence, never an unobserved cache. */
    public record Fields(List<Obj> arrangeMarriageChoices,Optional<Obj> campaignRootContextQuery,
            Optional<Obj> activeCombatRetreatToken,Optional<Obj> episodeSeed,Optional<Obj> episodeTransition,
            Optional<Obj> successionReconciliation,DynamicCapabilities.Configuration configuration,
            Optional<Obj> independentBattleSpeedReadiness,CapabilitySessionPresentation nativeSessionControl) {
        public Fields {
            arrangeMarriageChoices=List.copyOf(arrangeMarriageChoices);Objects.requireNonNull(campaignRootContextQuery);
            Objects.requireNonNull(activeCombatRetreatToken);Objects.requireNonNull(episodeSeed);Objects.requireNonNull(episodeTransition);
            Objects.requireNonNull(successionReconciliation);Objects.requireNonNull(configuration);
            Objects.requireNonNull(independentBattleSpeedReadiness);Objects.requireNonNull(nativeSessionControl);
        }
    }
    /** Shared serialization only. The real cache/session producer must archive and commit this before publication. */
    public static RawJson encode(Complete frame,Known driver,BigInteger actualRuntimeStateVersion,Fields actualFields) {
        Objects.requireNonNull(frame);Objects.requireNonNull(driver);Objects.requireNonNull(actualRuntimeStateVersion);Objects.requireNonNull(actualFields);
        require(actualRuntimeStateVersion.signum()>=0,"nonnegative actual runtime-owner state version required");
        Obj config=DynamicCapabilities.encodeConfiguration(actualFields.configuration());
        Map<String,Value> row=new LinkedHashMap<>();row.put("schema",new Text(DynamicCapabilities.DriverInputs.SCHEMA));
        row.put("driver_stamp",capabilityStamp(frame,driver));
        row.put("state_version",new IntegerValue(actualRuntimeStateVersion));
        row.put("arrange_marriage_choices",new Arr(actualFields.arrangeMarriageChoices().stream().map(v -> (Value)v).toList()));
        row.put("campaign_root_context_query",nullable(actualFields.campaignRootContextQuery()));row.put("active_combat_retreat_v1_token",nullable(actualFields.activeCombatRetreatToken()));
        row.put("episode_seed",nullable(actualFields.episodeSeed()));row.put("episode_transition",nullable(actualFields.episodeTransition()));
        row.put("succession_reconciliation",nullable(actualFields.successionReconciliation()));row.put("configuration",config);
        row.put("independent_battle_speed_readiness",nullable(actualFields.independentBattleSpeedReadiness()));
        row.put("native_session_control",actualFields.nativeSessionControl().original());
        RawJson original=new RawJson(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(new Obj(row)));
        // Encoding must be admitted by the identical real consumer before the producer may publish it.
        DynamicCapabilities.DriverInputs.decode(frame,driver,new ExactRef("capability-inputs/encoding-check.json",original.bytes().length,DriverJson.sha256(original.bytes())),original.bytes());
        return original;
    }
    /** Capability state excludes observation wall time, while retaining every other exact semantic stamp field and full native content. */
    public static Obj capabilityStamp(Complete frame,Known driver) {
        Obj received=DriverJson.object(NativeDriverStamp.encode(frame,driver),DriverJson.MAX_NATIVE_BYTES);
        Map<String,Value> fields=new LinkedHashMap<>(received.members());
        java.time.Instant.parse(text(fields.remove("observed_at"),"observed_at"));
        fields.put("schema",new Text("xar.native-capability-driver-stamp/v1"));
        fields.put("native_state_sha256",new Text(driver.observation().orElseThrow().nativeStateSha256()));
        return new Obj(fields);
    }
    public static Obj referenceJson(ExactRef actuallyArchived) {
        Objects.requireNonNull(actuallyArchived);
        return new Obj(Map.of("path",new Text(actuallyArchived.path()),"bytes",new IntegerValue(BigInteger.valueOf(actuallyArchived.bytes())),"sha256",new Text(actuallyArchived.sha256())));
    }
    private static ExactRef reference(Known current) {
        Obj row=object(current.auxiliary().get(AUXILIARY_KEY),AUXILIARY_KEY);
        require(row.members().keySet().equals(Set.of("path","bytes","sha256")),"exact original runtime input reference required");
        return new ExactRef(text(row.get("path"),"path"),integer(row.get("bytes"),"bytes").longValueExact(),text(row.get("sha256"),"sha256"));
    }
    private static void requireSame(Known current,Known supplied) {
        require(current.stamp().equals(supplied.stamp()) && current.auxiliary().equals(supplied.auxiliary())
                && Arrays.equals(current.driver().encode(),supplied.driver().encode()) && current.observation().equals(supplied.observation()),
                "capability caller left the actual frozen Driver owner version");
    }
    private static Value nullable(Optional<Obj> value) { return value.<Value>map(v -> v).orElse(Nil.INSTANCE); }
}
