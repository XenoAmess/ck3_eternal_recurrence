package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.RootMcpAubOperations;
import org.xar.ck3.control.service.mcp.RootMcpAubReads;

/** Actual original early-failure methods and the exact production prepare guard.
 * The software snapshot/probe is DATA only; it cannot qualify a live Root, Native write or retry. */
final class RootAubPreSubmissionRevisionTest {
    private static final String FIRST="aub_policy_treasury_only_pause_choice";
    private static final String LAST="aub_policy_treasury_first_continue_choice";
    private static final BigInteger ACTUAL=new BigInteger("9007199254740993");
    @TempDir Path temporary;

    @Test void actualOriginalSelectAndConfirmFaultsMatchBeforeQueriesClaimsOrSubmission()throws Exception {
        ObjectNode original=originalFailures();
        for(var row:original.withArray("mismatches")) {
            Mutation mutation=row.get("operation").textValue().equals("select")
                    ?new Select(PolicyKey.TREASURY_PAUSE,PolicyKey.TREASURY_FIRST_CONTINUE):new Confirm(PolicyKey.TREASURY_PAUSE);
            BigInteger expected=new BigInteger(row.get("expected_revision").textValue());
            var fault=assertThrows(RootAubRuntimeFactory.PreSubmissionRevisionMismatch.class,
                    ()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.of(expected),ACTUAL));
            assertEquals("PreSubmissionRevisionMismatchError",row.get("type").textValue());
            assertEquals(row.get("message").textValue(),fault.getMessage());
            assertEquals(mutation,fault.mutation());assertEquals(expected,fault.expectedRevision());assertEquals(ACTUAL,fault.actualRevision());
            assertTrue(row.get("selected_step").isNull());assertTrue(row.get("plan").isNull());assertEquals(0,row.get("replan_count").intValue());
            assertEquals(1,row.get("snapshots").intValue());assertEquals(0,row.get("later_calls").intValue());
        }
        assertEquals(4,original.withArray("mismatches").size());
        for(var row:original.withArray("passes"))assertTrue(row.get("reached_post_revision_boundary").booleanValue());
        assertEquals(4,original.withArray("passes").size());
        for(var row:original.withArray("invalid")){assertEquals("ValueError",row.get("type").textValue());assertEquals(0,row.get("later_calls").intValue());}
        assertEquals(6,original.withArray("invalid").size());
    }
    @Test void actualPublicDecodersKeepMissingNullAndCanonicalWideRevisionThroughJson() {
        var selection=RootMcpAubOperations.selection(arguments(selection("\"9007199254740992\"")));
        var confirmation=RootMcpAubOperations.confirmation(arguments(confirmation("\"18446744073709551615\"")));
        assertEquals(Optional.of(ACTUAL.subtract(BigInteger.ONE)),selection.revision().expected());
        assertEquals(Optional.of(NativeWire.UINT64_MAX),confirmation.revision().expected());
        assertEquals(selection,RootMcpAubOperations.selection(canonicalArguments(selection("\"9007199254740992\""))));
        assertEquals(confirmation,RootMcpAubOperations.confirmation(canonicalArguments(confirmation("\"18446744073709551615\""))));
        var selected=assertThrows(RootAubRuntimeFactory.PreSubmissionRevisionMismatch.class,
                ()->RootAubRuntimeFactory.requireExpectedPublicRevision(selection.mutation(),selection.revision().expected(),ACTUAL));
        var confirmed=assertThrows(RootAubRuntimeFactory.PreSubmissionRevisionMismatch.class,
                ()->RootAubRuntimeFactory.requireExpectedPublicRevision(confirmation.mutation(),confirmation.revision().expected(),ACTUAL));
        assertEquals("AUB select public revision changed",selected.getMessage());assertEquals("AUB Confirm public revision changed",confirmed.getMessage());
        assertInstanceOf(RootMcpAubReads.Missing.class,RootMcpAubOperations.selection(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"desired_key\":\""+LAST+"\"}")).revision());
        assertInstanceOf(RootMcpAubReads.NullValue.class,RootMcpAubOperations.confirmation(canonicalArguments(confirmation("null"))).revision());
    }
    @Test void malformedFieldsAndRevisionTypesRemainInputErrorsWithoutMintingMismatch() {
        for(String value:List.of("true","1.0","-1","9007199254740992","\"01\"","\"+1\"","\"18446744073709551616\"")) {
            assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.selection(arguments(selection(value))));
            assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.confirmation(arguments(confirmation(value))));
        }
        for(String json:List.of("{}","{\"expected_selected_key\":true}","{\"expected_selected_key\":null}","{\"expected_selected_key\":\"unknown\"}","{\"expected_selected_key\":\""+FIRST+"\",\"unknown\":0}"))
            assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.confirmation(arguments(json)));
        assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.selection(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"desired_key\":1}")));
        for(BigInteger invalid:List.of(BigInteger.valueOf(-1),NativeWire.UINT64_MAX.add(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->RootAubRuntimeFactory.requireExpectedPublicRevision(new Confirm(PolicyKey.TREASURY_PAUSE),Optional.of(invalid),ACTUAL));
    }
    @Test void matchingOrAbsentRevisionDoesNotBecomeAnErrorOrSubmitPermission() {
        for(Mutation mutation:List.<Mutation>of(new Select(PolicyKey.TREASURY_PAUSE,PolicyKey.PERSONAL_PAUSE),new Confirm(PolicyKey.TREASURY_PAUSE))) {
            assertDoesNotThrow(()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.empty(),ACTUAL));
            assertDoesNotThrow(()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.of(ACTUAL),ACTUAL));
        }
    }
    private static String selection(String revision){return "{\"expected_selected_key\":\""+FIRST+"\",\"desired_key\":\""+LAST+"\",\"expected_revision\":"+revision+"}";}
    private static String confirmation(String revision){return "{\"expected_selected_key\":\""+FIRST+"\",\"expected_revision\":"+revision+"}";}
    private static PublicMcpDirectory.Arguments arguments(String json){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8))));}
    private static PublicMcpDirectory.Arguments canonicalArguments(String json){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(StrictJson.canonical(StrictJson.parse(json.getBytes(StandardCharsets.UTF_8))))));}

    private ObjectNode originalFailures()throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python missing; original producer differential cannot skip");assertFalse(python.isBlank());
        assertNotNull(repository,"required xar.repository.root missing; original producer differential cannot skip");assertFalse(repository.isBlank());
        Path root=Path.of(repository).toRealPath();
        String script="""
            import json
            from copy import deepcopy
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError
            from xar_autoplayer.bridge.aub_policy_options_contract import SELECT_CAPABILITY,QUERY_CAPABILITY,POLICY_KEYS
            from xar_autoplayer.bridge.aub_business_state_contract import CONFIRM_CAPABILITY,QUERY_CAPABILITY as BUSINESS_QUERY
            from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256
            actual=9007199254740993
            snapshot=dict(revision=actual,native_revision=17,date_raw=1234,paused=True,map_ready=True,
                played_character=dict(character_id=31254,alive=True),active_event=None,pending_character_interaction=None,
                episode_run_id='source-only-aub-episode',diagnostics=dict(connection_generation=3,hello=dict(
                pid=4242,expected_ck3_version='1.20.0.3',expected_ck3_sha256=EXE_SHA256,ck3_build_match=True,game_adapter_id='ck3-1.20.0.3-msvc-x64')))
            class PastRevision(Exception):pass
            class Probe:
                def __init__(self):self.snapshots=0;self.later_calls=0
                def capabilities(self):return dict(bridge_capabilities=[SELECT_CAPABILITY,QUERY_CAPABILITY,CONFIRM_CAPABILITY,BUSINESS_QUERY])
                def take_snapshot(self):self.snapshots+=1;return deepcopy(snapshot)
                def __getattr__(self,name):
                    self.later_calls+=1
                    raise PastRevision(name)
            def invoke(operation,probe,expected):
                if operation=='select':return NativeHeadlessGameplayDriver.select_aub_policy_option_v1(probe,POLICY_KEYS[0],POLICY_KEYS[-1],expected_revision=expected)
                return NativeHeadlessGameplayDriver.confirm_aub_policy_v1(probe,POLICY_KEYS[0],expected_revision=expected)
            result=dict(mismatches=[],passes=[],invalid=[])
            for operation in ('select','confirm'):
                for expected in (actual-1,actual+1):
                    probe=Probe()
                    try:invoke(operation,probe,expected)
                    except PreSubmissionRevisionMismatchError as error:
                        result['mismatches'].append(dict(operation=operation,expected_revision=str(expected),type=type(error).__name__,message=str(error),
                            selected_step=error.selected_step,plan=error.plan,replan_count=error.replan_count,snapshots=probe.snapshots,later_calls=probe.later_calls))
                    else:raise AssertionError('original mismatch branch did not reject')
                for expected in (None,actual):
                    probe=Probe()
                    try:invoke(operation,probe,expected)
                    except PastRevision:result['passes'].append(dict(operation=operation,reached_post_revision_boundary=True))
                    else:raise AssertionError('original matched/absent revision did not reach its following branch')
                for expected in (True,1.0,-1):
                    probe=Probe()
                    try:invoke(operation,probe,expected)
                    except ValueError as error:result['invalid'].append(dict(operation=operation,type=type(error).__name__,later_calls=probe.later_calls))
                    else:raise AssertionError('original invalid revision was accepted')
            print(json.dumps(result,ensure_ascii=True,separators=(',',':')))
            """;
        var builder=new ProcessBuilder(python,"-X","utf8","-c",script).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        builder.environment().put("XAR_AUTOPLAYER_STATE_DIR",temporary.resolve("original-state").toAbsolutePath().toString());
        var child=builder.start();
        var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readAllBytes();}catch(IOException failure){throw new UncheckedIOException(failure);}});
        boolean ended=child.waitFor(45,TimeUnit.SECONDS);if(!ended)child.destroyForcibly();assertTrue(ended,"original AUB failure producer timed out");
        byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        return (ObjectNode)DriverJson.toNode(DriverJson.object(bytes,1<<20));
    }
}
