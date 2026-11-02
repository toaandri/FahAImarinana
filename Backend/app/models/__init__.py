"""Canonical models and aliases preserving the existing HTTP/service contracts."""
from .newsroom import Newsroom
from .identity import User, ContactJournaliste
from .monitoring import Source, Signal
from .investigation import Case, Claim, Evidence, ClaimEvidence
from .editorial import Draft, Publication
from .maharavo import ResearchJob, MediaAnalysis, EvaluationConfianceMaharavo
from .sms import SmsExchange
from .audit import CorrectionAudit
from .research import DocumentRecherche, SessionChat, MessageChat

Utilisateur = User
SourceSurveillee = Source
SignalBrut = Signal
DraftIA = Draft
ArticleCertifie = Publication
RechercheMaharavo = ResearchJob
AnalyseMediaMaharavo = MediaAnalysis
HistoriqueSms = SmsExchange
