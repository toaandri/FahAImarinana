import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Link } from 'expo-router';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
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

  useEffect(() => {
    if (reduceMotion) scale.setValue(1);
  }, [reduceMotion, scale]);

  const animateScale = (toValue: number) => {
    Animated.timing(scale, {
      toValue: reduceMotion ? 1 : toValue,
      duration: reduceMotion ? 0 : 180,
      useNativeDriver: false,
    }).start();
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
        if (!disabled) animateScale(0.98);
        onPressIn?.(event);
      }}
      onPressOut={(event) => {
        setPressed(false);
        animateScale(hovered ? 1.015 : 1);
        onPressOut?.(event);
      }}
      onHoverIn={(event) => {
        setHovered(true);
        if (!disabled) animateScale(1.015);
        onHoverIn?.(event);
      }}
      onHoverOut={(event) => {
        setHovered(false);
        animateScale(1);
        onHoverOut?.(event);
      }}
      style={[
        typeof style === 'function' ? style({ pressed }) : style,
        focused && styles.focusVisible,
        hovered && !disabled && styles.interactionHovered,
        pressed && !disabled && styles.interactionPressed,
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

export function Brand({ large = false }: { large?: boolean }) {
  return (
    <Text style={[styles.brand, large && styles.brandLarge]}>
      <Text style={[styles.brandText, large && styles.brandTextLarge]}>FAH </Text>
      <Text style={styles.brandAccent}>AI</Text>
      <Text style={[styles.brandText, large && styles.brandTextLarge]}> MARINANA</Text>
    </Text>
  );
}

const navigation = [
  { section: 'Découvrir', label: 'Accueil', icon: 'home-outline', href: '/' },
  { section: 'Découvrir', label: 'Actualités', icon: 'newspaper-variant-outline', href: '/actualites' },
  { section: 'Participer', label: 'Discuter', icon: 'message-processing-outline', href: '/verifier' },
  { section: 'Participer', label: 'Publier', icon: 'plus', href: '/publier' },
  { section: 'Compte', label: 'Profil', icon: 'account-outline', href: '/profil' },
] as const;

export function TopNav({ active, onNavigate }: { active?: string; onNavigate?: () => void }) {
  const sections = [...new Set(navigation.map((item) => item.section))];

  return (
    <View
      role="navigation"
      accessibilityLabel="Navigation principale"
      style={styles.nav}
    >
      {sections.map((section) => (
        <View key={section} style={styles.navSection}>
          <Text style={styles.navSectionLabel}>{section}</Text>
          <View style={styles.navItems}>
            {navigation.filter((item) => item.section === section).map((item) => {
              const selected = active === item.href;
              const isChat = item.href === '/verifier';
              const color = selected || isChat ? colors.accent : colors.muted;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  asChild
                  accessibilityRole="link"
                  accessibilityLabel={item.label}
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
                      {item.label}
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
  onNavigate,
}: {
  active: string;
  horizontalPadding: number;
  onNavigate: () => void;
}) {
  const reduceMotion = useContext(ReduceMotionContext);
  const [progress] = useState(() => new Animated.Value(reduceMotion ? 1 : 0));

  useEffect(() => {
    if (reduceMotion) {
      progress.setValue(1);
      return;
    }

    const animation = Animated.timing(progress, {
      toValue: 1,
      duration: 180,
      useNativeDriver: false,
    });
    animation.start();
    return () => animation.stop();
  }, [progress, reduceMotion]);

  return (
    <Animated.View
      role="region"
      accessibilityLabel="Menu de navigation"
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
}: {
  active: string;
  children: ReactNode;
}) {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;
  const horizontalPadding = width >= 1200 ? 48 : width >= 768 ? 32 : 20;
  const [navigationOpen, setNavigationOpen] = useState(false);
  const activeLabel = navigation.find((item) => item.href === active)?.label ?? 'Menu';

  return (
    <View style={[styles.app, desktop && styles.appDesktop]}>
      {desktop ? (
        <View role="complementary" accessibilityLabel="Navigation latérale" style={styles.sidebar}>
          <Link href="/" asChild accessibilityRole="link" accessibilityLabel="FAH AI MARINANA, accueil">
            <InteractivePressable style={styles.sidebarBrand}>
              <Text style={styles.sidebarBrandText}>
                FAH <Text style={styles.sidebarBrandAccent}>AI</Text> MARINANA
              </Text>
            </InteractivePressable>
          </Link>
          <TopNav active={active} />
          <View style={styles.sidebarStatus}>
            <View style={styles.onlineDot} />
            <Text style={styles.sidebarStatusText}>En ligne</Text>
          </View>
        </View>
      ) : (
        <View style={styles.header}>
          <View style={[styles.headerInner, { paddingHorizontal: horizontalPadding }]}>
            <Brand />
            <View style={styles.headerActions}>
              <View style={styles.currentPage}>
                <View style={styles.onlineDot} />
                <Text style={styles.currentPageText}>{activeLabel}</Text>
              </View>
              <InteractivePressable
                accessibilityRole="button"
                accessibilityLabel={navigationOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
                accessibilityState={{ expanded: navigationOpen }}
                aria-expanded={navigationOpen}
                onPress={() => setNavigationOpen((open) => !open)}
                style={styles.menuToggle}
              >
                <Icon name={navigationOpen ? 'close' : 'menu'} color={colors.deep} />
              </InteractivePressable>
            </View>
          </View>
          {navigationOpen ? (
            <MobileNavigation
              active={active}
              horizontalPadding={horizontalPadding}
              onNavigate={() => setNavigationOpen(false)}
            />
          ) : null}
        </View>
      )}
      <ScrollView
        role="main"
        style={[styles.page, desktop && styles.pageDesktop]}
        contentContainerStyle={[styles.pageInner, { paddingHorizontal: horizontalPadding }]}
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
  return (
    <InteractivePressable
      accessibilityRole="button"
      accessibilityLabel={loading ? `${label}, chargement` : label}
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
      {loading ? (
        <ActivityIndicator color={outline ? colors.accent : colors.deep} />
      ) : (
        <View style={styles.buttonContent}>
          {icon ? <Icon name={icon} color={outline ? colors.accent : colors.deep} /> : null}
          <Text style={[styles.buttonText, outline && styles.buttonOutlineText]}>{label}</Text>
        </View>
      )}
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
  caption = 'Crédibilité',
}: {
  value: string;
  caption?: string;
}) {
  return (
    <View style={styles.credibilityRow}>
      <View style={styles.scoreBox}>
        <Text style={styles.score}>{value}</Text>
      </View>
      <Text style={styles.credibilityCaption}>{caption}</Text>
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
  const compactWidth = width < 768 ? (width < 360 ? 64 : 76) : 164;
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
  currentPage: { minHeight: 40, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, borderRadius: 20, backgroundColor: '#EEF4F5' },
  currentPageText: { color: colors.deep, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  menuToggle: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.white },
  mobileNavigation: { paddingTop: 12, paddingBottom: 20, backgroundColor: colors.white, borderTopWidth: 1, borderTopColor: '#E4EBED' },
  brand: { fontSize: 19, lineHeight: 26, fontWeight: '800', letterSpacing: 0.1 },
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
  interactionHovered: { opacity: 0.92 },
  interactionPressed: { opacity: 0.82 },
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
  mediaPreviewCompact: { minHeight: 72, width: 164, paddingVertical: 12 },
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
