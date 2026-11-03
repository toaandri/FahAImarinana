import { useState } from 'react';
import { Link, useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Brand, Field, Icon, InteractivePressable, PrimaryButton } from '../components/ui';
import { colors } from '../theme';
import { register } from '../services/api';
import { useI18n } from '../components/i18n';

type FormErrors = {
  invitationToken?: string;
  email?: string;
  password?: string;
  passwordConfirmation?: string;
  status?: string;
};

export default function SignupScreen() {
  const router = useRouter();
  const { t } = useI18n();
  const { width } = useWindowDimensions();
  const narrow = width < 360;
  const [invitationToken, setInvitationToken] = useState('');
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
      invitationToken: invitationToken.trim() ? undefined : t('signup.invitationRequired'),
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
      await register(normalizedEmail, password, invitationToken.trim());
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
    <ScrollView role="main" contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
      <View style={styles.formCard}>
        <View style={styles.cardAccent} />
        <View style={[styles.form, narrow && styles.formNarrow]}>
          <Link href="/connexion" asChild>
            <InteractivePressable accessibilityRole="link" style={styles.brandLink}>
              <Brand large />
            </InteractivePressable>
          </Link>
          <Text style={[styles.heading, narrow && styles.headingNarrow]} accessibilityRole="header">
            {t('signup.heading')}
          </Text>
          <View style={styles.invitationNotice}>
            <Icon name="information-outline" color={colors.accent} size={20} />
            <Text style={styles.noticeText}>
              {t('signup.notice')}
            </Text>
          </View>
          <View style={styles.fields}>
            <Field
              label={t('signup.invitation')}
              value={invitationToken}
              onChangeText={(value) => updateField('invitationToken', () => setInvitationToken(value))}
              placeholder={t('signup.invitationPlaceholder')}
              error={errors.invitationToken}
              autoCapitalize="none"
              style={styles.field}
            />
            <Field
              label={t('login.email')}
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
                  <Text style={styles.showPasswordText}>{showPassword ? t('login.hidePassword') : t('login.showPassword')}</Text>
                </InteractivePressable>
              }
            />
            <Field
              label={t('signup.confirmPassword')}
              value={passwordConfirmation}
              onChangeText={(value) => updateField('passwordConfirmation', () => setPasswordConfirmation(value))}
              placeholder={t('signup.confirmPlaceholder')}
              error={errors.passwordConfirmation}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              style={styles.field}
            />
            <PrimaryButton
              label={t('signup.submit')}
              icon="arrow-right"
              onPress={submit}
              loading={submitting}
            />
            {errors.status ? (
              <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">
                {errors.status}
              </Text>
            ) : null}
          </View>
          <View style={styles.account}>
            <Text style={styles.accountText}>{t('signup.hasAccount')}</Text>
            <Link href="/connexion" asChild>
              <InteractivePressable accessibilityRole="link" style={styles.textLinkHitbox}>
                <Text style={styles.link}>{t('signup.back')}</Text>
              </InteractivePressable>
            </Link>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: {
    flexGrow: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  formCard: {
    width: '100%',
    maxWidth: 480,
    overflow: 'hidden',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  cardAccent: { height: 4, backgroundColor: colors.accent },
  form: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 24 },
  formNarrow: { paddingHorizontal: 16 },
  brandLink: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center' },
  heading: {
    color: colors.white,
    fontSize: 26,
    lineHeight: 34,
    fontWeight: '700',
    marginTop: 6,
    marginBottom: 8,
  },
  headingNarrow: { fontSize: 24, lineHeight: 32, marginBottom: 8 },
  invitationNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 8,
    marginBottom: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.deep,
  },
  noticeText: { flex: 1, color: colors.muted, fontSize: 14, lineHeight: 20 },
  fields: { gap: 12 },
  field: { marginBottom: 4 },
  showPassword: {
    minHeight: 44,
    minWidth: 80,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  showPasswordText: { color: colors.muted, fontSize: 13 },
  status: {
    color: '#FFD1D1',
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#FF8B8B',
    borderRadius: 10,
    backgroundColor: colors.deep,
  },
  account: { marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: colors.border, gap: 4 },
  accountText: { color: colors.white, fontSize: 15, lineHeight: 22 },
  textLinkHitbox: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start' },
  link: { color: colors.accent, fontSize: 15, lineHeight: 21, fontWeight: '700' },
});
