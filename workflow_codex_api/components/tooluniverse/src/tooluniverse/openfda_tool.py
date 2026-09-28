import requests
from .base_tool import BaseTool
from .tool_registry import register_tool
import copy
import re
import os

# Cache for GraphQL query to avoid repeated string operations
_OPENTARGETS_DRUG_NAMES_QUERY = None
_OPENTARGETS_ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"


def _get_drug_names_query():
    """Get the GraphQL query for drug names (cached)"""
    global _OPENTARGETS_DRUG_NAMES_QUERY
    if _OPENTARGETS_DRUG_NAMES_QUERY is None:
        _OPENTARGETS_DRUG_NAMES_QUERY = (
            "\n      query drugNames($chemblId: String!) {\n        "
            "drug(chemblId: $chemblId) {\n          id\n          name\n          "  # noqa: E501
            "tradeNames\n          synonyms\n        }\n      }\n    "
        )
    return _OPENTARGETS_DRUG_NAMES_QUERY


def _execute_opentargets_query(chembl_id):
    """Directly execute OpenTargets GraphQL query (most efficient)"""
    try:
        from tooluniverse.graphql_tool import execute_query

        query = _get_drug_names_query()
        variables = {"chemblId": chembl_id}
        return execute_query(
            endpoint_url=_OPENTARGETS_ENDPOINT, query=query, variables=variables
        )
    except ImportError:
        # Fallback if graphql_tool not available
        import requests

        query = _get_drug_names_query()
        variables = {"chemblId": chembl_id}
        response = requests.post(
            _OPENTARGETS_ENDPOINT, json={"query": query, "variables": variables}
        )
        try:
            result = response.json()
            if "errors" in result:
                return None
            return result
        except Exception:
            return None


def check_keys_present(api_capabilities_dict, keys):
    for key in keys:
        levels = key.split(".")
        current_dict = api_capabilities_dict
        key_present = True
        for level in levels:
            if level not in current_dict:
                print(f"Key '{level}' not found in dictionary.")
                key_present = False
                break
            if "properties" in current_dict[level]:
                current_dict = current_dict[level]["properties"]
            else:
                current_dict = current_dict[level]
    return key_present


def extract_nested_fields(records, fields, keywords=None):
    """
    Recursively extracts nested fields from a list of dictionaries.

    :param records: List of dictionaries from which to extract fields
    :param fields: List of nested fields to extract, each specified with dot notation (e.g., 'openfda.brand_name')

    :return: List of dictionaries containing only the specified fields
    """
    extracted_records = []
    for record in records:
        extracted_record = {}
        for field in fields:
            keys = field.split(".")
            # print("keys", keys)
            value = record
            try:
                for key in keys:
                    value = value[key]
                if key != "openfda" and key != "generic_name" and key != "brand_name":
                    if len(keywords) > 0:
                        # print("key words:", keywords)
                        # print(value)
                        # print(type(value))
                        value = extract_sentences_with_keywords(value, keywords)
                extracted_record[field] = value
            except KeyError:
                extracted_record[field] = None
        if any(extracted_record.values()):
            extracted_records.append(extracted_record)
    return extracted_records


def map_properties_to_openfda_fields(arguments, search_fields):
    """
    Maps the provided arguments to the corresponding openFDA fields based on the search_fields mapping.

    :param arguments: The input arguments containing property names and values.
    :param search_fields: The mapping of property names to openFDA fields.

    :return: A dictionary with openFDA fields and corresponding values.
    """
    mapped_arguments = {}

    for key, value in list(arguments.items()):
        if key in search_fields:
            # print("key in search_fields:", key)
            openfda_fields = search_fields[key]
            if isinstance(openfda_fields, list):
                for field in openfda_fields:
                    mapped_arguments[field] = value
            else:
                mapped_arguments[openfda_fields] = value
            del arguments[key]
    arguments["search_fields"] = mapped_arguments
    return arguments


def extract_sentences_with_keywords(text_list, keywords):
    """
    Extracts sentences containing any of the specified keywords from the text.

    Parameters
    - text (str): The input text from which to extract sentences.
    - keywords (list): A list of keywords to search for in the text.

    Returns
    - list: A list of sentences containing any of the keywords.
    """
    sentences_with_keywords = []
    for text in text_list:
        # Compile a regular expression pattern for sentence splitting
        sentence_pattern = re.compile(r"(?<=[.!?]) +")
        # Split the text into sentences
        sentences = sentence_pattern.split(text)
        # Initialize a list to hold sentences with keywords

        # Iterate through each sentence
        for sentence in sentences:
            # Check if any of the keywords are present in the sentence
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                # If a keyword is found, add the sentence to the list
                sentences_with_keywords.append(sentence)

    return "......".join(sentences_with_keywords)


def search_openfda(
    params=None,
    endpoint_url=None,
    api_key=None,
    sort=None,
    limit=5,
    skip=None,
    count=None,
    exists=None,
    return_fields=None,
    exist_option="OR",
    search_keyword_option="AND",
    keywords_filter=True,
):
    # Initialize params if not provided
    if params is None:
        params = {}

    if return_fields == "ALL":
        exists = None

    # Initialize search fields and construct search query
    search_fields = params.get("search_fields", {})
    search_query = []
    keywords_list = []
    if search_fields:
        for field, value in search_fields.items():
            # Merge multiple continuous black spaces into one and use one '+'
            if (
                keywords_filter
                and field != "openfda.brand_name"
                and field != "openfda.generic_name"
            ):
                keywords_list.extend(value.split())
            if field == "openfda.generic_name":
                value = value.upper()  # all generic names are in uppercase
            value = value.replace(" and ", " ")  # remove 'and' in the search query
            value = value.replace(" AND ", " ")  # remove 'AND' in the search query
            # Remove quotes to avoid query errors
            value = value.replace('"', "")
            value = value.replace("'", "")
            value = " ".join(value.split())
            if search_keyword_option == "AND":
                search_query.append(f"{field}:({value.replace(' ', '+AND+')})")
            elif search_keyword_option == "OR":
                search_query.append(f"{field}:({value.replace(' ', '+')})")
            else:
                print("Invalid search_keyword_option. Please use 'AND' or 'OR'.")
        del params["search_fields"]
    if search_query:
        params["search"] = "+".join(search_query)
        params["search"] = "(" + params["search"] + ")"
    # Validate the presence of at least one of search, count, or sort
    if not (
        params.get("search")
        or params.get("count")
        or params.get("sort")
        or search_fields
    ):
        return {
            "error": "You must provide at least one of 'search', 'count', or 'sort' parameters."
        }

    # Set additional query parameters
    params["limit"] = params.get("limit", limit)
    params["sort"] = params.get("sort", sort)
    params["skip"] = params.get("skip", skip)
    params["count"] = params.get("count", count)
    if exists is not None:
        if isinstance(exists, str):
            exists = [exists]
        if "search" in params:
            if exist_option == "AND":
                params["search"] += (
                    "+AND+("
                    + "+AND+".join([f"_exists_:{keyword}" for keyword in exists])
                    + ")"
                )
            elif exist_option == "OR":
                params["search"] += (
                    "+AND+("
                    + "+".join([f"_exists_:{keyword}" for keyword in exists])
                    + ")"
                )
        else:
            if exist_option == "AND":
                params["search"] = "+AND+".join(
                    [f"_exists_:{keyword}" for keyword in exists]
                )
            elif exist_option == "OR":
                params["search"] = "+".join(
                    [f"_exists_:{keyword}" for keyword in exists]
                )
        # Ensure that at least one of the search fields exists
        params["search"] += (
            "+AND+("
            + "+".join([f"_exists_:{field}" for field in search_fields.keys()])
            + ")"
        )
        # params['search']+="+AND+_exists_:openfda"

    # Construct full query with additional parameters
    query = "&".join(
        [f"{key}={value}" for key, value in params.items() if value is not None]
    )
    full_url = f"{endpoint_url}?{query}"
    if api_key:
        full_url += f"&api_key={api_key}"

    print(full_url)

    response = requests.get(full_url)

    # Get the JSON response
    response_data = response.json()
    if "error" in response_data:
        print("Invalid Query: ", response_data["error"])
        return None

    # Extract meta information
    meta_info = response_data.get("meta", {})
    meta_info = meta_info.get("results", {})

    # Extract results and return only the specified return fields
    results = response_data.get("results", [])
    if return_fields == "ALL":
        return {"meta": meta_info, "results": results}
    # If count parameter is used, return results directly (count API format)
    if params.get("count") or count:
        return {"meta": meta_info, "results": results}
    required_fields = list(search_fields.keys()) + return_fields
    extracted_results = extract_nested_fields(results, required_fields, keywords_list)
    return {"meta": meta_info, "results": extracted_results}


@register_tool("FDATool")
class FDATool(BaseTool):
    def __init__(self, tool_config, endpoint_url, api_key=None):
        super().__init__(tool_config)
        fields = tool_config["fields"]
        self.search_fields = fields.get("search_fields", {})
        self.return_fields = fields.get("return_fields", [])
        self.exists = fields.get("exists", None)
        if self.exists is None:
            self.exists = self.return_fields
        self.endpoint_url = endpoint_url
        self.api_key = api_key or os.getenv("FDA_API_KEY")

    def run(self, arguments):
        arguments = copy.deepcopy(arguments)
        # Set default limit to 100 if not provided
        if "limit" not in arguments or arguments["limit"] is None:
            arguments["limit"] = 100
        mapped_arguments = map_properties_to_openfda_fields(
            arguments, self.search_fields
        )
        return search_openfda(
            mapped_arguments,
            endpoint_url=self.endpoint_url,
            api_key=self.api_key,
            exists=self.exists,
            return_fields=self.return_fields,
            exist_option="OR",
        )


@register_tool("FDADrugLabel")
class FDADrugLabelTool(FDATool):
    def __init__(self, tool_config, api_key=None):
        endpoint_url = "https://api.fda.gov/drug/label.json"
        super().__init__(tool_config, endpoint_url, api_key)

    def _is_chembl_id(self, value):
        """Check if the value looks like a ChEMBL ID"""
        if not isinstance(value, str):
            return False
        # Normalize to uppercase for consistent handling
        return value.upper().startswith("CHEMBL")

    def _convert_id_to_drug_name(self, chembl_id):
        """Convert ChEMBL ID to drug name using OpenTargets API"""
        try:
            # Directly call GraphQL API (most efficient, no tool overhead)
            result = _execute_opentargets_query(chembl_id)

            if result and isinstance(result, dict):
                # Extract drug name from result
                drug = None
                if "drug" in result:
                    drug = result["drug"]
                elif "data" in result and "drug" in result["data"]:
                    drug = result["data"]["drug"]

                if drug:
                    # Prefer generic name, fallback to name, then trade names
                    name = drug.get("name")
                    if name:
                        msg = f"Converted ChEMBL ID {chembl_id} to drug name: {name}"
                        print(msg)
                        return name

                    # Try trade names as fallback
                    trade_names = drug.get("tradeNames", [])
                    if trade_names:
                        msg = (
                            f"Converted ChEMBL ID {chembl_id} "
                            f"to trade name: {trade_names[0]}"
                        )
                        print(msg)
                        return trade_names[0]

            # No drug name found - the compound may not be approved as a drug
            msg = (
                f"Warning: Could not convert ChEMBL ID {chembl_id} "
                f"to drug name. This compound may not be approved as a drug "
                f"or may not be available in the OpenTargets database."
            )
            print(msg)
            return None
        except Exception as e:
            msg = f"Error converting ChEMBL ID {chembl_id} to drug name: {e}"
            print(msg)
            return None

    def run(self, arguments):
        """Override run to support ChEMBL ID conversion"""
        arguments = copy.deepcopy(arguments)

        # Check if drug_name parameter is a ChEMBL ID
        drug_name = arguments.get("drug_name")
        # Only process if drug_name is a non-empty string
        if drug_name and isinstance(drug_name, str) and drug_name.strip():
            # Strip whitespace before checking
            drug_name = drug_name.strip()
            if self._is_chembl_id(drug_name):
                # Normalize ChEMBL ID to uppercase (OpenTargets API expects uppercase)
                chembl_id = drug_name.upper()
                # Convert ChEMBL ID to drug name
                converted_name = self._convert_id_to_drug_name(chembl_id)
                if converted_name:
                    arguments["drug_name"] = converted_name
                else:
                    # If conversion fails, provide helpful error message
                    error_msg = (
                        f"Could not convert ChEMBL ID {drug_name} to drug name. "
                        f"This compound (ChEMBL ID: {drug_name}) may not be "
                        f"approved as a drug yet, or it may not be available "
                        f"in the OpenTargets database. Please provide a drug "
                        f"name directly if you know it, or check if this "
                        f"compound is actually approved as a pharmaceutical "
                        f"drug."
                    )
                    return {"error": error_msg}
            else:
                # Not a ChEMBL ID, use original value (strip whitespace)
                arguments["drug_name"] = drug_name

        # Call parent run method
        return super().run(arguments)


@register_tool("FDADrugLabelSearchTool")
class FDADrugLabelSearchTool(FDATool):
    def __init__(self, tool_config=None, api_key=None):
        self.tool_config = {
            "name": "FDADrugLabelSearch",
            "description": "Retrieve information of a specific drug.",
            "label": ["search", "drug"],
            "type": "FDADrugLabelSearch",
            "parameter": {
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "The name of the drug.",
                        "required": True,
                    },
                    "return_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "ALL",
                                "abuse",
                                "accessories",
                                "active_ingredient",
                                "adverse_reactions",
                                "alarms",
                                "animal_pharmacology_and_or_toxicology",
                                "ask_doctor",
                                "ask_doctor_or_pharmacist",
                                "assembly_or_installation_instructions",
                                "boxed_warning",
                                "calibration_instructions",
                                "carcinogenesis_and_mutagenesis_and_impairment_of_fertility",
                                "cleaning",
                                "clinical_pharmacology",
                                "clinical_studies",
                                "compatible_accessories",
                                "components",
                                "contraindications",
                                "controlled_substance",
                                "dependence",
                                "description",
                                "diagram_of_device",
                                "disposal_and_waste_handling",
                                "do_not_use",
                                "dosage_and_administration",
                                "dosage_forms_and_strengths",
                                "drug_abuse_and_dependence",
                                "drug_and_or_laboratory_test_interactions",
                                "drug_interactions",
                                "effective_time",
                                "environmental_warning",
                                "food_safety_warning",
                                "general_precautions",
                                "geriatric_use",
                                "guaranteed_analysis_of_feed",
                                "health_care_provider_letter",
                                "health_claim",
                                "how_supplied",
                                "id",
                                "inactive_ingredient",
                                "indications_and_usage",
                                "information_for_owners_or_caregivers",
                                "information_for_patients",
                                "instructions_for_use",
                                "intended_use_of_the_device",
                                "keep_out_of_reach_of_children",
                                "labor_and_delivery",
                                "laboratory_tests",
                                "mechanism_of_action",
                                "microbiology",
                                "nonclinical_toxicology",
                                "nonteratogenic_effects",
                                "nursing_mothers",
                                "openfda",
                                "other_safety_information",
                                "overdosage",
                                "package_label_principal_display_panel",
                                "patient_medication_information",
                                "pediatric_use",
                                "pharmacodynamics",
                                "pharmacogenomics",
                                "pharmacokinetics",
                                "precautions",
                                "pregnancy",
                                "pregnancy_or_breast_feeding",
                                "purpose",
                                "questions",
                                "recent_major_changes",
                                "references",
                                "residue_warning",
                                "risks",
                                "route",
                                "safe_handling_warning",
                                "set_id",
                                "spl_indexing_data_elements",
                                "spl_medguide",
                                "spl_patient_package_insert",
                                "spl_product_data_elements",
                                "spl_unclassified_section",
                                "statement_of_identity",
                                "stop_use",
                                "storage_and_handling",
                                "summary_of_safety_and_effectiveness",
                                "teratogenic_effects",
                                "troubleshooting",
                                "use_in_specific_populations",
                                "user_safety_warnings",
                                "version",
                                "warnings",
                                "warnings_and_cautions",
                                "when_using",
                                "meta",
                            ],
                            "description": "Searchable field.",
                        },
                        "description": "Fields to search within drug labels.",
                        "required": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The number of records to return.",
                        "required": False,
                    },
                    "skip": {
                        "type": "integer",
                        "description": "The number of records to skip.",
                        "required": False,
                    },
                },
            },
            "fields": {
                "search_fields": {
                    "drug_name": ["openfda.brand_name", "openfda.generic_name"]
                },
            },
        }
        endpoint_url = "https://api.fda.gov/drug/label.json"
        super().__init__(self.tool_config, endpoint_url, api_key)

    def run(self, arguments):
        arguments = copy.deepcopy(arguments)
        mapped_arguments = map_properties_to_openfda_fields(
            arguments, self.search_fields
        )
        return_fields = arguments["return_fields"]
        del arguments["return_fields"]
        return search_openfda(
            mapped_arguments,
            endpoint_url=self.endpoint_url,
            api_key=self.api_key,
            return_fields=return_fields,
            exists=return_fields,
            exist_option="OR",
        )


@register_tool("FDADrugLabelSearchIDTool")
class FDADrugLabelSearchIDTool(FDATool):
    def __init__(self, tool_config=None, api_key=None):
        self.tool_config = {
            "name": "FDADrugLabelSearchALLTool",
            "description": "Retrieve any related information to the query.",
            "label": ["search", "drug"],
            "type": "FDADrugLabelSearch",
            "parameter": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "key words need to be searched.",
                        "required": True,
                    },
                    "return_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "ALL",
                                "abuse",
                                "accessories",
                                "active_ingredient",
                                "adverse_reactions",
                                "alarms",
                                "animal_pharmacology_and_or_toxicology",
                                "ask_doctor",
                                "ask_doctor_or_pharmacist",
                                "assembly_or_installation_instructions",
                                "boxed_warning",
                                "calibration_instructions",
                                "carcinogenesis_and_mutagenesis_and_impairment_of_fertility",
                                "cleaning",
                                "clinical_pharmacology",
                                "clinical_studies",
                                "compatible_accessories",
                                "components",
                                "contraindications",
                                "controlled_substance",
                                "dependence",
                                "description",
                                "diagram_of_device",
                                "disposal_and_waste_handling",
                                "do_not_use",
                                "dosage_and_administration",
                                "dosage_forms_and_strengths",
                                "drug_abuse_and_dependence",
                                "drug_and_or_laboratory_test_interactions",
                                "drug_interactions",
                                "effective_time",
                                "environmental_warning",
                                "food_safety_warning",
                                "general_precautions",
                                "geriatric_use",
                                "guaranteed_analysis_of_feed",
                                "health_care_provider_letter",
                                "health_claim",
                                "how_supplied",
                                "id",
                                "inactive_ingredient",
                                "indications_and_usage",
                                "information_for_owners_or_caregivers",
                                "information_for_patients",
                                "instructions_for_use",
                                "intended_use_of_the_device",
                                "keep_out_of_reach_of_children",
                                "labor_and_delivery",
                                "laboratory_tests",
                                "mechanism_of_action",
                                "microbiology",
                                "nonclinical_toxicology",
                                "nonteratogenic_effects",
                                "nursing_mothers",
                                "openfda",
                                "other_safety_information",
                                "overdosage",
                                "package_label_principal_display_panel",
                                "patient_medication_information",
                                "pediatric_use",
                                "pharmacodynamics",
                                "pharmacogenomics",
                                "pharmacokinetics",
                                "precautions",
                                "pregnancy",
                                "pregnancy_or_breast_feeding",
                                "purpose",
                                "questions",
                                "recent_major_changes",
                                "references",
                                "residue_warning",
                                "risks",
                                "route",
                                "safe_handling_warning",
                                "set_id",
                                "spl_indexing_data_elements",
                                "spl_medguide",
                                "spl_patient_package_insert",
                                "spl_product_data_elements",
                                "spl_unclassified_section",
                                "statement_of_identity",
                                "stop_use",
                                "storage_and_handling",
                                "summary_of_safety_and_effectiveness",
                                "teratogenic_effects",
                                "troubleshooting",
                                "use_in_specific_populations",
                                "user_safety_warnings",
                                "version",
                                "warnings",
                                "warnings_and_cautions",
                                "when_using",
                                "meta",
                            ],
                            "description": "Searchable field.",
                        },
                        "description": "Fields to search within drug labels.",
                        "required": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The number of records to return.",
                        "required": False,
                    },
                    "skip": {
                        "type": "integer",
                        "description": "The number of records to skip.",
                        "required": False,
                    },
                },
            },
            "fields": {
                "search_fields": {"query": ["id"]},
            },
        }
        endpoint_url = "https://api.fda.gov/drug/label.json"
        super().__init__(self.tool_config, endpoint_url, api_key)

    def run(self, arguments):
        arguments = copy.deepcopy(arguments)
        mapped_arguments = map_properties_to_openfda_fields(
            arguments, self.search_fields
        )
        return_fields = arguments["return_fields"]
        del arguments["return_fields"]
        return search_openfda(
            mapped_arguments,
            endpoint_url=self.endpoint_url,
            api_key=self.api_key,
            return_fields=return_fields,
            exists=return_fields,
            exist_option="OR",
        )


@register_tool("FDADrugLabelGetDrugGenericNameTool")
class FDADrugLabelGetDrugGenericNameTool(FDADrugLabelTool):
    def __init__(self, tool_config=None, api_key=None):
        if tool_config is None:
            tool_config = {
                "name": "get_drug_generic_name",
                "description": "Get the drug’s generic name based on the drug's generic or brand name.",
                "parameter": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "The generic or brand name of the drug.",
                            "required": True,
                        }
                    },
                },
                "fields": {
                    "search_fields": {
                        "drug_name": ["openfda.brand_name", "openfda.generic_name"]
                    },
                    "return_fields": ["openfda.generic_name"],
                },
                "type": "FDADrugLabelGetDrugGenericNameTool",
                "label": ["FDADrugLabel", "purpose", "FDA"],
            }

        from .data.fda_drugs_with_brand_generic_names_for_tool import drug_list

        self.brand_to_generic = {
            drug["brand_name"]: drug["generic_name"] for drug in drug_list
        }
        self.generic_to_brand = {
            drug["generic_name"]: drug["brand_name"] for drug in drug_list
        }

        super().__init__(tool_config, api_key)

    def run(self, arguments):
        drug_info = {}

        drug_name = arguments.get("drug_name")
        if "-" in drug_name:
            drug_name = drug_name.split("-")[
                0
            ]  # to handle some drug names such as tarlatamab-dlle
        if drug_name in self.brand_to_generic:
            drug_info["openfda.generic_name"] = self.brand_to_generic[drug_name]
            drug_info["openfda.brand_name"] = drug_name
        elif drug_name in self.generic_to_brand:
            drug_info["openfda.brand_name"] = self.generic_to_brand[drug_name]
            drug_info["openfda.generic_name"] = drug_name
        else:
            results = super().run(arguments)
            if results is not None:
                drug_info["openfda.generic_name"] = results["results"][0][
                    "openfda.generic_name"
                ][0]
                drug_info["openfda.brand_name"] = results["results"][0][
                    "openfda.brand_name"
                ][0]
                print("drug_info", drug_info)
            else:
                drug_info = None
        return drug_info


@register_tool("FDADrugLabelAggregated")
class FDADrugLabelGetDrugNamesByIndicationAggregated(FDADrugLabelTool):
    """
    Enhanced version of FDA_get_drug_names_by_indication that:
    - Iterates through all results in batches of 100 (no limit)
    - Aggregates results by generic name
    - Returns one entry per generic name with indication and all brand names
    """

    def __init__(self, tool_config, api_key=None):
        super().__init__(tool_config, api_key)

    def run(self, arguments):
        """
        Run the aggregated drug names search by indication.

        Iterates through all results in batches of 100, aggregates by
        generic name, and returns a list where each entry contains:
        - generic_name: The generic drug name
        - indication: The indication (from input)
        - brand_names: List of all brand names for this generic name
        """
        arguments = copy.deepcopy(arguments)
        indication = arguments.get("indication")

        if not indication:
            return {"error": "indication parameter is required"}

        # Dictionary to aggregate results by generic name
        # Key: generic_name (normalized), Value: set of brand names
        aggregated_results = {}

        # Iterate through results in batches of 1000
        step = 1000
        skip = 0
        total_fetched = 0
        max_iterations = 1000  # Safety limit to prevent infinite loops

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Prepare arguments for this batch
            batch_arguments = {"indication": indication, "limit": step, "skip": skip}

            # Call parent run method to get results
            batch_result = super().run(batch_arguments)

            # Check for errors
            if batch_result is None or "error" in batch_result:
                # If we've already fetched some results, return what we have
                if total_fetched > 0:
                    break
                # Otherwise return the error
                error_msg = "No results returned"
                return batch_result if batch_result else {"error": error_msg}

            # Extract results
            results = batch_result.get("results", [])
            meta = batch_result.get("meta", {})

            # Process each result
            for result in results:
                generic_names = result.get("openfda.generic_name", [])
                brand_names = result.get("openfda.brand_name", [])

                # Handle both list and single value cases
                if not isinstance(generic_names, list):
                    generic_names = [generic_names] if generic_names else []
                if not isinstance(brand_names, list):
                    brand_names = [brand_names] if brand_names else []

                # Normalize and process generic names
                for generic_name in generic_names:
                    if not generic_name:
                        continue

                    # Normalize generic name (uppercase, strip whitespace)
                    normalized_generic = str(generic_name).upper().strip()

                    if normalized_generic:
                        # Initialize if not exists
                        if normalized_generic not in aggregated_results:
                            aggregated_results[normalized_generic] = set()

                        # Add all brand names for this generic name
                        for brand_name in brand_names:
                            if brand_name:
                                normalized_brand = str(brand_name).strip()
                                if normalized_brand:
                                    aggregated_results[normalized_generic].add(
                                        normalized_brand
                                    )

            total_fetched += len(results)

            # Check if we've reached the end
            # If we got fewer results than requested, we've reached the end
            if len(results) < step:
                # No more results to fetch
                break

            # Also check meta for total if available
            total_available = meta.get("total", None)
            if total_available is not None:
                if skip + len(results) >= total_available:
                    # Reached the total available
                    break

            # Move to next batch
            skip += step

        # Convert aggregated results to list format
        result_list = []
        for generic_name, brand_names_set in sorted(aggregated_results.items()):
            result_list.append(
                {
                    "generic_name": generic_name,
                    "indication": indication,
                    "brand_names": sorted(list(brand_names_set)),
                }
            )

        return {
            "meta": {
                "total_generic_names": len(result_list),
                "total_records_processed": total_fetched,
                "indication": indication,
            },
            "results": result_list,
        }


@register_tool("FDADrugLabelStats")
class FDADrugLabelGetDrugNamesByIndicationStats(FDADrugLabelTool):
    """
    Enhanced version using FDA count API to efficiently aggregate drug names
    by indication. Uses count mechanism to get brand_name and generic_name
    distributions without fetching full records.
    """

    def __init__(self, tool_config, api_key=None):
        super().__init__(tool_config, api_key)

    def run(self, arguments):
        """
        Run the aggregated drug names search using count API.

        Uses count API to:
        1. Get all unique generic names for the indication
        2. For each generic name, get corresponding brand names
        3. Return aggregated results
        """
        arguments = copy.deepcopy(arguments)
        indication = arguments.get("indication")

        if not indication:
            return {"error": "indication parameter is required"}

        # Step 1: Get all unique generic names using count API
        # Build search query for indication
        # Use the same logic as parent class for building search query
        indication_processed = indication.replace(" and ", " ")
        indication_processed = indication_processed.replace(" AND ", " ")
        indication_processed = " ".join(indication_processed.split())
        # Remove or escape quotes to avoid query errors
        indication_processed = indication_processed.replace('"', "")
        indication_processed = indication_processed.replace("'", "")
        indication_query = indication_processed.replace(" ", "+")
        search_query = f'indications_and_usage:"{indication_query}"'

        # Get all unique generic names using count API (use large limit)
        generic_count_params = {
            "search": search_query,
            "count": "openfda.generic_name.exact",
            "limit": 1000,  # Large limit to get all results
        }

        generic_count_result = search_openfda(
            generic_count_params,
            endpoint_url=self.endpoint_url,
            api_key=self.api_key,
            return_fields=[],
            exist_option="OR",
        )

        # Handle no matches found as empty result, not error
        if generic_count_result is None:
            all_generic_names_data = []
        elif "error" in generic_count_result:
            # Check if it's a "No matches found" error
            error_msg = str(generic_count_result.get("error", {}))
            if "No matches found" in error_msg or "NOT_FOUND" in error_msg:
                all_generic_names_data = []
            else:
                return generic_count_result
        else:
            all_generic_names_data = generic_count_result.get("results", [])

        if not all_generic_names_data:
            return {
                "meta": {
                    "total_generic_names": 0,
                    "total_brand_names": 0,
                    "indication": indication,
                },
                "results": {"generic_names": [], "brand_names": []},
            }

        # Step 2: Get all brand names using count API (only 2 API calls total)
        brand_count_params = {
            "search": search_query,
            "count": "openfda.brand_name.exact",
            "limit": 1000,  # Large limit to get all results
        }

        brand_count_result = search_openfda(
            brand_count_params,
            endpoint_url=self.endpoint_url,
            api_key=self.api_key,
            return_fields=[],
            exist_option="OR",
        )

        # Handle no matches found as empty result, not error
        if brand_count_result is None:
            brand_names_data = []
        elif "error" in brand_count_result:
            # Check if it's a "No matches found" error
            error_msg = str(brand_count_result.get("error", {}))
            if "No matches found" in error_msg or "NOT_FOUND" in error_msg:
                brand_names_data = []
            else:
                # For other errors, still return generic names if available
                brand_names_data = []
        else:
            brand_names_data = brand_count_result.get("results", [])

        # Format generic names
        generic_names_list = [
            {"term": item.get("term", "").strip(), "count": item.get("count", 0)}
            for item in all_generic_names_data
            if item.get("term", "").strip()
        ]
        generic_names_list = sorted(generic_names_list, key=lambda x: x["term"])

        # Format brand names
        brand_names_list = [
            {"term": item.get("term", "").strip(), "count": item.get("count", 0)}
            for item in brand_names_data
            if item.get("term", "").strip()
        ]
        brand_names_list = sorted(brand_names_list, key=lambda x: x["term"])

        return {
            "meta": {
                "total_generic_names": len(generic_names_list),
                "total_brand_names": len(brand_names_list),
                "indication": indication,
            },
            "results": {
                "generic_names": generic_names_list,
                "brand_names": brand_names_list,
            },
        }
