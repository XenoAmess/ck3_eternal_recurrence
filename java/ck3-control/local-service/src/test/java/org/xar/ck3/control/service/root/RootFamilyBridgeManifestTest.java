package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.*;
import org.junit.jupiter.api.Test;

final class RootFamilyBridgeManifestTest {

    @Test void canonicalFamilyManifestGameKeepsItsOriginalGameBinding() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        
        // Verify strict typed comparison works
        assertEquals(game, GameGeneration.fromJson(read.get("game")));
        assertTrue(RootFamilyBridge.matchesPersistedGame(read.get("game"), game),
                "RootFamilyBridge.replay must accept the persisted Game from its current producer");
                
        // Verify old raw predicate fails (negative control)
        assertFalse(read.get("game").equals(game.toJson()),
                "Raw node equality must fail due to LongNode vs BigIntegerNode type mismatch");
    }

    @Test void rejectsChangedPid() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        gameNode.put("pid", 43L); // Change PID
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }

    @Test void rejectsChangedBirth() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        gameNode.put("creation_filetime", "134000000000000002"); // Change birth
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }

    @Test void rejectsInvalidPidTypes() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        
        var booleanExpected = new GameGeneration(1, game.creationFiletime());
        assertFalse(RootFamilyBridge.matchesPersistedGame(booleanExpected.toJson().put("pid", true), booleanExpected));

        gameNode.put("pid", true);
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.put("pid", 42.0);
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.put("pid", "42");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.putNull("pid");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.remove("pid");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }

    @Test void rejectsInvalidCreationFiletimeTypes() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        
        gameNode.put("creation_filetime", 134000000000000001L); // Numeric instead of string
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.put("creation_filetime", "0" + game.creationFiletime().value()); // Non-canonical string
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.putNull("creation_filetime");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.remove("creation_filetime");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }

    @Test void rejectsExtraFields() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        gameNode.put("extra_field", "value");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }

    @Test void rejectsFieldArraysAndObjects() {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var manifest = StrictJson.object().put("schema", RootFamilyBridge.SCHEMA);
        manifest.set("game", game.toJson());
        var read = StrictJson.parse(StrictJson.canonical(manifest));
        var gameNode = (ObjectNode) read.get("game");
        
        gameNode.set("pid", StrictJson.object());
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        
        gameNode.putArray("pid");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        gameNode.put("pid", game.pid());
        gameNode.putObject("creation_filetime");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
        gameNode.putArray("creation_filetime");
        assertFalse(RootFamilyBridge.matchesPersistedGame(gameNode, game));
    }
}