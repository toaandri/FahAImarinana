import { Link } from 'expo-router';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, CredibilityBadge, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';

export default function HomeScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;

  return (
    <AppShell active="/">
      <PageTitle>Accueil</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={styles.columnCard}>
          <Text style={styles.cardTitle}>Dernière information</Text>
          <View style={styles.headline}>
            <View style={styles.headlineAccent} />
            <Text style={styles.headlineText}>[Titre de l’information]</Text>
          </View>
          <CredibilityBadge value="85 %" />
          <View style={styles.metaRow}>
            <Text style={styles.meta}>[Source]</Text>
            <Text style={styles.meta}>1 / 3</Text>
            <Text style={styles.example}>Exemple</Text>
          </View>
        </Card>

        <Card style={styles.columnCard}>
          <Text style={styles.cardTitle}>Discuter et vérifier</Text>
          <Text style={styles.description}>
            Envoyez un texte, une photo ou une vidéo à FahAIMarinana.
          </Text>
          <Link href="/verifier" asChild>
            <InteractivePressable accessibilityRole="button" style={styles.cta}>
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
  columnsDesktop: { flexDirection: 'row', alignItems: 'stretch' },
  columnCard: { flex: 1, minHeight: 320 },
  cardTitle: { color: colors.white, fontSize: 22, lineHeight: 30, fontWeight: '700', marginBottom: 20 },
  headline: {
    minHeight: 140,
    backgroundColor: colors.deep,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    marginBottom: 20,
    borderRadius: 12,
  },
  headlineAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent, marginRight: 12 },
  headlineText: { flex: 1, color: colors.muted, fontSize: 17, lineHeight: 24, fontWeight: '700' },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, alignItems: 'center', marginTop: 12 },
  meta: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  example: { color: colors.muted, fontSize: 14, lineHeight: 20, marginLeft: 'auto' },
  description: { color: colors.white, fontSize: 17, lineHeight: 25, marginTop: 20, marginBottom: 'auto' },
  cta: { minHeight: 48, borderRadius: 12, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.accent },
  ctaText: { color: colors.deep, fontSize: 15, lineHeight: 20, fontWeight: '700' },
});
