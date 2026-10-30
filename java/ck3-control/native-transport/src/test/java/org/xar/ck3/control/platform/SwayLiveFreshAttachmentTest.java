package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

/** Actual newly supplied software process only. No CK3, Root or business qualification. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named = "xar.m6.livepeer.run", matches = ".+")
public final class SwayLiveFreshAttachmentTest {
    private org.xar.ck3.control.build.WindowsJobProcess softwarePeer;
    private String previousPeerPid;
    private boolean peerPidChanged;

    @org.junit.jupiter.api.BeforeEach void startActualSoftwarePeer() throws Exception {
        String runPathStr = System.getProperty("xar.m6.livepeer.run");
        String execPathStr = System.getProperty("xar.m6.livepeer.executable");
        if (runPathStr == null || runPathStr.isBlank() || execPathStr == null || execPathStr.isBlank()) {
            throw new java.io.IOException("Required system properties xar.m6.livepeer.run, xar.m6.livepeer.executable must be nonblank");
        }
        java.nio.file.Path runPath = java.nio.file.Path.of(runPathStr).toRealPath();
        java.nio.file.Path execPath = java.nio.file.Path.of(execPathStr).toRealPath();
        if (execPath.getFileName().toString().equalsIgnoreCase("ck3.exe")) throw new java.io.IOException("Refuse ck3.exe executable for no-current-Game test scope");

        byte[] raw;
        try (var input = java.nio.file.Files.newInputStream(runPath)) { raw = input.readNBytes(65537); }
        if (raw.length == 0 || raw.length > 65536) throw new java.io.IOException("Bounded run JSON required");
        var config = org.xar.ck3.control.contracts.StrictJson.parse(raw);
        assertEquals(execPath, java.nio.file.Path.of(org.xar.ck3.control.contracts.StrictJson.text(config.get("executable"))).toRealPath());
        var pipe = org.xar.ck3.control.contracts.StrictJson.text(config.get("pipe_name"));
        var workDir = java.nio.file.Path.of(org.xar.ck3.control.contracts.StrictJson.text(config.get("work_directory"))).toRealPath();
        var stdout = java.nio.file.Path.of(org.xar.ck3.control.contracts.StrictJson.text(config.get("stdout"))).toAbsolutePath().normalize();
        var stderr = java.nio.file.Path.of(org.xar.ck3.control.contracts.StrictJson.text(config.get("stderr"))).toAbsolutePath().normalize();
        var memoryLimit = org.xar.ck3.control.contracts.StrictJson.integer(config.get("memory_limit_bytes"), 1, Long.MAX_VALUE);
        var actor = org.xar.ck3.control.contracts.StrictJson.integer(config.get("actor"), Long.MIN_VALUE, Long.MAX_VALUE);
        var target = org.xar.ck3.control.contracts.StrictJson.integer(config.get("target"), Long.MIN_VALUE, Long.MAX_VALUE);
        var lifetime = org.xar.ck3.control.contracts.StrictJson.integer(config.get("lifetime_ms"), 1, Long.MAX_VALUE);
        var maxRequests = org.xar.ck3.control.contracts.StrictJson.integer(config.get("max_requests"), 1, Long.MAX_VALUE);

        var args = java.util.List.of(pipe, org.xar.ck3.control.contracts.StrictJson.text(config.get("archive_directory")),
                String.valueOf(actor), String.valueOf(target), String.valueOf(lifetime), String.valueOf(maxRequests));
        var env = new java.util.TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        env.putAll(System.getenv());
        var configEnv = config.get("environment");
        configEnv.fieldNames().forEachRemaining(key -> env.put(key, org.xar.ck3.control.contracts.StrictJson.text(configEnv.get(key))));

        var spec = new org.xar.ck3.control.build.WindowsJobProcess.CommandSpec(execPath, args, workDir, env, stdout, stderr, memoryLimit);
        softwarePeer = org.xar.ck3.control.build.WindowsJobProcess.start(spec);
        var identity = softwarePeer.identity();
        previousPeerPid = System.getProperty("xar.m6.livepeer.pid");
        System.setProperty("xar.m6.livepeer.pid", Long.toString(identity.pid()));
        peerPidChanged = true;
        System.out.println("Peer PID=" + identity.pid() + " creationFiletime=" + identity.creationFiletimeDecimal() + " executable=" + identity.executable());
    }

    @org.junit.jupiter.api.AfterEach void finishActualSoftwarePeer() throws Exception {
        if (softwarePeer == null) {
            if (peerPidChanged) {
                if (previousPeerPid == null) System.clearProperty("xar.m6.livepeer.pid");
                else System.setProperty("xar.m6.livepeer.pid", previousPeerPid);
            }
            return;
        }
        try {
            var actualTerminal = softwarePeer.await(java.time.Duration.ofSeconds(5), java.time.Instant.now().plusSeconds(8), () -> {});
            System.out.println(actualTerminal.toString());
            assertTrue(actualTerminal.passed(), actualTerminal.toString());
        } finally {
            try {
                softwarePeer.close();
            } finally {
                if (peerPidChanged) {
                    if (previousPeerPid == null) System.clearProperty("xar.m6.livepeer.pid");
                    else System.setProperty("xar.m6.livepeer.pid", previousPeerPid);
                }
                softwarePeer = null;
                previousPeerPid = null;
                peerPidChanged = false;
            }
        }
    }

    @org.junit.jupiter.api.Test void actualLivePeerReceivesTwoIndependentFreshRequests() throws Exception {
        String planPathStr = System.getProperty("xar.m6.livepeer.plan");
        String pidStr = System.getProperty("xar.m6.livepeer.pid");
        String execPathStr = System.getProperty("xar.m6.livepeer.executable");
        if (planPathStr == null || planPathStr.isBlank() || pidStr == null || pidStr.isBlank() || execPathStr == null || execPathStr.isBlank()) {
            throw new java.io.IOException("Required system properties xar.m6.livepeer.plan, xar.m6.livepeer.pid, xar.m6.livepeer.executable must be nonblank");
        }
        long pid = Long.parseLong(pidStr);
        if (pid <= 0 || pid > 0xffff_ffffL) throw new java.io.IOException("PID out of DWORD range");
        java.nio.file.Path planPath = java.nio.file.Path.of(planPathStr).toRealPath();
        java.nio.file.Path execPath = java.nio.file.Path.of(execPathStr).toRealPath();
        if (execPath.getFileName().toString().equalsIgnoreCase("ck3.exe")) throw new java.io.IOException("Refuse ck3.exe executable for no-current-Game test scope");

        byte[] raw;
        try (var input = java.nio.file.Files.newInputStream(planPath)) { raw = input.readNBytes(org.xar.ck3.control.platform.NativeLaunchPlanCodec.MAXIMUM_BYTES + 1); }
        if (raw.length == 0 || raw.length > org.xar.ck3.control.platform.NativeLaunchPlanCodec.MAXIMUM_BYTES) throw new java.io.IOException("Bounded plan JSON required");
        var digest = java.security.MessageDigest.getInstance("SHA-256").digest(raw);
        var sha = java.util.HexFormat.of().formatHex(digest);
        var planRef = new org.xar.ck3.control.contracts.ExactRef(planPath.toString(), raw.length, sha);
        var plan = org.xar.ck3.control.platform.NativeLaunchPlan.readExact(planRef, new org.xar.ck3.control.platform.NativeBridgeLaunchEvidence());

        var deadline = java.time.Instant.now().plusSeconds(20);
        var handle = org.xar.ck3.control.build.WindowsJobProcess.retainReadOnlyProcess(pid);
        try {
            if (handle.waitZero() != 258L) throw new java.io.IOException("Expected Game generation not running before HELLO");
            var identity = handle.identity();
            if (identity.pid() != pid) throw new java.io.IOException("Identity PID mismatch");
            if (!java.nio.file.Path.of(identity.executable()).toRealPath().equals(execPath)) throw new java.io.IOException("Identity executable mismatch");
            var generation = org.xar.ck3.control.platform.ManagedGameSession.generation(identity);

            var request = new org.xar.ck3.control.platform.NativeGameAttachment.Request(plan, generation, java.util.List.of(), 64, 8);
            var results = org.xar.ck3.control.platform.SwayLiveFreshAssertions.attachAndReadTwoFreshAndAssert(request, deadline);
            if (results.size() != 2) throw new java.io.IOException("Expected two fresh results");
            System.out.println("Peer PID=" + identity.pid() + " creationFiletime=" + identity.creationFiletimeDecimal() + " req1=" + results.get(0).acknowledgement().requestId() + " req2=" + results.get(1).acknowledgement().requestId());
        } finally {
            handle.close();
        }
    }
}

/** Receiver originals returned after close are historical test DATA, never a live capability. */
final class SwayLiveFreshAssertions {
    public static java.util.List<org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received> attachAndReadTwoFreshAndAssert(org.xar.ck3.control.platform.NativeGameAttachment.Request request, java.time.Instant deadline) throws Exception {
        try (var session = org.xar.ck3.control.platform.NativeGameAttachment.attach(request, deadline)) {
            assertEquals(org.xar.ck3.control.platform.ManagedGameSession.Mode.ATTACHED, session.mode());
            assertEquals(request.expectedGame(), session.generation());
            var transport = session.nativeTransport();
            var hello = transport.originalHello();
            assertEquals(request.expectedGame().pid(), hello.pid());


            var first = transport.readFreshFullState(deadline);
            assertInstanceOf(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received.class, first);
            var firstReceived = (org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received) first;

            var second = transport.readFreshFullState(deadline);
            assertInstanceOf(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received.class, second);
            var secondReceived = (org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received) second;

            var firstAck = firstReceived.acknowledgement();
            var firstFrame = firstReceived.originalFrame();
            assertEquals(request.expectedGame(), firstFrame.session().game());
            assertEquals(hello.connectionGeneration(), firstFrame.session().connectionGeneration());
            assertEquals(request.plan().sessionId(), firstFrame.session().sessionId());
            var firstEvent = firstReceived.snapshotReceived();
            org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.verifyOriginal(firstAck, firstFrame, firstEvent);

            var secondAck = secondReceived.acknowledgement();
            var secondFrame = secondReceived.originalFrame();
            assertEquals(request.expectedGame(), secondFrame.session().game());
            assertEquals(hello.connectionGeneration(), secondFrame.session().connectionGeneration());
            assertEquals(request.plan().sessionId(), secondFrame.session().sessionId());
            var secondEvent = secondReceived.snapshotReceived();
            org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.verifyOriginal(secondAck, secondFrame, secondEvent);

            assertEquals(firstFrame.session(), secondFrame.session());
            assertEquals(firstAck.custody().orElseThrow().session(), firstFrame.session());
            assertEquals(secondAck.custody().orElseThrow().session(), secondFrame.session());
            assertEquals(firstAck.custody().orElseThrow().custodyEpoch(), secondAck.custody().orElseThrow().custodyEpoch());
            assertNotEquals(firstAck.requestId(), secondAck.requestId());
            assertTrue(firstAck.custody().orElseThrow().responseReceived().order().compareTo(secondAck.custody().orElseThrow().writeEntered().order()) < 0);

            org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.verifyAfter(firstAck, secondReceived);

            var firstToken = transport.acceptedSnapshotRevision(firstFrame);
            firstToken.requireOriginal(firstFrame);
            assertEquals(firstFrame.session(), firstToken.session());
            assertEquals(firstFrame.snapshotId(), firstToken.snapshotId());
            assertEquals(firstFrame.nativeRevision(), firstToken.nativeRevision());
            assertEquals(firstEvent, firstToken.received());
            assertTrue(firstToken.publicRevision().signum() > 0);

            var secondToken = transport.acceptedSnapshotRevision(secondFrame);
            secondToken.requireOriginal(secondFrame);
            assertEquals(secondFrame.session(), secondToken.session());
            assertEquals(secondFrame.snapshotId(), secondToken.snapshotId());
            assertEquals(secondFrame.nativeRevision(), secondToken.nativeRevision());
            assertEquals(secondEvent, secondToken.received());
            assertTrue(secondToken.publicRevision().signum() > 0);
            assertTrue(secondToken.publicRevision().compareTo(firstToken.publicRevision()) >= 0);

            var firstPayload = org.xar.ck3.control.contracts.StrictJson.parse(java.util.Arrays.copyOfRange(firstFrame.originalPacket(), 4, firstFrame.originalPacket().length));
            assertEquals(firstAck.requestId(), firstPayload.get("read_request_id").textValue());
            var secondPayload = org.xar.ck3.control.contracts.StrictJson.parse(java.util.Arrays.copyOfRange(secondFrame.originalPacket(), 4, secondFrame.originalPacket().length));
            assertEquals(secondAck.requestId(), secondPayload.get("read_request_id").textValue());

            System.out.println("hello pid=" + hello.pid() + " connGen=" + hello.connectionGeneration() + " req1=" + firstAck.requestId() + " req2=" + secondAck.requestId() + " pubRev1=" + firstToken.publicRevision() + " pubRev2=" + secondToken.publicRevision() + " natRev1=" + firstFrame.nativeRevision() + " natRev2=" + secondFrame.nativeRevision());
            return java.util.List.of(firstReceived, secondReceived);
        }
    }
}
