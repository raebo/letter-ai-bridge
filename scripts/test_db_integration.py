import json
from app.core.config import settings
from app.database.services.entity_resolution.retrieve_infos_service import RetrieveInfosService
from app.database.connection import DBConnection


def run_live_test():
    DBConnection.set_config(settings.db_params)

    test_keys = {
            "PSN": ["PSN0113349"], 
            "SGH": ["SGH0103934"],
            "NST": ["NST0104832", "NST0103625"],
            "STM": ["STM0103862", "STM0103900"],
            "CRT": ["CRT0112501", "CRT0111666"],
            "PRC": ["PRC0100294", "PRC0100275"],
            # "WRK": ["WRK_Hebriden_Ouverture"],
            }

    print("="*60)
    print("LIVE DATABASE ENTITY RESOLUTION TEST")
    print("="*60)

    for prefix, keys in test_keys.items():
        print(f"\n--- Category: {prefix} ---")
        for key in keys:
            try:
                # 1. Call the service (hits DB -> InfoBuilder -> MetadataBuilder)
                result = RetrieveInfosService.get_info(prefix, key)

                if not result["info"]:
                    print(f"❌ [{key}]: No data found.")
                    continue

                # 2. Display the Searchable Info String
                print(f"✅ [{key}]")
                print(f"   INFO: {result['info']}")

                # 3. Display the Metadata (Pretty printed)
                meta_json = json.dumps(result['metadata'], indent=7, ensure_ascii=False)
                print(f"   META: {meta_json}")

            except Exception as e:
                print(f"🔥 [{key}]: Error occurred: {str(e)}")

    print("\n" + "="*60)
    print("TEST COMPLETE")

if __name__ == "__main__":
    run_live_test()
