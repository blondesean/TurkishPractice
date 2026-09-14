/* Turkish grammar for the Conjugation and Sentences modes.
 *
 * build_web.py inlines this file into web/index.html -- edit it here, then run
 * `py -3 build_web.py`. Check forms with `node web/grammar_test.js`.
 *
 * Forms are built from rules rather than stored, so each rule lives once:
 *   four-way harmony (ı-type):  a ı → ı    e i → i    o u → u    ö ü → ü
 *   two-way harmony  (a-type):  a ı o u → a            e i ö ü → e
 *   a suffix's d becomes t after a voiceless consonant (f s t k ç ş h p)
 *   a final p ç k g softens to b c ğ ğ before a vowel (nk → ng), in words of
 *   two or more syllables; t softens only in the words listed
 *   a y (or s, n) buffer separates two vowels
 * Words that break a rule are listed in NOUNS and VERBS.
 */
const Grammar = (() => {
"use strict";

/* --- people ------------------------------------------------------------- */
const PERSONS = ["p1s", "p2s", "p3s", "p1p", "p2p", "p3p"];
const PRONOUN = {p1s:"ben", p2s:"sen", p3s:"o", p1p:"biz", p2p:"siz", p3p:"onlar"};
const GENITIVE = {p1s:"benim", p2s:"senin", p3s:"onun", p1p:"bizim", p2p:"sizin", p3p:"onların"};
const PERSON_EN = {p1s:"I", p2s:"you", p3s:"he / she", p1p:"we", p2p:"you (plural)", p3p:"they"};
const SUBJECT_EN = {p1s:"I", p2s:"you", p3s:"he/she", p1p:"we", p2p:"you all", p3p:"they"};
const BE_EN = {p1s:"am", p2s:"are", p3s:"is", p1p:"are", p2p:"are", p3p:"are"};
const POSSESSIVE_EN = {p1s:"my", p2s:"your", p3s:"his/her", p1p:"our", p2p:"your", p3p:"their"};

/* --- sounds ------------------------------------------------------------- */
const VOWELS = ["a", "ı", "o", "u", "e", "i", "ö", "ü"];
const FOUR = {a:"ı", ı:"ı", o:"u", u:"u", e:"i", i:"i", ö:"ü", ü:"ü"};
const BACK = new Set(["a", "ı", "o", "u"]);
const CIRCUMFLEX = {"â":"a", "î":"i", "û":"u"};
const VOICELESS = new Set([..."fstkçşhp"]);

const lower = s => s.toLocaleLowerCase("tr");
const vowelOf = ch => { const c = CIRCUMFLEX[ch] || ch; return FOUR[c] ? c : null; };
const isVowel = ch => !!vowelOf(lower(ch));
const four = v => FOUR[v];
const two = v => BACK.has(v) ? "a" : "e";
const endsInVowel = w => isVowel(w[w.length - 1]);

function lastVowel(w){
  for(let i = w.length - 1; i >= 0; i--){
    const v = vowelOf(lower(w[i]));
    if(v) return v;
  }
  return null;
}

/* Suffixes attach to the last word of a phrase: "Güney Kore" → "Güney Koreli". */
function splitLast(phrase){
  const i = phrase.lastIndexOf(" ");
  return {head: phrase.slice(0, i + 1), last: phrase.slice(i + 1)};
}

/* --- exceptions --------------------------------------------------------- */
const NOUNS = {
  // Loanwords whose suffixes take front harmony despite the spelling.
  "saat":  {vowel:"e"},
  "kalp":  {vowel:"e", soft:"kalb"},
  "rol":   {vowel:"ö"},
  "alkol": {vowel:"ö"},
  "hayal": {vowel:"e"},
  // The last vowel drops before a vowel-initial suffix: ağız → ağzım.
  "ağız":  {drop:"ağz"},
  "burun": {drop:"burn"},
  "boyun": {drop:"boyn"},
  "beyin": {drop:"beyn"},
  "göğüs": {drop:"göğs"},
  "omuz":  {drop:"omz"},
  "oğul":  {drop:"oğl"},
  "alın":  {drop:"aln"},
  "karın": {drop:"karn"},
  // Softening the general rule gets wrong in one direction or the other.
  "avukat":  {soft:false},
  "sandviç": {soft:false},
  "yoğurt":  {soft:"yoğurd"},
  "renk":    {soft:"reng"},
  // Takes a y where a vowel-final noun would take nothing: suyum, suyu.
  "su": {buffer:"y"},
  // Front harmony on an Arabic loan: meşgulüm, not meşgulum.
  "meşgul": {vowel:"ü"},
  // One syllable, but softens anyway: genç → gencim.
  "genç": {soft:"genc"},
};

const VERBS = {
  // t → d before a vowel: gitmek → gidiyor, gideceğim (but gitti).
  "git": {soft:"gid"},
  "et":  {soft:"ed"},
  "tat": {soft:"tad"},
  "güt": {soft:"güd"},
  // e → i before a y: diyor, diyecek, yiyor, yiyecek -- but dedi, yedi. The
  // present happens to fall out of the vowel-drop rule, yet every grammar
  // teaches it as irregular, so it's marked there too.
  "de":  {future:"diy", irregularIn:["present", "future"]},
  "ye":  {future:"yiy", irregularIn:["present", "future"]},
};

/* o.plain ignores the exception lists -- comparing plain and real forms is how
   a word is found to be irregular. */
const nounLex = (w, o = {}) => (!o.plain && NOUNS[w]) || {};
const verbLex = (st, o = {}) => (!o.plain && VERBS[st]) || {};
const nounVowel = (w, o = {}) => nounLex(w, o).vowel || lastVowel(w);

/* Consonant softening before a vowel-initial suffix. */
function soften(w, o){
  if(o.noSoften) return w;
  const lex = nounLex(w, o);
  if(typeof lex.soft === "string") return lex.soft;
  if(lex.soft === false) return w;
  const last = w[w.length - 1];
  if(last === "t" || !"pçkg".includes(last)) return w;
  if([...w].filter(isVowel).length < 2) return w;   // saç → saçı, top → topu
  if(last === "k") return w.slice(0, -1) + (w[w.length - 2] === "n" ? "g" : "ğ");
  return w.slice(0, -1) + {p:"b", ç:"c", g:"ğ"}[last];
}

/* Possessive stems also lose a dropping vowel. */
function possessiveStem(w, o){
  if(o.noSoften) return w;
  return nounLex(w, o).drop || soften(w, o);
}

const verbStem = inf => lower(splitLast(inf).last).replace(/m[ae]k$/, "");

/* --- forms -------------------------------------------------------------- *
 * Each takes a vocab entry {tr, en}, a person, and options used to generate
 * plausible wrong answers:
 *   forceVowel  apply harmony as if the stem's vowel were this one
 *   noSoften    skip consonant softening, vowel drop, and d → t
 *   noBuffer    skip the y / s buffer between vowels
 * and returns {text, vowel}, where vowel is the harmony vowel the form really
 * depends on -- the column of the 6 × 8 mastery grid.
 * ----------------------------------------------------------------------- */

/* Nerelisin: place + -lı, then the personal ending. Bolivya → Bolivyalıyım. */
function nerelisin(entry, p, o = {}){
  const {head, last} = splitLast(entry.tr);
  const real = lastVowel(last);
  const u = four(o.forceVowel || real);
  const base = head + last + "l" + u;
  const y = o.noBuffer ? "" : "y";
  const text = {
    p1s: base + y + u + "m",
    p2s: base + "s" + u + "n",
    p3s: base,
    p1p: base + y + u + "z",
    p2p: base + "s" + u + "n" + u + "z",
    p3p: base + "l" + two(u) + "r",
  }[p];
  return {text, vowel: real};
}

/* Feelings: the personal "to be" endings on an adjective. yorgun → yorgunum. */
function feelings(entry, p, o = {}){
  const {head, last} = splitLast(lower(entry.tr));
  const real = nounVowel(last);
  const v = o.forceVowel || nounVowel(last, o);
  const u = four(v);
  const pre = endsInVowel(last) ? last + (o.noBuffer ? "" : "y") : soften(last, o);
  const text = {
    p1s: pre + u + "m",
    p2s: last + "s" + u + "n",
    p3s: last,
    p1p: pre + u + "z",
    p2p: last + "s" + u + "n" + u + "z",
    p3p: last + "l" + two(v) + "r",
  }[p];
  return {text: head + text, vowel: real};
}

/* Possession: anne → annem, annen, annesi … kulak → kulağım, ağız → ağzım. */
function possession(entry, p, o = {}){
  const {head, last} = splitLast(lower(entry.tr));
  const real = nounVowel(last);
  const v = o.forceVowel || nounVowel(last, o);
  const u = four(v), a = two(v);
  const lex = nounLex(last, o);
  const plural = last + "l" + a + "r" + four(a);        // -ları / -leri, no softening
  let text;
  if(endsInVowel(last) && !lex.buffer){
    text = {
      p1s: last + "m",
      p2s: last + "n",
      p3s: last + (o.noBuffer ? "" : "s") + u,
      p1p: last + "m" + u + "z",
      p2p: last + "n" + u + "z",
      p3p: plural,
    }[p];
  }else{
    const s = endsInVowel(last) ? last + (o.noBuffer ? "" : lex.buffer) : possessiveStem(last, o);
    text = {
      p1s: s + u + "m",
      p2s: s + u + "n",
      p3s: s + u,
      p1p: s + u + "m" + u + "z",
      p2p: s + u + "n" + u + "z",
      p3p: plural,
    }[p];
  }
  return {text: head + text, vowel: real};
}

/* Present continuous -(ı)yor: gel → geliyor; a final vowel drops: anla → anlıyor. */
function present(entry, p, o = {}){
  const head = lower(splitLast(entry.tr).head);
  const st = verbStem(entry.tr);
  let base, real;
  if(endsInVowel(st)){
    const cut = st.slice(0, -1);
    real = lastVowel(cut) || lastVowel(st);
    base = o.noSoften
      ? st + "yor"                                      // the classic slip: anlayor
      : cut + four(o.forceVowel || real) + "yor";
  }else{
    real = lastVowel(st);
    const s = o.noSoften ? st : (verbLex(st, o).soft || st);
    base = s + four(o.forceVowel || real) + "yor";
  }
  const text = {
    p1s: base + "um", p2s: base + "sun", p3s: base,
    p1p: base + "uz", p2p: base + "sunuz", p3p: base + "lar",
  }[p];
  return {text: head + text, vowel: real};
}

/* Going to -(y)acak/-(y)ecek; k → ğ before -ım/-ız: gideceğim, gidecek. */
function future(entry, p, o = {}){
  const head = lower(splitLast(entry.tr).head);
  const st = verbStem(entry.tr);
  const real = lastVowel(st);
  const a = two(o.forceVowel || real);
  const u = four(a);
  const lex = verbLex(st, o);
  const s = lex.future && !o.noSoften ? lex.future          // demek → diyecek
    : endsInVowel(st) ? st + (o.noBuffer ? "" : "y")
    : (o.noSoften ? st : (lex.soft || st));
  const k = a === "a" ? "acak" : "ecek";
  const g = o.noSoften ? k : k.slice(0, -1) + "ğ";
  const text = {
    p1s: s + g + u + "m",
    p2s: s + k + "s" + u + "n",
    p3s: s + k,
    p1p: s + g + u + "z",
    p2p: s + k + "s" + u + "n" + u + "z",
    p3p: s + k + "l" + a + "r",
  }[p];
  return {text: head + text, vowel: real};
}

/* Past -dı/-tı: gel → geldim, git → gittim, çalış → çalıştım. */
function past(entry, p, o = {}){
  const head = lower(splitLast(entry.tr).head);
  const st = verbStem(entry.tr);
  const real = lastVowel(st);
  const v = o.forceVowel || real;
  const u = four(v);
  const d = !o.noSoften && VOICELESS.has(st[st.length - 1]) ? "t" : "d";
  const base = st + d + u;
  const text = {
    p1s: base + "m", p2s: base + "n", p3s: base,
    p1p: base + "k", p2p: base + "n" + u + "z", p3p: base + "l" + two(v) + "r",
  }[p];
  return {text: head + text, vowel: real};
}

/* --- which vocab each form can use -------------------------------------- */
const usable = tr => !/[\/_]|see below/i.test(tr) && lastVowel(tr) !== null;

// Multi-word names that already carry a suffix, and plural names, don't take -lı
// cleanly (Amerika Birleşik Devletleri, Filipinler).
const acceptPlace = tr =>
  !/\s(Cumhuriyeti|Devletleri|Emirlikleri|Kıyısı)$/.test(tr) && !/^\S+l[ae]r$/.test(tr);
// "Kafası karışık" conjugates inside the phrase (kafaları karışık), not at the end.
const acceptFeeling = tr => tr !== "Kafası karışık";
// A compound that already ends in a possessive (Ayak bileği) can't take another.
const acceptPossessed = tr => !(/\s/.test(tr) && /s?[ıiuü]$/.test(tr));
// Any infinitive; the irregular ones (demek, yemek, gitmek…) are listed in VERBS.
const acceptVerb = tr => /m[ae]k$/i.test(tr);

const CATEGORIES = [
  {id:"nerelisin",  name:"Nerelisin",          en:"I am from…",
   rule:"-lı · -li · -lu · -lü, then “to be”",   example:["Bolivya", "Bolivyalıyım"],
   note:"This is the everyday “from X” form; some countries also have their own nationality word (Alman, Fransız, İngiliz).",
   source: m => m.startsWith("Countries/"), custom:"place", accept: acceptPlace, keepCase:true, form: nerelisin},
  {id:"feelings",   name:"Feelings & jobs",    en:"I am tired · a teacher · young",
   rule:"-(y)ım · -sın · — · -(y)ız · -sınız · -lar", example:["yorgun", "yorgunum"],
   note:"Occupations and adjectives for people share the same endings and fill in the vowels emotions lack (o, e, ö).",
   source: m => m === "Emotions" || m === "Occupations" || m === "Adjectives/People",
   custom:"adjective", accept: acceptFeeling, form: feelings},
  {id:"possession", name:"Possession",         en:"my mother, your hand",
   rule:"-(ı)m · -(ı)n · -(s)ı · -(ı)mız · -(ı)nız · -ları", example:["kulak", "kulağım"],
   source: m => m.startsWith("Family Members/") || m.startsWith("Parts Of The Body/"),
   custom:"noun", accept: acceptPossessed, form: possession},
  {id:"present",    name:"Present continuous", en:"I am going",
   rule:"-(ı)yor + -um · -sun · — · -uz · -sunuz · -lar", example:["gitmek", "gidiyorum"],
   source: m => m === "Verbs" || m === "More Verbs", custom:"verb", accept: acceptVerb, verb:true, form: present},
  {id:"future",     name:"Going to",           en:"I am going to go",
   rule:"-(y)acak · -(y)ecek, k → ğ before a vowel", example:["gitmek", "gideceğim"],
   source: m => m === "Verbs" || m === "More Verbs", custom:"verb", accept: acceptVerb, verb:true, form: future},
  {id:"past",       name:"Past",               en:"I went",
   rule:"-dı · -tı + -m · -n · — · -k · -nız · -lar", example:["gitmek", "gittim"],
   source: m => m === "Verbs" || m === "More Verbs", custom:"verb", accept: acceptVerb, verb:true, form: past},
];
const CATEGORY = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));
const TENSES = ["present", "future", "past"];

function eachEntry(vocab, fn){
  for(const [cat, subs] of Object.entries(vocab)){
    const keys = Object.keys(subs);
    const flat = keys.length === 1 && keys[0] === "Main";
    for(const [sub, words] of Object.entries(subs)){
      const module = flat ? cat : `${cat}/${sub}`;
      for(const [en, tr] of words) fn({en, tr, module});
    }
  }
}

/* Irregular in a category = the exception lists change any of its six forms
   there, or VERBS says so outright. So gitmek is irregular in the present
   (gidiyor) but not the past (gitti). */
function isIrregular(categoryId, entry){
  const c = CATEGORY[categoryId];
  if(c.verb && ((VERBS[verbStem(entry.tr)] || {}).irregularIn || []).includes(categoryId)) return true;
  return PERSONS.some(p => c.form(entry, p).text !== c.form(entry, p, {plain:true}).text);
}

/* {categoryId: [{en, tr, module, vowel, irregular}]}, de-duplicated on the
   Turkish. `extra` is My Words, each routed by the type the user picked. */
function buildPools(vocab, extra = []){
  const pools = {};
  for(const c of CATEGORIES){
    const seen = new Set(), list = [];
    const add = e => {
      if(!usable(e.tr) || !c.accept(e.tr) || seen.has(e.tr)) return;
      seen.add(e.tr);
      list.push(Object.assign({}, e, {vowel: c.form(e, "p3s").vowel, irregular: isIrregular(c.id, e)}));
    };
    eachEntry(vocab, e => { if(c.source(e.module)) add(e); });
    for(const e of extra) if(c.custom && e.type === c.custom) add(e);
    pools[c.id] = list;
  }
  return pools;
}

/* --- answer buttons ----------------------------------------------------- */
function shuffle(a){
  for(let i = a.length - 1; i > 0; i--){
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
const pick = a => a[Math.floor(Math.random() * a.length)];

/* The right form, plus wrong answers that each test one thing: a slip in the
   consonant / buffer rule, the wrong harmony, the wrong person. */
function choices(categoryId, entry, person, n = 6){
  const form = CATEGORY[categoryId].form;
  const correct = form(entry, person).text;
  const out = [correct];
  const take = (list, k) => {
    let added = 0;
    for(const t of list){
      if(added >= k || out.length >= n) return;
      if(!out.includes(t)){ out.push(t); added++; }
    }
  };
  const others = shuffle(PERSONS.filter(q => q !== person));
  const vowels = shuffle(VOWELS.slice());

  take(shuffle([{noSoften:true}, {noBuffer:true}].map(o => form(entry, person, o).text)), 1);
  take(vowels.map(v => form(entry, person, {forceVowel:v}).text), 2);
  take(others.map(q => form(entry, q).text), 2);
  for(const q of others){                                    // wrong on both counts
    take(vowels.map(v => form(entry, q, {forceVowel:v}).text), n);
  }
  return shuffle(out.slice(0, n));
}

/* --- sentences ---------------------------------------------------------- */
const INTRANSITIVE = {
  "Gitmek":    {base:"go",         ing:"going",       past:"went",       group:true},
  "Gelmek":    {base:"come",       ing:"coming",      past:"came",       group:true},
  "Beklemek":  {base:"wait",       ing:"waiting",     past:"waited",     group:true},
  "Çalışmak":  {base:"work",       ing:"working",     past:"worked",     group:true},
  "Düşünmek":  {base:"think",      ing:"thinking",    past:"thought"},
  "Anlamak":   {base:"understand", s:"understands",   past:"understood", stative:true},
  "Bakmak":    {base:"look",       ing:"looking",     past:"looked"},
  "Denemek":   {base:"try",        ing:"trying",      past:"tried"},
  "Uyumak":    {base:"sleep",      ing:"sleeping",    past:"slept",      group:true},
  "Yürümek":   {base:"walk",       ing:"walking",     past:"walked",     group:true},
  "Koşmak":    {base:"run",        ing:"running",     past:"ran"},
  "Oynamak":   {base:"play",       ing:"playing",     past:"played",     group:true},
  "Konuşmak":  {base:"talk",       ing:"talking",     past:"talked"},
  "Okumak":    {base:"read",       ing:"reading",     past:"read"},
  "Yazmak":    {base:"write",      ing:"writing",     past:"wrote"},
  "Oturmak":   {base:"sit",        ing:"sitting",     past:"sat"},
  "Çıkmak":    {base:"go out",     ing:"going out",   past:"went out",   group:true},
  "Dönmek":    {base:"come back",  ing:"coming back", past:"came back",  group:true},
  "Kalmak":    {base:"stay",       ing:"staying",     past:"stayed",     group:true},
};
const TRANSITIVE = {
  "Almak":     {base:"buy",  ing:"buying", past:"bought"},
  "İstemek":   {base:"want", s:"wants",    past:"wanted", stative:true, tenses:["present", "past"]},
  "Yemek":     {base:"eat",   ing:"eating",   past:"ate",   objects: en => !DRINKS.has(en) && !SEASONING.has(en)},
  "İçmek":     {base:"drink", ing:"drinking", past:"drank", objects: en => DRINKS.has(en)},
};
const TIME_WORDS = {
  "Bugün": {en:"today",     tenses:["present", "future", "past"]},
  "Dün":   {en:"yesterday", tenses:["past"]},
  "Yarın": {en:"tomorrow",  tenses:["future"]},
};
// Uncountable in English, so "I bought ___" reads naturally without an article.
const MASS_FOODS = new Set(["Water", "Bread", "Meat", "Cheese", "Milk", "Rice", "Pasta", "Soup",
  "Salad", "Fruit", "Salt", "Sugar", "Tea", "Coffee", "Yogurt", "Chicken", "Fish", "Ice-cream",
  "Chocolate", "Lamb"]);
// What you can drink, and what you wouldn't say you ate on its own.
const DRINKS = new Set(["Water", "Milk", "Tea", "Coffee"]);
const SEASONING = new Set(["Salt", "Sugar"]);

const SLOTS = {
  country:    {source: m => m.startsWith("Countries/"),      accept: e => acceptPlace(e.tr), custom:"place"},
  emotion:    {source: m => m === "Emotions" || m === "Adjectives/People",
               accept: e => acceptFeeling(e.tr), custom:"adjective"},
  family:     {source: m => m.startsWith("Family Members/"), accept: e => acceptPossessed(e.tr)},
  verb:       {source: m => m === "Verbs" || m === "More Verbs", accept: e => !!INTRANSITIVE[e.tr]},
  objectVerb: {source: m => m === "Verbs" || m === "More Verbs", accept: e => !!TRANSITIVE[e.tr]},
  food:       {source: m => m.startsWith("Food/"),           accept: e => MASS_FOODS.has(e.en) && !/\s/.test(e.tr)},
  occupation: {source: m => m === "Occupations",             accept: () => true},
  time:       {source: m => m === "Time/Days",               accept: e => !!TIME_WORDS[e.tr]},
};

/* {slot: [{en, tr, module}]} -- the app narrows these to mastered modules. */
function buildSlotPools(vocab, extra = []){
  const pools = {};
  for(const [slot, def] of Object.entries(SLOTS)){
    const seen = new Set(), list = [];
    const add = e => {
      if(!usable(e.tr) || !def.accept(e) || seen.has(e.tr)) return;
      seen.add(e.tr);
      list.push(e);
    };
    eachEntry(vocab, e => { if(def.source(e.module)) add(e); });
    for(const e of extra) if(def.custom && e.type === def.custom) add(e);
    pools[slot] = list;
  }
  return pools;
}

const cap = s => s.charAt(0).toLocaleUpperCase("tr") + s.slice(1);
const plainEn = en => en.replace(/\s*\(.*?\)/g, "").trim();
const lowEn = en => plainEn(en).toLowerCase();
const midSubject = p => p === "p1s" ? "I" : SUBJECT_EN[p];
const article = en => /^[aeiou]/i.test(en) ? "an" : "a";
const verbEntry = v => ({tr: v.tr, en: v.en});
const FORM_OF = {present, future, past};

function englishVerb(v, tense, p){
  if(tense === "present"){
    if(v.stative) return p === "p3s" ? v.s : v.base;
    return `${BE_EN[p]} ${v.ing}`;
  }
  if(tense === "future") return `${BE_EN[p]} going to ${v.base}`;
  return v.past;
}

/* Verb / time / tense combinations the learner can actually be asked. */
function timedVerbs(ctx, slot, table, filter = () => true){
  const out = [];
  for(const t of ctx.words("time")){
    for(const v of ctx.words(slot)){
      const info = table[v.tr];
      if(!filter(info)) continue;
      for(const tense of TIME_WORDS[t.tr].tenses){
        if(ctx.tenses().includes(tense) && (!info.tenses || info.tenses.includes(tense))){
          out.push({t, v, tense, info});
        }
      }
    }
  }
  return out;
}
function tensedVerbs(ctx, slot, table, filter = () => true){
  const out = [];
  for(const v of ctx.words(slot)){
    const info = table[v.tr];
    if(!filter(info)) continue;
    for(const tense of ctx.tenses()){
      if(!info.tenses || info.tenses.includes(tense)) out.push({v, tense, info});
    }
  }
  return out;
}
/* Object verbs paired with the foods that make sense after them. */
function objectOptions(ctx, timed, minFoods){
  const base = timed ? timedVerbs(ctx, "objectVerb", TRANSITIVE) : tensedVerbs(ctx, "objectVerb", TRANSITIVE);
  return base
    .map(o => Object.assign(o, {foods: ctx.words("food").filter(f => !o.info.objects || o.info.objects(f.en))}))
    .filter(o => o.foods.length >= minFoods);
}
const distinct = (list, k) => shuffle(list.slice()).slice(0, k);
// Pair different people, not "you" with "you all".
const personsExcept = p => PERSONS.filter(q => q[1] !== p[1]);
// A spouse has one owner -- "our husband" isn't a sentence anyone says.
const ONE_OWNER = new Set(["Koca", "Hanım", "Eş"]);
const ownerFor = (...family) => pick(family.some(f => ONE_OWNER.has(f.tr)) ? ["p1s", "p2s", "p3s"] : PERSONS);

/* Each template: a level, a check that it can be filled from what's mastered,
   and a builder returning the English prompt, the Turkish tiles in their
   natural order, and every order that counts as correct (as tile indices). */
const TEMPLATES = [
  {id:"from", level:"easy",
   ready: c => c.words("country").length > 0 && c.has("nerelisin"),
   build(c){
     const place = pick(c.words("country")), p = pick(PERSONS);
     return {en: `${cap(SUBJECT_EN[p])} ${BE_EN[p]} from ${plainEn(place.en)}.`,
             tiles: [PRONOUN[p], nerelisin(place, p).text], orders: [[0, 1]]};
   }},
  {id:"feel", level:"easy",
   ready: c => c.words("emotion").length > 0 && c.has("feelings"),
   build(c){
     const e = pick(c.words("emotion")), p = pick(PERSONS);
     return {en: `${cap(SUBJECT_EN[p])} ${BE_EN[p]} ${lowEn(e.en)}.`,
             tiles: [PRONOUN[p], feelings(e, p).text], orders: [[0, 1]]};
   }},
  {id:"doing", level:"easy",
   ready: c => tensedVerbs(c, "verb", INTRANSITIVE).length > 0,
   build(c){
     const {v, tense, info} = pick(tensedVerbs(c, "verb", INTRANSITIVE)), p = pick(PERSONS);
     return {en: `${cap(SUBJECT_EN[p])} ${englishVerb(info, tense, p)}.`,
             tiles: [PRONOUN[p], FORM_OF[tense](verbEntry(v), p).text], orders: [[0, 1]]};
   }},

  {id:"when", level:"medium",
   ready: c => timedVerbs(c, "verb", INTRANSITIVE).length > 0,
   build(c){
     const {t, v, tense, info} = pick(timedVerbs(c, "verb", INTRANSITIVE)), p = pick(PERSONS);
     return {en: `${cap(TIME_WORDS[t.tr].en)} ${midSubject(p)} ${englishVerb(info, tense, p)}.`,
             tiles: [lower(t.tr), PRONOUN[p], FORM_OF[tense](verbEntry(v), p).text],
             orders: [[0, 1, 2], [1, 0, 2]]};
   }},
  {id:"object", level:"medium",
   ready: c => objectOptions(c, false, 1).length > 0,
   build(c){
     const {v, tense, info, foods} = pick(objectOptions(c, false, 1));
     const f = pick(foods), p = pick(PERSONS);
     return {en: `${cap(SUBJECT_EN[p])} ${englishVerb(info, tense, p)} ${lowEn(f.en)}.`,
             tiles: [PRONOUN[p], lower(f.tr), FORM_OF[tense](verbEntry(v), p).text],
             orders: [[0, 1, 2]]};
   }},
  {id:"family-feel", level:"medium",
   ready: c => c.words("family").length > 0 && c.words("emotion").length > 0 && c.has("possession"),
   build(c){
     const f = pick(c.words("family")), e = pick(c.words("emotion")), p = ownerFor(f);
     return {en: `${cap(POSSESSIVE_EN[p])} ${lowEn(f.en)} is ${lowEn(e.en)}.`,
             tiles: [GENITIVE[p], possession(f, p).text, lower(e.tr)], orders: [[0, 1, 2]]};
   }},
  {id:"family-job", level:"medium",
   ready: c => c.words("family").length > 0 && c.words("occupation").length > 0 && c.has("possession"),
   build(c){
     const f = pick(c.words("family")), j = pick(c.words("occupation")), p = ownerFor(f);
     const job = lowEn(j.en);
     return {en: `${cap(POSSESSIVE_EN[p])} ${lowEn(f.en)} is ${article(job)} ${job}.`,
             tiles: [GENITIVE[p], possession(f, p).text, lower(j.tr)], orders: [[0, 1, 2]]};
   }},

  {id:"two-places", level:"hard",
   ready: c => c.words("country").length > 1 && c.has("nerelisin"),
   build(c){
     const [a, b] = distinct(c.words("country"), 2);
     const p = pick(PERSONS), q = pick(personsExcept(p));
     return {en: `${cap(SUBJECT_EN[p])} ${BE_EN[p]} from ${plainEn(a.en)} and ${midSubject(q)} ${BE_EN[q]} from ${plainEn(b.en)}.`,
             tiles: [PRONOUN[p], nerelisin(a, p).text, "ve", PRONOUN[q], nerelisin(b, q).text],
             orders: [[0, 1, 2, 3, 4], [3, 4, 2, 0, 1]]};
   }},
  {id:"shopping", level:"hard",
   ready: c => objectOptions(c, true, 2).length > 0,
   build(c){
     const {t, v, tense, info, foods} = pick(objectOptions(c, true, 2));
     const [f, g] = distinct(foods, 2), p = pick(PERSONS);
     return {en: `${cap(TIME_WORDS[t.tr].en)} ${midSubject(p)} ${englishVerb(info, tense, p)} ${lowEn(f.en)} and ${lowEn(g.en)}.`,
             tiles: [lower(t.tr), PRONOUN[p], lower(f.tr), "ve", lower(g.tr), FORM_OF[tense](verbEntry(v), p).text],
             orders: [[0, 1, 2, 3, 4, 5], [1, 0, 2, 3, 4, 5], [0, 1, 4, 3, 2, 5], [1, 0, 4, 3, 2, 5]]};
   }},
  {id:"family-plans", level:"hard",
   ready: c => c.words("family").length > 1 && c.has("possession")
            && timedVerbs(c, "verb", INTRANSITIVE, i => i.group).length > 0,
   build(c){
     const {t, v, tense, info} = pick(timedVerbs(c, "verb", INTRANSITIVE, i => i.group));
     const [f, g] = distinct(c.words("family"), 2), p = ownerFor(f, g);
     const my = POSSESSIVE_EN[p];
     return {en: `${cap(TIME_WORDS[t.tr].en)} ${my} ${lowEn(f.en)} and ${my} ${lowEn(g.en)} ${englishVerb(info, tense, "p3p")}.`,
             tiles: [lower(t.tr), possession(f, p).text, "ve", possession(g, p).text, FORM_OF[tense](verbEntry(v), "p3p").text],
             orders: [[0, 1, 2, 3, 4], [1, 2, 3, 0, 4], [0, 3, 2, 1, 4], [3, 2, 1, 0, 4]]};
   }},
  {id:"family-origin", level:"hard",
   ready: c => c.words("family").length > 0 && c.words("country").length > 0 && c.words("emotion").length > 0
            && c.has("possession") && c.has("nerelisin"),
   build(c){
     const f = pick(c.words("family")), place = pick(c.words("country")), e = pick(c.words("emotion"));
     const p = ownerFor(f);
     return {en: `${cap(POSSESSIVE_EN[p])} ${lowEn(f.en)} is from ${plainEn(place.en)} and ${lowEn(e.en)}.`,
             tiles: [GENITIVE[p], possession(f, p).text, nerelisin(place, "p3s").text, "ve", lower(e.tr)],
             orders: [[0, 1, 2, 3, 4], [0, 1, 4, 3, 2]]};
   }},
];

/* To unlock a level you need this many vocab modules and conjugation
   categories mastered, and at least one of its templates fillable. */
const LEVELS = [
  {id:"easy",   name:"Easy",   length:"2 words",   modules:1, categories:1},
  {id:"medium", name:"Medium", length:"3 words",   modules:3, categories:2},
  {id:"hard",   name:"Hard",   length:"5–6 words", modules:5, categories:3},
];

return {
  PERSONS, PRONOUN, GENITIVE, PERSON_EN, VOWELS, CATEGORIES, CATEGORY, TENSES,
  TEMPLATES, LEVELS, SLOTS,
  buildPools, buildSlotPools, isIrregular, choices, shuffle, pick, lower, cap,
  forms: {nerelisin, feelings, possession, present, future, past},
};
})();

if(typeof module !== "undefined" && module.exports) module.exports = Grammar;
