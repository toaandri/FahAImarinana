<<<<<<< Updated upstream
import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView, Image, Modal, ActivityIndicator } from 'react-native';
=======
import { useCallback, useState } from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView, Alert, Image, Modal, ActivityIndicator } from 'react-native';
>>>>>>> Stashed changes
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as ImagePicker from 'expo-image-picker';
import { router, useFocusEffect } from 'expo-router';
import { HeaderBar, BottomTabs, GlassCard } from '@/components/ui';
import { palette } from '@/theme/theme';
<<<<<<< Updated upstream
import { getProfile, logout, saveProfilePhoto } from '@/services/mockData';
import { useLanguage } from '@/i18n/LanguageProvider';
=======
import { getProfile, logout, saveProfilePhoto, saveResponseLanguage, type ResponseLanguage } from '@/services/mockData';
import { LanguageSelector } from '@/components/LanguageSelector';
>>>>>>> Stashed changes

export default function ProfilScreen() {
  const { language, persistenceFailed, setLanguage, t } = useLanguage();
  const selectedLanguageName = t(language === 'fr' ? 'languageFrench' : language === 'en' ? 'languageEnglish' : 'languageMalagasy');
  const languageLabel = t('languageSetting', { language: selectedLanguageName });
  const [profile, setProfile] = useState({ name: '', email: 'adresse@email.mg', publications: 0, verifications: 0, credibility: 0 });
  const displayName = profile.name || t('profileName');
  const [profileError, setProfileError] = useState('');
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState('');
  const [photoNotice, setPhotoNotice] = useState('');
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingPhoto, setSavingPhoto] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [languagePickerOpen, setLanguagePickerOpen] = useState(false);
  const [logoutError, setLogoutError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const [language, setLanguage] = useState<ResponseLanguage>('auto');
  const [savingLanguage, setSavingLanguage] = useState(false);
  const [languageNotice, setLanguageNotice] = useState('');

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoadingProfile(true);
    getProfile().then((saved) => {
      if (!active) return;
      setProfile(saved);
      setProfilePhoto(saved.photo);
      setLanguage(saved.language);
    }).catch((error) => {
<<<<<<< Updated upstream
      setProfileError(error instanceof Error ? error.message : '');
    }).finally(() => setLoadingProfile(false));
  }, []);
=======
      if (!active) return;
      Alert.alert('Profil indisponible', error instanceof Error ? error.message : 'Une erreur est survenue.');
    }).finally(() => { if (active) setLoadingProfile(false); });
    return () => { active = false; };
  }, []));

  async function changeLanguage(value: ResponseLanguage) {
    setSavingLanguage(true);
    setLanguageNotice('');
    try {
      const saved = await saveResponseLanguage(value);
      setLanguage(saved.language);
      setLanguageNotice('Préférence de langue enregistrée. / Voatahiry ny teny nofidina.');
    } catch (error) {
      setLanguageNotice(error instanceof Error ? error.message : 'Enregistrement impossible.');
    } finally {
      setSavingLanguage(false);
    }
  }
>>>>>>> Stashed changes

  async function chooseProfilePhoto() {
    if (loadingProfile || savingPhoto) return;
    setPhotoError('');
    setPhotoNotice('');
    setSavingPhoto(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
        base64: true,
      });
      if (result.canceled) return;
      const imageBase64 = result.assets[0].base64;
      if (!imageBase64) throw new Error('Impossible de lire cette photo. Choisissez une autre image.');
      if (imageBase64.length > 4 * Math.ceil((2 * 1024 * 1024) / 3)) {
        throw new Error('La photo dépasse 2 Mio. Choisissez une image plus petite.');
      }
      const saved = await saveProfilePhoto(imageBase64);
      setProfilePhoto(saved.photo);
      setPhotoNotice('Photo de profil enregistrée.');
    } catch (error) {
      setPhotoError(error instanceof Error ? error.message : t('photoSelectFailed'));
    } finally {
      setSavingPhoto(false);
    }
  }

  async function confirmAndLogout() {
    setLoggingOut(true);
    setLogoutError('');
    try {
      await logout();
      router.replace('/');
    } catch (error) {
      setLogoutError(error instanceof Error
        ? t('logoutServerError', { error: error.message })
        : t('logoutServerErrorGeneric'));
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <GlassCard style={styles.profileCard}>
          <View style={styles.profileHeader}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={profilePhoto ? t('changeProfilePhoto') : t('addProfilePhoto')}
              onPress={chooseProfilePhoto}
              disabled={loadingProfile || savingPhoto}
              accessibilityState={{ disabled: loadingProfile || savingPhoto, busy: savingPhoto }}
              style={styles.avatarButton}
            >
              {profilePhoto ? (
                <Image source={{ uri: profilePhoto }} style={styles.avatarImage} />
              ) : (
                <Text style={styles.avatar}>{displayName.slice(0, 1).toUpperCase()}</Text>
              )}
              <View style={styles.avatarCamera}>
                {savingPhoto ? <ActivityIndicator size="small" color={palette.ink} /> : <Ionicons name="camera" size={12} color={palette.ink} />}
              </View>
            </Pressable>
            <View style={styles.identity}>
              <Text style={styles.name}>{displayName}</Text>
              <Text style={styles.email}>{profile.email}</Text>
              <Pressable style={styles.outlineButton}>
                <Ionicons name="create-outline" size={12} color="#fff" />
                <Text style={styles.outlineText}>{t('editProfile')}</Text>
              </Pressable>
            </View>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.publications}</Text><Text style={styles.statLabel}>{t('publications')}</Text></View>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.verifications}</Text><Text style={styles.statLabel}>{t('verifications')}</Text></View>
            <View style={styles.stat}><Text style={styles.statNumber}>{profile.credibility}%</Text><Text style={styles.statLabel}>{t('credibility')}</Text></View>
          </View>
        </GlassCard>
        {profileError ? <Text accessibilityRole="alert" style={styles.photoError}>{t('profileUnavailable')}: {profileError}</Text> : null}
        {photoError ? <Text accessibilityRole="alert" style={styles.photoError}>{photoError}</Text> : null}
        {photoNotice ? <Text accessibilityLiveRegion="polite" style={styles.photoNotice}>{photoNotice}</Text> : null}

        <GlassCard style={styles.menuCard}>
<<<<<<< Updated upstream
          <View style={styles.menuRow}>
            <View style={styles.menuLeft}><Ionicons name="document-text-outline" size={18} color={palette.mint} /><Text style={styles.menuLabel}>{t('myPublications')}</Text></View>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </View>
          <View style={styles.menuRow}>
            <View style={styles.menuLeft}><Ionicons name="time-outline" size={18} color={palette.mint} /><Text style={styles.menuLabel}>{t('verificationHistory')}</Text></View>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </View>
          <View style={styles.menuRow}>
            <View style={styles.menuLeft}><Ionicons name="notifications-outline" size={18} color={palette.mint} /><Text style={styles.menuLabel}>{t('notifications')}</Text></View>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={languageLabel}
            onPress={() => setLanguagePickerOpen(true)}
            style={styles.menuRow}
          >
            <View style={styles.menuLeft}><Ionicons name="language-outline" size={18} color={palette.mint} /><Text style={styles.menuLabel}>{languageLabel}</Text></View>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </Pressable>
          <View style={[styles.menuRow, styles.menuRowLast]}>
            <View style={styles.menuLeft}><Ionicons name="settings-outline" size={18} color={palette.mint} /><Text style={styles.menuLabel}>{t('settings')}</Text></View>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </View>
=======
          <LanguageSelector value={language} onChange={(value) => void changeLanguage(value)} disabled={loadingProfile || savingLanguage} />
          {languageNotice ? <Text accessibilityLiveRegion="polite" style={styles.photoNotice}>{languageNotice}</Text> : null}
          {[
            ['Mes publications', 'document-text-outline'],
            ['Historique des vérifications', 'time-outline'],
            ['Notifications', 'notifications-outline'],
            ['Paramètres', 'settings-outline'],
          ].map(([label, icon]) => (
            <Pressable key={label} style={styles.menuRow}>
              <View style={styles.menuLeft}><Ionicons name={icon as any} size={18} color={palette.mint} /><Text style={styles.menuLabel}>{label}</Text></View>
              <Ionicons name="chevron-forward" size={18} color="#fff" />
            </Pressable>
          ))}
>>>>>>> Stashed changes
        </GlassCard>
        {persistenceFailed ? <Text accessibilityRole="alert" style={styles.photoError}>{t('languageSaveFailed')}</Text> : null}

        <Pressable
          accessibilityRole="button"
          style={styles.disconnectButton}
          onPress={() => {
            setLogoutError('');
            setConfirmLogout(true);
          }}
        >
          <Ionicons name="log-out-outline" size={18} color="#fff" />
          <Text style={styles.disconnectText}>{t('logout')}</Text>
        </Pressable>
      </ScrollView>
      <BottomTabs active="profil" />
      <Modal
        transparent
        visible={confirmLogout}
        animationType="fade"
        onRequestClose={() => {
          if (logoutError) router.replace('/');
          else setConfirmLogout(false);
        }}
      >
        <View style={styles.modalBackdrop}>
          <View
            accessibilityViewIsModal
            accessibilityLabel={logoutError ? t('logoutNotConfirmed') : t('logoutTitle')}
            style={styles.confirmCard}
          >
            <Text style={styles.confirmTitle}>{logoutError ? t('logoutNotConfirmed') : t('logoutTitle')}</Text>
            <Text style={styles.confirmMessage}>
              {logoutError || t('logoutPrompt')}
            </Text>
            {logoutError ? (
              <Pressable style={[styles.confirmButton, styles.confirmButtonStandalone]} onPress={() => router.replace('/')}>
                <Text style={styles.confirmButtonText}>{t('continue')}</Text>
              </Pressable>
            ) : (
              <View style={styles.confirmActions}>
                <Pressable
                  accessibilityRole="button"
                  disabled={loggingOut}
                  style={styles.cancelButton}
                  onPress={() => setConfirmLogout(false)}
                >
                  <Text style={styles.cancelButtonText}>{t('cancel')}</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  disabled={loggingOut}
                  style={styles.confirmButton}
                  onPress={confirmAndLogout}
                >
                  <Text style={styles.confirmButtonText}>{loggingOut ? t('loggingOut') : t('logout')}</Text>
                </Pressable>
              </View>
            )}
          </View>
        </View>
      </Modal>
      <Modal
        transparent
        visible={languagePickerOpen}
        animationType="fade"
        onRequestClose={() => setLanguagePickerOpen(false)}
      >
        <View style={styles.modalBackdrop}>
          <View accessibilityViewIsModal accessibilityLabel={t('languageTitle')} style={styles.confirmCard}>
            <Text style={styles.confirmTitle}>{t('languageTitle')}</Text>
            {([
              ['fr', 'languageFrench'],
              ['en', 'languageEnglish'],
              ['mg', 'languageMalagasy'],
            ] as const).map(([code, labelKey]) => (
              <Pressable
                key={code}
                accessibilityRole="radio"
                accessibilityState={{ checked: language === code }}
                onPress={() => {
                  setLanguagePickerOpen(false);
                  void setLanguage(code);
                }}
                style={styles.languageOption}
              >
                <Text style={styles.languageOptionText}>{t(labelKey)}</Text>
                {language === code ? <Ionicons name="checkmark" size={20} color={palette.mint} /> : null}
              </Pressable>
            ))}
            <Pressable style={[styles.cancelButton, styles.languageCancel]} onPress={() => setLanguagePickerOpen(false)}>
              <Text style={styles.cancelButtonText}>{t('cancel')}</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 16, paddingBottom: 120 },
  profileCard: { padding: 12 },
  profileHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarButton: { width: 61, height: 61, borderRadius: 31, backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center' },
  avatar: { color: '#0b2b2b', textAlign: 'center', textAlignVertical: 'center', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 21 },
  avatarImage: { width: 61, height: 61, borderRadius: 31 },
  avatarCamera: { position: 'absolute', right: -2, bottom: -2, width: 22, height: 22, borderRadius: 11, backgroundColor: palette.mint, borderWidth: 2, borderColor: palette.background, alignItems: 'center', justifyContent: 'center' },
  photoError: { marginTop: 8, color: '#ffd0d0', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  photoNotice: { marginTop: 8, color: palette.mint, fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
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
  menuRowLast: { borderBottomWidth: 0 },
  menuLeft: { flexDirection: 'row', alignItems: 'center' },
  menuLabel: { color: '#fff', marginLeft: 10, fontSize: 13, fontFamily: 'Montserrat_600SemiBold_Italic' },
  disconnectButton: { marginTop: 20, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: palette.mint, borderRadius: 12, paddingVertical: 14 },
  disconnectText: { color: '#fff', marginLeft: 8, fontFamily: 'Montserrat_700Bold_Italic' },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirmCard: { width: '100%', maxWidth: 360, borderRadius: 18, borderWidth: 1, borderColor: palette.cardBorder, backgroundColor: palette.backgroundDeep, padding: 20 },
  confirmTitle: { color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
  confirmMessage: { color: 'rgba(255,255,255,0.82)', fontSize: 13, lineHeight: 20, marginTop: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  confirmActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 20 },
  cancelButton: { minHeight: 42, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)', paddingHorizontal: 14, alignItems: 'center', justifyContent: 'center' },
  cancelButtonText: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic' },
  confirmButton: { minHeight: 42, borderRadius: 12, backgroundColor: palette.mint, paddingHorizontal: 14, alignItems: 'center', justifyContent: 'center' },
  confirmButtonStandalone: { marginTop: 20 },
  confirmButtonText: { color: palette.ink, fontFamily: 'Montserrat_700Bold_Italic' },
  languageOption: { minHeight: 48, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.12)', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  languageOptionText: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic' },
  languageCancel: { marginTop: 16, alignSelf: 'flex-end' },
});
