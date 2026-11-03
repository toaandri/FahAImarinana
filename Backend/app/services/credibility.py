"""Calculate an auditable share of source assessments supplied by a journalist."""
from collections import defaultdict

from ..schemas.credibility import CredibilityRequest


def calculate_corroboration(payload: CredibilityRequest) -> dict:
    # A conservative grouping: collapse subdomains and multi-level public suffixes
    # to the last two labels. This can merge unrelated outlets (e.g. *.co.uk), but
    # avoids counting ordinary subdomains as independent sources. It is not proof
    # of editorial independence; journalists must check syndication and ownership.
    groups = defaultdict(set)
    for source in payload.sources:
        host = 'fanilo.local' if isinstance(source.url, str) else (source.url.host or '').lower().rstrip('.')
        parts = host.split('.')
        group = '.'.join(parts[-2:]) if len(parts) > 1 else host
        groups[group].add(source.assessment)

    counts = {'supports': 0, 'contradicts': 0, 'inconclusive': 0}
    for assessments in groups.values():
        # Conflicting judgements for a single group cannot cast two votes.
        verdict = next(iter(assessments)) if len(assessments) == 1 else 'inconclusive'
        counts[verdict] += 1
    decisive = counts['supports'] + counts['contradicts']
    score = round(100 * counts['supports'] / decisive, 1) if decisive >= 2 else None
    return {
        'claim': payload.claim,
        'corroboration_percent': score,
        **counts,
        'source_groups': len(groups),
        'excluded_duplicates': len(payload.sources) - len(groups),
        'limitation': (
            'Part des groupes de sources jugés concordants par le journaliste parmi les groupes conclusifs. '
            'Ce calcul ne vérifie pas les liens ni les affirmations et ne mesure pas la probabilité de vérité. '
            'Vérifiez indépendance, contexte, dates et contenu ; les sous-domaines sont regroupés de façon conservatrice.'
        ),
    }
