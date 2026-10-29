package org.xar.ck3.control.service;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrants;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;

/** Reads only a server-fixed manifest. Offline publication can add evidence without restarting the host. */
public final class ProjectionEvidenceManifestReader implements ProjectionEvidenceGrants {
    private final Path manifest;
    public ProjectionEvidenceManifestReader(Path manifest) {
        Objects.requireNonNull(manifest);
        if (!manifest.isAbsolute()) { throw new IllegalArgumentException("absolute fixed server evidence manifest required"); }
        this.manifest = manifest.normalize();
    }
    @Override public List<ProjectionEvidenceGrant> currentGrants() {
        try {
            for (Path ancestor = manifest; ancestor != null; ancestor = ancestor.getParent()) {
                BasicFileAttributes attributes = Files.readAttributes(ancestor, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (attributes.isSymbolicLink() || attributes.isOther()
                        || !ancestor.toRealPath().equals(ancestor.toAbsolutePath().normalize())) {
                    throw new IOException("evidence manifest path has an indirect component");
                }
            }
            BasicFileAttributes before = Files.readAttributes(manifest, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!before.isRegularFile() || before.fileKey() == null || before.size() > ProjectionEvidenceCodec.MAX_BYTES) {
                throw new IOException("identity-bearing bounded evidence manifest required");
            }
            byte[] raw;
            try (InputStream input = Files.newInputStream(manifest)) { raw = input.readNBytes(ProjectionEvidenceCodec.MAX_BYTES + 1); }
            BasicFileAttributes after = Files.readAttributes(manifest, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!after.isRegularFile() || after.isSymbolicLink() || !Objects.equals(before.fileKey(), after.fileKey())
                    || before.size() != after.size() || raw.length != after.size()
                    || !before.lastModifiedTime().equals(after.lastModifiedTime())) {
                throw new IOException("evidence manifest identity or content changed during read");
            }
            return ProjectionEvidenceCodec.decode(raw);
        } catch (IOException | RuntimeException failure) {
            throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "fixed server evidence manifest unavailable");
        }
    }
}
