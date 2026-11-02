import { useState } from 'react';
import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Brand, Field, Icon, InteractivePressable, PrimaryButton } from '../components/ui';
import { colors } from '../theme';

type Mode = 'login' | 'signup' | 'recovery';
const socialProviders = [
  { label: 'Google', icon: 'google' },
  { label: 'Apple', icon: 'apple' },
  { label: 'Facebook', icon: 'facebook' },
] as const;

export default function LoginScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const narrow = width < 360;
  const horizontalPadding = narrow ? 16 : 24;
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; status?: string }>({});

  const submit = () => {
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
    const nextErrors = {
      email: emailValid ? undefined : 'Saisissez une adresse email valide.',
      password: mode === 'recovery' || password.length >= 8 ? undefined : 'Le mot de passe doit contenir au moins 8 caractères.',
    };
    if (nextErrors.email || nextErrors.password) {
      setErrors(nextErrors);
      return;
    }
    if (mode === 'login') {
      setErrors({ status: 'Aucun service d’authentification n’est encore connecté.' });
    } else {
      setErrors({ status: 'Cette fonctionnalité sera disponible lorsque le service sera connecté.' });
    }
  };

  const heading = mode === 'login'
    ? 'Connectez-vous à votre espace'
    : mode === 'signup'
      ? 'Créez votre compte'
      : 'Réinitialisez votre mot de passe';

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
              label="Adresse email"
              value={email}
              onChangeText={(value) => { setEmail(value); setErrors((current) => ({ ...current, email: undefined })); }}
              placeholder="adresse@email.mg"
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            {mode !== 'recovery' ? (
              <Field
                label="Mot de passe"
                value={password}
                onChangeText={(value) => { setPassword(value); setErrors((current) => ({ ...current, password: undefined })); }}
                placeholder="••••••••"
                error={errors.password}
                secureTextEntry={!showPassword}
                right={
                  <InteractivePressable
                    accessibilityRole="button"
                    accessibilityLabel={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    onPress={() => setShowPassword((value) => !value)}
                    style={styles.showPassword}
                  >
                    <Icon name={showPassword ? 'eye-off-outline' : 'eye-outline'} color={colors.muted} size={19} />
                    <Text style={styles.showPasswordText}>{showPassword ? 'Masquer' : 'Afficher'}</Text>
                  </InteractivePressable>
                }
              />
            ) : null}
            {mode === 'login' ? (
              <InteractivePressable accessibilityRole="button" onPress={() => { setMode('recovery'); setErrors({}); }} style={styles.textLinkHitbox}>
                <Text style={styles.link}>Mot de passe oublié ?</Text>
              </InteractivePressable>
            ) : null}
            <PrimaryButton
              label={mode === 'login' ? 'SE CONNECTER' : mode === 'signup' ? 'S’INSCRIRE' : 'RÉINITIALISER'}
              icon="arrow-right"
              onPress={submit}
            />
            {errors.status ? (
              <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="assertive">
                {errors.status}
              </Text>
            ) : null}
          </View>

          {mode === 'login' ? (
            <>
              <View style={styles.socialDivider}>
                <View style={styles.dividerLine} />
                <Text style={styles.socialIntro}>ou se connecter avec</Text>
                <View style={styles.dividerLine} />
              </View>
              <View style={[styles.socials, narrow && styles.socialsNarrow]}>
                {socialProviders.map((provider) => (
                  <InteractivePressable
                    key={provider.label}
                    accessibilityRole="button"
                    accessibilityLabel={`Continuer avec ${provider.label}`}
                    onPress={() => setErrors({ status: `La connexion avec ${provider.label} n’est pas configurée.` })}
                    style={[styles.socialButton, narrow && styles.socialButtonNarrow]}
                  >
                    <Icon name={provider.icon} color={colors.white} size={19} />
                    <Text style={styles.socialText}>{provider.label}</Text>
                  </InteractivePressable>
                ))}
              </View>
              <View style={styles.account}>
                <Text style={styles.accountText}>Vous n’avez pas de compte ?</Text>
                <InteractivePressable accessibilityRole="button" onPress={() => { setMode('signup'); setErrors({}); }} style={styles.textLinkHitbox}>
                  <Text style={styles.link}>Inscrivez-vous ici</Text>
                </InteractivePressable>
              </View>
            </>
          ) : (
            <InteractivePressable accessibilityRole="button" onPress={() => { setMode('login'); setErrors({}); }} style={styles.textLinkHitbox}>
              <Text style={styles.link}>Retour à la connexion</Text>
            </InteractivePressable>
          )}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flexGrow: 1, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 36 },
  formCard: { width: '100%', maxWidth: 440, overflow: 'hidden', borderRadius: 22, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  cardAccent: { height: 4, backgroundColor: colors.accent },
  form: { paddingHorizontal: 24, paddingTop: 28, paddingBottom: 24 },
  brandLink: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center' },
  heading: { color: colors.white, fontSize: 26, lineHeight: 34, fontWeight: '700', marginTop: 12, marginBottom: 28 },
  headingNarrow: { fontSize: 24, lineHeight: 32, marginBottom: 20 },
  fields: { gap: 8 },
  textLinkHitbox: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start' },
  link: { color: colors.accent, fontSize: 15, lineHeight: 21, fontWeight: '700' },
  showPassword: { minHeight: 44, minWidth: 80, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  showPasswordText: { color: colors.muted, fontSize: 13 },
  socialDivider: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 28, marginBottom: 18 },
  dividerLine: { flex: 1, height: 1, backgroundColor: colors.border },
  socialIntro: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  socials: { flexDirection: 'row', gap: 10 },
  socialsNarrow: { flexWrap: 'wrap' },
  socialButton: { flex: 1, minWidth: 0, minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, justifyContent: 'center', paddingHorizontal: 8, borderWidth: 1, borderColor: colors.border, borderRadius: 12, backgroundColor: colors.deep },
  socialButtonNarrow: { flexBasis: '45%' },
  socialText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  account: { marginTop: 32, paddingTop: 20, borderTopWidth: 1, borderTopColor: colors.border, gap: 4 },
  accountText: { color: colors.white, fontSize: 15, lineHeight: 22 },
  status: { color: '#FFD1D1', fontSize: 14, lineHeight: 20, marginTop: 8, padding: 12, borderWidth: 1, borderColor: '#FF8B8B', borderRadius: 10, backgroundColor: colors.deep },
});
