package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Same installed constructor and actual PreparationPort, SOFTWARE only; no Root/Core authority fixture. */
final class GovernancePublicCallerWiringTest {
    @TempDir Path temporary;
    private static final String VERSION="1.20.0.4",SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private ExactRef ref(String name,String sha){return new ExactRef(temporary.resolve(name).toAbsolutePath().toString(),1,sha.repeat(64));}
    private GovernanceRuntimeInstaller.Sources sources(Optional<ExactRef> publicSource){
        ExactRef raw=ref("original-native-source.cpp","a"),java=ref("original-decoder.java","b");
        return new GovernanceRuntimeInstaller.Sources(new GovernanceActionBindings.Sources(raw,raw,raw),java,java,java,java,java,raw,java,List.of(java),publicSource);
    }
    private GovernanceRuntimeInstaller.Config config(){return new GovernanceRuntimeInstaller.Config(VERSION,SHA,"software-caller-source",Set.of(new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN)),1,3);}
    private static ActionCommand command(ExactRef actualPublicSource){
        return command(Optional.of(actualPublicSource),"original-caller-id");
    }
    private static ActionCommand command(Optional<ExactRef> actualPublicSource,String callerId){
        var source=new G2Source("software-governance-only",Instant.EPOCH.toString(),VERSION,new ExactRef("synthetic-only",1,"a".repeat(64)));
        var frame=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(7),BigInteger.valueOf(53145072)),"software-snapshot",BigInteger.valueOf(8),"software-episode"),1);
        var fields=StrictJson.object().put("position_key",CouncilModels.Position.STEWARD.key()).put("candidate_character_id",2).put("expected_has_incumbent",false).put("expected_incumbent_character_id",-1)
                .put("public_submission_schema",CouncilCallerSubmission.SCHEMA).put("caller_request_id",callerId);fields.set("original_query",StrictJson.object());
        var complete=new Complete(frame,source,"software-session",BigInteger.ONE,new OpportunityJson.Obj(java.util.Map.of()),
                new ExactRef("software-command-data-only",1,"a".repeat(64)),Instant.EPOCH,"a".repeat(64));
        return RootDriverGovernancePublicService.produceCommand(complete,CouncilActionCodec.PRIVATE_ASSIGN,"original-caller-id",fields,
                List.of(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("council.position_key"),CouncilModels.Position.STEWARD.key())),
                Set.of(),Instant.parse("2026-10-24T00:00:30Z"),actualPublicSource);
    }
    private GovernanceActionPreparation producer(GovernanceRuntimeInstaller.Sources s){
        return GovernanceRuntimeInstaller.buildPreparation(s,config(),(same,value,id)->{throw new AssertionError("identity validation must not query");},(same,value)->{throw new AssertionError("identity validation must not query");});
    }
    @Test void actualInstalledConstructorAndRegisteredBindingConsumeTheSameConfiguredPublicProducer()throws Exception{
        ExactRef expected=ref("RootDriverGovernancePublicService.java","c");var s=sources(Optional.of(expected));
        var prepared=GovernanceRuntimeInstaller.prepare(temporary.resolve("original-writer.lock"),s,config(),Clock.fixed(Instant.EPOCH,ZoneOffset.UTC));
        assertEquals(Optional.of(expected),prepared.publicCallerProducer());
        var producer=producer(s);var command=command(expected);
        producer.requireProtocolIdentity(command);
        var bindings=GovernanceActionBindings.bindings(s.nativeProducers(),producer,(original,attempt,dispatch)->{throw new AssertionError("no effect observation permitted");},config().admittedActions());
        assertEquals(1,bindings.size());assertSame(producer,bindings.get(0).preparation());
        bindings.get(0).preparation().requireProtocolIdentity(command);
        new NativeEffectRegistry(bindings,1).requireProtocolIdentity(command);
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertEquals("original-caller-id",RequestIds.forCommand(command));
    }
    @Test void actualPublicCommandProducerKeepsTheEmptyCallerOnTheExistingDerivedBranch(){
        var command=command(Optional.empty(),"");
        assertInstanceOf(ProtocolRequestIdentity.BodyDerived.class,command.protocolIdentity());
        producer(sources(Optional.empty())).requireProtocolIdentity(command);
        assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void missingOrDifferentConfiguredSourceAndDerivedHeaderCannotAuthorizeCallerSuppliedId(){
        ExactRef original=ref("RootDriverGovernancePublicService.java","c"),other=ref("another.java","d");var command=command(original);
        assertThrows(IllegalArgumentException.class,()->producer(sources(Optional.empty())).requireProtocolIdentity(command));
        assertThrows(IllegalArgumentException.class,()->producer(sources(Optional.of(other))).requireProtocolIdentity(command));
        var derived=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.expectation(),command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->producer(sources(Optional.of(original))).requireProtocolIdentity(derived));
        var wrongHeader=new ExplicitOriginalProtocolId(ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT,"other-caller-id",original);
        var changed=new ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.expectation(),command.claims(),command.deadline(),wrongHeader);
        assertThrows(IllegalArgumentException.class,()->producer(sources(Optional.of(original))).requireProtocolIdentity(changed));
    }
    @Test void legacyDefinitionsRemainExplicitlyUnconfiguredAndRejectMalformedSourceIdentity(){
        var s=sources(Optional.empty());
        var legacy=new GovernanceRuntimeInstaller.Sources(s.nativeProducers(),s.planningDecoder(),s.councilDecoder(),s.actionDecoder(),s.effectVerifier(),s.councilEffectVerifier(),s.finalTermsNative(),s.finalTermsDecoder(),s.continuationClosure());
        assertTrue(legacy.publicCallerProducer().isEmpty());
        var prepared=GovernanceRuntimeInstaller.prepare(temporary.resolve("legacy-writer.lock"),legacy,config(),Clock.fixed(Instant.EPOCH,ZoneOffset.UTC));
        assertTrue(prepared.publicCallerProducer().isEmpty());
        assertThrows(IllegalArgumentException.class,()->sources(Optional.of(new ExactRef("relative-source.java",1,"a".repeat(64)))));
        assertThrows(IllegalArgumentException.class,()->sources(Optional.of(new ExactRef(temporary.resolve("empty.java").toString(),0,"a".repeat(64)))));
    }
}
