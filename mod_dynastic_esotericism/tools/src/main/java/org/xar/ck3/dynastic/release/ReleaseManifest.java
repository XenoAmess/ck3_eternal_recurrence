package org.xar.ck3.dynastic.release;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Objects;

/** The existing independent_mod_release v1 JSON contract, with explicit nullable fields. */
public record ReleaseManifest(
        @JsonProperty("format_version") int formatVersion,
        @JsonProperty("product_id") String productId,
        @JsonProperty("mod_version") String modVersion,
        @JsonProperty("git_tag") String gitTag,
        @JsonProperty("git_sha") String gitSha,
        @JsonProperty("workshop_item_id") String workshopItemId,
        @JsonProperty("files") List<FileEntry> files) {

    public ReleaseManifest {
        if (formatVersion != 1 || productId == null || !productId.matches("[a-z][a-z0-9_]*")
                || modVersion == null || !ReleaseProduct.VERSION.matcher(modVersion).matches()
                || gitSha == null || !ReleaseProduct.REVISION.matcher(gitSha).matches()) {
            throw new IllegalArgumentException("invalid release manifest identity");
        }
        if (gitTag != null && (gitTag.isBlank() || gitTag.chars().anyMatch(Character::isWhitespace))) {
            throw new IllegalArgumentException("invalid release Git tag");
        }
        workshopItemId = ReleaseProduct.workshopItemId(workshopItemId);
        files = List.copyOf(Objects.requireNonNull(files, "files"));
        if (files.isEmpty()) throw new IllegalArgumentException("manifest files cannot be empty");
    }

    public record FileEntry(String path, long size, String sha256) {
        public FileEntry {
            path = ReleaseProduct.relativePath(path);
            if (size < 0 || size > 9_007_199_254_740_991L || sha256 == null || !ReleaseProduct.DIGEST.matcher(sha256).matches()) {
                throw new IllegalArgumentException("invalid release file entry");
            }
        }
    }
}
