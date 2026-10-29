package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

final class GameLifecycleSerdeTest {
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134372284757522641")));
    private static final ExactRef PROOF=new ExactRef("software-proof.json",12,"0".repeat(64));
    @Test void producerAllBranchesRoundTripThroughExactSharedConsumer(){
        for(GameLifecycle.Observation value:List.of(new GameLifecycle.Running(GAME,PROOF),new GameLifecycle.Exited(GAME,259,false,GameLifecycle.TerminalKind.NATURAL_EXIT,PROOF),new GameLifecycle.Exited(GAME,125,false,GameLifecycle.TerminalKind.OWNER_STOP,PROOF),new GameLifecycle.Exited(GAME,125,true,GameLifecycle.TerminalKind.DEADLINE,PROOF),new GameLifecycle.Exited(GAME,125,false,GameLifecycle.TerminalKind.SOURCE_GUARD,PROOF),new GameLifecycle.Unavailable("actual-source-drift",PROOF)))
            assertEquals(value,GameLifecycle.fromJson(GameLifecycle.toJson(value)));
        assertEquals("134372284757522641",GameLifecycle.toJson(new GameLifecycle.Running(GAME,PROOF)).path("measured").path("creation_filetime").textValue());
    }
    @Test void wrongFieldsNullFloatAndUnknownEnumDoNotCoerce(){
        var row=GameLifecycle.toJson(new GameLifecycle.Exited(GAME,259,false,GameLifecycle.TerminalKind.NATURAL_EXIT,PROOF));
        var wrong=row.deepCopy();wrong.put("exit_code",259.0);assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(wrong));
        var missing=row.deepCopy();missing.remove("timed_out");assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(missing));
        var bool=row.deepCopy();bool.put("timed_out",1);assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(bool));
        var unknown=row.deepCopy();unknown.put("terminal","PASSED_FROM_ACK");assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(unknown));
        var extra=row.deepCopy();extra.put("native_grant",true);assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(extra));
    }
    @Test void persistedUnknownAndContradictoryTimeoutCannotBecomeKnownExit(){
        var actual=GameLifecycle.toJson(new GameLifecycle.Exited(GAME,259,false,GameLifecycle.TerminalKind.NATURAL_EXIT,PROOF));
        var unresolved=actual.deepCopy();unresolved.put("terminal","UNKNOWN");
        assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(unresolved));
        var falseTimeout=actual.deepCopy();falseTimeout.put("timed_out",true);
        assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(falseTimeout));
        var missingTimeout=actual.deepCopy();missingTimeout.put("terminal","DEADLINE");
        assertThrows(IllegalArgumentException.class,()->GameLifecycle.fromJson(missingTimeout));
        assertThrows(IllegalArgumentException.class,()->new GameLifecycle.Exited(GAME,0,false,GameLifecycle.TerminalKind.UNKNOWN,PROOF));
        assertThrows(IllegalArgumentException.class,()->new GameLifecycle.Exited(GAME,0,false,GameLifecycle.TerminalKind.DEADLINE,PROOF));
    }
}
