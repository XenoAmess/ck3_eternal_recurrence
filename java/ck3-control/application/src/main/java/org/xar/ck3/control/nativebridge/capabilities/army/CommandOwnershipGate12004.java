package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Original37EBC20 ownership branch. No queued, executed, or Game result is represented. */
public final class CommandOwnershipGate12004 {
    public static final int CALL_RVA=0x1A188BE, GATE_RVA=0x37EBC39, HANDOFF_RVA=0x37EBC59;
    public static final int MANAGER_RVA=0x5CC1240, FLAG_RVA=0x5CC14D0;
    private CommandOwnershipGate12004() { }
    public sealed interface Stage permits Cleanup, Handoff { }
    public record Cleanup() implements Stage { }
    public record Handoff(UInt64 managerIdentity, UInt64 localOwnedSlotIdentity, int forwardedArgumentRaw) implements Stage {
        public Handoff { positive(managerIdentity); positive(localOwnedSlotIdentity); }
    }
    public record Facts(OriginalCommandEnvelope12004.Facts originalCommand, int flagByteRaw,
                        UInt64 inputSlotIdentity, UInt64 clonedCommandPointerRaw, Stage stage) {
        public Facts {
            Objects.requireNonNull(originalCommand); positive(inputSlotIdentity);
            Objects.requireNonNull(clonedCommandPointerRaw); Objects.requireNonNull(stage);
            if (flagByteRaw<0 || flagByteRaw>255 || inputSlotIdentity.value().add(BigInteger.valueOf(7)).bitLength()>64)
                throw new IllegalArgumentException("raw byte and owned qword span");
            if (((flagByteRaw&0xFD)!=0)!=(stage instanceof Cleanup))
                throw new IllegalArgumentException("actual maskFD branch required");
            if (stage instanceof Handoff h) {
                BigInteger manager=originalCommand.call().moduleBaseIdentity().value().add(BigInteger.valueOf(MANAGER_RVA));
                if (!manager.equals(h.managerIdentity().value()) || manager.bitLength()>64
                        || !inputSlotIdentity.value().subtract(BigInteger.valueOf(0x30)).equals(h.localOwnedSlotIdentity().value())
                        || h.forwardedArgumentRaw()!=originalCommand.wrapperArgumentRaw())
                    throw new IllegalArgumentException("original manager, stack slots and distinct wrapper argument");
            }
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.originalCommand().scope(); }
    }
    public record Incomplete(Scope scope,String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic");
        }
    }
    public sealed interface Result permits ObservedOwnership, NotReady { }
    public record ObservedOwnership(Facts facts) implements Result { public ObservedOwnership {Objects.requireNonNull(facts);} }
    public record NotReady(String reason) implements Result { public NotReady {Objects.requireNonNull(reason);} }
    public static Result consume(Scope current, OriginalCommandEnvelope12004.CallKey currentOriginalCall, Observation read) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentOriginalCall); Objects.requireNonNull(read);
        if (!current.equals(read.scope())) return new NotReady("ownership_update_or_source_changed");
        if (read instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts f=((Available)read).facts();
        if (!currentOriginalCall.equals(f.originalCommand().call())) return new NotReady("ownership_original_occurrence_changed");
        return new ObservedOwnership(f);
    }
    public static Observation decode(byte[] wire) {
        ObjectNode n=closed(parse(wire),"schema_version","call_rva","gate_rva","handoff_rva","scope","status","reason","facts");
        if (i32(n.get("schema_version"))!=1 || i32(n.get("call_rva"))!=CALL_RVA || i32(n.get("gate_rva"))!=GATE_RVA
                || i32(n.get("handoff_rva"))!=HANDOFF_RVA) throw new IllegalArgumentException("exact ownership contract");
        Scope scope=LocalTargetScore12004.scope(n.get("scope")); String status=text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts null");
            return new Incomplete(scope,text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("ownership discriminant");
        ObjectNode f=closed(n.get("facts"),"original_command","flag_byte_raw","input_slot_identity","cloned_command_pointer_raw","stage");
        OriginalCommandEnvelope12004.Observation original=OriginalCommandEnvelope12004.decode(bytes(f.get("original_command")));
        if (!(original instanceof OriginalCommandEnvelope12004.Available a) || !scope.equals(original.scope()))
            throw new IllegalArgumentException("same-scope original command required");
        ObjectNode s=object(f.get("stage")); Stage stage;
        if (text(s.get("kind")).equals("cleanup")) {closed(s,"kind"); stage=new Cleanup();}
        else {
            closed(s,"kind","manager_identity","local_owned_slot_identity","forwarded_argument_raw");
            if (!text(s.get("kind")).equals("handoff")) throw new IllegalArgumentException("ownership stage");
            stage=new Handoff(address(s.get("manager_identity")),address(s.get("local_owned_slot_identity")),i32(s.get("forwarded_argument_raw")));
        }
        return new Available(new Facts(a.facts(),i32(f.get("flag_byte_raw")),address(f.get("input_slot_identity")),
                decimalPointer(text(f.get("cloned_command_pointer_raw"))),stage));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation); ObjectNode n=empty();n.put("schema_version",1);n.put("call_rva",CALL_RVA);
        n.put("gate_rva",GATE_RVA);n.put("handoff_rva",HANDOFF_RVA);n.set("scope",LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {n.put("status","incomplete");n.put("reason",missing.reason());n.putNull("facts");return bytes(n);}
        Facts f=((Available)observation).facts();n.put("status","available");n.putNull("reason");ObjectNode out=n.putObject("facts");
        out.set("original_command",parse(OriginalCommandEnvelope12004.encode(new OriginalCommandEnvelope12004.Available(f.originalCommand()))));
        out.put("flag_byte_raw",f.flagByteRaw());out.put("input_slot_identity",f.inputSlotIdentity().decimal());
        out.put("cloned_command_pointer_raw",f.clonedCommandPointerRaw().decimal());ObjectNode s=out.putObject("stage");
        if (f.stage() instanceof Cleanup) s.put("kind","cleanup");
        else {Handoff h=(Handoff)f.stage();s.put("kind","handoff");s.put("manager_identity",h.managerIdentity().decimal());
            s.put("local_owned_slot_identity",h.localOwnedSlotIdentity().decimal());s.put("forwarded_argument_raw",h.forwardedArgumentRaw());}
        return bytes(n);
    }
    private static UInt64 address(com.fasterxml.jackson.databind.JsonNode n) {UInt64 p=decimalPointer(text(n));positive(p);return p;}
    private static UInt64 decimalPointer(String s) {
        if (!s.matches("0|[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical uint64 pointer string");
        return new UInt64(new BigInteger(s));
    }
    private static void positive(UInt64 p) {Objects.requireNonNull(p);if(p.value().signum()<=0)throw new IllegalArgumentException("positive pointer");}
}
