package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual structural producers/codecs consume controlled identity DATA. No source issuer, Root readiness or live negative ID is invented. */
final class ObservedActorIdentityContractTest {
    private static final Instant NOW=Instant.parse("2026-10-24T06:00:00Z");
    private static final String MACHINE="controlled-observed-actor";
    private static final BigInteger CONNECTION=new BigInteger("9007199254740993");
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final ExactRef BEFORE=ref("before",'a'),AFTER=ref("after",'b'),HELLO=ref("hello",'c');
    private static final G2Source SOURCE=new G2Source(MACHINE,NOW.toString(),"1.20.0.4",ref("source",'d'));
    private static ExactRef ref(String name,char digest) {
        return new ExactRef(Path.of("controlled-observed-actor",name+".json").toAbsolutePath().normalize().toString(),1,String.valueOf(digest).repeat(64));
    }
    private static LifecycleIdentity terminal(BigInteger actor,LifecycleIdentity.CurrentPlayer actual,LifecycleIdentity.TerminalReason reason) {
        return new LifecycleIdentity(MACHINE,GAME,"terminal-1",CONNECTION,new LifecycleIdentity.Subject(actor,"episode-old",2,9),
                new LifecycleIdentity.Frame("native:7",BigInteger.valueOf(11),BigInteger.valueOf(7),BigInteger.valueOf(100),true,true),actual,reason,
                new LifecycleIdentity.Evidence(BEFORE,HELLO,ref("manifest",'e'),ref("old-driver",'f'),ref("qualification",'0')),NOW);
    }
    private static LifecycleIdentity dead(BigInteger actor) {return terminal(actor,new LifecycleIdentity.Character(actor,false),LifecycleIdentity.TerminalReason.DEAD);}
    private static ObjectNode cycle(ObjectNode value) {return (ObjectNode)StrictJson.parse(StrictJson.canonical(value));}

    @Test void lifecycleActualSubjectAndCurrentPlayerKeepFullSignedIdsThroughBothSoleCodecs() {
        for(int value:new int[]{Integer.MIN_VALUE,-16777217,-2,0,1,Integer.MAX_VALUE}) {
            var expected=dead(BigInteger.valueOf(value));var encoded=LifecycleIdentityCodec.encode(expected);
            assertEquals(Integer.toString(value),encoded.get("subject").get("character_id").textValue());
            assertEquals(Integer.toString(value),encoded.get("current_player").get("character_id").textValue());
            assertEquals(expected,LifecycleIdentityCodec.decode(cycle(encoded)));
            var origin=new CommandOrigin.LifecycleTerminal(expected);
            assertEquals(origin,CommandOriginCodec.origin(cycle(CommandOriginCodec.origin(origin))));
            assertEquals(expected.bindingSha256(),LifecycleIdentityCodec.decode(cycle(encoded)).bindingSha256());
        }
        var positive=LifecycleIdentityCodec.encode(dead(BigInteger.valueOf(7)));
        assertEquals("\"7\"",new String(StrictJson.canonical(positive.get("subject").get("character_id")),StandardCharsets.UTF_8));
        assertEquals("\"7\"",new String(StrictJson.canonical(positive.get("current_player").get("character_id")),StandardCharsets.UTF_8));
        assertEquals(CONNECTION.toString(),positive.get("connection_generation").textValue());
    }
    @Test void lifecycleMissingNullDeadAndChangedRemainDistinctSourceFacts() {
        BigInteger actor=BigInteger.valueOf(-2);
        var missing=terminal(actor,new LifecycleIdentity.Missing(),LifecycleIdentity.TerminalReason.MISSING);
        var nil=terminal(actor,new LifecycleIdentity.Null(),LifecycleIdentity.TerminalReason.MISSING);
        var changed=terminal(actor,new LifecycleIdentity.Character(BigInteger.valueOf(Integer.MIN_VALUE),true),LifecycleIdentity.TerminalReason.CHANGED);
        for(var value:List.of(missing,nil,changed,dead(actor)))assertEquals(value,LifecycleIdentityCodec.decode(cycle(LifecycleIdentityCodec.encode(value))));
        assertNotEquals(missing.currentPlayer(),nil.currentPlayer());
        assertThrows(IllegalArgumentException.class,()->terminal(actor,new LifecycleIdentity.Character(actor,true),LifecycleIdentity.TerminalReason.DEAD));
        assertThrows(IllegalArgumentException.class,()->terminal(actor,new LifecycleIdentity.Character(actor,false),LifecycleIdentity.TerminalReason.CHANGED));
        var inventedNull=LifecycleIdentityCodec.encode(nil);((ObjectNode)inventedNull.get("current_player")).put("character_id","-2");
        assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(inventedNull));
    }
    @Test void lifecycleDurableStringsAreCanonicalAndNeverAliasPublicIntegerOrWrongJsonTypes() {
        for(BigInteger value:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))) {
            assertThrows(IllegalArgumentException.class,()->new LifecycleIdentity.Subject(value,"episode",0,0));
            assertThrows(IllegalArgumentException.class,()->new LifecycleIdentity.Character(value,false));
        }
        assertThrows(IllegalArgumentException.class,()->new LifecycleIdentity.Character(null,false));
        var factory=JsonNodeFactory.instance;
        for(String field:List.of("subject","current_player")) {
            for(String value:List.of("-1","2147483648","-2147483649","-0","+2","02","-02","-2.0","-2e0"," -2")) {
                var row=LifecycleIdentityCodec.encode(dead(BigInteger.valueOf(-2)));((ObjectNode)row.get(field)).put("character_id",value);
                assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(row));
            }
            for(JsonNode value:List.of(factory.numberNode(-2),factory.numberNode(-2.0),factory.booleanNode(false),factory.booleanNode(true),factory.nullNode(),factory.arrayNode())) {
                var row=LifecycleIdentityCodec.encode(dead(BigInteger.valueOf(-2)));((ObjectNode)row.get(field)).set("character_id",value);
                assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(row));
            }
            var missing=LifecycleIdentityCodec.encode(dead(BigInteger.valueOf(-2)));((ObjectNode)missing.get(field)).remove("character_id");
            assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(missing));
        }
        assertThrows(IllegalArgumentException.class,()->NativeCharacterId.fromJson(factory.textNode("-2")),"durable decimal text is not a public-snapshot integer alias");
    }
    @Test void lifecycleNonActorPositiveAndReasonBindingRemainStrict() {
        var original=LifecycleIdentityCodec.encode(dead(BigInteger.valueOf(-2)));
        var connection=original.deepCopy();connection.put("connection_generation","0");assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(connection));
        for(String field:List.of("revision","native_revision")) {
            var row=original.deepCopy();((ObjectNode)row.get("frame")).put(field,"0");assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(row));
        }
        var epoch=original.deepCopy();((ObjectNode)epoch.get("subject")).put("episode_epoch",-1);assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(epoch));
        var version=original.deepCopy();((ObjectNode)version.get("subject")).put("driver_version",-1);assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(version));
        var alive=original.deepCopy();((ObjectNode)alive.get("current_player")).put("alive",true);assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(alive));
        var mismatch=original.deepCopy();((ObjectNode)mismatch.get("current_player")).put("character_id","-3");assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(mismatch));
    }

    private static FrontendIdentity menu() {return new FrontendIdentity(MACHINE,GAME,"frontend-1",CONNECTION,GAME.pid(),new FrontendFrame.Menu(BigInteger.ONE),BEFORE,HELLO);}
    private static List<ExpectedValue> entryValues() {
        return List.of(new ExpectedText(new FieldKey("selected_bookmark_key"),"bm_1066_rags_to_riches"),
                new ExpectedText(new FieldKey("selected_character_name_key"),"bookmark_rags_to_riches_duke_robert"),
                new ExpectedInteger(new FieldKey("date_raw"),BigInteger.valueOf(100)),new ExpectedBoolean(new FieldKey("map_ready"),true),new ExpectedBoolean(new FieldKey("paused"),true));
    }
    private static ObservationIdentity frame(BigInteger actor) {
        return new ObservationIdentity(MACHINE,GAME,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,BigInteger.TWO,BigInteger.valueOf(100)),
                "native:2",BigInteger.TWO,"episode-new"),1);
    }
    private static SemanticEvidence semantic(BigInteger actor) {return new SemanticEvidence(frame(actor),ref("semantic",'e'),AFTER,ref("stamp",'f'),ref("driver",'0'),NOW.plusSeconds(1));}
    private static PlanningReadReceipt root(BigInteger actor) {
        var identity=frame(actor);var operation=new OperationKey("query-campaign-root-context-v1");
        var binding=new GuardEvidence(identity,SOURCE,"gameplay-1",CONNECTION,operation,AFTER,HELLO,"controlled-root-read",NOW.plusSeconds(1),NOW.plusSeconds(20));
        var guard=new PlanningReadGuard(binding,true,true,true,"a".repeat(64));
        var request=new PlanningReadRequest(identity,SOURCE,"gameplay-1",operation,new OpportunityJson.Obj(Map.of()),NOW.plusSeconds(30));
        var ack=new NativeActionPort.AckReceived("independent-data-root",true,Optional.empty(),new RawJson("{}".getBytes(StandardCharsets.UTF_8)),new byte[]{1});
        return new PlanningReadReceipt(request,"controlled-campaign-root","independent-data-root",guard,guard,ack);
    }
    private static FrontendGameplayObservation entered(BigInteger actor) {
        return new FrontendGameplayObservation(menu(),SOURCE,new SessionIdentity(MACHINE,GAME,"gameplay-1"),CONNECTION,"entry-data/v1",entryValues(),semantic(actor),root(actor),List.of(ref("start-basis",'8')));
    }
    @Test void actualFrameSemanticAndRootReceiptProducersRoundtripTheSignedEntryConsumer() {
        for(int value:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}) {
            var actual=entered(BigInteger.valueOf(value));var read=actual.campaignRootRead();var original=ref("root-receipt",'9');
            var wire=CommandOriginCodec.gameplayEntry(actual,receipt->{assertEquals(read,receipt);return original;});
            assertEquals(actual,CommandOriginCodec.gameplayEntry(cycle(wire),ref->{assertEquals(original,ref);return read;}));
            assertEquals(BigInteger.valueOf(value),actual.after().frame().identity().player());
            var expected=new FrontendGameplayExpectedPostcondition(menu(),SOURCE,"entry-data/v1","bm_1066_rags_to_riches","bookmark_rags_to_riches_duke_robert",100,entryValues());
            var command=new ActionCommand("controlled-entry",new CommandOrigin.Frontend(menu()),SOURCE,"frontend-1",new OperationKey("start-selected-fixture"),
                    new OpportunityJson.Obj(Map.of()),new CommandExpectation.GameplayEntry(expected),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
            var guard=new GuardEvidence(new CommandOrigin.Frontend(menu()),SOURCE,"frontend-1",CONNECTION,command.operation(),BEFORE,HELLO,"controlled-start-data",NOW,NOW.plusSeconds(20));
            var attempt=new ActionState.Attempt("start-data-request",NOW,guard,new NativeRequest(command.operation().value(),"game.command.fixture",new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
            actual.validate(command,attempt);
        }
    }
    @Test void signedEntryDoesNotRelaxMenuSourceSessionConnectionOrExactObservedActorEquality() {
        BigInteger actor=BigInteger.valueOf(-2);var actual=entered(actor);
        assertThrows(IllegalArgumentException.class,()->new FrontendGameplayObservation(menu(),SOURCE,new SessionIdentity(MACHINE,GAME,"foreign-session"),CONNECTION,
                "entry-data/v1",entryValues(),semantic(actor),root(actor),actual.supportingEvidence()));
        assertThrows(IllegalArgumentException.class,()->new FrontendGameplayObservation(menu(),SOURCE,actual.gameplaySession(),CONNECTION.add(BigInteger.ONE),
                "entry-data/v1",entryValues(),semantic(actor),root(actor),actual.supportingEvidence()));
        assertThrows(IllegalArgumentException.class,()->new FrontendGameplayObservation(menu(),SOURCE,actual.gameplaySession(),CONNECTION,
                "entry-data/v1",entryValues(),semantic(actor),root(BigInteger.TEN),actual.supportingEvidence()));
        var otherSource=new G2Source(MACHINE,NOW.toString(),"1.20.0.4",ref("foreign-source",'7'));
        assertThrows(IllegalArgumentException.class,()->new FrontendGameplayObservation(menu(),otherSource,actual.gameplaySession(),CONNECTION,
                "entry-data/v1",entryValues(),semantic(actor),root(actor),actual.supportingEvidence()));
        var snapshot=new FrontendIdentity(MACHINE,GAME,"frontend-1",CONNECTION,GAME.pid(),new FrontendFrame.Snapshot("frontend:2",BigInteger.TWO,BigInteger.TWO,100,BigInteger.ONE),BEFORE,HELLO);
        assertThrows(IllegalArgumentException.class,()->new FrontendGameplayObservation(snapshot,SOURCE,actual.gameplaySession(),CONNECTION,
                "entry-data/v1",entryValues(),semantic(actor),root(actor),actual.supportingEvidence()));
    }
}
