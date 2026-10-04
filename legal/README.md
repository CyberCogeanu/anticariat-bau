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

## 3. Date de Identificare ale Operatorului

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

## 4. Instructiuni de Rulare si Publicare

### Regula de Securitate
Zero credentiale pe disc. Toti parametrii de autentificare Shopify sunt injectati exclusiv prin Doppler (`--project anticariat-bau --config prd`).

### Verificare in mod Dry-Run:
```bash
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html --dry-run
```

### Publicare Efectiva in Shopify:
```bash
doppler run --project anticariat-bau --config prd -- python3 bau/legal/deploy_legal_page.py --file bau/legal/anticariat_termeni_si_conditii.html
```

### Nota Privind Permisiunile Shopify:
Pentru crearea si actualizarea de pagini de continut, Custom App-ul din Shopify Admin utilizeaza permisiunile:
- `read_content`
- `write_content`

