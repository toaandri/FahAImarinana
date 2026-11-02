package utils;

import javax.microedition.lcdui.Display;
import javax.microedition.lcdui.Displayable;

public class ScreenManager {
    private static Display display;
    private static Displayable current;

    public static void init(Display d) {
        display = d;
    }

    public static void show(Displayable s) {
        current = s;
        if (display != null) {
            display.setCurrent(s);
        }
    }

    public static Displayable getCurrent() {
        return current;
    }

    public static Display getDisplay() {
        return display;
    }
}
