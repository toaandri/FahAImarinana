import { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { ActivityIndicator, Image, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Field, Icon, InteractivePressable, PageTitle, PrimaryButton, ProfileRow } from '../components/ui';
import { colors, spacing } from '../theme';
import { getProfile, logout, saveProfilePhoto } from '../services/api';

const profileLinks = [
  { icon: 'file-document-outline', label: 'Mes publications' },
  { icon: 'history', label: 'Historique des vérifications' },
  { icon: 'bell-outline', label: 'Notifications' },
  { icon: 'web', label: 'Langue : Français' },
  { icon: 'cog-outline', label: 'Paramètres' },
] as const;

export default function ProfileScreen() {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const desktop = width >= 1200;
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('[Nom de l’utilisateur]');
  const [email, setEmail] = useState('[adresse@email.mg]');
  const [notice, setNotice] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingPhoto, setSavingPhoto] = useState(false);
  const [photoError, setPhotoError] = useState('');
  const [photoNotice, setPhotoNotice] = useState('');
  useEffect(() => {
    getProfile().then((profile) => {
      setName(profile.role);
      setEmail(profile.email);
      setPhoto(profile.photo);
    }).catch((error) => setNotice(error instanceof Error ? error.message : 'Profil indisponible.'))
      .finally(() => setLoadingProfile(false));
  }, []);

  async function choosePhoto() {
    if (loadingProfile || savingPhoto) return;
    setSavingPhoto(true);
    setPhotoError('');
    setPhotoNotice('');
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'], allowsEditing: true, aspect: [1, 1], quality: 0.85, base64: true,
      });
      if (result.canceled) return;
      const imageBase64 = result.assets[0].base64;
      if (!imageBase64) throw new Error('Impossible de lire cette photo. Choisissez une autre image.');
      if (imageBase64.length > 4 * Math.ceil((2 * 1024 * 1024) / 3)) {
        throw new Error('La photo dépasse 2 Mio. Choisissez une image plus petite.');
      }
      const saved = await saveProfilePhoto(imageBase64);
      setPhoto(saved.photo);
      setPhotoNotice('Photo de profil enregistrée.');
    } catch (error) {
      setPhotoError(error instanceof Error ? error.message : 'Impossible d’enregistrer cette photo.');
    } finally {
      setSavingPhoto(false);
    }
  }

  const saveProfile = () => {
    setEditing(false);
    setNotice('Modifications conservées dans cette session. La sauvegarde du profil n’est pas encore connectée.');
  };

  return (
    <AppShell active="/profil">
      <PageTitle>Profil</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={styles.profileCard}>
          <View style={styles.identity}>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel={photo ? 'Changer la photo de profil' : 'Ajouter une photo de profil'}
              accessibilityState={{ disabled: loadingProfile || savingPhoto, busy: savingPhoto }}
              disabled={loadingProfile || savingPhoto}
              onPress={choosePhoto}
              style={styles.avatar}
            >
              {photo ? <Image source={{ uri: photo }} style={styles.avatarImage} /> : <Icon name="account-outline" size={32} color={colors.deep} />}
              <View style={styles.avatarCamera}>
                {savingPhoto ? <ActivityIndicator size="small" color={colors.deep} /> : <Icon name="camera" size={12} color={colors.deep} />}
              </View>
            </InteractivePressable>
            <Text style={styles.name}>{name}</Text>
          </View>
          {photoError ? <Text accessibilityRole="alert" style={styles.photoError}>{photoError}</Text> : null}
          {photoNotice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{photoNotice}</Text> : null}
          <View style={styles.emailRow}>
            <Icon name="email-outline" size={20} />
            <Text style={styles.email}>{email}</Text>
          </View>
          {editing ? (
            <View>
              <Field label="Nom" value={name} onChangeText={setName} placeholder="Votre nom" />
              <Field label="Adresse email" value={email} onChangeText={setEmail} placeholder="adresse@email.mg" keyboardType="email-address" autoCapitalize="none" />
              <PrimaryButton label="Enregistrer" onPress={saveProfile} />
            </View>
          ) : (
            <InteractivePressable
              accessibilityRole="button"
              onPress={() => setEditing(true)}
              style={styles.editButton}
            >
              <Icon name="pencil-outline" color={colors.white} />
              <Text style={styles.editText}>Modifier le profil</Text>
            </InteractivePressable>
          )}
          <View style={[styles.stats, width < 360 && styles.statsCompact]}>
            <Stat value="[0]" label="Publications" compact={width < 360} />
            <Stat value="[0]" label="Vérifications" compact={width < 360} />
            <Stat value="[0] %" label="Crédibilité" compact={width < 360} />
          </View>
        </Card>

        <View style={styles.links}>
          {profileLinks.map((item) => (
            <ProfileRow
              key={item.label}
              icon={item.icon}
              label={item.label}
              onPress={() => setNotice(`${item.label} : cette section sera disponible lorsque le service sera connecté.`)}
            />
          ))}
          <PrimaryButton
            label="Se déconnecter"
            icon="logout"
            outline
            onPress={async () => { await logout(); router.replace('/connexion'); }}
          />
          {notice ? <Text style={styles.notice} accessibilityLiveRegion="polite">{notice}</Text> : null}
        </View>
      </View>
    </AppShell>
  );
}

function Stat({ value, label, compact = false }: { value: string; label: string; compact?: boolean }) {
  return (
    <View style={[styles.stat, compact && styles.statCompact]}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={[styles.statLabel, compact && styles.statLabelCompact]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flexDirection: 'row', alignItems: 'flex-start' },
  profileCard: { flex: 1, minWidth: 0 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  avatar: { width: 60, height: 60, borderRadius: 40, backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center' },
  avatarImage: { width: 60, height: 60, borderRadius: 40 },
  avatarCamera: { position: 'absolute', bottom: -2, right: -2, width: 22, height: 22, borderRadius: 11, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center' },
  photoError: { color: '#ffd0d0', marginTop: 8, fontSize: 14 },
  name: { color: colors.white, fontSize: 20, lineHeight: 28, fontWeight: '700', flexShrink: 1 },
  emailRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 16, marginBottom: 16 },
  email: { color: colors.muted, fontSize: 14, lineHeight: 20, flexShrink: 1 },
  editButton: { minHeight: 48, borderRadius: 12, borderWidth: 1, borderColor: colors.accent, flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 14 },
  editText: { color: colors.white, fontSize: 15, fontWeight: '700' },
  stats: { flexDirection: 'row', marginTop: 24 },
  statsCompact: { flexDirection: 'column' },
  stat: { flex: 1, paddingHorizontal: 6, borderRightWidth: 1, borderRightColor: colors.border },
  statCompact: { flex: 0, minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 0, borderRightWidth: 0, borderBottomWidth: 1, borderBottomColor: colors.border },
  statValue: { color: colors.accent, fontSize: 20, lineHeight: 26, fontWeight: '700' },
  statLabel: { color: colors.white, fontSize: 12, lineHeight: 18, marginTop: 8 },
  statLabelCompact: { fontSize: 14, lineHeight: 20, marginTop: 0 },
  links: { flex: 1, gap: 8 },
  notice: { color: colors.muted, fontSize: 14, lineHeight: 20, marginTop: 8 },
});
