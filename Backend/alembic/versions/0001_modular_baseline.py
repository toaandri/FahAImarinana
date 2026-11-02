"""Initial frozen schema and explicit, validated adoption of legacy installations.

Revision ID: 0001_modular_baseline
"""
from alembic import op, context
import sqlalchemy as sa

revision = "0001_modular_baseline"
down_revision = None
branch_labels = None
depends_on = None


def baseline():
    metadata = sa.MetaData()
    sa.Table('documents_recherche', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('titre', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('contenu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('url', sa.String(length=500), primary_key=False, nullable=True),
        sa.Column('est_certifie', sa.Boolean(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    sa.Table('historique_sms', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('numero_expediteur', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('message_recu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('message_envoye', sa.Text(), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('statut_reponse', sa.String(length=30), primary_key=False, nullable=False),
    )
    sa.Table('sources_surveillees', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('nom', sa.String(length=150), primary_key=False, nullable=False),
        sa.Column('type', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('url', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=15), primary_key=False, nullable=False),
        sa.Column('frequence_scan_secondes', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('derniere_verification', sa.DateTime(timezone=True), primary_key=False, nullable=True),
    )
    sa.Table('utilisateurs', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), primary_key=False, nullable=False),
        sa.Column('mot_de_passe_hash', sa.String(length=255), primary_key=False, nullable=False),
        sa.Column('role', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('actif', sa.Boolean(), primary_key=False, nullable=False),
    )
    sa.Index('ix_utilisateurs_email', metadata.tables['utilisateurs'].c['email'], unique=True)
    sa.Table('analyses_media_maharavo', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), primary_key=False, nullable=False),
        sa.Column('type_media', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('reference_originale', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('empreinte_sha256', sa.String(length=64), primary_key=False, nullable=False),
        sa.Column('outil', sa.String(length=150), primary_key=False, nullable=False),
        sa.Column('version_outil', sa.String(length=80), primary_key=False, nullable=False),
        sa.Column('observations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('indice_indicatif', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('limites', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    sa.Table('contacts_journalistes', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), primary_key=False, nullable=False),
        sa.Column('numero_telephone', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('alertes_actives', sa.Boolean(), primary_key=False, nullable=False),
        sa.UniqueConstraint('numero_telephone', name=None),
    )
    sa.Table('evaluations_confiance_maharavo', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), primary_key=False, nullable=False),
        sa.Column('objet_type', sa.String(length=30), primary_key=False, nullable=False),
        sa.Column('objet_id', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('identite_source', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('solidite_preuves', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('validation_editoriale', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('conclusion', sa.String(length=40), primary_key=False, nullable=False),
        sa.Column('justification', sa.Text(), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    sa.Table('recherches_maharavo', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), primary_key=False, nullable=False),
        sa.Column('sujet', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('questions', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('periode', sa.String(length=100), primary_key=False, nullable=True),
        sa.Column('langues', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('territoire', sa.String(length=150), primary_key=False, nullable=True),
        sa.Column('requetes', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('documents_ouverts', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('citations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('synthese', sa.Text(), primary_key=False, nullable=True),
        sa.Column('erreurs', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('modele', sa.String(length=100), primary_key=False, nullable=False),
        sa.Column('debut', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('fin', sa.DateTime(timezone=True), primary_key=False, nullable=True),
    )
    sa.Table('sessions_chat', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), primary_key=False, nullable=False),
        sa.Column('titre', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('cree_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('mise_a_jour_le', sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    sa.Table('signaux_bruts', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('sources_surveillees.id'), primary_key=False, nullable=False),
        sa.Column('contenu_brut', sa.Text(), primary_key=False, nullable=False),
        sa.Column('contenu_normalise', sa.Text(), primary_key=False, nullable=False),
        sa.Column('url_origine', sa.String(length=500), primary_key=False, nullable=False),
        sa.Column('horodatage_publication', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('auteur', sa.String(length=150), primary_key=False, nullable=True),
        sa.Column('nombre_interactions', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('niveau_viralite', sa.Float(), primary_key=False, nullable=False),
        sa.Column('mots_cles_detectes', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('est_urgent', sa.Boolean(), primary_key=False, nullable=False),
    )
    sa.Table('drafts_ia', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('signal_id', sa.Integer(), sa.ForeignKey('signaux_bruts.id'), primary_key=False, nullable=False),
        sa.Column('titre_suggere', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('synthese_ia', sa.Text(), primary_key=False, nullable=False),
        sa.Column('score_credibilite_indicatif', sa.Float(), primary_key=False, nullable=False),
        sa.Column('sources_croisees', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('statut', sa.String(length=25), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.UniqueConstraint('signal_id', name='uq_drafts_ia_signal_id'),
    )
    sa.Table('messages_chat', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('sessions_chat.id'), primary_key=False, nullable=False),
        sa.Column('role', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('contenu', sa.Text(), primary_key=False, nullable=False),
        sa.Column('citations', sa.JSON(), primary_key=False, nullable=False),
        sa.Column('horodatage', sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    sa.Table('articles_certifies', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('draft_id', sa.Integer(), sa.ForeignKey('drafts_ia.id'), primary_key=False, nullable=True),
        sa.Column('titre_final', sa.String(length=250), primary_key=False, nullable=False),
        sa.Column('corps_article', sa.Text(), primary_key=False, nullable=False),
        sa.Column('categorie', sa.String(length=50), primary_key=False, nullable=False),
        sa.Column('statut_verification', sa.String(length=20), primary_key=False, nullable=False),
        sa.Column('id_journaliste_validateur', sa.Integer(), primary_key=False, nullable=False),
        sa.Column('horodatage_validation', sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column('contenu_optimise_sms', sa.String(length=480), primary_key=False, nullable=False),
    )
    return metadata


def validate_existing(connection, metadata):
    """Reject incompatible data structures before creating or stamping anything."""
    inspector = sa.inspect(connection)
    errors = []
    for table in metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        actual = {column["name"]: column for column in inspector.get_columns(table.name)}
        for column in table.columns:
            stored = actual.get(column.name)
            if stored is None:
                errors.append(f"{table.name}.{column.name}: colonne absente")
                continue
            expected_type = column.type._type_affinity
            actual_type = stored["type"]._type_affinity
            if expected_type is not actual_type:
                errors.append(f"{table.name}.{column.name}: type incompatible")
            expected_length = getattr(column.type, "length", None)
            stored_length = getattr(stored["type"], "length", None)
            if expected_length and stored_length and stored_length < expected_length:
                errors.append(f"{table.name}.{column.name}: longueur insuffisante")
            if not column.nullable and stored.get("nullable") and not column.primary_key:
                errors.append(f"{table.name}.{column.name}: nullabilité incompatible")
        primary = set(inspector.get_pk_constraint(table.name).get("constrained_columns") or [])
        if primary != {column.name for column in table.primary_key}:
            errors.append(f"{table.name}: clé primaire incompatible")
        foreign = {(tuple(item["constrained_columns"]), item["referred_table"], tuple(item["referred_columns"]))
                   for item in inspector.get_foreign_keys(table.name)}
        for constraint in table.foreign_key_constraints:
            expected = (tuple(element.parent.name for element in constraint.elements),
                        constraint.referred_table.name, tuple(element.column.name for element in constraint.elements))
            if expected not in foreign:
                errors.append(f"{table.name}: clé étrangère absente {expected[0]}")
        unique = {tuple(item["column_names"]) for item in inspector.get_unique_constraints(table.name)}
        unique.update(tuple(item["column_names"]) for item in inspector.get_indexes(table.name) if item.get("unique"))
        for constraint in table.constraints:
            if isinstance(constraint, sa.UniqueConstraint) and tuple(c.name for c in constraint.columns) not in unique:
                errors.append(f"{table.name}: unicité absente")
        for index in table.indexes:
            if index.unique and tuple(c.name for c in index.columns) not in unique:
                errors.append(f"{table.name}: index unique absent")
    if errors:
        raise RuntimeError("Schéma historique incompatible : " + "; ".join(errors))


def upgrade():
    metadata = baseline()
    if context.is_offline_mode():
        metadata.create_all(op.get_bind(), checkfirst=False)
        return
    connection = op.get_bind()
    existing = set(sa.inspect(connection).get_table_names()) & set(metadata.tables)
    if existing:
        if context.get_x_argument(as_dictionary=True).get("adopt_legacy") != "true":
            raise RuntimeError("Base existante : sauvegarder puis utiliser -x adopt_legacy=true après revue du schéma.")
        validate_existing(connection, metadata)
    metadata.create_all(connection, checkfirst=True)


def downgrade():
    # Dropping an adopted database is never implicitly safe.
    if context.get_x_argument(as_dictionary=True).get("allow_drop_baseline") != "true":
        raise RuntimeError("Downgrade destructif : utiliser -x allow_drop_baseline=true uniquement sur une base jetable.")
    baseline().drop_all(op.get_bind(), checkfirst=not context.is_offline_mode())
