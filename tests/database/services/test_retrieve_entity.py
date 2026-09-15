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
    # Since we are testing the Service's string-building logic, prefix/key/data
    # are all required positional arguments.
    res_1 = RetrieveInfosService.assemble_entity_package("PSN", "PSN_TEST_1", data_1)
    res_2 = RetrieveInfosService.assemble_entity_package("PSN", "PSN_TEST_2", data_2)
    res_3 = RetrieveInfosService.assemble_entity_package("PSN", "PSN_TEST_3", data_3)

    print("Test Case 1 Result: ", res_1)
    print("Test Case 2 Result: ", res_2)
    print("Test Case 3 Result: ", res_3)

    # Assertions on "info" (whitespace-normalized: InfoBuilder joins several
    # parts that each carry their own leading space, so incidental double
    # spaces are not part of the contract being tested here)
    info_1 = " ".join(res_1["info"].split())
    info_2 = " ".join(res_2["info"].split())
    info_3 = " ".join(res_3["info"].split())

    assert "Claude Lorrain (1600–1682)" in info_1
    assert "Johanna Kinkel (1810–??)" in info_2
    assert "[aka: Hanne, Hannchen]" in info_2
    assert "Joseph Fürst (??–1833)" in info_3
    assert "[MSB irrt.]" not in info_3  # Ensure error markers are cleaned
    assert "MSB irrt" not in info_3

    # --- Assertions for METADATA (Structured Hash) ---
    # PSN metadata (MetadataBuilder._build_person_meta) does not derive a
    # "lifespan" field — life dates only appear in the "info" prose above.
    # last_updated is passed through as-is (no reformatting/truncation).
    assert res_1["metadata"]["last_updated"] == "2021-10-14 12:20:35.076488"
    assert res_1["metadata"]["key"] == "PSN_TEST_1"

    # Case 2: missing death_year must not surface as a metadata error
    assert res_2["metadata"]["last_updated"] == "2021-10-14 12:20:35.076488"
    assert res_2["metadata"]["key"] == "PSN_TEST_2"


def test_sgh_formatting():
    # Test Case: Basic Sight Formatting
    data = {
        "name": "Eiffel Tower",
        "kind": "Paris, France",
        "notes": "Quelle: B. Boydell. Dublin. Grove Music Online. Retrieved 22 Feb. 2021.",
        "settlement_name": "Paris",
        "country_name": "France"
    }

    res = RetrieveInfosService.assemble_entity_package("SGH", "SGH_TEST_1", data)
    print("SGH Test Result: ", res)

    assert res["info"] == "Eiffel Tower (Paris, France) [Paris, France]"
    assert res["metadata"]["key"] == "SGH_TEST_1"
