package org.xar.ck3.control.application.readiness;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Win32 FILE_ID_INFO and FILETIME facts; never OS inode/nanosecond facts. */
public record NativeSourceFileIdentity(String volumeSerialDecimal, String fileIdDecimal,
        String legacyVolumeSerialDecimal, String legacyFileIdHex, String creationFiletimeDecimal,
        String lastWriteFiletimeDecimal, String changeFiletimeDecimal,
        long logicalBytes, long allocatedBytes, long linkCount) {
    public NativeSourceFileIdentity {
        unsignedDecimal(volumeSerialDecimal, 64);
        unsignedDecimal(fileIdDecimal, 128);
        unsignedDecimal(legacyVolumeSerialDecimal, 32);
        StrictJson.require(legacyFileIdHex != null && legacyFileIdHex.matches("[0-9a-f]{16}"),
                "exact original Win32 legacy FileID64 hex required");
        unsignedDecimal(creationFiletimeDecimal, 64);
        unsignedDecimal(lastWriteFiletimeDecimal, 64);
        unsignedDecimal(changeFiletimeDecimal, 64);
        StrictJson.safe(logicalBytes, 0);
        StrictJson.safe(allocatedBytes, 0);
        StrictJson.require(linkCount > 0 && linkCount <= 0xffff_ffffL,
                "positive native DWORD link count required");
    }

    private static void unsignedDecimal(String value, int bits) {
        StrictJson.require(value != null && value.length() <= 39 && value.matches("0|[1-9][0-9]*")
                        && new BigInteger(value).bitLength() <= bits,
                "canonical unsigned native decimal within " + bits + " bits required");
    }

    /** Allocation, link count and change time may change without replacing an immutable file. */
    public boolean sameImmutableFile(NativeSourceFileIdentity actual) {
        Objects.requireNonNull(actual);
        return volumeSerialDecimal.equals(actual.volumeSerialDecimal)
                && fileIdDecimal.equals(actual.fileIdDecimal)
                && legacyVolumeSerialDecimal.equals(actual.legacyVolumeSerialDecimal)
                && legacyFileIdHex.equals(actual.legacyFileIdHex)
                && creationFiletimeDecimal.equals(actual.creationFiletimeDecimal)
                && lastWriteFiletimeDecimal.equals(actual.lastWriteFiletimeDecimal)
                && logicalBytes == actual.logicalBytes;
    }

    /** Decoded or constructed witnesses are historical DATA, never live source qualification. */
    public record SourceWitness(ExactRef source, NativeSourceFileIdentity nativeFile) {
        public SourceWitness {
            Objects.requireNonNull(source);
            Objects.requireNonNull(nativeFile);
            StrictJson.require(source.bytes() == nativeFile.logicalBytes(),
                    "source size and original native logical size differ");
        }

        public boolean sameImmutableFile(SourceWitness actual) {
            Objects.requireNonNull(actual);
            return source.equals(actual.source) && nativeFile.sameImmutableFile(actual.nativeFile);
        }
    }
}
