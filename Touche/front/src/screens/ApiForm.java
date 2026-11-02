package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import utils.ScreenManager;

public abstract class ApiForm extends Form implements CommandListener {
    protected boolean busy;
    protected StringItem status = new StringItem("Etat","");
    protected Command home = new Command("Accueil",Command.BACK,9);
    protected ApiForm(String title) { super(title); append(status); addCommand(home); setCommandListener(this); }
    protected void call(String method,String path,Hashtable body,final Api.Listener listener) {
        if (busy) return;
        busy = true; status.setText("Chargement...");
        Api.request(method,path,body,new Api.Listener() {
            public void success(Object data) {
                busy = false; status.setText("Operation reussie");
                if (listener != null) listener.success(data);
            }
            public void failure(String message) { busy = false; status.setText(message); }
        });
    }
    public void commandAction(Command command,Displayable view) {
        if (busy) return;
        if (command == home) ScreenManager.show(new NewsroomScreen());
        else act(command);
    }
    protected abstract void act(Command command);
}
