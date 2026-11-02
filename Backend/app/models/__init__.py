"""Model registry; legacy imports remain supported."""
from .identity import Utilisateur, ContactJournaliste
from .monitoring import SourceSurveillee, SignalBrut
from .editorial import DraftIA, ArticleCertifie
from .sms import HistoriqueSms
from .research import DocumentRecherche, SessionChat, MessageChat
from .maharavo import RechercheMaharavo, AnalyseMediaMaharavo, EvaluationConfianceMaharavo
