import { useState } from 'react';
import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Field, Icon, InteractivePressable } from '../components/ui';
import { colors } from '../theme';
import { login, requestPasswordReset, resetPassword } from '../services/api';
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
  const { width, height } = useWindowDimensions();
  const narrow = width < 360;
  const logoSize = Math.min(48, Math.max(21, (width - 48) / 15));
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [recoveryRequested, setRecoveryRequested] = useState(false);
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
      password: mode === 'recovery'
        ? (recoveryRequested && newPassword.length < 8 ? t('login.invalidPassword') : undefined)
        : (password.length >= 8 ? undefined : t('login.invalidPassword')),
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
    } else if (recoveryRequested) {
      if (resetToken.length < 20 || newPassword.length < 8) {
        setErrors({ status: t('login.resetInvalid') });
        return;
      }
      try {
        await resetPassword(resetToken.trim(), newPassword);
        setErrors({ status: t('login.resetSuccess') });
        setMode('login');
        setRecoveryRequested(false);
        setResetToken('');
        setNewPassword('');
      } catch (error) {
        setErrors({ status: error instanceof Error ? error.message : t('login.failed') });
      }
    } else {
      try {
        const result = await requestPasswordReset(email.trim());
        setRecoveryRequested(true);
        if (result.reset_token) setResetToken(result.reset_token);
        setErrors({ status: result.message });
      } catch (error) {
        setErrors({ status: error instanceof Error ? error.message : t('login.failed') });
      }
    }
  };

  const heading = mode === 'login'
    ? t('login.heading')
    : t('login.recoveryHeading');

  return (
    <ScrollView role="main" contentContainerStyle={[styles.page, { minHeight: height }]} keyboardShouldPersistTaps="handled">
      <View style={styles.formCard}>
        <View style={styles.form}>
          <InteractivePressable accessibilityRole="link" onPress={() => router.replace('/')} style={styles.brandLink}>
            <Text accessibilityLabel="FAH AI MARINANA" style={[styles.wordmark, { fontSize: logoSize, lineHeight: logoSize * 1.3 }]}>FAH <Text style={styles.wordmarkAccent}>AI</Text> MARINANA</Text>
          </InteractivePressable>
          {mode === 'recovery' ? <Text style={styles.heading} accessibilityRole="header">{heading}</Text> : null}
          <View style={styles.fields}>
            <Field
              label={t('login.email')}
              underline leadingIcon="email-outline"
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
                underline leadingIcon="lock-outline"
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
                  </InteractivePressable>
                }
              />
            ) : null}
            {mode === 'recovery' && recoveryRequested ? (
              <>
                <Field label={t('login.resetToken')} value={resetToken} onChangeText={setResetToken} placeholder={t('login.resetTokenPlaceholder')} style={styles.field} />
                <Field label={t('login.newPassword')} value={newPassword} onChangeText={setNewPassword} placeholder={t('login.passwordPlaceholder')} secureTextEntry style={styles.field} />
              </>
            ) : null}
            {mode === 'login' ? (
              <InteractivePressable accessibilityRole="button" onPress={() => { setMode('recovery'); setRecoveryRequested(false); setErrors({}); }} style={styles.forgotLink}>
                <Text style={styles.link}>{t('login.forgot')}</Text>
              </InteractivePressable>
            ) : null}
            <InteractivePressable accessibilityRole="button" onPress={submit} style={styles.submitButton}>
              <Text style={styles.submitText}>{mode === 'login' ? t('login.submit') : t('login.recover')}</Text>
            </InteractivePressable>
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

            </>
          ) : (
            <InteractivePressable accessibilityRole="button" onPress={() => { setMode('login'); setErrors({}); }} style={styles.textLinkHitbox}>
              <Text style={styles.link}>{t('login.back')}</Text>
            </InteractivePressable>
          )}
        </View>
      </View>
      {mode === 'login' ? (
              <View style={styles.account}>
                <Text style={styles.accountText}>{t('login.noAccount')}</Text>
                <Link href="/inscription" asChild>
                  <InteractivePressable accessibilityRole="link" style={styles.textLinkHitbox}>
                    <Text style={styles.link}>{t('login.signUp')}</Text>
                  </InteractivePressable>
                </Link>
              </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1, backgroundColor: colors.background, alignItems: 'center', paddingHorizontal: 24, paddingTop: 48, paddingBottom: 24 },
  formCard: { width: '100%', maxWidth: 580, marginTop: 'auto' },
  form: { width: '100%' },
  brandLink: { alignSelf: 'center', minHeight: 60, justifyContent: 'center', marginBottom: 56 },
  wordmark: { color: colors.white, fontWeight: '900', fontStyle: 'italic', textAlign: 'center', letterSpacing: -1 },
  wordmarkAccent: { color: colors.accent },
  heading: { color: colors.white, fontSize: 26, lineHeight: 34, fontWeight: '700', marginBottom: 24 },
  fields: { gap: 12 },
  field: { marginBottom: 8 },
  textLinkHitbox: { minHeight: 44, justifyContent: 'center' },
  forgotLink: { minHeight: 44, alignSelf: 'flex-end', justifyContent: 'center', marginBottom: 12 },
  link: { color: colors.accent, fontSize: 16, lineHeight: 24, fontWeight: '800', fontStyle: 'italic' },
  showPassword: { minHeight: 44, minWidth: 44, alignItems: 'center', justifyContent: 'center' },
  submitButton: { minHeight: 72, paddingVertical: 18, paddingHorizontal: 20, borderRadius: 22, backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center', boxShadow: '0 12px 30px rgba(0,255,197,0.12)' },
  submitText: { color: colors.deep, fontSize: 22, lineHeight: 30, fontWeight: '900', fontStyle: 'italic', textTransform: 'uppercase', textAlign: 'center' },
  socialDivider: { flexDirection: 'row', alignItems: 'center', gap: 16, marginTop: 36, marginBottom: 20 },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  socialIntro: { flexShrink: 1, color: colors.white, fontSize: 16, lineHeight: 24, fontWeight: '700', fontStyle: 'italic', textAlign: 'center' },
  socials: { flexDirection: 'row', gap: 12 },
  socialsNarrow: { flexWrap: 'wrap' },
  socialButton: { flex: 1, minWidth: 0, minHeight: 64, flexDirection: 'row', alignItems: 'center', gap: 10, justifyContent: 'center', paddingHorizontal: 8, borderWidth: 1, borderColor: colors.border, borderRadius: 20, backgroundColor: colors.surface },
  socialButtonNarrow: { flexBasis: '45%' },
  socialText: { flexShrink: 1, color: colors.white, fontSize: 15, lineHeight: 22, fontWeight: '800', fontStyle: 'italic' },
  account: { width: '100%', maxWidth: 640, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', columnGap: 6, marginTop: 'auto', paddingTop: 64 },
  accountText: { color: colors.white, fontSize: 16, lineHeight: 24, fontStyle: 'italic', textAlign: 'center' },
  status: { color: '#FFD1D1', fontSize: 14, lineHeight: 20, marginTop: 8, padding: 12, borderWidth: 1, borderColor: '#FF8B8B', borderRadius: 10, backgroundColor: colors.deep },
});
