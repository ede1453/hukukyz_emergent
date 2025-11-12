"""Script to create sample legal documents for testing"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.qdrant_client import qdrant_manager
from backend.database.faiss_store import faiss_manager
from backend.database.mongodb import mongodb_client
from backend.utils.embeddings import get_embeddings_batch
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample TTK Articles
SAMPLE_TTK_ARTICLES = [
    {
        "madde_no": 11,
        "title": "Ticaret Şirketlerinin Kuruluşu",
        "content": """MADDE 11 - (1) Ticaret şirketleri, bu Kanunda öngörülen şirket türlerinden birisinin kurulması suretiyle ve bu Kanunda yazılı kurallara uyularak kurulur.

(2) Ticaret şirketlerinin kuruluşunda şirket sözleşmesi yapılması zorunludur. Sermaye şirketlerinde şirket sözleşmesi, noter tarafından onaylanmış bir sözleşme ile düzenlenir.

(3) Ticaret şirketleri, tescil ile tüzel kişilik kazanırlar.

(4) Ticaret şirketlerinin kuruluşunda bu Kanunda öngörülen asgari sermaye şartlarına uyulması zorunludur."""
    },
    {
        "madde_no": 124,
        "title": "Kollektif Şirketin Tanımı",
        "content": """MADDE 124 - (1) Kollektif şirket, bir ticari işletmeyi, ticari unvan altında işletmek amacıyla gerçek kişiler tarafından kurulan ve ortakların tamamının şirket alacaklılarına karşı, şirket borçlarından dolayı sınırsız sorumluluğu altında oldukları şirkettir.

(2) Kollektif şirket ortakları, şirket borçlarından dolayı kişisel ve müteselsil olarak sorumludur.

(3) Kollektif şirkette, ortakların sorumluluğu aksine sözleşme yapılmak suretiyle sınırlandırılamaz."""
    },
    {
        "madde_no": 329,
        "title": "Anonim Şirketin Tanımı",
        "content": """MADDE 329 - (1) Anonim şirket, sermayesi belirli ve paylara bölünmüş olan, borçlarından dolayı yalnız malvarlığıyla sorumlu bulunan şirkettir.

(2) Ortaklar, sadece taahhüt etmiş oldukları sermaye payları ile ve şirkete karşı sorumlu olup, şirket alacaklılarına karşı kişisel sorumlulukları yoktur.

(3) Anonim şirketler, en az elli bin Türk Lirası sermaye ile kurulabilir."""
    }
]

# Sample TBK Articles
SAMPLE_TBK_ARTICLES = [
    {
        "madde_no": 1,
        "title": "Sözleşmenin Kurulması",
        "content": """MADDE 1 - (1) Sözleşme, tarafların karşılıklı ve birbirine uygun irade beyanlarıyla kurulur.

(2) İrade beyanları söz, yazı veya başka bir şekilde açıkça veya örtülü olarak yapılabilir.

(3) Sözleşmenin kurulması için kanunda veya taraflarca kabul edilen bir şekle uyulması gerekli olan durumlarda, o şekil yerine getirilmedikçe sözleşme kurulmaz."""
    },
    {
        "madde_no": 112,
        "title": "İfa Zamanı",
        "content": """MADDE 112 - (1) Borç, tarafların anlaşması, borcun niteliği veya kanun gereği hemen ifa edilmelidir.

(2) Belirli bir günde ifa edilmesi gereken borçlarda, o gün sonunda ifanın gerçekleşmemesi halinde borçlu temerrüde düşer.

(3) İfanın belirli bir süre içinde yapılması öngörülmüşse, aksi kararlaştırılmadıkça borçlu o sürenin son günü sonuna kadar ifada bulunabilir."""
    }
]

# Sample İİK Articles
SAMPLE_IIK_ARTICLES = [
    {
        "madde_no": 1,
        "title": "İcranın Şartları",
        "content": """MADDE 1 - Alacaklı, mahkeme kararına veya diğer bir ilam niteliğindeki belgeye dayanarak alacağını icra dairesi aracılığıyla tahsil edebilir.

İcra takibi, borcun muaccel olması ve alacaklının icra takibi için başvurması ile başlar."""
    }
]


async def create_sample_documents():
    """Create sample legal documents in Qdrant and MongoDB"""
    
    try:
        # Initialize connections
        logger.info("Initializing databases...")
        await mongodb_client.connect()
        await qdrant_manager.initialize()
        
        logger.info("Creating sample documents...")
        
        # Prepare all documents
        all_documents = [
            (SAMPLE_TTK_ARTICLES, "TTK", "ticaret", "ticaret_hukuku"),
            (SAMPLE_TBK_ARTICLES, "TBK", "borclar", "borclar_hukuku"),
            (SAMPLE_IIK_ARTICLES, "İİK", "icra", "icra_iflas")
        ]
        
        total_uploaded = 0
        
        for articles, kaynak, hukuk_dali, collection in all_documents:
            logger.info(f"\nProcessing {kaynak} ({len(articles)} articles)...")
            
            points = []
            
            for article in articles:
                # Combine title and content
                full_text = f"{article['title']}\n\n{article['content']}"
                
                # Generate embedding
                embedding = await asyncio.create_task(
                    get_embeddings_batch([full_text])
                )
                
                if not embedding or embedding[0] is None:
                    logger.error(f"Failed to generate embedding for {kaynak} m.{article['madde_no']}")
                    continue
                
                # Create point
                point_id = f"sample_{kaynak}_{article['madde_no']}"
                payload = {
                    "doc_id": f"sample_{kaynak}",
                    "kaynak": kaynak,
                    "doc_type": "kanun",
                    "hukuk_dali": hukuk_dali,
                    "madde_no": article["madde_no"],
                    "title": article["title"],
                    "content": article["content"],
                    "version": "1.0",
                    "status": "active",
                    "is_sample": True
                }
                
                points.append({
                    "id": point_id,
                    "vector": embedding[0],
                    "payload": payload
                })
            
            # Upload to Qdrant
            if points:
                success = qdrant_manager.upsert_points(collection, points)
                if success:
                    total_uploaded += len(points)
                    logger.info(f"✅ Uploaded {len(points)} {kaynak} articles to {collection}")
                else:
                    logger.error(f"❌ Failed to upload {kaynak} articles")
        
        logger.info(f"\n🎉 Sample data creation completed!")
        logger.info(f"Total documents uploaded: {total_uploaded}")
        logger.info(f"\nCollections:")
        logger.info(f"  - ticaret_hukuku: {len(SAMPLE_TTK_ARTICLES)} articles")
        logger.info(f"  - borclar_hukuku: {len(SAMPLE_TBK_ARTICLES)} articles")
        logger.info(f"  - icra_iflas: {len(SAMPLE_IIK_ARTICLES)} articles")
        
        # Close connections
        await mongodb_client.close()
        
        return total_uploaded
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("HukukYZ - Sample Legal Documents Creator")
    print("=" * 60)
    print()
    
    # Run async function
    total = asyncio.run(create_sample_documents())
    
    print()
    print("=" * 60)
    print(f"✅ Successfully created {total} sample documents!")
    print("=" * 60)
    print()
    print("You can now test the system with queries like:")
    print("  - 'TTK 11. madde nedir?'")
    print("  - 'Anonim şirket nasıl kurulur?'")
    print("  - 'TBK'da sözleşmenin kurulması'")
    print()
