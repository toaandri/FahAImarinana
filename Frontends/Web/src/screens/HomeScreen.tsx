import { Link } from 'expo-router';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, CredibilityBadge, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';

export default function HomeScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;

  return (
    <AppShell active="/" fillHeight={desktop}>
      <PageTitle>Accueil</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={styles.columnCard}>
          <View style={styles.cardHeader}>
            <View style={styles.cardIcon}>
              <Icon name="newspaper-variant-outline" color={colors.accent} />
            </View>
            <Text style={styles.cardTitle} accessibilityRole="header" aria-level={2}>
              Dernière information
            </Text>
            <Text style={styles.example} accessibilityLabel="Score présenté à titre d’exemple">
              Exemple
            </Text>
          </View>
          <View style={[styles.headline, desktop && styles.headlineDesktop]}>
            <View style={styles.headlineAccent} />
            <Text style={styles.headlineText}>[Titre de l’information]</Text>
          </View>
          <View style={styles.scorePanel}>
            <CredibilityBadge value="85 %" />
            <View style={styles.metaRow}>
              <View style={styles.metaItem}>
                <Icon name="link-variant" size={16} />
                <Text style={styles.meta}>[Source]</Text>
              </View>
              <View style={styles.metaItem}>
                <Icon name="layers-outline" size={16} />
                <Text style={styles.meta}>1 / 3</Text>
              </View>
            </View>
          </View>
        </Card>

        <Card style={styles.columnCard}>
          <View style={styles.cardHeader}>
            <View style={styles.cardIcon}>
              <Icon name="message-processing-outline" color={colors.accent} />
            </View>
            <Text style={styles.cardTitle} accessibilityRole="header" aria-level={2}>
              Discuter et vérifier
            </Text>
          </View>
          <Text style={styles.description}>
            Envoyez un texte, une photo ou une vidéo à FahAIMarinana.
          </Text>
          <Link href="/verifier" asChild>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel="Parler et vérifier une information"
              style={styles.cta}
            >
              <Icon name="arrow-right" color={colors.deep} />
              <Text style={styles.ctaText}>Parler</Text>
            </InteractivePressable>
          </Link>
        </Card>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flex: 1, flexDirection: 'row', alignItems: 'stretch' },
  columnCard: {
    flex: 1,
    minHeight: 320,
    gap: 20,
    shadowColor: colors.deep,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.24,
    shadowRadius: 16,
    elevation: 3,
  },
  cardHeader: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 12 },
  cardIcon: {
    width: 44,
    height: 44,
    flexShrink: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    backgroundColor: colors.deep,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTitle: { flex: 1, color: colors.white, fontSize: 22, lineHeight: 30, fontWeight: '700' },
  headline: {
    minHeight: 140,
    backgroundColor: colors.deep,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(130,148,156,0.45)',
  },
  headlineDesktop: { flex: 1 },
  headlineAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent, marginRight: 12 },
  headlineText: { flex: 1, color: colors.muted, fontSize: 17, lineHeight: 24, fontWeight: '700' },
  scorePanel: {
    gap: 12,
    padding: 14,
    borderRadius: 14,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: 'rgba(130,148,156,0.55)',
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(130,148,156,0.45)',
  },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  meta: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  example: {
    color: colors.accent,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 12,
    backgroundColor: colors.deep,
    borderWidth: 1,
    borderColor: colors.border,
  },
  description: {
    color: colors.white,
    fontSize: 17,
    lineHeight: 26,
    marginTop: 4,
    marginBottom: 'auto',
    maxWidth: 480,
  },
  cta: {
    minHeight: 48,
    alignSelf: 'stretch',
    borderRadius: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: colors.accent,
  },
  ctaText: { color: colors.deep, fontSize: 16, lineHeight: 22, fontWeight: '700' },
});
