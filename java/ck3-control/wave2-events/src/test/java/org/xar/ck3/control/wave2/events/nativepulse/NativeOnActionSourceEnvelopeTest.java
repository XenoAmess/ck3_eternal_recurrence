package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFields.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionSourceEnvelope.*;

final class NativeOnActionSourceEnvelopeTest {
    private static final String MACHINE = "software-fixture-machine", TIME = "2026-10-23T22:30:00Z";
    private static final BigInteger EVENT = new BigInteger("18446744073709550001"), ACTION = new BigInteger("18446744073709550002");
    private static final NativePlayableAnnualGate.Executable EXE = NativePlayableAnnualGate.Executable.exact(NativePlayableAnnualGate.EXECUTABLE_SHA256).orElseThrow();

    @Test void sourceEnvelopePreservesOriginalProducerBothConsumersAndColdReplay() throws Exception {
        Fixture fixture = fixture(); Sources sources = fixture.sources(Origin.SOFTWARE_FIXTURE, Optional.of(fixture.boundary()));
        ExactRef saved = preserve(fixture.input(), sources, fixture.store());
        Replayed cold = replay(saved, fixture.store());
        assertEquals(Custody.SOFTWARE_FIXTURE, cold.custody());
        assertEquals(fixture.input(), cold.fields().original());
        assertEquals(List.of(EVENT, ACTION), cold.fields().recomputed().emissions().stream().map(Emission::address).toList());
        assertEquals(sources, cold.envelope().sources());
        assertArrayEquals(encode(cold.envelope()), encode(decode(encode(cold.envelope()))));
        assertFalse(cold.fields().recomputed().currentLoadedSourceQualified());
        assertFalse(cold.fields().recomputed().nativeGameExecuted());
    }

    @Test void externalByteCustodyDoesNotCreateLoadedNativeOrGameAuthority() throws Exception {
        Fixture fixture = fixture();
        Replayed cold = replay(preserve(fixture.input(), fixture.sources(Origin.EXTERNAL_CAPTURE, Optional.of(fixture.boundary())), fixture.store()), fixture.store());
        assertEquals(Custody.ORIGINAL_BYTES_ACCOUNTED, cold.custody());
        assertFalse(cold.fields().recomputed().currentLoadedSourceQualified());
        assertFalse(cold.fields().recomputed().completeNativeDispatcher());
        assertFalse(cold.fields().recomputed().nativeGameExecuted());
        assertEquals(fixture.files().stream().map(OpenedFile::nativePathHex).toList(), cold.envelope().sources().files().stream().map(OpenedFile::nativePathHex).toList());
    }

    @Test void vfsAndPayloadSandwichesDetectDifferentIndependentInvalidations() throws Exception {
        Fixture fixture = fixture(); Boundary boundary = fixture.boundary();
        ExactRef changed = fixture.store().preserve(bytes("different original snapshot"));
        Boundary vfsChanged = new Boundary(boundary.mountTable(), boundary.replacementRules(), boundary.vfsBefore(), changed, boundary.payloadBefore(), boundary.payloadAfter());
        Boundary payloadChanged = new Boundary(boundary.mountTable(), boundary.replacementRules(), boundary.vfsBefore(), boundary.vfsAfter(), boundary.payloadBefore(), changed);
        for (Boundary candidate : List.of(vfsChanged, payloadChanged)) {
            Replayed cold = replay(preserve(fixture.input(), fixture.sources(Origin.EXTERNAL_CAPTURE, Optional.of(candidate)), fixture.store()), fixture.store());
            assertEquals(Custody.CHANGED_DURING_CAPTURE, cold.custody());
        }
    }

    @Test void unavailableBoundaryAndPartiallyMappedFieldsKeepTheirOriginalGap() throws Exception {
        Fixture fixture = fixture();
        Replayed noBoundary = replay(preserve(fixture.input(), fixture.sources(Origin.EXTERNAL_CAPTURE, Optional.empty()), fixture.store()), fixture.store());
        assertEquals(Custody.SOURCE_BINDING_UNAVAILABLE, noBoundary.custody());
        Sources partial = new Sources(MACHINE, TIME, Origin.EXTERNAL_CAPTURE, List.of(fixture.files().getFirst()), Optional.of(fixture.boundary()));
        Replayed missingPiece = replay(preserve(fixture.input(), partial, fixture.store()), fixture.store());
        assertEquals(Custody.SOURCE_BINDING_UNAVAILABLE, missingPiece.custody());
        assertEquals(2, missingPiece.fields().recomputed().emissions().size());
    }

    @Test void exactSourceSlicesRejectWrongBytesOutOfRangeAndDuplicateOwnership() throws Exception {
        Fixture fixture = fixture(); OpenedFile first = fixture.files().getFirst();
        ExactRef different = fixture.store().preserve(bytes("different bytes at the original offset"));
        List<OpenedFile> candidates = List.of(new OpenedFile(0, first.nativePathHex(), different, first.pieces()),
                new OpenedFile(0, first.nativePathHex(), first.originalBytes(), List.of(new Piece(0, MAX_BYTES))),
                new OpenedFile(0, first.nativePathHex(), first.originalBytes(), List.of(new Piece(0, 7), new Piece(0, 7))));
        for (OpenedFile candidate : candidates) {
            Sources sources = new Sources(MACHINE, TIME, Origin.EXTERNAL_CAPTURE, List.of(candidate), Optional.of(fixture.boundary()));
            assertThrows(IllegalArgumentException.class, () -> preserve(fixture.input(), sources, fixture.store()));
        }
    }

    @Test void coldReplayRejectsOpenedBytesFieldArchiveAndSnapshotDrift() throws Exception {
        Fixture fixture = fixture(); ExactRef saved = preserve(fixture.input(), fixture.sources(Origin.EXTERNAL_CAPTURE, Optional.of(fixture.boundary())), fixture.store());
        for (ExactRef target : List.of(fixture.files().getFirst().originalBytes(), fixture.boundary().mountTable(), fixture.boundary().payloadAfter())) {
            byte[] before = fixture.store().load(target); fixture.store().contents.put(target.path(), bytes("drift"));
            assertThrows(IllegalArgumentException.class, () -> replay(saved, fixture.store())); fixture.store().contents.put(target.path(), before);
        }
        Envelope old = decode(fixture.store().load(saved));
        ExactRef changed = fixture.store().preserve(bytes("{}"));
        Envelope wrong = new Envelope(old.sources(), new NativeOnActionFieldArchive.Recorded(old.fieldArchive().original(), changed));
        ExactRef wrongRef = fixture.store().preserve(encode(wrong));
        assertThrows(IllegalArgumentException.class, () -> replay(wrongRef, fixture.store()));
    }

    @Test void codecRejectsMissingNullUnknownFieldsAndIntegerCoercion() throws Exception {
        Fixture fixture = fixture(); ExactRef saved = preserve(fixture.input(), fixture.sources(Origin.SOFTWARE_FIXTURE, Optional.empty()), fixture.store());
        byte[] valid = fixture.store().load(saved); ObjectNode root = json(valid); root.remove("boundary"); rejects(root);
        root = json(valid); root.putNull("opened_files"); rejects(root);
        root = json(valid); root.put("unreviewed", true); rejects(root);
        root = json(valid); file(root).put("ordinal", true); rejects(root);
        root = json(valid); file(root).put("ordinal", 0.0); rejects(root);
        root = json(valid); piece(root).put("offset", "7"); rejects(root);
        root = json(valid); piece(root).put("block", 0.0); rejects(root);
        root = json(valid); file(root).put("native_path_hex", "00"); rejects(root);
        root = json(valid); root.put("origin", "READY"); rejects(root);
        root = json(valid); root.put("exe_sha256", "0".repeat(64)); rejects(root);
        assertThrows(IllegalArgumentException.class, () -> new Sources(MACHINE, TIME, Origin.SOFTWARE_FIXTURE,
                List.of(new OpenedFile(1, "61", fixture.files().getFirst().originalBytes(), List.of())), Optional.empty()));
    }

    private record Fixture(MemoryStore store, Input input, List<OpenedFile> files, Boundary boundary) {
        Sources sources(Origin origin, Optional<Boundary> selected) { return new Sources(MACHINE, TIME, origin, files, selected); }
    }
    private static Fixture fixture() {
        MemoryStore store = new MemoryStore(); ExactRef observed = store.preserve(bytes("original independent observation fixture"));
        String event = "source-piece-event", action = "source-piece-action";
        ExactRef eventPiece = store.preserve(bytes(event)), actionPiece = store.preserve(bytes(action));
        // These bytes test custody only. They are not a native script parser or actual loaded input claim.
        ExactRef eventFile = store.preserve(bytes("prefix\n" + event + "\ntrailing")), actionFile = store.preserve(bytes(action + "\n"));
        var name = new NativeOnActionNameIndex.Name("child"); long hash = NativeOnActionNameIndex.hash(name);
        var table = new NativeOnActionNameIndex.Table(EXE, List.of(new NativeOnActionNameIndex.Entry(name, ACTION, hash)), List.of(hash));
        Input input = new Input(EXE, observed, List.of(new Block(Field.EVENTS_0270, eventPiece,
                List.of(new EventReference(new NativeOnActionNameIndex.Name("event"), Optional.of(new EventTarget(EVENT, EVENT_SIGNATURE, 0))))),
                new Block(Field.ACTIONS_02B8, actionPiece, List.of(new ActionReference(name)))), table, 0,
                List.of(new Predicate(Field.EVENTS_0270, 0, EVENT, true), new Predicate(Field.ACTIONS_02B8, 0, ACTION, true)),
                new RandomState(7, 123), new RandomState(99, 456));
        List<OpenedFile> files = List.of(new OpenedFile(0, HexFormat.of().formatHex(bytes("B.txt")), eventFile, List.of(new Piece(0, 7))),
                new OpenedFile(1, HexFormat.of().formatHex(bytes("a.txt")), actionFile, List.of(new Piece(1, 0))));
        ExactRef mounts = store.preserve(bytes("original mount snapshot")), rules = store.preserve(bytes("original replace rules"));
        ExactRef vfs1 = store.preserve(bytes("original vfs selection bytes")), vfs2 = store.preserve(bytes("original vfs selection bytes"));
        ExactRef payload1 = store.preserve(bytes("original loaded payload bytes")), payload2 = store.preserve(bytes("original loaded payload bytes"));
        return new Fixture(store, input, files, new Boundary(mounts, rules, vfs1, vfs2, payload1, payload2));
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode json(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, MAX_BYTES); }
    private static ObjectNode file(ObjectNode root) { return (ObjectNode) root.withArray("opened_files").get(0); }
    private static ObjectNode piece(ObjectNode root) { return (ObjectNode) ((ArrayNode) file(root).get("pieces")).get(0); }
    private static void rejects(ObjectNode root) { assertThrows(IllegalArgumentException.class, () -> decode(bytes(root.toString()))); }
    private static final class MemoryStore implements NativeOnActionFieldArchive.Store {
        private final Map<String, byte[]> contents = new HashMap<>(); private int sequence;
        @Override public ExactRef preserve(byte[] raw) {
            try {
                String path = "memory/" + sequence++; byte[] exact = raw.clone(); contents.put(path, exact);
                return new ExactRef(path, exact.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(exact)));
            } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        }
        @Override public byte[] load(ExactRef ref) throws IOException {
            byte[] raw = contents.get(ref.path()); if (raw == null) throw new IOException("original is unavailable"); return raw.clone();
        }
    }
}
