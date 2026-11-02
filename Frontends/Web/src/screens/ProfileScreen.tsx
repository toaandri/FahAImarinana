import { useState } from 'react';
import { useRouter } from 'expo-router';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Field, Icon, InteractivePressable, PageTitle, PrimaryButton, ProfileRow } from '../components/ui';
import { colors, spacing } from '../theme';

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
            <View style={styles.avatar}><Icon name="account-outline" size={32} color={colors.deep} /></View>
            <Text style={styles.name}>{name}</Text>
          </View>
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
            onPress={() => router.replace('/connexion')}
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
