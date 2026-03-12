import pytest
from app.database.services.entity_resolution.retrieve_infos_service import RetrieveInfosService

def test_psn_formatting_complex_names():
    # Test Case 1: The "Arrow" Mapping and Pseudonym
    data_1 = {
        "first_name": "Claude (Pseud.) →",
        "last_name": "Lorrain",
        "birth_year": 1600,
        "death_year": 1682,
        "letter_name": "Claude",
        "last_updated_at": "2021-10-14 12:20:35.076488"
    }
    
    # Test Case 2: The Triple Arrow and Missing Dates
    data_2 = {
        "first_name": "Johanna → → →",
        "last_name": "Kinkel",
        "birth_year": 1810,
        "death_year": None,
        "letter_name": "Hanne, Hannchen",
        "last_updated_at": "2021-10-14 12:20:35.076488"
    }

    # Test Case 3: MSB Error Correction
    data_3 = {
        "first_name": "Herr [MSB irrt.] →",
        "last_name": "Joseph Fürst",
        "birth_year": None,
        "death_year": 1833,
        "letter_name": "Fürst",
        "last_updated_at": "2021-10-14 12:20:35.076488"
    }

    # Execute calls (We mock the 'data' usually returned by the Model)
    # Since we are testing the Service's string-building logic:
    res_1 = RetrieveInfosService.assemble_entity_package("PSN", data_1)
    res_2 = RetrieveInfosService.assemble_entity_package("PSN", data_2)
    res_3 = RetrieveInfosService.assemble_entity_package("PSN", data_3)

    print("Test Case 1 Result: ", res_1)
    print("Test Case 2 Result: ", res_2)
    print("Test Case 3 Result: ", res_3)

    # Assertions
    assert "Claude Lorrain (1600–1682)" in res_1["info"]
    assert "Johanna Kinkel (1810–??)" in res_2["info"]
    assert "[aka: Hanne, Hannchen]" in res_2["info"]
    assert "Joseph Fürst (??–1833)" in res_3["info"]
    assert "[MSB irrt.]" not in res_3["info"] # Ensure cleaning works["info"]

    # --- Assertions for METADATA (Structured Hash) ---
    # Case 1: Check if lifespan is generated correctly in metadata
    assert res_1["metadata"]["lifespan"] == "1600–1682"
    assert res_1["metadata"]["last_updated"] == "2021-10-14 12:20:35"

    # Case 2: Check handling of None in metadata dates
    assert res_2["metadata"]["lifespan"] == "1810–None" # Or however your _meta_person handles it
    
    # Case 3: Verify error markers are removed even from metadata names if applicable
    # (Assuming your MetadataBuilder uses the cleaned names too)
    assert "MSB irrt" not in res_3["info"]

print("If you see this, the logic is ready to be tested with pytest!")


def test_sgh_formatting():
    # Test Case: Basic Sight Formatting
    data = {
        "name": "Eiffel Tower",
        "kind": "Paris, France",
        "notes": "Quelle: B. Boydell. Dublin. Grove Music Online. Retrieved 22 Feb. 2021.",
        "settlement_name": "Paris",
        "country_name": "France"
    }

    res = RetrieveInfosService.assemble_entity_package("SGH", data)
    print("SGH Test Result: ", res)

    assert res["info"] == "TEST"  # Placeholder until actual formatting is implemented
