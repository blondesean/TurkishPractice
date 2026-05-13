import io

new_vocab = """Numbers	Main	1	Bir
Numbers	Main	2	İki
Numbers	Main	3	Üç
Numbers	Main	4	Dört
Numbers	Main	5	Beş
Numbers	Main	6	Altı
Numbers	Main	7	Yedi
Numbers	Main	8	Sekiz
Numbers	Main	9	Dokuz
Numbers	Main	10	On
Numbers	Main	20	Yirmi
Numbers	Main	30	Otuz
Numbers	Main	40	Kırk
Numbers	Main	50	Elli
Numbers	Main	60	Altmış
Numbers	Main	70	Yetmiş
Numbers	Main	80	Seksen
Numbers	Main	90	Doksan
Numbers	Main	100	Yüz
Verbs	Main	To be	Olmak
Verbs	Main	To do / To make	Yapmak
Verbs	Main	To go	Gitmek
Verbs	Main	To come	Gelmek
Verbs	Main	To say	Demek
Verbs	Main	To see	Görmek
Verbs	Main	To take / To buy	Almak
Verbs	Main	To give	Vermek
Verbs	Main	To want	İstemek
Verbs	Main	To know	Bilmek
Verbs	Main	To think	Düşünmek
Verbs	Main	To find	Bulmak
Verbs	Main	To understand	Anlamak
Verbs	Main	To work / To study	Çalışmak
Verbs	Main	To look	Bakmak
Verbs	Main	To use	Kullanmak
Verbs	Main	To ask	Sormak
Verbs	Main	To tell / To explain	Anlatmak
Verbs	Main	To try	Denemek
Verbs	Main	To wait	Beklemek
Food	Main	Water	Su
Food	Main	Bread	Ekmek
Food	Main	Meat	Et
Food	Main	Chicken	Tavuk
Food	Main	Fish	Balık
Food	Main	Egg	Yumurta
Food	Main	Cheese	Peynir
Food	Main	Milk	Süt
Food	Main	Apple	Elma
Food	Main	Tomato	Domates
Food	Main	Potato	Patates
Food	Main	Onion	Soğan
Food	Main	Rice	Pirinç
Food	Main	Pasta	Makarna
Food	Main	Soup	Çorba
Food	Main	Salad	Salata
Food	Main	Fruit	Meyve
Food	Main	Vegetable	Sebze
Food	Main	Salt	Tuz
Food	Main	Sugar	Şeker
Emotions	Main	Happy	Mutlu
Emotions	Main	Sad	Üzgün
Emotions	Main	Angry	Kızgın
Emotions	Main	Tired	Yorgun
Emotions	Main	Surprised	Şaşkın
Emotions	Main	Scared	Korkmuş
Emotions	Main	Excited	Heyecanlı
Emotions	Main	Bored	Sıkılmış
Emotions	Main	Confused	Kafası karışık
Emotions	Main	Anxious	Endişeli
Emotions	Main	Calm	Sakin
Emotions	Main	Nervous	Gergin
Emotions	Main	Proud	Gururlu
Emotions	Main	Disappointed	Hayal kırıklığına uğramış
Emotions	Main	Jealous	Kıskanç
Emotions	Main	Hopeful	Umutlu
Emotions	Main	Lonely	Yalnız
Emotions	Main	Shy	Utangaç
Emotions	Main	Relieved	Rahatlamış
Emotions	Main	Guilty	Suçlu
Occupations	Main	Teacher	Öğretmen
Occupations	Main	Doctor	Doktor
Occupations	Main	Engineer	Mühendis
Occupations	Main	Nurse	Hemşire
Occupations	Main	Lawyer	Avukat
Occupations	Main	Police Officer	Polis
Occupations	Main	Chef / Cook	Aşçı
Occupations	Main	Waiter	Garson
Occupations	Main	Student	Öğrenci
Occupations	Main	Manager	Müdür
Occupations	Main	Accountant	Muhasebeci
Occupations	Main	Driver	Şoför
Occupations	Main	Farmer	Çiftçi
Occupations	Main	Writer	Yazar
Occupations	Main	Artist	Sanatçı
Occupations	Main	Musician	Müzisyen
Occupations	Main	Actor	Oyuncu
Occupations	Main	Secretary	Sekreter
Occupations	Main	Architect	Mimar
Occupations	Main	Businessman	İş adamı"""

file_path = r"g:\Programming\TurkishPractice\vocab_turkish.txt"
with open(file_path, 'a', encoding='utf-8') as f:
    f.write('\n' + new_vocab + '\n')
