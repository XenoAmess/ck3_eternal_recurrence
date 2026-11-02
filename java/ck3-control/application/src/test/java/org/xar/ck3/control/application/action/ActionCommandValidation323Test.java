package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic immutable DATA only: no Original, Root, writer, issuer or Native authority. */
public final class ActionCommandValidation323Test {
    private static final String MACHINE="command-fixture323";
    private static final Instant NOW=Instant.parse("2026-11-02T00:00:00Z");
    private static final G2Source SOURCE=new G2Source(MACHINE,NOW.toString(),"fixture-build323",
            new ExactRef("fixture-only/source323",1L,"0".repeat(64)));
    private static final ProposalLifecycle.ObservationIdentity BEFORE=new ProposalLifecycle.ObservationIdentity(
            MACHINE,new GameGeneration(323L,new PythonOnlyUInt64(BigInteger.ONE)),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                    BigInteger.TWO,BigInteger.valueOf(100)),"snapshot323",BigInteger.TWO,"episode323"),1L);
    private static final ProposalLifecycle.ExpectedPostcondition EXPECTED=new ProposalLifecycle.ExpectedPostcondition(
            1,BEFORE,SOURCE,"fixture-observer323",List.of(new ProposalLifecycle.ExpectedBoolean(
                    new ProposalLifecycle.FieldKey("ready"),true)));
    private static final JointBudgetSelector.Claims NONE=new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of());
    private static ActionCommand command(OpportunityJson.Obj arguments) {
        return command("action323","session323",arguments);
    }
    private static ActionCommand command(String id,String session,OpportunityJson.Obj arguments) {
        return new ActionCommand(id,BEFORE,SOURCE,session,new OperationKey("fixture-operation323"),
                arguments,EXPECTED,NONE,NOW.plusSeconds(30));
    }
    private static OpportunityJson.Obj textArgs(String text) {
        return new OpportunityJson.Obj(Map.of("s",new OpportunityJson.Text(text)));
    }
    private static OpportunityJson.Obj nestedArgs(int arrays) {
        OpportunityJson.Value value=new OpportunityJson.IntegerValue(BigInteger.ZERO);
        for(int i=0;i<arrays;i++)value=new OpportunityJson.Arr(List.of(value));
        return new OpportunityJson.Obj(Map.of("v",value));
    }
    @Test void typedArgumentsRetainOriginalTokensAndRoleBudget() {
        var original = new OpportunityJson.Obj(Map.of(
                "negative_zero",new OpportunityJson.DecimalValue("-0.0"),
                "exponent",new OpportunityJson.DecimalValue("1E+3"),
                "wide_exponent",new OpportunityJson.DecimalValue("1e10000"),
                "integer",new OpportunityJson.IntegerValue(new BigInteger("9".repeat(120))),
                "unicode",new OpportunityJson.Text("é"+new String(Character.toChars(0x1F600))),
                "nested",new OpportunityJson.Arr(List.of(new OpportunityJson.Bool(true),OpportunityJson.Nil.INSTANCE))));
        var accepted = command(original);
        assertSame(original,accepted.arguments());
        assertEquals("-0.0",((OpportunityJson.DecimalValue)accepted.arguments().get("negative_zero")).token());
        assertEquals("1e10000",((OpportunityJson.DecimalValue)accepted.arguments().get("wide_exponent")).token());
        assertEquals(new BigInteger("9".repeat(120)),((OpportunityJson.IntegerValue)accepted.arguments().get("integer")).value());
        assertEquals(1_048_576,ActionCommand.MAX_ARGUMENT_BYTES);
        int payloadCharacters=ActionCommand.MAX_ARGUMENT_BYTES-8;
        var exact=textArgs("x".repeat(payloadCharacters));
        assertEquals(ActionCommand.MAX_ARGUMENT_BYTES,DriverJson.encode(exact).length);
        assertSame(exact,command(exact).arguments());
        var excess=textArgs("x".repeat(payloadCharacters+1));
        assertEquals(ActionCommand.MAX_ARGUMENT_BYTES+1,DriverJson.encode(excess).length);
        var rejected=assertThrows(ProjectionProtocolException.class,()->command(excess));
        assertEquals(ProjectionError.Code.INVALID_ENVELOPE,rejected.code());
        assertEquals("projection JSON exceeds explicit role budget",rejected.getMessage());
    }

    @Test void depthUnicodeAndOriginalGuardOrderStayStrict() {
        // 1. Valid shallow control (object depth0, array depth1, scalar depth2)
        var valid = command(nestedArgs(1));
        assertNotNull(valid);

        // 2. Invalid actionId (regex fail) takes precedence over depth/Unicode checks
        try {
            new ActionCommand("bad id", BEFORE, SOURCE, "session323", new OperationKey("op"), nestedArgs(64), EXPECTED, NONE, NOW);
            fail("expected actionId rejection");
        } catch (IllegalArgumentException e) {
            assertTrue(e.getMessage().contains("bounded action ID required"));
        }

        // 3. Invalid Unicode session (surrogate fail) takes precedence over depth check
        try {
            new ActionCommand("action323", BEFORE, SOURCE, Character.toString((char)0xD800), new OperationKey("op"), nestedArgs(64), EXPECTED, NONE, NOW);
            fail("expected session Unicode rejection");
        } catch (IllegalArgumentException e) {
            assertTrue(e.getMessage().contains("unpaired Unicode surrogate"));
        }

        // 4. Too deep arguments (root + 64 arrays + scalar = depth 65 > 64 limit)
        try {
            command(nestedArgs(64));
            fail("expected depth rejection");
        } catch (IllegalArgumentException e) {
            assertTrue(e.getMessage().contains("bounded full JSON depth"));
        }

        // 5. Unpaired surrogate in Text argument value
        assertThrows(IllegalArgumentException.class, () -> command(textArgs(Character.toString((char)0xD800))));

        // 6. Valid boundary depth (root + 63 arrays + scalar = depth 64)
        assertNotNull(command(nestedArgs(63)));
    }
}
