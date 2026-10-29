package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Native primitive spellings and pure original EXECUTE parsers. Parsing grants no read/action authority. */
public final class ArmySteps {
    private ArmySteps() { }
    private static final String CONTROL="query-battle-control-snapshot-v1-",TRANSITION="query-battle-transition-v1-",
            TERMINAL="query-battle-terminal-transition-v1-",REINFORCEMENT="query-battle-reinforcement-assignment-v1-",
            PHASE="query-combat-phase-event-trace-v1-";
    private static final Pattern TERMINAL_PARTS=Pattern.compile("(-?(?:0|[1-9][0-9]*))-(0|[1-9][0-9]*)-(0|[1-9][0-9]*)");
    public static String terminal(ArmyRequests.Terminal request) {
        String step = "query-battle-terminal-transition-v1-";
        if (request.priorCombat().isEmpty()) step += "none";
        else step += request.priorCombat().orElseThrow().value() + "-" + request.subject().orElseThrow().value() + "-" + request.afterSequence().map(UInt64::decimal).orElse("0");
        if (!request.characters().isEmpty()) step += ":characters:" + request.characters().stream().map(id -> Integer.toString(id.value())).collect(Collectors.joining(","));
        return step;
    }
    public static String commander(ArmyRequests.Commander request) { return "query-army-commander-candidates-v1-for-army-" + request.army().value() + request.target().map(id -> "-at-province-" + id.value()).orElse(""); }
    public static String combat(ArmyRequests.CombatInputs request, boolean version3) {
        return "query-combat-simulation-inputs-v" + (version3 ? "3" : "2") + "-" + request.target().value() + "-" + request.attackerEntry().map(id -> Integer.toString(id.value())).orElse("ctor0") + "-a-" + request.attackers().size() + "-" + request.attackers().stream().map(id -> Integer.toString(id.value())).collect(Collectors.joining("-")) + "-d-" + request.defenders().size() + "-" + request.defenders().stream().map(id -> Integer.toString(id.value())).collect(Collectors.joining("-"));
    }
    public static String warEntry(ArmyRequests.WarEntry request) { return "query-war-entry-assessments-v1-1-" + request.targets().get(0).value(); }

    /** The seven original Driver READ branches; invalid/reserved labels do not match. */
    public static Optional<ArmyCalls.Call> parseCombatRead(OperationKey original,ArmyCalls.Revision revision) {
        java.util.Objects.requireNonNull(original);java.util.Objects.requireNonNull(revision);String step=original.value();
        try {
            if(step.startsWith(CONTROL))return Optional.of(new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,revision,new PublicUnitId(decimal(step.substring(CONTROL.length()),false))));
            if(step.startsWith(TRANSITION))return Optional.of(new ArmyCalls.CombatId(PublicMethod.QUERY_BATTLE_TRANSITION_V1,revision,new FullId(signed(step.substring(TRANSITION.length())))));
            if(step.startsWith(TERMINAL))return Optional.of(parseTerminal(step.substring(TERMINAL.length()),revision));
            if(step.startsWith(REINFORCEMENT))return Optional.of(new ArmyCalls.Unit(PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,revision,new PublicUnitId(decimal(step.substring(REINFORCEMENT.length()),false))));
            if(step.startsWith(PHASE))return Optional.of(new ArmyCalls.CombatId(PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,revision,new FullId(decimal(step.substring(PHASE.length()),true))));
            Optional<CombatRequest> v2=CombatRequest.parseStep(step);
            if(v2.isPresent())return Optional.of(combatCall(PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,revision,v2.orElseThrow()));
            return CombatPhaseInputsCodec.parseStep(step).map(request->combatCall(PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,revision,request));
        }catch(IllegalArgumentException invalid){return Optional.empty();}
    }
    private static ArmyCalls.Combat combatCall(PublicMethod method,ArmyCalls.Revision revision,CombatRequest request){
        Field<Integer> constructor=request.constructorAdjacencyKindRaw()==null?new Missing<>():new Present<>(request.constructorAdjacencyKindRaw());
        return new ArmyCalls.Combat(method,revision,request,constructor);
    }
    private static ArmyCalls.Terminal parseTerminal(String suffix,ArmyCalls.Revision revision){
        String wire=suffix;Field<List<PositiveId>> characters=new Missing<>();
        int marker=suffix.indexOf(":characters:");
        if(marker>=0){
            wire=suffix.substring(0,marker);String tail=suffix.substring(marker+12);var ids=new LinkedHashSet<PositiveId>();
            for(String part:tail.split(",",-1))ids.add(new PositiveId(decimal(part,true)));
            characters=new Present<>(List.copyOf(ids));
        }
        if(wire.equals("none"))return new ArmyCalls.Terminal(revision,new NullValue<>(),new NullValue<>(),new Missing<>(),characters);
        var match=TERMINAL_PARTS.matcher(wire);if(!match.matches())throw new IllegalArgumentException("original terminal query literal required");
        int combat=signed(match.group(1)),subject=decimal(match.group(2),false);BigInteger cursor=new BigInteger(match.group(3));
        UInt64 parsed=new UInt64(cursor);Field<UInt64> after=cursor.signum()==0?new Missing<>():new Present<>(parsed);
        return new ArmyCalls.Terminal(revision,new Present<>(new FullId(combat)),new Present<>(new PublicUnitId(subject)),after,characters);
    }
    /** Strict semantic equivalence for an explicitly retained terminal request literal, never an alias. */
    public static void requireTerminalLiteral(OperationKey original,ArmyRequests.Terminal expected){
        ArmyCalls.Call parsed=parseCombatRead(original,new ArmyCalls.Revision(new Missing<>())).orElseThrow(()->new IllegalArgumentException("malformed original terminal literal"));
        if(!(parsed instanceof ArmyCalls.Terminal terminal))throw new IllegalArgumentException("original literal is not terminal");
        Optional<FullId> combat=terminal.combat() instanceof Present<FullId> p?Optional.of(p.value()):Optional.empty();
        Optional<PublicUnitId> subject=terminal.subject() instanceof Present<PublicUnitId> p?Optional.of(p.value()):Optional.empty();
        Optional<UInt64> after=terminal.afterSequence() instanceof Present<UInt64> p?Optional.of(p.value()):Optional.empty();
        ArmyRequests.Terminal actual=new ArmyRequests.Terminal(combat,subject,after,terminal.effectiveCharacters().stream().map(id->new FullId(id.value())).toList());
        if(!actual.equals(expected))throw new IllegalArgumentException("original terminal literal changed its typed selection");
    }
    private static int decimal(String text,boolean positive){
        if(!text.matches(positive?"[1-9][0-9]*":"0|[1-9][0-9]*"))throw new IllegalArgumentException("canonical ASCII decimal required");
        return Integer.parseInt(text);
    }
    private static int signed(String text){int value=Integer.parseInt(text);if(!Integer.toString(value).equals(text)||value==-1)throw new IllegalArgumentException("complete signed32 component required");return value;}
}
