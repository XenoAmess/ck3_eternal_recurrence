package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** One process-local gate per actual Strengths runtime. A certificate grants no action or Native admission. */
public final class ArmyPrivateScalarControl {
    public static final String CAPABILITY="game.command.query-army-strengths-private-auto-scalar-v1";
    public enum Mode { OFF, COMPARE, USE; public String wire(){return name().toLowerCase(java.util.Locale.ROOT);} }
    @FunctionalInterface public interface Qualification { ExactRef verify(ArmyStrengthsService.CurrentFrame actual)throws IOException; }
    @FunctionalInterface public interface OptionalQualification { Optional<ExactRef> verify(ArmyStrengthsService.CurrentFrame actual)throws IOException; }
    private record Identity(String machine,org.xar.ck3.control.contracts.GameGeneration game,String session,
            long pid,BigInteger generation,int actor,String episode,String adapter,Optional<String> build) { }
    public record State(Mode mode,boolean comparisonVerified,boolean nativeCapabilityAdvertised,ArmyStrengths.Binding source) {
        public State { Objects.requireNonNull(mode);Objects.requireNonNull(source); }
    }
    private final ArmyStrengthsService.Current current;
    private final OptionalQualification actual;
    private Mode mode=Mode.OFF;
    private Identity armed;
    private Identity certificate;
    public ArmyPrivateScalarControl(ArmyStrengthsService.Current sameCurrent,Qualification actualQualification){
        this(before->Optional.of(Objects.requireNonNull(actualQualification).verify(before)),sameCurrent);
    }
    private ArmyPrivateScalarControl(OptionalQualification qualification,ArmyStrengthsService.Current sameCurrent){current=Objects.requireNonNull(sameCurrent);actual=Objects.requireNonNull(qualification);}
    public static ArmyPrivateScalarControl ordinary(ArmyStrengthsService.Current current,OptionalQualification qualification){return new ArmyPrivateScalarControl(qualification,current);}
    public ArmyStrengthsService.Current current(){return current;}
    public synchronized State set(Mode requested,BigInteger expectedRevision)throws IOException {
        Objects.requireNonNull(requested);var frame=frame(expectedRevision);var identity=identity(frame);
        require(requested==Mode.OFF||capable(frame),"native private Army scalar capability is unavailable");
        require(requested!=Mode.USE||identity.equals(certificate)&&identity.equals(armed),"same-identity rich/private comparison is required before use");
        mode=requested;if(requested!=Mode.USE){certificate=null;armed=requested==Mode.COMPARE?identity:null;}
        return state(frame,identity);
    }
    public synchronized State query(BigInteger expectedRevision)throws IOException {var frame=frame(expectedRevision);selectedMode(frame);return state(frame,identity(frame));}
    public synchronized Mode selectedMode(ArmyStrengthsService.CurrentFrame before){
        Objects.requireNonNull(before);if(mode==Mode.OFF)return mode;
        Identity now;try{now=identity(before);}catch(RuntimeException invalid){disable();throw invalid;}
        if(!capable(before)||!now.equals(armed)||mode==Mode.USE&&!now.equals(certificate))disable();
        return mode;
    }
    /** The callback validates actual frame custody; returned software provenance is optional DATA. */
    public synchronized Optional<ExactRef> qualification(ArmyStrengthsService.CurrentFrame before)throws IOException {
        require(selectedMode(before)!=Mode.OFF&&capable(before),"private scalar gate is not armed for the current identity");
        return Objects.requireNonNull(actual.verify(before));
    }
    /** Compare only original semantic rows/status and exact frame/scope. Query sequence/timing are separate receipts. */
    public synchronized void markCompared(ArmyStrengthsService.CurrentFrame before,ArmyStrengthsService.Reply rich,ArmyStrengthsService.Reply scalar){
        try {
            require(selectedMode(before)==Mode.COMPARE,"private scalar comparison is not armed");
            var expected=before.snapshot();
            require(rich.selection().query().mode()==ArmyStrengths.Mode.AUTO_CORE&&scalar.selection().query().mode()==ArmyStrengths.Mode.PRIVATE_AUTO_SCALAR,
                    "comparison requires actual rich AUTO and qualified private AUTO results");
            require(rich.selection().snapshot().binding().equals(expected.binding())&&scalar.selection().snapshot().binding().equals(expected.binding())
                    &&rich.selection().snapshot().scope().equals(expected.scope())&&scalar.selection().snapshot().scope().equals(expected.scope()),"rich/private comparison crossed its original frame/scope");
            require(rich.status()==scalar.status()&&rich.scopeStatus()==scalar.scopeStatus()&&rich.selected().equals(scalar.selected()),"private scalar result differs from actual rich rows/status");
            require(!rich.original().original().equals(scalar.original().original()),"comparison needs two independent actual read receipts");
            certificate=identity(before);
        }catch(RuntimeException mismatch){disable();throw mismatch;}
    }
    public synchronized void disable(){mode=Mode.OFF;armed=null;certificate=null;}
    private ArmyStrengthsService.CurrentFrame frame(BigInteger expected)throws IOException {
        require(expected!=null&&expected.signum()>0&&expected.bitLength()<=64,"positive exact public revision required");
        var frame=Objects.requireNonNull(current.current());require(frame.snapshot().binding().publicRevision().equals(expected),"private scalar source revision changed");identity(frame);return frame;
    }
    private State state(ArmyStrengthsService.CurrentFrame frame,Identity identity){return new State(mode,identity.equals(certificate),capable(frame),frame.snapshot().binding());}
    private static boolean capable(ArmyStrengthsService.CurrentFrame frame){return frame.originalHello().capabilities().contains(CAPABILITY);}
    private static Identity identity(ArmyStrengthsService.CurrentFrame frame){
        var b=frame.snapshot().binding();var hello=frame.originalHello();
        require(b.actorCharacterId()>0&&b.episodeRunId().isPresent()&&!b.episodeRunId().orElseThrow().isBlank()
                &&hello.pid()==b.game().pid()&&hello.connectionGeneration().equals(b.connectionGeneration()),"private scalar current identity is incomplete");
        try {
            var semantic=ArmyJson.parse(frame.snapshot().original().bytes());
            require(semantic.path("paused").isBoolean()&&semantic.path("paused").booleanValue()
                    &&semantic.path("map_ready").isBoolean()&&semantic.path("map_ready").booleanValue(),"private scalar control needs a paused map frame");
            var actor=semantic.path("played_character");require(actor.path("alive").isBoolean()&&actor.path("alive").booleanValue()
                    &&actor.path("character_id").isIntegralNumber()&&actor.path("character_id").intValue()==b.actorCharacterId(),"private scalar player is not the actual living actor");
            byte[] packet=hello.packet().value();var raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)));
            JsonNode build=raw.get("game_build");Optional<String> token=build==null?Optional.empty():Optional.of(ArmyJson.bytes(build).length+":"+new String(ArmyJson.bytes(build),java.nio.charset.StandardCharsets.UTF_8));
            return new Identity(b.machineId(),b.game(),b.sessionId(),hello.pid(),b.connectionGeneration(),b.actorCharacterId(),b.episodeRunId().orElseThrow(),hello.adapterId(),token);
        }catch(IOException invalid){throw new java.io.UncheckedIOException("actual private scalar identity unavailable",invalid);}
    }
}
