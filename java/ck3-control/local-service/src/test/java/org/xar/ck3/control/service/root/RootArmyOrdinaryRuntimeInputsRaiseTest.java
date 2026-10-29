package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.junit.jupiter.api.Assertions.*;

/** Retained native raise producer -> shared strict decoder -> concrete factory's final gate. No writer/Game authority. */
final class RootArmyOrdinaryRuntimeInputsRaiseTest {
    private static final String SHA="c5e6ab6e78efcc705ab555f2f23f2e4741d484aba14667742caf7058e58bbdb3";
    private static final BigInteger ACTOR=BigInteger.valueOf(29829);
    private static ObjectNode fixture()throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"NOT_RUN: original repository property required");
        byte[] original=Files.readAllBytes(Path.of(repository,"ck3_autonomous_player/native_bridge/research/fixtures/ck3_12003_player_default_raise_reserve_v1.json"));
        assertEquals(SHA,ActionCodec.sha256(original),"native producer fixture bytes changed");
        return (ObjectNode)StrictJson.parse(original);
    }
    private static ArmyTypes.Context context() {
        var t=Instant.parse("2026-10-23T22:50:00Z");var ref=new ExactRef("software-raise-gate-no-native-qualification",1,"a".repeat(64));
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186",t.toString(),"1.20.0.3",ref);
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(ACTOR,BigInteger.valueOf(11),BigInteger.valueOf(53238336)),"native:11",BigInteger.valueOf(7),"software-raise-gate"),1);
        return new ArmyTypes.Context(before,source,"software-raise-gate-session",t.plusSeconds(30));
    }
    private static ArmyCalls.Frame input() {return new ArmyCalls.Frame(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.valueOf(7))));}
    private static ArmyClosedReads.Observation decode(ObjectNode original) {return ArmyClosedReadCodec.decodeToken(input(),context(),StrictJson.canonical(original));}
    @Test void actualPositiveReserveDoesNotOverrideActualNativeIllegality()throws Exception {
        var original=(ObjectNode)fixture().get("positive");
        var quote=assertInstanceOf(ArmyClosedReads.DefaultRaise.class,decode(original));
        assertEquals(new ArmyTypes.Present<>(1373),quote.soldiers());assertEquals(new ArmyTypes.Present<>(false),quote.legal());
        assertThrows(IllegalArgumentException.class,()->RootArmyOrdinaryRuntimeInputs.requireDefaultRaise(ACTOR,quote));
    }
    @Test void explicitlySyntheticLegalVariantUsesTheSameGateAndSurvivesPublicJsonRoundtrip()throws Exception {
        var original=((ObjectNode)fixture().get("positive")).deepCopy();((ObjectNode)original.get("player_default_raise")).put("native_default_raise_legal",true);
        var quote=decode(original);assertDoesNotThrow(()->RootArmyOrdinaryRuntimeInputs.requireDefaultRaise(ACTOR,quote));
        var encoded=ArmyClosedReadCodec.encode(quote,context());var restored=ArmyClosedReadCodec.decodePublic(input(),context(),encoded);
        assertEquals(quote,restored);assertDoesNotThrow(()->RootArmyOrdinaryRuntimeInputs.requireDefaultRaise(ACTOR,restored));
        assertThrows(IllegalArgumentException.class,()->RootArmyOrdinaryRuntimeInputs.requireDefaultRaise(ACTOR.add(BigInteger.ONE),restored));
    }
    @Test void zeroReserveAndWrongNativeBooleanOrMissingQuoteFieldCannotQualify()throws Exception {
        var original=((ObjectNode)fixture().get("zero")).deepCopy();((ObjectNode)original.get("player_default_raise")).put("native_default_raise_legal",true);
        var zero=decode(original);assertThrows(IllegalArgumentException.class,()->RootArmyOrdinaryRuntimeInputs.requireDefaultRaise(ACTOR,zero));
        var wrong=original.deepCopy();((ObjectNode)wrong.get("player_default_raise")).put("native_default_raise_legal",1);
        assertThrows(IllegalArgumentException.class,()->decode(wrong));
        var missing=original.deepCopy();((ObjectNode)missing.get("player_default_raise")).remove("unraised_troops_ready");
        assertThrows(IllegalArgumentException.class,()->decode(missing));
    }
}
