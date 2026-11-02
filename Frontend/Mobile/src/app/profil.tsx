import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { HeaderBar, BottomTabs, GlassCard } from '@/components/ui';
import { palette } from '@/theme/theme';
import { getProfile, logout } from '@/services/mockData';

export default function ProfilScreen() {
  const [profile, setProfile] = useState({ name: 'Nom de l’utilisateur', email: 'adresse@email.mg', publications: 0, verifications: 0, credibility: 0 });

  useEffect(() => {
    getProfile().then(setProfile).catch((error) => {
      Alert.alert('Profil indisponible', error instanceof Error ? error.message : 'Une erreur est survenue.');
    });
  }, []);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <GlassCard style={styles.profileCard}>
<<<<<<< Updated upstream
          <Text style={styles.avatar}>N</Text>
          <Text style={styles.name}>{profile.name}</Text>
          <Text style={styles.email}>{profile.email}</Text>
          <Pressable style={styles.outlineButton}><Text style={styles.outlineText}>Modifier le profil</Text></Pressable>
=======
          <View style={styles.profileHeader}>
            <Text style={styles.avatar}>{profile.name.slice(0, 1).toUpperCase()}</Text>
            <View style={styles.identity}>
              <Text style={styles.name}>{profile.name}</Text>
              <Text style={styles.email}>{profile.email}</Text>
              <Pressable style={styles.outlineButton}>
                <Ionicons name="create-outline" size={12} color="#fff" />
                <Text style={styles.outlineText}>Modifier le profil</Text>
              </Pressable>
            </View>
          </View>
>>>>>>> Stashed changes
          <View style={styles.statsRow}>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.publications}</Text><Text style={styles.statLabel}>Publications</Text></View>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.verifications}</Text><Text style={styles.statLabel}>Vérifications</Text></View>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.credibility}%</Text><Text style={styles.statLabel}>Crédibilité</Text></View>
          </View>
        </GlassCard>

        <GlassCard style={styles.menuCard}>
          {[
            ['Mes publications', 'document-text-outline'],
            ['Historique des vérifications', 'time-outline'],
            ['Notifications', 'notifications-outline'],
            ['Langue : Français', 'language-outline'],
            ['Paramètres', 'settings-outline'],
          ].map(([label, icon]) => (
            <Pressable key={label} style={styles.menuRow}>
              <View style={styles.menuLeft}><Ionicons name={icon as any} size={18} color={palette.mint} /><Text style={styles.menuLabel}>{label}</Text></View>
              <Ionicons name="chevron-forward" size={18} color="#fff" />
            </Pressable>
          ))}
        </GlassCard>

        <Pressable style={styles.disconnectButton} onPress={async () => { await logout(); router.replace('/'); }}>
          <Ionicons name="log-out-outline" size={18} color="#fff" />
          <Text style={styles.disconnectText}>Se déconnecter</Text>
        </Pressable>
      </ScrollView>
      <BottomTabs active="profil" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 16, paddingBottom: 120 },
  profileCard: { padding: 12 },
  profileHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar: { width: 58, height: 58, borderRadius: 29, backgroundColor: palette.mint, color: '#0b2b2b', textAlign: 'center', textAlignVertical: 'center', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 21 },
  identity: { flex: 1, minWidth: 0, alignItems: 'flex-start' },
  name: { color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
  email: { color: '#fff', fontSize: 12, marginTop: 4, opacity: 0.8, fontFamily: 'Montserrat_600SemiBold_Italic' },
  outlineButton: { minHeight: 30, flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)', borderRadius: 12, paddingHorizontal: 10, marginTop: 6 },
  outlineText: { color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  statsRow: { width: '100%', flexDirection: 'row', justifyContent: 'space-between', marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.12)' },
  stat: { alignItems: 'center', flex: 1 },
  statNumber: { color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 18 },
  statLabel: { fontSize: 10, color: 'rgba(255,255,255,0.7)', marginTop: 4, fontFamily: 'Montserrat_600SemiBold_Italic' },
  menuCard: { marginTop: 18, paddingHorizontal: 12 },
  menuRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.12)' },
  menuLeft: { flexDirection: 'row', alignItems: 'center' },
  menuLabel: { color: '#fff', marginLeft: 10, fontSize: 13, fontFamily: 'Montserrat_600SemiBold_Italic' },
  disconnectButton: { marginTop: 20, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: palette.mint, borderRadius: 12, paddingVertical: 14 },
  disconnectText: { color: '#fff', marginLeft: 8, fontFamily: 'Montserrat_700Bold_Italic' },
});
