package org.xar.ck3.control.contracts;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** One lifecycle observation domain for the application loop and the held Windows producer. */
public final class GameLifecycle {
    private GameLifecycle() { }
    public enum TerminalKind { NATURAL_EXIT, OWNER_STOP, DEADLINE, SOURCE_GUARD, UNKNOWN }
    public sealed interface Observation permits Running, Exited, Unavailable { ExactRef evidence(); }
    public record Running(GameGeneration measured, ExactRef evidence) implements Observation {
        public Running { Objects.requireNonNull(measured); Objects.requireNonNull(evidence);StrictJson.require(evidence.bytes()>0,"actual lifecycle evidence required"); }
    }
    public record Exited(GameGeneration measured, int exitCode, boolean timedOut,
            TerminalKind terminal, ExactRef evidence) implements Observation {
        public Exited {
            Objects.requireNonNull(measured); Objects.requireNonNull(terminal); Objects.requireNonNull(evidence);
            StrictJson.require(evidence.bytes()>0,"actual terminal evidence required");
            StrictJson.require(terminal!=TerminalKind.UNKNOWN,"unresolved lifecycle state must remain unavailable");
            StrictJson.require(timedOut==(terminal==TerminalKind.DEADLINE),"timeout must agree with the actual deadline terminal");
        }
    }
    public record Unavailable(String reason, ExactRef evidence) implements Observation {
        public Unavailable { StrictJson.text(reason); Objects.requireNonNull(evidence);StrictJson.require(evidence.bytes()>0,"actual failure evidence required"); }
    }
    @FunctionalInterface public interface Port {
        Observation inspect(GameGeneration expected, Instant deadline) throws IOException;
    }
    /** Explicit JSON domain: GameGeneration preserves canonical decimal-string FILETIME identity. */
    public static ObjectNode toJson(Observation value){
        ObjectNode row=StrictJson.object();row.put("schema","xar.java-game-lifecycle-observation/v1");
        row.set("evidence",value.evidence().toJson());
        if(value instanceof Running running){row.put("state","running");row.set("measured",running.measured().toJson());}
        else if(value instanceof Exited exited){row.put("state","exited");row.set("measured",exited.measured().toJson());row.put("exit_code",exited.exitCode());row.put("timed_out",exited.timedOut());row.put("terminal",exited.terminal().name());}
        else if(value instanceof Unavailable unavailable){row.put("state","unavailable");row.put("reason",unavailable.reason());}
        return row;
    }
    public static Observation fromJson(JsonNode value){
        StrictJson.require(value!=null&&value.isObject(),"lifecycle observation object required");
        StrictJson.require("xar.java-game-lifecycle-observation/v1".equals(StrictJson.text(value.get("schema"))),"exact lifecycle schema required");
        String state=StrictJson.text(value.get("state"));
        if(state.equals("running")){
            ObjectNode row=StrictJson.object(value,Set.of("schema","state","measured","evidence"));return new Running(GameGeneration.fromJson(row.get("measured")),ExactRef.fromJson(row.get("evidence")));
        }
        if(state.equals("exited")){
            ObjectNode row=StrictJson.object(value,Set.of("schema","state","measured","exit_code","timed_out","terminal","evidence"));
            StrictJson.require(row.get("timed_out").isBoolean(),"explicit timeout boolean required");
            return new Exited(GameGeneration.fromJson(row.get("measured")),(int)StrictJson.integer(row.get("exit_code"),Integer.MIN_VALUE,Integer.MAX_VALUE),row.get("timed_out").booleanValue(),TerminalKind.valueOf(StrictJson.text(row.get("terminal"))),ExactRef.fromJson(row.get("evidence")));
        }
        StrictJson.require(state.equals("unavailable"),"known lifecycle state required");
        ObjectNode row=StrictJson.object(value,Set.of("schema","state","reason","evidence"));return new Unavailable(StrictJson.text(row.get("reason")),ExactRef.fromJson(row.get("evidence")));
    }
}
