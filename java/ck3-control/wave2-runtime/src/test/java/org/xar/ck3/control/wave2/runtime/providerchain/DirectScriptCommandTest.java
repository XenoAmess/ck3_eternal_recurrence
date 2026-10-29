package org.xar.ck3.control.wave2.runtime.providerchain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.DirectScriptCommand.ResolvedOperand;
import static org.junit.jupiter.api.Assertions.*;

final class DirectScriptCommandTest {
    @Test void allOriginalInterpreterModesAndRejectionsMatchTheOriginalProducer() throws IOException {
        JsonNode golden = ProviderChainManifestTest.golden();
        String entry = golden.get("frozen_entry").textValue();
        for (JsonNode sample : golden.get("command_cases")) {
            if (sample.get("expected_accept").booleanValue()) {
                DirectScriptCommand command = ProviderChainCodec.parseCommand(sample.get("argv"));
                int index = sample.get("expected_index").intValue();
                assertEquals(index, command.scriptOperandIndex());
                DirectScriptCommand.Inspection actual = command.inspect(entry,
                        new ResolvedOperand(index, command.argv().get(index), sample.get("resolved_operand").textValue()));
                assertEquals(index, actual.scriptOperandIndex()); assertFalse(actual.grantsProcessOrProviderQualification());
            } else {
                assertThrows(ContractViolationException.class, () -> {
                    DirectScriptCommand command = ProviderChainCodec.parseCommand(sample.get("argv"));
                    int index = command.scriptOperandIndex();
                    command.inspect(entry, new ResolvedOperand(index, command.argv().get(index), command.argv().get(index)));
                }, sample.get("argv").toString());
            }
        }
    }

    @Test void resolvedOperandMustBelongToTheSameCommandIndexAndExactFrozenEntry() throws IOException {
        JsonNode golden = ProviderChainManifestTest.golden();
        DirectScriptCommand command = ProviderChainCodec.parseCommand(golden.get("command_cases").get(0).get("argv"));
        int index = command.scriptOperandIndex(); String entry = golden.get("frozen_entry").textValue();
        assertThrows(ContractViolationException.class, () -> command.inspect(entry, null));
        assertThrows(ContractViolationException.class, () -> command.inspect(entry, new ResolvedOperand(index + 1, entry, entry)));
        assertThrows(ContractViolationException.class, () -> command.inspect(entry, new ResolvedOperand(index, "D:/other.py", entry)));
        assertThrows(ContractViolationException.class, () -> command.inspect(entry, new ResolvedOperand(index, entry, "D:/other.py")));
    }

    @Test void commandArgumentsKeepEmptyScriptValuesAndRemainDetached() throws IOException {
        JsonNode golden = ProviderChainManifestTest.golden(); String entry = golden.get("frozen_entry").textValue();
        List<String> source = new ArrayList<>(List.of("C:/Python/python.exe", entry, "", "-c", "script-value"));
        DirectScriptCommand command = new DirectScriptCommand(source); source.clear();
        assertEquals("", command.argv().get(2)); assertEquals(1, command.scriptOperandIndex());
        assertThrows(UnsupportedOperationException.class, () -> command.argv().clear());
    }

    @Test void rawCommandBoundaryRejectsNonTextAndWrongRootShapes() {
        for (String wire : List.of("null", "{}", "true", "[]", "[\"C:/Python/python.exe\",true]",
                "[\"C:/Python/python.exe\",1.0]", "[\"C:/Python/python.exe\",null]")) {
            assertThrows(ContractViolationException.class,
                    () -> ProviderChainCodec.parseCommand(StrictJson.parse(wire.getBytes(StandardCharsets.UTF_8))));
        }
        ArrayNode command = StrictJson.object().putArray("args"); command.add("relative-python.exe"); command.add("D:/entry.py");
        assertThrows(ContractViolationException.class, () -> ProviderChainCodec.parseCommand(command));
    }
}
