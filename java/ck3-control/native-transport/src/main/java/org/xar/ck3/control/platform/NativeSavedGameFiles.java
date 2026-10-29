package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.xar.ck3.control.build.ControlBuild;

/**
 * Materializes the exact save file required by -loadsave into the profile's save games directory.
 * Preserves the original source reference and returns the actual target FileRef.
 */
final class NativeSavedGameFiles {
    static ControlBuild.FileRef materialize(Path profileDirectory, NativeLaunchPlan.SavedGame load) throws IOException {
        Path target = profileDirectory.resolve("save games").resolve(load.basename() + ".ck3");
        Path source = Path.of(load.save().path());
        
        // Ensure target directory exists
        Files.createDirectories(target.getParent());
        
        // If source is already the target, verify and return
        if (source.equals(target)) {
            ControlBuild.FileRef actual = ControlBuild.FileRef.measure(target);
            if (actual.bytes() != load.save().bytes() || !actual.sha256().equals(load.save().sha256())) {
                throw new IOException("In-place source changed from expected original: " + target);
            }
            return actual;
        }
        
        // Check if target already exists
        if (Files.exists(target)) {
            if (!Files.isRegularFile(target)) {
                throw new IOException("Target save path is not a regular file: " + target);
            }
            
            // Verify existing target matches expected source
            ControlBuild.FileRef targetRef = ControlBuild.FileRef.measure(target);
            if (targetRef.bytes() != load.save().bytes() || !targetRef.sha256().equals(load.save().sha256())) {
                throw new IOException("Conflicting save target exists with different bytes: " + target);
            }
            
            return targetRef;
        }
        
        // Create our own staging file before copying; the final move never replaces a target.
        Path temp = Files.createTempFile(target.getParent(), "xar-save-", ".pending");
        Throwable primary = null;
        try {
            try (var input = Files.newInputStream(source); var output = Files.newOutputStream(temp)) {
                input.transferTo(output);
            }
            
            // Verify copied temp matches expected source before moving
            ControlBuild.FileRef tempRef = ControlBuild.FileRef.measure(temp);
            if (tempRef.bytes() != load.save().bytes() || !tempRef.sha256().equals(load.save().sha256())) {
                throw new IOException("Copied source changed from expected original: " + source);
            }
            
            Files.move(temp, target);
            return new ControlBuild.FileRef(target.toString(), tempRef.bytes(), tempRef.sha256());
        } catch (IOException | RuntimeException | Error error) {
            primary = error;
            throw error;
        } finally {
            try {
                Files.deleteIfExists(temp);
            } catch (IOException cleanup) {
                if (primary != null) primary.addSuppressed(cleanup);
                else throw cleanup;
            }
        }
    }
}
