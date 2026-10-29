package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Exact live Status capability refusal. This failure carries original DATA, never a read or action grant. */
public final class StatusCapabilityFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final CommandOrigin origin;
    private final G2Source source;
    private final ExactRef originalHello;

    private StatusCapabilityFailure(CommandOrigin origin, G2Source source, ExactRef originalHello) {
        super("native DLL does not advertise required capability " + PhysicalStatusIdentity.CAPABILITY);
        this.origin = origin; this.source = source; this.originalHello = originalHello;
    }
    public CommandOrigin origin() { return origin; }
    public G2Source source() { return source; }
    public ExactRef originalHello() { return originalHello; }
    public String requiredCapability() { return PhysicalStatusIdentity.CAPABILITY; }

    /** Called only after the actual live authority has verified its complete source and same writer scope. */
    static void requireAdvertised(CommandOrigin origin, G2Source source, ExactRef originalHello, byte[] packet) throws IOException {
        Objects.requireNonNull(origin); Objects.requireNonNull(source); Objects.requireNonNull(originalHello); Objects.requireNonNull(packet);
        require(source.machineId().equals(origin.machineId()) && originalHello.bytes() > 0
                && originalHello.bytes() <= 1 << 20 && Path.of(originalHello.path()).isAbsolute()
                && packet.length == originalHello.bytes() && DriverJson.sha256(packet).equals(originalHello.sha256()),
                "Status capability check requires its exact original HELLO/source/origin");
        var original = NativeWire.decode(packet);
        require(original instanceof NativeWire.Hello, "Status capability check requires the complete original HELLO packet");
        var hello = (NativeWire.Hello) original;
        BigInteger connection;
        if (origin instanceof CommandOrigin.PhysicalStatusOnly physical) {
            require(physical.identity().source().equals(source) && physical.identity().helloEvidence().equals(originalHello),
                    "Status capability original differs from the physical source/origin");
            connection = physical.identity().connectionGeneration();
        } else throw new IllegalArgumentException("only the actual dedicated Status origin can report this capability refusal");
        require(hello.pid() == origin.game().pid() && hello.connectionGeneration().equals(connection)
                && hello.buildMatch() && hello.adapterStatus().equals("ready") && hello.capabilities().contains("game.state.snapshot"),
                "Status capability original HELLO crossed its actual Game/connection/build");
        if (!hello.capabilities().contains(PhysicalStatusIdentity.CAPABILITY))
            throw new StatusCapabilityFailure(origin, source, originalHello);
    }
}
