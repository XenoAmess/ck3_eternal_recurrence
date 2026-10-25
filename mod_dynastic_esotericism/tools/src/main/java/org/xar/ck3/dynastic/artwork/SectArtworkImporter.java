package org.xar.ck3.dynastic.artwork;

import java.awt.AlphaComposite;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import javax.imageio.ImageIO;

/** Imports the two owner-supplied icons without changing their artwork. */
public final class SectArtworkImporter {
    private static final int SIZE = 256;

    private SectArtworkImporter() { }

    public record AssetPin(String path, int bytes, String sha256) { }
    public record ImportReport(String archiveSha256, List<AssetPin> assets) {
        public ImportReport { assets = List.copyOf(assets); }
    }

    public static ImportReport importArchive(Path archive, Path source) throws IOException {
        byte[] procreation;
        byte[] vivhite;
        try (ZipFile zip = new ZipFile(archive.toFile())) {
            procreation = entry(zip, "繁育教派.dds");
            vivhite = entry(zip, "白绮教派.png");
        }
        validateDds(procreation);
        BufferedImage original = ImageIO.read(new ByteArrayInputStream(vivhite));
        if (original == null || original.getWidth() != original.getHeight()) {
            throw new IllegalArgumentException("Vivhite icon must be a readable square PNG");
        }
        BufferedImage resized = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = resized.createGraphics();
        try {
            graphics.setComposite(AlphaComposite.Src);
            graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            graphics.drawImage(original, 0, 0, SIZE, SIZE, null);
        } finally {
            graphics.dispose();
        }
        Path icons = source.resolve("gfx/interface/icons/faith");
        Path emblems = source.resolve("gfx/coat_of_arms/textured_emblems");
        Path originals = source.resolve("tools/artwork/source");
        Files.createDirectories(icons);
        Files.createDirectories(emblems);
        Files.createDirectories(originals);
        Path procreationPath = icons.resolve("des_procreation.dds");
        Path vivhitePath = icons.resolve("des_vivhite.dds");
        Path originalPath = originals.resolve("des_vivhite.png");
        Files.write(procreationPath, procreation);
        Files.write(vivhitePath, encodeDds(resized));
        Files.write(originalPath, vivhite);
        Path procreationEmblem = emblems.resolve("des_procreation.dds");
        Path vivhiteEmblem = emblems.resolve("des_vivhite.dds");
        Files.write(procreationEmblem, procreation);
        Files.write(vivhiteEmblem, Files.readAllBytes(vivhitePath));
        return new ImportReport(sha256(Files.readAllBytes(archive)), List.of(
                pin(procreationPath), pin(vivhitePath), pin(procreationEmblem), pin(vivhiteEmblem), pin(originalPath)));
    }

    private static byte[] entry(ZipFile zip, String name) throws IOException {
        ZipEntry entry = zip.getEntry(name);
        if (entry == null) throw new IllegalArgumentException("Uploaded icon archive is missing " + name);
        try (var input = zip.getInputStream(entry)) { return input.readAllBytes(); }
    }

    private static void validateDds(byte[] data) {
        if (data.length != 128 + SIZE * SIZE * 4) throw new IllegalArgumentException("Expected supplied 256x256 RGBA DDS");
        ByteBuffer header = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        if (header.getInt(0) != 0x20534444 || header.getInt(4) != 124
                || header.getInt(12) != SIZE || header.getInt(16) != SIZE
                || header.getInt(76) != 32 || header.getInt(88) != 32) {
            throw new IllegalArgumentException("Invalid supplied RGBA DDS header");
        }
    }

    private static byte[] encodeDds(BufferedImage image) {
        ByteBuffer data = ByteBuffer.allocate(128 + SIZE * SIZE * 4).order(ByteOrder.LITTLE_ENDIAN);
        data.putInt(0x20534444).putInt(124).putInt(0x100f);
        data.putInt(SIZE).putInt(SIZE).putInt(SIZE * 4).putInt(0).putInt(0);
        for (int reserved = 0; reserved < 11; reserved++) data.putInt(0);
        data.putInt(32).putInt(0x41).putInt(0).putInt(32);
        data.putInt(0x00ff0000).putInt(0x0000ff00).putInt(0x000000ff).putInt(0xff000000);
        data.putInt(0x1000).putInt(0).putInt(0).putInt(0).putInt(0);
        for (int y = 0; y < SIZE; y++) for (int x = 0; x < SIZE; x++) data.putInt(image.getRGB(x, y));
        return data.array();
    }

    private static AssetPin pin(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        return new AssetPin(path.toString(), bytes.length, sha256(bytes));
    }

    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }

    /** Source-file mode is also available before the first Maven build. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 2) throw new IllegalArgumentException("Expected uploaded ZIP and mod source directory");
        ImportReport report = importArchive(Path.of(arguments[0]), Path.of(arguments[1]));
        System.out.println("Imported owner-supplied artwork: " + report);
    }
}
