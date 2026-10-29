package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.ExecutableCapabilities;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Genuine public PLAN fixtures call these entries inside their actual raw observation callback.
 * No test constructs a Game, ACK, Known, source issuer or capability result. Missing genuine DATA is NOT_RUN. */
public final class DriverPublicPlanningInputsAssertions {
    private DriverPublicPlanningInputsAssertions() { }
    public record RetainedScope(DriverStateAssembler.ReadOnlyPlanningScope scope) { }
    public record RetainedTerminalScope(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope) { }

    /** Invoke on actual running and same-actor dead frames, before the original planner's branch selection. */
    public static RetainedScope assertActualRawInputs(DriverStateAssembler authority,DriverCapabilityRuntime runtime,
            RootExecutableBindings bindings,Session same,Complete frame,Known known,Obj received,Instant deadline)throws Exception {
        String head=same.head().digest();byte[] driver=known.driver().encode();Obj auxiliary=known.auxiliary();
        var installed=List.copyOf(bindings.installed());var actions=List.copyOf(bindings.actionBindings());
        var archives=List.copyOf(bindings.archivedBindings());
        var scope=authority.openReadOnlyPlanningScope(same,frame,known,deadline);
        ExecutableCapabilities result=runtime.collectPublicPlanningInputs(same,frame,known,received,deadline);
        assertNotNull(result);assertFalse(result.bridgeCapabilities().isEmpty());
        assertEquals(installed,bindings.installed());assertEquals(actions,bindings.actionBindings());assertEquals(archives,bindings.archivedBindings());
        assertSame(known,current(authority,same));assertArrayEquals(driver,current(authority,same).driver().encode());
        assertEquals(auxiliary,current(authority,same).auxiliary());assertEquals(head,same.head().digest());scope.requireCurrent();
        Complete equalCopy=new Complete(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),frame.semantic(),
                frame.originalEvidence(),frame.observedAt(),frame.fullBindingSha256(),frame.originalProjection());
        assertEquals(frame,equalCopy);assertNotSame(frame,equalCopy);
        assertThrows(IllegalArgumentException.class,()->scope.requireInputs(equalCopy,known));
        return new RetainedScope(scope);
    }

    /** Invoke on real changed/missing-actor full terminal DATA. It cannot be replaced by an ordinary Complete. */
    public static RetainedTerminalScope assertActualTerminalInputs(DriverStateAssembler authority,DriverCapabilityRuntime runtime,
            RootExecutableBindings bindings,Session same,FullSnapshot full,Known known,Obj received,Instant deadline,
            ActionPorts.OutcomeArchive actualArchive)throws Exception {
        String head=same.head().digest();var installed=List.copyOf(bindings.installed());
        var actions=List.copyOf(bindings.actionBindings());var archives=List.copyOf(bindings.archivedBindings());
        var scope=authority.openReadOnlyTerminalPlanningScope(same,full,known,deadline);
        var input=runtime.capturePublicTerminalInputs(same,full,known,deadline);
        byte[] original=actualArchive.loadMaterial(input.original()).bytes();assertTerminalWire(original);
        var decoded=DriverCapabilityStateProducer.decodePublicTerminalWire(original);
        var declared=decoded.lifecycleInputs();
        if(declared.mode()!=DriverCapabilityStateProducer.PublicTerminalLifecycleMode.OBSERVED_BINDING){
            var source=runtime.actualPublicPlanningLifecycleSource(same);
            var actual=source.capture(same,full,known);source.requireCurrent(same,full,known,actual);
            assertEquals(actual.sourceClosure(),declared.sourceClosure());
            assertEquals(actual.policySource(),declared.policySource().orElseThrow());
            assertEquals(actual.environmentSource(),declared.environmentSource().orElseThrow());
            assertEquals(actual.source().sourceRef(),declared.nativeSource().orElseThrow());
        }
        boolean present=full.semantic().members().containsKey("succession_lifecycle");
        assertEquals(present?full.semantic().get("succession_lifecycle"):Nil.INSTANCE,declared.declaredLifecycle());
        assertEquals(present?declared.declaredLifecycle()==Nil.INSTANCE?DriverCapabilityStateProducer.DeclaredLifecyclePresence.NULL:
                DriverCapabilityStateProducer.DeclaredLifecyclePresence.VALUE:DriverCapabilityStateProducer.DeclaredLifecyclePresence.MISSING,declared.declaredPresence());
        ExecutableCapabilities result=runtime.collectPublicTerminalInputs(same,full,known,received,deadline);
        assertTrue(result.actionSteps().stream().allMatch(step->Set.of("death-terminal","start-next-episode","continue-as-reconciled-successor").contains(step.value())));
        assertFalse(result.bridgeCapabilities().isEmpty());assertTrue(result.battleSpeedReadiness().isEmpty());
        assertEquals(installed,bindings.installed());assertEquals(actions,bindings.actionBindings());assertEquals(archives,bindings.archivedBindings());
        assertSame(known,current(authority,same));assertEquals(head,same.head().digest());scope.requireCurrent();input.requireScope(full,known);
        FullSnapshot equalCopy=new FullSnapshot(full.actual(),full.facts(),full.semantic(),full.originalEvidence(),full.fullBindingSha256());
        assertEquals(full,equalCopy);assertNotSame(full,equalCopy);
        assertThrows(IllegalArgumentException.class,()->scope.requireInputs(equalCopy,known));
        return new RetainedTerminalScope(scope);
    }
    public static void assertEscaped(RetainedScope actual){
        assertThrows(IllegalArgumentException.class,actual.scope()::requireCurrent);
    }
    public static void assertEscapedTerminal(RetainedTerminalScope actual){
        assertThrows(IllegalArgumentException.class,actual.scope()::requireCurrent);
    }
    /** Real LS private issuer only: equal constructor DTOs cannot replace its actual retained capture. */
    public static void assertActualConstructorSource(DriverCapabilityRuntime runtime,
            DriverStateAssembler authority,RootExecutableBindings bindings,ActionPorts.OutcomeArchive archive,
            Session same,FullSnapshot full,Known known)throws Exception {
        String head=same.head().digest();var actual=runtime.actualPublicPlanningLifecycleSource(same);actual.requireOwner(same,authority,archive,bindings);
        var original=actual.capture(same,full,known);actual.requireCurrent(same,full,known,original);
        assertSame(original,actual.capture(same,full,known));assertEquals(actual.sources(),original.sourceClosure());
        var copied=new DriverCapabilityRuntime.NativeCampaignConstructorFacts(original.constructor(),original.game(),original.sessionId(),
                original.source(),original.policySource(),original.environmentSource(),original.sourceClosure(),original.headDigest());
        assertEquals(original,copied);assertNotSame(original,copied);
        assertThrows(IllegalArgumentException.class,()->actual.requireCurrent(same,full,known,copied));
        actual.requireCurrent(same,full,known,original);assertSame(known,current(authority,same));assertEquals(head,same.head().digest());
    }
    /** Actual public raw scope only. Both supplied physical references must already belong to the real issuer. */
    public static RetainedTerminalScope assertActualPhysicalClosureInputs(DriverCapabilityRuntime runtime,
            DriverStateAssembler authority,RootExecutableBindings bindings,ActionPorts.OutcomeArchive archive,
            Session same,FullSnapshot full,Known known,Obj received,Instant deadline,
            org.xar.ck3.control.contracts.ExactRef actualEmpty,org.xar.ck3.control.contracts.ExactRef actualLarge)throws Exception {
        assertEquals(0,actualEmpty.bytes());
        assertTrue(actualLarge.bytes()>org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
        String head=same.head().digest();byte[] driver=known.driver().encode();
        var actual=runtime.actualPublicPlanningLifecycleSource(same);
        actual.requireOwner(same,authority,archive,bindings);var facts=actual.capture(same,full,known);
        assertTrue(facts.sourceClosure().containsAll(List.of(actualEmpty,actualLarge)));
        assertEquals(actual.sources(),facts.sourceClosure());
        assertTrue(facts.policySource().bytes()>0&&facts.environmentSource().bytes()>0&&facts.source().sourceRef().bytes()>0);
        assertActualConstructorSource(runtime,authority,bindings,archive,same,full,known);
        var input=runtime.capturePublicTerminalInputs(same,full,known,deadline);
        byte[] original=archive.loadMaterial(input.original()).bytes();assertTerminalWire(original);
        var restored=DriverCapabilityStateProducer.decodePublicTerminalWire(original);
        assertEquals(facts.sourceClosure(),restored.lifecycleInputs().sourceClosure());
        assertTrue(restored.lifecycleInputs().sourceClosure().containsAll(List.of(actualEmpty,actualLarge)));
        var retained=assertActualTerminalInputs(authority,runtime,bindings,same,full,known,received,deadline,archive);
        input.requireScope(full,known);actual.requireCurrent(same,full,known,facts);
        assertSame(known,current(authority,same));assertArrayEquals(driver,current(authority,same).driver().encode());
        assertEquals(head,same.head().digest());return retained;
    }
    /** Strict missing/null/type/renaming and full native/history-reference roundtrip over the actual producer bytes. */
    public static void assertTerminalWire(byte[] actualOriginal){
        var decoded=DriverCapabilityStateProducer.decodePublicTerminalWire(actualOriginal);Obj row=decoded.toJson();
        assertEquals(decoded,DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(row)));
        assertArrayEquals(actualOriginal,DriverJson.encode(row));
        reject(changed(row,"state_version",new Bool(true)));reject(changed(row,"state_version",new Text("01")));
        reject(changed(row,"episode_seed",new Arr(List.of())));reject(changed(row,"schema",new Text("unknown")));
        Map<String,Value> missing=new LinkedHashMap<>(row.members());missing.remove("episode_transition");reject(new Obj(missing));
        Map<String,Value> renamed=new LinkedHashMap<>(row.members());renamed.put("native_packet",renamed.remove("native"));reject(new Obj(renamed));
        Map<String,Value> extra=new LinkedHashMap<>(row.members());extra.put("ready",new Bool(true));reject(new Obj(extra));
        Obj nativeRef=OpportunityJson.object(row.get("native"),"actual native ref");reject(changed(row,"native",changed(nativeRef,"bytes",new Bool(true))));
        Obj absent=changed(row,"episode_seed",Nil.INSTANCE);
        assertTrue(DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(absent)).episodeSeed().isEmpty());
        missing=new LinkedHashMap<>(absent.members());missing.remove("episode_seed");reject(new Obj(missing));
        Obj lifecycle=OpportunityJson.object(row.get("lifecycle_inputs"),"actual lifecycle inputs");
        reject(changed(row,"lifecycle_inputs",changed(lifecycle,"mode",new Bool(true))));
        reject(changed(row,"lifecycle_inputs",changed(lifecycle,"declared_presence",new Bool(true))));
        Map<String,Value> noSource=new LinkedHashMap<>(lifecycle.members());noSource.remove("policy_source");reject(changed(row,"lifecycle_inputs",new Obj(noSource)));
        if(decoded.lifecycleInputs().mode()!=DriverCapabilityStateProducer.PublicTerminalLifecycleMode.OBSERVED_BINDING)
            reject(changed(row,"lifecycle_inputs",changed(lifecycle,"source_closure",new Arr(List.of()))));
    }
    private static Obj changed(Obj actual,String key,Value value){Map<String,Value> fields=new LinkedHashMap<>(actual.members());fields.put(key,value);return new Obj(fields);}
    private static void reject(Obj malformed){assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(malformed)));}
    private static Known current(DriverStateAssembler actual,Session same)throws Exception {
        return actual.withFrozenFacts(same,frozen->assertInstanceOf(Known.class,frozen.state()));
    }
}
