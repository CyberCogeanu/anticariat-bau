# Cadrul Legal si Proceduri de Publicare - Anticariat Albert

Acest modul contine documentatia juridica si scriptul de sincronizare determinista a documentelor **Termeni si Conditii** si **Politica de Confidentialitate (GDPR)** pentru magazinul online **Anticariat Albert** (Shopify).

---

## 1. Structura Fisiere

- `anticariat_termeni_si_conditii.html`: Documentul HTML semantic complet redactat in limba romana, conform legislatiei nationale si europene aplicabile comertului electronic si anticariatelor. Include stilizare universala inline (fara blocuri izolate `<style>` sau etichete `<head>`) pentru compatibilitate perfecta pe ambele endpoint-uri Shopify.
- `anticariat_politica_de_confidentialitate.html`: Politica de Confidentialitate GDPR (12 sectiuni), cu acelasi sistem vizual (carduri sumar, badge-uri numerotate, callout fiscal 10 ani, tabel sinteza prelucrari, card CTA ANSPDCP).
- `deploy_legal_page.py`: Script Python determinist pentru sincronizarea ambelor documente prin Admin GraphQL API atat ca Online Store Page (`/pages/*`), cat si ca Native Shop Policy (`/policies/*`). Preset selectat cu `--type terms|privacy` sau detectat automat din numele fisierului.

| Document | Page handle | Page ID | Shop Policy |
|---|---|---|---|
| Termeni si Conditii | `termeni-si-conditii` | `gid://shopify/Page/762875904391` | `TERMS_OF_SERVICE` -> `/policies/terms-of-service` |
| Politica de Confidentialitate | `politica-de-confidentialitate` | `gid://shopify/Page/762881114503` | `PRIVACY_POLICY` -> `/policies/privacy-policy` |

---

## 2. Arhitectura de Publicare Duala (Page vs. Shop Policy)

Shopify gestioneaza termenii legali prin doua mecanisme distincte:
1. **Online Store Page (`/pages/termeni-si-conditii`):**
   - Resursa: `gid://shopify/Page/762875904391`
   - Accesibila direct din meniul de navigare si footer.
   - Permite HTML standard randat in template-ul temei Dawn/Horizon.
2. **Native Shop Policy (`/policies/terms-of-service`):**
   - Resursa: `ShopPolicy` de tip `TERMS_OF_SERVICE`.
   - Accesibila automat in procesul de checkout Shopify si linkurile de sistem.
   - **Particularitate critica:** Motorul nativ de politici Shopify filtreaza etichetele `<style>`, `<head>`, `<title>`, dar arunca continutul lor textual direct in fluxul vizual al documentului daca sunt transmise ca atare.

### Solutia implementata:
- Continutul HTML foloseste exclusiv stiluri inline (`style="..."`) si taguri semantice native (`<article>`, `<section>`, `<h2>`, `<h3>`, `<table>`, `<div>`).
- S-au eliminat complet etichetele `<html>`, `<head>`, `<title>`, `<meta>`, `<body>` si `<style>`.
- Ambele pagini randeaza identic, curat, cu tipografie eleganta si fara scurgeri de cod CSS.

---

## 3. Conformitate Legislativa si Particularitati de Anticariat

Textul acopera integral cerintele obligatorii din:
- **Legea nr. 365/2002** privind comertul electronic.
- **OUG nr. 34/2014** privind drepturile consumatorilor (drept legal de retur in 14 zile calendaristice de la primire, cost retur in sarcina cumparatorului).
- **OUG nr. 140/2021** privind vanzarea de bunuri si garantiile de conformitate (aplicata specific bunurilor second-hand).
- **Legea nr. 227/2015 (Codul Fiscal)**, Art. 312: Regimul special al marjei de profit pentru bunuri second-hand (TVA neinclus separat pe factura, mentiunea legala obligatorie pe document: *"regimul marjei - bunuri second-hand"*).
- **Regulamentul (UE) 2016/679 (GDPR)** privind protectia datelor cu caracter personal.
- **Bannere oficiale ANPC si SOL**: Linkuri directe catre ANPC (https://anpc.ro/) si platforma europeana SOL / ODR (https://ec.europa.eu/consumers/odr).

### Clauze esentiale specifice anticariatului:
1. **Exemplar unic si stoc sincronizat fizic & online**: Volumele sunt expuse in magazinul fizic din **Strada Alexandru Lapusneanu nr. 11, Iasi**. Contractul la distanta se incheie doar la confirmarea disponibilitatii fizice pe raft. Daca o carte a fost vanduta la tejghea inainte de sincronizare, comanda se anuleaza fara penalitati si banii platiti cu cardul se restituie in 24 - 48 ore lucratoare.
2. **Grila obiectiva de gradare a starii**:
   - *Noua / Nefolosita* (lichidari stoc, necitita)
   - *Foarte buna* (urme minime de manipulare)
   - *Buna* (urme normale de lectura, ingalbenire fireasca)
   - *Anticariat / Uzata* (patina timpului, semne descrise explicit)
3. **Modalitati de livrare**: Curier rapid 24 - 48h sau ridicare gratuita din magazinul fizic (cu confirmare telefonica sau prin e-mail prealabila, rezervare 5 zile lucratoare).
4. **Modalitati de plata**: Card online (Shopify Payments), ramburs la curier sau numerar/card la ridicarea din magazin.

---

## 4. Date de Identificare ale Operatorului

Documentul include datele autentice de identificare ale operatorului comercial:
- **Denumire operator:** Albert M. Maria PFA
- **Cod Unic de Inregistrare (CUI):** 40913605
- **Nr. Registrul Comertului (ORC):** F22/443/04.04.2019
- **Sediu social / Corespondenta:** OP 1, CP 58, Iasi, Cod postal 700750
- **Cont bancar (IBAN):** RO44INGB000099909043235 (ING Bank Romania)
- **Punct de lucru (Magazin fizic):** Strada Alexandru Lapusneanu nr. 11, cod postal 700259, Iasi, Romania
- **E-mail de contact:** contact@anticariatalbert.com
- **Telefon de asistenta:** +40 760 806 656
- **Program magazin fizic:** Luni - Vineri: 09:00 - 17:00, Sambata: 10:00 - 15:00, Duminica: Inchis

---

## 5. Instructiuni de Rulare si Publicare

### Regula de Securitate
Zero credentiale pe disc. Toti parametrii de autentificare Shopify sunt injectati exclusiv prin Doppler (`--project anticariat-bau --config prd`).

### Verificare in mod Dry-Run:
```bash
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html --dry-run
```

### Publicare Simultan pe Ambele Endpoint-uri (Page + Shop Policy):
```bash
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html
```

### Optiuni de Targetare Individuala:
```bash
# Sincronizare exclusiva pentru Pagina Online Store (/pages/termeni-si-conditii)
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html --target page

# Sincronizare exclusiva pentru Politica Nativa Shopify (/policies/terms-of-service)
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html --target policy
```

### Politica de Confidentialitate (Page + Shop Policy):
```bash
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --type privacy --dry-run
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --type privacy
```

---

## 6. Politica de Confidentialitate: Audit si Particularitati

### Benchmark (Octombrie 2026)
- **Textul anterior** de pe `/policies/privacy-policy` era sablonul generic generat automat de Shopify (fara operator identificat, fara temeiuri GDPR Art. 6, fara termene de pastrare, fara ANSPDCP).
- **Printre Carti** (`printrecarti.ro/politica-de-confidentialitate`): structura I-VII buna (operator, categorii, scopuri + temeiuri, durata, dezvaluire, transfer, drepturi), dar nu mentioneaza ANSPDCP cu date de contact, nu are tabel sinteza si nu acopera minorii sau securitatea.
- **Documentul nostru** preia structura lor si adauga: tabel categorii/scop/temei/durata, callout fiscal 10 ani (Legea 82/1991), garantia "fara stocare date card" (PCI-DSS), transfer international (decizie de adecvare Canada + SCC 2021/914), card ANSPDCP cu adresa si link, securitate si minori.

### Gotcha Shopify: politica gestionata automat
- `shopPolicyUpdate` pentru `PRIVACY_POLICY` esueaza cu `Automatic management for Privacy Policy must be turned off` cat timp e activa gestionarea automata (Settings > Customer privacy).
- Scriptul detecteaza eroarea, apeleaza `privacyFeaturesDisable(featuresToDisable: [PRIVACY_POLICY])` si reincearca. Gestionarea automata a fost dezactivata pe 2026-10-04; Shopify nu va mai rescrie textul.
- Parserul `/policies/*` elimina tagul `<article>` si spatiile din atributele `style`, dar pastreaza flex/grid, badge-urile si tabelele. Verificarile de stil trebuie facute fara spatii (`align-items:flex-start`).

### Puncte de validat de catre operator
- Lista curierilor (Fan Courier, Sameday, DPD, Posta Romana) si mentiunea contabil CECCAR: de confirmat ca reflecta furnizorii reali.
- Telefonul ANSPDCP (+40 318 059 211/212) provine din datele publice ale autoritatii; de reverificat periodic.
- Newsletter-ul este descris ca serviciu bazat pe consimtamant; daca nu exista inca formular, sectiunea ramane valabila preventiv.
