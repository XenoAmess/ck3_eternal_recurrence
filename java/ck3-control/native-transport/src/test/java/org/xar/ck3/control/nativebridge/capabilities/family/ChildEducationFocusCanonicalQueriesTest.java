package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Software scope/source boundaries only. No Root, native, writer or Game qualification is synthesized. */
final class ChildEducationFocusCanonicalQueriesTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final G2Source SOURCE=new G2Source("synthetic-focus-machine",NOW.toString(),"1.20.0.4",ref("source",1));
    private static final Frame PRE=new Frame("native:53","synthetic-focus-episode",BigInteger.valueOf(53),53220000,101);
    @TempDir Path directory;

    @Test void typedQueryEncodingPreservesFullIntegerFieldsAndExactShape() {
        var typed=new ChildEducationFocusQueries.QueryArguments(StrictJson.UINT64_MAX,new Selection(0xFE000001L,Key.EDUCATION_MARTIAL));
        Obj encoded=ChildEducationFocusQueries.queryArguments(typed);
        assertEquals(typed,ChildEducationFocusQueries.queryArguments(encoded));
        assertEquals(java.util.Set.of("expected_revision","child_full_id","target_key"),encoded.members().keySet());
    }
    @Test void typedReceiptEncodingRetainsTheOriginalUnknownPendingWithoutInventingAcceptance() {
        var typed=new ChildEducationFocusQueries.ReceiptArguments(BigInteger.valueOf(56),pending("focus-attempt-1"));
        Obj encoded=ChildEducationFocusQueries.receiptArguments(typed);
        assertEquals(typed,ChildEducationFocusQueries.receiptArguments(encoded));
        var original=OpportunityJson.toNode(encoded).get("pending");
        assertTrue(original.get("accepted").isNull());assertTrue(original.get("native_command_submitted").isNull());
    }
    @Test void argumentParsersRejectMissingNullFloatingAndBooleanRevisions() {
        var query=OpportunityJson.toNode(ChildEducationFocusQueries.queryArguments(new ChildEducationFocusQueries.QueryArguments(BigInteger.valueOf(56),selection())));
        for(var invalid:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(56.0),StrictJson.object().nullNode())) {
            var value=((ObjectNode)query).deepCopy();value.set("expected_revision",invalid);
            assertThrows(IllegalArgumentException.class,()->ChildEducationFocusQueries.queryArguments(app(value)));
        }
        var missing=((ObjectNode)query).deepCopy();missing.remove("expected_revision");
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusQueries.queryArguments(app(missing)));
    }
    @Test void canonicalContextUsesItsFactualCurrentFrameAndKeepsOriginalBeforeSeparate() {
        PlanningReadRequest request=request(pending("focus-attempt-1"));
        assertThrows(IllegalStateException.class,request::before);
        var actual=ChildEducationFocusQueries.context(request);
        assertEquals(BigInteger.valueOf(54),actual.frame().nativeRevision());assertEquals(BigInteger.valueOf(56),actual.publicRevision());
        assertEquals(PRE.episode(),actual.frame().episode());assertEquals(101,actual.frame().controller());
    }
    @Test void canonicalDefinitionReusesTheActualNativeSourceAndHasAnIndependentGuardProfile() throws Exception {
        var ordinary=ordinary();var canonical=ChildEducationFocusQueries.reconciliationReceipt(ordinary.receipt(),profile(),admission(new AtomicInteger()));
        assertSame(ordinary.receipt().sourceRef(),canonical.sourceRef());
        assertEquals(ChildEducationFocusQueries.RECONCILIATION_RECEIPT_CONTRACT,canonical.contractId());
        assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION,canonical.guardMode());assertTrue(canonical.hasPureReplay());
        assertEquals(ordinary.receipt().operation(),canonical.operation());assertEquals(ordinary.receipt().permissionKey(),canonical.permissionKey());
    }
    @Test void softwareCanonicalRequestInvokesOnlyItsCurrentCallbackAndPreservesOriginalNativeFields() throws Exception {
        var calls=new AtomicInteger();var canonical=ChildEducationFocusQueries.reconciliationReceipt(ordinary().receipt(),profile(),admission(calls));
        var request=request(pending("focus-attempt-1"));var nativeRequest=canonical.prepare(request,"independent-read-1");
        assertEquals(1,calls.get());assertEquals(ChildEducationFocus.RECEIPT_STEP,nativeRequest.step());
        var expected=ChildEducationFocusQueries.nativeRequest(new OperationKey(ChildEducationFocus.RECEIPT_STEP),
                ChildEducationFocusQueries.context(request),selection(),Optional.of("focus-attempt-1"));
        assertArrayEquals(expected.additionalFields().bytes(),nativeRequest.additionalFields().bytes());
    }
    @Test void canonicalRequestRejectsAnotherPendingAttemptBeforeTheRootCallback() throws Exception {
        var calls=new AtomicInteger();var canonical=ChildEducationFocusQueries.reconciliationReceipt(ordinary().receipt(),profile(),admission(calls));
        assertThrows(IllegalArgumentException.class,()->canonical.prepare(request(pending("foreign-attempt")),"independent-read-1"));
        assertEquals(0,calls.get());
    }
    @Test void canonicalRequestRejectsAnotherOriginalPreFrameAndNeverUsesLegacyDriverAdmission() throws Exception {
        var calls=new AtomicInteger();var canonical=ChildEducationFocusQueries.reconciliationReceipt(ordinary().receipt(),profile(),admission(calls));
        ObjectNode changed=StrictJson.object(StrictJson.parse(pending("focus-attempt-1").original().bytes()),
                java.util.Set.of("schema","kind","status","unavailable_reason","action_request_id","accepted","child_full_id","requested_focus_key",
                        "pre_frame","native_command_submitted","request_id","source_public_revision","source_context"));
        ((ObjectNode)changed.get("pre_frame")).put("date_raw",53219999);
        ((ObjectNode)changed.get("source_context")).put("date_raw",53219999);
        var pending=ChildEducationFocus.decodePending(new RawJson(StrictJson.canonical(changed)));
        assertThrows(IllegalArgumentException.class,()->canonical.prepare(request(pending),"independent-read-1"));assertEquals(0,calls.get());
    }
    @Test void changedProfileSourceRefusesBeforeAnyCanonicalAdmission() throws Exception {
        var calls=new AtomicInteger();ExactRef profile=profile();var canonical=ChildEducationFocusQueries.reconciliationReceipt(ordinary().receipt(),profile,admission(calls));
        Files.writeString(Path.of(profile.path()),"changed profile",StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->canonical.prepare(request(pending("focus-attempt-1")),"independent-read-1"));assertEquals(0,calls.get());
    }
    @Test void ordinaryReceiptDoesNotAcquireCanonicalPermissionAndWrongNativeSourceProfileRejects() throws Exception {
        var ordinary=ordinary();assertThrows(IllegalArgumentException.class,()->ordinary.receipt().prepare(request(pending("focus-attempt-1")),"independent-read-1"));
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusQueries.reconciliationReceipt(ordinary.query(),profile(),admission(new AtomicInteger())));
    }
    private static ChildEducationFocusQueries.Contracts ordinary() {
        return ChildEducationFocusQueries.contracts(ref("native-producer",2),(request,pending)->{throw new AssertionError("canonical path must not call legacy Driver-history admission");});
    }
    private static ChildEducationFocusQueries.CanonicalAdmission admission(AtomicInteger current) {
        return new ChildEducationFocusQueries.CanonicalAdmission(){
            @Override public void verifyCurrent(PlanningReadRequest request,Pending pending){current.incrementAndGet();}
            @Override public void verifyOriginal(PlanningReadReceipt receipt,Pending pending){throw new AssertionError("software request preparation must not manufacture an original receipt");}
        };
    }
    private ExactRef profile() throws Exception {
        Path path=directory.resolve("actual-profile-source.java");byte[] bytes="source-shaped software fixture only".getBytes(StandardCharsets.UTF_8);Files.write(path,bytes);
        return new ExactRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static PlanningReadRequest request(Pending pending) {
        var before=identity(53,55);var current=identity(54,56);
        var original=new ReconciliationIdentity.Pending("synthetic-focus-action","1".repeat(64),"focus-attempt-1",before,ref("original-receipt",3),ref("original-driver",4));
        var evidence=new ReconciliationIdentity.Evidence(ref("current-native",5),ref("current-hello",6),ref("heartbeat",7),ref("current-driver",8),ref("current-observation",9),ref("current-source",10));
        var reconciliation=new ReconciliationIdentity(current,SOURCE,"synthetic-focus-session",BigInteger.TWO,original,evidence,NOW);
        return PlanningReadRequest.newReconciliation(reconciliation,new OperationKey(ChildEducationFocus.RECEIPT_STEP),
                ChildEducationFocusQueries.receiptArguments(new ChildEducationFocusQueries.ReceiptArguments(BigInteger.valueOf(56),pending)),NOW.plusSeconds(30));
    }
    private static ObservationIdentity identity(int nativeRevision,int publicRevision) {
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(PRE.dateRaw())),
                "native:"+nativeRevision,BigInteger.valueOf(publicRevision),PRE.episode());
        return new ObservationIdentity(SOURCE.machineId(),game,frame,1);
    }
    private static Pending pending(String action) {
        var n=StrictJson.object().put("schema",ChildEducationFocus.SCHEMA).put("kind","submit").put("status","action_state_unknown")
                .putNull("unavailable_reason").put("action_request_id",action).putNull("accepted").put("child_full_id",202)
                .put("requested_focus_key",selection().target().wire()).putNull("native_command_submitted").put("request_id",action).put("source_public_revision",55);
        n.set("pre_frame",ChildEducationFocus.encodeFrame(PRE));n.set("source_context",ChildEducationFocus.encodeContext(new Context(PRE,BigInteger.valueOf(55))));
        return ChildEducationFocus.decodePending(new RawJson(StrictJson.canonical(n)));
    }
    private static Selection selection(){return new Selection(202,Key.EDUCATION_STEWARDSHIP);}
    private static Obj app(ObjectNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"software focus arguments");}
    private static ExactRef ref(String path,int digit){return new ExactRef("synthetic/"+path,1,Integer.toHexString(digit%15+1).repeat(64));}
}
