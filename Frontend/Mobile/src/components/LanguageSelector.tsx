import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ResponseLanguage } from '@/services/mockData';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';

const choices = [{ value: 'auto', label: 'aiAutomatic' }, { value: 'fr', label: 'languageFrench' }, { value: 'mg', label: 'languageMalagasy' }] as const;

export function LanguageSelector({ value, onChange, disabled = false }: {
  value: ResponseLanguage; onChange: (language: ResponseLanguage) => void; disabled?: boolean;
}) {
  const { t } = useLanguage();
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{t('aiResponseLanguage')}</Text>
      <View style={styles.choices}>
        {choices.map((choice) => (
          <Pressable key={choice.value} accessibilityRole="radio" accessibilityLabel={t(choice.label)}
            accessibilityState={{ checked: value === choice.value, disabled }} disabled={disabled}
            onPress={() => onChange(choice.value)} style={[styles.choice, value === choice.value && styles.selected]}>
            <Text style={[styles.text, value === choice.value && styles.selectedText]}>{t(choice.label)}</Text>
          </Pressable>
        ))}
      </View>
      {value === 'auto' ? <Text style={styles.hint}>{t('aiAutoHint')}</Text> : null}
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
