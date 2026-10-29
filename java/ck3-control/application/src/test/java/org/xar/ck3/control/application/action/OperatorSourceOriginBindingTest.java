package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Descriptor and unavailable-source regressions. Actual Root operator qualifications belong to its real issuer tests. */
final class OperatorSourceOriginBindingTest {
    private static final ExactRef SOURCE=new ExactRef("D:/operator-descriptor/source.java",1,"a".repeat(64));
    private static final ExactRef FOREIGN=new ExactRef("D:/operator-descriptor/foreign.java",1,"b".repeat(64));
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static final class RefusingSource implements RootExecutableBindings.OperatorSourceOriginProof {
        private int prepared,qualified;
        @Override public ExactRef operatorDefinitionSource(){return SOURCE;}
        @Override public void requireOperatorOrigin(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionCommand exact)throws IOException {
            qualified++;throw new IOException("descriptor fixture has no actual Root operator scope");
        }
        @Override public NativeRequest prepare(ActionCommand command){prepared++;throw new AssertionError("descriptor fixture must never prepare a native operator command");}
    }
    private static NativeEffectRegistry.Binding effect(String step,ExactRef source,ActionPorts.PreparationPort preparation) {
        return new NativeEffectRegistry.Binding(new OperationKey(step),source,preparation,
                (command,attempt,dispatch)->{throw new AssertionError("descriptor fixture cannot confirm an operator effect");});
    }
    @Test void originalCanonicalInt32TargetsShareOneActualEffectAndOnlyTheirFiniteTwoOriginDescriptors() {
        var proof=new RefusingSource();
        for(long target:new long[]{1,7,Integer.MAX_VALUE}) {
            var original=effect("set-played-character-v1-"+target,SOURCE,proof);
            var action=RootExecutableBindings.ActionBinding.operatorSource(original,SOURCE,proof);
            var catalog=RootExecutableBindings.freeze(List.of(action),RootReadContractCatalog.staticOnly(List.of()),List.of(),4);
            assertSame(original,catalog.actualActionBinding(original.operation()).orElseThrow());assertEquals(1,catalog.effects().installed().size());
            assertEquals(Set.of(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION),action.originModes());
            assertEquals(SOURCE,catalog.resolve(original.operation(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().implementationSource());
            assertEquals(SOURCE,catalog.resolve(original.operation(),ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION).orElseThrow().implementationSource());
            assertTrue(catalog.resolve(original.operation(),ReadContract.GuardMode.FRONTEND_SESSION).isEmpty());
            assertTrue(catalog.resolve(original.operation(),ReadContract.GuardMode.RECONCILIATION_OBSERVATION).isEmpty());
            assertThrows(IllegalArgumentException.class,()->catalog.resolve(original.operation()));
            assertThrows(IllegalArgumentException.class,catalog::requireCompleteArchiveCoverage);
        }
        assertEquals(0,proof.prepared);assertEquals(0,proof.qualified);
    }
    @Test void invalidNativeGrammarDetachedPreparationSourceAndCapabilityCannotInstallAnOperatorProfile() {
        var proof=new RefusingSource();
        for(String suffix:List.of("0","-1","01","+7","7.0","2147483648","99999999999","7-other"))
            assertThrows(IllegalArgumentException.class,()->RootExecutableBindings.ActionBinding.operatorSource(effect("set-played-character-v1-"+suffix,SOURCE,proof),SOURCE,proof));
        assertThrows(IllegalArgumentException.class,()->RootExecutableBindings.ActionBinding.operatorSource(effect("pause-map",SOURCE,proof),SOURCE,proof));
        var exact=effect("set-played-character-v1-7",SOURCE,proof);
        assertThrows(IllegalArgumentException.class,()->RootExecutableBindings.ActionBinding.operatorSource(exact,SOURCE,new RefusingSource()));
        assertThrows(IllegalArgumentException.class,()->RootExecutableBindings.ActionBinding.operatorSource(effect(exact.operation().value(),FOREIGN,proof),SOURCE,proof));
        assertThrows(IllegalArgumentException.class,()->new RootExecutableBindings.ActionBinding(exact,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of("game.command.set-played-character-v1-7"),SOURCE,Optional.empty(),Optional.empty(),Optional.of(proof)));
        assertThrows(IllegalArgumentException.class,()->new RootExecutableBindings.ActionBinding(exact,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,
                Optional.of(OperatorPlayerSwitch.CAPABILITY),SOURCE,Optional.empty(),Optional.empty(),Optional.of(proof)));
        assertEquals(0,proof.prepared);assertEquals(0,proof.qualified);
    }
    @Test void dynamicFamilyColdOperationDecodeKeepsTheSameFiniteProducerAndReplayBindingWithoutGrantingAuthority() {
        var proof=new RefusingSource();
        var family=new RootExecutableBindings.Family<Long>("operator-descriptor-family",Long.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                Optional.of(OperatorPlayerSwitch.CAPABILITY),SOURCE,SOURCE,SOURCE,
                target->raw("{\"character_id\":"+target+"}"),target->new OperationKey("set-played-character-v1-"+target),
                target->{var effect=effect("set-played-character-v1-"+target,SOURCE,proof);return new RootExecutableBindings.IssuedAction(
                        RootExecutableBindings.ActionBinding.operatorSource(effect,SOURCE,proof),new NativeRecordedEvidenceVerifier.Binding(effect.operation(),SOURCE,
                        (head,receipt,originals)->{throw new AssertionError("descriptor fixture cannot replay an actual operator qualification");}));},
                operation->{String value=operation.value(),prefix="set-played-character-v1-";if(!value.startsWith(prefix))return Optional.empty();
                    String target=value.substring(prefix.length());if(!target.matches("[1-9][0-9]{0,9}"))return Optional.empty();long actual=Long.parseLong(target);
                    return actual<=Integer.MAX_VALUE?Optional.of(actual):Optional.empty();});
        var catalog=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of()),List.of(),List.of(),List.of(family),4);
        var step=new OperationKey("set-played-character-v1-7");
        assertEquals(0,catalog.effects().installed().size());
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,catalog.resolve(step,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION).orElseThrow().guardMode());
        assertSame(catalog.issue(family,7L).effect(),catalog.actualActionBinding(step).orElseThrow());assertEquals(1,catalog.effects().installed().size());
        assertTrue(catalog.actualArchivedVerifier(step).isPresent());catalog.requireCompleteArchiveCoverage();
        assertTrue(catalog.resolve(new OperationKey("set-played-character-v1-07"),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).isEmpty());
        assertEquals(0,proof.prepared);assertEquals(0,proof.qualified);
    }
    @Test void detachedTypedCommandCannotPrepareWithoutTheActualBorrowedWriter() {
        var proof=new RefusingSource();var effect=effect("set-played-character-v1-7",SOURCE,proof);
        var catalog=RootExecutableBindings.freeze(List.of(RootExecutableBindings.ActionBinding.operatorSource(effect,SOURCE,proof)),RootReadContractCatalog.staticOnly(List.of()),List.of(),4);
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
        var frame=new ObservationIdentity("operator-descriptor",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(3),BigInteger.TEN,BigInteger.valueOf(100)),"snapshot",BigInteger.TEN,"episode"),1);
        var origin=new CommandOrigin.Gameplay(frame);var source=new G2Source("operator-descriptor",Instant.now().toString(),"1.19.0.6",SOURCE);
        var request=new OperatorPlayerSwitch.Request(7,BigInteger.TEN);
        var expectation=new CommandExpectation.OperatorRebind(new OperatorRebindExpectation(origin,source,request,"episode",0,SOURCE));
        var command=new ActionCommand("operator-descriptor-no-dispatch",origin,source,"session",effect.operation(),new OpportunityJson.Obj(Map.of()),expectation,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(30));
        assertThrows(IllegalStateException.class,()->catalog.prepare(command));assertThrows(IllegalStateException.class,()->catalog.prepare(command,"request"));
        assertEquals(0,proof.prepared);assertEquals(0,proof.qualified);
    }
}
