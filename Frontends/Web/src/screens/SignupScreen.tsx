import { useState } from 'react';
import { Link, useRouter } from 'expo-router';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Field, Icon, InteractivePressable } from '../components/ui';
import { colors } from '../theme';
import { AuthBrand, authTypography } from '../components/AuthBrand';
import { register } from '../services/api';
import { useI18n } from '../components/i18n';

type FormErrors = {
  email?: string;
  password?: string;
  passwordConfirmation?: string;
  status?: string;
};

export default function SignupScreen() {
  const router = useRouter();
  const { t } = useI18n();
  const { width, height } = useWindowDimensions();
  const narrow = width < 360;
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const submit = async () => {
    const normalizedEmail = email.trim();
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail);
    const nextErrors: FormErrors = {
      email: emailValid ? undefined : t('login.invalidEmail'),
      password: password.length >= 8 ? undefined : t('login.invalidPassword'),
      passwordConfirmation: passwordConfirmation === password ? undefined : t('signup.passwordMismatch'),
    };

    if (Object.values(nextErrors).some(Boolean)) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});
    try {
      await register(normalizedEmail, password);
      router.replace('/actualites');
    } catch (error) {
      setErrors({ status: error instanceof Error ? error.message : t('signup.failed') });
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = (field: keyof FormErrors, update: () => void) => {
    update();
    setErrors((current) => ({ ...current, [field]: undefined, status: undefined }));
  };

  return (
    <ScrollView role="main" contentContainerStyle={[styles.page, { minHeight: height }, narrow && styles.pageNarrow]} keyboardShouldPersistTaps="handled">
      <View style={styles.formCard}>
        <View style={styles.form}>
          <Link href="/connexion" asChild>
            <InteractivePressable accessibilityRole="link" style={styles.brandLink}>
              <AuthBrand />
            </InteractivePressable>
          </Link>
          <Text style={styles.heading} accessibilityRole="header">
            {t('signup.heading')}
          </Text>
          <View style={styles.fields}>
            <Field
              label={t('login.email')}
              underline leadingIcon="email-outline"
              value={email}
              onChangeText={(value) => updateField('email', () => setEmail(value))}
              placeholder={t('login.emailPlaceholder')}
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.field}
            />
            <Field
              label={t('login.password')}
              underline leadingIcon="lock-outline"
              value={password}
              onChangeText={(value) => updateField('password', () => setPassword(value))}
              placeholder={t('signup.passwordPlaceholder')}
              error={errors.password}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              style={styles.field}
              right={
                <InteractivePressable
                  accessibilityRole="button"
                  accessibilityLabel={t(showPassword ? 'login.hidePassword' : 'login.showPassword')}
                  onPress={() => setShowPassword((value) => !value)}
                  style={styles.showPassword}
                >
                  <Icon name={showPassword ? 'eye-off-outline' : 'eye-outline'} color={colors.muted} size={19} />
                </InteractivePressable>
              }
            />
            <Field
              label={t('signup.confirmPassword')}
              underline leadingIcon="lock-outline"
              value={passwordConfirmation}
              onChangeText={(value) => updateField('passwordConfirmation', () => setPasswordConfirmation(value))}
              placeholder={t('signup.confirmPlaceholder')}
              error={errors.passwordConfirmation}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              style={styles.field}
            />
            <InteractivePressable accessibilityRole="button" accessibilityState={{ disabled: submitting, busy: submitting }} disabled={submitting} onPress={submit} style={styles.primaryButton}>
              {submitting ? <ActivityIndicator color={colors.deep} /> : null}
              <Text style={styles.primaryButtonText}>{t('signup.submit')}</Text>
            </InteractivePressable>
            {errors.status ? (
              <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">
                {errors.status}
              </Text>
            ) : null}
          </View>

        </View>
      </View>
          <View style={styles.account}>
            <Text style={styles.accountText}>{t('signup.hasAccount')}</Text>
            <Link href="/connexion" asChild>
              <InteractivePressable accessibilityRole="link" style={styles.textLinkHitbox}>
                <Text style={styles.link}>{t('signup.back')}</Text>
              </InteractivePressable>
            </Link>
          </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1, backgroundColor: colors.background, alignItems: 'center', paddingHorizontal: 32, paddingTop: 32, paddingBottom: 16 },
  pageNarrow: { paddingHorizontal: 20, paddingTop: 16 },
  formCard: { width: '100%', maxWidth: 520 },
  form: { width: '100%' },
  brandLink: { alignSelf: 'center', minHeight: 72, alignItems: 'center', justifyContent: 'center', marginBottom: 32 },
  heading: { color: colors.white, ...authTypography, fontWeight: '700', fontStyle: 'italic', marginBottom: 12 },
  fields: { gap: 14 },
  field: { marginBottom: 0 },
  showPassword: { minHeight: 44, minWidth: 44, alignItems: 'center', justifyContent: 'center' },
  primaryButton: { minHeight: 56, flexDirection: 'row', gap: 10, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 14, marginTop: 10, borderRadius: 16, backgroundColor: colors.accent },
  primaryButtonText: { flexShrink: 1, color: colors.deep, ...authTypography, fontWeight: '800', fontStyle: 'italic', textAlign: 'center' },
  status: { color: '#FFD1D1', ...authTypography, marginTop: 10, textAlign: 'center' },
  account: { width: '100%', maxWidth: 520, flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', columnGap: 4, marginTop: 'auto', paddingTop: 32 },
  accountText: { color: colors.white, ...authTypography, fontWeight: '600', fontStyle: 'italic', textAlign: 'center' },
  textLinkHitbox: { minHeight: 44, justifyContent: 'center' },
  link: { color: colors.accent, ...authTypography, fontWeight: '800', fontStyle: 'italic', textAlign: 'center' },
});
