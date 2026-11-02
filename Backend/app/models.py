from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base


class SourceSurveillee(Base):
    __tablename__ = "sources_surveillees"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    type: Mapped[str] = mapped_column(String(30))
    url: Mapped[str] = mapped_column(String(500))
    statut: Mapped[str] = mapped_column(String(15), default="Actif")
    frequence_scan_secondes: Mapped[int] = mapped_column(Integer, default=900)
    derniere_verification: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SignalBrut(Base):
    __tablename__ = "signaux_bruts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources_surveillees.id"))
    contenu_brut: Mapped[str] = mapped_column(Text)
    contenu_normalise: Mapped[str] = mapped_column(Text)
    url_origine: Mapped[str] = mapped_column(String(500))
    horodatage_publication: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    auteur: Mapped[str | None] = mapped_column(String(150))
    nombre_interactions: Mapped[int] = mapped_column(Integer, default=0)
    niveau_viralite: Mapped[float] = mapped_column(Float, default=0)
    mots_cles_detectes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    est_urgent: Mapped[bool] = mapped_column(Boolean, default=False)


class DraftIA(Base):
    __tablename__ = "drafts_ia"
    __table_args__ = (UniqueConstraint("signal_id", name="uq_drafts_ia_signal_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signaux_bruts.id"))
    titre_suggere: Mapped[str] = mapped_column(String(250))
    synthese_ia: Mapped[str] = mapped_column(Text)
    score_credibilite_indicatif: Mapped[float] = mapped_column(Float)
    sources_croisees: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    statut: Mapped[str] = mapped_column(String(25), default="En_Attente")
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ArticleCertifie(Base):
    __tablename__ = "articles_certifies"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts_ia.id"))
    titre_final: Mapped[str] = mapped_column(String(250))
    corps_article: Mapped[str] = mapped_column(Text)
    categorie: Mapped[str] = mapped_column(String(50))
    statut_verification: Mapped[str] = mapped_column(String(20))
    id_journaliste_validateur: Mapped[int] = mapped_column(Integer)
    horodatage_validation: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    contenu_optimise_sms: Mapped[str] = mapped_column(String(480))


class HistoriqueSms(Base):
    __tablename__ = "historique_sms"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_expediteur: Mapped[str] = mapped_column(String(30))
    message_recu: Mapped[str] = mapped_column(Text)
    message_envoye: Mapped[str] = mapped_column(Text)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    statut_reponse: Mapped[str] = mapped_column(String(30))


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Journaliste")
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class ContactJournaliste(Base):
    __tablename__ = "contacts_journalistes"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    numero_telephone: Mapped[str] = mapped_column(String(30), unique=True)
    alertes_actives: Mapped[bool] = mapped_column(Boolean, default=True)


class DocumentRecherche(Base):
    __tablename__ = "documents_recherche"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(250))
    contenu: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    est_certifie: Mapped[bool] = mapped_column(Boolean, default=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionChat(Base):
    __tablename__ = "sessions_chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    titre: Mapped[str] = mapped_column(String(250), default="Investigation")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mise_a_jour_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageChat(Base):
    __tablename__ = "messages_chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions_chat.id"))
    role: Mapped[str] = mapped_column(String(20))
    contenu: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RechercheMaharavo(Base):
    __tablename__ = "recherches_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    sujet: Mapped[str] = mapped_column(String(500))
    questions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    periode: Mapped[str | None] = mapped_column(String(100))
    langues: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    territoire: Mapped[str | None] = mapped_column(String(150))
    requetes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    documents_ouverts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    synthese: Mapped[str | None] = mapped_column(Text)
    erreurs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="en_cours")
    modele: Mapped[str] = mapped_column(String(100))
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnalyseMediaMaharavo(Base):
    __tablename__ = "analyses_media_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    type_media: Mapped[str] = mapped_column(String(20))
    reference_originale: Mapped[str] = mapped_column(String(500))
    empreinte_sha256: Mapped[str] = mapped_column(String(64))
    outil: Mapped[str] = mapped_column(String(150))
    version_outil: Mapped[str] = mapped_column(String(80))
    observations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    indice_indicatif: Mapped[str] = mapped_column(String(20))
    limites: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EvaluationConfianceMaharavo(Base):
    __tablename__ = "evaluations_confiance_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    objet_type: Mapped[str] = mapped_column(String(30))
    objet_id: Mapped[int] = mapped_column(Integer)
    identite_source: Mapped[str] = mapped_column(String(20))
    solidite_preuves: Mapped[str] = mapped_column(String(20))
    validation_editoriale: Mapped[str] = mapped_column(String(20))
    conclusion: Mapped[str] = mapped_column(String(40))
    justification: Mapped[str] = mapped_column(Text)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
