import javax.microedition.midlet.MIDlet;
import javax.microedition.lcdui.Display;
import javax.microedition.lcdui.Form;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import network.PublicCache;
import utils.ScreenManager;

/** Integration test MIDlet: actual Connector HTTP and RMS against a disposable backend. */
public class MobileSmoke extends MIDlet implements Api.Listener {
    private int step;
    private String caseId,claimId,evidenceId,signalId,draftId;
    private Hashtable published;
    protected void startApp() {
        ScreenManager.init(Display.getDisplay(this));
        ScreenManager.show(new Form("Test reseau reel"));
        Api.configure(System.getProperty("fa.test.url"));
        next();
    }
    protected void pauseApp() { }
    protected void destroyApp(boolean unconditional) { }
    private Hashtable data(String key,Object value) { Hashtable valueMap=Json.object(); valueMap.put(key,value); return valueMap; }
    private Hashtable article() {
        Hashtable body=data("titre_final","Vérification mobile eau");
        body.put("corps_article","Résultat éditorial approuvé concernant eau."); body.put("categorie","Test mobile");
        body.put("statut_verification","Vrai"); body.put("contenu_optimise_sms","Résumé humain eau."); return body;
    }
    private void send(String method,String path,Hashtable body) { Api.request(method,path,body,this); }
    private void next() {
        Hashtable body;
        switch(step) {
        case 0: case 11:
            if(step==11) Api.clear();
            body=data("email",step==0?"mobile-journalist@example.invalid":"mobile-editor@example.invalid");
            body.put("mot_de_passe","mobile-test-password-only"); send("POST","/auth/login",body); break;
        case 1: case 12: send("GET","/auth/me",null); break;
        case 2: send("POST","/cases",data("title","Dossier du test mobile")); break;
        case 3: send("POST","/cases/"+caseId+"/claims",data("statement","Affirmation test eau")); break;
        case 4:
            body=data("title","Preuve originale eau"); body.put("content","PRIVATE_MOBILE_EVIDENCE eau"); body.put("kind","document");
            send("POST","/cases/"+caseId+"/evidence",body); break;
        case 5:
            body=data("evidence_id",Long.valueOf(evidenceId)); send("POST","/cases/"+caseId+"/claims/"+claimId+"/evidence",body); break;
        case 6:
            body=data("case_id",Long.valueOf(caseId)); body.put("source_id",new Long(1)); body.put("contenu","Signal eau");
            body.put("url_origine","https://mobile-source.example.invalid/item"); body.put("horodatage_publication","2026-11-02T12:00:00Z");
            send("POST","/signals/ingest",body); break;
        case 7:
            body=data("signal_id",Long.valueOf(signalId)); body.put("claim_id",Long.valueOf(claimId));
            body.put("titre_suggere","Brouillon test"); body.put("synthese_ia","PRIVATE_MOBILE_DRAFT");
            send("POST","/cases/"+caseId+"/drafts",body); break;
        case 8: send("POST","/cases/"+caseId+"/research",data("question","eau")); break;
        case 9: send("GET","/public/sync",null); break;
        case 10: send("POST","/auth/logout",null); break;
        case 13:
            body=data("expected_version",new Long(2)); body.put("decision","reviewed"); body.put("notes","Pièces examinées humainement.");
            send("POST","/workflow/drafts/"+draftId+"/review",body); break;
        case 14:
            body=article(); body.put("expected_version",new Long(2)); send("POST","/workflow/drafts/"+draftId+"/validate",body); break;
        case 15: send("POST","/workflow/drafts/"+draftId+"/publish",article()); break;
        case 16: send("GET","/public/sync",null); break;
        case 17:
            body=data("numero_expediteur","+261000000"); body.put("message","eau"); send("POST","/sms/citizen",body); break;
        case 18:
            body=data("numero_expediteur","+261000000"); body.put("message","PRIVATE_MOBILE_EVIDENCE"); send("POST","/sms/citizen",body); break;
        case 19:
            send("GET","/drafts/"+draftId+"/history",null); break;
        case 20:
            send("POST","/workflow/publications/"+Json.str(published,"id")+"/withdraw",data("reason","Retrait du test mobile")); break;
        case 21: send("GET","/public/sync",null); break;
        case 22:
            body=data("expected_version",new Long(1)); body.put("synthese_ia","PRIVATE_MOBILE_REVISED_DRAFT");
            send("POST","/drafts/"+draftId+"/revisions",body); break;
        default:
            System.out.println("MOBILE_SMOKE_OK: HTTP journalist/editor workflow, SMS lookup, private-data isolation and RMS public cache");
            System.exit(0);
        }
    }
    private void check(boolean condition,String message) { if(!condition) throw new IllegalStateException(message); }
    public void success(Object result) {
        try {
            Hashtable item=result instanceof Hashtable?(Hashtable)result:Json.object();
            switch(step) {
            case 0: case 11: Api.tokens(item); check(Api.authenticated(),"Token manquant"); break;
            case 1: Api.profile(item); check(Api.can("cases.create") && !Api.can("publications.publish"),"Permissions journaliste incorrectes"); break;
            case 2: caseId=Json.str(item,"id"); break;
            case 3: claimId=Json.str(item,"id"); break;
            case 4: evidenceId=Json.str(item,"id"); break;
            case 6: signalId=Json.str(item,"id"); break;
            case 7: draftId=Json.str(item,"id"); step=22; next(); return;
            case 8: check(((Vector)item.get("citations")).size()==1,"Recherche locale vide"); break;
            case 9: check(((Vector)item.get("items")).size()==0,"Fuite de brouillon public"); break;
            case 12: Api.profile(item); check(Api.can("versions.validate"),"Permissions editeur incorrectes"); break;
            case 15: published=item; break;
            case 16:
                check(Json.encode(item).indexOf("PRIVATE_MOBILE_")<0,"Fuite de pieces privees");
                check(((Vector)item.get("items")).size()==1,"Publication manquante");
                item.put("server",Api.baseUrl); PublicCache.save(item);
                check(PublicCache.load()!=null,"Cache RMS manquant");
                check(Json.str(PublicCache.load(),"snapshot_version").equals(Json.str(item,"snapshot_version")),"Version cache incorrecte");
                break;
            case 17: check("Résumé humain eau.".equals(Json.str(item,"message")),"SMS publication introuvable"); break;
            case 18: check("Aucune vérification publiée trouvée pour cette demande.".equals(Json.str(item,"message")),"SMS confidentiel expose"); break;
            case 19: check(((Vector)result).size()==6,"Historique incomplet"); break;
            case 21:
                check(((Vector)item.get("items")).size()==0,"Retrait non synchronise");
                item.put("server",Api.baseUrl); PublicCache.save(item);
                check(((Vector)PublicCache.load().get("items")).size()==0,"Ancienne publication encore en cache");
                step=23; next(); return;
            case 22:
                check("2".equals(Json.str(item,"version")),"Revision mobile non enregistree");
                step=8; next(); return;
            }
            step++; next();
        } catch(Exception ex) { failure(ex.toString()); }
    }
    public void failure(String message) { System.err.println("MOBILE_SMOKE_FAILED step="+step+" "+message); System.exit(1); }
}
