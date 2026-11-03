import { useCallback, useState } from 'react';
import { useFocusEffect, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { ActivityIndicator, Image, Modal, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Field, Icon, InteractivePressable, PageTitle, PrimaryButton, ProfileRow } from '../components/ui';
import { colors, spacing } from '../theme';
import { getNotifications, getProfile, logout, saveProfilePhoto, updateProfile } from '../services/api';
import { InterfaceLanguageSelector } from '../components/InterfaceLanguageSelector';
import { useI18n } from '../components/i18n';

const profileLinks = [
  { icon: 'file-document-outline', label: 'profile.myPublications' },
  { icon: 'history', label: 'profile.history' },
  { icon: 'bell-outline', label: 'profile.notifications' },
  { icon: 'cog-outline', label: 'profile.settings' },
] as const;

export default function ProfileScreen() {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const { t } = useI18n();
  const desktop = width >= 1200;
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [stats, setStats] = useState({ publications: 0, verifications: 0, credibility: null as number | null });
  const [notifications, setNotifications] = useState<{ title: string; message: string }[]>([]);
  const [notice, setNotice] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingPhoto, setSavingPhoto] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [photoError, setPhotoError] = useState('');
  const [photoNotice, setPhotoNotice] = useState('');
  const [logoutConfirmationOpen, setLogoutConfirmationOpen] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setLoadingProfile(true);
    getProfile().then((profile) => {
      if (!active) return;
      setName(profile.name || profile.role);
      setEmail(profile.email);
      setPhoto(profile.photo);
      setStats({ publications: profile.publications, verifications: profile.verifications, credibility: profile.credibility });
      getNotifications().then((items) => { if (active) setNotifications(items); }).catch(() => undefined);
    }).catch((error) => { if (active) setNotice(error instanceof Error ? error.message : t('profile.unavailable')); })
      .finally(() => { if (active) setLoadingProfile(false); });
    return () => { active = false; };
  }, [t]));

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
      if (!imageBase64) throw new Error(t('profile.photoUnavailable'));
      if (imageBase64.length > 4 * Math.ceil((2 * 1024 * 1024) / 3)) {
        throw new Error(t('profile.photoTooLarge'));
      }
      const saved = await saveProfilePhoto(imageBase64);
      setPhoto(saved.photo);
      setPhotoNotice(t('profile.photoSaved'));
    } catch (error) {
      setPhotoError(error instanceof Error ? error.message : t('profile.photoSaveFailed'));
    } finally {
      setSavingPhoto(false);
    }
  }

  const saveProfile = async () => {
    try {
      const saved = await updateProfile(name, email);
      setName(saved.name);
      setEmail(saved.email);
      setEditing(false);
      setNotice(t('profile.photoSaved'));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t('profile.unavailable'));
    }
  };

  const handleLogout = async () => {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await logout();
      router.replace('/connexion');
    } catch (error) {
      const details = error instanceof Error ? error.message : t('profile.logoutError');
      router.replace({
        pathname: '/connexion',
        params: { statusKey: 'profile.logoutServerError', details },
      });
    } finally {
      setLoggingOut(false);
      setLogoutConfirmationOpen(false);
    }
  };

  return (
    <AppShell active="/profil">
      <PageTitle>{t('profile.title')}</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={styles.profileCard}>
          <View style={styles.identity}>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel={t(photo ? 'profile.changePhoto' : 'profile.addPhoto')}
              accessibilityState={{ disabled: loadingProfile || savingPhoto, busy: savingPhoto }}
              disabled={loadingProfile || savingPhoto}
              onPress={choosePhoto}
              style={styles.avatar}
            >
              {photo ? <Image source={{ uri: photo }} accessibilityLabel={name} style={styles.avatarImage} resizeMode="cover" /> : <Icon name="account-outline" size={32} color={colors.deep} />}
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
              <Field label={t('profile.name')} value={name} onChangeText={setName} placeholder={t('profile.namePlaceholder')} />
              <Field label={t('profile.email')} value={email} onChangeText={setEmail} placeholder={t('login.emailPlaceholder')} keyboardType="email-address" autoCapitalize="none" />
              <PrimaryButton label={t('profile.save')} onPress={saveProfile} />
            </View>
          ) : (
            <InteractivePressable
              accessibilityRole="button"
              onPress={() => setEditing(true)}
              style={styles.editButton}
            >
              <Icon name="pencil-outline" color={colors.white} />
              <Text style={styles.editText}>{t('profile.edit')}</Text>
            </InteractivePressable>
          )}
          <View style={[styles.stats, width < 360 && styles.statsCompact]}>
            <Stat value={String(stats.publications)} label={t('profile.publications')} compact={width < 360} />
            <Stat value={String(stats.verifications)} label={t('profile.verifications')} compact={width < 360} />
            <Stat value={stats.credibility == null ? '—' : `${stats.credibility}%`} label={t('profile.credibility')} compact={width < 360} />
          </View>
        </Card>

        <View style={styles.links}>
          <InterfaceLanguageSelector />
          {profileLinks.map((item) => (
            <ProfileRow
              key={item.label}
              icon={item.icon}
              label={t(item.label)}
              onPress={() => item.label === 'profile.notifications'
                ? setNotice(notifications.length ? notifications.map((notification) => `${notification.title} : ${notification.message}`).join('\n') : 'Aucune notification.')
                : setNotice(`${t(item.label)} : ${t('profile.sectionUnavailable')}`)}
            />
          ))}
          <PrimaryButton
            label={t('profile.logout')}
            icon="logout"
            outline
            loading={loggingOut}
            onPress={() => setLogoutConfirmationOpen(true)}
          />
          {notice ? <Text style={styles.notice} accessibilityLiveRegion="polite">{notice}</Text> : null}
        </View>
      </View>
      <Modal
        visible={logoutConfirmationOpen}
        transparent
        animationType="none"
        onRequestClose={() => { if (!loggingOut) setLogoutConfirmationOpen(false); }}
      >
        <View style={styles.modalBackdrop}>
          <View role="alertdialog" accessibilityLabel={t('profile.logoutTitle')} style={styles.confirmation}>
            <Text style={styles.confirmationTitle}>{t('profile.logoutTitle')}</Text>
            <Text style={styles.confirmationText}>{t('profile.logoutPrompt')}</Text>
            <View style={styles.confirmationActions}>
              <InteractivePressable
                accessibilityRole="button"
                disabled={loggingOut}
                onPress={() => setLogoutConfirmationOpen(false)}
                style={[styles.confirmationButton, styles.cancelButton, loggingOut && styles.disabledButton]}
              >
                <Text style={styles.cancelText}>{t('common.cancel')}</Text>
              </InteractivePressable>
              <InteractivePressable
                accessibilityRole="button"
                disabled={loggingOut}
                accessibilityState={{ disabled: loggingOut, busy: loggingOut }}
                onPress={() => void handleLogout()}
                style={[styles.confirmationButton, styles.confirmButton, loggingOut && styles.disabledButton]}
              >
                {loggingOut ? <ActivityIndicator size="small" color={colors.deep} /> : null}
                <Text style={styles.confirmText}>{loggingOut ? t('profile.loggingOut') : t('profile.logoutConfirm')}</Text>
              </InteractivePressable>
            </View>
          </View>
        </View>
      </Modal>
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
  identity: { alignItems: 'flex-start', gap: 20 },
  avatar: { width: 104, height: 104, borderRadius: 52, backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center' },
  avatarImage: { width: 104, height: 104, borderRadius: 52 },
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
  statLabel: { color: colors.white, fontSize: 14, lineHeight: 21, marginTop: 8 },
  statLabelCompact: { fontSize: 14, lineHeight: 20, marginTop: 0 },
  links: { flex: 1, gap: 12 },
  notice: { color: colors.muted, fontSize: 14, lineHeight: 20, marginTop: 8 },
  modalBackdrop: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20, backgroundColor: 'rgba(0,0,0,0.55)' },
  confirmation: { width: '100%', maxWidth: 420, gap: 16, padding: 24, borderRadius: 16, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  confirmationTitle: { color: colors.white, fontSize: 20, lineHeight: 28, fontWeight: '700' },
  confirmationText: { color: colors.muted, fontSize: 16, lineHeight: 24 },
  confirmationActions: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'flex-end', gap: 10 },
  confirmationButton: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 16, borderRadius: 12, borderWidth: 1 },
  cancelButton: { borderColor: colors.border },
  confirmButton: { borderColor: colors.accent, backgroundColor: colors.accent },
  cancelText: { color: colors.white, fontSize: 15, fontWeight: '700' },
  confirmText: { color: colors.deep, fontSize: 15, fontWeight: '700' },
  disabledButton: { opacity: 0.5 },
});
