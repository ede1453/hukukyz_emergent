"""Add Consumer Protection Law (TKHK) and more articles"""

import asyncio
import sys
sys.path.insert(0, '/app')

from backend.database.faiss_store import faiss_manager
from backend.database.mongodb import mongodb_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tüketici Hakları (TKHK - Tüketicinin Korunması Hakkında Kanun)
TKHK_ARTICLES = [
    {
        "madde_no": 3,
        "title": "Tüketici Tanımı",
        "content": """MADDE 3 - Tüketici: Ticari veya mesleki olmayan amaçlarla hareket eden gerçek veya tüzel kişiyi ifade eder.

Tüketici haklarının korunması, piyasada mal ve hizmet sunumu yapan satıcı ve sağlayıcılar ile tüketici arasındaki ilişkilerde uygulanır."""
    },
    {
        "madde_no": 4,
        "title": "Satıcı ve Sağlayıcı",
        "content": """MADDE 4 - Satıcı: Kamu tüzel kişileri de dâhil olmak üzere ticari veya mesleki amaçlarla tüketiciye mal sunan ya da mal sunanın adına ya da hesabına hareket eden gerçek veya tüzel kişiyi,

Sağlayıcı: Kamu tüzel kişileri de dâhil olmak üzere ticari veya mesleki amaçlarla tüketiciye hizmet sunan ya da hizmet sunanın adına ya da hesabına hareket eden gerçek veya tüzel kişiyi ifade eder."""
    },
    {
        "madde_no": 11,
        "title": "Cayma Hakkı",
        "content": """MADDE 11 - Tüketici, mesafeli sözleşmelerde ve kapı dışı satışlarda on dört gün içinde herhangi bir gerekçe göstermeksizin ve cezai şart ödemeksizin sözleşmeden cayma hakkına sahiptir.

Cayma hakkının kullanıldığına dair bildirimin bu süre içinde satıcı veya sağlayıcıya yöneltilmesi yeterlidir."""
    },
    {
        "madde_no": 58,
        "title": "Ayıplı Mal ve Hizmetlerde Tüketici Hakları",
        "content": """MADDE 58 - Satılan bir maldaki ayıbın, malın tüketiciye teslimi tarihinden itibaren altı ay içinde ortaya çıkması durumunda, ayıbın teslim tarihinde var olduğu kabul edilir.

Tüketici, ayıplı maldan kaynaklanan seçimlik haklarını kullanabilir:
a) Satılanı geri vermeye hazır olduğunu bildirerek sözleşmeden dönme,
b) Satılanı alıkoyup ayıp oranında satış bedelinden indirim isteme,
c) Aşırı bir masraf gerektirmediği takdirde, bütün masrafları satıcıya ait olmak üzere satılanın ücretsiz onarılmasını isteme,
d) İmkân varsa, satılanın ayıpsız bir misli ile değiştirilmesini isteme."""
    },
    {
        "madde_no": 73,
        "title": "Tüketici Hakem Heyetleri",
        "content": """MADDE 73 - Tüketici hakem heyetleri, tüketici işlemlerinden doğan uyuşmazlıkların çözümünde görevlidir.

Parasal sınırlar:
- İl hakem heyetleri: Yıllık olarak belirlenen parasal sınıra kadar
- İlçe hakem heyetleri: Daha düşük parasal sınıra kadar

Tüketici mahkemelerine başvuruda bulunmak isteyen tüketici, başvurudan önce hakem heyetine başvuruda bulunmak zorundadır."""
    }
]

# Additional BK (İş Kanunu gibi) Articles
ISKANUNU_ARTICLES = [
    {
        "madde_no": 2,
        "title": "İşçi ve İşveren",
        "content": """MADDE 2 - İşçi: Bir iş sözleşmesine dayanarak çalışan gerçek kişidir.

İşveren: İşçi çalıştıran gerçek veya tüzel kişi yahut tüzel kişiliği olmayan kurum ve kuruluştur.

İş sözleşmesi: Bir tarafın (işçi) bağımlı olarak iş görmeyi, diğer tarafın (işveren) da ücret ödemeyi üstlenmesinden oluşan sözleşmedir."""
    },
    {
        "madde_no": 17,
        "title": "Bildirim Süreleri",
        "content": """MADDE 17 - Belirsiz süreli iş sözleşmelerinin feshinde bildirim süreleri:

- Altı aydan az kıdemlerde: İki hafta
- Altı aydan bir buçuk yıla kadar: Dört hafta  
- Bir buçuk yıldan üç yıla kadar: Altı hafta
- Üç yıldan fazla: Sekiz hafta

İşveren bildirim süresini vermeden feshettiği takdirde, bildirim süresine ait ücret ve diğer haklar peşin olarak ödenir."""
    },
    {
        "madde_no": 32,
        "title": "Hafta Tatili Ücreti",
        "content": """MADDE 32 - İşçilere tatil gününden önce veya sonra iş verilmesi şartıyla hafta tatili gününde çalışmamış olsalar bile bir günlük ücret tutarında hafta tatili ücreti ödenir.

İşçi hafta tatili gününde çalıştırılırsa, fazla çalışma ücretine ek olarak bir günlük ücret de ödenir."""
    },
    {
        "madde_no": 120,
        "title": "Kıdem Tazminatı",
        "content": """MADDE 120 - İşçinin kıdem tazminatına hak kazanabilmesi için:

- İş sözleşmesinin işverence feshedilmesi
- İşçinin askerlik hizmeti dolayısıyla feshetmesi  
- Emeklilik veya yaşlılık aylığı almak amacıyla feshetmesi
- Bağlı oldukları kanunlar gereğince emeklilik için yaş hadlerini doldurmuş olmaları

Kıdem tazminatı, işçinin her geçen tam yıl için otuz günlük ücreti tutarındadır."""
    }
]

# Additional HMK Articles
HMK_ARTICLES = [
    {
        "madde_no": 118,
        "title": "Dava Şartları",
        "content": """MADDE 118 - Dava şartları, davanın esasının incelenebilmesi için bulunması gereken ön koşullardır:

1. Hukuki yararın bulunması
2. Ehliyet  
3. Taraf ehliyeti
4. Husumet
5. Dava için gereken harç ve giderlerin yatırılmış olması

Dava şartları yokluğu halinde, dava usulden reddedilir."""
    },
    {
        "madde_no": 119,
        "title": "Görevli ve Yetkili Mahkeme",
        "content": """MADDE 119 - Davalar, aksine hüküm bulunmadıkça asliye hukuk mahkemesinde görülür.

Konusu bir miktar para veya değeri ölçülebilen bir mal olan davalarda, sulh hukuk mahkemesinin görevine giren bir miktar Yargıtay Birinci Başkanlık Kurulunca belirlenir.

Taraflar aralarında yetki sözleşmesi ile yetkili mahkemeyi kararlaştırabilirler."""
    },
    {
        "madde_no": 125,
        "title": "İhtiyati Tedbir",
        "content": """MADDE 125 - Hakkın güvence altına alınması için zorunluluk arz eden hâllerde ihtiyati tedbir kararı verilebilir.

İhtiyati tedbir kararı verilmesi için:
1. Hakkın varlığının muhtemel olması
2. Hakkın daha sonra korunmasının önemli ölçüde zorlaşacağının veya imkânsız hâle geleceğinin veya acil durumun varlığının

İspat edilmesi gerekir."""
    }
]


async def add_consumer_and_labor_law():
    """Add consumer protection and labor law articles"""
    
    try:
        logger.info("Initializing databases...")
        await mongodb_client.connect()
        await faiss_manager.initialize()
        
        logger.info("Adding consumer protection and labor law documents...")
        
        all_documents = [
            (TKHK_ARTICLES, "TKHK", "tuketici", "tuketici_haklari"),
            (ISKANUNU_ARTICLES, "İşK", "is_hukuku", "borclar_hukuku"),
            (HMK_ARTICLES, "HMK", "usul", "hmk"),
        ]
        
        total_uploaded = 0
        
        for articles, kaynak, hukuk_dali, collection in all_documents:
            logger.info(f"\nProcessing {kaynak} ({len(articles)} articles)...")
            
            texts = []
            metadatas = []
            ids = []
            
            for article in articles:
                full_text = f"{article['title']}\n\n{article['content']}"
                
                metadata = {
                    "doc_id": f"{kaynak}_{article['madde_no']}",
                    "kaynak": kaynak,
                    "doc_type": "kanun",
                    "hukuk_dali": hukuk_dali,
                    "madde_no": article["madde_no"],
                    "title": article["title"],
                    "content": article["content"],
                    "version": "1.0",
                    "status": "active",
                    "is_sample": False
                }
                
                texts.append(full_text)
                metadatas.append(metadata)
                ids.append(f"{kaynak}_m{article['madde_no']}")
            
            if texts:
                await faiss_manager.add_documents(
                    collection_name=collection,
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                total_uploaded += len(texts)
                logger.info(f"✅ Uploaded {len(texts)} {kaynak} articles to {collection}")
        
        logger.info(f"\n🎉 Consumer & Labor Law upload completed!")
        logger.info(f"Total NEW documents uploaded: {total_uploaded}")
        
        stats = faiss_manager.get_stats()
        logger.info(f"\n📊 Updated Collection Stats:")
        total_docs = 0
        for name, stat in stats.items():
            count = stat['document_count']
            total_docs += count
            logger.info(f"  {name}: {count} documents")
        logger.info(f"  TOTAL: {total_docs} documents")
        
        await mongodb_client.close()
        
        return total_uploaded
        
    except Exception as e:
        logger.error(f"Error adding data: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("HukukYZ - Consumer & Labor Law Loader")
    print("=" * 60)
    print()
    
    total = asyncio.run(add_consumer_and_labor_law())
    
    print()
    print("=" * 60)
    print(f"✅ Successfully added {total} documents!")
    print("=" * 60)
    print()
    print("New collections added:")
    print("  - TKHK (Tüketici Hakları): 5 madde")
    print("  - İşK (İş Kanunu): 4 madde")
    print("  - HMK (Hukuk Muhakemeleri): 3 madde")
    print()
