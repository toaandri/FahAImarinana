import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ResponseLanguage } from '@/services/mockData';
import { palette } from '@/theme/theme';

const choices = [{ value: 'auto', label: 'Auto' }, { value: 'fr', label: 'Français' }, { value: 'mg', label: 'Malagasy' }] as const;

export function LanguageSelector({ value, onChange, disabled = false }: {
  value: ResponseLanguage; onChange: (language: ResponseLanguage) => void; disabled?: boolean;
}) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Langue des réponses IA / Tenin’ny valiny</Text>
      <View style={styles.choices}>
        {choices.map((choice) => (
          <Pressable key={choice.value} accessibilityRole="radio" accessibilityLabel={choice.label}
            accessibilityState={{ checked: value === choice.value, disabled }} disabled={disabled}
            onPress={() => onChange(choice.value)} style={[styles.choice, value === choice.value && styles.selected]}>
            <Text style={[styles.text, value === choice.value && styles.selectedText]}>{choice.label}</Text>
          </Pressable>
        ))}
      </View>
      {value === 'auto' ? <Text style={styles.hint}>Auto suit la langue de la question. Vous pouvez choisir explicitement.</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8, marginVertical: 12 },
  label: { color: '#fff', fontSize: 12 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 14, borderRadius: 12, borderWidth: 1, borderColor: palette.mint },
  selected: { backgroundColor: palette.mint },
  text: { color: '#fff', fontSize: 13 },
  selectedText: { color: palette.ink, fontWeight: '700' },
  hint: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
});
