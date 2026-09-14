/* Checks web/grammar.js against hand-verified Turkish forms.
 *
 *   node web/grammar_test.js
 *
 * Add a row here whenever you add a word to an exception list or a new
 * conjugation category -- a wrong suffix is easy to ship and hard to unlearn.
 */
const fs = require("fs");
const path = require("path");
const G = require("./grammar.js");

const EXPECTED = {
  nerelisin: {
    "Bolivya": ["Bolivyalıyım", "Bolivyalısın", "Bolivyalı", "Bolivyalıyız", "Bolivyalısınız", "Bolivyalılar"],
    "Peru": ["Peruluyum", "Perulusun", "Perulu", "Peruluyuz", "Perulusunuz", "Perulular"],
    "Şili": ["Şililiyim", "Şililisin", "Şilili", "Şililiyiz", "Şililisiniz", "Şilililer"],
    "Ürdün": ["Ürdünlüyüm", "Ürdünlüsün", "Ürdünlü", "Ürdünlüyüz", "Ürdünlüsünüz", "Ürdünlüler"],
    "Türkiye": [, , "Türkiyeli", "Türkiyeliyiz"],
    "Güney Kore": [, , "Güney Koreli"],
    "Mısır": [, , , , "Mısırlısınız"],
    "Kıbrıs": ["Kıbrıslıyım"],
    "Ekvador": [, , , , , "Ekvadorlular"],
  },
  feelings: {
    "Yorgun": ["yorgunum", "yorgunsun", "yorgun", "yorgunuz", "yorgunsunuz", "yorgunlar"],
    "Mutlu": ["mutluyum", "mutlusun", "mutlu", "mutluyuz", "mutlusunuz", "mutlular"],
    "Kıskanç": ["kıskancım", "kıskançsın", "kıskanç", "kıskancız", "kıskançsınız", "kıskançlar"],
    "Üzgün": ["üzgünüm", , , , "üzgünsünüz", "üzgünler"],
    "Sakin": [, , , "sakiniz", "sakinsiniz", "sakinler"],
    "Utangaç": ["utangacım"],
    "Endişeli": ["endişeliyim", , , "endişeliyiz"],
    "Korkmuş": [, "korkmuşsun"],
    "Hayal kırıklığına uğramış": ["hayal kırıklığına uğramışım"],
    "Öğretmen": ["öğretmenim", , , "öğretmeniz"],
    "Şoför": [, , , , "şoförsünüz"],
    "Doktor": [, , , , , "doktorlar"],
    "Avukat": ["avukatım", , , "avukatız"],
    "Aşçı": ["aşçıyım"],
    "Diş hekimi": ["diş hekimiyim"],
    "Genç": ["gencim", "gençsin", "genç", "genciz", "gençsiniz", "gençler"],
    "Meşgul": ["meşgulüm", , , , "meşgulsünüz", "meşguller"],
    "Aç": ["açım"],
    "Nazik": ["naziğim"],
    "İyi": ["iyiyim", , , "iyiyiz"],
    "Kötü": ["kötüyüm"],
    "Hasta": ["hastayım", , , , , "hastalar"],
  },
  possession: {
    "Anne": ["annem", "annen", "annesi", "annemiz", "anneniz", "anneleri"],
    "Baba": [, , "babası", , , "babaları"],
    "Kardeş": ["kardeşim", , "kardeşi"],
    "Oğul": ["oğlum", , "oğlu", , , "oğulları"],
    "Ağız": ["ağzım", , "ağzı", , , "ağızları"],
    "Burun": [, "burnun"],
    "Boyun": ["boynum"],
    "Beyin": [, , "beyni"],
    "Göğüs": ["göğsüm"],
    "Omuz": ["omzum"],
    "Kulak": ["kulağım", , "kulağı", "kulağımız", , "kulakları"],
    "Kalp": ["kalbim", , "kalbi", , , "kalpleri"],
    "Göz": [, , , "gözümüz"],
    "Saç": ["saçım", , "saçı"],
    "Diş": [, , , , "dişiniz"],
    "Dayı": [, , "dayısı"],
    "Kız kardeş": ["kız kardeşim", , "kız kardeşi"],
    "Mide": [, , "midesi"],
    "Parmak": ["parmağım"],
    "El": [, "elin"],
    "Dudak": [, , "dudağı"],
    "Su": ["suyum", , "suyu", , , "suları"],
    "Saat": ["saatim", , "saati", , , "saatleri"],
    "Araba": ["arabam", , "arabası"],
  },
  present: {
    "Gitmek": ["gidiyorum", "gidiyorsun", "gidiyor", "gidiyoruz", "gidiyorsunuz", "gidiyorlar"],
    "Anlamak": ["anlıyorum"],
    "Beklemek": ["bekliyorum"],
    "İstemek": ["istiyorum"],
    "Denemek": [, , "deniyor"],
    "Görmek": ["görüyorum"],
    "Bulmak": [, "buluyorsun"],
    "Çalışmak": [, , , "çalışıyoruz"],
    "Düşünmek": [, , , , , "düşünüyorlar"],
    "Olmak": [, , "oluyor"],
    "Sormak": ["soruyorum"],
    "Anlatmak": ["anlatıyorum"],
    "Yemek": ["yiyorum", , "yiyor"],
    "Demek": ["diyorum"],
    "İçmek": ["içiyorum"],
    "Uyumak": ["uyuyorum"],
    "Okumak": [, , "okuyor"],
    "Yürümek": ["yürüyorum"],
    "Oynamak": [, , "oynuyor"],
    "Ödemek": ["ödüyorum"],
    "Yıkamak": ["yıkıyorum"],
    "Yardım etmek": ["yardım ediyorum"],
    "Satmak": [, , "satıyor"],
    "Unutmak": ["unutuyorum"],
    "Konuşmak": [, , , "konuşuyoruz"],
  },
  future: {
    "Gitmek": ["gideceğim", "gideceksin", "gidecek", "gideceğiz", "gideceksiniz", "gidecekler"],
    "Almak": ["alacağım", , , , , "alacaklar"],
    "Beklemek": ["bekleyeceğim"],
    "Anlamak": [, , , "anlayacağız"],
    "İstemek": [, "isteyeceksin"],
    "Görmek": ["göreceğim"],
    "Çalışmak": [, , , , "çalışacaksınız"],
    "Olmak": ["olacağım"],
    "Bulmak": [, , "bulacak"],
    "Yemek": ["yiyeceğim", "yiyeceksin", "yiyecek", "yiyeceğiz", "yiyeceksiniz", "yiyecekler"],
    "Demek": ["diyeceğim"],
    "Yardım etmek": [, , "yardım edecek"],
    "Uyumak": ["uyuyacağım"],
    "Oynamak": [, , "oynayacak"],
    "Ödemek": ["ödeyeceğim"],
    "İçmek": [, , "içecek"],
  },
  past: {
    "Gitmek": ["gittim", "gittin", "gitti", "gittik", "gittiniz", "gittiler"],
    "Yapmak": ["yaptım"],
    "Bakmak": [, , "baktı"],
    "Çalışmak": [, , , "çalıştık"],
    "Anlatmak": [, , , , , "anlattılar"],
    "Görmek": ["gördüm"],
    "Bulmak": [, , , , , "buldular"],
    "İstemek": ["istedim"],
    "Beklemek": [, , , , "beklediniz"],
    "Düşünmek": [, , "düşündü"],
    "Vermek": [, , , , , "verdiler"],
    "Yemek": ["yedim", , "yedi"],
    "Demek": [, , "dedi"],
    "İçmek": ["içtim"],
    "Konuşmak": [, , "konuştu"],
    "Açmak": [, , "açtı"],
    "Yardım etmek": ["yardım ettim"],
    "Okumak": [, , , , , "okudular"],
  },
};

let failures = 0, checked = 0;
for(const [cat, words] of Object.entries(EXPECTED)){
  const form = G.CATEGORY[cat].form;
  for(const [tr, row] of Object.entries(words)){
    row.forEach((want, i) => {
      if(want === undefined) return;
      const got = form({tr, en:""}, G.PERSONS[i]).text;
      checked++;
      if(got !== want){ failures++; console.log(`FAIL ${cat} ${tr} ${G.PERSONS[i]}: got ${got}, want ${want}`); }
    });
  }
}

// Irregular marking is per category, from the exception lists.
for(const [cat, tr, want] of [
  ["future", "Yemek", true], ["present", "Yemek", true], ["past", "Yemek", false],
  ["future", "Demek", true], ["present", "Gitmek", true], ["past", "Gitmek", false],
  ["present", "Yardım etmek", true], ["present", "Anlamak", false], ["future", "Okumak", false],
  ["possession", "Ağız", true], ["possession", "Kalp", true], ["possession", "Kulak", false],
  ["feelings", "Genç", true], ["feelings", "Meşgul", true], ["feelings", "Yorgun", false],
  ["nerelisin", "Bolivya", false],
]){
  checked++;
  const got = G.isIrregular(cat, {tr, en:""});
  if(got !== want){ failures++; console.log(`FAIL irregular ${cat} ${tr}: got ${got}, want ${want}`); }
}

// Wrong answers: six distinct buttons, exactly one of them right.
for(const [cat, tr] of [["possession", "Kulak"], ["future", "Gitmek"], ["nerelisin", "Peru"], ["feelings", "Mutlu"]]){
  for(const p of G.PERSONS){
    const right = G.CATEGORY[cat].form({tr, en:""}, p).text;
    const set = G.choices(cat, {tr, en:""}, p);
    checked++;
    if(set.length !== 6 || new Set(set).size !== 6 || set.filter(t => t === right).length !== 1){
      failures++; console.log(`FAIL choices ${cat} ${tr} ${p}: ${set.join(", ")}`);
    }
  }
}

// Real vocab: which harmony vowels each category can reach.
const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const vocab = JSON.parse(html.match(/<script id="vocab-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const pools = G.buildPools(vocab);
console.log("\ncategory      words  vowels reachable");
for(const c of G.CATEGORIES){
  const vs = new Set(pools[c.id].map(e => e.vowel));
  console.log(`${c.id.padEnd(13)} ${String(pools[c.id].length).padStart(5)}  ${G.VOWELS.map(v => vs.has(v) ? v : "·").join(" ")}`);
}

// Sample sentences with everything unlocked, for reading over.
const slots = G.buildSlotPools(vocab);
const ctx = {words: s => slots[s], has: () => true, tenses: () => G.TENSES};
// My Words: a typed word joins its categories; an untyped one joins none.
{
  const extra = [{tr:"Yüzmek", en:"To swim", module:"My Words", type:"verb"},
                 {tr:"Araba", en:"Car", module:"My Words", type:"noun"},
                 {tr:"Yorgunluk", en:"Tiredness", module:"My Words", type:"word"}];
  const withExtra = G.buildPools(vocab, extra);
  checked++;
  if(!withExtra.present.some(e => e.tr === "Yüzmek") || !withExtra.possession.some(e => e.tr === "Araba")
     || Object.values(withExtra).some(list => list.some(e => e.tr === "Yorgunluk"))){
    failures++; console.log("FAIL My Words routing");
  }
  const irregularNow = Object.fromEntries(G.CATEGORIES.map(c => [c.id, pools[c.id].filter(e => e.irregular).map(e => e.tr)]));
  console.log("\nirregular words by category");
  for(const [id, list] of Object.entries(irregularNow)) console.log(`  ${id.padEnd(11)} ${list.join(", ") || "—"}`);
}

console.log("\nsample sentences");
for(const t of G.TEMPLATES){
  if(!t.ready(ctx)){ failures++; console.log(`FAIL template ${t.id} not fillable with everything mastered`); continue; }
  for(let i = 0; i < 2; i++){
    const s = t.build(ctx);
    checked++;
    const bad = s.orders.some(o => o.length !== s.tiles.length || new Set(o).size !== o.length);
    if(bad){ failures++; console.log(`FAIL template ${t.id} orders`); }
    console.log(`  ${t.level.padEnd(6)} ${s.en}\n         ${s.tiles.join(" ")}`);
  }
}

console.log(`\n${checked - failures}/${checked} checks passed`);
process.exit(failures ? 1 : 0);
