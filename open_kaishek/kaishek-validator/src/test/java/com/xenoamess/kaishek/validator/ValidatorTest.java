package com.xenoamess.kaishek.validator;

import com.xenoamess.kaishek.profile.Ck3Profile11906;
import com.xenoamess.kaishek.syntax.Parser;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class ValidatorTest {
    private static final Ck3Profile11906 PROFILE = new Ck3Profile11906();
    @Test void validEffectHasNoSchemaErrors() throws Exception {
        var p = Parser.parse(Files.readString(Path.of("src/test/resources/fixtures/valid_effects.txt")));
        var ds = Validator.validate(p, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(ds.stream().noneMatch(d -> d.severity() == Diagnostic.Severity.ERROR), ds::toString);
    }
    @Test void mutationProducesStrictDiagnostics() throws Exception {
        var p = Parser.parse(Files.readString(Path.of("src/test/resources/fixtures/invalid_effects.txt")));
        var codes = Validator.validate(p, "common/scripted_effects/xar.txt", PROFILE).stream().map(Diagnostic::code).toList();
        assertTrue(codes.contains("DUPLICATE_KEY"));
        assertTrue(codes.contains("UNKNOWN_OPCODE"));
        assertTrue(codes.contains("WRONG_DOMAIN"));
    }

    @Test void profileApiOverloadPreservesParserDiagnostics() {
        var parsed = Parser.parse("broken = { value = 1".getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE.gameProfile());
        assertTrue(diagnostics.stream().anyMatch(d -> d.code().equals("UNCLOSED_BLOCK")), diagnostics::toString);
    }

    @Test void guiDeclarationHeadersDoNotBecomeUnknownOpcodes() {
        String source = "types ZG361ScoreboardTypes {\n"
                + "  blockoverride \"header_text\" { text = \"title\" }\n"
                + "}\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        assertTrue(parsed.diagnostics().isEmpty(), () -> parsed.diagnostics().toString());
        var diagnostics = Validator.validate(parsed, "gui/zg361_scoreboard.gui", PROFILE);
        assertTrue(diagnostics.stream().noneMatch(d -> d.code().equals("UNKNOWN_OPCODE")), diagnostics::toString);
    }

    @Test void gameProfileAdapterKeepsEventEffectDomain() {
        String source = "trigger_event = { id = test_event days = 1 }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_triggers/xar.txt",
                PROFILE.gameProfile());
        assertTrue(diagnostics.stream().anyMatch(d -> d.code().equals("WRONG_DOMAIN")),
                diagnostics::toString);
    }

    @Test void gameProfileAdapterKeepsOptionalParameterArity() {
        String source = "set_variable = { name = sample }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt",
                PROFILE.gameProfile());
        assertTrue(diagnostics.stream().noneMatch(d -> d.code().equals("INVALID_PARAMETERS")),
                diagnostics::toString);
    }

    @Test void registeredOpcodeChecksDeclaredScope() {
        String source = "set_character_flag = { scope = TITLE flag = sample }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(diagnostics.stream().anyMatch(d -> d.code().equals("INVALID_SCOPE")),
                diagnostics::toString);
    }

    @Test void registeredOpcodeRejectsUnknownParameterName() {
        String source = "set_variable = { bogus = sample }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(diagnostics.stream().anyMatch(d -> d.code().equals("INVALID_PARAMETERS")),
                diagnostics::toString);
    }

    @Test void observedCk3ParameterFormsAreNotRejected() {
        String source = "change_variable = { name = sample add = 1 }\n"
                + "trigger_event = { id = test_event days = 1 }\n"
                + "add_prestige = { value = 0 subtract = 100 }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(diagnostics.stream().noneMatch(d -> d.code().equals("INVALID_PARAMETERS")),
                diagnostics::toString);
    }

    @Test void repeatedCk3ParameterKeysRemainOrderedInput() {
        String source = "set_variable = { name = sample value = 1 value = 2 }\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(diagnostics.stream().noneMatch(d -> d.code().equals("DUPLICATE_KEY")),
                diagnostics::toString);
    }

    @Test void repeatedExecutableOpcodesRemainOrderedInput() {
        String source = "wrapper = {\n"
                + "  set_variable = { name = first value = 1 }\n"
                + "  set_variable = { name = second value = 2 }\n"
                + "}\n";
        var parsed = Parser.parse(source.getBytes(StandardCharsets.UTF_8));
        var diagnostics = Validator.validate(parsed, "common/scripted_effects/xar.txt", PROFILE);
        assertTrue(diagnostics.stream().noneMatch(d -> d.code().equals("DUPLICATE_KEY")),
                diagnostics::toString);
    }
}
