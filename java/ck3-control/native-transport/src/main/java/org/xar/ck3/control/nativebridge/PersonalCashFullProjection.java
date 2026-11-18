package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Packet-checked CASH input DATA only. This never creates a Full/Live receipt, Driver, public revision or source authority.
 * HELLO binds PID and connection generation; its wire has no machine, session ID or process-birth evidence.
 * The caller's private receiver must separately retain the identical live issuer, session and custody. */
public final class PersonalCashFullProjection {
    private PersonalCashFullProjection() { }

    public static RawJson snapshotData(ObservedFrame actual, NativeWire.Hello originalHello) {
        Objects.requireNonNull(actual); Objects.requireNonNull(originalHello);
        Obj state = DriverObservationAssembler.originalNativeState(actual);
        NativeWire.Hello decoded;
        try {
            var original = NativeWire.decode(originalHello.packet().value());
            StrictJson.require(original instanceof NativeWire.Hello, "original HELLO packet required for CASH projection");
            decoded = (NativeWire.Hello) original;
        } catch (IOException invalid) {
            throw new IllegalArgumentException("invalid original HELLO packet for CASH projection", invalid);
        }
        StrictJson.require(sameHello(decoded, originalHello), "typed HELLO differs from its original packet");
        byte[] packet = originalHello.packet().value();
        Obj hello = DriverJson.object(Arrays.copyOfRange(packet, 4, packet.length), DriverJson.MAX_NATIVE_BYTES);
        var build = ExactCk3Build.CK3_1210;
        StrictJson.require(decoded.pid() == actual.session().game().pid()
                && decoded.connectionGeneration().equals(actual.session().connectionGeneration()),
                "CASH frame and HELLO PID or connection generation differ");
        StrictJson.require(build.matches(text(hello.get("expected_ck3_version"), "HELLO version"), decoded.gameSha256())
                && decoded.adapterId().equals("ck3-1.21.0-msvc-x64") && decoded.adapterStatus().equals("ready")
                && decoded.buildMatch(), "CASH projection requires the original exact Florin HELLO");
        StrictJson.require(new Text(NativeSemanticNormalizer.FLORIN_SCHEMA).equals(state.get("schema"))
                && build.matches(text(state.get("game_version"), "Full version"), text(state.get("executable_sha256"), "Full SHA"))
                && new Text("ck3-1.21.0-msvc-x64").equals(state.get("adapter_id"))
                && new Text("ck3-1.21.0-native-headless-main-thread").equals(state.get("backend")),
                "CASH projection requires the original exact Florin Full state");
        StrictJson.require(actual.nativeRevision().signum() > 0 && actual.nativeRevision().compareTo(StrictJson.UINT64_MAX) <= 0,
                "CASH projection requires the original positive uint64 Native revision");
        Obj result = retainOrAdd(state, "native_revision", new IntegerValue(actual.nativeRevision()));
        Obj diagnostics;
        if (result.members().containsKey("diagnostics"))
            diagnostics = object(result.get("diagnostics"), "original diagnostics object");
        else diagnostics = new Obj(java.util.Map.of());
        diagnostics = retainOrAdd(diagnostics, "hello", hello);
        result = result.with("diagnostics", diagnostics);
        return new RawJson(DriverJson.encode(result));
    }

    private static Obj retainOrAdd(Obj original, String key, OpportunityJson.Value derived) {
        if (original.members().containsKey(key)) {
            StrictJson.require(derived.equals(original.get(key)), "original CASH projection field conflicts: " + key);
            return original;
        }
        return original.with(key, derived);
    }

    private static boolean sameHello(NativeWire.Hello actual, NativeWire.Hello supplied) {
        return actual.pid() == supplied.pid() && actual.buildMatch() == supplied.buildMatch()
                && Objects.equals(actual.connectionGeneration(), supplied.connectionGeneration())
                && Objects.equals(actual.bridgeVersion(), supplied.bridgeVersion())
                && Objects.equals(actual.gameSha256(), supplied.gameSha256())
                && Objects.equals(actual.adapterId(), supplied.adapterId())
                && Objects.equals(actual.adapterStatus(), supplied.adapterStatus())
                && actual.capabilities().equals(supplied.capabilities());
    }
}
