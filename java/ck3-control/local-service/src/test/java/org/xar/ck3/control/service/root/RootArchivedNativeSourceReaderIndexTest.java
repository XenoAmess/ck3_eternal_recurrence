package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootArchivedNativeSourceReader.EpochData;
import org.xar.ck3.control.service.root.RootArchivedNativeSourceReader.EpochInput;
import org.xar.ck3.control.service.root.RootArchivedNativeSourceReader.EpochRole;

/** Synthetic historical DATA only: no files, source custody, guard or current Root authority. */
final class RootArchivedNativeSourceReaderIndexTest {
    private static final String BASE = "c:/reader-index-data/";
    private static final String MACHINE = "reader-index-data";
    private static final String SOURCE_SHA = DriverJson.sha256(new byte[] {1});
    private static final String OTHER_SHA = DriverJson.sha256(new byte[] {2});
    private static final String NO_WITNESS = "archived source role lacks its actual persisted native witness";
    private static final List<EpochInput> INPUTS = List.of(
            input(EpochRole.BRIDGE_DLL, "bridge.dll"),
            input(EpochRole.GAME_EXECUTABLE, "game.exe"),
            input(EpochRole.INJECTOR, "injector.exe"),
            input(EpochRole.JAVA_RUNTIME, "runtime.jar"),
            input(EpochRole.LAUNCHER_SETTINGS, "launcher.json"),
            input(EpochRole.NATIVE_SOURCE, "native.cpp"));

    @Test
    void acceptsWitnessesWithEquivalentCaseAndSlashSpelling() {
        EpochData data = read(INPUTS, witnesses());
        assertEquals(MACHINE, data.machineId());
        assertEquals(INPUTS, data.inputs());
    }

    @Test
    void rejectsMismatchMissingAndDuplicateDataAtTheirFirstPublicCheck() {
        List<SourceWitness> witnesses = witnesses();
        ExactRef bridge = INPUTS.getFirst().source();
        rejects(NO_WITNESS, changedFirst(new ExactRef(bridge.path(), bridge.bytes() + 1, bridge.sha256())), witnesses);
        rejects(NO_WITNESS, changedFirst(new ExactRef(bridge.path(), bridge.bytes(), OTHER_SHA)), witnesses);
        rejects(NO_WITNESS, changedFirst(new ExactRef(BASE + "missing.dll", bridge.bytes(), bridge.sha256())), witnesses);

        // The producer-normalized path check precedes a simultaneous witness mismatch.
        rejects("original epoch path is not the producer's normalized path",
                changedFirst(new ExactRef("C:\\READER-INDEX-DATA\\BRIDGE.DLL", bridge.bytes() + 1, OTHER_SHA)), witnesses);

        // A repeated role/path key must fail before its conflicting bytes/SHA are compared.
        List<EpochInput> duplicateInputs = new ArrayList<>(INPUTS);
        duplicateInputs.add(1, new EpochInput(EpochRole.BRIDGE_DLL,
                new ExactRef(bridge.path(), bridge.bytes() + 1, OTHER_SHA)));
        rejects("original epoch inputs are duplicated or outside the producer's exact order", duplicateInputs, witnesses);

        // Public proof construction rejects this before the reader; its private duplicate branch is unreachable here.
        List<SourceWitness> duplicateWitnesses = new ArrayList<>(witnesses);
        duplicateWitnesses.add(new SourceWitness(bridge, witnesses.getFirst().nativeFile()));
        rejects("duplicate physical source Witness path", INPUTS, duplicateWitnesses);
    }

    private static EpochInput input(EpochRole role, String file) {
        return new EpochInput(role, source(file));
    }

    private static ExactRef source(String file) {
        return new ExactRef(BASE + file, 1, SOURCE_SHA);
    }

    private static List<SourceWitness> witnesses() {
        // All references describe synthetic one-byte DATA; no native identity is sampled or qualified.
        var nativeFile = new NativeSourceFileIdentity("1", "1", "1", "0000000000000001", "1", "1", "1", 1, 1, 1);
        List<SourceWitness> result = new ArrayList<>();
        for (EpochInput input : INPUTS) {
            ExactRef source = input.source();
            ExactRef spelling = new ExactRef(source.path().toUpperCase(Locale.ROOT).replace('/', '\\'),
                    source.bytes(), source.sha256());
            result.add(new SourceWitness(spelling, nativeFile));
        }
        return result;
    }

    private static List<EpochInput> changedFirst(ExactRef source) {
        List<EpochInput> changed = new ArrayList<>(INPUTS);
        changed.set(0, new EpochInput(EpochRole.BRIDGE_DLL, source));
        return changed;
    }

    private static EpochData read(List<EpochInput> inputs, List<SourceWitness> witnesses) {
        var epoch = StrictJson.object().put("schema", "xar.java-root-source-epoch/v1").put("machine_id", MACHINE);
        var rows = epoch.putArray("inputs");
        for (EpochInput input : inputs) {
            var row = rows.addObject().put("role", input.role().wire());
            row.set("source", input.source().toJson());
        }
        byte[] original = FullJsonTree.encode(epoch, RootArchivedNativeSourceReader.MAXIMUM_SOURCE_BYTES);
        ExactRef manifest = new ExactRef(BASE + "epoch.json", original.length, DriverJson.sha256(original));
        var proof = new NativeSourceProofDocument(MACHINE, "reader-index-session", "2026-11-03T00:00:00Z",
                NativeSourceProofDocument.Mode.HTTP, INPUTS.get(3).source(), source("snapshot.packet"),
                manifest.sha256(), manifest, INPUTS.get(1).source(),
                INPUTS.stream().map(EpochInput::source).toList(), witnesses);
        return RootArchivedNativeSourceReader.readEpochData(manifest, original, proof);
    }

    private static void rejects(String message, List<EpochInput> inputs, List<SourceWitness> witnesses) {
        RuntimeException failure = assertThrows(RuntimeException.class, () -> read(inputs, witnesses));
        assertEquals(message, failure.getMessage());
    }
}
