package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.util.RawValue;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import static org.junit.jupiter.api.Assertions.*;

/** Controlled retained SEM fixtures exercise the production codec and assessment chain; no live authority. */
class NativeSemanticCharacterIdTest {
    private static final String SHA="1".repeat(64);
    private static final Instant NOW=Instant.parse("2026-10-22T13:30:00Z");
    private static final int ACTOR=40526;
    private enum Role {
        EPISODE("episode_character_id"), PLAYED("character_id");
        private final String field;
        Role(String field){this.field=field;}
        private ObjectNode parent(ObjectNode frame){return this==PLAYED?(ObjectNode)frame.get("played_character"):frame;}
        void set(ObjectNode frame,int value){parent(frame).put(field,value);}
        void raw(ObjectNode frame,String token){parent(frame).putRawValue(field,new RawValue(token));}
        void remove(ObjectNode frame){parent(frame).remove(field);}
    }
    private static byte[] retained(String name,String expected) throws Exception {
        try(var input=NativeSemanticCharacterIdTest.class.getResourceAsStream("/"+name)) {
            assertNotNull(input,"retained original fixture is required, never skipped");
            byte[] value=input.readAllBytes();
            assertEquals(expected,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)));
            return value;
        }
    }
    private static ObjectNode frame() throws Exception {
        return (ObjectNode)StrictJson.parse(retained("synthetic-late-semantic.json","0bb2012e12681a4c6faa94373d04d0fb18be5c0db0c57d07019ecf634edc9be8"));
    }
    private static Status stop() throws Exception {
        return SentinelCodec.decode(retained("synthetic-late-status.json","c48feb50adf7a132a04dbb3fd9723c747e5dddf53188093278fc0e24efe545c4"));
    }
    private static byte[] wire(ObjectNode row){return row.toString().getBytes(StandardCharsets.UTF_8);}
    private static Semantic decode(ObjectNode row){return NativeSemanticCodec.decode(wire(row),16_384);}
    private static CrossJsDecimalUInt64 u(long value){return new CrossJsDecimalUInt64(Long.toString(value));}
    private static ContentEvidenceRef ref(String key){return new ContentEvidenceRef(SHA,1,key);}
    private static Scope scope(int actor){
        return new Scope("synthetic-machine-not-runtime",new ProcessIdentity(12345,u(1000)),new ProcessIdentity(23456,u(2000)),
                new ProcessIdentity(34567,u(3000)),"synthetic-session",new SourceBinding(SHA,SHA,SHA,SHA,SHA),1,actor,
                "synthetic-episode",new WorldIdentity(u(111),u(222)));
    }
    private static Attempt attempt(Scope scope){
        return new Attempt(scope,new OriginalFailure(ref("original-error"),11543,11558,false,false),
                new Arm(u(1),53279400,53279424,3,Mode.TERMINAL_OR_SENTINEL,List.of(),0),ref("original-writer-head"),3,u(101),u(201));
    }
    private static Evidence evidence(Scope scope,long sequence,long elapsed){
        return new Evidence(scope,scope,sequence,ref("synthetic-read-"+sequence),elapsed,NOW.minusMillis(1000-elapsed),u(900100));
    }
    private static Assessment assess(Attempt attempt,Semantic semantic,Status stop){
        Scope scope=attempt.scope();List<Read> reads=List.of(new StatusRead(evidence(scope,11559,100),stop),
                new SemanticRead(evidence(scope,11560,200),semantic),new StatusRead(evidence(scope,11561,300),stop));
        return LateOutcomePlanner.assess(attempt,new Budget(30_000,8,2000,100,NOW.plusSeconds(30)),
                new Context(GameLife.SAME_PROCESS_ALIVE,1000,NOW,reads.size()),reads);
    }
    private static Semantic actors(Semantic source,int actor,int played){
        return new Semantic(source.dateRaw(),source.paused(),source.mapReady(),source.speed(),source.nativeRevision(),source.publicRevision(),
                source.snapshotId(),actor,source.episodeId(),played,source.playedActorAlive(),source.oneLifeTerminal(),source.episodeIdentityPending(),
                source.connected(),source.connectionGeneration(),source.bridgePid(),source.heartbeatSequence(),source.heartbeatMillis(),source.heartbeatPid(),
                source.pumpEpoch(),source.verifiedPumpEpoch(),source.ownerTid(),source.currentTid(),source.world(),source.ownerDateRaw(),
                source.ownerPaused(),source.stampReadSuccess(),source.mailboxStop(),source.mailboxFailure());
    }

    @Test void signedPublicActorValuesReachExistingPlannerAndAssessmentSerdeWithoutPrivateScopeWidening() throws Exception {
        Status status=stop();
        for(int value:new int[]{Integer.MIN_VALUE,-2147418112,-2,0,1,ACTOR,Integer.MAX_VALUE}) {
            ObjectNode original=frame();Role.EPISODE.set(original,value);Role.PLAYED.set(original,value);
            Semantic semantic=decode(original);
            assertEquals(value,semantic.actorId());assertEquals(value,semantic.playedActorId());
            assertEquals(NativeCharacterId.of(BigInteger.valueOf(value)).value(),semantic.actorId());
            assertEquals(semantic,NativeSemanticCodec.decode(StrictJson.canonical(original,16_384),16_384));
            assertEquals(semantic,actors(decode(frame()),value,value),"direct immutable Semantic construction uses the same formal domain");
            // Public observations do not authorize a new nonpositive Queue/action scope.
            Scope expectedScope=scope(value>0?value:ACTOR);Attempt attempt=attempt(expectedScope);
            Assessment result=assess(attempt,semantic,status);
            assertEquals(value>0?Outcome.PROPOSED:Outcome.REJECTED,result.outcome());
            assertEquals(value>0?Reason.LATE_STOP_REQUIRES_WRITER_REDUCER:Reason.FRAME_IDENTITY_CHANGED,result.reason());
            assertEquals(result,AssessmentCodec.decode(AssessmentCodec.encode(attempt,result),attempt));
            assertEquals(0,result.originalCredit());assertTrue(result.neverReplay());
            if(value<=0)assertThrows(ContractViolationException.class,()->scope(value));
        }
    }

    @Test void eachSelectedRoleAcceptsSignedIdentityIndependentlyAndNeverReinterpretsItAsUnsigned() throws Exception {
        for(Role role:Role.values())for(int value:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}) {
            ObjectNode original=frame();role.set(original,value);Semantic semantic=decode(original);
            assertEquals(value,role==Role.EPISODE?semantic.actorId():semantic.playedActorId());
            assertEquals(ACTOR,role==Role.EPISODE?semantic.playedActorId():semantic.actorId());
            if(value<0)assertTrue((role==Role.EPISODE?semantic.actorId():semantic.playedActorId())<0);
        }
    }

    @Test void absentSentinelOverflowBoolFloatStringNullAndWrongFieldsCannotAliasEitherObservedRole() throws Exception {
        for(Role role:Role.values()) {
            for(String token:List.of("-1","2147483648","-2147483649","4294967294","true","false","1.0","-2.0","\"0\"","\"-2\"","null","[]","{}")) {
                ObjectNode original=frame();role.raw(original,token);
                assertThrows(ContractViolationException.class,()->decode(original),role+"="+token);
            }
            ObjectNode missing=frame();role.remove(missing);
            assertThrows(ContractViolationException.class,()->decode(missing));
            ObjectNode alias=frame();role.remove(alias);role.parent(alias).put("actor_id",0);
            assertThrows(ContractViolationException.class,()->decode(alias),"an old or guessed field name is not an alias");
        }
    }

    @Test void directSemanticConstructionCannotBypassSentinelGuardAndUnrelatedPositiveContractsStayStrict() throws Exception {
        Semantic original=decode(frame());
        assertThrows(ContractViolationException.class,()->actors(original,-1,ACTOR));
        assertThrows(ContractViolationException.class,()->actors(original,ACTOR,-1));
        for(int value:new int[]{Integer.MIN_VALUE,-2,-1,0})assertThrows(ContractViolationException.class,()->scope(value));
        assertThrows(ContractViolationException.class,()->new Arm(u(1),53279400,53279424,3,Mode.TERMINAL_OR_SENTINEL,List.of(-2),0));
        ObjectNode invalidSpeed=frame();invalidSpeed.put("speed",0);assertThrows(ContractViolationException.class,()->decode(invalidSpeed));
        ObjectNode invalidConnection=frame();((ObjectNode)invalidConnection.get("diagnostics")).put("connection_generation",0);
        assertThrows(ContractViolationException.class,()->decode(invalidConnection));
    }
}
