import javax.microedition.midlet.MIDlet;
import javax.microedition.lcdui.Display;
import utils.ScreenManager;
import screens.LoginScreen;

public class Main extends MIDlet {
    public void startApp() {
        ScreenManager.init(Display.getDisplay(this));
        ScreenManager.show(new LoginScreen());
    }

    public void pauseApp() {
    }

    public void destroyApp(boolean unconditional) {
    }
}
