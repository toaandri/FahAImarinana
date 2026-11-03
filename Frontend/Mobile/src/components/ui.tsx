import React from 'react';
import { View, Text, Pressable, StyleSheet, Image } from 'react-native';
import { router } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { palette } from '@/theme/theme';
import { CredibilityRing as CredibilityRingCore } from '@/components/CredibilityRing';

export { CredibilityRingCore as CredibilityRing };

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <View style={styles.logoRow}>
      <Text numberOfLines={1} style={[styles.logoText, compact && styles.logoTextCompact]}>FAH</Text>
      <View style={[styles.aiPill, compact && styles.aiPillCompact]}>
        <Text style={[styles.aiPillText, compact && styles.aiPillTextCompact]}>AI</Text>
      </View>
      <Text numberOfLines={1} style={[styles.logoText, compact && styles.logoTextCompact]}>MARINANA</Text>
    </View>
  );
}

export function HeaderBar({ title, showBack = false }: { title?: string; showBack?: boolean }) {
  return (
    <View style={styles.headerShell}>
      {showBack ? (
        <Pressable accessibilityRole="button" accessibilityLabel="Retour" onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={18} color="#fff" />
        </Pressable>
      ) : null}
      <View style={styles.headerCenter}>{title ? <Text style={styles.headerTitle}>{title}</Text> : <Logo compact />}</View>
      <View style={styles.onlineWrap}>
        <View style={styles.onlineDot} />
        <Text style={styles.onlineText}>En ligne</Text>
      </View>
    </View>
  );
}

export function GlassCard({ children, style }: { children: React.ReactNode; style?: any }) {
  return <View style={[styles.glassCard, style]}>{children}</View>;
}

export function PrimaryButton({ title, onPress }: { title: string; onPress?: () => void }) {
  return (
    <Pressable onPress={onPress as any} style={styles.primaryButton}>
      <Text style={styles.primaryButtonText}>{title}</Text>
    </Pressable>
  );
}

export function TagChip({ label, active = false, small = false }: { label: string; active?: boolean; small?: boolean }) {
  return (
    <View style={[styles.chip, active && styles.chipActive, small && styles.chipSmall]}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </View>
  );
}

export function BottomTabs({ active = 'home' }: { active?: 'home' | 'actus' | 'discussion' | 'publier' | 'profil' }) {
  const { bottom } = useSafeAreaInsets();
  const items = [
    { key: 'home', label: 'Accueil', icon: 'home-outline', route: '/home' },
    { key: 'actus', label: 'Actus', icon: 'newspaper-outline', route: '/actualites' },
    { key: 'publier', label: 'Publier', icon: 'add-outline', route: '/publier' },
    { key: 'profil', label: 'Profil', icon: 'person-outline', route: '/profil' },
  ] as const;

  return (
    <View style={[styles.tabBar, { bottom: Math.max(bottom, 12) + 8 }]} accessibilityRole="tablist">
      {items.slice(0, 2).map((item) => {
        const isActive = active === item.key;
        const color = isActive ? palette.mint : palette.textMuted;
        return (
          <Pressable
            key={item.key}
            accessibilityRole="tab"
            accessibilityLabel={item.label}
            accessibilityState={{ selected: isActive }}
            onPress={() => router.push(item.route)}
            style={styles.tabButton}
          >
            <Ionicons name={item.icon} size={20} color={color} />
            <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>{item.label}</Text>
          </Pressable>
        );
      })}
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Discuter avec l’IA"
        accessibilityHint={active === 'discussion' ? 'Écran de discussion ouvert' : 'Ouvre la vérification avec l’IA'}
        accessibilityState={{ selected: active === 'discussion' }}
        onPress={() => router.push('/discussion')}
        style={styles.centerTab}
      >
        <Ionicons name="chatbubble-ellipses-outline" size={26} color="#0E1B21" />
      </Pressable>
      {items.slice(2).map((item) => {
        const isActive = active === item.key;
        const color = isActive ? palette.mint : palette.textMuted;
        return (
          <Pressable
            key={item.key}
            accessibilityRole="tab"
            accessibilityLabel={item.label}
            accessibilityState={{ selected: isActive }}
            onPress={() => router.push(item.route)}
            style={styles.tabButton}
          >
            <Ionicons name={item.icon} size={20} color={color} />
            <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function StoryCard({ title, source, credibility, image, label = 'Dernière information', onPress }: { title: string; source: string; credibility: number; image?: string; label?: string; onPress?: () => void }) {
  return (
    <Pressable onPress={onPress} style={styles.storyCard}>
      <View style={styles.storyContentRow}>
        <View style={styles.storyImageWrap}>
          {image ? <Image source={{ uri: image }} style={styles.storyImage} /> : <View style={styles.storyImagePlaceholder} />}
          <View style={styles.storyImageScrim} />
          <View style={styles.storyBadge}><Text numberOfLines={1} style={styles.storyBadgeText}>{label}</Text></View>
          <Text numberOfLines={4} style={styles.storyImageTitle}>
            <Text style={styles.storyTitleLabel}>TITRE :</Text>
            {'\n'}{title}
          </Text>
        </View>
        <View style={styles.storyDetails}>
          <View style={styles.ringWrap}>
          <CredibilityRingCore value={credibility} size={40} />
          <Text style={styles.credibilityCaption}>Crédibilité</Text>
          </View>
          <Text numberOfLines={2} style={styles.storySource}>{source}</Text>
        </View>
      </View>
    </Pressable>
  );
}

export function SimpleListRow({ label, value }: { label: string; value?: string }) {
  return (
    <View style={styles.listRow}>
      <Text style={styles.listLabel}>{label}</Text>
      {value ? <Text style={styles.listValue}>{value}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  logoRow: { flexDirection: 'row', alignItems: 'center', flexShrink: 1 },
  logoText: { color: palette.backgroundDeep, fontSize: 20, fontWeight: '800', fontStyle: 'italic', fontFamily: 'Montserrat_800ExtraBold_Italic', flexShrink: 1 },
  logoTextCompact: { fontSize: 20 },
  aiPill: { backgroundColor: palette.backgroundDeep, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, marginHorizontal: 4 },
  aiPillCompact: { paddingHorizontal: 7, paddingVertical: 4, borderRadius: 9 },
  aiPillText: { color: palette.mint, fontSize: 17, fontWeight: '800', fontStyle: 'italic', fontFamily: 'Montserrat_800ExtraBold_Italic' },
  aiPillTextCompact: { fontSize: 21 },
  headerShell: { minHeight: 64, backgroundColor: palette.headerTint, borderBottomWidth: 2, borderBottomColor: '#1688E8', borderBottomLeftRadius: 18, borderBottomRightRadius: 18, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  headerCenter: { flex: 1, minWidth: 0, alignItems: 'flex-start' },
  headerTitle: { color: '#1b2d30', fontWeight: '700', fontFamily: 'Montserrat_700Bold_Italic' },
  backButton: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#263a40', alignItems: 'center', justifyContent: 'center' },
  onlineWrap: { flexDirection: 'row', alignItems: 'center', gap: 6, flexShrink: 0 },
  onlineDot: { width: 14, height: 14, borderRadius: 7, backgroundColor: palette.mint, borderWidth: 2, borderColor: palette.backgroundDeep },
  onlineText: { color: palette.backgroundDeep, fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic' },
  glassCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 18, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', overflow: 'hidden' },
  primaryButton: { backgroundColor: palette.mint, borderRadius: 14, paddingVertical: 14, alignItems: 'center' },
  primaryButtonText: { color: palette.ink, fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic' },
  chip: { backgroundColor: 'rgba(10,20,25,0.18)', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 8, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  chipActive: { backgroundColor: palette.mint },
  chipSmall: { paddingVertical: 6 },
  chipText: { color: '#fff', fontSize: 11, fontFamily: 'Montserrat_600SemiBold_Italic' },
  chipTextActive: { color: '#0b2b2b' },
  tabBar: { position: 'absolute', left: 16, right: 16, height: 68, borderRadius: 34, backgroundColor: 'rgba(14,27,33,0.94)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', paddingHorizontal: 8, shadowColor: '#000', shadowOpacity: 0.4, shadowRadius: 16, shadowOffset: { width: 0, height: 10 }, elevation: 12 },
  tabButton: { minWidth: 52, height: 52, flex: 1, alignItems: 'center', justifyContent: 'center', gap: 3 },
  tabLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  tabLabelActive: { color: palette.mint },
  centerTab: { width: 56, height: 56, flexShrink: 0, borderRadius: 28, borderWidth: 4, borderColor: '#0E1B21', backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center', marginTop: -26, shadowColor: palette.mint, shadowOpacity: 0.4, shadowRadius: 10, shadowOffset: { width: 0, height: 6 }, elevation: 8 },
  storyCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 18, overflow: 'hidden', padding: 8, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  storyContentRow: { flexDirection: 'row', alignItems: 'stretch', gap: 8 },
  storyBadge: { position: 'absolute', top: 8, left: 8, maxWidth: '90%', backgroundColor: 'rgba(17,21,25,0.55)', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6 },
  storyBadgeText: { color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  storyDetails: { width: 60, alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 },
  ringWrap: { alignItems: 'center' },
  credibilityCaption: { color: '#fff', fontSize: 8, marginTop: 4, fontFamily: 'Montserrat_600SemiBold_Italic' },
  storyImageWrap: { flex: 1, width: '100%', maxWidth: 303, height: 189, alignSelf: 'flex-start', borderRadius: 14, overflow: 'hidden', justifyContent: 'flex-end' },
  storyImage: StyleSheet.absoluteFill,
  storyImagePlaceholder: { ...StyleSheet.absoluteFill, backgroundColor: '#31545A' },
  storyImageScrim: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(14,27,33,0.28)' },
  storyImageTitle: { color: '#fff', fontSize: 11, lineHeight: 15, padding: 10, paddingTop: 44, fontFamily: 'Montserrat_700Bold_Italic' },
  storyTitleLabel: { color: palette.mint, fontSize: 10 },
  storySource: { width: '100%', backgroundColor: 'rgba(255,255,255,0.08)', paddingHorizontal: 4, paddingVertical: 6, borderRadius: 12, color: '#fff', textAlign: 'center', fontSize: 9, fontFamily: 'Montserrat_600SemiBold_Italic' },
  listRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.12)' },
  listLabel: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 12 },
  listValue: { color: 'rgba(255,255,255,0.75)', fontSize: 11 },
});
