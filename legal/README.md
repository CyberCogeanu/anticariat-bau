# Cadrul Legal si Proceduri de Publicare - Anticariat Albert

Acest modul contine documentatia juridica si scriptul de sincronizare determinista a paginii de **Termeni si Conditii** pentru magazinul online **Anticariat Albert** (Shopify).

---

## 1. Structura Fisiere

- `anticariat_termeni_si_conditii.html`: Documentul HTML semantic complet redactat in limba romana, conform legislatiei nationale si europene aplicabile comertului electronic si anticariatelor.
- `deploy_legal_page.py`: Script Python determinist pentru crearea sau actualizarea paginii Shopify prin Admin GraphQL API (handle: `termeni-si-conditii`).

---

## 2. Conformitate Legislativa si Particularitati de Anticariat

Textul acopera integral cerintele obligatorii din:
- **Legea nr. 365/2002** privind comertul electronic.
- **OUG nr. 34/2014** privind drepturile consumatorilor (termen legal de retragere in 14 zile calendaristice, cost retur in sarcina cumparatorului).
- **OUG nr. 140/2021** privind vanzarea de bunuri si garantiile de conformitate (aplicata specific bunurilor second-hand).
- **Legea nr. 227/2015 (Codul Fiscal)**, Art. 312: Regimul special al marjei de profit pentru bunuri second-hand (TVA neinclus separat pe factura, mentiunea legala obligatorie pe document).
- **Regulamentul (UE) 2016/679 (GDPR)** privind protectia datelor cu caracter personal.
- **Bannere oficiale ANPC si SOL**: Linkuri directe catre ANPC (https://anpc.ro/) si platforma europeana SOL / ODR (https://ec.europa.eu/consumers/odr).

### Clauze esentiale specifice anticariatului:
1. **Exemplar unic si stoc sincronizat fizic & online**: Volumele sunt expuse in magazinul fizic din **Strada Alexandru Lapusneanu nr. 11, Iasi**. Contractul la distanta se incheie doar la confirmarea disponibilitatii fizice pe raft. Daca o carte a fost vanduta la tejghea inainte de sincronizare, comanda se anuleaza fara penalitati si banii platiti cu cardul se restituie in 24 - 48 ore.
2. **Grila obiectiva de gradare a starii**:
   - *Noua / Nefolosita* (lichidari stoc, necitita)
   - *Foarte buna* (urme minime de manipulare)
   - *Buna* (urme normale de lectura, ingalbenire fireasca)
   - *Anticariat / Uzata* (patina timpului, semne descrise explicit)
3. **Modalitati de livrare**: Curier rapid 24 - 48h sau ridicare gratuita din magazinul fizic (rezervare 5 zile lucratoare).
4. **Modalitati de plata**: Card online (Shopify Payments), ramburs la curier sau numerar/card la ridicare.

---

## 3. Placeholders Companie

Pentru personalizarea finala, operatorul poate ajusta urmatoarele variabile marcate in document:
- `[DENUMIRE_FIRMA_SRL]`
- `[CUI_FIRMA]`
- `[NUMAR_REGISTRU_COMERT]`
- `[SEDIU_SOCIAL]`
- `[ADRESA_MAGAZIN_FIZIC]` (implicit: Strada Alexandru Lapusneanu nr. 11, cod postal 700259, Iasi)
- `[EMAIL_CONTACT]`
- `[TELEFON_CONTACT]`
- `[PROGRAM_MAGAZIN]`

---

## 4. Instructiuni de Rulare

### Regula de Securitate
Zero credentiale pe disc. Toti parametrii de autentificare sunt injectati exclusiv prin Doppler.

### Verificare in mod Dry-Run:
```bash
doppler run --project anticariat-bau --config prd -- python3 deploy_legal_page.py --dry-run
```

### Publicare Efectiva in Shopify:
```bash
doppler run --project anticariat-bau --config prd -- python3 deploy_legal_page.py
```

### Nota Privind Permisiunile Shopify:
Pentru crearea de pagini de continut, Custom App-ul din Shopify Admin necesita permisiunile:
- `read_content`
- `write_content`

Daca aceste permisiuni nu sunt inca bifate, activati-le din:
*Shopify Admin -> Settings -> Apps and sales channels -> Develop apps -> [Nume App] -> Configuration -> Admin API access scopes -> Online Store -> bifati read_content & write_content -> Save.*
