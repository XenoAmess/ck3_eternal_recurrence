package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.HistoryEntry;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Missing;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Session;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Slot;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure public DATA. Frozen old encoder is an independent byte/error oracle.
 * No archive, machine-original dependency, reflection, Root issuer or benchmark.
 */
final class DriverCompleteOwnedEncodeTest {
    private static final Session SESSION = new Session("owner50-pipe", 123, BigInteger.valueOf(31254), "owner50-episode");
    private static final List<String> ALL_FIELDS = List.of("format_version", "pipe_name", "bridge_pid",
            "episode_character_id", "episode_run_id", "command_history", "last_checkpoint", "rollback_war_failure",
            "managed_restore_transaction", "succession_expectation", "succession_lifecycle", "campaign_goal", "rollback_war_failures");
    private static final String NUMBERS = """
            {"integer_zero":-0,"decimal_zero":-0.0,"spelling":-0.000e+0,"plus_exp":1.2300e+12,"wide":18446744073709551616,"huge":1e2147483648,"tiny":-1e-2147483648,"unknown":{"中文":"雪é","array":[true,false,null,{},[]]}}
            """.strip();

    @Test void allThirteenFieldsUnknownMaterialAndNumericTokensMatchTheFrozenEncoder() {
        var history = List.of(new HistoryEntry(1, value(row(1, NUMBERS))), new HistoryEntry(2, value(row(2, "[]"))));
        var snapshot = new Complete(SESSION, history, value(NUMBERS), new NullValue(), value("[]"), value("false"),
                value("{}"), value(NUMBERS), value("[null,true,false]"));
        byte[] expected = oldEncode(snapshot); byte[] actual = snapshot.encode();
        assertArrayEquals(expected, actual);
        ObjectNode parsed = object(parse(actual)); var fields = new ArrayList<String>(); parsed.fieldNames().forEachRemaining(fields::add);
        assertEquals(ALL_FIELDS, fields);
        String wire = new String(actual, StandardCharsets.UTF_8);
        assertTrue(wire.contains(quote("integer_zero") + ":0"));
        for (String token : List.of("-0.0", "-0.000e+0", "1.2300e+12", "18446744073709551616", "1e2147483648", "-1e-2147483648", "中文", "雪é"))
            assertTrue(wire.contains(token), token);
        assertEquals(2, parsed.path("command_history").size());
        assertTrue(parsed.path("campaign_goal").path("unknown").path("array").isArray());
        assertArrayEquals(expected, DriverStateSnapshot.decodeComplete(actual).encode());
        assertArrayEquals(expected, oldEncode(DriverStateSnapshot.decodeComplete(actual)));
    }

    @Test void embeddedHistoryAndSlotDepth63_64_65KeepScalarAndEmptyContainerBoundaries() {
        for (int depth : List.of(63, 64, 65)) {
            int historyArrays = depth - 3;
            for (String leaf : List.of("0", "[]")) {
                Value historyValue = value(row(1, nested(historyArrays, leaf)));
                var snapshot = snapshot(SESSION, List.of(new HistoryEntry(1, historyValue)), new NullValue(), new Missing());
                if (depth <= 64) assertArrayEquals(oldEncode(snapshot), snapshot.encode(), "history depth=" + depth + " leaf=" + leaf);
                else sameFailure(() -> oldEncode(snapshot), snapshot::encode, "history depth65 " + leaf);
            }
            // Slot prefix contributes exactly one level; the scalar itself is at the requested global depth.
            var scalar = snapshot(SESSION, List.of(), value(nested(depth - 1, "0")), new Missing());
            if (depth <= 64) assertArrayEquals(oldEncode(scalar), scalar.encode(), "slot scalar depth=" + depth);
            else sameFailure(() -> oldEncode(scalar), scalar::encode, "slot scalar depth65");
        }
        for (int containers : List.of(63, 64)) {
            Value empty = value("[".repeat(containers) + "]".repeat(containers));
            var snapshot = snapshot(SESSION, List.of(), empty, new Missing());
            assertArrayEquals(oldEncode(snapshot), snapshot.encode(), "empty slot containers=" + containers);
        }
        // An empty 65-container value cannot enter either encoder through the unchanged public constructor.
        sameOutcome(() -> oldValue(utf8("[".repeat(65) + "]".repeat(65))),
                () -> value("[".repeat(65) + "]".repeat(65)).json(), "empty constructor depth65");
        String quotedBraces = quote("brackets [ ] { } quote " + (char)34 + " escape " + (char)92 + " slash");
        var string = snapshot(SESSION, List.of(new HistoryEntry(1, value(row(1, quotedBraces)))), value(quotedBraces), new Missing());
        assertArrayEquals(oldEncode(string), string.encode());
    }

    @Test void unicodeBomAndMalformedUtf8KeepTheOriginalConstructorAndEncoderPipeline() {
        String slashU = Character.toString(0x5c) + "u";
        String high = slashU + "D800", low = slashU + "DC00";
        var raws = List.of(quote("雪é"), quote(new String(Character.toChars(0x1f600))),
                rawQuote(slashU + "0061"), quote("literal " + slashU + "0061"),
                rawQuote(high + low), rawQuote(high), rawQuote(low),
                "{" + rawQuote(high) + ":1}", "{" + rawQuote(low) + ":1}",
                rawQuote(slashU + "0000"), quote("line" + (char)10 + "tab" + (char)9));
        for (int index = 0; index < raws.size(); index++) {
            String raw = raws.get(index); String label = "unicode-" + index;
            sameOutcome(() -> oldValue(utf8(raw)), () -> value(raw).json(), label + " public Value");
            try { oldValue(utf8(raw)); }
            catch (RuntimeException originalConstructorRejection) { continue; }
            sameOutcome(() -> oldEncode(snapshot(SESSION, List.of(new HistoryEntry(1, value(row(1, raw)))), value(raw), new Missing())),
                    () -> snapshot(SESSION, List.of(new HistoryEntry(1, value(row(1, raw)))), value(raw), new Missing()).encode(), label + " public Complete");
            sameOutcome(() -> oldEncode(DriverStateSnapshot.decodeComplete(utf8(envelope(raw)))),
                    () -> DriverStateSnapshot.decodeComplete(utf8(envelope(raw))).encode(), label + " strict decoder producer");
        }
        for (String header : List.of("雪é", new String(Character.toChars(0x1f600)),
                "header-" + (char)0xd800, "header-" + (char)0xdc00)) {
            sameOutcome(() -> {
                var session = new Session("pipe-" + header, 123, BigInteger.valueOf(31254), "episode-" + header);
                var snapshot = snapshot(session, List.of(new HistoryEntry(1, value(row(1, "[]")))), value("{}"), new Missing());
                return oldEncode(snapshot);
            }, () -> {
                var session = new Session("pipe-" + header, 123, BigInteger.valueOf(31254), "episode-" + header);
                var snapshot = snapshot(session, List.of(new HistoryEntry(1, value(row(1, "[]")))), value("{}"), new Missing());
                return snapshot.encode();
            }, "header unicode");
        }
        byte[] text = utf8("{ " + quote("value") + ": -0.00e+2 }");
        byte[] bom = new byte[text.length + 3]; bom[0]=(byte)0xef; bom[1]=(byte)0xbb; bom[2]=(byte)0xbf;
        System.arraycopy(text,0,bom,3,text.length);
        sameOutcome(() -> oldValue(bom), () -> new Value(bom).json(), "BOM public ingress");
        for (byte[] invalid : List.of(new byte[]{(byte)0xc3,0x28}, new byte[]{(byte)0xf0,(byte)0x80,(byte)0x80,(byte)0x80},
                new byte[]{(byte)0xe9,(byte)0x9b}, utf8("{} {}"), utf8("{" + quote("duplicate") + ":1," + quote("duplicate") + ":2}"), utf8("null")))
            sameOutcome(() -> oldValue(invalid), () -> new Value(invalid).json(), "invalid public Value ingress");
    }

    @Test void missingNullAndAllConstructorGetterOutputAliasesStayDetached() {
        byte[] input = utf8(row(1, NUMBERS)); Value shared = new Value(input); byte[] privateExpected = shared.json();
        var callerHistory = new ArrayList<HistoryEntry>(); callerHistory.add(new HistoryEntry(1, shared));
        var snapshot = new Complete(SESSION, callerHistory, shared, new NullValue(), shared, value(rawQuote("")),
                new Missing(), shared, new Missing());
        byte[] expected = oldEncode(snapshot); callerHistory.clear(); Arrays.fill(input,(byte)'!');
        byte[] getter1=shared.json(),getter2=shared.json();assertNotSame(getter1,getter2);Arrays.fill(getter1,(byte)'!');
        assertArrayEquals(privateExpected,getter2);assertArrayEquals(privateExpected,shared.json());
        assertEquals(1,snapshot.commandHistory().size());assertThrows(UnsupportedOperationException.class,()->snapshot.commandHistory().clear());
        byte[] output1=snapshot.encode(),output2=snapshot.encode();assertNotSame(output1,output2);assertArrayEquals(expected,output1);
        Arrays.fill(output1,(byte)'!');Arrays.fill(snapshot.commandHistory().getFirst().originalRow().json(),(byte)'!');
        Arrays.fill(((Value)snapshot.lastCheckpoint()).json(),(byte)'!');assertArrayEquals(expected,snapshot.encode());
        ObjectNode row=object(parse(output2));assertFalse(row.has("succession_lifecycle"));assertFalse(row.has("rollback_war_failures"));
        assertTrue(row.get("rollback_war_failure").isNull());
        var explicitNull=snapshot(SESSION,List.of(new HistoryEntry(1,shared)),shared,new NullValue());
        ObjectNode nullRow=object(parse(explicitNull.encode()));assertTrue(nullRow.has("succession_lifecycle"));assertTrue(nullRow.get("succession_lifecycle").isNull());
        assertArrayEquals(oldEncode(explicitNull),explicitNull.encode());
        byte[] source=expected.clone();Complete decoded=DriverStateSnapshot.decodeComplete(source);Arrays.fill(source,(byte)'!');
        assertArrayEquals(expected,decoded.encode());assertArrayEquals(expected,oldEncode(decoded));
    }

    @Test void bigIntegerSubclassKeepsItsOriginalCallbackAndFirstFailureBehavior() {
        var oldNumber=new ObservedInteger(false);var newNumber=new ObservedInteger(false);
        var oldSnapshot=snapshot(new Session("subclass-pipe",123,oldNumber,"subclass-episode"),List.of(),value("{}"),new Missing());
        var newSnapshot=snapshot(new Session("subclass-pipe",123,newNumber,"subclass-episode"),List.of(),value("{}"),new Missing());
        assertSame(newNumber,newSnapshot.session().actorId());oldNumber.calls=0;newNumber.calls=0;
        assertArrayEquals(oldEncode(oldSnapshot),newSnapshot.encode());assertTrue(oldNumber.calls>0);assertEquals(oldNumber.calls,newNumber.calls);
        var oldThrowing=new ObservedInteger(true);var newThrowing=new ObservedInteger(true);
        var oldFailure=snapshot(new Session("throwing-pipe",123,oldThrowing,"throwing-episode"),List.of(),value("{}"),new Missing());
        var newFailure=snapshot(new Session("throwing-pipe",123,newThrowing,"throwing-episode"),List.of(),value("{}"),new Missing());
        oldThrowing.calls=0;newThrowing.calls=0;
        sameFailure(()->oldEncode(oldFailure),newFailure::encode,"BigInteger callback failure");assertEquals(oldThrowing.calls,newThrowing.calls);
        // Full-tree depth validation precedes numeric serialization in the original route.
        var tooDeep=value(nested(64,"0"));oldThrowing.calls=0;newThrowing.calls=0;
        var oldDepth=snapshot(oldFailure.session(),List.of(),tooDeep,new Missing());var newDepth=snapshot(newFailure.session(),List.of(),tooDeep,new Missing());
        sameFailure(()->oldEncode(oldDepth),newDepth::encode,"depth before actor callback");
        assertEquals(0,oldThrowing.calls);assertEquals(0,newThrowing.calls);
    }

    @Test void publicIngressStillRejectsIndicesAndRequiredMissingSlotsAfterSuccessfulEncoding() {
        Value row=value(row(1,"[]"));var complete=snapshot(SESSION,List.of(new HistoryEntry(1,row)),value("{}"),new Missing());
        assertArrayEquals(oldEncode(complete),complete.encode());
        assertThrows(IllegalArgumentException.class,()->new HistoryEntry(2,row));
        assertThrows(IllegalArgumentException.class,()->new HistoryEntry(1,value("{"+quote("index")+":1.0}")));
        assertThrows(IllegalArgumentException.class,()->new HistoryEntry(1,value("[]")));
        assertThrows(IllegalArgumentException.class,()->new Complete(SESSION,List.of(),new Missing(),new NullValue(),new NullValue(),new NullValue(),new Missing(),new NullValue(),new Missing()));
        assertArrayEquals(oldEncode(complete),complete.encode());
    }

    /* Exact NEW-reference encode statements, mechanically exposed through public record
     * accessors. Value.json() adds a defensive clone here; this oracle is not a perf baseline.
     * No candidate encode or private helper/reflection is used to compute expected bytes. */
    private static byte[] oldEncode(Complete complete) {
        Session session=complete.session(); List<HistoryEntry> commandHistory=complete.commandHistory();
        Slot lastCheckpoint=complete.lastCheckpoint(),rollbackWarFailure=complete.rollbackWarFailure();
        Slot managedRestoreTransaction=complete.managedRestoreTransaction(),successionExpectation=complete.successionExpectation();
        Slot successionLifecycle=complete.successionLifecycle(),campaignGoal=complete.campaignGoal(),rollbackWarFailures=complete.rollbackWarFailures();
            ObjectNode row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); row.put("format_version", 2); row.put("pipe_name", session.pipeName()); row.put("bridge_pid", session.bridgePid());
            row.put("episode_character_id", session.actorId()); row.put("episode_run_id", session.episodeRunId());
            var history = row.putArray("command_history"); commandHistory.forEach(entry -> history.add(parse(entry.originalRow().json())));
            oldPut(row,"last_checkpoint",lastCheckpoint); oldPut(row,"rollback_war_failure",rollbackWarFailure); oldPut(row,"managed_restore_transaction",managedRestoreTransaction);
            oldPut(row,"succession_expectation",successionExpectation); oldPut(row,"succession_lifecycle",successionLifecycle); oldPut(row,"campaign_goal",campaignGoal); oldPut(row,"rollback_war_failures",rollbackWarFailures);
            return bytes(row);
    }
    private static void oldPut(ObjectNode row,String key,Slot slot) {
        switch(slot) {
            case Missing ignored -> { }
            case NullValue ignored -> row.putNull(key);
            case Value value -> row.set(key,parse(value.json()));
        }
    }
    private static byte[] oldValue(byte[] raw) {
        JsonNode value=parse(raw);StrictJson.require(!value.isNull(),"null has its own explicit Driver slot");return bytes(value);
    }
    private static void sameOutcome(Supplier<byte[]> expected,Supplier<byte[]> actual,String label) {
        final byte[] original;
        try {original=expected.get();}
        catch(RuntimeException rejected) {compareFailure(rejected,assertThrows(RuntimeException.class,actual::get,label),label);return;}
        assertArrayEquals(original,actual.get(),label);
    }
    private static void sameFailure(Supplier<byte[]> expected,Supplier<byte[]> actual,String label) {
        compareFailure(assertThrows(RuntimeException.class,expected::get,label),assertThrows(RuntimeException.class,actual::get,label),label);
    }
    private static void compareFailure(RuntimeException expected,RuntimeException actual,String label) {
        assertEquals(expected.getClass(),actual.getClass(),label+" first class");assertEquals(expected.getMessage(),actual.getMessage(),label+" first message");
        Throwable oldCause=expected.getCause(),newCause=actual.getCause();int depth=0;
        while(oldCause!=null||newCause!=null) {
            assertTrue(++depth<20,label+" finite cause chain");
            assertEquals(oldCause==null?null:oldCause.getClass(),newCause==null?null:newCause.getClass(),label+" cause class");
            assertEquals(oldCause==null?null:oldCause.getMessage(),newCause==null?null:newCause.getMessage(),label+" cause message");
            oldCause=oldCause==null?null:oldCause.getCause();newCause=newCause==null?null:newCause.getCause();
        }
    }
    private static Complete snapshot(Session session,List<HistoryEntry> history,Slot goal,Slot optional) {
        return new Complete(session,history,new NullValue(),new NullValue(),new NullValue(),new NullValue(),optional,goal,new Missing());
    }
    private static String nested(int arrays,String leaf) {return "[".repeat(arrays)+leaf+"]".repeat(arrays);}
    private static Value value(String raw) {return new Value(utf8(raw));}
    private static String row(long index,String payload) {return "{"+quote("index")+":"+index+","+quote("payload")+":"+payload+"}";}
    private static String quote(String text) {return new String(bytes(JsonNodeFactory.instance.textNode(text)),StandardCharsets.UTF_8);}
    private static String rawQuote(String rawContent) {return Character.toString(34)+rawContent+Character.toString(34);}
    private static byte[] utf8(String text) {return text.getBytes(StandardCharsets.UTF_8);}
    private static JsonNode parse(byte[] raw) {return FullJsonTree.parse(raw,DriverCheckpointStore.MAX_DRIVER_BYTES);}
    private static byte[] bytes(JsonNode node) {return FullJsonTree.encode(node,DriverCheckpointStore.MAX_DRIVER_BYTES);}
    private static ObjectNode object(JsonNode node) {StrictJson.require(node instanceof ObjectNode,"Driver object required");return (ObjectNode)node;}
    private static String envelope(String payload) {
        return """
                {"format_version":2,"pipe_name":"owner50-decoded-pipe","bridge_pid":123,"episode_character_id":31254,"episode_run_id":"owner50-decoded-episode","command_history":[{"index":1,"payload":%s}],"last_checkpoint":{},"rollback_war_failure":null,"managed_restore_transaction":[],"succession_expectation":"","campaign_goal":%s}
                """.formatted(payload,payload).strip();
    }
    private static final class ObservedInteger extends BigInteger {
        private static final long serialVersionUID=1L;
        private final boolean fail;private int calls;
        private ObservedInteger(boolean fail) {super("31254");this.fail=fail;}
        @Override public String toString() {calls++;if(fail)throw new IllegalStateException("owner50 original numeric callback");return super.toString();}
    }
}
