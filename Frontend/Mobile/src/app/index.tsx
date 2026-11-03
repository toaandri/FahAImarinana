import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Logo } from '@/components/Logo';
import { palette } from '@/theme/theme';
import { login, requestPasswordReset, resetPassword } from '@/services/mockData';
import { useLanguage } from '@/i18n/LanguageProvider';

const socialProviders = [
  { label: 'Google', icon: 'logo-google' },
  { label: 'Apple', icon: 'logo-apple' },
  { label: 'Facebook', icon: 'logo-facebook' },
] as const;

export default function LoginScreen() {
  const { t } = useLanguage();
  const { width, height } = useWindowDimensions();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [status, setStatus] = useState('');
  const [recovering, setRecovering] = useState(false);
  const [recoveryRequested, setRecoveryRequested] = useState(false);
  const [recoveryToken, setRecoveryToken] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleLogin = async () => {
    const normalizedEmail = email.trim();
    const nextEmailError = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail) ? '' : t('invalidEmail');
    const nextPasswordError = recovering || password.length >= 8 ? '' : t('invalidPassword');
    setEmailError(nextEmailError);
    setPasswordError(nextPasswordError);
    setStatus('');
    if (nextEmailError || nextPasswordError || loading) return;

    setLoading(true);
    try {
      if (recovering) {
        if (recoveryRequested) {
          if (recoveryToken.length < 20 || newPassword.length < 8) {
            setStatus(t('recoveryInvalid'));
            return;
          }
          const result = await resetPassword(recoveryToken.trim(), newPassword);
          setStatus(result.message || t('recoverySuccess'));
          setRecovering(false);
          setRecoveryRequested(false);
          setRecoveryToken('');
          setNewPassword('');
        } else {
          const result = await requestPasswordReset(normalizedEmail);
          setRecoveryRequested(true);
          if (result.reset_token) setRecoveryToken(result.reset_token);
          setStatus(result.message || t('recoverySent'));
        }
      } else {
        await login(normalizedEmail, password);
        router.replace('/home');
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t('loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView
          contentContainerStyle={[
            styles.content,
            { paddingTop: Math.min(140, height * 0.17) },
            width < 360 && styles.contentNarrow,
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.main}>
            <View style={styles.logoWrap}>
              <Logo compact={width < 340} />
            </View>

            <View style={styles.form}>
              <View style={styles.fieldWrap}>
                <View style={[styles.inputRow, emailError ? styles.inputRowError : null]}>
                  <Ionicons name="mail-outline" size={24} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
                  <TextInput
                    value={email}
                    onChangeText={(value) => { setEmail(value); setEmailError(''); setStatus(''); }}
                    style={styles.input}
                    placeholder={t('email')}
                    placeholderTextColor={palette.textMuted}
                    accessibilityLabel={t('email')}
                    autoCapitalize="none"
                    autoCorrect={false}
                    keyboardType="email-address"
                    textContentType="emailAddress"
                    autoComplete="email"
                    returnKeyType="next"
                    underlineColorAndroid="transparent"
                  />
                </View>
                {emailError ? <Text style={styles.error} accessibilityRole="alert">{emailError}</Text> : null}
              </View>

              {!recovering ? <View style={styles.fieldWrap}>
                <View style={[styles.inputRow, passwordError ? styles.inputRowError : null]}>
                  <Ionicons name="lock-closed-outline" size={24} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
                  <TextInput
                    value={password}
                    onChangeText={(value) => { setPassword(value); setPasswordError(''); setStatus(''); }}
                    style={styles.input}
                    placeholder={t('password')}
                    placeholderTextColor={palette.textMuted}
                    accessibilityLabel={t('password')}
                    secureTextEntry={!showPassword}
                    textContentType="password"
                    autoComplete="current-password"
                    returnKeyType="go"
                    onSubmitEditing={() => { void handleLogin(); }}
                    underlineColorAndroid="transparent"
                  />
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={t(showPassword ? 'hidePassword' : 'showPassword')}
                    onPress={() => setShowPassword((shown) => !shown)}
                    hitSlop={8}
                    style={styles.passwordToggle}
                  >
                    <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={22} color={palette.textMuted} />
                  </Pressable>
                </View>
                {passwordError ? <Text style={styles.error} accessibilityRole="alert">{passwordError}</Text> : null}
              </View> : null}
              {recovering && recoveryRequested ? (
                <>
                  <View style={styles.fieldWrap}>
                    <View style={styles.inputRow}>
                      <Ionicons name="key-outline" size={24} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
                      <TextInput value={recoveryToken} onChangeText={setRecoveryToken} style={styles.input} placeholder={t('recoveryToken')} placeholderTextColor={palette.textMuted} accessibilityLabel={t('recoveryToken')} autoCapitalize="none" />
                    </View>
                  </View>
                  <View style={styles.fieldWrap}>
                    <View style={styles.inputRow}>
                      <Ionicons name="lock-closed-outline" size={24} color={palette.text} accessibilityElementsHidden importantForAccessibility="no" />
                      <TextInput value={newPassword} onChangeText={setNewPassword} style={styles.input} placeholder={t('newPassword')} placeholderTextColor={palette.textMuted} accessibilityLabel={t('newPassword')} secureTextEntry />
                    </View>
                  </View>
                </>
              ) : null}

              <Pressable
                accessibilityRole="button"
                onPress={() => { setRecovering((value) => !value); setRecoveryRequested(false); setStatus(''); setPasswordError(''); }}
                style={styles.forgotButton}
              >
                <Text style={styles.forgotText}>{recovering ? t('backToLogin') : t('forgotPassword')}</Text>
              </Pressable>

              <Pressable
                accessibilityRole="button"
                accessibilityState={{ disabled: loading, busy: loading }}
                disabled={loading}
                onPress={() => { void handleLogin(); }}
                style={({ pressed }) => [styles.primaryButton, pressed && styles.primaryButtonPressed, loading && styles.primaryButtonDisabled]}
              >
                <Text style={styles.primaryButtonText}>{loading ? t('loginLoading') : recovering ? t('recoverPassword') : t('loginTitle')}</Text>
              </Pressable>
              {status ? <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">{status}</Text> : null}

              <View style={styles.separatorWrap}>
                <View style={styles.separator} />
                <Text style={styles.separatorText}>{t('orLoginWith')}</Text>
                <View style={styles.separator} />
              </View>

              <View style={styles.socialRow}>
                {socialProviders.map((provider) => (
                  <Pressable
                    key={provider.label}
                    accessibilityRole="button"
                    accessibilityLabel={`${t('continueWith')} ${provider.label}`}
                    onPress={() => setStatus(t('socialNotConfigured', { provider: provider.label }))}
                    style={({ pressed }) => [styles.socialButton, pressed && styles.socialButtonPressed, width < 360 && styles.socialButtonNarrow]}
                  >
                    <Ionicons name={provider.icon} size={22} color={palette.text} />
                    <Text style={[styles.socialText, width < 360 && styles.socialTextNarrow]}>{provider.label}</Text>
                  </Pressable>
                ))}
              </View>
            </View>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>{t('noAccount')}</Text>
            <Pressable accessibilityRole="link" onPress={() => router.push('/inscription')} hitSlop={8}>
              <Text style={styles.footerLink}>{t('signUp')}</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#37515E' },
  keyboard: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'space-between', paddingHorizontal: 32, paddingBottom: 12 },
  contentNarrow: { paddingHorizontal: 20 },
  main: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  logoWrap: { minHeight: 52, alignItems: 'center', justifyContent: 'center', marginBottom: 48 },
  form: { width: '100%' },
  fieldWrap: { marginBottom: 20 },
  inputRow: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 16, borderBottomWidth: 2, borderBottomColor: 'rgba(255,255,255,0.55)' },
  inputRowError: { borderBottomColor: '#FF8B8B' },
  input: { flex: 1, minWidth: 0, color: palette.text, fontSize: 17, paddingVertical: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  passwordToggle: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  error: { color: '#FFD1D1', fontSize: 12, lineHeight: 18, marginTop: 6 },
  forgotButton: { minHeight: 44, alignSelf: 'flex-end', justifyContent: 'center', marginTop: -12, marginBottom: 16 },
  forgotText: { color: palette.mint, fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic' },
  primaryButton: { minHeight: 58, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16, borderRadius: 16, backgroundColor: palette.mint, shadowColor: palette.mint, shadowOpacity: 0.18, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  primaryButtonPressed: { opacity: 0.84 },
  primaryButtonDisabled: { opacity: 0.65 },
  primaryButtonText: { color: palette.ink, fontSize: 18, fontWeight: '800', fontFamily: 'Montserrat_700Bold_Italic' },
  status: { color: '#FFD1D1', fontSize: 13, lineHeight: 20, marginTop: 10, textAlign: 'center' },
  separatorWrap: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 28, marginBottom: 16 },
  separator: { flex: 1, height: 1, backgroundColor: 'rgba(255,255,255,0.45)' },
  separatorText: { color: palette.text, fontSize: 13, fontFamily: 'Montserrat_600SemiBold_Italic' },
  socialRow: { flexDirection: 'row', gap: 10 },
  socialButton: { flex: 1, minWidth: 0, minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 6, borderRadius: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.42)', backgroundColor: 'rgba(255,255,255,0.08)' },
  socialButtonPressed: { backgroundColor: 'rgba(255,255,255,0.16)' },
  socialButtonNarrow: { gap: 4, paddingHorizontal: 3 },
  socialText: { color: palette.text, fontSize: 13, fontFamily: 'Montserrat_600SemiBold_Italic' },
  socialTextNarrow: { fontSize: 11 },
  footer: { width: '100%', maxWidth: 520, alignSelf: 'center', alignItems: 'center', justifyContent: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 4, paddingTop: 28 },
  footerText: { color: palette.text, fontSize: 14, fontFamily: 'Montserrat_600SemiBold_Italic', textAlign: 'center' },
  footerLink: { color: palette.mint, fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic', textAlign: 'center' },
});
