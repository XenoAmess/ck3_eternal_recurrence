package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Durable action metadata. Native originals are archived once and read with exact byte/SHA identity by OutcomeArchive. */

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Public codec DATA only. No writer, packet submission, permit or Guard is issued here. */
final class ReceiptCommandProjection76Test {
    private static final Instant NOW=Instant.parse("2026-10-24T03:00:00Z");
    private static final String MACHINE="numeric-command-contract";
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final ExactRef SOURCE_REF=new ExactRef("contract-data/source.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source(MACHINE,NOW.toString(),"1.20.0.4",SOURCE_REF);
    private static final ExactRef FAILING_DISPATCH=new ExactRef("contract-data/not-a-dispatch-original",1,"b".repeat(64));
    private static final String EMPTY_STATE="{\"kind\":\"INTENT_DURABLE\"}";

    @Test void originalNumericLexemesAndLargeNonCommandMaterialMatchCompleteLegacy() {
        String numbers="{\"event_resolution\":{\"negative_zero\":-0.0,\"zero\":0.0,\"decimal_integer\":1.0,\"trailing\":1.2300,\"exponent\":1E+3,\"wide\":1e10000,\"huge\":"
                +"9".repeat(120)+",\"nested\":[-0.0,1,1.0,null,true,\"😀\"],\"keys\":{\"\":1,\"😀\":2}}}";
        ActionCommand command=command("numeric-original",args(numbers));
        ActionReceipt expected=receipt(command,new ActionState.IntentDurable());
        byte[] raw=LegacyActionReceiptCodec.encodeReceipt(expected,null);
        for(boolean reuse:List.of(false,true)) {
            assertEquivalentSuccess(raw,expected,reuse);
            String canonical=new String(ActionCodec.encodeCommand(decode(false,raw,new Probe().archive(),reuse).command()),StandardCharsets.UTF_8);
            assertTrue(canonical.contains("\"negative_zero\":-0.0"));
            assertTrue(canonical.contains("\"trailing\":1.2300"));
            assertTrue(canonical.contains("\"exponent\":1E+3"));
            assertTrue(canonical.contains("1e10000"));
        }
        // The repeated ExactRefs are ordinary DATA, not physical originals or archival authority.
        ExactRef opaque=new ExactRef("contract-data/opaque-"+"x".repeat(32),1,"c".repeat(64));
        ActionReceipt wide=receipt(command("wide-metadata",args("{}")),new ActionState.Unknown(
                Optional.empty(),Optional.empty(),"unresolved DATA",Collections.nCopies(9000,opaque)));
        byte[] wideRaw=LegacyActionReceiptCodec.encodeReceipt(wide,null);
        assertTrue(wideRaw.length>1024*1024&&wideRaw.length<=ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES,
                "complete noncommand receipt material exercises its real two MiB role, not StrictJson's default lane");
        for(boolean reuse:List.of(false,true))assertEquivalentSuccess(wideRaw,wide,reuse);
    }

    @Test void commandDepthAndAllNonCommandLexicalValidationRetainWholePayloadBoundaries() {
        ActionCommand edge=command("depth-original",args("{\"deep\":"+arrays(61)+"}"));
        ActionReceipt original=receipt(edge,new ActionState.IntentDurable());
        byte[] edgeRaw=LegacyActionReceiptCodec.encodeReceipt(original,null);
        for(boolean reuse:List.of(false,true))assertEquivalentSuccess(edgeRaw,original,reuse);
        String edgeText=new String(edgeRaw,StandardCharsets.UTF_8);
        String tooDeep=edgeText.replace("\"deep\":"+arrays(61),"\"deep\":"+arrays(62));
        assertNotEquals(edgeText,tooDeep);
        ActionCommand small=command("validation-original",args("{}"));
        byte[] deepState=wire(small,"1","1",ActionReceiptCodec.SCHEMA,
                "{\"kind\":\"INTENT_DURABLE\",\"unused\":"+arrays(63)+"}");
        byte[] duplicate=wire(small,"1","1",ActionReceiptCodec.SCHEMA,
                "{\"kind\":\"INTENT_DURABLE\",\"kind\":\"INTENT_DURABLE\"}");
        byte[] trailing=concat(wire(small,"1","1",ActionReceiptCodec.SCHEMA,EMPTY_STATE)," true".getBytes(StandardCharsets.UTF_8));
        byte[] badTail=concat(wire(small,"1","1","wrong-schema",EMPTY_STATE),new byte[]{(byte)0xc3});
        byte[] lone=wire(small,"1","1",ActionReceiptCodec.SCHEMA,
                "{\"kind\":\"INTENT_DURABLE\",\"unused\":\""+"\\"+"uD800\"}");
        for(byte[] invalid:List.of(tooDeep.getBytes(StandardCharsets.UTF_8),deepState,duplicate,trailing,badTail,lone))
            for(boolean reuse:List.of(false,true))assertEquivalentFailure(invalid,reuse,List.of(),null);
        for(boolean reuse:List.of(false,true)) {
            assertEquivalentFailure(null,reuse,List.of(),null);
            assertEquivalentFailure(new byte[0],reuse,List.of(),null);
            assertEquivalentFailure(new byte[ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES+1],reuse,List.of(),null);
        }
    }

    @Test void SchemaPrecedesSecondParseAndMetadataDecimalsFailAfterTheOriginalCommandCallback() {
        ActionCommand small=command("metadata-original",args("{}"));
        byte[] wrongSchemaDeep=wire(small,"1","1","wrong-schema",
                "{\"kind\":\"INTENT_DURABLE\",\"unused\":"+arrays(63)+"}");
        for(boolean reuse:List.of(false,true)) {
            Throwable failure=assertEquivalentFailure(wrongSchemaDeep,reuse,List.of(),null);
            assertEquals("exact action receipt schema required",failure.getMessage());
            for(String token:List.of("1.0","1.00","1e0","-0.0")) {
                List<String> expectedCalls=reuse?List.of("command"):List.of();
                Throwable badVersion=assertEquivalentFailure(wire(small,token,"1",ActionReceiptCodec.SCHEMA,EMPTY_STATE),reuse,expectedCalls,null);
                assertEquals("exact JSON integer required; no boolean, float or string",badVersion.getMessage());
                Throwable badSequence=assertEquivalentFailure(wire(small,"1",token,ActionReceiptCodec.SCHEMA,EMPTY_STATE),reuse,expectedCalls,null);
                assertEquals("exact JSON integer required; no boolean, float or string",badSequence.getMessage());
            }
            // These whole metadata trees remain in the original BigDecimal lane; neither token becomes an integer.
            var metadata=ProposalLifecycleCodec.decodePayload(wire(small,"1.00","1e0",ActionReceiptCodec.SCHEMA,EMPTY_STATE),ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
            assertTrue(metadata.get("version").isBigDecimal());assertTrue(metadata.get("sequence").isBigDecimal());
        }
    }

    @Test void ArchiveCallbacksReentryFailuresAndCallerMutationPreserveActualOrdering() {
        ActionCommand small=command("callback-original",args("{}"));
        ActionReceipt good=receipt(small,new ActionState.IntentDurable());
        byte[] raw=LegacyActionReceiptCodec.encodeReceipt(good,null);
        String failingState="{\"kind\":\"UNKNOWN\",\"attempt\":null,\"dispatch_ref\":"+FAILING_DISPATCH.toJson()
                +",\"reason\":\"unresolved DATA\",\"evidence\":[]}";
        byte[] callbackRaw=wire(small,"1","1",ActionReceiptCodec.SCHEMA,failingState);
        IllegalStateException originalFailure=new IllegalStateException("specific original archive failure");
        for(boolean reuse:List.of(false,true)) {
            List<String> order=reuse?List.of("command","load:"+FAILING_DISPATCH.sha256()):List.of("load:"+FAILING_DISPATCH.sha256());
            assertSame(originalFailure,assertEquivalentFailure(callbackRaw,reuse,order,originalFailure));
        }
        for(boolean legacy:List.of(true,false)) {
            Probe failed=new Probe();failed.commandFailure=originalFailure;
            assertSame(originalFailure,assertThrows(IllegalStateException.class,()->decode(legacy,callbackRaw,failed.archive(),true)));
            assertEquals(List.of("command"),failed.calls);
            Probe reentrant=new Probe();ActionPorts.OutcomeArchive archive=reentrant.archive();
            ActionReceipt nested=receipt(command("nested-original",args("{\"score\":-0.0}")),new ActionState.IntentDurable());
            byte[] nestedRaw=LegacyActionReceiptCodec.encodeReceipt(nested,null);
            reentrant.duringCommand=()->assertEquals(nested,decode(legacy,nestedRaw,archive,true));
            assertEquals(good,decode(legacy,raw,archive,true));
            assertEquals(List.of("command","command"),reentrant.calls);
            reentrant.calls.clear();assertEquals(good,decode(legacy,raw,archive,true));
            assertEquals(List.of("command"),reentrant.calls);
            Probe mutation=new Probe();byte[] caller=raw.clone();
            mutation.duringCommand=()->Arrays.fill(caller,(byte)'!');
            assertEquals(good,decode(legacy,caller,mutation.archive(),true));
            assertEquals((byte)'!',caller[0]);assertEquals(List.of("command"),mutation.calls);
            assertEquals(good,decode(legacy,raw,null,true),"null archive preserves the original nonreuse command decoder");
        }
    }

    private static void assertEquivalentSuccess(byte[] raw,ActionReceipt expected,boolean reuse) {
        byte[] before=raw.clone();Probe left=new Probe(),right=new Probe();
        ActionReceipt old=decode(true,raw,left.archive(),reuse),actual=decode(false,raw,right.archive(),reuse);
        assertEquals(expected,old);assertEquals(old,actual);assertEquals(expected.command().arguments(),actual.command().arguments());
        assertArrayEquals(LegacyActionReceiptCodec.encodeReceipt(old,left.archive()),ActionReceiptCodec.encodeReceipt(actual,right.archive()));
        assertEquals(ActionCodec.bodySha256(old.command()),ActionCodec.bodySha256(actual.command()));
        assertEquals(left.calls,right.calls);assertEquals(reuse?List.of("command"):List.of(),right.calls);
        assertArrayEquals(before,raw);
    }
    private static Throwable assertEquivalentFailure(byte[] raw,boolean reuse,List<String> calls,RuntimeException sharedFailure) {
        Probe left=new Probe(),right=new Probe();left.loadFailure=sharedFailure;right.loadFailure=sharedFailure;
        Throwable old=assertThrows(RuntimeException.class,()->decode(true,raw,left.archive(),reuse));
        Throwable actual=assertThrows(RuntimeException.class,()->decode(false,raw,right.archive(),reuse));
        assertEquals(failureData(old),failureData(actual),"complete messages, causes, suppressed errors and parser locations stay exact");
        assertEquals(calls,left.calls);assertEquals(calls,right.calls);
        if(sharedFailure!=null){assertSame(sharedFailure,old);assertSame(sharedFailure,actual);}
        return actual;
    }
    private static ActionReceipt decode(boolean legacy,byte[] raw,ActionPorts.OutcomeArchive archive,boolean reuse) {
        if(legacy)return reuse?LegacyActionReceiptCodec.decodeReceiptUsingCanonicalCommand(raw,archive):LegacyActionReceiptCodec.decodeReceipt(raw,archive);
        return reuse?ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(raw,archive):ActionReceiptCodec.decodeReceipt(raw,archive);
    }
    private record FailureData(String type,String message,String location,FailureData cause,List<FailureData> suppressed) { }
    private static FailureData failureData(Throwable value) {
        String location=null;
        if(value instanceof JsonProcessingException json&&json.getLocation()!=null) {
            var at=json.getLocation();location=at.getByteOffset()+":"+at.getCharOffset()+":"+at.getLineNr()+":"+at.getColumnNr();
        }
        return new FailureData(value.getClass().getName(),value.getMessage(),location,value.getCause()==null?null:failureData(value.getCause()),
                Arrays.stream(value.getSuppressed()).map(ReceiptCommandProjection76Test::failureData).toList());
    }
    private static final class Probe implements InvocationHandler {
        final List<String> calls=new ArrayList<>();
        RuntimeException commandFailure,loadFailure;Runnable duringCommand;
        ActionPorts.OutcomeArchive archive() {
            return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] arguments) {
            if(method.getDeclaringClass()==Object.class)return switch(method.getName()) {
                case "toString"->"receipt-codec public DATA archive";case "hashCode"->System.identityHashCode(proxy);case "equals"->proxy==arguments[0];
                default->throw new AssertionError(method.getName());
            };
            if(method.getName().equals("decodeCanonicalCommand")) {
                calls.add("command");if(commandFailure!=null)throw commandFailure;
                Runnable callback=duringCommand;duringCommand=null;if(callback!=null)callback.run();
                return ActionCodec.decodeCommand((byte[])arguments[0]);
            }
            if(method.getName().equals("load")) {
                calls.add("load:"+((ExactRef)arguments[0]).sha256());
                if(loadFailure!=null)throw loadFailure;
            }
            throw new AssertionError("unexpected public archive callback "+method.getName());
        }
    }
    private static OpportunityJson.Obj args(String raw) {
        return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),ActionCommand.MAX_ARGUMENT_BYTES);
    }
    // Public gameplay DATA constructor adapted from the complete original ActionCodecNumericTokenTest.
    private static ActionCommand command(String id,OpportunityJson.Obj arguments) {
        var before=new ProposalLifecycle.ObservationIdentity(MACHINE,GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(100)),"native:2",BigInteger.TWO,"episode-decimal"),1);
        var expected=new ExpectedPostcondition(1,before,SOURCE,"numeric-contract/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("ready"),true)));
        return new ActionCommand(id,before,SOURCE,"ordinary-session",new OperationKey("select-event-option-1"),arguments,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
    }
    private static ActionReceipt receipt(ActionCommand command,ActionState state) {
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),state);
    }
    private static String arrays(int count) {return "[".repeat(count)+"0"+"]".repeat(count);}
    private static byte[] concat(byte[] first,byte[] tail) {
        byte[] joined=Arrays.copyOf(first,first.length+tail.length);System.arraycopy(tail,0,joined,first.length,tail.length);return joined;
    }
    private static byte[] wire(ActionCommand command,String version,String sequence,String schema,String state) {
        return ("{\"schema\":\""+schema+"\",\"version\":"+version+",\"sequence\":"+sequence
                +",\"command\":"+new String(ActionCodec.encodeCommand(command),StandardCharsets.UTF_8)
                +",\"body_sha256\":\""+ActionCodec.bodySha256(command)+"\",\"state\":"+state+"}").getBytes(StandardCharsets.UTF_8);
    }

    // LEGACY_WHOLE_BASE_BEGIN: only nested static placement, class/ctor rename and indentation differ.
    public static final class LegacyActionReceiptCodec {
        public static final String SCHEMA = "xar.java-action-receipt/v1";
        public static final String EVOLVED_SCHEMA = "xar.java-action-receipt/v2";
        public static final String PROVENANCE_SCHEMA = "xar.java-action-receipt/v3";
        public static final String FAMILY_SEND_SCHEMA = "xar.java-action-receipt/v4";
        public static final String PHYSICAL_SCHEMA = "xar.java-action-receipt/v5";
        public static final String RECONCILED_CONTROL_SCHEMA = "xar.java-action-receipt/v6";
        public static final String OPERATOR_SCHEMA = "xar.java-action-receipt/v7";
        public static final String PAUSE_CONTROL_SCHEMA = "xar.java-action-receipt/v8";
        public static final String DIRECT_WINDOW_SCHEMA = "xar.java-action-receipt/v9";
        public static final String COMPOSITE_FAILURE_EVIDENCE_SCHEMA = "xar.java-action-receipt/v10";
        public static final String FIXTURE_SCHEMA = "xar.java-action-receipt/v11";
        public static final String COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA = "xar.java-action-receipt/v12";
        public static final String LIFE_CONTROL_PREFIX_SCHEMA = "xar.java-action-receipt/v13";
        public static final String INTENT_ABANDONED_SCHEMA = "xar.java-action-receipt/v14";
        public static final String FRESH_SNAPSHOT_QUERY_SCHEMA = "xar.java-action-receipt/v15";
        public static final String TIMELINE_AFTER_ACK_SCHEMA = "xar.java.timeline-physical-after-ack-receipt/v1";
        public static final int MAXIMUM_RECEIPT_BYTES = 2 * 1024 * 1024;
        private LegacyActionReceiptCodec() { }
        public static byte[] encodeReceipt(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
            if (receipt.state() instanceof ActionState.CompositeOperatorQuarantined) return CompositeOperatorQuarantineReceiptCodec.encodeReceipt(receipt, archive);
            boolean evolved = !(receipt.command().origin() instanceof CommandOrigin.Gameplay) || evolved(receipt.state());
            boolean typed = containsPush(receipt.state()) || containsFreshSnapshotQuery(receipt.state()) || containsPhysicalAfterAcknowledgement(receipt.state()); boolean family = containsFamilySend(receipt.state());
            ObjectNode row = StrictJson.object(); row.put("schema", containsPhysicalAfterAcknowledgement(receipt.state()) ? TIMELINE_AFTER_ACK_SCHEMA : containsFreshSnapshotQuery(receipt.state()) ? FRESH_SNAPSHOT_QUERY_SCHEMA : receipt.state() instanceof ActionState.IntentAbandoned ? INTENT_ABANDONED_SCHEMA : lifeControlPrefix(receipt) ? LIFE_CONTROL_PREFIX_SCHEMA : compositeNoGameplayWrite(receipt) ? COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA : fixture(receipt) ? FIXTURE_SCHEMA : compositeFailureEvidence(receipt) ? COMPOSITE_FAILURE_EVIDENCE_SCHEMA : directWindow(receipt) ? DIRECT_WINDOW_SCHEMA : pauseControl(receipt) ? PAUSE_CONTROL_SCHEMA : operator(receipt) ? OPERATOR_SCHEMA : containsReconciledControl(receipt.state()) ? RECONCILED_CONTROL_SCHEMA : extended(receipt.state()) ? PHYSICAL_SCHEMA : family ? FAMILY_SEND_SCHEMA : containsFreshSnapshotQuery(receipt.state()) ? FRESH_SNAPSHOT_QUERY_SCHEMA : typed ? PROVENANCE_SCHEMA : evolved ? EVOLVED_SCHEMA : SCHEMA); row.put("version", receipt.version()); row.put("sequence", receipt.sequence());
            row.put("body_sha256", receipt.bodySha256()); row.set("state", state(receipt.state(), archive, evolved || typed || family, typed, family));
            // The sole command codec owns numeric tokens in arguments. A JsonNode round trip here
            // would erase decimal category/negative zero and change the durable command body SHA.
            var headers = DriverJson.object(ProposalLifecycleCodec.encodePayload(row, MAXIMUM_RECEIPT_BYTES), MAXIMUM_RECEIPT_BYTES);
            var command = DriverJson.object(ActionCodec.encodeCommand(receipt.command()), ActionCodec.MAX_COMMAND_BYTES);
            byte[] encoded = PublicDataJson.encodeTyped(headers.with("command", command)).bytes();
            StrictJson.require(encoded.length <= MAXIMUM_RECEIPT_BYTES, "bounded action receipt required");
            return encoded;
        }
        public static ActionReceipt decodeReceipt(byte[] bytes, ActionPorts.OutcomeArchive archive) {
            return decodeReceipt(bytes, archive, false);
        }
        /** Explicit pure-DATA reuse entry. Legacy archive adapters keep the original two-argument dispatch. */
        public static ActionReceipt decodeReceiptUsingCanonicalCommand(byte[] bytes, ActionPorts.OutcomeArchive archive) {
            return decodeReceipt(bytes, archive, true);
        }
        private static ActionReceipt decodeReceipt(byte[] bytes, ActionPorts.OutcomeArchive archive, boolean reuseCanonicalCommand) {
            JsonNode document = ProposalLifecycleCodec.decodePayload(bytes, MAXIMUM_RECEIPT_BYTES);
            if (CompositeOperatorQuarantineReceiptCodec.SCHEMA.equals(document.path("schema").asText())) return CompositeOperatorQuarantineReceiptCodec.decodeReceipt(document, archive);
            ObjectNode row = StrictJson.object(document, Set.of("schema", "version", "sequence", "command", "body_sha256", "state"));
            String schema = text(row, "schema"); StrictJson.require(SCHEMA.equals(schema) || EVOLVED_SCHEMA.equals(schema) || PROVENANCE_SCHEMA.equals(schema) || FAMILY_SEND_SCHEMA.equals(schema) || PHYSICAL_SCHEMA.equals(schema) || RECONCILED_CONTROL_SCHEMA.equals(schema) || OPERATOR_SCHEMA.equals(schema) || PAUSE_CONTROL_SCHEMA.equals(schema) || DIRECT_WINDOW_SCHEMA.equals(schema) || COMPOSITE_FAILURE_EVIDENCE_SCHEMA.equals(schema) || FIXTURE_SCHEMA.equals(schema) || COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA.equals(schema) || LIFE_CONTROL_PREFIX_SCHEMA.equals(schema) || INTENT_ABANDONED_SCHEMA.equals(schema) || FRESH_SNAPSHOT_QUERY_SCHEMA.equals(schema) || TIMELINE_AFTER_ACK_SCHEMA.equals(schema), "exact action receipt schema required");
            OpportunityJson.Obj originalCommand = OpportunityJson.object(DriverJson.object(bytes, MAXIMUM_RECEIPT_BYTES).get("command"), "original receipt command");
            byte[] canonicalCommand = PublicDataJson.encodeTyped(originalCommand).bytes();
            ActionCommand command = !reuseCanonicalCommand || archive == null ? ActionCodec.decodeCommand(canonicalCommand)
                    : archive.decodeCanonicalCommand(canonicalCommand);
            ActionReceipt receipt = new ActionReceipt(Math.toIntExact(StrictJson.integer(row.get("version"), 1, 1)), StrictJson.integer(row.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                    command, text(row, "body_sha256"), state(row.get("state"), archive, !SCHEMA.equals(schema), PROVENANCE_SCHEMA.equals(schema) || PAUSE_CONTROL_SCHEMA.equals(schema) || FRESH_SNAPSHOT_QUERY_SCHEMA.equals(schema) || TIMELINE_AFTER_ACK_SCHEMA.equals(schema), FAMILY_SEND_SCHEMA.equals(schema)));
            String expectedSchema = containsPhysicalAfterAcknowledgement(receipt.state()) ? TIMELINE_AFTER_ACK_SCHEMA : containsFreshSnapshotQuery(receipt.state()) ? FRESH_SNAPSHOT_QUERY_SCHEMA : receipt.state() instanceof ActionState.IntentAbandoned ? INTENT_ABANDONED_SCHEMA : lifeControlPrefix(receipt) ? LIFE_CONTROL_PREFIX_SCHEMA : compositeNoGameplayWrite(receipt) ? COMPOSITE_NO_GAMEPLAY_WRITE_SCHEMA : fixture(receipt) ? FIXTURE_SCHEMA : compositeFailureEvidence(receipt) ? COMPOSITE_FAILURE_EVIDENCE_SCHEMA : directWindow(receipt) ? DIRECT_WINDOW_SCHEMA : pauseControl(receipt) ? PAUSE_CONTROL_SCHEMA : operator(receipt) ? OPERATOR_SCHEMA : containsReconciledControl(receipt.state()) ? RECONCILED_CONTROL_SCHEMA : extended(receipt.state()) ? PHYSICAL_SCHEMA : containsFamilySend(receipt.state()) ? FAMILY_SEND_SCHEMA : containsFreshSnapshotQuery(receipt.state()) ? FRESH_SNAPSHOT_QUERY_SCHEMA : containsPush(receipt.state()) ? PROVENANCE_SCHEMA
                    : !(command.origin() instanceof CommandOrigin.Gameplay) || evolved(receipt.state()) ? EVOLVED_SCHEMA : SCHEMA;
            StrictJson.require(expectedSchema.equals(schema), "receipt schema must describe its exact origin/evidence/provenance version");
            return receipt;
        }
        private static boolean fixture(ActionReceipt receipt){
            var settlement=receipt.state() instanceof ActionState.Settled settled?settled.settlement()
                    :receipt.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
            if(settlement instanceof ActionState.FixtureStarted started){
                StrictJson.require(receipt.state() instanceof ActionState.Settled,"fixture Start is one original native primitive");
                var primitive=(ActionState.Settled)receipt.state();started.observation().validate(receipt.command(),primitive.attempt(),primitive.dispatch());return true;
            }
            if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
                StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,"fixture business settles only its upfront composite");
                completed.observation().validateParent(receipt.command());return true;
            }
            if(FixturePlan.isParent(receipt.command())){FixturePlan.requireParent(receipt.command());return true;}
            return false;
        }
        private static boolean compositeFailureEvidence(ActionReceipt receipt) {
            return receipt.state() instanceof ActionState.CompositeSettled settled
                    && settled.settlement() instanceof ActionState.CompositeRejected rejected && !rejected.evidence().isEmpty();
        }
        private static boolean lifeControlPrefix(ActionReceipt receipt) {
            var value = receipt.state() instanceof ActionState.Settled primitive ? primitive.settlement()
                    : receipt.state() instanceof ActionState.CompositeSettled composite ? composite.settlement() : null;
            if (!(value instanceof ActionState.LifeControlPrefixInterrupted terminal)) return false;
            StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,
                    "Life control-prefix interruption requires its original composite envelope");
            terminal.observation().validateParent(receipt.command(), ((ActionState.CompositeSettled) receipt.state()).execution());
            return true;
        }
        private static boolean compositeNoGameplayWrite(ActionReceipt receipt) {
            var value = receipt.state() instanceof ActionState.Settled primitive ? primitive.settlement()
                    : receipt.state() instanceof ActionState.CompositeSettled composite ? composite.settlement() : null;
            if (!(value instanceof ActionState.CompositeNoGameplayWrite terminal)) return false;
            StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled,
                    "no-gameplay-write terminal requires its original composite envelope");
            terminal.observation().validate(receipt.command(), ((ActionState.CompositeSettled) receipt.state()).execution());
            return true;
        }
        private static void requireCompositeFailureMaterial(ExactRef ref,ActionPorts.OutcomeArchive archive) {
            StrictJson.require(ref.bytes()>0,"actual composite failure material required");var bytes=archive.loadMaterial(ref).bytes();
            StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(ActionCodec.sha256(bytes)),"composite failure evidence original bytes changed");
        }
        private static boolean directWindow(ActionReceipt receipt) {
            var value = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                    : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            if (!(value instanceof ActionState.DirectFixedWindowCompleted completed)) return false;
            StrictJson.require(receipt.state() instanceof ActionState.Settled
                    && receipt.command().origin() instanceof CommandOrigin.Gameplay
                    && receipt.command().expectation() instanceof CommandExpectation.Gameplay,
                    "direct fixed-window execution completion is only a gameplay native primitive");
            var primitive = (ActionState.Settled) receipt.state();
            completed.completion().validate(receipt.command(), primitive.attempt(), primitive.dispatch());
            return true;
        }
        private static boolean pauseControl(ActionReceipt receipt) {
            var settlement = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                    : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            if (settlement instanceof ActionState.PauseConfirmed) {
                StrictJson.require(receipt.state() instanceof ActionState.Settled
                        && receipt.command().expectation() instanceof CommandExpectation.Gameplay
                        && receipt.command().operation().value().equals("pause-map"),
                        "pause confirmation belongs only to its original gameplay native primitive");
                return true;
            }
            if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
                StrictJson.require(receipt.state() instanceof ActionState.CompositeSettled, "control sequence requires its exact composite");
                org.xar.ck3.control.application.effects.control.ControlSequenceObservation.validateParent(receipt.command());
                StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(receipt.command()), ActionCodec.encodeCommand(sequence.observation().parent())),
                        "control sequence changed its original complete parent command");
                return true;
            }
            return false;
        }
        private static boolean operator(ActionReceipt receipt) {
            ActionState.Settlement settlement = receipt.state() instanceof ActionState.Settled settled ? settled.settlement()
                    : receipt.state() instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            boolean expected = receipt.command().expectation() instanceof CommandExpectation.OperatorRebind;
            StrictJson.require(!(settlement instanceof ActionState.OperatorRebound) || expected,
                    "operator settlement requires the exact operator command schema/expectation");
            StrictJson.require(!expected || !(receipt.state() instanceof ActionState.CompositeRunning
                    || receipt.state() instanceof ActionState.CompositeUnknown || receipt.state() instanceof ActionState.CompositeSettled
                    || receipt.state() instanceof PhysicalActionState), "operator identity rebind is only a native primitive");
            StrictJson.require(!expected || settlement == null || settlement instanceof ActionState.OperatorRebound || settlement instanceof ActionState.Rejected,
                    "operator command cannot reinterpret an ordinary gameplay/control settlement");
            return expected;
        }
        private static boolean containsReconciledControl(ActionState state) {
            var value = state instanceof ActionState.Settled settled ? settled.settlement()
                    : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            return value instanceof ActionState.ControlApplied control && control.reconciledAck().isPresent();
        }
        private static boolean extended(ActionState state) {
            return state instanceof PhysicalActionState || state instanceof ActionState.Settled settled
                    && (settled.settlement() instanceof ActionState.NativeSourceCompleted || settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed);
        }
        private static boolean evolved(ActionState state) {
            if (ActionTransitions.attempt(state).map(attempt -> !attempt.guard().supportingEvidence().isEmpty()).orElse(false)
                    || ActionTransitions.composite(state).map(execution -> !execution.guard().supportingEvidence().isEmpty()).orElse(false)) return true;
            ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                    : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            return settlement != null && (!(settlement instanceof ActionState.Applied || settlement instanceof ActionState.Rejected || settlement instanceof ActionState.ControlApplied)
                    || settlement instanceof ActionState.Applied applied && !applied.observation().supportingEvidence().isEmpty());
        }
        private static boolean containsFamilySend(ActionState state) {
            return state instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed;
        }
        private static boolean containsPush(ActionState state) {
            ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                    : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            return settlement instanceof ActionState.PauseConfirmed
                    || settlement instanceof ActionState.Applied applied && applied.observation().provenance() instanceof ObservationProvenance.Push
                    || settlement instanceof ActionState.CompositeControlApplied control && control.observation().semantic().provenance() instanceof ObservationProvenance.Push;
        }
        private static boolean containsFreshSnapshotQuery(ActionState state) {
            ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                    : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            return settlement instanceof ActionState.LifeControlPrefixInterrupted prefix && prefix.observation().ending().provenance() instanceof ObservationProvenance.FreshSnapshotQuery
                    || settlement instanceof ActionState.PauseConfirmed pause && pause.observation().provenance() instanceof ObservationProvenance.FreshSnapshotQuery
                    || settlement instanceof ActionState.Applied applied && applied.observation().provenance() instanceof ObservationProvenance.FreshSnapshotQuery
                    || settlement instanceof ActionState.CompositeControlApplied control && control.observation().semantic().provenance() instanceof ObservationProvenance.FreshSnapshotQuery;
        }
        private static boolean containsPhysicalAfterAcknowledgement(ActionState state) {
            ActionState.Settlement settlement = state instanceof ActionState.Settled settled ? settled.settlement()
                    : state instanceof ActionState.CompositeSettled settled ? settled.settlement() : null;
            return settlement instanceof ActionState.LifeControlPrefixInterrupted prefix && prefix.observation().ending().provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement
                    || settlement instanceof ActionState.PauseConfirmed pause && pause.observation().provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement
                    || settlement instanceof ActionState.Applied applied && applied.observation().provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement
                    || settlement instanceof ActionState.CompositeControlApplied control && control.observation().semantic().provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement;
        }
        private static ObjectNode state(ActionState state, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
            ObjectNode row = StrictJson.object();
            if (state instanceof PhysicalActionState physical) return PhysicalActionCodec.encode(physical, archive);
            if (state instanceof ActionState.IntentDurable) { row.put("kind", "INTENT_DURABLE"); return row; }
            if (state instanceof ActionState.IntentAbandoned value) {
                row.put("kind", "INTENT_ABANDONED"); row.set("original_intent_record", value.originalIntentRecord().toJson());
                row.set("original_action_head", value.originalActionHead().toJson()); return row;
            }
            if (ActionTransitions.composite(state).isPresent()) {
                row.put("kind", state instanceof ActionState.CompositeRunning ? "COMPOSITE_RUNNING" : state instanceof ActionState.CompositeUnknown ? "COMPOSITE_UNKNOWN" : "COMPOSITE_SETTLED");
                row.set("execution", execution(ActionTransitions.composite(state).orElseThrow()));
                if (state instanceof ActionState.CompositeUnknown unknown) { row.put("reason", unknown.reason()); var refs = row.putArray("evidence"); unknown.evidence().forEach(ref -> refs.add(ref.toJson())); }
                if (state instanceof ActionState.CompositeSettled settled) row.set("settlement", settlement(settled.settlement(), archive, evolved, typed, family)); return row;
            }
            if (state instanceof ActionState.Submitting value) { row.put("kind", "SUBMITTING"); row.set("attempt", attempt(value.attempt(), archive)); return row; }
            if (state instanceof ActionState.Unknown value) {
                row.put("kind", "UNKNOWN"); row.set("attempt", value.attempt().map(item -> (JsonNode) attempt(item, archive)).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
                row.set("dispatch_ref", value.dispatch().map(item -> (JsonNode) archive.referenceOf(item).toJson()).orElse(com.fasterxml.jackson.databind.node.NullNode.instance)); row.put("reason", value.reason());
                var refs = row.putArray("evidence"); value.evidence().forEach(ref -> refs.add(ref.toJson())); return row;
            }
            ActionState.Attempt attempt = ActionTransitions.attempt(state).orElseThrow();
            NativeActionPort.DispatchOutcome dispatch = ActionTransitions.dispatch(state).orElseThrow();
            row.put("kind", state instanceof ActionState.AckReceived ? "ACK_RECEIVED" : state instanceof ActionState.Settled ? "SETTLED" : "REJECTED_BEFORE_DISPATCH");
            row.set("attempt", attempt(attempt, archive)); row.set("dispatch_ref", archive.referenceOf(dispatch).toJson());
            if (state instanceof ActionState.Settled settled) row.set("settlement", settlement(settled.settlement(), archive, evolved, typed, family)); return row;
        }
        private static ActionState state(JsonNode node, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
            StrictJson.require(node instanceof ObjectNode, "action state object required"); ObjectNode row = (ObjectNode) node;
            String kind = text(row, "kind");
            return switch (kind) {
                case "PHYSICAL_ACTION" -> PhysicalActionCodec.decode(row, archive);
                case "INTENT_DURABLE" -> { StrictJson.object(row, Set.of("kind")); yield new ActionState.IntentDurable(); }
                case "INTENT_ABANDONED" -> {
                    StrictJson.object(row, Set.of("kind", "original_intent_record", "original_action_head"));
                    yield new ActionState.IntentAbandoned(ExactRef.fromJson(row.get("original_intent_record")), ExactRef.fromJson(row.get("original_action_head")));
                }
                case "SUBMITTING" -> { StrictJson.object(row, Set.of("kind", "attempt")); yield new ActionState.Submitting(attempt(row.get("attempt"), archive)); }
                case "ACK_RECEIVED" -> {
                    StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref")); var dispatch = archive.load(ExactRef.fromJson(row.get("dispatch_ref")));
                    StrictJson.require(dispatch instanceof NativeActionPort.AckReceived, "ACK branch requires original ACK"); yield new ActionState.AckReceived(attempt(row.get("attempt"), archive), (NativeActionPort.AckReceived) dispatch);
                }
                case "UNKNOWN" -> {
                    StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref", "reason", "evidence")); List<ExactRef> evidence = new ArrayList<>();
                    StrictJson.require(row.get("evidence").isArray(), "UNKNOWN evidence array required"); row.get("evidence").forEach(item -> evidence.add(ExactRef.fromJson(item)));
                    yield new ActionState.Unknown(row.get("attempt").isNull() ? Optional.empty() : Optional.of(attempt(row.get("attempt"), archive)),
                            row.get("dispatch_ref").isNull() ? Optional.empty() : Optional.of(archive.load(ExactRef.fromJson(row.get("dispatch_ref")))), text(row, "reason"), evidence);
                }
                case "SETTLED" -> {
                    StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref", "settlement"));
                    yield new ActionState.Settled(attempt(row.get("attempt"), archive), archive.load(ExactRef.fromJson(row.get("dispatch_ref"))), settlement(row.get("settlement"), archive, evolved, typed, family));
                }
                case "COMPOSITE_RUNNING" -> { StrictJson.object(row, Set.of("kind", "execution")); yield new ActionState.CompositeRunning(execution(row.get("execution"))); }
                case "COMPOSITE_UNKNOWN" -> {
                    StrictJson.object(row, Set.of("kind", "execution", "reason", "evidence")); List<ExactRef> evidence = new ArrayList<>();
                    StrictJson.require(row.get("evidence").isArray(), "composite evidence array required"); row.get("evidence").forEach(item -> evidence.add(ExactRef.fromJson(item)));
                    yield new ActionState.CompositeUnknown(execution(row.get("execution")), text(row, "reason"), evidence);
                }
                case "COMPOSITE_SETTLED" -> { StrictJson.object(row, Set.of("kind", "execution", "settlement")); yield new ActionState.CompositeSettled(execution(row.get("execution")), settlement(row.get("settlement"), archive, evolved, typed, family)); }
                case "REJECTED_BEFORE_DISPATCH" -> {
                    StrictJson.object(row, Set.of("kind", "attempt", "dispatch_ref")); var dispatch = archive.load(ExactRef.fromJson(row.get("dispatch_ref")));
                    StrictJson.require(dispatch instanceof NativeActionPort.RejectedBeforeDispatch, "zero dispatch branch requires original explicit proof");
                    yield new ActionState.RejectedBeforeDispatch(attempt(row.get("attempt"), archive), (NativeActionPort.RejectedBeforeDispatch) dispatch);
                }
                default -> throw new IllegalArgumentException("unsupported action state kind");
            };
        }
        private static ObjectNode lifePrefixFrame(org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord frame) {
            var row = StrictJson.object();
            row.set("identity", ProposalLifecycleCodec.observation(frame.identity()));
            row.set("observation_provenance", ObservationProvenanceCodec.encode(frame.provenance()));
            row.put("observed_at_utc", frame.observedAt().toString());
            row.set("native_frame", frame.nativeFrame().toJson());
            row.set("driver_facts", frame.driverFacts().toJson());
            row.set("semantic", frame.semantic().toJson());
            return row;
        }
        private static org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord lifePrefixFrame(JsonNode value) {
            var row = StrictJson.object(value, Set.of("identity", "observation_provenance", "observed_at_utc", "native_frame", "driver_facts", "semantic"));
            return new org.xar.ck3.control.application.advance.LifeAdvanceEvidence.FrameRecord(
                    ProposalLifecycleCodec.decodeObservation(row.get("identity")), ObservationProvenanceCodec.decode(row.get("observation_provenance")),
                    Instant.parse(StrictJson.utc(text(row,"observed_at_utc"))), ExactRef.fromJson(row.get("native_frame")),
                    ExactRef.fromJson(row.get("driver_facts")), ExactRef.fromJson(row.get("semantic")));
        }
        private static ObjectNode attempt(ActionState.Attempt attempt, ActionPorts.OutcomeArchive archive) {
            ObjectNode row = StrictJson.object(); row.put("request_id", attempt.requestId()); row.put("submitted_at", attempt.submittedAt().toString());
            row.set("guard", encodeGuard(attempt.guard())); row.set("prepared_request_ref", archive.requestReferenceOf(attempt.preparedRequest()).toJson()); return row;
        }
        private static ActionState.Attempt attempt(JsonNode node, ActionPorts.OutcomeArchive archive) {
            ObjectNode row = StrictJson.object(node, Set.of("request_id", "submitted_at", "guard", "prepared_request_ref"));
            return new ActionState.Attempt(text(row, "request_id"), Instant.parse(text(row, "submitted_at")), decodeGuard(row.get("guard")), archive.loadRequest(ExactRef.fromJson(row.get("prepared_request_ref"))));
        }
        public static ObjectNode encodeGuard(GuardEvidence guard) {
            return CommandOriginCodec.guard(guard);
        }
        public static GuardEvidence decodeGuard(JsonNode node) {
            return CommandOriginCodec.guard(node);
        }
        private static ObjectNode settlement(ActionState.Settlement settlement, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
            ObjectNode row = StrictJson.object();
            if (settlement instanceof ActionState.LifeControlPrefixInterrupted interrupted) {
                StrictJson.require(evolved, "Life control-prefix interruption requires receipt v13");
                row.put("kind", "LIFE_CONTROL_PREFIX_INTERRUPTED");
                row.put("action_id", interrupted.observation().actionId());
                row.put("body_sha256", interrupted.observation().bodySha256());
                row.set("execution", execution(interrupted.observation().execution()));
                row.set("ending", lifePrefixFrame(interrupted.observation().ending()));
                return row;
            }
            if(settlement instanceof ActionState.FixtureStarted started){
                StrictJson.require(evolved&&!typed&&!family,"fixture first-map proof requires exact receipt v11");
                row.put("kind","FIXTURE_STARTED");row.set("observation",FixtureProofCodec.start(started.observation(),archive));return row;
            }
            if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
                StrictJson.require(evolved&&!typed&&!family,"fixture business proof requires exact receipt v11");
                row.put("kind","FIXTURE_BUSINESS_COMPLETED");row.set("observation",FixtureProofCodec.business(completed.observation(),archive));return row;
            }
            if (settlement instanceof ActionState.DirectFixedWindowCompleted completed) {
                StrictJson.require(evolved && !typed && !family, "direct fixed-window completion requires exact receipt v9");
                row.put("kind", "DIRECT_FIXED_WINDOW_COMPLETED");
                row.set("completion", completed.completion().encode(archive)); return row;
            }
            if (settlement instanceof ActionState.PauseConfirmed pause) {
                boolean fresh = pause.observation().provenance() instanceof ObservationProvenance.FreshSnapshotQuery;
                StrictJson.require(evolved && (typed || fresh), "native pause confirmation requires receipt v8 or v15");
                row.put("kind", "PAUSE_CONFIRMED");
                row.set("semantic", settlement(new ActionState.Applied(pause.observation()), archive, true, typed || fresh, false)); return row;
            }
            if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
                StrictJson.require(evolved, "source-bound control sequence requires receipt v8");
                row.put("kind", "CONTROL_SEQUENCE_COMPLETED");
                row.set("observation", StrictJson.parse(sequence.observation().encode())); return row;
            }
            if (settlement instanceof ActionState.OperatorRebound rebound) {
                row.put("kind", "OPERATOR_REBOUND"); row.set("observation", StrictJson.parse(rebound.observation().encode())); return row;
            }
            if (settlement instanceof ActionState.NativeSourceCompleted source) {
                row.put("kind", "NATIVE_SOURCE_COMPLETED"); row.set("observation", StrictJson.parse(source.observation().encode())); return row;
            }
            if (settlement instanceof ActionState.NormalExitPhaseConfirmed phase) {
                row.put("kind", "NORMAL_EXIT_PHASE_CONFIRMED"); row.set("observation", phase.observation().encode(archive)); return row;
            }
            if (settlement instanceof ActionState.FamilySendConfirmed sent) {
                StrictJson.require(family && evolved && !typed, "typed outgoing family request requires exact receipt v4");
                row.put("kind", "FAMILY_SEND_CONFIRMED");
                row.set("observation", org.xar.ck3.control.application.effects.family.FamilySendObservationCodec.encode(sent.observation(), archive)); return row;
            }
            if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) {
                StrictJson.require(evolved, "canonical Sway scheduler completion requires receipt v2"); row.put("kind", "SWAY_SCHEDULER_COMPLETED");
                row.set("proof_ref", archive.materialReferenceOf(new RawJson(scheduler.proof().encode())).toJson()); return row;
            }
            if (settlement instanceof ActionState.LifecycleControlApplied control) {
                StrictJson.require(evolved, "terminal modal control requires receipt v2"); row.put("kind", "LIFECYCLE_CONTROL_APPLIED");
                row.set("observation", LifecycleControlCodec.encode(control.observation(), archive::readReferenceOf)); return row;
            }
            if (settlement instanceof ActionState.NonAppliedTerminal terminal) {
                StrictJson.require(evolved, "independent non-applied terminal requires receipt v2"); row.put("kind", "NON_APPLIED_TERMINAL");
                row.set("observation", ActionTerminalCodec.encode(terminal.observation(), archive::readReferenceOf)); return row;
            }
            if (settlement instanceof ActionState.CompositeRejected rejected) {
                StrictJson.require(evolved, "canonical composite rejection requires receipt v2"); row.put("kind", "COMPOSITE_REJECTED"); row.put("reason", rejected.reason());
                var children = row.putArray("children"); rejected.children().forEach(child -> { var item = children.addObject(); item.put("action_id", child.actionId()); item.put("body_sha256", child.bodySha256()); });
                if(!rejected.evidence().isEmpty()){var evidence=row.putArray("evidence");for(var ref:rejected.evidence()){requireCompositeFailureMaterial(ref,archive);evidence.add(ref.toJson());}}return row;
            }
            if (settlement instanceof ActionState.CompositeNoGameplayWrite write) {
                StrictJson.require(evolved, "composite no-gameplay write requires receipt v12");
                row.put("kind", "COMPOSITE_NO_GAMEPLAY_WRITE");
                row.put("action_id", write.observation().actionId());
                row.put("body_sha256", write.observation().bodySha256());
                row.set("execution", execution(write.observation().execution()));
                return row;
            }
            if (settlement instanceof ActionState.LifecycleApplied lifecycle) {
                StrictJson.require(evolved, "canonical lifecycle settlement requires receipt v2"); row.put("kind", "LIFECYCLE_APPLIED");
                row.set("proof_ref", archive.materialReferenceOf(new RawJson(lifecycle.proof().encode())).toJson()); return row;
            }
            if (settlement instanceof ActionState.CompositeControlApplied control) {
                StrictJson.require(evolved, "composite control requires receipt v2"); row.put("kind", "COMPOSITE_CONTROL_APPLIED");
                row.set("terminal_status_ref", archive.readReferenceOf(control.observation().terminalStatus()).toJson());
                var reads = row.putArray("supporting_reads"); control.observation().supportingReads().forEach(read -> reads.add(archive.readReferenceOf(read).toJson()));
                row.set("semantic", settlement(new ActionState.Applied(control.observation().semantic()), archive, true, typed, family)); return row;
            }
            if (settlement instanceof ActionState.FrontendApplied frontend) {
                StrictJson.require(evolved, "frontend settlement requires receipt v2"); row.put("kind", "FRONTEND_APPLIED"); row.set("observation", CommandOriginCodec.frontendEffect(frontend.observation())); return row;
            }
            if (settlement instanceof ActionState.GameplayEntered entered) {
                StrictJson.require(evolved, "gameplay entry requires receipt v2"); row.put("kind", "GAMEPLAY_ENTERED"); row.set("observation", CommandOriginCodec.gameplayEntry(entered.observation(), archive::readReferenceOf)); return row;
            }
            if (settlement instanceof ActionState.ControlApplied control) {
                row.put("kind", control.reconciledAck().isPresent() ? "CONTROL_APPLIED_RECONCILED" : "CONTROL_APPLIED");
                control.reconciledAck().ifPresent(value -> row.set("reconciled_ack_ref", value.reference(archive).toJson()));
                row.set("read_ref", archive.readReferenceOf(control.read()).toJson());
                var supporting = row.putArray("supporting_reads"); control.supportingReads().forEach(read -> supporting.add(archive.readReferenceOf(read).toJson()));
                row.set("observation", ProposalLifecycleCodec.expected(new ExpectedPostcondition(1, controlIdentity(control.read()), control.read().request().source(), control.observerSchema(), control.actual()))); return row;
            }
            if (settlement instanceof ActionState.Rejected rejected) {
                row.put("kind", "REJECTED"); row.put("request_id", rejected.requestId()); row.put("reason", rejected.reason()); row.set("original_evidence", rejected.originalEvidence().toJson()); return row;
            }
            ActionState.EffectObservation effect = ((ActionState.Applied) settlement).observation(); row.put("kind", "APPLIED");
            row.set("observation", ProposalLifecycleCodec.expected(new ExpectedPostcondition(1, effect.after(), effect.source(), effect.observerSchema(), effect.actual())));
            row.put("session_id", effect.sessionId());
            if (typed) row.set("observation_provenance", ObservationProvenanceCodec.encode(effect.provenance()));
            else { StrictJson.require(effect.provenance() instanceof ObservationProvenance.Query, "historical effect requires its actual query request ID"); row.put("read_request_id", ((ObservationProvenance.Query) effect.provenance()).requestId()); }
            row.put("observed_at", effect.observedAt().toString()); row.set("original_evidence", effect.originalEvidence().toJson());
            if (evolved) { var supporting = row.putArray("supporting_evidence"); effect.supportingEvidence().forEach(ref -> supporting.add(ref.toJson())); }
            return row;
        }
        private static ActionState.Settlement settlement(JsonNode node, ActionPorts.OutcomeArchive archive, boolean evolved, boolean typed, boolean family) {
            StrictJson.require(node instanceof ObjectNode, "settlement object required"); ObjectNode row = (ObjectNode) node;
            if (text(row,"kind").equals("LIFE_CONTROL_PREFIX_INTERRUPTED")) {
                StrictJson.require(evolved, "Life control-prefix interruption requires receipt v13");
                StrictJson.object(row, Set.of("kind", "action_id", "body_sha256", "execution", "ending"));
                return new ActionState.LifeControlPrefixInterrupted(new org.xar.ck3.control.application.advance.LifeControlPrefixInterruption(
                        text(row,"action_id"), text(row,"body_sha256"), execution(row.get("execution")), lifePrefixFrame(row.get("ending"))));
            }
            if(text(row,"kind").equals("FIXTURE_STARTED")){
                StrictJson.require(evolved&&!typed&&!family,"fixture first-map proof requires exact receipt v11");StrictJson.object(row,Set.of("kind","observation"));
                return new ActionState.FixtureStarted(FixtureProofCodec.start(row.get("observation"),archive));
            }
            if(text(row,"kind").equals("FIXTURE_BUSINESS_COMPLETED")){
                StrictJson.require(evolved&&!typed&&!family,"fixture business proof requires exact receipt v11");StrictJson.object(row,Set.of("kind","observation"));
                return new ActionState.FixtureBusinessCompleted(FixtureProofCodec.business(row.get("observation"),archive));
            }
            if (text(row, "kind").equals("DIRECT_FIXED_WINDOW_COMPLETED")) {
                StrictJson.require(evolved && !typed && !family, "direct fixed-window completion requires exact receipt v9");
                StrictJson.object(row, Set.of("kind", "completion"));
                return new ActionState.DirectFixedWindowCompleted(
                        org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.Completion.decode(row.get("completion"), archive));
            }
            if (text(row, "kind").equals("PAUSE_CONFIRMED")) {
                StrictJson.require(evolved && typed, "native pause requires exact typed receipt v8 or v15");
                StrictJson.object(row, Set.of("kind", "semantic"));
                var semantic = settlement(row.get("semantic"), archive, true, true, false);
                StrictJson.require(semantic instanceof ActionState.Applied applied && (applied.observation().provenance() instanceof ObservationProvenance.Push || applied.observation().provenance() instanceof ObservationProvenance.FreshSnapshotQuery || applied.observation().provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement),
                        "pause requires the exact original native Push or FreshSnapshotQuery semantic DATA");
                return new ActionState.PauseConfirmed(((ActionState.Applied) semantic).observation());
            }
            if (text(row, "kind").equals("CONTROL_SEQUENCE_COMPLETED")) {
                StrictJson.require(evolved, "source-bound control requires receipt v8");
                StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.ControlSequenceCompleted(org.xar.ck3.control.application.effects.control.ControlSequenceObservation.decode(StrictJson.canonical(row.get("observation"))));
            }
            if (text(row, "kind").equals("OPERATOR_REBOUND")) {
                StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.OperatorRebound(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(row.get("observation"))));
            }
            if (text(row, "kind").equals("NATIVE_SOURCE_COMPLETED")) {
                StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.NativeSourceCompleted(org.xar.ck3.control.application.effects.coa.NativeSourceObservation.decode(StrictJson.canonical(row.get("observation"))));
            }
            if (text(row, "kind").equals("NORMAL_EXIT_PHASE_CONFIRMED")) {
                StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.NormalExitPhaseConfirmed(org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation.decode(row.get("observation"), archive));
            }
            if (text(row, "kind").equals("FAMILY_SEND_CONFIRMED")) {
                StrictJson.require(family && evolved && !typed, "typed outgoing family request requires exact receipt v4");
                StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.FamilySendConfirmed(org.xar.ck3.control.application.effects.family.FamilySendObservationCodec.decode(row.get("observation"), archive));
            }
            if (text(row, "kind").equals("SWAY_SCHEDULER_COMPLETED")) {
                StrictJson.require(evolved, "canonical Sway scheduler completion requires receipt v2"); StrictJson.object(row, Set.of("kind", "proof_ref"));
                return new ActionState.SwaySchedulerCompleted(org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletionCodec.decodeRecorded(archive.loadMaterial(ExactRef.fromJson(row.get("proof_ref"))).bytes()));
            }
            if (text(row, "kind").equals("LIFECYCLE_CONTROL_APPLIED")) {
                StrictJson.require(evolved, "terminal modal control requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.LifecycleControlApplied(LifecycleControlCodec.decode(row.get("observation"), archive::loadRead));
            }
            if (text(row, "kind").equals("NON_APPLIED_TERMINAL")) {
                StrictJson.require(evolved, "independent non-applied terminal requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation"));
                return new ActionState.NonAppliedTerminal(ActionTerminalCodec.decode(row.get("observation"), archive::loadRead));
            }
            if (text(row, "kind").equals("COMPOSITE_REJECTED")) {
                StrictJson.require(evolved, "canonical composite rejection requires receipt v2"); StrictJson.object(row, row.has("evidence") ? Set.of("kind", "reason", "children", "evidence") : Set.of("kind", "reason", "children"));
                StrictJson.require(row.get("children").isArray(), "exact rejected child array required"); List<CompositeExecution.Child> children = new ArrayList<>();
                row.get("children").forEach(raw -> { var child = StrictJson.object(raw, Set.of("action_id", "body_sha256")); children.add(new CompositeExecution.Child(text(child, "action_id"), text(child, "body_sha256"))); });
                var evidence=new ArrayList<ExactRef>();if(row.has("evidence")){StrictJson.require(row.get("evidence").isArray()&&row.get("evidence").size()>0&&row.get("evidence").size()<=64,"nonempty bounded composite failure evidence required");for(var item:row.get("evidence")){var ref=ExactRef.fromJson(item);requireCompositeFailureMaterial(ref,archive);evidence.add(ref);}}
                return new ActionState.CompositeRejected(text(row, "reason"), children,evidence);
            }
            if (text(row, "kind").equals("COMPOSITE_NO_GAMEPLAY_WRITE")) {
                StrictJson.require(evolved, "composite no-gameplay write requires receipt v12");
                StrictJson.object(row, Set.of("kind", "action_id", "body_sha256", "execution"));
                var exec = execution(row.get("execution"));
                var obs = new CompositeNoGameplayWriteObservation(text(row, "action_id"), text(row, "body_sha256"), exec);
                return new ActionState.CompositeNoGameplayWrite(obs);
            }
            if (text(row, "kind").equals("LIFECYCLE_APPLIED")) {
                StrictJson.require(evolved, "canonical lifecycle settlement requires receipt v2"); StrictJson.object(row, Set.of("kind", "proof_ref"));
                RawJson original = archive.loadMaterial(ExactRef.fromJson(row.get("proof_ref")));
                return new ActionState.LifecycleApplied(org.xar.ck3.control.application.lifecycle.LifecycleProofCodec.decodeRecorded(original.bytes()));
            }
            if (text(row, "kind").equals("FRONTEND_APPLIED")) {
                StrictJson.require(evolved, "frontend settlement requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation")); return new ActionState.FrontendApplied(CommandOriginCodec.frontendEffect(row.get("observation")));
            }
            if (text(row, "kind").equals("GAMEPLAY_ENTERED")) {
                StrictJson.require(evolved, "gameplay entry requires receipt v2"); StrictJson.object(row, Set.of("kind", "observation")); return new ActionState.GameplayEntered(CommandOriginCodec.gameplayEntry(row.get("observation"), archive::loadRead));
            }
            if (text(row, "kind").equals("COMPOSITE_CONTROL_APPLIED")) {
                StrictJson.require(evolved, "composite control requires receipt v2"); StrictJson.object(row, Set.of("kind", "terminal_status_ref", "supporting_reads", "semantic"));
                StrictJson.require(row.get("supporting_reads").isArray(), "supporting control reads array required"); List<PlanningReadReceipt> supporting = new ArrayList<>();
                row.get("supporting_reads").forEach(ref -> supporting.add(archive.loadRead(ExactRef.fromJson(ref))));
                ActionState.Settlement semantic = settlement(row.get("semantic"), archive, true, typed, family); StrictJson.require(semantic instanceof ActionState.Applied, "composite control semantic branch must be an actual original semantic observation");
                return new ActionState.CompositeControlApplied(new CompositeControlObservation(archive.loadRead(ExactRef.fromJson(row.get("terminal_status_ref"))), supporting, ((ActionState.Applied) semantic).observation()));
            }
            if (text(row, "kind").equals("CONTROL_APPLIED") || text(row, "kind").equals("CONTROL_APPLIED_RECONCILED")) {
                boolean reconciled = text(row, "kind").equals("CONTROL_APPLIED_RECONCILED");
                StrictJson.object(row, reconciled ? Set.of("kind", "read_ref", "supporting_reads", "observation", "reconciled_ack_ref") : Set.of("kind", "read_ref", "supporting_reads", "observation"));
                ObjectNode observation = StrictJson.object(row.get("observation"), Set.of("version", "before", "source", "observer_schema", "values")); StrictJson.integer(observation.get("version"), 1, 1);
                PlanningReadReceipt read = archive.loadRead(ExactRef.fromJson(row.get("read_ref")));
                StrictJson.require(ProposalLifecycleCodec.decodeObservation(observation.get("before")).equals(controlIdentity(read)) && G2Wire.source(observation.get("source")).equals(read.request().source()), "control read original observation/source drift");
                StrictJson.require(row.get("supporting_reads").isArray(), "supporting reads array required"); List<PlanningReadReceipt> supporting = new ArrayList<>();
                row.get("supporting_reads").forEach(item -> supporting.add(archive.loadRead(ExactRef.fromJson(item))));
                Optional<ReconciledControlAck> late = Optional.empty();
                if (reconciled) {
                    var received = archive.load(ExactRef.fromJson(row.get("reconciled_ack_ref")));
                    StrictJson.require(received instanceof NativeActionPort.AckReceived, "reconciled control sidecar must be the actual received original ACK");
                    late = Optional.of(new ReconciledControlAck((NativeActionPort.AckReceived) received));
                }
                return new ActionState.ControlApplied(read, supporting, text(observation, "observer_schema"), ProposalLifecycleCodec.values(observation.get("values")), late);
            }
            if (text(row, "kind").equals("REJECTED")) {
                StrictJson.object(row, Set.of("kind", "request_id", "reason", "original_evidence"));
                return new ActionState.Rejected(text(row, "request_id"), text(row, "reason"), ExactRef.fromJson(row.get("original_evidence")));
            }
            StrictJson.object(row, typed ? Set.of("kind", "observation", "session_id", "observation_provenance", "observed_at", "original_evidence", "supporting_evidence")
                    : evolved ? Set.of("kind", "observation", "session_id", "read_request_id", "observed_at", "original_evidence", "supporting_evidence") : Set.of("kind", "observation", "session_id", "read_request_id", "observed_at", "original_evidence")); StrictJson.require(text(row, "kind").equals("APPLIED"), "known settlement kind required");
            ObjectNode observation = StrictJson.object(row.get("observation"), Set.of("version", "before", "source", "observer_schema", "values"));
            StrictJson.integer(observation.get("version"), 1, 1);
            List<ExactRef> supporting = new ArrayList<>();
            if (evolved) { StrictJson.require(row.get("supporting_evidence").isArray(), "supporting effect evidence array required"); row.get("supporting_evidence").forEach(ref -> supporting.add(ExactRef.fromJson(ref))); }
            return new ActionState.Applied(new ActionState.EffectObservation(ProposalLifecycleCodec.decodeObservation(observation.get("before")), G2Wire.source(observation.get("source")),
                    text(row, "session_id"), text(observation, "observer_schema"), ProposalLifecycleCodec.values(observation.get("values")), typed ? ObservationProvenanceCodec.decode(row.get("observation_provenance")) : new ObservationProvenance.Query(text(row, "read_request_id")),
                    Instant.parse(text(row, "observed_at")), ExactRef.fromJson(row.get("original_evidence")), supporting));
        }
        private static ObjectNode execution(CompositeExecution execution) {
            ObjectNode row = StrictJson.object(); row.put("handler_id", execution.handlerId()); row.put("started_at", execution.startedAt().toString()); row.set("guard", encodeGuard(execution.guard()));
            var children = row.putArray("children"); for (CompositeExecution.Child child : execution.children()) { var item = children.addObject(); item.put("action_id", child.actionId()); item.put("body_sha256", child.bodySha256()); } return row;
        }
        private static CompositeExecution execution(JsonNode node) {
            ObjectNode row = StrictJson.object(node, Set.of("handler_id", "started_at", "guard", "children")); StrictJson.require(row.get("children").isArray(), "composite child array required");
            List<CompositeExecution.Child> children = new ArrayList<>(); row.get("children").forEach(item -> { ObjectNode child = StrictJson.object(item, Set.of("action_id", "body_sha256")); children.add(new CompositeExecution.Child(text(child, "action_id"), text(child, "body_sha256"))); });
            return new CompositeExecution(text(row, "handler_id"), Instant.parse(text(row, "started_at")), decodeGuard(row.get("guard")), children);
        }
        private static ObservationIdentity controlIdentity(PlanningReadReceipt read) {
            var origin = read.after().binding().origin();
            if (origin instanceof CommandOrigin.Gameplay gameplay) return gameplay.before();
            if (origin instanceof CommandOrigin.Reconciliation reconciliation) return reconciliation.identity().factual();
            throw new IllegalStateException("unsupported control read origin");
        }
        private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    }
    // LEGACY_WHOLE_BASE_END
}
