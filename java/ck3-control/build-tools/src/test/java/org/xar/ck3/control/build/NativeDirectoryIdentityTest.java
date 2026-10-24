package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class NativeDirectoryIdentityTest {
    @TempDir Path temporary;
    @Test void actualDirectoryIdentitySurvivesChildWritesAndRetainsDecimalKernelTypes() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("owned"));
        var before = SharedSourceFiles.nativeDirectory(root);
        Files.writeString(root.resolve("payload.json"), "{}");
        assertEquals(before, SharedSourceFiles.nativeDirectory(root));
        assertTrue(before.fileIdDecimal().matches("0|[1-9][0-9]*"));
        String u64 = "18446744073709551615", u128 = "340282366920938463463374607431768211455";
        var maximum = new SharedSourceFiles.DirectoryIdentity(u64, u128, u64);
        com.fasterxml.jackson.databind.node.ObjectNode json = ControlBuild.strictMapper().valueToTree(maximum);
        assertTrue(json.path("volume_serial_decimal").isTextual()); assertEquals(u64, json.path("volume_serial_decimal").textValue());
        assertTrue(json.path("file_id_decimal").isTextual()); assertEquals(u128, json.path("file_id_decimal").textValue());
        assertEquals(maximum, ControlBuild.strictMapper().treeToValue(json, SharedSourceFiles.DirectoryIdentity.class));
        var extra = json.deepCopy(); extra.put("file_id", "1");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(extra, SharedSourceFiles.DirectoryIdentity.class));
        var missing = json.deepCopy(); missing.remove("creation_filetime_decimal");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(missing, SharedSourceFiles.DirectoryIdentity.class));
        for (com.fasterxml.jackson.databind.JsonNode invalid : java.util.List.of(
                com.fasterxml.jackson.databind.node.NullNode.instance,
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                com.fasterxml.jackson.databind.node.LongNode.valueOf(9_007_199_254_740_991L),
                com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0))) {
            var changed = json.deepCopy(); changed.set("creation_filetime_decimal", invalid);
            assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(changed, SharedSourceFiles.DirectoryIdentity.class));
        }
        for (String invalid : new String[]{null, "", "01", "-1", "+1", "1.0", "1e0", "true", "18446744073709551616"}) {
            assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.DirectoryIdentity(invalid, "1", "1"));
            assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.DirectoryIdentity("1", "1", invalid));
        }
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.DirectoryIdentity("1", "340282366920938463463374607431768211456", "1"));
    }
    @Test void replacedDirectoryAtTheSamePathCannotReuseItsOriginalIdentity() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("owned"));
        var before = SharedSourceFiles.nativeDirectory(root);
        var modified = Files.getLastModifiedTime(root);
        Files.move(root, temporary.resolve("retired"));
        Files.createDirectory(root);
        Files.setLastModifiedTime(root, modified);
        assertNotEquals(before, SharedSourceFiles.nativeDirectory(root));
    }
    @Test void nativeFileAndDirectoryBoundariesRejectTheOtherEntryTypeAndMissingPaths() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("owned"));
        Path file = Files.writeString(root.resolve("payload.json"), "{}");
        var nativeFile = SharedSourceFiles.nativeFile(file);
        assertEquals(Files.size(file), nativeFile.logicalBytes());
        assertEquals(nativeFile, SharedSourceFiles.nativeFile(file));
        var maximum = new SharedSourceFiles.NativeFile("18446744073709551615", "340282366920938463463374607431768211455", "4294967295", "ffffffffffffffff",
                "18446744073709551615", "18446744073709551615", "18446744073709551615", 0, 0, 1);
        var mapper = ControlBuild.strictMapper();
        com.fasterxml.jackson.databind.node.ObjectNode json = mapper.valueToTree(maximum);
        assertTrue(json.path("creation_filetime_decimal").isTextual());
        assertEquals("18446744073709551615", json.path("creation_filetime_decimal").textValue());
        assertEquals(maximum, mapper.readValue(mapper.writeValueAsBytes(maximum), SharedSourceFiles.NativeFile.class));
        var numeric = json.deepCopy(); numeric.put("creation_filetime_decimal", 1L);
        assertThrows(IOException.class, () -> mapper.treeToValue(numeric, SharedSourceFiles.NativeFile.class));
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.NativeFile("18446744073709551616", "1", "1", "0000000000000001", "1", "1", "1", 0, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.NativeFile("1", "340282366920938463463374607431768211456", "1", "0000000000000001", "1", "1", "1", 0, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.NativeFile("1", "1", "4294967296", "0000000000000001", "1", "1", "1", 0, 0, 1));
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.NativeFile("1", "1", "1", "0000000000000001", null, "1", "1", 0, 0, 1));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeDirectory(file));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeFile(root));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeDirectory(root.resolve("missing")));
    }
}
