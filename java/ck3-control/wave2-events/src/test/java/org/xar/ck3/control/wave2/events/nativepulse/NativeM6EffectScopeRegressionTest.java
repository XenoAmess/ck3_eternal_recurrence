package org.xar.ck3.control.wave2.events.nativepulse;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeRawScriptValue.*;
import java.io.InputStream;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** M6's reviewed3765E50 scope gate consumes M2's sole implementation; no Game/effect result. */
final class NativeM6EffectScopeRegressionTest {
    private static final ScopeMask EMPTY = new ScopeMask(BigInteger.ZERO, BigInteger.ZERO);
    private static final ScopeMask FIRST = new ScopeMask(BigInteger.ONE, BigInteger.ZERO);
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    @Test void actualSourceAndZeroKindDistinguishEffectFromTheScopeChain() throws Exception {
        try (InputStream original = getClass().getResourceAsStream("/m6/source12.json")) {
            assertNotNull(original, "the complete current native evidence must be packaged into persistent CI");
            var source = StrictJson.parse(original.readAllBytes());
            assertEquals("m6-r3-native12-manager-scope", source.get("graph_id").textValue());
            assertEquals(128, source.at("/scope_gate/mask_bits").intValue());
            assertEquals("3766140", source.at("/scope_gate/eligible_dispatch/rva").textValue());
            assertFalse(source.at("/scope_gate/ineligible_dispatch/effect_B0_called").booleanValue());
        }
        Scope zero = scope(0);
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.CHAIN_3755500, 0, zero, FIRST));
        assertEquals(ScopeEligibility.INELIGIBLE, scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, zero, FIRST));
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, zero, EMPTY));
    }

    @Test void declaredExactAndEmptyMaskPrecedeBitsButOutOfRangeRemainsUnknown() {
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 65, scope(65), FIRST));
        assertEquals(ScopeEligibility.INELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 64, scope(65), FIRST));
        ScopeMask secondFirst = new ScopeMask(BigInteger.ZERO, BigInteger.ONE);
        ScopeMask secondLast = new ScopeMask(BigInteger.ZERO, BigInteger.ONE.shiftLeft(63));
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(65), secondFirst));
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(128), secondLast));
        assertEquals(ScopeEligibility.MASK_OUT_OF_BOUNDS,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(129), secondFirst));
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 129, scope(129), FIRST));
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(129), EMPTY));
    }

    @Test void rawScopeIdentityStaysExactAndEligibilityDoesNotSubstituteForAnEffectReceipt() {
        Scope original = new Scope(U64, new BigInteger("9007199254740993"));
        assertEquals(65535, original.nativeTypeU16());
        assertEquals(U64, original.metadataU64());
        assertEquals("9007199254740993", original.payloadU64().toString());
        assertEquals(ScopeEligibility.MASK_OUT_OF_BOUNDS,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, original, FIRST));
        assertEquals(ScopeEligibility.ELIGIBLE,
                scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 65535, original, FIRST));
        // This return is only the mask gate; the actual source separately validates
        // object, virtual+B0 and effect after-state. No terminal/benefit API is called here.
        assertThrows(IllegalArgumentException.class,
                () -> scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 65536, original, FIRST));
        assertThrows(IllegalArgumentException.class, () -> new Scope(U64.add(BigInteger.ONE), BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> new ScopeMask(BigInteger.ONE.negate(), BigInteger.ZERO));
    }

    private static Scope scope(int kind) {
        return new Scope(new BigInteger("1234000000000000", 16).or(BigInteger.valueOf(kind)), U64);
    }
}

