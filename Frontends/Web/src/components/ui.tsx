import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Link } from 'expo-router';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  AccessibilityInfo,
  ActivityIndicator,
  Animated,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
  type PressableProps,
} from 'react-native';
import { colors, spacing } from '../theme';
import { useI18n } from './i18n';

export type IconName = keyof typeof MaterialCommunityIcons.glyphMap;

const ReduceMotionContext = createContext(true);

export function InteractionProvider({ children }: { children: ReactNode }) {
  const [reduceMotion, setReduceMotion] = useState(true);

  useEffect(() => {
    let active = true;
    let preferenceChanged = false;
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (value) => {
      preferenceChanged = true;
      setReduceMotion(value);
    });

    AccessibilityInfo.isReduceMotionEnabled()
      .then((value) => {
        if (active && !preferenceChanged) setReduceMotion(value);
      })
      .catch((error: unknown) => {
        console.error('Impossible de lire la préférence de réduction des animations.', error);
      });

    return () => {
      active = false;
      subscription.remove();
    };
  }, []);

  return <ReduceMotionContext.Provider value={reduceMotion}>{children}</ReduceMotionContext.Provider>;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function InteractivePressable({
  style,
  onFocus,
  onBlur,
  onPressIn,
  onPressOut,
  onHoverIn,
  onHoverOut,
  disabled,
  ...props
}: PressableProps) {
  const reduceMotion = useContext(ReduceMotionContext);
  const [focused, setFocused] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [pressed, setPressed] = useState(false);
  const [scale] = useState(() => new Animated.Value(1));
  const [opacity] = useState(() => new Animated.Value(1));

  useEffect(() => {
    if (reduceMotion || disabled) {
      scale.setValue(1);
      opacity.setValue(disabled ? 0.5 : 1);
    } else {
      opacity.setValue(1);
    }
  }, [disabled, opacity, reduceMotion, scale]);

  const animateInteraction = (toScale: number, toOpacity: number) => {
    Animated.parallel([
      Animated.timing(scale, {
        toValue: reduceMotion || disabled ? 1 : toScale,
        duration: reduceMotion ? 0 : 180,
        useNativeDriver: false,
      }),
      Animated.timing(opacity, {
        toValue: disabled ? 0.5 : reduceMotion ? 1 : toOpacity,
        duration: reduceMotion ? 0 : 180,
        useNativeDriver: false,
      }),
    ]).start();
  };

  return (
    <AnimatedPressable
      {...props}
      disabled={disabled}
      onFocus={(event) => {
        setFocused(true);
        onFocus?.(event);
      }}
      onBlur={(event) => {
        setFocused(false);
        onBlur?.(event);
      }}
      onPressIn={(event) => {
        setPressed(true);
        if (!disabled) animateInteraction(0.98, 0.84);
        onPressIn?.(event);
      }}
      onPressOut={(event) => {
        setPressed(false);
        animateInteraction(hovered ? 1.015 : 1, hovered ? 0.94 : 1);
        onPressOut?.(event);
      }}
      onHoverIn={(event) => {
        setHovered(true);
        if (!disabled) animateInteraction(1.015, 0.94);
        onHoverIn?.(event);
      }}
      onHoverOut={(event) => {
        setHovered(false);
        animateInteraction(1, 1);
        onHoverOut?.(event);
      }}
      style={[
        typeof style === 'function' ? style({ pressed }) : style,
        focused && styles.focusVisible,
        { opacity },
        { transform: [{ scale }] },
      ]}
    />
  );
}

export function Icon({
  name,
  size = 22,
  color = colors.muted,
}: {
  name: IconName;
  size?: number;
  color?: string;
}) {
  return <MaterialCommunityIcons name={name} size={size} color={color} accessible={false} />;
}

export function Brand({ large = false, compact = false }: { large?: boolean; compact?: boolean }) {
  return (
    <Text style={[styles.brand, large && styles.brandLarge, compact && styles.brandCompact]}>
      <Text style={[styles.brandText, large && styles.brandTextLarge]}>FAH </Text>
      <Text style={styles.brandAccent}>AI</Text>
      <Text style={[styles.brandText, large && styles.brandTextLarge]}> MARINANA</Text>
    </Text>
  );
}

const navigation = [
  { section: 'navigation.discover', label: 'navigation.home', icon: 'home-outline', href: '/' },
  { section: 'navigation.discover', label: 'navigation.news', icon: 'newspaper-variant-outline', href: '/actualites' },
  { section: 'navigation.participate', label: 'navigation.discuss', icon: 'message-processing-outline', href: '/verifier' },
  { section: 'navigation.participate', label: 'navigation.publish', icon: 'plus', href: '/publier' },
  { section: 'navigation.account', label: 'navigation.profile', icon: 'account-outline', href: '/profil' },
] as const;

export function TopNav({ active, onNavigate }: { active?: string; onNavigate?: () => void }) {
  const { t } = useI18n();
  const sections = [...new Set(navigation.map((item) => item.section))];

  return (
    <View
      role="navigation"
      accessibilityLabel={t('navigation.main')}
      style={styles.nav}
    >
      {sections.map((section) => (
        <View key={section} style={styles.navSection}>
          <Text style={styles.navSectionLabel}>{t(section)}</Text>
          <View style={styles.navItems}>
            {navigation.filter((item) => item.section === section).map((item) => {
              const selected = active === item.href;
              const isChat = item.href === '/verifier';
              const color = selected || isChat ? colors.accent : colors.muted;
              const label = t(item.label);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  asChild
                  accessibilityRole="link"
                  accessibilityLabel={label}
                  aria-current={selected ? 'page' : undefined}
                >
                  <InteractivePressable
                    onPress={onNavigate}
                    style={StyleSheet.flatten([
                      styles.navItem,
                      selected && styles.navItemSelected,
                    ])}
                  >
                    {selected ? <View style={styles.navActiveMarker} /> : null}
                    <View style={[styles.navIcon, isChat && styles.chatIcon]}>
                      <Icon name={item.icon} size={isChat ? 24 : 22} color={isChat ? colors.deep : color} />
                    </View>
                    <Text style={[
                      styles.navLabel,
                      { color },
                      selected && styles.navLabelSelected,
                    ]}>
                      {label}
                    </Text>
                  </InteractivePressable>
                </Link>
              );
            })}
          </View>
        </View>
      ))}
    </View>
  );
}

function MobileNavigation({
  active,
  horizontalPadding,
  open,
  onNavigate,
  onCloseComplete,
}: {
  active: string;
  horizontalPadding: number;
  open: boolean;
  onNavigate: () => void;
  onCloseComplete: () => void;
}) {
  const { t } = useI18n();
  const reduceMotion = useContext(ReduceMotionContext);
  const [progress] = useState(() => new Animated.Value(open && reduceMotion ? 1 : 0));

  useEffect(() => {
    if (reduceMotion) {
      progress.setValue(open ? 1 : 0);
      if (!open) onCloseComplete();
      return;
    }

    const animation = Animated.timing(progress, {
      toValue: open ? 1 : 0,
      duration: 180,
      useNativeDriver: false,
    });
    animation.start(({ finished }) => {
      if (finished && !open) onCloseComplete();
    });
    return () => animation.stop();
  }, [onCloseComplete, open, progress, reduceMotion]);

  return (
    <Animated.View
      role="region"
      accessibilityLabel={t('navigation.menu')}
      style={[
        styles.mobileNavigation,
        { paddingHorizontal: horizontalPadding, opacity: progress },
        { transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [-6, 0] }) }] },
      ]}
    >
      <TopNav active={active} onNavigate={onNavigate} />
    </Animated.View>
  );
}

export function AppShell({
  active,
  children,
  fillHeight = false,
}: {
  active: string;
  children: ReactNode;
  fillHeight?: boolean;
}) {
  const { t } = useI18n();
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;
  const horizontalPadding = width >= 1200 ? 48 : width >= 768 ? 32 : width < 360 ? 16 : 20;
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [navigationMounted, setNavigationMounted] = useState(false);
  const activeLabel = t(navigation.find((item) => item.href === active)?.label ?? 'navigation.main');
  const closeMobileNavigation = useCallback(() => setNavigationOpen(false), []);
  const completeMobileNavigationExit = useCallback(() => setNavigationMounted(false), []);
  const toggleNavigation = () => {
    if (navigationOpen) {
      setNavigationOpen(false);
      return;
    }
    setNavigationMounted(true);
    setNavigationOpen(true);
  };

  return (
    <View style={[styles.app, desktop && styles.appDesktop]}>
      {desktop ? (
        <View role="complementary" accessibilityLabel={t('navigation.sidebar')} style={styles.sidebar}>
          <Link href="/" asChild accessibilityRole="link" accessibilityLabel={t('navigation.homeBrand')}>
            <InteractivePressable style={styles.sidebarBrand}>
              <Text style={styles.sidebarBrandText}>
                FAH <Text style={styles.sidebarBrandAccent}>AI</Text> MARINANA
              </Text>
            </InteractivePressable>
          </Link>
          <TopNav active={active} />
          <View style={styles.sidebarStatus}>
            <View style={styles.onlineDot} />
            <Text style={styles.sidebarStatusText}>{t('navigation.online')}</Text>
          </View>
        </View>
      ) : (
        <View style={styles.header}>
          <View style={[styles.headerInner, { paddingHorizontal: horizontalPadding }]}>
            <Brand compact={width < 360} />
            <View style={[styles.headerActions, width < 360 && styles.headerActionsCompact]}>
              <View style={[styles.currentPage, width < 360 && styles.currentPageCompact]}>
                <View style={styles.onlineDot} />
                <Text style={[styles.currentPageText, width < 360 && styles.currentPageTextCompact]}>{activeLabel}</Text>
              </View>
              <InteractivePressable
                accessibilityRole="button"
                accessibilityLabel={t(navigationOpen ? 'navigation.close' : 'navigation.open')}
                accessibilityState={{ expanded: navigationOpen }}
                aria-expanded={navigationOpen}
                onPress={toggleNavigation}
                style={styles.menuToggle}
              >
                <Icon name={navigationOpen ? 'close' : 'menu'} color={colors.deep} />
              </InteractivePressable>
            </View>
          </View>
          {navigationMounted ? (
            <MobileNavigation
              active={active}
              horizontalPadding={horizontalPadding}
              open={navigationOpen}
              onNavigate={closeMobileNavigation}
              onCloseComplete={completeMobileNavigationExit}
            />
          ) : null}
        </View>
      )}
      <ScrollView
        role="main"
        style={[styles.page, desktop && styles.pageDesktop]}
        contentContainerStyle={[
          styles.pageInner,
          fillHeight && styles.pageInnerFill,
          { paddingHorizontal: horizontalPadding },
        ]}
        keyboardShouldPersistTaps="handled"
      >
        {children}
      </ScrollView>
    </View>
  );
}

export function PageTitle({ children }: { children: ReactNode }) {
  const { width } = useWindowDimensions();
  const titleSize = width < 768 ? styles.pageTitleMobile : width < 1200 ? styles.pageTitleTablet : null;
  return <Text style={[styles.pageTitle, titleSize]} accessibilityRole="header">{children}</Text>;
}

export function Card({
  children,
  style,
}: {
  children: ReactNode;
  style?: object;
}) {
  const { width } = useWindowDimensions();
  return <View style={[styles.card, width < 768 && styles.cardMobile, style]}>{children}</View>;
}

export function PrimaryButton({
  label,
  onPress,
  icon,
  disabled = false,
  loading = false,
  outline = false,
}: {
  label: string;
  onPress: () => void;
  icon?: IconName;
  disabled?: boolean;
  loading?: boolean;
  outline?: boolean;
}) {
  const { t } = useI18n();
  return (
    <InteractivePressable
      accessibilityRole="button"
      accessibilityLabel={loading ? `${label}, ${t('common.loading')}` : label}
      accessibilityState={{ disabled, busy: loading }}
      aria-busy={loading}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        outline && styles.buttonOutline,
        (disabled || loading) && styles.buttonDisabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      <View style={styles.buttonContent}>
        {loading ? (
          <ActivityIndicator color={outline ? colors.accent : colors.deep} />
        ) : icon ? (
          <Icon name={icon} color={outline ? colors.accent : colors.deep} />
        ) : null}
        <Text style={[styles.buttonText, outline && styles.buttonOutlineText]}>{label}</Text>
      </View>
    </InteractivePressable>
  );
}

export function Field({
  label,
  value,
  onChangeText,
  placeholder,
  error,
  secureTextEntry,
  multiline = false,
  numberOfLines,
  keyboardType,
  autoCapitalize,
  right,
  style,
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  error?: string;
  secureTextEntry?: boolean;
  multiline?: boolean;
  numberOfLines?: number;
  keyboardType?: 'default' | 'email-address';
  autoCapitalize?: 'none' | 'sentences';
  right?: ReactNode;
  style?: object;
}) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={[styles.fieldGroup, style]}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.inputWrap, multiline && styles.textAreaWrap, error && styles.inputError, focused && styles.inputFocused]}>
        <TextInput
          accessibilityLabel={label}
          accessibilityHint={error}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          secureTextEntry={secureTextEntry}
          multiline={multiline}
          numberOfLines={numberOfLines}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          style={[styles.input, multiline && styles.textArea]}
        />
        {right}
      </View>
      {error ? <Text style={styles.errorText} accessibilityLiveRegion="polite">{error}</Text> : null}
    </View>
  );
}

export function CredibilityBadge({
  value,
  caption,
}: {
  value: string;
  caption?: string;
}) {
  const { t } = useI18n();
  return (
    <View style={styles.credibilityRow}>
      <View style={styles.scoreBox}>
        <Text style={styles.score}>{value}</Text>
      </View>
      <Text style={styles.credibilityCaption}>{caption ?? t('profile.credibility')}</Text>
    </View>
  );
}

export function MediaPreview({
  uri,
  title,
  onRemove,
  compact = false,
}: {
  uri?: string;
  title: string;
  onRemove?: () => void;
  compact?: boolean;
}) {
  const { width } = useWindowDimensions();
  const compactWidth = width < 768 ? 112 : 204;
  return (
    <View style={[styles.mediaPreview, compact && [styles.mediaPreviewCompact, { width: compactWidth }]]}>
      {uri ? <Image source={{ uri }} style={styles.mediaImage} resizeMode="cover" /> : null}
      <View style={styles.mediaAccent} />
      <Text style={styles.mediaText}>{title}</Text>
      {onRemove ? (
        <InteractivePressable
          accessibilityRole="button"
          accessibilityLabel={`Supprimer ${title}`}
          onPress={onRemove}
          hitSlop={8}
          style={styles.mediaRemove}
        >
          <Icon name="close" size={18} />
        </InteractivePressable>
      ) : null}
    </View>
  );
}

export function ProfileRow({
  icon,
  label,
  onPress,
}: {
  icon: IconName;
  label: string;
  onPress: () => void;
}) {
  return (
    <InteractivePressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [styles.profileRow, pressed && styles.pressed]}
    >
      <Icon name={icon} color={colors.accent} />
      <Text style={styles.profileRowLabel}>{label}</Text>
      <Icon name="chevron-right" />
    </InteractivePressable>
  );
}

const styles = StyleSheet.create({
  app: { flex: 1, backgroundColor: colors.white },
  appDesktop: { flexDirection: 'row', backgroundColor: colors.background },
  sidebar: {
    width: 272,
    flexShrink: 0,
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 28,
    backgroundColor: colors.deep,
    borderRightWidth: 1,
    borderRightColor: 'rgba(255,255,255,0.08)',
  },
  sidebarBrand: { minHeight: 56, justifyContent: 'center', marginBottom: 36, paddingHorizontal: 8 },
  sidebarBrandText: { color: colors.white, fontSize: 18, lineHeight: 26, fontWeight: '800', letterSpacing: 0.2 },
  sidebarBrandAccent: { color: colors.accent },
  sidebarStatus: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 'auto', paddingHorizontal: 12, paddingTop: 24 },
  onlineDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.accent },
  sidebarStatusText: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  header: { backgroundColor: colors.white },
  headerInner: {
    width: '100%',
    minHeight: 80,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerActionsCompact: { gap: 6 },
  currentPage: { minHeight: 40, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, borderRadius: 20, backgroundColor: '#EEF4F5' },
  currentPageCompact: { paddingHorizontal: 6 },
  currentPageTextCompact: { fontSize: 13, lineHeight: 18 },
  currentPageText: { color: colors.deep, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  menuToggle: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.white },
  mobileNavigation: { paddingTop: 12, paddingBottom: 20, backgroundColor: colors.white, borderTopWidth: 1, borderTopColor: '#E4EBED' },
  brand: { fontSize: 19, lineHeight: 26, fontWeight: '800', letterSpacing: 0.1 },
  brandCompact: { fontSize: 14, lineHeight: 20, letterSpacing: 0 },
  brandText: { color: colors.background },
  brandTextLarge: { color: colors.accent },
  brandAccent: { color: colors.accent },
  brandLarge: { fontSize: 28, lineHeight: 36, marginBottom: 24 },
  nav: { gap: 28 },
  navSection: { gap: 10 },
  navSectionLabel: { color: '#A8BBC1', fontSize: 11, lineHeight: 16, fontWeight: '700', letterSpacing: 1.1, textTransform: 'uppercase', paddingHorizontal: 12, marginBottom: 2 },
  navItems: { flexDirection: 'column', alignItems: 'stretch', gap: 6 },
  navItem: {
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  navItemSelected: { backgroundColor: '#2A424B', borderColor: 'rgba(0,255,197,0.22)' },
  navActiveMarker: { position: 'absolute', left: 0, top: 10, bottom: 10, width: 3, borderRadius: 2, backgroundColor: colors.accent },
  navIcon: {
    width: 32,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatIcon: { width: 38, height: 38, borderRadius: 20, backgroundColor: colors.accent, justifyContent: 'center', alignItems: 'center' },
  navLabel: { flex: 1, fontSize: 15, lineHeight: 22, fontWeight: '500' },
  navLabelSelected: { fontWeight: '700' },
  focusVisible: { borderWidth: 2, borderColor: colors.accent, borderRadius: 12 },
  page: {
    flex: 1,
    width: '100%',
    maxWidth: 1296,
    alignSelf: 'center',
    backgroundColor: colors.background,
  },
  pageDesktop: { maxWidth: undefined, alignSelf: 'stretch' },
  pageInner: {
    width: '100%',
    paddingTop: 28,
    paddingBottom: 48,
  },
  pageInnerFill: { flexGrow: 1, paddingBottom: 92 },
  pageTitle: { color: colors.white, fontSize: 32, lineHeight: 40, fontWeight: '700', marginBottom: 24 },
  pageTitleTablet: { fontSize: 28, lineHeight: 36 },
  pageTitleMobile: { fontSize: 26, lineHeight: 34 },
  card: {
    padding: spacing.xl,
    borderRadius: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardMobile: { padding: spacing.lg },
  button: {
    minHeight: 48,
    borderRadius: 12,
    paddingHorizontal: 16,
    justifyContent: 'center',
    alignItems: 'flex-start',
    backgroundColor: colors.accent,
  },
  buttonOutline: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.accent },
  buttonDisabled: { opacity: 0.5 },
  buttonContent: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  buttonText: { color: colors.deep, fontSize: 15, lineHeight: 20, fontWeight: '700' },
  buttonOutlineText: { color: colors.white },
  pressed: { opacity: 0.78 },
  fieldGroup: { marginBottom: 20 },
  fieldLabel: { color: colors.white, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 6 },
  inputWrap: {
    minHeight: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.deep,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
  },
  inputError: { borderColor: '#FF8B8B' },
  inputFocused: { borderColor: colors.accent, borderWidth: 2 },
  input: { flex: 1, minHeight: 48, color: colors.white, fontSize: 16, paddingVertical: 10 },
  textAreaWrap: { minHeight: 150, alignItems: 'stretch', borderRadius: 16, paddingVertical: 8 },
  textArea: { minHeight: 134, textAlignVertical: 'top' },
  errorText: { color: '#FFD1D1', fontSize: 14, lineHeight: 20, marginTop: 4 },
  credibilityRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  scoreBox: { minWidth: 78, minHeight: 54, paddingHorizontal: 12, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.deep },
  score: { color: colors.accent, fontSize: 20, lineHeight: 26, fontWeight: '700' },
  credibilityCaption: { color: colors.white, fontWeight: '700', fontSize: 15, lineHeight: 20 },
  mediaPreview: {
    minHeight: 120,
    paddingHorizontal: 16,
    paddingVertical: 20,
    backgroundColor: colors.deep,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  mediaPreviewCompact: { minHeight: 96, width: 204, paddingHorizontal: 16, paddingVertical: 16, gap: 12 },
  mediaAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent },
  mediaText: { flex: 1, color: colors.muted, fontSize: 15, lineHeight: 22, fontWeight: '700' },
  mediaImage: { width: 64, height: 64, borderRadius: 6 },
  mediaRemove: { minWidth: 44, minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  profileRow: {
    minHeight: 64,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 6,
  },
  profileRowLabel: { flex: 1, color: colors.white, fontSize: 16, lineHeight: 22, fontWeight: '700' },
});
