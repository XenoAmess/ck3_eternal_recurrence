package org.xar.ck3.control.wave2.events.interactionregistry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry.*;

class InteractionRegistryTest {
    @TempDir Path temporary;
    private static final String RESOURCE = "/interactionregistry/legacy-producer-golden-v1.json";

    @Test void actualLegacyProducerAndReaderCasesRequireActualFileValidation() throws IOException {
        JsonNode golden = golden(); assertEquals(16, golden.get("cases").size());
        for (JsonNode row : golden.get("cases")) {
            String name = row.get("name").textValue(); Fixture fixture = materialize(name); Lookup lookup = fixture.lookup();
            if (name.equals("hash_bool") || name.equals("hash_float")) {
                String wire = new String(InteractionRegistryCodec.encodeLookup(lookup), StandardCharsets.UTF_8)
                        .replace("\"deterministic_key_hash\":12", "\"deterministic_key_hash\":" + (name.equals("hash_bool") ? "true" : "12.0"));
                assertTrue(wire.contains(name.equals("hash_bool") ? ":true" : ":12.0"));
                assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseLookup(wire.getBytes(StandardCharsets.UTF_8)));
                assertFalse(row.get("expected_known").booleanValue()); continue;
            }
            switch (name) {
                case "build" -> lookup = new Lookup(new BuildIdentity("1.20.0.5", lookup.build().exeSha256()), lookup.definition(), lookup.guiSha256());
                case "exe_sha" -> lookup = new Lookup(new BuildIdentity(lookup.build().version(), "b".repeat(64)), lookup.definition(), lookup.guiSha256());
                case "hash" -> lookup = new Lookup(lookup.build(), new Definition(lookup.definition().canonicalKey(), 13), lookup.guiSha256());
                case "gui_pin" -> lookup = new Lookup(lookup.build(), lookup.definition(), "0".repeat(64));
                case "source_changed" -> Files.writeString(fixture.source(), golden.get("source_utf8").textValue() + "\n# changed");
                case "gui_changed" -> Files.writeString(fixture.gui(), golden.get("gui_utf8").textValue() + " changed");
                case "facts_changed" -> Files.writeString(fixture.facts(), "{}");
                case "entry_fingerprint" -> mutateEntry(fixture, "fingerprint", "0".repeat(64));
                case "entry_schema" -> mutateEntry(fixture, "schema", "bad-schema");
                case "classification" -> mutateEntry(fixture, "classification", "reviewed=true");
                case "preferred_action" -> mutateEntry(fixture, "preferred_action", "accept");
                case "facts_schema" -> { ObjectNode facts = json(fixture.facts()); facts.put("schema", "bad-schema"); rewriteFacts(fixture, facts); }
                case "facts_receipt_sha" -> { ObjectNode entry = json(fixture.entry()); ((ObjectNode) entry.get("source_facts")).put("sha256", "0".repeat(64)); write(fixture.entry(), entry); }
                case "known" -> { }
                default -> throw new AssertionError(name);
            }
            Result actual = new InteractionRegistryReader().load(fixture.roots(), lookup);
            assertEquals(row.get("expected_known").booleanValue(), actual instanceof Known, name);
            if (actual instanceof Known known) {
                assertEquals(row.get("legacy_audit").get("fingerprint").textValue(), known.review().audit().fingerprint());
                assertEquals(CLASSIFICATION, known.review().entry().classification());
                assertFalse(known.review().materialEffectsVerified()); assertFalse(known.review().nativeAiEquivalent()); assertFalse(known.review().replayAllowed());
            }
        }
    }

    @Test void originalEntryAndFactsRetainSourceDigestsAndRoundTrip() throws IOException {
        JsonNode golden = golden(); byte[] entryRaw = utf8(golden.get("entry_utf8").textValue()); byte[] factsRaw = utf8(golden.get("facts_utf8").textValue());
        assertEquals(golden.get("entry_sha256").textValue(), InteractionRegistryCodec.digest(entryRaw));
        assertEquals(golden.get("facts_sha256").textValue(), InteractionRegistryCodec.digest(factsRaw));
        Entry entry = InteractionRegistryCodec.parseEntry(entryRaw); Facts facts = InteractionRegistryCodec.parseFacts(factsRaw);
        assertEquals(entry, InteractionRegistryCodec.parseEntry(InteractionRegistryCodec.encodeEntry(entry)));
        assertEquals(facts, InteractionRegistryCodec.parseFacts(InteractionRegistryCodec.encodeFacts(facts)));
        assertEquals(entry.fingerprint(), InteractionRegistryCodec.fingerprint(entry.binding()));
        assertEquals(entry.binding(), facts.binding());
        assertEquals(entry.binding().sourceSha256(), InteractionRegistryCodec.digest(utf8(golden.get("source_utf8").textValue())));
        assertEquals(entry.binding().guiSha256(), InteractionRegistryCodec.digest(utf8(golden.get("gui_utf8").textValue())));
        assertTrue(facts.onAccept().contains("add_stress = 10")); assertTrue(facts.onDecline().contains("add_piety = -5"));
        assertThrows(UnsupportedOperationException.class, () -> facts.category().clear());
    }

    @Test void sameLengthAndTimestampContentReplacementCannotReuseCachedKnown() throws IOException {
        Fixture fixture = materialize("same-stamp"); InteractionRegistryReader reader = new InteractionRegistryReader();
        assertInstanceOf(Known.class, reader.load(fixture.roots(), fixture.lookup()));
        FileTime originalTime = Files.getLastModifiedTime(fixture.source()); byte[] bytes = Files.readAllBytes(fixture.source());
        bytes[0] = bytes[0] == 'x' ? (byte) 'y' : (byte) 'x'; Files.write(fixture.source(), bytes); Files.setLastModifiedTime(fixture.source(), originalTime);
        assertInstanceOf(Unknown.class, reader.load(fixture.roots(), fixture.lookup()));
    }

    @Test void fakeReviewFlagsUnknownFieldsAndMaterialClaimsCannotGrantKnowledge() throws IOException {
        Fixture flagged = materialize("flags"); ObjectNode entry = json(flagged.entry()); entry.put("reviewed", true); write(flagged.entry(), entry);
        assertInstanceOf(Unknown.class, new InteractionRegistryReader().load(flagged.roots(), flagged.lookup()));
        Fixture material = materialize("material"); ObjectNode facts = json(material.facts()); facts.put("material_effects_verified", true); rewriteFacts(material, facts);
        assertInstanceOf(Unknown.class, new InteractionRegistryReader().load(material.roots(), material.lookup()));
    }

    @Test void filePathsMustStayInExplicitRootsAndMatchFacts() throws IOException {
        Fixture fixture = materialize("outside"); Path outside = temporary.resolve("outside-source.txt"); Files.writeString(outside, golden().get("source_utf8").textValue());
        mutateEntry(fixture, "source_path", outside.toAbsolutePath().toString());
        assertInstanceOf(Unknown.class, new InteractionRegistryReader().load(fixture.roots(), fixture.lookup()));
        Fixture drift = materialize("relative"); ObjectNode facts = json(drift.facts()); facts.put("source_relative", "../outside-source.txt"); rewriteFacts(drift, facts);
        assertInstanceOf(Unknown.class, new InteractionRegistryReader().load(drift.roots(), drift.lookup()));
        Fixture factsDrift = materialize("paths"); ObjectNode divergent = json(factsDrift.facts()); divergent.put("gui_path", outside.toString()); rewriteFacts(factsDrift, divergent);
        assertInstanceOf(Unknown.class, new InteractionRegistryReader().load(factsDrift.roots(), factsDrift.lookup()));
    }

    @Test void rawBooleanFloatMissingNullDuplicateAndWrongHashTypesAreRejected() throws IOException {
        Fixture fixture = materialize("types"); String valid = new String(InteractionRegistryCodec.encodeLookup(fixture.lookup()), StandardCharsets.UTF_8);
        for (String token : List.of("true", "12.0", "12e0", "\"12\"", "null", "-1", "4294967296")) {
            String wire = valid.replace("\"deterministic_key_hash\":12", "\"deterministic_key_hash\":" + token);
            assertTrue(wire.contains("\"deterministic_key_hash\":" + token));
            assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseLookup(utf8(wire)), token);
            String entryWire = Files.readString(fixture.entry()).replace("\"deterministic_key_hash\":12", "\"deterministic_key_hash\":" + token);
            String factsWire = Files.readString(fixture.facts()).replace("\"deterministic_key_hash\":12", "\"deterministic_key_hash\":" + token);
            assertTrue(entryWire.contains("\"deterministic_key_hash\":" + token)); assertTrue(factsWire.contains("\"deterministic_key_hash\":" + token));
            assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseEntry(utf8(entryWire)), token);
            assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseFacts(utf8(factsWire)), token);
        }
        ObjectNode missing = (ObjectNode) StrictJson.parse(utf8(valid)); ((ObjectNode) missing.get("definition")).remove("deterministic_key_hash");
        assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseLookup(utf8(missing.toString())));
        String duplicate = valid.replaceFirst("\\{", "{\"schema\":\"duplicate\",");
        assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseLookup(utf8(duplicate)));
        assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseEntry(new byte[] {(byte) 0xc0, (byte) 0xaf}));
        assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseEntry(new byte[InteractionRegistryCodec.MAX_ENTRY_BYTES + 1]));
        assertThrows(ContractViolationException.class, () -> InteractionRegistryCodec.parseFacts(new byte[InteractionRegistryCodec.MAX_FACTS_BYTES + 1]));
    }

    @Test void missingRegistryAndBoundedEnumerationReturnTypedUnknown() throws IOException {
        Fixture fixture = materialize("missing"); Roots absent = new Roots(temporary.resolve("no-state").toAbsolutePath(), fixture.roots().gameRoot());
        assertEquals(UnknownReason.NO_MATCH, ((Unknown) new InteractionRegistryReader().load(absent, fixture.lookup())).reason());
        Path directory = fixture.entry().getParent();
        for (int index = 0; index < 129; index++) { Files.writeString(directory.resolve(String.format("%064x.json", index)), "{}"); }
        assertEquals(UnknownReason.RESOURCE_LIMIT, ((Unknown) new InteractionRegistryReader().load(fixture.roots(), fixture.lookup())).reason());
    }

    @Test void nullableAuthoredEffectBlocksAndFullUint32HashKeepTheirDomains() throws IOException {
        Facts original = InteractionRegistryCodec.parseFacts(utf8(golden().get("facts_utf8").textValue()));
        Facts absent = new Facts(original.fingerprint(), original.binding(), original.paths(), original.sourceRelative(), List.of(), original.definition(), null, null, original.analysis());
        assertEquals(absent, InteractionRegistryCodec.parseFacts(InteractionRegistryCodec.encodeFacts(absent)));
        Definition maximum = new Definition("synthetic_key", 0xffff_ffffL); Fixture fixture = materialize("uint32");
        Lookup lookup = new Lookup(fixture.lookup().build(), maximum, fixture.lookup().guiSha256());
        assertEquals(lookup, InteractionRegistryCodec.parseLookup(InteractionRegistryCodec.encodeLookup(lookup)));
    }

    @Test void trustedOptionalEntryFactsSourceAndRegistryFailuresStayUnknownWithoutGrantingKnowledge() throws IOException {
        for(String fault:List.of("oversized_entry","missing_facts","missing_source","undeclared_facts","registry_directory")) {
            Fixture fixture=materialize("trusted-"+fault);
            var trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext("test-machine",fixture.roots().stateRoot(),fixture.roots().gameRoot()));
            switch(fault) {
                case "oversized_entry" -> Files.write(fixture.entry(),new byte[65_537]);
                case "missing_facts" -> Files.delete(fixture.facts());
                case "missing_source" -> Files.delete(fixture.source());
                case "undeclared_facts" -> {
                    Path historical=temporary.resolve("ungranted-facts.json");Files.copy(fixture.facts(),historical);
                    ObjectNode entry=json(fixture.entry());((ObjectNode)entry.get("source_facts")).put("path",historical.toString());write(fixture.entry(),entry);
                }
                case "registry_directory" -> {
                    Path directory=fixture.entry().getParent();Files.move(directory,directory.resolveSibling("old-registry"));
                    Files.writeString(directory,"optional registry is now a regular file");
                }
                default -> throw new AssertionError(fault);
            }
            Unknown result=assertInstanceOf(Unknown.class,new InteractionRegistryReader("test-machine").load(trusted,fixture.lookup()),fault);
            assertTrue(result.reason()==UnknownReason.REJECTED_ENTRY||result.reason()==UnknownReason.REGISTRY_UNAVAILABLE,fault);
            trusted.requireInteractionGui(fixture.lookup().guiSha256());
        }
    }

    @Test void typedObservedRootFailureRemainsRequiredAfterRestoreAndEveryLookupExitRechecksRootsAndGui() throws IOException {
        for(String rootName:List.of("state","stock")) {
            Fixture fixture=materialize("required-"+rootName);
            var trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext("test-machine",fixture.roots().stateRoot(),fixture.roots().gameRoot()));
            Path root=rootName.equals("state")?fixture.roots().stateRoot():fixture.roots().gameRoot(),moved=root.resolveSibling(root.getFileName()+"-original");
            Files.move(root,moved);Files.createDirectory(root);
            var observed=assertThrows(TrustedEventSourceContext.UnavailableException.class,()->trusted.readInteractionEntry(fixture.entry()));
            assertEquals(TrustedEventSourceContext.FailureKind.REQUIRED_SOURCE_UNAVAILABLE,observed.failureKind());
            assertThrows(TrustedEventSourceContext.UnavailableException.class,()->new InteractionRegistryReader("test-machine").load(trusted,fixture.lookup()));
            Files.delete(root);Files.move(moved,root);
            trusted.requireInteractionGui(fixture.lookup().guiSha256());
            assertEquals(TrustedEventSourceContext.FailureKind.REQUIRED_SOURCE_UNAVAILABLE,observed.failureKind(),"restoring a directory cannot reclassify an observed required failure");
            assertInstanceOf(Known.class,new InteractionRegistryReader("test-machine").load(trusted,fixture.lookup()));
        }
        Fixture gui=materialize("required-gui");
        var trusted=TrustedEventSourceContext.openEvidence(new EventSourceReadContext("test-machine",gui.roots().stateRoot(),gui.roots().gameRoot()));
        Files.delete(gui.entry());Files.writeString(gui.gui(),"different required GUI");
        var mismatch=assertThrows(TrustedEventSourceContext.UnavailableException.class,()->new InteractionRegistryReader("test-machine").load(trusted,gui.lookup()));
        assertEquals(TrustedEventSourceContext.FailureKind.REQUIRED_SOURCE_UNAVAILABLE,mismatch.failureKind());
    }

    private Fixture materialize(String name) throws IOException {
        JsonNode g = golden(); Path root = temporary.resolve(name); Path game = root.resolve("game").toAbsolutePath(); Path state = root.resolve("state").toAbsolutePath();
        Path source = game.resolve("common/character_interactions/synthetic.txt"); Path gui = game.resolve("gui/interaction_notification_window.gui");
        Files.createDirectories(source.getParent()); Files.createDirectories(gui.getParent()); Files.writeString(source, g.get("source_utf8").textValue()); Files.writeString(gui, g.get("gui_utf8").textValue());
        Entry oldEntry = InteractionRegistryCodec.parseEntry(utf8(g.get("entry_utf8").textValue())); Facts oldFacts = InteractionRegistryCodec.parseFacts(utf8(g.get("facts_utf8").textValue()));
        Path factsPath = state.resolve("evidence/interaction-source-registry/facts/" + oldEntry.fingerprint() + ".json"); Files.createDirectories(factsPath.getParent());
        SourcePaths paths = new SourcePaths(source.toString(), gui.toString());
        Facts facts = new Facts(oldFacts.fingerprint(), oldFacts.binding(), paths, oldFacts.sourceRelative(), oldFacts.category(), oldFacts.definition(), oldFacts.onAccept(), oldFacts.onDecline(), oldFacts.analysis());
        byte[] factsRaw = InteractionRegistryCodec.encodeFacts(facts); Files.write(factsPath, factsRaw);
        Entry entry = new Entry(oldEntry.fingerprint(), oldEntry.binding(), oldEntry.classification(), oldEntry.preferredAction(), paths,
                new SourceRef(factsPath.toString(), InteractionRegistryCodec.digest(factsRaw)), oldEntry.reason());
        Path entryPath = factsPath.getParent().getParent().resolve(entry.fingerprint() + ".json"); Files.write(entryPath, InteractionRegistryCodec.encodeEntry(entry));
        return new Fixture(new Roots(state, game), new Lookup(entry.binding().build(), entry.binding().definition(), entry.binding().guiSha256()), source, gui, factsPath, entryPath);
    }
    private static void mutateEntry(Fixture fixture, String field, String value) throws IOException { ObjectNode row = json(fixture.entry()); row.put(field, value); write(fixture.entry(), row); }
    private static void rewriteFacts(Fixture fixture, ObjectNode facts) throws IOException {
        write(fixture.facts(), facts); ObjectNode entry = json(fixture.entry()); ((ObjectNode) entry.get("source_facts")).put("sha256", InteractionRegistryCodec.digest(Files.readAllBytes(fixture.facts()))); write(fixture.entry(), entry);
    }
    private static ObjectNode json(Path path) throws IOException { return (ObjectNode) StrictJson.parse(Files.readAllBytes(path)); }
    private static void write(Path path, ObjectNode value) throws IOException { Files.write(path, utf8(value.toString())); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (var stream = InteractionRegistryTest.class.getResourceAsStream(RESOURCE)) { assertNotNull(stream, "committed actual-producer golden required"); return StrictJson.parse(stream.readAllBytes()); }
    }
    private record Fixture(Roots roots, Lookup lookup, Path source, Path gui, Path facts, Path entry) { }
}
