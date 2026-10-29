package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

final class ConstructionRestoreProvenanceTest {
    @Test void completeProducerMetadataRoundTripsWithoutChangingOriginalFieldNamesOrFiletimePrecision() {
        var actual = actual();
        Obj serialized = object(parse(encode(actual.toJson())), "actual restore metadata round trip");
        assertEquals(actual, ConstructionRestoreProvenance.decode(serialized));
        assertEquals(new Text("18446744073709551615"), object(serialized.get("replacement_game"), "replacement Game").get("creation_filetime"));
        assertEquals(actual.toJson(), serialized);
    }
    @Test void missingNullUnknownAndWrongTypedOriginalMetadataAreRejected() {
        Obj original = actual().toJson();
        for (String field : original.members().keySet()) {
            var missing = new LinkedHashMap<String,Value>(original.members()); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(new Obj(missing)), field);
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with(field, Nil.INSTANCE)), field);
        }
        assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with("unregistered_sidecar", new Text("path-only"))));
        for (String field : java.util.List.of("saved_head_sequence", "saved_actor_character_id")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with(field, new Bool(true))));
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with(field, parse("1.0".getBytes(java.nio.charset.StandardCharsets.UTF_8)))));
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with(field, new Text("1"))));
            assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with(field, new IntegerValue(new BigInteger("9007199254740992")))));
        }
        assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with("saved_actor_character_id", new IntegerValue(BigInteger.ZERO))));
        Obj game = object(original.get("replacement_game"), "replacement Game").with("creation_filetime", new IntegerValue(new BigInteger("18446744073709551615")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionRestoreProvenance.decode(original.with("replacement_game", game)));
    }
    private static ConstructionRestoreProvenance actual() {
        return new ConstructionRestoreProvenance(ref("restore", "a"), ref("material", "b"), ref("body", "c"),
                7, "d".repeat(64), "actual-saved-episode", BigInteger.valueOf(42),
                new GameGeneration(43, new PythonOnlyUInt64(new BigInteger("18446744073709551615"))), "actual-replacement-session");
    }
    private static ExactRef ref(String name, String digest) { return new ExactRef("D:/fixture/" + name + ".json", 2, digest.repeat(64)); }
}
