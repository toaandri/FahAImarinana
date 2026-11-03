import { useState, type ComponentProps, type ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Logo } from '@/components/Logo';
import { palette } from '@/theme/theme';
import { register } from '@/services/mockData';
import { useLanguage } from '@/i18n/LanguageProvider';

type FormErrors = {
  email?: string;
  password?: string;
  confirmation?: string;
  status?: string;
};

export default function SignupScreen() {
  const { t } = useLanguage();
  const { width } = useWindowDimensions();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const submit = async () => {
    const normalizedEmail = email.trim();
    const nextErrors: FormErrors = {
      email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail) ? undefined : t('invalidEmail'),
      password: password.length >= 8 ? undefined : t('invalidPassword'),
      confirmation: confirmation === password ? undefined : t('passwordMismatch'),
    };
    if (Object.values(nextErrors).some(Boolean) || submitting) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});
    try {
      await register(normalizedEmail, password);
      router.replace('/home');
    } catch (error) {
      setErrors({ status: error instanceof Error ? error.message : t('signupFailed') });
    } finally {
      setSubmitting(false);
    }
  };

  const update = (field: keyof FormErrors, setter: (value: string) => void, value: string) => {
    setter(value);
    setErrors((current) => ({ ...current, [field]: undefined, status: undefined }));
  };

  return (
    <SafeAreaView style={styles.screen}>
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView
          contentContainerStyle={[styles.content, width < 360 && styles.contentNarrow]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.main}>
            <Pressable accessibilityRole="link" accessibilityLabel={t('backToLogin')} onPress={() => router.replace('/')} style={styles.logoWrap}>
              <Logo compact={width < 340} />
            </Pressable>

            <Text accessibilityRole="header" style={styles.heading}>{t('signupHeading')}</Text>
            <View style={styles.form}>
              <AuthInput
                icon="mail-outline"
                value={email}
                onChangeText={(value) => update('email', setEmail, value)}
                placeholder={t('email')}
                accessibilityLabel={t('email')}
                error={errors.email}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
                textContentType="emailAddress"
                autoComplete="email"
                returnKeyType="next"
              />
              <AuthInput
                icon="lock-closed-outline"
                value={password}
                onChangeText={(value) => update('password', setPassword, value)}
                placeholder={t('password')}
                accessibilityLabel={t('password')}
                error={errors.password}
                secureTextEntry={!showPassword}
                textContentType="newPassword"
                autoComplete="new-password"
                returnKeyType="next"
                trailing={
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={t(showPassword ? 'hidePassword' : 'showPassword')}
                    onPress={() => setShowPassword((shown) => !shown)}
                    hitSlop={8}
                    style={styles.passwordToggle}
                  >
                    <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={22} color={palette.textMuted} />
                  </Pressable>
                }
              />
              <AuthInput
                icon="lock-closed-outline"
                value={confirmation}
                onChangeText={(value) => update('confirmation', setConfirmation, value)}
                placeholder={t('confirmPassword')}
                accessibilityLabel={t('confirmPassword')}
                error={errors.confirmation}
                secureTextEntry={!showPassword}
                textContentType="newPassword"
                autoComplete="new-password"
                returnKeyType="go"
                onSubmitEditing={() => { void submit(); }}
              />

              <Pressable
                accessibilityRole="button"
                accessibilityState={{ disabled: submitting, busy: submitting }}
                disabled={submitting}
                onPress={() => { void submit(); }}
                style={({ pressed }) => [styles.primaryButton, pressed && styles.primaryButtonPressed, submitting && styles.primaryButtonDisabled]}
              >
                <Text style={styles.primaryButtonText}>{submitting ? t('signupLoading') : t('signupSubmit')}</Text>
              </Pressable>
              {errors.status ? <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">{errors.status}</Text> : null}
            </View>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>{t('hasAccount')}</Text>
            <Pressable accessibilityRole="link" onPress={() => router.replace('/')} hitSlop={8}>
              <Text style={styles.footerLink}>{t('backToLogin')}</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function AuthInput({
  icon,
  value,
  onChangeText,
  placeholder,
  accessibilityLabel,
  error,
  trailing,
  ...inputProps
}: {
  icon: ComponentProps<typeof Ionicons>['name'];
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  accessibilityLabel: string;
  error?: string;
  trailing?: ReactNode;
} & Omit<ComponentProps<typeof TextInput>, 'value' | 'onChangeText' | 'placeholder'>) {
  return (
    <View style={styles.fieldWrap}>
      <View style={[styles.inputRow, error ? styles.inputRowError : null]}>
        <Ionicons name={icon} size={24} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
        <TextInput
          {...inputProps}
          value={value}
          onChangeText={onChangeText}
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={palette.textMuted}
          accessibilityLabel={accessibilityLabel}
          underlineColorAndroid="transparent"
        />
        {trailing}
      </View>
      {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#37515E' },
  keyboard: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'space-between', paddingHorizontal: 32, paddingTop: 24, paddingBottom: 12 },
  contentNarrow: { paddingHorizontal: 20, paddingTop: 16 },
  main: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  logoWrap: { minHeight: 52, alignItems: 'center', justifyContent: 'center', marginBottom: 24 },
  heading: { color: palette.text, fontSize: 24, lineHeight: 32, fontFamily: 'Montserrat_700Bold_Italic', marginBottom: 12 },
  noticeText: { flex: 1, color: palette.text, fontSize: 13, lineHeight: 19 },
  form: { width: '100%' },
  fieldWrap: { marginBottom: 14 },
  inputRow: { minHeight: 54, flexDirection: 'row', alignItems: 'center', gap: 14, borderBottomWidth: 2, borderBottomColor: 'rgba(255,255,255,0.55)' },
  inputRowError: { borderBottomColor: '#FF8B8B' },
  input: { flex: 1, minWidth: 0, color: palette.text, fontSize: 16, paddingVertical: 11, fontFamily: 'Montserrat_600SemiBold_Italic' },
  passwordToggle: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  error: { color: '#FFD1D1', fontSize: 12, lineHeight: 18, marginTop: 5 },
  primaryButton: { minHeight: 56, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16, marginTop: 10, borderRadius: 16, backgroundColor: palette.mint },
  primaryButtonPressed: { opacity: 0.84 },
  primaryButtonDisabled: { opacity: 0.65 },
  primaryButtonText: { color: palette.ink, fontSize: 17, fontFamily: 'Montserrat_700Bold_Italic' },
  status: { color: '#FFD1D1', fontSize: 13, lineHeight: 20, marginTop: 10, textAlign: 'center' },
  footer: { width: '100%', maxWidth: 520, alignSelf: 'center', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 4, paddingTop: 24 },
  footerText: { color: palette.text, fontSize: 14, fontFamily: 'Montserrat_600SemiBold_Italic', textAlign: 'center' },
  footerLink: { color: palette.mint, fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic', textAlign: 'center' },
});
