import java.awt.AlphaComposite;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import javax.imageio.ImageIO;

/** One-use consumption-format export; no generation, cropping, recoloring or compositing. */
public final class ExportDoctrineIcon {
    private static final int SIZE = 120;

    private ExportDoctrineIcon() { }

    public record AssetPin(String path, int bytes, String sha256) { }

    public static void main(String[] args) throws IOException, NoSuchAlgorithmException {
        if (args.length != 4) throw new IllegalArgumentException("PNG, group DDS, doctrine DDS, decoded preview PNG required");
        Path source = Path.of(args[0]).toAbsolutePath().normalize();
        Path group = Path.of(args[1]).toAbsolutePath().normalize();
        Path doctrine = Path.of(args[2]).toAbsolutePath().normalize();
        Path preview = Path.of(args[3]).toAbsolutePath().normalize();
        if (source.equals(group) || source.equals(doctrine) || group.equals(doctrine)) {
            throw new IllegalArgumentException("Distinct input and output paths required");
        }
        BufferedImage original = ImageIO.read(source.toFile());
        if (original == null || original.getWidth() != original.getHeight() || !original.getColorModel().hasAlpha()) {
            throw new IllegalArgumentException("A square PNG with its original alpha is required");
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
        ByteBuffer data = ByteBuffer.allocate(128 + SIZE * SIZE * 4).order(ByteOrder.LITTLE_ENDIAN);
        data.putInt(0x20534444).putInt(124).putInt(0x100f);
        data.putInt(SIZE).putInt(SIZE).putInt(SIZE * 4).putInt(0).putInt(0);
        for (int index = 0; index < 11; index++) data.putInt(0);
        data.putInt(32).putInt(0x41).putInt(0).putInt(32);
        data.putInt(0x00ff0000).putInt(0x0000ff00).putInt(0x000000ff).putInt(0xff000000);
        data.putInt(0x1000).putInt(0).putInt(0).putInt(0).putInt(0);
        for (int y = 0; y < SIZE; y++) for (int x = 0; x < SIZE; x++) data.putInt(resized.getRGB(x, y));
        BufferedImage decoded = new BufferedImage(SIZE, SIZE, BufferedImage.TYPE_INT_ARGB);
        int transparent = 0;
        int opaque = 0;
        for (int y = 0; y < SIZE; y++) for (int x = 0; x < SIZE; x++) {
            int pixel = data.getInt(128 + (y * SIZE + x) * 4);
            if (pixel != resized.getRGB(x, y)) throw new IllegalStateException("DDS pixel round trip differs");
            decoded.setRGB(x, y, pixel);
            if ((pixel >>> 24) == 0) transparent++;
            if ((pixel >>> 24) == 255) opaque++;
        }
        if (transparent == 0 || opaque == 0) throw new IllegalStateException("Transparent and opaque pixels must survive");
        Files.createDirectories(group.getParent());
        Files.createDirectories(doctrine.getParent());
        Files.createDirectories(preview.getParent());
        Files.write(group, data.array());
        Files.write(doctrine, data.array());
        if (!ImageIO.write(decoded, "png", preview.toFile())) throw new IOException("PNG writer unavailable");
        if (Files.mismatch(group, doctrine) != -1L) throw new IllegalStateException("DDS copies differ");
        System.out.println("source=" + pin(source));
        System.out.println("group=" + pin(group));
        System.out.println("doctrine=" + pin(doctrine));
        System.out.println("decodedPreview=" + pin(preview));
        System.out.println("dimensions=" + SIZE + "x" + SIZE + "; transparent=" + transparent + "; opaque=" + opaque);
    }

    private static AssetPin pin(Path path) throws IOException, NoSuchAlgorithmException {
        byte[] raw = Files.readAllBytes(path);
        return new AssetPin(path.toString(), raw.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
}
