package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.action.RawJson;

/** Uses the existing real Java framed-native/Driver producer fixtures, then the shared runtime encoder and decoder. */
final class CapabilityInputsRoundTripTest {
    private static DriverObservationAssembler.Complete frame() {
        return assertInstanceOf(DriverObservationAssembler.Complete.class,DriverObservationAssemblerTest.join(DriverObservationAssemblerTest.STATE));
    }
    private static DriverSnapshotFacts.Known current() {
        var before=DriverStateAssemblerTest.known();
        var facts=DriverObservationAssemblerTest.facts(DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE));
        return new DriverSnapshotFacts.Known(before.driver(),before.stamp(),before.originalHistoryBasis(),before.actionRows(),before.auxiliary(),before.loop(),Optional.of(facts));
    }
    private static DriverRuntimeCapabilities.Fields fields() {
        var config=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
        var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.empty(),CapabilitySessionPresentation.BindingState.UNBOUND,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        return new DriverRuntimeCapabilities.Fields(List.of(new Obj(Map.of("choice_id",new Text("73-74")))),Optional.empty(),Optional.empty(),
                Optional.empty(),Optional.empty(),Optional.empty(),config,Optional.empty(),session);
    }
    @Test void actualProducerConsumerRoundTripKeepsNullEmptyAndExactLargeStateVersion() {
        var current=current();var frame=frame();BigInteger version=new BigInteger("9007199254740993");
        RawJson wire=DriverRuntimeCapabilities.encode(frame,current,version,fields());
        var decoded=DynamicCapabilities.DriverInputs.decode(frame,current,DriverStateAssemblerTest.ref(wire.bytes()),wire.bytes());
        assertEquals(version,decoded.stateVersion());assertEquals(1,decoded.marriageChoices().size());assertTrue(decoded.campaignRootQuery().isEmpty());
        assertEquals(Nil.INSTANCE,decoded.original().get("campaign_root_context_query"));
        assertEquals(decoded.original(),DriverJson.object(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(decoded.original()),65536));
        assertEquals(CapabilitySessionPresentation.BindingState.UNBOUND,decoded.nativeSessionControl().bindingState());
    }
    @Test void missingNullWrongTypeAndOldSchemaNeverBecomeKnownInputs() {
        var current=current();var frame=frame();RawJson original=DriverRuntimeCapabilities.encode(frame,current,BigInteger.ONE,fields());
        Obj valid=DriverJson.object(original.bytes(),65536);
        for(String field:List.of("arrange_marriage_choices","native_session_control","state_version")) {
            var missing=new LinkedHashMap<>(valid.members());missing.remove(field);reject(new Obj(missing));
        }
        for(Value wrong:List.of(new Bool(true),new DecimalValue("1.0"),Nil.INSTANCE)) {
            var malformed=new LinkedHashMap<>(valid.members());malformed.put("state_version",wrong);reject(new Obj(malformed));
        }
        var nulled=new LinkedHashMap<>(valid.members());nulled.put("arrange_marriage_choices",Nil.INSTANCE);reject(new Obj(nulled));
        var old=new LinkedHashMap<>(valid.members());old.put("schema",new Text("xar.native-driver-capability-inputs/v1"));reject(new Obj(old));
        var alien=new LinkedHashMap<>(valid.members());alien.put("extra_field",new Text("not admitted"));reject(new Obj(alien));
        var malformedSession=new LinkedHashMap<>(object(valid.get("native_session_control"),"native_session_control").members());
        malformedSession.put("queue_dir",new Text(java.nio.file.Path.of("D:/actual-session/bridge").toAbsolutePath().toString()));
        var inconsistent=new LinkedHashMap<>(valid.members());inconsistent.put("native_session_control",new Obj(malformedSession));reject(new Obj(inconsistent));
        byte[] changed=original.bytes();changed[changed.length-1]=' ';
        assertThrows(IllegalArgumentException.class,() -> DynamicCapabilities.DriverInputs.decode(frame,current,DriverStateAssemblerTest.ref(original.bytes()),changed));
    }
    @Test void sessionStateRoundTripsAndUnknownStateIsRejected() {
        var session=fields().nativeSessionControl();assertEquals(session,CapabilitySessionPresentation.decode(session.original()));
        var unknown=new LinkedHashMap<>(session.original().members());unknown.put("episode_binding_state",new Text("unknown-must-not-be-active"));
        assertThrows(IllegalArgumentException.class,() -> CapabilitySessionPresentation.decode(new Obj(unknown)));
        var missing=new LinkedHashMap<>(session.original().members());missing.remove("driver_state_error");
        assertThrows(IllegalArgumentException.class,() -> CapabilitySessionPresentation.decode(new Obj(missing)));
    }
    private static void reject(Obj row) {
        byte[] wire=org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(row);
        assertThrows(IllegalArgumentException.class,() -> DynamicCapabilities.DriverInputs.decode(frame(),current(),DriverStateAssemblerTest.ref(wire),wire));
    }
}
