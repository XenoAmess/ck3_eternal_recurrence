package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.governance.crownauthority.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceDomainDocument.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Retained native query -> actual strict normalizer/policy/preparer -> original holding body. No runtime qualification. */
final class RootGovernancePendingTest {
    private static final String SHA="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final Instant NOW=Instant.parse("2026-10-23T19:00:00Z");
    private static final ExactRef REF=new ExactRef("synthetic-domain-source-no-native-qualification",1,"a".repeat(64));
    private static ActionCommand command(String operation,Obj arguments,String snapshot,int publicRevision,int nativeRevision,int date) {
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186",NOW.toString(),"1.20.0.2",REF);
        var observed=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777217),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(date)),snapshot,BigInteger.valueOf(publicRevision),"domain-software-episode"),1);
        return new ActionCommand("governance-pending-software",observed,source,"domain-software-session",new OperationKey(operation),arguments,
                new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,observed,source,GovernancePolicies.EFFECT_SCHEMA,List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
    }
    private static GovernanceActionPreparation preparation() {return new GovernanceActionPreparation("1.20.0.2",SHA,(session,command,id)->{throw new AssertionError("real private Council scope is required");},(session,command)->{throw new AssertionError("real LIFE preflight is required");});}
    private static ObjectNode original(String path)throws Exception {String root=System.getProperty("xar.repository.root");assertNotNull(root,"required original repository");return CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,path))).get("result"));}
    @Test void retainedCouncilCandidateSelectionAndActualWireBecomeTheFullOriginalPendingShape()throws Exception {
        var original=original("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json").get("council_composition_candidates");
        var frame=new CouncilModels.Frame("native:council12002",BigInteger.valueOf(8),BigInteger.valueOf(7),53178264,16777217);
        var decoded=CouncilCodec.decodeNative(StrictJson.canonical(original),frame,CouncilModels.Position.STEWARD,"1.20.0.2",SHA);
        var placeholder=command(CouncilActionCodec.ASSIGN,obj(),frame.snapshotId(),8,7,frame.dateRaw());
        Obj query=object(parse(CouncilCodec.encode(decoded)),"typed native Council");var decision=CouncilSelection.choose(CouncilSelection.decodeCompositionObserved(placeholder.before(),query));
        int selected=decision.selected().orElseThrow().characterId().intValueExact();Obj args=obj("position_key",new Text("councillor_steward"),"candidate_character_id",new IntegerValue(BigInteger.valueOf(selected)),"original_query",query,"expected_has_incumbent",new Bool(true),"expected_incumbent_character_id",new IntegerValue(BigInteger.valueOf(16777218)));
        var command=command(CouncilActionCodec.ASSIGN,args,frame.snapshotId(),8,7,frame.dateRaw());String id=RequestIds.forActionBody(ActionCodec.bodySha256(command));var wire=preparation().prepare(command,id);
        var expectedWire=CouncilActionCodec.wireFields(GovernanceActionPreparation.councilRequest(command,id),false);
        var parsedWire=StrictJson.parse(wire.additionalFields().bytes());
        assertArrayEquals(StrictJson.canonical(expectedWire),StrictJson.canonical(parsedWire),"actual original producer must equal the complete typed request");
        var pending=assertDoesNotThrow(()->RootGovernanceDomains.makePending(command,wire),
                ()->"same canonical original wire; parsed candidate="+parsedWire.get("candidate_character_id").getClass().getSimpleName()
                        +", expected candidate="+expectedWire.get("candidate_character_id").getClass().getSimpleName());
        var state=pending(initial(Domain.COUNCIL),pending);assertEquals(state,decode(Domain.COUNCIL,encode(state)));
        var row=GovernanceDomainDocument.object(pending);assertEquals(id,row.get("action_request_id").textValue());assertEquals(id,row.get("request").get("request_id").textValue());assertNull(row.get("request").get("action_request_id"));assertTrue(row.get("action_ack").isNull());assertEquals(decision.outcome().name(),row.get("source_decision").get("outcome").textValue());
        var wrong=CouncilCodec.object(StrictJson.parse(wire.additionalFields().bytes())).deepCopy().put("candidate_character_id",selected+1);assertThrows(IllegalArgumentException.class,()->RootGovernanceDomains.makePending(command,new NativeRequest(wire.step(),wire.requiredCapability(),new RawJson(StrictJson.canonical(wrong)))));
        var wrongType=CouncilCodec.object(parsedWire).deepCopy().put("candidate_character_id",true);
        var boolWire=new NativeRequest(wire.step(),wire.requiredCapability(),new RawJson(StrictJson.canonical(wrongType)));
        assertThrows(IllegalArgumentException.class,()->RootGovernanceDomains.makePending(command,boolWire));
        String originalWire=new String(wire.additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8);
        String floatWire=originalWire.replace("\"candidate_character_id\":"+selected,"\"candidate_character_id\":"+selected+".0");
        assertNotEquals(originalWire,floatWire,"raw malformed float must reach the real consumer unchanged");
        var floating=new NativeRequest(wire.step(),wire.requiredCapability(),new RawJson(floatWire.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->RootGovernanceDomains.makePending(command,floating));
    }
    private static ActionCommand crownCommand()throws Exception {
        var raw=original("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_action/wire-law-crown-query.json");var placeholder=command(GovernanceActionPreparation.CROWN,obj(),"public:100",100,40,53169072);
        var request=new PlanningReadRequest(placeholder.before(),placeholder.source(),placeholder.sessionId(),new OperationKey(GovernancePlanningReads.CROWN),obj(),placeholder.deadline());
        var normalized=GovernancePlanningReads.crown(raw,request,"1.20.0.2",SHA);var readback=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(normalized));var choice=CrownAuthorityPolicy.choose(readback);
        return command(GovernanceActionPreparation.CROWN,obj("readback",parse(StrictJson.canonical(normalized)),"law_key",new Text(choice.lawKey()),"choice",parse(CrownAuthorityCodec.encodeChoice(choice))),"public:100",100,40,53169072);
    }
    @Test void retainedCrownQuoteAndExactPreparationRetainAllPendingIdentityAndBudgetFields()throws Exception {
        var command=crownCommand();var nativeRequest=preparation().prepare(command,RequestIds.forActionBody(ActionCodec.bodySha256(command)));var pending=RootGovernanceDomains.makePending(command,nativeRequest);var state=pending(initial(Domain.CROWN),pending);
        assertEquals(state,decode(Domain.CROWN,encode(state)));var row=GovernanceDomainDocument.object(pending);assertEquals("submission_unresolved",row.get("stage").textValue());assertTrue(row.get("ack").isNull());assertEquals(123,row.get("source_context").get("bridge_pid").intValue());assertEquals(20000000,row.get("budgets").get("prestige").intValue());
        var fields=CouncilCodec.object(StrictJson.parse(nativeRequest.additionalFields().bytes())).deepCopy();fields.put("budget_prestige_raw",0);
        assertThrows(IllegalArgumentException.class,()->RootGovernanceDomains.makePending(command,new NativeRequest(nativeRequest.step(),nativeRequest.requiredCapability(),new RawJson(StrictJson.canonical(fields)))));
    }
    @Test void parsedCommandAndPreparedBytesCannotMintTheLivePreIntentPreparationScope()throws Exception {
        var command=crownCommand();assertThrows(IllegalArgumentException.class,()->ActionPreparationScope.requirePrepared(null,command));
    }
    private static RootGovernanceDomains metadataHolder() {
        var lock=Path.of("synthetic-governance-no-writer-created.lock").toAbsolutePath();
        var material=new CrownRetryPublication.MaterialPort() {
            @Override public CrownRetryPublication.Material capture(WriterContracts.Head head,CrownRetryPublication.Input input,Instant callerDeadline) {throw new AssertionError("body classification cannot execute a native query");}
            @Override public void requireCurrent(WriterContracts.Head head,CrownRetryPublication.Input input,ObservationIdentity current,G2Source source,Instant callerDeadline) {throw new AssertionError("body classification grants no current runtime authority");}
        };
        var retry=new CrownRetryPublication(lock,CROWN_SCHEMA,List.of(REF),List.of(REF),material,(id,body)->{throw new AssertionError("no publication in this boundary test");});
        return new RootGovernanceDomains(lock,new RootGovernanceDomains.Sources(REF,List.of(REF),List.of(REF)),retry);
    }
    @Test void historicalCodeTraceRetainsTheActualPreviousPendingAndDoesNotHideTheMaterialBodyContract() throws Exception {
        var holder=metadataHolder();var command=crownCommand();
        var nativeRequest=preparation().prepare(command,RequestIds.forActionBody(ActionCodec.bodySha256(command)));
        var crown=pending(initial(Domain.CROWN),RootGovernanceDomains.makePending(command,nativeRequest));
        var historical=new ExactRef("missing-historical-code.java",1,"b".repeat(64));
        for(var domain:Domain.values()) {
            var contract=domain==Domain.CROWN?holder.crownBody():holder.councilBody();
            var document=domain==Domain.CROWN?crown:initial(Domain.COUNCIL);byte[] bytes=encode(document);
            var payload=new ExactRef("retained-"+domain,bytes.length,ActionCodec.sha256(bytes));
            var member=new DomainBodies.BodyRef(contract.slot(),contract.schema(),payload,
                    new WriterContracts.FileIdentity("1","2","133700000000000001",NOW.toString(),bytes.length),List.of(historical));
            var raw=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id","retained-domain-unit")
                    .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",1000)
                    .put("target_days",1).put("target_date_raw",1024).put("last_settled_cycles",0).put("last_settled_date_raw",1000);
            var state=DomainBodies.reduceImport(ContinuityState.fromJson(raw,"retained-domain-unit"),member);
            var head=new WriterContracts.Head(state,List.of(),List.of(),List.of(),false);
            var retained=holder.retainedPrevious(head,Optional.of(member),domain,payload);
            assertEquals(member,retained);assertEquals(List.of(historical),retained.producerSources());
            assertEquals(member,DomainBodies.BodyRef.fromJson(StrictJson.parse(StrictJson.canonical(member.toJson()))));
            assertEquals(document,decode(domain,bytes));assertArrayEquals(bytes,encode(decode(domain,bytes)));
            assertTrue(holder.isDomainBodyContract(domain,retained),"classification grants no canonical material or cadence credit");
            if(domain==Domain.CROWN) {
                assertEquals(Stage.SUBMISSION_UNRESOLVED,decode(domain,bytes).pending().orElseThrow().stage());
                assertEquals(document.pending(),decode(domain,bytes).pending());assertTrue(decode(domain,bytes).latest().isEmpty());
            }
            assertThrows(java.io.IOException.class,()->holder.retainedPrevious(head,Optional.empty(),domain,payload));
            assertThrows(IllegalArgumentException.class,()->holder.retainedPrevious(head,Optional.of(member),domain,REF));
            var changed=new DomainBodies.BodyRef(member.slot(),member.contractSchema(),member.payload(),
                    new WriterContracts.FileIdentity("1","3","133700000000000001",NOW.toString(),bytes.length),member.producerSources());
            assertThrows(IllegalArgumentException.class,()->holder.retainedPrevious(head,Optional.of(changed),domain,payload));
            var otherDomain=domain==Domain.CROWN?Domain.COUNCIL:Domain.CROWN;
            assertFalse(holder.isDomainBodyContract(otherDomain,member));
            var wrongSchema=new DomainBodies.BodyRef(member.slot(),"wrong-schema",member.payload(),member.identity(),member.producerSources());
            assertFalse(holder.isDomainBodyContract(domain,wrongSchema));
            assertEquals(member,DomainBodies.reference(head.state(),contract.slot()).orElseThrow());
            assertSame(state,head.state());assertEquals(0,head.state().sequence());
        }
    }
    @Test void actualHolderKeepsTheTwoBodyContractsAcrossJavaProducerTraceChanges() {
        var lock=Path.of("synthetic-governance-no-writer-created.lock").toAbsolutePath();
        var materials=new CrownRetryPublication.MaterialPort() {
            @Override public CrownRetryPublication.Material capture(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,CrownRetryPublication.Input input,Instant callerDeadline) {throw new AssertionError("registration metadata must not execute a native query or publication");}
            @Override public void requireCurrent(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,CrownRetryPublication.Input input,ObservationIdentity current,G2Source source,Instant callerDeadline) {throw new AssertionError("no runtime qualification in this test");}
        };
        var retry=new CrownRetryPublication(lock,CROWN_SCHEMA,List.of(REF),List.of(REF),materials,(id,body)->{throw new AssertionError("no writer in metadata test");});
        var holder=new RootGovernanceDomains(lock,new RootGovernanceDomains.Sources(REF,List.of(REF),List.of(REF)),retry);
        assertSame(holder.domainRegistrations(),holder.domainRegistrations());assertSame(holder.domainRegistrations().get(0),holder.domainRegistrations().get(0));assertSame(holder.domainRegistrations().get(1),holder.domainRegistrations().get(1));
        assertEquals(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.COUNCIL,holder.domainRegistrations().get(0).slot());assertEquals(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CROWN,holder.domainRegistrations().get(1).slot());
        var other=new ExactRef("another-original-producer",1,"b".repeat(64));
        var rebuilt=new RootGovernanceDomains(lock,new RootGovernanceDomains.Sources(REF,List.of(REF),List.of(other)),retry);
        assertEquals(List.of(other),rebuilt.domainRegistrations().get(1).producerSources());
        assertEquals(List.of(REF),retry.registration().producerSources());
        var wrongSchema=new CrownRetryPublication(lock,"wrong-crown-schema",List.of(REF),List.of(REF),materials,(id,body)->{throw new AssertionError("no writer in metadata test");});
        assertThrows(IllegalArgumentException.class,()->new RootGovernanceDomains(lock,new RootGovernanceDomains.Sources(REF,List.of(REF),List.of(other)),wrongSchema));
    }
}
