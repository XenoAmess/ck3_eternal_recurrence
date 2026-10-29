package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.junit.jupiter.api.Assertions.*;

/** Runs the retained original terminal encoder, then the actual ordinary dispatcher selection parser. */
final class MilitaryTerminalReadSelectionOriginalTest {
    @Test void originalTerminalSelectionKeepsCharacterOnlyAndZeroCursorSemantics()throws Exception {
        String python=System.getProperty("xar.python"),root=System.getProperty("xar.repository.root");
        assertNotNull(python,"actual retained Python producer is mandatory");assertNotNull(root,"actual source repository is mandatory");
        String script="import json,sys;sys.path.insert(0,sys.argv[1]);from xar_autoplayer.bridge.battle_terminal_transition_contract import query_battle_terminal_transition_v1_step as s;print(json.dumps([s(-2147483648,0,None,[1,2]),s(0,0,18446744073709551615,[2]),s(None,None,None,[3])]))";
        var process=new ProcessBuilder(python,"-c",script,Path.of(root,"ck3_autonomous_player","src").toString()).redirectErrorStream(true).start();
        assertTrue(process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS),"original terminal producer timed out");
        byte[] bytes=process.getInputStream().readAllBytes();assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        var rows=StrictJson.parse(bytes);assertTrue(rows.isArray());assertEquals(3,rows.size());
        var revision=new ArmyCalls.Revision(new Present<>(BigInteger.ONE));
        var first=MilitaryNativeReadDispatcher.terminal(rows.get(0).textValue(),revision).orElseThrow();
        assertEquals(new Present<>(new FullId(Integer.MIN_VALUE)),first.combat());assertEquals(new Present<>(new PublicUnitId(0)),first.subject());
        assertInstanceOf(Missing.class,first.afterSequence());assertEquals(List.of(new PositiveId(1),new PositiveId(2)),first.effectiveCharacters());
        var second=MilitaryNativeReadDispatcher.terminal(rows.get(1).textValue(),revision).orElseThrow();
        assertEquals(new Present<>(new UInt64(new BigInteger("18446744073709551615"))),second.afterSequence());
        var third=MilitaryNativeReadDispatcher.terminal(rows.get(2).textValue(),revision).orElseThrow();
        assertInstanceOf(NullValue.class,third.combat());assertInstanceOf(NullValue.class,third.subject());assertInstanceOf(Missing.class,third.afterSequence());
        for(String invalid:List.of("none","none:characters:0","0-0-0:characters:1,1","-0-0-0","0-0-00","0-0-0:characters:1:characters:2"))
            assertTrue(MilitaryNativeReadDispatcher.terminal("query-battle-terminal-transition-v1-"+invalid,revision).isEmpty(),invalid);
        assertThrows(IllegalArgumentException.class,()->MilitaryNativeReadDispatcher.terminal("query-battle-terminal-transition-v1--1-0-0",revision));
    }
}
