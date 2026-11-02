import React from 'react';
import { View, Text, Pressable, StyleSheet, Image } from 'react-native';
import { router } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { palette, radius, spacing } from '@/theme/theme';
import { CredibilityRing as CredibilityRingCore } from '@/components/CredibilityRing';

export { CredibilityRingCore as CredibilityRing };

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <View style={styles.logoRow}>
      <Text style={[styles.logoText, compact && styles.logoTextCompact]}>FAH</Text>
      <View style={[styles.aiPill, compact && styles.aiPillCompact]}>
        <Text style={[styles.aiPillText, compact && styles.aiPillTextCompact]}>AI</Text>
      </View>
      <Text style={[styles.logoText, compact && styles.logoTextCompact]}>MARINANA</Text>
    </View>
  );
}

export function HeaderBar({ title, showBack = false }: { title?: string; showBack?: boolean }) {
  return (
    <View style={styles.headerShell}>
      {showBack ? (
        <Pressable style={styles.backButton}>
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

export function BottomTabs({ active = 'home' }: { active?: 'home' | 'actus' | 'publier' | 'profil' }) {
  const items = [
    { key: 'home', label: 'Accueil', icon: 'home-outline' },
    { key: 'actus', label: 'Actus', icon: 'newspaper-outline' },
    { key: 'publier', label: 'Publier', icon: 'add-outline' },
    { key: 'profil', label: 'Profil', icon: 'person-outline' },
  ] as const;

  return (
    <View style={styles.tabBar}>
      {items.map((item) => {
        const isActive = active === item.key;
        const isPublish = item.key === 'publier';
        const target = item.key === 'home' ? '/home' : item.key === 'actus' ? '/actualites' : item.key === 'profil' ? '/profil' : '/publier';

        return (
          <View key={item.key} style={isPublish ? styles.publishWrap : styles.tabItem}>
            {isPublish ? (
              <Pressable style={styles.centerTab} onPress={() => router.push(target as any)}>
                <Ionicons name={item.icon as any} size={28} color="#0B2B2B" />
              </Pressable>
            ) : (
              <Pressable style={styles.tabButton} onPress={() => router.push(target as any)}>
                <Ionicons name={item.icon as any} size={20} color={isActive ? palette.mint : 'rgba(255,255,255,0.7)'} />
                <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>{item.label}</Text>
              </Pressable>
            )}
          </View>
        );
      })}
    </View>
  );
}

export function StoryCard({ title, source, credibility, image, onPress }: { title: string; source: string; credibility: number; image?: string; onPress?: () => void }) {
  return (
    <Pressable onPress={onPress} style={styles.storyCard}>
      <View style={styles.storyTopRow}>
        <View style={styles.storyBadge}><Text style={styles.storyBadgeText}>Dernière information</Text></View>
        <View style={styles.ringWrap}><CredibilityRingCore value={credibility} size={60} /></View>
      </View>
      <View style={styles.storyImageWrap}>
        {image ? <Image source={{ uri: image }} style={styles.storyImage} /> : <View style={styles.storyImagePlaceholder} />}
      </View>
      <Text style={styles.storyTitle}>TITRE : <Text style={styles.storyTitleStrong}>{title}</Text></Text>
      <View style={styles.storyFooter}><Text style={styles.storySource}>{source}</Text></View>
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
  logoRow: { flexDirection: 'row', alignItems: 'center' },
  logoText: { color: '#fff', fontSize: 20, fontWeight: '800', fontStyle: 'italic', fontFamily: 'Montserrat_800ExtraBold' },
  logoTextCompact: { fontSize: 16 },
  aiPill: { backgroundColor: palette.mint, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, marginHorizontal: 4 },
  aiPillCompact: { paddingHorizontal: 5, paddingVertical: 2 },
  aiPillText: { color: palette.ink, fontSize: 17, fontWeight: '800', fontFamily: 'Montserrat_800ExtraBold' },
  aiPillTextCompact: { fontSize: 12 },
  headerShell: { backgroundColor: palette.headerTint, borderBottomLeftRadius: 18, borderBottomRightRadius: 18, paddingHorizontal: 14, paddingVertical: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { color: '#1b2d30', fontWeight: '700', fontFamily: 'Montserrat_700Bold_Italic' },
  backButton: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#263a40', alignItems: 'center', justifyContent: 'center' },
  onlineWrap: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  onlineDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: palette.mint },
  onlineText: { color: '#1c2b2e', fontSize: 11, fontFamily: 'Montserrat_600SemiBold_Italic' },
  glassCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 18, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', overflow: 'hidden' },
  primaryButton: { backgroundColor: palette.mint, borderRadius: 14, paddingVertical: 14, alignItems: 'center' },
  primaryButtonText: { color: palette.ink, fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic' },
  chip: { backgroundColor: 'rgba(10,20,25,0.18)', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 8, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  chipActive: { backgroundColor: palette.mint },
  chipSmall: { paddingVertical: 6 },
  chipText: { color: '#fff', fontSize: 11, fontFamily: 'Montserrat_600SemiBold_Italic' },
  chipTextActive: { color: '#0b2b2b' },
  tabBar: { position: 'absolute', left: 12, right: 12, bottom: 14, height: 74, borderRadius: 20, backgroundColor: 'rgba(35,45,50,0.82)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', paddingHorizontal: 8 },
  tabItem: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  publishWrap: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  tabButton: { alignItems: 'center', justifyContent: 'center', paddingVertical: 8 },
  tabLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 10, marginTop: 4, fontFamily: 'Montserrat_600SemiBold_Italic' },
  tabLabelActive: { color: palette.mint },
  centerTab: { width: 58, height: 58, borderRadius: 29, backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center', marginTop: -20, shadowColor: '#000', shadowOpacity: 0.18, shadowRadius: 10, shadowOffset: { width: 0, height: 5 } },
  storyCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 18, overflow: 'hidden', padding: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  storyTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  storyBadge: { backgroundColor: 'rgba(17,21,25,0.2)', borderRadius: 12, paddingHorizontal: 12, paddingVertical: 6 },
  storyBadgeText: { color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  ringWrap: { marginRight: 8 },
  storyImageWrap: { height: 140, borderRadius: 14, overflow: 'hidden', marginTop: 12, marginBottom: 10 },
  storyImage: { width: '100%', height: '100%' },
  storyImagePlaceholder: { flex: 1, backgroundColor: '#646d70' },
  storyTitle: { color: '#fff', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic', marginBottom: 8 },
  storyTitleStrong: { color: '#fff', fontWeight: '800' },
  storyFooter: { alignItems: 'flex-end' },
  storySource: { backgroundColor: 'rgba(255,255,255,0.08)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  listRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.12)' },
  listLabel: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 12 },
  listValue: { color: 'rgba(255,255,255,0.75)', fontSize: 11 },
});
