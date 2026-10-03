/**
 * Mock Data Fixtures for Anticariat Albert Executive Operator Interface
 * Strictly follows Romanian antiquarian domain models and privacy guidelines (Zero customer PII).
 * No Unicode em dash (U+2014) is used in this file.
 */

export const INITIAL_ORDERS = [
  {
    id: "CMD-2026-1042",
    shopify_order_id: "5839201948",
    created_at: "2026-10-03T09:15:00+03:00",
    customer_display: "Elena V. (Iași)",
    destination_city: "Iași",
    delivery_method: "Curier Rapid (Fan Courier)",
    payment_status: "Plătit online (Card)",
    total_ron: 84.50,
    status: "pending_pack", // 'pending_pack' | 'packed' | 'shipped'
    awb_code: null,
    items: [
      {
        id_product: 10482,
        title: "Istoria credințelor și ideilor religioase (Vol. I)",
        author: "Mircea Eliade",
        publisher: "Editura Științifică și Enciclopedică",
        publication_year: 1981,
        binding: "Cartonata",
        price_ron: 45.00,
        cod_reference: "100482",
        location_id: "C1-R04-S2",
        condition_grade: "Foarte buna",
        packed: false
      },
      {
        id_product: 8391,
        title: "Nunta în cer",
        author: "Mircea Eliade",
        publisher: "Editura Cugetarea",
        publication_year: 1939,
        binding: "Brosata",
        price_ron: 39.50,
        cod_reference: "100839",
        location_id: "C1-R02-S1",
        condition_grade: "Buna",
        packed: false
      }
    ]
  },
  {
    id: "CMD-2026-1043",
    shopify_order_id: "5839202051",
    created_at: "2026-10-03T10:30:00+03:00",
    customer_display: "Radu M. (București - Sector 1)",
    destination_city: "București",
    delivery_method: "Sameday Easybox (Locker Romexpo)",
    payment_status: "Plătit online (Card)",
    total_ron: 65.00,
    status: "pending_pack",
    awb_code: null,
    items: [
      {
        id_product: 12044,
        title: "Moromeții (Volumul I și II)",
        author: "Marin Preda",
        publisher: "Cartea Românească",
        publication_year: 1975,
        binding: "Brosata",
        price_ron: 65.00,
        cod_reference: "101204",
        location_id: "C2-R01-S3",
        condition_grade: "Buna",
        packed: false
      }
    ]
  },
  {
    id: "CMD-2026-1044",
    shopify_order_id: "5839202118",
    created_at: "2026-10-03T11:45:00+03:00",
    customer_display: "Constantin T. (Cluj-Napoca)",
    destination_city: "Cluj-Napoca",
    delivery_method: "Curier Rapid (Fan Courier)",
    payment_status: "Ramburs la livrare (Cash)",
    total_ron: 110.00,
    status: "pending_pack",
    awb_code: null,
    items: [
      {
        id_product: 3412,
        title: "Frații Jderi (Trilogie completă)",
        author: "Mihail Sadoveanu",
        publisher: "Editura Minerva",
        publication_year: 1968,
        binding: "Panza",
        price_ron: 110.00,
        cod_reference: "100341",
        location_id: "C1-R05-S4",
        condition_grade: "Foarte buna",
        packed: false
      }
    ]
  }
];

export const CATALOG_AUTOCOMPLETE_KNOWLEDGE = [
  {
    title: "Istoria literaturii române de la origini până în prezent",
    author: "George Călinescu",
    publisher: "Editura Minerva",
    publication_year: 1982,
    binding: "Cartonata",
    page_count: 1050,
    suggested_price_ron: 95.00,
    isbn: "973210145X",
    category: "Critică literară & Istorie"
  },
  {
    title: "Trilogia culturii",
    author: "Lucian Blaga",
    publisher: "Fundația Regală pentru Literatură și Artă",
    publication_year: 1944,
    binding: "Brosata",
    page_count: 420,
    suggested_price_ron: 120.00,
    isbn: null,
    category: "Filosofie românească"
  },
  {
    title: "Pe culmile disperării",
    author: "Emil Cioran",
    publisher: "Fundația pentru Literatură și Artă Regele Carol II",
    publication_year: 1934,
    binding: "Brosata",
    page_count: 192,
    suggested_price_ron: 180.00,
    isbn: null,
    category: "Filosofie & Eseistică"
  },
  {
    title: "Maitreyi",
    author: "Mircea Eliade",
    publisher: "Editura Națională Ciornei",
    publication_year: 1933,
    binding: "Brosata",
    page_count: 240,
    suggested_price_ron: 65.00,
    isbn: null,
    category: "Literatură română"
  },
  {
    title: "Enigma Otiliei",
    author: "George Călinescu",
    publisher: "Editura pentru Literatură",
    publication_year: 1961,
    binding: "Cartonata",
    page_count: 512,
    suggested_price_ron: 30.00,
    isbn: null,
    category: "Literatură română"
  },
  {
    title: "Craii de Curtea-Veche",
    author: "Mateiu I. Caragiale",
    publisher: "Editura Cartea Românească",
    publication_year: 1929,
    binding: "Cartonata",
    page_count: 210,
    suggested_price_ron: 140.00,
    isbn: null,
    category: "Romane clasice"
  },
  {
    title: "Dacica. Studii și articole privind istoria veche a României",
    author: "Constantin Daicoviciu",
    publisher: "Editura Academiei RSR",
    publication_year: 1969,
    binding: "Panza",
    page_count: 610,
    suggested_price_ron: 55.00,
    isbn: null,
    category: "Istorie & Arheologie"
  }
];

export const COMPETITOR_LEADERBOARD = [
  {
    rank: 1,
    domain: "printrecarti.ro",
    name: "Printre Cărți",
    score: 920000,
    score_display: "920.000",
    catalog_volume: "100.000+ titluri",
    monthly_traffic: "~700.000 vizite",
    badge: "Lider Național",
    badge_type: "gold",
    platform: "PrestaShop",
    headquarters: "București"
  },
  {
    rank: 2,
    domain: "targulcartii.ro",
    name: "Târgul Cărții",
    score: 810000,
    score_display: "810.000",
    catalog_volume: "80.000+ titluri",
    monthly_traffic: "~500.000 vizite",
    badge: "Lanț Fizic + Online",
    badge_type: "silver",
    platform: "OpenCart",
    headquarters: "București (4 librării)"
  },
  {
    rank: 3,
    domain: "anticariat-ursu.ro",
    name: "Anticariat Ursu",
    score: 520000,
    score_display: "520.000",
    catalog_volume: "54.732 în stoc real (107.664 epuizate)",
    monthly_traffic: "~120.000 vizite",
    badge: "Rival Direct Iași",
    badge_type: "bronze",
    platform: "OpenCart",
    headquarters: "Mogoșești, Iași"
  },
  {
    rank: 4,
    domain: "anticariatulonline.com",
    name: "Anticariatul Online",
    score: 310000,
    score_display: "310.000",
    catalog_volume: "35.000 titluri",
    monthly_traffic: "~65.000 vizite",
    badge: "E-Commerce Național",
    badge_type: "standard",
    platform: "WooCommerce",
    headquarters: "Arad"
  },
  {
    rank: 5,
    domain: "anticariat.net",
    name: "Anticariat.net",
    score: 280000,
    score_display: "280.000",
    catalog_volume: "45.000 titluri",
    monthly_traffic: "~60.000 vizite",
    badge: "Portal Istoric & Anunțuri",
    badge_type: "standard",
    platform: "Portal Personalizat",
    headquarters: "București / Național"
  },
  {
    rank: 6,
    domain: "anticariathermes.ro",
    name: "Anticariat Hermes",
    score: 195000,
    score_display: "195.000",
    catalog_volume: "25.000 titluri",
    monthly_traffic: "~40.000 vizite",
    badge: "Regional & Achiziții Iași",
    badge_type: "standard",
    platform: "WooCommerce",
    headquarters: "Cluj-Napoca & Iași"
  },
  {
    rank: 7,
    domain: "anticariatlogos.ro",
    name: "Anticariat Logos",
    score: 180000,
    score_display: "180.000",
    catalog_volume: "23.000 titluri",
    monthly_traffic: "~38.000 vizite",
    badge: "Prezență Activă Iași",
    badge_type: "standard",
    platform: "WooCommerce",
    headquarters: "Iași & Cluj-Napoca"
  },
  {
    rank: 8,
    domain: "anticariatdalles.ro",
    name: "Anticariat Dalles",
    score: 165000,
    score_display: "165.000",
    catalog_volume: "20.000 titluri",
    monthly_traffic: "~35.000 vizite",
    badge: "Prestigiu Istoric",
    badge_type: "standard",
    platform: "OpenCart",
    headquarters: "București (Sala Dalles)"
  },
  {
    rank: 9,
    domain: "anticariat-doamnei.com",
    name: "Anticariatul de pe Doamnei",
    score: 155000,
    score_display: "155.000",
    catalog_volume: "19.000 titluri",
    monthly_traffic: "~32.000 vizite",
    badge: "Centrul Vechi București",
    badge_type: "standard",
    platform: "OpenCart",
    headquarters: "București (Str. Doamnei)"
  },
  {
    rank: 10,
    domain: "anticariat-odin.ro",
    name: "Anticariat Odin",
    score: 140000,
    score_display: "140.000",
    catalog_volume: "18.000 titluri",
    monthly_traffic: "~28.000 vizite",
    badge: "Transilvania Activ",
    badge_type: "standard",
    platform: "PrestaShop",
    headquarters: "Brașov"
  },
  {
    rank: 11,
    domain: "anticariatsophia.ro",
    name: "Anticariat Sophia",
    score: 130000,
    score_display: "130.000",
    catalog_volume: "15.000 titluri",
    monthly_traffic: "~25.000 vizite",
    badge: "Teologie & Științe Iași",
    badge_type: "standard",
    platform: "Platformă Proprie",
    headquarters: "Iași & București"
  },
  {
    rank: 12,
    domain: "carti-vechi.ro",
    name: "Cărți Vechi",
    score: 120000,
    score_display: "120.000",
    catalog_volume: "14.000 titluri",
    monthly_traffic: "~22.000 vizite",
    badge: "Ediții Princeps & Rare",
    badge_type: "standard",
    platform: "PrestaShop",
    headquarters: "București / Național"
  },
  {
    rank: 13,
    domain: "anticariatagora.ro",
    name: "Anticariat Agora",
    score: 110000,
    score_display: "110.000",
    catalog_volume: "12.000 titluri",
    monthly_traffic: "~20.000 vizite",
    badge: "Catalog Generalist",
    badge_type: "standard",
    platform: "PrestaShop",
    headquarters: "Craiova & Iași"
  },
  {
    rank: 14,
    domain: "anticariatarhaic.ro",
    name: "Anticariat Arhaic",
    score: 95000,
    score_display: "95.000",
    catalog_volume: "10.000 titluri",
    monthly_traffic: "~16.000 vizite",
    badge: "Colecții Vintage",
    badge_type: "standard",
    platform: "WooCommerce",
    headquarters: "Sibiu"
  },
  {
    rank: 15,
    domain: "anticariataleph.ro",
    name: "Anticariat Aleph",
    score: 85000,
    score_display: "85.000",
    catalog_volume: "9.000 titluri",
    monthly_traffic: "~14.000 vizite",
    badge: "Drept, Medicină & Iudaică",
    badge_type: "standard",
    platform: "WooCommerce",
    headquarters: "Cluj-Napoca"
  },
  {
    rank: 16,
    domain: "anticariatonline.ro",
    name: "Anticariat Online",
    score: 80000,
    score_display: "80.000",
    catalog_volume: "11.000 titluri",
    monthly_traffic: "~12.000 vizite",
    badge: "Agregare & Vânzări",
    badge_type: "standard",
    platform: "Custom Portal",
    headquarters: "București"
  },
  {
    rank: 17,
    domain: "anticariatalbert.com",
    name: "Anticariat Albert",
    score: 76500,
    score_display: "76.500",
    catalog_volume: "12.488 în stoc activ",
    monthly_traffic: "~4.500 vizite (Legacy)",
    badge: "Librărie Fizică Iași (Lăpușneanu)",
    badge_type: "albert",
    platform: "Modernizare Shopify",
    headquarters: "Strada Lăpușneanu 11, Iași"
  },
  {
    rank: 18,
    domain: "anticariatuldenoapte.ro",
    name: "Anticariatul de Noapte",
    score: 65000,
    score_display: "65.000",
    catalog_volume: "8.000 titluri",
    monthly_traffic: "~9.000 vizite",
    badge: "Eseistică & Filosofie",
    badge_type: "standard",
    platform: "Custom",
    headquarters: "Cluj-Napoca"
  },
  {
    rank: 19,
    domain: "anticariat.org",
    name: "Anticariat.org",
    score: 55000,
    score_display: "55.000",
    catalog_volume: "7.500 titluri",
    monthly_traffic: "~8.000 vizite",
    badge: "Beletristică & Tehnică",
    badge_type: "standard",
    platform: "Custom",
    headquarters: "București / Național"
  },
  {
    rank: 20,
    domain: "anticariat-unu.ro",
    name: "Anticariat Unu",
    score: 48000,
    score_display: "48.000",
    catalog_volume: "6.000 titluri",
    monthly_traffic: "~6.500 vizite",
    badge: "Avangardă & Bibliofilie",
    badge_type: "standard",
    platform: "Custom",
    headquarters: "București"
  },
  {
    rank: 21,
    domain: "cumparcarti.ro",
    name: "Cumpăr Cărți (Serviciu)",
    score: 45000,
    score_display: "45.000",
    catalog_volume: "Achiziții Domiciliu",
    monthly_traffic: "~15.000 vizite",
    badge: "Magnet Achiziții",
    badge_type: "standard",
    platform: "WordPress",
    headquarters: "Național / Iași"
  },
  {
    rank: 22,
    domain: "la-belle-epoque.ro",
    name: "La Belle Époque",
    score: 35000,
    score_display: "35.000",
    catalog_volume: "3.500 titluri",
    monthly_traffic: "~4.000 vizite",
    badge: "Antichități & Cărți Iași",
    badge_type: "standard",
    platform: "Custom",
    headquarters: "Iași"
  }
];

export const FEATURE_RADAR_CARDS = [
  {
    id: "feat_stock_alerts",
    competitor: "Printre Cărți",
    competitor_url: "printrecarti.ro",
    title: "Alerte de Stoc: Notifică-mă când apare cartea",
    benefit_summary: "Clienții pot lăsa adresa de email pentru volume epuizate. Când mama adaugă o carte la raft, clientul primește instant email de achiziție.",
    operational_impact: "Zero efort suplimentar pentru mamă: platforma trimite automat emailul la simpla scanare.",
    status: "pending", // 'approved' | 'rejected' | 'pending'
    impact_score: "+15.000 puncte index"
  },
  {
    id: "feat_cover_filter",
    competitor: "Târgul Cărții",
    competitor_url: "targulcartii.ro",
    title: "Filtrare Rapidă după Tip Copertă (Cartonată / Broșată / Piele)",
    benefit_summary: "Colecționarii caută frecvent ediții cartonate sau legate în piele. Acest filtru crește vânzările cărților vechi valoroase.",
    operational_impact: "Se bazează direct pe câmpul 'Legătură' completat la scanare.",
    status: "pending",
    impact_score: "+10.000 puncte index"
  },
  {
    id: "feat_local_pickup",
    competitor: "Anticariat Dalles",
    competitor_url: "anticariatdalles.ro",
    title: "Rezervare cu Ridicare din Magazin (Str. Lăpușneanu 11)",
    benefit_summary: "Clienții din Iași pot rezerva cartea online și o pot achita și ridica direct din librărie în maxim 48 de ore fără cost de transport.",
    operational_impact: "Comanda apare în lista de împachetare marcată cu eticheta 'Ridicare Magazin'.",
    status: "pending",
    impact_score: "+20.000 puncte index"
  },
  {
    id: "feat_home_buyback",
    competitor: "Printre Cărți & Anticariat Ursu",
    competitor_url: "printrecarti.ro",
    title: "Formular Consignație & 'Cumpărăm Cărți la Domiciliu în Iași'",
    benefit_summary: "O pagină dedicată unde familiile din Iași pot trimite poze cu biblioteci pe care doresc să le vândă sau doneze.",
    operational_impact: "Cererile ajung pe emailul office@anticariatalbert.com cu fotografii atașate.",
    status: "pending",
    impact_score: "+25.000 puncte index"
  },
  {
    id: "feat_out_of_stock_buyback",
    competitor: "Anticariat Ursu & Strategie Arhivă",
    competitor_url: "anticariat-ursu.ro",
    title: "Magnet Achiziții pe Cărți Epuizate: 'Cumpărăm această carte în Iași'",
    benefit_summary: "Pe paginile cărților din arhivă cu stoc zero, afișăm un banner dedicat: 'Ai această carte în bibliotecă? O cumpărăm noi cu plata pe loc în librăria din Strada Lăpușneanu 11!'",
    operational_impact: "Transformă căutările pe Google ale celor ce dețin cărți vechi într-o sursă gratuită de reaprovizionare a stocului.",
    status: "pending",
    impact_score: "+30.000 puncte index"
  }
];

export const SALES_PULSE_SUMMARY = {
  today_sales_ron: 259.50,
  today_orders_count: 3,
  pending_orders_count: 3,
  month_sales_ron: 3140.00,
  month_orders_count: 42,
  average_order_ron: 74.76,
  active_catalog_books: 12488,
  albert_points: 76500,
  target_stage_points: 150000
};
