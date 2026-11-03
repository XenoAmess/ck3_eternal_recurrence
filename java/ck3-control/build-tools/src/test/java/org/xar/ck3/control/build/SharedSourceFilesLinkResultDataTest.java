package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.LinkResult;
import org.xar.ck3.control.build.SharedSourceFiles.NativeFile;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Public constructor DATA contract only; these declarations are not native observations. */
final class SharedSourceFilesLinkResultDataTest {
    @Test void sameContentReplacementWithLegacyIdCollisionCannotBecomeAHardlinkDeclaration() {
        FileRef source = new FileRef("D:/data-witness/source.py", 3,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        FileRef destination = new FileRef("D:/data-witness/view.py", 3,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        NativeFile original = new NativeFile("18446744073709551615", "18446744073709551615",
                "4294967295", "ffffffffffffffff", "91", "120", "121", 3, 4096, 1);
        NativeFile linked = new NativeFile("18446744073709551615", "18446744073709551615",
                "4294967295", "ffffffffffffffff", "91", "120", "122", 3, 8192, 2);
        Witness before = new Witness(source, original);
        LinkResult accepted = new LinkResult(before, new Witness(source, linked), new Witness(destination, linked));
        assertEquals(4096L, accepted.allocatedGrowthBytes());

        NativeFile replacement = new NativeFile("18446744073709551615", "184467440737095516159",
                "4294967295", "ffffffffffffffff", "1", "120", "122", 3, 8192, 2);
        IllegalArgumentException rejected = assertThrows(IllegalArgumentException.class,
                () -> new LinkResult(before, new Witness(source, replacement), new Witness(destination, replacement)));
        assertEquals("hardlink must preserve exact bytes/native identity/mtime and add exactly one link", rejected.getMessage());
    }
}
