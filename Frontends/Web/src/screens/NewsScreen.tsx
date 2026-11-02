import { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, InteractivePressable, MediaPreview, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { getArticles } from '../services/api';

const filters = ['Tous', 'Vérifiés', 'Politique', 'Sport'];
export default function NewsScreen() {
  const { width } = useWindowDimensions();
  const mobile = width < 768;
  const [filter, setFilter] = useState('Tous');
  const [stories, setStories] = useState<Array<{ source: string; title: string; category: string }>>([]);
  const [error, setError] = useState('');
  useEffect(() => {
    getArticles().then((articles) => setStories(articles.map((article) => ({
      source: 'FANILO',
      title: article.titre_final,
      category: article.categorie,
    })))).catch((reason) => setError(reason instanceof Error ? reason.message : 'Actualités indisponibles.'));
  }, []);
  const visibleStories = useMemo(
    () => (filter === 'Tous' ? stories : filter === 'Vérifiés' ? [] : stories.filter((story) => story.category === filter)),
    [filter],
  );

  return (
    <AppShell active="/actualites">
      <PageTitle>Actualités</PageTitle>
      <View style={styles.filters} accessibilityRole="radiogroup">
        {filters.map((item) => {
          const selected = filter === item;
          return (
            <InteractivePressable
              key={item}
              accessibilityRole="radio"
              accessibilityLabel={`Filtrer les actualités : ${item}`}
              accessibilityState={{ checked: selected }}
              aria-checked={selected}
              onPress={() => setFilter(item)}
              style={[styles.filterButton, selected && styles.filterSelected]}
            >
              <Text style={[styles.filterText, selected && styles.filterTextSelected]}>{item}</Text>
            </InteractivePressable>
          );
        })}
      </View>
      <View style={styles.list}>
        {error ? <Text style={styles.empty}>{error}</Text> : null}
        {visibleStories.length === 0 ? (
          <Text style={styles.empty}>Aucune actualité vérifiée n’est disponible pour le moment.</Text>
        ) : visibleStories.map((story, index) => (
          <View key={`${story.source}-${index}`} style={styles.story}>
            <View style={styles.storyText}>
              <Text style={styles.source}>{story.source} [heure]</Text>
              <Text style={[styles.title, mobile && styles.titleMobile]}>{story.title}</Text>
            </View>
            <MediaPreview title={mobile ? 'Visuel' : 'Média'} compact />
          </View>
        ))}
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: spacing.xl },
  filterButton: {
    minHeight: 44,
    minWidth: 72,
    justifyContent: 'center',
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  filterSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  filterText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  filterTextSelected: { color: colors.deep },
  list: { gap: 8 },
  story: {
    minHeight: 120,
    padding: 16,
    backgroundColor: colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
    borderRadius: 16,
  },
  storyText: { flex: 1, minWidth: 0 },
  source: { color: colors.background, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 8 },
  title: { color: colors.background, fontSize: 18, lineHeight: 26, fontWeight: '700' },
  titleMobile: { fontSize: 16, lineHeight: 24 },
  empty: { color: colors.muted, fontSize: 16, lineHeight: 24 },
});
