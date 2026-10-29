package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;

final class RootRestorationMaterialWitnessTest {
    @TempDir Path temporary;
    private ExactRef ref(String name) {return new ExactRef(temporary.resolve(name).toString(),5,"a".repeat(64));}
    @Test void retainedOriginalJsonRoundTripPreservesExactMaterialIdentity() {
        var witness=new CheckpointPair.FileWitness(ref("controlled-material"),
                new FileStatIdentity(BigInteger.valueOf(5),"18446744073709551615","1792800000000000000"));
        var original=StrictJson.object();original.put("schema","xar.java.restoration-domain-originals/v3");
        original.put("saved_material_kind",SavedCheckpointMaterial.Kind.ORDINARY.name());
        original.set("saved_material_witness",CheckpointPairCodec.fileWitnessToJson(witness));
        var sources=new SavedAttachmentSourceStore.Sources(SavedCheckpointMaterial.Kind.ORDINARY,witness,
                ref("basis"),ref("game"),ref("opening"),ref("progress"),ref("restored-native")).toJson();
        var typed=SavedAttachmentSourceStore.Sources.decode(StrictJson.parse(StrictJson.canonical(sources)));
        assertEquals(new RootRestorationOriginalProof.MaterialIdentity(SavedCheckpointMaterial.Kind.ORDINARY,witness),RootRestorationOriginalProof.requireMaterialIdentity(
                StrictJson.parse(StrictJson.canonical(original)),typed));
        var changed=original.deepCopy();changed.withObject("saved_material_witness").withObject("identity").put("file_id","18446744073709551614");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(changed,typed));
        var legacy=original.deepCopy();legacy.put("schema","xar.java.restoration-domain-originals/v1");
        legacy.remove("saved_material_witness");legacy.set("saved_material",witness.reference().toJson());
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(legacy,typed));
        var missing=original.deepCopy();missing.withObject("saved_material_witness").remove("identity");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(missing,typed));
        var rounded=original.deepCopy();rounded.withObject("saved_material_witness").withObject("identity").put("file_id",18446744073709551614d);
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(rounded,typed));
        var v2=original.deepCopy();v2.put("schema","xar.java.restoration-domain-originals/v2");v2.remove("saved_material_kind");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(v2,typed));
        var first=original.deepCopy();first.put("saved_material_kind",SavedCheckpointMaterial.Kind.FIRST_BASELINE.name());
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(first,typed));
        var firstSources=sources.deepCopy();firstSources.put("material_kind",SavedCheckpointMaterial.Kind.FIRST_BASELINE.name());
        assertEquals(new RootRestorationOriginalProof.MaterialIdentity(SavedCheckpointMaterial.Kind.FIRST_BASELINE,witness),
                RootRestorationOriginalProof.requireMaterialIdentity(StrictJson.parse(StrictJson.canonical(first)),
                        SavedAttachmentSourceStore.Sources.decode(StrictJson.parse(StrictJson.canonical(firstSources)))));
        var unknown=first.deepCopy();unknown.put("saved_material_kind","first");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(unknown,SavedAttachmentSourceStore.Sources.decode(firstSources)));
        var noKind=first.deepCopy();noKind.remove("saved_material_kind");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(noKind,SavedAttachmentSourceStore.Sources.decode(firstSources)));
        var nullKind=first.deepCopy();nullKind.putNull("saved_material_kind");
        assertThrows(IllegalArgumentException.class,()->RootRestorationOriginalProof.requireMaterialIdentity(nullKind,SavedAttachmentSourceStore.Sources.decode(firstSources)));
        var wrongSource=sources.deepCopy();wrongSource.put("material_kind",1);
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.Sources.decode(wrongSource));
        var missingSource=sources.deepCopy();missingSource.remove("restored_native");
        assertThrows(IllegalArgumentException.class,()->SavedAttachmentSourceStore.Sources.decode(missingSource));
    }
}
