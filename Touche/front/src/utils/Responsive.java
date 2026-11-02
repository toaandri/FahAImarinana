package utils;

import javax.microedition.lcdui.Display;
import javax.microedition.lcdui.Canvas;

public class Responsive {
    public static int screenWidth = 240;
    public static int screenHeight = 320;

    public static void init(Canvas c) {
        screenWidth = c.getWidth();
        screenHeight = c.getHeight();
    }

    public static int scale(int base) {
        if (screenWidth <= 128) return base * 128 / 240;
        if (screenWidth <= 176) return base * 176 / 240;
        if (screenWidth <= 240) return base;
        return base * screenWidth / 240;
    }

    public static boolean isSmall() {
        return screenWidth <= 176;
    }
}
