"""Script to add more legal documents - Extended dataset"""

import asyncio
import sys
sys.path.insert(0, '/app')

from backend.database.faiss_store import faiss_manager
from backend.database.mongodb import mongodb_client
from backend.utils.embeddings import get_embeddings_batch
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Additional TTK Articles
ADDITIONAL_TTK = [
    {
        "madde_no": 6,
        "title": "Ticari İşletme",
        "content": """MADDE 6 - (1) Ticari işletme, esnaf işletmesi için öngörülen sınırı aşan düzeyde gelir sağlamayı hedef tutan faaliyetlerin devamlı ve bağımsız şekilde yürütüldüğü işletmedir.

(2) Ticari işletme, işletme sahibinin kişisel emeğini aşan düzeyde sermaye ve emek birleşimini gerektirir."""
    },
    {
        "madde_no": 18,
        "title": "Ticaret Unvanı",
        "content": """MADDE 18 - (1) Tacir, ticari işletmesini bir ticaret unvanı altında işletir.

(2) Ticaret unvanı, ticari işletmeyi tanıtan ve diğer işletmelerden ayıran isimdir.

(3) Gerçek kişi tacirler için ticaret unvanında en az soyadı bulunur."""
    },
    {
        "madde_no": 137,
        "title": "Kollektif Şirketin Temsili",
        "content": """MADDE 137 - (1) Aksi kararlaştırılmadıkça, kollektif şirketin temsil yetkisi her ortağa aittir.

(2) Temsil yetkisi şirket sözleşmesi ile sınırlandırılabilir.

(3) Şirketi temsile yetkili ortak, şirket adına her türlü hukuki işlemi yapabilir."""
    },
    {
        "madde_no": 340,
        "title": "Anonim Şirket Yönetim Kurulu",
        "content": """MADDE 340 - (1) Anonim şirketin yönetim kurulu en az üç üyeden oluşur.

(2) Yönetim kurulu üyeleri pay sahipleri arasından genel kurul tarafından seçilir.

(3) Yönetim kurulu üyelerinin görev süresi üç yılı geçemez."""
    },
    {
        "madde_no": 621,
        "title": "Limited Şirket Yönetimi",
        "content": """MADDE 621 - (1) Limited şirket müdürler tarafından yönetilir ve temsil olunur.

(2) En az bir müdür şirket merkezinin bulunduğu yerde ikamet etmelidir.

(3) Müdürler genel kurulca atanır."""
    }
]

# Additional TBK Articles
ADDITIONAL_TBK = [
    {
        "madde_no": 11,
        "title": "Genel İşlem Koşulları",
        "content": """MADDE 11 - (1) Bir sözleşme türüne özgü olmak üzere, bir tarafça hazırlanan ve sözleşme kurulurken karşı tarafa sunulan genel işlem koşulları, karşı tarafın bunları kabul etmesiyle sözleşmenin içeriği hâline gelir.

(2) Genel işlem koşullarının, karşı tarafın menfaatlerini ağır biçimde zedeleyici ve dürüstlük kurallarına aykırı düşen hükümleri geçersizdir."""
    },
    {
        "madde_no": 26,
        "title": "Hakkın Kötüye Kullanılması",
        "content": """MADDE 26 - (1) Bir hakkın açıkça kötüye kullanılmasını hukuk düzeni korumaz.

(2) Özellikle bir hak, başkasına zarar vermek, kendine yarar sağlamamak veya amacına uymayan bir sonuca yol açmak maksadıyla kullanılıyorsa kötüye kullanılmış sayılır."""
    },
    {
        "madde_no": 136,
        "title": "Alacaklı Temerrüdü",
        "content": """MADDE 136 - (1) Alacaklı borcun ifasını kabule hazır değilse veya alacaklıya yüklenebilen bir sebeple ifası mümkün olmazsa, alacaklı temerrüde düşer.

(2) Alacaklının temerrüdü hâlinde, borçlu borcun ifası için hazırlık yapmış bulunursa, alacaklı ifaya ilişkin masrafları ödemekle yükümlüdür."""
    },
    {
        "madde_no": 179,
        "title": "Tazminat Türleri",
        "content": """MADDE 179 - Tazminat, zarar görenin malvarlığındaki eksilmeyi (olumlu zarar), malvarlığında meydana gelmesi olanaklı artışın gerçekleşmemesini (yoksun kalınan kâr) ve manevi zararı kapsar."""
    },
    {
        "madde_no": 438,
        "title": "Satıcının Ayıptan Sorumluluğu",
        "content": """MADDE 438 - (1) Satıcı, satılanı alıcıya sözleşmeye uygun olarak teslimle yükümlüdür.

(2) Satılan malın niteliği bakımından öngörülen veya sözleşmede kararlaştırılan kullanım amacına uygun olmaması ayıp sayılır.

(3) Satıcı ayıptan, bu ayıbın satılanın ona teslim anında bulunmuş olması hâlinde sorumludur."""
    }
]

# Additional İİK Articles  
ADDITIONAL_IIK = [
    {
        "madde_no": 16,
        "title": "İcra Emri",
        "content": """MADDE 16 - İcra emri, borçluya yapılacak bir ihtar olup borcun yedi gün içinde ödenmesi veya mal bildiriminde bulunulmasını içerir.

İcra emrinde borçlunun borca itiraz edebileceği de belirtilir."""
    },
    {
        "madde_no": 45,
        "title": "Haciz",
        "content": """MADDE 45 - (1) Haciz, borçlunun mallarının tasfiye için muhafaza altına alınmasıdır.

(2) Haciz, icra dairesince yapılır ve tutanak düzenlenir.

(3) Haczedilen mallar üzerinde borçlunun tasarruf yetkisi ortadan kalkar."""
    },
    {
        "madde_no": 82,
        "title": "İflas Yoluyla Takip",
        "content": """MADDE 82 - (1) İflasa tabi olan borçlular aleyhine yapılacak takiplerde iflas yolu takip edilebilir.

(2) İflas yoluyla takip, borcun tamamının tahsili için yapılır.

(3) İflas kararı mahkemece verilir."""
    },
    {
        "madde_no": 166,
        "title": "Borçların Sırası",
        "content": """MADDE 166 - İflas masasına giren malların paraya çevrilmesinden elde edilen bedel, imtiyazlı alacaklara öncelikle ödenir. Kalan miktar adi alacaklılara paylaştırılır."""
    }
]

# TMK (Medeni Kanun) Articles
TMK_ARTICLES = [
    {
        "madde_no": 1,
        "title": "Kanunun Kaynağı",
        "content": """MADDE 1 - Kanun, lafzı ve ruhuna göre uygulanır.

Kanunda uygulanabilir bir hüküm yoksa, hâkim, örf ve âdet hukukuna göre, bu da yoksa kendisi kanun koyucu olsaydı nasıl bir kural koyacak idiyse ona göre karar verir."""
    },
    {
        "madde_no": 2,
        "title": "İyiniyet",
        "content": """MADDE 2 - Herkes, haklarını kullanırken ve borçlarını yerine getirirken dürüstlük kurallarına uymak zorundadır.

Bir hakkın açıkça kötüye kullanılmasını hukuk düzeni korumaz."""
    },
    {
        "madde_no": 8,
        "title": "İspat Yükü",
        "content": """MADDE 8 - Kanunda aksine bir hüküm bulunmadıkça, taraflardan her biri, hakkını dayandırdığı olguların varlığını ispatla yükümlüdür."""
    }
]


async def add_extended_data():
    """Add extended legal document dataset"""
    
    try:
        # Initialize databases
        logger.info("Initializing databases...")
        await mongodb_client.connect()
        await faiss_manager.initialize()
        
        logger.info("Adding extended legal documents...")
        
        # Prepare all documents
        all_documents = [
            (ADDITIONAL_TTK, "TTK", "ticaret", "ticaret_hukuku"),
            (ADDITIONAL_TBK, "TBK", "borclar", "borclar_hukuku"),
            (ADDITIONAL_IIK, "İİK", "icra", "icra_iflas"),
            (TMK_ARTICLES, "TMK", "medeni", "medeni_hukuk"),
        ]
        
        total_uploaded = 0
        
        for articles, kaynak, hukuk_dali, collection in all_documents:
            logger.info(f"\nProcessing {kaynak} ({len(articles)} articles)...")
            
            texts = []
            metadatas = []
            ids = []
            
            for article in articles:
                # Combine title and content
                full_text = f"{article['title']}\n\n{article['content']}"
                
                # Prepare metadata
                metadata = {
                    "doc_id": f"extended_{kaynak}",
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
                ids.append(f"extended_{kaynak}_{article['madde_no']}")
            
            # Upload to FAISS
            if texts:
                await faiss_manager.add_documents(
                    collection_name=collection,
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                total_uploaded += len(texts)
                logger.info(f"✅ Uploaded {len(texts)} {kaynak} articles to {collection}")
        
        logger.info(f"\n🎉 Extended data upload completed!")
        logger.info(f"Total NEW documents uploaded: {total_uploaded}")
        
        # Get stats
        stats = faiss_manager.get_stats()
        logger.info(f"\n📊 Updated Collection Stats:")
        for name, stat in stats.items():
            logger.info(f"  {name}: {stat['document_count']} documents")
        
        # Close connections
        await mongodb_client.close()
        
        return total_uploaded
        
    except Exception as e:
        logger.error(f"Error adding extended data: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("HukukYZ - Extended Legal Documents Loader")
    print("=" * 60)
    print()
    
    # Run async function
    total = asyncio.run(add_extended_data())
    
    print()
    print("=" * 60)
    print(f"✅ Successfully added {total} extended documents!")
    print("=" * 60)
    print()
    print("New articles added:")
    print("  - TTK: 5 additional articles")
    print("  - TBK: 5 additional articles")
    print("  - İİK: 4 additional articles")
    print("  - TMK: 3 articles (NEW)")
    print()
