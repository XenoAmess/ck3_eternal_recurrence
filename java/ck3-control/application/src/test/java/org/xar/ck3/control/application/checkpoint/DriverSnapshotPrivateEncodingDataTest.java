package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonLocation;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Whole frozen legacy oracle and original public DATA boundaries; no candidate writer implementation is copied. */
final class DriverSnapshotPrivateEncodingDataTest {
    private static final int MAX=DriverCheckpointStore.MAX_DRIVER_BYTES;

    @Test void completeHistoryAndAllSlotsKeepEveryTokenAndCanonicalWireFromTheWholeLegacyImplementation() {
        String huge="9".repeat(4301);
        String payload="{\"ascii\":\"original\",\"bmp\":\"??\",\"fraction\":1.2300e+004,\"negativeZero\":-0.000e-02,\"huge\":"+huge+",\"array\":[true,null,{},[]]}";
        byte[] raw=document(payload);
        byte[] backup=raw.clone();
        var actual=assertEquivalent(raw);
        assertNotNull(actual);
        String encoded=text(actual.encode());
        assertTrue(encoded.contains("1.2300e+004"));assertTrue(encoded.contains("-0.000e-02"));assertTrue(encoded.contains(huge));
        assertArrayEquals(backup,raw);
        var old=LegacyDriverStateSnapshot.decodeComplete(backup);
        assertComplete(old,actual);
        byte[] row=actual.commandHistory().getFirst().originalRow().json();Arrays.fill(row,(byte)0);
        byte[] slot=((DriverStateSnapshot.Value)actual.lastCheckpoint()).json();Arrays.fill(slot,(byte)0);
        byte[] output=actual.encode();Arrays.fill(output,(byte)0);Arrays.fill(raw,(byte)0);
        assertComplete(old,actual);
        assertThrows(UnsupportedOperationException.class,()->actual.commandHistory().clear());
        String optional=text(backup).replace("\"succession_lifecycle\":{\"original\":true},","").replace(",\"rollback_war_failures\":[{\"reason\":\"original\"}]","");
        var absent=assertEquivalent(bytes(optional));
        assertNotNull(absent);assertInstanceOf(DriverStateSnapshot.Missing.class,absent.successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.Missing.class,absent.rollbackWarFailures());
        var nulls=assertEquivalent(bytes(text(backup).replace("\"campaign_goal\":"+payload,"\"campaign_goal\":null")));
        assertNotNull(nulls);assertInstanceOf(DriverStateSnapshot.NullValue.class,nulls.campaignGoal());
    }

    @Test void originalUnicodeKeysValuesLiteralEscapesAndSurrogateFallbackRetainTheLegacyDomainAndBytes() {
        String slash=Character.toString((char)92),escaped=slash+"u";
        String emoji=new String(Character.toChars(0x1f600));
        List<String> values=List.of("\"ASCII ??\"","\""+emoji+"\"",
                "\""+escaped+"D83D"+escaped+"DE00\"","\""+escaped+"D83D\"","\""+escaped+"DE00\"",
                "{\""+emoji+"\":1,\"ascii\":2}","{\""+escaped+"D83D"+escaped+"DE00\":1,\"ascii\":2}",
                "{\""+escaped+"D83D\":1,\"ascii\":2}","{\""+escaped+"DE00\":1,\"ascii\":2}",
                "\""+slash+slash+"uD83D\"","{\"literal\":\""+slash+slash+"uDE00\",\"n\":-0.00e+03}",
                "[\""+emoji+"\",{\"nested\":\""+escaped+"D83D\"},18446744073709551617]",
                "\""+escaped+"0000\"","\""+slash+"n"+slash+"t"+slash+Character.toString((char)34)+slash+slash+"\"");
        for(String value:values) {
            byte[] raw=document(value);byte[] backup=raw.clone();
            assertEquivalent(raw);assertArrayEquals(backup,raw);
            var legacy=LegacyDriverStateSnapshot.decodeComplete(backup);
            var verified=DriverStateSnapshot.Complete.decodeAndVerify(raw,(complete,row)->assertComplete(legacy,complete));
            assertComplete(legacy,verified);
        }
        assertEquivalent(document("\""+"a".repeat(32769)+"\""));
        assertEquivalent(document("\""+"?".repeat(4096)+"\""));
    }

    @Test void duplicateTrailingDepthAndMalformedUtf8ErrorsHaveExactlyTheOriginalCauseAndLocationOrder() {
        List<byte[]> invalid=new ArrayList<>();
        invalid.add(bytes("{"));invalid.add(bytes("[]"));invalid.add(bytes("null"));
        invalid.add(bytes(text(document("{}"))+" false"));
        invalid.add(bytes(text(document("{}" )).replace("\"format_version\":2","\"format_version\":2,\"format_version\":2")));
        invalid.add(document("{\"duplicate\":1,\"duplicate\":2}"));
        invalid.add(document("\"bad"+Character.toString((char)1)+"control\""));
        invalid.add(document("\"bad"+Character.toString((char)92)+"q\""));
        invalid.add(bytes(text(document("{}" )).replace("\"index\":1,","\"index\":1.0,")));
        invalid.add(bytes(text(document("{}" )).replace("\"index\":1,","\"index\":2,")));
        invalid.add(bytes(text(document("{}" )).replace("\"format_version\":2","\"unknown_top\":1,\"format_version\":2")));
        for(byte[] raw:List.copyOf(invalid)) {
            byte[] tail=Arrays.copyOf(raw,raw.length+1);tail[tail.length-1]=(byte)0xff;invalid.add(tail);
        }
        byte[] truncated=Arrays.copyOf(document("{}"),document("{}").length+2);
        truncated[truncated.length-2]=(byte)0xe2;truncated[truncated.length-1]=(byte)0x82;invalid.add(truncated);
        for(byte[] raw:invalid)assertNull(assertEquivalent(raw));
        int accepted=0,rejected=0;
        for(int depth:new int[]{0,1,58,59,60,61,62,63,64,65}) {
            var value=assertEquivalent(document("[".repeat(depth)+"0"+"]".repeat(depth)));
            if(value==null)rejected++;else accepted++;
        }
        assertTrue(accepted>0);assertTrue(rejected>0);
        byte[] original=document("{}");
        byte[] bom=new byte[original.length+3];bom[0]=(byte)0xef;bom[1]=(byte)0xbb;bom[2]=(byte)0xbf;System.arraycopy(original,0,bom,3,original.length);
        assertEquivalent(bom);
        assertEquivalent(text(original).getBytes(StandardCharsets.UTF_16BE));
        assertEquivalent(text(original).getBytes(StandardCharsets.UTF_16LE));
    }

    @Test void actualVerifierNestedDecodeAndCallerMutationsCannotAlterAnyConstructedTypedValue() {
        byte[] raw=document("{\"tag\":\"outer\",\"n\":1.00e+2}");byte[] backup=raw.clone();
        byte[] nestedRaw=document("{\"tag\":\"inner\",\"n\":-0.000e-02}");byte[] nestedBackup=nestedRaw.clone();
        var expected=LegacyDriverStateSnapshot.decodeComplete(backup);
        var nestedExpected=LegacyDriverStateSnapshot.decodeComplete(nestedBackup);
        var events=new ArrayList<String>();var escapedRow=new AtomicReference<ObjectNode>();
        var actual=DriverStateSnapshot.Complete.decodeAndVerify(raw,(complete,row)->{
            events.add("outer");escapedRow.set(row);assertComplete(expected,complete);assertArrayEquals(backup,raw);
            var nested=DriverStateSnapshot.Complete.decodeAndVerify(nestedRaw,(inner,innerRow)->{
                events.add("inner");assertComplete(nestedExpected,inner);assertNotSame(row,innerRow);
                innerRow.removeAll();Arrays.fill(nestedRaw,(byte)0);rejectPublicForgeries();assertComplete(nestedExpected,inner);
            });
            assertComplete(nestedExpected,nested);assertComplete(expected,complete);events.add("outer-after-inner");
            row.withArray("command_history").removeAll();row.removeAll();row.put("changed_after_decode",true);
            Arrays.fill(raw,(byte)0);rejectPublicForgeries();assertComplete(expected,complete);
        });
        assertEquals(List.of("outer","inner","outer-after-inner"),events);
        assertComplete(expected,actual);escapedRow.get().put("later_mutation",true);assertComplete(expected,actual);
        var oldEvents=new ArrayList<String>();
        var old=LegacyDriverStateSnapshot.Complete.decodeAndVerify(backup,(complete,row)->{
            oldEvents.add("outer");
            LegacyDriverStateSnapshot.Complete.decodeAndVerify(nestedBackup,(inner,innerRow)->{oldEvents.add("inner");innerRow.removeAll();});
            oldEvents.add("outer-after-inner");row.removeAll();
        });
        assertEquals(oldEvents,events);assertComplete(old,actual);
        assertComplete(expected,DriverStateSnapshot.decodeComplete(backup));
    }

    @Test void nullVerifierFailureIdentityAndRecoveryKeepTheOriginalCallbackBoundaries() {
        assertSameFailure(()->LegacyDriverStateSnapshot.Complete.decodeAndVerify(null,null),
                ()->DriverStateSnapshot.Complete.decodeAndVerify(null,null));
        assertSameFailure(()->LegacyDriverStateSnapshot.Complete.decodeAndVerify(bytes("{"),null),
                ()->DriverStateSnapshot.Complete.decodeAndVerify(bytes("{"),null));
        var calls=new AtomicInteger();
        assertSameFailure(()->LegacyDriverStateSnapshot.Complete.decodeAndVerify(bytes("{"),(value,row)->calls.incrementAndGet()),
                ()->DriverStateSnapshot.Complete.decodeAndVerify(bytes("{"),(value,row)->calls.incrementAndGet()));
        assertEquals(0,calls.get());
        byte[] raw=document("{\"original\":true}");byte[] backup=raw.clone();
        var expected=LegacyDriverStateSnapshot.decodeComplete(raw);
        var sentinel=new IllegalStateException("original verifier failure",new IllegalArgumentException("original cause"));
        assertSame(sentinel,assertThrows(IllegalStateException.class,()->LegacyDriverStateSnapshot.Complete.decodeAndVerify(raw,(value,row)->{throw sentinel;})));
        assertSame(sentinel,assertThrows(IllegalStateException.class,()->DriverStateSnapshot.Complete.decodeAndVerify(raw,(value,row)->{
            calls.incrementAndGet();assertComplete(expected,value);row.removeAll();rejectPublicForgeries();throw sentinel;
        })));
        assertArrayEquals(backup,raw);assertEquals(1,calls.get());
        var marker=new AssertionError("original verifier Error");
        assertSame(marker,assertThrows(AssertionError.class,()->DriverStateSnapshot.Complete.decodeAndVerify(raw,(value,row)->{throw marker;})));
        var next=DriverStateSnapshot.Complete.decodeAndVerify(raw,(value,row)->{calls.incrementAndGet();assertComplete(expected,value);rejectPublicForgeries();});
        assertEquals(2,calls.get());assertComplete(expected,next);rejectPublicForgeries();
    }

    @Test void allPublicConstructorsAndBoundedInputRejectionsRemainIndependentOfThePrivateEncoder() {
        for(byte[] raw:new byte[][]{null,new byte[0]}) {
            assertBoundedFailure(()->LegacyDriverStateSnapshot.decodeComplete(raw),()->DriverStateSnapshot.decodeComplete(raw),raw);
            assertBoundedFailure(()->new LegacyDriverStateSnapshot.Value(raw),()->new DriverStateSnapshot.Value(raw),raw);
        }
        rejectPublicForgeries();
        byte[] raw=document("{\"one\":1}");var expected=LegacyDriverStateSnapshot.decodeComplete(raw);var actual=DriverStateSnapshot.decodeComplete(raw);
        var originalHistory=new ArrayList<>(actual.commandHistory());
        var copied=publicCopy(actual,originalHistory,actual.lastCheckpoint());originalHistory.clear();assertComplete(expected,copied);
        assertSameFailure(()->publicCopy(expected,List.of(expected.commandHistory().get(1),expected.commandHistory().getFirst()),expected.lastCheckpoint()),
                ()->publicCopy(actual,List.of(actual.commandHistory().get(1),actual.commandHistory().getFirst()),actual.lastCheckpoint()));
        assertSameFailure(()->publicCopy(expected,expected.commandHistory(),new LegacyDriverStateSnapshot.Missing()),
                ()->publicCopy(actual,actual.commandHistory(),new DriverStateSnapshot.Missing()));
        byte[] mutable=bytes("{\"index\":1,\"n\":1.00}");
        var oldValue=new LegacyDriverStateSnapshot.Value(mutable);var currentValue=new DriverStateSnapshot.Value(mutable);
        byte[] oldBytes=oldValue.json();Arrays.fill(mutable,(byte)0);byte[] returned=currentValue.json();Arrays.fill(returned,(byte)0);
        assertArrayEquals(oldBytes,currentValue.json());
        JsonNode originalTree=FullJsonTree.parse(bytes("{\"n\":1.2300e+004}"),128);
        assertEquals("complete JSON material exceeds its explicit lease",assertThrows(IllegalArgumentException.class,()->FullJsonTree.encode(originalTree,1)).getMessage());
        // MAX is 256 MiB. Its unchanged public guard is source-bound; no oversized allocation is manufactured here.
        assertEquals(268435456,MAX);
    }

    private static DriverStateSnapshot.Complete assertEquivalent(byte[] raw) {
        LegacyDriverStateSnapshot.Complete expected=null;RuntimeException oldFailure=null;
        try{expected=LegacyDriverStateSnapshot.decodeComplete(raw);}catch(RuntimeException failure){oldFailure=failure;}
        DriverStateSnapshot.Complete actual=null;RuntimeException newFailure=null;
        try{actual=DriverStateSnapshot.decodeComplete(raw);}catch(RuntimeException failure){newFailure=failure;}
        if(oldFailure!=null){assertNotNull(newFailure,"candidate accepted legacy-rejected bytes");assertEquals(failure(oldFailure),failure(newFailure));return null;}
        if(newFailure!=null)throw new AssertionError("candidate rejected legacy-accepted bytes",newFailure);
        assertNotNull(expected);assertNotNull(actual);assertComplete(expected,actual);return actual;
    }
    private static void assertComplete(LegacyDriverStateSnapshot.Complete expected,DriverStateSnapshot.Complete actual) {
        assertEquals(expected.session().pipeName(),actual.session().pipeName());assertEquals(expected.session().bridgePid(),actual.session().bridgePid());
        assertEquals(expected.session().actorId(),actual.session().actorId());assertEquals(expected.session().episodeRunId(),actual.session().episodeRunId());
        assertEquals(expected.commandHistory().size(),actual.commandHistory().size());
        for(int i=0;i<expected.commandHistory().size();i++){
            assertEquals(expected.commandHistory().get(i).index(),actual.commandHistory().get(i).index());
            assertArrayEquals(expected.commandHistory().get(i).originalRow().json(),actual.commandHistory().get(i).originalRow().json());
        }
        var es=List.of(expected.lastCheckpoint(),expected.rollbackWarFailure(),expected.managedRestoreTransaction(),expected.successionExpectation(),expected.successionLifecycle(),expected.campaignGoal(),expected.rollbackWarFailures());
        var as=List.of(actual.lastCheckpoint(),actual.rollbackWarFailure(),actual.managedRestoreTransaction(),actual.successionExpectation(),actual.successionLifecycle(),actual.campaignGoal(),actual.rollbackWarFailures());
        for(int i=0;i<es.size();i++){
            assertEquals(es.get(i).getClass().getSimpleName(),as.get(i).getClass().getSimpleName());
            if(es.get(i) instanceof LegacyDriverStateSnapshot.Value value)assertArrayEquals(value.json(),((DriverStateSnapshot.Value)as.get(i)).json());
        }
        assertArrayEquals(expected.encode(),actual.encode());
        assertEquals(FullJsonTree.parse(expected.encode(),MAX),FullJsonTree.parse(actual.encode(),MAX));
    }
    private static void assertSameFailure(Executable oldCall,Executable currentCall) {
        RuntimeException expected=assertThrows(RuntimeException.class,oldCall);RuntimeException actual=assertThrows(RuntimeException.class,currentCall);
        assertEquals(failure(expected),failure(actual));
    }
    private static void assertBoundedFailure(Executable oldCall,Executable currentCall,byte[] raw) {
        RuntimeException expected=assertThrows(RuntimeException.class,oldCall);RuntimeException actual=assertThrows(RuntimeException.class,currentCall);
        assertEquals(expected.getClass(),actual.getClass());
        String prefix="bounded complete JSON material required: input="+(raw==null?"null":raw.length)+" max="+MAX+" callers=";
        assertTrue(expected.getMessage().startsWith(prefix));assertTrue(actual.getMessage().startsWith(prefix));
        assertTrue(expected.getMessage().substring(prefix.length()).contains("LegacyDriverStateSnapshot"));
        assertTrue(actual.getMessage().substring(prefix.length()).contains("DriverStateSnapshot"));
        assertTrue(expected.getMessage().substring(prefix.length()).length()<=768);assertTrue(actual.getMessage().substring(prefix.length()).length()<=768);
        assertNull(expected.getCause());assertNull(actual.getCause());assertEquals(0,expected.getSuppressed().length);assertEquals(0,actual.getSuppressed().length);
    }
    private record Location(long bytes,long chars,int line,int column) { }
    private record Failure(String type,String message,Location location,Failure cause,List<Failure> suppressed) { }
    private static Failure failure(Throwable value) {
        Location location=null;
        if(value instanceof JsonProcessingException json && json.getLocation()!=null){
            JsonLocation at=json.getLocation();assertNull(at.contentReference().getRawContent());
            location=new Location(at.getByteOffset(),at.getCharOffset(),at.getLineNr(),at.getColumnNr());
        }
        var suppressed=new ArrayList<Failure>();for(Throwable child:value.getSuppressed())suppressed.add(failure(child));
        return new Failure(value.getClass().getName(),value.getMessage(),location,value.getCause()==null?null:failure(value.getCause()),List.copyOf(suppressed));
    }
    private static void rejectPublicForgeries() {
        assertSameFailure(()->new LegacyDriverStateSnapshot.Value(bytes("null")),()->new DriverStateSnapshot.Value(bytes("null")));
        assertSameFailure(()->new LegacyDriverStateSnapshot.Value(bytes("{")),()->new DriverStateSnapshot.Value(bytes("{")));
        assertSameFailure(()->new LegacyDriverStateSnapshot.HistoryEntry(2,new LegacyDriverStateSnapshot.Value(bytes("{\"index\":1}"))),
                ()->new DriverStateSnapshot.HistoryEntry(2,new DriverStateSnapshot.Value(bytes("{\"index\":1}"))));
        assertSameFailure(()->new LegacyDriverStateSnapshot.HistoryEntry(1,new LegacyDriverStateSnapshot.Value(bytes("{\"index\":1.0}"))),
                ()->new DriverStateSnapshot.HistoryEntry(1,new DriverStateSnapshot.Value(bytes("{\"index\":1.0}"))));
    }
    private static DriverStateSnapshot.Complete publicCopy(DriverStateSnapshot.Complete x,List<DriverStateSnapshot.HistoryEntry> rows,DriverStateSnapshot.Slot checkpoint){
        return new DriverStateSnapshot.Complete(x.session(),rows,checkpoint,x.rollbackWarFailure(),x.managedRestoreTransaction(),x.successionExpectation(),x.successionLifecycle(),x.campaignGoal(),x.rollbackWarFailures());
    }
    private static LegacyDriverStateSnapshot.Complete publicCopy(LegacyDriverStateSnapshot.Complete x,List<LegacyDriverStateSnapshot.HistoryEntry> rows,LegacyDriverStateSnapshot.Slot checkpoint){
        return new LegacyDriverStateSnapshot.Complete(x.session(),rows,checkpoint,x.rollbackWarFailure(),x.managedRestoreTransaction(),x.successionExpectation(),x.successionLifecycle(),x.campaignGoal(),x.rollbackWarFailures());
    }
    private static byte[] document(String payload) {
        return bytes("{\"format_version\":2,\"pipe_name\":\"legacy-private-writer\",\"bridge_pid\":42,\"episode_character_id\":73,\"episode_run_id\":\"legacy-episode\","
                +"\"last_checkpoint\":{\"path\":\"original\",\"revision\":9007199254740993},\"command_history\":[{\"index\":1,\"result\":"+payload+"},{\"index\":2,\"ok\":false,\"error\":\"????\"}],"
                +"\"rollback_war_failure\":null,\"managed_restore_transaction\":{\"phase\":\"completed\",\"lineage\":[\"parent\"]},\"succession_expectation\":{\"actor\":73,\"enabled\":false},"
                +"\"succession_lifecycle\":{\"original\":true},\"campaign_goal\":"+payload+",\"rollback_war_failures\":[{\"reason\":\"original\"}]}");
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static String text(byte[] value){return new String(value,StandardCharsets.UTF_8);}

    /** Complete original Driver v2 envelope. Legacy nested business values are retained, never invented. */
    private sealed interface LegacyDriverStateSnapshot permits LegacyDriverStateSnapshot.Complete, LegacyDriverStateSnapshot.Incomplete {
        record Incomplete(List<String> missingOrUnreconciledFields) implements LegacyDriverStateSnapshot {
            public Incomplete { missingOrUnreconciledFields = List.copyOf(missingOrUnreconciledFields); StrictJson.require(!missingOrUnreconciledFields.isEmpty(), "explicit incomplete Driver reasons"); }
        }
        sealed interface Slot permits Missing, NullValue, Value { }
        record Missing() implements Slot { }
        record NullValue() implements Slot { }
        record Value(byte[] json) implements Slot {
            public Value { json = checked(json); }
            @Override public byte[] json() { return json.clone(); }
            @Override public boolean equals(Object other) { return other instanceof Value value && java.util.Arrays.equals(json,value.json); }
            @Override public int hashCode() { return java.util.Arrays.hashCode(json); }
        }
        record HistoryEntry(long index, Value originalRow) {
            public HistoryEntry { StrictJson.safe(index, 1); Objects.requireNonNull(originalRow);
                StrictJson.require(historyIndex(originalRow) == index, "history entry typed index equals original integer token"); }
        }
        record Session(String pipeName, long bridgePid, BigInteger actorId, String episodeRunId) {
            public Session { StrictJson.text(pipeName); StrictJson.require(bridgePid > 0 && bridgePid <= 0xffff_ffffL, "uint32 Driver PID"); NativeCharacterId.of(actorId); StrictJson.text(episodeRunId); }
        }
        record Complete(Session session, List<HistoryEntry> commandHistory, Slot lastCheckpoint, Slot rollbackWarFailure,
                Slot managedRestoreTransaction, Slot successionExpectation, Slot successionLifecycle, Slot campaignGoal,
                Slot rollbackWarFailures) implements LegacyDriverStateSnapshot {
            // Exact, one-use constructor identities; never a cache or a caller-declared trust flag.
            private static final ThreadLocal<java.util.IdentityHashMap<Object, Object>> CONSTRUCTION = new ThreadLocal<>();
            public Complete {
                Objects.requireNonNull(session); commandHistory = List.copyOf(commandHistory);
                for (int i = 0; i < commandHistory.size(); i++) StrictJson.require(commandHistory.get(i).index() == i + 1L, "complete ordered Driver history");
                for (Slot slot : List.of(lastCheckpoint, rollbackWarFailure, managedRestoreTransaction, successionExpectation, successionLifecycle, campaignGoal, rollbackWarFailures)) Objects.requireNonNull(slot);
                StrictJson.require(!(lastCheckpoint instanceof Missing) && !(rollbackWarFailure instanceof Missing) && !(managedRestoreTransaction instanceof Missing)
                        && !(successionExpectation instanceof Missing) && !(campaignGoal instanceof Missing), "required original Driver fields may be null, never absent");
            }
            /** Strict bytes stay local; only detached typed DATA reaches the fixed anchor verifier. */
            static Complete decodeAndVerify(byte[] raw, java.util.function.BiConsumer<Complete, ObjectNode> verifier) {
                Objects.requireNonNull(verifier);
                byte[] owned = raw == null || raw.length == 0 || raw.length > DriverCheckpointStore.MAX_DRIVER_BYTES ? raw : raw.clone();
                ObjectNode row = object(parse(owned));
                Complete complete = decodeParsedComplete(row, provenStable(owned));
                verifier.accept(complete, row);
                return complete;
            }
            public byte[] encode() {
                ObjectNode row = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); row.put("format_version", 2); row.put("pipe_name", session.pipeName()); row.put("bridge_pid", session.bridgePid());
                row.put("episode_character_id", session.actorId()); row.put("episode_run_id", session.episodeRunId());
                var history = row.putArray("command_history"); commandHistory.forEach(entry -> history.add(parse(entry.originalRow().json)));
                put(row,"last_checkpoint",lastCheckpoint); put(row,"rollback_war_failure",rollbackWarFailure); put(row,"managed_restore_transaction",managedRestoreTransaction);
                put(row,"succession_expectation",successionExpectation); put(row,"succession_lifecycle",successionLifecycle); put(row,"campaign_goal",campaignGoal); put(row,"rollback_war_failures",rollbackWarFailures);
                return bytes(row);
            }
        }
        static Complete decodeComplete(byte[] raw) {
            byte[] owned = raw == null || raw.length == 0 || raw.length > DriverCheckpointStore.MAX_DRIVER_BYTES ? raw : raw.clone();
            ObjectNode row = object(parse(owned));
            return decodeParsedComplete(row, provenStable(owned));
        }
        private static Complete decodeParsedComplete(ObjectNode row, boolean provenStable) {
            Set<String> allowed = Set.of("format_version","pipe_name","bridge_pid","episode_character_id","episode_run_id","last_checkpoint","command_history","rollback_war_failure","managed_restore_transaction","succession_expectation","succession_lifecycle","campaign_goal","rollback_war_failures");
            row.fieldNames().forEachRemaining(key -> StrictJson.require(allowed.contains(key), "unmigrated top-level Driver field: " + key));
            StrictJson.integer(row.get("format_version"), 2, 2); StrictJson.require(row.get("command_history") != null && row.get("command_history").isArray(), "full Driver history required");
            List<HistoryEntry> history = new ArrayList<>(); for (JsonNode item : row.get("command_history")) { ObjectNode entry = object(item); history.add(parsedEntry(entry, provenStable)); }
            return new Complete(new Session(StrictJson.text(row.get("pipe_name")), StrictJson.integer(row.get("bridge_pid"), 1, 0xffff_ffffL),
                    NativeCharacterId.fromJson(row.get("episode_character_id")).asBigInteger(), StrictJson.text(row.get("episode_run_id"))), history,
                    slot(row,"last_checkpoint",provenStable),slot(row,"rollback_war_failure",provenStable),slot(row,"managed_restore_transaction",provenStable),slot(row,"succession_expectation",provenStable),slot(row,"succession_lifecycle",provenStable),slot(row,"campaign_goal",provenStable),slot(row,"rollback_war_failures",provenStable));
        }
        private static Slot slot(ObjectNode row, String key, boolean provenStable) { return !row.has(key) ? new Missing() : row.get(key).isNull() ? new NullValue() : parsedValue(row.get(key), provenStable); }
        private static void put(ObjectNode row, String key, Slot slot) { switch (slot) { case Missing ignored -> { } case NullValue ignored -> row.putNull(key); case Value value -> row.set(key,parse(value.json)); } }
        private static byte[] checked(byte[] raw) {
            var scope = Complete.CONSTRUCTION.get();
            if (raw != null && scope != null && scope.remove(raw) == raw) return raw.clone();
            JsonNode value=parse(raw); StrictJson.require(!value.isNull(),"null has its own explicit Driver slot"); return bytes(value);
        }
        private static long historyIndex(Value value) {
            var scope = Complete.CONSTRUCTION.get();
            Object index = scope == null ? null : scope.remove(value);
            if (index instanceof Long original) return original;
            ObjectNode row = object(parse(value.json));
            return StrictJson.integer(row.get("index"), 1, StrictJson.MAX_SAFE_INTEGER);
        }
        // Called only with private strict-parser trees. The first encode retains all original tree/budget checks.
        private static Value parsedValue(JsonNode node, boolean provenStable) {
            byte[] raw = bytes(node);
            if (!provenStable && !stableParserTree(node)) return new Value(raw);
            var previous = Complete.CONSTRUCTION.get();
            var scope = new java.util.IdentityHashMap<Object, Object>();
            scope.put(raw, raw); Complete.CONSTRUCTION.set(scope);
            try { return new Value(raw); }
            finally { if (previous == null) Complete.CONSTRUCTION.remove(); else Complete.CONSTRUCTION.set(previous); }
        }
        private static HistoryEntry parsedEntry(ObjectNode node, boolean provenStable) {
            long index = StrictJson.integer(node.get("index"), 1, StrictJson.MAX_SAFE_INTEGER);
            byte[] raw = bytes(node);
            if (!provenStable && !stableParserTree(node)) return new HistoryEntry(index, new Value(raw));
            var previous = Complete.CONSTRUCTION.get();
            var scope = new java.util.IdentityHashMap<Object, Object>();
            scope.put(raw, raw); Complete.CONSTRUCTION.set(scope);
            try {
                Value value = new Value(raw);
                scope.put(value, index);
                return new HistoryEntry(index, value);
            } finally { if (previous == null) Complete.CONSTRUCTION.remove(); else Complete.CONSTRUCTION.set(previous); }
        }
        // Surrogate handling can affect an encode/parse round trip; retain the original constructors for that domain.
        private static boolean stableParserTree(JsonNode node) {
            if (node.isTextual() && hasSurrogate(node.textValue())) return false;
            if (node.isObject()) {
                var names = node.fieldNames();
                while (names.hasNext()) if (hasSurrogate(names.next())) return false;
            }
            for (JsonNode child : node) if (!stableParserTree(child)) return false;
            return true;
        }
        private static boolean hasSurrogate(String text) {
            for (int i = 0; i < text.length(); i++) if (Character.isSurrogate(text.charAt(i))) return true;
            return false;
        }

        private static boolean provenStable(byte[] raw) {
            if (raw == null) return false;
            for (int i = 0; i < raw.length; i++) {
                int b = raw[i] & 0xFF;
                if (b == 0x5C && i + 1 < raw.length && raw[i + 1] == 0x75) return false;
                if (b >= 0xF0) return false;
            }
            return true;
        }
        private static JsonNode parse(byte[] raw) {
            // The sole material parser validates JSON tokens. Opaque decimal lexemes are not binary64 fields.
            return FullJsonTree.parse(raw,DriverCheckpointStore.MAX_DRIVER_BYTES);
        }
        private static ObjectNode object(JsonNode node) { StrictJson.require(node instanceof ObjectNode, "Driver object required"); return (ObjectNode)node; }
        private static byte[] bytes(JsonNode node) { return FullJsonTree.encode(node,DriverCheckpointStore.MAX_DRIVER_BYTES); }
    }
}
