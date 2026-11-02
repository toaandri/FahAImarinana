import javax.microedition.midlet.MIDlet;
import javax.microedition.lcdui.Display;
import utils.ScreenManager;
import screens.ChatScreen;

public class Main extends MIDlet {
    public void startApp() {
        ScreenManager.init(Display.getDisplay(this));
        ScreenManager.show(new ChatScreen());
    }

    public void pauseApp() {
    }

    public void destroyApp(boolean unconditional) {
    }
}
