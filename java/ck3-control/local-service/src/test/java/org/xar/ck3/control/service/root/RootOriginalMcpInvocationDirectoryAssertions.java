package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Assertions for the real Root public-host fixture. The caller supplies its actual
 * complete directory and privately issued Inputs; this class creates neither.
 */
public final class RootOriginalMcpInvocationDirectoryAssertions {
    private RootOriginalMcpInvocationDirectoryAssertions() { }

    public static void metadataRetainsActualDirectory(McpExecutableDirectory.Complete actualComplete,
            RootRuntimeDefinitions.Inputs identicalInputs, Clock actualClock) throws IOException {
        var checked = RootOriginalMcpInvocationDirectory.bind(actualComplete, identicalInputs, actualClock);
        assertSame(actualComplete.coverage(), checked.coverage());
        assertEquals(actualComplete.directory().scope(), checked.directory().scope());
        assertEquals(actualComplete.directory().tools(), checked.directory().tools());
        assertEquals(actualComplete.directory().resources(), checked.directory().resources());
    }

    public static void expiredInputsRejectBeforeDispatch(McpExecutableDirectory.Complete actualComplete,
            RootRuntimeDefinitions.Inputs identicalInputs, Clock actualClock,
            PublicMcpDirectory.ToolCall actualSnapshotCall, PublicMcpDirectory.ResourceCall actualResourceCall)
            throws IOException {
        requireSnapshot(actualSnapshotCall);
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, false, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()), identicalInputs, clock);
        clock.expire();
        var toolFailure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().invoke(actualSnapshotCall));
        assertTrue(toolFailure.getMessage().contains("no directory dispatch"));
        var resourceFailure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().read(actualResourceCall));
        assertTrue(resourceFailure.getMessage().contains("no directory dispatch"));
        assertThrows(UncheckedIOException.class, () -> checked.directory().tools());
        assertThrows(UncheckedIOException.class, () -> checked.directory().resources());
        assertEquals(0, probe.toolsInvoked);
        assertEquals(0, probe.resourcesRead);
        assertEquals(0, probe.toolLists);
        assertEquals(0, probe.resourceLists);
    }

    public static void expiryAfterActualSnapshotDoesNotAcceptOrRepeatTheResult(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ToolCall actualSnapshotCall) throws IOException {
        requireSnapshot(actualSnapshotCall);
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, true, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()), identicalInputs, clock);
        var failure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().invoke(actualSnapshotCall));
        assertTrue(failure.getMessage().contains("unconfirmed"));
        assertTrue(failure.getMessage().contains("do not resend"));
        assertEquals(1, probe.toolsInvoked);
        assertEquals(0, probe.resourcesRead);
    }

    public static void expiryAfterActualResourceReadDoesNotAcceptOrRepeatTheResult(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ResourceCall actualResourceCall) throws IOException {
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, false, true);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()), identicalInputs, clock);
        var failure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().read(actualResourceCall));
        assertTrue(failure.getMessage().contains("result cannot be accepted"));
        assertEquals(0, probe.toolsInvoked);
        assertEquals(1, probe.resourcesRead);
    }

    public static void expiryAfterRejectedInvocationIsVisibleAndPreservesItsOriginalCause(
            McpExecutableDirectory.Complete actualComplete, RootRuntimeDefinitions.Inputs identicalInputs,
            Clock actualClock, PublicMcpDirectory.ToolCall actualSnapshotCall) throws IOException {
        requireSnapshot(actualSnapshotCall);
        var rejected = new PublicMcpDirectory.ToolCall(actualSnapshotCall.name(),
                new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE, Optional.of(
                        new RawJson("{\"include_native_command_history\":null}".getBytes(StandardCharsets.UTF_8)))),
                actualSnapshotCall.meta(), actualSnapshotCall.cancellation());
        var clock = new ProbeClock(actualClock);
        var probe = new Probe(actualComplete.directory(), clock, true, false);
        var checked = RootOriginalMcpInvocationDirectory.bind(
                new McpExecutableDirectory.Complete(probe, actualComplete.coverage()), identicalInputs, clock);
        var failure = assertThrows(PublicMcpDirectory.ToolFailure.class,
                () -> checked.directory().invoke(rejected));
        assertNotNull(probe.originalFailure, "the actual snapshot decoder must reject null before application work");
        assertSame(probe.originalFailure, failure.getCause());
        assertTrue(failure.getMessage().contains("unconfirmed"));
        assertTrue(failure.getMessage().contains("do not resend"));
        assertTrue(java.util.Arrays.stream(failure.getSuppressed()).anyMatch(IOException.class::isInstance));
        assertEquals(1, probe.toolsInvoked);
    }

    private static void requireSnapshot(PublicMcpDirectory.ToolCall call) {
        assertEquals("ck3_take_snapshot", Objects.requireNonNull(call).name(),
                "the actual Root fixture must supply the original read-only snapshot invocation");
    }

    /** Observation only: every operation still forwards to the supplied actual production directory. */
    private static final class Probe implements PublicMcpDirectory {
        private final PublicMcpDirectory actual;
        private final ProbeClock clock;
        private final boolean expireAfterTool, expireAfterResource;
        private int toolsInvoked, resourcesRead, toolLists, resourceLists;
        private Throwable originalFailure;

        private Probe(PublicMcpDirectory actual, ProbeClock clock, boolean expireAfterTool, boolean expireAfterResource) {
            this.actual = Objects.requireNonNull(actual); this.clock = clock;
            this.expireAfterTool = expireAfterTool; this.expireAfterResource = expireAfterResource;
        }
        @Override public Scope scope() { return actual.scope(); }
        @Override public List<ToolDescriptor> tools() { toolLists++; return actual.tools(); }
        @Override public List<ResourceDescriptor> resources() { resourceLists++; return actual.resources(); }
        @Override public CallResult invoke(ToolCall call) throws ToolFailure, RpcFailure {
            toolsInvoked++;
            final CallResult result;
            try { result = actual.invoke(call); }
            catch (ToolFailure | RpcFailure failure) {
                originalFailure = failure; if (expireAfterTool) clock.expire(); throw failure;
            } catch (RuntimeException failure) {
                originalFailure = failure; if (expireAfterTool) clock.expire(); throw failure;
            }
            if (expireAfterTool) clock.expire();
            return result;
        }
        @Override public ResourceResult read(ResourceCall call) throws ToolFailure, RpcFailure {
            resourcesRead++; var result = actual.read(call);
            if (expireAfterResource) clock.expire();
            return result;
        }
    }

    /** Only this wrapper's clock changes; the real Root/Native clock and source files are never modified. */
    private static final class ProbeClock extends Clock {
        private final AtomicReference<Instant> instant;
        private final ZoneId zone;
        private ProbeClock(Clock actual) { this(new AtomicReference<>(actual.instant()), actual.getZone()); }
        private ProbeClock(AtomicReference<Instant> instant, ZoneId zone) { this.instant = instant; this.zone = zone; }
        private void expire() { instant.set(Instant.MAX); }
        @Override public ZoneId getZone() { return zone; }
        @Override public Clock withZone(ZoneId requested) { return new ProbeClock(instant, Objects.requireNonNull(requested)); }
        @Override public Instant instant() { return instant.get(); }
    }
}


