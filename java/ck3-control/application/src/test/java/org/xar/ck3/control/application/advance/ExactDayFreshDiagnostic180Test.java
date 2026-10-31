package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Private diagnostic DATA boundary only; no Root decoder, endpoint custody or gameplay authority. */
final class ExactDayFreshDiagnostic180Test {
    private static final Instant NOW=Instant.parse("2026-10-31T16:00:00Z");
    private static final BigInteger ONE=BigInteger.ONE;
    private static final GameGeneration GAME=new GameGeneration(4242,new PythonOnlyUInt64(new BigInteger("133700000000000001")));

    @Test void freshQueryRetainsProvenanceAndInvokesVerifier() {
        var actual = new Fixture();
        var proof = actual.fresh();
        var counter = new int[1];
        var loader = new NativeEffectEvidence.FrameLoader() {
            @Override public Complete load(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive originals) {
                assertEquals(new NativeEffectEvidence.FrameBasis(actual.nativeRef, actual.factsRef), basis);
                assertSame(actual.archive, originals);
                return actual.complete;
            }
            @Override public void verifyFreshSnapshotQuery(ObservationProvenance.FreshSnapshotQuery query, Complete actualComplete, ActionPorts.OutcomeArchive originals) {
                counter[0]++;
                assertEquals(proof, query);
                assertSame(actual.complete, actualComplete);
                assertSame(actual.archive, originals);
            }
        };
        var frame = actual.read(proof, loader);
        assertEquals(1, counter[0]);
        assertEquals(proof, frame.provenance());
        assertEquals(actual.complete.observedAt(), frame.observedAt());
        assertEquals(actual.nativeRef, frame.originalEvidence());
    }

    @Test void rejectingAndAbsentFreshVerifierCannotAuthorizeDiagnostic() {
        var fixture=new Fixture();var proof=fixture.fresh();
        var sentinel=new IllegalStateException("diagnostic verifier refused its original");
        NativeEffectEvidence.FrameLoader rejecting=new NativeEffectEvidence.FrameLoader() {
            @Override public Complete load(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive originals) { return fixture.complete; }
            @Override public void verifyFreshSnapshotQuery(ObservationProvenance.FreshSnapshotQuery query,Complete actual,ActionPorts.OutcomeArchive originals) { throw sentinel; }
        };
        assertSame(sentinel,assertThrows(IllegalStateException.class,()->fixture.read(proof,rejecting)));
        assertThrows(IllegalStateException.class,()->fixture.read(proof,fixture.loader(fixture.complete)));
        assertThrows(IllegalArgumentException.class,()->fixture.read(new ObservationProvenance.Query("legacy-read"),fixture.loader(fixture.complete)));
    }

    @Test void oldPushAndDiagnosticOriginalBindingsRemainExact() {
        var fixture=new Fixture();var push=fixture.push();var loader=fixture.loader(fixture.complete);
        assertEquals(push,fixture.read(push,loader).provenance());
        List<ObservationProvenance.Push> badPushes=List.of(
                new ObservationProvenance.Push("other-snapshot",ONE,fixture.nativeRef),
                new ObservationProvenance.Push("native:1",BigInteger.TWO,fixture.nativeRef),
                new ObservationProvenance.Push("native:1",ONE,fixture.put("foreign-packet",fixture.originals.get(fixture.nativeRef))));
        for(var bad:badPushes)assertThrows(IllegalArgumentException.class,()->fixture.read(bad,loader));
        for(ExactRef original:List.of(fixture.nativeRef,fixture.factsRef,fixture.semanticRef)) {
            byte[] saved=fixture.originals.get(original);byte[] damaged=saved.clone();damaged[2]^=1;
            fixture.originals.put(original,damaged);
            assertThrows(IllegalArgumentException.class,()->fixture.read(push,loader));
            fixture.originals.put(original,saved);
        }
        var differentSemantic=fixture.semantic.with("speed",new OpportunityJson.IntegerValue(BigInteger.TWO));
        assertThrows(IllegalArgumentException.class,()->fixture.read(push,fixture.loader(fixture.complete(differentSemantic,fixture.source,"fixture-session",fixture.identity,fixture.nativeRef))));
        var otherSource=new G2Source(fixture.source.machineId(),NOW.plusSeconds(1).toString(),"1.20.0.4",fixture.definition);
        assertThrows(IllegalArgumentException.class,()->fixture.read(push,fixture.loader(fixture.complete(fixture.semantic,otherSource,"fixture-session",fixture.identity,fixture.nativeRef))));
        assertThrows(IllegalArgumentException.class,()->fixture.read(push,fixture.loader(fixture.complete(fixture.semantic,fixture.source,"other-session",fixture.identity,fixture.nativeRef))));
        var otherGame=new ObservationIdentity(fixture.identity.machineId(),new GameGeneration(4343,new PythonOnlyUInt64(new BigInteger("133700000000000002"))),fixture.identity.frame(),1);
        assertThrows(IllegalArgumentException.class,()->fixture.read(push,fixture.loader(fixture.complete(fixture.semantic,fixture.source,"fixture-session",otherGame,fixture.nativeRef))));
        var foreignNative=fixture.put("same-bytes-other-path",fixture.originals.get(fixture.nativeRef));
        var foreignPush=new ObservationProvenance.Push("native:1",ONE,foreignNative);
        assertThrows(IllegalArgumentException.class,()->fixture.read(foreignPush,fixture.loader(fixture.complete(fixture.semantic,fixture.source,"fixture-session",fixture.identity,foreignNative))));
    }

    private static final class Fixture {
        final Map<ExactRef,byte[]> originals=new HashMap<>();
        final ExactRef definition=put("definition","{\"software_definition\":true}".getBytes(StandardCharsets.UTF_8));
        final G2Source source=new G2Source("xenoamess-full-tower-eb9d2c1186",NOW.toString(),"1.20.0.4",definition);
        final ExactRef nativeRef=put("native","{\"software_native_packet\":true}".getBytes(StandardCharsets.UTF_8));
        final ExactRef factsRef=put("facts","{\"software_driver_facts\":true}".getBytes(StandardCharsets.UTF_8));
        final OpportunityJson.Obj semantic=DriverJson.object("""
                {"snapshot_id":"native:1","revision":1,"native_revision":1,"date_raw":53288256,
                 "paused":true,"map_ready":true,"speed":1,"episode_run_id":"fixture-episode","episode_character_id":29829,
                 "local_player_id":0,"played_character":{"character_id":29829,"alive":true},
                 "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
                 "diagnostics":{"bridge_pid":4242,"connection_generation":1},"player_armies":[],"active_wars":[],
                 "top_exclusive_modal_choice_hint":{"status":"absent"},"war_objective_assault_supported":true}
                """.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES)
                .with("java_driver_facts_evidence",OpportunityJson.parse(StrictJson.canonical(factsRef.toJson())));
        final ExactRef semanticRef=put("semantic",DriverJson.encode(semantic));
        final ObservationIdentity identity=new ObservationIdentity(source.machineId(),GAME,
                new ProposalFrame(new Frame(BigInteger.valueOf(29829),ONE,BigInteger.valueOf(53288256)),"native:1",ONE,"fixture-episode"),1);
        final Complete complete=complete(semantic,source,"fixture-session",identity,nativeRef);
        final ActionCommand parent=new ActionCommand("diagnostic-parent",identity,source,"fixture-session",new OperationKey("life-advance"),
                new OpportunityJson.Obj(Map.of()),new ExpectedPostcondition(1,identity,source,"fixture/diagnostic",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
        final ActionPorts.OutcomeArchive archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                    if(method.getName().equals("loadNativeFrame"))return originals.get((ExactRef)args[0]).clone();
                    if(method.getName().equals("loadFullMaterial"))return RawJson.fullMaterial(originals.get((ExactRef)args[0]));
                    throw new UnsupportedOperationException("diagnostic DATA archive does not implement "+method.getName());
                });
        ExactRef put(String label,byte[] bytes) {
            var ref=new ExactRef("software-fixtures/exact-day-fresh180/"+label+".json",bytes.length,ActionCodec.sha256(bytes));
            originals.put(ref,bytes.clone());return ref;
        }
        Complete complete(OpportunityJson.Obj body,G2Source actualSource,String session,ObservationIdentity actualIdentity,ExactRef nativeEvidence) {
            return new Complete(actualIdentity,actualSource,session,ONE,body,nativeEvidence,NOW,ActionCodec.sha256(DriverJson.encode(body)));
        }
        ObservationProvenance.FreshSnapshotQuery fresh() {
            return new ObservationProvenance.FreshSnapshotQuery("fresh-diagnostic-read",definition,
                    new NativeRequestChronology.Event(BigInteger.valueOf(4),NOW),new ObservationProvenance.LiveAfterSetter(factsRef));
        }
        ObservationProvenance.Push push() { return new ObservationProvenance.Push("native:1",ONE,nativeRef); }
        NativeEffectEvidence.FrameLoader loader(Complete actual) {
            return (basis,originalsArchive)->{
                assertEquals(new NativeEffectEvidence.FrameBasis(nativeRef,factsRef),basis);assertSame(archive,originalsArchive);return actual;
            };
        }
        AdvanceObservationPort.Frame read(ObservationProvenance proof,NativeEffectEvidence.FrameLoader loader) {
            ObjectNode row=StrictJson.object();row.set("native_frame",nativeRef.toJson());row.set("driver_facts",factsRef.toJson());
            row.set("provenance",ObservationProvenanceCodec.encode(proof));row.set("semantic",semanticRef.toJson());
            try {
                Method method=ExactDayClockFailureEvidence.class.getDeclaredMethod("loadFrame",JsonNode.class,ActionCommand.class,ActionPorts.OutcomeArchive.class);
                method.setAccessible(true);return (AdvanceObservationPort.Frame)method.invoke(new ExactDayClockFailureEvidence(loader),row,parent,archive);
            } catch(InvocationTargetException wrapper) {
                Throwable cause=wrapper.getCause();
                if(cause instanceof RuntimeException failure)throw failure;
                if(cause instanceof Error failure)throw failure;
                throw new AssertionError(cause);
            } catch(ReflectiveOperationException failure) { throw new AssertionError(failure); }
        }
    }
}
