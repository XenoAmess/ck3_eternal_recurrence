package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original episode01 startup event is observed unchanged; this producer never selects its preparation options. */
public final class FixtureStartupObservation {
    public static final class Proof {
        private final BigInteger eventInstanceId;
        private final List<Integer> nativeOptionIndices;
        private final ExactRef originalRead;
        private final Obj before,after;
        private Proof(BigInteger id,List<Integer> indices,ExactRef read,Obj before,Obj after) {
            eventInstanceId=id;nativeOptionIndices=List.copyOf(indices);originalRead=read;this.before=before;this.after=after;
        }
        public BigInteger eventInstanceId() {return eventInstanceId;}
        public List<Integer> nativeOptionIndices() {return nativeOptionIndices;}
        public ExactRef originalRead() {return originalRead;}
        public Obj before() {return before;}
        public Obj after() {return after;}
        public boolean selectionAttempted() {return false;}
        public String status() {return "OBSERVED_UNCHANGED_STARTUP_EVENT";}
    }
    private final ReadContract<EventPolicies.ReadPublication> actualWindow;
    public FixtureStartupObservation(ReadContract<EventPolicies.ReadPublication> actualWindow) {
        this.actualWindow=Objects.requireNonNull(actualWindow);
        StrictJson.require(actualWindow.operation().value().equals(EventWindowRead.STEP)&&actualWindow.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&actualWindow.hasPureReplay(),"actual original-only replay event-window contract required");
    }
    public Proof observe(PreparedFixture fixture,FixtureStartSubmission submission,FixtureBusinessQualification.Owner previous,
            FixtureBusinessQualification.Owner current,Obj before,PlanningReadResult.Known<EventPolicies.ReadPublication> observed,
            Obj after,ActionPorts.OutcomeArchive sameOriginals) {
        PlanningReadReceipt receipt=observed.receipt();org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(receipt,sameOriginals);
        StrictJson.require(receipt.contractId().equals(actualWindow.contractId())&&receipt.request().operation().equals(actualWindow.operation())
                &&receipt.request().origin() instanceof CommandOrigin.Gameplay&&receipt.request().before().frame().snapshotId().equals(current.snapshotId())
                &&receipt.request().before().frame().revision().equals(current.revision())&&receipt.request().before().frame().identity().nativeRevision().equals(current.nativeRevision())
                &&sameOriginals.readReferenceOf(receipt).equals(observed.originalReceipt())
                &&actualWindow.decode(receipt).equals(observed.value()),"scenario startup must consume original installed exact-frame event read");
        List<Integer> indices=validatePresentation(fixture,submission,previous,current,before,observed.value().result(),after);
        return new Proof(integer(current.activeEvent().orElseThrow().get("instance_id"),"instance_id"),indices,observed.originalReceipt(),before,after);
    }
    /** Pure data regression seam cannot construct Proof or a Root lease. */
    public static List<Integer> validatePresentation(PreparedFixture fixture,FixtureStartSubmission submission,FixtureBusinessQualification.Owner previous,
            FixtureBusinessQualification.Owner current,Obj before,Obj packet,Obj after) {
        StrictJson.require(fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO&&submission.policyBinding().equals(fixture.binding()),"closed exact prepared scenario required");
        var owner=FixtureBusinessQualification.owner(before,submission,true).orElseThrow();
        StrictJson.require(owner.equals(current)&&previous.stable().equals(current.stable())&&current.pumpEpoch().compareTo(previous.pumpEpoch())>0,"startup event query needs two completed stable owner frames");
        completed(before);Obj diagnostics=object(before.get("diagnostics"),"diagnostics"),hello=object(diagnostics.get("hello"),"hello");
        StrictJson.require(new Bool(true).equals(diagnostics.get("connected"))&&new Text("1.20.0.4").equals(hello.get("expected_ck3_version"))
                &&new Text("ck3-1.20.0.4-msvc-x64").equals(hello.get("game_adapter_id"))&&new Bool(true).equals(hello.get("ck3_build_match"))
                &&integer(hello.get("pid"),"hello.pid").equals(BigInteger.valueOf(current.bridgePid()))
                &&integer(hello.get("connection_generation"),"connection_generation").equals(current.connectionGeneration()),"startup event requires actual current4 connected HELLO");
        var build=org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build.require("1.20.0.4",text(hello.get("expected_ck3_sha256"),"expected_ck3_sha256"));
        StrictJson.require(build==org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build.CK3_12004,"startup exact .4 executable required");
        Obj context=object(packet.get("current_event_window_context"),"current_event_window_context");
        Obj event=current.activeEvent().orElseThrow();BigInteger instance=integer(event.get("instance_id"),"instance_id");
        StrictJson.require(new Text("native").equals(event.get("source"))&&instance.signum()>0&&new Text("available").equals(packet.get("status"))
                &&new Bool(true).equals(packet.get("current_event_window_context_ready"))&&new Text("current-event-window-context-v1").equals(context.get("schema"))
                &&integer(context.get("schema_version"),"schema_version").equals(BigInteger.ONE)&&new Text("available").equals(context.get("status"))
                &&integer(context.get("window_match_count"),"window_match_count").equals(BigInteger.ONE)
                &&integer(context.get("current_event_instance_id"),"current_event_instance_id").equals(instance)
                &&new Text(FrontendFixturePolicy.STARTUP_EVENT).equals(context.get("event_definition_key"))
                &&integer(context.get("snapshot_revision"),"snapshot_revision").equals(current.nativeRevision())
                &&integer(context.get("date_raw"),"date_raw").intValueExact()==current.dateRaw()
                &&new Text("ck3-1.20.0.4-native-event-window-v1").equals(object(context.get("provenance"),"provenance").get("backend_id"))
                &&new Text(current.snapshotId()).equals(packet.get("queried_snapshot_id"))&&new IntegerValue(current.revision()).equals(packet.get("queried_revision"))
                &&new IntegerValue(current.nativeRevision()).equals(packet.get("queried_native_revision")),"startup event crossed actual definition/root/frame");
        Obj scope=object(context.get("root_scope"),"root_scope"),identity=object(scope.get("typed_identity"),"typed_identity"),ready=object(context.get("readiness"),"readiness");
        StrictJson.require(new Text("available").equals(scope.get("status"))&&new Text("character").equals(scope.get("type_key"))
                &&new Text("available").equals(identity.get("status"))&&new Text("character").equals(identity.get("kind"))
                &&integer(identity.get("character_id"),"character_id").equals(current.actor()),"startup event root differs from actual current player");
        for(String key:List.of("event_definition_identity_ready","root_scope_ready","option_presentation_ready"))StrictJson.require(new Bool(true).equals(ready.get(key)),"actual startup event presentation incomplete: "+key);
        List<Value> options=array(context.get("options"),"options"),visible=array(event.get("options"),"public options");
        StrictJson.require(options.size()==2&&visible.size()==2,"exact two startup preparation options required");
        List<Integer> indices=new ArrayList<>();
        for(int index=0;index<2;index++) {
            Obj option=object(options.get(index),"option"),publicOption=object(visible.get(index),"visible");
            StrictJson.require(integer(option.get("rendered_index"),"rendered_index").intValueExact()==index
                    &&integer(publicOption.get("option_number"),"option_number").intValueExact()==index+1
                    &&new Bool(true).equals(option.get("shown"))&&new Bool(true).equals(option.get("enabled"))
                    &&new Bool(false).equals(option.get("fallback"))&&new Bool(false).equals(option.get("cancel"))
                    &&new Bool(true).equals(publicOption.get("enabled")),"actual startup option ordering/availability differs");
            int nativeIndex=integer(option.get("native_option_index"),"native_option_index").intValueExact();StrictJson.require(nativeIndex>=0,"nonnegative actual native option index required");indices.add(nativeIndex);
        }
        StrictJson.require(!indices.get(0).equals(indices.get(1)),"startup option native identities must differ");
        completed(after);var later=FixtureBusinessQualification.owner(after,submission,true).orElseThrow();
        StrictJson.require(later.stable().equals(current.stable())&&later.pumpEpoch().compareTo(current.pumpEpoch())>=0
                &&after.get("active_event").equals(before.get("active_event"))
                &&object(after.get("diagnostics"),"diagnostics").get("hello").equals(hello)
                &&new Bool(true).equals(object(after.get("diagnostics"),"diagnostics").get("connected")),"startup event changed during independent read-only observation");
        return List.copyOf(indices);
    }
    private static void completed(Obj snapshot) {
        Obj observer=object(object(object(snapshot.get("diagnostics"),"diagnostics").get("last_heartbeat"),"last_heartbeat").get("snapshot_observer_12002"),"snapshot_observer_12002");
        StrictJson.require(new Bool(false).equals(observer.get("read_in_progress"))&&integer(observer.get("completed_ms"),"completed_ms").compareTo(integer(observer.get("started_ms"),"started_ms"))>=0,"completed actual native owner event frame required");
    }
}
