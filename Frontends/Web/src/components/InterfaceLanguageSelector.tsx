import { Pressable, StyleSheet, Text, View } from 'react-native';
import { appLanguageNames, type AppLanguage, useI18n } from './i18n';
import { colors } from '../theme';

const languages: AppLanguage[] = ['mg', 'fr', 'en'];

export function InterfaceLanguageSelector() {
  const { language, setLanguage, t } = useI18n();

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{t('profile.languageTitle')}</Text>
      <View style={styles.choices} accessibilityRole="radiogroup">
        {languages.map((item) => {
          const selected = language === item;
          return (
            <Pressable
              key={item}
              accessibilityRole="radio"
              accessibilityLabel={appLanguageNames[item]}
              accessibilityState={{ checked: selected }}
              aria-checked={selected}
              onPress={() => setLanguage(item)}
              style={[styles.choice, selected && styles.selected]}
            >
              <Text style={[styles.text, selected && styles.selectedText]}>{appLanguageNames[item]}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8, marginVertical: 12 },
  label: { color: colors.white, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 14, borderRadius: 12, borderWidth: 1, borderColor: colors.accent },
  selected: { backgroundColor: colors.accent },
  text: { color: colors.white, fontSize: 14 },
  selectedText: { color: colors.deep, fontWeight: '700' },
});
