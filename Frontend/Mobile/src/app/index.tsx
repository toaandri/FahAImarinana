import { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet, Alert } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Logo } from '@/components/ui';
import { palette, radius } from '@/theme/theme';
import { login } from '@/services/mockData';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const validate = () => {
    let valid = true;
    setEmailError('');
    setPasswordError('');

    if (!email.includes('@')) {
      setEmailError('Adresse email invalide');
      valid = false;
    }
    if (password.length < 6) {
      setPasswordError('Mot de passe invalide');
      valid = false;
    }

    return valid;
  };

  const handleLogin = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      await login(email, password);
      router.replace('/home' as any);
    } catch (error) {
      Alert.alert('Connexion impossible', error instanceof Error ? error.message : 'Une erreur est survenue.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.container}>
        <View style={styles.logoWrap}><Logo /></View>

        <View style={styles.fieldWrap}>
          <View style={styles.inputRow}>
            <Ionicons name="mail-outline" size={18} color="rgba(255,255,255,0.8)" />
            <TextInput
              value={email}
              onChangeText={setEmail}
              style={styles.input}
              placeholder="Adresse email"
              placeholderTextColor="rgba(255,255,255,0.5)"
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>
          {emailError ? <Text style={styles.error}>{emailError}</Text> : null}
        </View>

        <View style={styles.fieldWrap}>
          <View style={styles.inputRow}>
            <Ionicons name="lock-closed-outline" size={18} color="rgba(255,255,255,0.8)" />
            <TextInput
              value={password}
              onChangeText={setPassword}
              style={styles.input}
              placeholder="Mot de passe"
              secureTextEntry
              placeholderTextColor="rgba(255,255,255,0.5)"
            />
          </View>
          {passwordError ? <Text style={styles.error}>{passwordError}</Text> : null}
        </View>

        <Text style={styles.link}>Mot de passe oublié ?</Text>

        <Pressable style={[styles.primaryButton, loading && styles.primaryButtonDisabled]} onPress={handleLogin}>
          <Text style={styles.primaryButtonText}>{loading ? 'CONNEXION...' : 'SE CONNECTER'}</Text>
        </Pressable>

        <View style={styles.separatorWrap}>
          <View style={styles.separator} />
          <Text style={styles.separatorText}>ou se connecter avec</Text>
          <View style={styles.separator} />
        </View>

        <View style={styles.socialRow}>
          <Pressable style={styles.socialButton}><Ionicons name="logo-google" size={18} color="#fff" /><Text style={styles.socialText}>Google</Text></Pressable>
          <Pressable style={styles.socialButton}><Ionicons name="logo-apple" size={18} color="#fff" /><Text style={styles.socialText}>Apple</Text></Pressable>
          <Pressable style={styles.socialButton}><Ionicons name="logo-facebook" size={18} color="#fff" /><Text style={styles.socialText}>Facebook</Text></Pressable>
        </View>

        <Text style={styles.footerText}>Vous n&apos;avez pas de compte ? <Text style={styles.footerLink}>Inscrivez-vous ici</Text></Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: palette.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
    justifyContent: 'center',
  },
  logoWrap: {
    alignItems: 'center',
    marginBottom: 30,
  },
  fieldWrap: {
    marginBottom: 10,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.5)',
    paddingBottom: 10,
  },
  input: {
    flex: 1,
    color: '#fff',
    fontSize: 14,
    marginLeft: 10,
    fontStyle: 'italic',
    fontFamily: 'Montserrat_600SemiBold_Italic',
  },
  link: {
    alignSelf: 'flex-end',
    color: palette.mint,
    fontSize: 12,
    marginTop: 8,
    marginBottom: 18,
    fontFamily: 'Montserrat_600SemiBold_Italic',
  },
  primaryButton: {
    backgroundColor: palette.mint,
    borderRadius: radius.md,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 18,
  },
  primaryButtonDisabled: {
    opacity: 0.8,
  },
  primaryButtonText: {
    color: palette.ink,
    fontSize: 16,
    fontWeight: '800',
    fontFamily: 'Montserrat_700Bold_Italic',
    letterSpacing: 0.5,
  },
  separatorWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  separator: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.3)',
  },
  separatorText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 11,
    marginHorizontal: 12,
    fontFamily: 'Montserrat_600SemiBold_Italic',
  },
  socialRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  socialButton: {
    flex: 1,
    marginHorizontal: 4,
    borderRadius: 14,
    paddingVertical: 10,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  socialText: {
    color: '#fff',
    fontSize: 12,
    marginLeft: 6,
    fontFamily: 'Montserrat_600SemiBold_Italic',
  },
  footerText: {
    textAlign: 'center',
    color: '#fff',
    fontSize: 12,
    fontFamily: 'Montserrat_600SemiBold_Italic',
  },
  footerLink: {
    color: palette.mint,
  },
  error: {
    color: '#ff8b8b',
    fontSize: 10,
    marginTop: 6,
    marginLeft: 26,
  },
});
