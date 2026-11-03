import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { calculateCorroboration, startPrecompute, getPrecompute, type PrecomputeResult, type Corroboration, type SourceAssessment } from '@/services/mockData';

const choices = [
  { value: 'supports', label: 'Confirme' },
  { value: 'contradicts', label: 'Contredit' },
  { value: 'inconclusive', label: 'Non concluant' },
] as const;
const blank = (): SourceAssessment => ({ url: '', assessment: 'inconclusive' });

export function CredibilityForm({ articleUrl, onResultChange }: { articleUrl?: string; onResultChange?: (result: Corroboration | null, provisional?: boolean) => void }) {
  const [claim, setClaim] = useState('');
  const [sources, setSources] = useState<SourceAssessment[]>([blank(), blank()]);
  const [result, setResult] = useState<Corroboration | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [suggestion, setSuggestion] = useState<PrecomputeResult | null>(null);
  const [preStatus, setPreStatus] = useState('');
  const [provisional, setProvisional] = useState(false);
  const dirty = useRef(false);
  const callback = useRef(onResultChange);
  useEffect(() => { callback.current = onResultChange; }, [onResultChange]);

  useEffect(() => {
    if (!articleUrl) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async (id: string, attempts: number) => {
      try {
        const job = await getPrecompute(id);
        if (!active) return;
        if (job.status === 'completed' && job.result) {
          setSuggestion(job.result);
          setPreStatus('Pré-calcul terminé : vérifiez les propositions et les extraits.');
          if (!dirty.current) {
            if (job.result.claim) setClaim(job.result.claim);
            if (job.result.sources.length) setSources(job.result.sources.map(({ url, assessment }) => ({ url, assessment })));
            setResult(job.result.calculation);
            setProvisional(true);
            callback.current?.(job.result.calculation, true);
          }
        } else if (job.status === 'failed') setPreStatus('Pré-calcul indisponible. Vous pouvez vérifier les sources manuellement.');
        else if (attempts < 90) timer = setTimeout(() => void poll(id, attempts + 1), 2000);
        else setPreStatus('Pré-calcul trop long. Réessayez en rouvrant l’article.');
      } catch (reason) {
        if (active) setPreStatus(reason instanceof Error ? reason.message : 'Pré-calcul indisponible.');
      }
    };
    Promise.resolve().then(() => { if (active) setPreStatus('Recherche de sources et pré-calcul IA en cours…'); });
    startPrecompute(articleUrl).then((job) => { if (active) void poll(job.job_id, 0); })
      .catch((reason) => { if (active) setPreStatus(reason instanceof Error ? reason.message : 'Pré-calcul indisponible.'); });
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [articleUrl]);

  function applySuggestions() {
    if (!suggestion) return;
    setClaim(suggestion.claim || '');
    setSources(suggestion.sources.length ? suggestion.sources.map(({ url, assessment }) => ({ url, assessment })) : [blank(), blank()]);
    setResult(suggestion.calculation);
    setProvisional(true);
    onResultChange?.(suggestion.calculation, true);
    dirty.current = false;
  }


  function update(index: number, changes: Partial<SourceAssessment>) {
    dirty.current = true;
    setSources((current) => current.map((source, position) => position === index ? { ...source, ...changes } : source));
    setResult(null);
    onResultChange?.(null);
    setError('');
  }

  async function calculate() {
    if (busy) return;
    const assessed = sources.filter((source) => source.url.trim()).map((source) => ({ ...source, url: source.url.trim() }));
    if (claim.trim().length < 3 || !assessed.length) {
      setError('Indiquez une affirmation précise et au moins une adresse de source.');
      return;
    }
    setBusy(true);
    setError('');
    setResult(null);
    onResultChange?.(null);
    try {
      const calculated = await calculateCorroboration(claim.trim(), assessed);
      setProvisional(false);
      setResult(calculated);
      onResultChange?.(calculated);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Calcul indisponible.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Calcul de corroboration</Text>
      {preStatus ? <Text accessibilityLiveRegion="polite" style={styles.note}>{preStatus}</Text> : null}
      {suggestion ? <View style={styles.result}>
        <Text style={styles.note}>{suggestion.notice}</Text>
        <Text style={styles.note}>Recherche : {new Date(suggestion.checked_at).toLocaleString()}</Text>
        {suggestion.warnings.length ? <Text style={styles.note}>Certaines recherches sont indisponibles ou non configurées : {suggestion.warnings.join(', ')}.</Text> : null}
        {suggestion.sources.map((source, index) => <View key={`${source.url}-${index}`} style={styles.source}>
          <Text selectable style={styles.label}>{source.title} · {source.origin}{source.date ? ` · ${source.date}` : ''}</Text>
          <Text selectable style={styles.note}>{source.url}</Text>
          <Text selectable style={styles.note}>{source.quote || source.excerpt || 'Titre uniquement : preuve insuffisante.'}</Text>
          {source.duplicate ? <Text style={styles.note}>Reprise potentielle : non comptabilisée automatiquement.</Text> : null}
        </View>)}
        <Pressable accessibilityRole="button" onPress={applySuggestions}><Text style={styles.link}>Appliquer les propositions IA</Text></Pressable>
      </View> : null}
      <Text style={styles.note}>Après avoir lu chaque source, indiquez si elle confirme ou contredit la même affirmation. Vérifiez que les sources sont indépendantes et ne reprennent pas la même dépêche.</Text>
      <TextInput accessibilityLabel="Affirmation vérifiée" value={claim}
        onChangeText={(value) => { dirty.current = true; setClaim(value); setResult(null); onResultChange?.(null); setError(''); }}
        editable={!busy} maxLength={2000} multiline placeholder="Affirmation précise à vérifier"
        placeholderTextColor="#b7c5c8" style={styles.input} />
      {sources.map((source, index) => (
        <View key={index} style={styles.source}>
          <Text style={styles.label}>Source {index + 1}</Text>
          <TextInput accessibilityLabel={`Adresse de la source ${index + 1}`} value={source.url}
            onChangeText={(value) => update(index, { url: value })} editable={!busy}
            autoCapitalize="none" autoCorrect={false} keyboardType="url" maxLength={500}
            placeholder="https://..." placeholderTextColor="#b7c5c8" style={styles.input} />
          <View style={styles.choices}>
            {choices.map((choice) => (
              <Pressable key={choice.value} accessibilityRole="radio"
                accessibilityState={{ checked: source.assessment === choice.value, disabled: busy }}
                disabled={busy} onPress={() => update(index, { assessment: choice.value })}
                style={[styles.choice, source.assessment === choice.value && styles.selected]}>
                <Text style={[styles.choiceText, source.assessment === choice.value && styles.selectedText]}>{choice.label}</Text>
              </Pressable>
            ))}
          </View>
          {sources.length > 2 ? <Pressable accessibilityRole="button" disabled={busy} onPress={() => { dirty.current = true; setSources((current) => current.filter((_, position) => position !== index)); setResult(null); onResultChange?.(null); setError(''); }}><Text style={styles.link}>Retirer cette source</Text></Pressable> : null}
        </View>
      ))}
      {sources.length < 10 ? <Pressable accessibilityRole="button" disabled={busy} onPress={() => { dirty.current = true; setSources((current) => [...current, blank()]); setResult(null); onResultChange?.(null); }}><Text style={styles.link}>+ Ajouter une source</Text></Pressable> : null}
      <Pressable accessibilityRole="button" disabled={busy} accessibilityState={{ disabled: busy, busy }}
        onPress={() => void calculate()} style={styles.submit}><Text style={styles.submitText}>{busy ? 'Calcul…' : 'Valider et calculer la corroboration'}</Text></Pressable>
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      {result ? <View accessibilityLiveRegion="polite" style={styles.result}>
        {provisional ? <Text style={styles.label}>Estimation IA provisoire — non validée</Text> : null}
        <Text style={styles.score}>{result.corroboration_percent === null ? 'Preuves insuffisantes' : `${result.corroboration_percent} % de sources concordantes`}</Text>
        <Text style={styles.note}>{result.supports} confirme(nt) · {result.contradicts} contredit(sent) · {result.inconclusive} non concluant(s)</Text>
        <Text style={styles.note}>{result.source_groups} groupe(s) de domaines · {result.excluded_duplicates} source(s) regroupée(s)</Text>
        {result.corroboration_percent === null ? <Text style={styles.note}>Il faut au moins deux groupes de sources conclusifs pour calculer cet indice.</Text> : null}
        <Text style={styles.note}>{result.limitation}</Text>
      </View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10, marginTop: 18, borderWidth: 1, borderColor: '#69dcb5', borderRadius: 14, padding: 14 },
  heading: { color: '#fff', fontSize: 16, fontWeight: '700' },
  label: { color: '#fff', fontSize: 13, fontWeight: '700' },
  note: { color: '#d7e8e5', fontSize: 12, lineHeight: 19 },
  input: { minHeight: 46, color: '#fff', borderWidth: 1, borderColor: '#9bb7b2', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 8 },
  source: { gap: 7, marginTop: 6 },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  choice: { minHeight: 40, justifyContent: 'center', paddingHorizontal: 10, borderWidth: 1, borderColor: '#69dcb5', borderRadius: 8 },
  selected: { backgroundColor: '#69dcb5' },
  choiceText: { color: '#fff', fontSize: 12 },
  selectedText: { color: '#0b2b2b', fontWeight: '700' },
  link: { color: '#69dcb5', paddingVertical: 6, textDecorationLine: 'underline' },
  submit: { backgroundColor: '#69dcb5', borderRadius: 10, minHeight: 46, justifyContent: 'center', alignItems: 'center', padding: 10 },
  submitText: { color: '#0b2b2b', fontWeight: '700' },
  error: { color: '#ffd0d0', fontSize: 13 },
  result: { gap: 6, paddingTop: 4 },
  score: { color: '#69dcb5', fontSize: 17, fontWeight: '700' },
});
