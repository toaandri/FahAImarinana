import { useState } from 'react';
import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Brand, Field, Icon, InteractivePressable, PrimaryButton } from '../components/ui';
import { colors } from '../theme';
import { login } from '../services/api';
import { useI18n } from '../components/i18n';

type Mode = 'login' | 'recovery';
const socialProviders = [
  { label: 'Google', icon: 'google' },
  { label: 'Apple', icon: 'apple' },
  { label: 'Facebook', icon: 'facebook' },
] as const;

export default function LoginScreen() {
  const router = useRouter();
  const { t } = useI18n();
  const { status: routeStatus, statusKey, details } = useLocalSearchParams<{
    status?: string | string[];
    statusKey?: string | string[];
    details?: string | string[];
  }>();
  const { width } = useWindowDimensions();
  const narrow = width < 360;
  const horizontalPadding = narrow ? 16 : 24;
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; status?: string }>(() => ({
    status: Array.isArray(routeStatus) ? routeStatus[0] : routeStatus,
  }));
  const logoutErrorDetails = Array.isArray(details) ? details[0] : details;
  const logoutErrorKey = Array.isArray(statusKey) ? statusKey[0] : statusKey;
  const statusMessage = errors.status ?? (logoutErrorKey === 'profile.logoutServerError'
    ? t('profile.logoutServerError', { error: logoutErrorDetails ?? t('profile.logoutError') })
    : undefined);

  const submit = async () => {
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
    const nextErrors = {
      email: emailValid ? undefined : t('login.invalidEmail'),
      password: mode === 'recovery' || password.length >= 8 ? undefined : t('login.invalidPassword'),
    };
    if (nextErrors.email || nextErrors.password) {
      setErrors(nextErrors);
      return;
    }
    if (mode === 'login') {
      try {
        await login(email.trim(), password);
        router.replace('/actualites');
      } catch (error) {
        setErrors({ status: error instanceof Error ? error.message : t('login.failed') });
      }
    } else {
      setErrors({ status: t('login.recoveryUnavailable') });
    }
  };

  const heading = mode === 'login'
    ? t('login.heading')
    : t('login.recoveryHeading');

  return (
    <ScrollView role="main" contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
      <View style={styles.formCard}>
        <View style={styles.cardAccent} />
        <View style={[styles.form, { paddingHorizontal: horizontalPadding }]}>
          <InteractivePressable accessibilityRole="link" onPress={() => router.replace('/')} style={styles.brandLink}>
            <Brand large />
          </InteractivePressable>
          <Text style={[styles.heading, narrow && styles.headingNarrow]} accessibilityRole="header">{heading}</Text>
          <View style={styles.fields}>
            <Field
              label={t('login.email')}
              value={email}
              onChangeText={(value) => { setEmail(value); setErrors((current) => ({ ...current, email: undefined })); }}
              placeholder={t('login.emailPlaceholder')}
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.field}
            />
            {mode !== 'recovery' ? (
              <Field
                label={t('login.password')}
                value={password}
                onChangeText={(value) => { setPassword(value); setErrors((current) => ({ ...current, password: undefined })); }}
                placeholder={t('login.passwordPlaceholder')}
                error={errors.password}
                secureTextEntry={!showPassword}
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
            ) : null}
            {mode === 'login' ? (
              <InteractivePressable accessibilityRole="button" onPress={() => { setMode('recovery'); setErrors({}); }} style={styles.textLinkHitbox}>
                <Text style={styles.link}>{t('login.forgot')}</Text>
              </InteractivePressable>
            ) : null}
            <PrimaryButton
              label={mode === 'login' ? t('login.submit') : t('login.recover')}
              icon="arrow-right"
              onPress={submit}
            />
            {statusMessage ? (
              <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">
                {statusMessage}
              </Text>
            ) : null}
          </View>

          {mode === 'login' ? (
            <>
              <View style={styles.socialDivider}>
                <View style={styles.dividerLine} />
                <Text style={styles.socialIntro}>{t('login.social')}</Text>
                <View style={styles.dividerLine} />
              </View>
              <View style={[styles.socials, narrow && styles.socialsNarrow]}>
                {socialProviders.map((provider) => (
                  <InteractivePressable
                    key={provider.label}
                    accessibilityRole="button"
                    accessibilityLabel={`${t('login.social')} ${provider.label}`}
                    onPress={() => setErrors({ status: t('login.notConfigured', { provider: provider.label }) })}
                    style={[styles.socialButton, narrow && styles.socialButtonNarrow]}
                  >
                    <Icon name={provider.icon} color={colors.white} size={19} />
                    <Text style={styles.socialText}>{t(`login.${provider.label.toLowerCase()}` as 'login.google' | 'login.apple' | 'login.facebook')}</Text>
                  </InteractivePressable>
                ))}
              </View>
              <View style={styles.account}>
                <Text style={styles.accountText}>{t('login.noAccount')}</Text>
                <Link href="/inscription" asChild>
                  <InteractivePressable accessibilityRole="link" style={styles.textLinkHitbox}>
                    <Text style={styles.link}>{t('login.signUp')}</Text>
                  </InteractivePressable>
                </Link>
              </View>
            </>
          ) : (
            <InteractivePressable accessibilityRole="button" onPress={() => { setMode('login'); setErrors({}); }} style={styles.textLinkHitbox}>
              <Text style={styles.link}>{t('login.back')}</Text>
            </InteractivePressable>
          )}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 24 },
  formCard: { width: '100%', maxWidth: 480, overflow: 'hidden', borderRadius: 22, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  cardAccent: { height: 4, backgroundColor: colors.accent },
  form: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 24 },
  brandLink: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center' },
  heading: { color: colors.white, fontSize: 26, lineHeight: 34, fontWeight: '700', marginTop: 6, marginBottom: 16 },
  headingNarrow: { fontSize: 24, lineHeight: 32, marginBottom: 10 },
  fields: { gap: 12 },
  field: { marginBottom: 4 },
  textLinkHitbox: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start' },
  link: { color: colors.accent, fontSize: 15, lineHeight: 21, fontWeight: '700' },
  showPassword: { minHeight: 44, minWidth: 80, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  showPasswordText: { color: colors.muted, fontSize: 13 },
  socialDivider: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 12, marginBottom: 8 },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  socialIntro: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  socials: { flexDirection: 'row', gap: 10 },
  socialsNarrow: { flexWrap: 'wrap' },
  socialButton: { flex: 1, minWidth: 0, minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, justifyContent: 'center', paddingHorizontal: 8, borderWidth: 1, borderColor: colors.border, borderRadius: 12, backgroundColor: colors.deep },
  socialButtonNarrow: { flexBasis: '45%' },
  socialText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  account: { marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: colors.border, gap: 4 },
  accountText: { color: colors.white, fontSize: 15, lineHeight: 22 },
  status: { color: '#FFD1D1', fontSize: 14, lineHeight: 20, marginTop: 8, padding: 12, borderWidth: 1, borderColor: '#FF8B8B', borderRadius: 10, backgroundColor: colors.deep },
});
