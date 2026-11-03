import { useState } from 'react';
import { Link, useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Brand, Field, Icon, InteractivePressable, PrimaryButton } from '../components/ui';
import { colors } from '../theme';
import { register } from '../services/api';

type FormErrors = {
  invitationToken?: string;
  email?: string;
  password?: string;
  passwordConfirmation?: string;
  status?: string;
};

export default function SignupScreen() {
  const router = useRouter();
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
      invitationToken: invitationToken.trim() ? undefined : 'Saisissez le code d’invitation fourni par un administrateur.',
      email: emailValid ? undefined : 'Saisissez une adresse email valide.',
      password: password.length >= 8 ? undefined : 'Le mot de passe doit contenir au moins 8 caractères.',
      passwordConfirmation: passwordConfirmation === password ? undefined : 'Les mots de passe ne correspondent pas.',
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
      setErrors({ status: error instanceof Error ? error.message : 'Inscription impossible.' });
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
            Créez votre compte
          </Text>
          <View style={styles.invitationNotice}>
            <Icon name="information-outline" color={colors.accent} size={20} />
            <Text style={styles.noticeText}>
              L’inscription nécessite un code d’invitation fourni par un administrateur.
            </Text>
          </View>
          <View style={styles.fields}>
            <Field
              label="Code d’invitation"
              value={invitationToken}
              onChangeText={(value) => updateField('invitationToken', () => setInvitationToken(value))}
              placeholder="Votre code d’invitation"
              error={errors.invitationToken}
              autoCapitalize="none"
              style={styles.field}
            />
            <Field
              label="Adresse email"
              value={email}
              onChangeText={(value) => updateField('email', () => setEmail(value))}
              placeholder="adresse@email.mg"
              error={errors.email}
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.field}
            />
            <Field
              label="Mot de passe"
              value={password}
              onChangeText={(value) => updateField('password', () => setPassword(value))}
              placeholder="Au moins 8 caractères"
              error={errors.password}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              style={styles.field}
              right={
                <InteractivePressable
                  accessibilityRole="button"
                  accessibilityLabel={showPassword ? 'Masquer les mots de passe' : 'Afficher les mots de passe'}
                  onPress={() => setShowPassword((value) => !value)}
                  style={styles.showPassword}
                >
                  <Icon name={showPassword ? 'eye-off-outline' : 'eye-outline'} color={colors.muted} size={19} />
                  <Text style={styles.showPasswordText}>{showPassword ? 'Masquer' : 'Afficher'}</Text>
                </InteractivePressable>
              }
            />
            <Field
              label="Confirmer le mot de passe"
              value={passwordConfirmation}
              onChangeText={(value) => updateField('passwordConfirmation', () => setPasswordConfirmation(value))}
              placeholder="Saisissez à nouveau le mot de passe"
              error={errors.passwordConfirmation}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              style={styles.field}
            />
            <PrimaryButton
              label="S’INSCRIRE"
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
            <Text style={styles.accountText}>Vous avez déjà un compte ?</Text>
            <Link href="/connexion" asChild>
              <InteractivePressable accessibilityRole="link" style={styles.textLinkHitbox}>
                <Text style={styles.link}>Retour à la connexion</Text>
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
    paddingVertical: 8,
  },
  formCard: {
    width: '100%',
    maxWidth: 440,
    overflow: 'hidden',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  cardAccent: { height: 4, backgroundColor: colors.accent },
  form: { paddingHorizontal: 24, paddingTop: 16, paddingBottom: 12 },
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
  fields: { gap: 2 },
  field: { marginBottom: 2 },
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
